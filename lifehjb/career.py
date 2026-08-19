"""Career risk: involuntary separation, forced search, and seat availability.

Three things v2 assumed away:

* **Employment is not guaranteed until voluntary exit.** There is an involuntary
  separation hazard, and it is *correlated with bad market states* -- which is
  the tail that matters, because it is exactly when the portfolio cannot absorb
  the shock.
* **Seats do not arrive on demand.** They are drawn. Modelling that is what
  produces a dollar value for holding an outside option.
* **A crunch is a real commitment.** During lockout no seat change is on the
  table, so the solver must not be allowed to recommend one.

The correlation is the whole point of this module: separation is resolved
against the *same realized return draw* used to update wealth in that period,
never an independent one. ``tests/test_v3.py::test_correlation_is_real``
catches an implementation that gets this wrong.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from .model import (AvailabilityParams, CareerParams, CrunchParams, Params, Seat)

SEARCHING = "searching"
RETIRED_ACTION = "retired"
NO_STATE = -1          # sentinel: transition lands in the absorbing retired value fn


# --------------------------------------------------------------------------- #
# Seat variants                                                                #
# --------------------------------------------------------------------------- #

def searching_seat(cp: CareerParams) -> Seat:
    """Unemployment as a seat.

    Note what the defaults say: c_load 0.45, travel 0.05, autonomy 0.30,
    r 0.55 gives h* = 0.788, *above* h*(current350) = 0.668. Being out of work
    is less damaging to health than the current job. That is a finding, and the
    report surfaces it rather than burying it.
    """
    d = dict(c_load=0.45, travel=0.05, autonomy=0.30, r=0.55, phi=0.35)
    d.update(cp.searching_seat or {})
    return Seat(id=SEARCHING, y=0.0, c_load=d["c_load"], travel=d["travel"],
                autonomy=d["autonomy"], r=d["r"], phi=d["phi"],
                note="forced search after involuntary separation")


def crunch_variant(seat: Seat, multiplier: float) -> Seat:
    """The lockout seat: same job, cognitive load multiplied up."""
    return replace(seat, id=seat.id, c_load=min(seat.c_load * multiplier, 1.0),
                   note=seat.note + " (crunch lockout)")


def scarred_variant(seat: Seat, haircut: float) -> Seat:
    """Post-separation comp haircut: a reduced negotiating position, made permanent.

    The spec applies the haircut 'to whatever seat is drawn' on re-entry. Making
    it persistent rather than one-off is the scarring reading, and it is the one
    that matches what a reduced negotiating position actually does: it follows
    you. A single separation scars; a second does not compound.
    """
    if seat.y <= 0:
        return seat
    return replace(seat, y=seat.y * (1.0 - haircut))


def search_year_distribution(cp: CareerParams) -> Dict[int, float]:
    """Months-of-search distribution collapsed onto the annual grid.

    Rounds half **up**, so 3mo -> 0 further years and 6/9/12mo -> 1. At the
    defaults that is {0: 0.30, 1: 0.70}, an expected 0.70 unemployed years
    against a true expectation of 6.15 months = 0.51 years. The annual grid
    cannot represent a half-year of search, and rounding half up makes the model
    conservative rather than optimistic about career risk -- the right direction
    of error for a risk module. The mapping is general, so a distribution with
    longer tails produces 2-year states without any code change.
    """
    dist = cp.search_duration_dist or {3: 0.30, 6: 0.45, 9: 0.15, 12: 0.10}
    out: Dict[int, float] = {}
    for months, p in dist.items():
        yrs = int(np.floor(float(months) / 12.0 + 0.5))
        out[yrs] = out.get(yrs, 0.0) + float(p)
    total = sum(out.values())
    return {k: v / total for k, v in sorted(out.items())}


def severance_amount(seat: Seat, cp: CareerParams) -> float:
    return cp.severance_months * seat.y / 12.0


# --------------------------------------------------------------------------- #
# Career state                                                                 #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class CState:
    """(current seat, auxiliary counter, scarred).

    ``aux`` means different things per seat, which is what keeps the state space
    small: years already served in ``amat400`` (which drives the seasoning of its
    separation rate), remaining forced-search years in ``searching``, and nothing
    anywhere else.
    """
    seat: str
    aux: int = 0
    scarred: bool = False

    def label(self) -> str:
        bits = [self.seat]
        if self.seat == "amat400":
            bits.append(f"ten{self.aux}")
        elif self.seat == SEARCHING:
            bits.append(f"rem{self.aux}")
        if self.scarred:
            bits.append("scarred")
        return "/".join(bits)


class CareerSpace:
    """Enumerates the reachable career states and their transitions."""

    def __init__(self, params: Params, seats: Optional[Sequence[Seat]] = None):
        self.p = params
        self.cp = params.career
        self.av = params.availability
        self.cr = params.crunch
        base = list(seats if seats is not None else params.seats)
        self.base_seats = base
        self.work_seats = [s for s in base if not s.absorbing]
        self.retired = next(s for s in base if s.absorbing)
        self.search_seat = searching_seat(self.cp)

        self.max_search = max(search_year_distribution(self.cp)) if self.cp.enabled else 0
        self.n_ten = max(int(self.cp.amat_seasoning_years), 1)

        self.states: List[CState] = []
        scars = (False, True) if self.cp.enabled else (False,)
        for sc in scars:
            for s in self.work_seats:
                if s.id == "amat400" and self.cp.enabled:
                    # aux = years already served, 1..seasoning. Year 1 is served on
                    # arrival, so aux = 0 is unreachable and is not enumerated.
                    # With no separation hazard the seasoning is inert, so the
                    # dimension is dropped and the state space collapses to v2's.
                    for ten in range(1, self.n_ten + 1):
                        self.states.append(CState(s.id, ten, sc))
                else:
                    self.states.append(CState(s.id, 0, sc))
        if self.cp.enabled:
            for rem in range(self.max_search + 1):
                self.states.append(CState(SEARCHING, rem, True))

        self.idx: Dict[CState, int] = {s: i for i, s in enumerate(self.states)}
        self.n = len(self.states)
        self._seat_map = {s.id: s for s in base}
        self._variants: Dict[Tuple[str, bool, bool], Seat] = {}

    # -- seats ------------------------------------------------------------ #
    def seat_for(self, seat_id: str, scarred: bool = False, crunch: bool = False) -> Seat:
        key = (seat_id, bool(scarred), bool(crunch))
        hit = self._variants.get(key)
        if hit is not None:
            return hit
        s = self.search_seat if seat_id == SEARCHING else self._seat_map[seat_id]
        if scarred:
            s = scarred_variant(s, self.cp.reentry_haircut)
        if crunch:
            s = crunch_variant(s, self.cr.multiplier)
        self._variants[key] = s
        return s

    # -- structure -------------------------------------------------------- #
    def is_forced_search(self, i: int) -> bool:
        st = self.states[i]
        return st.seat == SEARCHING and st.aux > 0

    def in_lockout(self, ti: int) -> bool:
        return ti < int(self.cr.periods)

    def sep_rate(self, i: int, seat_id: str) -> float:
        """Annual separation probability for working *seat_id* from state *i*.

        The rate applies to the year about to be worked, so amat400's seasoning
        is read off *years already served*: a new joiner has served none and is
        in year 1, which is inside the seasoning window.
        """
        if seat_id == SEARCHING:
            return 0.0
        st = self.states[i]
        served = st.aux if (seat_id == "amat400" and st.seat == "amat400") else 0
        return self.cp.sep_rate(seat_id, served)

    def availability(self, i: int, ti: int) -> List[Tuple[str, float]]:
        """(seat id, probability it is on offer) for the choice at this state.

        Staying put is always possible; everything else may have to arrive.
        """
        st = self.states[i]
        if self.is_forced_search(i):
            return [(SEARCHING, 1.0)]
        if self.in_lockout(ti):
            # No seat change is permitted during the crunch. The spec names
            # current350; when a restricted roster does not contain it (the
            # fixed-seat analyses), the lockout falls back to holding whatever
            # seat the state is already in, which is the same commitment.
            locked = "current350" if "current350" in self._seat_map else st.seat
            return [(locked, 1.0)]

        av = self.av
        if av.unrestricted:
            return [(s.id, 1.0) for s in self.base_seats]
        # After separation the current employer's seats are off the table.
        gone = set(av.same_employer) if st.seat == SEARCHING else set()
        out: List[Tuple[str, float]] = []
        for s in self.base_seats:
            if s.id in gone:
                continue
            if s.id == st.seat:
                p = 1.0                                    # already in it
            elif s.id in ("current350", "downshift250") or s.absorbing:
                p = 1.0                                    # status quo / floor / stop
            elif s.id == "grind500":
                p = av.p_grind
            elif s.id == "oldrole350":
                p = av.p_oldrole
            elif s.id == "amat400":
                p = av.outside()
            elif s.id == "renegotiated350":
                # Negotiation is with the current employer about the current role,
                # so it is only on the table from current350. The 12-month one-shot
                # plus cooldown is folded into an effective annual arrival rate --
                # carrying the cooldown counter in the state triples the current350
                # branch for a second-order effect. See README.
                p = av.p_nego_effective if st.seat == "current350" else 0.0
            else:
                p = 1.0
            if p > 0.0:
                out.append((s.id, float(p)))
        return out

    def target(self, i: int, seat_id: str) -> int:
        """State index entered by choosing *seat_id* from state *i*."""
        st = self.states[i]
        if seat_id == RETIRED_ACTION:
            return NO_STATE
        if seat_id == SEARCHING:
            return self.idx[CState(SEARCHING, max(st.aux - 1, 0), True)]

        scarred = st.scarred
        if seat_id == "amat400" and self.cp.enabled:
            served = st.aux if st.seat == "amat400" else 0
            return self.idx[CState("amat400", min(served + 1, self.n_ten), scarred)]
        return self.idx[CState(seat_id, 0, scarred)]

    def separation_targets(self) -> List[Tuple[int, float]]:
        """(state index, probability) of the searching states entered on separation."""
        if not self.cp.enabled:
            return []
        return [(self.idx[CState(SEARCHING, k, True)], p)
                for k, p in search_year_distribution(self.cp).items()]

    def switched(self, i: int, seat_id: str) -> bool:
        """Does taking *seat_id* incur a switching cost?

        Leaving ``searching`` does not: you are already displaced, and the move
        cost has been paid by the separation itself.
        """
        st = self.states[i]
        if st.seat == SEARCHING:
            return False
        return seat_id != st.seat

    def start_index(self, seat_id: str = "current350") -> int:
        """Index of the starting career state.

        Falls back to the roster's first working seat when the named seat is not
        in it -- the fixed-seat analyses restrict the roster to one seat plus
        retirement.
        """
        key = CState(seat_id, 0, False)
        if key in self.idx:
            return self.idx[key]
        first = self.work_seats[0]
        aux = 1 if first.id == "amat400" else 0
        return self.idx[CState(first.id, aux, False)]


# --------------------------------------------------------------------------- #
# Metrics                                                                      #
# --------------------------------------------------------------------------- #

def annuity_factor(params: Params, seat_id: str = "current350") -> float:
    """Discounted survival-weighted horizon, sum_k beta^k * S_k.

    Converts a utility *stock* into an equivalent constant flow. Using rho as a
    perpetuity rate instead would understate the flow by roughly a factor of two,
    because the horizon here is ~25 discounted survival-years, not infinite.
    """
    from .model import death_prob
    from . import health as _H
    beta = np.exp(-params.rho)
    seat = params.seat(seat_id) if seat_id in params.seat_map else params.seats[0]
    h = float(params.h0)
    surv, total = 1.0, 0.0
    for k, age in enumerate(params.ages[:-1]):
        total += (beta ** k) * surv
        q = float(np.atleast_1d(death_prob(float(age), np.array([h]), params))[0])
        surv *= (1.0 - q)
        h = float(_H.step(h, seat, params.health, float(_H.h_max(float(age), params.health))))
    return total


def monthly_full_expenses(params: Params) -> float:
    return params.annual_full_expenses / 12.0


def runway_months(W: float, params: Params) -> float:
    """The concrete operational meaning of W_BATNA: months of full expenses on hand."""
    m = monthly_full_expenses(params)
    return float(W) / m if m > 0 else float("inf")


def expected_cycle_multiplier(w: np.ndarray, down: np.ndarray, factor: float) -> float:
    """E[cycle_mult] under a given return distribution -- used for H valuation."""
    p_down = float(w[down].sum())
    return 1.0 + (factor - 1.0) * p_down


def stress_test(params: Params, W: float, seat: Seat, drawdown: float,
                search_years: Optional[float] = None) -> Dict[str, float]:
    """Joint scenario: a portfolio drawdown *and* separation in the same year.

    This is the scenario W_BATNA exists for. Reports post-shock wealth, runway,
    and whether liquid assets survive the search.
    """
    cp = params.career
    sev = severance_amount(seat, cp)
    dist = search_year_distribution(cp)
    yrs = search_years if search_years is not None else sum(k * p for k, p in dist.items())

    W_after = W * (1.0 + drawdown) + sev
    burn = params.annual_full_expenses * (yrs + 1.0)     # search year(s) plus the shock year
    return dict(
        W_pre=float(W), W_post_drawdown=float(W * (1.0 + drawdown)),
        severance=float(sev), W_after=float(W_after),
        runway_months=runway_months(W_after, params),
        burn_during_search=float(burn),
        W_at_reentry=float(W_after - burn),
        exhausts=float(W_after < burn),
        search_years=float(yrs),
    )


# --------------------------------------------------------------------------- #
# The option value of a maintained outside option                              #
# --------------------------------------------------------------------------- #

@dataclass
class OptionValue:
    total: float                  # $/yr
    insurance: float              # component attributable to the separation hazard
    bargaining: float             # component attributable to seat availability
    V_maintained: float
    V_unmaintained: float
    V_W: float
    p_outside_maintained: float
    p_outside_unmaintained: float
    phi_maintain: float
    scenario: str

    @property
    def as_fraction_of_net(self) -> float:
        return self.total


def _value_and_vw(params: Params, b: float, scenario: str, state_seat: str = "current350"):
    """Solve v3 and read (V, V_W) at the subject's current state."""
    from .solver import shadow_prices_v3, solve_v3        # local: solver imports career
    sol = solve_v3(params, scenario=scenario, b=b)
    i = sol.space.start_index(state_seat)
    sp = shadow_prices_v3(sol, params.W0, params.h0, params.age0, i)
    return sp["V"], sp["V_W"]


def option_value_outside(params: Params, b: float, scenario: Optional[str] = None,
                         annualize: bool = True) -> OptionValue:
    """OV = V(maintain) - V(no maintain), at the current state, in dollars.

    Decomposed by re-running both legs with the separation hazard switched off.
    What survives with no separation risk is the **bargaining** component -- the
    value of being able to move to a better seat. The remainder is **insurance**:
    the option is worth more precisely when you are more likely to need it, which
    is the mechanism that makes it insurance rather than a bluff.

    ``annualize`` converts the utility difference into an equivalent constant
    dollar flow over the model's own discounted survival horizon, so the number
    reads as $/yr rather than as a stock.
    """
    scen = scenario or params.scenario
    av = params.availability

    on = params.evolve(availability=replace(av, maintain_outside_option=True))
    off = params.evolve(availability=replace(av, maintain_outside_option=False))
    V_on, VW_on = _value_and_vw(on, b, scen)
    V_off, _ = _value_and_vw(off, b, scen)

    A = annuity_factor(params)
    scale = (1.0 / A) if annualize else 1.0
    total = (V_on - V_off) / VW_on * scale

    # Bargaining-only leg: same comparison with the separation hazard removed.
    nosep = replace(params.career, base_sep={k: 0.0 for k in params.career.base_sep})
    on_b = on.evolve(career=nosep)
    off_b = off.evolve(career=nosep)
    Vb_on, VWb_on = _value_and_vw(on_b, b, scen)
    Vb_off, _ = _value_and_vw(off_b, b, scen)
    bargaining = (Vb_on - Vb_off) / VWb_on * scale

    return OptionValue(total=total, insurance=total - bargaining, bargaining=bargaining,
                       V_maintained=V_on, V_unmaintained=V_off, V_W=VW_on,
                       p_outside_maintained=av.p_outside,
                       p_outside_unmaintained=av.p_outside_unmaintained,
                       phi_maintain=av.phi_maintain, scenario=scen)

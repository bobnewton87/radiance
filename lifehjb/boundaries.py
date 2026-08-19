"""Three wealth thresholds that are routinely conflated.

They answer different questions and they are an order of magnitude apart:

* ``W_BATNA``  -- the wealth at which walking away is *credible in a
  negotiation*. Runway, not retirement.
* ``W_coast``  -- the wealth today that drifts up to the retirement number by a
  target age with **zero further saving**.
* ``W_star``   -- the solver's actual free boundary: the smallest wealth at
  which the optimal seat is ``retired``.

Ordering at the defaults is W_BATNA < W_coast(late) < W_coast(early) < W_star.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np

from . import health as H
from .model import Params, death_prob, social_security
from .solver import Solution


@dataclass
class BoundaryReport:
    W_BATNA: float
    runway_years: float
    annual_full_expenses: float
    W_star_by_age_h0: Dict[int, float]
    W_star_by_age_hstar: Dict[int, float]
    W_star_now: float
    W_coast: Dict[int, float]
    g_real: float
    h0: float
    h_current_star: float
    W_now: float

    def multiples(self) -> Dict[str, float]:
        w = self.W_now
        out = {"W_BATNA": self.W_BATNA / w}
        for a, v in sorted(self.W_coast.items()):
            out[f"W_coast({a})"] = v / w
        out["W_star"] = self.W_star_now / w
        return out


def w_star(sol: Solution, age: float, h: float) -> float:
    """Smallest grid wealth at which the optimal seat is ``retired`` at (age, h).

    Read as a *free boundary*: the largest wealth still choosing to work, plus
    one grid step. Returns +inf if the agent never retires at that (age, h).
    """
    ri = sol.retired_index()
    if ri < 0:
        return float("inf")
    g = sol.grids
    ti = int(np.clip(round(age - sol.params.age0), 0, sol.pol_e.shape[0] - 1))
    j = 0 if g.n_h == 1 else int(np.clip(round(np.interp(h, g.h, np.arange(g.n_h))),
                                         0, g.n_h - 1))
    seats = sol.pol_e[ti, :, j]
    working = np.nonzero(seats != ri)[0]
    if working.size == 0:
        return float(g.W[0])
    last = int(working[-1])
    if last >= g.n_W - 1:
        return float("inf")
    return float(g.W[last + 1])


def w_star_curve(sol: Solution, ages: Sequence[float], h: float) -> Dict[int, float]:
    return {int(a): w_star(sol, float(a), h) for a in ages}


def w_batna(params: Params) -> float:
    """Credible-walk-away wealth: runway years of full expenses."""
    return params.runway_years * params.annual_full_expenses


def years_to_target(W0: float, target: float, g_real: float,
                    saving_per_year: float = 0.0) -> float:
    """Years for wealth to reach *target*, growing at g_real and saving each year.

    Answers the question a reader actually has -- "when do I get there?" -- for a
    given savings rate. Returns inf if the target is never reached.
    """
    W, g = float(W0), float(g_real)
    if W >= target:
        return 0.0
    for k in range(1, 200):
        W = W * (1.0 + g) + saving_per_year
        if W >= target:
            return float(k)
    return float("inf")


def w_coast(params: Params, target_age: int, w_star_at_target: float,
            g_real: float) -> float:
    """Wealth today that reaches the retirement number by *target_age* unaided."""
    yrs = float(target_age) - params.age0
    if yrs <= 0:
        return w_star_at_target
    return w_star_at_target / (1.0 + g_real) ** yrs


def compute(sol: Solution, params: Optional[Params] = None,
            ages: Optional[Sequence[float]] = None) -> BoundaryReport:
    p = params or sol.params
    sc = p.returns[sol.scenario]
    g_real = sc.geometric_real_full_equity

    h_cur = H.h_star(p.seat("current350"), p.health) if "current350" in p.seat_map \
        else p.h0
    ages = list(ages) if ages is not None else list(range(int(p.age0), 71))

    by_h0 = w_star_curve(sol, ages, p.h0)
    by_hs = w_star_curve(sol, ages, h_cur)

    coast = {}
    for a in p.coast_target_ages:
        wt = w_star(sol, float(a), h_cur)
        coast[int(a)] = w_coast(p, int(a), wt, g_real)

    return BoundaryReport(
        W_BATNA=w_batna(p), runway_years=p.runway_years,
        annual_full_expenses=p.annual_full_expenses,
        W_star_by_age_h0=by_h0, W_star_by_age_hstar=by_hs,
        W_star_now=w_star(sol, p.age0, p.h0), W_coast=coast, g_real=g_real,
        h0=p.h0, h_current_star=h_cur, W_now=p.W0,
    )


# --------------------------------------------------------------------------- #
# v3                                                                           #
# --------------------------------------------------------------------------- #

def w_star_v3(sol, age: float, h: float, state: Optional[int] = None) -> float:
    """Free boundary under the v3 solution.

    The stopping decision is read off the *preference ordering*: the agent stops
    when ``retired`` is the top-ranked action, since retirement is always on
    offer. That is the same test as v2's ``e* == retired``, expressed in the
    ranking the v3 solver stores.
    """
    g = sol.grids
    ri = sol.retired_action
    i = int(sol.space.start_index() if state is None else state)
    ti = int(np.clip(round(age - sol.params.age0), 0, sol.pol_rank.shape[0] - 1))
    j = 0 if g.n_h == 1 else int(np.clip(round(np.interp(h, g.h, np.arange(g.n_h))),
                                         0, g.n_h - 1))
    top = sol.pol_rank[ti, i, :, j, 0]
    working = np.nonzero(top != ri)[0]
    if working.size == 0:
        return float(g.W[0])
    last = int(working[-1])
    if last >= g.n_W - 1:
        return float("inf")
    return float(g.W[last + 1])


def compute_v3(sol, params: Optional[Params] = None,
               ages: Optional[Sequence[float]] = None,
               state: Optional[int] = None) -> BoundaryReport:
    """The three boundaries, read off a v3 solution."""
    p = params or sol.params
    sc = p.returns[sol.scenario]
    g_real = sc.geometric_real_full_equity
    h_cur = (H.h_star(p.seat("current350"), p.health)
             if "current350" in p.seat_map else p.h0)
    ages = list(ages) if ages is not None else list(range(int(p.age0), 71))

    by_h0 = {int(a): w_star_v3(sol, float(a), p.h0, state) for a in ages}
    by_hs = {int(a): w_star_v3(sol, float(a), h_cur, state) for a in ages}
    coast = {int(a): w_coast(p, int(a), w_star_v3(sol, float(a), h_cur, state), g_real)
             for a in p.coast_target_ages}

    return BoundaryReport(
        W_BATNA=w_batna(p), runway_years=p.runway_years,
        annual_full_expenses=p.annual_full_expenses,
        W_star_by_age_h0=by_h0, W_star_by_age_hstar=by_hs,
        W_star_now=_first_finite_w_star(sol, p, state), W_coast=coast, g_real=g_real,
        h0=p.h0, h_current_star=h_cur, W_now=p.W0)


def _first_finite_w_star(sol, p: Params, state: Optional[int]) -> float:
    """W* at the earliest age where stopping is actually on the table.

    During the crunch lockout no seat change is permitted, so ``retired`` cannot
    be top-ranked and W* is legitimately undefined. Reporting +inf there would be
    correct but useless, so the boundary is quoted from the first age at which
    the decision exists.
    """
    for k in range(0, sol.pol_rank.shape[0]):
        v = w_star_v3(sol, p.age0 + k, p.h0, state)
        if np.isfinite(v):
            return v
    return float("inf")


def inaction_band_v3(sol_frictional, sol_frictionless, state: int, age: float) -> Dict[str, float]:
    """Share of the (W, h) grid where friction changes the seat decision.

    The band is where the frictionless policy would move but the frictional one
    stays put -- the real-options region, and the formal explanation for staying
    in a suboptimal seat.
    """
    ti = int(np.clip(round(age - sol_frictional.params.age0), 0,
                     sol_frictional.pol_rank.shape[0] - 1))
    cur = sol_frictional.space.states[state].seat
    a_cur = sol_frictional.actions.index(cur) if cur in sol_frictional.actions else -1
    stay = sol_frictional.pol_rank[ti, state, :, :, 0] == a_cur
    free_moves = sol_frictionless.pol_rank[ti, state, :, :, 0] != a_cur
    band = stay & free_moves
    return dict(frac_stay=float(stay.mean()),
                frac_frictionless_moves=float(free_moves.mean()),
                frac_inaction_band=float(band.mean()),
                band_mask=band)


# --------------------------------------------------------------------------- #
# The freedom number: what wealth actually funds this life                     #
# --------------------------------------------------------------------------- #

@dataclass
class FundedWealth:
    """Wealth at which spending is funded for life with a given confidence.

    This is a *sustainability* question -- can this pile of money pay for this
    life? -- and it is emphatically **not** the same question as W*, which asks
    what wealth would make the model *choose* to stop earning forever. The two
    are routinely conflated and they differ by more than 2x here.
    """
    W: float
    success: float
    equity_share: float
    to_age: Optional[float]
    annual_spend_now: float
    annual_spend_later: float
    withdrawal_rate: float
    mortality_weighted: bool


def _funded_paths(params: Params, W0: float, pi: float, shocks: np.ndarray,
                  mort: np.ndarray, mortality_weighted: bool,
                  to_age: Optional[float]) -> float:
    """Share of paths that never run out. Shocks are passed in so that common
    random numbers make the success rate monotone in W and the bisection clean."""
    sc = params.returns[params.scenario]
    n_t, n_p = shocks.shape
    W = np.full(n_p, float(W0))
    alive = np.ones(n_p, dtype=bool)
    ruined = np.zeros(n_p, dtype=bool)
    ages = params.ages
    drift = sc.rf_real + pi * sc.erp - 0.5 * pi ** 2 * sc.sigma ** 2
    for k in range(n_t):
        age = float(ages[k])
        if to_age is not None and age >= to_age:
            break
        m = params.mortgage.payment_at(age, params.age0) if params.mortgage_enabled else 0.0
        need = params.spend_base + m - social_security(age, params)
        W = np.where(alive & ~ruined, W - need, W)
        ruined |= alive & (W <= 0.0)
        W = np.where(alive & ~ruined, W * np.exp(drift + pi * sc.sigma * shocks[k]), W)
        if mortality_weighted:
            q = death_prob(age, np.full(n_p, 0.85), params)
            alive &= mort[k] >= q
    return 1.0 - float(ruined.mean())


def funded_wealth(params: Params, success: float = 0.95, equity_share: float = 0.6,
                  paths: int = 12_000, seed: int = 202, to_age: Optional[float] = None,
                  mortality_weighted: bool = True,
                  bounds: Tuple[float, float] = (5e5, 2.5e7)) -> FundedWealth:
    """Smallest wealth that funds ``spend_base`` for life with probability ``success``.

    Spending is the configured real budget plus mortgage service while it lasts,
    less Social Security once it starts. No labour income: this asks what the
    portfolio alone can carry.
    """
    rng = np.random.default_rng(seed)
    n_t = params.ages.size - 1
    shocks = rng.standard_normal((n_t, paths))
    mort = rng.random((n_t, paths))

    lo, hi = bounds
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        if _funded_paths(params, mid, equity_share, shocks, mort,
                         mortality_weighted, to_age) < success:
            lo = mid
        else:
            hi = mid
    W = 0.5 * (lo + hi)
    full = params.annual_full_expenses
    return FundedWealth(W=W, success=success, equity_share=equity_share, to_age=to_age,
                        annual_spend_now=full, annual_spend_later=params.spend_base,
                        withdrawal_rate=full / W if W else float("nan"),
                        mortality_weighted=mortality_weighted)


def funded_wealth_table(params: Params, shares: Sequence[float] = (0.4, 0.6, 0.8),
                        success: float = 0.95) -> Dict[str, List[FundedWealth]]:
    """The freedom number under both readings of 'for life'."""
    return {
        "for life (mortality-weighted)":
            [funded_wealth(params, success, s) for s in shares],
        "to age 100 regardless":
            [funded_wealth(params, success, s, to_age=None, mortality_weighted=False)
             for s in shares],
    }


def survival_at(params: Params, W: float, equity_share: float = 0.6,
                paths: int = 12_000, seed: int = 202,
                mortality_weighted: bool = True) -> float:
    rng = np.random.default_rng(seed)
    n_t = params.ages.size - 1
    return _funded_paths(params, W, equity_share,
                         rng.standard_normal((n_t, paths)), rng.random((n_t, paths)),
                         mortality_weighted, None)

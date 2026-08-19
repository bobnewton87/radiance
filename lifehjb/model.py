"""LifeHJB v2 -- model primitives.

Dynamics, felicity, mortality hazard, taxes, mortgage, returns and seat
definitions for the personal lifecycle HJB console.

All money is in **real (inflation-adjusted) 2026 dollars**.

This is a decision-support model. It is not financial or medical advice.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Dict, Iterable, List, Optional, Sequence

import math
import numpy as np
import yaml

# The Gompertz-Makeham hazard in the spec is anchored at chronological age 39.
AGE_ANCHOR = 39.0

# Floor used inside the bequest function, per spec: Bq(W) = w*(b + ln max(W, 50_000)).
BEQUEST_FLOOR = 50_000.0


# --------------------------------------------------------------------------- #
# Taxes                                                                        #
# --------------------------------------------------------------------------- #

# 2026 federal brackets, married filing jointly. (upper_edge, marginal_rate)
FED_MFJ_2026: List[tuple] = [
    (24_800.0, 0.10),
    (100_800.0, 0.12),
    (211_100.0, 0.22),
    (402_800.0, 0.24),
    (511_300.0, 0.32),
    (767_000.0, 0.35),
    (math.inf, 0.37),
]

STANDARD_DEDUCTION_MFJ = 30_000.0

SS_WAGE_BASE = 184_000.0        # Social Security taxable wage base, 2026
SS_RATE = 0.062
MEDICARE_RATE = 0.0145
ADDL_MEDICARE_RATE = 0.009
ADDL_MEDICARE_THRESHOLD = 250_000.0   # MFJ


def federal_tax(taxable: float) -> float:
    """Piecewise-linear 2026 MFJ federal income tax on *taxable* income."""
    taxable = max(float(taxable), 0.0)
    tax = 0.0
    lower = 0.0
    for upper, rate in FED_MFJ_2026:
        if taxable <= lower:
            break
        span = min(taxable, upper) - lower
        tax += span * rate
        lower = upper
    return tax


def fica_tax(gross_wages: float) -> float:
    """Employee-side FICA: OASDI to the wage base, Medicare, Additional Medicare."""
    g = max(float(gross_wages), 0.0)
    ss = SS_RATE * min(g, SS_WAGE_BASE)
    medicare = MEDICARE_RATE * g
    addl = ADDL_MEDICARE_RATE * max(g - ADDL_MEDICARE_THRESHOLD, 0.0)
    return ss + medicare + addl


def total_tax(gross_wages: float, standard_deduction: float = STANDARD_DEDUCTION_MFJ) -> float:
    """Total federal + FICA tax. Texas domicile => no state income tax."""
    g = max(float(gross_wages), 0.0)
    taxable = max(g - standard_deduction, 0.0)
    return federal_tax(taxable) + fica_tax(g)


def net_income(gross_wages: float, standard_deduction: float = STANDARD_DEDUCTION_MFJ) -> float:
    """After-tax wage income."""
    g = max(float(gross_wages), 0.0)
    return g - total_tax(g, standard_deduction)


def effective_tax_rate(gross_wages: float) -> float:
    g = max(float(gross_wages), 0.0)
    return 0.0 if g <= 0.0 else total_tax(g) / g


def gross_for_net(target_net: float, standard_deduction: float = STANDARD_DEDUCTION_MFJ) -> float:
    """Invert :func:`net_income` by bisection: the gross wage delivering *target_net*."""
    target = float(target_net)
    if target <= 0.0:
        return 0.0
    lo, hi = 0.0, max(4.0 * target, 1.0e5)
    while net_income(hi, standard_deduction) < target:
        hi *= 2.0
        if hi > 1e12:
            break
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if net_income(mid, standard_deduction) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# --------------------------------------------------------------------------- #
# Mortgage                                                                     #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Mortgage:
    balance: float = 126_000.0
    rate_nominal: float = 0.03625
    years: int = 7
    inflation: float = 0.025

    @property
    def rate_real(self) -> float:
        """Fisher-exact real rate: (1+i)/(1+pi) - 1."""
        return (1.0 + self.rate_nominal) / (1.0 + self.inflation) - 1.0

    @property
    def payment_real(self) -> float:
        """Level *real* annual payment amortizing the balance over ``years``."""
        if self.balance <= 0.0 or self.years <= 0:
            return 0.0
        r = self.rate_real
        n = int(self.years)
        if abs(r) < 1e-12:
            return self.balance / n
        return self.balance * r / (1.0 - (1.0 + r) ** (-n))

    def payment_at(self, age: float, age0: float) -> float:
        """Payment due at *age*; zero once amortization is complete."""
        k = age - age0
        return self.payment_real if 0.0 <= k < self.years else 0.0


# --------------------------------------------------------------------------- #
# Seats                                                                        #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Seat:
    """A job 'seat': what it pays, what it costs you, and how well you recover in it."""
    id: str
    y: float                 # gross income, real $/yr
    c_load: float            # cognitive load in [0, 1]
    travel: float            # fraction of nights away, [0, 1]
    autonomy: float          # control over your own calendar, [0, 1]
    r: float                 # recovery quality in [0, 1]
    phi: float               # direct seat disutility (utils/yr)
    absorbing: bool = False
    note: str = ""

    def with_travel(self, travel: float) -> "Seat":
        return replace(self, travel=float(travel))


DEFAULT_SEATS: List[Dict[str, Any]] = [
    dict(id="grind500", y=500_000, c_load=1.00, travel=0.25, autonomy=0.30, r=0.35,
         phi=0.30, note="more scope, more money"),
    dict(id="current350", y=350_000, c_load=0.85, travel=0.20, autonomy=0.35, r=0.45,
         phi=0.18, note="status quo"),
    dict(id="oldrole350", y=350_000, c_load=0.30, travel=0.55, autonomy=0.55, r=0.40,
         phi=0.12, note="mastered role, heavy travel"),
    dict(id="amat400", y=400_000, c_load=0.60, travel=0.25, autonomy=0.60, r=0.62,
         phi=0.10, note="outside role, correctly leveled"),
    dict(id="renegotiated350", y=350_000, c_load=0.50, travel=0.15, autonomy=0.65, r=0.70,
         phi=0.08, note="same pay, scope relief"),
    dict(id="downshift250", y=250_000, c_load=0.35, travel=0.10, autonomy=0.75, r=0.80,
         phi=0.04, note="lower pay, low load"),
    dict(id="retired", y=0, c_load=0.05, travel=0.02, autonomy=0.95, r=0.92,
         phi=0.00, absorbing=True, note="absorbing"),
]


# --------------------------------------------------------------------------- #
# Parameter blocks                                                             #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class HealthParams:
    delta0: float = 0.02
    delta_cognitive: float = 0.08
    delta_travel: float = 0.10
    delta_autonomy: float = 0.04
    rho_h: float = 0.6
    h_min: float = 0.35
    h_max_decay: float = 0.004


@dataclass(frozen=True)
class ReturnScenario:
    rf_real: float
    erp: float
    sigma: float

    @property
    def geometric_real_full_equity(self) -> float:
        """Geometric real return of a 100% risky portfolio: rf + erp - sigma^2/2."""
        return self.rf_real + self.erp - 0.5 * self.sigma ** 2


@dataclass(frozen=True)
class Numerics:
    n_W: int = 60
    W_min: float = 50_000.0
    W_max: float = 30_000_000.0
    n_h: int = 14
    n_c: int = 30
    c_frac_min: float = 0.01
    c_frac_max: float = 0.95
    # Absolute subsistence floor on the consumption grid, real $/yr. The grid is
    # log-spaced in c/resources, but a fixed fraction of a small W is an
    # economically meaningless consumption level; flooring it keeps every grid
    # node interpretable and is what makes the felicity condition
    # (b + ln c > 0) satisfiable jointly with the VSL calibration. See README.
    c_floor: float = 15_000.0
    n_pi: int = 6
    pi_max: float = 1.0
    n_gh: int = 7
    age_max: float = 100.0

    @property
    def pi_grid(self) -> np.ndarray:
        return np.linspace(0.0, self.pi_max, self.n_pi)


@dataclass(frozen=True)
class QuadratureSpec:
    """How the return expectation is integrated.

    ``gauss_hermite`` is the v2 rule. It is excellent for smooth integrands and
    **useless** for the v3 downturn indicator: the separation multiplier is a step
    function of the realized return, and whether a Hermite node happens to land
    past the threshold is an accident of node placement. At the base scenario and
    pi = 1 the true P(R' < 0.85) is 0.1037, and Gauss-Hermite reports 0.031 at 7
    nodes, 0.108 at 15, 0.150 at 21 and 0.056 at 25 -- it does not converge.

    ``split`` breaks the domain at the threshold and runs composite
    Gauss-Legendre against the normal density on each side. The mass either side
    is then exact by construction, and 4 panels x 8 nodes reproduces E[z], E[z^2]
    and E[e^(sigma z)] to machine precision.
    """
    kind: str = "split"          # "split" | "gauss_hermite"
    panels: int = 4
    m: int = 8
    z_max: float = 8.5
    n_gh: int = 7


@dataclass(frozen=True)
class HumanCapitalParams:
    """Human capital is an equity-like claim, not a bond. v2 assumed beta_H = 0."""
    beta_H: float = 1.6
    portfolio_sector_overlap: float = 0.35
    gammas_reported: tuple = (1.0, 1.5, 2.0, 3.0)
    T_work_cap: float = 65.0
    diversifying_sleeve: float = 0.0      # share of W genuinely orthogonal to H


@dataclass(frozen=True)
class CareerParams:
    """Involuntary separation, and what it costs."""
    base_sep: Dict[str, float] = field(default_factory=dict)
    amat_seasoning_years: int = 2
    amat_sep_after: float = 0.05
    downturn_threshold: float = -0.15
    downturn_factor: float = 3.0
    severance_months: float = 4.0
    search_duration_dist: Dict[int, float] = field(default_factory=dict)   # months -> prob
    reentry_haircut: float = 0.10
    searching_seat: Dict[str, float] = field(default_factory=dict)

    def sep_rate(self, seat_id: str, tenure: int = 99) -> float:
        if seat_id == "amat400":
            base = self.base_sep.get("amat400", 0.10)
            return base if tenure < self.amat_seasoning_years else self.amat_sep_after
        return float(self.base_sep.get(seat_id, 0.0))

    @property
    def enabled(self) -> bool:
        return any(v > 0 for v in self.base_sep.values())


@dataclass(frozen=True)
class AvailabilityParams:
    """Seats arrive; they are not on tap. This is what gives an option a price."""
    p_nego: float = 0.35
    # Negotiation success when the outside option is NOT maintained. A
    # negotiation without a credible alternative is a request, not a
    # negotiation -- and the v3 spec's own note that downshift250's permanent
    # availability "is what makes every other negotiation credible" points the
    # same way. Setting this equal to p_nego recovers the literal spec, under
    # which the two channels are pure substitutes and OV *falls* in p_nego.
    p_nego_unmaintained: float = 0.10
    nego_cooldown_years: int = 2
    p_outside: float = 0.40
    p_outside_unmaintained: float = 0.05
    phi_maintain: float = 0.02
    p_oldrole: float = 0.50
    p_grind: float = 1.0                 # not specified in v3; internal scope expansion
    maintain_outside_option: bool = True
    # Seats at the *current* employer. The v3 availability table ("current350:
    # always available (status quo)") is written from the perspective of an
    # employed agent -- the status quo is on offer because you are already in it.
    # After an involuntary separation it is not: you cannot walk back into the
    # job you were just let go from. These are therefore withdrawn from the
    # choice set while searching, which is what gives the outside option an
    # insurance value rather than a purely cosmetic one.
    same_employer: tuple = ("current350", "grind500", "renegotiated350")
    # Null value for v2 recovery: every seat on offer from every state, every year.
    unrestricted: bool = False

    def outside(self) -> float:
        return self.p_outside if self.maintain_outside_option else self.p_outside_unmaintained

    def nego(self) -> float:
        return self.p_nego if self.maintain_outside_option else self.p_nego_unmaintained

    @staticmethod
    def _effective(p: float, cooldown: float) -> float:
        return p / (1.0 + (1.0 - p) * float(cooldown))

    @property
    def p_nego_effective(self) -> float:
        """Long-run annual arrival rate once the cooldown is accounted for.

        The one-shot-plus-cooldown renewal process has mean time between
        attempts ``1 + (1-p)*cooldown``, so folding it into a constant annual
        arrival rate costs one state dimension and preserves the long-run rate.
        """
        return self._effective(self.nego(), self.nego_cooldown_years)


@dataclass(frozen=True)
class CrunchParams:
    """A real execution commitment the solver must not be allowed to wish away."""
    periods: int = 1
    multiplier: float = 1.30


@dataclass(frozen=True)
class StressTest:
    drawdown: float = -0.35
    ages: tuple = (42, 46, 50)


@dataclass(frozen=True)
class Params:
    age0: float = 39.0
    W0: float = 1_850_000.0
    h0: float = 0.72
    spend_base: float = 150_000.0
    mortgage: Mortgage = field(default_factory=Mortgage)

    rho: float = 0.02
    omega_bequest: float = 2.0
    vsl_target: float = 22_000_000.0
    vsl_band: tuple = (15_000_000.0, 30_000_000.0)

    health: HealthParams = field(default_factory=HealthParams)
    mortality_health_coupled: bool = True
    mortality_h_ref: float = 0.85
    mortality_kappa: float = 1.0
    mortality_scale: float = 1.0

    returns: Dict[str, ReturnScenario] = field(default_factory=dict)
    scenario: str = "base"

    ss_enabled: bool = True
    ss_amount: float = 40_000.0
    ss_age: float = 67.0

    switching_enabled: bool = False
    kappa_W: float = 40_000.0
    kappa_h: float = 0.02

    runway_years: float = 3.0
    coast_target_ages: tuple = (49, 52, 55, 57, 60)

    mc_paths: int = 10_000
    mc_seed: int = 42

    seats: tuple = ()
    numerics: Numerics = field(default_factory=Numerics)

    # -- v3 -------------------------------------------------------------------
    human_capital: HumanCapitalParams = field(default_factory=HumanCapitalParams)
    career: CareerParams = field(default_factory=CareerParams)
    availability: AvailabilityParams = field(default_factory=AvailabilityParams)
    crunch: CrunchParams = field(default_factory=CrunchParams)
    stress: StressTest = field(default_factory=StressTest)
    quadrature: QuadratureSpec = field(default_factory=QuadratureSpec)

    # Calibrated utility intercept. Filled in by calibrate.py; None until then.
    b: Optional[float] = None

    # Test/aux switches -------------------------------------------------------
    health_enabled: bool = True     # False collapses h to a single node at 1.0
    labor_enabled: bool = True      # False zeroes all wage income
    taxes_enabled: bool = True
    mortgage_enabled: bool = True
    mortality_enabled: bool = True

    # -- convenience ---------------------------------------------------------
    @property
    def ret(self) -> ReturnScenario:
        return self.returns[self.scenario]

    @property
    def seat_map(self) -> Dict[str, Seat]:
        return {s.id: s for s in self.seats}

    def seat(self, sid: str) -> Seat:
        return self.seat_map[sid]

    @property
    def ages(self) -> np.ndarray:
        return np.arange(self.age0, self.numerics.age_max + 1.0, 1.0)

    @property
    def annual_full_expenses(self) -> float:
        """Spending plus mortgage service, i.e. what a walk-away year actually costs."""
        return self.spend_base + (self.mortgage.payment_real if self.mortgage_enabled else 0.0)

    def evolve(self, **kw) -> "Params":
        return replace(self, **kw)


# --------------------------------------------------------------------------- #
# Config loading                                                               #
# --------------------------------------------------------------------------- #

def _seats_from_cfg(raw: Optional[Iterable[Dict[str, Any]]]) -> tuple:
    rows = list(raw) if raw else DEFAULT_SEATS
    return tuple(Seat(**dict(r)) for r in rows)


def load_params(path: str) -> Params:
    with open(path, "r") as fh:
        cfg = yaml.safe_load(fh) or {}
    return params_from_dict(cfg)


def params_from_dict(cfg: Dict[str, Any]) -> Params:
    mtg = cfg.get("mortgage", {}) or {}
    hlt = cfg.get("health", {}) or {}
    ss = cfg.get("ss", {}) or {}
    sw = cfg.get("switching_costs", {}) or {}
    bnd = cfg.get("boundaries", {}) or {}
    mc = cfg.get("mc", {}) or {}
    num = cfg.get("numerics", {}) or {}
    rets = cfg.get("returns", {}) or {}
    hcap = cfg.get("human_capital", {}) or {}
    car = cfg.get("career", {}) or {}
    avail = cfg.get("availability", {}) or {}
    crun = cfg.get("crunch", {}) or {}
    stres = cfg.get("stress_test", {}) or {}
    quad = cfg.get("quadrature", {}) or {}

    scenarios = {k: ReturnScenario(**v) for k, v in rets.items()}
    if not scenarios:
        scenarios = {
            "base": ReturnScenario(0.020, 0.032, 0.16),
            "bear": ReturnScenario(0.015, 0.015, 0.18),
            "bull": ReturnScenario(0.020, 0.055, 0.16),
        }

    band = cfg.get("vsl_band", [15_000_000.0, 30_000_000.0])

    return Params(
        age0=float(cfg.get("age0", 39.0)),
        W0=float(cfg.get("W0", 1_850_000.0)),
        h0=float(cfg.get("h0", 0.72)),
        spend_base=float(cfg.get("spend_base", 150_000.0)),
        mortgage=Mortgage(
            balance=float(mtg.get("balance", 126_000.0)),
            rate_nominal=float(mtg.get("rate_nominal", 0.03625)),
            years=int(mtg.get("years", 7)),
            inflation=float(mtg.get("inflation", 0.025)),
        ),
        rho=float(cfg.get("rho", 0.02)),
        omega_bequest=float(cfg.get("omega_bequest", 2.0)),
        vsl_target=float(cfg.get("vsl_target", 22_000_000.0)),
        vsl_band=(float(band[0]), float(band[1])),
        health=HealthParams(
            delta0=float(hlt.get("delta0", 0.02)),
            delta_cognitive=float(hlt.get("delta_cognitive", 0.08)),
            delta_travel=float(hlt.get("delta_travel", 0.10)),
            delta_autonomy=float(hlt.get("delta_autonomy", 0.04)),
            rho_h=float(hlt.get("rho_h", 0.6)),
            h_min=float(hlt.get("h_min", 0.35)),
            h_max_decay=float(hlt.get("h_max_decay", 0.004)),
        ),
        mortality_health_coupled=bool(cfg.get("mortality_health_coupled", True)),
        mortality_h_ref=float(cfg.get("mortality_h_ref", 0.85)),
        mortality_kappa=float(cfg.get("mortality_kappa", 1.0)),
        returns=scenarios,
        scenario=str(cfg.get("scenario", "base")),
        ss_enabled=bool(ss.get("enabled", True)),
        ss_amount=float(ss.get("amount", 40_000.0)),
        ss_age=float(ss.get("age", 67.0)),
        switching_enabled=bool(sw.get("enabled", True)),
        kappa_W=float(sw.get("kappa_W", 40_000.0)),
        kappa_h=float(sw.get("kappa_h", 0.02)),
        runway_years=float(bnd.get("runway_years", 3.0)),
        coast_target_ages=tuple(int(a) for a in bnd.get("coast_target_ages", [49, 52, 55, 57, 60])),
        mc_paths=int(mc.get("paths", 10_000)),
        mc_seed=int(mc.get("seed", 42)),
        seats=_seats_from_cfg(cfg.get("seats")),
        numerics=Numerics(
            n_W=int(num.get("n_W", 60)),
            W_min=float(num.get("W_min", 50_000.0)),
            W_max=float(num.get("W_max", 30_000_000.0)),
            n_h=int(num.get("n_h", 14)),
            n_c=int(num.get("n_c", 30)),
            c_frac_min=float(num.get("c_frac_min", 0.01)),
            c_frac_max=float(num.get("c_frac_max", 0.95)),
            c_floor=float(num.get("c_floor", 15_000.0)),
            n_pi=int(num.get("n_pi", 6)),
            pi_max=float(num.get("pi_max", 1.0)),
            n_gh=int(num.get("n_gh", 7)),
            age_max=float(num.get("age_max", 100.0)),
        ),
        b=(float(cfg["b"]) if cfg.get("b") is not None else None),
        human_capital=HumanCapitalParams(
            beta_H=float(hcap.get("beta_H", 1.6)),
            portfolio_sector_overlap=float(hcap.get("portfolio_sector_overlap", 0.35)),
            gammas_reported=tuple(float(g) for g in
                                  hcap.get("gammas_reported", [1.0, 1.5, 2.0, 3.0])),
            T_work_cap=float(hcap.get("T_work_cap", 65.0)),
            diversifying_sleeve=float(hcap.get("diversifying_sleeve", 0.0)),
        ),
        career=CareerParams(
            base_sep={str(k): float(v) for k, v in (car.get("base_sep") or {}).items()},
            amat_seasoning_years=int(car.get("amat_seasoning_years", 2)),
            amat_sep_after=float(car.get("amat_sep_after", 0.05)),
            downturn_threshold=float(car.get("downturn_threshold", -0.15)),
            downturn_factor=float(car.get("downturn_factor", 3.0)),
            severance_months=float(car.get("severance_months", 4.0)),
            search_duration_dist={int(k): float(v) for k, v in
                                  (car.get("search_duration_dist")
                                   or {3: 0.30, 6: 0.45, 9: 0.15, 12: 0.10}).items()},
            reentry_haircut=float(car.get("reentry_haircut", 0.10)),
            searching_seat={str(k): float(v) for k, v in
                            (car.get("searching_seat") or {}).items()},
        ),
        availability=AvailabilityParams(
            p_nego=float(avail.get("p_nego", 0.35)),
            p_nego_unmaintained=float(avail.get("p_nego_unmaintained", 0.10)),
            nego_cooldown_years=int(avail.get("nego_cooldown_years", 2)),
            p_outside=float(avail.get("p_outside", 0.40)),
            p_outside_unmaintained=float(avail.get("p_outside_unmaintained", 0.05)),
            phi_maintain=float(avail.get("phi_maintain", 0.02)),
            p_oldrole=float(avail.get("p_oldrole", 0.50)),
            p_grind=float(avail.get("p_grind", 1.0)),
            maintain_outside_option=bool(avail.get("maintain_outside_option", True)),
            same_employer=tuple(avail.get("same_employer",
                                          ["current350", "grind500", "renegotiated350"])),
            unrestricted=bool(avail.get("unrestricted", False)),
        ),
        crunch=CrunchParams(
            periods=int(crun.get("periods", 1)),
            multiplier=float(crun.get("multiplier", 1.30)),
        ),
        stress=StressTest(
            drawdown=float(stres.get("drawdown", -0.35)),
            ages=tuple(int(a) for a in stres.get("ages", [42, 46, 50])),
        ),
        quadrature=QuadratureSpec(
            kind=str(quad.get("kind", "split")),
            panels=int(quad.get("panels", 4)),
            m=int(quad.get("m", 8)),
            z_max=float(quad.get("z_max", 8.5)),
            n_gh=int(num.get("n_gh", quad.get("n_gh", 7))),
        ),
    )


# --------------------------------------------------------------------------- #
# Mortality                                                                    #
# --------------------------------------------------------------------------- #

def hazard(age, params: Params) -> np.ndarray:
    """Gompertz-Makeham force of mortality, lambda(t)."""
    a = np.asarray(age, dtype=float)
    lam = 2e-4 + 1e-3 * np.power(2.0, (a - AGE_ANCHOR) / 8.0)
    return lam * params.mortality_scale


def hazard_health(age, h, params: Params) -> np.ndarray:
    """Health-coupled hazard: lambda_eff = lambda(t) * (h_ref/h)**kappa."""
    lam = hazard(age, params)
    if not params.mortality_health_coupled:
        return np.broadcast_to(np.atleast_1d(lam), np.shape(np.asarray(h))) * np.ones_like(np.asarray(h, float))
    hh = np.asarray(h, dtype=float)
    return lam * np.power(params.mortality_h_ref / np.maximum(hh, 1e-6), params.mortality_kappa)


def death_prob(age, h, params: Params) -> np.ndarray:
    """q_t = 1 - exp(-lambda_eff)."""
    if not params.mortality_enabled:
        return np.zeros_like(np.asarray(h, dtype=float))
    lam = hazard_health(age, h, params)
    return 1.0 - np.exp(-lam)


# --------------------------------------------------------------------------- #
# Returns                                                                      #
# --------------------------------------------------------------------------- #

def gauss_hermite(n: int):
    """Nodes/weights for E[f(Z)], Z ~ N(0,1)."""
    x, w = np.polynomial.hermite.hermgauss(n)
    return np.sqrt(2.0) * x, w / np.sqrt(np.pi)


def return_quadrature(pi: np.ndarray, sc: ReturnScenario, spec: QuadratureSpec,
                      downturn_threshold: float):
    """Nodes, weights and the downturn mask for the return expectation.

    Returns ``(lnR, w, down)``, each shaped ``(n_pi, n_k)``. Weights sum to 1
    along the node axis for every pi. ``down`` marks the nodes where
    ``R' < 1 + downturn_threshold`` -- the states in which the separation hazard
    is multiplied up.

    Under ``kind="split"`` the domain is broken exactly at the threshold, so
    ``w[down].sum()`` equals the true P(R' < 1 + threshold) to machine precision
    rather than to wherever the nodes happened to fall.
    """
    from scipy.stats import norm

    pi = np.asarray(pi, dtype=float)
    mu = sc.rf_real + pi * sc.erp - 0.5 * pi ** 2 * sc.sigma ** 2
    sd = pi * sc.sigma
    ln_thr = np.log(1.0 + downturn_threshold)

    if spec.kind == "gauss_hermite":
        z, wk = gauss_hermite(spec.n_gh)
        lnR = mu[:, None] + sd[:, None] * z[None, :]
        w = np.broadcast_to(wk[None, :], lnR.shape).copy()
        return lnR, w, lnR < ln_thr

    if spec.kind != "split":
        raise ValueError(f"unknown quadrature kind {spec.kind!r}")

    x, gl = np.polynomial.legendre.leggauss(spec.m)
    n_k = 2 * spec.panels * spec.m
    lnR = np.empty((pi.size, n_k))
    w = np.zeros((pi.size, n_k))

    for i in range(pi.size):
        if sd[i] <= 0.0:
            # Degenerate: a single certain return. Pad the rest with zero weight.
            lnR[i, :] = mu[i]
            w[i, 0] = 1.0
            continue
        z_star = float(np.clip((ln_thr - mu[i]) / sd[i], -spec.z_max, spec.z_max))
        zs, ws = [], []
        for lo, hi in ((-spec.z_max, z_star), (z_star, spec.z_max)):
            edges = np.linspace(lo, hi, spec.panels + 1)
            for a, bnd in zip(edges[:-1], edges[1:]):
                half = 0.5 * (bnd - a)
                zz = half * x + 0.5 * (a + bnd)
                zs.append(zz)
                ws.append(half * gl * norm.pdf(zz))
        zz = np.concatenate(zs)
        ww = np.concatenate(ws)
        ww = ww / ww.sum()
        lnR[i] = mu[i] + sd[i] * zz
        w[i] = ww

    return lnR, w, lnR < ln_thr


def log_return_grid(pi: np.ndarray, sc: ReturnScenario, n_gh: int) -> np.ndarray:
    """ln R for each (pi, quadrature node).

    ln R ~ Normal(rf + pi*erp - 0.5*pi^2*sigma^2, pi^2*sigma^2)
    """
    z, _ = gauss_hermite(n_gh)
    pi = np.asarray(pi, dtype=float)
    mu = sc.rf_real + pi * sc.erp - 0.5 * pi ** 2 * sc.sigma ** 2
    sd = pi * sc.sigma
    return mu[:, None] + sd[:, None] * z[None, :]


# --------------------------------------------------------------------------- #
# Income & felicity                                                            #
# --------------------------------------------------------------------------- #

def seat_net_income(seat: Seat, params: Params) -> float:
    if not params.labor_enabled:
        return 0.0
    if not params.taxes_enabled:
        return float(seat.y)
    return net_income(seat.y)


def social_security(age: float, params: Params) -> float:
    if not params.ss_enabled:
        return 0.0
    return params.ss_amount if age >= params.ss_age else 0.0


def felicity(c, h, seat: Seat, b: float) -> np.ndarray:
    """u(c, h, e) = h*(b + ln c) - phi(e)."""
    return np.asarray(h) * (b + np.log(np.asarray(c))) - seat.phi


def bequest(W, params: Params, b: float) -> np.ndarray:
    return params.omega_bequest * (b + np.log(np.maximum(np.asarray(W, float), BEQUEST_FLOOR)))


# --------------------------------------------------------------------------- #
# Balance provider (stub; an IBKR adapter drops in behind this interface)      #
# --------------------------------------------------------------------------- #

class BalanceProvider:
    """Interface for sourcing the liquid balance W0."""

    def liquid_balance(self) -> float:  # pragma: no cover - interface
        raise NotImplementedError


class YamlBalanceProvider(BalanceProvider):
    """Reads W0 straight out of config.yaml. The default provider."""

    def __init__(self, params: Params):
        self._params = params

    def liquid_balance(self) -> float:
        return float(self._params.W0)

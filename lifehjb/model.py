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
        switching_enabled=bool(sw.get("enabled", False)),
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

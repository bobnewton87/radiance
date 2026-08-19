"""Calibration: rho from the savings history, b from a VSL target.

Two parameters are not assumed but *backed out* of observables:

* ``rho`` -- pure time preference, from the realized 2010 -> 2026 savings path.
* ``b``   -- the felicity intercept, from a target value of statistical life,
  VSL = V / V_W evaluated at the subject's current state.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Tuple

import numpy as np

from .model import Params, net_income
from .solver import (Solution, build_grids, felicity_check, shadow_prices, solve,
                     subsistence_consumption)

# --------------------------------------------------------------------------- #
# rho from savings history                                                     #
# --------------------------------------------------------------------------- #

HISTORY = dict(
    year0=2010, W0=25_000.0, gross0=90_000.0,
    year1=2026, W1=1_850_000.0, gross1=350_000.0,
    nominal_return=0.10, inflation=0.025,
)


@dataclass
class SavingsFit:
    savings_rate: float
    years: int
    real_return: float
    gross_growth_real: float
    W_start_real: float
    W_end_real: float
    W_end_model: float
    rho_band: Tuple[float, float]
    rho_default: float

    @property
    def note(self) -> str:
        return ("Everything is expressed in real 2026 dollars, so the 2026 tax "
                "function is applied to 2026-dollar incomes rather than to "
                "nominal historical ones.")


def _terminal_wealth(savings_rate: float, gross_real: np.ndarray, W0: float,
                     r_real: float) -> float:
    W = W0
    for g in gross_real:
        W = (W + savings_rate * net_income(float(g))) * (1.0 + r_real)
    return W


def calibrate_rho(hist: Optional[Dict] = None) -> SavingsFit:
    """Back out the constant savings-rate-out-of-net that reproduces W_2026.

    Assumptions (all stated in the report's provenance table): gross income grew
    geometrically between the endpoints; the realized portfolio returned 10%
    nominal against 2.5% inflation; taxes are the 2026 MFJ schedule.
    """
    h = dict(HISTORY)
    if hist:
        h.update(hist)
    n = int(h["year1"] - h["year0"])
    infl = float(h["inflation"])
    r_real = (1.0 + float(h["nominal_return"])) / (1.0 + infl) - 1.0

    # Deflate the 2010 endpoints into 2026 dollars.
    W_start_real = float(h["W0"]) * (1.0 + infl) ** n
    gross_start_real = float(h["gross0"]) * (1.0 + infl) ** n
    gross_end_real = float(h["gross1"])
    g_growth = (gross_end_real / gross_start_real) ** (1.0 / n) - 1.0
    gross_real = gross_start_real * (1.0 + g_growth) ** np.arange(n)

    lo, hi = 0.0, 1.0
    target = float(h["W1"])
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if _terminal_wealth(mid, gross_real, W_start_real, r_real) < target:
            lo = mid
        else:
            hi = mid
    s = 0.5 * (lo + hi)

    if s >= 0.30:
        band = (0.015, 0.025)
    elif s >= 0.20:
        band = (0.025, 0.035)
    else:
        band = (0.035, 0.050)

    return SavingsFit(
        savings_rate=s, years=n, real_return=r_real, gross_growth_real=g_growth,
        W_start_real=W_start_real, W_end_real=target,
        W_end_model=_terminal_wealth(s, gross_real, W_start_real, r_real),
        rho_band=band, rho_default=0.02,
    )


# --------------------------------------------------------------------------- #
# b from a VSL target                                                          #
# --------------------------------------------------------------------------- #

COARSE = dict(n_W=36, n_h=8, n_c=20, n_pi=4)


@dataclass
class VSLFit:
    b: float
    vsl_target: float
    vsl_achieved: float
    Lambda_h: float
    V: float
    V_W: float
    V_h: float
    c_sub: float
    admissible: bool
    iterations: int
    scenario: str

    @property
    def rel_error(self) -> float:
        return abs(self.vsl_achieved / self.vsl_target - 1.0)


def _coarse(params: Params) -> Params:
    return params.evolve(numerics=replace(params.numerics, **COARSE))


def _vsl_of_b(params: Params, b: float, scenario: str) -> Dict[str, float]:
    sol = solve(params, scenario=scenario, b=b, check_felicity=False)
    return shadow_prices(sol, params.W0, params.h0, params.age0)


def calibrate_b(params: Params, vsl_target: Optional[float] = None,
                scenario: Optional[str] = None, tol: float = 0.005,
                max_iter: int = 12, verbose: bool = False) -> VSLFit:
    """Solve VSL(b) = vsl_target.

    VSL = V/V_W is increasing in b (b shifts V roughly linearly while leaving
    V_W nearly alone), so a coarse-grid bisection brackets the root cheaply and a
    secant refinement on the production grid lands it inside ``tol``.
    """
    target = float(params.vsl_target if vsl_target is None else vsl_target)
    scen = scenario or params.scenario

    # --- stage 1: bracket on a coarse grid ------------------------------- #
    cp = _coarse(params)
    lo, hi = -20.0, 5.0
    f_lo = _vsl_of_b(cp, lo, scen)["VSL"] - target
    f_hi = _vsl_of_b(cp, hi, scen)["VSL"] - target
    if f_lo > 0 or f_hi < 0:
        raise ValueError(
            f"VSL target {target:,.0f} is not bracketed by b in [{lo}, {hi}] "
            f"(VSL spans {f_lo + target:,.0f} .. {f_hi + target:,.0f})."
        )
    for _ in range(22):
        mid = 0.5 * (lo + hi)
        if _vsl_of_b(cp, mid, scen)["VSL"] - target < 0:
            lo = mid
        else:
            hi = mid
    b_coarse = 0.5 * (lo + hi)

    # --- stage 2: secant refinement on the production grid --------------- #
    b0, b1 = b_coarse - 0.25, b_coarse + 0.25
    sp0 = _vsl_of_b(params, b0, scen)
    sp1 = _vsl_of_b(params, b1, scen)
    f0, f1 = sp0["VSL"] - target, sp1["VSL"] - target
    it = 2
    best_b, best_sp = (b1, sp1) if abs(f1) < abs(f0) else (b0, sp0)
    while it < max_iter and abs(best_sp["VSL"] / target - 1.0) > tol:
        denom = (f1 - f0)
        if abs(denom) < 1e-12:
            break
        b2 = b1 - f1 * (b1 - b0) / denom
        b2 = float(np.clip(b2, -25.0, 10.0))
        sp2 = _vsl_of_b(params, b2, scen)
        f2 = sp2["VSL"] - target
        b0, f0, b1, f1 = b1, f1, b2, f2
        it += 1
        if abs(f2) < abs(best_sp["VSL"] - target):
            best_b, best_sp = b2, sp2
        if verbose:
            print(f"  iter {it}: b={b2:.4f} VSL={sp2['VSL']:,.0f}")

    chk = felicity_check(params, build_grids(params), best_b)
    return VSLFit(
        b=float(best_b), vsl_target=target, vsl_achieved=float(best_sp["VSL"]),
        Lambda_h=float(best_sp["Lambda_h"]), V=float(best_sp["V"]),
        V_W=float(best_sp["V_W"]), V_h=float(best_sp["V_h"]),
        c_sub=subsistence_consumption(best_b), admissible=bool(chk["ok"]),
        iterations=it, scenario=scen,
    )


def calibrate_b_sweep(params: Params, targets: Optional[List[float]] = None,
                      scenario: Optional[str] = None) -> Dict[float, VSLFit]:
    """Calibrate b at each VSL target in the sensitivity sweep."""
    tgts = targets or [params.vsl_band[0], params.vsl_target, params.vsl_band[1]]
    return {float(t): calibrate_b(params, vsl_target=float(t), scenario=scenario)
            for t in sorted(set(float(t) for t in tgts))}

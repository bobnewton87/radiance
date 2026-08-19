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
from .model import Params
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

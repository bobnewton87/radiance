"""Health capital dynamics -- the core of LifeHJB v2.

v1 treated health as monotone decay. v2 lets health *recover* toward a
slowly-declining ceiling, so every seat has a **steady state** h*(e) rather
than a decay slope, plus a time constant that says how fast you get there.

    delta_total(e) = d0 + d_c*c_load + d_t*travel + d_a*(1 - autonomy)
    recovery(e)    = rho_h * r(e)
    h_max(t)       = 1 - h_max_decay*(t - 39)
    h'             = h + recovery*(h_max(t) - h) - delta_total*h
    h'             = clip(h', h_min, h_max(t))

Fixed points of the (unclipped) map:

    h*(e) = recovery*h_max / (recovery + delta_total)
    tau(e) = 1 / (recovery + delta_total)          [years]
    half-life to h* = tau * ln 2

Note on travel: the spec's recovery term is rho_h*r(e) only, so travel enters
the *damage* channel explicitly. Travel's damage to the **recovery** channel is
carried by the seat's own r (recovery quality) -- which is why oldrole350
carries r = 0.40 despite having the second-lowest cognitive load in the roster.
"""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np

from .model import AGE_ANCHOR, HealthParams, Params, Seat


def delta_total(seat: Seat, hp: HealthParams) -> float:
    """Total annual health depreciation rate in seat *e*."""
    return (hp.delta0
            + hp.delta_cognitive * seat.c_load
            + hp.delta_travel * seat.travel
            + hp.delta_autonomy * (1.0 - seat.autonomy))


def recovery(seat: Seat, hp: HealthParams) -> float:
    """Annual pull-back-toward-ceiling rate in seat *e*."""
    return hp.rho_h * seat.r


def h_max(age, hp: HealthParams) -> np.ndarray:
    """Recoverable ceiling; declines slowly with chronological age."""
    return 1.0 - hp.h_max_decay * (np.asarray(age, dtype=float) - AGE_ANCHOR)


def h_star(seat: Seat, hp: HealthParams, ceiling: float = 1.0) -> float:
    """Steady-state health in seat *e* at a fixed ceiling."""
    rec = recovery(seat, hp)
    dep = delta_total(seat, hp)
    denom = rec + dep
    if denom <= 0.0:
        return ceiling
    return rec * ceiling / denom


def tau(seat: Seat, hp: HealthParams) -> float:
    """Time constant of convergence to h*, in years."""
    denom = recovery(seat, hp) + delta_total(seat, hp)
    return float("inf") if denom <= 0.0 else 1.0 / denom


def half_life(seat: Seat, hp: HealthParams) -> float:
    """Years to close half the gap to h*."""
    return tau(seat, hp) * np.log(2.0)


def step(h, seat: Seat, hp: HealthParams, ceiling: float = 1.0) -> np.ndarray:
    """One annual health transition, with clipping."""
    h = np.asarray(h, dtype=float)
    rec = recovery(seat, hp)
    dep = delta_total(seat, hp)
    nxt = h + rec * (ceiling - h) - dep * h
    return np.clip(nxt, hp.h_min, ceiling)


def trajectory(h0: float, seat: Seat, hp: HealthParams, years: int,
               age0: float = AGE_ANCHOR, age_varying_ceiling: bool = True) -> np.ndarray:
    """Deterministic h path of length ``years + 1`` starting at *h0*."""
    out = np.empty(years + 1, dtype=float)
    out[0] = h0
    h = float(h0)
    for k in range(years):
        ceil_k = float(h_max(age0 + k, hp)) if age_varying_ceiling else 1.0
        h = float(step(h, seat, hp, ceil_k))
        out[k + 1] = h
    return out


def seat_health_table(params: Params) -> Dict[str, Dict[str, float]]:
    """Per-seat depreciation, recovery, steady state and time constants."""
    hp = params.health
    rows: Dict[str, Dict[str, float]] = {}
    for s in params.seats:
        rows[s.id] = dict(
            delta_total=delta_total(s, hp),
            recovery=recovery(s, hp),
            h_star=h_star(s, hp),
            tau=tau(s, hp),
            half_life=half_life(s, hp),
        )
    return rows


def min_delta_total(params: Params) -> float:
    """Depreciation of the healthiest seat in the roster -- the Theta reference."""
    return min(delta_total(s, params.health) for s in params.seats)

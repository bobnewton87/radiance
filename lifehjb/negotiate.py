"""Negotiation module -- the headline outputs.

Converts the solved value function into the three numbers that actually settle
job decisions:

* the **maximum permanent pay cut** worth taking for a given health improvement
  (the indifference matrix, section 6.2);
* a **dollars-per-year seat score** Theta that puts income, health depreciation
  and direct disutility on one axis (section 6.3);
* the **break-even stress increase** for a proposed raise (section 6.4).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from . import health as H
from .model import Params, Seat, gross_for_net, net_income, seat_net_income
from .solver import Solution, shadow_prices


# --------------------------------------------------------------------------- #
# 6.1 per-seat table                                                           #
# --------------------------------------------------------------------------- #

@dataclass
class SeatRow:
    id: str
    y: float
    y_net: float
    delta_total: float
    recovery: float
    h_star: float
    tau: float
    half_life: float
    savings_capacity: float
    phi: float
    note: str


def seat_table(params: Params) -> List[SeatRow]:
    hp = params.health
    m = params.mortgage.payment_real if params.mortgage_enabled else 0.0
    rows = []
    for s in params.seats:
        yn = seat_net_income(s, params)
        rows.append(SeatRow(
            id=s.id, y=s.y, y_net=yn,
            delta_total=H.delta_total(s, hp), recovery=H.recovery(s, hp),
            h_star=H.h_star(s, hp), tau=H.tau(s, hp), half_life=H.half_life(s, hp),
            savings_capacity=yn - params.spend_base - m, phi=s.phi, note=s.note,
        ))
    return rows


# --------------------------------------------------------------------------- #
# 6.2 health-consumption indifference                                          #
# --------------------------------------------------------------------------- #

def indifferent_consumption(h_from: float, h_to: float, c_from: float, b: float) -> float:
    """Solve h1*(b + ln c1) = h2*(b + ln c2) for c2.

    With h2 > h1 this returns a *lower* c2: the consumption you could live on at
    the healthier seat and be exactly as well off. c_from - c2 is therefore the
    maximum permanent consumption cut the health gain is worth.
    """
    if h_to <= 0:
        return float("nan")
    return float(np.exp((h_from / h_to) * (b + np.log(c_from)) - b))


@dataclass
class IndifferenceCell:
    from_id: str
    to_id: str
    h_from: float
    h_to: float
    c_indiff: float
    c_cut: float                 # spend_base - c_indiff  (positive => can pay to move)
    gross_indiff: float
    gross_cut: float


def indifference_matrix(params: Params, b: float,
                        c_ref: Optional[float] = None) -> List[IndifferenceCell]:
    """Every ordered seat pair: what you could live on after the move."""
    c1 = float(params.spend_base if c_ref is None else c_ref)
    hp = params.health
    hs = {s.id: H.h_star(s, hp) for s in params.seats}
    gross_ref = gross_for_net(c1)
    out: List[IndifferenceCell] = []
    for a in params.seats:
        for z in params.seats:
            c2 = indifferent_consumption(hs[a.id], hs[z.id], c1, b)
            g2 = gross_for_net(c2) if np.isfinite(c2) and c2 > 0 else float("nan")
            out.append(IndifferenceCell(
                from_id=a.id, to_id=z.id, h_from=hs[a.id], h_to=hs[z.id],
                c_indiff=c2, c_cut=c1 - c2, gross_indiff=g2, gross_cut=gross_ref - g2,
            ))
    return out


# --------------------------------------------------------------------------- #
# 6.3 seat score in dollars per year                                           #
# --------------------------------------------------------------------------- #

@dataclass
class ThetaRow:
    id: str
    theta: float
    y_net: float
    health_cost: float
    disutility_cost: float
    delta_total: float
    h_star: float


def theta(params: Params, Lambda_h: float, V_W: float,
          delta_ref: Optional[float] = None,
          seats: Optional[Sequence[Seat]] = None) -> List[ThetaRow]:
    """Theta(e) = y_net(e) - (Lambda_h/0.01)*(delta_total(e) - delta_ref) - phi(e)/V_W.

    ``delta_ref`` defaults to the *baseline* roster's lowest depreciation, and is
    passed explicitly when scoring perturbed seats so that scores stay
    comparable across the perturbation (otherwise perturbing the healthiest seat
    silently moves the origin).
    """
    hp = params.health
    pool = list(seats) if seats is not None else list(params.seats)
    ref = float(H.min_delta_total(params) if delta_ref is None else delta_ref)
    rows: List[ThetaRow] = []
    for s in pool:
        d = H.delta_total(s, hp)
        health_cost = (Lambda_h / 0.01) * (d - ref)
        dis_cost = s.phi / V_W if V_W else float("inf")
        rows.append(ThetaRow(
            id=s.id, y_net=seat_net_income(s, params), health_cost=health_cost,
            disutility_cost=dis_cost, delta_total=d, h_star=H.h_star(s, hp),
            theta=seat_net_income(s, params) - health_cost - dis_cost,
        ))
    rows.sort(key=lambda r: -r.theta)
    return rows


def theta_from_solution(sol: Solution, params: Optional[Params] = None,
                        delta_ref: Optional[float] = None) -> List[ThetaRow]:
    p = params or sol.params
    sp = shadow_prices(sol, p.W0, p.h0, p.age0)
    return theta(p, sp["Lambda_h"], sp["V_W"], delta_ref=delta_ref)


def dominance(grid: Dict[Tuple[str, float], List[ThetaRow]]) -> Dict[str, List[str]]:
    """Pairwise dominance: which seats beat which in *every* cell of the grid.

    Rank stability is a weak test -- with Lambda_h moving 4x across the
    scenario x VSL grid almost every rank moves somewhere. Pairwise dominance is
    the statement that actually survives, and it is the one a negotiation can
    lean on.
    """
    scores: Dict[str, List[float]] = {}
    for rows in grid.values():
        for r in rows:
            scores.setdefault(r.id, []).append(r.theta)
    ids = sorted(scores)
    out: Dict[str, List[str]] = {}
    for a in ids:
        beaten = [z for z in ids
                  if z != a and all(x > y for x, y in zip(scores[a], scores[z]))]
        out[a] = beaten
    return out


def rank_stability(grid: Dict[Tuple[str, float], List[ThetaRow]]) -> Dict[str, Dict[str, object]]:
    """Where each seat ranks across the whole scenario x VSL grid."""
    ranks: Dict[str, List[int]] = {}
    for rows in grid.values():
        for i, r in enumerate(rows):
            ranks.setdefault(r.id, []).append(i + 1)
    return {sid: dict(min_rank=min(v), max_rank=max(v), stable=(min(v) == max(v)),
                      modal_rank=int(np.bincount(v).argmax()))
            for sid, v in sorted(ranks.items())}


# --------------------------------------------------------------------------- #
# 6.4 break-even depreciation for a proposed raise                             #
# --------------------------------------------------------------------------- #

@dataclass
class BreakEven:
    delta_y_gross: float
    delta_y_net: float
    delta_delta: float          # the delta_total increase that neutralizes it
    equiv_travel: float         # ... expressed as extra nights away
    equiv_c_load: float         # ... expressed as extra cognitive load


def break_even_delta(params: Params, Lambda_h: float, base_gross: float,
                     raises: Sequence[float]) -> List[BreakEven]:
    """For a raise of Delta_y, how much extra depreciation makes it a bad trade.

    Utility-neutral when the after-tax raise exactly buys back the health it
    costs: Delta_y_net = (Lambda_h/0.01) * Delta_delta.
    """
    hp = params.health
    base_net = net_income(base_gross)
    out = []
    for dy in raises:
        dnet = net_income(base_gross + dy) - base_net
        dd = dnet * 0.01 / Lambda_h if Lambda_h else float("inf")
        out.append(BreakEven(
            delta_y_gross=float(dy), delta_y_net=float(dnet), delta_delta=float(dd),
            equiv_travel=float(dd / hp.delta_travel) if hp.delta_travel else float("nan"),
            equiv_c_load=float(dd / hp.delta_cognitive) if hp.delta_cognitive else float("nan"),
        ))
    return out

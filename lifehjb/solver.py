"""Backward-induction Bellman solver over (W, h, t).

    V_t(W,h) = max_{c,pi,e} u(c,h,e) + beta*[ (1-q_t(h))*E V_{t+1}(W',h') + q_t(h)*Bq(W') ]

Numerical structure
-------------------
The expensive object is E[V_{t+1}(W', h')]. Two facts make it cheap:

* h' depends only on (h, e) -- never on c or pi. So next-period value can be
  pre-collapsed along the h axis into ``Vh[:, j] = V_{t+1}(W_grid, h'(h_j, e))``.
* W' = (W + y - m - c) * R'(pi, node), so ln W' depends on (W, c, pi, node)
  but **not** on h. Its bilinear-in-ln W interpolation weights are therefore
  shared across every h.

So for each (seat, age) we build one sparse-in-effect weight matrix
``A`` of shape (n_W*n_c*n_pi, n_W) that already folds in the Gauss-Hermite
weights, and get the whole expectation with a single dense matmul
``A @ Vh``. The W grid is log-spaced, so ln W is uniform and the bracketing
index is a floor division -- no searchsorted needed.

Outside the ln W grid the interpolation is *linearly extrapolated* rather than
clamped. Under log utility V is close to affine in ln W, so this is far more
accurate at the boundaries than flattening.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from . import health as H
from .model import (BEQUEST_FLOOR, Params, ReturnScenario, Seat, death_prob,
                    log_return_grid, seat_net_income, social_security)

NEG = -1.0e300


@dataclass
class Grids:
    lnW: np.ndarray          # (n_W,) uniform in ln W
    W: np.ndarray            # (n_W,)
    h: np.ndarray            # (n_h,)
    c_frac: np.ndarray       # (n_c,)
    pi: np.ndarray           # (n_pi,)
    ages: np.ndarray         # (T+1,) incl. terminal age

    @property
    def n_W(self) -> int:
        return self.lnW.size

    @property
    def n_h(self) -> int:
        return self.h.size

    @property
    def dlnW(self) -> float:
        return float(self.lnW[1] - self.lnW[0])


@dataclass
class Solution:
    params: Params
    grids: Grids
    seats: List[Seat]                 # seats available while working
    V_work: np.ndarray                # (T+1, n_W, n_h)
    V_ret: np.ndarray                 # (T+1, n_W, n_h)
    pol_c: np.ndarray                 # (T, n_W, n_h) consumption / resources
    pol_pi: np.ndarray                # (T, n_W, n_h)
    pol_e: np.ndarray                 # (T, n_W, n_h) index into `seats`
    pol_c_ret: np.ndarray             # (T, n_W, n_h)
    pol_pi_ret: np.ndarray            # (T, n_W, n_h)
    b: float
    scenario: str

    @property
    def seat_ids(self) -> List[str]:
        return [s.id for s in self.seats]

    def retired_index(self) -> int:
        for i, s in enumerate(self.seats):
            if s.absorbing:
                return i
        return -1


def consumption_grid(res: np.ndarray, grids: Grids, c_floor: float) -> np.ndarray:
    """Consumption choices, shape (n_W, n_c).

    Log-spaced in c/resources, then floored at an absolute subsistence level
    (never above the top of the proportional grid, so savings stay positive).
    """
    hi = grids.c_frac[-1] * res
    lo = np.minimum(c_floor, hi)
    return np.maximum(grids.c_frac[None, :] * res[:, None], lo[:, None])


def build_grids(params: Params) -> Grids:
    n = params.numerics
    lnW = np.linspace(np.log(n.W_min), np.log(n.W_max), n.n_W)
    if params.health_enabled:
        h = np.linspace(params.health.h_min, 1.0, n.n_h)
    else:
        h = np.array([1.0])
    c_frac = np.exp(np.linspace(np.log(n.c_frac_min), np.log(n.c_frac_max), n.n_c))
    pi = n.pi_grid
    ages = np.arange(params.age0, n.age_max + 1.0, 1.0)
    return Grids(lnW=lnW, W=np.exp(lnW), h=h, c_frac=c_frac, pi=pi, ages=ages)


def subsistence_consumption(b: float) -> float:
    """c_sub = exp(-b): the consumption level at which flow utility hits zero.

    Below it, u = h*(b + ln c) - phi is *decreasing* in h, so the model would say
    better health makes you worse off. The VSL calibration of b pins this number,
    which makes it a first-class diagnostic rather than an implementation detail.
    """
    return float(np.exp(-b))


def felicity_check(params: Params, grids: Grids, b: float) -> Dict[str, float]:
    """Diagnostics for the b + ln c > 0 condition over the consumption grid."""
    res_min = _min_resources(params, grids)
    c_min = float(consumption_grid(np.array([max(res_min, 1.0)]), grids,
                                   params.numerics.c_floor).min())
    c_sub = subsistence_consumption(b)
    return dict(c_min_grid=c_min, c_sub=c_sub, margin=b + np.log(max(c_min, 1e-12)),
                ok=float(c_min > c_sub))


def assert_felicity_positive(params: Params, grids: Grids, b: float) -> None:
    """b + ln c > 0 must hold over the whole consumption grid.

    Otherwise u = h*(b + ln c) - phi is decreasing in h somewhere, i.e. better
    health would lower utility -- the model would be nonsense there.
    """
    chk = felicity_check(params, grids, b)
    if not chk["ok"]:
        raise ValueError(
            f"Felicity intercept b={b:.4f} is inadmissible: it implies a "
            f"subsistence consumption c_sub = exp(-b) = ${chk['c_sub']:,.0f}/yr, "
            f"above the consumption-grid floor of ${chk['c_min_grid']:,.0f}/yr. "
            "Over that range higher health would reduce utility. Either raise "
            "vsl_target or raise numerics.c_floor."
        )


def _min_resources(params: Params, grids: Grids) -> float:
    """Smallest resources reachable on the grid across seats and ages."""
    best = np.inf
    for s in params.seats:
        yn = seat_net_income(s, params)
        for age in grids.ages[:-1]:
            m = params.mortgage.payment_at(age, params.age0) if params.mortgage_enabled else 0.0
            res = grids.W[0] + yn + social_security(age, params) - m
            best = min(best, res)
    return float(best)


# --------------------------------------------------------------------------- #
# Core kernel                                                                  #
# --------------------------------------------------------------------------- #

class _Kernel:
    """Precomputed, grid-shaped constants for the expectation operator.

    Everything here depends only on the grids and the return scenario, so it is
    built once per solve rather than once per (seat, age).
    """

    __slots__ = ("grids", "lnR_over_d", "gh_w", "rows_base", "w_flat", "n_rows",
                 "n_k", "lnR", "c_floor", "_cache", "_order", "_max_cache")

    def __init__(self, grids: Grids, lnR: np.ndarray, gh_w: np.ndarray,
                 c_floor: float = 0.0, max_cache: int = 24):
        self.grids = grids
        self.c_floor = float(c_floor)
        self.lnR = lnR
        self.lnR_over_d = lnR / grids.dlnW
        self.gh_w = gh_w
        n_rows = grids.n_W * grids.c_frac.size * grids.pi.size
        n_k = lnR.shape[1]
        self.n_rows = n_rows
        self.n_k = n_k
        self.rows_base = (np.repeat(np.arange(n_rows, dtype=np.int64), n_k)
                          * grids.n_W)
        self.w_flat = np.broadcast_to(gh_w[None, :], (n_rows, n_k)).ravel().copy()
        self._cache: Dict[float, Tuple[np.ndarray, np.ndarray]] = {}
        self._order: List[float] = []
        self._max_cache = max_cache

    # -- cache ------------------------------------------------------------ #
    def operator(self, offset: float) -> Tuple[np.ndarray, np.ndarray]:
        """(A, EBq_ln) for resources ``W_grid + offset``.

        ``offset = net wage + social security - mortgage payment - switch cost``
        is constant across long stretches of the age grid (the mortgage amortizes
        once, social security switches on once), so the operator is memoized on
        it. This is what keeps a full solve to a few seconds.
        """
        key = round(float(offset), 6)
        hit = self._cache.get(key)
        if hit is not None:
            self._order.remove(key)
            self._order.append(key)
            return hit
        built = self._build(offset)
        self._cache[key] = built
        self._order.append(key)
        while len(self._order) > self._max_cache:
            self._cache.pop(self._order.pop(0), None)
        return built

    def _build(self, offset: float) -> Tuple[np.ndarray, np.ndarray]:
        g = self.grids
        res = g.W + offset
        res_safe = np.maximum(res, 1.0)
        c = consumption_grid(res_safe, g, self.c_floor)
        sav = np.maximum(res_safe[:, None] - c, 1e-8)

        u = (np.log(sav) - g.lnW[0]) / g.dlnW                 # (n_W, n_c)
        pos = u[:, :, None, None] + self.lnR_over_d[None, None, :, :]
        pos = pos.reshape(self.n_rows, self.n_k)

        idx = np.floor(pos).astype(np.int64)
        np.clip(idx, 0, g.n_W - 2, out=idx)
        # frac is measured against the *clipped* index, so points off the end of
        # the grid are linearly extrapolated rather than clamped.
        frac = (pos - idx).ravel()
        idx_f = idx.ravel()

        base = self.rows_base + idx_f
        size = self.n_rows * g.n_W
        A = np.bincount(base, weights=self.w_flat * (1.0 - frac), minlength=size)
        A += np.bincount(base + 1, weights=self.w_flat * frac, minlength=size)
        A = A.reshape(self.n_rows, g.n_W)

        ln_floor = np.log(BEQUEST_FLOOR)
        lnWp = pos * g.dlnW + g.lnW[0]
        EBq_ln = (np.maximum(lnWp, ln_floor) * self.gh_w[None, :]).sum(axis=1)
        return A, EBq_ln


def _seat_value_and_policy(seat: Seat, age: float, params: Params, grids: Grids,
                           V_next: np.ndarray, b: float, kern: "_Kernel",
                           wealth_penalty: float = 0.0,
                           health_penalty: float = 0.0):
    """Value and (c, pi) argmax of choosing *seat* at *age*. Shapes (n_W, n_h)."""
    n_W, n_h, n_c, n_pi = grids.n_W, grids.n_h, grids.c_frac.size, grids.pi.size

    m = params.mortgage.payment_at(age, params.age0) if params.mortgage_enabled else 0.0
    offset = seat_net_income(seat, params) + social_security(age, params) - m - wealth_penalty
    A, EBq_ln = kern.operator(offset)

    res = grids.W + offset
    ok = res > 1.0
    c = consumption_grid(np.maximum(res, 1.0), grids, kern.c_floor)

    # --- next-period health, per current-h node -------------------------- #
    ceiling = float(H.h_max(age, params.health))
    if params.health_enabled:
        h_now = np.clip(grids.h - health_penalty, params.health.h_min, 1.0)
        h_next = H.step(h_now, seat, params.health, ceiling)
        hg = grids.h
        pos = np.interp(h_next, hg, np.arange(hg.size))
        j0 = np.clip(np.floor(pos).astype(int), 0, hg.size - 2)
        a = pos - j0
        Vh = V_next[:, j0] * (1.0 - a)[None, :] + V_next[:, j0 + 1] * a[None, :]
    else:
        Vh = V_next[:, :1]

    EV = (A @ Vh).reshape(n_W, n_c, n_pi, n_h)
    EBq = params.omega_bequest * (b + EBq_ln.reshape(n_W, n_c, n_pi))

    q = death_prob(age, grids.h, params)                        # (n_h,)
    beta = np.exp(-params.rho)

    u = grids.h[None, None, :] * (b + np.log(c)[:, :, None]) - seat.phi   # (n_W,n_c,n_h)
    cont = (1.0 - q)[None, None, None, :] * EV + q[None, None, None, :] * EBq[..., None]
    total = u[:, :, None, :] + beta * cont                      # (n_W,n_c,n_pi,n_h)
    if not ok.all():
        total = np.where(ok[:, None, None, None], total, NEG)

    flat = np.moveaxis(total, 3, 1).reshape(n_W, n_h, n_c * n_pi)
    k = np.argmax(flat, axis=2)
    val = np.take_along_axis(flat, k[:, :, None], axis=2)[:, :, 0]
    return val, k // n_pi, k % n_pi


def solve(params: Params, scenario: Optional[str] = None,
          seats_allowed: Optional[Sequence[str]] = None,
          b: Optional[float] = None,
          check_felicity: bool = True) -> Solution:
    """Backward induction over the whole age grid.

    ``retired`` is absorbing, so two value functions are carried: ``V_ret``
    (already retired -- seat locked) and ``V_work`` (still working, may retire).
    """
    scenario = scenario or params.scenario
    sc = params.returns[scenario]
    bb = params.b if b is None else b
    if bb is None:
        raise ValueError("Utility intercept b is not set; run calibrate.calibrate_b first.")

    grids = build_grids(params)
    if check_felicity:
        assert_felicity_positive(params, grids, bb)

    all_seats = list(params.seats)
    if seats_allowed is not None:
        keep = set(seats_allowed)
        all_seats = [s for s in all_seats if s.id in keep]
    ret_seats = [s for s in all_seats if s.absorbing]
    if not ret_seats:
        raise ValueError("The seat roster must contain an absorbing 'retired' seat.")
    retired = ret_seats[0]

    _, gh_w = np.polynomial.hermite.hermgauss(params.numerics.n_gh)
    gh_w = gh_w / np.sqrt(np.pi)
    lnR = log_return_grid(grids.pi, sc, params.numerics.n_gh)
    kern = _Kernel(grids, lnR, gh_w, c_floor=params.numerics.c_floor)

    T = grids.ages.size - 1
    n_W, n_h = grids.n_W, grids.n_h

    V_work = np.empty((T + 1, n_W, n_h))
    V_ret = np.empty((T + 1, n_W, n_h))
    pol_c = np.zeros((T, n_W, n_h), dtype=np.int16)
    pol_pi = np.zeros((T, n_W, n_h), dtype=np.int16)
    pol_e = np.zeros((T, n_W, n_h), dtype=np.int16)
    pol_c_ret = np.zeros((T, n_W, n_h), dtype=np.int16)
    pol_pi_ret = np.zeros((T, n_W, n_h), dtype=np.int16)

    terminal = params.omega_bequest * (bb + np.log(np.maximum(grids.W, BEQUEST_FLOOR)))
    V_work[T] = terminal[:, None]
    V_ret[T] = terminal[:, None]

    for ti in range(T - 1, -1, -1):
        age = float(grids.ages[ti])

        v_r, c_r, p_r = _seat_value_and_policy(retired, age, params, grids,
                                               V_ret[ti + 1], bb, kern)
        V_ret[ti] = v_r
        pol_c_ret[ti] = c_r
        pol_pi_ret[ti] = p_r

        best = np.full((n_W, n_h), NEG)
        best_c = np.zeros((n_W, n_h), dtype=np.int16)
        best_pi = np.zeros((n_W, n_h), dtype=np.int16)
        best_e = np.zeros((n_W, n_h), dtype=np.int16)

        for ei, seat in enumerate(all_seats):
            if seat.absorbing:
                v, ci, pj = v_r, c_r, p_r
            else:
                v, ci, pj = _seat_value_and_policy(seat, age, params, grids,
                                                   V_work[ti + 1], bb, kern)
            better = v > best
            best = np.where(better, v, best)
            best_c = np.where(better, ci.astype(np.int16), best_c)
            best_pi = np.where(better, pj.astype(np.int16), best_pi)
            best_e = np.where(better, np.int16(ei), best_e)

        V_work[ti] = best
        pol_c[ti] = best_c
        pol_pi[ti] = best_pi
        pol_e[ti] = best_e

    return Solution(params=params, grids=grids, seats=all_seats, V_work=V_work,
                    V_ret=V_ret, pol_c=pol_c, pol_pi=pol_pi, pol_e=pol_e,
                    pol_c_ret=pol_c_ret, pol_pi_ret=pol_pi_ret, b=bb, scenario=scenario)


# --------------------------------------------------------------------------- #
# Shadow prices                                                                #
# --------------------------------------------------------------------------- #

def value_at(sol: Solution, W: float, h: float, age: float, retired: bool = False) -> float:
    """Bilinear interpolation of V in (ln W, h)."""
    V = sol.V_ret if retired else sol.V_work
    ti = int(round(age - sol.params.age0))
    ti = int(np.clip(ti, 0, V.shape[0] - 1))
    g = sol.grids
    x = (np.log(max(W, 1e-6)) - g.lnW[0]) / g.dlnW
    i0 = int(np.clip(np.floor(x), 0, g.n_W - 2))
    ax = x - i0
    if g.n_h == 1:
        col = V[ti][:, 0]
        return float(col[i0] * (1 - ax) + col[i0 + 1] * ax)
    y = np.interp(h, g.h, np.arange(g.n_h))
    j0 = int(np.clip(np.floor(y), 0, g.n_h - 2))
    ay = y - j0
    v = (V[ti][i0, j0] * (1 - ax) * (1 - ay) + V[ti][i0 + 1, j0] * ax * (1 - ay)
         + V[ti][i0, j0 + 1] * (1 - ax) * ay + V[ti][i0 + 1, j0 + 1] * ax * ay)
    return float(v)


def shadow_prices(sol: Solution, W: float, h: float, age: float) -> Dict[str, float]:
    """V, V_W, V_h, VSL = V/V_W, and Lambda_h = 0.01 * V_h/V_W.

    Central differences on the interpolated V. The wealth step is relative (so
    it is well-scaled on a log grid); the health step is absolute.
    """
    dW = 0.02 * W
    dh = 0.02
    g = sol.grids
    h_lo = max(h - dh, g.h[0] + 1e-9) if g.n_h > 1 else h
    h_hi = min(h + dh, g.h[-1] - 1e-9) if g.n_h > 1 else h

    V = value_at(sol, W, h, age)
    V_W = (value_at(sol, W + dW, h, age) - value_at(sol, W - dW, h, age)) / (2.0 * dW)
    if g.n_h > 1 and h_hi > h_lo:
        V_h = (value_at(sol, W, h_hi, age) - value_at(sol, W, h_lo, age)) / (h_hi - h_lo)
    else:
        V_h = float("nan")

    vsl = V / V_W if V_W != 0 else float("inf")
    lam_h = 0.01 * V_h / V_W if V_W != 0 else float("inf")
    return dict(V=V, V_W=V_W, V_h=V_h, VSL=vsl, Lambda_h=lam_h)


def consumption_at(sol: Solution, W: float, h: float, age: float,
                   retired: bool = False) -> Dict[str, float]:
    """Nearest-grid-node policy readout at a queried state."""
    g = sol.grids
    ti = int(np.clip(round(age - sol.params.age0), 0, sol.pol_c.shape[0] - 1))
    i = int(np.clip(round((np.log(max(W, 1e-6)) - g.lnW[0]) / g.dlnW), 0, g.n_W - 1))
    j = 0 if g.n_h == 1 else int(np.clip(round(np.interp(h, g.h, np.arange(g.n_h))), 0, g.n_h - 1))
    if retired:
        ci, pj, ei = sol.pol_c_ret[ti, i, j], sol.pol_pi_ret[ti, i, j], sol.retired_index()
    else:
        ci, pj, ei = sol.pol_c[ti, i, j], sol.pol_pi[ti, i, j], sol.pol_e[ti, i, j]
    seat = sol.seats[int(ei)]
    m = sol.params.mortgage.payment_at(age, sol.params.age0) if sol.params.mortgage_enabled else 0.0
    res = W + seat_net_income(seat, sol.params) + social_security(age, sol.params) - m
    frac = float(g.c_frac[int(ci)])
    return dict(seat=seat.id, c_frac=frac, c=frac * max(res, 0.0),
                pi=float(g.pi[int(pj)]), resources=res)


# --------------------------------------------------------------------------- #
# Section 7 extension: switching costs and the inaction band                   #
# --------------------------------------------------------------------------- #

@dataclass
class SwitchingSolution:
    """Solution when seat changes cost kappa_W dollars and kappa_h health.

    The previous seat becomes part of the state, so the seat choice turns into a
    genuine optimal-stopping problem with hysteresis. The interesting object is
    the **inaction band**: states where you stay put even though a different
    seat scores strictly higher statically. That band is why rational people sit
    in suboptimal jobs longer than a static score says they should.
    """
    params: Params
    grids: Grids
    seats: List[Seat]
    prev_seats: List[Seat]
    V_work: np.ndarray                # (T+1, n_prev, n_W, n_h)
    V_ret: np.ndarray                 # (T+1, n_W, n_h)
    pol_e: np.ndarray                 # (T, n_prev, n_W, n_h)
    b: float
    scenario: str

    def stay_mask(self, prev_id: str, age: float) -> np.ndarray:
        """(n_W, n_h) bool: does the agent keep seat *prev_id* at this age?"""
        pi_ = [s.id for s in self.prev_seats].index(prev_id)
        ei = [s.id for s in self.seats].index(prev_id)
        ti = int(np.clip(round(age - self.params.age0), 0, self.pol_e.shape[0] - 1))
        return self.pol_e[ti, pi_] == ei


def solve_switching(params: Params, scenario: Optional[str] = None,
                    b: Optional[float] = None) -> SwitchingSolution:
    """Backward induction with the previous seat carried in the state."""
    scenario = scenario or params.scenario
    sc = params.returns[scenario]
    bb = params.b if b is None else b
    if bb is None:
        raise ValueError("Utility intercept b is not set.")

    grids = build_grids(params)
    seats = list(params.seats)
    prev_seats = [s for s in seats if not s.absorbing]
    retired = next(s for s in seats if s.absorbing)
    prev_index = {s.id: i for i, s in enumerate(prev_seats)}

    _, gh_w = np.polynomial.hermite.hermgauss(params.numerics.n_gh)
    gh_w = gh_w / np.sqrt(np.pi)
    lnR = log_return_grid(grids.pi, sc, params.numerics.n_gh)
    kern = _Kernel(grids, lnR, gh_w, c_floor=params.numerics.c_floor,
                   max_cache=2 * len(seats) + 8)

    T = grids.ages.size - 1
    n_W, n_h, n_p = grids.n_W, grids.n_h, len(prev_seats)

    V_work = np.empty((T + 1, n_p, n_W, n_h))
    V_ret = np.empty((T + 1, n_W, n_h))
    pol_e = np.zeros((T, n_p, n_W, n_h), dtype=np.int16)

    terminal = params.omega_bequest * (bb + np.log(np.maximum(grids.W, BEQUEST_FLOOR)))
    V_work[T] = terminal[None, :, None]
    V_ret[T] = terminal[:, None]

    kW, kh = params.kappa_W, params.kappa_h
    for ti in range(T - 1, -1, -1):
        age = float(grids.ages[ti])
        V_ret[ti] = _seat_value_and_policy(retired, age, params, grids,
                                           V_ret[ti + 1], bb, kern)[0]
        # Each (seat, switched?) pair is evaluated once and reused across e_prev.
        cache = {}
        for ei, seat in enumerate(seats):
            for switched in (False, True):
                nxt = V_ret[ti + 1] if seat.absorbing else V_work[ti + 1, prev_index[seat.id]]
                cache[(ei, switched)] = _seat_value_and_policy(
                    seat, age, params, grids, nxt, bb, kern,
                    wealth_penalty=kW if switched else 0.0,
                    health_penalty=kh if switched else 0.0)[0]

        for pi_, prev in enumerate(prev_seats):
            best = np.full((n_W, n_h), NEG)
            best_e = np.zeros((n_W, n_h), dtype=np.int16)
            for ei, seat in enumerate(seats):
                v = cache[(ei, seat.id != prev.id)]
                better = v > best
                best = np.where(better, v, best)
                best_e = np.where(better, np.int16(ei), best_e)
            V_work[ti, pi_] = best
            pol_e[ti, pi_] = best_e

    return SwitchingSolution(params=params, grids=grids, seats=seats,
                             prev_seats=prev_seats, V_work=V_work, V_ret=V_ret,
                             pol_e=pol_e, b=bb, scenario=scenario)


def inaction_band(sw: SwitchingSolution, frictionless: Solution, prev_id: str,
                  age: float) -> Dict[str, float]:
    """The hysteresis region, measured against the frictionless policy.

    A state is *in the band* when the frictionless solver would move to a
    different seat but the frictional one stays in ``prev_id``. That is the
    real-options structure: the option to move is worth keeping unexercised.
    """
    ti = int(np.clip(round(age - sw.params.age0), 0, sw.pol_e.shape[0] - 1))
    pi_ = [s.id for s in sw.prev_seats].index(prev_id)
    ei = [s.id for s in sw.seats].index(prev_id)

    stay = sw.pol_e[ti, pi_] == ei
    free_ids = [s.id for s in frictionless.seats]
    free = np.vectorize(lambda k: free_ids[int(k)])(frictionless.pol_e[ti])
    free_moves = free != prev_id

    band = stay & free_moves
    return dict(frac_stay=float(stay.mean()),
                frac_frictionless_moves=float(free_moves.mean()),
                frac_inaction_band=float(band.mean()),
                n_states=int(stay.size))

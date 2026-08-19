"""Forward Monte Carlo under a solved policy.

Vectorized across paths: 10_000 paths x 61 years runs in well under a second.
Seeded with ``mc.seed`` so every reported number is reproducible.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np

from . import health as H
from .model import (Params, death_prob, seat_net_income, social_security)
from .solver import Solution, consumption_grid


@dataclass
class MCResult:
    label: str
    scenario: str
    retire_age: np.ndarray        # (paths,) nan if never retired while alive
    terminal_W: np.ndarray
    terminal_h: np.ndarray
    death_age: np.ndarray         # nan if survived to age_max
    coverage_shortfall: np.ndarray  # bool: ever c < 0.5*spend_base after retiring
    c_over_W: np.ndarray          # (T, paths)
    W_path: np.ndarray            # (T+1, paths)
    h_path: np.ndarray            # (T+1, paths)
    alive: np.ndarray             # (T+1, paths) bool
    ages: np.ndarray

    def quantiles(self, x: np.ndarray) -> Dict[str, float]:
        v = np.asarray(x, dtype=float)
        v = v[np.isfinite(v)]
        if v.size == 0:
            return dict(p10=float("nan"), median=float("nan"), p90=float("nan"))
        return dict(p10=float(np.percentile(v, 10)),
                    median=float(np.percentile(v, 50)),
                    p90=float(np.percentile(v, 90)))

    def summary(self) -> Dict[str, object]:
        return dict(
            label=self.label, scenario=self.scenario,
            retire_age=self.quantiles(self.retire_age),
            terminal_W=self.quantiles(self.terminal_W),
            terminal_h=self.quantiles(self.terminal_h),
            p_never_retired=float(np.mean(~np.isfinite(self.retire_age))),
            p_coverage_shortfall=float(np.mean(self.coverage_shortfall)),
        )


def _bilinear_weights(x: np.ndarray, grid_lo: float, d: float, n: int):
    pos = (x - grid_lo) / d
    i0 = np.clip(np.floor(pos).astype(np.int64), 0, n - 2)
    a = np.clip(pos - i0, 0.0, 1.0)
    return i0, a


def simulate(sol: Solution, params: Optional[Params] = None,
             paths: Optional[int] = None, seed: Optional[int] = None,
             label: str = "optimal", W0: Optional[float] = None,
             h0: Optional[float] = None) -> MCResult:
    """Roll the solved policy forward under fresh return and mortality draws.

    Continuous controls (consumption share, risky share) are interpolated
    bilinearly in (ln W, h); the discrete seat choice is read off the nearest
    grid node, as it must be.
    """
    p = params or sol.params
    g = sol.grids
    n_paths = int(paths if paths is not None else p.mc_paths)
    rng = np.random.default_rng(int(seed if seed is not None else p.mc_seed))
    sc = p.returns[sol.scenario]

    T = sol.pol_c.shape[0]
    ages = g.ages
    ri = sol.retired_index()

    W = np.full(n_paths, float(W0 if W0 is not None else p.W0))
    h = np.full(n_paths, float(h0 if h0 is not None else p.h0))
    alive = np.ones(n_paths, dtype=bool)
    retired = np.zeros(n_paths, dtype=bool)

    retire_age = np.full(n_paths, np.nan)
    death_age = np.full(n_paths, np.nan)
    shortfall = np.zeros(n_paths, dtype=bool)

    W_path = np.zeros((T + 1, n_paths))
    h_path = np.zeros((T + 1, n_paths))
    alive_path = np.zeros((T + 1, n_paths), dtype=bool)
    cw = np.full((T, n_paths), np.nan)
    W_path[0], h_path[0], alive_path[0] = W, h, alive

    net_by_seat = np.array([seat_net_income(s, p) for s in sol.seats])
    seats = list(sol.seats)

    for ti in range(T):
        age = float(ages[ti])
        m = p.mortgage.payment_at(age, p.age0) if p.mortgage_enabled else 0.0
        ss = social_security(age, p)

        i0, ax = _bilinear_weights(np.log(np.maximum(W, 1e-6)), g.lnW[0], g.dlnW, g.n_W)
        if g.n_h == 1:
            j0 = np.zeros(n_paths, dtype=np.int64)
            ay = np.zeros(n_paths)
            jn = np.zeros(n_paths, dtype=np.int64)
        else:
            posh = np.interp(h, g.h, np.arange(g.n_h))
            j0 = np.clip(np.floor(posh).astype(np.int64), 0, g.n_h - 2)
            ay = np.clip(posh - j0, 0.0, 1.0)
            jn = np.clip(np.rint(posh).astype(np.int64), 0, g.n_h - 1)
        inear = np.clip(np.rint((np.log(np.maximum(W, 1e-6)) - g.lnW[0]) / g.dlnW
                                ).astype(np.int64), 0, g.n_W - 1)

        # --- discrete seat: nearest node, absorbing once retired ---------- #
        e_idx = np.where(retired, ri, sol.pol_e[ti, inear, jn].astype(np.int64))
        newly = (~retired) & (e_idx == ri) & alive
        retire_age[newly] = age
        retired = retired | (e_idx == ri)

        # --- continuous controls: bilinear on the *fraction* grids -------- #
        # Retired paths read the absorbing-state policy; the rest read the
        # working policy. Both are interpolated in (ln W, h).
        cfr = np.empty(n_paths)
        pir = np.empty(n_paths)
        for arr_c, arr_pi, mask in ((sol.pol_c_ret[ti], sol.pol_pi_ret[ti], retired),
                                    (sol.pol_c[ti], sol.pol_pi[ti], ~retired)):
            if not mask.any():
                continue
            fc = g.c_frac[arr_c]
            fp = g.pi[arr_pi]
            v_c = (fc[i0, j0] * (1 - ax) * (1 - ay) + fc[i0 + 1, j0] * ax * (1 - ay)
                   + fc[i0, j0 + 1] * (1 - ax) * ay + fc[i0 + 1, j0 + 1] * ax * ay)
            v_p = (fp[i0, j0] * (1 - ax) * (1 - ay) + fp[i0 + 1, j0] * ax * (1 - ay)
                   + fp[i0, j0 + 1] * (1 - ax) * ay + fp[i0 + 1, j0 + 1] * ax * ay)
            cfr[mask] = v_c[mask]
            pir[mask] = v_p[mask]

        y = net_by_seat[e_idx] + ss
        res = W + y - m
        res = np.maximum(res, 1.0)
        hi = g.c_frac[-1] * res
        c = np.clip(cfr * res, np.minimum(p.numerics.c_floor, hi), hi)
        sav = np.maximum(res - c, 1e-8)

        cw[ti] = np.where(alive, c / np.maximum(W, 1.0), np.nan)
        shortfall |= alive & retired & (c < 0.5 * p.spend_base)

        # --- returns ------------------------------------------------------ #
        eps = rng.standard_normal(n_paths)
        lnR = (sc.rf_real + pir * sc.erp - 0.5 * pir ** 2 * sc.sigma ** 2
               + pir * sc.sigma * eps)
        W_new = sav * np.exp(lnR)

        # --- health -------------------------------------------------------- #
        ceiling = float(H.h_max(age, p.health))
        h_new = h.copy()
        for ei, seat in enumerate(seats):
            sel = e_idx == ei
            if sel.any():
                h_new[sel] = H.step(h[sel], seat, p.health, ceiling)

        # --- mortality ----------------------------------------------------- #
        q = death_prob(age, h, p)
        died = alive & (rng.random(n_paths) < q)
        death_age[died] = age
        alive = alive & ~died

        W = np.where(alive, W_new, W)
        h = np.where(alive, h_new, h)
        W_path[ti + 1], h_path[ti + 1], alive_path[ti + 1] = W, h, alive

    return MCResult(label=label, scenario=sol.scenario, retire_age=retire_age,
                    terminal_W=W, terminal_h=h, death_age=death_age,
                    coverage_shortfall=shortfall, c_over_W=cw, W_path=W_path,
                    h_path=h_path, alive=alive_path, ages=ages)


def median_finish_age(sol: Solution, params: Optional[Params] = None,
                      paths: int = 4000, seed: Optional[int] = None) -> float:
    """Median age at which the optimal policy enters ``retired``."""
    r = simulate(sol, params=params, paths=paths, seed=seed, label="finish")
    v = r.retire_age[np.isfinite(r.retire_age)]
    return float(np.median(v)) if v.size else float("nan")

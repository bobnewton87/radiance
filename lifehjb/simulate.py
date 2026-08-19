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


# =========================================================================== #
# v3 forward simulation                                                       #
# =========================================================================== #

from . import career as _C            # noqa: E402
from .solver import SolutionV3        # noqa: E402


@dataclass
class MCResultV3(MCResult):
    n_separations: np.ndarray = None      # (paths,) count of involuntary exits
    ever_separated: np.ndarray = None
    scarred: np.ndarray = None
    search_years: np.ndarray = None
    min_runway_months: np.ndarray = None
    sep_events: np.ndarray = None         # (T, paths) bool: separated this year
    downturn_events: np.ndarray = None    # (T, paths) bool: R' < 1 + threshold
    at_risk: np.ndarray = None            # (T, paths) bool: alive, working, separable

    def separation_by_market_state(self) -> Dict[str, float]:
        """Realized separation rate in downturn years vs normal years.

        Conditioning is on the return that actually moved wealth. In the joint
        model the ratio comes out at ``downturn_factor``; under independent
        sampling it collapses to 1.0 while the *marginal* rate is unchanged.
        That is the signature a tail quantile of terminal wealth is far too noisy
        to detect.
        """
        risk = self.at_risk
        down = self.downturn_events & risk
        norm = (~self.downturn_events) & risk
        r_down = float(self.sep_events[down].mean()) if down.any() else float("nan")
        r_norm = float(self.sep_events[norm].mean()) if norm.any() else float("nan")
        return dict(rate_downturn=r_down, rate_normal=r_norm,
                    ratio=(r_down / r_norm) if r_norm else float("nan"),
                    marginal=float(self.sep_events[risk].mean()) if risk.any() else float("nan"),
                    p_downturn_year=float(down.sum()) / float(risk.sum()) if risk.any() else float("nan"))

    def summary(self) -> Dict[str, object]:
        out = super().summary()
        out.update(
            p_ever_separated=float(np.mean(self.ever_separated)),
            mean_separations=float(np.mean(self.n_separations)),
            mean_search_years=float(np.mean(self.search_years)),
            p_runway_under_12m=float(np.mean(self.min_runway_months < 12.0)),
        )
        return out


def simulate_v3(sol: SolutionV3, params: Optional[Params] = None,
                paths: Optional[int] = None, seed: Optional[int] = None,
                label: str = "optimal", W0: Optional[float] = None,
                h0: Optional[float] = None,
                independent_separation: bool = False,
                start_state: Optional[int] = None) -> MCResultV3:
    """Roll the v3 policy forward.

    Separation is resolved **after** the return is drawn, against that same
    draw. ``independent_separation=True`` breaks that link -- drawing a second,
    independent shock with the same marginal separation rate -- and exists only
    so the test suite can prove the correlation is doing work rather than
    sitting in the code unused.
    """
    p = params or sol.params
    g = sol.grids
    space = sol.space
    n_paths = int(paths if paths is not None else p.mc_paths)
    # One generator per source of randomness, all fixed-size draws per period.
    # This keeps the streams synchronized across runs that differ only in model
    # structure -- which is what makes the joint-vs-independent separation
    # comparison a *paired* experiment rather than a noise measurement.
    ss_ = np.random.SeedSequence(int(seed if seed is not None else p.mc_seed))
    rng_ret, rng_alt, rng_sep, rng_avail, rng_search, rng_mort = [
        np.random.default_rng(x) for x in ss_.spawn(6)]
    sc = p.returns[sol.scenario]
    cp = p.career

    T = sol.pol_c.shape[0]
    ages = g.ages
    n_act = len(sol.actions)
    ret_a = sol.retired_action
    search_a = sol.search_action
    ln_thr = np.log(1.0 + cp.downturn_threshold)

    sep_states = space.separation_targets()
    sep_idx = np.array([j for j, _ in sep_states], dtype=np.int64) if sep_states else None
    sep_p = np.array([q for _, q in sep_states]) if sep_states else None

    # income / severance lookups, per (action, scarred, crunch)
    def _net(seat_id, scarred, crunch):
        if space.is_absorbing(seat_id):
            return 0.0
        return seat_net_income(space.seat_for(seat_id, scarred, crunch), p)

    def _sev(seat_id, scarred, crunch):
        if space.is_absorbing(seat_id) or seat_id == _C.SEARCHING:
            return 0.0
        return _C.severance_amount(space.seat_for(seat_id, scarred, crunch), cp)

    W = np.full(n_paths, float(W0 if W0 is not None else p.W0))
    h = np.full(n_paths, float(h0 if h0 is not None else p.h0))
    alive = np.ones(n_paths, dtype=bool)
    retired = np.zeros(n_paths, dtype=bool)
    state = np.full(n_paths, int(start_state if start_state is not None
                                 else space.start_index()), dtype=np.int64)

    retire_age = np.full(n_paths, np.nan)
    death_age = np.full(n_paths, np.nan)
    shortfall = np.zeros(n_paths, dtype=bool)
    n_sep = np.zeros(n_paths, dtype=np.int32)
    search_years = np.zeros(n_paths, dtype=np.float64)
    min_runway = np.full(n_paths, np.inf)
    sep_events = np.zeros((T, n_paths), dtype=bool)
    down_events = np.zeros((T, n_paths), dtype=bool)
    at_risk = np.zeros((T, n_paths), dtype=bool)

    W_path = np.zeros((T + 1, n_paths))
    h_path = np.zeros((T + 1, n_paths))
    alive_path = np.zeros((T + 1, n_paths), dtype=bool)
    cw = np.full((T, n_paths), np.nan)
    W_path[0], h_path[0], alive_path[0] = W, h, alive

    monthly = _C.monthly_full_expenses(p)

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

        action = np.full(n_paths, ret_a, dtype=np.int64)

        # Fixed-size draws, taken up front so the streams never desynchronize.
        u_avail = rng_avail.random((n_paths, n_act))
        eps = rng_ret.standard_normal(n_paths)
        eps_alt = rng_alt.standard_normal(n_paths)
        u_sep = rng_sep.random(n_paths)
        u_search = rng_search.random(n_paths)
        u_mort = rng_mort.random(n_paths)

        # --- seat choice, state by state ---------------------------------- #
        for i in np.unique(state[alive & ~retired]):
            sel = alive & ~retired & (state == i)
            if not sel.any():
                continue
            avail = space.availability(int(i), ti)
            n_sel = int(sel.sum())
            ok = np.zeros((n_sel, n_act), dtype=bool)
            for seat_id, pr in avail:
                a = sol.actions.index(seat_id)
                ok[:, a] = True if pr >= 1.0 else (u_avail[sel, a] < pr)
            rank = sol.pol_rank[ti, int(i)][inear[sel], jn[sel]].astype(np.int64)
            by_rank = np.take_along_axis(ok, rank, axis=1)
            first = np.argmax(by_rank, axis=1)
            has = by_rank.any(axis=1)
            chosen = rank[np.arange(n_sel), first]
            # A state with nothing on offer cannot occur (current350 and
            # downshift250 are always available), but fall back safely.
            chosen = np.where(has, chosen, rank[:, 0])
            action[sel] = chosen

        newly = (~retired) & alive & (action == ret_a)
        retire_age[newly] = age
        retired = retired | newly
        action[retired] = ret_a

        # --- controls ------------------------------------------------------ #
        cfr = np.zeros(n_paths)
        pir = np.zeros(n_paths)
        y = np.zeros(n_paths)
        sev_amt = np.zeros(n_paths)
        base_sep = np.zeros(n_paths)
        switch_cost = np.zeros(n_paths)
        seat_of_path: Dict[int, np.ndarray] = {}

        # retired paths
        if retired.any():
            fc = g.c_frac[sol.pol_c_ret[ti]]
            fp = g.pi[sol.pol_pi_ret[ti]]
            cfr[retired] = _bilerp(fc, i0, j0, ax, ay)[retired]
            pir[retired] = _bilerp(fp, i0, j0, ax, ay)[retired]

        for i in np.unique(state[alive & ~retired]):
            for a in np.unique(action[alive & ~retired & (state == i)]):
                sel = alive & ~retired & (state == i) & (action == a)
                if not sel.any():
                    continue
                seat_id = sol.actions[int(a)]
                st = space.states[int(i)]
                crunch = space.in_lockout(ti) and seat_id != _C.SEARCHING
                switched = (space.switched(int(i), seat_id) and p.switching_enabled)
                fc = g.c_frac[sol.pol_c[ti, int(i), int(a)]]
                fp = g.pi[sol.pol_pi[ti, int(i), int(a)]]
                cfr[sel] = _bilerp(fc, i0, j0, ax, ay)[sel]
                pir[sel] = _bilerp(fp, i0, j0, ax, ay)[sel]
                y[sel] = _net(seat_id, st.scarred, crunch)
                sev_amt[sel] = _sev(seat_id, st.scarred, crunch)
                base_sep[sel] = space.sep_rate(int(i), seat_id)
                switch_cost[sel] = p.kappa_W if switched else 0.0
                seat_of_path[(int(i), int(a))] = sel

        res = np.maximum(W + y + ss - m - switch_cost, 1.0)
        hi = g.c_frac[-1] * res
        c = np.clip(cfr * res, np.minimum(p.numerics.c_floor, hi), hi)
        sav = np.maximum(res - c, 1e-8)
        cw[ti] = np.where(alive, c / np.maximum(W, 1.0), np.nan)
        shortfall |= alive & retired & (c < 0.5 * p.spend_base)
        min_runway = np.where(alive, np.minimum(min_runway, W / monthly), min_runway)

        # --- returns, then separation against the SAME draw ---------------- #
        drift = sc.rf_real + pir * sc.erp - 0.5 * pir ** 2 * sc.sigma ** 2
        lnR = drift + pir * sc.sigma * eps
        W_new = sav * np.exp(lnR)

        # The correlation is the whole point: the cycle multiplier reads the
        # realized return that just moved wealth. `independent_separation` swaps
        # in a second draw with the same marginal law and exists only to prove
        # that swap costs something.
        lnR_for_sep = (drift + pir * sc.sigma * eps_alt) if independent_separation else lnR
        cyc = np.where(lnR_for_sep < ln_thr, cp.downturn_factor, 1.0)
        lam = np.clip(base_sep * cyc, 0.0, 1.0)
        sep = alive & ~retired & (u_sep < lam)
        sep_events[ti] = sep
        # Conditioned on the return that actually moved wealth -- so that under
        # independent sampling the ratio collapses to 1.0, which is the point.
        down_events[ti] = lnR < ln_thr
        at_risk[ti] = alive & ~retired & (base_sep > 0.0)

        # --- health, under the seat actually worked ------------------------ #
        ceiling = float(H.h_max(age, p.health))
        h_new = h.copy()
        for (i, a), sel in seat_of_path.items():
            st = space.states[i]
            seat_id = sol.actions[a]
            crunch = space.in_lockout(ti) and seat_id != _C.SEARCHING
            switched = (space.switched(i, seat_id) and p.switching_enabled)
            seat = space.seat_for(seat_id, st.scarred, crunch)
            hh = np.clip(h[sel] - (p.kappa_h if switched else 0.0), p.health.h_min, 1.0)
            h_new[sel] = H.step(hh, seat, p.health, ceiling)
        if retired.any():
            h_new[retired] = H.step(h[retired], space.retired, p.health, ceiling)

        # --- career state transition --------------------------------------- #
        new_state = state.copy()
        for (i, a), sel in seat_of_path.items():
            new_state[sel] = space.target(i, sol.actions[a])
        if sep.any() and sep_idx is not None:
            draw = np.searchsorted(np.cumsum(sep_p), u_search[sep], side="right")
            draw = np.clip(draw, 0, len(sep_idx) - 1)
            new_state[sep] = sep_idx[draw]
            W_new = np.where(sep, W_new + sev_amt, W_new)
            n_sep += sep.astype(np.int32)
        state = new_state
        search_years += (alive & ~retired
                         & np.isin(state, [space.idx[k] for k in space.states
                                           if k.seat == _C.SEARCHING and k.aux > 0])
                         ).astype(float)

        # --- mortality ------------------------------------------------------ #
        q = death_prob(age, h, p)
        died = alive & (u_mort < q)
        death_age[died] = age
        alive = alive & ~died

        W = np.where(alive, W_new, W)
        h = np.where(alive, h_new, h)
        W_path[ti + 1], h_path[ti + 1], alive_path[ti + 1] = W, h, alive

    return MCResultV3(
        label=label, scenario=sol.scenario, retire_age=retire_age, terminal_W=W,
        terminal_h=h, death_age=death_age, coverage_shortfall=shortfall,
        c_over_W=cw, W_path=W_path, h_path=h_path, alive=alive_path, ages=ages,
        n_separations=n_sep, ever_separated=(n_sep > 0), scarred=(n_sep > 0),
        search_years=search_years, min_runway_months=min_runway,
        sep_events=sep_events, downturn_events=down_events, at_risk=at_risk)


def _bilerp(f: np.ndarray, i0, j0, ax, ay) -> np.ndarray:
    """Bilinear read of a (n_W, n_h) policy-fraction array at path coordinates."""
    return (f[i0, j0] * (1 - ax) * (1 - ay) + f[i0 + 1, j0] * ax * (1 - ay)
            + f[i0, j0 + 1] * (1 - ax) * ay + f[i0 + 1, j0 + 1] * ax * ay)

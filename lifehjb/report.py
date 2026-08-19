"""Tables, plots and report.md generation.

Every number in the report is a state query with a numeric answer. If a figure
needs the source read to interpret it, it does not belong here.

The report is deterministic: no timestamps, fixed seeds, fixed formatting.
"""
from __future__ import annotations

import os
from dataclasses import replace
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import boundaries as B
from . import health as H
from . import negotiate as N
from .calibrate import calibrate_b, calibrate_rho, VSLFit
from .model import Params, Seat, gross_for_net, net_income, seat_net_income
from .solver import (Solution, build_grids, felicity_check, inaction_band,
                     shadow_prices, solve, solve_switching, subsistence_consumption)
from .simulate import MCResult, simulate

SCENARIOS = ("bear", "base", "bull")

FAST = dict(n_W=30, n_h=6, n_c=14, n_pi=4)


# --------------------------------------------------------------------------- #
# formatting                                                                   #
# --------------------------------------------------------------------------- #

def m(x: float, nd: int = 0) -> str:
    if x is None or not np.isfinite(x):
        return "n/a"
    return f"${x:,.{nd}f}"


def num(x: float, nd: int = 3) -> str:
    if x is None or not np.isfinite(x):
        return "n/a"
    return f"{x:.{nd}f}"


def pct(x: float, nd: int = 1) -> str:
    if x is None or not np.isfinite(x):
        return "n/a"
    return f"{100.0 * x:.{nd}f}%"


def table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# statistics                                                                   #
# --------------------------------------------------------------------------- #

def finish_stats(r: MCResult) -> Dict[str, float]:
    """Retirement-age statistics, with the censoring made explicit.

    A large share of paths never reach the stopping boundary before dying. The
    median is therefore reported *conditional on retiring*, alongside the
    probability of retiring at all -- reporting one without the other would be
    misleading.
    """
    v = r.retire_age[np.isfinite(r.retire_age)]
    q = r.quantiles(r.retire_age)
    return dict(median=q["median"], p10=q["p10"], p90=q["p90"],
                p_retire=float(v.size) / float(r.retire_age.size))


# --------------------------------------------------------------------------- #
# the run                                                                      #
# --------------------------------------------------------------------------- #

class ReportRun:
    """Holds every solve the report needs, so nothing is computed twice."""

    def __init__(self, params: Params, fast: bool = False, outdir: str = "out"):
        self.p = params
        self.fast = fast
        self.outdir = outdir
        if fast:
            self.p = self.p.evolve(numerics=replace(self.p.numerics, **FAST),
                                   mc_paths=min(self.p.mc_paths, 600))
        self.vsl_targets = sorted({float(self.p.vsl_band[0]), float(self.p.vsl_target),
                                   float(self.p.vsl_band[1])})
        self.fits: Dict[float, VSLFit] = {}
        self.sols: Dict[Tuple[str, float], Solution] = {}
        self.rho_fit = calibrate_rho()

    # -- solving ---------------------------------------------------------- #
    def calibrate(self) -> None:
        for t in self.vsl_targets:
            self.fits[t] = calibrate_b(self.p, vsl_target=t, scenario="base",
                                       tol=0.005, max_iter=10 if not self.fast else 6)

    def solution(self, scenario: str, vsl: float) -> Solution:
        key = (scenario, float(vsl))
        if key not in self.sols:
            self.sols[key] = solve(self.p, scenario=scenario, b=self.fits[vsl].b,
                                   check_felicity=False)
        return self.sols[key]

    @property
    def base_vsl(self) -> float:
        return min(self.vsl_targets, key=lambda t: abs(t - self.p.vsl_target))

    @property
    def base(self) -> Solution:
        return self.solution("base", self.base_vsl)

    @property
    def b(self) -> float:
        return self.fits[self.base_vsl].b


# --------------------------------------------------------------------------- #
# sections                                                                     #
# --------------------------------------------------------------------------- #

def section_boundaries(run: ReportRun) -> Tuple[str, B.BoundaryReport]:
    p = run.p
    br = B.compute(run.base, p)
    rows = [
        ["W_BATNA (walk-away runway)", m(br.W_BATNA),
         f"{br.W_BATNA / br.W_now:.2f}x",
         f"{p.runway_years:.0f} yr x {m(br.annual_full_expenses)} full expenses"],
    ]
    for a in sorted(br.W_coast):
        rows.append([f"W_coast({a})", m(br.W_coast[a]), f"{br.W_coast[a] / br.W_now:.2f}x",
                     f"reaches W*({a}) by age {a} at {pct(br.g_real, 2)} real, zero saving"])
    rows.append(["W* (stopping boundary, age %d)" % int(p.age0), m(br.W_star_now),
                 f"{br.W_star_now / br.W_now:.2f}x",
                 f"smallest W with e* = retired at h = {br.h0:.2f}"])
    rows.append(["**W today**", f"**{m(br.W_now)}**", "**1.00x**", "liquid only; home equity excluded"])

    txt = ["## 2. The three wealth boundaries", "",
           "These are routinely conflated. They answer different questions and they are "
           "an order of magnitude apart.", "",
           table(["boundary", "wealth", "x current W", "what it means"], rows), "",
           f"Ordering check (W_BATNA < W_coast(60) < W_coast({min(br.W_coast)}) < W*): "
           f"**{'holds' if br.W_BATNA < br.W_coast[max(br.W_coast)] < br.W_coast[min(br.W_coast)] < br.W_star_now else 'VIOLATED'}**.", "",
           f"The walk-away number is **{br.W_now / br.W_BATNA:.1f}x covered already**. The "
           f"stopping number is **{br.W_star_now / br.W_now:.1f}x away**. Those two facts "
           "together are the whole negotiating position: the outside option is credible "
           "today, and stopping is not close.", ""]
    return "\n".join(txt), br


def section_seats(run: ReportRun, finish: Dict[Tuple[str, str], Dict[str, float]]) -> str:
    p = run.p
    rows = []
    for r in N.seat_table(p):
        cells = [f"`{r.id}`", m(r.y), m(r.y_net), num(r.delta_total, 4), num(r.recovery, 3),
                 f"**{r.h_star:.3f}**", num(r.tau, 2), num(r.half_life, 2),
                 m(r.savings_capacity)]
        for sc in SCENARIOS:
            st = finish.get((r.id, sc))
            cells.append("absorbing" if r.id == "retired" else
                         (f"{st['median']:.0f} ({pct(st['p_retire'], 0)})" if st else "n/a"))
        rows.append(cells)
    hdr = ["seat", "gross", "net", "delta_total", "recovery", "h*", "tau (yr)",
           "half-life", "savings cap."] + [f"finish {s}" for s in SCENARIOS]
    return "\n".join([
        "## 3. Per-seat table", "",
        "`h*` is the **steady-state** health this seat converges to -- the number v1 "
        "could not produce, because v1 had no recovery term. `tau` is how long it takes "
        "to get most of the way there.", "",
        table(hdr, rows), "",
        "Finish-age cells are the median retirement age from Monte Carlo with that seat "
        "as the only working option, with the share of paths that retire before dying in "
        "parentheses. A low share means the boundary is rarely reached, not that "
        "retirement is early.", "",
        f"**The v2 result on `oldrole350`.** h*(oldrole350) = "
        f"{H.h_star(p.seat('oldrole350'), p.health):.3f} versus h*(current350) = "
        f"{H.h_star(p.seat('current350'), p.health):.3f} -- a difference of "
        f"{abs(H.h_star(p.seat('oldrole350'), p.health) - H.h_star(p.seat('current350'), p.health)):.3f}. "
        "Dropping cognitive load from 0.85 to 0.30 while raising travel from 0.20 to 0.55 "
        "is **a wash**. Under v1's scalar-stress model the old role looked like a clear "
        "improvement. It is not.", ""])


def section_indifference(run: ReportRun) -> str:
    p = run.p
    cells = N.indifference_matrix(p, run.b)
    ids = [s.id for s in p.seats]
    idx = {(c.from_id, c.to_id): c for c in cells}

    rows = []
    for a in ids:
        row = [f"`{a}`"]
        for z in ids:
            c = idx[(a, z)]
            row.append("--" if a == z else m(c.c_cut, 0))
        rows.append(row)
    consumption = table(["from \\ to"] + [f"`{i}`" for i in ids], rows)

    grows = []
    for a in ids:
        row = [f"`{a}`"]
        for z in ids:
            c = idx[(a, z)]
            row.append("--" if a == z else m(c.gross_cut, 0))
        grows.append(row)
    gross = table(["from \\ to"] + [f"`{i}`" for i in ids], grows)

    return "\n".join([
        "## 4. Indifference matrix -- the maximum acceptable pay cut", "",
        f"Solve h1*(b + ln c1) = h2*(b + ln c2) for c2, starting from c1 = "
        f"spend_base = {m(p.spend_base)}. A **positive** number is the largest permanent "
        "consumption cut worth accepting to move from the row seat to the column seat. A "
        "negative number is what you would need to be *paid* to move.", "",
        "### 4a. In permanent consumption ($/yr)", "", consumption, "",
        "### 4b. In gross income ($/yr, inverting the 2026 MFJ + FICA schedule)", "", gross, "",
        f"Read the `current350` row. Moving to `renegotiated350` is worth up to "
        f"{m(idx[('current350', 'renegotiated350')].gross_cut, 0)} of gross pay per year, "
        f"and moving to `downshift250` is worth up to "
        f"{m(idx[('current350', 'downshift250')].gross_cut, 0)} -- against an actual pay "
        f"cut of {m(350_000 - 250_000)}. ", ""])


def section_theta(run: ReportRun) -> Tuple[str, Dict]:
    p = run.p
    delta_ref = H.min_delta_total(p)
    grid: Dict[Tuple[str, float], List[N.ThetaRow]] = {}
    lam: Dict[Tuple[str, float], float] = {}
    for sc in SCENARIOS:
        for t in run.vsl_targets:
            sol = run.solution(sc, t)
            sp = shadow_prices(sol, p.W0, p.h0, p.age0)
            grid[(sc, t)] = N.theta(p, sp["Lambda_h"], sp["V_W"], delta_ref=delta_ref)
            lam[(sc, t)] = sp["Lambda_h"]

    base_rows = grid[("base", run.base_vsl)]
    stab = N.rank_stability(grid)

    rows = []
    for i, r in enumerate(base_rows):
        s = stab[r.id]
        flag = "stable" if s["stable"] else f"**{s['min_rank']}-{s['max_rank']}**"
        rows.append([f"{i + 1}", f"`{r.id}`", m(r.theta), m(r.y_net), m(r.health_cost),
                     m(r.disutility_cost), num(r.delta_total, 4), num(r.h_star, 3), flag])
    main = table(["#", "seat", "Theta ($/yr)", "net income", "health cost",
                  "disutility cost", "delta_total", "h*", "rank across 3x3"], rows)

    lrows = []
    for sc in SCENARIOS:
        lrows.append([sc] + [m(lam[(sc, t)]) for t in run.vsl_targets])
    lam_tbl = table(["scenario"] + [f"VSL {t / 1e6:.0f}M" for t in run.vsl_targets], lrows)

    dom = N.dominance(grid)
    unstable = [k for k, v in stab.items() if not v["stable"]]
    cur = "current350" if "current350" in [s.id for s in p.seats] else base_rows[0].id
    beats_cur = sorted(a for a, z in dom.items() if cur in z)
    drows = [[f"`{a}`", ", ".join(f"`{x}`" for x in dom[a]) or "--", str(len(dom[a]))]
             for a in sorted(dom, key=lambda k: -len(dom[k]))]

    return "\n".join([
        "## 5. Seat scores", "",
        "Theta(e) = y_net(e) - (Lambda_h/0.01)*(delta_total(e) - delta_ref) - phi(e)/V_W, "
        f"with delta_ref = {delta_ref:.4f} (the healthiest seat in the roster, held fixed "
        "so scores stay comparable). Everything is $/yr.", "",
        main, "",
        "### Lambda_h across the scenario x VSL grid ($ per 1 percentage point of permanent health)",
        "", lam_tbl, "",
        f"Lambda_h moves {max(lam.values()) / min(lam.values()):.1f}x across the nine "
        "combinations, so bare rank stability is close to useless as a test -- "
        + ("every seat" if len(unstable) == len(stab) else
           ", ".join(f"`{u}`" for u in unstable))
        + " moves rank somewhere. What survives is **pairwise dominance**.", "",
        "### Pairwise dominance (Theta strictly higher in all nine combinations)", "",
        table(["seat", "beats, always", "count"], drows), "",
        (f"**The robust result: {', '.join(f'`{x}`' for x in beats_cur)} beat "
         f"`{cur}` in every one of the nine scenario x VSL combinations.**"
         if beats_cur else
         f"No seat dominates `{cur}` across all nine combinations."),
        "", ]), dict(grid=grid, lam=lam, stab=stab, dom=dom)


def section_stopping(run: ReportRun, br: B.BoundaryReport) -> str:
    p = run.p
    ages = list(range(int(p.age0), 71))
    rows = []
    for a in ages:
        if (a - int(p.age0)) % 2:
            continue
        rows.append([str(a), m(br.W_star_by_age_h0.get(a, float("nan"))),
                     m(br.W_star_by_age_hstar.get(a, float("nan")))])
    return "\n".join([
        "## 6. Stopping boundary W*(t)", "",
        f"Smallest wealth at which the optimal seat is `retired`, at h = h0 = {p.h0:.2f} "
        f"and at h = h*(current350) = {br.h_current_star:.3f}. Grid resolution in W is "
        f"{100 * (np.exp(run.base.grids.dlnW) - 1):.1f}% per node, so the boundary is "
        "reported to that granularity.", "",
        table(["age", f"W* at h={p.h0:.2f}", f"W* at h={br.h_current_star:.3f}"], rows), "",
        "The boundary falls with age because retirement is absorbing: stopping at 39 "
        "forfeits sixty years of optional income, and that option is expensive. It is the "
        "option value, not the spending need, that puts W*(39) an order of magnitude above "
        "the coast numbers.", ""])


def section_mc(run: ReportRun, mcs: Dict[str, MCResult]) -> str:
    rows = []
    for label, r in mcs.items():
        s = r.summary()
        f = finish_stats(r)
        rows.append([
            f"`{label}`", pct(f["p_retire"], 0),
            "n/a" if not np.isfinite(f["median"]) else f"{f['median']:.0f}",
            "n/a" if not np.isfinite(f["p10"]) else f"{f['p10']:.0f}",
            "n/a" if not np.isfinite(f["p90"]) else f"{f['p90']:.0f}",
            m(s["terminal_W"]["p10"]), m(s["terminal_W"]["median"]), m(s["terminal_W"]["p90"]),
            num(s["terminal_h"]["p10"], 3), num(s["terminal_h"]["median"], 3),
            num(s["terminal_h"]["p90"], 3), pct(s["p_coverage_shortfall"], 2)])
    return "\n".join([
        "## 7. Monte Carlo", "",
        f"{run.p.mc_paths:,} paths, seed {run.p.mc_seed}, base scenario. Each fixed-seat "
        "policy solves the model with that seat as the only working option (retirement "
        "always remains available -- otherwise 'finish age' is undefined).", "",
        table(["policy", "P(retire)", "finish p50", "p10", "p90", "term. W p10",
               "p50", "p90", "term. h p10", "p50", "p90", "P(coverage < 0.5x)"], rows), "",
        "`P(coverage < 0.5x)` is the probability of ever consuming less than "
        f"{m(0.5 * run.p.spend_base)} in a year after retiring.", ""])


def section_tornado(run: ReportRun, bars: List[Tuple[str, List[Tuple[str, float, float]]]]) -> str:
    rows = []
    for name, legs in bars:
        span = max(v for _, v, _ in legs) - min(v for _, v, _ in legs)
        cells = [name, f"{span:.2f}"]
        cells.append(" / ".join(f"{lab}: {v:.1f}" if np.isfinite(v) else f"{lab}: n/a"
                                for lab, v, _ in legs))
        cells.append(" / ".join(f"{pr * 100:.0f}%" for _, _, pr in legs))
        rows.append(cells)
    rows.sort(key=lambda r: -float(r[1]))
    return "\n".join([
        "## 8. Sensitivity tornado", "",
        "Median finish age under the fully optimal policy, one parameter at a time from "
        "base. Sorted by span. Retirement probability is shown alongside because the "
        "median is conditional on retiring.", "",
        table(["parameter", "span (yr)", "legs (value: median finish age)", "P(retire) by leg"], rows), "",
        "**`spend_base` has a span of exactly zero, by construction.** Retirement "
        "spending is chosen by the solver; `spend_base` enters only the coverage metric, "
        "the boundary calculations and this sweep's labelling. A non-zero bar there would "
        "have meant a bug.", ""])


PROVENANCE = [
    ("age0", "years", "39.0", "observed", "end of August 2026"),
    ("W0", "2026 $", "1,850,000", "observed", "liquid only; ~900,000 home equity excluded"),
    ("h0", "index", "0.72", "assumed", "from reported perceived age ~50 at chronological 39 -- MEASURE THIS"),
    ("spend_base", "2026 $/yr", "150,000", "observed", "ex mortgage P&I; includes ~20,000 DFW property tax"),
    ("mortgage balance", "2026 $", "126,000", "observed", "3.625% nominal, ~7 yr remaining"),
    ("rho", "1/yr", "0.02", "calibrated", "from the 2010->2026 savings path; see section 1"),
    ("omega_bequest", "utils", "2.0", "assumed", "bequest weight"),
    ("b", "utils", "calibrated", "calibrated", "bisection on VSL = V/V_W at the current state"),
    ("vsl_target", "2026 $", "22,000,000", "assumed", "band 15M-30M swept in section 5"),
    ("delta0", "1/yr", "0.02", "assumed", "baseline health depreciation"),
    ("delta_cognitive", "1/yr", "0.08", "assumed", "per unit of cognitive load"),
    ("delta_travel", "1/yr", "0.10", "assumed", "per unit of nights-away fraction"),
    ("delta_autonomy", "1/yr", "0.04", "assumed", "per unit of autonomy deficit"),
    ("rho_h", "1/yr", "0.6", "assumed", "recovery rate scale; pins tau to 1.7-2.8 yr"),
    ("h_max_decay", "1/yr", "0.004", "assumed", "decline in the recoverable ceiling"),
    ("seat c_load / travel / autonomy / r", "index", "per seat", "assumed", "self-reported seat attributes -- MEASURE THESE"),
    ("phi(e)", "utils/yr", "per seat", "assumed", "direct seat disutility"),
    ("rf_real", "1/yr", "0.020", "observed", "10-year TIPS real yield, Aug 2026"),
    ("erp", "1/yr", "0.032", "assumed", "CAPE ~42 vs long-run median ~16"),
    ("sigma", "1/yr", "0.16", "observed", "long-run real equity volatility"),
    ("lambda(t)", "1/yr", "Gompertz-Makeham", "assumed", "2e-4 + 1e-3 * 2^((t-39)/8)"),
    ("kappa (mortality-health)", "-", "1.0", "assumed", "lambda_eff = lambda*(0.85/h)^kappa"),
    ("tax schedule", "-", "2026 MFJ + FICA", "observed", "standard deduction 30,000; Texas, no state tax"),
    ("SS", "2026 $/yr", "40,000 from 67", "assumed", "real benefit"),
    ("c_floor", "2026 $/yr", "15,000", "assumed", "subsistence floor on the consumption grid; see README"),
]


# Which provenance rows each tornado bar actually moves.
BAR_PARAMS = {
    "rho": ("rho",),
    "return scenario": ("rf_real", "erp", "sigma"),
    "spend_base": ("spend_base",),
    "delta_travel": ("delta_travel",),
    "rho_h": ("rho_h",),
    "omega_bequest": ("omega_bequest",),
    "h0": ("h0",),
}


def section_provenance(top_bars: Sequence[str]) -> str:
    hot = {n for bar in top_bars for n in BAR_PARAMS.get(bar, ())}
    rows = []
    flagged = []
    for name, unit, val, prov, note in PROVENANCE:
        flag = ""
        if prov == "assumed" and name in hot:
            flag = " **<- MEASUREMENT PRIORITY**"
            flagged.append(name)
        rows.append([f"`{name}`", unit, val, f"*{prov}*", note + flag])
    tail = ("\n\nNo *assumed* parameter appears in the top three tornado bars."
            if not flagged else
            "\n\n**Measurement priorities** (assumed parameters that appear in the top "
            "three tornado bars): " + ", ".join(f"`{f}`" for f in flagged) + ".")
    return "\n".join(["## 9. Parameter provenance", "",
                      table(["parameter", "units", "value", "provenance", "note"], rows)]) + tail + "\n"


def section_switching(run: ReportRun) -> str:
    """Appendix A -- the section 7 extension, only computed when enabled."""
    p = run.p
    head = ["## Appendix A. Switching costs and the inaction band", ""]
    if not p.switching_enabled:
        return "\n".join(head + [
            "Not computed: `switching_costs.enabled` is `false`. Set it to `true` in "
            f"config.yaml (kappa_W = {m(p.kappa_W)} one-off, kappa_h = {p.kappa_h:.3f} of "
            "health) to carry the previous seat in the state and measure the hysteresis "
            "region.", ""])

    free = run.base
    sw = solve_switching(p, scenario="base", b=run.b)
    rows = []
    for prev in sw.prev_seats:
        d = inaction_band(sw, free, prev.id, p.age0)
        rows.append([f"`{prev.id}`", pct(d["frac_stay"], 0),
                     pct(d["frac_frictionless_moves"], 0),
                     f"**{pct(d['frac_inaction_band'], 0)}**"])
    return "\n".join(head + [
        f"Seat changes cost {m(p.kappa_W)} once (search, relocation, forfeited variable "
        f"comp) plus a transition health hit of {p.kappa_h:.3f}. The previous seat then "
        "enters the state and the seat choice becomes a genuine optimal-stopping problem.", "",
        "The **inaction band** is the share of the (W, h) grid at age "
        f"{p.age0:.0f} where the frictionless policy would move but the frictional one "
        "stays put. It is the real-options structure that explains why rational people sit "
        "in suboptimal seats longer than a static score implies.", "",
        table(["currently in", "stays put", "frictionless would move", "inaction band"], rows), "",
        "Where the band is 0%, the static gap is too large for this friction to hold you: "
        "the move is worth making even after paying for it.", ""])


# --------------------------------------------------------------------------- #
# plots                                                                        #
# --------------------------------------------------------------------------- #

def _save(fig, path: str) -> str:
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return os.path.basename(path)


def make_plots(run: ReportRun, br: B.BoundaryReport, mcs: Dict[str, MCResult],
               bars: List[Tuple[str, List[Tuple[str, float, float]]]]) -> List[str]:
    p = run.p
    od = run.outdir
    names = []

    # 1. h* bar chart
    rows = N.seat_table(p)
    fig, ax = plt.subplots(figsize=(7.5, 4))
    ax.bar([r.id for r in rows], [r.h_star for r in rows], color="#3b6ea5")
    ax.axhline(p.h0, ls="--", c="k", lw=1, label=f"h0 = {p.h0:.2f}")
    ax.set_ylabel("steady-state health h*")
    ax.set_title("Steady-state health by seat")
    ax.tick_params(axis="x", rotation=30)
    ax.legend()
    names.append(_save(fig, os.path.join(od, "h_star_by_seat.png")))

    # 2. h trajectories
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    yrs = 30
    for s in p.seats:
        traj = H.trajectory(p.h0, s, p.health, yrs, age0=p.age0)
        ax.plot(np.arange(yrs + 1) + p.age0, traj, label=s.id)
    ax.set_xlabel("age")
    ax.set_ylabel("h")
    ax.set_title(f"Health trajectories from h0 = {p.h0:.2f}")
    ax.legend(fontsize=7)
    names.append(_save(fig, os.path.join(od, "h_trajectories.png")))

    # 3. policy heatmap
    sol = run.base
    g = sol.grids
    j = int(np.clip(round(np.interp(0.72, g.h, np.arange(g.n_h))), 0, g.n_h - 1))
    pol = sol.pol_e[:, :, j].T
    fig, ax = plt.subplots(figsize=(8, 4.5))
    im = ax.pcolormesh(g.ages[:pol.shape[1]], g.W, pol, cmap="viridis", shading="auto")
    ax.set_yscale("log")
    ax.set_xlabel("age")
    ax.set_ylabel("wealth (real $, log)")
    ax.set_title("Optimal seat e*(W, t) at h = 0.72")
    cb = fig.colorbar(im, ax=ax, ticks=range(len(sol.seats)))
    cb.ax.set_yticklabels([s.id for s in sol.seats], fontsize=7)
    names.append(_save(fig, os.path.join(od, "policy_heatmap.png")))

    # 4. c/W vs age
    r = mcs["optimal"]
    fig, ax = plt.subplots(figsize=(7.5, 4))
    med = np.nanmedian(r.c_over_W, axis=1)
    ax.plot(r.ages[:len(med)], med, lw=2)
    ax.set_xlabel("age")
    ax.set_ylabel("c / W (median across paths)")
    ax.set_title("Consumption rate under the optimal policy")
    names.append(_save(fig, os.path.join(od, "c_over_W.png")))

    # 5. wealth fan
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    W = np.where(r.alive, r.W_path, np.nan)
    for lo, hi, al in ((10, 90, 0.18), (25, 75, 0.28)):
        ax.fill_between(r.ages, np.nanpercentile(W, lo, axis=1),
                        np.nanpercentile(W, hi, axis=1), alpha=al, color="#3b6ea5")
    ax.plot(r.ages, np.nanmedian(W, axis=1), c="#16324f", lw=2, label="median")
    ax.axhline(br.W_star_now, ls=":", c="crimson", lw=1.2, label="W*(39)")
    ax.set_yscale("log")
    ax.set_xlabel("age")
    ax.set_ylabel("wealth (real $, log)")
    ax.set_title("Wealth fan under the optimal policy (survivors)")
    ax.legend(fontsize=8)
    names.append(_save(fig, os.path.join(od, "wealth_fan.png")))

    # 6. W*(t)
    fig, ax = plt.subplots(figsize=(7.5, 4))
    ages = sorted(br.W_star_by_age_h0)
    ax.plot(ages, [br.W_star_by_age_h0[a] for a in ages], marker="o", ms=3,
            label=f"h = {p.h0:.2f}")
    ax.plot(ages, [br.W_star_by_age_hstar[a] for a in ages], marker="s", ms=3,
            label=f"h = {br.h_current_star:.3f}")
    ax.axhline(p.W0, ls="--", c="k", lw=1, label="current W")
    ax.set_yscale("log")
    ax.set_xlabel("age")
    ax.set_ylabel("W* (real $, log)")
    ax.set_title("Stopping boundary")
    ax.legend(fontsize=8)
    names.append(_save(fig, os.path.join(od, "stopping_boundary.png")))

    # 7. tornado
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    labs, spans = [], []
    for name, legs in bars:
        vals = [v for _, v, _ in legs if np.isfinite(v)]
        labs.append(name)
        spans.append(max(vals) - min(vals) if vals else 0.0)
    order = np.argsort(spans)
    ax.barh([labs[i] for i in order], [spans[i] for i in order], color="#a5533b")
    ax.set_xlabel("span of median finish age (years)")
    ax.set_title("Sensitivity tornado")
    names.append(_save(fig, os.path.join(od, "tornado.png")))

    return names


# --------------------------------------------------------------------------- #
# tornado computation                                                          #
# --------------------------------------------------------------------------- #

def _finish(p: Params, b: float, scenario: str = "base",
            paths: Optional[int] = None) -> Tuple[float, float]:
    sol = solve(p, scenario=scenario, b=b, check_felicity=False)
    r = simulate(sol, params=p, paths=paths or p.mc_paths, label="tornado")
    f = finish_stats(r)
    return f["median"], f["p_retire"]


def tornado(run: ReportRun) -> List[Tuple[str, List[Tuple[str, float, float]]]]:
    p, b = run.p, run.b
    hp = p.health
    paths = min(p.mc_paths, 4000)
    out: List[Tuple[str, List[Tuple[str, float, float]]]] = []

    def leg(params: Params, label: str, scenario: str = "base"):
        med, pr = _finish(params, b, scenario, paths)
        return (label, med, pr)

    out.append(("rho", [leg(p.evolve(rho=v), f"{v:.0%}") for v in (0.01, 0.02, 0.03)]))
    out.append(("return scenario", [leg(p, s, s) for s in SCENARIOS]))
    out.append(("spend_base", [leg(p.evolve(spend_base=v), f"{v / 1000:.0f}k")
                               for v in (130_000, 150_000, 170_000)]))
    out.append(("delta_travel", [leg(p.evolve(health=replace(hp, delta_travel=v)), f"{v:.2f}")
                                 for v in (0.05, 0.10, 0.20)]))
    out.append(("rho_h", [leg(p.evolve(health=replace(hp, rho_h=v)), f"{v:.1f}")
                          for v in (0.4, 0.6, 0.9)]))
    out.append(("omega_bequest", [leg(p.evolve(omega_bequest=v), f"{v:.0f}")
                                  for v in (0.0, 2.0, 5.0)]))
    # h0 shifts only the simulation's starting state, not the solved policy.
    sol = run.base
    h0_legs = []
    for v in (0.65, 0.72, 0.85):
        r = simulate(sol, params=p, paths=paths, h0=v, label="h0")
        f = finish_stats(r)
        h0_legs.append((f"{v:.2f}", f["median"], f["p_retire"]))
    out.append(("h0", h0_legs))
    return out


# --------------------------------------------------------------------------- #
# top-level                                                                    #
# --------------------------------------------------------------------------- #

def build_report(params: Params, outdir: str = "out", fast: bool = False,
                 make_figures: bool = True) -> str:
    os.makedirs(outdir, exist_ok=True)
    run = ReportRun(params, fast=fast, outdir=outdir)
    p = run.p
    run.calibrate()

    base = run.base
    fit = run.fits[run.base_vsl]
    sp = shadow_prices(base, p.W0, p.h0, p.age0)

    # -- Monte Carlo: optimal + one solve per fixed seat ------------------- #
    mcs: Dict[str, MCResult] = {"optimal": simulate(base, params=p, label="optimal")}
    finish: Dict[Tuple[str, str], Dict[str, float]] = {}
    for s in p.seats:
        if s.absorbing:
            continue
        for sc in SCENARIOS:
            sol_s = solve(p, scenario=sc, b=run.b, seats_allowed=[s.id, "retired"],
                          check_felicity=False)
            r = simulate(sol_s, params=p, paths=min(p.mc_paths, 4000), label=s.id)
            finish[(s.id, sc)] = finish_stats(r)
            if sc == "base":
                mcs[s.id] = r

    bars = tornado(run)
    b_txt, br = section_boundaries(run)
    theta_txt, theta_info = section_theta(run)
    best = theta_info["grid"][("base", run.base_vsl)][0]

    spans = sorted(((max(v for _, v, _ in legs) - min(v for _, v, _ in legs), name)
                    for name, legs in bars), reverse=True)
    top_bars = [n for _, n in spans[:3]]

    chk = felicity_check(p, build_grids(p), run.b)

    admissible_note = ""
    bad = [t for t, f in run.fits.items() if not f.admissible]
    if bad:
        admissible_note = (
            "\n> **Inadmissible VSL legs.** At vsl_target "
            + ", ".join(f"{t / 1e6:.0f}M" for t in sorted(bad))
            + " the calibrated intercept implies a subsistence consumption "
            + ", ".join(m(run.fits[t].c_sub) for t in sorted(bad))
            + "/yr, above the consumption-grid floor of "
            + m(p.numerics.c_floor)
            + "/yr. Over that range the felicity condition b + ln c > 0 fails and better "
              "health would reduce utility. Those legs are still solved and reported, "
              "but they are the *conservative bound*, not a usable calibration.\n")

    head = [
        "# LifeHJB v2 -- lifecycle report", "",
        "> **This is a decision-support model, not financial or medical advice.** It is a "
        "numerical solution to a stochastic control problem under assumptions listed in "
        "section 9. Several of those assumptions are self-reported and unmeasured.", "",
        "All figures are real (inflation-adjusted) 2026 dollars.", "",
        "## 1. Executive summary", "",
        f"- **State.** Age {p.age0:.0f}, liquid W = {m(p.W0)}, h0 = {p.h0:.2f}, "
        f"currently in `current350` (h* = {H.h_star(p.seat('current350'), p.health):.3f}, "
        f"tau = {H.tau(p.seat('current350'), p.health):.1f} yr).",
        f"- **Boundaries as multiples of W.** Walk-away "
        f"{br.W_BATNA / p.W0:.2f}x, coast-to-60 {br.W_coast[max(br.W_coast)] / p.W0:.2f}x, "
        f"stop-now {br.W_star_now / p.W0:.1f}x. The outside option is already funded "
        f"{p.W0 / br.W_BATNA:.1f}x over; stopping is {br.W_star_now / p.W0:.1f}x away.",
        f"- **Top-ranked seat: `{best.id}`** at Theta = {m(best.theta)}/yr, versus "
        f"`current350` at "
        f"{m([r for r in theta_info['grid'][('base', run.base_vsl)] if r.id == 'current350'][0].theta)}/yr. "
        f"The gap is {m(best.theta - [r for r in theta_info['grid'][('base', run.base_vsl)] if r.id == 'current350'][0].theta)}/yr "
        "of equivalent income at identical pay.",
        f"- **Lambda_h = {m(sp['Lambda_h'])} per 1 percentage point of permanent health** "
        f"(VSL {m(fit.vsl_achieved, 0)} against a {m(fit.vsl_target, 0)} target, b = "
        f"{run.b:.4f}, implied subsistence consumption {m(chk['c_sub'])}/yr).",
        f"- **The decision this model actually settles is which seat, not when to stop.** "
        f"Only {finish_stats(mcs['optimal'])['p_retire'] * 100:.0f}% of paths ever reach "
        "the stopping boundary before dying, while the spread between the best and worst "
        f"seat is {m(best.theta - theta_info['grid'][('base', run.base_vsl)][-2].theta)}/yr.",
        "", admissible_note,
        f"Calibration: savings rate {pct(run.rho_fit.savings_rate)} out of net income over "
        f"{run.rho_fit.years} years reproduces W_2026 exactly, implying rho in "
        f"[{run.rho_fit.rho_band[0]:.3f}, {run.rho_fit.rho_band[1]:.3f}]; rho = "
        f"{p.rho:.3f} is used. Under log utility that is also the optimal consumption "
        "fraction of wealth in the infinite-horizon limit.", "",
    ]

    parts = ["\n".join(head), b_txt, section_seats(run, finish),
             section_indifference(run), theta_txt, section_stopping(run, br),
             section_mc(run, mcs), section_tornado(run, bars),
             section_provenance(top_bars), section_switching(run)]

    if make_figures:
        figs = make_plots(run, br, mcs, bars)
        parts.append("## 10. Figures\n\n" + "\n".join(f"![{f}]({f})" for f in sorted(figs)) + "\n")

    text = "\n".join(parts)
    path = os.path.join(outdir, "report.md")
    with open(path, "w") as fh:
        fh.write(text)
    return path

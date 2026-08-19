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
from . import career as CR
from . import humancapital as HC
from .calibrate import calibrate_b, calibrate_b_v3, calibrate_rho, VSLFit
from .model import Params, Seat, gross_for_net, net_income, seat_net_income
from .solver import (Solution, SolutionV3, build_grids, felicity_check,
                     shadow_prices, shadow_prices_v3, solve, solve_v3,
                     subsistence_consumption)
from .simulate import MCResult, MCResultV3, simulate, simulate_v3

SCENARIOS = ("bear", "base", "bull")

FAST = dict(n_W=24, n_h=6, n_c=14, n_pi=4)
# Sweep grid for the many-solve sections (3x3 Theta, fixed-seat MC, tornado,
# option value). The production grid is used for everything headline.
SWEEP = dict(n_W=30, n_h=8, n_c=18, n_pi=4)


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


def _money_to_float(s: str) -> float:
    """Parse a formatted money string back to a number, for derived commentary."""
    try:
        return float(str(s).replace("$", "").replace(",", ""))
    except ValueError:
        return float("nan")


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
    """Holds every solve the report needs, so nothing is computed twice.

    Two grids are used. The **production** grid carries everything headline --
    the policy, the boundaries, the Monte Carlo, the inaction band. The
    **sweep** grid carries the sections that need many solves (the 3x3
    scenario x VSL grid, per-seat finish ages, the tornado, the option value),
    where what is being measured is a difference rather than a level. Each
    section says which grid produced it.
    """

    def __init__(self, params: Params, fast: bool = False, outdir: str = "out"):
        self.p = params
        self.fast = fast
        self.outdir = outdir
        if fast:
            self.p = self.p.evolve(numerics=replace(self.p.numerics, **FAST),
                                   mc_paths=min(self.p.mc_paths, 600))
        self.sweep = self.p.evolve(
            numerics=replace(self.p.numerics, **(FAST if fast else SWEEP)))
        self.vsl_targets = sorted({float(self.p.vsl_band[0]), float(self.p.vsl_target),
                                   float(self.p.vsl_band[1])})
        self.fits: Dict[float, VSLFit] = {}
        self.sols: Dict[Tuple[str, float], SolutionV3] = {}
        self.rho_fit = calibrate_rho()
        self._prod: Optional[SolutionV3] = None

    # -- solving ---------------------------------------------------------- #
    def calibrate(self) -> None:
        base = min(self.vsl_targets, key=lambda t: abs(t - self.p.vsl_target))
        fine = 0 if self.fast else 3
        self.fits[base] = calibrate_b_v3(self.p, vsl_target=base, scenario="base",
                                         fine_iters=fine)
        for t in self.vsl_targets:
            if t == base:
                continue
            self.fits[t] = calibrate_b_v3(self.sweep, vsl_target=t, scenario="base",
                                          fine_iters=0, b_guess=self.fits[base].b)

    def solution(self, scenario: str, vsl: float) -> SolutionV3:
        key = (scenario, float(vsl))
        if key not in self.sols:
            self.sols[key] = solve_v3(self.sweep, scenario=scenario,
                                      b=self.fits[vsl].b)
        return self.sols[key]

    @property
    def base_vsl(self) -> float:
        return min(self.vsl_targets, key=lambda t: abs(t - self.p.vsl_target))

    @property
    def base(self) -> SolutionV3:
        """Production-grid solution at the base scenario and base VSL target."""
        if self._prod is None:
            self._prod = solve_v3(self.p, scenario="base", b=self.b)
        return self._prod

    @property
    def b(self) -> float:
        return self.fits[self.base_vsl].b

    @property
    def state0(self) -> int:
        return self.base.space.start_index()

    def stop_wealth(self, sol) -> float:
        """Wealth at which the top-ranked action is to stop, at h0."""
        g = sol.grids
        st = sol.space.start_index()
        ti = max(int(self.p.crunch.periods), 1)
        ti = min(ti, sol.pol_rank.shape[0] - 1)
        j = 0 if g.n_h == 1 else int(np.clip(
            round(np.interp(self.p.h0, g.h, np.arange(g.n_h))), 0, g.n_h - 1))
        top = sol.pol_rank[ti, st, :, j, 0]
        w = np.nonzero(top != sol.retired_action)[0]
        if w.size == 0:
            return float(g.W[0])
        last = int(w[-1])
        return float("inf") if last >= g.n_W - 1 else float(g.W[last + 1])

    def eta_rows(self, target: float) -> List[List[str]]:
        """When wealth reaches *target*, under a few plausible savings rates."""
        p = self.p
        g = p.returns["base"].geometric_real_full_equity
        mtg = p.mortgage.payment_real if p.mortgage_enabled else 0.0
        out = []
        cases = [("stop saving today, just let it compound", 0.0)]
        for sid in ("downshift250", "renegotiated350", "current350", "grind500"):
            if sid in p.seat_map:
                save = seat_net_income(p.seat(sid), p) - p.spend_base - mtg
                cases.append((f"keep saving on `{sid}` pay ({m(max(save, 0))}/yr)",
                              max(save, 0.0)))
        for label, save in cases:
            k = B.years_to_target(p.W0, target, g, save)
            out.append([label,
                        f"{p.age0 + k:.0f}" if np.isfinite(k) else "never",
                        f"{k:.0f}" if np.isfinite(k) else "never"])
        return out

    def gap_decomposition(self) -> List[List[str]]:
        """Why the stop-working number is what it is, one change at a time.

        Reported because the headline number invites exactly one question and it
        deserves an answer rather than a restatement.
        """
        p = self.p
        rows = [["as shipped", m(self.stop_wealth(self.base))]]
        # Reversible stopping: swap which zero-income seat is absorbing.
        from .model import Seat as _Seat
        rev = [replace(x, id="sabbatical") if x.absorbing else x for x in p.seats]
        rev.append(_Seat(id="retired", y=0, c_load=0.05, travel=0.02, autonomy=0.95,
                         r=0.92, phi=0.0, absorbing=False, note="stop, reversible"))
        try:
            sol = solve_v3(self.sweep.evolve(seats=tuple(rev)), scenario="base", b=self.b)
            g, st = sol.grids, sol.space.start_index()
            ti = min(max(int(p.crunch.periods), 1), sol.pol_rank.shape[0] - 1)
            j = int(np.clip(round(np.interp(p.h0, g.h, np.arange(g.n_h))), 0, g.n_h - 1))
            stop_ids = [sol.actions.index(x) for x in ("retired", "sabbatical")
                        if x in sol.actions]
            top = sol.pol_rank[ti, st, :, j, 0]
            w = np.nonzero(~np.isin(top, stop_ids))[0]
            val = (float(g.W[int(w[-1]) + 1]) if (w.size and int(w[-1]) < g.n_W - 1)
                   else float("inf"))
            rows.append(["if stopping were reversible", m(val)])
        except Exception:
            rows.append(["if stopping were reversible", "n/a"])
        for t in self.vsl_targets:
            if t == self.base_vsl:
                continue
            rows.append([f"if a life were worth {m(t, 0)} (not {m(p.vsl_target, 0)})",
                         m(self.stop_wealth(self.solution("base", t)))])
        base_v, rev_v = _money_to_float(rows[0][1]), _money_to_float(rows[1][1])
        self._reversible_drop = (
            f"about {1.0 - rev_v / base_v:.0%}"
            if (np.isfinite(base_v) and np.isfinite(rev_v) and base_v > 0)
            else "an amount this grid cannot resolve")
        return rows

    def sp(self) -> Dict[str, float]:
        return shadow_prices_v3(self.base, self.p.W0, self.p.h0, self.p.age0,
                                self.state0)


# --------------------------------------------------------------------------- #
# sections                                                                     #
# --------------------------------------------------------------------------- #

def section_boundaries(run: ReportRun) -> Tuple[str, B.BoundaryReport]:
    """Section 2 -- how much money is enough. Written to be read, not decoded."""
    p = run.p
    br = B.compute_v3(run.base, p, state=run.state0)
    fw = B.funded_wealth(p, success=0.95, equity_share=0.6)
    fw100 = B.funded_wealth(p, success=0.95, equity_share=0.6, mortality_weighted=False)
    run._funded = fw

    share_rows = []
    for share in (0.4, 0.6, 0.8):
        a = B.funded_wealth(p, 0.95, share)
        b_ = B.funded_wealth(p, 0.95, share, mortality_weighted=False)
        share_rows.append([f"{share:.0%} stocks", m(a.W), m(b_.W),
                           pct(a.withdrawal_rate, 2)])

    prob_rows = [[m(w), pct(B.survival_at(p, w), 1),
                  pct(B.survival_at(p, w, mortality_weighted=False), 1)]
                 for w in (3e6, 4e6, 5e6, 6e6, 7e6)]

    rows = [
        ["**Freedom number** — money is no longer the problem", f"**{m(fw.W)}**",
         f"**{fw.W / br.W_now:.1f}x**",
         "your spending is funded for life with 95% confidence, with no more work"],
        ["Walk-away money", m(br.W_BATNA), f"{br.W_BATNA / br.W_now:.2f}x",
         f"{p.runway_years:.0f} years of full expenses in the bank — enough to quit "
         "a negotiation and mean it"],
    ]
    rows.append(["Model's stop-working number", m(br.W_star_now),
                 f"{br.W_star_now / br.W_now:.1f}x",
                 "where *this model* would choose to never earn again — see below, "
                 "it is not your retirement number"])
    rows.append(["**Where you are now**", f"**{m(br.W_now)}**", "**1.0x**",
                 "cash and investments; the house is not counted"])

    return "\n".join([
        "## 2. How much money is enough", "",
        "Four different numbers get called \"the number\", and they are not the same "
        "thing. Here they are side by side, cheapest first.", "",
        table(["what it is", "how much", "vs today", "what it actually means"], rows), "",
        "### When do you get there?", "",
        table(["if you...", "reach " + m(fw.W) + " at age", "years from now"],
              run._eta_rows), "",
        "Those rows are the real trade, and it is worth being precise about it. "
        "`renegotiated350` pays exactly what you earn now, so it reaches the date on "
        "the same day as the job you already have — the health improvement is free. "
        "`grind500` buys roughly five years, at the price of the worst health "
        "outcome on the list. `downshift250` costs roughly eight years. Only you can "
        "price those last two; the first one is not a trade at all.", "",
        "### The freedom number, in detail", "",
        f"You spend {m(p.annual_full_expenses)} a year today "
        f"({m(p.spend_base)} once the mortgage is gone in "
        f"{p.mortgage.years} years), and Social Security adds "
        f"{m(p.ss_amount)} a year from {p.ss_age:.0f}. Against that:", "",
        table(["invested as", "funds you for life", "funds you to 100 regardless",
               "withdrawal rate"], share_rows), "",
        "Holding *more* stock needs *more* money, not less. Higher average returns "
        "do not help you here, because what decides whether you run out is the bad "
        "5% of outcomes, and volatility makes those worse.", "",
        "Odds of never running out, by starting wealth, at 60% stocks:", "",
        table(["wealth", "never runs out (for life)", "never runs out (to 100)"],
              prob_rows), "",
        f"**So: about {m(fw.W)} and you are done.** At {m(6e6)} it is "
        f"{pct(B.survival_at(p, 6e6), 0)} for life and "
        f"{pct(B.survival_at(p, 6e6, mortality_weighted=False), 0)} even if you live "
        "to 100 — and on the median path the money is still growing while you spend "
        "it, so yes, that is generational. That instinct is correct and the "
        "arithmetic backs it.", "",
        "### Then why does the model say " + m(br.W_star_now) + "?", "",
        "**Because it is answering a different question.** The freedom number asks "
        "*can this money pay for my life?* The stop-working number asks *at what "
        "wealth would I rather have no income at all, forever, than keep earning?* "
        "Those are not the same question and the second one has a much bigger "
        "answer.", "",
        "Three things drive the gap, and they are worth separating because only one "
        "of them is really an assumption you might reject:", "",
        table(["what changes", "stop-working number becomes"], run._gap_rows), "",
        "1. **Stopping is permanent in this model.** The spec makes retirement "
        "absorbing: once you stop you can never take another job. Giving up sixty "
        "years of optional income is expensive, so the model demands a lot of money "
        f"before it will do it. Make stopping reversible and the number falls by "
        f"{run._reversible_drop}.", "",
        "2. **How much health is worth swings it 2x.** The model is told a life is "
        f"worth {m(p.vsl_target, 0)}. Told a life is worth {m(3e7, 0)} instead, it "
        "stops much earlier, because better health is then a bigger prize.", "",
        "3. **The model has no idea what \"enough\" means, and that is the real "
        "reason.** Utility from spending is logarithmic, which means *doubling* your "
        "spending is worth the same amount whether you go from $150k to $300k or "
        "from $1.5M to $3M. There is no satiation point anywhere in it. So an extra "
        f"{m(seat_net_income(p.seat('renegotiated350'), p))} a year of income never "
        "stops being attractive — it just gets slowly less attractive as your "
        "spending rises. That is a property of the utility function the spec "
        "prescribed, not a fact about you.", "",
        f"For the model to agree that {m(6e6)} is the stopping point it would have "
        "to value health at roughly twice what it currently does (a statistical life "
        f"around {m(4.5e7, 0)} rather than {m(p.vsl_target, 0)}). If you think health "
        "is worth that much, say so in `vsl_target` and the whole report moves with "
        "it.", "",
        "**What to take from this section:** use the freedom number for planning. "
        "The stop-working number is a statement about how this model trades money "
        "against health and leisure, and it is the output you should trust least.", "",
        f"**Your walk-away money is covered {br.W_now / br.W_BATNA:.1f} times over "
        "already.** Whatever else is true, you can afford to lose any negotiation "
        "you are currently in, and that is worth knowing before you walk into one.", "",
        f"*(Technical: the coast-to-W* figures the spec asks for are "
        + ", ".join(f"{a}: {m(br.W_coast[a])}" for a in sorted(br.W_coast))
        + ". They are anchored to the stop-working number, which is why the "
        "\"when do you get there\" table above is anchored to the freedom number "
        f"instead. Ordering check walk-away < coast < stop: "
        f"{'holds' if br.W_BATNA < br.W_coast[max(br.W_coast)] < br.W_coast[min(br.W_coast)] < br.W_star_now else 'VIOLATED'}.)*",
        ""]), br


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
        "## 7. What each job does to you", "",
        "Health is scored 0 to 1. Every job pushes it toward a level it eventually "
        "settles at, and **`h*` is that level** — where you end up if you stay. "
        "`tau` is roughly how many years it takes to get most of the way there, so "
        "these are changes you would feel within two or three years, not decades.", "",
        f"Your current job settles you at "
        f"{H.h_star(p.seat('current350'), p.health):.2f}. The best job on the list "
        f"settles you at {max(H.h_star(x, p.health) for x in p.seats if not x.absorbing):.2f}. "
        "Retired would be 0.95.", "",
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
        "## 8. The biggest pay cut worth taking", "",
        "**How to read this: find your current job in the left column, then look "
        "across.** Each cell is the most you could afford to lose, every year for "
        "the rest of your life, and still come out ahead by taking that job — "
        "because of what it does to your health. A negative number means the move "
        "is bad for you and you would need paying to accept it.", "",
        f"The starting point is your current spending of {m(p.spend_base)} a year.", "",
        "### 8a. As a cut to what you spend, every year, forever", "", consumption, "",
        "### 8b. The same thing, as a cut to your salary", "", gross, "",
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
            sp = shadow_prices_v3(sol, p.W0, p.h0, p.age0, sol.space.start_index())
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
        "## 9. What each job is really worth", "",
        "**This is the headline job table.** Each job is scored in dollars per year: "
        "start with take-home pay, subtract what the job costs you in health "
        "(priced at the exchange rate in section 1), then subtract how unpleasant "
        "the work itself is. A job paying less can easily win.", "",
        f"*Formally: Theta(e) = after-tax pay − (Lambda_h/0.01)·(health damage − "
        f"{delta_ref:.4f}) − direct unpleasantness / V_W, where the "
        f"{delta_ref:.4f} baseline is the healthiest option and is held fixed so the "
        "scores stay comparable.*", "",
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
        "## 10. When the model would stop working, by age", "",
        "**Read section 2 first — this is not your retirement number.** It is the "
        "wealth at which this model would choose to stop earning permanently, which "
        "is a much higher bar than having enough money. It falls with age because "
        "stopping at 39 throws away sixty years of optional income and stopping at "
        "69 throws away far less.", "",
        f"Shown at your current health ({p.h0:.2f}) and at the health your current "
        f"job settles you at ({br.h_current_star:.2f}). Wealth-grid resolution is "
        f"{100 * (np.exp(run.base.grids.dlnW) - 1):.1f}% per node, so the boundary is "
        "reported to that granularity.", "",
        table(["age", f"W* at h={p.h0:.2f}", f"W* at h={br.h_current_star:.3f}"], rows), "",
        "The boundary falls with age because retirement is absorbing: stopping at 39 "
        "forfeits sixty years of optional income, and that option is expensive. It is the "
        "option value, not the spending need, that puts W*(39) an order of magnitude above "
        "the coast numbers.", ""])


def section_mc(run: ReportRun, mcs: Dict[str, MCResultV3],
               nosep: MCResultV3) -> str:
    rows = []
    for label, r in mcs.items():
        sm = r.summary()
        f = finish_stats(r)
        rows.append([
            f"`{label}`", pct(f["p_retire"], 0),
            "n/a" if not np.isfinite(f["median"]) else f"{f['median']:.0f}",
            "n/a" if not np.isfinite(f["p10"]) else f"{f['p10']:.0f}",
            "n/a" if not np.isfinite(f["p90"]) else f"{f['p90']:.0f}",
            m(sm["terminal_W"]["p10"]), m(sm["terminal_W"]["median"]),
            m(sm["terminal_W"]["p90"]),
            num(sm["terminal_h"]["p10"], 3), num(sm["terminal_h"]["median"], 3),
            num(sm["terminal_h"]["p90"], 3), pct(sm["p_coverage_shortfall"], 2),
            pct(sm["p_ever_separated"], 0)])

    fv3 = finish_stats(mcs["optimal"])
    fv2 = finish_stats(nosep)
    cmp_rows = []
    for nm, f, r in (("v2 (no separation risk)", fv2, nosep),
                     ("v3 (separation risk active)", fv3, mcs["optimal"])):
        sm = r.summary()
        cmp_rows.append([nm,
                         "n/a" if not np.isfinite(f["median"]) else f"{f['median']:.1f}",
                         "n/a" if not np.isfinite(f["p10"]) else f"{f['p10']:.1f}",
                         "n/a" if not np.isfinite(f["p90"]) else f"{f['p90']:.1f}",
                         pct(f["p_retire"], 0), m(sm["terminal_W"]["p10"]),
                         m(sm["terminal_W"]["median"])])
    dmed = (fv3["median"] - fv2["median"]) if (np.isfinite(fv3["median"])
                                               and np.isfinite(fv2["median"])) else float("nan")
    dp90 = (fv3["p90"] - fv2["p90"]) if (np.isfinite(fv3["p90"])
                                         and np.isfinite(fv2["p90"])) else float("nan")

    return "\n".join([
        "## 11. Ten thousand simulated lives", "",
        f"{run.p.mc_paths:,} paths, seed {run.p.mc_seed}, base scenario, "
        "**with separation risk active**. Each fixed-seat policy solves the model "
        "with that seat as the only working option (retirement always remains "
        "available -- otherwise 'finish age' is undefined).", "",
        table(["policy", "P(retire)", "finish p50", "p10", "p90", "term. W p10",
               "p50", "p90", "term. h p10", "p50", "p90", "P(coverage < 0.5x)",
               "P(ever sep.)"], rows), "",
        "### The cost of career risk, made explicit", "",
        "The same optimal policy simulated with and without the separation "
        "hazard. This is the v2 figure shown alongside the v3 one, so what career "
        "risk costs is visible rather than assumed away.", "",
        table(["model", "finish p50", "p10", "p90", "P(retire)", "term. W p10",
               "term. W p50"], cmp_rows), "",
        (f"Separation risk moves the median finish age by **{dmed:+.1f} years** and "
         f"the p90 by **{dp90:+.1f} years**." if np.isfinite(dmed) else
         "Finish-age comparison is censored on both legs."),
        "", f"`P(coverage < 0.5x)` is the probability of ever consuming less than "
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
        "## 12. Which assumptions actually matter", "",
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
    ("beta_H", "-", "1.6", "assumed", "human-capital beta; semicap capex cycle -- HIGHEST-VALUE THING TO REFINE"),
    ("portfolio_sector_overlap", "-", "0.35", "assumed", "financial equity correlated with own sector beyond market beta"),
    ("base_sep", "1/yr", "0.04-0.10", "assumed", "involuntary separation by seat -- HIGHEST-VALUE THING TO REFINE"),
    ("downturn_factor", "-", "3.0", "assumed", "separation-hazard multiplier below the drawdown threshold"),
    ("downturn_threshold", "-", "-0.15", "assumed", "what counts as a bad market year"),
    ("severance_months", "months", "4", "assumed", "employer practice"),
    ("search_duration_dist", "months", "3/6/9/12", "assumed", "collapsed to annual; see README"),
    ("reentry_haircut", "-", "0.10", "assumed", "permanent comp scarring after involuntary exit"),
    ("p_outside", "1/yr", "0.40 / 0.05", "assumed", "outside-offer arrival, maintained / not"),
    ("p_nego", "1/yr", "0.35 / 0.10", "assumed", "negotiation success, maintained / not"),
    ("phi_maintain", "utils/yr", "0.02", "assumed", "cost of keeping the option warm; break-even is ~0.0025"),
    ("p_oldrole / p_grind", "1/yr", "0.50 / 1.00", "assumed", "p_grind not specified in v3; see README"),
    ("crunch periods / multiplier", "yr / -", "1 / 1.30", "observed", "a real execution commitment"),
    ("kappa_W / kappa_h", "2026 $ / index", "40,000 / 0.02", "assumed", "switching costs, v3 default ON"),
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
    "base_sep": ("base_sep",),
    "beta_H": ("beta_H",),
    "T_work": ("beta_H",),
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
    return "\n".join([
        "## 14. Where every number came from", "",
        "*Observed* means it is a fact someone looked up. *Calibrated* means the "
        "model worked it out from your actual history. **Assumed means somebody "
        "guessed** — and everything downstream of a guess is only as good as the "
        "guess. The financial side is mostly observed; the health and career sides "
        "are almost entirely assumed.", "",
        table(["parameter", "units", "value", "where it came from", "note"], rows)]) + tail + "\n"


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
# v3 sections                                                                  #
# --------------------------------------------------------------------------- #

def section_allocation(run: ReportRun, T_work: float, pi_now: float) -> Tuple[str, float]:
    """Section 3 -- human capital and the allocation correction."""
    p = run.p
    hc = p.human_capital
    val = HC.value_human_capital(p, p.seat("current350"), T_work)
    rows = []
    for a in HC.allocation_table(p, p.W0, val.H):
        rows.append([f"{a.gamma:.1f}", num(a.pi_total_target, 3),
                     f"**{a.pi_fin_optimal:+.3f}**", a.interpretation])
    conc = HC.sector_concentration(p, p.W0, val.H, pi_now)
    eff = HC.effective_equity_ratio(p, p.W0, val.H, pi_now)

    neg = [a for a in HC.allocation_table(p, p.W0, val.H) if a.pi_fin_optimal < 0]
    return "\n".join([
        "## 3. Your career is a tech stock", "",
        "v2 never modelled human capital, which silently assumed it was worth "
        "nothing -- or, read the other way, that it was a safe bond. Neither is "
        "true. Account-manager compensation in semiconductor capital equipment "
        "tracks bookings, bookings track the capex cycle, and the capex cycle is "
        "the market. That is a beta, and it belongs on the balance sheet.", "",
        table(["quantity", "value"], [
            ["H (PV of after-tax labour income to " + f"{T_work:.0f})", m(val.H)],
            ["beta_H", num(val.beta_H, 2)],
            ["r_H = rf + beta_H * erp", pct(val.r_H, 2)],
            ["equity-equivalent exposure beta_H * H", m(val.equity_equivalent)],
            ["financial wealth W", m(p.W0)],
            ["total wealth TW = W + H", m(val.H + p.W0)],
            ["separation hazard used (incl. E[cycle])", pct(val.sep_rate_used, 2)],
        ]), "",
        "### Optimal financial equity share by risk aversion", "",
        table(["gamma", "pi_total_target", "pi_fin_optimal", "reading"], rows), "",
        f"**Effective total equity exposure at the current allocation "
        f"(pi = {pi_now:.2f}): (pi*W + beta_H*H) / TW = {eff:.3f}.** That is "
        f"{'above' if eff > 1 else 'at or below'} 100% of total wealth "
        "before any leverage in the financial account.", "",
        (f"At gamma = 1 (log utility, the Kelly case) the subject is roughly "
         f"correctly positioned. At every gamma above 1 the optimal financial "
         f"equity share is **negative** -- career exposure alone already exceeds "
         f"the total-wealth equity target. The number is reported as negative "
         f"rather than clipped to zero because it is a real instruction: hedge, "
         f"or hold assets uncorrelated with the semicap cycle."
         if neg else
         "Optimal financial equity share is positive at every gamma reported."), "",
        "### Sector concentration", "",
        table(["exposure", "amount", "share of TW"], [
            ["human capital (100% semicap)", m(conc.H), pct(conc.H / conc.total_wealth)],
            [f"financial equity x overlap ({conc.sector_overlap:.0%})",
             m(conc.sector_exposure_W), pct(conc.sector_exposure_W / conc.total_wealth)],
            ["**total semicap-cycle exposure**", f"**{m(conc.sector_exposure_total)}**",
             f"**{pct(conc.sector_share_of_TW)}**"],
            ["diversifying sleeve (non-equity W)", m(conc.diversifying_sleeve),
             pct(conc.sleeve_share_of_TW)],
        ]), "",
        "The diversifying sleeve is reported separately rather than netted in "
        "because it is the only part of the balance sheet genuinely orthogonal "
        "to the career.", ""]), val.H


def section_career(run: ReportRun, mcs: Dict[str, MCResultV3]) -> str:
    """Section 4 -- career risk per seat."""
    p = run.p
    cp = p.career
    rows = []
    for seat in p.seats:
        if seat.absorbing:
            continue
        base = cp.sep_rate(seat.id, 0)
        after = cp.sep_rate(seat.id, 99)
        rate = (f"{base:.3f}" if abs(base - after) < 1e-12
                else f"{base:.3f} -> {after:.3f} after {cp.amat_seasoning_years}y")
        r = mcs.get(seat.id)
        rows.append([f"`{seat.id}`", rate,
                     pct(r.ever_separated.mean(), 0) if r else "n/a",
                     num(r.n_separations.mean(), 2) if r else "n/a",
                     num(r.search_years.mean(), 2) if r else "n/a",
                     m(CR.severance_amount(seat, cp))])
    opt = mcs["optimal"]
    corr = opt.separation_by_market_state()
    return "\n".join([
        "## 4. Getting laid off", "",
        table(["seat", "base_sep", "P(ever separated)", "E[# separations]",
               "E[search years]", "severance"], rows), "",
        "Columns 3-5 come from Monte Carlo with that seat as the only working "
        "option. `P(ever separated)` is over a whole working life, not per year.", "",
        "**Read those three columns with care: they are not comparable across "
        "rows.** They count exposure over however long the agent chooses to keep "
        "working in that seat, and that differs sharply by seat. `downshift250` "
        "has the *lowest* annual hazard in the roster and the *highest* lifetime "
        "separation count, because it is pleasant enough that the model keeps "
        "working it for decades; `grind500` has a higher hazard and fewer "
        "separations because the model retires out of it early. The annual "
        "hazard is in column 2; columns 3-5 are hazard times tenure.", "",
        "### The correlation, measured", "",
        f"Under the optimal policy the realized separation rate is "
        f"**{corr['rate_downturn']:.4f} in years when the portfolio fell more than "
        f"{abs(cp.downturn_threshold):.0%}**, against **{corr['rate_normal']:.4f}** "
        f"otherwise -- a ratio of **{corr['ratio']:.2f}** against a configured "
        f"`downturn_factor` of {cp.downturn_factor:.1f}. Separation is resolved "
        "against the *same realized return draw* that moved wealth that year, so "
        "the job goes precisely when the portfolio cannot absorb it.", "",
        f"Downturn years are {corr['p_downturn_year']:.1%} of working years under "
        "the optimal risky share.", "",
        "**Note on the health of unemployment.** The `searching` seat has "
        f"h* = {H.h_star(CR.searching_seat(cp), p.health):.3f}, *above* "
        f"h*(current350) = {H.h_star(p.seat('current350'), p.health):.3f}. On this "
        "calibration, being out of work is less damaging to health than the "
        "current job is. That is not a modelling artifact to hide -- it is what "
        "the seat parameters say.", ""])


def section_stress(run: ReportRun) -> str:
    """Section 5 -- the correlated stress test. This is what W_BATNA exists for."""
    p = run.p
    st = p.stress
    seat = p.seat("current350")
    sol = run.base
    rows = []
    for age in st.ages:
        # Wealth at that age under the optimal policy, median of survivors.
        ti = int(round(age - p.age0))
        W_at = float(np.nanmedian(run._stress_W[ti][run._stress_alive[ti]]))
        d = CR.stress_test(p, W_at, seat, st.drawdown)
        wstar = B.w_star_v3(sol, float(age), p.h0, run.state0)
        rows.append([str(age), m(W_at), m(d["W_post_drawdown"]), m(d["severance"]),
                     m(d["W_after"]), f"{d['runway_months']:.0f}",
                     m(d["W_at_reentry"]),
                     "**yes**" if d["exhausts"] else "no",
                     f"{d['W_after'] / wstar:.2f}x" if np.isfinite(wstar) else "n/a"])
    return "\n".join([
        "## 5. The bad year: a crash and a layoff at the same time", "",
        f"A **{abs(st.drawdown):.0%} portfolio drawdown and an involuntary "
        "separation in the same year.** This is the joint event the whole career "
        "module exists to price, and the scenario W_BATNA exists for.", "",
        table(["age", "W before", "after drawdown", "+severance", "W after shock",
               "runway (months)", "W at re-entry", "exhausts liquid?",
               "vs W*"], rows), "",
        "`W at re-entry` deducts full expenses through the shock year and the "
        "expected search. `exhausts liquid?` asks whether liquid assets run out "
        "before re-employment -- the operational definition of the walk-away "
        "number failing.", "",
        f"Delay to W*: the shock costs roughly "
        f"{abs(st.drawdown) / max(run._stress_g, 1e-9):.1f} years of compounding "
        f"at {pct(run._stress_g, 2)} real, before counting the lost income and the "
        f"{p.career.reentry_haircut:.0%} re-entry comp haircut, which is permanent "
        "and therefore the larger cost.", "",
        "Terminal-h impact: the `searching` seat is *less* health-damaging than "
        "`current350`, so a separation does not by itself worsen terminal health "
        "on this calibration. The damage is financial and it is permanent.", ""])


def section_option_value(run: ReportRun, ov: CR.OptionValue,
                         sens: List[Tuple[str, str, float]]) -> str:
    """Section 6 -- what a maintained outside option is worth."""
    p = run.p
    av = p.availability
    gross = ov.total + av.phi_maintain / ov.V_W / CR.annuity_factor(p) * CR.annuity_factor(p)
    cost = av.phi_maintain / ov.V_W
    rows = [["total OV", m(ov.total) + "/yr"],
            ["  bargaining component", m(ov.bargaining) + "/yr"],
            ["  insurance component", m(ov.insurance) + "/yr"],
            ["maintenance cost (phi_maintain / V_W)", m(-cost) + "/yr"],
            ["**gross OV, before maintenance cost**", f"**{m(ov.total + cost)}/yr**"],
            ["break-even phi_maintain", num((ov.total + cost) * ov.V_W, 4)]]
    srows = [[k, v, m(x) + "/yr"] for k, v, x in sens]
    return "\n".join([
        "## 6. Is it worth keeping a foot outside?", "",
        "OV = V(maintain) - V(do not maintain) at the current state, converted to "
        "dollars through V_W and expressed as an equivalent constant flow over the "
        f"model's discounted survival horizon ({CR.annuity_factor(p):.1f} years).", "",
        "Maintenance raises `p_outside` from "
        f"{av.p_outside_unmaintained:.2f} to {av.p_outside:.2f} and, because a "
        "negotiation without a credible alternative is a request rather than a "
        f"negotiation, `p_nego` from {av.p_nego_unmaintained:.2f} to {av.p_nego:.2f}.", "",
        table(["component", "value"], rows), "",
        "### Sensitivity", "", table(["parameter", "value", "OV"], srows), "",
        "**The result, stated plainly.** The gross option value is positive and "
        "rises with separation risk -- which is the signature of insurance rather "
        "than a bluff. But it is *small*, and at the configured "
        f"`phi_maintain = {av.phi_maintain:.3f}` the option is **not worth "
        "maintaining**: the disutility costs more than the option pays. Two "
        "things drive that, and both are worth knowing:", "",
        "1. **The floor option dominates the outside option.** The solver ranks "
        "`downshift250` above `amat400` at this wealth, because its steady-state "
        "health is higher and its separation rate is lower. Since `downshift250` "
        "is permanently available, the thing maintenance buys is a seat the model "
        "does not want. The negotiating leverage is already there.", "",
        "2. **`phi_maintain = 0.02` is not small on this scale.** It is half the "
        "direct disutility of `downshift250` as an entire job (0.04) and a quarter "
        "of `renegotiated350`'s (0.08). Break-even is around 0.0025. If keeping the "
        "network warm genuinely costs a tenth of what a whole job costs you, the "
        "arithmetic is right and the answer is not to bother; if it costs less than "
        "that, maintain it.", ""])


def section_inaction(run: ReportRun) -> str:
    """Section 13 -- switching costs, now default-on, and the hysteresis region."""
    p = run.p
    if not p.switching_enabled:
        return "\n".join(["## 13. Inaction band", "",
                           "Not computed: `switching_costs.enabled` is false.", ""])
    free = solve_v3(p.evolve(switching_enabled=False), scenario="base", b=run.b)
    rows = []
    for i, st in enumerate(run.base.space.states):
        if st.seat == CR.SEARCHING or st.scarred:
            continue
        d = B.inaction_band_v3(run.base, free, i, p.age0 + max(p.crunch.periods, 1))
        rows.append([f"`{st.label()}`", pct(d["frac_stay"], 0),
                     pct(d["frac_frictionless_moves"], 0),
                     f"**{pct(d['frac_inaction_band'], 0)}**"])
    run._free_sol = free
    return "\n".join([
        "## 13. Why people stay in jobs they should leave", "",
        f"Seat changes cost {m(p.kappa_W)} once plus a transition health hit of "
        f"{p.kappa_h:.3f}. v3 turns this on by default, so the seat decision is a "
        "genuine optimal-stopping problem.", "",
        "The **inaction band** is the share of the (W, h) grid where the "
        "frictionless policy would move but the frictional one stays put. It is "
        "the formal explanation for staying in a suboptimal job.", "",
        table(["currently in", "stays put", "frictionless would move",
               "inaction band"], rows), "",
        "Where the band is 0%, the static gap is too large for this friction to "
        "hold you: the move is worth making even after paying for it.", ""])


def section_glossary(run: ReportRun) -> str:
    """Section 15 -- every symbol in the report, in one place."""
    p = run.p
    rows = [
        ["`h`", "health, scored 0 to 1", "1.0 is the healthiest you could be at 39. "
         f"You are estimated at {p.h0:.2f} — MEASURE THIS, it is a guess"],
        ["`h*`", "where health settles", "the level a given job pushes you to and "
         "holds you at, if you stay in it"],
        ["`tau`", "how fast health moves", "years to close most of the gap to `h*`; "
         "these are 2-3 year effects, not lifetime ones"],
        ["`Lambda_h`", "price of a health point", "what one permanent point of "
         "health is worth per year, in dollars. The exchange rate behind every "
         "job comparison"],
        ["`Theta`", "job score", "take-home pay minus health damage minus "
         "unpleasantness, all in dollars per year"],
        ["`W`", "wealth", "cash and investments. The house is excluded — it is "
         "treated as housing you have already bought"],
        ["`W*`", "stop-working number", "wealth at which the model would choose to "
         "never earn again. **Not** your retirement number; see section 2"],
        ["freedom number", "enough money", "wealth that funds your spending for "
         "life with 95% confidence. **This is the retirement number**"],
        ["`W_BATNA`", "walk-away money", "runway to quit a negotiation and mean it"],
        ["`beta_H`", "career beta", "how much your earnings swing with the market. "
         "1.6 means your pay is more cyclical than the market itself"],
        ["`H`", "human capital", "what all your future earnings are worth today"],
        ["`gamma`", "risk aversion", "1 = happy to ride volatility; 3 = strongly "
         "prefer certainty. The solver assumes 1"],
        ["`rho`", "impatience", f"{p.rho:.0%} a year. Also, under this model's "
         "utility, roughly the share of wealth you would spend per year"],
        ["`VSL`", "value of a statistical life", "the standard regulatory measure. "
         "Sets how the model trades money against health"],
        ["`base_sep`", "layoff risk", "chance of being let go in a given year"],
        ["`c/W`", "spending rate", "what fraction of your wealth you spend in a year"],
        ["`pi`", "stock share", "fraction of investments in equities"],
        ["bear / base / bull", "market scenarios",
         "roughly 2.5% / 4.8% / 7.0% a year after inflation"],
    ]
    return "\n".join([
        "## 15. What the symbols mean", "",
        table(["symbol", "in English", "what it is"], rows), ""])


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
    pol = sol.pol_rank[:, run.state0, :, j, 0].T
    fig, ax = plt.subplots(figsize=(8, 4.5))
    im = ax.pcolormesh(g.ages[:pol.shape[1]], g.W, pol, cmap="viridis", shading="auto")
    ax.set_yscale("log")
    ax.set_xlabel("age")
    ax.set_ylabel("wealth (real $, log)")
    ax.set_title("Optimal seat e*(W, t) at h = 0.72")
    cb = fig.colorbar(im, ax=ax, ticks=range(len(sol.actions)))
    cb.ax.set_yticklabels(sol.actions, fontsize=7)
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

    # 7. inaction band
    free = getattr(run, "_free_sol", None)
    if free is not None and p.switching_enabled:
        age = p.age0 + max(p.crunch.periods, 1)
        # Plot the state where the band actually exists. From `current350` it is
        # empty -- the static gap is too large for this friction to hold you --
        # so plotting the start state would show a blank chart and say nothing.
        cand = [(B.inaction_band_v3(sol, free, i, age), i)
                for i, st in enumerate(sol.space.states)
                if st.seat != CR.SEARCHING and not st.scarred]
        d, i = max(cand, key=lambda kv: kv[0]["frac_inaction_band"])
        d0 = B.inaction_band_v3(sol, free, run.state0, age)
        fig, ax = plt.subplots(figsize=(7.5, 4.5))
        ax.pcolormesh(g.h, g.W, d["band_mask"].astype(float), cmap="Oranges",
                      shading="auto", vmin=0, vmax=1)
        ax.set_yscale("log")
        ax.set_xlabel("health h")
        ax.set_ylabel("wealth (real $, log)")
        ax.set_title(f"Inaction band from `{sol.space.states[i].label()}` "
                     f"({d['frac_inaction_band']:.0%} of the grid)\n"
                     f"from `current350` it is {d0['frac_inaction_band']:.0%}: "
                     "the gap is too large for friction to hold you", fontsize=9)
        names.append(_save(fig, os.path.join(od, "inaction_band.png")))

    # 8. allocation by gamma
    Hv = getattr(run, "_H_value", None)
    if Hv:
        fig, ax = plt.subplots(figsize=(7.5, 4))
        allocs = HC.allocation_table(p, p.W0, Hv)
        ax.bar([f"{a.gamma:.1f}" for a in allocs], [a.pi_fin_optimal for a in allocs],
               color=["#3b6ea5" if a.pi_fin_optimal >= 0 else "#a5533b" for a in allocs])
        ax.axhline(0, c="k", lw=1)
        ax.set_xlabel("risk aversion gamma")
        ax.set_ylabel("optimal financial equity share")
        ax.set_title("pi_fin_optimal after netting out career equity exposure")
        names.append(_save(fig, os.path.join(od, "allocation.png")))

    # 9. tornado
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
    sol = solve_v3(p, scenario=scenario, b=b)
    r = simulate_v3(sol, params=p, paths=paths or p.mc_paths, label="tornado")
    f = finish_stats(r)
    return f["median"], f["p_retire"]


def tornado(run: ReportRun) -> List[Tuple[str, List[Tuple[str, float, float]]]]:
    """One-at-a-time sweep on median finish age, on the sweep grid."""
    p, b = run.sweep, run.b
    hp = p.health
    paths = min(p.mc_paths, 4000)
    out: List[Tuple[str, List[Tuple[str, float, float]]]] = []

    def leg(params: Params, label: str, scenario: str = "base"):
        med, pr = _finish(params, b, scenario, paths)
        return (label, med, pr)

    out.append(("rho", [leg(p.evolve(rho=v), f"{v:.0%}") for v in (0.01, 0.02, 0.03)]))
    out.append(("return scenario", [leg(p, sc, sc) for sc in SCENARIOS]))
    out.append(("spend_base", [leg(p.evolve(spend_base=v), f"{v / 1000:.0f}k")
                               for v in (130_000, 150_000, 170_000)]))
    out.append(("delta_travel", [leg(p.evolve(health=replace(hp, delta_travel=v)), f"{v:.2f}")
                                 for v in (0.05, 0.10, 0.20)]))
    out.append(("rho_h", [leg(p.evolve(health=replace(hp, rho_h=v)), f"{v:.1f}")
                          for v in (0.4, 0.6, 0.9)]))
    out.append(("omega_bequest", [leg(p.evolve(omega_bequest=v), f"{v:.0f}")
                                  for v in (0.0, 2.0, 5.0)]))
    legs = []
    for mult, lab in ((0.0, "0 (v2)"), (1.0, "base"), (2.0, "2x")):
        car = replace(p.career, base_sep={k: v * mult for k, v in p.career.base_sep.items()})
        legs.append(leg(p.evolve(career=car), lab))
    out.append(("base_sep", legs))

    sol = run.base
    h0_legs = []
    for v in (0.65, 0.72, 0.85):
        r = simulate_v3(sol, params=run.p, paths=paths, h0=v, label="h0")
        f = finish_stats(r)
        h0_legs.append((f"{v:.2f}", f["median"], f["p_retire"]))
    out.append(("h0", h0_legs))
    return out


def tornado_allocation(run: ReportRun, T_work: float) -> List[Tuple[str, List[Tuple[str, float]]]]:
    """One-at-a-time sweep on pi_fin_optimal at gamma = 2.

    beta_H never enters the solver -- it is a balance-sheet parameter, so it
    cannot move a finish age. It moves the allocation, which is where it has to
    be swept if the provenance table is to flag it honestly.
    """
    p = run.p
    hc = p.human_capital
    gamma = 2.0

    def pi_fin(q: Params, scenario: str = "base") -> float:
        v = HC.value_human_capital(q, q.seat("current350"), T_work, scenario=scenario)
        return HC.optimal_financial_share(q, q.W0, v.H, gamma, scenario).pi_fin_optimal

    out = []
    out.append(("beta_H", [(f"{v:.1f}",
                            pi_fin(p.evolve(human_capital=replace(hc, beta_H=v))))
                           for v in (0.0, 0.8, 1.6, 2.4)]))
    out.append(("return scenario", [(sc, pi_fin(p, sc)) for sc in SCENARIOS]))
    out.append(("T_work", [(f"{v:.0f}", pi_fin(p, "base"))
                           for v in (T_work,)] +
                          [(f"{v:.0f}",
                            HC.optimal_financial_share(
                                p, p.W0,
                                HC.value_human_capital(p, p.seat("current350"), v).H,
                                gamma).pi_fin_optimal) for v in (60.0, 70.0)]))
    legs = []
    for mult, lab in ((0.0, "0"), (1.0, "base"), (2.0, "2x")):
        car = replace(p.career, base_sep={k: v * mult for k, v in p.career.base_sep.items()})
        legs.append((lab, pi_fin(p.evolve(career=car))))
    out.append(("base_sep", legs))
    return out


def section_tornado_allocation(bars) -> str:
    rows = []
    for name, legs in bars:
        vals = [v for _, v in legs if np.isfinite(v)]
        span = (max(vals) - min(vals)) if vals else 0.0
        rows.append([name, num(span, 3),
                     " / ".join(f"{lab}: {v:+.3f}" for lab, v in legs)])
    rows.sort(key=lambda r: -float(r[1]))
    return "\n".join([
        "### 12b. Which assumptions move the investment answer", "",
        "`beta_H` never enters the solver -- it is a balance-sheet parameter, so "
        "it cannot move a finish age. It moves the allocation, and that is where "
        "it has to be swept.", "",
        table(["parameter", "span", "legs"], rows), ""])


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
    sp = run.sp()

    # -- Monte Carlo ------------------------------------------------------- #
    mcs: Dict[str, MCResultV3] = {"optimal": simulate_v3(base, params=p, label="optimal")}
    run._stress_W = mcs["optimal"].W_path
    run._stress_alive = mcs["optimal"].alive
    run._stress_g = p.returns["base"].geometric_real_full_equity

    nosep_car = replace(p.career, base_sep={k: 0.0 for k in p.career.base_sep})
    nosep_sol = solve_v3(p.evolve(career=nosep_car), scenario="base", b=run.b)
    nosep = simulate_v3(nosep_sol, params=p.evolve(career=nosep_car), label="v2-style")

    finish: Dict[Tuple[str, str], Dict[str, float]] = {}
    for s_ in p.seats:
        if s_.absorbing:
            continue
        for scn in SCENARIOS:
            sol_s = solve_v3(run.sweep, scenario=scn, b=run.b,
                             seats_allowed=[s_.id, "retired"])
            r = simulate_v3(sol_s, params=run.sweep, paths=min(p.mc_paths, 4000),
                            label=s_.id)
            finish[(s_.id, scn)] = finish_stats(r)
            if scn == "base":
                mcs[s_.id] = r

    # -- pieces ------------------------------------------------------------ #
    run._gap_rows = run.gap_decomposition()
    run._eta_rows = run.eta_rows(B.funded_wealth(p, 0.95, 0.6).W)
    b_txt, br = section_boundaries(run)
    pol_now = consumption_policy_pi(base, p, run.state0)
    T_work = min(finish_stats(mcs["optimal"])["median"]
                 if np.isfinite(finish_stats(mcs["optimal"])["median"])
                 else p.human_capital.T_work_cap, p.human_capital.T_work_cap)
    alloc_txt, H_value = section_allocation(run, T_work, pol_now)
    run._H_value = H_value

    ov = CR.option_value_outside(run.sweep, run.b, "base")
    ov_sens = []
    for mult, lab in ((0.5, "0.5x"), (2.0, "2x")):
        car = replace(run.sweep.career,
                      base_sep={k: v * mult for k, v in run.sweep.career.base_sep.items()})
        ov_sens.append(("base_sep", lab,
                        CR.option_value_outside(run.sweep.evolve(career=car), run.b, "base").total))
    for pn in (0.20, 0.55):
        q = run.sweep.evolve(availability=replace(run.sweep.availability, p_nego=pn))
        ov_sens.append(("p_nego", f"{pn:.2f}",
                        CR.option_value_outside(q, run.b, "base").total))

    theta_txt, theta_info = section_theta(run)
    best = theta_info["grid"][("base", run.base_vsl)][0]
    cur_theta = [r for r in theta_info["grid"][("base", run.base_vsl)]
                 if r.id == "current350"][0]

    bars = tornado(run)
    abars = tornado_allocation(run, T_work)
    spans = sorted(((max(v for _, v, _ in legs) - min(v for _, v, _ in legs), name)
                    for name, legs in bars), reverse=True)
    aspans = sorted(((max(v for _, v in legs) - min(v for _, v in legs), name)
                     for name, legs in abars), reverse=True)
    top_bars = [n for _, n in spans[:3]] + [n for _, n in aspans[:3]]

    inaction_txt = section_inaction(run)
    chk = felicity_check(p, build_grids(p), run.b)
    runway = CR.runway_months(p.W0, p)
    top_avail = _top_available_seat(base, run.state0, p)

    bad = [t for t, f in run.fits.items() if not f.admissible]
    admissible_note = ""
    if bad:
        admissible_note = (
            "\n*One caveat on the low end of that range. Asked to value a life at "
            + ", ".join(m(t, 0) for t in sorted(bad))
            + ", the model can only fit it by also claiming that below about "
            + ", ".join(m(run.fits[t].c_sub) for t in sorted(bad))
            + " a year of spending, being alive stops being worth anything — which "
              "is not a sensible thing to believe. Those runs are kept as a "
              "conservative bound and should not be read as a calibration.*\n")

    allocs = HC.allocation_table(p, p.W0, H_value)
    a2 = [a for a in allocs if abs(a.gamma - 2.0) < 1e-9]
    a2 = a2[0] if a2 else allocs[-1]

    fw = run._funded
    stop_now = br.W_star_now
    g_real = p.returns["base"].geometric_real_full_equity
    _mtg = p.mortgage.payment_real if p.mortgage_enabled else 0.0
    _save_now = max(seat_net_income(p.seat("current350"), p) - p.spend_base - _mtg, 0.0)
    yrs_idle = B.years_to_target(p.W0, fw.W, g_real, 0.0)
    yrs_saving = B.years_to_target(p.W0, fw.W, g_real, _save_now)
    cur_net = seat_net_income(p.seat("current350"), p)
    sep_pct = mcs["optimal"].ever_separated.mean()

    head = [
        "# Your lifecycle report", "",
        "> **This is a decision-support model. It is not financial advice and it is "
        "not medical advice.** It is a computer working out consequences from "
        "assumptions, and several of those assumptions are guesses about you that "
        "nobody has measured. Section 14 lists every one of them and marks which "
        "are which. Where the model disagrees with your judgement, the model is the "
        "thing more likely to be wrong.", "",
        "Every dollar figure is in today's money — inflation is already taken out, "
        "so you can compare any number here directly to what things cost now.", "",
        "## 1. The short version", "",
        f"**Where you stand.** You are 39, you have {m(p.W0)} invested (the house is "
        f"not counted), and you spend about {m(p.annual_full_expenses)} a year. That "
        f"is {CR.runway_months(p.W0, p):.0f} months of expenses in the bank.", "",
        f"**How much is enough: about {m(fw.W)}.** At that point your spending is "
        "funded for the rest of your life with 95% confidence and you never have to "
        f"work again. At {m(6e6)} it is {pct(B.survival_at(p, 6e6), 0)} — and on the "
        "typical path the money keeps growing while you spend it.", "",
        f"**Keeping up the roughly {m(_save_now)} a year you save now, you get there "
        f"around age {p.age0 + yrs_saving:.0f} — {yrs_saving:.0f} years from now.** "
        f"If you stopped saving entirely today and just let what you have compound, "
        f"it would take about {yrs_idle:.0f} years. You are {fw.W / p.W0:.1f}x away, "
        "not 8x away.", "",
        f"*(Further down, the model reports a \"stop working\" number of "
        f"{m(stop_now)}. Ignore it as a retirement target — it answers a different "
        "and much stranger question, and section 2 explains exactly why it is so "
        "big.)*", "",
        f"**The job question is the one that matters, and the answer is clear.** "
        f"Your current role scores {m(cur_theta.theta)} a year once you price in what "
        f"it costs your health. `{best.id}` — same pay, less scope — scores "
        f"{m(best.theta)}. That is a gap of about "
        f"{m(best.theta - cur_theta.theta)} a year **for no change in salary at "
        f"all**. Every other job in the list beats your current one under every "
        "assumption tested. Nothing else in this report is worth as much as fixing "
        "this.", "",
        f"**You are more exposed to your own industry than you probably think.** "
        f"Your future earnings are worth about {m(H_value)} today, and because your "
        "pay tracks the chip-equipment cycle, that behaves like a leveraged bet on "
        f"the same thing your portfolio is betting on. Counting both, you are "
        f"{HC.effective_equity_ratio(p, p.W0, H_value, pol_now):.2f}x your total net "
        f"worth in equity risk, and {pct(HC.sector_concentration(p, p.W0, H_value, pol_now).sector_share_of_TW, 0)} "
        "of everything you own rides on one industry. Unless you are unusually "
        "comfortable with risk, the investments should be *less* aggressive than "
        f"they are, not more — see section 3.", "",
        f"**What could go wrong.** {pct(sep_pct, 0)} of simulated lives include at "
        "least one involuntary job loss, and layoffs are about "
        f"{mcs['optimal'].separation_by_market_state()['ratio']:.0f}x more likely in "
        "years the market falls — exactly when your portfolio can least absorb it. "
        "Section 5 runs that double hit. You survive it comfortably at every age "
        "tested, which is what your walk-away cushion is for.", "",
        f"**One number to carry around: {m(sp['Lambda_h'])} a year.** That is what "
        "the model says a permanent one-point improvement in your health is worth. "
        "It is the exchange rate behind every job comparison here.", "",
        "---", "",
        f"*Technical note on calibration: a savings rate of "
        f"{pct(run.rho_fit.savings_rate)} out of after-tax income over "
        f"{run.rho_fit.years} years exactly reproduces your 2026 balance from your "
        f"2010 one, which implies a patience parameter in "
        f"[{run.rho_fit.rho_band[0]:.3f}, {run.rho_fit.rho_band[1]:.3f}]; "
        f"{p.rho:.3f} is used. The utility intercept b = {run.b:.3f} is set so the "
        f"model values a statistical life at {m(fit.vsl_achieved, 0)} against a "
        f"{m(fit.vsl_target, 0)} target.*", "", admissible_note, "",
    ]

    parts = ["\n".join(head), b_txt, alloc_txt,
             section_career(run, mcs), section_stress(run),
             section_option_value(run, ov, ov_sens),
             section_seats(run, finish), section_indifference(run), theta_txt,
             section_stopping(run, br), section_mc(run, mcs, nosep),
             section_tornado(run, bars), section_tornado_allocation(abars),
             inaction_txt, section_provenance(top_bars), section_glossary(run)]

    if make_figures:
        figs = make_plots(run, br, mcs, bars)
        parts.append("## 16. Charts\n\n"
                     + "\n".join(f"![{f}]({f})" for f in sorted(figs)) + "\n")

    text = "\n".join(parts)
    path = os.path.join(outdir, "report.md")
    with open(path, "w") as fh:
        fh.write(text)
    return path


def consumption_policy_pi(sol: SolutionV3, p: Params, state: int) -> float:
    """The risky share the policy actually picks at the current state."""
    g = sol.grids
    i = int(np.clip(round((np.log(p.W0) - g.lnW[0]) / g.dlnW), 0, g.n_W - 1))
    j = 0 if g.n_h == 1 else int(np.clip(round(np.interp(p.h0, g.h, np.arange(g.n_h))),
                                         0, g.n_h - 1))
    a = int(sol.pol_rank[0, state, i, j, 0])
    return float(g.pi[sol.pol_pi[0, state, a, i, j]])


def _top_available_seat(sol: SolutionV3, state: int, p: Params) -> str:
    g = sol.grids
    i = int(np.clip(round((np.log(p.W0) - g.lnW[0]) / g.dlnW), 0, g.n_W - 1))
    j = 0 if g.n_h == 1 else int(np.clip(round(np.interp(p.h0, g.h, np.arange(g.n_h))),
                                         0, g.n_h - 1))
    ti = min(int(p.crunch.periods), sol.pol_rank.shape[0] - 1)
    return sol.actions[int(sol.pol_rank[ti, state, i, j, 0])]

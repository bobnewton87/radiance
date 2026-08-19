"""Command line: solve | calibrate | boundaries | negotiate | report | test."""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Optional

import numpy as np

from . import boundaries as B
from . import health as H
from . import negotiate as N
from . import career as CR
from . import humancapital as HC
from .calibrate import calibrate_b_v3, calibrate_rho
from .model import Params, load_params
from .report import build_report, m
from .simulate import simulate_v3
from .solver import shadow_prices_v3, solve_v3


def _params(args) -> Params:
    p = load_params(args.config)
    if getattr(args, "scenario", None):
        p = p.evolve(scenario=args.scenario)
    if getattr(args, "b", None) is not None:
        p = p.evolve(b=args.b)
    return p


def _ensure_b(p: Params, args) -> float:
    if p.b is not None:
        return p.b
    fit = calibrate_b_v3(p, scenario=p.scenario)
    if not args.quiet:
        print(f"calibrated b = {fit.b:.4f}  (VSL {fit.vsl_achieved:,.0f} vs target "
              f"{fit.vsl_target:,.0f}, {fit.rel_error * 100:.2f}% error)", file=sys.stderr)
    return fit.b


def cmd_calibrate(args) -> int:
    p = _params(args)
    rf = calibrate_rho()
    print("== rho from savings history ==")
    print(f"  savings rate out of net : {rf.savings_rate:.4f}")
    print(f"  real portfolio return   : {rf.real_return:.4f}")
    print(f"  real gross income growth: {rf.gross_growth_real:.4f}")
    print(f"  W {rf.W_start_real:,.0f} -> {rf.W_end_model:,.0f} (target {rf.W_end_real:,.0f})")
    print(f"  implied rho band        : [{rf.rho_band[0]:.3f}, {rf.rho_band[1]:.3f}]")
    print(f"  rho in use              : {p.rho:.3f}")
    print(f"  note: {rf.note}")
    print()
    print("== b from VSL target ==")
    for t in sorted({p.vsl_band[0], p.vsl_target, p.vsl_band[1]}):
        fit = calibrate_b_v3(p, vsl_target=float(t))
        flag = "" if fit.admissible else "   [INADMISSIBLE: c_sub above grid floor]"
        print(f"  target {t/1e6:5.1f}M -> b = {fit.b:8.4f}  VSL {fit.vsl_achieved:,.0f} "
              f"({fit.rel_error*100:.2f}%)  Lambda_h {fit.Lambda_h:,.0f}  "
              f"c_sub {fit.c_sub:,.0f}{flag}")
    return 0


def cmd_solve(args) -> int:
    p = _params(args)
    b = _ensure_b(p, args)
    sol = solve_v3(p, b=b)
    st = sol.space.start_index()
    sp = shadow_prices_v3(sol, p.W0, p.h0, p.age0, st)
    print(f"scenario={sol.scenario}  b={b:.4f}  career states={sol.space.n}")
    print(f"V={sp['V']:.4f}  V_W={sp['V_W']:.6e}  V_h={sp['V_h']:.4f}")
    print(f"VSL={sp['VSL']:,.0f}  Lambda_h={sp['Lambda_h']:,.0f} per 1pp of h")
    g = sol.grids
    j = int(np.clip(round(np.interp(p.h0, g.h, np.arange(g.n_h))), 0, g.n_h - 1))
    i = int(np.clip(round((np.log(p.W0) - g.lnW[0]) / g.dlnW), 0, g.n_W - 1))
    for ti, lab in ((0, "now (crunch lockout)" if p.crunch.periods else "now"),
                    (max(int(p.crunch.periods), 1), "after lockout")):
        rank = sol.pol_rank[ti, st, i, j]
        a = int(rank[0])
        print(f"  {lab:22s} seat={sol.actions[a]:<16s} "
              f"c/resources={g.c_frac[sol.pol_c[ti, st, a, i, j]]:.4f}  "
              f"pi={g.pi[sol.pol_pi[ti, st, a, i, j]]:.2f}   "
              f"order: {' > '.join(sol.actions[int(x)] for x in rank[:3])}")
    return 0


def cmd_allocate(args) -> int:
    """Human capital and the allocation correction."""
    p = _params(args)
    T_work = float(p.human_capital.T_work_cap)
    v = HC.value_human_capital(p, p.seat(args.seat), T_work)
    print(f"H({args.seat}) = {v.H:>15,.0f}   r_H={v.r_H:.4f}  beta_H={v.beta_H:.2f}  "
          f"horizon={v.years} yr")
    print(f"equity-equivalent exposure beta_H*H = {v.equity_equivalent:>15,.0f}")
    print(f"financial wealth W                  = {p.W0:>15,.0f}")
    print(f"total wealth TW                     = {p.W0 + v.H:>15,.0f}\n")
    print(f"{'gamma':>7}{'pi_total':>11}{'pi_fin_opt':>13}   reading")
    for a in HC.allocation_table(p, p.W0, v.H):
        print(f"{a.gamma:>7.1f}{a.pi_total_target:>11.3f}{a.pi_fin_optimal:>13.3f}   "
              f"{a.interpretation}")
    for pi in (float(args.pi),):
        print(f"\neffective total equity exposure at pi={pi:.2f}: "
              f"{HC.effective_equity_ratio(p, p.W0, v.H, pi):.3f}x total wealth")
        c = HC.sector_concentration(p, p.W0, v.H, pi)
        print(f"semicap-cycle exposure across W and H: {c.sector_exposure_total:,.0f} "
              f"({c.sector_share_of_TW:.1%} of TW); "
              f"diversifying sleeve {c.diversifying_sleeve:,.0f}")
    return 0


def cmd_career(args) -> int:
    """Separation risk, runway, and the correlated stress test."""
    p = _params(args)
    print(f"runway = {CR.runway_months(p.W0, p):.0f} months of full expenses "
          f"({m(p.annual_full_expenses)}/yr)\n")
    print("== separation risk by seat ==")
    for s in p.seats:
        if s.absorbing:
            continue
        base, after = p.career.sep_rate(s.id, 0), p.career.sep_rate(s.id, 99)
        rate = f"{base:.3f}" if abs(base - after) < 1e-12 else f"{base:.3f}->{after:.3f}"
        print(f"  {s.id:<17}{rate:>14}   severance {CR.severance_amount(s, p.career):>10,.0f}")
    print(f"\n== stress test: {p.stress.drawdown:+.0%} drawdown AND separation ==")
    seat = p.seat(args.seat)
    print(f"{'age':>5}{'W before':>14}{'W after shock':>15}{'runway mo':>11}"
          f"{'W at re-entry':>15}{'exhausts':>10}")
    for age in p.stress.ages:
        W = p.W0 * (1 + p.returns[p.scenario].geometric_real_full_equity) ** (age - p.age0)
        d = CR.stress_test(p, W, seat, p.stress.drawdown)
        print(f"{age:>5}{W:>14,.0f}{d['W_after']:>15,.0f}{d['runway_months']:>11.0f}"
              f"{d['W_at_reentry']:>15,.0f}{'YES' if d['exhausts'] else 'no':>10}")
    return 0


def cmd_option(args) -> int:
    """The dollar value of maintaining an outside option."""
    p = _params(args)
    b = _ensure_b(p, args)
    ov = CR.option_value_outside(p, b, p.scenario)
    cost = p.availability.phi_maintain / ov.V_W
    print(f"OV_outside          = {ov.total:>12,.0f} /yr")
    print(f"  bargaining        = {ov.bargaining:>12,.0f} /yr")
    print(f"  insurance         = {ov.insurance:>12,.0f} /yr")
    print(f"maintenance cost    = {-cost:>12,.0f} /yr  (phi_maintain={p.availability.phi_maintain:.3f})")
    print(f"gross OV            = {ov.total + cost:>12,.0f} /yr")
    print(f"break-even phi      = {(ov.total + cost) * ov.V_W:>12.4f}")
    return 0


def cmd_boundaries(args) -> int:
    p = _params(args)
    sol = solve_v3(p, b=_ensure_b(p, args))
    br = B.compute_v3(sol, p, state=sol.space.start_index())
    print(f"W today                : {br.W_now:>15,.0f}")
    print(f"W_BATNA ({br.runway_years:.0f} yr runway): {br.W_BATNA:>15,.0f}   "
          f"{br.W_BATNA / br.W_now:.2f}x")
    for a in sorted(br.W_coast):
        print(f"W_coast({a})            : {br.W_coast[a]:>15,.0f}   {br.W_coast[a]/br.W_now:.2f}x")
    print(f"W* (age {p.age0:.0f}, h={p.h0:.2f})    : {br.W_star_now:>15,.0f}   "
          f"{br.W_star_now / br.W_now:.2f}x")
    print()
    print("W*(t):    age      h=h0          h=h*(current350)")
    for a in sorted(br.W_star_by_age_h0):
        if (a - int(p.age0)) % 5:
            continue
        print(f"          {a:3d}  {br.W_star_by_age_h0[a]:>15,.0f}  {br.W_star_by_age_hstar[a]:>15,.0f}")
    return 0


def cmd_negotiate(args) -> int:
    p = _params(args)
    b = _ensure_b(p, args)
    sol = solve_v3(p, b=b)
    sp = shadow_prices_v3(sol, p.W0, p.h0, p.age0, sol.space.start_index())
    print(f"Lambda_h = {sp['Lambda_h']:,.0f} per 1pp of permanent health\n")

    print("== per-seat ==")
    print(f"{'seat':<17}{'gross':>10}{'net':>10}{'delta':>9}{'rec':>7}{'h*':>8}"
          f"{'tau':>7}{'half':>7}{'save cap':>11}")
    for r in N.seat_table(p):
        print(f"{r.id:<17}{r.y:>10,.0f}{r.y_net:>10,.0f}{r.delta_total:>9.4f}"
              f"{r.recovery:>7.3f}{r.h_star:>8.3f}{r.tau:>7.2f}{r.half_life:>7.2f}"
              f"{r.savings_capacity:>11,.0f}")

    print("\n== seat scores Theta ($/yr) ==")
    for i, r in enumerate(N.theta(p, sp["Lambda_h"], sp["V_W"])):
        print(f"{i+1:>2}. {r.id:<17}{r.theta:>12,.0f}   "
              f"(net {r.y_net:,.0f} - health {r.health_cost:,.0f} - phi {r.disutility_cost:,.0f})")

    print(f"\n== max acceptable pay cut from `{args.seat}` (gross $/yr) ==")
    for c in N.indifference_matrix(p, b):
        if c.from_id == args.seat and c.to_id != args.seat:
            print(f"   -> {c.to_id:<17} h* {c.h_from:.3f} -> {c.h_to:.3f}   "
                  f"cut up to {c.gross_cut:>12,.0f}")

    print("\n== break-even extra depreciation for a raise ==")
    base = p.seat(args.seat).y if args.seat in p.seat_map else 350_000
    for be in N.break_even_delta(p, sp["Lambda_h"], base, [25_000, 50_000, 100_000, 150_000]):
        print(f"   +{be.delta_y_gross:>8,.0f} gross (+{be.delta_y_net:>8,.0f} net) -> "
              f"d_delta {be.delta_delta:.4f}  = +{be.equiv_travel:.3f} travel "
              f"or +{be.equiv_c_load:.3f} cognitive load")
    return 0


def cmd_report(args) -> int:
    path = build_report(_params(args), outdir=args.out, fast=args.fast,
                        make_figures=not args.no_figures)
    print(path)
    return 0


def cmd_test(args) -> int:
    import subprocess
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return subprocess.call([sys.executable, "-m", "pytest", "-q", os.path.join(root, "tests")])


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="lifehjb", description=__doc__)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--scenario", choices=["bear", "base", "bull"], default=None)
    ap.add_argument("--b", type=float, default=None, help="override the felicity intercept")
    ap.add_argument("--quiet", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("solve").set_defaults(func=cmd_solve)
    sub.add_parser("calibrate").set_defaults(func=cmd_calibrate)
    sub.add_parser("boundaries").set_defaults(func=cmd_boundaries)

    ng = sub.add_parser("negotiate")
    ng.add_argument("--seat", default="current350")
    ng.set_defaults(func=cmd_negotiate)

    rp = sub.add_parser("report")
    rp.add_argument("--out", default="out")
    rp.add_argument("--fast", action="store_true", help="coarse grids, small MC")
    rp.add_argument("--no-figures", action="store_true")
    rp.set_defaults(func=cmd_report)

    al = sub.add_parser("allocate")
    al.add_argument("--seat", default="current350")
    al.add_argument("--pi", type=float, default=1.0, help="current financial risky share")
    al.set_defaults(func=cmd_allocate)

    cr = sub.add_parser("career")
    cr.add_argument("--seat", default="current350")
    cr.set_defaults(func=cmd_career)

    sub.add_parser("option").set_defaults(func=cmd_option)

    sub.add_parser("test").set_defaults(func=cmd_test)
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)

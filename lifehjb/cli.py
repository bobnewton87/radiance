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
from .calibrate import calibrate_b, calibrate_rho
from .model import Params, load_params
from .report import build_report, m
from .simulate import simulate
from .solver import shadow_prices, solve


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
    fit = calibrate_b(p, scenario=p.scenario)
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
        fit = calibrate_b(p, vsl_target=float(t))
        flag = "" if fit.admissible else "   [INADMISSIBLE: c_sub above grid floor]"
        print(f"  target {t/1e6:5.1f}M -> b = {fit.b:8.4f}  VSL {fit.vsl_achieved:,.0f} "
              f"({fit.rel_error*100:.2f}%)  Lambda_h {fit.Lambda_h:,.0f}  "
              f"c_sub {fit.c_sub:,.0f}{flag}")
    return 0


def cmd_solve(args) -> int:
    p = _params(args)
    b = _ensure_b(p, args)
    sol = solve(p, b=b)
    sp = shadow_prices(sol, p.W0, p.h0, p.age0)
    print(f"scenario={sol.scenario}  b={b:.4f}")
    print(f"V={sp['V']:.4f}  V_W={sp['V_W']:.6e}  V_h={sp['V_h']:.4f}")
    print(f"VSL={sp['VSL']:,.0f}  Lambda_h={sp['Lambda_h']:,.0f} per 1pp of h")
    g = sol.grids
    j = int(np.clip(round(np.interp(p.h0, g.h, np.arange(g.n_h))), 0, g.n_h - 1))
    i = int(np.clip(round((np.log(p.W0) - g.lnW[0]) / g.dlnW), 0, g.n_W - 1))
    seat = sol.seats[int(sol.pol_e[0, i, j])]
    print(f"optimal seat at (W0, h0, age0): {seat.id}  "
          f"c/resources={g.c_frac[sol.pol_c[0, i, j]]:.4f}  pi={g.pi[sol.pol_pi[0, i, j]]:.2f}")
    return 0


def cmd_boundaries(args) -> int:
    p = _params(args)
    sol = solve(p, b=_ensure_b(p, args))
    br = B.compute(sol, p)
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
    sol = solve(p, b=b)
    sp = shadow_prices(sol, p.W0, p.h0, p.age0)
    print(f"Lambda_h = {sp['Lambda_h']:,.0f} per 1pp of permanent health\n")

    print("== per-seat ==")
    print(f"{'seat':<17}{'gross':>10}{'net':>10}{'delta':>9}{'rec':>7}{'h*':>8}"
          f"{'tau':>7}{'half':>7}{'save cap':>11}")
    for r in N.seat_table(p):
        print(f"{r.id:<17}{r.y:>10,.0f}{r.y_net:>10,.0f}{r.delta_total:>9.4f}"
              f"{r.recovery:>7.3f}{r.h_star:>8.3f}{r.tau:>7.2f}{r.half_life:>7.2f}"
              f"{r.savings_capacity:>11,.0f}")

    print("\n== seat scores Theta ($/yr) ==")
    for i, r in enumerate(N.theta_from_solution(sol, p)):
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

    sub.add_parser("test").set_defaults(func=cmd_test)
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)

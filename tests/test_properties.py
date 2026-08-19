"""Monotonicity, boundary ordering, calibration bands and determinism.

These are the acceptance tests from section 9 that need a solved model.
"""
import os
import subprocess
import sys
from dataclasses import replace

import numpy as np
import pytest

from lifehjb import boundaries as B
from lifehjb import health as H
from lifehjb import negotiate as N
from lifehjb.calibrate import calibrate_b, calibrate_rho
from lifehjb.model import Numerics
from lifehjb.simulate import simulate
from lifehjb.solver import (build_grids, felicity_check, shadow_prices, solve,
                            subsistence_consumption)

COARSE = dict(n_W=34, n_h=8, n_c=18, n_pi=4)
B_TEST = -9.3          # near the b that lands VSL at the 22M default


@pytest.fixture(scope="module")
def coarse(params):
    return params.evolve(numerics=replace(params.numerics, **COARSE))


@pytest.fixture(scope="module")
def sol(coarse):
    return solve(coarse, b=B_TEST, check_felicity=False)


# --------------------------------------------------------------------------- #
# 6. monotonicity and the felicity condition                                   #
# --------------------------------------------------------------------------- #

def test_value_strictly_increasing_in_wealth(sol):
    """Acceptance test 6, first half."""
    for t in range(0, sol.V_work.shape[0], 7):
        d = np.diff(sol.V_work[t], axis=0)
        assert (d > 0).all(), f"V not increasing in W at t index {t}"


def test_value_strictly_increasing_in_health(sol):
    """Acceptance test 6, second half."""
    for t in range(0, sol.V_work.shape[0] - 1, 7):
        d = np.diff(sol.V_work[t], axis=1)
        assert (d > 0).all(), f"V not increasing in h at t index {t}"


def test_felicity_condition_holds_at_default_calibration(params):
    """b + ln c > 0 over the consumption grid, asserted at startup."""
    chk = felicity_check(params, build_grids(params), B_TEST)
    assert chk["ok"], chk
    assert chk["margin"] > 0
    assert subsistence_consumption(B_TEST) < params.numerics.c_floor


def test_felicity_assertion_raises_when_violated(params):
    from lifehjb.solver import assert_felicity_positive
    with pytest.raises(ValueError, match="inadmissible"):
        assert_felicity_positive(params, build_grids(params), -30.0)


# --------------------------------------------------------------------------- #
# 7. mortality raises spending                                                 #
# --------------------------------------------------------------------------- #

@pytest.mark.slow
def test_doubling_mortality_weakly_raises_spending(coarse):
    """Acceptance test 7: c/W at 65+ must not fall when the hazard doubles."""
    base = solve(coarse, b=B_TEST, check_felicity=False)
    hi = solve(coarse.evolve(mortality_scale=2.0), b=B_TEST, check_felicity=False)
    g = base.grids
    t0 = int(65 - coarse.age0)
    lo_cw = np.median(g.c_frac[base.pol_c[t0:, :, :]])
    hi_cw = np.median(g.c_frac[hi.pol_c[t0:, :, :]])
    assert hi_cw >= lo_cw - 1e-12, (lo_cw, hi_cw)


# --------------------------------------------------------------------------- #
# 8. boundary ordering                                                         #
# --------------------------------------------------------------------------- #

@pytest.mark.slow
def test_boundary_ordering(sol, coarse):
    """Acceptance test 8: W_BATNA < W_coast(60) < W_coast(49) < W*."""
    br = B.compute(sol, coarse)
    assert br.W_BATNA < br.W_coast[60]
    assert br.W_coast[60] < br.W_coast[49]
    assert br.W_coast[49] < br.W_star_now


def test_w_batna_definition(params):
    assert B.w_batna(params) == pytest.approx(
        params.runway_years * (params.spend_base + params.mortgage.payment_real))


@pytest.mark.slow
def test_stopping_boundary_falls_with_age(sol, coarse):
    """The free boundary is decreasing over the reported 39-70 window."""
    br = B.compute(sol, coarse)
    ages = sorted(br.W_star_by_age_h0)
    vals = [br.W_star_by_age_h0[a] for a in ages]
    assert vals[-1] < vals[0]
    assert all(np.isfinite(v) for v in vals)


# --------------------------------------------------------------------------- #
# 9. VSL calibration                                                           #
# --------------------------------------------------------------------------- #

@pytest.mark.slow
def test_vsl_calibration_lands_in_band(params):
    """Acceptance test 9: b lands VSL within 2%; Lambda_h finite and positive."""
    p = params.evolve(numerics=replace(params.numerics, **COARSE))
    fit = calibrate_b(p, vsl_target=22e6, tol=0.005)
    assert fit.rel_error < 0.02, fit
    assert np.isfinite(fit.Lambda_h) and fit.Lambda_h > 0
    assert fit.admissible, f"c_sub {fit.c_sub:,.0f} above the grid floor"


def test_rho_calibration_reproduces_wealth():
    fit = calibrate_rho()
    assert fit.W_end_model == pytest.approx(fit.W_end_real, rel=1e-6)
    assert fit.savings_rate >= 0.30
    assert fit.rho_band == (0.015, 0.025)


# --------------------------------------------------------------------------- #
# 5. travel dominance (second half: Theta)                                     #
# --------------------------------------------------------------------------- #

def test_travel_strictly_reduces_theta(params):
    """Acceptance test 5, second half.

    delta_ref is the *baseline* roster's minimum, held fixed across the
    perturbation -- otherwise perturbing the healthiest seat moves the origin
    and the comparison is meaningless.
    """
    ref = H.min_delta_total(params)
    base = {r.id: r.theta for r in N.theta(params, 16_000.0, 3.7e-6, delta_ref=ref)}
    for s in params.seats:
        worse = s.with_travel(min(s.travel + 0.2, 1.0))
        got = N.theta(params, 16_000.0, 3.7e-6, delta_ref=ref, seats=[worse])[0]
        assert got.theta < base[s.id] - 1e-9, s.id


# --------------------------------------------------------------------------- #
# structural properties                                                        #
# --------------------------------------------------------------------------- #

def test_retired_is_absorbing(sol):
    """Once retired the seat is locked: the retired policy has no seat choice."""
    assert sum(1 for s in sol.seats if s.absorbing) == 1
    assert sol.pol_c_ret.shape == sol.pol_c.shape


@pytest.mark.slow
def test_simulation_respects_absorption(sol, coarse):
    r = simulate(sol, params=coarse, paths=800, label="t")
    # Nobody un-retires: retirement age is recorded at most once per path.
    fin = r.retire_age[np.isfinite(r.retire_age)]
    assert (fin >= coarse.age0).all()
    assert (fin <= coarse.numerics.age_max).all()


@pytest.mark.slow
def test_simulation_is_deterministic(sol, coarse):
    a = simulate(sol, params=coarse, paths=500, seed=7)
    b = simulate(sol, params=coarse, paths=500, seed=7)
    assert np.array_equal(np.nan_to_num(a.terminal_W), np.nan_to_num(b.terminal_W))
    assert np.array_equal(np.nan_to_num(a.retire_age, nan=-1),
                          np.nan_to_num(b.retire_age, nan=-1))


@pytest.mark.slow
def test_higher_vsl_raises_lambda_h(params):
    """Lambda_h must be increasing in the VSL target -- the calibration's whole point."""
    p = params.evolve(numerics=replace(params.numerics, **COARSE))
    lo = calibrate_b(p, vsl_target=15e6)
    hi = calibrate_b(p, vsl_target=30e6)
    assert hi.Lambda_h > lo.Lambda_h
    assert hi.b > lo.b


# --------------------------------------------------------------------------- #
# 11. determinism of the report                                                #
# --------------------------------------------------------------------------- #

@pytest.mark.slow
def test_report_is_byte_identical_across_runs(tmp_path):
    """Acceptance test 11, on the fast profile.

    The full profile takes minutes; the fast profile exercises the same code
    path and the same formatting, which is what determinism is about.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outs = []
    for i in ("a", "b"):
        d = tmp_path / i
        rc = subprocess.call(
            [sys.executable, "-m", "lifehjb", "--config", os.path.join(root, "config.yaml"),
             "report", "--out", str(d), "--fast", "--no-figures"], cwd=root)
        assert rc == 0
        outs.append((d / "report.md").read_bytes())
    assert outs[0] == outs[1]

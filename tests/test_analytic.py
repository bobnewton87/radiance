"""Closed-form recoveries. These are what say the solver is a solver.

Both tests strip the model down to a case with a known answer and check that
backward induction reproduces it.
"""
from dataclasses import replace

import numpy as np
import pytest

from lifehjb.model import Numerics, ReturnScenario, Seat, params_from_dict
from lifehjb.solver import build_grids, solve

RETIRED_ONLY = [dict(id="retired", y=0, c_load=0.0, travel=0.0, autonomy=1.0,
                     r=0.0, phi=0.0, absorbing=True)]


def _bare(**kw):
    """No labour, no tax, no mortgage, no mortality, no health, no bequest."""
    cfg = dict(
        age0=0.0, W0=1_000_000.0, h0=1.0, spend_base=0.0,
        mortgage={"balance": 0.0, "rate_nominal": 0.0, "years": 0},
        rho=0.02, omega_bequest=0.0, seats=RETIRED_ONLY,
        ss={"enabled": False}, mortality_health_coupled=False,
    )
    p = params_from_dict(cfg)
    return p.evolve(health_enabled=False, labor_enabled=False, taxes_enabled=False,
                    mortgage_enabled=False, mortality_enabled=False, **kw)


@pytest.mark.slow
def test_merton_recovery():
    """Acceptance test 1: interior pi* -> erp/sigma^2, c/W -> rho.

    The production pi grid has six nodes, far too coarse to resolve 0.48, so the
    test refines it -- grid resolution is numerics, not economics.
    """
    erp, sigma, rho = 0.03, 0.25, 0.02
    p = _bare(
        returns={"base": ReturnScenario(rf_real=0.0, erp=erp, sigma=sigma)},
        scenario="base", rho=rho,
        numerics=Numerics(n_W=40, W_min=50_000.0, W_max=30_000_000.0, n_h=1,
                          n_c=60, c_frac_min=0.002, c_frac_max=0.95, c_floor=0.0,
                          n_pi=51, n_gh=7, age_max=200.0),
    )
    sol = solve(p, b=20.0)
    g = sol.grids
    mid = slice(g.n_W // 4, 3 * g.n_W // 4)          # interior wealth only

    pi_star = g.pi[sol.pol_pi[0, mid, 0]]
    assert np.allclose(pi_star, erp / sigma ** 2, atol=0.07), pi_star

    c_over_W = g.c_frac[sol.pol_c[0, mid, 0]]         # resources == W here
    assert np.allclose(c_over_W, rho, rtol=0.15), c_over_W


@pytest.mark.slow
@pytest.mark.parametrize("N", [10, 30])
@pytest.mark.parametrize("rho", [0.0, 0.02])
def test_annuity_consumption(N, rho):
    """Acceptance test 2: with sigma = 0, pi = 0 and rf = rho, consumption is the
    exact annuity draw.

    The spec states the target as ``c_t/W_t = 1/(remaining periods)``. That is
    the *zero-rate* case. With rf = rho = r > 0 the Euler equation gives
    beta*R = 1, so consumption is constant in level and the exact draw is the
    annuity factor ``(1 - 1/R) / (1 - R^-n)``, which collapses to 1/n as r -> 0.
    Both readings are checked: rho = 0 reproduces 1/n on the nose.
    """
    p = _bare(
        returns={"base": ReturnScenario(rf_real=rho, erp=0.0, sigma=0.0)},
        scenario="base", rho=rho,
        numerics=Numerics(n_W=30, W_min=50_000.0, W_max=30_000_000.0, n_h=1,
                          n_c=300, c_frac_min=0.01, c_frac_max=0.999, c_floor=0.0,
                          n_pi=1, pi_max=0.0, n_gh=1, age_max=float(N)),
    )
    sol = solve(p, b=20.0)
    g = sol.grids
    mid = slice(g.n_W // 4, 3 * g.n_W // 4)
    R = np.exp(rho)
    for t in range(N):
        n = N - t
        want = 1.0 / n if rho == 0.0 else (1.0 - 1.0 / R) / (1.0 - R ** (-n))
        got = g.c_frac[sol.pol_c[t, mid, 0]]
        assert np.allclose(got, want, rtol=0.03), (t, n, want, got)


def test_gauss_hermite_weights_integrate_to_one():
    from lifehjb.model import gauss_hermite
    z, w = gauss_hermite(7)
    assert w.sum() == pytest.approx(1.0)
    assert (z * w).sum() == pytest.approx(0.0, abs=1e-12)
    assert (z ** 2 * w).sum() == pytest.approx(1.0)          # unit variance


def test_mortgage_payment_amortizes(params):
    mg = params.mortgage
    bal = mg.balance
    for _ in range(mg.years):
        bal = bal * (1 + mg.rate_real) - mg.payment_real
    assert bal == pytest.approx(0.0, abs=1e-6)

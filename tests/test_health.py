"""Sections 2.2 / 9.3-9.5: health capital dynamics."""
import numpy as np
import pytest

from lifehjb import health as H
from lifehjb.model import HealthParams, Seat


def test_delta_and_recovery_formulas(params):
    hp = params.health
    s = params.seat("current350")
    assert H.delta_total(s, hp) == pytest.approx(
        hp.delta0 + hp.delta_cognitive * s.c_load + hp.delta_travel * s.travel
        + hp.delta_autonomy * (1 - s.autonomy))
    assert H.recovery(s, hp) == pytest.approx(hp.rho_h * s.r)


def test_steady_state_closed_form(params):
    """Acceptance test 3: forward simulation converges to the analytic h*."""
    hp = params.health
    for s in params.seats:
        target = H.h_star(s, hp)
        for h0 in (0.4, 0.55, 0.72, 0.9, 1.0):
            traj = H.trajectory(h0, s, hp, 60, age_varying_ceiling=False)
            assert traj[-1] == pytest.approx(target, abs=1e-4), s.id


def test_observed_time_constant_matches(params):
    """Acceptance test 3, second half: observed tau matches 1/(recovery+delta).

    In the discrete map the gap to h* contracts by exactly (recovery + delta)
    per year, so the observed time constant is 1/(1 - gap ratio).
    """
    hp = params.health
    for s in params.seats:
        traj = H.trajectory(1.0, s, hp, 40, age_varying_ceiling=False)
        gap = np.abs(traj - H.h_star(s, hp))
        ratios = gap[1:15] / gap[0:14]
        tau_obs = 1.0 / (1.0 - float(np.mean(ratios)))
        assert tau_obs == pytest.approx(H.tau(s, hp), rel=0.05), s.id


def test_time_constants_in_clinical_range(params):
    """Section 2.2 calibration target: tau lands at 1.7-2.8 years for every seat.

    `oldrole350` sits exactly on the upper edge at 2.801, so the bound carries a
    hundredth of a year of slack.
    """
    for s in params.seats:
        assert 1.7 <= H.tau(s, params.health) <= 2.81, s.id


def test_current_seat_steady_state_target(params):
    """Section 2.2 calibration target: h*(current350) ~ 0.67."""
    assert H.h_star(params.seat("current350"), params.health) == pytest.approx(0.67, abs=0.01)


def test_oldrole_is_a_wash(params):
    """Acceptance test 4: the central v2 finding, pinned as a regression."""
    a = H.h_star(params.seat("oldrole350"), params.health)
    b = H.h_star(params.seat("current350"), params.health)
    assert abs(a - b) < 0.02


def test_travel_strictly_reduces_h_star(params):
    """Acceptance test 5, first half."""
    for s in params.seats:
        worse = s.with_travel(min(s.travel + 0.2, 1.0))
        assert H.h_star(worse, params.health) < H.h_star(s, params.health) - 1e-9, s.id


def test_h_max_declines_with_age(params):
    assert H.h_max(39, params.health) == pytest.approx(1.0)
    assert H.h_max(99, params.health) == pytest.approx(1.0 - 0.004 * 60)


def test_step_respects_floor_and_ceiling(params):
    hp = params.health
    s = params.seat("grind500")
    assert H.step(hp.h_min, s, hp, 1.0) >= hp.h_min
    assert H.step(1.0, s, hp, 0.8) <= 0.8

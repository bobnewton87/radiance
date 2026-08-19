"""Section 2.6: the 2026 MFJ + FICA schedule."""
import pytest

from lifehjb.model import (SS_WAGE_BASE, effective_tax_rate, federal_tax, fica_tax,
                           gross_for_net, net_income, total_tax)


def test_net_at_350k():
    """Acceptance test 10: y = 350_000 -> net ~ 270_000 +/- 5_000."""
    assert net_income(350_000) == pytest.approx(270_000, abs=5_000)


def test_fica_components():
    g = 350_000
    expected = 0.062 * SS_WAGE_BASE + 0.0145 * g + 0.009 * (g - 250_000)
    assert fica_tax(g) == pytest.approx(expected)


def test_ss_wage_base_caps():
    """Above the wage base only Medicare keeps scaling."""
    d = fica_tax(400_000) - fica_tax(300_000)
    assert d == pytest.approx(100_000 * (0.0145 + 0.009))


def test_zero_and_below_deduction():
    assert total_tax(0) == 0.0
    assert federal_tax(0) == 0.0
    # Under the standard deduction there is no income tax, but FICA still bites.
    assert total_tax(20_000) == pytest.approx(fica_tax(20_000))


def test_monotone_and_progressive():
    prev_net, prev_rate = -1.0, -1.0
    for g in range(0, 900_000, 25_000):
        n = net_income(g)
        assert n >= prev_net
        prev_net = n
        r = effective_tax_rate(g)
        assert r >= prev_rate - 1e-9
        prev_rate = r


def test_gross_for_net_inverts():
    for target in (50_000, 150_000, 270_615, 500_000):
        g = gross_for_net(target)
        assert net_income(g) == pytest.approx(target, abs=1.0)

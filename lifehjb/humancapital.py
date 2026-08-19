"""Human capital as an equity-like claim.

v2 never modelled H at all, which silently assumed it was worth nothing -- or,
read the other way, that it was a safe bond whose value was already implicit in
the income stream. Neither is true. Account-manager compensation in
semiconductor capital equipment tracks bookings, bookings track the capex cycle,
and the capex cycle is the market. That is a beta, and it belongs on the balance
sheet.

    r_H    = rf_real + beta_H * erp
    S(s)   = prod (1 - q_u)*(1 - lambda_sep_eff(u))      # alive AND employed
    H_t(e) = sum_s y(e)*(1 - tau) * S(s) / (1 + r_H)^(s-t)

Setting ``beta_H = 0`` recovers the v2 reading, and the test suite pins that.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np

from . import career as C
from . import health as H
from .model import (Params, ReturnScenario, Seat, death_prob, return_quadrature,
                    seat_net_income, social_security)


@dataclass
class HCValuation:
    seat_id: str
    H: float
    r_H: float
    beta_H: float
    T_work: float
    net_income: float
    years: int
    sep_rate_used: float
    expected_cycle_mult: float

    @property
    def equity_equivalent(self) -> float:
        """beta_H * H -- the equity exposure already held through the career."""
        return self.beta_H * self.H


def discount_rate(params: Params, scenario: Optional[str] = None) -> float:
    sc = params.returns[scenario or params.scenario]
    return sc.rf_real + params.human_capital.beta_H * sc.erp


def expected_cycle_mult(params: Params, scenario: Optional[str] = None,
                        pi_ref: float = 1.0) -> float:
    """E[cycle multiplier] on the separation hazard, at a reference risky share."""
    sc = params.returns[scenario or params.scenario]
    _, w, down = return_quadrature(np.array([pi_ref]), sc, params.quadrature,
                                   params.career.downturn_threshold)
    return C.expected_cycle_multiplier(w[0], down[0], params.career.downturn_factor)


def value_human_capital(params: Params, seat: Seat, T_work: float,
                        scenario: Optional[str] = None,
                        h0: Optional[float] = None) -> HCValuation:
    """Present value of after-tax labour income, risk-adjusted and hazard-weighted."""
    sc = params.returns[scenario or params.scenario]
    r_H = discount_rate(params, scenario)
    cyc = expected_cycle_mult(params, scenario)
    lam_sep = min(params.career.sep_rate(seat.id) * cyc, 1.0)

    yn = seat_net_income(seat, params)
    h = float(params.h0 if h0 is None else h0)
    age = params.age0
    surv = 1.0
    total = 0.0
    k = 0
    while age < T_work:
        q = float(np.atleast_1d(death_prob(age, np.array([h]), params))[0])
        surv *= (1.0 - q) * (1.0 - lam_sep)
        total += yn * surv / (1.0 + r_H) ** (k + 1)
        h = float(H.step(h, seat, params.health, float(H.h_max(age, params.health))))
        age += 1.0
        k += 1

    return HCValuation(seat_id=seat.id, H=total, r_H=r_H,
                       beta_H=params.human_capital.beta_H, T_work=T_work,
                       net_income=yn, years=k, sep_rate_used=lam_sep,
                       expected_cycle_mult=cyc)


# --------------------------------------------------------------------------- #
# The allocation correction -- headline output                                 #
# --------------------------------------------------------------------------- #

@dataclass
class Allocation:
    gamma: float
    pi_total_target: float
    pi_fin_optimal: float
    total_wealth: float
    W: float
    H: float
    equity_from_H: float

    @property
    def interpretation(self) -> str:
        if self.pi_fin_optimal >= 0.95:
            return "financial portfolio should be fully in equities"
        if self.pi_fin_optimal >= 0.05:
            return "reduce financial equity"
        if self.pi_fin_optimal >= -1e-9:
            return "hold no financial equity"
        return "career exposure already exceeds the target: hedge, or hold uncorrelated assets"


def optimal_financial_share(params: Params, W: float, H_value: float, gamma: float,
                            scenario: Optional[str] = None) -> Allocation:
    """Merton on *total* wealth, net of the equity you already hold via your career.

        TW              = W + H
        E_from_H        = beta_H * H
        pi_total_target = erp / (gamma * sigma^2)
        pi_fin_optimal  = (pi_total_target * TW - E_from_H) / W

    The result is **not clipped**. A negative number is a real answer -- it says
    the career alone overshoots the total-wealth equity target -- and clipping it
    to zero in the report would hide exactly the finding the module exists to
    produce. Clipping for the solver's control grid is a separate matter.
    """
    sc = params.returns[scenario or params.scenario]
    beta_H = params.human_capital.beta_H
    TW = W + H_value
    e_from_H = beta_H * H_value
    pi_tot = sc.erp / (gamma * sc.sigma ** 2)
    pi_fin = (pi_tot * TW - e_from_H) / W if W > 0 else float("nan")
    return Allocation(gamma=gamma, pi_total_target=pi_tot, pi_fin_optimal=pi_fin,
                      total_wealth=TW, W=W, H=H_value, equity_from_H=e_from_H)


def effective_equity_ratio(params: Params, W: float, H_value: float, pi: float) -> float:
    """(pi*W + beta_H*H) / TW -- total equity exposure, legible without reference to gamma."""
    TW = W + H_value
    return (pi * W + params.human_capital.beta_H * H_value) / TW if TW > 0 else float("nan")


# --------------------------------------------------------------------------- #
# Sector concentration                                                         #
# --------------------------------------------------------------------------- #

@dataclass
class Concentration:
    financial_equity: float
    sector_overlap: float
    sector_exposure_W: float
    H: float
    sector_exposure_total: float
    total_wealth: float
    diversifying_sleeve: float

    @property
    def sector_share_of_TW(self) -> float:
        return self.sector_exposure_total / self.total_wealth if self.total_wealth else float("nan")

    @property
    def sleeve_share_of_TW(self) -> float:
        return self.diversifying_sleeve / self.total_wealth if self.total_wealth else float("nan")


def sector_concentration(params: Params, W: float, H_value: float, pi: float) -> Concentration:
    """Total exposure to the semicap cycle across W and H, in one line.

    Human capital is 100% semicap by construction. The financial side adds
    ``portfolio_sector_overlap`` of its equity sleeve -- the part correlated with
    the subject's own sector beyond broad-market beta. The remainder of W (cash,
    short TIPS, gold) is the only genuinely orthogonal holding, so it is reported
    separately rather than netted in.
    """
    hc = params.human_capital
    fin_eq = pi * W
    sector_W = hc.portfolio_sector_overlap * fin_eq
    sleeve = (1.0 - pi) * W + hc.diversifying_sleeve * fin_eq
    return Concentration(
        financial_equity=fin_eq, sector_overlap=hc.portfolio_sector_overlap,
        sector_exposure_W=sector_W, H=H_value,
        sector_exposure_total=sector_W + H_value, total_wealth=W + H_value,
        diversifying_sleeve=sleeve)


def allocation_table(params: Params, W: float, H_value: float,
                     scenario: Optional[str] = None) -> List[Allocation]:
    return [optimal_financial_share(params, W, H_value, g, scenario)
            for g in params.human_capital.gammas_reported]

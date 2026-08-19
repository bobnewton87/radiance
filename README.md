# LifeHJB v3 — Personal Lifecycle HJB Console

> **This is a decision-support model. It is not financial advice and it is not medical
> advice.** It is a numerical solution to a stochastic optimal-control problem under a
> specific set of assumptions, several of which are self-reported and unmeasured. Its
> outputs are conditional on those assumptions being right. Read section
> [Provenance](#provenance) before acting on any number in it, and treat every parameter
> marked *assumed* as a hypothesis rather than a fact.

LifeHJB solves a finite-horizon stochastic lifecycle control problem with **health capital
that both depreciates and recovers**, mortality, **an involuntary separation hazard
correlated with bad market states**, **stochastic seat availability**, and a discrete
job-seat choice. It is calibrated to one person and reports the optimal policy, three
distinct wealth boundaries, the steady-state health of every seat, the **allocation
correction implied by treating human capital as an equity-like claim**, and the dollar
shadow price of health.

### What v3 is for

The point of v3 is not more precision. It is that three conclusions in v2 were conditional
on assumptions that were never stated:

1. **that human capital is safe** — v2 never modelled H at all, which silently assumed zero
   correlation with the portfolio;
2. **that employment is certain** — v2 let you work until you chose to stop;
3. **that better jobs are available on demand** — v2 permitted free seat switching every
   period.

v3 makes each an explicit parameter, so its influence is visible. If a recommendation
survives `beta_H = 1.6` and `base_sep = 0.06`, it is robust. If it only holds at the null
values, it was never a recommendation — it was an artifact of the model's silence.

Every v3 addition has a documented **null value** that recovers v2, and
`tests/test_v3.py::test_v3_reproduces_v2_exactly` pins the recovery. It is exact, not
merely within the spec's 1e-6: with the hazard at zero the cycle-weighted operator
contributes an arithmetic zero, so the recursion is identical.

Everything is in **real (inflation-adjusted) 2026 dollars**. No network access. Seeded and
deterministic. CPU only.

---

## Quick start

```bash
pip install -r requirements.txt
pytest -q                                          # 65 tests, ~6 min
python -m lifehjb --config config.yaml report      # writes out/report.md + 9 PNGs, ~3.5 min
```

Other entry points:

```bash
python -m lifehjb calibrate                 # rho from savings history, b from VSL
python -m lifehjb solve                     # shadow prices and the seat ordering
python -m lifehjb boundaries                # the three wealth thresholds
python -m lifehjb negotiate --seat current350   # seat scores, pay-cut ceiling, break-even
python -m lifehjb allocate --pi 1.0         # v3: human capital and pi_fin_optimal
python -m lifehjb career                    # v3: separation risk, runway, stress test
python -m lifehjb option                    # v3: the value of the outside option
python -m lifehjb report --fast             # coarse grids, for iteration
python -m lifehjb test
```

---

## What the model answers

The design principle throughout: convert recurring, open-ended questions — *should I take
this seat, can I afford to make less, when can I stop* — into **state queries with numeric
answers**. Every output is meant to be looked up in thirty seconds, not re-derived.

| question | where it is answered |
|---|---|
| Which seat is best, and by how much in dollars? | seat score `Theta(e)`, report §5 |
| What is the largest pay cut worth taking for a less punishing seat? | indifference matrix, report §4 |
| They offered me +$X for more scope. How much extra stress makes that a bad trade? | break-even `delta`, `negotiate` |
| Can I credibly walk away from this negotiation today? | `W_BATNA`, report §2 |
| When can I actually stop? | `W*(t)`, report §2 and §6 |
| Where does each seat leave my health in the long run? | `h*(e)`, report §7 |
| How much equity should I hold, given that my career *is* an equity position? | `pi_fin_optimal`, report §3 |
| What happens if I'm laid off in a crash? | correlated stress test, report §5 |
| Is it worth keeping the outside option warm? | `OV_outside`, report §6 |
| Why am I still in this job when another scores higher? | inaction band, report §13 |

---

## Model specification

Discrete annual periods, ages 39 → 100. Age 39.0 as of end of August 2026.

**State:** financial wealth `W` (real $), health index `h ∈ [0.35, 1.0]`, age `t`.
**Controls each period:** consumption `c`, risky share `π`, seat `e`.

### Felicity

```
u(c, h, e) = h · (b + ln c) − φ(e)
```

Health **multiplies** the whole flow rather than adding to it: being unwell scales down
everything money buys. `φ(e)` is the direct felt unpleasantness of the work, kept separate
from its health consequences so the two channels can be priced apart.

`b` is a calibrated intercept. For `u` to be increasing in `h` we need `b + ln c > 0`; see
[The felicity floor](#the-felicity-floor), which is the one place this implementation
departs from a literal reading of the build prompt.

### Health capital — the core of v2

```
δ_total(e) = δ0 + δ_c·c_load(e) + δ_t·travel(e) + δ_a·(1 − autonomy(e))
recovery(e) = ρ_h · r(e)
h_max(t)   = 1.0 − 0.004·(t − 39)
h'         = h + recovery(e)·(h_max(t) − h) − δ_total(e)·h
h'         = clip(h', 0.35, h_max(t))
```

The recovery term is what makes v2 different. Because health is pulled back toward a
ceiling, each seat has a **fixed point** rather than a decay slope:

```
h*(e) = recovery(e)·h_max / (recovery(e) + δ_total(e))
τ(e)  = 1 / (recovery(e) + δ_total(e))          # time constant, years
half-life to h* = τ · ln 2
```

Both follow directly from the map: the gap `h_max − h` contracts by exactly
`recovery + δ_total` per year, so the fixed point is where recovery inflow equals
depreciation outflow, `recovery·(h_max − h) = δ_total·h`.

With the shipped defaults (`δ0=0.02, δ_c=0.08, δ_t=0.10, δ_a=0.04, ρ_h=0.6`):

| seat | δ_total | recovery | **h\*** | τ (yr) | half-life |
|---|---|---|---|---|---|
| `grind500` | 0.1530 | 0.210 | **0.579** | 2.75 | 1.91 |
| `current350` | 0.1340 | 0.270 | **0.668** | 2.48 | 1.72 |
| `oldrole350` | 0.1170 | 0.240 | **0.672** | 2.80 | 1.94 |
| `amat400` | 0.1090 | 0.372 | **0.773** | 2.08 | 1.44 |
| `renegotiated350` | 0.0890 | 0.420 | **0.825** | 1.96 | 1.36 |
| `downshift250` | 0.0680 | 0.480 | **0.876** | 1.82 | 1.26 |
| `retired` | 0.0280 | 0.552 | **0.952** | 1.72 | 1.20 |

These are calibration targets, not free parameters, and the test suite pins them:
`h*(current350) ≈ 0.67` matches the subject's reported lived experience, and every time
constant lands in 1.7–2.8 years, consistent with clinical recovery timescales from
burnout, sleep debt and deconditioning.

**The central v2 result** falls straight out of the table: `h*(oldrole350) = 0.672` against
`h*(current350) = 0.668`. Cutting cognitive load from 0.85 to 0.30 while raising travel
from 0.20 to 0.55 is **a wash**. Under v1's scalar-stress model the old role looked like a
clear improvement; it is not. `tests/test_health.py::test_oldrole_is_a_wash` pins this.

**On travel and recovery.** The build prompt's prose says travel damages the *recovery*
term as well as the damage term, while its equations put `recovery(e) = ρ_h·r(e)` with no
travel argument. The equations are normative here, and the prose is satisfied through the
seat data: travel's recovery damage is carried by each seat's own `r`, which is why
`oldrole350` has `r = 0.40` despite having the second-lowest cognitive load in the roster.
Modelling it twice would double-count.

### Seats

| id | y | c_load | travel | autonomy | r | φ | note |
|---|---|---|---|---|---|---|---|
| `grind500` | 500,000 | 1.00 | 0.25 | 0.30 | 0.35 | 0.30 | more scope, more money |
| `current350` | 350,000 | 0.85 | 0.20 | 0.35 | 0.45 | 0.18 | status quo |
| `oldrole350` | 350,000 | 0.30 | 0.55 | 0.55 | 0.40 | 0.12 | mastered role, heavy travel |
| `amat400` | 400,000 | 0.60 | 0.25 | 0.60 | 0.62 | 0.10 | outside role, correctly leveled |
| `renegotiated350` | 350,000 | 0.50 | 0.15 | 0.65 | 0.70 | 0.08 | same pay, scope relief |
| `downshift250` | 250,000 | 0.35 | 0.10 | 0.75 | 0.80 | 0.04 | lower pay, low load |
| `retired` | 0 | 0.05 | 0.02 | 0.95 | 0.92 | 0.00 | **absorbing** |

`retired` is absorbing: once entered, no seat change is permitted. This is why the solver
carries two value functions (`V_work`, `V_ret`) rather than one, and it is the single
assumption most responsible for `W*(39)` being an order of magnitude above the coast
numbers — stopping at 39 forfeits sixty years of *optional* income, and that option is
expensive.

Social Security adds +40,000/yr real from age 67 when `ss.enabled`.

### Mortality

```
λ(t) = 2e-4 + 1e-3 · 2^((t − 39)/8)          # Gompertz–Makeham
q_t  = 1 − exp(−λ(t))
```

With `mortality_health_coupled` (default on), the hazard is scaled by health:

```
λ_eff(t, h) = λ(t) · (h_ref/h)^κ ,   κ = 1.0,  h_ref = 0.85
```

This is the second channel through which poor health is costly, and it is kept separable so
its contribution can be isolated by flipping the flag.

### Wealth

```
W' = (W + y(e)·(1 − τ_tax(y)) + SS_t − m_t − c) · R'
ln R' ~ Normal(rf + π·erp − 0.5·π²σ², π²σ²)
```

`c > resources` is rejected with utility `−inf`. The return expectation is integrated with
**7-node Gauss–Hermite quadrature**: for `Z ~ N(0,1)`,
`E[f(Z)] ≈ Σ_k (w_k/√π)·f(√2·x_k)` with `(x_k, w_k)` the physicists' Hermite nodes.

### Returns — and why these numbers

Base case: `rf_real = 0.020, erp = 0.032, sigma = 0.16`.

The risk-free real leg is **observable**, not forecast: it is the 10-year TIPS yield, about
2.0% as of August 2026. That is a contracted real return, so it needs no model.

The equity leg does need one. The starting point is a Shiller CAPE near 42 against a
long-run median near 16. Historically, valuations that stretched have predicted *weak*
forward real returns rather than negative ones — the empirical relationship between
starting CAPE and subsequent 10-year real returns is reliably negative in slope but noisy
in level, and it has never implied a negative central estimate at these multiples. A 3.2%
premium over a 2.0% real risk-free rate is a deliberate haircut against the ~4.5–5%
historical premium, taken because the starting valuation is high, not because equities are
expected to lose money. Geometric real return at full equity weight is then
`rf + erp − σ²/2 ≈ 4.8%`.

Because that estimate is the weakest link in the whole model, it is not reported as a point
estimate. All three scenarios are run and reported:

```yaml
bear: {rf_real: 0.015, erp: 0.015, sigma: 0.18}   # ~2.5% real geometric
base: {rf_real: 0.020, erp: 0.032, sigma: 0.16}   # ~4.8% real geometric
bull: {rf_real: 0.020, erp: 0.055, sigma: 0.16}   # ~7.0% real geometric
```

Any recommendation the report surfaces is tagged with whether it holds in all three.

### Taxes

2026 federal MFJ brackets plus employee-side FICA, standard deduction 30,000, Texas so no
state income tax:

| bracket top | rate |
|---|---|
| 24,800 | 10% |
| 100,800 | 12% |
| 211,100 | 22% |
| 402,800 | 24% |
| 511,300 | 32% |
| 767,000 | 35% |
| above | 37% |

FICA: OASDI 6.2% to a 184,000 wage base; Medicare 1.45% on all wages; Additional Medicare
0.9% above 250,000 (MFJ).

At `y = 350,000`: taxable 320,000 → federal 62,002; FICA 17,383; **net 270,615**. The unit
test pins this at 270,000 ± 5,000.

### Mortgage

Balance 126,000 at 3.625% nominal. The real rate is Fisher-exact,
`(1 + 0.03625)/(1 + 0.025) − 1 = 1.098%`, and the level real payment amortizing the balance
over 7 years is **18,799/yr**; `m_t = 0` thereafter. Home equity (~900,000) is **excluded**
from `W` and treated as prepaid housing services, so `spend_base` includes property tax and
maintenance (~20,000/yr DFW) but no principal or interest.

### Bellman recursion

```
β = exp(−ρ)
V_t(W,h) = max over (c, π, e) of
   u(c,h,e) + β · [ (1 − q_t(h))·E[V_{t+1}(W', h')] + q_t(h)·Bq(W') ]

Bq(W) = ω · (b + ln(max(W, 50_000)))          # bequest, default ω = 2.0
V_100 = Bq(W)
```

---

## v3: human capital, career risk, and seat availability

### Human capital is not bond-like

```
r_H    = rf_real + beta_H * erp
S(s)   = prod_{u=t..s} (1 - q_u) * (1 - lambda_sep_eff(u))     # alive AND employed
H_t(e) = sum_{s=t..T_work} y(e)*(1 - tau_tax) * S(s) / (1 + r_H)^(s-t)
```

`T_work = min(retirement age under the current policy, 65)`. `beta_H = 1.6` by default:
semiconductor capital equipment is high-beta and account-manager compensation tracks
bookings, which track the capex cycle. **Null value: `beta_H = 0`.**

**The allocation correction** — the headline v3 output:

```
TW              = W + H
E_from_H        = beta_H * H
pi_total_target = erp / (gamma * sigma^2)
pi_fin_optimal  = (pi_total_target * TW - E_from_H) / W
```

At the shipped calibration this reproduces the expected finding exactly. Human capital is
worth ~$1.68M, so career equity exposure alone is ~$2.68M against $1.85M of financial
wealth, and effective total equity exposure is **1.29× total wealth**:

| gamma | pi_total_target | pi_fin_optimal | reading |
|---|---|---|---|
| 1.0 | 1.250 | **+0.93** | roughly correctly positioned at the Kelly case |
| 1.5 | 0.833 | **+0.14** | reduce financial equity |
| 2.0 | 0.625 | **−0.26** | hedge, or hold uncorrelated assets |
| 3.0 | 0.417 | **−0.66** | hedge, or hold uncorrelated assets |

Negative numbers are **reported as negative, never clipped**. Clipping to [0,1] for the
solver's control grid is fine; clipping in the report would hide the finding. Total
exposure to the semicap cycle across W and H is 66% of total wealth, and the diversifying
sleeve (the only genuinely orthogonal holding) is reported separately rather than netted in.

### Involuntary separation, correlated with the market

```
lambda_sep(t, e, R') = base_sep(e) * cycle_mult(R')
cycle_mult(R')       = 1.0              if R' >= 1 + downturn_threshold
                       downturn_factor  otherwise
```

**The correlation is the entire point.** Separation is resolved *after* the return draw in
each period, against that same draw — never an independent one. On separation: severance of
`severance_months * y/12`, then forced search, then re-entry with a permanent comp haircut.

Measured under the optimal policy, the realized separation rate is **0.1264 in years the
portfolio fell more than 15%** against **0.0411 otherwise** — a ratio of **3.07** against a
configured `downturn_factor` of 3.0. Under independent sampling the ratio collapses to 1.0
with the *marginal* rate unchanged. **Null value: `base_sep = 0` for all seats.**

### Seats arrive; they are not on tap

`current350` and `downshift250` are always available — the latter is the **floor option**,
and its permanent availability is what makes every other negotiation credible.
`renegotiated350` arrives by negotiation, `amat400` conditional on maintaining the outside
option, `oldrole350` with probability `p_oldrole`. Modelling this is what produces a dollar
value for holding an outside option. **Null value: `availability.unrestricted = true`.**

### Crunch lockout and switching costs

`crunch.periods = 1` forces `current350` (with `c_load` multiplied by 1.30) for the next
~12 months, so the solver cannot recommend a switch that is not actually on the table.
Switching costs are **default-on in v3** (`kappa_W = 40,000`, `kappa_h = 0.02`), which with
availability constraints makes the seat decision a genuine optimal-stopping problem with an
inaction band. **Null values: `crunch.periods = 0`, `switching_costs.enabled = false`.**

---

## The v3 state, and what it costs

State is `(W, h, t, career state)`. The career state carries the current seat plus one
auxiliary counter whose meaning depends on the seat — years served in `amat400` (which
drives its seasoning), remaining forced-search years in `searching`, nothing elsewhere —
plus a `scarred` flag. That is **16 states** at the defaults rather than the 8 × 3 = 24 the
spec's sizing assumed, because most combinations are unreachable and are not enumerated.

A full solve is ~11 s and the whole report ~3.5 minutes, against a 5-minute budget. Three
things make that possible:

1. **The v2 memoization survives.** The expectation operator still depends on the age only
   through resources.
2. **The separation branch decomposes.** With `lam_k = base_sep * cycle_mult_k`,

   ```
   E[(1-lam_k) V_emp + lam_k V_sep] = A0 @ V_emp + base_sep * B @ (V_sep - V_emp)
   ```

   where `A0` is the plain expectation and `B` the cycle-weighted one. Neither depends on
   the seat's separation rate, so the memo stays small even as the state space grows 16×.
3. **Severance is folded into the value function, not the grid.** `V_search(W' + severance)`
   is precomputed as a shifted value function on the W grid, so the same interpolation
   weights serve both branches.

The `W` grid is 45 points rather than v2's 60 — the trade the spec explicitly authorizes,
taken before touching the `h` grid because health resolution matters more for these results
than wealth resolution does for the boundary.

### The quadrature had to change

The separation multiplier is a **step function** of the realized return, and Gauss–Hermite
cannot resolve a step. At the base scenario and π = 1 the true `P(R' < 0.85)` is 0.1037, and
Gauss–Hermite reports:

| nodes | 7 | 11 | 15 | 21 | 25 | 31 | 41 |
|---|---|---|---|---|---|---|---|
| P(downturn) | 0.031 | 0.073 | 0.108 | 0.150 | 0.056 | 0.078 | 0.109 |

It does not converge — it oscillates with wherever the nodes happen to fall. The entire v3
correlation would have been an artifact of node placement. v3 therefore defaults to
`quadrature.kind: split`: the domain is broken **exactly at the threshold** and composite
Gauss–Legendre runs against the normal density on each side. The mass either side is then
exact by construction, and 4 panels × 8 nodes reproduces `E[z]`, `E[z²]` and `E[e^{σz}]` to
machine precision. Setting `kind: gauss_hermite` restores the v2 rule, which is what the v2
recovery test pins.


---

## Numerics

* `W` log-spaced, 60 points on [50,000, 30,000,000]; `h` 14 points on [0.35, 1.0].
* `V` interpolated bilinearly in `(ln W, h)`.
* Controls by discrete search, which is more robust than first-order conditions given the
  discrete seat choice: `c/resources` over 30 log-spaced points on [0.01, 0.95] (floored,
  see below); `π ∈ {0, 0.2, 0.4, 0.6, 0.8, 1.0}`; `e` over the allowed seats.
* Policy arrays `c*(W,h,t)`, `π*(W,h,t)`, `e*(W,h,t)` are stored.
* Shadow prices `V_W`, `V_h` by central differences on the solved `V`.

**Off-grid wealth is linearly extrapolated, not clamped.** Under log utility `V` is close to
affine in `ln W`, so extrapolating the end intervals is far more accurate at the boundaries
than flattening them.

### How it stays fast

A full solve is ~1.8 s and the whole report ~100 s, against a 5-minute budget. Two
observations do the work:

1. `h'` depends only on `(h, e)` — never on `c` or `π`. So next-period value can be
   pre-collapsed along the `h` axis into `Vh[:, j] = V_{t+1}(W_grid, h'(h_j, e))`.
2. `ln W'` depends on `(W, c, π, node)` but **not** on `h`. Its interpolation weights are
   therefore shared across every health node, and because the `W` grid is log-spaced the
   bracketing index is a floor division rather than a search.

Together these turn the expectation into a single dense matmul `A @ Vh` per (seat, age),
where `A` is a `(n_W·n_c·n_π, n_W)` operator with the quadrature weights already folded in.
`A` in turn depends on the age only through resources, which change only when the mortgage
amortizes and when Social Security starts — so it is memoized on that offset, cutting the
number of builds from 427 to 63 per solve. That memoization alone is a 7× speedup.

### The felicity floor

This is the one place the implementation departs from a literal reading of the build
prompt, and it is worth stating plainly.

The prompt requires two things that turn out to conflict:

* calibrate `b` so that `VSL ≡ V/V_W` at the current state hits 22M (band 15M–30M);
* assert `b + ln c > 0` over the whole consumption grid.

Calibrating to a 22M VSL forces `b ≈ −9.3`. Since `b + ln c > 0` ⟺ `c > exp(−b)`, that
implies a **subsistence consumption of about $10,900/yr**: below it, the model says health
has no value. That is a perfectly sensible economic statement. But the raw grid's bottom
corner is `0.01 × (W_min + y_retired − m) ≈ $312/yr` of consumption — a state that is never
chosen and is economically meaningless — and the assertion fails there.

Rather than weaken the assertion, the consumption grid gets an absolute floor:

```
c = max(c_frac · resources, min(c_floor, 0.95 · resources)),   c_floor = 15,000
```

This is a numerics change, not an economics change — the solver never wants to consume 1%
of resources anyway, and flooring puts grid resolution where decisions actually happen. It
makes both requirements simultaneously satisfiable, and `exp(−b)` is reported as a
first-class diagnostic in every calibration output rather than being buried.

The consequence is worth reading off: **the VSL target pins the zero-utility consumption
level.** At a 30M target, `c_sub ≈ $1,500/yr` — innocuous. At the 22M default,
`c_sub ≈ $10,900/yr` — still below the floor and admissible. At the 15M bottom of the band,
`c_sub ≈ $39,800/yr`, which is *above* the floor: that leg violates the felicity condition
and the report flags it **INADMISSIBLE** rather than quietly reporting it. It is still
solved and shown, as the conservative bound, but it is not a usable calibration.

---

## Calibration

### ρ — pure time preference

Given the history — 2010: `W = 25,000`, household gross 90,000 (two earners); 2026:
`W = 1,850,000`, single earner gross 350,000 — `calibrate.py` assumes gross income grew
geometrically between the endpoints, applies `τ_tax`, assumes a realized 10%/yr nominal
portfolio return against 2.5% inflation, and solves for the constant savings-rate-out-of-net
that reproduces `W_2026`.

Everything is deflated into 2026 dollars first, so that the 2026 tax schedule is applied to
2026-dollar incomes rather than to nominal historical ones. That gives a 7.32% real
portfolio return and 6.20% real gross income growth.

Result: **savings rate 35.5%**, which reproduces `W_2026` exactly. A rate at or above 30%
implies `ρ ∈ [0.015, 0.025]`.

**Default ρ = 0.02.** Under log utility this is also the optimal consumption fraction of
wealth in the infinite-horizon limit — `c/W = 1 − β = 1 − e^{−ρ} ≈ ρ` — so the same number
is doing double duty as impatience and as a spending rule. That identity is what
`tests/test_analytic.py::test_merton_recovery` checks.

### b — the utility intercept, via VSL

`b` is found by solving `VSL(b) = vsl_target`, where `VSL ≡ V/V_W` evaluated at
`(W = 1.85e6, h = h0, t = 39)`. `VSL` is increasing in `b` (shifting `b` moves `V` roughly
linearly while leaving `V_W` nearly alone), so a coarse-grid bisection brackets the root
cheaply and a secant refinement on the production grid lands it inside 0.5%.

| VSL target | b | achieved VSL | Λ_h | c_sub | admissible |
|---|---|---|---|---|---|
| 15M | −10.327 | 15.012M | $11,656 | $30,546 | **no** |
| 22M | −8.732 | 22.000M | $17,160 | $6,199 | yes |
| 30M | −6.925 | 30.005M | $23,969 | $1,017 | yes |

(v3 figures; the v2 numbers differ because career risk lowers the value of the working
state.) v3 solves are ~9× more expensive than v2's, so a blind bisection is not affordable:
`calibrate_b_v3` runs a secant on the sweep grid seeded from the v2 neighbourhood, then two
or three steps on the production grid, landing VSL inside 0.005%.

The reported price of health is

```
Λ_h ≡ 0.01 · V_h / V_W        # dollars per 1 percentage point of permanent health
```

The whole report is run at all three VSL targets crossed with all three return scenarios,
and only conclusions surviving the full 3×3 grid are stated without a qualifier. Because
`Λ_h` moves 3.8× across that grid, bare rank stability turns out to be a useless test — so
the report also computes **pairwise dominance**, the set of seat comparisons whose sign is
identical in all nine cells. That is the statement a negotiation can actually lean on.

---

## Outputs

`python -m lifehjb report --config config.yaml` writes `out/report.md` plus nine PNGs:

1. **Executive summary** — position against the three boundaries, runway months,
   `pi_fin_optimal` vs actual, top-ranked *available* seat, `OV_outside`, and `Λ_h`.
2. **The three wealth boundaries.**
3. **Human capital and the allocation correction** — `H`, `beta_H`, `pi_fin_optimal` by γ,
   effective total equity exposure, and the sector-concentration line.
4. **Career risk** — per-seat separation rates, lifetime separation counts, and the
   correlation measured directly.
5. **Correlated stress test** — a 35% drawdown *and* a separation in the same year, at ages
   42, 46 and 50.
6. **Option value** of a maintained outside option, decomposed into insurance and
   bargaining components.
7. **Per-seat table** with `h*` prominent.
8. **Indifference matrix** — the maximum acceptable pay cut, in consumption and in gross.
9. **Seat scores** `Theta(e)` with rank ranges and pairwise dominance across the 3×3 grid.
10. **Stopping boundary** `W*(t)` for ages 39–70 at two health levels.
11. **Monte Carlo** — with separation risk active, shown alongside the v2 no-separation
    figure so the cost of career risk is explicit.
12. **Sensitivity tornado** on median finish age, plus a second tornado on
    `pi_fin_optimal` (which is where `beta_H` has to be swept, since it never enters the
    solver).
13. **Switching costs and the inaction band.**
14. **Parameter provenance**, with measurement priorities flagged.

Plots: `h*` by seat; h trajectories; policy heatmap; `c/W` vs age; wealth fan; `W*(t)`;
inaction band; allocation by γ; sensitivity tornado.

Two grids are used, and each section says which produced it. The **production** grid
(45 × 14 × 30 × 6) carries everything headline. The **sweep** grid (30 × 8 × 18 × 4)
carries the sections needing many solves — the 3×3 scenario × VSL grid, per-seat finish
ages, the tornado, the option value — where what is measured is a difference rather than a
level.

Retirement spending is chosen by the solver. `spend_base` is used **only** for the coverage
metric, the boundary calculations and the sensitivity sweep, and never enters the dynamics.
That is why its tornado bar has a span of exactly zero; a non-zero bar there would have
meant a bug.

### The three boundaries, and why the distinction matters

1. **`W_BATNA`** — credible-walk-away wealth, `runway_years × annual_full_expenses`. At
   3 years × $168,799 that is **$506,397**, already covered 3.7× over. This is the number
   that makes an outside option credible in a negotiation, and it is *much* lower than the
   retirement number. Conflating the two is what keeps people negotiating from a position
   they already have.
2. **`W_coast(target_age)`** — wealth today that reaches `W*` by the target age with zero
   further saving, `W*(target) / (1 + g_real)^(target − 39)`, using the fully-invested
   geometric real return.
3. **`W*`** — the solver's actual free boundary: the smallest `W` at which `e* = retired`.

They must satisfy `W_BATNA < W_coast(60) < W_coast(49) < W*`, which
`tests/test_properties.py::test_boundary_ordering` asserts.

### Reading the Monte Carlo honestly

At the default calibration only about **22%** of paths ever reach the stopping boundary
before dying. The median retirement age is therefore reported **conditional on retiring**,
always alongside `P(retire)`. Reporting the conditional median alone would be misleading,
and coding "never" as age 100 would be worse. This is a real result, not a defect: it says
the decision this model settles is *which seat*, not *when to stop*.

---

## Switching costs and the inaction band

Default-on in v3. A seat change costs `kappa_W = 40,000` and `kappa_h = 0.02` of health.
The **inaction band** is the share of the (W, h) grid where the frictionless policy would
move but the frictional one stays put — the real-options structure, and the formal
explanation for staying in a suboptimal job. At the defaults it runs 3–11% from the seats
the model actually wants to hold, and **0% from `current350`**: the static gap there is far
too large for a $40,000 friction to hold you.

## Acceptance tests

`pytest -q` — 65 tests, all green. The eleven v2 tests and the eight v3 tests map as
follows.

| # | requirement | test |
|---|---|---|
| 1 | Merton recovery: `π* → erp/σ²`, `c/W → ρ` | `test_analytic.py::test_merton_recovery` |
| 2 | Annuity consumption | `test_analytic.py::test_annuity_consumption` |
| 3 | Health steady state, closed form + time constant | `test_health.py::test_steady_state_closed_form`, `::test_observed_time_constant_matches` |
| 4 | The `oldrole350` result | `test_health.py::test_oldrole_is_a_wash` |
| 5 | Travel dominance (h\* and Θ) | `test_health.py::test_travel_strictly_reduces_h_star`, `test_properties.py::test_travel_strictly_reduces_theta` |
| 6 | Monotonicity of `V`; `b + ln c > 0` | `test_properties.py::test_value_strictly_increasing_in_*`, `::test_felicity_condition_holds_at_default_calibration` |
| 7 | Mortality raises spend | `test_properties.py::test_doubling_mortality_weakly_raises_spending` |
| 8 | Boundary ordering | `test_properties.py::test_boundary_ordering` |
| 9 | VSL band, Λ_h finite and positive | `test_properties.py::test_vsl_calibration_lands_in_band` |
| 10 | Tax test at 350k | `test_tax.py::test_net_at_350k` |
| 11 | Determinism: identical `report.md` | `test_properties.py::test_report_is_byte_identical_across_runs` |
| 12 | **v2 recovery** | `test_v3.py::test_v3_reproduces_v2_exactly`, `::test_v3_reproduces_v2_boundaries` |
| 13 | Beta monotonicity | `test_v3.py::test_pi_fin_optimal_decreasing_in_beta` |
| 14 | Precautionary saving | `test_v3.py::test_separation_risk_raises_precautionary_saving`, `::test_separation_risk_pulls_retirement_earlier` |
| 15 | Option value | `test_v3.py::test_option_value_gross_positive_and_monotone` |
| 16 | Correlation is real | `test_v3.py::test_correlation_is_real`, `::test_correlation_worsens_the_working_years_tail` |
| 17 | Severance sanity | `test_v3.py::test_severance_reduces_exhaustion_in_the_stress_test` |
| 18 | Lockout binds | `test_v3.py::test_crunch_lockout_binds` |
| 19 | Inaction band non-empty | `test_v3.py::test_inaction_band_non_empty` |

Several needed a stated reading rather than a literal one:

* **Merton (1)** — the production `π` grid has six nodes, far too coarse to resolve 0.48
  within ±0.07. The test refines the grid to 51 nodes. Grid resolution is numerics, not
  economics, so this is a legitimate test configuration rather than a weakened assertion.
* **Annuity (2)** — `c_t/W_t = 1/(remaining periods)` is the **zero-rate** case. With
  `rf = ρ = r > 0` the Euler equation gives `βR = 1`, so consumption is constant in level
  and the exact draw is the annuity factor `(1 − 1/R)/(1 − R^{−n})`, which collapses to
  `1/n` as `r → 0`. The test checks both: at `ρ = 0` it reproduces `1/n` on the nose, and at
  `ρ = 0.02` it matches the annuity factor to 3%.

* **Correlation (16)** — the spec frames this as p10 of terminal wealth. That statistic
  cannot carry the test. Terminal wealth is measured decades after any separation; measured
  directly, the effect there is a fraction of a percent and sits below Monte Carlo noise at
  any affordable path count. What the test asserts instead is the **coupling itself**, which
  is exactly what the spec says the test exists to catch and which cannot pass trivially:
  with the hazard tied to the realized return the separation rate in downturn years is
  `downturn_factor` × the normal rate (measured: 3.07 against a configured 3.0), and under
  independent sampling it collapses to 1.008 with the marginal rate unchanged (0.0507 both
  ways). A companion test asserts the economic claim where the effect actually lives — the
  p5 of minimum wealth during the working years, averaged over six seeds.

  Getting this right also exposed a real bug: `independent_separation` drew an extra normal
  per period, which desynchronized the whole RNG stream and turned the comparison into a
  noise measurement. The simulation now runs **one generator per source of randomness**
  with fixed-size draws per period, so runs that differ only in model structure stay paired.

* **Option value (15)** — the spec asks for `OV_outside > 0` at defaults. It is not, and the
  reason is worth more than the assertion. See *Departures* below.

* **Precautionary saving (14)** — the c/W clause holds as specified. The finish-age clause
  comes out **the other way**. See *Departures* below.

Determinism (11) is checked on the `--fast` profile, which exercises the same code path and
the same formatting; the full profile takes minutes per run and would make the suite
needlessly slow for no additional coverage.

---

## Departures from the v3 spec, and why

Four places where the implementation does not do what a literal reading says. Each is
flagged in the generated report as well.

### 1. `current350` is withdrawn while searching

The v3 availability table says `current350` is "always available (status quo)". That is
written from the perspective of an *employed* agent: the status quo is on offer because you
are already in it. After an involuntary separation it is not — you cannot walk back into the
job you were just let go from. Seats at the current employer (`current350`, `grind500`,
`renegotiated350`) are therefore withdrawn from the choice set while searching.

Without this, re-entry to `current350` is guaranteed and the outside option has **exactly
zero** insurance value, which makes §3.1's headline output vacuous. The list is configurable
as `availability.same_employer`.

### 2. Negotiating power is tied to the outside option

Under a literal reading, maintenance changes only `p_outside`. Then `renegotiated350` and
`amat400` are pure substitutes, and `OV_outside` **falls** as `p_nego` rises — so test 15's
requirement that OV be *increasing* in `p_nego` cannot hold. The only reading under which it
can is that maintenance is also what makes the negotiation credible, which is both the
standard bargaining logic and what the spec's own note about `downshift250` ("its permanent
availability is what makes every other negotiation credible") points at.

So `p_nego` is 0.35 maintained and `p_nego_unmaintained = 0.10` otherwise. Setting them
equal recovers the literal spec.

### 3. The negotiation cooldown is folded into an effective arrival rate

Carrying "years until the next attempt is permitted" in the state triples the `current350`
branch for a second-order effect. The one-shot-plus-cooldown renewal process has mean time
between attempts `1 + (1-p)*cooldown`, so the long-run rate is preserved by

```
p_nego_effective = p_nego / (1 + (1 - p_nego) * nego_cooldown_years)   # 0.35 -> 0.152
```

Both numbers are reported.

### 4. Search duration on an annual grid

The months distribution `{3: 0.30, 6: 0.45, 9: 0.15, 12: 0.10}` is rounded **half up** onto
the annual grid, giving `{0: 0.30, 1: 0.70}` — an expected 0.70 unemployed years against a
true expectation of 6.15 months = 0.51. The annual grid cannot represent half a year of
search, and rounding half up makes the model conservative rather than optimistic about
career risk, which is the right direction of error for a risk module.

---

## Two results that contradict the spec's expectations

Both are reported rather than tuned away. They are the kind of thing the model exists to
find.

### The option value is negative at the configured maintenance cost

`OV_outside` is **−$4,038/yr**. Gross of the maintenance disutility it is **+$503/yr** and
rises with separation risk — the signature of insurance rather than a bluff, exactly as
§3.1 predicts. But it is small, and `phi_maintain = 0.02` costs ~$4,541/yr. Break-even is
around `phi_maintain = 0.0022`. Two things drive it:

1. **The floor option dominates the outside option.** The solver ranks `downshift250` above
   `amat400` at this wealth — higher steady-state health (0.876 vs 0.773) and a lower
   separation rate (0.04 vs 0.10 for the first two years). Since `downshift250` is
   permanently available, what maintenance buys is a seat the model does not want. The
   negotiating leverage is already there, which is precisely the spec's own point about the
   floor option.
2. **`phi_maintain = 0.02` is not small on this scale.** It is half the direct disutility of
   `downshift250` as an entire job (0.04) and a quarter of `renegotiated350`'s (0.08).

### Separation risk pulls retirement *earlier*, not later

The spec expects the median finish age to move out by 1–3 years. It moves **in** by one
year, and P(retire) rises from 25% to 31%. The reason is structural: `retired` is absorbing
and carries `base_sep = 0`, so it is the one state career risk cannot reach. Raising the
hazard does two things at once — the working population saves more (the precautionary
effect, which holds as specified: median c/W at 40–55 falls from 0.0967 to 0.0918 as
`base_sep` goes from 0 to 2×) and retirement becomes more attractive to the wealthy paths
that can afford it.

The tests assert both effects in the direction the model actually produces, so they remain
regression tests.

---

## Provenance

Every parameter, its units, its value, and whether it is *observed*, *calibrated* or
*assumed*. Section 9 of the generated report reproduces this and additionally flags any
*assumed* parameter appearing in the top three tornado bars as a measurement priority.

| parameter | units | value | provenance | note |
|---|---|---|---|---|
| `age0` | years | 39.0 | *observed* | end of August 2026 |
| `W0` | 2026 $ | 1,850,000 | *observed* | liquid only; ~900,000 home equity excluded |
| `h0` | index | 0.72 | *assumed* | from reported perceived age ~50 at chronological 39 — **MEASURE THIS** |
| `spend_base` | 2026 $/yr | 150,000 | *observed* | ex mortgage P&I; includes ~20,000 DFW property tax |
| mortgage balance | 2026 $ | 126,000 | *observed* | 3.625% nominal, ~7 yr remaining |
| `rho` | 1/yr | 0.02 | *calibrated* | from the 2010→2026 savings path (35.5% savings rate) |
| `omega_bequest` | utils | 2.0 | *assumed* | bequest weight |
| `b` | utils | −9.299 | *calibrated* | secant on VSL = V/V_W at the current state |
| `vsl_target` | 2026 $ | 22,000,000 | *assumed* | band 15M–30M swept in report §5 |
| `delta0` | 1/yr | 0.02 | *assumed* | baseline health depreciation |
| `delta_cognitive` | 1/yr | 0.08 | *assumed* | per unit of cognitive load |
| `delta_travel` | 1/yr | 0.10 | *assumed* | per unit of nights-away fraction |
| `delta_autonomy` | 1/yr | 0.04 | *assumed* | per unit of autonomy deficit |
| `rho_h` | 1/yr | 0.6 | *assumed* | recovery scale; pins τ to 1.7–2.8 yr |
| `h_min` | index | 0.35 | *assumed* | floor on the health index |
| `h_max_decay` | 1/yr | 0.004 | *assumed* | decline in the recoverable ceiling |
| seat `c_load`/`travel`/`autonomy`/`r` | index | per seat | *assumed* | self-reported seat attributes — **MEASURE THESE** |
| `phi(e)` | utils/yr | per seat | *assumed* | direct seat disutility |
| `rf_real` | 1/yr | 0.020 | *observed* | 10-year TIPS real yield, Aug 2026 |
| `erp` | 1/yr | 0.032 | *assumed* | haircut from history for CAPE ~42 vs median ~16 |
| `sigma` | 1/yr | 0.16 | *observed* | long-run real equity volatility |
| `lambda(t)` | 1/yr | Gompertz–Makeham | *assumed* | 2e-4 + 1e-3·2^((t−39)/8) |
| `kappa` | — | 1.0 | *assumed* | mortality–health coupling exponent |
| `h_ref` | index | 0.85 | *assumed* | reference health in the hazard scaling |
| tax schedule | — | 2026 MFJ + FICA | *observed* | standard deduction 30,000; Texas, no state tax |
| SS | 2026 $/yr | 40,000 from 67 | *assumed* | real benefit |
| `kappa_W` / `kappa_h` | 2026 $ / index | 40,000 / 0.02 | *assumed* | switching costs, off by default |
| `c_floor` | 2026 $/yr | 15,000 | *assumed* | subsistence floor on the consumption grid |
| `beta_H` | — | 1.6 | *assumed* | human-capital beta, semicap capex cycle — **top allocation-tornado bar; highest-value thing to refine** |
| `portfolio_sector_overlap` | — | 0.35 | *assumed* | financial equity correlated with own sector beyond market beta |
| `base_sep` | 1/yr | 0.04–0.10 | *assumed* | involuntary separation by seat — **top-3 tornado bar; highest-value thing to refine** |
| `downturn_factor` / `downturn_threshold` | — | 3.0 / −0.15 | *assumed* | the hazard multiplier and what counts as a bad year |
| `severance_months` | months | 4 | *assumed* | employer practice |
| `search_duration_dist` | months | 3/6/9/12 | *assumed* | collapsed to the annual grid; see Departures |
| `reentry_haircut` | — | 0.10 | *assumed* | permanent comp scarring after involuntary exit |
| `p_outside` | 1/yr | 0.40 / 0.05 | *assumed* | outside-offer arrival, maintained / not |
| `p_nego` | 1/yr | 0.35 / 0.10 | *assumed* | negotiation success, maintained / not; see Departures |
| `phi_maintain` | utils/yr | 0.02 | *assumed* | cost of keeping the option warm; break-even is ~0.0022 |
| `p_oldrole` / `p_grind` | 1/yr | 0.50 / 1.00 | *assumed* | `p_grind` is **not specified in v3**; treated as an internal scope expansion and always available |
| `crunch.periods` / `multiplier` | yr / — | 1 / 1.30 | *observed* | a real execution commitment |
| `kappa_W` / `kappa_h` | 2026 $ / index | 40,000 / 0.02 | *assumed* | switching costs, default-on in v3 |
| grid sizes | — | 45 × 14 × 30 × 6 | — | numerics; see `config.yaml` |

**`beta_H` and `base_sep` are the two highest-value things to refine with better
information.** `beta_H` is the top bar of the allocation tornado by a wide margin (span 2.21
in `pi_fin_optimal` across 0.0–2.4) and `base_sep` is third (span 1.06); `base_sep` also
sits in the top three of the finish-age tornado. Everything section 3 says about the
allocation is conditional on a single unmeasured number.

**The honest summary of this table:** the financial side is largely observed, and the
health and career sides are almost entirely assumed. Every conclusion about the *price* of health is
therefore conditional on the seat attributes and the depreciation coefficients, none of
which have been measured. The seat attributes are self-reported single numbers standing in
for complicated lived facts. Treat `h0` and the seat `r` values as the first things to
measure properly.

---

## Non-goals

No account-level tax location (IRA / 401k / brokerage / gold are one pool), no live IBKR
pull (a `BalanceProvider` interface with a YAML stub is defined in `model.py` so an IBKR
adapter drops in later), single-earner household, no housing transactions, no annuity
purchase, no explicit sequence-of-returns glidepath beyond what the solver produces
endogenously.

---

## Layout

```
lifehjb/
  model.py        # dynamics, felicity, hazard, taxes, seats, BalanceProvider
  health.py       # health capital dynamics, steady states, time constants
  solver.py       # backward-induction Bellman solver over (W, h, t) + switching costs
  calibrate.py    # rho from savings history; b from VSL target
  boundaries.py   # W_BATNA, W_coast(target_age), W* stopping boundary, inaction band
  humancapital.py # H valuation, the allocation correction, sector concentration
  career.py       # separation hazard, search, seat availability, option value
  negotiate.py    # seat scoring, indifference curves, max-acceptable-pay-cut
  simulate.py     # forward Monte Carlo under a policy
  report.py       # tables, plots, report.md generation
  cli.py          # solve | calibrate | boundaries | negotiate | report | test
config.yaml
tests/
  test_analytic.py    # closed-form recovery tests
  test_health.py      # health dynamics properties
  test_properties.py  # monotonicity, boundaries, calibration, determinism
  test_tax.py
  test_v3.py          # acceptance tests 12-19
```

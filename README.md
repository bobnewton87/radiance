# LifeHJB v2 — Personal Lifecycle HJB Console with Health Capital

> **This is a decision-support model. It is not financial advice and it is not medical
> advice.** It is a numerical solution to a stochastic optimal-control problem under a
> specific set of assumptions, several of which are self-reported and unmeasured. Its
> outputs are conditional on those assumptions being right. Read section
> [Provenance](#provenance) before acting on any number in it, and treat every parameter
> marked *assumed* as a hypothesis rather than a fact.

LifeHJB solves a finite-horizon stochastic lifecycle control problem with **health capital
that both depreciates and recovers**, mortality, and a discrete job-seat choice. It is
calibrated to one person and reports the optimal policy, three distinct wealth boundaries,
the steady-state health of every seat, and the dollar shadow price of health — the last of
which is the headline number used to evaluate real job offers.

Everything is in **real (inflation-adjusted) 2026 dollars**. No network access. Seeded and
deterministic. CPU only.

---

## Quick start

```bash
pip install -r requirements.txt
pytest -q                                          # 38 tests, ~2 min
python -m lifehjb --config config.yaml report      # writes out/report.md + 7 PNGs, ~100 s
```

Other entry points:

```bash
python -m lifehjb calibrate                 # rho from savings history, b from VSL
python -m lifehjb solve                     # shadow prices at the current state
python -m lifehjb boundaries                # the three wealth thresholds
python -m lifehjb negotiate --seat current350   # seat scores, pay-cut ceiling, break-even
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
| Where does each seat leave my health in the long run? | `h*(e)`, report §3 |

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
| 15M | −10.593 | 15.022M | $10,833 | $39,846 | **no** |
| 22M | −9.299 | 21.902M | $16,160 | $10,928 | yes |
| 30M | −7.290 | 29.985M | $21,370 | $1,465 | yes |

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

`python -m lifehjb report --config config.yaml` writes `out/report.md` plus seven PNGs:

1. **Executive summary** — current state, the three boundaries as multiples of `W`, the
   top-ranked seat, and `Λ_h`.
2. **The three wealth boundaries.**
3. **Per-seat table** with `h*` prominent.
4. **Indifference matrix** — the maximum acceptable pay cut, in consumption and in gross.
5. **Seat scores** `Theta(e)` with rank ranges and pairwise dominance across the 3×3 grid.
6. **Stopping boundary** `W*(t)` for ages 39–70 at two health levels.
7. **Monte Carlo** — 10,000 paths, seed 42, per fixed-seat policy and for the fully optimal
   policy.
8. **Sensitivity tornado** on median finish age, one parameter at a time.
9. **Parameter provenance**, with measurement priorities flagged.
   *Appendix A* — switching costs and the inaction band, when enabled.

Plots: `h*` by seat; h trajectories from `h0`; policy heatmap `e*(W,t)` at `h = 0.72`;
`c/W` vs age; wealth fan chart; `W*(t)`; sensitivity tornado.

Retirement spending is chosen by the solver — it approximates the mortality-adjusted annuity
rule on its own. `spend_base` is used **only** for the coverage metric, the boundary
calculations and the sensitivity sweep, and never enters the dynamics. That is why its
tornado bar has a span of exactly zero; a non-zero bar there would have meant a bug.

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

## Section 7 extension: switching costs

Behind `switching_costs.enabled` (default `false`). A seat change costs `κ_W` dollars
(search, relocation, forfeited variable comp; default 40,000) and `κ_h` of health (default
0.02, transition stress). The previous seat then enters the state and the seat choice
becomes a genuine optimal-stopping problem with hysteresis.

The **inaction band** is the share of the `(W, h)` grid where the frictionless policy would
move but the frictional one stays put — the real-options structure that explains why
rational people sit in suboptimal jobs longer than static scoring implies. At the defaults
it is about 28% of the grid starting from `renegotiated350`, and **0% starting from
`current350`**: the static gap there is too large for a $40,000 friction to hold you.

---

## Acceptance tests

`pytest -q` — 38 tests, all green. The eleven from the build prompt map as follows:

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

Two of these needed a stated reading rather than a literal one:

* **Merton (1)** — the production `π` grid has six nodes, far too coarse to resolve 0.48
  within ±0.07. The test refines the grid to 51 nodes. Grid resolution is numerics, not
  economics, so this is a legitimate test configuration rather than a weakened assertion.
* **Annuity (2)** — `c_t/W_t = 1/(remaining periods)` is the **zero-rate** case. With
  `rf = ρ = r > 0` the Euler equation gives `βR = 1`, so consumption is constant in level
  and the exact draw is the annuity factor `(1 − 1/R)/(1 − R^{−n})`, which collapses to
  `1/n` as `r → 0`. The test checks both: at `ρ = 0` it reproduces `1/n` on the nose, and at
  `ρ = 0.02` it matches the annuity factor to 3%.

Determinism (11) is checked on the `--fast` profile, which exercises the same code path and
the same formatting; the full profile takes 100 s per run and would make the suite
needlessly slow for no additional coverage.

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
| grid sizes | — | 60 × 14 × 30 × 6 | — | numerics; see `config.yaml` |

**The honest summary of this table:** the financial side is largely observed, and the
health side is almost entirely assumed. Every conclusion about the *price* of health is
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
  boundaries.py   # W_BATNA, W_coast(target_age), W* stopping boundary
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
```

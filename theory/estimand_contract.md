# Gate A estimand and probability-space contract

Status: **proved under the additional model stated below**. The adaptive claim in
the supplied manuscript remains **unproved**. This document changes neither the
scientific target silently nor the original theorem merely to accommodate code.
The first implementation is a separately identified, restricted experiment.

## Source convention and inspected files

All `paper/...:line` references in the Gate A audit refer to the **original ZIP
source**, before the Gate A patch. The ZIP SHA-256 and extraction destination are
in `source_manifest.json`; the source baseline and diff preserve these references.
Both compact and full sources were inspected: `main.tex:61–87`,
`full_working_draft.tex:61–86`, `sections/02_setup.tex:4–81`,
`03_method.tex:6–71`, `04_theory.tex:6–58`, `05_discover_repair.tex:4–37`,
`06_experiments.tex:4–45`, `appendix.tex:1–304`; their `sections/full/`
counterparts at lines `4–113`, `6–107`, `6–78`, `4–63`, `4–95`, and `1–304`;
and `RESEARCH_TODO.md:9–69,155–165`. The entire supplied master task was read;
Gates C–F and their large experiments are outside this run.

## Three different targets

1. **Original predictable path target.** Write
   `M_path = N^(-1) sum_u E[Z_u^oracle | F_(t(u)-1)]` as in compact setup
   lines 27–33 and full setup lines 37–44. This is generally random because
   histories include earlier actions/outcomes. It is not an unconditional
   stationary mean. Also, the displayed equation conditions on `F_(t-1)`, not
   `(X_u,F_(t-1))`. If the current context is not already measurable in that
   history, it is integrated out. The prose “observed context path” then needs
   an explicit pre-action sigma field, e.g. `H_t = sigma(F_(t-1), X_t, I_t)`.
   Replacing the conditioning field by `H_t` is a substantive estimand change
   that must be stated, not inferred from the phrase “predictable.”
2. **Gate B fixed-design local intervention target.** Condition on a valid
   exogenous design `D`. For each frozen `theta=(q,h)`, define
   `M_D(theta) = N^(-1) sum_u h_u[sum_s q_u(s) mu_u(s) - f_u]`,
   where `mu_u(s)=E[Y_u(s)|D]`. This is deterministic conditional on `D` and is
   the implemented estimand. Repeated predeclared context templates make each
   macro-block target identical to `M_D`. It coincides with the corresponding
   predictable target only in this restricted exogenous setting, with design
   already in the pre-action information. The certificate is explicitly not a
   proof for the adaptive target in item 1.
3. **Population target.** `E_D M_D(theta)` averages over a new design/context
   population. A conditional CI for `M_D` is not automatically a CI for this
   population mean. Random contexts must be included in a separately proved
   sampling model before using this interpretation.

## Gate B probability space, timing, and independence

The design `D` contains the full predeclared evaluation layout, block and cluster
membership, repeated context template, logging distributions, frozen `q,h,f`,
fixed nuisance prediction vectors, graph/coloring algorithm, confidence levels,
moment order, and deterministic MOM partition rule. It contains **no evaluation
assignment or outcome, future outcome-derived context, or fitted function trained
on evaluation data**. A separately sampled nuisance pilot can be included only
when conditionally independent of the entire evaluation experiment given the
exogenous design; Gate B can use a predeclared fixed bounded `mu_hat` instead.

There are `B` independent evaluation macro-blocks of exactly `n0` rows. In each
block there are `n0/chi` independent random clusters, each copied into `chi`
rows. An entire cluster's logging assignment and potential-outcome randomness
are independent of those in every other cluster and block, given `D`. Cluster
labels are unique across blocks. The same fixed context template is repeated
across blocks. No permanent random user effect crosses block boundaries.

Timing is: freeze `D` and family; generate each cluster's potential outcomes and
independent logging assignment; observe only `S` and `Y(S)`; score observed
rows; group **whole** blocks; compute certificates; finally join an oracle-only
truth object for diagnostics. The estimator may use known support, reward bounds,
and exact logged propensities. It must not receive true response probabilities,
potential-outcome arrays, the true target, or oracle-centered scores.

This construction proves the graph assumption: within each block the disjoint
union of `chi`-cliques is a sufficient dependency graph. Any two disjoint sets
with no connecting edge depend on disjoint independent cluster randomness.
Choosing one vertex from each clique therefore gives a mutually independent
color class. A correct edge list alone cannot establish that assumption for an
arbitrary observed dataset. A hidden cross-cluster shock would invalidate it.

## Identification and score

Assume local consistency `Y=Y(S)` and exposure completeness: two assignments
mapped to the same `s` have the same local potential outcome. Conditional on `D`,
logging assignment is independent of the potential outcomes and
`e_u(s)=P(S_u=s|D)`. Require `q_u(s)>0 => e_u(s)>0`; no numerical clipping is
permitted. This is the restricted version of compact setup lines 17–24 and
full setup lines 20–35.

With a fixed `mu_hat`,

`Z_u(theta) = h_u [sum_s q_u(s) mu_hat_u(s)
                    + q_u(S_u)/e_u(S_u) (Y_u-mu_hat_u(S_u)) - f_u]`.

Taking expectation under the exact logging mechanism cancels `mu_hat`:

`E[Z_u(theta)|D] = h_u [sum_s q_u(s) mu_u(s)-f_u]`.

For a fixed or independent-pilot `e_hat`, the conditional bias is
`h_u sum_s q_u(s)(mu_hat_u(s)-mu_u(s))(e_hat_u(s)-e_u(s))/e_hat_u(s)`.
This proves the algebraic DR identity in compact setup lines 35–44 and appendix
lines 21–49 under the stated conditioning. Exact `e` removes this bias, but does
not establish independence of scores that share outcome-trained nuisance fits.

## Known moment envelope

The initial certified model has `Y in [0,1]`, `mu_hat(s),f in [0,1]`, `|h|<=1`,
and a declared `1<p<=2`. For every row and candidate,

`|Z| <= 1 + q(S)/e(S)`,

`E[|Z|^p|D] <= A_u(theta)
 = 2^(p-1) [1 + sum_(s:e(s)>0) q(s)^p e(s)^(1-p)]`.

Terms with `q=e=0` contribute zero; target mass on zero logging support fails
identification. By convexity and conditional Jensen,

`E[|Z-E(Z|D)|^p|D] <= 2^(p-1)(E|Z|^p+|E Z|^p) <= 2^p A_u(theta)`.

Thus a known sufficient envelope is
`nu_p^p = max_(u,theta) 2^(2p-1)
 [1 + sum_s q_u(s)^p e_u(s)^(1-p)]`.
Candidate-specific maxima are also valid with the same simultaneous family
budget. This quantity uses design probabilities and bounds, not observed reward
tails or true outcome regression. It is deliberately conservative. A fixed
positive propensity floor gives a nonrandom envelope. A valid realized exogenous
design can instead yield a `D`-measurable envelope, but that does not justify a
uniform-in-design rate. Gate B does not equate finite unconditional moments under
unbounded `q/e` with this conditional envelope.

## Block targets, grouping, and explicit simultaneous CI

Require `E[bar Z_b(theta)|D]=M_D(theta)` for every block. Set `m=|Theta|`,
`delta_stat=alpha`, `K=ceil(8 log(2m/delta_stat))`; reject `B<2K`.
Partition all `B` complete blocks deterministically into `K` groups with sizes
`L_g in {floor(B/K),ceil(B/K)}`. No block is discarded and no clique is split
between MOM groups. Unequal group counts do not change the target because every
block has the same conditional mean. Put `L_min=floor(B/K)`.

For centered row scores `X_u`, von Bahr–Esseen with constant 2 inside each
independent color class, followed by convexity across at most `chi` color sums,
gives

`E[|bar Z_b-M_D|^p|D] <= 2 nu_p^p (chi/n0)^(p-1)`.

A second application across independent blocks gives

`E[|group_mean_g-M_D|^p|D]
 <= 4 nu_p^p (chi/(L_g n0))^(p-1)`.

Set

`r = 32^(1/p) nu_p (chi/(L_min n0))^((p-1)/p)`.

Markov bounds each group's two-sided failure probability by `1/8`.
Conditional independence of the group vectors implies independence of their bad
indicators for each candidate. Hoeffding gives
`P(sum_g bad_g >= K/2 | D) <= exp(-9K/32)`.
If strictly more than half the groups are good, any usual median (including the
average of the two central order statistics when `K` is even) lies in
`[M_D-r,M_D+r]`. Union bounding yields

`P(exists theta: |median_g group_mean_g(theta)-M_D(theta)|>r | D)
 <= m exp(-9K/32) <= delta_stat`.

Indeed, writing `x=2m/delta_stat`, `K>=8 log x` implies
`m exp(-9K/32) <= m x^(-9/4) = (delta_stat/2)x^(-5/4) <= delta_stat`.
The choice of `K` is more conservative than necessary, but explicit and valid.
The guarantee is simultaneous over the frozen family at each requested level,
not a claim that the realized coverage equals exactly 90% or 95%.

## Error budgets and statuses

In this model `r_nuis=0`, `r_drift=0`, and `epsilon_coup=0`, by exact `e`, stable
block targets, and actual independence. A 95% family CI therefore uses
`alpha=.05`; a 90% family CI uses `.10`. For a future extended theorem with
proved coupling and random nuisance/drift/tail-bound events, the total failure
budget must satisfy

`delta_stat + epsilon_coup + delta_nuis + delta_drift + delta_scale <= alpha`.

Nuisance/drift bounds enter the radius; their failure probabilities enter this
budget. A coupling failure probability is never a numeric radius. For an actual
coupling, derive the concentration bound for the independent copies under their
unconditional/conditional-on-`D` law and transfer by
`P(failure_original)<=P(failure_copy)+P(copy != original)`; do **not** condition
on successful coupling and assert the copies remain independent.

`CERTIFIED` is justified only under the declared proof model with all numerical
inputs established. Missing or estimated scales, mutually trained cross-fits,
unknown drift, unsupported graphs, or unknown mixing rates cannot enter this
certified API. An unsupported model is `UNVERIFIED_ASSUMPTION`; unsupported
target mass or infeasible block/confidence settings are `NOT_CERTIFIABLE`.
Sensitivity analysis, if separately implemented later, is `SENSITIVITY_ONLY`.

## Subgroup mass and intervention scope

For a binary fixed-design auditor, `pi_D=N^(-1)sum_u h_u` is exactly observed
before actions: its uncertainty radius is zero. For positive `pi_D`, a signed
ratio CI is `[lo/pi_D,hi/pi_D]`; a bound on the absolute subgroup residual is
`(|estimate|+r)/pi_D`. If `pi_D=0`, abstain. Nonzero count does not ensure target
support or a useful precision; retain propensity and radius diagnostics.
If instead `pi=E h(X)` is the target, observed frequency is only an estimator and
requires a separate population sampling theorem. If current `h` is not measurable
in the original history, the original predictable denominator is likewise
`N^(-1)sum E[h_u|F_(t-1)]`, not the realized count.

For a full assignment `A` and exposure `g(A)`,
`e_u(s)=sum_(a:g_u(a)=s) pi_log(a|D)`; the analogous marginalization defines `q`.
An ordered two-item Plackett–Luce slate has
`P((i,j))=w_i/(sum_k w_k) * w_j/(sum_(k!=i)w_k)`.
A mixture with uniform slates is formed over the same complete-slate sample
space. It is not a mixture of a single-item softmax and a slate distribution,
and joint exposure probabilities are not products of item marginals.

Finally, pessimistic selection algebra (compact repair lines 29–36; appendix
lines 222–239) is valid **on a simultaneous event for these specified moments**.
It certifies local intervention feasibility on this fixed design/logging path.
It makes no claim about future policy-induced contexts, long-run dynamics, or
pathwise closed-loop deployment safety. Error spending over epochs
`alpha_e=alpha_total/[e(e+1)]` is valid only if each epoch has the needed
conditional guarantee given its past and the expenditure is preallocated.

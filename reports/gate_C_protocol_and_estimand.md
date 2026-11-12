# Gate C protocol and estimand — C-PREFLIGHT

This phase verifies a frozen six-cell synthetic protocol and small CPU batch
execution. It does not run C-STAT, C.2 power sweeps, C.3 discovery or C.4 repair.
The full preregistration is `gate_C_preregistration.md`; numerical evidence and
phase decision belong in `gate_C_report.md`. References below use the Gate C
source frozen for preflight, whose exact SHA is recorded in the run manifest.
Existing A+B+C0 proof files are unchanged from `3f8902d`.

## Target and legitimate conditioning

The certified target is the conditional raw-row window moment

    M_D(q,h;f) = N^-1 sum_u h(x_u) [sum_s q(s) mu_u(s) - f].

D contains only exogenous layout/graph, logging law, frozen q/h family,
reference, declared outcome family and its known parameters, and predeclared
nuisance predictions. It contains no future-outcome-derived contexts or fitted
evaluation history. This is a fixed-design conditional target, **not a fully
adaptive pathwise or long-run deployment target**. q and f are constant across
rows within a candidate; h is either all or the fixed context-1 indicator.
All rows are retained. The oracle integrates actual row/context counts, rather
than substituting a population subgroup prevalence
(`comet/gate_c_truth.py:13–29`; `tests/test_gate_c_model.py:52–84`).

In the balanced primary designs, M_all=.025+.425 q1 and
M_group1=.05+.225 q1. These formulas are test/evaluation fixtures, never estimator
inputs. Subgroup mass is known exactly from D: 1 or .5. The current constraints
are numerator constraints M_D<=.2*pi_h. No unknown population mass is estimated
or divided into a ratio. A zero-mass ratio would require separate handling.

Every method at both confidence levels completes before the runner imports
and calls the oracle (`experiments/gate_c_preflight.py:141–172`). The certifier
has no oracle/simulation imports, including its transitive imports
(`tests/test_gate_c_methods.py:182–195`). Oracle calculation is analytic, with
zero integration/Monte Carlo error mathematically and ordinary floating-point
arithmetic at export. The seven-stream manifest reserves but does not consume
truth-MC randomness.

## Assumptions mapped to implementation and proof

| Obligation | Construction and verification |
|---|---|
| Exact exposure e and support | Binary S=A; e1 is fixed by context and e0=1-e1. The new sampler uses an integer lottery for the exact dyadic representation of e1 (`comet/gate_c_simulation.py:21–32,64–71`). Logged e, action/exposure equality and provenance are checked at `comet/gate_c_contract.py:145–157`. Probability/positive-support checks reuse `comet/schema.py:53–78` and `comet/dr_scores.py:15–24`. Integer-boundary/enumeration tests are `tests/test_gate_c_model.py:31–49`. |
| Sufficient conditional graph | Each independent cluster's entire randomized record is copied chi times, with fresh cluster draws in every block (`comet/gate_c_simulation.py:57–85`). Nonadjacent disjoint sets involve disjoint independent cluster randomness, proving conditional vector independence; see `theory/gate_c_heavy_tail_contract.md:9–43`. The graph is constructed and its coloring verified, rather than accepting a smaller chi (`comet/gate_c_methods.py:201–205`; `tests/test_gate_c_methods.py:103–111`). |
| Nuisance and pilot separation | mu_hat=(.5,.5) is fixed before all evaluation randomness. No nuisance or discovery pilot is fitted in preflight. Other fixed bounded fits may be arbitrarily misspecified without breaking exact-e DR expectation (`tests/test_gate_c_model.py:87–109`). Evaluation-trained fits are outside this API (`comet/gate_c_contract.py:54–55,158–159`). |
| Frozen real family | A has one q/h pair; B–F have eight distinct q values crossed with all/group1, m=16. Their candidate identifiers and analytic targets are distinct (`tests/test_gate_c_model.py:154–164`). Family equality and immutability are checked at `comet/gate_c_contract.py:137–138`. |
| MOM common target | Primary blocks repeat the same context counts and response law, hence equal block targets. Unequal MOM group sizes are permitted because all group targets agree, with L_min>=2 and no dropped blocks (`theory/exact_binomial_mom.md:18–59,89–118`; `tests/test_gate_c_methods.py:114–128`). Actual exogenous drift is tested separately and refuses MOM (`tests/test_gate_c_methods.py:131–136`). |
| Known conditional moments | A–E reuse the C0 bounded envelope. F uses the proved Pareto conditional envelope from design-known p, q/e, mean-class/nuisance bounds and noise moment (`comet/gate_c_contract.py:93–124`; `theory/gate_c_heavy_tail_contract.md:113–162`). No empirical tail scale or true response location enters the radius. |
| Confidence budget | Every method uses its own frozen q/h family and alpha, .05 primary and .10 secondary. The graph mean radius is sqrt(mV/alpha); the exact MOM K uses the exact binomial tail with fixed eta=1/8. There is no simultaneous guarantee across post-hoc method choices or both reported levels (`comet/gate_c_methods.py:117–181,189–194`). Coupling failure and nuisance/drift radii are zero by this construction. |

The e0 complement, score operations and radii are stored in ordinary floating
point. The integer lottery removes fixed-grid threshold distortion for the
declared e1; it does not assert interval-arithmetic guarantees for every final
rounding bit. No numerical propensity floor, estimated e or self-normalization
is used. The primary experiment has no joint-slate reduction beyond S=A;
preserved categorical/slate tests do not expand this simulator's scope.

For the weak-design e1 values, the stored floating e0 minus the exact symbolic
complement is `-5/576460752303423488` at e1=.01 and
`-5/288230376151711744` at e1=.02; the absolute difference is below 2e-17.
The design-only rational diagnostic records these representation differences.
Here exact e means the known randomization law, not an estimated propensity;
scores, radii and target exports follow the existing ordinary-float convention.
The theorem is not a machine-verified outward-rounding theorem. No cell or
parameter was changed using outcomes to hide this numerical convention.

## Heavy-tail F and method applicability

F uses Y(s)=mu_s(x)+R*.1*U^(-1/1.75), with independent fair sign R and uniform U
for each cluster/exposure. The ideal law is unbounded with finite p=1.5 moment
and infinite second moment. Its known noise moment is
`k_p=1.75*.1^p/(1.75-p)`, hence `k_1.5=7*.1^1.5`. A valid centered score bound is

    nu_p^p = 2^(2p-1) [1 + 2^(p-1)(1+k_p) sum_s q(s)^p e(s)^(1-p)].

The full derivation uses the valid centering factor 2^p and conditional
randomization; it does not replace a centered moment with a raw moment without
a constant (`theory/gate_c_heavy_tail_contract.md:113–162`). This is a new
unbounded-reward DGP, not the C0 bounded-outcome p=1.5 cell. F's positive
53-bit inverse-CDF grid is a finite numerical approximation. Symmetry preserves
zero noise mean; a right Riemann sum is bounded by the ideal p-moment integral.
The finite machine law is not literally infinite-variance. Rewards are not
clipped into [0,1] (`theory/gate_c_heavy_tail_contract.md:202–237`).

| Method | A–E | F | Meaning |
|---|---|---|---|
| orig_mom | CERTIFIED | CERTIFIED | Existing finite-p theorem with the appropriate known envelope and common block target. |
| exact_binomial_mom | CERTIFIED | CERTIFIED | Same target/moment theorem, exact-binomial K, fixed eta. |
| bounded_graph_chebyshev | CERTIFIED | NOT_APPLICABLE | The bounded-residual variance proof does not apply to F, even if one observed sample lies inside [0,1]. |
| ips, dm, dr | POINT_ONLY | POINT_ONLY | No confidence interval or certified decision is assigned. DM may be misspecified. |
| full_feasible_range | CERTIFIED, vacuous | CERTIFIED, vacuous | A known conditional-mean-class bound, not a concentration result. |

F's range baseline is justified because **conditional means**, not outcomes,
belong to the declared class [0,1]. Thus M_D belongs to
[-pi_h f,pi_h(1-f)] in both families. Records explicitly set
`target_range_is_outcome_support=False` for F. This range uses no oracle
location. Tests enforce the distinction and F's unconditional method
inapplicability (`tests/test_gate_c_methods.py:47–72,198–205`). Raw intervals and
their intersections are separate. A full-range intersection is vacuous;
an empty one cannot issue a decision. Clipped-weight methods, empirical-scale
methods and optional heuristic intervals are not exposed in this protocol.

## Streams, paired computation and preflight limit

The SHA-256-128-v1 seed mapping separates phase, cell, replication and role
(`comet/gate_c_seeds.py:4–35`). All 6,000 future confirmatory IDs and twelve
preflight IDs are allocated before any primary preflight outcomes. Seed
uniqueness is checked by the runner. Only preflight IDs can be selected by
this entry point (`experiments/gate_c_preflight.py:80–126`).

| Role | Use in this fixed-design protocol |
|---|---|
| design_context | Reserved; layout is deterministic. |
| graph_shocks | Reserved; graph structure is fixed and the within-clique shared draw is already the potential-outcome draw. |
| logging_exposure | Active, exact binary randomization. |
| potential_outcomes | Active, Bernoulli or Pareto potential outcomes; shared only inside the declared clique. |
| nuisance_discovery_pilot | Reserved; no fit or discovery is performed. |
| evaluation_outcomes | Reserved; consistency reveals Y(S), without a second observation-noise draw. |
| truth_mc | Reserved; exact analytic integration is used. |

These are distinct allocated streams, not seven falsely claimed active
experiments. Deterministic tests verify active-stream separation and unchanged
outputs when only reserved streams change (`tests/test_gate_c_model.py:167–187`).
Both levels and all methods use the same logged replicate. Two full-N logs per
cell are an explicit integration-only choice under the user's current scope;
they cannot estimate coverage or power precisely. Successful checkpoint resume,
actual resource measurements, failed commands and the final PASS/BLOCKED
decision are reported from the executed job, not inferred from this protocol.

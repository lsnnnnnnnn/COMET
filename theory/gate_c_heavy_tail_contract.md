# Gate C preflight: conditional target, genuine heavy-tail model and known envelope

Status: **proved under the stated independent exogenous-clique model**. This
extends the registered synthetic data contract to unbounded rewards while
reusing the already-proved finite-p MOM theorem and its constants. It does not
change the A+B+C0 files, prove arbitrary adaptive-history concentration, or
authorize a bounded-reward variance bound for an unbounded-reward law.

## Frozen design and probability space

Let D contain the complete exogenous design: B, n0, chi, a repeated context
layout, logging probabilities, the finite policy/auditor family, reference f,
the outcome-family and known tail parameters, and fixed nuisance predictions.
None is computed from evaluation actions, rewards or oracle targets. This
implementation uses predeclared nuisance values, not a fitted pilot. An
independent pilot could enter the existing theorem only with an appropriate
conditional independence construction; no learned-nuisance API is added here.

There are n0/chi clusters in each macro-block. Cluster c has context x=c mod 2.
All chi row copies of a cluster share one randomized exposure and the potential
outcomes of that cluster. Independent clusters, including clusters in different
blocks, have independent logging and potential-outcome randomness conditional
on D. Define S=A in {0,1}, with

    P(S=1 | D) = e1(x),      e(0)=1-e1(x), e(1)=e1(x).

Both exposures are supported in every primary cell. Every q is the distribution
(1-q1,q1) on this same state space. Thus e is an exact exposure law, with no
joint-slate approximation or propensity fitting. Existing slate enumeration
tests remain intact, but this new simulator claims only this binary S=A model.
The subtype validation checks finite positive support and exact agreement of
the logged representation with the declared design.

A macro-block's sufficient dependency graph is the disjoint union of complete
chi-cliques. Nonadjacent disjoint vertex sets involve disjoint collections of
clusters. Their score vectors are measurable functions of disjoint independent
cluster randomness and fixed D, and are therefore conditionally independent.
This proves the stronger dependency-graph property, not merely pairwise
uncorrelatedness. A proper coloring takes one row from each clique in each
color; the existing graph constructor/color verifier supplies chi colors.
There is no permanent shock shared across blocks. The common potential-outcome
draw of a cluster is its latent shared shock; it is not an observed graph edge
substituted for a stochastic model.

## Potential outcomes and exact conditional target

In the stable model the response locations are

    mu(0,0)=.2, mu(0,1)=.6, mu(1,0)=.35, mu(1,1)=.8.

These are parameters of the potential-outcome generator. The optional
deterministic drift descriptor adds +.05 in even-numbered blocks and -.05 in
odd-numbered blocks. All resulting locations remain in [0,1]. It is used only
to test method applicability; the six primary cells are stable. For bounded
outcomes, a single cluster-specific uniform couples the two Bernoulli
potential outcomes and gives each its stated conditional mean.

For the heavy family, independently for each cluster and exposure, let

    epsilon = R sigma U^(-1/a),
    P(R=+1)=P(R=-1)=1/2, U uniform on (0,1), R independent of U,
    Y(s) = mu(x,s) + epsilon_s.

The primary F declaration uses a=7/4, sigma=1/10 and p=3/2. This is a
deliberately chosen analytically tractable heavy-tail family, permitted by the
master's example-based tail specification; it is not the C0 bounded-reward
p=1.5 stress cell. No evaluation results or oracle target selected a or sigma.
The ideal law has unbounded rewards, zero-mean noise and infinite variance.

For a>1, E|epsilon| is finite, and sign symmetry gives E epsilon=0. Consequently
E[Y_u(s)|D]=mu_u(s) in both reward families. The oracle target is exactly

    M_D(q,h;f) = N^(-1) sum_u h(x_u) [sum_s q(s) mu_u(s) - f].

Here q is constant over rows within each candidate; f is the frozen scalar
reference; h is all or the context-1 indicator, fixed before actions. There
are eight distinct q values and two distinct auditors in m=16, not sixteen
copies of one auditor. The oracle sums the actual finite design, including an
unequal context count if n0/chi is odd. This is neither a population-average
target nor the realized potential-outcome average nor post-deployment utility.
The equal-size clique representation cancels chi in the target average; it
does not cancel chi from uncertainty.

For the balanced primary layout, exact closed forms are

    M_D(q,all)    = .025 + .425 q1,
    M_D(q,group1) = .05  + .225 q1.

`comet/gate_c_truth.py:exact_targets` integrates the generator's conditional
response locations and performs no Monte Carlo. Its integration error is zero
mathematically, with ordinary floating-point arithmetic at export. No truth-MC
standard error is estimated. The evaluator is imported only for final metrics
and tests, after certificates have been produced. The generator itself does
not call this target evaluator and logs contain neither counterfactual targets
nor unobserved potential outcomes nor response locations.

## Exact-e DR expectation, including misspecified frozen fits

With fixed mu_hat(s) in [0,1], fixed reference f in [0,1], and |h|<=1, write

    Z = h [d-f + q(S)/e(S)(Y-mu_hat(S))], d=sum_s q(s)mu_hat(s).

Conditional randomization and consistency imply

    E[Z|D] = h [d-f + sum_s q(s)(mu(s)-mu_hat(s))]
           = h [sum_s q(s)mu(s)-f].

Integrability holds in the heavy family because a>1 and finite positive
propensities make the finite-state importance weights finite. No nuisance
consistency or correct response fit is needed. This identity alone does not
justify concentration with evaluation-trained fits; those are refused.

## Known conditional p-moment envelope

For p<a, direct integration gives

    k_p := E|epsilon|^p
         = sigma^p int_0^1 u^(-p/a) du
         = a sigma^p/(a-p).

The integral diverges at and above p=a. In primary F,
k_(3/2)=7*(.1)^(3/2), whereas the second-moment integral diverges because 2>a.
This is a **conditional** bound given D: the noise distribution/scale do not
change with a context or an evaluation history. It is not an empirical tail
estimate or an unconditional integrated envelope.

For the declared location class 0<=mu(s)<=1 and fit class 0<=mu_hat(s)<=1,

    E[|Y(s)-mu_hat(s)|^p |D]
       <= 2^(p-1) [|mu(s)-mu_hat(s)|^p + E|epsilon_s|^p]
       <= 2^(p-1) (1+k_p).

Let J_p(q,e)=sum_{s:q(s)>0} q(s)^p e(s)^(1-p), which is known from D.
Since |d-f|<=1 and |h|<=1, conditional randomization gives

    E[|Z|^p|D]
       <= 2^(p-1) [1 + 2^(p-1)(1+k_p) J_p(q,e)].

Finally use the valid centering bound, proved by convexity and Jensen,

    E[|Z-E(Z|D)|^p|D]
      <= 2^(p-1) [E(|Z|^p|D)+|E(Z|D)|^p]
      <= 2^p E[|Z|^p|D].

Therefore a known sufficient centered envelope is

    nu_p(q,e)^p = 2^(2p-1) [1 + 2^(p-1)(1+k_p) J_p(q,e)].

This derivation does not use the false inequality that a centered p-moment is
always at most the raw p-moment. The formula uses the declared mean-class
bounds, p, tail parameters and q/e; it never reads true response locations,
observed rewards, scores, a sample tail estimate or the oracle target. The
implementation takes the maximum over the exogenous contexts. Small positive
e may make this finite envelope enormous; positivity is not useful overlap.
At p>=a the heavy-cell validator returns NOT_APPLICABLE rather than substituting
a sample estimate. Numerical overflow also refuses a finite certificate.

For bounded Bernoulli rewards, retain the sharper existing envelope

    nu_p^p = 2^(2p-1) [1+J_p(q,e)]

because |Y-mu_hat|<=1 directly. No old formula or theorem statement is changed.

## Applicability to the existing finite-p MOM theorem

In stable cells each block repeats the same design/context counts and response
law, so every block's average conditional target equals M_D. The preceding
known row envelope and the sufficient clique graphs satisfy the existing
theorem's conditional assumptions. Two von Bahr–Esseen steps give group moment
constant 4. The old K rule and the exact-binomial rule use the already-proved
radius `32^(1/p) nu_p (chi/(L_min*n0))^((p-1)/p)`, with all complete blocks
retained and L_min>=2. Failure probabilities, finite-family multiplicity and
eta=1/8 are unchanged. There is no coupling failure, nuisance radius or drift
radius in a primary cell.

Drifting exogenous block means do not satisfy the MOM common-target premise.
The drift descriptor is therefore NOT_APPLICABLE to either MOM method without
a separate proved drift debit. It still meets the bounded graph-mean theorem
when the reward family is Bernoulli: the raw-row mean's expectation is the
correct heterogeneous-window average. All heavy-family cells are
NOT_APPLICABLE to the existing bounded graph Chebyshev certificate, regardless
of whether one realized sample happened to lie in [0,1]. The residual bound
|Y-mu_hat|<=1 fails for that law. No estimated variance or new unbounded-variance
theorem is silently substituted.

## Known target range

The **declared conditional mean class** is [0,1] for both families. For binary
h with fixed design mass pi_h and scalar f,

    -pi_h f <= M_D(q,h;f) <= pi_h(1-f).

Thus the full-feasible-range reference and intersection with these bounds are
valid even for F, although F's observed outcomes are unbounded. This is a
mean-class guarantee, not an assertion that heavy outcomes have bounded
support. The record field `target_range_is_outcome_support` is false for F.
The target range uses only known class bounds and exact design mass, not the
oracle's particular response means. Its diameter is pi_h. Zero subgroup mass
does not identify a subgroup ratio. The preflight reports numerator moments
and known masses, not ratios with estimated denominators.

## Sampling, seed separation and finite arithmetic

The manifest allocates seven distinct domain-separated seed roles:
design_context, graph_shocks, logging_exposure, potential_outcomes,
nuisance_discovery_pilot, evaluation_outcomes, truth_mc. In the fixed-design
model only logging_exposure and potential_outcomes are consumed. Design and
graph structure are deterministic; cluster potential outcomes already supply
the common within-clique randomness. Nuisance is predeclared, evaluation reveals
the generated potential outcome Y(S) by consistency, and truth is analytic.
The remaining roles are reserved and explicitly unused, not aliases of active
streams. There is no hidden nuisance/discovery fit. Different replication and
phase namespaces receive separate seeds; preflight does not consume the
reserved confirmatory streams.

The new logging sampler uses `float(e1).as_integer_ratio()` followed by an
unbiased integer lottery `rng.randrange(denominator)<numerator`, rather than
thresholding a fixed 53-bit uniform at e1. Bernoulli potential outcomes use a
single uniform integer on the largest of their power-of-two denominators,
thereby preserving the common-uniform coupling and each declared floating
response mean. The complement e(0)=1-e1 and scores/radii are represented in
ordinary floating-point arithmetic; they are not interval-arithmetic proofs
of every final rounding bit. No propensity floor or empirical e is used.

For Pareto generation the positive grid U=(J+1)/2^53, J uniform on
{0,...,2^53-1}, excludes U=0 without clipping a realized reward. The independent
fair sign preserves exact zero noise expectation. Since u^(-p/a) is decreasing,
the grid average is a right Riemann sum bounded above by its continuous
integral. Hence the stated ideal k_p is also a conservative upper bound for the
implemented finite-grid noise p-moment (apart from ordinary arithmetic
rounding). The ideal model has infinite variance; a finite floating-point
simulation does not literally have unbounded representable support or infinite
variance. Reports must not conflate those statements. It nevertheless samples
unbounded-law heavy-tail rewards without clipping them into [0,1], so the
bounded-reward certificate remains inapplicable. Tests check inverse-tail
behavior, sign symmetry, the moment-domain boundary and finite-grid upper bound,
not a noisy empirical claim that a finite sample proves infinite variance.

## Tests and implementation boundary

The new contract module imports neither the simulator nor the truth evaluator.
The certified-method module imports the contract, not the oracle. The generator
returns only existing `LoggedEvaluation`/`LoggedRow` inputs. Deterministic tests
cover exact target formulas, unequal context weights, odd-B drift averaging,
DR enumeration under arbitrary frozen nuisance, p-moment calculations and
failure thresholds, dyadic Bernoulli sampling boundaries, separate seed roles,
genuine distinct family members, exact clique copies, and observable guard
failures. There are no assertions that small-sample empirical coverage exceeds
nominal. Model labels cannot expose every hidden dependence or training leak;
the proof requires the actual declared DGP, not merely passing a schema check.

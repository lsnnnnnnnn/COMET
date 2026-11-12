# Gate C0: bounded-outcome graph variance certificate

**Status: proved under the explicit exogenous-design model below.** This is a
different estimator and theorem from the finite-p graph/block MOM certificate.
It does not establish arbitrary adaptive-path or deployment safety. Graph
coloring plus Chebyshev is a standard concentration argument, not a claim of
major theoretical novelty.

The audit baseline is experiment commit `d11a36f`. Relevant implementation
locations at that baseline are `comet/dr_scores.py:26–42` (DR score),
`comet/certification.py:15–46` (registered-model validation),
`comet/certification.py:89–93` (computed graph/color count), and
`comet/schema.py:33–77` (predeclared design). The Gate A probability model is
stated in `theory/theorem_to_code_contract.md`. This document proves a new
variance route without modifying that original theorem's assumptions or saved
results.

## Model and exact target

Let D contain only an exogenous design fixed before evaluation randomness and,
optionally, a nuisance pilot independent of the entire evaluation experiment
conditional on that design. Conditional on D:

1. The B evaluation-block score vectors are independent. Inside block b a
   **sufficient conditional dependency graph** has a verified proper coloring
   with chi_b colors. Disjoint vertex sets without connecting edges have
   independent score vectors. Shared identifiers alone are not a proof.
2. The finite family Theta, of size m, is frozen. Each q_u is a nonnegative
   distribution on the same finite exposure state space as the exact logging
   law e_u. Every q-supported state has e_u(s)>0.
3. Potential rewards satisfy 0<=Y_u(s)<=1, consistency holds, and assignment is
   conditionally independent of potential outcomes given D. Define
   mu_u(s)=E[Y_u(s)|D].
4. h_u, f_u and mu_hat_u(s) are D-measurable, with |h_u|<=1 and
   0<=mu_hat_u(s)<=1. The implementation uses fixed fits and binary h. A fit
   that is merely predictable along an adaptive evaluation history is not
   automatically covered: conditioning on its whole realized fitted path may
   destroy the block-independence or mean statements required here.

For N retained rows, let

    Z_u = h_u [sum_s q_u(s) mu_hat_u(s) - f_u
               + q_u(S_u)/e_u(S_u) (Y_u-mu_hat_u(S_u))],
    M_D(theta) = N^(-1) sum_u h_u [sum_s q_u(s) mu_u(s)-f_u].

The same exact-e DR calculation as Gate A gives E[Z_u|D] equal to its summand
in M_D. Thus the ordinary raw-row sample mean estimates exactly M_D. Unlike
MOM, this fact does **not** require all blocks to have equal target means.
The theorem allows different block sizes and heterogeneous fixed-design means;
the initial registered simulator/API still uses the original equal-block,
repeated-context stable-target design. It does not silently expose a new generic
data model just because the theorem permits a wider one.

## Lemma 1: a known conditional row variance envelope

For each row and candidate, set

    v_u(theta) = h_u^2 sum_{s:e_u(s)>0} q_u(s)^2/e_u(s).

Then Var(Z_u|D)<=v_u. To prove it, write the D-measurable direct term as d_u
and the random residual term as

    R_u = q_u(S_u)/e_u(S_u) (Y_u-mu_hat_u(S_u)),
    Z_u = h_u (d_u+R_u).

Since both Y and mu_hat lie in [0,1], |Y-mu_hat(S)|<=1. Consequently

    Var(Z_u|D) = h_u^2 Var(R_u|D)
      <= h_u^2 E[R_u^2|D]
      = h_u^2 sum_s e_u(s) [q_u(s)/e_u(s)]^2
                  E[(Y_u-mu_hat_u(s))^2 | S_u=s,D]
      <= h_u^2 sum_s q_u(s)^2/e_u(s) = v_u.

This proof never substitutes a raw moment envelope for a centered variance.
Exchangeability is required for the DR target identity; bounded observed
residuals already suffice for this variance inequality. The fitted response may
be arbitrarily misspecified within [0,1], provided it satisfies the conditioning
and separation requirements. e(s) must be the exact exposure-state probability,
including marginalization of a full joint assignment when appropriate.

The envelope is known from pre-outcome design. It does not use oracle response
means or an empirical variance. A finite supported realized design has finite
v in exact arithmetic, but random propensities approaching zero need not admit
a nonrandom uniform conditional envelope. Small e can make the radius useless;
support positivity does not imply useful precision. Numerical overflow causes
explicit refusal rather than clipping e or returning an infinite certificate.

## Lemma 2: graph and independent-block variance reduction

Center each row X_u=Z_u-E[Z_u|D]. In block b, let C_bc be its color classes and
T_bc=sum_{u in C_bc} X_u. Strong graph sufficiency implies mutual conditional
independence inside each color class, so

    E[T_bc^2|D] = sum_{u in C_bc} Var(Z_u|D).

The different color sums need not be independent. Pointwise Cauchy–Schwarz gives
(sum_c T_bc)^2 <= chi_b sum_c T_bc^2. Hence

    Var(sum_{u in b} Z_u |D) <= chi_b sum_{u in b} v_u.

Actual conditional independence of the blocks, not merely within-block
coloring, now implies

    Var(Mhat_mean(theta)|D)
      = N^(-2) sum_b Var(sum_{u in b} Z_u |D)
      <= V_theta := N^(-2) sum_b chi_b sum_{u in b} v_u.

Every retained row appears once. No group count K, group dropping, or stable
group-mean argument is involved. A missing cross-block permanent shock makes
the variance-additivity equality invalid and is outside the model. A caller
cannot replace chi_b by an unverified smaller number: the implementation
constructs the registered clique graph and checks its proper coloring.

## Theorem: simultaneous graph Chebyshev intervals

Fix alpha in (0,1) before evaluation. For every theta in the frozen family,
define

    r_theta = sqrt(m V_theta / alpha),
    I_theta = [Mhat_mean(theta)-r_theta, Mhat_mean(theta)+r_theta].

Then P(for every theta: M_D(theta) in I_theta |D)>=1-alpha. For V_theta>0,
conditional Chebyshev gives

    P(|Mhat_mean-M_D|>r_theta |D)
      <= Var(Mhat_mean|D)/r_theta^2 <= alpha/m.

If V_theta=0 the centered estimator is zero almost surely, and r_theta=0 is
valid directly. A union bound gives the family statement, without requiring
independence between candidates. Integrating over a legitimate D gives the same
unconditional coverage for the **random fixed-design target M_D**, not for an
unconditional superpopulation target substituted in its place.

There is no nuisance bias radius with exact e and a permissible fixed fit, no
MOM drift correction, and no coupling failure in this independent-block model.
If any additional random envelope/pilot event requires a failure allowance, it
must be spent from alpha in a separate theorem. The current implementation
accepts no unknown coupling, estimated-scale or drift-budget knob.

For a binary fixed-design auditor, the feasible numerator interval is
[-N^(-1)sum_u h_u f_u, N^(-1)sum_u h_u(1-f_u)], with diameter
N^(-1)sum h_u. Intersecting a valid CI with this known support preserves coverage
because the target lies in the support surely. Store raw and intersected bounds
separately; a full-support intersection is vacuous even if coverage is perfect.
An empty intersection is an empty confidence set on a coverage-failure event,
not permission to fabricate a nonempty interval. A subgroup ratio additionally
requires positive known subgroup mass; mass zero is ratio nonidentification.

## Optional clipping: proved bias and variance, not a C0 certified API

For a positive finite cap c fixed given D, replace q/e in the augmentation by
w_c(s)=min(q(s)/e(s),c). Let t_s=(q(s)-c e(s))_+. Taking the exact expectation,

    E[Z_{u,c}|D] - m_u
      = h_u sum_s [q_u(s)-e_u(s)w_c(s)] [mu_hat_u(s)-mu_u(s)]
      = h_u sum_s t_s [mu_hat_u(s)-mu_u(s)].

Since the two regressions belong to [0,1], the absolute raw-row mean bias obeys

    |E[Mhat_c|D]-M_D| <= b_c
      := N^(-1) sum_u |h_u| sum_s (q_u(s)-c e_u(s))_+.

The previous residual argument gives

    Var(Z_{u,c}|D) <= v_u(c)
      := h_u^2 sum_s e_u(s) min(q_u(s)/e_u(s),c)^2.

Apply the same graph/block reduction to obtain V_theta(c). Conditional Chebyshev
and the deterministic triangle inequality yield radius
sqrt(m V_theta(c)/alpha)+b_c for the original target, not merely the clipped
estimand. Clipping without b_c would generally be invalid.

A cap selected solely from D by minimizing this proved total radius over a
predeclared finite grid is fixed in the conditional proof and needs no extra
selection union bound. A cap selected using certification outcomes or oracle
truth has no such justification; either use an independent pilot preserving
the evaluation law or simultaneous coverage across all tested caps (and pay
the resulting multiplicity). The same warning applies to post-hoc selection
of methods or K. A missing-support state q>0=e remains nonidentified and is
rejected even though a different partial-identification analysis might exist.

C0 implements the **unclipped** variance route only. The clipping formula is
verified by deterministic categorical enumeration in the unit tests and saved
as a future option, not exposed as an additional certified method or tuned in
the pilot.

## Implementation and testing contract

`comet/bounded_variance.py` exports:

    row_variance_envelope(q, e, h=1.0) -> v
    graph_variance_bound(row_envelopes, graph) -> (bound, chi_used)
    certify_bounded_graph(log, alpha=0.05) -> list[certificate dict]

The certificate method is `bounded_graph_chebyshev`; it reports the design
variance bound V, multiplier m/alpha, p_declared=2 justified by bounded rewards,
actual graph count, and all retained rows. K/L_min are null because this method
does not use MOM. The API shares the existing registered-DGP validation and
refuses mismatched or unknown model tags. It does not detect every mislabeled
hidden shock from its observed realization: correctness is conditional on the
declared DGP, not conferred by passing schema validation.

Deterministic tests cover row DR expectation and variance under misspecified
fixed fits; clique/edgeless graph fixtures; wrong color counts and invalid
graphs; categorical/slate exposure support; all-row mean aggregation including
heterogeneous means at the theorem level; zero support and out-of-range reward
refusal; unknown shared-shock, future-design and evaluation-nuisance labels;
and exact clipped bias/variance identities. No test requires 30-replication
empirical coverage to exceed a nominal level.

# Gate A theorem-to-code contract

Status: **proved under the explicit additional assumptions below**. This is a
separate initial certificate, not a validation of the adaptive theorem in the
submitted draft. All source line numbers in this file refer to the original ZIP
sources before patches, with the `paper/` prefix added at extraction.

## Source obligations

The DR identity is in `paper/sections/02_setup.tex:35–44` and
`paper/sections/full/02_setup.tex:46–56`. The conditional graph lemma is in
`paper/sections/04_theory.tex:6–15` / `sections/full/04_theory.tex:9–23`.
The proposed general certificate is at `sections/04_theory.tex:19–37` /
`sections/full/04_theory.tex:28–53`; its proof blueprint is at
`sections/appendix.tex:90–126` and the same lines of the original full appendix.
The working numerical radius at `sections/03_method.tex:41–59` /
`sections/full/03_method.tex:61–87` is **not** directly executable as a certified
interval: its constant is unspecified, its estimated scale is not an upper
confidence bound, and coupling is written as a radius. Gate B implements the
following explicit theorem instead. The original broad theorem must remain
tagged unresolved outside this model, as explained in `proof_gap_report.md`.

## Probability model and theorem A

Let D be a sigma field generated only by the exogenous pre-action design and,
if used, an independent nuisance pilot. Gate B uses fixed predeclared regression
values, so D is deterministic. Conditional on D:

1. There are B independent evaluation macro-blocks, each containing n0 rows.
   Their sufficient dependency graphs are disjoint unions of chi-cliques.
   Each clique contains exact copies of one independently randomized cluster
   record. Different clusters, including clusters in different macro-blocks,
   use independent logging and outcome draws. There is no persistent latent
   effect spanning macro-blocks.
2. All contexts, logging probabilities, reference values, candidate policies,
   and auditors are fixed before the first evaluation draw. The same context
   pattern is repeated in every block. The finite family Theta has m members.
3. Local consistency and randomization identify each exposure response. Logging
   e is exact, q is a distribution on the identical exposure state space, and
   q(s)>0 implies e(s)>0. In the synthetic path, S=A is binary and Y is Bernoulli.
4. The fixed mu_hat and reference f belong to [0,1]; |h|<=1. The implemented
   auditors are binary indicators. Neither nuisance fitting nor family
   selection reads evaluation outcomes. The estimator has no oracle input.
5. For each theta, E[Z_bi(theta)|D]=m_bi(theta) and
   n0^{-1} sum_i m_bi(theta)=M(theta), the same in every block. There is a known
   finite, D-measurable bound nu(theta)^p on every conditional centered score
   p-moment, for a predeclared 1<p<=2.

For any alpha in (0,1), set delta_stat=alpha, epsilon_coup=0, and

    K = ceil(8 log(2m/delta_stat)),     B >= 2K.

Partition all B complete blocks deterministically into K consecutive groups
whose lengths are floor(B/K) or ceil(B/K); L_min=floor(B/K). Within each group
average its actual number of complete block means. The estimate is the usual
median of these K group means, averaging the two middle values when K is even.
For each theta define

    C_p_used = 32^(1/p),
    r(theta) = C_p_used * nu(theta)
               * (chi/(L_min*n0))^((p-1)/p).

Then, conditional on D, with probability at least 1-alpha, **all m** intervals
[estimate(theta)-r(theta), estimate(theta)+r(theta)] contain their fixed-design
targets M(theta). Integrating this conditional statement also gives
unconditional coverage. The result applies at a single predeclared window and
confidence level; it is not an anytime or post-deployment trajectory statement.

### Complete conservative constant derivation

Write X_bi=Z_bi-E[Z_bi|D]. In color c, conditional independence and the
von Bahr–Esseen inequality (constant at most 2 for 1<p<=2) give

    E[|sum_{i in c} X_bi|^p | D] <= 2 sum_{i in c} E[|X_bi|^p | D].

For arbitrary dependent color sums, |sum_c S_c|^p <=
chi^(p-1) sum_c |S_c|^p. Thus

    E[|bar Z_b-M|^p | D] <= 2 nu^p (chi/n0)^(p-1).

Group g contains L_g independent, centered block means. A second application
of the same inequality gives

    E[|T_g-M|^p | D] <= 4 nu^p (chi/(L_g*n0))^(p-1)
                     <= 4 nu^p (chi/(L_min*n0))^(p-1).

Markov's inequality at the stated r makes Pr(|T_g-M|>r |D)<=4/32=1/8.
Disjoint groups are independent conditional on D. With I_g denoting bad-group
indicators, Hoeffding gives

    Pr(sum_g I_g >= K/2 |D)
      <= exp(-2K(1/2-1/8)^2) = exp(-9K/32) <= exp(-K/8).

If fewer than K/2 groups are bad, the median is inside [M-r,M+r], including the
even-K convention. A union bound over m candidates is at most
m exp(-K/8)<=delta_stat/2<=alpha. No independence across candidates is needed.
The factor 32 and K rule are deliberately conservative. The exact implemented
radius uses L_min; it does not replace L_min by B/K or hide rounding in C_p.

**Why leftovers are valid here:** every block target equals M. Consequently
every group target equals M even when group lengths differ by one. Every block
and row is retained. Under changing block targets this argument fails; an
additional valid drift bound would be needed. No such extension is exposed by
the certified API.

### A known, non-oracle bounded-reward envelope

The plug-in score is Z=h[sum_s q(s)mu_hat(s)-f+
q(S)/e(S)(Y-mu_hat(S))]. Its absolute value is at most 1+q(S)/e(S).
Therefore, using the exact logging law rather than realized empirical weights,

    E[|Z|^p |D] <= 2^(p-1) [1+sum_s q(s)^p e(s)^(1-p)].

Jensen and |a-b|^p<=2^(p-1)(|a|^p+|b|^p) imply the valid centering bound

    E[|Z-E(Z|D)|^p |D] <= 2^p E[|Z|^p |D].

The implementation sets nu(theta)^p to the maximum over the predeclared
context pattern of

    2^(2p-1) [1+sum_s q(s)^p e(s)^(1-p)].

It is known before outcomes and requires neither true response means nor a
sample-based tail estimate. It remains conservative for h=0 rows. A state with
q=0 contributes zero, including when e=0; q>0,e=0 is nonidentification and is
never clipped. Gate B's standard synthetic design uses strictly positive e in
both states. The maximum is finite because the fixed design is finite with
positive support. This is **not** a uniform assertion over arbitrarily small
random e, nor a demonstration of an unbounded-weight population model.

Exact e and fixed nuisance values make the algebraic nuisance bias zero. They
do not justify evaluation-trained nuisances. The computed envelope controls the
implemented score, not just its oracle-nuisance version.

## Confidence accounting and refusal rules

For a future separately proved coupling/bias-envelope extension, total failure
would obey delta_stat+epsilon_coup+delta_aux<=alpha, while numerical radius
would be r_stat+r_nuisance+r_drift. A coupling probability is never added to
radius. Here all three extra error budgets/radii are exactly zero by the
declared synthetic model. The pure budget helper can check arithmetic with a
nonzero epsilon, but that helper is not a coupling theorem or certificate.

| Input / situation | Required behavior |
|---|---|
| Valid supported fixed-design bounded-reward model | `CERTIFIED`, certified_level=1-alpha |
| B<2K, invalid alpha/p, incomplete blocks, missing support | `NOT_CERTIFIABLE`, no interval |
| Unrecognized or absent sufficient graph / stable-target / independent-block model | `UNVERIFIED_ASSUMPTION`, no interval |
| Estimated nu, mutually trained cross-fit nuisances, adaptive family, unknown drift, nonzero unproved coupling | No certified API path; unsupported argument/model is rejected |
| Zero subgroup mass | Numerator remains defined; subgroup ratio abstains |
| Positive mass but weak overlap | Keep the proved possibly vacuous radius and report overlap/width; mass alone is not precision |

The certified API computes the bound from the registered synthetic model. A
caller-provided provenance string cannot empirically prove a stochastic
assumption: arbitrary externally assembled rows remain outside this contract,
even if they imitate the schema. Validation catches schema/design mismatches;
the declared DGP supplies independence and boundedness.

## Concrete Gate B interface

All public design and record dataclasses are frozen. The proposed runtime is
Python standard library only, with pytest as a development dependency.

    SyntheticConfig(B=128, n0=32, chi=4,
                    e_by_context=(0.2,0.4),
                    mu_hat=(0.5,0.5), reference=0.25,
                    q_probs=(0.25,0.75), auditors=('all','group1'))
    generate_evaluation(config, seed) -> (LoggedEvaluation, OracleTruth)
    certify(logged_evaluation, alpha=0.05, p=1.5) -> list[dict]

The generator uses independent deterministic RNG streams for logging and
potential outcomes; contexts/graph/family are deterministic exogenous design.
Each log row records unit/block/round/cluster/entity/slate identifiers, context,
pre-action subgroup, feature availability, action/exposure, logged e and full e
vector, reward, fixed reference and nuisance values, and exposure provenance.
Candidate q vectors are fixed in the frozen family. Exact response functions
and analytic target moments live only in `OracleTruth`, returned separately.
The estimator accepts only logs and imports no oracle truth module. Coverage
evaluation reads `OracleTruth.moments[candidate_id]` only after certification.

Each certificate reports: estimand_id, candidate_id, estimator, estimate, lo,
hi, nominal_delta, certified_level, status/reason, proof_model, p_declared,
nu_p and nu_p_source, C_p_used, stochastic_radius, nuisance_radius=0,
drift_radius=0, coupling_failure_epsilon=0, delta_stat, subgroup_mass,
overlap_metrics, effective_support_metrics, raw_N, retained_N, N_eff, B, n0,
K, L_min, group_sizes, chi_max, chi_by_block, graph nodes/edges,
assumption_audit, and seed. No truth is stored in this object.

For the default m=4 family, alpha=.05 gives K=41 and alpha=.10 gives K=36;
B=128 satisfies both feasibility conditions. Both use L_min=3. Consequently
these conservative 90% and 95% radii happen to coincide; this is expected
rounding behavior, not a changed confidence target. They are simultaneous
over the declared four candidates at each stated level separately.

## Validation mapped to obligations

Unit tests cover exact DR expectations with either nuisance correct, explicit
support failure, complete-slate Plackett–Luce/mixed-distribution enumeration
and exposure marginalization, deterministic clique coloring, all-row retention,
K and budget arithmetic, conservative constant fixtures, known envelope
monotonicity, schema/model rejection, and absence of oracle dependencies.
Independent mathematical audit tests cover false centering, the corrected Le
Cam construction, conditional-vs-integrated moment examples and nuisance leaks.
The tiny 30-replication smoke run produces raw logs/certificates/truth separately,
actual CSV/JSON and Wilson uncertainty; it is a debugging run and cannot
establish final nominal coverage. Gates C–F remain deferred.

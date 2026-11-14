# Heterogeneous conditional-graph residual certificates

Status: independently derived mathematical result for the new post-C-STAT
workstream. This file does not alter the historical C-STAT theorem or experiment.
`POST_CSTAT_OVERRIDE.md` and `CODEX_MASTER_GOAL.md` were read in full.
`THEORY_NOTE.md` was unavailable when this derivation was written; no claim is
made that its unseen derivation or threshold grid has been verified.
The proof below establishes the explicit formula in the override, with the
necessary restriction **1 < p <= 2**. Floating-point execution is not a
machine-verified, outward-rounded realization of this real-arithmetic theorem.

## 1. Conditional probability and estimand contract

Condition on a legitimate exogenous sigma-field D and any independent
training/discovery information. All arrays, graph certificates, queries,
normalizers, envelopes, thresholds, candidate-method choices, and allocated
error probabilities below are measurable with respect to this conditioning
information. Independent training means independent random-source pools, not a
row split of a realized connected source graph. Conditioning on an evaluation
fit is not a way to manufacture independence.

There are N rows. Row u has finite exposure S_u with exact known probabilities
`e[u,s] = P(S_u=s | D)`. Let `mu[u,s]` be the identified conditional response
mean. In a causal interpretation this identity requires the stated exposure
sufficiency and assignment/potential-outcome assumptions; an exact marginal e
alone does not prove causal identification. Fix a nuisance `muhat[u,s]`, a
signed coefficient `d[u,s,theta]`, a known offset `a[theta]`, and a strictly
positive D-measurable normalizer `B[theta]`. For ordinary raw moments B=N;
for a subgroup ratio B=N*pi, with known positive design mass pi. Define

    M_theta = a_theta + sum_{u,s} d[u,s,theta] mu[u,s] / B_theta,
    D_theta = a_theta + sum_{u,s} d[u,s,theta] muhat[u,s] / B_theta,
    R[u,theta] = d[u,S_u,theta] (Y_u-muhat[u,S_u]) / e[u,S_u].

A level query has d=h*q; a direct paired contrast has d=h*(q-q0). Both signs
of a contrast belong to this one signed moment, not two independent datasets.
A nonzero coefficient at e=0 is nonidentified unless a separate known-response
argument identifies that term. It is not repaired by clipping a weight.
An exactly zero coefficient contributes zero without evaluating 0/0.

The conditional identification identity is

    E[R[u,theta] | D]
      = sum_s d[u,s,theta] (mu[u,s]-muhat[u,s]),
    M_theta = D_theta + sum_u E[R[u,theta] | D] / B_theta.

This is finite enumeration over S. It uses exact e and supported coefficients,
not correctness of the fixed nuisance. In causal notation the corresponding
weighted residual identity must follow from the generator's full assignment
law. If local q is described as an implementable policy, it must be the
exposure marginal of a compatible joint policy Q.

## 2. Legal raw residual moments

For a common p in (1,2], suppose the declared model supplies

    E[|Y_u-muhat[u,s]|^p | S_u=s,D] <= b[u,s]^p.

Then a valid row envelope, including signed contrasts, is

    v[u,theta] = sum_{s:e>0} |d[u,s,theta]|^p
                              e[u,s]^(1-p) b[u,s]^p,
    E[|R[u,theta]|^p | D] <= v[u,theta].

The p-moment is about the **raw residual**, not a centered residual with an
unknown mean subtracted by the implementation. A bound on centered outcome
noise alone does not justify substituting its moment for this expression.
For Y in a known interval [L,U], the legal residual magnitude is
`b=max(|L-muhat|,|U-muhat|)`. In particular, Y in [0,1] with midpoint nuisance
.5 has b=.5, for COMET and every matched baseline.

For Y=mu+xi with mu in a known location class and a known noise p-norm K,
Minkowski gives the legal envelope

    b <= max_{mu in declared class}|mu-muhat| + K.

For a linear combination of primitive shocks with known p-norms K_j,
`||sum_j a_j xi_j||_p <= sum_j |a_j| K_j`. This conservative inequality requires
no cancellation or independence. A sharper envelope needs its own proof.
Unknown scale estimated from this evaluation log is not a known moment bound.

## 3. Sufficient graphs and active support

A conditional dependency graph is required in the strong sense: whenever two
disjoint row sets have no crossing edge, the corresponding random row vectors
are conditionally independent given D. Pairwise zero covariance is insufficient.
One sufficient construction declares independent primitive source collections
conditional on D, represents the **whole** row score/residual vector as a
measurable function of its listed sources, and connects every pair of rows
whose source sets overlap. Two vertex sets with no crossing edge then depend
on disjoint independent primitive collections, proving the graph property.
Logging sources, outcome sources, shared nuisance randomness not conditioned
away legitimately, and all retained response channels must be included.

The design-active support of a query consists of rows whose residual is not
known identically zero from D. Nonzero d for a possible exposure is active even
if the realized exposure happens to make the residual zero. An inactive row
still contributes any nonzero known direct term. The graph on retained rows is
the induced subgraph of the sufficient source graph (or another separately
proved sufficient graph). Removing an intermediate inactive row does not
remove a source shared by two retained rows.

A proper coloring C_1,...,C_chi is checked against all retained edges. Within
each color the row variables are jointly conditionally independent. Chi is the
number of colors in a verified available coloring, not a claim of optimal
chromatic number. The minimum among available **verified proper colorings**
may be used based on D alone. A connected cycle/path of overlapping source
pairs remains a global connected graph, not fake independent macro-blocks.
Heterogeneous means and unequal color sizes are permitted throughout.

## 4. Sharp bias, second moment, and range

Let T_tau(x)=sign(x) min(|x|,tau), tau>0. For 1<p and all real x,

    |x-T_tau(x)| <= c_p tau^(1-p) |x|^p,
    c_p = (p-1)^(p-1) / p^p.

Proof: for z=|x|/tau>1 maximize (z-1)/z^p. Its derivative has the sign of
`p-(p-1)z`, so the maximum occurs at z=p/(p-1), with the stated value;
for z<=1 the left side vanishes. This constant is sharp. It equals 1/4 at
p=2 and tends to 1 as p decreases to 1. Consequently

    |E[T_tau(R)]-E[R]| <= c_p v tau^(1-p).

For **p<=2**,

    T_tau(x)^2 <= tau^(2-p) |x|^p,
    Var(T_tau(R) | D) <= E[T_tau(R)^2 | D]
                         <= v tau^(2-p).

This follows separately on |x|<=tau and |x|>tau. It is false for p>2:
x=.1, tau=1, p=3 gives .01 > .001. The displayed radius must not be labelled
certified for p>2 by reusing that variance bound. A different legal second
moment would be needed. Finally,

    |T_tau(R)-E[T_tau(R) | D]| <= 2 tau.

Centering is solely a proof operation. The estimator never receives E[R]
or E[T_tau(R)]. Heterogeneous row means cause no additional centering term.

## 5. Graph-coloring/Hölder MGF and the explicit radius

Fix a query and its positive D-measurable row thresholds tau_u. Write

    X_u = T_tau_u(R_u)-E[T_tau_u(R_u) | D],
    A = sum_u v_u tau_u^(2-p),  tmax=max_u tau_u.

All sums and maxima in stochastic terms are over active rows. A centered
bounded variable X with |X|<=b and variance<=a satisfies

    log E exp(lambda X) <= lambda^2 a / [2(1-b|lambda|/3)]

for b|lambda|<3. This follows by expanding the exponential, using
`|E X^k| <= a b^(k-2)` for k>=2 and `k! >= 2*3^(k-2)`, then `log(1+z)<=z`.
For each proper color the joint MGF factorizes. Hölder with chi equal exponents
across colors gives

    log E exp(lambda sum_u X_u)
      <= chi lambda^2 A / [2(1-(2/3)chi*tmax*|lambda|)].

Indeed, apply the independent bound to chi*lambda inside each color's MGF,
then take its 1/chi power. Unequal color sizes do not change the calculation.
With V=chi*A and c=(2/3)chi*tmax this is a two-sided sub-gamma bound. Chernoff's
inequality yields, for t>0,

    P(sum X_u > sqrt(2 V t)+c t | D) <= exp(-t),
    P(-sum X_u > sqrt(2 V t)+c t | D) <= exp(-t).

For completeness lambda=sqrt(2t/V)/(1+c*sqrt(2t/V)) gives exponent at least t
at the displayed boundary; the V=0 case is deterministic. Set
`t=log(2/delta_theta)` and add the absolute clipping bias. The estimator and
radius for the **original, unclipped** target are

    Mhat_theta = D_theta + sum_u T_tau_u(R_u)/B_theta,
    radius_theta = [ c_p sum_u v_u tau_u^(1-p)
                     + sqrt(2 chi t sum_u v_u tau_u^(2-p))
                     + (2/3) chi tmax t ] / B_theta.

Thus `P(|Mhat_theta-M_theta|>radius_theta | D)<=delta_theta`. One threshold
per query is the special case tau_u=tau_theta. It is the required first API;
per-row tuning is not a prerequisite. When no random residual remains, use
radius zero directly, with no artificial max over an empty support.

For a finite frozen family Theta, allocate positive delta_theta with
`sum_theta delta_theta<=delta` (equal allocation delta/m is permitted). A union
bound proves simultaneous coverage at least 1-delta conditional on D, hence
also unconditionally. It does not require independence between queries, methods,
or confidence levels. Each method/level has its own statement unless a joint
budget across them is expressly allocated.

## 6. Sharp bounded branches with the same information

When response intervals [L_us,U_us] are known, compute the actual possible
residual endpoints over every supported exposure:

    ell_u = min_s min{d_us/e_us*(L_us-muhat_us),
                      d_us/e_us*(U_us-muhat_us)},
    upper_u = max_s max{d_us/e_us*(L_us-muhat_us),
                        d_us/e_us*(U_us-muhat_us)},
    w_u = upper_u-ell_u.

Do not add hypothetical exposures with e=0 to the extrema. Do not use observed
sample extrema as known support. Given the same query, nuisance, support,
source graph, normalizer and family budget, untruncated graph Hoeffding has

    Mhat = D_theta+sum R_u/B_theta,
    r_H = sqrt( chi log(2/delta_theta) sum_u w_u^2 / 2 ) / B_theta.

Proof: each row's centered MGF is at most lambda^2*w_u^2/8; the same coloring
Hölder argument inserts chi. Graph Bernstein has

    A2_u = sum_s d_us^2/e_us * b_us^2,
    V_u = min(A2_u, w_u^2/4),
    r_B = [sqrt(2 chi log(2/delta_theta) sum_u V_u)
           + chi max_u(w_u) log(2/delta_theta)/3] / B_theta.

Both A2 and Popoviciu's range bound are legal variance upper bounds, so their
minimum is legal. Bernstein uses centered range bound w_u, sharper than
2*max(|ell_u|,|upper_u|) when the support is asymmetric. All eligible methods
must receive these same legal quantities. Neither bound is guaranteed better
than the other for every design. A D-only choice of the smaller proved radius
is legal; choosing by realized intersected widths is a different operation.

### Deterministic historical-A fixture

For q=e=(.5,.5), muhat=.5, offset/reference .25, the score is Y-.25. With
N=8192 independent rows, delta=.05, m=1 and Y in [0,1], w_u=1, chi=1:

    r_H = sqrt(log(40)/(2*8192)) = 0.015005043614373761.
    gamma = .2375-.2 = .0375 > 2*r_H = .030010087228747522.

If |Mhat-M|<=r_H, then Mhat-r_H >= M-2r_H > .2. Hence the theorem gives at
least .95 detection probability in this stated DGP. This is an analytic fixture,
not a newly sampled empirical power result, not an m=16/chi>1 claim, and not
an addition to the historical 17 C-STAT tests.

## 7. Tuning, strong comparisons, and equivalence

A threshold/method selected solely from D, independent pilot data and legal
bound inputs is fixed in the conditional proof. Thus minimizing the radius over
a prespecified available grid requires no extra outcome-search union budget.
The exact proposed THEORY_NOTE grid remains unverified until that file is read;
any implemented replacement must be explicitly versioned before its outcomes.
Thresholds may scale with signed query magnitude. If d becomes eta*d for eta>0,
then direct terms and targets scale by eta, v by eta^p, and thresholds by eta.
Every radius component above scales by eta. Small policy steps therefore do
not automatically improve sign-certification power. Eta=0 is deterministic.

A generic bias-corrected truncated graph mean with the same d, v, support,
coloring, tau, normalizer and error allocation is **algebraically identical**
to the residual-truncation configuration above. Equality must be reported and
tested; this comparator cannot establish estimator superiority. Global envelope
or global graph ablations isolate the cost of discarding local information;
matched local competitors receive local information too.

A separate colorwise comparator is valid by giving color c its own failure
budget delta_c, summing over colors. If `sum_c delta_c<=delta_theta`, independent
truncation in color c has numerator radius

    bias_c + sqrt(2 A_c log(2/delta_c))
           +(2/3) max_{u in c}(tau_u) log(2/delta_c).

Sum **all** color numerators and divide by the original B_theta. Equivalently
weight color averages by their actual sizes/B_theta. Dropping colors, treating
unequal colors as equally weighted, or replacing N by active-support size changes
the target. The direct term remains the original query direct term.

## 8. Independent discovery, decisions and mixtures

An independent discovery pool may choose the finite family, policies, auditors,
fits and D-measurable budgets before certification outcomes. Conditional on that
pool the same theorem applies. Every risk coordinate and utility contrast used
by subsequent selection belongs to the combined simultaneous family. m is the
number of actual distinct coordinates after legitimate deduplication, not an
old conventional number of tests. Known design service/capacity can be evaluated
exactly without artificial outcome intervals.

On the simultaneous event, any returned candidate whose risk upper bounds meet
the constraints, known service/capacity meet their bounds, and utility lower
contrast meets the declared usefulness/noninferiority requirement is safe and
useful in the **fixed-design moment sense defined by those constraints**.
Consequently P(return AND unsafe)<=delta. This is not a delta bound on
P(unsafe | return), which can only be bounded by delta/P(return) without more
structure. Abstention is not useful return. Reject-all violates a positive
service floor. An uncertified fallback cannot be labelled safe.

For a radius-symmetric risk interval, a true risk slack of 2r is sufficient for
certification on the coverage event. If selection maximizes a certified utility
lower bound, its utility is within 2r_p of any comparator p with enough true
slack to enter the certified library. This robust-slack comparator is distinct
from the oracle best feasible candidate, which may have zero margin and be
uncertifiable. These are eventwise algebraic consequences, not empirical
performance guarantees.

For compatible base joint policies Q_j and nonnegative weights summing to one,
Q_w=sum_j w_j Q_j is a valid joint mixture. With fixed auditors and normalizers,
all relevant moments are affine. Simultaneous base intervals propagate as

    L(w)=sum_j w_j L_j,  U(w)=sum_j w_j U_j.

They hold on the same event for every weight vector, including one selected
from certification results. For signed affine combinations, multiply interval
endpoints according to each coefficient's sign. No new union over weights is
needed for this deterministic implication. The estimator of a mixture is the
corresponding linear combination of base estimates. Recomputing a nonlinear
clipped estimator at an outcome-selected mixture is not generally equal and
is not justified by this corollary. Changing bins, normalizers, or nonlinear
fairness metrics also requires separate analysis.

## 9. Numerical and reporting obligations

The theorem is in real arithmetic. The new protocol must declare its own
production environment, deterministic IDs, immutable completed checkpoints,
cross-platform numerical tolerance and conservative near-boundary rule before
outcomes. Old C-STAT tolerances and source hashes remain untouched. An interval
intersected with a known target range remains valid; an empty intersection is a
coverage failure. Nonidentification, assumption uncertainty, numeric failure,
valid but vacuous intervals, and ordinary abstention remain distinct recorded
statuses. Source lists and schemas verify a **declared construction**; they do
not detect arbitrary hidden shared randomness from one log.

A concrete conditional-independence counterexample is independent Rademacher
X1,X2 with evaluation-derived D=X1*X2. Conditional on D=1, X1=X2. One cannot
condition on such evaluation information and retain the original empty graph.
Likewise, a domain star graph does not prove a dependency graph if two leaves
share a primitive: their missing leaf-to-leaf edge invalidates the graph.

Optional predictable/adaptive theorems are not established by this document.

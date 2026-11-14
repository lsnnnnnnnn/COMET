# COMET — proposed core theorem and proof obligations

Status: mathematical derivation supplied with the research plan; NOT a claim that this theorem has been independently audited, implemented, or experimentally validated in the repository. Codex must write and check a complete version, map it to the implementation, and retain counterexamples to invalid extensions. This note supplements, rather than silently modifies, the user's attached scope discussion.

## 1. Probability space and target

Let D contain an exogenous pre-evaluation design and any genuinely independent nuisance-training/discovery information. Conditional on D, the finite collection of queries Theta, reference functions, logging laws, nuisance functions, moment envelopes, dependency graphs, colorings, and truncation choices are fixed. D must not contain future adaptive contexts or evaluation-trained nuisance functions merely to manufacture independence.

The principal target is

    M_D(theta) = N^{-1} sum_u h_u [sum_s q_u(s) mu_u(s) - f_u],
    mu_u(s) = E[Y_u(s) | D].

Identification requires consistency, conditional exchangeability of the relevant exposure and potential outcome given D, exact exposure probabilities e_u(s), and q-supported states having positive e_u(s). No uniform numerical lower bound on all propensities is imposed. Positivity does not guarantee an informative interval.

Write

    a_u = h_u [sum_s q_u(s) muhat_u(s) - f_u],
    W_u = h_u q_u(S_u)/e_u(S_u) [Y_u - muhat_u(S_u)].

Then E[a_u+W_u | D] is the target summand. The full residual vector W has a sufficient conditional dependency graph: disjoint sets without connecting edges have independent vectors given D. Pairwise zero correlation is insufficient. A graph on social links is not automatically such a graph. The graph is D-measurable: it cannot be shrunk after observing realized treatments or residuals without a separate conditional argument.

This formulation permits heterogeneous mu_u, unequal block sizes, and a single connected dependence graph. It requires neither repeated contexts nor common block targets nor a partition into independently repeated macro-blocks. It does not cover arbitrary adaptive histories.

For a signed policy contrast under the same h, f, nuisance and response channel, replace q by d=q-q0 in both a and W; the reference cancels. More generally, a fixed signed coefficient array d is permitted if its functional and identification are stated. For value queries d=hq; for paired contrasts d=h(q-q0).

## 2. Legal, query-specific moment information

Assume a known D-measurable upper bound

    E[|Y_u(s)-muhat_u(s)|^p | D] <= rho_{us,p},  1<p<=2.

By identification,

    E[|W_u|^p | D] <= v_{u,theta,p}
      := |h_u|^p sum_s |q_u(s)|^p e_u(s)^(1-p) rho_{us,p}.

For contrasts substitute |q-q0|^p. A zero coefficient contributes zero; a nonzero coefficient at e=0 is unsupported and must not be repaired by flooring e.

For bounded Y in [L,U], a legal residual bound is

    rho_{us,p} = max(|L-muhat_u(s)|, |U-muhat_u(s)|)^p.

Use this same information for all eligible baselines. In particular, muhat=.5 and Y in [0,1] imply a residual bound .5, not 1. Smaller predictive error observed on a pilot is NOT automatically a valid smaller moment envelope.

For synthetic heavy-tail noise with known sources, derive an envelope before observing evaluation outcomes. A useful inequality for coefficients b_j and noises xi_j with E|xi_j|^p<=k_j is

    E|sum_j b_j xi_j|^p
      <= (sum_j |b_j|)^(p-1) sum_j |b_j| k_j.

Add the unknown-location discrepancy using a declared location class, not its oracle point value. Preserve any finite-grid sampler qualifications. With only the existence of a p-moment, an empirical pilot p-moment is not a distribution-free upper confidence bound on the unobserved tail.

## 3. Query support and graph

Let A_theta contain rows whose random contribution is not identically zero by design. The induced subgraph of the sufficient graph on A_theta is still sufficient. Compute a valid coloring using chi_theta colors. This is a coloring count, not a claim of an optimal chromatic number.

Removing a row from A_theta does NOT remove the source it shares with two retained rows; the full source-intersection graph must already contain the retained pair's edge. An inactive hub in a social graph does not necessarily eliminate dependence between its active neighbors.

Known deterministic a_u terms remain in the target even if W_u=0. For an empty active set the estimator is deterministic; handle this without dividing by chi=0 or using an undefined tau.

## 4. Residual truncation and explicit radius

For positive D-measurable tau_u on the active set, define

    T_u = clip(W_u, -tau_u, tau_u),
    Mhat_tau = N^{-1} sum_u (a_u + T_u),
    c_p = (p-1)^(p-1)/p^p,
    B_theta = c_p sum_u v_u tau_u^(1-p),
    A_theta = sum_u v_u tau_u^(2-p),
    tau_max = max_u tau_u.

Choose delta_theta>0 with sum_theta delta_theta<=delta, fixed given D, and set t_theta=log(2/delta_theta). Equal allocation gives t_theta=log(2m/delta).

A valid candidate radius is

    r_theta = [B_theta + sqrt(2 chi_theta A_theta t_theta)
                         + (2 chi_theta tau_max/3) t_theta] / N.

This radius concerns the original untruncated target, not a clipped target.

### 4.1 Bias

For x>=0, tau>0,

    (x-tau)_+ <= c_p tau^(1-p) x^p.

The maximum of (z-1)/z^p over z>=1 occurs at z=p/(p-1). Hence

    |E[T_u-W_u | D]| <= c_p v_u tau_u^(1-p).

Summing yields the deterministic bias debit B_theta/N. It cannot be removed because the observed sample contains no extreme score.

### 4.2 Variance and range

For 1<p<=2,

    min(x^2,tau^2) <= tau^(2-p) |x|^p.

Consequently Var(T_u | D)<=E[T_u^2 | D]<=v_u tau_u^(2-p). Let X_u=T_u-E[T_u|D]. Then |X_u|<=2 tau_u. The estimator never needs the unknown E[T_u|D]; it appears only in the proof.

### 4.3 Coloring and exponential bound

For each independent color class, the bounded-centered-variable Bernstein MGF bound applies. Hölder with chi_theta factors combines color sums without assuming independence between colors. For |lambda|<3/(2 chi_theta tau_max),

    log E[exp(lambda sum_u X_u) | D]
       <= chi_theta lambda^2 A_theta
            / [2(1 - (2 chi_theta tau_max/3)|lambda|)].

Thus sum X_u is conditionally sub-gamma with variance proxy chi_theta A_theta and scale 2 chi_theta tau_max/3. The two-sided deviation is at most

    sqrt(2 chi_theta A_theta t) + (2 chi_theta tau_max/3)t

with failure probability at most 2 exp(-t). For completeness, choose lambda=s/(1+cs), s=sqrt(2t/v), v=chi_theta A_theta and c=2 chi_theta tau_max/3 in the Chernoff calculation. This gives the displayed square-root-plus-linear form; do not mix it with a differently inverted, looser Bernstein tail formula.

Add the bias debit and union-bound over the fixed query family. Then

    P(all theta: |Mhat_tau(theta)-M_D(theta)|<=r_theta | D)>=1-delta.

Integrating conditional validity preserves coverage for the random fixed-design target. It does not change the target into an unconditional population quantity.

## 5. Transparent tuning and scaling

Implement a single common tau per query first. With Vp=sum_u v_u and x=chi_theta t_theta, write

    tau = c (Vp/x)^(1/p),
    r_theta = kappa_p(c) Vp^(1/p) x^((p-1)/p) / N,
    kappa_p(c) = c_p c^(1-p) + sqrt(2) c^((2-p)/2) + (2/3)c.

One reproducible default is to choose the smallest-radius c from the fixed grid c=2^(j/4), j=-24,...,24. Recompute the certified radius at the selected point. The grid need not contain the mathematical optimum to preserve validity. All selection uses D, not scores, empirical errors, oracle means, or realized interval widths.

Using the same principle, selection between several valid certificate constructions is legitimate when the selection criterion is fixed and D-measurable (e.g., known raw radius). Outcome-based selection of the shortest support-intersected interval needs a separate simultaneous argument. Retain each comparison method separately in scientific reporting.

Per-row truncation can be an extension, but a single tau per query is the required interpretable implementation. Heterogeneous tau introduces a max-range cost; do not claim local optimization removes it without proof.

For a binary auditor, pi_theta=N^{-1}sum h_u is known in the fixed design. Normalize both estimate and radius by pi_theta when pi_theta>0; pi_theta=0 is an undefined subgroup ratio. For the rare-action homogeneous subclass, Vp approximately scales like N pi rho epsilon^(1-p). This yields the explanatory subgroup-radius scale

    rho^(1/p) [chi_theta log(2m/delta)/(N pi epsilon)]^((p-1)/p).

This is a subclass calculation, not a universal scalar effective-sample-size characterization for arbitrary q/e heterogeneity.

## 6. Lower-bound strengthening: constructive route, precise limitations

Retain the existing chi-clique lower bound. A proposed extension makes exposure and group size explicit. Put n_g=N pi/chi independent clusters in the audited subgroup and replicate each chi times. For each cluster, S~Bernoulli(epsilon); the informative Y(1) is seen only when S=1. Other data have identical laws under both hypotheses.

For n_g epsilon>=1, set

    beta=1/(2 n_g epsilon),
    P0: Y(1)=0,
    P1: Y(1)=a with probability beta and 0 otherwise,
    a=(rho/(2 beta))^(1/p).

The centered p-moment is at most rho (and the raw p-moment is rho/2). The subgroup mean gap is

    Delta = rho^(1/p) / [2 (n_g epsilon)^((p-1)/p)].

The total variation distance of the observed n_g-cluster laws is at most n_g epsilon beta=1/2. The common-measure Le Cam argument gives expected absolute-risk lower bound Delta/4. This exhibits the proposed exposure/group/dependence scale in a subclass.

Codex must explicitly handle integer group sizes, n_g epsilon<1, zero support, fixed mean-class bounds, and the fact that this is a sequence of least-favorable distributions. If a bounded mean class is imposed, limit the parameter regime or rescale the construction to remain inside it. For bounded outcomes, this unbounded-spike construction does not establish the sharp bound; use an appropriate bounded two-hypothesis argument separately.

This does NOT prove a graph-specific minimax result on every sparse graph, a matching log(m/delta) factor, or a simultaneous confidence-width optimum. A fixed-confidence confidence-set consequence can be separately derived from two hypotheses, but must not be described as established by an expected-risk bound alone.

## 7. Decision corollaries and guardrails

For an upper constraint M(theta)<=alpha, U<=alpha certifies safe and L>alpha certifies violation. On the simultaneous event no claim is false. For deterministic radius r and true violation gap gamma=M-alpha>2r, the same event implies detection. Merely gamma>r does not imply nominal-level detection probability.

Paired contrast: for q_eta=q0+eta(q1-q0), eta>0, a common-nuisance contrast and appropriately scaled tau have both true contrast and radius scaled by eta. The sign-certification signal-to-radius ratio need not improve as eta shrinks. Localizing a change or removing common noise is distinct from simply taking a smaller mixture step.

Discovery: condition on independent discovery/training information; freeze L auditors and all candidate policies before certification. Independence concerns random sources, not just row IDs. The theorem covers the returned finite family, not every possible subgroup in an infinite class.

Policy selection: certify utility and every risk/guardrail moment jointly. The safe-selection event is

    P(return a policy AND some certified constraint is truly violated)<=delta,

not generally P(unsafe | return)<=delta. Report both. Abstention is not a successful useful return.

Mixture extension: if Q_k are valid joint assignment policies and objectives/constraints are affine in their assignment laws, Q_w=sum w_k Q_k is valid, and on the base-policy simultaneous event the interval [sum w_k L_k, sum w_k U_k] covers its moment for every w in the simplex, including a subsequently selected w. This does not require the truncated estimator re-evaluated at q_w to equal sum w_k Mhat_k; generally it does not. The argument fails for arbitrary policy-dependent ratios or moving calibration bins. In interference settings mix full assignment laws, not independently chosen inconsistent local exposure marginals.

## 8. Optional predictable, fixed-horizon extension

A separate theorem may condition round by round on pre-action H_t. If a valid conditional MGF is established for each round's centered truncated residual sum and cumulative bias/variance/range budgets have deterministic valid upper bounds, exponential-supermartingale arguments may replace cross-round independence. Predictable nuisance learning is not mutual cross-fitting.

Do not replace deterministic budgets by their realized stochastic totals inside a deterministic Bernstein radius without a proof. Any time-uniform, self-normalized, stopping-time, unknown-scale or long-run deployment claim is a separate obligation. This extension is nonblocking for the graph-dependent fixed-design paper.

## 9. Novelty and implementation warnings

Graph coloring/Hölder concentration, truncation with a bias debit, policy differences, and independent learn-then-test procedures are established tools. The research must test whether their query-specific combination and certifiability analysis provide a substantive contribution. A correctly matched generic truncated graph-Bernstein baseline can be algebraically identical to a COMET configuration; disclose equivalence rather than manufacture a performance advantage.

Reference anchors, to be checked in full before implementation:
- Janson (2004), Large deviations for sums of partly dependent random variables. https://doi.org/10.1002/rsa.20008
- Bhatt, Fang, Li, Samorodnitsky (2022), Nearly Optimal Catoni's M-estimator for Infinite Variance. https://proceedings.mlr.press/v162/bhatt22b.html
- Waudby-Smith et al., Anytime-valid off-policy inference for contextual bandits. https://arxiv.org/abs/2210.10768

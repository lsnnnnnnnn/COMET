# Gate A proof-gap report

All source references are **original ZIP-source** line numbers in baseline
commit `58ad7bd`. Compact and full appendix references agree in the relevant
proofs. The source remains auditable even after lower-bound and status patches.
“Proved” below means a mathematical derivation under stated assumptions;
“unproved” is not a claim that no future theorem is possible. The explicit
restricted theorem is proved in `estimand_contract.md`.

## P0.1 — Adaptive path target versus independent MOM blocks

**Blocker; original adaptive theorem unproved.** Sources: compact setup 27–33,
75–81; full setup 37–44,103–113; compact theory 21–37; full theory 26–53;
both appendices 90–126. The proof conditions on “design and nuisance-training
data” without specifying a field that preserves both target centering and block
independence. A history-dependent design is not generally exogenous.

Let `U,V` be independent Rademachers, `F0` trivial, `F1=sigma(U)`, and let
`Z1=U`, `Z2=U+V`. Then predictable means are `m1=0,m2=U`, and the path target is
`M_path=U/2`. The unconditional block means are both zero. Moreover
`Cov(Z1,Z2)=1`, so the blocks are not independent. If the second-round context
`X2=U` is included in a purported “fixed design” field `D=sigma(X2)`,
`E[Z1|D]=U`, not its original predictable mean zero. Independent marginal block
copies centered at their unconditional means do not preserve the random path
target's joint relationship with the observations.

Even zero predictable means do not imply independent blocks: with symmetric
`U in {-2,-1,1,2}` and independent Rademacher `V`, set `Z1=U,Z2=|U|V`.
Then both predictable means are zero, but `|Z1|=|Z2|`; their bad indicators for
threshold 1.5 coincide. One cannot invoke independent Bernoulli majority tails
merely because the scores are martingale differences.

**Correct patch:** explicitly separate fixed/exogenous-design independent-block
Theorem A from an adaptive extension. Under Theorem A, condition on a design
that predates all evaluation randomness, require stable conditional block
targets, and use a fixed fit/independent pilot. For the adaptive extension,
define pre-action fields, predictable fits, and conditional p-moment bounds and
prove an appropriate martingale robustification theorem. The current streaming
paragraph (appendices 203–217) is a research outline, not that proof.

## P0.2 — Mutually trained cross-fit scores

**Blocker; joint conditioning argument invalid without additional assumptions.**
Sources: compact method 6–12, theory 21,37; full method 6–13, theory 30,53;
appendices 60,92,144–152.

Counterexample preserving conditional mean zero: let `Y1,Y2,Y3` be iid
Rademachers and take a singleton action/exposure with `e=q=1`. DR scores are
exactly `Zi=Yi`, whatever the nuisance prediction. Train each held-out nuisance
as `mu_hat_i=Yj Yk` on the other two outcomes. Each fit is independent of its own
evaluation outcome. But conditioning on all three fits reveals every pairwise
product. On `D={all three fits=1}`, the conditional outcomes are `(1,1,1)` or
`(-1,-1,-1)`, each with probability 1/2. Thus conditional means remain zero,
while `P(Y1=1,Y2=1|D)=1/2 != 1/4`; an edgeless conditional graph is false.

A binary DR example also shows unconditional score dependence. Independently
draw `Si~Bernoulli(1/2)`, with deterministic potential outcomes `Y_i(s)=s`.
For `q(1)=1`, use exact `e(1)=1/2` and `mu_hat_i(1)=Y_j=S_j` fitted on the
other row. Then
`Zi = S_j + 2 S_i(1-S_j)`, `E Zi=1`, but `Cov(Z1,Z2)=1/4`.
Each row's DR identity holds conditional on its own training data; the two
scored rows are dependent. Conditioning on both fits instead reveals both
assignments, so `E[Zi|all fits]=Zi`, not 1 in general.

Direct outcome leakage can even destroy unbiasedness with exact `e`: use the
same `Y(s)=s` and set `mu_hat(1)=Y=S`. Then `Z=S+2S(1-S)=S`, whose mean is
1/2 although target mean is 1. Exact propensity corrects algebraic nuisance
bias only when the conditioning/learning independence needed for the algebra
holds.

**Correct patch:** fixed predeclared bounded fit or a pilot independent of all
evaluation blocks conditional on valid exogenous design. Ordinary guarded
cross-fitting remains exploratory until a concentration proof includes its
score dependence. Enlarging the conflict graph must include training-induced
edges and may eliminate useful independence; row identifiers alone do not do so.

## P0.3 — Moment assumption and centering mismatch

**Blocker for using the setup assumption alone; repaired in Theorem A.** Sources:
compact setup 63–73; full setup 83–101; compact graph lemma 6–15; full graph
lemma 9–23; appendices 65–83,92–95.

The setup controls a window average of raw **oracle** moments conditional on
different histories. The lemma needs centered **implemented** score moments
under one common field. These are three distinct changes.

* Window average does not imply per-row envelope: with `N` rows, let
  `X1=N^(1/p) R`, `R` Rademacher, and all remaining `Xi=0`. The average raw
  p-moment is 1, while row 1's centered p-moment is `N`.
* The oracle envelope need not control a wrong-regression score even with exact
  propensities. With `Y(s)=0`, `e(1)=1/2`, `q(1)=1`, and fixed
  `mu_hat(1)=C`, oracle score is zero but `Z=C(1-2S)` has centered moment `C^p`.
* Conditional moments need not remain bounded after enlarging the conditioning
  field to include future designs or evaluation-dependent fitted functions.

The valid centering bound under one field is
`E|Z-E(Z|D)|^p <= 2^p E|Z|^p`, by convexity and conditional Jensen. A more
flexible graph lemma uses row envelopes `v_i=E[|Xi|^p|D]`:

`E[|n0^-1 sum_i Xi|^p|D] <= 2 chi^(p-1) n0^(-p) sum_i v_i`.

Thus `sum_(i in block b) v_i <= n0 nu_p^p` for **every** block suffices;
per-row uniform bounds are convenient but stronger. A single whole-window sum
bound cannot be substituted into the proof's per-group 1/8 failure statement
without an additional allocation/majority argument. Theorem A instead uses the
analytic bounded-reward envelope proved in the estimand contract.

## P0.4 — Explicit MOM constants, full grouping, and feasibility

**Major; repaired by explicit restricted derivation.** Sources: compact method
20–26,45–48; full method 29–39,66–70; compact theory 23–34; full theory 32–47;
appendices 98–124.

With `1<p<=2`, common centered score envelope, sufficient conditional graph,
and independent blocks: graph convexity plus von Bahr–Esseen constant 2 gives
block moment `<=2 nu_p^p(chi/n0)^(p-1)`; another constant 2 across complete
blocks gives group moment `<=4 nu_p^p(chi/(L_g n0))^(p-1)`.
Hence `r=32^(1/p)nu_p(chi/(L_min n0))^((p-1)/p)` has group failure <=1/8.
Independent group indicators imply `P(>=K/2 bad)<=exp(-9K/32)` by Hoeffding.
The exact proposed `K=ceil(8 log(2m/delta_stat))` therefore suffices by a
union bound; the full algebra appears in `estimand_contract.md`.

Use all blocks in deterministic groups of sizes floor/ceil(B/K), enforce
`B>=2K`, and use `L_min=floor(B/K)` in the radius. This is valid with stable
targets because all group expectations equal the target. General drifting
targets require an explicit bound on each group target's distance to the
reported window mean. “Discarded or deterministically distributed without
changing constants” (appendix 98) is not an adequate executable rule.
For m=16 and delta=.05, K=52, hence B must be at least 104; for larger families
the advertised fixed B may become infeasible. Never reduce K to force a run.

## P0.5 — Coupling event is not a radius or a conditioning trick

**Blocker for a numerical advertised level outside independence.** Sources:
compact method 45–48 versus theory 25; full method 66–74 versus theory 35;
appendices 98,119,126,179.

The paper's probability is at least `1-delta_stat-epsilon_coup`.
An advertised 95% interval needs total failure <=.05, not delta=.05 followed
by an extra unbudgeted coupling error. `epsilon_coup` has probability units;
it is not an additive score/radius term.

Also, “super-blocks are independent on the coupling event” (appendix 119) is
not justified: conditioning independent copies on a joint successful-coupling
event can make them dependent. The valid transfer is
`P(failure_original|D) <= P(failure_copy|D)+P(any mismatch|D)`.
Concentration is proved for the independent copy law **before** conditioning on
coupling success. A coupling must concern the whole relevant vector (including
all candidate scores), preserve the target/design relationship, and have a
specified measurable failure bound. A bound for raw observations need not
survive evaluation-dependent nuisance fitting.

**Correct patch:** independent Gate B sets epsilon=0 by DGP construction. A
future mixing corollary needs a precise beta convention, process, gap and joint
coupling theorem. Unknown mixing rates imply sensitivity status, not epsilon=0.

## P0.6 — Drift and MOM nuisance-bias transfer

**Blocker for unknown drift or average-only nuisance correction.** Sources:
compact setup 78, method 54–59, theory 25–37; full setup 108–113, method 76–87,
theory 44–53; appendices 124–126,154–160.

For deterministic block/group means `(0,0,3)`, the window average is 1 but
MOM is 0 even with no random estimation error. Unknown counterfactual drift is
not removed by equal block sizes, and a fitted drift diagnostic is not a proved
upper bound. The full theory calls drift “measurable” at line 50, which is not
equivalent to observable or estimable with a valid finite-sample bound.

There is a second transfer gap: the displayed nuisance remainder is a window
average, while MOM is nonlinear. Suppose oracle block targets are all zero
but deterministic plug-in biases of three equal groups are `(0,c,c)`. The
average absolute bias is `2c/3`, yet the MOM bias is `c`. Replicate each group
into any equal number of blocks to meet B>=2K. Therefore a window-average
`R_nuis` cannot be added with coefficient one as a uniform MOM shift bound.
This is separate from the validity of the pointwise DR identity.

**Correct patch:** stable targets and exact e/fixed fit imply both corrections
zero in Gate B. For an extension, require known simultaneous bounds
`max_b |E bar Z_b - M_b^oracle| <= r_nuis` and
`max_b |M_b^oracle-M_W| <= Delta`, or a proved alternative controlling good
group biases. If these bounds are random, their failure probabilities must be
spent separately. Do not substitute oracle errors into the estimator interface.

## P0.7 — False centering inequality and corrected lower bound

**Blocker in original proof; corrected construction proved.** Sources: compact
theory 44–55; full theory 60–75; both appendices 184–198, especially 191–192.

For `X~Bernoulli(.1)` and `p=1.5`, `E|X|^p=.1`, but
`E|X-EX|^p=.9*.1^1.5+.1*.9^1.5=.11384199576606167>.1`.
The asserted inequality is false. Also epsilon=1/n at n=1 gives mutually
singular point masses, so “small n absorbed into the constant” is not a proof
with that construction.

For every integer `n>=1`, use `epsilon=1/(2n)`,
`a=nu_p(2epsilon)^(-1/p)=nu_p n^(1/p)`,
`P0=delta_0`, `P1=(1-epsilon)delta_0+epsilon delta_a`.
The exact centered p-moment is

`a^p [(1-epsilon)epsilon^p + epsilon(1-epsilon)^p]
 <= a^p(epsilon^p+epsilon) <= 2epsilon a^p = nu_p^p`.

The mean gap is `Delta=epsilon a=(nu_p/2)n^(-(p-1)/p)`.
The sample laws overlap only at the all-zero vector and
`1-TV(P0^n,P1^n)=(1-epsilon)^n >=1-n epsilon=1/2`.
For any estimator T, including randomized T, the triangle inequality integrated
against the overlap measure yields

`E0|T| + E1|T-Delta| >= Delta(1-TV)`.

Consequently
`max(E0|T|,E1|T-Delta|) >= Delta(1-TV)/2
 >= Delta/4 = (nu_p/8)n^(-(p-1)/p)`.
Thus the theorem can take explicit constant `c_p=1/8` (independent of p) by
this valid, conservative argument. The looser testing reduction constant 1/16
would also be valid, but is unnecessary. Exact chi-fold replication is a
statistically equivalent experiment with n=N/chi.

This establishes an **expected absolute-risk** lower bound over the clique
replication subclass. It neither proves sharpness for every fixed sparse graph
nor supplies the confidence/family-size logarithms in a simultaneous
high-probability theorem. Scope wording after the theorem must preserve this
distinction.

## P0.8 — Subgroup denominator target

**Major; resolved by declaring the target.** Sources: compact method 61–68,
theory 39–42; full method 89–104, theory 55–58; appendices 10.

For a realized fixed pre-action design, binary h has exact mass
`pi_D=N^-1 sum h_u`; r_pi=0. For a random population, `pi=E h(X)` is different.
For example h~Bernoulli(.1) can produce an all-zero observed sample while
population mass remains .1. A ratio theorem must state which quantity is in
the denominator. In the original path equation, if h is not Fprev measurable,
the predictable denominator is `N^-1 sum E[h|Fprev]`, not the observed count.
For positive exact mass, divide the numerator interval by pi; if zero, abstain.
Nonzero count does not fix a target support violation or make a wide CI useful.

## P0.9 — Repair and deployment scope

**Eventwise algebra proved; stronger deployment claim unproved.** Sources:
compact repair 29–37; full repair 51–63; both appendices 222–239; main abstract
62; RESEARCH_TODO 5.

On a simultaneous event for the specified frozen moments, UCB feasibility gives
`C_j(q_hat)<=C_hat_j(q_hat)+r_j(q_hat)<=alpha_j`. A comparator satisfying
`C_j(q)+2r_j(q)<=alpha_j` is feasible and LCB optimality yields
`V(q_hat)>=V(q)-2r_V(q)`. The original proof of this deterministic implication
is correct when a solution exists and the simultaneous premise holds.

It is silent about future transitions. A policy can have zero one-step harm
on today's contexts while sending every unit into a future state with harm one.
No current-context moment bound excludes that. Repeated-epoch union bounds with
`alpha_e=alpha_total/[e(e+1)]` require each epoch's conditional validity given
its past and a preallocated schedule; spending alone cannot repair an invalid
per-epoch theorem. Patch language to local/logging-path feasibility.

## P0.10 — Exact slate and interference exposure probabilities

**Major; identified finite-state calculation, not item-propensity substitution.**
Sources: compact setup 4–24, experiments 7–19; full setup 5–35, experiments
15–31; both appendices 4.

For a full logging assignment A and exposure g,
`e(s)=sum_(a:g(a)=s) pi_log(a)`; q uses the same exposure state. Sampling two
distinct items uniformly from three gives marginal inclusion 2/3 for each item,
but joint inclusion of items 1 and 2 is 1/3, not 4/9. For ordered
Plackett–Luce draws, `P((i,j))=w_i/W * w_j/(W-w_i)`; sum these probabilities
over every ordered slate with the given multicomponent exposure. Neighbor
assignment must be part of that same complete assignment distribution.

The synthetic softmax/UniformTopK mixture in the manuscript needs a common
sample space: define a distribution over complete slates before mixing. The
finite enumerator and normalization/support tests are an appropriate Gate B
check. They do not establish exposure completeness for a real interference map.

## P0.11 — Finite moment order is not a tail exponent

**Major reporting correction; large rate studies deferred.** Sources: compact
theory 37, experiments 4,19; full theory 50, experiments 31–33;
RESEARCH_TODO 84,96. Student-t(df=5) has a finite p=1.5 moment and finite
variance. Its empirical error can decrease at an n^-1/2 rate, faster than the
n^-1/3 finite-p worst-case upper bound. Pareto exponent alpha must exceed p;
it is not equal to the available moment order p. Use the N-dependent Le Cam
family for a worst-case illustration and call fixed-DGP slopes descriptive.

## P0.12 — Unconditional finite moments versus a uniform conditional envelope

**Blocker for substituting integrated weak-overlap moments.** Sources: compact
setup 64–73 versus theory 8,21; full setup 85–101 versus theory 11,30.

Let `E~Beta(a,b)` with positive shapes, `S|E~Bernoulli(E)`, and independent
Rademacher R. Let target q(1)=1, Y(1)=R, Y(0)=0, mu_hat=0, h=1, f=0. Then
`Z=S R/E`, `E[Z|E]=0`, and
`E[|Z|^p|E=e]=e^(1-p)`.
Integration gives
`E|Z|^p=B(a+1-p,b)/B(a,b)<infinity` exactly when `a>p-1`.
Nevertheless `sup_(e>0)e^(1-p)=infinity`. With a=1,b=1,p=1.5, the integrated
moment is 2 while the conditional moment at e=10^-8 is 10^4.

The same gap occurs with bounded nonnegative reward: take Y(1) Bernoulli(1/2)
independent of E,S and mu_hat(1)=1/2. The centered score is
`S(Y(1)-1/2)/E`, whose conditional moment is `2^-p e^(1-p)`.

Three honest routes are distinct: an annealed graph model integrating random
contexts; a legitimate exogenous-design conditional model with an analytically
computed design-dependent envelope; or a positive-floor design. Theorem A and
Gate B use the declared bounded-reward design envelope and fixed support floor.
They do not establish the original arbitrary unbounded-ratio adaptive theorem.
If nu changes with N or realized design, a rate plot must disclose that change.

## Additional technical findings and remaining work

* **Graph sufficiency:** pairwise independence is insufficient. Independent
  Rademachers U,V give `(U,V,UV)` pairwise independent but not mutually
  independent; an edgeless dependency graph requires independence of arbitrary
  disjoint vertex sets. The clique DGP satisfies the stronger property.
* **Coloring algorithm:** full setup 104 asserts chi_used<=degeneracy+1 for a
  “fixed proper-coloring algorithm.” This bound requires an appropriate
  reverse-degeneracy ordering, not an arbitrary greedy ordering. A path with
  vertex order `(v1,v4,v2,v3)` greedily uses three colors although degeneracy=1.
  Report the actual valid coloring count; do not replace it by an unsupported
  smaller value.
* **Uniform class extension:** full theory 4 mentions an entropy integral for
  VC-type classes without stating/proving assumptions. This is a proposed
  extension, not a proved consequence of the finite-family union bound.
* **Tail tuning:** compact method 70–71 and full method 58–59 distinguish known
  scale from proposed Lepski tuning, but empirical validation cannot turn
  estimated nu into a finite-sample theorem. Keep it outside the certified API.
* **Empirical claims:** the compact/full experiment sections are protocols,
  and full experiments 75–95 is an empty table shell. Neither supplies measured
  coverage. Gate B smoke runs must remain labeled debugging, with Wilson
  uncertainty and no publication claim.

Gate A closes the restricted theorem's proof obligations and the lower-bound
error. Adaptive path inference, mutually trained nuisance concentration,
unknown drift/bias/scale calibration, general mixing coupling, rich auditor
classes, and closed-loop deployment guarantees remain open research tasks.

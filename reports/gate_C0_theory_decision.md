# Gate C0 theory decision

The exact-binomial MOM refinement and the bounded-outcome graph-variance
certificate are proved under explicit independent, exogenous-design models.
They support the focused C0 comparison. They do not resolve the paper's general
adaptive-path claim or establish useful heavy-tail performance. Retain finite-p
MOM as the robust theoretical benchmark; make the bounded-outcome comparison
the immediate practical test and leave adaptive martingale theory to Gate C1.

This decision uses the frozen pilot code at
`15af1842dff7dddf89bbad1c98e8b3ac7a8de3b0`. Code and proof line references below
refer to that revision. Gate A+B theory and saved outputs remain the baseline;
no manuscript theorem was silently broadened or narrowed. The copy-pastable
suggestions are in `reports/gate_C0_paper_patch_suggestion.tex` and are not
included in the manuscript.

## What is established

| Route | Proved statement and its conditions | C0 implementation/status |
|---|---|---|
| Conservative finite-p MOM | Simultaneous intervals for a frozen family, known conditional centered p-moment envelope, independent evaluation blocks and a common block target. Sufficient graphs justify within-block reduction. | Original default remains available; `CERTIFIED` only in the registered bounded synthetic model. See `theory/theorem_to_code_contract.md:23–104`, `comet/certification.py:91–147`. |
| Exact-binomial finite-p MOM | Same model, target and radius constant. Independent bad-group indicators with individual probabilities at most eta are dominated by Bin(K,eta); choose feasible odd K using the exact familywise tail. | Implemented switch, eta fixed at 1/8; no outcome-based K selection. See `theory/exact_binomial_mom.md:18–118`, `comet/robust_mean.py:58–120`, `comet/certification.py:105–129`. |
| Bounded graph Chebyshev | For bounded rewards and permissible fixed fits, exact e yields unbiased row scores, known row variance bounds, graph-adjusted block variance, and a simultaneous sample-mean interval. Heterogeneous exogenous row/block expectations are allowed by this theorem. | Separate `bounded_graph_chebyshev` method. API retains the narrower stable registered model; it does not accept arbitrary heterogeneous logs. See `theory/bounded_graph_variance.md:18–138`, `comet/bounded_variance.py:60–156`. |
| Known-support intersection | Intersecting an interval with surely known target support preserves its coverage. Full-range intersections supply no information; empty intersections remain empty confidence sets. | Raw and intersected bounds are retained; an empty intersection cannot authorize a decision. See `theory/bounded_graph_variance.md:140–147`, `comet/informativeness.py:5–39`. |
| Weight clipping with bias debit | A fixed cap has an explicit bias bound and a smaller variance envelope under the same bounded/exogenous conditions. The stochastic radius plus the bias bound covers the original target. | Proof and deterministic identity tests only; no clipping API or clipping pilot. See `theory/bounded_graph_variance.md:149–185`. |

All nominal claims concern each method's full frozen `(q,h)` family at a single
predeclared level and window. They are not simultaneous over a post-hoc choice
among methods, confidence levels or windows. Reporting several separate nominal
procedures does not justify selecting the narrowest or best observed method
with the same unadjusted confidence label. Such a selection needs a legitimate
design-only conditional proof, an independent pilot that preserves evaluation
assumptions, or a simultaneous budget across the procedures considered. For
example, allocating alpha across method-specific error budgets would support a
union guarantee; running every method at alpha does not supply that guarantee.
The C0 comparison evaluates the methods separately and does not implement such
a selected-method certificate.

## Why the two refinements are valid

For MOM, the conditional color-class moment argument gives block constant 2;
a second independent-block moment bound gives group constant 4. Markov at
`a=(4/eta)^(1/p) nu_p (chi/(L_min*n0))^((p-1)/p)` makes each group's failure
probability at most eta. Disjoint groups remain independent after conditioning
only on exogenous design and a permissible independent pilot. Conditional
Bernoulli domination requires independent indicators, not identically
distributed ones. These are the proofs at
`theory/exact_binomial_mom.md:40–87`.

With eta=1/8, the radius retains `32^(1/p)`; the improvement changes K and thus
L_min. For m=16, alpha=.05 and B=128, old K=52/L_min=2 becomes K=9/L_min=14;
the exact family tail is `0.039716482162475586`. The radius ratio is
`7^(-(p-1)/p)`. These are deterministic fixtures, not empirical measurements
(`theory/exact_binomial_mom.md:120–147`). The exact rational comparison avoids
tail-underflow decisions, and the displayed tail is rounded upward. All blocks
are retained by `comet/robust_mean.py:123–139`. Unequal group sizes are harmless
here precisely because their target means are equal. Merely changing the K rule
cannot repair varying-target MOM; that still needs a proved drift debit or a
different estimator (`theory/exact_binomial_mom.md:173–176`).

For the bounded alternative, the direct-method component is fixed conditional
on D and `|Y-mu_hat|<=1`. Thus
`Var(Z_u|D)<=h_u^2 sum_s q_u(s)^2/e_u(s)`. Color-class variance additivity and
Cauchy–Schwarz across colors give `chi_b sum_u v_u`; actual block independence
then gives `V=N^(-2) sum_b chi_b sum_u v_u`. Chebyshev and a union bound give
`r=sqrt(m V/alpha)` (`theory/bounded_graph_variance.md:54–132`). This proof uses
no empirical variance, oracle response means or nuisance-consistency claim.
The code computes e/q/h-only envelopes at `comet/bounded_variance.py:16–35` and
`91–100`, with verified coloring at lines 38–57 and 85–86.

The sample mean's conditional expectation is the raw-row average of the row
targets, even when those expectations differ. Consequently this theorem needs
no MOM group-target alignment or drift correction. That benefit does not make
an adaptive future-context-conditioned target valid: D must still be exogenous,
and conditional block independence must still hold. The conditional coverage
integrates to coverage of the random fixed-design target `M_D`, not an
unconditional superpopulation moment substituted in its place
(`theory/bounded_graph_variance.md:40–52`, `122–132`).

## Scope that remains unresolved

The implemented fits are predeclared bounded constants, enforced together with
exact logging and the repeated exogenous context design at
`comet/certification.py:18–49`. A nuisance pilot independent of the entire
evaluation experiment is covered at the theorem level. A fit merely predictable
along the same adaptive evaluation history is not automatically covered.
Conditioning on the collection of those fitted values can reveal past evaluation
outcomes and destroy the claimed block factorization. Mutually trained cross-fit
fits can likewise induce score dependence; exact-e DR algebra alone does not
restore concentration. See `theory/exact_binomial_mom.md:20–25` and
`theory/bounded_graph_variance.md:34–38`.

Known conditional moment envelopes are different from unconditional finite-p
moments. The present bounded-reward envelope is explicitly
`2^(2p-1) [1+sum_s q(s)^p e(s)^(1-p)]`, maximized over the fixed contexts
(`comet/dr_scores.py:40–52`, `comet/certification.py:143–147`). Finite supported
designs make this quantity known and finite in exact arithmetic, but neither
support positivity nor an unconditional moment assumption supplies a uniform
conditional bound when random e approaches zero. No estimated tail scale has
been promoted to a known envelope. The bounded variance route also deteriorates
as q/e grows; missing target support remains nonidentification
(`comet/dr_scores.py:15–21`).

The graph is a sufficient stochastic dependency model, not a statement that can
be established by matching observed identifiers or testing correlations. A
hidden permanent shock across blocks invalidates both proofs. Schema guards
refuse disclosed unsupported models and inconsistencies but cannot identify
every hidden violation in an otherwise plausible realization
(`theory/bounded_graph_variance.md:195–201`). No general dependent-block coupling
theorem was added. Here coupling failure, nuisance bias and drift budgets are
zero by construction. Any future coupling failure must consume probability
budget; it cannot be added as a numerical radius
(`theory/theorem_to_code_contract.md:135–157`).

The certified simulator remains bounded-Y even when p=1.5 or p=1.2 is used in
the MOM radius. Those cells stress the weaker moment bound and its constants;
they do not demonstrate an infinite-variance reward distribution. Finite-p MOM
still has a theoretically relevant role when variance is unavailable, but C0
has not established practical heavy-tail superiority or a useful unbounded-
reward certified implementation. Preserve the existing chi-clique lower-bound
scope from Gate A; no refinement here proves sharpness for every sparse graph.

Fixed eta=1/8 is the implemented comparison. A predeclared deterministic eta/K
optimization using only legitimate design and known envelopes has a conditional
selection argument, but no eta optimizer is implemented or tuned here
(`theory/exact_binomial_mom.md:155–171`). The optional clipping derivation likewise
does not authorize a cap chosen from observed certification outcomes. Its bias
cost must accompany any future variance gain.

## Gate C1 proof checklist, outside this implementation

The next adaptive theory should start with an explicit predictable target and
prove concentration for that target, rather than condition an independent-block
argument on a realized adaptive history. Before exposing a C1 certified API,
the following obligations remain:

1. **Filtration and estimand.** Define `F_(t-1)` immediately before round t's
   randomization. For a predeclared finite horizon and normalization, specify
   `m_t(theta)=E[sum_{u in t} Z_u(theta) | F_(t-1)]` and the target
   `N^(-1) sum_t m_t(theta)`. Show that centered round increments are integrable
   martingale differences for the stated filtration. Distinguish this random
   predictable target from a target conditional on future contexts and from
   long-run closed-loop deployment performance.
2. **Randomization and dependence.** Specify the exact conditional joint-slate
   assignment law and derive the exposure-state e(s). State consistency and
   conditional randomization. Prove sufficient within-round score dependency
   graphs conditional on `F_(t-1)` and justify graph measurability. Coloring
   adjacent adaptive rounds does not make those rounds independent.
3. **Predictable nuisance and family.** Require mu_hat, q and h to be measurable
   before the current action under the chosen filtration, and show the actual
   score has the claimed conditional expectation. Identify how training data
   and any policy/auditor selection enter that filtration. A large or growing
   family requires its own complexity or probability allocation argument;
   arbitrary post-evaluation family selection is not covered.
4. **Bias and conditional moments.** State known conditional p-moment envelopes
   for the variable actually truncated. Derive the conditional truncation or
   weight-clipping bias relative to the original predictable target, accumulate
   it with the correct normalization, and add it as a numerical bias budget.
   For example, the bound `E[|W| 1{|W|>c}|F] <= E[|W|^p|F]/c^(p-1)` requires the
   displayed conditional raw moment; a centered envelope cannot be silently
   substituted for it. Estimated envelopes need a separate valid confidence
   event and its probability debit.
5. **Variance and martingale concentration.** Derive the conditional variance
   bound for the centered round increment, including genuine within-round
   graph dependence, and establish any bounded-increment requirement. Supply
   either a deterministic bound on the accumulated predictable variance or a
   proved self-normalized/peeling/mixture construction. A random realized
   predictable variance cannot simply be plugged into a fixed-variance
   Freedman bound. Any peeling or stopping event must be covered by the proof
   and its failure budget; no such theorem is implemented in C0.
6. **Simultaneous probability accounting.** Allocate failure across policies,
   auditors, time windows or stopping times, nuisance/envelope events, and
   tuning choices such as clipping caps. Prove an anytime statement if repeated
   monitoring is intended. Keep statistical and coupling failure probabilities
   separate from nuisance, truncation and drift radii. Map every reported
   certificate field to that explicit theorem.

## Experimental decision boundary

Theoretical approval is limited to running the preregistered C0 diagnostic with
the three separate valid methods under the registered model. A sharper bounded
certificate is a useful theorem-to-code addition; graph coloring plus Chebyshev
alone is not a major novelty claim. Whether the paper should emphasize a new
adaptive contribution depends on resolving C1, not on renaming this baseline.

The final C0 PASS and full-Gate-C GO/NO-GO decision belongs in
`reports/gate_C0_report.md` after inspecting the frozen pilot outputs. It requires
all four task criteria: a proved radius, a strictly nontrivial interval in at
least one predeclared useful bounded-Y/exact-e setting without truth selection,
honest refusal/status for inapplicable settings, and passing existing plus new
tests. If every rigorous route remains vacuous even in the predeclared easy
setting, the decision must be NO-GO and theory redesign. Weak-overlap or tail
stress failures must remain visible even if an easy setting passes.

No pilot coverage, width, non-vacuity, abstention or false-safe value is asserted
in this theory document. Those numbers must come from saved outputs. Small
replication counts provide debugging evidence with Wilson uncertainty, not a
verification of nominal coverage. Passing C0 authorizes the next research stage
only; it does not establish final paper claims or deployment safety.

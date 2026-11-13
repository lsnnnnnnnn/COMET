# D3 — policy repair with competing outcomes (UNRUN PROPOSAL)

Fresh domain: `COMET-D3-v1`. Introduce distinct bounded utility and harm/cost
potential-outcome channels; shared primitives inside a cluster are allowed and
must be included in its graph. Specify genuine tradeoffs: interventions can
increase utility and harm differently across exogenous contexts. Register
8/16/32 valid target joint policies or feasible mixtures, 2/3/4 constraints,
exact induced exposure laws, and a substantively safe fallback. Include a
setting with no statistically certified feasible candidate despite a truly
feasible policy, so abstention is observable and permissible.

Freeze a single simultaneous family over every policy × (utility + all costs),
including auditor indices if constraints are subgroup-specific. Each procedure
gets its own explicitly allocated alpha; no shortest-method selection. For
bounded channels the graph theorem applies to every score, followed by a union
bound over the complete library. Fixed or independent-pilot nuisance only.
COMET chooses the largest utility lower bound among policies with every cost
upper bound ≤ its threshold; if none exist, report ABSTAIN, unless a fallback
has a separate deterministic/model-certified guarantee. Never silently deploy
an uncertified fallback as certified.

Comparators: utility-only argmax; DR point empirical constraints; clipped/SNIPS
point constraints (POINT_ONLY); pessimistic COMET; oracle hindsight evaluation
never used as a fit or selection input. Tie rules are frozen. Primary outcomes:
true selected utility, max true constraint violation, per-log false-safe
selection, abstention and certified feasible-set size. Regret uses two distinct
comparators: (1) best policy with true costs below thresholds by the required
2r margins, for which the eventwise proof guarantees inclusion; (2) best truly
feasible policy, an informative oracle benchmark without that regret theorem.

Only fixed-window eventwise feasibility is claimed. If policy q* is in the
2r-margin comparator set, simultaneous coverage puts it in the certified set;
LCB maximization gives utility regret at most 2r_U(q*) (or the appropriate
candidate-specific width). It gives no adaptive deployment trajectory safety.
Propose 1,000 independent logs per final cell; exact channel constants, policy
list, sample sizes, confidence budget and null/alternative grid need a separate
freeze. Analytic feasibility precedes pilot resource allocation. D3 is unrun.

# Mapping from the earlier heavy-tailed COPF notes to COMET

The earlier source was organized as three parallel tasks: heavy-tailed COPF auditing, normalized-momentum online control, and random-graph bounds for dependence and propensity moments. The new paper keeps the useful counterfactual ingredients but changes the scientific object and paper identity.

| Earlier component | New role | Treatment in the bundle |
|---|---|---|
| Evolving-graph link recommendation | One application | Moved out of the problem definition; retained as the COPF specialization |
| Shown/not-shown potential outcomes | One exposure mapping | Generalized to a finite local exposure state `S = g(A_I)` |
| Strict overlap `e_min <= e <= 1-e_min` | Too strong for the intended tail regime | Replaced by target-support positivity plus finite-p counterfactual score moments |
| GA-DR pseudo-outcomes | Core reusable idea | Rewritten as a generalized orthogonal score for arbitrary target interventions |
| Residual-OI over fixed group/score slices | Special counterfactual moment family | Generalized to policy–auditor moments and learn-then-certify auditors |
| Maximum-degree `kappa` and mixing time | Coarse dependence summary | Replaced in the main result by logged conflict-graph coloring plus an explicit block-coupling correction |
| Dynamic truncated mean | Initial robust estimator | Moved to a streaming appendix variant; graph–time median-of-means is the main estimator |
| Ratio fairness certificate | Important but incomplete denominator treatment | Rewritten with simultaneous numerator and subgroup-mass uncertainty and mandatory abstention |
| Heavy-tailed NSGDM controller | Parallel optimization contribution | Removed from the main identity; replaced by certificate-guided finite-library policy repair |
| Random-graph generative Task C | Optional model-specific direction | Reduced to protocol/design discussion and future appendix work |
| Fixed stationary expectation | Mismatched with adaptive deployment | Replaced by a predictable window-average target and an explicit drift term |
| Placeholder rate `Rate(T; ...)` | Not yet a theorem | Removed; the compact paper states a concrete finite-p upper rate and cluster lower bound |

## What was intentionally preserved

- counterfactual exposure effects;
- doubly robust/orthogonal pseudo-outcomes;
- residual tests as an auditing interface;
- local interference and observable dependence structure;
- the idea that candidate/slate design affects statistical effective sample size;
- the evolving-graph COPF setting as a motivating and experimental special case.

## What makes the new paper distinct

1. The primary object is a general family of counterfactual moments rather than one fairness metric.
2. Weak overlap and outcome heavy tails are modeled separately through finite-p score moments.
3. Dependence enters through a constructible conflict graph and guarded temporal blocks.
4. Rich subgroup discovery is separated from valid certification.
5. Uncertainty is used to select a feasible policy, not attached after a generic optimizer has run.
6. The experiment design is centered on coverage, false certification, abstention, and policy feasibility.

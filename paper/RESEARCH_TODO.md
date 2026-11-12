# Research completion plan

The paper is now organized around a single claim:

> Counterfactual moment families can be estimated, audited, and used for safe policy repair under weak overlap, finite-p score moments, and observable graph–time dependence.

The items below are ordered by submission risk rather than convenience.

## P0 — theorem and assumption closure

### 1. Fix one primary probability model

Write an assumptions table that separates:

- predictable adaptive history and the pathwise window target;
- the within-block conditional dependency graph;
- the exact condition under which a proper coloring creates conditionally independent color classes;
- the cross-block coupling or mixing assumption and its observable/tunable gap parameter;
- within-window drift;
- whether propensities are exactly logged or estimated.

Do not mix a stationary beta-mixing target with an adaptively changing deployment target in the same theorem. The compact draft uses a predictable target and an optional offline coupling correction.

### 2. Close the upper-bound proof

Verify every transition in Appendix D:

- conditional von Bahr–Esseen within color classes;
- convexity across dependent color sums;
- equal-block target preservation;
- coupling from original blocks to independent copies;
- median-of-means majority probability;
- union bound over the frozen finite policy–auditor family;
- drift transfer from block means to the window target;
- nuisance bias transfer from the exact DR remainder.

Produce a lemma-by-lemma proof file or proof checklist. Track constants only after the logical dependencies are stable.

### 3. Make nuisance handling operational

Use one of these clean routes in the primary theorem:

- **Exact propensity route:** propensities are logged by design; outcome regression may be arbitrary/cross-fitted. This gives the cleanest certificate.
- **Estimated propensity route:** state high-probability overlap-weighted norms for outcome and propensity errors and derive a computable product bound.
- **Sensitivity route:** report certificates over a user-specified nuisance-bias budget rather than pretending the true bias is observable.

The paper should not call a radius “computable” unless every term can be obtained from logs and declared assumptions.

### 4. Finish the lower bound

For the cluster-replication subclass:

- choose explicit two-point distributions with finite pth centered moment;
- compute mean separation and total variation/KL exactly;
- apply Le Cam’s lemma;
- scale from n = N/chi independent clusters back to N rows;
- state precisely which graph class the lower bound covers.

A lower bound for clique replication is evidence that the general chi penalty is unavoidable; it is not automatically sharp for every sparse structured graph.

### 5. Decide the tail-tuning claim

Choose one:

- assume known p and scale in the theorem, with sensitivity analysis in experiments;
- prove a Lepski/multiscale adaptive rule;
- use a robust estimator whose tuning depends only on a confidence level and an estimable scale under additional assumptions.

Do not claim adaptive validity until the selection step is included in the probability argument.

## P0 — minimum credible experiment set

### A. Controlled synthetic coverage study

Implement four regimes:

1. strong overlap + light-tailed outcome;
2. weak overlap + bounded outcome;
3. strong overlap + heavy-tailed outcome;
4. weak overlap + heavy-tailed outcome.

Cross with:

- tail index p in {1.2, 1.5, 1.8, 2.0};
- sample size over at least one order of magnitude;
- exploration probability;
- graph coloring/dependence strength;
- temporal persistence;
- correctly specified and misspecified nuisance models.

Required plots:

- nominal versus empirical coverage;
- interval width and median error versus raw N;
- the same quantities versus N_eff;
- fitted log–log slope versus the predicted -(p-1)/p;
- undercoverage when graph/time correction is removed;
- support-stratified abstention and false-certification rates.

For the central 95% coverage plots, use enough repetitions that Monte Carlo uncertainty is reported and is small relative to the claimed differences. Store every configuration and seed.

### B. TGB semi-synthetic dependence study

Keep real timestamps, node recurrence, degree heterogeneity, and candidate structure. Simulate logging and potential outcomes so truth is known. Compare:

- no dependence correction;
- temporal blocks only;
- graph correction only;
- graph + temporal correction;
- maximum-degree, degeneracy, and greedy-coloring design effects.

The graph backbone is not the contribution; hold it fixed across estimators.

### C. Open Bandit OPE

Use one behavior-policy log to evaluate another and compare with a disjoint on-policy target. Repeat in both directions and along interpolated target-policy mixtures. Report:

- importance-ratio tails;
- standard and conflict-adjusted effective sample size;
- point error, coverage, width, and abstention;
- exact data splits and whether any context filtering affects support.

### D. Discover–certify subgroup study

Plant a subgroup that cannot be represented by the fixed slices. Compare:

- fixed auditors;
- in-sample rich auditor search;
- ordinary sample splitting;
- graph/time-separated discover–certify.

Report subgroup support, overlap with the planted rule, discovery effect, certified effect, false discoveries under a null generator, and replication after drift.

### E. Pessimistic repair

Construct a finite policy library with controlled utility and constraint frontiers. Compare utility-only, empirical constraints, clipped-DR constraints, and COMET pessimistic repair. Report true utility, maximum violation, infeasibility/abstention, and how the feasible set expands with N_eff.

## P1 — strong ICLR additions

- KuaiRand watch-time and repeated-user study.
- Unknown-p adaptive estimator with a formal guarantee.
- Fractional coloring or a tighter graph-specific design effect.
- Rich auditor classes with complexity control beyond frozen finite candidates.
- Time-uniform or repeated-epoch confidence sequences for sequential repair.
- A sharp comparison between score truncation, MOM, and Catoni-type aggregation.

## P2 — appendix or follow-up work

- Random-graph generative bounds for candidate-set moments.
- Continuous policy classes certified through covering or localized complexity.
- Partial identification when target support is absent rather than merely weak.
- Interference-map sensitivity analysis.
- Privacy-preserving or federated counterfactual auditing.

## Claim audit before submission

- Every theorem is matched to the implementation’s estimator.
- Every confidence interval has all tuning and nuisance terms justified.
- “Heavy-tailed” is tied to a finite-moment assumption or measured tail diagnostic, not just high variance.
- Weak overlap and outcome-tail mechanisms are tested separately.
- Discovery, hyperparameter tuning, nuisance training, and certification data are separated.
- Real-data claims do not exceed what randomization or logged propensities identify.
- Coverage is reported together with abstention.
- COPF is cited as a special-case application, not described as the new paper’s baseline identity.
- The final manuscript is recompiled with exact official ICLR style files and remains within the current page limit.

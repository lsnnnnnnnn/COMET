# Bounded independent agent review of the new core

Review scope: the core residual-truncation proof, scoped lower bound, recovered
`task_materials/post_cstat/THEORY_NOTE.md` and its reconciliation, and the
post-C-STAT manuscript's mathematical scope and interpretation of completed
E1/E2 summaries. This was a separate agent review with shared conversation
context, not a blind human review or formal proof verification. No outcomes
were drawn, no experiment or complete statistical analysis was rerun, and no
frozen file was changed.

## Finding requiring wording correction

**P2 — distinguish the unweighted response moment from the IPW moment in the
main lower-bound proposition.** In
`paper/post_cstat/sections/theory.tex`, the phrase “residual p-moment at most
nu^p” in the scoped lower-bound proposition should explicitly mean

    E|Y(1)-b|^p <= nu^p.

It must not be read as a bound on the weighted raw residual R. In the actual
construction,

    E|R|^p = epsilon^(1-p) E|Y(1)-b|^p
            <= epsilon^(1-p) nu^p.

The appendix already states the weighted bound correctly. Because the preceding
main theorem uses raw weighted residual moments v, the abbreviated main
proposition risks assigning nu to the wrong scale and counting the overlap
penalty incorrectly. The direct repair is to say “unweighted potential-response
residual” and include the weighted bound in the proposition. For example,
p=2, epsilon=.25 and an unweighted moment nu^2 imply weighted moment 4*nu^2,
not nu^2. This is a statement-precision issue; the construction and its risk
calculation do not depend on the ambiguous abbreviation.

## Mathematical conclusions of this review

No additional critical mathematical error was identified within this bounded
review. In particular:

- The sharp clipping-bias constant, restriction 1<p<=2, truncated second-moment
  inequality and centered range 2*tau agree with the recovered theory note.
- Proper-coloring/Hölder gives the stated sub-gamma proxy and the
  square-root-plus-linear tail with scale (2/3)*chi*tau_max. Heterogeneous means
  do not require a common-target or independent-macro-block assumption.
- Query-active induced support retains all edges between retained shared-source
  rows. Signed contrasts, design-only tuning and affine mixture propagation
  preserve their stated targets and do not permit retrospective outcome tuning.
- Actual supported residual ranges and legal bounded variance bounds justify
  the Hoeffding/Bernstein branches. Colorwise recombination retains every color
  and the original normalizer. The fully matched generic configuration is
  expressly reported as equal, rather than an inferior estimator.
- The symmetric thinning construction has observable TV at most 1/2. Its
  parameter distance is 2*eta, so the common-measure argument gives
  risk_sum >= 2*eta*(1-TV) and max risk >= eta/2. Integer constraints, finite
  mean saturation, small effective counts and the unbounded-response limitation
  are explicit. The separate confidence-width consequence is nonsharp and is
  not asserted merely by converting an expected-risk theorem.
- The source note's 49-point grid and the independent proof are reconciled
  explicitly. The original proof files' historical unavailable-note language
  is explained by the addendum rather than silently rewritten inside a freeze.
- The paper distinguishes separate method/level family statements from a
  joint budget across all displayed engines and levels, and distinguishes
  return-and-unsafe from conditional unsafe-given-return.

## Completed E1/E2 interpretation checked against saved summaries

The review read existing `E1_analysis_v1/summary.json`,
`E2_analysis_v1/summary.json` and `E2_detailed_v1/summary.json`; it did not rebuild
their analyses or validate all raw checkpoints.

- E1 reports 12,000 complete logs, 96 primary diagnostics, and 1,000/1,000
  family coverage for each fixed comparison. COMET's saved whole-log detection
  counts are 1,000/1,000 in five bounded cells, 2/1,000 in weak-overlap triangular
  dependence, and 0/1,000 in each heavy cell. These are detection endpoints,
  not pipeline useful-return evidence.
- E2 reports 1,800 condition logs with 300 paired replicate vectors across the
  six conditions. The paper expressly avoids interpreting them as 1,800
  independent vectors. Fixed-cell Wilson intervals use denominator 300, and
  matched-method differences are paired. Holm comparisons need not themselves
  be independent.
- The pointwise fixed-comparison Wilson endpoints [0.996173,1] at 1,000/1,000
  and [0.987357,1] at 300/300 are numerically consistent. They are not promoted
  to simultaneous Monte Carlo confidence across the 96/60 comparisons, and
  nonrejection is not promoted to a proof.
- The E2 text separates pure local truncation radius .03254654 from bounded
  dispatch radius .02110065 and from the global-moment/global-coloring ablation.
  The local width/diameter ratio .04220130 is twice the bounded radius for this
  unit-diameter normalized target. Descriptive per-query and pooled-coordinate
  summaries are not given fictitious candidate-level binomial replication.
- The finite-grid Pareto statement is qualified as a finite machine law, and
  the real-arithmetic envelope argument is not presented as outward-rounded
  machine verification. The manuscript does not infer universal information
  limits or estimator superiority from these results.

There is no recommendation here to alter frozen cells, increase gaps, drop
uninformative logs or weaken matched baselines. Any statement changes needed
for the finding above belong in the manuscript or a versioned addendum, with
frozen scientific evidence preserved.

## Resolution

Root applied the statement-precision repair in the main proposition: it now
explicitly bounds E|Y(1)-b|^p by nu^p and states the weighted IPW bound
epsilon^(1-p)nu^p. The appendix construction and all frozen sources/results
remain unchanged. This resolves the wording finding without a scientific rerun.

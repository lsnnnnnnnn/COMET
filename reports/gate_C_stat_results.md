# Frozen C-STAT results

**C-STAT PASS within the proved independent, exogenous evaluation-block model.** This denotes complete, unchanged-protocol execution and validation. Empirical coverage or nonrejection does not prove the theorem, novelty, fully adaptive validity or long-run safety.

Each coverage observation is one independent complete log family. Candidate-level fractions pool correlated candidates and are explicitly descriptive; they are not additional independent replications. Both nominal levels and all methods share each log. The original twelve preflight logs are excluded.

## Primary 95% comparison

|Cell|Method|Covered / 1000|Wilson95%|Median intersected width / diameter|Candidate nontrivial|No certified decision|Candidate true-violation detection|Exact p|Holm p|
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
|A|orig_mom|1000/1000|[0.996173,1]|1|0.000%|100.000%|0.000%|1|1|
|A|exact_binomial_mom|1000/1000|[0.996173,1]|0.872872|100.000%|100.000%|0.000%|1|1|
|A|bounded_graph_chebyshev|1000/1000|[0.996173,1]|0.0988212|100.000%|98.800%|1.200%|1|1|
|B|orig_mom|1000/1000|[0.996173,1]|1|0.000%|100.000%|0.000%|1|1|
|B|exact_binomial_mom|1000/1000|[0.996173,1]|0.916332|50.000%|100.000%|0.000%|1|1|
|B|bounded_graph_chebyshev|1000/1000|[0.996173,1]|0.268917|100.000%|50.994%|70.000%|1|1|
|C|orig_mom|1000/1000|[0.996173,1]|1|0.000%|100.000%|0.000%|1|1|
|C|exact_binomial_mom|1000/1000|[0.996173,1]|1|0.000%|100.000%|0.000%|1|1|
|C|bounded_graph_chebyshev|1000/1000|[0.996173,1]|0.531225|100.000%|99.981%|0.030%|1|1|
|D|orig_mom|1000/1000|[0.996173,1]|1|0.000%|100.000%|0.000%|1|1|
|D|exact_binomial_mom|1000/1000|[0.996173,1]|1|11.188%|100.000%|0.000%|1|1|
|D|bounded_graph_chebyshev|1000/1000|[0.996173,1]|0.865982|61.806%|93.794%|0.000%|1|1|
|E|orig_mom|1000/1000|[0.996173,1]|1|0.000%|100.000%|0.000%|1|1|
|E|exact_binomial_mom|1000/1000|[0.996173,1]|1|0.000%|100.000%|0.000%|1|1|
|E|bounded_graph_chebyshev|1000/1000|[0.996173,1]|1|31.244%|100.000%|0.000%|1|1|
|F|orig_mom|1000/1000|[0.996173,1]|1|0.000%|100.000%|0.000%|1|1|
|F|exact_binomial_mom|1000/1000|[0.996173,1]|1|0.000%|100.000%|0.000%|1|1|
|F|bounded_graph_chebyshev|NA|[NA,NA]|NA|NA|100.000%|NA|NA|NA|

The17 registered eligible 95% comparisons use exact inclusive lower-tail tests under H0 coverage≥.95, followed by Holm across exactly17. The F graph row is kept as NOT_APPLICABLE and is not an18th test. Full-range and point baselines are outside these17. A failure to reject is not proof of95% coverage. The complete90% secondary summaries are in `summary.csv/json/md`; no extra17+17-family confirmatory claim is made.

## Decisions at the frozen threshold

|Cell|95% graph any true-violation detection / logs|Wilson95%|95% graph any false certification / logs|Wilson95%|
|---|---:|---|---:|---|
|A|12/1000|[0.00687765,0.0208573]|0/1000|[0,0.00382676]|
|B|1000/1000|[0.996173,1]|0/1000|[0,0.00382676]|
|C|3/1000|[0.00102078,0.00878301]|0/1000|[0,0.00382676]|
|D|0/1000|[0,0.00382676]|0/1000|[0,0.00382676]|
|E|0/1000|[0,0.00382676]|0/1000|[0,0.00382676]|

The threshold remains M_D≤.2*pi_h. The per-log table is distinct from the correlated-candidate detection fraction above. Full per-log any-false-safe/any-false-violation, detection, abstention and Wilson uncertainties for every method and both levels are in `independent_validation/family_decisions_and_widths.csv`. Zero observed false certification is not a zero-risk or deployment-safety claim. POINT_ONLY and NOT_APPLICABLE methods issue no certified decision; their zero false-decision count is not evidence of certification validity.

## Informativeness and scope

- A: exact MOM median width/diameter 0.872872, nontrivial candidate fraction 100.000%, no-certified-decision fraction 100.000%. Graph mean: median width/diameter 0.0988212, nontrivial 100.000%, no-certified-decision 98.800%.
- B: exact MOM median width/diameter 0.916332, nontrivial candidate fraction 50.000%, no-certified-decision fraction 100.000%. Graph mean: median width/diameter 0.268917, nontrivial 100.000%, no-certified-decision 50.994%.
- C: exact MOM median width/diameter 1, nontrivial candidate fraction 0.000%, no-certified-decision fraction 100.000%. Graph mean: median width/diameter 0.531225, nontrivial 100.000%, no-certified-decision 99.981%.
- D: exact MOM median width/diameter 1, nontrivial candidate fraction 11.188%, no-certified-decision fraction 100.000%. Graph mean: median width/diameter 0.865982, nontrivial 61.806%, no-certified-decision 93.794%.
- E: exact MOM median width/diameter 1, nontrivial candidate fraction 0.000%, no-certified-decision fraction 100.000%. Graph mean: median width/diameter 1, nontrivial 31.244%, no-certified-decision 100.000%.
- F: exact MOM median width/diameter 1, nontrivial candidate fraction 0.000%, no-certified-decision fraction 100.000%. Graph mean: NOT_APPLICABLE.

Full feasible range has deterministic width/diameter1 and uses the known conditional mean class, including F; it is not a concentration method. Original/exact MOM and graph mean retain separate confidence guarantees. No shortest observed interval was selected across methods. Raw-width, support-intersected width, IQR/P90, family some/all nontriviality, marginal coverage and error/radius details are preserved in the complete artifacts.

F remains a necessary tail-domain stress cell, even if every MOM interval is vacuous. Its ideal Pareto law has finite p=1.5 moment and infinite variance; its finite numerical grid does not literally have infinite variance. E combines weak supported exposure with clique dependence. These cells must remain in the results and figures; good coverage can coexist with uninformative intervals and abstention. No minimax-rate slope is inferred from this fixed DGP.

## Resources, figures and manuscript recommendation

Combined main-batch and zero-draw-resume wall 10677.944s and parent+child CPU 55676.733s; maximum parent/child process peaks across both invocations 211.500/116.828MiB. Detailed invocation scope, failures and recovery are in the execution report. The five regenerable figure families are under `independent_validation/figures/`: coverage with Wilson uncertainty, widths and range baseline, nontriviality/abstention, error/radius including maxima, and resource costs.

**Manuscript: ready for scope/results review, not a submission-readiness claim.** The separate proposal promotes the proved independent-block results and removes unproved adaptive/mutual-cross-fitting main guarantees. This study does not demonstrate discovery, policy repair, realistic non-copy graph dependence or future deployment safety. D1–D5 are separate unrun preregistration proposals. The original paper and independent Overleaf repository remain untouched.

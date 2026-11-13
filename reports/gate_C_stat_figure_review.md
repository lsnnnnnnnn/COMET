# C-STAT completed-figure review

**PASS.** All five actual confirmatory PNGs were visually inspected after independent validation reported PASS for 6,000 complete logs, 1,134,000 candidate records and 28,884,898 checks. The companion PDF exports and all ten file hashes are retained. This review generated no outcomes, changed no statistics and did not regenerate or alter the validated plot bytes.

## Review findings

- All six cells A–F are visible throughout. Titles, axes, legends and annotations are readable without clipping or overlap. Coverage shows both nominal levels and descriptive Wilson uncertainty; no POINT_ONLY confidence intervals are fabricated. The F graph method remains N/A.
- The 17 registered primary 95% comparisons each have 1,000/1,000 family coverage, Wilson interval [0.996173, 1], and exact/Holm p-values of one. These observations match the independent tables; they are not stated as a proof of nominal coverage. The 90% comparisons remain secondary.
- Unfavorable informativeness is preserved: at 95%, F MOM intervals all have width/diameter one, zero nontriviality and 100% no certified decision. E graph mean has median width/diameter one, nontrivial fraction 0.3124375 and 100% no certified decision. No negative cell or inapplicable method is hidden.
- Width plots distinguish full range from nontrivial intervals. The nontriviality heatmap marks point-only/F-graph cells N/A while the adjacent no-certified-decision heatmap retains 100%. Its reusable caption below explicitly supplies the nominal 95% level, which is not printed in the PNG title.
- Error/radius plots retain zeros and display every observed maximum with a diamond. Every maximum is inside its axis limits, and the ratio-one reference line remains visible. IQR, median and min/P90 conventions are stated.
- Resource plots use actual saved evaluation timings and cumulative worker RSS. The reusable caption explicitly states the resource time-box minimum/P90 convention, which is not printed in the PNG title; this is not a standalone method-memory estimate. No statistical or figure-byte change was needed.

## Source and resource reconciliation

The completed `independent_summary.json`, `methods_validation.md`, `reports/gate_C_stat_results.md` and `reports/gate_C_stat_execution.md` were read alongside the figures. All 84 method/cell/level summaries retain allocated denominators. IPS/DM/DR have POINT_ONLY status, undefined coverage and width; F graph has NOT_APPLICABLE status and undefined coverage/width. Zero false certification for those procedures is not evidence of certification validity.

The execution report separately records a 10,389.879-second computation/aggregation invocation and a 288.065-second zero-new-outcome resume, totaling 10,677.944 measured wall seconds. Maximum parent/child process RSS is 211.500/116.828 MiB. The figure shows worker peaks only. Invocation wall/CPU timing begins after initial source/configuration/environment setup; RSS includes startup. Parallel per-log wall totals are not batch elapsed time.

## Reusable figure captions

### 01_family_coverage

Familywise coverage at the separately specified 95% (circles) and 90% (squares) nominal levels, using 1,000 independent complete logs per cell. Error bars are descriptive Wilson 95% intervals for the observed family-coverage frequency; horizontal lines show the two nominal levels. Each method has its own within-family guarantee. F graph mean is N/A because the bounded-outcome theorem does not apply. Point-only procedures have no coverage points. Nonrejection of an undercoverage diagnostic does not prove validity.

### 02_width_distributions

Support-intersected interval width divided by the known feasible target diameter, at nominal 95%. Boxes show the candidate-level 25th–75th percentiles, the line is the median, and whiskers are the minimum and 90th percentile. Candidates sharing a log are correlated; these are descriptive width distributions. A value of one is the full feasible range. The range benchmark uses the known conditional-mean class. F graph mean is N/A; the original and exact MOM intervals in F remain fully vacuous.

### 03_nontriviality_abstention

Candidate-level fractions at nominal 95%. Left: fraction of allocated candidate intervals narrower than the known feasible target range. N/A marks POINT_ONLY IPS/DM/DR and the inapplicable F graph certificate; their frozen numerical nontriviality fraction is zero, but no interval claim is made. Right: fraction of candidates receiving no certified safe/violation decision, including abstention, point-only and inapplicable procedures. Hence these latter methods correctly have 100% no certified decision. Values rounded to two decimals can display 1.00 even when a small number of certificates were issued; exact counts and fractions are in the CSV summaries.

### 04_error_radius

Absolute estimation error divided by the raw certified radius, at nominal 95%, pooled descriptively over candidates within each cell/method. Boxes show the IQR and median, whiskers the minimum and 90th percentile, and open diamonds the observed maximum over all plotted candidate records. Axes include every maximum, zero ratios remain included, and the dashed line marks ratio one. F graph mean is N/A. Small ratios can reflect conservative or vacuous intervals and do not by themselves establish useful decision power.

### 05_resources

Actual per-log evaluation wall/CPU time for all seven methods at both nominal levels on the same log. These payload timings include simulation, score/certificate evaluation and the final oracle/metric join, and exclude checkpoint writing and global batch aggregation. Time boxes show the median and IQR with minimum/P90 whiskers; they are not maximum-runtime whiskers. The memory bar is the maximum saved worker-process RSS high-water observed in each cell, includes process startup and earlier tasks handled by that worker, and is neither standalone per-method allocation nor summed concurrent memory. Complete per-log timings and invocation resources are retained separately; summing parallel per-log wall times does not give batch elapsed time.

These same captions are saved beside the plots in `results/gate_C/confirmatory/independent_validation/figures/README.md`.

## Reviewed file hashes

|File|SHA-256|
|---|---|
|01_family_coverage.png|`36586d8966a3d1c90c282cd3759b580adf94ff137647febc704a39a22d7a288c`|
|01_family_coverage.pdf|`e0d08217710ad00d85b09dd6d93c0654a965df584e83c87fe3bff301ae73a90e`|
|02_width_distributions.png|`4d3238587242bdce39e4be720ff1b9ee354e47dd2499e5e9cbba34fac66f10ca`|
|02_width_distributions.pdf|`a0e751603965bcd4f30f44c4ab5ba4c8eb8506454a1e571a080b8aded81afc59`|
|03_nontriviality_abstention.png|`30bfd89f5c38334292515af3221ca2003ad77180205667e3dda283d9fd62f448`|
|03_nontriviality_abstention.pdf|`6663b8be44f290fcdeb26f0ae03882ed186051cb94425a51ba63668779da1e55`|
|04_error_radius.png|`4e68f985908351d73ba82c1562f2cb790ab4fbae9b6b7e6cbfa6a038e183bfbf`|
|04_error_radius.pdf|`a589704bd0814839193c32ee7f9b231004e23f91b5bf2da623db1f6a0cade64a`|
|05_resources.png|`baec928c630e2141017653ac8b67f6000307adf4b493a8f3ab51200a6a50dc38`|
|05_resources.pdf|`cca301d0c190f32c22023055b7a78d2dce9c030d5b2ab0ba659d217635684365`|

The machine-readable review manifest is `results/gate_C/confirmatory/independent_validation/figure_review_manifest.json`. The PNGs were inspected directly; PDFs are companion vector exports of the same figures, not a claim of a second independent statistical analysis.

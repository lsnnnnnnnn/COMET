# Captions for the completed frozen C-STAT figures

All six cells contain 1,000 independent confirmatory logs. The twelve historical preflight logs are excluded. These captions accompany the unchanged validated PNG and PDF exports. Coverage uncertainty is computed per complete log family; candidate-level displays remain descriptive.

## 01_family_coverage

Familywise coverage at the separately specified 95% (circles) and 90% (squares) nominal levels, using 1,000 independent complete logs per cell. Error bars are descriptive Wilson 95% intervals for the observed family-coverage frequency; horizontal lines show the two nominal levels. Each method has its own within-family guarantee. F graph mean is N/A because the bounded-outcome theorem does not apply. Point-only procedures have no coverage points. Nonrejection of an undercoverage diagnostic does not prove validity.

## 02_width_distributions

Support-intersected interval width divided by the known feasible target diameter, at nominal 95%. Boxes show the candidate-level 25th–75th percentiles, the line is the median, and whiskers are the minimum and 90th percentile. Candidates sharing a log are correlated; these are descriptive width distributions. A value of one is the full feasible range. The range benchmark uses the known conditional-mean class. F graph mean is N/A; the original and exact MOM intervals in F remain fully vacuous.

## 03_nontriviality_abstention

Candidate-level fractions at nominal 95%. Left: fraction of allocated candidate intervals narrower than the known feasible target range. N/A marks POINT_ONLY IPS/DM/DR and the inapplicable F graph certificate; their frozen numerical nontriviality fraction is zero, but no interval claim is made. Right: fraction of candidates receiving no certified safe/violation decision, including abstention, point-only and inapplicable procedures. Hence these latter methods correctly have 100% no certified decision. Values rounded to two decimals can display 1.00 even when a small number of certificates were issued; exact counts and fractions are in the CSV summaries.

## 04_error_radius

Absolute estimation error divided by the raw certified radius, at nominal 95%, pooled descriptively over candidates within each cell/method. Boxes show the IQR and median, whiskers the minimum and 90th percentile, and open diamonds the observed maximum over all plotted candidate records. Axes include every maximum, zero ratios remain included, and the dashed line marks ratio one. F graph mean is N/A. Small ratios can reflect conservative or vacuous intervals and do not by themselves establish useful decision power.

## 05_resources

Actual per-log evaluation wall/CPU time for all seven methods at both nominal levels on the same log. These payload timings include simulation, score/certificate evaluation and the final oracle/metric join, and exclude checkpoint writing and global batch aggregation. Time boxes show the median and IQR with minimum/P90 whiskers; they are not maximum-runtime whiskers. The memory bar is the maximum saved worker-process RSS high-water observed in each cell, includes process startup and earlier tasks handled by that worker, and is neither standalone per-method allocation nor summed concurrent memory. Complete per-log timings and invocation resources are retained separately; summing parallel per-log wall times does not give batch elapsed time.

Regeneration from the complete saved corpus:

```sh
MPLCONFIGDIR=/tmp/comet-matplotlib .venv/bin/python reports/gate_C_stat_audit/validate_confirmatory.py --input results/gate_C/confirmatory --output results/gate_C/confirmatory/independent_validation --phase confirmatory --figures
```

This command validates and plots existing checkpoints; it generates no outcomes. Visual-review hashes are recorded in `../figure_review_manifest.json` and `reports/gate_C_stat_figure_review.md`.

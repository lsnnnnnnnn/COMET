# Gate B smoke coverage — debugging only

30 independent replications; fixed configuration; CPU only. This small smoke run is not statistical evidence of final nominal coverage.

Wilson intervals below are 95% Monte Carlo uncertainty intervals, separate from the estimator’s nominal 90%/95% family confidence level. Each family row has one Bernoulli event per independent replication. Candidate rows share replications and are not independent observations.

| Nominal | Candidate | Issued / total | Covered / issued | Conditional coverage (Wilson 95%) | Issued and covers / total | Mean width | Vacuous |
|---|---|---:|---:|---|---:|---:|---:|
| 95% | SIMULTANEOUS_FAMILY | 30/30 | 30/30 | 1.000 [0.886, 1.000] | 30/30 | 30.7605 | 100.0% |
| 95% | q0.25__all | 30/30 | 30/30 | 1.000 [0.886, 1.000] | 30/30 | 28.2906 | 100.0% |
| 95% | q0.25__group1 | 30/30 | 30/30 | 1.000 [0.886, 1.000] | 30/30 | 28.2906 | 100.0% |
| 95% | q0.75__all | 30/30 | 30/30 | 1.000 [0.886, 1.000] | 30/30 | 33.2305 | 100.0% |
| 95% | q0.75__group1 | 30/30 | 30/30 | 1.000 [0.886, 1.000] | 30/30 | 33.2305 | 100.0% |
| 90% | SIMULTANEOUS_FAMILY | 30/30 | 30/30 | 1.000 [0.886, 1.000] | 30/30 | 30.7605 | 100.0% |
| 90% | q0.25__all | 30/30 | 30/30 | 1.000 [0.886, 1.000] | 30/30 | 28.2906 | 100.0% |
| 90% | q0.25__group1 | 30/30 | 30/30 | 1.000 [0.886, 1.000] | 30/30 | 28.2906 | 100.0% |
| 90% | q0.75__all | 30/30 | 30/30 | 1.000 [0.886, 1.000] | 30/30 | 33.2305 | 100.0% |
| 90% | q0.75__group1 | 30/30 | 30/30 | 1.000 [0.886, 1.000] | 30/30 | 33.2305 | 100.0% |

“Issued and covers” counts abstentions as unsuccessful issuance, not as coverage. Unconditional Wilson bounds are in coverage.csv/json. A vacuous interval contains the entire bounded-outcome feasible target range. Family width and vacuity summarize all issued candidate intervals. No clipping of intervals to the feasible range is performed.

# Gate C0 forensic audit of the preserved Gate A+B smoke

Baseline: `d11a36f3b967165f4e0cdf56bf6a262d178e41bd`. All source line references below are to that exact commit, not later C0 edits. The original artifacts were opened; no previous measurement is inferred from a task description. All original report bytes and saved source hashes are checked by `experiments/forensic_c0.py`. The analysis uses all 240 saved intervals (30 replications × two levels × four candidates). The saved smoke metadata honestly records a dirty precursor checkout at `58ad7bdf8965418cb8c3b48b2214fbc2aadd2a56`; every saved Python module SHA-256 matches the finalized d11a36f baseline. The finalized commit is therefore the line-reference anchor, not a claim that the smoke was executed with that later HEAD.

## Confirmed diagnosis

**The dominant cause is the conservative general finite-p moment/Markov conversion applied to a bounded-reward problem.** At p=1.5 it combines C_p=32^(2/3)=10.07937 with a loose, valid centered envelope nu_p=4.04808 or 4.75493. The current majority rule leaves only L_min=3 blocks per group, so the effective group size is L_min*n0/chi=24. The resulting radii are 14.14529 and 16.61524, against feasible diameters 1 and 0.5. This is not caused by support clipping, an added coupling radius, a hidden bias budget, dropped rows, or a coding double-count of corrections.

The causal arithmetic is explicit: r = 10.07937 × nu_p × 24^(-1/3). As a design-only diagnostic, even the hypothetical largest possible group L=128 (K=1) with the **same** moment/Markov formula gives r=nu_p=4.04808 or 4.75493, still larger than the entire feasible range. K=1 is not claimed to satisfy the family confidence budget. This proves that reducing K alone cannot make this original smoke design informative. The old grouping adds a factor (128/3)^(1/3)=3.49432 over that already-vacuous lower limit of the same formula. All h=0 rows are conservatively ignored by the envelope maximum, so subgroup moments receive the same raw radius while their feasible diameter halves.

## Exact path through the baseline code

| Stage | Verified source lines | Actual behavior |
|---|---|---|
| Frozen settings | `configs/smoke.json:2–14`; `comet/schema.py:43–78` | R=30, p=1.5, B=128, n0=32, chi=4, e1=(.2,.4), fixed mu_hat=(.5,.5), f=.25, q1=(.25,.75), h=all/group1; m=4 |
| CLI / timing | `comet/smoke.py:33–68` | Configuration precedes generation; certify is called before oracle truth is joined |
| DGP | `comet/synthetic.py:10–41`; `comet/truth.py:5–27` | Separate logging/outcome RNG streams; independent cluster records replicated four times; repeated exogenous context pattern; analytic conditional expectation truth |
| Model guard | `comet/certification.py:15–46` | Checks registered design, exact e, fixed nuisance, binary Y, clique duplication; cannot discover an unreported hidden common shock from these checks alone |
| DR | `comet/dr_scores.py:15–37` | Exact same-state e/q, no numerical clipping; known support |
| Moment scale | `comet/dr_scores.py:40–52`; `comet/certification.py:105–109` | nu^p=max_context 2^(2p-1)[1+sum q^p e^(1-p)]; valid conditional bound, no outcome/oracle estimate |
| K and grouping | `comet/robust_mean.py:21–45`; `comet/certification.py:82–104` | K=ceil(8 log(2m/delta)); B>=2K; all blocks assigned once in groups differing by at most one; median of complete-block means |
| Raw radius/status | `comet/robust_mean.py:48–53`; `comet/certification.py:124–148` | r=32^(1/p)nu(chi/(L_min*n0))^((p-1)/p); raw endpoints estimate±r; CERTIFIED under registered DGP; nuisance/drift/coupling zero |
| Existing feasible-range treatment | `comet/smoke.py:60–68,100–104` | Only a vacuity flag; **no support clipping occurred** in saved results |
| Existing export/coverage | `comet/smoke.py:73–105`; `comet/metrics.py:39–63` | Full-range intervals retained in coverage; family denominators are replications, not candidate rows |

For each binary h, the known feasible target interval is [-pi_h f, pi_h(1-f)], where pi_h is exactly 1 or .5. This forensic pass stores the additional intersection with that range without modifying the original interval files. Such intersection preserves coverage because the target belongs to the range. It cannot create information when the raw interval already contains that whole range. Nontriviality uses tolerance `1e-12*max(1, feasible_diameter)` and excludes empty intersections.

## Each nominal level and candidate

All point estimates/endpoints below are medians over the 30 original records; radii, feasible/clipped ranges, and design quantities are constant within each row. Full per-replication raw values are saved in `results/gate_C0/forensic_intervals.csv` and JSON.

| Level | Candidate | Median estimate | Radius | Median raw [lo, hi] | Feasible = clipped [lo, hi] | Clipped width / diameter | Information | Nontrivial |
|---|---|---:|---:|---|---|---:|---:|---:|
| 95% | q0.25__all | 0.119792 | 14.145293 | [-14.025501, 14.265085] | [-0.250, 0.750] | 1.000 | 0.000 | 0% |
| 95% | q0.25__group1 | 0.105469 | 14.145293 | [-14.039824, 14.250762] | [-0.125, 0.375] | 1.000 | 0.000 | 0% |
| 95% | q0.75__all | 0.330295 | 16.615241 | [-16.284946, 16.945536] | [-0.250, 0.750] | 1.000 | 0.000 | 0% |
| 95% | q0.75__group1 | 0.222656 | 16.615241 | [-16.392584, 16.837897] | [-0.125, 0.375] | 1.000 | 0.000 | 0% |
| 90% | q0.25__all | 0.127523 | 14.145293 | [-14.017770, 14.272816] | [-0.250, 0.750] | 1.000 | 0.000 | 0% |
| 90% | q0.25__group1 | 0.102214 | 14.145293 | [-14.043080, 14.247507] | [-0.125, 0.375] | 1.000 | 0.000 | 0% |
| 90% | q0.75__all | 0.334229 | 16.615241 | [-16.281012, 16.949469] | [-0.250, 0.750] | 1.000 | 0.000 | 0% |
| 90% | q0.75__group1 | 0.217231 | 16.615241 | [-16.398010, 16.832472] | [-0.125, 0.375] | 1.000 | 0.000 | 0% |

Both levels: raw_N=retained_N=4096, B=128, n0=32, chi_b=4 for every block, chi_max=4, N_eff=1024, graph nodes=4096, edges=6144. No rows or blocks discarded. 95% uses K=41 (five groups of four blocks and 36 of three); 90% uses K=36 (20 groups of four and 16 of three). Both L_min=3 and L_max=4, explaining identical radii despite different levels and sometimes different point estimates. delta_stat=.05/.10 respectively; epsilon_coup=0, nuisance_radius=drift_radius=0. Every original record has status CERTIFIED, justified only by the specified independent-block synthetic model.

## Coverage, informativeness and abstention

| Level | Issued families | Family coverage | Coverage given issued | Some nontrivial | All nontrivial | Marginal nontrivial | Median clipped width / diameter | Median raw radius / diameter |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 95% | 30/30 | 100% | 100% | 0% | 0% | 0% | 1.000 | 22.452913 |
| 90% | 30/30 | 100% | 100% | 0% | 0% | 0% | 1.000 | 22.452913 |

No full-range interval was omitted. Each level has zero abstention and 100% full-range intervals; the 30/30 family coverage has Wilson 95% uncertainty [0.88649,1], as in the preserved table. It is debugging output, not coverage evidence for a final paper. False-safe certification is **not applicable**, not zero: this smoke defined no safety threshold or policy-selection rule.

## q/e and support accounting

The interval artifact retained only maxima/ESS, and only seed 20261112 has a full saved log. To recover every replication’s missing quantiles, the script replays **only the historical logging assignment stream** from the saved seeds and baseline algorithm; it generates no outcomes, no new truths and no new replication-cells. The first saved seed’s assignments agree exactly with its saved log; all 30 replays agree with saved maximum observed weights and ESS. The q/e columns distinguish realized observed exposures from all row/exposure states given equal state weight. The latter is not the logging probability-weighted distribution. Linear empirical quantiles are used.

| Policy q1 | Observed q/e min, median, p95, p99, max (median across seeds) | All-state q/e min, median, p95, p99, max | Median importance ESS |
|---|---|---|---:|
| q0.25 | 0.62500, 0.93750, 1.25000, 1.25000, 1.25000 | 0.62500, 1.09375, 1.25000, 1.25000, 1.25000 | 3882.583 |
| q0.75 | 0.31250, 0.41667, 3.75000, 3.75000, 3.75000 | 0.31250, 1.14583, 3.75000, 3.75000, 3.75000 | 1865.481 |

The all auditor has 4096 rows / 1024 independent clusters and prevalence 1; group1 has 2048 rows / 512 independent clusters and prevalence .5. Minimum logging probability is .2. There is no support failure. ESS is diagnostic, not substituted for the theorem’s graph effective sample size. Neither positive subgroup mass nor moderate importance ratios rescues the large certified radius.

## Reproducibility and unchanged prior records

Run `.venv/bin/python experiments/forensic_c0.py`. The script checks original source hashes against d11a36f, checks every original report byte against the same commit, checks all 240 radius/endpoints/coverage records, and writes separate C0 files. `forensic_intervals.csv/json` contains every requested per-record design/radius/status quantity including full chi_b and group_sizes; `forensic_candidates.csv/json` and `forensic_family.csv/json` contain the compact summaries. `forensic_provenance.json` records hashes and the zero-new-outcome replay statement. No original report, test, source result, or failed-run log is removed or overwritten.

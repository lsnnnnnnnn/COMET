# Gate C0 report: validity, width and informativeness

This run executes C0 only from experiment baseline
`d11a36f3b967165f4e0cdf56bf6a262d178e41bd`. The branch is
`codex/gate-c0-informativeness`. Proofs, implementation, 377 passing tests and
the full seven-cell pilot configuration were committed **before outcomes** as
`15af1842dff7dddf89bbad1c98e8b3ac7a8de3b0`. Exact delivery/sync SHAs are in
`gate_C0_sync_status.md`. Paper branch SHA remains
`df70f486fc08139057436e2781c212ad741ef646`; only a separate suggested TeX patch
was produced, with no C0 manuscript edits.

## Why the original intervals were vacuous

The forensic reproduction opened all original reports and all 240 saved
intervals. The dominant cause is the loose finite-p envelope plus the
Markov conversion constant, not clipping or a coupling-radius mistake. At
p=1.5, C_p=32^(2/3)=10.07937 and the known conditional scales are 4.04808
and 4.75493. With chi=4, n0=32 and L_min=3 the radius is
`10.07937 * nu_p * 24^(-1/3)` = 14.14529 or 16.61524, versus feasible
diameters 1 and 0.5. Even hypothetical L=128 would give radius nu_p>4;
that algebraic diagnostic does not assert that K=1 meets the confidence budget.
Thus reducing K alone cannot make the original design useful.

The old smoke never applied support clipping. Its raw intervals already
contained the entire feasible range. Nuisance/drift budgets and coupling
failure were zero; no rows or blocks were dropped. Full source/line tracing,
per-candidate quantities, ESS and q/e quantiles are in `gate_C0_forensic.md`
and `results/gate_C0/forensic_*`. The existing 30/30 coverage remains a
debugging observation with Wilson [0.88649,1], and zero informativeness.

The following comparison uses the **original design only**, with no new
outcomes and no retuning of p or nu. Radii apply to q1=.25 / q1=.75;
the all/group1 auditors share these conservative radii.

| Nominal level | Old K → exact K | L_min | Old radii | Exact radii | Useful in original design? |
|---|---:|---:|---|---|---|
| 95% | 41 → 7 | 3 → 18 | 14.14529 / 16.61524 | 7.78445 / 9.14372 | No |
| 90% | 36 → 5 | 3 → 25 | 14.14529 / 16.61524 | 6.97706 / 8.19534 | No |

## Two proved refinements and their scope

1. **Exact-binomial MOM** retains the existing stable-target independent-block
   theorem. Two conditional von Bahr–Esseen steps give group p-moment
   constant A_p=4; fixed eta=1/8 retains C_p=32^(1/p). Independent bad-group
   indicators are dominated by independent Bernoulli(eta), even with unequal
   probabilities. Exact rational arithmetic selects the smallest feasible odd
   K with `m*Pr(Bin(K,1/8)>=ceil(K/2))<=alpha`. All blocks are retained and
   L_min>=2 is required. For m=16, alpha=.05: K=52→9, L_min=2→14 and family
   failure bound 166583/4194304=0.039716482162475586. The radius decreases by
   sqrt(7) at p=2 or 7^(1/3) at p=1.5. This is a sharper sufficient bound,
   not a new adaptive estimand or major novelty claim.
2. **Bounded graph Chebyshev** is a separate sample-mean theorem. Exact e and
   fixed bounded nuisance give unbiased DR scores with known row variance
   `v_u=h_u^2 sum_s q_u(s)^2/e_u(s)`. A sufficient graph with verified proper
   coloring gives `V=N^-2 sum_b chi_b sum_{u in b} v_u`. Independent blocks,
   conditional Chebyshev and a finite-family union bound give radius
   `sqrt(m V/alpha)`. The theorem permits heterogeneous block means under a
   legitimate exogenous design; the initial API intentionally keeps the
   original registered synthetic design. Merely predictable adaptive fits do
   not automatically satisfy this conditional model.

Full proofs are `theory/exact_binomial_mom.md` and
`theory/bounded_graph_variance.md`. The old method remains the default. No
empirical variance/tail estimate, oracle mean, tuned clipping cap, or
outcome-selected K enters a certified radius. Optional clipped-score bias
and variance are proved and enumerated in tests, but no clipped certified API
is exposed. Each method has its own familywise guarantee; inspecting all
methods and picking the most favorable interval does not inherit that level.
Nominality is per method and requested level; no joint guarantee across every
plotted procedure and confidence level is asserted.

## Algebra before outcomes

The independent `experiments/nonvacuity_budget.py` generated 200 design-only
rows, verified all 12 hand fixtures in the task, and produced
`theoretical_sample_need.png/.pdf`. It neither imports the certifier nor reads
outcomes/oracle truth. The inversion is a sufficient sample requirement for
this particular radius, not a minimax lower bound. With p near 1 it may be
astronomical even after exact K. Known subgroup mass, small denominators and
zero-support refusal are separate from width. These calculations preceded
the pilot; no p, eta, cell or method was selected using observed coverage.

## Pilot design and interpretation

Seven predeclared cells, 30 independent generated logs each, total 210.
Both levels and all four methods are paired on each log. B=128, fixed
mu_hat=(.5,.5), f=.25; m=1 with q=e=.5 at N=8192/32768; m=16 with eight
q values and all/group1 auditors at N=8192/32768; then chi=4, weak logging
e1=(.01,.02), and a p=1.5 envelope stress at N=32768. The latter still has
bounded Bernoulli rewards and known finite variance; it is not an
infinite-variance outcome experiment.

Oracle truth is the exact fixed-design conditional expectation
`N^-1 sum_u h_u[sum_s q_u(s) mu_u(s)-f]`, using synthetic response means
((.2,.6),(.35,.8)); it is joined only after all certificates are computed.
It is not the realized potential-outcome average. The frozen constraint is
M_D<=0.2*pi_h. Safe/unsafe/unresolved decisions concern this fixed window,
not pathwise deployment safety.

Raw and support-intersected endpoints are both saved. Full-range intervals
stay in coverage denominators; empty intersections cannot issue decisions.
The raw family coverage and issued-and-covers rate retain every replication;
coverage_given_issued is a descriptive conditional metric. Width fraction 1
means zero information. The family-any, family-all and marginal nontrivial
rates have distinct denominators. CI abstention and unresolved constraint
decisions are separately recorded. Wilson intervals use 30 independent logs,
not the number of policies, candidates, levels or methods.

## Verification and limitations

The original 243 tests remain unchanged; the final preregistration suite has
**377 passing tests**. The independent negative-control subset has 24 passing
tests. The only failing C0 test run was one wrong hand-entered expected fraction
in a budget fixture (1 failed/12 passed); it was corrected without changing
the implementation and the subsequent 13-test suite passed. The actual
diagnostic excerpt is retained in `gate_C0_budget_initial_failure.txt`.
No empirical-coverage threshold is a test assertion. Raw data summaries,
intervals/statuses and PNG/PDF plots reproduce byte-for-byte on repeated tiny
fixtures; execution timings are excluded from equality.

Both APIs reject declared shared shocks, false graphs, evaluation-trained
nuisance, future-conditioned design, moment violations and unadjusted
outcome-selected procedures. Actual zero-support and out-of-range reward
fixtures also refuse certification. See `gate_C0_negative_controls.md` for
precise statuses and test references. Hidden mislabeled stochastic violations
cannot all be detected from one observed log; schema acceptance is not proof
of independence or of graph sufficiency.

All 78 baseline paper/report/result/test/theory files were checked byte-for-byte
against d11a36f and remain unchanged (`baseline_preservation.json`). The only
modified existing implementation files are `comet/certification.py` and
`comet/robust_mean.py`; their default baseline outputs are regression-checked
against the saved original log. Full path inventory and executed commands are
`gate_C0_modified_files.txt` and `gate_C0_commands.md`.

Remaining gaps: arbitrary adaptive pathwise targets; dependence induced by
mutually trained cross-fitting; deriving uniform conditional envelopes from
unconditional moments under unbounded q/e; hidden cross-block dependence;
unknown/estimated tail scales; generic sparse-graph minimax sharpness; and
time-uniform deployment guarantees. The existing lower bound still applies
only to the proved clique-replication subclass. Future predictable-martingale
work and valid random-variance/bias/union accounting are scoped in
`gate_C0_theory_decision.md`; C0 does not start that theory project.

## Actual saved pilot results

The CPU command exited 0: 210 independent logs, 19,680 candidate-level records, 56 cell/level/method summaries, Python 3.12.2, two workers, 283.15 seconds wall time. All scientific code and config hashes match preregistration. No pilot run failed or was restarted. The only post-preregistration additions are results, audit and reports.

Each of the 56 summaries has 30/30 raw family coverage and 30/30 issued-family coverage, Wilson 95% [0.88649,1]. CI abstention is zero in these applicable cells. All records have CERTIFIED status under the registered model; support-only intervals are deterministic valid range bounds. These observations do not estimate final nominal coverage precisely. They are not pooled as 1,680 independent successes.

The table shows **median support-intersected width / feasible diameter**. Width 1 is vacuous; candidate nontriviality can be positive even when the median equals 1. Complete p90 widths, raw half-widths, errors, any/all/marginal nontriviality, abstention and unresolved decisions are in `pilot_summary.csv/json` and `pilot_table.md`.

| Cell | Level | Old MOM | Exact MOM | Graph Chebyshev | Support only |
|---|---:|---:|---:|---:|---:|
| iid_single_8192 | 95% | 1.00000 | 0.87287 | 0.09882 | 1.00000 |
| iid_single_8192 | 90% | 1.00000 | 0.87287 | 0.06988 | 1.00000 |
| iid_single_32768 | 95% | 1.00000 | 0.43644 | 0.04941 | 1.00000 |
| iid_single_32768 | 90% | 1.00000 | 0.43644 | 0.03494 | 1.00000 |
| iid_family16_8192 | 95% | 1.00000 | 1.00000 | 0.53745 | 1.00000 |
| iid_family16_8192 | 90% | 1.00000 | 1.00000 | 0.38031 | 1.00000 |
| iid_family16_32768 | 95% | 1.00000 | 0.91362 | 0.26892 | 1.00000 |
| iid_family16_32768 | 90% | 1.00000 | 0.88490 | 0.19015 | 1.00000 |
| clique4_family16_32768 | 95% | 1.00000 | 1.00000 | 0.53673 | 1.00000 |
| clique4_family16_32768 | 90% | 1.00000 | 1.00000 | 0.38031 | 1.00000 |
| weak_e_family16_32768 | 95% | 1.00000 | 1.00000 | 0.87175 | 1.00000 |
| weak_e_family16_32768 | 90% | 1.00000 | 1.00000 | 0.65004 | 1.00000 |
| finite_p15_family16_32768 | 95% | 1.00000 | 1.00000 | 0.26892 | 1.00000 |
| finite_p15_family16_32768 | 90% | 1.00000 | 1.00000 | 0.19015 | 1.00000 |

At 95%, the easy N=8192, m=1, q=e cell uses old K=30/L_min=4 versus exact K=3/L_min=42. The actual raw half-widths are 1.414214 → 0.436436, and 0.049411 for graph Chebyshev. At N=32768 these halve to 0.707107 → 0.218218 and 0.024705. Unlike the original p=1.5 smoke design, exact MOM is therefore strictly nontrivial in a predeclared easy setting.

| 95% cell | Exact MOM marginal nontrivial | Chebyshev marginal / all-family nontrivial | Chebyshev p90 width fraction | Chebyshev unresolved constraint fraction |
|---|---:|---|---:|---:|
| iid_single_8192 | 100.00% | 100.00% / 100.00% | 0.09882 | 100.00% |
| iid_single_32768 | 100.00% | 100.00% / 100.00% | 0.04941 | 0.00% |
| iid_family16_8192 | 0.00% | 100.00% / 100.00% | 0.72169 | 100.00% |
| iid_family16_32768 | 50.00% | 100.00% / 100.00% | 0.36084 | 51.04% |
| clique4_family16_32768 | 0.00% | 100.00% / 100.00% | 0.72169 | 100.00% |
| weak_e_family16_32768 | 10.62% | 63.12% / 0.00% | 1.00000 | 93.96% |
| finite_p15_family16_32768 | 0.00% | 100.00% / 100.00% | 0.36084 | 51.46% |

The original MOM baseline and support-only benchmark are full-range in all pilot cells. Exact MOM remains weak in the larger family, clique and low-p stress cells. Graph Chebyshev makes every candidate nontrivial in each moderate-overlap cell, including chi=4, but does not resolve every constraint. For weak e, at 95% only 63.125% of candidate intervals are nontrivial, no replication has every candidate nontrivial, and 93.96% of candidate constraint decisions remain unresolved. This limitation is retained in the table, not hidden by perfect observed coverage.

False-safe count is zero for every method/cell/level. This is a descriptive debug outcome for the predeclared threshold, not a deployment guarantee or a bound on long-run false-safe risk. `timings.csv` reports actual computation time by method/replication/level; `pilot.csv` includes absolute error, raw radius, K/L, graph size, q/e quantiles, empirical score-tail diagnostics and known scale sources. The empirical moments and ESS are diagnostic only. `data_summaries.json` records counts and SHA-256 for each generated log; `run_manifest.json` records all 210 seeds and frozen source/config hashes. No full raw-data dump is necessary to regenerate them from those inputs.

The comparison plot is `results/gate_C0/informativeness.png/.pdf`; it was visually inspected. Its sample/graph axis uses N/chi, not empirical importance ESS.

## Decision: PASS C0; GO for the scoped full Gate C campaign

**PASS / GO**: (i) both new bounds have explicit proofs; (ii) the predeclared easy scenario has strictly nontrivial exact-MOM and graph-variance intervals without truth selection; (iii) inapplicable declared controls refuse certification, with hidden-assumption limits disclosed; (iv) all 243 prior tests plus 134 new tests pass. This clears the C0 gate for a separately preregistered larger study of the established independent-exogenous-block model. It does not itself establish empirical 90%/95% coverage.

The next session may run the full Gate C campaign within that model, keeping the old baseline, exact MOM and bounded graph method separately labeled and reporting width, abstention and support failures alongside coverage. It should retain difficult weak-overlap/low-p cells, and keep truly unbounded/infinite-variance designs outside the bounded certificate unless a known valid envelope and applicable implementation are supplied.

**NO-GO for broader theorem claims** about fully adaptive logged-history paths, mutually trained cross-fit scores, estimated scales, arbitrary sparse-graph sharpness, or long-run deployment safety. Those require additional proofs, particularly the C1 martingale/explicit-bias program. No 1,000-replication campaign, external dataset download or C1 implementation began in this run.

## Runtime accounting

Total pilot wall time was 283.15 seconds with two CPU worker processes. The following medians are actual per-log/per-confidence-level certifier calls across the predeclared cells, not isolated complexity benchmarks. Different cells have different N and m.

| Method | Timed calls | Median seconds | Total measured call-seconds |
|---|---:|---:|---:|
| bounded_graph_chebyshev | 420 | 0.278003 | 78.694 |
| conservative_hoeffding | 420 | 0.528582 | 149.372 |
| exact_binomial | 420 | 0.539283 | 149.252 |
| trivial_support | not separately timed | not measured | included in total runner wall time |

Support-only construction has no independent timer in this frozen runner. Its exact mathematical width and status are recorded; no elapsed value is invented. Generation, diagnostics, support construction and export are included in total wall time. Summed call-seconds can exceed wall time because two workers run concurrently.

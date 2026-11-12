# C-PREFLIGHT phase report

**C-PREFLIGHT PASS; GO for the separately authorized C-STAT phase within the
frozen independent-exogenous-block model. No C-STAT job was started.**
This phase verifies a proof-to-code/data contract and a recoverable small
batch, not empirical 95% calibration or useful heavy-tail power.

The verified starting SHA is `3f8902d1033f3c4eece9a3746912ac9f1d8904ef`.
The reproducible code/proof/config/seed freeze, made before any primary
preflight outcomes, is **`ab4c74fbf1ae84c0e5ffd72d77ce5b48d3fba8cb`**.
The branch is `codex/gate-c-preflight`; final delivery/synchronization is
recorded in `gate_C_sync_status.md` and the final response. The actual batch
manifest records that code SHA and all source/config/seed hashes. Model code,
tests, proof and frozen settings stayed unchanged during and after the batch.

## Inspected evidence and reconciliation

The complete 6,747-token master, Chinese decision and initial prompt were read.
The A/B/C0 reports, all eight baseline test modules, proofs, implementation,
commands and failed-run logs were inspected. The independent reproducible audit
in `experiments/reconcile_gate_c_baseline.py` checked **879,955 invariants with
zero discrepancies**: 19,680 C0 interval rows, 210 draws, 56 family summaries,
70 displayed Markdown rows, all saved source/config hashes and all 152 baseline
files. Precise line references and numerical comparisons are in
`gate_C_evidence_inventory.md` and `preflight/c0_reconciliation.json`.

The reported C0 easy-setting radii 1.41421, .43644 and .04941 and width fractions
1, .87287 and .09882 agree with the actual artifacts. The m=16/N=32768 graph
width is .2689167149232915. Different quoted K values in the task history refer
to different family sizes/designs, not conflicting outputs. C0's p=1.5 cell
was bounded Bernoulli and cannot stand in for new heavy-tail F. Optional
clipping was proof-only; there was no clipped certified API, checkpoint resume,
memory measurement or separate support-only timer in C0. The new phase addresses
the relevant implementation gaps without rewriting those old observations.

## Frozen design and exact target

The six primary cells match the master's N/m/chi/overlap table. A has N=8192,
m=1, chi=1; B–F have N=32768,m=16. C/E/F use chi=4. D/E use exact design
e1=(.01,.02); B/C/F use (.4,.6), A uses (.5,.5). All have B=128, full complete
cliques, fixed bounded nuisance (.5,.5), f=.25 and stable block targets.
The family is eight distinct q values crossed with all/group1 auditors, with
known subgroup mass, rather than sixteen copied auditors.

F adds symmetric Pareto noise, a=1.75 and scale .1, to the conditional response
location. The ideal noise has zero mean, finite p=1.5 moment and infinite
variance. Its known conditional moment yields the proved centered DR envelope
in `theory/gate_c_heavy_tail_contract.md`. This is not a data-driven tail fit.
The finite-precision right-grid sampler is dominated by that moment integral;
no claim is made that a finite machine law literally has infinite variance.
Its observed rewards are not clipped to [0,1]. Actual F reward ranges were
[-120.30033,14.01311] and [-9.16364,51.42712]; respectively 4,136 and 4,036
retained rows lay outside [0,1] (including clique copies). These observations
check implementation only and do not prove tail properties.

The target is the legitimate fixed-design conditional finite-window moment
M_D=N^-1 sum h[sum q mu-f], analytically evaluated after every procedure at
both levels completes. It is not a population target, a realized-potential
average, a fully adaptive history target or long-run deployment performance.
Independent cluster randomness, replicated within known cliques, proves the
strong conditional dependency-graph property and block independence. Fixed
nuisance values require no fitted pilot; reserved pilot streams are explicitly
unused. All seven stream roles are separately allocated, with only logging and
potential outcomes active in this deterministic design.

Exact e means the known randomization law. Integer lotteries match each stored
dyadic e1; ordinary float complements/scores/radii retain the same numerical
theorem convention as C0. The largest weak-e complement representation error
is 1.734723475976807e-17, recorded before outcomes in
`numerical_probability_audit.json`. This is not estimated-propensity uncertainty
or a claim of bit-level outward-rounded computation. The protocol documents
that numerical limitation explicitly instead of silently changing cells.

The known conditional mean class [0,1] provides finite target bounds even in F.
Thus F's full-target-range benchmark and support intersection are valid from
that mean-class assumption; they do not assert bounded Y. Graph Chebyshev
remains NOT_APPLICABLE in F regardless of a realized sample's range.

## Completed and skipped work

**A–F: exactly two preflight logs each, twelve unique logs total**, at the full
declared N. All seven methods and both levels share each log. Output has 2,268
candidate records and 84 method/cell/level summaries, with 1,134 individual
candidate summaries. All 6,000 confirmatory seed entries are frozen and remain
unexecuted. Preflight and confirmatory namespaces are disjoint.

The user requested small integration jobs; the master's 50–100 preflight
example was treated as an example. Two per cell was explicitly preregistered
before outcomes, with no later reduction of R or selective omission. Symmetric
Pareto was chosen instead of the master's example Student t for an elementary
known-moment proof, also before outcomes. Fixed nuisance constants are the
permitted separation route; no independent fitted pilot is falsely reported.
These choices and the finite target-mean class for F are explicit in
`gate_C_preregistration.md`, not silent deviations.

C-STAT, secondary sensitivity, gap/power sweeps, discovery, policy repair,
optional Bernstein/adaptive theory, real datasets and manuscript edits are
deferred. No placeholder confirmatory/power/auditor/repair output is created.
The preflight's single frozen threshold tests decision bookkeeping only.

## Actual coverage, uncertainty and usefulness

At both nominal levels, all applicable certifier/target-range comparisons
observed **2/2 family coverage**, Wilson 95% **[.3423802275,1]**. The 17
predeclared primary 95% exact-binomial undercoverage p-values and Holm-adjusted
p-values are all 1. Such tiny samples provide almost no calibration evidence;
nonrejection is not validation of 95% coverage. The exact test and Holm family
are frozen for the later confirmatory analysis. Full-range intervals remain
in every applicable coverage denominator.

| Cell | 95% old MOM median width/diameter | Exact MOM | Graph Chebyshev | Graph marginal nontrivial | Graph no-certified-decision fraction |
|---|---:|---:|---:|---:|---:|
| A | 1 | .87287 | .09882 | 100% | 100% |
| B | 1 | .91327 | .26892 | 100% | 53.125% |
| C | 1 | 1 | .53783 | 100% | 100% |
| D | 1 | 1 | .88362 | 65.625% | 93.75% |
| E | 1 | 1 | 1 | 31.25% | 100% |
| F | 1 | 1 | NOT_APPLICABLE | NA | 100% (no interval) |

The target-range benchmark has width fraction 1 everywhere. Median width 1
does not imply every candidate is full-range: D exact MOM has 9.375% marginal
nontriviality, and E graph Chebyshev has 31.25%. The full tables preserve this
distinction. F's applicable MOM methods remain entirely vacuous and abstain.
That limits practical informativeness, but is not a theorem/status failure.

All false-safe and false-violation counts are zero in these twelve logs.
At the fixed .2*pi_h threshold, B graph Chebyshev detected 70% of truly
violating candidate instances at 95%; the other listed 95% certifier cells
detected none. These counts are debugging outcomes at one threshold, not
independent policy-level trials or evidence of power. Point-only methods issue
no certified decision; their coverage, widths and power are NA, not artificial
zeros or perfect success. F graph rows are retained as NOT_APPLICABLE, not
dropped from applicability denominators. See `gate_C_statistical_summary.md`
for both levels, Wilson/test statistics, IQR/p90 widths, power and abstention,
and the saved CSV for signed errors, RMSE, q/e and score-tail diagnostics.

## Checkpoint recovery and resources

The actual first invocation atomically saved `preflight/A/0000` and deliberately
raised `INTENTIONAL_CHECKPOINT_RESUME_TEST`. The next invocation skipped that
checkpoint and generated only the remaining eleven logs. Its checkpoint hash
before/after resume was identical:
`59e64d94a02cdf1c4ed8a65bd3d6869aeeb6c5e076a933bf3ac0fcd0356d6fb8`.
There are twelve RUN_COMPLETED events with twelve unique IDs and zero
confirmatory IDs. A third, direct idempotent resume exited 0, skipped all twelve
and generated zero outcomes. Failure JSON, tracebacks, events and completed
checkpoints are preserved. The evidence is in `checkpoint_resume_evidence.json`.

Execution used Python 3.12.2, macOS 27.2 arm64, Apple M1, eight reported CPUs,
one sequential CPU process, no GPU. The eleven-log resume took **52.2174 seconds
wall / 51.0667 CPU seconds**, including summary/export work. Peak process RSS
was **124,190,720 bytes = 118.44 MiB**. Summed per-log work across all twelve logs
was 51.8397 wall / 50.6983 CPU seconds; this excludes invocation-level startup
and aggregation and is a different denominator. Per-method timings include
all seven methods, including the full-range benchmark, and are family-call
costs repeated in candidate records rather than additive per-candidate costs.
RSS is a process cumulative high-water mark, not isolated per-method memory.

The external `/usr/bin/time -l` wrapper printed elapsed time but returned 1
because the sandbox denied `kern.clockrate` after Python completed. This
monitoring failure is preserved, not represented as a successful shell exit.
The process-internal `perf_counter`, `process_time` and `getrusage` measurements,
batch-completion event and successful direct resume establish actual execution.
CPU-brand inspection was initially sandbox-denied; the read-only escalated
query succeeded. No extra replication was run to repair monitoring.

## Tests, failure history and remaining boundary

All **377 baseline tests remain unchanged and pass**; **95 new deterministic
tests** bring the total to **472 passed in 5.70s**. Tests cover analytic target,
DR misspecification identity, exact exposure law, graph/coloring, known heavy
moment/domain, F's strict applicability, drift rejection for MOM, oracle import
separation, seed separation, exact binomial/Holm/Wilson calculations, abstention
and crash/resume. The deterministic empty-intersection fixture verifies that
a real coverage failure still receives its undercoverage p-value (.0025 for
0/2; Holm17 .0425), rather than disappearing as an unissued decision.

No pytest run failed. Two inventory path typos, the deliberate crash, and the
system monitoring errors are separately recorded in `gate_C_commands.md` and
`gate_C_logs/`. The deliberate crash is the only injected batch failure; no
scientific run was silently skipped or erased. A full source/config checksum
comparison verifies the code used in the batch against the preregistration;
the independent final audit passed 127,613 checks with zero failures and is
recorded with its source in `preflight/final_audit.json`.

There is no current in-scope blocker for C-STAT. A future launcher must consume
the frozen confirmatory seed lists without changing model/selection settings
using their outcomes, preserve incremental checkpoints, report all outcomes
and inspect the predeclared undercoverage diagnostics before downstream stages.
The present runner intentionally exposes only preflight execution. This GO
does not authorize real-data work or resolve adaptive histories, mutual
cross-fitting, unknown scales, hidden dependence, general sparse-graph
sharpness or long-run deployment safety. The Overleaf state remains
`df70f486fc08139057436e2781c212ad741ef646` with no paper edits.

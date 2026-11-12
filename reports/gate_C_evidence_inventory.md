# C-PREFLIGHT evidence inventory and C0 reconciliation

Audit anchor: **`3f8902d1033f3c4eece9a3746912ac9f1d8904ef`**. All existing-source
line references below use that commit. The entire supplied
`CODEX_COMET_GATE_C_MASTER.md` was read; its later C-STAT/C-DECISION/data phases
are roadmap instructions, not authorization to execute them in this C-PREFLIGHT
task. No evaluation outcomes were generated for this reconciliation.

The starting HEAD matched the requested SHA and the initial worktree was clean.
The baseline suite was rerun before implementation: **377 passed in 4.43s**
(`reports/gate_C_logs/baseline_pytest.txt`). The independent read-only audit
`experiments/reconcile_gate_c_baseline.py` completed **879,955 checks, zero
discrepancies**, preserving all **152** files tracked at the anchor commit.
Their paths and SHA-256 values, recomputed numerical summaries and audit limits
are saved in `results/gate_C/preflight/c0_reconciliation.json`.

## Actual proof and implementation evidence

| Obligation | Inspected source and exact scope |
|---|---|
| A/B restricted theorem | `reports/gate_A_report.md:25–36,53–73`; `reports/gate_B_report.md:9–23`; `theory/theorem_to_code_contract.md:23–67` establish an exogenous fixed-design target, independent macro-blocks, known sufficient clique graphs, fixed nuisances, exact e, frozen finite family and known conditional score moments. General adaptive/cross-fit claims remain open. |
| Conditional target / oracle | `comet/truth.py:16–27` averages conditional response means over the actual repeated context design; `comet/synthetic.py:15–41` returns the oracle separately. The target is `N^-1 sum h[sum q mu-f]`, not a realized potential-outcome average or a post-deployment target. C0 joins truth only after all intervals at `experiments/gate_c0_pilot.py:82–115`. |
| Exact randomization / graph | `comet/schema.py:44–78`; `comet/synthetic.py:17–40` use binary S=A and exact context-specific e, independent cluster records, and chi exact copies per clique. Thus nonadjacent disjoint score sets depend on disjoint random draws conditional on the exogenous design. `comet/conflict_graph.py:6–32` constructs and verifies proper coloring. Matching IDs or observed correlations alone would not prove this property. |
| Joint-slate exposure distinction | `comet/exposure.py:10–39` enumerates the complete ordered Plackett–Luce slate law and marginalizes exposure preimages. `tests/test_core.py:61–87` and `tests/test_bounded_variance.py:85–94` check exact probabilities. The C0 pilot itself is binary S=A; it is not a simulated joint-slate experiment. |
| Known conditional p envelope | `comet/dr_scores.py:40–52`; `theory/theorem_to_code_contract.md:106–133`; `comet/certification.py:143–147` use `nu^p=max_x 2^(2p-1)[1+sum q^p e^(1-p)]`. The scale depends on frozen q/e and the bounded reward/fit assumptions, not observed tails or oracle response means. |
| Original and exact MOM | `comet/certification.py:91–147`; `comet/robust_mean.py:22–36,58–147`. The original conservative K remains the default; the new switch uses minimal feasible odd K and exact rational binomial tails at eta=1/8. B>=2K, deterministic complete-block grouping and stable block targets are retained. `theory/exact_binomial_mom.md:20–118` supplies the two-stage moment bound A_p=4 and conditional independent-Bernoulli domination proof. |
| Bounded graph variance | `theory/bounded_graph_variance.md:20–138`; `comet/bounded_variance.py:16–156` prove and implement a separate raw-row sample-mean certificate using `v_u=h_u² sum q²/e`, graph coloring, independent-block variance additivity and radius `sqrt(mV/alpha)`. The theorem permits heterogeneous exogenous means, but C0's API still validates the narrower stable Bernoulli model. |
| Support and subgroup mass | `comet/informativeness.py:5–39` stores raw bounds separately from their known-support intersection; empty intersections do not authorize decisions. `comet/certification.py:196–205` uses exact design subgroup mass; zero mass refuses a ratio bound. |
| Status / nuisance separation | `comet/certification.py:18–49` enforces exact e, frozen family/reference/nuisance, pre-action fields, Bernoulli outcomes and clique replication. Unsupported models return `UNVERIFIED_ASSUMPTION`, numerical/design failures return `NOT_CERTIFIABLE`. These are declared-model guards, not automatic detectors of hidden dependence or nuisance training provenance. |
| Conditional probability budget | `comet/robust_mean.py:10–19`; `theory/theorem_to_code_contract.md:135–157` keep coupling failure as probability debit, separate from bias/drift radii. All three extras are zero in the registered model. Coverage is per method, family, level and fixed window—not simultaneous over post-hoc method or window selection. |
| C0's actual procedures | `experiments/gate_c0_pilot.py:82–107` compares conservative MOM, exact-binomial MOM, bounded graph Chebyshev, and a deterministic full feasible-range benchmark. There is **no** clipped certified API, adaptive/mutual-cross-fit mode, learned nuisance pilot, estimated-nu certificate, genuine heavy-tail simulator, discovery or repair experiment. |
| Optional clipping | `theory/bounded_graph_variance.md:149–185` proves its bias/variance formulas; `tests/test_bounded_variance.py:97–114` enumerates the identity. This is proof-only, not an implemented C0 method. |

## All persisted C0 numbers reconciled

The audit parses every row in `results/gate_C0/pilot.csv:2–19681` and every row
of the 56-row `pilot_summary.json`. It independently recomputes analytic truth,
known scales, K/L, exact binomial budget, raw radius/endpoints, support
intersection, coverage/issuance, nontriviality, decisions, absolute errors and
the full summary. Persisted observed count tables additionally reconstruct
sample-mean estimates, importance/score quantiles, empirical score moments and
ESS; these diagnostics are never inputs to the certifier. No sampling or
oracle-based tuning occurs during the audit.

All **19,680** candidate records correspond to **210** distinct cell/replication
seeds, **7 cells × 30 logs**, paired across two levels and four methods. Every
family is complete. The 17 recorded source hashes and the config hash
`32ff81d41b1bf008d62ade8a02ecc0a2625df0ba4ae796ed1ae7ddff30b7a98a` agree with
both the preregistration source commit and current preserved files. The run's
`15af1842dff7dddf89bbad1c98e8b3ac7a8de3b0` SHA is the preregistered ancestor
of the result commit `f2b4e4c70d5837296e73709cf3ac547c6f46f116` and delivery
commit `3f8902d...`; these are different provenance roles, not divergent code.

All 56 summaries have **30/30** raw and issued-family coverage and Wilson 95%
interval **[0.8864866068260314,1]**. All 14 width-table rows in
`reports/gate_C0_report.md:153–168`, all 56 displayed rows in
`results/gate_C0/pilot_table.md:7–62`, and all three timed-method rows at
`reports/gate_C0_report.md:200–205` match the CSV-derived values and their stated
display precision. This reconciliation finds no numerical discrepancy or
excluded failure; it does not convert 30 trials into confirmatory evidence.

| Verified 95% easy-cell quantity | Original MOM | Exact MOM | Graph Chebyshev |
|---|---:|---:|---:|
| N=8192, m=1: K / L_min | 30 / 4 | 3 / 42 | not used |
| Raw half-width | 1.4142135623730951 | 0.4364357804719848 | 0.04941058844013093 |
| Median width / feasible diameter | 1 | 0.8728715609439696 | 0.09882117688026185 |

For m=16, N=32768, chi=1 at 95%, graph Chebyshev's median width fraction is
0.2689167149232915 (26.89% after rounding). Its entire family is nontrivial in
every replicate, yet 51.04% of candidate constraint decisions are unresolved.
The C0 original-MOM and support-only baselines comprise **9,840** full-range
records; their 100% coverage conveys no width improvement. Weak-e graph
Chebyshev has only 63.125% marginal nontriviality, zero all-family nontriviality,
and about 93.96% unresolved constraint decisions at 95%. These are retained in
the existing report (`gate_C0_report.md:172–184`).

The audit cannot recover MOM point estimates or row-order hashes from aggregate
counts alone; it checks their saved intervals/radii, paired digest consistency,
and exact source/config provenance. Re-running the frozen generator with its
saved seed would recover those sequences, but no such extra outcomes are needed
or generated in this phase's reconciliation.

## Differences that matter for C-PREFLIGHT

1. **Three K comparisons describe different designs.** The old smoke m=4,
   p=1.5 has K41→7 and radii 14.145/16.615→7.784/9.144 at 95%; C0's easy
   m=1,p=2 cell has K30→3; the m=16 fixture has K52→9. These figures are
   consistent and must not be interchanged (`gate_C0_report.md:31–50,170`).
2. **C0's p=1.5 cell was bounded Bernoulli.** It exercised a weaker moment
   order, not unbounded rewards or infinite variance (`gate_C0_report.md:85–91`).
   Gate C primary F therefore needs a new declared DGP, known conditional
   envelope and strict `NOT_APPLICABLE` label for bounded graph variance.
3. **A useful interval is not a resolved constraint.** CI abstention was zero
   throughout C0; unresolved constraint fractions can be near 100%. The two
   columns have different events and denominators. Full-range intervals remain
   in coverage, and selection among methods was not certified.
4. **Resources were only partly measured.** C0 wall time was
   283.14724458398996 seconds with two workers. Each of three statistical
   methods has 420 recorded call times, but support-only construction has no
   separate timer and no peak-memory value was recorded. Neither missing
   quantity can be inferred retrospectively (`gate_C0_report.md:196–207`).
5. **Resume and stream separation are new obligations.** C0 writes artifacts
   after all cells complete (`experiments/gate_c0_pilot.py:225–249`) and lacks
   incremental checkpoint/retry support. Its generator uses two active streams
   (`comet/synthetic.py:10–17`); contexts/graph/nuisance are deterministic. Gate C
   needs the newly declared stream/manifest contract rather than claiming C0
   already had it.
6. **m=16 means eight distinct policies × two auditors.** The all/group1
   auditors are not 16 duplicated definitions. C0's synthetic effects and true
   moments vary with q; subgroup mass is fixed at 1 or 1/2. A more elaborate
   discovery library belongs to its separately authorized phase.

## Inspected tests and retained failure history

All eight baseline test modules were read. Core DR/support/slate/graph/budget
and schema tests are in `tests/test_core.py:17–282`; oracle isolation/Wilson and
reproducibility are in `tests/test_isolation_and_smoke.py:16–79`; exact
counterexamples and the corrected clique-subclass Le Cam bound are in
`tests/test_mathematical_audit.py:8–138`. C0's additional modules are
`test_exact_binomial_mom.py` (tail thresholds, tiny delta, feasibility,
leftovers and domination), `test_bounded_variance.py` (variance, graph, support,
clipped-bias identity and status guards), `test_c0_integration.py` (saved baseline
regression and no new tuning inputs), `test_c0_pilot.py` (scientific-output and
plot reproducibility/no-issuance), and `test_nonvacuity_budget.py` (12 hand
fixtures and independent design-only inversion). The actual baseline rerun
passes all 377 tests; no existing test was modified for this audit.

The original editable-install CLI failure is retained at
`reports/smoke_initial_failure.txt:1–5`, explained at
`reports/gate_B_report.md:79–85`. C0's wrong expected fraction caused one test
failure, then was corrected to 166583/4194304; its preserved diagnostic is an
explicit reconstructed excerpt (`reports/gate_C0_budget_initial_failure.txt`),
not a claimed full raw log. Other recorded audit/monitoring mistakes and their
resolution remain in `reports/gate_C0_commands.md:109–120`. The historical
command files, logs and all prior artifacts were byte-checked against the
anchor commit. This new reconciliation command exited 0 with no failures.

The existing Overleaf state remains
`df70f486fc08139057436e2781c212ad741ef646` as recorded in the preserved sync
reports. Local paper files are byte-identical to the anchor. This audit makes
no new remote-write or compilation claim. The proof gaps listed in
`reports/gate_A_report.md:53–70` and `reports/gate_C0_report.md:136–143` remain
open: arbitrary adaptive histories, mutual-cross-fit dependence, conditional
envelopes from unconditional moments, unknown scales/coupling, general sparse
graph sharpness and long-term deployment safety.

Reproduction: `.venv/bin/python -m experiments.reconcile_gate_c_baseline`.

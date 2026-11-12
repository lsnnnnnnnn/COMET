# COMET — Gate C: Confirmatory Synthetic Experiments, Auditing Power, and Pessimistic Repair

## Authority and starting state

You are continuing a completed Gate A+B+C0 project. DO NOT rebuild the project from scratch. The owner reports:
- Experiment repository: `lsnnnnnnnn/COMET` at `3f8902d1033f3c4eece9a3746912ac9f1d8904ef`.
- Paper repository: `lsnnnnnnnn/COMET_overleaf` at `df70f486fc08139057436e2781c212ad741ef646` (not updated during C0).
- 377 tests passed; C0 210 CPU replications; 30/30 simultaneous coverage in the reported pilot is not confirmatory evidence.
- In the 95% C0 pilot: N=8192,m=1, original MOM radius 1.41421 and 100% feasible-range width; exact-binomial MOM radius 0.43644 and 87.29% width; bounded graph Chebyshev radius 0.04941 and 9.88% width. With m=16,N=32768, the graph variance median width was 26.89%.
- Proved scope ONLY: independent exogenous evaluation macro-blocks, conditional dependency graph under the declared assumptions, exact logged exposure propensities, bounded-outcome graph-variance certificate; finite-p MOM under its actual stronger moment and stable-target conditions. Arbitrary adaptive histories, mutually trained cross-fit, estimated nuisance scale/drift, general graph minimax sharpness, and long-term deployment safety remain unproved.

Treat the numbers above as user-reported until you have read and verified the actual files. Read `reports/gate_A_report.md`, `reports/gate_B_report.md`, `reports/gate_C0_report.md`, `results/gate_C0/pilot.csv`, `results/gate_C0/pilot_table.md`, the exact binomial MOM proof, graph variance proof, 377 tests, commands and failed-run logs. Cite actual file/line locations in a short evidence inventory. If files are missing or the SHA does not match, stop and report; do not fabricate verification. Create a fresh feature branch from the verified starting SHA. Preserve previous reports, tests, and failed-run logs. Do not modify the Overleaf paper until the empirical report and claim audit have been reviewed; provide proposed TeX patches separately.

## Goal

Produce a defensible, preregistered, reproducible **Gate C empirical package** that answers four questions independently:
1. Are the *proved* simultaneous confidence intervals well-calibrated across genuinely independent replications, and where do their assumptions break?
2. In which combinations of family size, dependence, overlap and tail severity are they informative and powerful enough to certify a violation or a safe policy?
3. Does a discover-then-freeze-then-certify workflow identify real hidden subgroup violations without false confirmation under the null?
4. Does pessimistic constrained policy selection improve the **true certified-window utility--violation--abstention tradeoff** compared with point-estimate selection?

Do not silently convert any result into a claim about general adaptive feedback or long-term safety. Evidence from 1,000 runs is not a proof of nominal coverage; proof and simulation play different roles. For each method produce an explicit assumption/status label.

## C.0 — Mandatory start and reproducibility contract

1. Inspect the existing code/data contract and list exactly which certified procedures C0 actually implemented. Do not assume that the optional clipped certificate was implemented. Reuse the established CLI, config schema, artifact paths, test infrastructure and graph generator where possible.
2. Capture `git rev-parse HEAD`, `git status --porcelain`, exact dependencies, Python version, OS/CPU, config hashes, seed algorithm/version, entry-point commands and source file checksums. Verify all 377 previously passing tests first. If any new baseline changes tests, document each intentional difference.
3. Build a `reports/gate_C_preregistration.md` and frozen machine-readable manifest before confirmatory outcomes are generated. Specify all primary cells, primary confidence level, methods, truth definitions, stopping rules, sample sizes, policy/auditor family composition, all seeds, all comparisons and all metrics.
4. Create a private (in-code) true-target evaluator that obtains the target from the known potential-outcome DGP or exact integration over exposures. The oracle may be used ONLY in final evaluation metrics and tests, never in estimator inputs, tail-scale estimation, method selection, tuning, discovery selection, or feasibility decisions.
5. Set a separate seed stream for the exogenous design/context, graph/shocks, logging/exposure draw, potential outcomes, nuisance/discovery pilot, evaluation outcomes, and independent truth Monte Carlo if analytic truth is impossible. The default should be analytic truth; if MC truth is used, report its standard error and ensure it is negligible relative to the smallest interval tested.
6. Use a unique run_id for each `(cell, replication)` and checkpoint results incrementally. A resumed run must not repeat completed rows or change their data. Log crashes and retries without silently removing failure cases.
7. Never compare methods on different random replications if paired comparisons are feasible. 90% and 95% intervals use the SAME logged replicate, not twice the simulated-data cost.

### Exact estimand and model conditions

For the certified exogenous-design experiment, define the conditional finite-window target explicitly, e.g.

`M_D(q,h;f) = N^{-1} * sum_u h_u * [sum_s q_u(s)*mu_u(s) - f_u]`

with all design variables in D fixed legitimately before evaluation actions/outcomes. Check equivalence to the implemented estimand, and document if `h`, `q`, or `f` vary by u. Do not unintentionally evaluate a population-average or a post-deployment target while displaying coverage for a fixed-design/window target.

The DGP must satisfy the stronger **conditional dependency-graph** property: nonadjacent disjoint sets' score variables are independent conditional on the declared design. Merely constructing edges for repeated user IDs or observed graph neighbors does not prove this. Use truly independent clique-specific latent shocks and independent macro-blocks in certified graph scenarios. Ensure each reported coloring is a valid proper coloring. Verify exact exposure propensity `e_u(s)` including any joint slate/exposure mapping and support implication `q>0 => e>0`. With bounded-Y variance certificates require Y(s) and frozen nuisance predictions in [0,1]. Distinguish the finite-p MOM's stable block target assumptions from the graph-mean method's potentially heterogeneous exogenous block means.

## C.1 — Mechanism-separated synthetic simulator

Implement or validate four orthogonal switches, keeping one fixed baseline DGP for interpretable one-factor comparisons:
- **Overlap**: strong (e comfortably positive), graded weak (e small for some supported actions, with recorded exact e), and deliberately zero-support negative control (abstain). Do not label positivity failure as weak overlap.
- **Dependence**: chi=1 independent; chi in {2,4,8,16} formed by exactly independent replicated cliques (theorem-matching); optionally a genuine sparse dependency-graph simulator with proven conditional independence outside neighborhoods. A graph constructed only from observed edges without a valid DGP is exploratory.
- **Outcome tails**: bounded Bernoulli / bounded continuous with frozen mu_hat in [0,1]; finite-p heavy tail (e.g., t distribution with df>p and known conservative conditional p-moment envelope), under which bounded-Y certificates are `NOT_APPLICABLE`; invalid infinite-p-moment control is assumption violation, not a certified case.
- **Target drift**: stable mean per block for MOM, and exogenous nonidentical block means for the graph mean certificate. The latter must not be used to make an unsupported stable-target MOM claim.

Include a real causal signal (known potential outcomes under the exposure state) and genuine multiple q/h candidates. Avoid 16 duplicated or near-identical auditors just to set m=16. Record subgroup support and true moment magnitude by candidate.

### PRIMARY confirmatory cells (1000 independent replications each)

Use existing C0 N/B/n0 choices when compatible with the proof. Start with the table below; adjust only during preregistration if implementation reveals a theorem/size inconsistency. Do not revise cells after looking at confirmatory coverage without marking a separately versioned exploratory analysis.

| Cell | N | m=|Theta| | Graph | e | Y | Applicable certificates |
|---|---:|---:|---|---|---|---|
| A: easy positive control | 8192 | 1 | chi=1 | strong | bounded | original MOM, exact-binomial MOM, graph Chebyshev |
| B: multiple auditing | 32768 | 16 | chi=1 | strong | bounded | all three |
| C: dependent audits | 32768 | 16 | chi=4 clique | strong | bounded | all three |
| D: weak support | 32768 | 16 | chi=1 | graded weak | bounded | applicable bounded and finite-p methods with valid recorded moments |
| E: two simultaneous difficulties | 32768 | 16 | chi=4 clique | graded weak | bounded | as in D |
| F: genuine heavy tail | 32768 | 16 | chi=4 clique | strong | p=1.5 finite moment, unbounded Y | finite-p MOM ONLY; bounded variance `NOT_APPLICABLE` |

For weak e choices, predeclare the q/e spectrum and verify it on design-only diagnostics; ensure the DGP satisfies the actual **conditional** moment envelopes used by MOM. Do not replace a valid moment envelope by an unconditional empirical tail moment. If no usable envelope is known, mark MOM not certifiable for that cell. The graph variance method may still be valid because its variance bound is conditional on the exact realized e and bounded Y.

Before the large confirmatory runs, execute a low-cost integration preflight (e.g., 50–100 runs per cell) for runtime/memory/CSV consistency and analytic fixtures. Keep preflight results disjoint from the frozen 1000-replication confirmatory seed lists and report them separately. Once preflight succeeds, run these six cells using CPU batch jobs with deterministic checkpointing. Do not start downloads or GPU training.

### SECONDARY sensitivity cells (200–300 replications per selected cell)

Do NOT take a full Cartesian product. Run one factor at a time around anchor B or C:
- N in {8192,16384,32768,65536} with chi and m held fixed.
- chi in {1,2,4,8,16} at fixed N and m; include a repeated-clique thought experiment in which raw N increases but the independent-clique count does not.
- m in {1,4,16,64} with policy/auditor family genuinely enlarged, and quantify the multiplicity cost.
- overlap severity with quantiles of `q/e`, including an extreme but positive scenario and one explicit support violation.
- p in {1.2,1.5,1.8,2.0} only in DGPs with **known valid** p-moment constants; record when finite-p confidence radii exceed the feasible range.
- heterogeneous exogenous block means for graph-mean method; stable-target restriction for MOM; outcome model deliberately misspecified but fitted on legal independent pilot data.

Use a small predeclared list of ~12–20 secondary cells, not thousands of grid cells. State computational budgets and actual total replications in the report.

### Methods and theorem status

- `orig_mom`: proved conservative finite-p MOM, when assumptions match.
- `exact_binomial_mom`: C0 improved finite-p MOM, when assumptions match.
- `bounded_graph_chebyshev`: C0 independent-block bounded-Y exact-e theorem, when assumptions match.
- `bounded_clipped_graph_chebyshev`: ONLY if proved in C0, including explicit clipping bias budget; otherwise skip and document.
- `ips`, `dm`, `dr`: point baselines; show bias, RMSE and raw sample variability, but do not invent 95% certificates.
- `iid_normal_dr`, `naive_block_bootstrap`, `iid_mom`, and `graph_blind_interval`: optional diagnostic/heuristic intervals with conspicuous `HEURISTIC_CI` / `INVALID_UNDER_DEPENDENCE` labels when relevant. They are not evidence of proven superiority.
- `full_feasible_range`: vacuous trivial interval for calibration reference.

Each row stores the estimator, true target, signed error, raw lower/upper/radius, support-clipped lower/upper, feasible diameter, width fraction, coverage, `status`, `assumptions`, reason for abstention and resources. Keep `raw` vs `clipped` diagnostics; do not turn clamping into an illusion of a sharper stochastic radius.

### Statistical reporting

Primary endpoint: familywise 95% coverage (all eligible theta in the frozen family simultaneously), with 90% secondary. Report numerator/denominator, Wilson intervals, and individual auditor coverage. To flag demonstrable undercoverage, preregister a one-sided exact-binomial test of H0: actual coverage >= nominal for each primary cell and apply Holm correction across declared confirmatory comparisons; report both unadjusted and adjusted p-values. A nonsignificant p-value **does not prove** nominal coverage; the theorem carries validity.

Also show median, IQR and p90 width/feasible diameter, non-vacuous fraction, median |error|/raw_radius, abstention, inferred support problems, q/e quantiles, chi, N_eff, B, K, K feasibility, p, true vs declared scale, method applicability, runtime and failures. Do not drop `NOT_APPLICABLE` rows from applicability denominators or silently count abstentions as successful narrow intervals. Conditional coverage among issued intervals is a separate diagnostic from the unconditional certificate event.

Output clean CSV/Parquet plus human-readable Markdown, and a minimum of:
1. Coverage-vs-width (both axes, 95%) by method/cell with Wilson error bars.
2. Width, non-vacuity and abstention vs overlap severity and chi.
3. Log-log absolute error and width vs N_eff (with separate rate guide), clearly distinguishing empirical slopes from theorem bounds.
4. Family size m vs CI width/power; invalid naive baselines explicitly marked.
5. Heavy-tail p sensitivity, including negative/inapplicable regions rather than only success cases.

## C.2 — Decision usefulness: false-safe, false-violation and power

Coverage is not enough. Define a fixed policy/auditor cost constraint `C_j(q) <= alpha_j` and use the simultaneous interval:
- `CERTIFIED_SAFE` iff `upper_C_j <= alpha_j` for every relevant j;
- `CERTIFIED_VIOLATION` iff `lower_C_j > alpha_j` for the tested inequality;
- `ABSTAIN` otherwise.

For ratio constraints, if the denominator is **known from frozen exogenous contexts**, use it exactly and record that choice; if it is a genuinely unknown population mass, require a joint certified lower bound. Never divide by an unsupported near-zero estimate.

Run null (all constraints satisfied, including near-boundary) and alternatives (true violations). Predeclare true signed gaps relative to feasible diameter, e.g. 0, +/-0.025, +/-0.05, +/-0.10, +/-0.20; also include one or two standardized gaps based only on pre-outcome theoretical radius. Measure:
- true safe / true violating / borderline counts;
- fraction certified safe, certified violation and abstained;
- **false-safe certification** when `true C>alpha` but method says safe;
- **false-violation certification** when `true C<=alpha` but method says violation;
- power to certify a planted violation vs gap, m, chi, e and sample size.

The decision rule may be conservative and abstain extensively; this is a substantive negative result, not a bug. Explain the minimum gap necessary for usable power. Only produce claims under the correctly combined familywise probability budget.

## C.3 — Discover → freeze → certify hidden subgroup

Implement the original paper's intended four-way interaction example as a hidden violation, e.g.
`h*(X) = 1{G=1 AND degree>80th percentile AND new_user=1 AND regime=high}`.

Control subgroup prevalence using the generator (e.g., 2%, 5%, 10%, 20%) rather than accidentally making it effectively empty. Ensure the planted effect changes actual *potential-outcome conditional means* and has an exactly computable true moment. Define q/h before outcome generation where required. Discovery must see only its disjoint independent pilot/discovery blocks, and certification must use untouched independent exogenous macroblocks. Any learned auditor selected using evaluation outcomes is an invalid negative control.

Freeze Top-L discovered auditor definitions (L in {1,5,10}), hyperparameters, selection rule and constraints before issuing a single certification interval. Pay the simultaneous family size for the frozen L candidates and all tested q/constraints. Never report the selected best among multiple post-hoc CI methods as certified unless the selection is design-only or appropriately multiplicity-adjusted.

Compare:
- fixed coarse auditors,
- in-sample discovered (explicitly invalid/optimistic reference),
- split discovered but dependence-unaware heuristic,
- COMET independent discovery + certified evaluation.

Run at least one true-null DGP, one planted-violation DGP and graded subgroup support/effect magnitude; target ~300–500 independent trials per core cell, with uncertainty intervals. Metrics: recovered subgroup similarity/precision, rate the true planted subgroup is among Top-L, `P(certified violation)`, `P(any false certified violation)` under null, abstention, effect-size power, split efficiency, and compute cost. Keep discovery FDR (if calculated) separate from final certified false-violation FWER.

## C.4 — Pessimistic policy repair

Create exogenously/pilot-frozen candidate policy libraries Q of sizes 8, 16, 32 with 2–4 predeclared constraints. Include a true-safe fallback policy when feasible and document when it is truly feasible yet not certifiably feasible. Candidate policies must induce explicitly known positive exact e support. The policy library may be learned on independent pilot data, never on evaluation outcomes unless validity is separately established.

Implement:
1. utility-only max empirical point estimate;
2. point-DR hard constraints (uncertified);
3. clipped or self-normalized DR point constraints (uncertified unless proved);
4. COMET pessimistic selection: maximize `L_V(q)` subject to `U_Cj(q)<=alpha_j` for all j;
5. hindsight oracle for evaluation metrics only (never a deployable baseline).

The whole family Q x {utility, costs} must be included in the simultaneous confidence budget; reuse the same correct evaluation event, no post-hoc select-the-narrowest interval. If the certified feasible set is empty, return `ABSTAIN_NO_CERTIFIED_POLICY`, not an arbitrary fallback labeled safe.

Report true short-window utility, true max constraint violation, false-safe policy-selection rate, abstention, fraction of candidates certified feasible, utility regret vs the oracle **truly feasible** library policy, and the stronger theorem-matched comparator with `C_j(q)+2r_j(q)<=alpha_j`. Do not claim a regret guarantee against every truly feasible near-boundary policy; the original comparator requires a robust margin. Include Pareto curves for constraint stringency and overlap. These results are **fixed-window/exogenous**; any closed-loop adaptive deployment simulator is exploratory and must appear separately, not as a certified conclusion.

## C.5 — Realistic graphs after synthetic acceptance

Only after C.1–C.4 pass, prepare a resource estimate and a separate proposal for TGB `tgbl-wiki-v2` semi-synthetic evaluation; do not download substantial datasets merely because the Gate C task exists. Preserve observed graph/time features while generating exact e and potential outcomes. Declare precisely which dependence structure is genuinely induced by the DGP; graph edges alone do not validate dependence assumptions. Analytical ground truth should be derived from generated potential means. This can yield a **semi-synthetic theorem-matching setting**, not a claim that real TGB data had recorded randomized propensities.

Open Bandit and KuaiRand should be a later protocol: exact logged propensity interpretation, on-policy reference uncertainty, dependence/identification and train-test leakage must be checked. If unproved block independence is assumed for real logs, label results descriptive or sensitivity, **not finite-sample certified**.

## C.6 — Optional independent theorem experiment, not a blocker

The 95% C0 bounded graph-variance width may still be too wide for small safety thresholds. In a separate `theory/` exploratory branch, consider a genuinely improved finite-sample bounded-reward certificate using independent macro-block sums and a Bernstein bound. Let block contributions W_b be conditionally independent centered increments, with deterministic conditional variance upper sum V and design-known |W_b|<=c. A candidate Bernstein inversion for fixed x=log(2m/delta) is

`r_B = c*x/3 + sqrt(2*V*x + (c*x/3)^2)`.

This is a proposal requiring a complete proof of block independence, variance bound and **design-measurable** c; c must account for worst-case importance-weighted residuals, not observed residuals alone. Validate the exact inequality and constants from an authoritative statement before adopting it. It may be worse than Chebyshev for very small e. A deterministic choice of certificate based ONLY on frozen exogenous design may retain conditional validity if proved; outcome-driven select-the-shorter is not automatically valid. Do not call this a new original theoretical contribution merely because it combines standard concentration inequalities. Keep this optional task separate from the preregistered main Gate C evaluation unless a wholly new freeze/version is written before confirmatory outcomes.

Separately, the high-value theoretical milestone remains an actual predictable-martingale certificate for adaptive histories. This is **T1**, not part of the independent-block Gate C truth claim. No implied long-term deployment guarantee.

## C.7 — Mandatory negative controls and failure cases

Include at minimum:
1. permanent latent shock shared across independent macro-blocks: violation of independence, mark `ASSUMPTION_VIOLATING`;
2. graph missing true shared-shock edges: invalid chi correction, label clearly;
3. propensity misspecified or q>0/e=0: decline exact-e certification;
4. nuisance fit on evaluation outcomes: decline certificate unless distinct proof;
5. true p-moment assumption violated: finite-p MOM is inapplicable;
6. select q/h/auditors or shortest interval from outcomes without independent split or simultaneous correction: decline post-selection certification;
7. stable-target MOM applied to drifting blocks without a proved drift term: not applicable;
8. giant q/e ratios where every certified interval is vacuous: report high abstention, not a validity failure.

A hidden assumption violation is not always discoverable from observations; negative controls should expose *scope*, not imply a perfect automatic validity detector. Set expected theorem-status guards separately from stochastic empirical coverage.

## C.8 — Code quality, provenance and tests

- Preserve previous tests and add deterministic unit tests for target oracle, DR identity under arbitrary frozen mu_hat with exact e, block graph construction and coloring, conditional variance finite bound, method status/positivity, family cardinality, score-range handling, counterfactual oracle not leaking to fits, independent rep seed streams, correct simultaneous Bonferroni accounting, exact binomial lower/upper diagnostic tests, Wilson CI, Holm adjustment, abstention and repair decisions.
- Integration tests should use tiny replicates and exact enumeration whenever possible; NEVER assert that stochastic coverage in 30 trials >=95%.
- Every numerical result must contain a schema version, run_id, git SHA, config hash, seed, model assumptions, method/proof name, status, point estimate, true target, raw interval, clipped interval, costs, family size and decision.
- Save checkpointed results and enough seeds to reproduce any outlier. Use resource-aware batching, no silent skipped failures, and no late post-hoc parameter changes in confirmatory sets.
- Do not massage, filter, subset, or clip away undercoverage; show negative findings and inapplicable baselines.

## C.9 — Deliverables and STOP/GO conditions

Produce at least:
- `reports/gate_C_preregistration.md`, `configs/gate_C_frozen.*`, `reports/gate_C_protocol_and_estimand.md`;
- `reports/gate_C_evidence_inventory.md` pinpointing the actual C0 proof/implementation scope;
- `results/gate_C/confirmatory_coverage.csv`, `results/gate_C/secondary_sensitivity.csv`, `results/gate_C/power.csv`, `results/gate_C/auditor.csv`, `results/gate_C/repair.csv` (as completed; no fake placeholders);
- `reports/gate_C_statistical_summary.md`, `reports/gate_C_power_and_abstention.md`, `reports/gate_C_auditor_and_repair.md`, `reports/gate_C_assumption_failures.md`;
- figures in `figures/gate_C/` with plotting source and all run manifests;
- `reports/gate_C_paper_patch_suggestions.tex` with *only verified* claims and exact scope, not a silent manuscript rewrite;
- `reports/gate_C_commands.md`, `reports/gate_C_modified_files.txt`, `reports/gate_C_report.md` including failed commands and exact verified commit SHAs.

**Phased signoffs (do not skip):**
- **C-PREFLIGHT PASS**: 377 baseline tests (or documented deliberate changes) + new deterministic tests, correct target/truth, positive support, correct statuses, preregistered manifest, successful CPU batch resume.
- **C-STAT PASS**: 1000 confirmatory reps completed for all preregistered primary cells; all outcomes reported even if very conservative; familywise 95% coverage analyzed with Wilson and predeclared undercoverage tests, and no code/theory mismatch. If a certificate shows significant undercoverage within the proved model, declare BLOCKED and investigate immediately before doing downstream decision experiments.
- **C-DECISION PASS**: null and planted-violation power/abstention, frozen auditor discovery+certification and policy repair all executed with independent splits and correct family budgets, with transparent positive/negative results. Do not force a positive-power outcome to earn PASS; if power/utility gains are absent, record a substantive research limitation and advise changes to the paper.
- **REAL-DATA GO**: requires the above plus an explicit dataset-specific causal design/assumption feasibility plan and resource approval; not automatically implied by C-STAT.

## Exact response format for Codex

At the end of each phase report (1) reproducible code commit SHA, (2) files and tests inspected, (3) completed/skipped cells and actual replication counts, (4) 95% family coverage with Wilson interval + appropriate exact one-sided undercoverage diagnostic, (5) median width/diameter, nonvacuity, power and abstention, (6) support/assumption violations or inapplicable comparisons, (7) failure log entries, (8) next phase PASS/BLOCKED/GO decision. Never claim a long-running future job is already done. If compute budget is exhausted, stop at the completed subphase, save artifacts, and report honestly rather than quietly reducing R.

# COMET NEXT CODEX MASTER — C-STAT + Separate Manuscript Rewrite Proposal

**Audit date:** 2026-11-12  
**Experiment repo:** `lsnnnnnnnn/COMET`  
**Evidence/result commit:** `06a39b89e579aef57d14ae51e86d74ecf9b6b768`  
**Frozen scientific code / preregistration commit:** `ab4c74fbf1ae84c0e5ffd72d77ce5b48d3fba8cb`  
**Frozen config:** `configs/gate_C_frozen.json`, `configs/gate_C_seed_manifest.json`  
**Scope:** C-STAT is GO for the *proved independent, exogenous evaluation-macro-block model with exact logging e, fixed nuisance and a known moment envelope*. No fully adaptive histories, mutually evaluation-trained cross-fitting, unknown moment scales, learned e, arbitrary graph/shock models, or future-trajectory safety claim.

## Objective and nonnegotiable scientific rules

1. First inspect the exact current commit and reports; do not assume the user's Mac path is accessible outside the Mac. Required: `reports/gate_C_report.md`, `gate_C_preregistration.md`, `gate_C_statistical_summary.md`, `gate_C_commands.md`, `theory/theorem_to_code_contract.md`, `theory/exact_binomial_mom.md`, `theory/bounded_graph_variance.md`, `theory/gate_c_heavy_tail_contract.md`, `theory/lower_bound.md`, `comet/gate_c_{contract,methods,simulation,statistics,truth,seeds}.py`, `experiments/gate_c_preflight.py`, `paper/sections/{02_setup,03_method,04_theory,05_discover_repair,06_experiments}.tex` and `paper/main.tex`. Record SHA-256, source tree, git status and current tests.
2. Never change frozen scientific assumptions, methods, randomization distributions, moment envelopes, candidate families, confidence levels, six-cell definitions, priors, outcome truths, scoring formulas, canonical seed list or preregistered analysis. The two C-PREFLIGHT logs per cell must remain outside confirmatory numerators and denominators. Do not edit old checksums, prior outputs or deliberately failed logs.
3. Treat one `(cell, replicate)` as one independent family coverage observation. The 16 candidate outcomes from the same log are correlated and cannot be counted as 16 independent replicates. Each family remains intact; all covered/status/issued counts must use predeclared denominators.
4. The certifier must never read ground-truth response locations, analytical target, or any oracle output; the evaluation layer obtains truth only after all methods and both confidence levels are finished for that log.
5. No data-dependent modification, intermediate result-based parameter tuning, selective subset report, outcome-based stopping, or selecting the shortest of separately certified methods as if jointly 95%. Interruption for infrastructure is allowed, with strict immutable checkpoints and complete accounting.
6. Keep method eligibility: `orig_mom`, `exact_binomial_mom`, `bounded_graph_chebyshev` each has its **own** 90%/95% within-method family guarantee. `bounded_graph_chebyshev` for F is `NOT_APPLICABLE`, `ips/dm/dr` are `POINT_ONLY`, and `full_feasible_range` is a deterministic support benchmark. Preserve these rows and never fabricate CIs.
7. A green pytest suite is not evidence of novel theory, exact finite-precision confidence or empirically validated coverage. Theorems depend on actual conditional stochastic assumptions, not simply matching a metadata tag.

## Part 1. C-STAT: new confirmatory-only execution entry point

**Problem:** Existing `experiments/gate_c_preflight.py` explicitly authorizes only preflight. Existing frozen JSON also contains `phase_authorized: "preflight"` and `stopping_rule` for 12 integration logs. Do not bypass this by renaming the phase or toggling the old freeze. Create a new, clearly scoped `experiments/gate_c_confirmatory.py`, distinct result schema and output directory (`results/gate_C/confirmatory/`). Reuse the exact frozen scientific simulator/estimators/statistics with unmodified code. This is a *new-phase launcher*, not a modification of the frozen scientific protocol. Validate that all 6,000 planned IDs come from `phase="confirmatory"` in the **existing** hashed seed manifest. The launcher must require explicit `--confirmatory` and fail without it. Include the manifest/config hashes and exact science-source hashes (from the freeze) in the run metadata.

Preflight's current `source_checksums()` uses broad `glob("*.py")`, which will include a newly added runner and produce a changed fingerprint. Design a forward-compatible strict science-source allowlist or equivalent immutable source digest **without modifying preflight's existing manifests or checkpoints**. Demonstrate bytewise scientific outputs on previously frozen 12 preflight seeds when obtained with the new shared evaluation routine, ignoring only phase/runner provenance; perform this integration check before drawing confirmatory data. Do not quietly claim a changed code tree is byte-identical. If a true science bug or proven theorem mismatch is found, stop with `BLOCKED`; document the defect and a proposed new preregistration rather than reusing the old confirmation label after a code change.

The confirmatory runner should:
- Validate all seeds, cells, family definitions, known e and p domain, input SHA-256, declared graph and nuisance conditions, and theorem status before generation.
- Generate *exactly* 1,000 independent logs in each frozen cell A–F (6,000 logs total) with the existing manifest; the two levels (alpha=0.05 and 0.10) and all seven methods use the same generated log within a replication.
- Save each completed run atomically and cryptographically with fingerprint, canonical input digest, run ID, complete candidate statuses/intervals and metrics; reject changed/corrupt checkpoints.
- Resume only incomplete run IDs. Log intentional vs actual errors separately, never turn crashed runs into missing observations and never drop them from final denominator.
- Stream and aggregate rather than deserialize the entire corpus into memory at the end. Expected output is **1,134,000 candidate-level records**: A = 1000*1*7*2 = 14,000 and B–F = 5*1000*16*7*2 = 1,120,000. Use partitioned compressed CSV/JSONL/Parquet if available and consider a bounded-memory streaming summary, with exact cross-checks on the small preflight fixture. Do not add heavy runtime dependencies unless demonstrably necessary and lock them if introduced.
- Save `run_manifest`, `source_and_environment`, `timings`, `failures`, `run_checkpoints`, complete raw-metric columns and `summary.md/.csv/.json`. Provide CPU/wall and RSS per invocation, not guessed standalone per-method memory.
- Before the full launch, run only deterministic no-outcome checks, unit tests and preflight-seed fixtures; do NOT consume any of the 6,000 confirmatory IDs as an exploratory tuning budget. After explicit readiness inspection, perform the already authorized 6,000 runs. Preserve all material even if the findings are disappointing.

### Frozen cells

| Cell | N | chi | e1 by context | family | Y law | theorem eligibility |
|---|---:|---:|---|---|---|---|
| A | 8192 | 1 | (.5,.5) | 1 q/h | Bernoulli | MOM/exact/graph |
| B | 32768 | 1 | (.4,.6) | 8 q x 2 h = 16 | Bernoulli | MOM/exact/graph |
| C | 32768 | 4 | (.4,.6) | 16 | Bernoulli | MOM/exact/graph |
| D | 32768 | 1 | (.01,.02) | 16 | Bernoulli | MOM/exact/graph |
| E | 32768 | 4 | (.01,.02) | 16 | Bernoulli | MOM/exact/graph |
| F | 32768 | 4 | (.4,.6) | 16 | symmetric Pareto alpha=1.75, sigma=.1, p=1.5 | MOM/exact only |

All have 128 independent exogenous blocks, complete replicated cliques, frozen mu_hat=(.5,.5), reference f=.25, exact e, conditional analytic fixed-window oracle, and seed manifest master 2026111203. This table explains the frozen JSON, but the files — not this human text — are authoritative. Never silently change values after observing results.

### Confirmatory endpoints and statistics

**Primary:** within-cell, within-method 95% *familywise* simultaneous coverage, where `covered_family` means every eligible candidate CI covers the exact analytic `M_D`. For each 17 predefined cell-method 95% comparison, report successes/1000, observed family rate, Wilson 95% descriptive CI, exact lower-tail p under H0 P(coverage)>=.95, and Holm adjusted p across exactly the registered 17 tests. Rejection is a diagnostic of undercoverage; **nonrejection does not prove 95% validity**. Count full-range intervals as covered when appropriate. A null or impossible confidence intersection must count as a coverage failure, never disappear under a non-issued decision.

**Secondary:** 90% analog with no inflated claims of 17+17-family corrected inference; marginal coverage per candidate; raw and support-intersected width/feasible diameter (median/IQR/P90); family `some` vs `all` nontriviality; estimated error/radius ratios; exact e and q/e diagnostics; chi and N_eff=N/chi; applicability and reason; safe/violation/abstain counts; true violation detection and false-safe/false-violation at threshold `0.2*pi_h`; runtime and memory. Report candidate-level metrics separately from independent replication-level uncertainty. Never call B's candidate-level ~70% detection from 2 logs a formal 70% power estimate.

**Prescribed plots:** (1) coverage vs nominal with Wilson uncertainty for each eligible method/cell; (2) width distribution and `full_feasible_range`; (3) nontriviality/abstention heatmap by cell and method; (4) error-to-radius diagnostic; (5) resource cost. Show unfavorable F and E results transparently. No log-log minimax slope claim from a fixed Pareto DGP.

**Phase completion:** `C-STAT PASS` is allowed only if all 6,000 assigned logs have a validated complete checkpoint and honest report; all registered statuses and denominators are consistent; no new theorem/model mismatch was found; results are reproduced from checksums and independent aggregation; no preregistered protocol has been rewritten based on outcomes. A statistically unfavorable result is a scientific finding, not automatically an implementation failure. If coverage is unexpectedly below nominal, investigate in a *separate* diagnostic branch while retaining the original frozen confirmatory result.

## Part 2. Separate, newly preregistered D-stage experiments (DO NOT RUN IN C-STAT)

Create a plan and estimated design-only feasibility tables, not new outcomes, for the following future studies. Each future study needs its own fresh seed domain, standalone preregistration, theorem applicability checklist, and no confirmed outcome-based tuning.

### D1. Violation magnitude and certificate power
- Construct settings with known true signed gaps relative to the constraint threshold gamma in `{0, ±.025, ±.05, ±.10, ±.20}`, plus normalized gamma/r in `{.5,1,2,4}` using **design-only** radii.
- Include all-null/boundary-null settings and true alternatives; group prevalence `{.02,.05,.10,.20}`, chi `{1,4,8}`, family size `{1,16,64}` and strong/weak supported e. Freeze target and thresholds before draws.
- Primary output: probability per independent log of correctly certifying a violation, any false-safe/false-violation, and abstention. Distinguish marginal candidate power from family-level error.
- Optimize pilot sample sizes using power calculations or design-only radius inversion, never on the same confirmatory seeds.

### D2. True discover–freeze–certify
- New DGP includes at least 4 exogenous pre-action features and planted interaction group `1{G=1,degree>q80,new_user=1,Z=high}` with intervention-dependent effect. Ensure the group exists with controlled mass and proof-compatible independent macro-block data.
- Discovery on distinct independent pilot blocks only; freeze rules/threshold/top L before certification (`L in {1,5,10}`). No oracle labels or certification outcomes during discovery.
- Evaluate held-out certified violation detection power, zero-effect familywise false positives, subgroup IoU/precision/recall, mass, width and abstention. Pay correct policy×auditor×constraint multiplicity on the held-out sample.
- Comparators: coarse fixed slices, invalid in-sample selection (clearly labeled exploratory/uncertified), independent split with naive iid CI, and valid graph-aware certification.

### D3. Pessimistic policy repair with genuine competing objectives
- Implement distinct potential outcome channels for utility and harm/cost; do not claim policy repair performance from a single scalar `Y` and one arbitrary threshold. Ensure legitimate targeted policy mixtures and feasible/safe fallbacks.
- Predeclare 8/16/32 target policies and 2–4 constraints; compute a valid simultaneous CI budget across every policy×(utility + all cost constraints) under the same independent block model.
- Compare utility-only selection, point-DR empirical constraints, clipped/SNIPS point constraints (point-only), COMET pessimistic selection, and oracle hindsight evaluation (never an estimator input). Report real value, true max violation, false-safe selected policy, abstention and two separate regret comparators (robust margin feasible vs truly feasible oracle).
- Eventwise fixed-design feasibility is the only claimed guarantee. No future closed-loop safety guarantee.

### D4. Stronger dependence model / exposure-policy compatibility (separate proof gate)
- Before any certified extension to slates/networks, specify a **valid joint action policy** `Q(A|D)` inducing every local target marginal `q_u(s)=P_Q(g_u(A)=s|D)`. Arbitrarily chosen local q values may be incompatible: for a single display slot over two units, `q_1(shown)=q_2(shown)=1` is impossible.
- Build block-local independent stochastic primitive variables (shared slate randomization, shared node/edge shocks) and derive a sufficient conflict graph from exactly shared primitive supports. Prove conditional independence of all disconnected sets, not just pairwise zero covariance; maintain independent macro-blocks.
- Test whether chi and variance graph bounds are informative when the observations are not literal clique copies; do not treat a network adjacency list as a sufficient stochastic dependency graph without proof.

### D5. Weak overlap, finite-p tails, optional learned independent pilot
- Explicitly vary e_min with N or exogenous context in a declared design while recomputing valid design-conditional moments; distinguish positive support from non-identification at e=0.
- Keep original heavy-tail F even if fully vacuous. For any new method, prove its coverage, including truncation bias or tail scale upper-confidence events, before labeling CERTIFIED. Analytically examine N needed for nontrivial F before expensive runs.
- Independently train a bounded mu_hat on a separate pilot and freeze it before evaluation; this is allowed under the proved theorem. Mutual cross-fitting remains unproved.

## Part 3. Manuscript rewrite PROPOSAL, not direct Overleaf mutation

The experiment repo contains `paper/` copies; separate `COMET_overleaf` was not accessible in this review. Create only a **reviewable proposal** under `paper/rewrite_proposals/` or a fresh branch and produce `paper_rewrite_diff.patch` plus a claim-to-proof-to-experiment matrix. Do not force-push, overwrite the independent Overleaf repo, or insert unrun empirical findings.

1. Replace `paper/main.tex` abstract's claims about fully adaptive logged feedback, dependence-separated mutual cross-fitting and an already operational generic coupled/drifting certificate. Make the proved fixed-design independent-block theory the main claim. Retain broader adaptive extensions only as explicitly unproved future work. If a stronger theorem is subsequently proved, update scope in a new branch.
2. `paper/sections/01_introduction.tex`: rewrite the problem as **simultaneous certified counterfactual moments under known exposure propensities, independent evaluation blocks and within-block graph dependence**; list actual contributions separately from existing DR, MOM, graph coloring and one-step pessimistic selection. Do not claim tested real-slate exposure effects or adaptive feedback.
3. `paper/sections/02_setup.tex`: main estimand `M_D=N^-1 sum_u h_u(sum_s q_u(s)mu_u(s)-f_u)` with D fixed pre-outcome, independence, support, and proven graph definition; distinguish `M_path` as future target. Require a joint target action law Q when interpreting q as a globally implementable slate/network policy; otherwise call q an exposure-marginal functional.
4. `paper/sections/03_method.tex`: show **two certified branches** with actual constants: (i) finite-p robust MOM + exact-binomial K, (ii) bounded-outcome graph-aware mean + Chebyshev. Use fixed/independent-pilot mu_hat and known moment envelope; remove unproved estimated nu/coupling/drift radius from the executable advertised algorithm. Make abstention explicit.
5. `paper/sections/04_theory.tex`: remove the original unproved `thm:uniform-comet` from the theorem environment. Elevate `thm:gate-a-clean` to main text, add exact-binomial theorem and bounded-graph variance theorem, with precise assumptions and separate proven estimators. State 1/8 Le Cam lower bound only for chi-clique exact-replication subclass and expected absolute risk, not a general sparse-graph high-confidence minimax theorem.
6. `paper/sections/05_discover_repair.tex`: prove eventwise local feasibility with simultaneous budget over the whole candidate library, utility + cost; explicitly state comparator safety margin and possibility of no certified feasible policy. Independent discovery must not leak into the certification window. No long-run safety claim.
7. `paper/sections/06_experiments.tex`: replace unperformed planned protocol tables with actual C-STAT results **after** confirmation is complete; show eligibility/width/abstention/power alongside coverage; label optional D and real-data studies as planned rather than done. Don't write invented empirical numbers.
8. Related Work: clearly distinguish from existing off-policy confidence sequences (Karampatziakis, Mineiro and Ramdas, ICML 2021), uniform heavy-tail MOM (Høgsgaard and Paudice, ICML 2025), weak-overlap OPE (Mehrabi and Wager, 2024) and combinatorial-bandit OPE (Shimizu et al., RecSys 2024). Contributions cannot be just standard components bundled together.
9. Include one honest limitations section: no arbitrary adaptive pathwise guarantee, unknown tail-scale fitting, cross-fit mutual dependence, arbitrary sparse-graph optimality, hidden cross-block shocks or deployment trajectory guarantees; F can remain vacuous.
10. Provide alternate titles; favor `COMET: Certified Counterfactual Auditing under Weak Overlap and Block Dependence` if keeping weak-overlap focus, or `COMET: Simultaneous Counterfactual Moment Certificates under Graph Dependence` if prioritizing verified scope. Retain original title only if a matching adaptive-feedback theorem and evidence become available.

## Required deliveries

- `reports/gate_C_stat_scientific_lock.md` — exact science/code/seed checksums and executed evidence.
- `reports/gate_C_stat_execution.md` — commands, actual outcomes, failures, checkpoints, recovery, resources, all 6,000 IDs and no excluded records.
- `results/gate_C/confirmatory/` — raw output shards + summary tables, figures with a regeneration script, and canonical manifest.
- `reports/gate_C_stat_methods_validation.md` — independent recomputation of coverage, Holm p-values, statuses, denominator preservation, last-commit and source provenance.
- `reports/gate_C_stat_results.md` — interpretation of favorable and **unfavorable** results without extending the theorem.
- `reports/next_phase_D_preregistration_proposal.md` — unrun future design D1–D5 plus sample/memory feasibility.
- `paper/rewrite_proposals/` — scope-correct LaTeX/prose diffs, bibliography crosswalk, no fabricated results; label as proposal.
- Final concise `PASS/BLOCKED` decision for C-STAT and a separate recommendation for manuscript readiness. Commit on a new branch and preserve all previous branches/tags. Make no claim of full manuscript or Overleaf synchronization unless actually done.

**Stop-on-theorem-mismatch rule:** The original proof assumptions, current scientific code and frozen probabilistic model are the ground truth. If any new source inspection uncovers a mathematical mistake, invalid marginal assignment, incorrect confidence denominator, or oracle leak, report it immediately and BLOCK C-STAT rather than choosing a convenient fix that compromises preregistration.

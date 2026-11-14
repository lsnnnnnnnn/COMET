# COMET master research goal — post-C-STAT version 2

**Read POST_CSTAT_OVERRIDE.md first.** This version starts from the completed
C-STAT anchor `ca5bb878cf9635fac4381d03281df0bc8a900daa`.
E0 is complete: reuse it, generate zero additional historical confirmatory logs.
The required new work remains the heterogeneous global-graph auditing core,
E1–E6, strong comparisons, and a complete local manuscript. The old D1–D5
proposal names do not override this scope or require repeated user approvals.


## 0. Execute the whole goal, not another preflight

Deliver a complete, reviewable research package answering:

> For heterogeneous logged observations with an explicitly justified conditional dependency graph and weak exposure overlap, which subgroup- and policy-specific counterfactual moments can be certified, what determines their evidence requirements, and do the certificates support useful auditing and constrained policy updates?

The working title is **COMET: Counterfactual Moment Auditing under Weak Overlap and Graph Dependence**. Policy selection is a downstream use, not a replacement for the statistical research question. The old independent-block MOM implementation is a preserved reference implementation, not the intended final scope.

This goal authorizes work on proofs, implementations, preregistered experiments within the budgets below, analysis, and a complete local manuscript revision. It supersedes earlier instructions to stop after preflight **for this new workstream only**. Do not stop after preparing a plan, passing tests, or producing another GO memo. Proceed automatically along validated dependencies. Do not repeatedly ask the user to approve each stage.

An invalid theorem or model blocks only the methods/claims depending on it. Preserve the failure and continue independent valid work. Never silently relax an assumption, change a frozen experiment, discard unfavorable results, or label a heuristic certified to avoid a blocker. No paid compute, destructive repository operation, forced push, or remote Overleaf overwrite is authorized.

Read this file, `SCOPE_CN.md`, `THEORY_NOTE.md`, `EXPERIMENT_BLUEPRINT.json`, and `CLAIM_EVIDENCE.csv` completely. These are **planning artifacts**, not an already frozen protocol or completed result. Convert them into an executable, versioned protocol before new scientific outcomes are drawn.

## 1. Starting state and evidence boundaries

Reviewed delivery anchor: `lsnnnnnnnn/COMET`, branch `codex/gate-c-stat`, commit `ca5bb878cf9635fac4381d03281df0bc8a900daa`. C-STAT is complete: 6,000 frozen confirmatory logs, 1,134,000 candidate records, 485 passing tests and 28,884,898 reported independent validation checks. The completed result anchor is `dd59ec61a08b72cf241e87bcf575f9ce5ae585a7`; the final delivery commit is metadata-only. The historical scientific freeze remains `ab4c74fbf1ae84c0e5ffd72d77ce5b48d3fba8cb`.

The reviewed results and nine-page proposal support the old independent-block scope. They do not establish the required new global-graph residual-truncation core. Inspect newer local work before declaring any theorem absent or duplicating work. Preserve all valid newer work; never reset destructively. The original Overleaf source was not changed in this phase. Its last recorded anchor is `df70f486fc08139057436e2781c212ad741ef646`.

Read the current results, delivery, scientific-lock report and proposal main source once. Reuse the completed validator/provenance rather than rerunning the entire 6,000-log campaign or spending the session on redundant audit prose. A small deterministic compatibility check is sufficient for workstream startup unless an actual discrepancy is found.

Create a new research branch/worktree, e.g. `codex/query-specific-graph-auditing`. Preserve the historical commits and result directories. Use a separate isolated worktree or runner for frozen C-STAT; do not change the historical model/configuration/seed files or silently add the new method to its preregistered primary family.

Read the existing theorem contract, exact-binomial MOM, bounded graph variance, lower bound, Gate C heavy-tail contract, protocol, statistical code, and available paper source. Record exact paths and checksums. Do not spend the whole task producing repetitive audit prose.

## 2. Scope charter — mandatory deliverable before new claims

Write `reports/scope_charter.md` and a machine-readable claim ledger. Three claim levels must never be conflated:

1. **Established baseline:** fixed/exogenous independent blocks, valid graph structure, stable block targets for MOM, exact e, fixed or independent nuisance, known envelopes; the historical proofs and logs.
2. **Required new core:** a global sufficient conditional graph, heterogeneous per-row targets, a residual-truncated linear estimator, finite-family simultaneous certificates, query-specific active support/moments/coloring, paired contrasts, and useful auditing/updates in this model.
3. **Optional extension:** fixed-horizon predictable sequential inference with a complete filtration and valid cumulative budgets. This is not necessary for the core paper and cannot delay its completion.

Explicitly exclude from current core claims: arbitrary feedback-driven future distributions, long-run performative safety, mutual cross-fitting, unknown graph sufficiency learned from observed correlations, automatic distribution-free unknown-tail-scale estimation, graph-specific minimax sharpness for every sparse graph, infinite-class fairness, and arbitrary-stopping-time validity.

The theorem permits no numerical global propensity floor, but finite designs may have positive minima; intervals can become uninformative as support deteriorates. Distinguish this from demonstrating an annealed population theorem for arbitrarily small random propensities. Interference requires an exposure sufficiency assumption and a compatible full assignment law; shared outcome noise alone is not causal spillover.

## 3. Theory workstream — finish proofs before certified implementations

### T0. Audit and implement the core derivation

Use `THEORY_NOTE.md` as a derivation to verify, not as an instruction to assert a theorem. Prove the DR identity, legal residual moment bound, truncation-bias inequality with its stated constant, truncated second-moment bound, centered range bound, graph-coloring/Hölder MGF calculation, two-sided deviation, and finite-family union bound.

Let `d[u,s,theta]` denote the signed coefficient: h*q for a level query, h*(q-q0) for a paired contrast. Keep the known deterministic term separate. Derive an explicit radius for the **original, unclipped** moment. Retain an explicit bias term and ordinary finite-precision qualifications.

The proof should allow one connected graph and heterogeneous means. Do not reintroduce common block means or independently repeated macro-blocks through the implementation. If a part of the proposed derivation is false, supply a counterexample and a corrected conservative theorem; update affected proposed claims transparently before freezing new scientific runs.

### T1. Query-specific structure

Prove the active-support induced-graph lemma, the role of signed contrast coefficients, and the legality of design-only truncation selection. Use the smallest *verified available coloring*, without calling it an optimal chromatic number. Compute the graph from random-source overlap; do not confuse a domain network with the score-dependency graph.

The required implementation starts with one truncation level per query. Use the fixed grid of scale multipliers specified in THEORY_NOTE. Per-row thresholds are optional, not a reason to delay the main study. A bounded-outcome branch may select a proved untruncated graph Hoeffding/Bernstein certificate by a D-measurable rule; it may not inspect realized interval widths, empirical errors, or oracle means.

### T2. Certifiability and lower bounds

Complete a clearly scoped lower-bound result involving subgroup mass pi, rare exposure epsilon, clique replication chi, and moment order p. The proposed observation-thinning construction is in THEORY_NOTE. State the risk, parameter regime, observable experiment, integer requirements, and bounded-mean saturation explicitly. Do not claim matching simultaneous-confidence logarithms or arbitrary-graph optimality.

Derive the sufficient decision condition gamma>2r and analytic sample-budget diagrams. Distinguish a sufficient sample requirement of one procedure from an information-theoretic necessary requirement. Include fixed-DGP rate studies only as descriptive; a Pareto exponent is not the same as the moment order supplied to the procedure.

### T3. Discovery, selection, and mixtures

Give corollaries for a finite discovered family conditional on independent discovery information, false-certification control, and eventwise feasible selection. Report P(return and unsafe), not just P(unsafe | return). Define a useful policy using a nontrivial service requirement and utility condition.

For mixtures, certify a finite set of base-policy coordinates, then linearly propagate their simultaneous bounds. Implement mixtures only for affine moments and compatible joint assignment laws. Do not reapply a nonlinear clipped estimator to an outcome-selected mixture and pretend it equals the mixture of the certified base estimates. Moving score bins, arbitrary denominators, and nonlinear fairness metrics are not covered automatically.

### T4. Optional, nonblocking sequential extension

Attempt a fixed-horizon predictable theorem using per-round conditional MGFs, one-way/past-only nuisance fitting, correct within-round graphs, and deterministic valid cumulative budgets. If it is fully proved and tested, add an appendix experiment within the remaining budget. Otherwise deliver a precise proof-status memo. Do not put adaptive feedback in the title or abstract merely because this task was attempted.

## 4. Code architecture and contracts

Implement new modules without rewriting frozen historical science. Suggested modules (names may adapt to the repository):

- `comet/queries.py`: immutable query definitions, coordinate IDs, normalizers, signed contrasts, response-channel IDs, and policy provenance.
- `comet/source_graph.py`: source-to-row incidence, sufficient dependency graphs, induced support, deterministic proper coloring, and proof diagnostics.
- `comet/residual_truncation.py`: score, bias, variance proxy, range contribution, design-only tuning, and explicit certified radius.
- `comet/certificate_dispatch.py`: assumptions, eligibility, and design-only selection of valid constructions.
- `comet/audit_pipeline.py`: independent discovery, frozen finite family, certification, and documented decisions.
- `comet/policy_update.py`: finite selection and optional certified affine mixtures.
- `experiments/core_graph_dgp.py`, `experiments/pipeline_dgp.py`, `experiments/semisynthetic_selective_labels.py`: distinct model and oracle interfaces.
- `experiments/run_confirmatory.py`: new recoverable streaming runner; separate legacy wrapper.

Every output must name estimand, response channel, normalization, confidence budget, applicable assumptions, selected method, envelope provenance, active rows, coloring count, raw/clipped endpoints, bias/variance/range pieces, data digest, seed namespace, code/config hashes, and failure status. Cache design-only quantities without leaking outcomes or changing frozen computation.

Statuses include `CERTIFIED_UNDER_DECLARED_ASSUMPTIONS`, `POINT_ONLY`, `ASYMPTOTIC`, `HEURISTIC`, `NOT_APPLICABLE`, `NONIDENTIFIED`, `NUMERICAL_FAILURE`, and `ASSUMPTION_UNVERIFIED`. Use existing compatible names where necessary; document mappings. Zero support is not an extreme-weight clipping setting. A vacuous but valid certificate remains in coverage denominators. An empty intersection is a confidence failure, not permission to invent a nonempty interval. Do not use absence of certificates as evidence of zero error.

Separate candidate construction, logging, fitting, certification, and oracle metrics. An analytic DGP may use true means to generate data and to construct a prespecified null/alternative, but the certifier and selector must not receive those means or oracle errors. All truths are joined after methods and decisions finish.

## 5. Baselines — correctness, strength, and equality of information

Keep old MOM/exact MOM/Chebyshev as historical references where their assumptions hold. They are not the only comparison methods. In heterogeneous settings, common-target MOM is inapplicable unless a separate valid extension is supplied.

Required strong comparisons:

1. **Graph Hoeffding and graph Bernstein for bounded outcomes.** Derive them using the actual known score ranges and legal variance bounds. Use the same q/e, nuisance, support, graph and familywise delta as COMET. Include both global and query-local versions where mathematically legitimate.
2. **Generic bias-corrected truncated graph mean.** Give it the same legal moment information. Include a global-envelope/global-graph instantiation as a component ablation and a fully matched local instantiation as an honest strong comparator. If the latter is algebraically identical to COMET, show the equivalence and do not count it as an inferior independent method.
3. **Colorwise independent truncation with a valid union budget and weighted recombination.** This supplies a separate valid comparator on heterogeneous graph data; color sizes and target weights must be retained. It cannot discard colors or change the estimand.
4. **Finite-moment Catoni on a truly i.i.d./identically distributed or otherwise theorem-supported anchor.** Conditional independence alone does not license an i.i.d. theorem for different means. Add an appropriate homogeneous independent anchor rather than declaring the baseline inapplicable everywhere.
5. **Strong OPE inference on a matched bounded independent/sequential submodel.** Verify the exact theorem/implementation before porting; do not ignore within-round dependence to make an OPE confidence sequence appear applicable. Compare at the same horizon and error budget and disclose stronger time-uniform guarantees where present.
6. **Paired graph confidence bounds vs subtraction of two separately certified policy levels.** The level-difference baseline must pay for both levels in the same total budget. Give strong baselines the same contrast information wherever applicable.

Diagnostic-only methods: unadjusted in-sample subgroup search, i.i.d. Wald intervals under dependence, residual clipping without a bias debit, and point-constraint policy choice. Keep their scientific error rates, but never rename them certified or treat their abstention/status as comparable theorem guarantees.

Audit primary references and write `reports/novelty_and_baseline_matrix.md`. At minimum check Janson (2004), Bhatt et al. (2022), anytime-valid OPE, and ESGuard (2026). ESGuard's interference/smoothing assumptions and asymptotic selection guarantee differ; do not claim either dominance or applicability without mapping the target and assumptions. A recent paper must be read from its actual source, not inferred from its title. Reuse available implementations where licensed and appropriate, otherwise implement the stated procedure with tests. Unsupported baselines get explicit reasons, not fictitious results.

## 6. Experimental architecture

Run the six new suites below after their method/model prerequisites pass. All proposed parameters must be committed in a new freeze before new confirmatory outcomes. They do not alter legacy C-STAT. Do not run an unrestricted Cartesian product.

### E0. Completed historical C-STAT — reuse only; zero new draws

E0 is closed at `ca5bb878cf9635fac4381d03281df0bc8a900daa`. Reuse all 6,000
completed IDs and the original 17-test primary family without modification.
Do not rerun, extend, overwrite, or append new methods to its confirmatory
claim. Reuse its launcher/checkpoint engineering where appropriate in an
isolated new module, not its restricted probability model.

If a new method is evaluated on regenerated historical data, call this a
**post-hoc retrospective benchmark**, write to a separate namespace, and
never include it in the original preregistered 17 comparisons. No such replay
is required: a deterministic analytic A-setting check plus fresh E1–E6
outcomes already supplies a cleaner route. Historical exact-byte provenance
is preserved; new science has its own freeze and numerical contract.

### E1. Core heterogeneous graph validity — 12 cells x 1,000 logs

Purpose: establish validity and usefulness beyond replicated cliques/common block means.

- Certification N=32,768, primary delta=.05, secondary delta=.10, m=16.
- 3 dependence constructions: independent heterogeneous rows; a connected cycle/path from overlapping source pairs; a connected chain of overlapping triangular factors.
- 2 propensity regimes: moderate overlap and rare-action overlap.
- 2 outcome regimes: bounded responses with p=2; symmetric Pareto-source responses with p=1.5, tail exponent 1.75 and known noise scale .1.
- All 12 cells have heterogeneous conditional means and context-dependent policies. The independent case is not falsely called identically distributed.

Suggested reproducible design: fix x in [-1,1]^4 before outcomes with a deterministic index trend; choose moderate e1=.2+.6*sigmoid(x1-x2), weak e1=.005+.045*sigmoid(x1-x2). Use 4 distinct q functions (including a constant anchor and context-dependent logits) crossed with 4 auditor indicators: all, x1>0, x2>0, and x1>0 & x3>0. Freeze exact coefficients and all ties. Do not optimize these choices using coverage or power.

Response locations can be heterogeneous smooth functions constrained analytically to an interior of [0,1], e.g. mu0=.35+.1*sin(2*pi*u/N)+.05*x1 and mu1=.55+.1*x2+.05*sin(4*pi*u/N). These are generator parameters, not estimator inputs. In bounded cells, use centered independent-source Rademacher noise whose coefficient absolute sum is at most .1, preserving support [0,1]. In heavy cells use symmetric Pareto sources with analytically derived moments and location-class bounds. The oracle conditional mean is the location, analytically known.

Use fixed midpoint nuisances in the primary validity grid, and independent fitted nuisances later. Build the dependency graph by intersecting all logging/outcome source sets. Nonreplication must be real: connected rows may share one source but also have distinct private sources or locations. Do not duplicate a single record and rename it a graph model.

Record coverage of the whole 16-coordinate family per independent log, width, decision errors, component radii, support, and compute resources. Report where new and reference methods coincide, win, or lose. Do not treat a full-range interval as informative.

### E2. Query locality and evidence costs — 6 cells x 300 logs

Purpose: determine whether unrelated difficult regions impose unnecessary cost, without conflating the effect of multiple components.

Use one connected graph containing an audited low-degree region and an unaudited hub/source clique. Keep the audited region's outcome/propensity law fixed. Vary the outside hub size across {1,16,64} and outside propensity severity across {moderate,1e-4}, giving 6 conditions. Freeze a query family including both local and global queries. Correlate paired data across outside-only variants for mechanism comparisons, but treat replicate IDs, not queries/variants, as independent inference units.

Compare: global max envelope/global coloring; summed local moment with global coloring; local moment plus induced-support coloring; matched strong query-local Bernstein/truncation. Export the decomposition and analytic invariance tests. Restricting a valid query to active rows should not change its estimand. A matched local baseline may recover the same gain; report this rather than pretending locality is unavailable to competitors.

Produce design-only cost maps for N in {8192,32768,131072}, subgroup mass pi in {.02,.1,.5}, rare exposure epsilon in {.002,.02,.2}, p in {1.5,2}, and verified coloring counts. Add a declining-propensity schedule epsilon_N=.2*(N/8192)^(-beta), beta in {0,.5,1}, to distinguish fixed weak overlap from deteriorating support. These broad maps are algebraic calculations, not thousands of new Monte Carlo cells. Use the combined 1,600-unit anchor budget for two homogeneous independent strong-baseline anchors (200 logs each) and at most six stochastic scaling anchors (200 logs each), selected by declared parameter positions rather than favorable pilot results. These are not additive budgets.

### E3. Paired policy contrasts — 12 cells x 300 logs

Purpose: test whether the relevant policy change avoids paying for unrelated levels, and whether gains survive fair strong baselines.

Use a connected source-overlap graph. Cross changed-support fractions {.02,.1,1} with 2 overlap regimes and 2 outcome regimes (bounded/heavy), yielding 12 settings. Fix q0 and context-dependent q1. Use the same outcome, nuisance, auditor, and logged rows for paired contrasts. Compare direct contrast certificates with differences of two simultaneous level certificates under equal total delta and with matched contrast-aware strong baselines.

Report raw and normalized contrast errors, radii, false improvement, power, and utility-noninferiority decisions. Add a deterministic/scaled-noise test with q_eta=q0+eta(q1-q0), eta in {.1,.25,.5,1}, verifying that signal and radius scale together when tau is scaled. Do not turn this scaling grid into four independent data sets or claim that tiny steps automatically have higher sign-certification power.

Candidate policies must be deployable in the stated assignment model. For interference/slates, derive all exposure marginals from a joint policy. Pointwise arbitrary marginals that violate a capacity constraint are not a policy repair.

### E4. Power–gap and false-certification boundaries — 24 cells x 300 logs

Purpose: separate information scarcity from conservative bounds.

Use 4 prespecified environments: moderate/weak overlap x bounded/heavy outcomes on the connected source-overlap graph. For a fixed meaningful subgroup (primary pi=.1), fix an upper risk threshold alpha=.4 and construct analytic normalized subgroup targets alpha+gamma with

    gamma in {-.10,-.03,0,.03,.10,.20}.

These 24 cells are defined before data. The DGP may use its parameters to plant the specified mean; the procedure receives only the task threshold, not the true gap. Keep locations within their declared class. Other frozen family members supply heterogeneous null/alternative coordinates, and m remains the actual total family size.

Report: probability of any false-safe claim, any false-violation claim, any false claim, violation power, safe-certification power, and abstention. Distinguish marginal candidate power and the event of detecting at least one prespecified true violation. At gamma=0, a false violation event is a type-I error. Use whole-run denominators.

Plot empirical decisions against the known design-only radius and the sufficient boundary gamma>2r. Also show local subgroup/exposure sample costs, with the limitations of the lower bound. Do not use only gamma>r as a claimed nominal-power guarantee. Results on different gamma settings may be paired for comparison; uncertainty calculations must respect that pairing.

### E5. Full discovery–certification–update — 8 cells x 500 independent trials

Purpose: show that a valid certificate supports useful decisions, rather than only returning narrow intervals or abstaining.

Cross dependence {independent,source-overlap graph}, overlap {moderate,weak}, and world {null,mixed planted violations}. Bounded utility and risk outcomes are the required primary task; heavy-tail pipeline is not mandatory because it is already tested in E1/E3/E4.

Each trial has genuinely independent random-source pools for nuisance training, discovery, and certification. Suggested sizes: 4,096 training rows, 8,192 discovery rows, 32,768 certification rows. Context layouts may be fixed, but outcome/assignment sources must not cross the split. Row-wise random splitting of a connected realized source graph is not sufficient. Train nuisance once on the training pool. Fit policies and auditors only on training/discovery pools, then freeze them. A reasonable primary auditor is a shallow rule tree of maximum depth 4, at most L=4 returned rules, and minimum design mass .02. Deduplicate identical queries before computing m.

Plant an interaction subgroup not itself supplied as a feature. E.g. a 3–4-way interaction among pre-action group/continuous features with a bounded risk increment when exposed. Include covariate interactions outside the discovery search's exact simplest rules so the task is not only rule recovery. Freeze the actual DGP; do not increase the planted gap after seeing weak power.

Use separate utility and risk channels. Generate at most 8 candidate policies using training/discovery data (including a baseline), with a fixed trade-off grid and deterministic tie rules. Define normalized subgroup risk constraints, an expected service floor .2, an expected capacity ceiling .6, and a utility noninferiority margin relative to the baseline. Service/capacity may be exactly computable from fixed q and X; do not attach unnecessary outcome intervals to known quantities. Reject-all must fail the service requirement. If no safe useful candidate can be certified, abstain; do not label an uncertified fallback safe.

The combined family must include every utility contrast and every risk query used in audit and selection. For example, 8 policies x 5 risk auditors plus 7 nontrivial baseline utility contrasts already gives 47 distinct coordinates; do not keep m=16 from the old experiment. Use a single simultaneous event for the combined decision, or an explicit preallocated failure split. Candidate-generation and selection procedures remain identical when comparing certificate engines.

Primary arms: point-constraint selection; unadjusted in-sample auditing (diagnostic); properly independent discovery plus global certificate; independent discovery plus query-specific certificate; strongest matched eligible certificate; and abstain/status-quo reference. Include a fixed-slice auditing baseline. Match certification sample sizes as well as total data budgets; show both accounting views where an in-sample method uses more evaluation labels.

Report independently:

- recovery/overlap of the discovered and planted subgroup (not a certificate),
- P(at least one true violation is discovered AND certified),
- P(any false certification among frozen discovered tests),
- P(return and unsafe), P(unsafe | return), and return rate,
- P(return and safe and useful), true utility, utility gain, maximum true risk violation, expected service, and abstention,
- oracle best feasible candidate value and robust-slack comparator value, evaluation-only.

Repeated empty outputs are not success. A failed pipeline does not falsify a valid interval theorem; it falsifies the claimed practical usefulness in that regime. Do not adjust thresholds to make the method look useful.

### E6. One real-covariate semi-synthetic task — 4 cells x 250 trials

Choose exactly one data pipeline before its outcomes. Prefer an existing valid, small TGB semi-synthetic pipeline if it is already available and its graph/exposure contract is complete. Otherwise use a single fixed ACS/Folktables state/year (default: California, 2018, one-year person data) with selective labels. Verify source, task definition, license/terms and download size; do not silently substitute another data set if unavailable. Report DATA_BLOCKED and continue synthetic/theory/manuscript work if access fails.

ACS is a real-covariate, fixed-population selective-label benchmark, NOT randomized evidence about a social intervention. Use fully available benchmark labels only in the allowed training/discovery pool and the evaluator; hide certification labels unless the simulated logger exposes them. For selection action 1, utility can be Y and risk 1-Y; for action 0 service outcomes are known zero. The counterfactual estimand is the finite-population policy-weighted selection outcome, not the causal effect of selection on income.

The 4 cells are overlap {moderate,weak} x label-availability dependence {independent,known source-overlap}. A suitable non-clique dependent logger uses independent Gaussian sources Z_i and U_i=Phi((Z_i+Z_{i+1})/sqrt(2)), then A_i=1{U_i<=e_i}. Each marginal propensity is e_i and neighboring assignments share a source. Prove the dependency graph and record finite-arithmetic conventions. Fixed labels do not make the random logging masks independent. Use independent sources between training/discovery/certification. Real household identifiers may guide group-preserving splits, but do not assume they capture all statistical dependence.

Reuse the E5 decision rules with service and capacity constraints. A fixed unit count must respect actual data availability; before outcomes, either use the prescribed 16,384 certification rows plus adequate disjoint training/discovery rows or record a design-only availability amendment. No duplication of rows to pretend that more independent people were observed. Repeat only the declared logging/pipeline randomness, with the finite-population estimand clearly labeled.

If TGB is selected, its real topology is only a structural template. Specify synthetic independent sources and derive the resulting score graph; include any source-induced extra edges. No raw network is declared a dependency graph by observation alone. Do not start ACS, TGB, OBD and KuaiRand concurrently. OBD/KuaiRand are outside the required deliverable.

## 7. Negative controls and optional extensions

Reserve up to 400 draws for predeclared negative controls: hidden shared shock, omitted source edges, wrong propensity, outcome-selected truncation, missing clipping bias, cross-split source leakage, unsupported exposures, and a falsely asserted moment domain. Some failures are detectable schema violations; others require an intentionally incorrect-assumption experiment and may not be identifiable from one log. Do not claim the API automatically detects hidden dependence.

A matched i.i.d. homogeneous anchor for Catoni/OPE and a small local-interference/slate example can use the remaining extension budget. If a spillover claim remains in the abstract or Contributions, an actual outcome depending on neighbor actions and valid full-policy exposure calculation become mandatory; otherwise remove that empirical claim and leave interference as a conditional instantiation/example. Do not substitute shared noise for interference.

## 8. Statistics and experimental governance

Freeze actual configurations, candidate generation rules, method applicability, confidence budgets, seeds, and stopping rules before confirmatory outcomes. Separate design calculations, deterministic tests, engineering pilot data, confirmatory runs, and subsequent exploratory work in filenames and metadata. Primary science grid changes require a new version; an improved method may be a new arm, not a rewrite of old results.

Use 95% simultaneous coverage as the primary level and 90% as secondary on the same logs. Familywise coverage is one Bernoulli observation per independent logged data set, never per candidate. For new core-validity methods, predeclare the cell-method diagnostic family after applicability is fixed but before outcomes. Use exact one-sided binomial undercoverage tests plus Holm as an implementation diagnostic; nonrejection does not prove coverage. Preserve the old 17-test family separately. New validity screening is not a joint theorem over every plotted method.

Report Wilson or exact Monte Carlo intervals for Bernoulli endpoints; use replicate-level paired bootstrap or paired differences for method contrasts. Bootstrap resampling is for uncertainty of Monte Carlo performance summaries, not a substitute for a certificate theorem. Give simultaneous curve bands or label pointwise bands accurately. Candidate pooling must not shrink confidence intervals artificially.

Primary practical endpoints are (a) any false claim, (b) detection of true violations, (c) safe-and-useful return. Report coverage/width jointly, raw and feasible-set-intersected intervals, normalized subgroup widths, component radii, legal-envelope slack diagnostics, and non-vacuity. The finite known mean class, not observed reward extrema, determines any target-range intersection. In heavy cases without a legal finite target range, relative-support width is NA; do not invent one.

If a preregistered diagnostic flags serious undercoverage, preserve all data, isolate the cause, and suspend the affected certified claim. Replaying an identical seed for debugging is not a new independent trial. A fixed error may justify a versioned rerun; never delete the failed result or mix versions. Do not stop a study early because significance or favorable power has appeared.

## 9. Execution and resource budget

Required new scientific trials: E1 12,000 + E2 1,800 + E3 3,600 + E4 7,200 + E5 4,000 + E6 1,000 = **29,600**, plus the separate 6,000 legacy confirmation logs if unexecuted. Pipeline trials contain multiple separately generated splits; report this resource distinction. Do not describe all candidate rows or paired design variants as independent replications.

Cap additional new-study log/trial units at **32,000 total**, including pilots and optional anchors, not counting legacy C-STAT. Default allowance: <=200 engineering pilot units; <=400 negative-control units; <=1,600 design-selected scaling/strong-baseline anchors; <=200 optional extension units. This is a cap, not a requirement to consume unused budget. No giant full-factorial expansion.

Use CPU by default, at most 2 worker processes, no paid/cloud resources or required GPU. Inspect free RAM/disk first. Target <=4 GiB combined worker memory and <=1.5 GiB new persistent compressed artifacts; keep >=2 GiB free disk. Download only the one selected dataset, default total <=512 MiB compressed unless it already exists locally. If a resource limit is binding, stream/compress or reduce concurrency, not scientific replications silently. If the full plan cannot be completed safely, checkpoint, list exact outstanding IDs, and deliver a resumable report without claiming completion.

Cache design-only arrays and operate on NumPy-style arrays in the NEW implementation rather than Python objects per row/query whenever safe. Graph memory should track actual source overlaps, not allocate an N x N matrix. Validate vectorized results against transparent scalar fixtures. Do not change legacy scientific arithmetic just to accelerate it.

Store one immutable atomic checkpoint per scientific run; use separate manifests for shared metadata and compact, compressed tabular scientific outputs. Do not load all candidate records into RAM for final aggregation. Retain enough seed/config/source information to regenerate raw logs. Store representative raw debug cases by predeclared run IDs and all relevant failures, not only favorable examples. Preserve phase labels and provenance across retries. Repeated resumes must neither redraw completed data nor alter completed payload bytes.

A user goal can require many operations, but an execution agent must not imply work continued after its actual session ended. Log actual completed work and exact resume commands. Do not give fabricated completion counts.

## 10. Paper revision — required deliverable, not a future offer

Prepare a complete revised local manuscript using the available `paper/` source on the new branch. If a separate Overleaf repository is readable, reconcile its source; otherwise the local version plus a patch/change inventory is sufficient. Do not push or overwrite the independent Overleaf remote without explicit permission.

Proposed main structure:

1. Problem: which counterfactual questions are certifiable from selective, dependent logs?
2. Estimand and assumption contract: fixed-design target, exact e, independent training/discovery, sufficient source graph, supported exposure, legal residual moments.
3. Method: residual truncation, explicit bias + stochastic radius, query support and contrasts.
4. Theory: heterogeneous global-graph certificate; query-local/contrast corollaries; scope-accurate certifiability/lower-bound result.
5. Evidence: core heterogeneous graphs; locality/cost; power–gap; paired contrasts; complete synthetic and one real-covariate pipeline.
6. Discussion: what is identified vs assumed, when the data are insufficient vs when a bound is conservative, unknown scale and adaptive limitations.

Historical MOM and C-STAT belong in baselines/appendix; do not let them consume the main narrative. Remove the unproved adaptive theorem as a claimed main theorem. Remove audit-Gate labels from polished mathematical theorem names. Preserve audit history outside the submitted narrative.

Proposed main visual evidence (do not make a decorative diagram in place of results):
- Table 1: claim/assumption/applicability map.
- Figure 1: valid coverage and informativeness across nonreplicated heterogeneous graph regimes.
- Figure 2: query-local cost decomposition and support/overlap/sample-budget map.
- Figure 3: power versus true gap, false certification, and the 2r sufficient boundary.
- Figure 4: paired contrast versus separately estimated levels, including a no-free-small-step control.
- Table/Figure 5: safe-and-useful return, utility, risk and service in the complete synthetic and semi-synthetic tasks.

Every empirical sentence must reference a generated result table/figure and exact configuration. Do not prewrite favorable quantitative results, invent missing experiments, hide unfavorable regimes, or leave an unproved extension as a theorem with a disclaimer. If core results are not supported, deliver an honest limited-scope draft and `research_verdict.md` describing the gap; passing unit tests is not research success.

Create a contribution audit. Standard ingredients must be credited as standard. If matched generic methods reproduce all gains, the paper must characterize its contribution as a target-specific formulation/analysis/workflow where justified, not a new universally superior estimator. Any stronger novelty claim needs an explicit distinction and evidence. Do not claim a venue acceptance threshold has been met.

## 11. Tests and acceptance conditions

Required deterministic/property tests include:

1. Scalar DR identity by finite enumeration with misspecified fixed nuisance and exact e.
2. Signed contrast identity and zero contrast gives zero random uncertainty.
3. Bias constant inequality, including p near 1 and p=2.
4. Truncated second-moment and centered-range bounds.
5. Small-graph MGF verification/enumeration and proper coloring.
6. Source-intersection graph sufficiency constructions; wrong original-star graph counterexample.
7. Heterogeneous targets and unequal sizes preserve the full raw-row target.
8. No common-block-mean requirement in the new API.
9. Active support and induced graph keep all retained shared-source edges.
10. Legal design-only threshold selection; refusal/explicit exploratory status for outcome tuning.
11. Known residual bounds for midpoint and other bounded fits, shared with baselines.
12. No oracle/truth dependency in estimation and selection code.
13. Unsupported q/e is refused; zero subgroup mass has no ratio.
14. Null/gap fixtures; gamma>2r implication; gamma>r is not substituted.
15. Contrast mixture scaling and policy-mixture interval propagation.
16. Discovery split random-source separation and no evaluation feedback.
17. Full decision family/budget includes utilities, risks, signs and baselines.
18. False-safe and unsafe-given-return denominators; abstention is not useful success.
19. Empty confidence intersections and numerical failures cannot vanish from reports.
20. Preflight/confirmatory/legacy seed and phase isolation.
21. Resume/corruption/source-change rejection and streaming vs small in-memory summary equivalence.
22. Baseline algebraic equivalence tests where two labels implement the same bound.
23. Heavy sampler moment-domain proof/fixtures and explicit finite arithmetic limits.
24. Exact-e exposure pushforward for any retained slate/interference example.

Acceptance is evidence-based, not a prescribed positive result. At completion deliver:

- `reports/scope_charter.md`, theorem/implementation/experiment claim ledger;
- completed theorem files with proofs and limitations; optional theorem status;
- frozen protocols/manifests and provenance;
- all actual runs, raw summaries, failures, checkpoints and remaining IDs;
- valid strong-baseline comparison and novelty matrix;
- generated paper figures/tables and complete revised local LaTeX source;
- `reports/research_verdict.md` distinguishing correctness, utility, distinctiveness, and readiness;
- one `reports/FINAL_HANDOFF.md` with actual commands, test totals, completed/blocked work, source SHAs and exact resume instructions.

## 12. Autonomous continuation policy

After the scope inventory, proceed to proofs, code, deterministic tests, analytic design audit, frozen empirical studies, analysis, and local paper rewrite without requesting approval between each. At each dependency checkpoint record GO/BLOCKED internally and move to the next valid task. Do not stop with a report that only says "next phase GO."

If the core graph theorem is blocked, continue legacy results, lower-bound analysis, applicable strong baselines and a limited manuscript; do not spend thousands of runs validating an unproved certificate. If a dataset is blocked, complete the synthetic task and document the missing external validation. If the optional adaptive theorem is blocked, leave it out and finish the primary paper. If practical gains vanish under fair strong baselines, report that result and revise the contribution claims rather than constructing a weaker comparison.

The final question to answer is not "how many gates passed?" It is:

> Exactly which COMET claims are now proved, implemented, and supported by informative experiments, and what evidence supports each claim in the revised paper?

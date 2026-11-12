# COMET — Master Codex Task: theorem audit, trustworthy implementation, and experimental campaign

**Project:** *COMET: Counterfactual Moment Auditing under Weak Overlap and Dependent Feedback*
**Source bundle:** the user-supplied ZIP, containing `main.tex`, `full_working_draft.tex`, `sections/`, `sections/full/`, `references.bib`, `RESEARCH_TODO.md`, and PDFs. Treat the LaTeX sources as the scientific source of truth. The bundle has no experimental code/results.

## Mission and non-negotiable rules

You are the research engineer and mathematical proof-audit assistant. First establish which probability model actually supports each statement; then implement code and experiments under that model. The project is judged primarily by **honest 90%/95% finite-sample coverage, false certification, abstention, and validity-to-utility trade-offs**, not by minimum RMSE alone.

1. Never invent measurements, data downloads, citations, proof steps, theoretical guarantees, or numerical results. Never conceal failed experiments. Distinguish `proved`, `proved only under additional assumptions`, `simulation-validated`, `heuristic`, and `unresolved`.
2. Do not silently change the estimand, condition on future outcomes, leak oracle information into an estimator, call sample-based tuning “certified” without a proof, or select hyperparameters using final-test counterfactual truth.
3. **Do not treat a conflict graph obtained from shared observed identifiers as proof that it captures all stochastic dependence.** It must be a declared sufficient conditional dependency graph, supported by a DGP or model assumption.
4. **Never call a nominal 95% interval a certified CI if its finite-sample constant, moment envelope, nuisance bound, coupling failure budget, or drift allowance is unavailable.** Return `UNVERIFIED_ASSUMPTION`, `NOT_CERTIFIABLE`, or `SENSITIVITY_ONLY`, as appropriate.
5. Logged propensities and target marginal exposure probabilities must describe the **same exposure state**; do not substitute item propensities for joint slate/spillover probabilities. No silent numerical clipping of e=0.
6. Preserve all original source files in version control; use transparent, reviewable patches. Record what changed and why. Keep anonymous submission sources anonymous.
7. Work autonomously using available compute and data. If a large dataset is missing, leave an operational loader, explicit instructions, and a verified smoke fixture, then continue the synthetic work. Never fabricate downloaded dataset results.
8. Every table and figure must derive from saved, machine-readable run outputs and be reproducible from one command. Write technical prose in clear, direct English, with no gratuitous hype.

## Phase 0 — Mandatory mathematical and identification audit **BEFORE** long experiments

Read `main.tex`, `sections/{02_setup,03_method,04_theory,05_discover_repair,06_experiments,appendix}.tex`, the corresponding `sections/full` drafts, and `RESEARCH_TODO.md`. Produce:

- `theory/estimand_contract.md`: exact probability space, conditioning sigma fields, unit/block timing, potential-outcome interpretation, whether target `M_W` is a realized-path predictable average or an unconditional superpopulation average, and what a repair certificate does **not** promise about subsequent closed-loop deployment.
- `theory/assumptions_matrix.md`: rows for local consistency, conditional exchangeability, exposure-mapping completeness, target support, score p-moment, strong conditional graph independence, across-block dependence/coupling, stable versus drifting block targets, frozen policies/auditors, nuisance-training independence, and estimability of radii. Columns: theorem location, required assumption, what data can establish, stress-test, status, and possible repair.
- `theory/proof_gap_report.md`: each disputed mathematical step, severity (blocker/major/minor), explicit counterexample or valid derivation, recommended change, and whether theorem statements must be weakened.
- `theory/theorem_to_code_contract.md`: required estimator parameters, confidence budget, and exact output status that matches each proof.

### Specific proof blockers to investigate, not silently assume away

**P0.1 — Random pathwise target vs block independence.** `M_W` uses history-specific conditional expectations, which are generally random and depend on prior logged outcomes/actions. The appendix conditions on design and cross-fitting training data, then replaces block means by independent copies. This does not automatically preserve their joint relationship with a pathwise target under adaptive feedback. Give a rigorous justification under a precise sigma field **or split the claims**:

- *Theorem A (initial certified implementation):* conditionally independent evaluation macro-blocks given a **legitimate exogenous/pre-treatment design sigma field**, with a fixed or conditionally deterministic window estimand, fixed/frozen auditors/policies, known moment envelope, and explicit block targets. An offline stationary-beta-mixing corollary is acceptable with a correctly derived coupling failure budget.
- *Adaptive prequential extension:* separately formulate a martingale-difference approach with predictable fits/targets and conditional p-moments. Do not apply an independent-block MOM Chernoff proof to arbitrary adaptive blocks. A predictable-truncation/martingale alternative can be a new theorem or honestly labeled research direction.

**P0.2 — Conditioning on nuisance training.** Explain why cross-fitting over overlapping time/entity folds does not make all evaluation block scores independent conditional on the entire collection of fitted nuisances; training sets can contain each other's evaluation outcomes. Prove a valid independence/conditional-moment statement, or use an independent pilot nuisance training set plus fresh certification blocks for the clean theorem. Evaluate practical guarded cross-fitting separately and do not label it certified without sufficient justification. Exact e removes *algebraic* propensity-bias remainder, not leakage or moment problems.

**P0.3 — Moment assumption mismatch.** Section `02_setup` states a window-average conditional raw p-moment, whereas the conflict-graph lemma assumes per-unit conditional centered moments under a common conditioning sigma field. Precisely reconcile them; give a blockwise conditional sum form if more efficient. The centered cross-fitted score requires its own verified moment envelope.

**P0.4 — Explicit CI constants.** Do not leave `C_p` as an unidentified oracle hyperparameter for anything called a numeric 95% certificate. Under a **valid** equal-block independent model, check the following conservative derivation (confirm constants): von Bahr–Esseen <=2 within each color class, graph convexity, another <=2 across independent temporal blocks; thus each MOM supergroup of L complete blocks has centered p-moment <=4*nu_p^p*(chi/(L*n0))^(p-1). Markov threshold `a=(32)^(1/p)*nu_p*(chi/(L*n0))^((p-1)/p)` gives per-group failure <=1/8; a majority Chernoff/Hoeffding bound controls K groups, and union bound handles the finite family. Validate `K=ceil(8 log(2|Theta|/delta_stat))`, `B>=2K`, and do not silently drop excess blocks; either require `B % K == 0`, or rigorously use minimum supergroup size and a target-drift correction. Report the actual, possibly conservative constant and abstention rate.

**P0.5 — Coupling probability is not automatically a numerical radius.** The proof states failure probability `delta_stat + epsilon_coup`, but Section `03_method` writes `r_coup`. Reconcile these: for an advertised total alpha, budget `delta_stat + epsilon_coup <= alpha`, unless a separate proved additive bias/radius bound exists. For beta-mixing only claim valid epsilon from specified, justifiable mixing coefficients and guard gaps. If unknown, report a sensitivity assumption, not a certified value.

**P0.6 — Drift allowance is not automatically observable.** `Delta_W=max_b |M_b-M_W|` involves unknown counterfactual expectations. A fitted proxy is not a high-probability bound. Use a stable-target theorem, a stated `Delta_max` budget, or a separately proved drift-estimation procedure; surface `SENSITIVITY_ONLY` otherwise. If target is a path-average and block means vary, uncorrected MOM can introduce bias.

**P0.7 — Lower-bound proof contains a false inequality.** `sections/appendix.tex` around lines 191–193 asserts `E|X-EX|^p <= E|X|^p`; this is false for general `1<p<2` (e.g. Bernoulli(0.1), p=1.5). Replace the two-point proof by `epsilon=1/(2n)`, `a=nu_p*(2epsilon)^(-1/p)`, `P0=delta_0`, `P1=(1-epsilon)delta_0+epsilon delta_a`. Then `E|X-EX|^p <=2epsilon*a^p=nu_p^p`, mean gap `epsilon a=(nu_p/2)n^(-(p-1)/p)`, and `TV(P0^n,P1^n)=1-(1-epsilon)^n` is uniformly bounded away from 1. Complete Le Cam constants. State scope: exact replication in chi-cliques, not all fixed sparse graphs, and an expected-risk lower bound is not the same as the paper's simultaneous high-probability upper bound.

**P0.8 — Subgroup denominator estimand.** If `h(X,history)` is pre-action observed and the target is the **realized-path empirical window**, `pi_W=N_W^(-1) sum h_u` can be known exactly for binary h (r_pi=0). If targeting a superpopulation subgroup mass `E h`, uncertainty needs a separate theorem and sampling model. Do not conflate them. Support abstention must also account for weak overlap/effective support, not merely nonzero subgroup count.

**P0.9 — Repair scope.** Proposition 05 proves safety for simultaneous moments evaluated along the certified logging-path distribution; it does not prove long-term safety after target policy deployment changes future contexts or feedback dynamics. Rewrite “safe” claims as one-step/logging-path feasibility unless transition dynamics are explicitly modeled. Across repeated epochs, use preallocated delta spending (e.g. delta_epoch=delta_total/(e(e+1)) for epoch e>=1); spell out conditions needed for each epoch's conditional validity.

**P0.10 — Identification of interference and slate exposure.** For a joint action A with local exposure `S=g(A)`, e(s) must be the marginalized probability induced by the full logging assignment. For small slate/candidate examples, enumerate or analytically calculate the true e(s) and compare Monte Carlo frequencies. Never multiply item-level probabilities unless the logging design actually factorizes. Distinguish intervention under a fixed observed history from a full trajectory counterfactual.

**P0.11 — Tail order vs actual tail index.** Finite p is an available moment order, *not* necessarily the exact Pareto tail exponent. If Student-t df or Pareto alpha is strictly greater than p, empirical rates can beat the conservative `-(p-1)/p` guarantee; do not demand equality. Use the Le Cam N-dependent hard family for a minimax rate illustration and label fixed-DGP slope plots descriptive.

**P0.12 — Genuine weak overlap vs uniform conditional score moments.** A conditional per-row envelope `E(|Z_u-E[Z_u|design]|^p | design) <= nu_p^p` with a **nonrandom uniform** nu_p may fail for unbounded `q/e` as `e(X)->0`, even if the *unconditional* p-moment is finite. In the Beta(a,b) example, `E[e^(1-p)]<infinity` does not imply `sup_x e(x)^(1-p)<infinity`. Distinguish (i) an unconditional/annealed graph model with finite integrated p-moment, (ii) a realized-design conditional theorem using explicit possibly data-dependent envelope computed from logged e and bounded Y, and (iii) a truncated weak-overlap design with a fixed positive lower support floor. Do not substitute an integrated moment into a uniform conditional theorem. Demonstrate the gap with an analytic example and tests. If nu depends on N or the realized design, disclose this in claimed rates and figures.

**P0.13 — Source novelty.** Read and compare prior work on adaptive off-policy confidence sequences, unbounded weights, dependent robust means, and uniform MOM; identify precise differences, not just the words “adaptive”, “robust”, or “weak overlap”. At minimum examine: Waudby-Smith et al. (2024, *Anytime-valid off-policy inference for contextual bandits*), Mineiro (2022, *A lower confidence sequence ... heavy-tailed observations*), Høgsgaard & Paudice (ICML 2025, *Uniform Mean Estimation ... via Median-of-Means*), Janson on graph dependence, and relevant mixing-MOM work. Add accurate BibTeX after verification. Acknowledge prior work that handles time-varying means more strongly than the proposed offline MOM theorem.

### Novelty decision after the proof audit

Write `theory/novelty_options.md` choosing one defensible primary technical contribution: (A) adaptive pathwise graph-aware finite-p certificate using predictable/martingale robustification (high-risk research theorem), (B) operational bounded-reward simultaneous graph CI with tighter heterogeneous-graph design effect and explicit computable scale, or (C) provable finite-family counterfactual auditing plus repair in a clearly defined local-interference model. Standard DR+MOM+graph coloring+union bound, a clique replication lower bound, and three-line pessimistic-selection algebra may each be viewed as familiar ingredients; do not present their assembly alone as a strong new theoretical theorem without distinguishing prior work. Document exactly which stronger claim is proved and what remains a proposed extension.

**Hard gate:** Do not mark P0 complete until the initial theorem-supported CI code has an explicit probability model and all required quantities are either proven/known/declared ex ante. It is acceptable to narrow the theorem and separate weaker exploratory results instead of claiming unproved generality.

## Phase 1 — Build a transparent, reproducible Python research package

Suggested layout (adjust to existing repository conventions):

```text
comet/
  data/{schema,synthetic,tgb_adapter,obd_adapter,kuairand_adapter}.py
  {policies,exposure,dr_scores,folds,conflict_graph,robust_mean,
   certification,subgroup_audit,policy_repair,truth,metrics,plotting}.py
configs/{smoke,synthetic_main,synthetic_dependence,synthetic_tails,
         drift,nuisance,discover,repair,tgb,obd,kuairand}.yaml
scripts/{run_smoke,run_synthetic,run_discovery,run_repair,run_tgb,
         run_obd,run_kuairand,aggregate_results,make_figures}.py
tests/...
theory/...
reports/{run_manifest,assumption_check,results_summary}.md
results/{raw,aggregated,figures,tables}/
pyproject.toml
```

### Explicit logged-unit schema

Every row carries: `unit_id`, `round_t`, `block_id`, `subgroup_pre_action`, `features_available_at`, `entity_id`, `slate_id`, `cluster_id` or declared dependence labels, `observed_action`, `observed_exposure_s`, `e_s_logged`, full `e_vector` if available, `reward_y`, `reference_f`, `policy_q_vector`, and a provenance tag explaining the exposure mapping. Include pre-action timestamp ordering. Use a separate **oracle-only** object for full potential outcomes, conditional response functions, moments, latent DGP state, true nuisance functions, and true dependency edges. Audit that estimator code cannot import/use oracle-only truth in real-run mode.

### Initial score and propensity implementation

Start with `S in {0,1}` and a finite stochastic target q. For a logged exposure S:

`psi_q(mu_hat,e_hat) = sum_s q(s)*mu_hat(s) + q(S)/e_hat(S)*(Y-mu_hat(S))`;
`Z(q,h) = h*(psi_q - f)`.

Then implement finite slates and exposure mapping only after unit-tested marginal exposure probabilities. Test `sum_s e_s=1`, `sum_s q_s=1`, finite ratios or explicit support failure, correct h/f timing, exact equality to direct randomized evaluation in simple DGPs, the DR algebra under fixed nuisances, and no hidden target/action mismatch.

### Estimators / baseline matrix

Implement the same fixed scored units, same target, same frozen candidate family, and same seed for:

1. DM, IPS, SNIPS (self-normalized), ordinary DR (sample mean);
2. clipped IPS/DR and switch/truncated DR, with predeclared clipping thresholds and explicit bias caveats;
3. iid-MOM DR, time-block MOM DR, graph-aware sample-mean DR, and full graph-time MOM DR;
4. COMET certified mode with exact e, proven model, known valid p and nu; COMET sensitivity mode with declared budgets; COMET empirical-scale exploratory mode clearly **not certified**;
5. where assumptions match, at least one competitive confidence method based on martingale/anytime-valid OPE or heavy-tail truncation/Catoni-type inference; record when it is inapplicable (e.g. interference, unbounded outcomes, or target mismatch).

Point estimators without a proved confidence bound must be tagged `point_only`. If showing a conventional Wald or bootstrap interval, tag `heuristic_ci`; distinguish nominal level from guarantees. Never present a graph-only/time-only ablation as certified outside its actual assumptions.

### Conflict graphs and folds

- Build edges from **predeclared structural labels** (same random slate, same known cluster shock, declared local interference edge, repeat-entity state known not absorbed by context); no outcome-correlation-based edge learning on evaluation rows.
- Properly color each within-block graph using documented deterministic order and report the actual **number of colors used** `chi_used` (which need not be the chromatic minimum). Compare max degree+1, degeneracy+1, and greedy coloring, and verify every edge crosses color classes.
- Record `raw_N`, `retained_N`, `B`, `n0`, `K`, minimum group length `L_min`, each `chi_b`, `max_chi`, `N_eff=retained_N/max_chi`, guard exclusions, and the count of nodes and edges. The graph bound applies only to the retained units and declared dependency model.
- Build an **independent pilot/fresh evaluation** path for proof-matched experiments. A practical time/entity guarded cross-fit mode is an exploratory comparison until the needed conditional concentration theorem is established. Avoid fitting one fold's nuisance on another evaluation fold if claiming conditional block independence.
- Reject `B < 2K`, `delta_stat <= 0`, missing nu, unproved graph/coupling status, nonpositive support, and target exposure mismatch with explicit diagnostic labels. Never silently weaken confidence requirements or drop data post hoc to make the method work.

### Certificate API

Return a machine-readable object for every `(q,h)`:

`{estimand_id, estimator, estimate, lo, hi, nominal_delta, certified_level,
  status, proof_model, p_declared, nu_p_source, C_p_used, stochastic_radius,
  nuisance_radius, drift_radius, coupling_failure_epsilon, delta_stat,
  subgroup_mass, overlap_metrics, effective_support_metrics, N_eff,
  B, K, L_min, chi_max, assumption_audit, seed}`.

For the clean oracle exact-e, stable conditionally independent model: `nuisance_radius=0`, `drift_radius=0`, `epsilon_coup=0`, unless a different **proven** model is selected. In general keep `epsilon_coup` as error-probability spending, not an invented additive radius. For clipped scores, show the estimand bias or say `heuristic`.

### Computable bounded-outcome envelope option

For binary reward and bounded clipped regression/reference in `[0,1]`, using exact known e and `|h|<=1`:

`|h*(psi_hat-f)| <= 1+q(S)/e(S)`, hence a conservative conditional raw p-moment envelope follows from `2^(p-1)*(1+sum_s q(s)^p * e(s)^(1-p))`. Obtain a centered-moment envelope using a justified centering inequality (e.g. factor `2^p`), and apply it to a valid common conditioning sigma field. This permits a **non-oracle** bounded-reward experiment without assuming an estimated tail scale is an upper confidence bound. If the design conditioning is invalid, mark it unverified. For truly unbounded Y, use a known/declared bound on conditional residual p-moments or a proved upper bound; otherwise sensitivity only.

## Phase 2 — Three-layer synthetic experiment suite

**Layer A (proof matched):** fixed/exogenous contexts or conditionally independent randomized evaluation macro-blocks, known sufficient conflict graphs, exact logging propensity, independent nuisance training, known p moment envelope, stable target. Every claimed theorem coverage plot must include this layer. Use graph replication cliques and explicit independent cluster shocks. This is the mathematical validation bed.

**Layer B (structured, assumption-provided):** dynamic graph streams, known finite-state Markov temporal dependence with proved coupling bound, known local interference and stable/exogenous intervention estimand. Add window drift with a declared valid bound if possible. Do not equate checking observed autocorrelations with proof of mixing.

**Layer C (intentional assumption failures):** omitted conflict edges, permanent shared user random intercept across far-away blocks, hidden common shocks, incorrect slate propensity, trained-on-evaluation nuisances, unknown drift treated as zero, adaptive reuse of certification data, and positivity violations. **These are negative controls**; undercoverage here is evidence of a boundary, not a failure of a theorem whose assumptions are violated.

### Generators and control knobs

Implement at least:

- IID/categorical exposure, equal-size graph clique replication where `chi` is known exactly.
- Structured bipartite graph / dynamic degree-corrected block model (DCSBM); preferential attachment variant for hub stress tests. Keep all actions/candidate sets predeclared and reproducible.
- Weak overlap caused by a `Beta(a,b)` propensity near zero, using a target that gives nontrivial mass to the rare action. The score p-moment requires `E[e^(1-p)]<infinity`; for Beta(a,b), check `a>p-1` analytically. Show scenarios with unbounded ratios yet finite declared p-moment, plus controlled support failure where q>0 and e=0.
- Outcome heavy tails as independent symmetric Student-t with df `nu>p`, or centered/signed Pareto/Lomax with exact finite moments and variance behavior documented. For p=2, choose a distribution with finite second moment. Keep separate controls with bounded Y and near-zero propensity (weight-induced tails) versus strong overlap with heavy Y (outcome-induced tails).
- Independently controlled repeated-entity effects, within-round random cluster shocks, limited interference, and a two-state Markov process with persistence parameter rho. **Do not retain a permanent unobserved random intercept across blocks when claiming separated blocks are independent**; reserve it for Layer C, unless the proof model explicitly handles it.
- A shift point with known change in `mu`, `q`, or context mix; record the exact target per original observed context/history, not a stationary average silently substituted for it.

If Top-K/slates are added, first implement a correct stochastic sampler (e.g. Plackett–Luce with a mixture over *complete slates*). Verify marginal exposure e(s) by enumeration for a small candidate set (M<=6, K<=2), including multi-component neighbor-exposure states. Do not mix a one-item softmax distribution and a distribution over slates without defining a common sample space.

### Fixed experiment grids and resource policy

Create a pilot (`R=50` or `100`) for debugging and a main run (`R>=1000` for the most important 90%/95% coverage and false-certification cells; `R>=300` elsewhere, always show Monte Carlo Wilson intervals). Do NOT do one enormous full factorial grid: preregister a backbone and sweep one or two factors at a time.

Recommended initial backbone:

- Confidence levels: 90%, 95%; finite frozen family `|Theta|=16` (e.g. 4 q by 4 h); K chosen from the **full simultaneous** family, not an individual moment.
- Retained raw N `{8192, 16384, 32768, 65536}`; `B=128` equal-size macro-blocks, `n0=N/B`; graph clique sizes `chi in {1,2,4,8,16}`, ensuring n0 divisible by chi. If proof requires different B, record it and update design. Keep B/K feasibility explicit.
- Available moment orders `p in {1.2,1.5,1.8,2.0}`; generate strictly heavier-than-p distributions in the valid scenarios, and expose the true exponent separately.
- Weak-overlap targets vary behavior exploration `{0.01,0.05,0.1,0.2}`, or Beta shape parameter documented so moment admissibility can be checked; target mixtures fixed before evaluation.
- Within-block graph replication `chi in {1,4,16}` for main plots; temporal persistence `{0,0.5,0.9}` with theoretically bounded coupling budgets or marked sensitivity.
- Four primary regime labels: `strong_e_light_Y`, `weak_e_bounded_Y`, `strong_e_heavy_Y`, `weak_e_heavy_Y`.

Record every seed and the exact exogenous DGP setting. Use deterministic seeds `seed=base_seed+replicate_id` with independent RNG streams for graph, context, logging, potential outcomes, and oracle truth. All methods use identical generated logs for each replication.

### RQ1: Coverage, sharpness, and abstention

For 90% and 95%, show: marginal and **simultaneous familywise** empirical coverage, worst-covered auditor/policy, mean/median interval width, median absolute error, target support, graph design effects, certificate issuance rate, abstention reasons, false-safe certification, and time. Wilson 95% intervals for empirical coverage. **Report both unconditional familywise success and coverage conditional on non-abstention**; never declare coverage=1 simply because no certificates were issued. Acceptance/coverage tests need explicit denominators.

### RQ2: Tail/dependence lower-bound scaling

Use fixed-DGP log–log plots of median absolute error and certified radius against raw N and N_eff, with slope estimates and uncertainty, but do not assert the slope must equal `-(p-1)/p` for an arbitrary fixed Student-t/Pareto generator. Add an **N-dependent hard family** matching the lower-bound two-point construction:

- `n=N/chi` independent clusters, chi identical copies per cluster;
- select P0 or P1 (not revealed to estimators), where `epsilon=1/(2n)`, `a=nu_p*(2epsilon)^(-1/p)`, and P1 is zero except for a with probability epsilon;
- compare maximum absolute estimation risk over P0 and P1, versus `nu_p*n^(-(p-1)/p)`, for n in `{256,512,1024,2048,4096,8192}`, chi in `{1,4,16}`;
- distinguish expected-risk lower bound from high-probability simultaneous CI radius.

The core dependence plot is coverage+width versus chi at **fixed raw N**, then versus N_eff. Demonstrate what is lost by using raw N as though replicated rows were independent.

### RQ3: Component ablations and intentional failure boundaries

With matched seeds vary: raw mean vs MOM; no graph inflation vs valid graph colors; no temporal separation vs justified gap; independent-pilot nuisances vs row-wise/random-fold leakage; exact e vs estimated e and independently imposed nuisance-bias budgets; no drift correction vs stated budget; valid vs incomplete exposure map; fixed p envelope vs unjustified empirical plug-in; ratio denominator known pathwise vs estimated population mass. Include overlap-weighted nuisance errors, not only standard RMSE. **When e is estimated and no bias upper bound exists, output point/sensitivity results only.**

For a two-state symmetric stationary Markov chain with persistence rho, validate or derive `beta(ell) <= (1/2)|rho|^ell` (confirm exact parameterization) and a conservative block coupling epsilon such as `(B-1)*beta(ell)`; do not call the bound certified without checking assumptions. Show guard gap (retained N) vs epsilon and false certification; abstain if total error budget unavailable.

### RQ4: Discover–certify hidden-subgroup auditing

Plant a true subgroup based on an interaction absent from the fixed auditor list, e.g. `group=1 AND degree above a predeclared percentile AND new_user=1 AND observed_pre_action_regime=high`. Tune prevalence to 2–8% so it is detectable; include a smaller 0.2–1% stress slice. Generate true violations (+0.15/+0.30 effects) and a null family with zero violation. Search with a shallow depth-4 tree or predeclared interpretable rules, ranking by discovery-only score; freeze top `L in {1,5,10}` (paid log L penalty). Compare fixed marginal slices, in-sample unrestricted search (invalid baseline), ordinary iid split with leakage, and graph/time-separated discover–certify. Perform discovery, nuisance training, and certification on non-overlapping, proof-compatible data. Report subgroup prevalence, precision/recall or Jaccard against true planted h, signed true effect, discovered score vs fresh score, familywise null false certification, statistical power, abstention, and time-regime replication after shift.

### RQ5: Pessimistic policy repair

Predeclare a finite policy library: baseline logging policy, exploration mixtures, group offsets/thresholds, and 6–20 fixed candidates. Let reward utility be V and safety constraint(s) C_j<=alpha_j, with known oracle truths for synthetic. For two-sided absolute fairness difference, implement two signed one-sided constraints or a valid simultaneous absolute-value bound; do not test just one direction.

Compare utility-only, empirical constraint selection, clipped-DR constraint selection, conservative static baseline, and COMET LCB-utility/UCB-risk selection. Report true V, max_j(C_j-alpha_j)_+, probability any truly unsafe policy certified, feasible/abstention fraction, regret relative to best **robustly feasible** comparator (`C_j+2r_j<=alpha_j`), and frontier versus sample size/overlap/chi. Test that widening confidence bounds cannot silently make unsafe q certified. Show when COMET is safe but too conservative.

Optional multi-epoch stress: log under q_t, certify q_{t+1}, deploy in a simulated state transition model, and separately plot (a) one-step logged-path violations and (b) actual multi-step violations. Explicitly warn that the paper's finite-window guarantee does not automatically imply (b). If claiming simultaneous across epochs, use predeclared delta spending and verify assumptions after every policy change.

## Phase 3 — Real structure and real bandit logs, **after** synthetic correctness

### TGB semi-synthetic

Pin dataset version and official loader. Favor `tgbl-wiki-v2` for manageable graph scale; add `tgbl-review-v2` if resources permit. TGB provides real historical timestamped edges, **not randomized logs with observed counterfactual rewards**. Use its timestamps, node recurrence/degree/candidates as an exogenous backbone; build a transparent randomized exposure policy, and simulate potential outcomes and overlap while preserving real graph structure. Generate truth analytically or using an independent extremely accurate oracle intervention Monte Carlo with reported standard error (<10% of the smallest tested CI half-width). Never mistake TGB negative samples or observed edges for random counterfactual exposure. Compare raw-N and graph-time correction under exactly shared data. If true interference spans blocks, either derive a sufficient graph/coupling or label results exploratory.

### Open Bandit Dataset (OBD)

Start with official 10k-record smoke data, then verified full OBD if accessible. Pin source and schema (`random` vs `bts`, campaign, `timestamp`, `action`, `position`, `reward`, `pscore`, context). The observed pscore is **item-at-position** logging probability under a particular policy; do not treat it as a joint whole-slate e(s) without proof. A Bernoulli Thompson Sampling target action distribution may require Monte Carlo approximation; record this separate approximation error and avoid calling it exact. Compare random→BTS and BTS→random on the **same campaign and aligned positions/time periods**, with propensity/support diagnostics; a separate target-policy on-policy sample mean is a noisy external benchmark, not exact ground truth. Propagate benchmark uncertainty and flag possible population/time mismatch. Treat the natural binary click as a test of importance-weight tails, not heavy Y. Primary OBD outputs: estimate, CI width, target on-policy benchmark uncertainty, gap, standardized gap, ESS, q/e quantiles, certification/abstention, and stability across matched time splits. **Do not report ground-truth nominal coverage from a single noisy on-policy benchmark.**

### KuaiRand (optional P1)

Use documented random-replacement portion and explicit user/time ordering. Only a small fraction of impressions are randomized replacements (official site describes approx. 0.37%); don't infer that every feed item's propensity is known or that random replacement identifies all possible new policies. Binary feedback and watch time should be separate analyses. Chronological/user splits, exposure mapping, held-out intervention scope, and repeated-user dependence limits must be explicit. Stop certification if required propensities or conditional dependence assumptions cannot be justified; exploratory replication/abstention results are still useful.

## Phase 4 — Output expectations: tables, figures, manuscript edits

Create these numbered publication outputs from persisted runs:

- `fig01_coverage_regimes`: 90/95 coverage + Wilson uncertainty across four regimes, including issuance fraction.
- `fig02_dependence_design_effect`: raw N vs N_eff; fixed-N chi coverage and width.
- `fig03_heavy_tail_rates`: fixed-DGP descriptive slopes plus N-dependent Le Cam hard family.
- `fig04_failure_ablation`: no-graph/no-time/no-separation/no-drift negative controls with validity labels.
- `fig05_auditor_discover_certify`: true subgroup, false discoveries under null, held-out certified effects.
- `fig06_policy_repair_frontier`: true violation and true utility, feasible versus abstain.
- `table01_main_results`: RQ1 method comparison, with true nominal and certified/sensitivity/heuristic status.
- `table02_assumptions`: all assumptions, observable diagnostics, and what can/cannot be certified.
- `table03_real_data`: TGB and OBD metrics, distinguish exact semi-synthetic truth from noisy real target.
- `table04_runtime`: score, graph, coloring, nuisance fitting, robust aggregation, memory.

All plots should have legible axes, error bars/intervals, units, and the number of replications. Avoid performance claims based on oracle nuisance inputs unless explicitly labeled oracle. Produce both PDF and PNG figures; keep underlying CSV/Parquet, YAML config, and run metadata.

Patch the LaTeX only after there are real results. Put full protocols, assumption table, failure cases, and theorem derivations in appendix. Main narrative prioritizes: (1) coverage/abstention; (2) graph-time effect and tail rate; (3) discover–certify and repair; (4) external datasets. Remove any claim not backed by a proof or measurement. Preserve original sources and provide a text diff. Do **not** claim full adaptive closed-loop safety from a logging-path moment theorem.

## Testing and scientific invariants

Implement `pytest` tests with deterministic mini examples:

1. Logged q/e score identity and DR expectation with correct e and intentionally wrong mu.
2. DR expectation with correct mu and intentionally wrong e **when conditional independence of nuisance learning is satisfied**.
3. Failure counterexample when mu_hat uses the evaluation outcome (demonstrates invalid leakage).
4. Every exposure probability e(s) matches exact enumeration for small Top-K slate and neighbor assignment.
5. No support: `q(s)>0, e(s)=0` raises explicit nonidentification; never fabricates finite CI.
6. For Beta(a,b) weak e, threshold `a>p-1` checked for finite importance p-moment.
7. Student-t chosen df>p and p=2 requires df>2; no mislabeling p as exact tail exponent.
8. Known chi-clique graph yields `chi_used=chi` with proper coloring; no accidental edge omission.
9. Graph node count equals retained units, not raw unguarded sample count.
10. Exact K/delta budget and `B>=2K` enforced; no dropped leftover blocks unless explicitly justified.
11. Oracle ν_p and explicit C_p reproduce the code's radius formula, with literal numerical fixture.
12. `epsilon_coup` reduces the available failure-probability budget, not secretly added to interval width.
13. Drift unknown gives `SENSITIVITY_ONLY` or abstain, not `CERTIFIED`.
14. In realized-path subgroup ratio, denominator is exact observed pre-action mass; population ratio has separately calibrated uncertainty.
15. Confidence interval is nested/conservative under increasing declared ν_p or drift budget (holding estimator fixed).
16. All candidates chosen by repair satisfy their **reported** UCB constraints; no candidate violates a proved simultaneous constraint on a simulated coverage event.
17. Discover split, nuisance pilot, cert split, and oracle truth are disjoint in declared protected dimensions; no final-test truth in tuning.
18. A negative control with unmodeled permanent entity shocks is not wrongly tagged certified.
19. Le Cam construction central p-moment and TV bound verified numerically over several p,n,chi.
20. Save-and-resume reproduces exact output from same seed/config, including figure data.

Use CI Monte Carlo **diagnostics**, not brittle single-batch assertions that empirical coverage is always >= nominal. Report Wilson uncertainty and flag material/significant undercoverage for review. Include an explicit smoke command that finishes using only synthetic data and CPU.

## Priority and completion gates

**Gate A — proof integrity (must be first):** documents listed in Phase 0; fixed graph-unit and independent-block theorem either validated and patched or tagged unproved; lower bound corrected; computable certificate design agreed in code.

**Gate B — minimal runnable system:** package installs; score/propensity graph and robust CI tests pass; one seed generates logs, oracle truth, and interval without leakage; CLI creates structured results.

**Gate C — rigorous core empirical claims:** four-regime synthetic study, chi/weak-overlap/rate/negative-control plots with Wilson uncertainty; disclose conservative/vacuous interval behavior.

**Gate D — auditing and repair:** held-out hidden-subgroup discovery with null false certification; pessimistic policy library with truth-based safety and utility frontier.

**Gate E — realistic evidence:** TGB semi-synthetic and OBD (provided data and assumptions permit); optional KuaiRand.

**Gate F — paper integration:** figure/table scripts, appendix protocol, updated theorem limitations, verified references, compilation and claim-to-evidence map.

For every gate produce `reports/gate_<letter>_report.md` showing: exactly what was implemented, commands actually run, tests passed/failed, filenames, dataset availability, unresolved proof/data issues, and next decision. Give the user a final concise summary with truthfully completed gates and commands. If interrupted, leave the repo in a reproducible state and prioritize Gate A + B + a small valid coverage study over shallow implementations of every requested feature.

## Reference anchors for literature audit

- Waudby-Smith et al., *Anytime-valid off-policy inference for contextual bandits*: https://arxiv.org/abs/2210.10768
- Mineiro, *A lower confidence sequence for the changing mean of non-negative right heavy-tailed observations with bounded mean*: https://arxiv.org/abs/2210.11133
- Høgsgaard and Paudice, *Uniform Mean Estimation for Heavy-Tailed Distributions via Median-of-Means*: https://proceedings.mlr.press/v267/hogsgaard25a.html
- Open Bandit official project: https://github.com/st-tech/zr-obp and https://huggingface.co/datasets/zozonext/open-bandit
- TGB documentation: https://tgb.complexdatalab.com/docs/ and https://tgb.complexdatalab.com/docs/linkprop/
- KuaiRand: https://kuairand.com/

**Important:** verify every retrieved source and its assumptions and publication details before editing `references.bib`. Do not treat external code/papers as proof that COMET's particular interference or dependence guarantees hold.

# COMET — Gate C0: Non-vacuous certificates before any large experiment

## Context / authority

This task follows **completed Gate A+B**, not a restart. Read the current actual workspace and reports FIRST. The reported snapshots are:

- Experiment repo `lsnnnnnnnn/COMET`, branch `codex/gates-a-b`, reported commit `d11a36f`.
- Paper repo `lsnnnnnnnn/COMET_overleaf`, branch `codex/gates-a-b`, reported commit `df70f48`.
- Local reports `reports/gate_A_report.md`, `reports/gate_B_report.md`, `results/smoke/coverage.md`, `reports/modified_files.txt`, and `reports/commands.md`.
- The owner reports 243 tests passed, both LaTeX documents compile, an explicit lower bound constant 1/8 was proved for the chi-clique replication subclass, and a valid theorem was proved only for the independent evaluation macro-block model. In 30 smoke replications both 90% and 95% familywise coverage were 30/30, with Wilson [0.8865,1], **but every interval covered the entire feasible parameter range**. These are user-reported observations, not independently reverified in this task description.

**Your job is to find an implementable way to obtain useful, mathematically justified, non-vacuous certificates and to diagnose when that is impossible.** It is not your job to maximize coverage by issuing the full feasible range. Preserve the scientific distinction between validity, sharpness, and decision usefulness.

## Hard constraints

1. Stay on a new `codex/gate-c0-informativeness` branch created from the exact Gate A+B state. Verify git SHAs and clean status. Do not rewrite/force-push Gate A+B history or remove previous failed-run logs.
2. **Do not run 1,000 repetitions, real datasets, full factor grids, or extensive GPU jobs.** Start with deterministic algebra + unit tests. Use a CPU-only focused diagnostic, at most ~30–50 replications for a few predeclared cells (total ≤400 new replication-cells until inspected). If even that is not needed, stop earlier.
3. Never call an interval `CERTIFIED` solely because the point estimator and tests run or because it has high empirical coverage. Every numeric radius must map to a proved probability statement and measurable/known/declared inputs.
4. Preserve distinctions: independent exogenous macro-blocks vs arbitrary adaptive paths; exact propensity vs estimated; bounded reward vs heavy-tailed reward; realized-design conditional moment vs unconditional integrated moment; known vs estimated scale; stationary/stable block targets vs nonidentical targets; CI failure probability vs coupling failure probability.
5. Do not select K, clipping cap, tail order, nuisance tuning, a new bound, or an estimator using validation/test outcomes or oracle counterfactual truth and then report unadjusted nominal coverage. All pre-outcome design-based choices must be recorded; outcome-driven selections require an independent pilot or a proved simultaneous adjustment.
6. Every compared method must be tagged `CERTIFIED`, `CERTIFIED_UNDER_DECLARED_ASSUMPTIONS`, `SENSITIVITY_ONLY`, `HEURISTIC_CI`, `POINT_ONLY`, `NOT_CERTIFIABLE`, or an equivalently explicit code-status enum. If no valid assumptions apply, abstain.

## A. Mandatory forensic reproduction (first deliverable)

Open ALL current A+B reports and the actual implementation. Trace the CLI from config to source probability model to scores to MOM grouping to raw radius to feasible-range clipping to exported status. Record precise file/line references in `reports/gate_C0_forensic.md`.

For the existing 30-replication smoke outputs, produce a table for **each** nominal level and each `(q,h)`:

- `raw_estimate`, `raw_radius`, `raw_lo`, `raw_hi`, `feasible_lo`, `feasible_hi`, `clipped_lo`, `clipped_hi`.
- `clipped_width`, `feasible_diameter`, `informativeness_fraction = 1 - clipped_width / feasible_diameter` for positive finite diameters; `is_full_range`, and `is_nontrivial` (with numerical tolerance). A value zero means the interval gives no information beyond support.
- `raw_N`, `retained_N`, `B`, `K`, min/max group block count `L_min/L_max`, number of discarded rows/blocks if any, `n0`, `chi_b`, `chi_max`, `N_eff`, `p`, actual known/assumed `nu_p`, `C_p`, `delta_stat`, `epsilon_coup`, nuisance/drift budgets, exact status.
- per-policy target-to-logging propensity ratios (`q/e`) with min/median/p95/p99/max; graph size; effective support and subgroup prevalence; whether scales derive from a *valid* conditional moment bound.
- `familywise_coverage`, `familywise_nontrivial_rate` (some vs all family members), `marginal_nontrivial_rate`, `median_width_fraction`, `median_raw_radius / feasible_diameter`, `familywise_coverage_given_issued`, and `false_safe_certification` if meaningful. Do NOT drop full-range intervals when calculating coverage; report issuance and conditional performance separately.

Document the single most important causal source of vacuity. Possibilities include moment envelope, Markov constant, `K`, family size, `chi`, small supergroups, insufficient N, ratio support, block count, target range clipping, or accidental double-counting of a correction. Do NOT claim the cause before tracing the code.

If original reports cannot be opened, say exactly why, and generate a fresh diagnostic from the checked-out local code. Do not hallucinate prior logs.

## B. Algebraic informativeness feasibility BEFORE stochastic experiments

Using the **actual code's verified formula**, create an independent calculator in `experiments/nonvacuity_budget.py` with no access to outcomes or oracle truth. It should produce `results/gate_C0/theoretical_radius_budget.csv` and one readable PNG/PDF plot showing estimated sample needs for non-vacuity. Compare the numerical output to small hand-derived fixtures.

For reference ONLY, the first Gate A+B candidate from the original task is

\[
 a=(32)^{1/p}\,\nu_p\left(\frac{\chi}{L n_0}\right)^{(p-1)/p},
 \quad K=\lceil8\log(2|\Theta|/\delta)\rceil,
 \quad L=\lfloor B/K\rfloor.
\]

For `B=128, |Theta|=16, delta=0.05`, the conservative choice yields `K=52, L_min=2`. If `chi=nu=1`, the raw radii for `N=8192,16384,32768,65536` should approximately equal:

- p=1.2: `8.000, 7.127, 6.350, 5.657`;
- p=1.5: `2.000, 1.587, 1.260, 1.000`;
- p=2.0: `0.500, 0.354, 0.250, 0.177`.

These numbers assume the stated constant and no other radius. If the verified implementation differs, explain why rather than forcing it to match this fixture. Note that p close to 1 can make any such bound astronomically conservative.

Invert the actual radius expression to calculate the *theoretical N required* for, e.g., raw radius <=25% of the parameter-range diameter, separately by p, known nu, chi, family size, and group count. Label this as a **sufficient condition for a particular bound**, not a minimax sample-complexity lower bound. For ratios, include denominator-small and zero-support abstention independently from CI width.

## C. Primary theorem-preserving improvement: exact binomial MOM majority bound

**This is the first improvement to investigate and, if the proof checks out, implement.** Current sufficient choice `K=ceil(8 log(2m/delta))` is deliberately conservative. Assume that conditional on legitimate exogenous design/pilot information: (a) supergroup errors are independent, (b) each group's probability of exceeding a common threshold is <= eta, where 0<eta<1/2, and (c) every group is centered at the SAME target as required by the stable-target theorem. Then

\[
 \Pr\big(|\operatorname{MOM}-M|>a\big)
 \le \Pr\{\mathrm{Bin}(K,\eta)\ge \lceil K/2\rceil\}.
\]

The familywise failure probability is at most `m * binom.sf(ceil(K/2)-1,K,eta)` for a finite, *frozen* family of size m. With eta=1/8, m=16, delta=.05, a sufficient odd K is **9** because `16*Pr(Bin(9,1/8)>=5)≈0.03972<.05`; the old conservative recipe uses K=52.

You must PROVE this replacement carefully before modifying certified code:

1. Establish the exact per-supergroup p-moment bound (including the correct constant) conditional on one legitimate sigma-field, not a future-outcome-dependent sigma-field.
2. Markov: if moment bound is `A_p nu_p^p (chi/(L*n0))^(p-1)`, choosing `a=(A_p/eta)^(1/p) nu_p (chi/(L*n0))^((p-1)/p)` gives per-group bad probability ≤eta. `A_p=4` and `eta=1/8` recover `(32)^(1/p)` **only if** the Gate A proof actually supports `A_p=4`.
3. Independence of bad-group indicators conditional on the design must be justified. The stochastic domination by Bin(K,eta) does not require identical distributions, only independent indicators with individual upper probabilities <=eta.
4. For an even K, define the median and exactly check the majority condition; preferably restrict the new selector to odd K for simplicity.
5. The available `B` and group partition must meet proof feasibility (`L_min>=2` if the existing model requires it). Distribute leftovers deterministically. Because all group means must have the same target, unequal **group sizes** can be acceptable under stable targets when variance is bounded by `L_min`, but this must be proven. Do not silently discard rows and continue to call the original estimand unchanged.
6. Choose K via the exact `scipy.stats.binom.sf` or stable log-tail arithmetic, with independent high-precision small K numerical fixtures. Set `K` from m, delta, eta, B before looking at evaluation outcomes. If no feasible K exists, emit a non-certifiable status.
7. Add a reproducible `mom_majority_rule = conservative_hoeffding | exact_binomial` switch; preserve the old certified mode as a frozen baseline. Record eta, K, binomial familywise failure bound and resulting common radius.
8. FIRST compare **fixed eta=1/8**. Only afterward investigate a fully preregistered deterministic optimization of eta and odd K minimizing the proved radius given exogenous known p, nu, chi, B, n0; prove conditional validity of the selection rule, or pay a union bound. Never choose via realized coverage or oracle truth.

Make `theory/exact_binomial_mom.md` a full lemma/proof and give a copy-pastable LaTeX theorem patch in `reports/gate_C0_paper_patch_suggestion.tex` (do not silently rewrite manuscript-wide claims yet).

## D. Secondary valid alternative: graph-aware variance certificate for bounded outcomes

The heavy-tail MOM should stay primary for p<2 where finite variance is unavailable. However, in a **separately labeled bounded-Y experiment** with exact logged e, independent exogenous blocks, frozen q/h, independent/predictable outcome-regression fits, `Y(s)` and `mu_hat(s)` in [0,1], and pre-action fixed h, consider an alternative rigorous p=2 baseline.

For unit u, with `w_u(s)=q_u(s)/e_u(s)` and `h_u` measurable before action, let `Z_u=h_u(psi_u^q(mu_hat,e)-f_u)`. Conditional on a valid exogenous design sigma-field D,

\[
 \operatorname{Var}(Z_u\mid D) \le
  v_u=h_u^2\sum_{s:e_u(s)>0}\frac{q_u(s)^2}{e_u(s)}.
\]

This follows by subtracting the predictable direct-method component and bounding the outcome residual by 1. Verify all conditions, including nonnegative q and correct exposure-state probabilities. Under a genuine conditional dependency graph with proper coloring `chi_b` within each block,

\[
 \operatorname{Var}\big(\sum_{u\in b}Z_u\mid D\big)
 \le \chi_b\sum_{u\in b}v_u.
\]

The proof colors the graph and uses variance additivity within independent color classes and Cauchy-Schwarz across the color sums. For conditionally independent blocks, let

\[
 \hat M_{\rm mean}=N^{-1}\sum_{u=1}^N Z_u,
 \qquad V_\theta=N^{-2}\sum_b\chi_b\sum_{u\in b}v_u.
\]

If D is legitimate (not conditioned on future adaptive contexts), the exact propensity removes the nuisance *expectation* bias and the realized-design target equals `E[hat M | D]` even if different blocks have different expectations. Conditional Chebyshev + union bound yields a simultaneous certificate

\[
 |\hat M_{\rm mean}(\theta)-M_D(\theta)|
 \le \sqrt{\frac{|\Theta| V_\theta}{\delta}}
 \quad\text{for all frozen }\theta\in\Theta
\]

with probability at least 1-delta conditional on D. This is a **different theorem/estimator** and must not be presented as proving the original fully adaptive pathwise claim. Heterogeneous means are permitted under the independent-exogenous-design conditions; group-median drift correction is not needed for the *sample mean* target.

Important checks:
- If q(s)>0 and e(s)=0, signal nonidentification instead of inventing a finite variance bound.
- A small realized e can make V enormous: the bound is still valid given the design, not necessarily useful. Distinguish support positivity from a uniform overlap floor.
- For graph dependence across blocks, neither independence nor variance additivity follows from within-block coloring; reject certification unless proved.
- If graph labels miss a shared shock, treat this as a failure-model negative control, not a certified guarantee.
- If Y can be outside [0,1], this variance formula no longer follows; retain the known finite-p MOM or sensitivity path.
- Use exact *marginal exposure-state* e(s), including correct joint-slate derivation when S is induced by a joint assignment.

Implement as a separate `bounded_graph_chebyshev` certified method only after proving and testing `theory/bounded_graph_variance.md`. This will be a stronger practical baseline and may be a useful theorem-side addition. Do not imply that Chebyshev + graph coloring by itself is a major novel theorem.

### Optional variance/bias-aware clipping, only after the previous proof passes

For a deterministic cap c>0, use `w_c(s)=min(q(s)/e(s),c)` with the same bounded-reward/exact-e setting. The clipped score **is biased** for the original target unless mu_hat is correct. A valid worst-case absolute bias budget is

\[
 b_c(\theta)=N^{-1}\sum_u |h_u|\sum_s (q_u(s)-c e_u(s))_+.
\]

Prove this explicitly from the expectation of the clipped DR score and `[0,1]` residual range. A valid variance envelope is `v_u(c)=h_u^2 sum_s e_u(s) min(q_u(s)/e_u(s),c)^2`. Combine the *proved* stochastic radius and `b_c`; never clip the weight without paying this bias. Reject q>0/e=0 as outside point identification even if a coarse partial-identification interval exists.

Choose c from a frozen grid with an appropriate simultaneous confidence budget, or by a pilot/design-only rule proved legitimate; do not use certification outcomes or oracle truth to pick c without adjustment. Keep labeled results for both variance gain and bias price. Implement only if this increases rigor and remains inside budget; otherwise provide the proof + proposed design without code.

## E. Tiny predeclared informativeness pilot (not the paper's coverage study)

Only once the above proofs, tests, and deterministic feasibility calculator pass, run a focused synthetic check. Start with no graph dependence, exact e, bounded Y, p=2, q=e or moderate mismatch, |Theta|=1 and 16, N=8192 and 32768, B=128. Test the two MOM K rules, trivial feasible-range CI, and (if proved) bounded graph Chebyshev. Then add a small controlled `chi=4`, a weak-e bounded-Y cell, and a p=1.5 or p=1.2 known-envelope stress cell if feasible. Up to 30–50 independent replicates per *few* selected configurations; overall total ≤400 replication-cells. No external datasets.

Persist a *preregistered* config **before running the outcomes**. Report all selected cells, not only successful ones. Do not alter DGP after observing the result without recording the change as a separate exploratory run. For every method show:

1. 90/95 simultaneous family coverage + Wilson intervals (debugging only at this R).
2. Median and p90 CI width divided by feasible diameter, raw half-width, familywise/marginal nontriviality, unresolved/abstention fraction, false-safe count.
3. Absolute error, oracle truth definition, valid p/envelope construction, observed q/e quantiles and score-tail diagnostics, chi, B, K, L_min, effective sample size and compute time.
4. Exact status as `CERTIFIED` only under matching assumptions; if one baseline is not valid for a cell, output `NOT_APPLICABLE`, not a fake interval.
5. A Pareto plot of interval informativeness versus sample size / graph cost; do not make a paper claim from 30 replicates.

### Negative controls (quick unit or micro-simulation)

Include a hidden permanent shared shock across blocks, a false dependency graph missing edges, a nuisance trained on evaluation outcomes, a zero-support target, a p-moment violation, and an outcome-driven selected K/c without multiplicity adjustment. Each must either be detected/refused by certification guards or explicitly tagged as an assumption-violating negative control. Do not expect the algorithm to detect every hidden assumption failure from observed logs; record this limitation.

## F. Testing requirements

In addition to preserving the 243 previously passing tests (or identifying every intentional modification), add deterministic tests for:

- Exact binomial tail `K=9` for m=16, delta=.05, eta=1/8; old conservative K=52; valid conditional group bad-event domination logic in the documented proof.
- Minimal odd K around thresholds across m and delta, numerical stability at small delta, infeasible K/B, and honest handling of B mod K.
- Group mean target alignment for stable blocks; reject or debit varying-block-target MOM cases without a valid drift budget.
- Both `raw` and `support_clipped` intervals are stored, with full-range width classified as 100% vacuity even if observed coverage is 100%.
- Numerical graph variance fixture for a clique and for an independent edgeless graph; no `chi` lower than an independently verified valid coloring.
- Small categorical/Top-K enumeration verifying e(s) and `sum_s q(s)=sum_s e(s)=1`.
- Exact-e + arbitrarily misspecified frozen outcome regression: unbiased expected DR score and proven variance envelope hold.
- Clipped weight at fixed c: expected score bias equals the derived nuisance-weight product, with its absolute value below b_c in an analytically enumerable example.
- Graph/block variance formula rejects outcome-dependent nuisance fits, uncontrolled between-block dependence, future-outcome-dependent D, Y outside [0,1], and positivity failures as certified mode.
- Same seed/config reproduces raw data summary, intervals, CI-status, and plots.

Do not write stochastic tests requiring empirical coverage >= nominal on 30 replications. Tests should check mathematical and implementation invariants, not low-power simulation luck.

## G. Do NOT prematurely make the fully adaptive claim

The current independent-block theorem does **not** automatically cover a future-context-conditioned adaptive window. The next theoretical research direction, after Gate C0, is a **predictable martingale / bounded clipping with an explicit bias budget**, perhaps graph-adjusted conditional variance under within-round dependence. That may remove the stable-target/MOM issue for the fully adaptive predictable target. If proposing this, document:

- pre-action filtration and per-round conditional expectation;
- randomization and graph dependency conditional on that filtration;
- a valid predictable nuisance estimator and target q/h;
- a deterministic bound or a rigorously proven self-normalized/peeling rule for any random predictable variance process;
- a truncation bias bound under known conditional p-moments;
- union probability accounting across policies, auditors, time windows, and hyperparameters.

**Do not substitute a random realized predictable variance into a fixed-variance Freedman inequality without proving that self-normalized bound.** Do not claim graph/color corrections over adjacent adaptive rounds imply independent blocks. This is a future `Gate C1` theory task; avoid scope creep in C0.

## H. Required deliverables and pass/fail decision

Create:

- `reports/gate_C0_forensic.md`: precise diagnosis from actual smoke output and source lines.
- `reports/gate_C0_theory_decision.md`: which refinements are fully proved, what assumes exogenous design, and what remains unproved; advice on whether to keep heavy-tail MOM as headline or pivot to a sharper bounded-outcome/adaptive theory.
- `theory/exact_binomial_mom.md` (full proof) and, if implemented, `theory/bounded_graph_variance.md`.
- `results/gate_C0/theoretical_radius_budget.csv` and plot(s).
- `results/gate_C0/pilot.csv` plus a human-readable table explicitly showing **coverage AND informativeness**; one config/seed manifest, run commands, and failure logs.
- `reports/gate_C0_paper_patch_suggestion.tex` (suggested changes only, annotated assumptions).
- `reports/gate_C0_report.md`, `reports/gate_C0_commands.md`, `reports/gate_C0_modified_files.txt`; git commits on the new branches with exact SHAs and clean status.

Declare **PASS for Gate C0** only if (i) a new radius is proved under an explicit legitimate model, (ii) a strictly nontrivial interval is possible in at least one *predeclared* useful bounded-Y/exact-e scenario without oracle-truth selection, (iii) no valid-status inflation occurs in inapplicable scenarios, and (iv) the existing tests plus new ones pass. Passing C0 does NOT establish empirical nominal coverage or justify final paper claims; it merely unlocks the full Gate C study.

If every rigorous route remains vacuous in the predeclared easy setting, give an honest **NO-GO** for 1,000-repetition coverage and recommend the next theory redesign. It is acceptable for extreme weak-overlap/heavy-tail settings to abstain; this must be disclosed as a meaningful support/tail limitation, not hidden as a success.

In your final response to me, state: exact repo SHA(s), the confirmed cause of smoke vacuity, old/new certified K and radius, pilot width vs trivial range, remaining proof gaps, test counts, and a GO/NO-GO decision on full Gate C. Do not claim code was run unless logs prove it.

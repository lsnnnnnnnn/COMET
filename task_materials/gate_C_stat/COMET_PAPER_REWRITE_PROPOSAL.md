# COMET Paper Rewrite Proposal — scope-correct, reviewable plan

This is **a proposed narrative and passage draft, not a manuscript with newly observed results**. Verified experiments code: `lsnnnnnnnn/COMET` scientific commit `ab4c74fb...`, evidence commit `06a39b89...`; Overleaf `COMET_overleaf` was not accessible for independent verification. Avoid direct synchronization until the right source is accessible.

## Best paper thesis at the currently proved scope

> Can we issue simultaneous, explicitly computable counterfactual moment certificates from randomized logged exposures when evaluation records are dependent within known graph clusters and effective overlap may be poor? We provide separate finite-p robust and bounded-reward variance routes, quantify when certificates are too broad to decide, and use the same certified event to justify held-out subgroup auditing and local constrained policy selection.

**The last downstream portion is a *proposed application* until D-stage experiments are implemented.** Be careful to distinguish existing eventwise algebra from experimentally demonstrated reliability.

## Candidate title

**COMET: Counterfactual Moment Certificates under Weak Overlap and Block Dependence**

Alternative: **COMET: Simultaneous Counterfactual Auditing with Graph-Dependent Logged Data**

The current "Dependent Feedback" title should be avoided for a submission limited to independent exogenous macro-blocks, unless a separate valid adaptive-history result is proved.

## Proposed Abstract — conservative on unrun experiments

Logged recommendation and decision systems often contain correlated observations and rare exposures. These features make off-policy estimates unreliable precisely when they are used to test subgroup disparities or certify constraints. We study simultaneous inference for a finite family of counterfactual moments under a transparent design: logging propensities are known, target policies and auditors are fixed before evaluation, macro-blocks are independent, and within-block dependence is described by a sufficient conflict graph. We provide two complementary certificates. A median-of-means construction requires only a known conditional finite-p moment envelope and admits an exact-binomial choice of the number of groups; a separate graph-aware variance certificate yields tighter intervals for bounded outcomes. Both account explicitly for graph inflation and preserve coverage over the full family under their stated assumptions. We also show a minimax expected-risk lower bound for a clique-replication subclass and derive local feasibility guarantees for pessimistic selection on a simultaneous-coverage event. The approach separates statistical validity from practical informativeness: weak overlap and heavy tails may lead to abstention rather than unsupported safety claims. Extensions to fully adaptive feedback, mutually trained nuisance models, and long-run deployment remain open.

**After C-STAT and D experiments**: replace a sentence or two with measured results, stating the actual numbers including negative F/E findings; do not claim preflight coverage is confirmation.

## Section-by-section structural rewrite

| Source | Current obstacle | Required rewrite |
|---|---|---|
| `paper/main.tex` abstract | Claims robust adaptive, time-coupled, cross-fitted deployed-feedback inference | Replace with proved conditional exogenous-block scope and two methods; remove preceding Gate-A disclaimer by making the actual main text valid |
| `sections/01_introduction.tex` | Contributions include unproved adaptive and cross-fit methods | Open on coverage vs usefulness; identify finite-family and abstention, separate aspirations in Limitations |
| `sections/02_setup.tex` | Predicted history target `M_W` is primary though main proof targets `M_D` | Make `M_D` primary; define sigma-field D, assignment/exposure law and joint target Q; pathwise target later |
| `sections/03_method.tex` | Generic unimplemented radius C_p * estimated ν_p + nuisance/coupling/drift and guarded cross-fitting | State actual fixed/independent-pilot nuisance, exact e, finite-p MOM, exact K and graph variance as distinct procedures; precise refusal states |
| `sections/04_theory.tex` | Unproved adaptive theorem still has theorem environment even while labeled unproved | Remove that theorem; elevate proved main theorems; attach lower bound to replicated-clique expected-risk subclass |
| `sections/05_discover_repair.tex` | Downstream story still algorithmically proposed | Keep deterministic proposition under simultaneous event; require frozen family and independent discovery; state missing experimental proof and fallback |
| `sections/06_experiments.tex` | A plan of DCSBM/PA/TGB/Open Bandit/KuaiRand as if results | Insert only real frozen confirmatory figures after C-STAT; follow with new D stages; don't represent unrun datasets as empirical support |
| `sections/07_related_work.tex` | Overclaims originality of standard components | Discuss existing OPE confidence sequences, finite-p uniform MOM, overlap/truncation and dependence graph approaches; clarify distinct contribution |
| `sections/08_conclusion.tex` | Broad long-run robustness implications | Match proof scope and observed outcomes; explicit abstention and limits |

## Main theorem and estimator placement

**Main theorem A: finite-p robust.** State D, independent blocks, sufficient graph coloring χ, stable per-block target, exact e, frozen q/h, fixed/independent-pilot nuisance, known conditional centered moment ν_{θ,p}^p. The finite-family simultaneous certificate is

\[
 \widehat M_\theta=\operatorname{median}_{g=1}^K \bar Z_g(\theta), \quad
 r^{\mathrm{MOM}}_\theta = 32^{1/p}\nu_{\theta,p}
 \left(\frac{\chi}{L_{\min}n_0}\right)^{(p-1)/p}.
\]

Use K from the exact-binomial majority condition `m P(Bin(K,1/8)>=ceil(K/2))<=δ`, odd K, B>=2K. Retain conservative historical K as a baseline; no claimed novel adaptive concentration.

**Main theorem B: bounded graph variance.** Conditional variance envelope and independent block additivity give

\[
V_\theta=N^{-2}\sum_b\chi_b\sum_{u\in b}h_u^2\sum_s q_u(s)^2/e_u(s), \quad
r^{\mathrm{GV}}_\theta=\sqrt{mV_\theta/\delta}.
\]

This covers heterogeneous exogenous block means under bounded outcomes; it does not cover heavy-tail F. Show it as a separate estimator, not an empirical choice among multiple CIs.

**Lower bound.** For N/χ independent clusters copied χ times, known centered p-moment envelope, an expected absolute-error minimax lower bound is `ν_p/8 (χ/N)^((p-1)/p)`. It is not a high-probability CI lower bound and does not cover all sparse graphs.

**Repair.** If every candidate q and all costs/utility moments have a valid simultaneous event and the algorithm selects q satisfying `UCB(C_j(q))<=alpha_j`, then local fixed-design feasibility follows; compare utility to a safely separated robust-margin comparator, not any unconstrained post-deployment policy. Absence of a certifiably feasible q implies abstention or a separate truly safe fallback.

## Table and figure structure after actual results

1. **Table 1—Assumption and method applicability**: MOM, exact MOM, graph variance, IPS/DM/DR point, full-range, bounded vs heavy; do not hide NA.
2. **Figure 1—Main coverage**: 95% family coverage successes/1000 and Wilson intervals, 17 Holm diagnostics, with 90% separately.
3. **Figure 2—Information utility**: width/feasible range, fraction nonvacuous, abstention across A–F, including negative E/F.
4. **Figure 3—Dependence/overlap**: χ and q/e spectra and effective sample size, comparisons with no-graph exploratory CI.
5. **Figure 4—Discovery / certificate power** (after D1/D2, only with independent pilot and confirmatory): power vs gamma/r, subgroup size, Type I errors.
6. **Figure 5—Policy repair** (after D3): true utility vs true constraint violation, false-safe and abstention. This is what differentiates the paper from a confidence bound tutorial.
7. **Appendix**: full proofs, exact group-selection code and known moment envelope derivations, Le Cam subclass, negative controls, seed manifest, model/schema guards, separate empirical prototype details.

## Publication strategy warning

All main concentration arguments use standard tools (exact-e DR, von Bahr–Esseen, MOM, coloring, Chebyshev/union). The independent-block model and frozen `m=16` family alone are unlikely to sustain a broad methodological novelty claim. For a more compelling conference paper, demonstrate actual discover–certify–repair tradeoffs with correct error control, add non-duplicated shared-slate or graph primitive dependence with a sufficient-graph proof, or prove a genuinely adaptive martingale certificate. Until then, honest narrower framing is preferable to inflated claims about deployment-stable feedback.

## Literature crosswalk (verify bibliographic entries before writing)

- Karampatziakis, Mineiro, Ramdas, "Off-Policy Confidence Sequences", ICML 2021, https://proceedings.mlr.press/v139/karampatziakis21a.html
- Høgsgaard and Paudice, "Uniform Mean Estimation for Heavy-Tailed Distributions via Median-of-Means", ICML 2025, https://proceedings.mlr.press/v267/hogsgaard25a.html
- Mehrabi and Wager, "Off-Policy Evaluation in Markov Decision Processes under Weak Distributional Overlap", arXiv 2024, https://arxiv.org/abs/2402.08201
- Shimizu et al., "Effective Off-Policy Evaluation and Learning in Contextual Combinatorial Bandits", RecSys 2024, https://arxiv.org/abs/2408.11202

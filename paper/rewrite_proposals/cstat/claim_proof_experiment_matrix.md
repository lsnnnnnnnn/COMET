# Claim-to-proof-to-experiment matrix

Source line references are to experiment commit
`06a39b89e579aef57d14ae51e86d74ecf9b6b768`; scientific module contents agree with
freeze `ab4c74fbf1ae84c0e5ffd72d77ce5b48d3fba8cb`. Proposed file references are
relative to `overlay/`. The proposal is not an edit of the archival manuscript.

| Claim / original location | Proposed disposition | Proof / implementation anchor | Evidence and limits |
|---|---|---|---|
| Broad adaptive, cross-fitted, coupled/drifting certificate; `paper/main.tex:62`, `sections/01_introduction.tex:8,22`, `03_method.tex:6–12,41–59` | Replace abstract/introduction/method with the independent exogenous-block contract. | `sections/gate_a_certificate.tex:14–61`; `theory/theorem_to_code_contract.md`; `comet/gate_c_contract.py:127`. | The six frozen cells implement fixed nuisance and independent clusters/blocks. No empirical adaptive, cross-fit or learned-e inference claim. |
| Pathwise realized-history target; original `02_setup.tex:27–33` | Main target becomes M_D. M_path appears only in the proposed appendix's open extensions. | `theory/gate_c_heavy_tail_contract.md`, sections “Frozen design” and “Potential outcomes”; `comet/gate_c_truth.py:13`; `gate_c_simulation.py:50`. | Conditional analytic target evaluated after methods; never substitute an unconditional population target or realized potential outcomes. |
| Exposure / support; original `02_setup.tex:4–21` | State exact pushforward of the joint logging law and require a joint target Q for policy-value interpretation. Otherwise call q an exposure-marginal functional. | Exact DR calculation; `comet/gate_c_methods.py:69`; binary sampling `gate_c_simulation.py:21,50`. | C-STAT uses S=A, not a real slate. Compatibility of arbitrary local q under a constrained slate remains a D4 proof gate. |
| Generic finite-p guarantee; original `04_theory.tex:30–46` | Remove `thm:uniform-comet` entirely. Elevate `thm:gate-a-clean` as main theorem and give proof with explicit 32^(1/p). | `paper/sections/gate_a_certificate.tex:54–130`; `comet/robust_mean.py:22,123,135,142`; `gate_c_methods.py:129,154`. | Requires stable block targets, known conditional envelope, full grouping and B≥2K. Passing schema checks does not prove a real dataset satisfies these assumptions. |
| Exact-binomial improvement | Add separate main theorem, smallest feasible odd K with exact tail; same radius constant. | `theory/exact_binomial_mom.md`; `comet/robust_mean.py:58,87`. | Pre-outcome selection, η=1/8, full family. Does not address varying targets or adaptive choice of η/K. |
| Bounded graph certificate | Add separate graph-aware ordinary-mean theorem and full variance argument. | `theory/bounded_graph_variance.md`; `comet/bounded_variance.py:16,38`; `gate_c_methods.py:171`. | Stable block means unnecessary mathematically; requires actual independent blocks and bounded outcomes. F remains NOT_APPLICABLE. |
| Known finite-p scale and weak overlap; original `02_setup.tex:63–73`, `03_method.tex:70–71` | Report model-supplied conditional scales; remove advertised empirical tail tuning. | `gate_c_contract.py:93,104`; `theory/gate_c_heavy_tail_contract.md`, moment derivation. | Finite-p ideal Pareto F has known parameters. Ordinary float simulation is distinguished from a literal infinite-variance machine distribution and exact outward rounding. |
| Subgroup denominator; original `03_method.tex:61–68`, `04_theory.tex:50–53` | Known fixed-design mass, positive-mass division only. | `paper/sections/gate_a_certificate.tex:197–203`; `gate_c_methods.py:40`. | No estimated-mass/superpopulation ratio guarantee. Mass zero refuses the ratio. |
| “Matching” dependence-tail lower bound; original `01_introduction.tex:22`, `04_theory.tex:55–66` | Explicit ν_p/8 expected-risk bound for exact χ-clique replication; remove generic graph/high-confidence sharpness prose. | `theory/lower_bound.md`; corrected `paper/sections/appendix.tex:191–222`. | ε=1/(2n), a=ν_p(2ε)^(-1/p), centered moment≤ν_p^p, TV≤1/2. An n-dependent minimax construction, not a prediction for fixed F. |
| Discover–certify; original `05_discover_repair.tex:4–11` | Independent pilot only, freeze all selected tests, pay full policy×auditor×constraint multiplicity. | Conditional finite-family theorem, conditioning on an independent pilot. | Eventwise validity is justified; learned discovery effectiveness has not been tested by A–F. D2 remains future. |
| Repair / long-run safety; original `05_discover_repair.tex:13–37` | Retain and prove eventwise local feasibility and the 2r robust-margin comparator; state empty-library abstention. | Proposed `05_discover_repair.tex`, complete deterministic proof; original simultaneous-event algebra `05_discover_repair.tex:14–35`. | Utility and all costs need a common simultaneous budget. No future path guarantee and no D3 performance results. |
| Planned dynamic / real-data studies; original `06_experiments.tex:4–45` | Replace with an explicitly pending frozen A–F results section and unrun D1–D5 plan. | Frozen config and seed manifests; existing `reports/gate_C_report.md:79–85`. | No confirmatory numbers inserted until validated complete C-STAT. Preflight is debugging evidence and is excluded from all confirmatory denominators. |
| Novelty claim; original `07_related_work.tex:5–11` | Four verified source comparisons and explicit distinction from standard components. | `bibliography_crosswalk.md` and added BibTeX. | Scope-correct exposition alone does not establish competitive methodological novelty. |

## Exact differences in theorem domains

- All claims condition on a legitimate exogenous design and optional independent
  pilot. Neither future adaptive contexts nor mutually evaluation-trained fits
  can be included merely to make them “fixed.”
- MOM needs every block to share the same conditional target. The graph-aware
  mean does not. These are different estimators, not interchangeable proof
  labels attached to a selected interval.
- A conditional p-moment envelope can depend on the design. Unconditional
  integrability does not give a uniform envelope across histories/designs.
- The fixed conditional-mean class [0,1] provides F's target range, whereas
  graph variance needs the stronger bounded-outcome condition. This distinction
  is explicit in the proposal.
- Coupling failure, if ever proved in a new model, contributes to a failure
  probability budget. The proposed executable algorithms contain none of the
  unproved nuisance, coupling or drift additions from the original radius.

## Acceptance checks for eventual adoption

The proposed main and appendix contain no theorem labeled `thm:uniform-comet`,
no operational mutually cross-fitted certificate, no invented C-STAT number,
and no claim of tested real-slate exposures or long-run safety. Original paper
files and full working versions remain unchanged. The final phase audit, not
this writing proposal, determines whether the frozen C-STAT result may be used.

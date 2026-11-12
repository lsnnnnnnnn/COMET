# Gate A — completed for the explicitly restricted model

The whole 290-line master task was read. Its future experiments were treated as
the research roadmap; the user's request restricted this run to Gates A+B.
All requested compact/full LaTeX sources and RESEARCH_TODO were inspected.
Original ZIP checksums are in `source_manifest.json`, and commit `58ad7bd`
preserves every original source. Audit references use that baseline's lines.

## Delivered

- `theory/estimand_contract.md`: probability space, pre-action fields, target
  distinctions, graph construction, full conservative proof and deployment scope.
- `theory/assumptions_matrix.md`: assumptions, source locations, what data can
  establish, stress tests, proof status and mathematically valid repairs.
- `theory/proof_gap_report.md`: explicit adaptive/cross-fit/moment/bias/coupling
  counterexamples, subgroup/exposure issues, and precise recommended patches.
- `theory/theorem_to_code_contract.md`: proof constants, supported model,
  delta/grouping rules, machine-readable status and API obligations.
- `theory/novelty_options.md`: verified prior work and option C as a research
  direction, without claiming that standard DR+MOM+coloring is itself new.
- `theory/lower_bound.md` and `theory/verified_references.bib`.
- `paper/sections/gate_a_certificate.tex`: complete independent-block theorem
  and proof, incorporated in both appendices. Both entry points and both theory
  sections explicitly mark the broader adaptive/cross-fit statement unresolved.
- Both appendix lower bounds corrected without changing their mathematical
  theorem statements. Original invalid centering is replaced by the exact
  centered moment, epsilon=1/(2n), a=nu_p(2epsilon)^(-1/p), TV<=1/2 for every
  n>=1, and the common-measure Le Cam lower bound with constant 1/8.

The clean theorem uses an exogenous conditioning field, independent macro-blocks,
a sufficient conditional dependency graph, stable targets, frozen family,
fixed nuisances/exact e, and known centered score moments. The explicit
`32^(1/p)` MOM constant and complete-block grouping are proved. A bounded-reward
envelope supplies the required known moment without using oracle response means.
This narrowing addresses missing probability-model assumptions; it is not a
change made simply to ease implementation.

## Validation and actual results

The final pytest run passed **243 tests, 0 failures**, including exact finite-space
counterexamples and 180 parameterized Le Cam moment/risk-constant checks. The
small finite-n product-law TV tests enumerate every sample. The initial and final
unit-test runs had no failures; review-found implementation issues are documented
in Gate B. The smoke CLI initially failed after editable installation; that
environment issue was fixed and is fully recorded in Gate B and commands.md.

Both final latexmk commands exited 0. Current compact/full PDFs have 18/23 pages
including appendices. Final logs have no undefined references or overfull boxes;
existing underfull boxes remain. These are working drafts, not submission-layout
certification. Original checked-in PDFs remain unchanged. Commands and raw logs
are in `reports/commands.md` and `reports/latex/`.

## Proof gaps that remain open

1. Arbitrary adaptive pathwise targets need a separate filtration/martingale
   theorem; independent-block MOM cannot be substituted.
2. Mutually trained cross-fits can create unconditional score dependence and
   dependence after conditioning on every fitted nuisance.
3. Integrated finite-p moments under unbounded q/e do not supply a uniform
   realized-design conditional envelope. The initial bounded fixed-design
   implementation does not establish the paper's full weak-overlap program.
4. Evaluation-driven tail estimates and nuisance/drift estimates require their
   own valid bounds and failure-budget allocation. A window-average nuisance
   bias alone cannot be added to a MOM radius with coefficient one.
5. Mixing requires a specified joint coupling theorem and known coefficients;
   copies need not stay independent conditional on coupling success.
6. Local-intervention repair is eventwise feasibility on the certified design;
   deployment-induced future dynamics and long-run safety are unproved.
7. The clique lower bound is expected-risk and subclass-specific. Tighter
   heterogeneous/sparse-graph results and scientific novelty remain research tasks.

Gate A is closed as the requested proof audit plus valid restricted theorem.
It is not a declaration that the original broad theorem has been proved.
Gate C and later work were not started. Full changed-file inventory and source
diff are in `reports/modified_files.txt` and `reports/source_diff.patch`.

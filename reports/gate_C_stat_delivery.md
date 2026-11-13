# C-STAT delivery

**C-STAT PASS.** All 6,000 frozen confirmatory logs and 1,134,000 candidate
records are complete and independently validated. There are no excluded logs
or saved confirmatory execution errors. The twelve preflight logs remain
outside the study. The separate manuscript is a review proposal; submission
readiness is not claimed.

The complete results/proposal commit is **`dd59ec61a08b72cf241e87bcf575f9ce5ae585a7`**, pushed and verified
on `origin/codex/gate-c-stat`. This delivery note is a subsequent metadata-only
commit so the result commit can be recorded without a self-referential hash.
The final branch-tip SHA is reported in the user-facing handoff and Git history.

|Provenance|Commit|
|---|---|
|Starting evidence|`06a39b89e579aef57d14ae51e86d74ecf9b6b768`|
|Scientific freeze|`ab4c74fbf1ae84c0e5ffd72d77ce5b48d3fba8cb`|
|Immutable run-manifest launch provenance|`5f9a221062e67af492f1145dfd7ed3bec050de15`|
|Main invocation finish / report-generation working HEAD|`3542853df786f32cce5d1b49ae7b7910919a76d3`|
|Completed result and proposal anchor|`dd59ec61a08b72cf241e87bcf575f9ce5ae585a7`|

The 26 scientific sources and the launcher bytes stayed unchanged. All 222
files tracked at the starting evidence commit are byte-identical. Every path
added in this phase is listed in `gate_C_stat_modified_files.tsv`; no original
paper file or independent Overleaf repository was modified or synchronized.
The remote verification also retains the earlier A+B, C0 and preflight branch
references in `gate_C_stat_logs/remote_results_commit.txt`.

## Validation and substantive findings

- All 485 pytest tests passed; no pytest run failed. Independent aggregation
  passed 28,884,898 checks over 84 summaries and exactly 17 primary tests.
- Full idempotent resume skipped 6,000 IDs, generated zero new outcomes and
  preserved every completed checkpoint byte.
- Each registered 95% comparison covered 1000/1000 complete families, Wilson
  interval [0.996173, 1], exact and Holm p-values 1. Secondary 90% comparisons
  also covered 1000/1000. Nonrejection is not a proof of coverage validity.
- At 95%, B graph mean has median width/diameter 0.268917, 100% nontrivial
  candidate intervals and 50.99375% no certified decision. E graph mean has
  median width/diameter 1, 31.24375% nontriviality and 100% no decision.
  Both MOM methods in F are fully vacuous and always abstain; F graph is N/A.
- Eligible methods recorded zero false-certification families; each zero-of-1000
  Wilson interval is [0, 0.00382676]. Point-only and inapplicable methods make
  no certification claim. Candidate fractions are not independent-log power.
- Main execution used 10,389.879 wall seconds; zero-draw resume 288.065 seconds.
  Combined parent/child CPU was 55,676.733 seconds. Separate parent/child peak
  RSS was 211.500/116.828 MiB, not summed simultaneous memory.

The server connection works, but its historical F fixture failed strict
cross-platform byte compatibility because of floating-point power rounding.
That failure is preserved; zero confirmatory logs ran there. All confirmation
used the locally passing environment. No scientific formula, tolerance or
budget was changed to bypass the host mismatch.

## Review artifacts

- `gate_C_stat_scientific_lock.md`, `gate_C_stat_execution.md`,
  `gate_C_stat_methods_validation.md`, `gate_C_stat_results.md`.
- Complete outputs: `../results/gate_C/confirmatory/`; immutable outcome hashes
  in `checkpoint_index.json`, other export hashes in `export_checksums.json`.
- Five figure families, companion captions and visual-review hashes:
  `gate_C_stat_figure_review.md` and the independent-validation figure directory.
- Nine-page manuscript PDF, editable overlay, unapplied patch, claim matrix
  and bibliography crosswalk: `../paper/rewrite_proposals/cstat/`.
- Separate unrun D1–D5 proposals: `next_phase_D_preregistration_proposal.md` and
  `D_preregistrations/`. No D-stage seeds were drawn or datasets downloaded.
- Actual commands, operational issues and all failure accounting:
  `gate_C_stat_commands.md` and `gate_C_stat_logs/`.

The proved scope remains independent exogenous evaluation blocks with exact
logging, fixed or independent-pilot nuisance, a sufficient dependency graph
and known conditional moment bounds. Arbitrary adaptive histories, mutual
cross-fitting, learned tail scales, general sparse-graph sharpness and future
trajectory safety remain unproved. The proposal removes these from main claims.

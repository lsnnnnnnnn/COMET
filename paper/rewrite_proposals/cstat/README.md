# Review-only manuscript rewrite proposal

This proposal is based on the experiment-repository paper snapshot at
`06a39b89e579aef57d14ae51e86d74ecf9b6b768`. It has **not** been applied to any
existing manuscript file or to the independent Overleaf repository. The
scientific freeze remains `ab4c74fbf1ae84c0e5ffd72d77ce5b48d3fba8cb`.

The central change is to make the proved independent-block model the paper's
actual setup and main theorem, replacing the broad abstract and the formally
numbered but unproved adaptive theorem. The proposal presents the original
MOM result, exact-majority MOM result, and bounded graph-variance result as
separate certificates with their actual constants and assumptions.

- `review_proposal.pdf`: eight-page review rendering, with a visible proposal
  notice and an explicitly pending confirmatory-results section.
- `overlay/`: editable replacement LaTeX for the main manuscript, nine sections
  including a rewritten appendix, and three added bibliography entries.
- `paper_rewrite_diff.patch`: reviewable unified diff against the existing
  `paper/` source paths. It has been checked for applicability but not applied.
- `claim_proof_experiment_matrix.md`: claim-level disposition and precise source
  references, including what remains unproved or untested.
- `bibliography_crosswalk.md`: four requested source comparisons, verified
  against primary PMLR/arXiv records on 2026-11-13, including the dated arXiv
  version distinction for Mehrabi–Wager.
- `baseline_sources.json`: checksums of the original sources used by the diff.
- `build_logs/`: actual compilation commands, exits and final TeX log.

Regenerate from the repository root:

```sh
.venv/bin/python paper/rewrite_proposals/cstat/build_review.py
git apply --check paper/rewrite_proposals/cstat/paper_rewrite_diff.patch
```

The build script creates a temporary assembly, compiles it with the existing
local TeX style, and verifies that original paper source hashes are unchanged.
No existing `paper/sections/full/` version is changed. The proposed main file
loads only the replacement sections; old adaptive appendix blueprints and the
old overview diagram are intentionally absent from this proposed assembly.
The original working/full draft remains an archival research draft, not a
second scope-correct submission manuscript.

## Readiness and decisions for the authors

**Ready for scope/theorem review; not ready for submission.** The proposal has
complete mathematical arguments for the stated results and a compilable source
assembly. Its experiment section is deliberately an integration template: it
contains the frozen design and reporting contract, but no newly claimed
coverage, runtime, detection or repair result. The final C-STAT report must be
reviewed before numerical results enter this proposal. If the scientific lock
is blocked, that status must replace the pending template rather than being
hidden by a narrative rewrite.

The proof tools are standard. A competitive methodological claim still needs a
clear advance beyond their assembly, for example genuinely demonstrated
independent discovery/selection or a new proved dependence model. Future
D1–D5 experiments are separate preregistrations, not completed evidence.

Preferred title: **COMET: Certified Counterfactual Auditing under Weak Overlap
and Block Dependence**. A second option is **COMET: Simultaneous Counterfactual
Moment Certificates under Graph Dependence**. The old “Dependent Feedback”
framing needs a matching adaptive-feedback theorem before reuse.

Before adoption, the authors should choose the contribution emphasis, inspect
the proof-to-code lock outcome, replace the results template only with validated
outputs, and assess the substantive novelty. Adoption and independent Overleaf
synchronization are outside this proposal's actions.

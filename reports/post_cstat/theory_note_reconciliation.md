# Reconciliation of the recovered theory note

The recovered `task_materials/post_cstat/THEORY_NOTE.md` was read in full before
the E1–E5 production freezes. Its SHA-256 is
`44457a770bcaf35ae2b5a5141da6dc860d6c4d62dc59c9871a028aec49fdfd4f`.
The earlier proof files retain their original dated statements that the note
was unavailable when they were written. They are immutable scientific inputs
to the frozen runs; this addendum records the subsequent reconciliation.

The independently derived proof agrees with the note's residual identity,
raw moment budget, sharp bias constant, restriction 1<p<=2, centered range
2 tau, coloring/Hölder MGF, two tails, and finite-family union bound. It also
agrees on independent discovery, signed contrasts, the 2r sufficient decision
boundary, and affine propagation of base-policy intervals. The conditional
residual formulation in the implementation is the observable version of the
potential-outcome moment assumption under the separately required
identification assumptions.

The production truncation grid is exactly c=2^(j/4), j=-24,...,24. The earlier
five-point deterministic maps are archived as design_v0. Reconciled maps in
design_v1 use all 49 points, draw no outcomes, and bind this note's hash. E5's
p=2 evaluation uses the analytically equivalent minimizer of kappa_2 on that
same grid, with deterministic equivalence checks against the full grid.

The lower bound uses a symmetric positive/negative spike pair rather than the
note's zero/positive pair. It explicitly caps the mean displacement and handles
small effective counts and integer subgroup/clique sizes. This proves a scoped
expected absolute-risk obstruction and a separate nonsharp two-point interval
consequence. It does not claim matching confidence logarithms, bounded-response
optimality, or sharpness for every sparse graph.

No new assumptions, gaps, thresholds, observed outcomes, or historical results
are changed by this reconciliation. EXPERIMENT_BLUEPRINT.json remains missing
and explicitly waived by the user; no contents are attributed to it.

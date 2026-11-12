# Gate A source status

The two manuscript entry points now visibly distinguish the unresolved broad
adaptive/cross-fit theorem from the proved independent-block certificate in
`sections/gate_a_certificate.tex`. Original theorem statements were retained;
the additional assumptions and mathematical reasons are explicit.

Both lower-bound proofs now use epsilon=1/(2n), the correct centered moment,
and a Le Cam expected absolute-risk constant of 1/8 for the exact clique
replication subclass. They make no sharpness claim for every sparse graph.

The checked-in `main.pdf` and `full_working_draft.pdf` are the original ZIP
artifacts and are intentionally preserved. Recompile the LaTeX for the current
version. The experiment checkout saves current compiled PDFs under
`build/paper/`, outside this manuscript subtree.

No empirical paper results were inserted: the Gate B 30-replication smoke run
is only a software/debugging check and all its intervals were vacuous. Full
theory reports, source-line references, tests and smoke artifacts are maintained
in the accompanying experiment repository.

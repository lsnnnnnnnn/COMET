# COMET — ICLR 2027 LaTeX bundle

This bundle contains two versions of the same proposed paper.

## Entry points

- `main.tex`: compact ICLR submission draft. With the bundled local style copy, the research body ends on page 7; reproducibility, ethics, AI-use, and references occupy page 8; the appendix begins on page 9. The exact page count may shift after replacing the style files, adding results, and revising prose, so the official nine-page main-text limit must be rechecked before submission.
- `full_working_draft.tex`: overlength 20-page working draft containing more motivation, method detail, experiment planning, and explicit placeholders. It is a research source, not a page-limit-compliant submission.
- `sections/`: compact main-paper sections and appendix.
- `sections/full/`: the overlength versions retained for later editing.
- `RESEARCH_TODO.md`: prioritized theory, implementation, and experiment work needed to turn the draft into a defensible submission.
- `SOURCE_MAPPING.md`: how the earlier heavy-tailed COPF notes were restructured into the general COMET paper.
- `source_snapshot/`: copies of the earlier source notes supplied with the project.

## Compile

```bash
make main       # builds main.pdf
make full       # builds full_working_draft.pdf
make all        # builds both
make clean
```

The Makefile uses `bibtex` when available and falls back to `bibtex8`. A manual build is:

```bash
pdflatex main.tex
bibtex main       # use bibtex8 main when needed
pdflatex main.tex
pdflatex main.tex
```

## Submission mode

The paper is anonymous by default. Do not add identifying acknowledgements, repository links, or author metadata during review. Use `\iclrfinalcopy` only for a camera-ready version.

`iclr2027_conference.sty` and `.bst` are self-contained local compilation copies. They preserve the expected package interface and approximate conference layout, but they are **not asserted to be byte-identical to the official archive**. Before submission, replace both files with the exact official ICLR 2027 style files and recompile without modifying margins, font sizes, or spacing. See `STYLE_NOTICE.md`.

## Scientific status of this draft

The manuscript is intentionally honest about what is and is not complete.

- The problem, estimands, orthogonal score, dependence interface, COMET estimator, discover–certify protocol, and pessimistic repair rule are written as a coherent paper.
- The finite-sample theorem is stated under explicit conditional dependency-graph, block-coupling, score-moment, and nuisance-bias assumptions. The appendix gives a detailed proof under the equal-block coupled model, but the exact implementation-level conditional assumptions and constants still require independent verification.
- The cluster-replication lower bound has a proof blueprint that should be checked and polished before it is claimed as final.
- For exact logged propensities, the propensity nuisance remainder vanishes. With estimated propensities, a valid high-probability bound on the overlap-weighted nuisance product is required; an empirical plug-in diagnostic is not automatically a confidence guarantee.
- No experimental values were invented. The long draft contains a blank result-table shell; the compact submission draft omits it. All numerical claims must come from fixed scripts and stored configurations.
- Adaptive unknown-tail tuning is currently an experimental plan and possible secondary theorem, not a completed result.

## Recommended editing order

1. Lock the exact dependence and nuisance assumptions used by code.
2. Complete and independently check the main upper-bound and lower-bound proofs.
3. Implement the controlled synthetic coverage/rate study before adding real datasets.
4. Add TGB semi-synthetic and Open Bandit experiments; add KuaiRand after the core claims are stable.
5. Run discover–certify and policy-repair studies with strict data separation.
6. Replace placeholders, update the abstract with measured findings, then compress against the exact official style.

## ICLR-specific components already included

- anonymous review mode;
- author–year references;
- a compact main paper plus appendix after the bibliography;
- reproducibility statement;
- ethics statement;
- AI use statement describing the role of generative AI and retaining author responsibility.

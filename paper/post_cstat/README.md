# COMET local post-C-STAT manuscript

This manuscript uses heterogeneous fixed-design moments and a sufficient global
conditional dependency graph. The historical independent-block proposal stays
in `paper/rewrite_proposals/cstat/`; the independent Overleaf source is separate.

The current source is a research revision while the live fixed-count suites
finish. `reports/post_cstat/ACTIVE_STATE.json` records actual tool sessions;
`reports/post_cstat/remaining_run_ids.json` records a dated inventory. The final
research verdict and handoff must be read together with the final PDF. A valid
certificate, a useful decision and a distinct estimator contribution are
different claims.

Build locally from this directory:

```sh
/Library/TeX/texbin/pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
/Library/TeX/texbin/pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
```

The output is `build/main.pdf`. The bibliography is embedded in `main.tex`;
no network, remote Overleaf operation, or bibliography service is required.

Analytic figures use `results/post_cstat/design_v1` and the recovered theory
note's exact49-point grid. The older design_v0 files remain archived. Empirical
figure bundles are generated from completed analysis receipts and independent
detailed diagnostics; each bundle includes hashes, CSV exports and captions.
They never draw an experiment or silently substitute missing suite results.

From the repository root, the figure command accepts completed inputs only:

```sh
MPLCONFIGDIR=/private/tmp/comet-post-cstat-mpl .venv/bin/python -m experiments.post_cstat_empirical_figures --help
```

Full numerical exports may contain more rows than are practical to print in
the manuscript. The CSV/JSON artifacts retain every method, both levels,
all fixed cells, unknown failures and the actual complete-trial denominators.
Monte Carlo intervals and bootstrap intervals are pointwise unless expressly
labeled otherwise. Supplemental diagnostics do not join the historical17-test
family or create new independent replication units.

The source proof is a real-arithmetic result. The implementation's documented
floating-point padding is not formal verification of outward-rounded arithmetic.
Assumption schemas do not discover hidden sources or unknown moment scales.

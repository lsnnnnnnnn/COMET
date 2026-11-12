# COMET: Gate A + Gate B

This repository contains a mathematical audit and the smallest proof-matched
synthetic certificate. Only Gates A and B of the supplied master task were run.
The broad adaptive/cross-fit manuscript theorem remains unresolved. Large
synthetic studies, external datasets, discovery and policy repair experiments
are deferred to later sessions.

Start with [Gate A](reports/gate_A_report.md), [Gate B](reports/gate_B_report.md),
the [estimand contract](theory/estimand_contract.md), and the
[theorem-to-code contract](theory/theorem_to_code_contract.md).

## Reproduce

Python 3.10+; runtime uses the standard library. pytest is a test dependency.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[test]'
.venv/bin/python -m pytest -q
.venv/bin/comet-smoke --config configs/smoke.json --output results/smoke
```

The actual local offline setup and all validation/failure commands are recorded
in [commands.md](reports/commands.md). An ordinary installation was used after
this Mac's Python skipped the editable installation's hidden `.pth` file.
The module form also works from the checkout:

```sh
.venv/bin/python -m comet.smoke --config configs/smoke.json --output results/smoke
```

The default is **30 independent CPU debugging replications**, 4,096 rows each,
128 macro-blocks, 4-clique replication, four frozen policy/auditor candidates,
and 90%/95% simultaneous intervals. The envelope and radius are deliberately
conservative. The saved run produced entirely vacuous intervals: the smoke
coverage table is not evidence for final empirical coverage or utility.

## What is certified

The supported stochastic model has exogenous repeated contexts, independent
clusters and macro-blocks, known sufficient clique graphs, exact binary logging
probabilities, bounded rewards, fixed regression predictions, and stable block
targets. The known centered moment envelope is computed from pre-action e/q
and the reward range. No oracle response mean or empirical tail estimate enters
the certificate. `comet/truth.py` is used only by generation and downstream
evaluation. Exact truth is a conditional expectation, not a realized potential
outcome average.

`K=ceil(8 log(2|Theta|/delta_stat))`, `B>=2K`, all complete blocks are retained,
and `r=32^(1/p) nu_p (chi/(floor(B/K)*n0))^((p-1)/p)`.
Coupling error is a failure probability, not a numeric radius; it and nuisance/
drift radii are zero in this model by construction. Unsupported model tags and
infeasible designs return explicit refusal statuses. Arbitrary external rows
with a copied provenance tag do not acquire a stochastic guarantee.

## Artifacts and source history

- `paper/`: original supplied LaTeX plus explicit audit notices, a separate
  independent-block theorem, and corrected lower-bound proofs. Original PDFs
  are preserved, not overwritten. Current builds are under `build/paper/`.
- `theory/`: all five requested audit documents, corrected Le Cam derivation,
  and verified literature metadata.
- `results/smoke/`: actual interval CSV/JSON, conditional and unconditional
  coverage summaries with Wilson uncertainty, one example log and separate
  oracle object, resolved config, seeds, and source hashes.
- `reports/`: gate reports, real test/build/install output, initial CLI failure,
  command history, exact changed-file inventory, and auditable paper patch.
- `source_manifest.json`: ZIP SHA-256 checksums. Git baseline `58ad7bd` preserves
  original source lines cited by the audit; `task_materials/` preserves the full
  master task. Its future phases did not override the user's A+B-only scope.

The experiment repository is `lsnnnnnnnn/COMET`; the manuscript subtree is
synchronized separately with `lsnnnnnnnn/COMET_overleaf`. See the final
synchronization record in `reports/sync_status.md`.

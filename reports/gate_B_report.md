# Gate B — completed minimal runnable certified path

The package installs, the installed CPU CLI runs, and **243 pytest tests pass**.
Runtime has no third-party dependency. The supported probability model and
numeric certificate are exactly those proved in the Gate A contract.

## Implemented

`comet/schema.py`, `synthetic.py` and `truth.py` define immutable pre-action
design/logs and a separate oracle-only object. Each block repeats a fixed context
pattern; independent randomized clusters are replicated chi times, yielding
known sufficient chi-clique graphs. Assignments and potential-outcome draws have
separate seeded RNG streams; there is no cross-block latent effect. Oracle
targets are exact conditional expectations, not sample potential-outcome means.

`dr_scores.py`, `exposure.py`, `conflict_graph.py`, `robust_mean.py` and
`certification.py` implement exact-e DR, exact small complete-slate probability
enumeration and marginalization, graph coloring, known bounded-reward centered
envelopes, all-block MOM grouping, and explicit 90%/95% family statuses. The
certifier imports no oracle/generator module. No estimated-nu, mutual-cross-fit,
adaptive-family, unknown-drift or nonzero-coupling certified entry point exists.
The subgroup denominator is the exact pre-action design mass, with zero mass
causing ratio abstention.

`metrics.py`, `smoke.py`, `configs/smoke.json`, and the installed `comet-smoke`
command save structured results and Wilson uncertainty, with correct replication
denominators. No-issuance coverage is undefined, not silently reported as one.

## Actual CPU smoke output — debugging only

Command:

```sh
.venv/bin/comet-smoke --config configs/smoke.json --output results/smoke
```

30 independent replications, integer seeds 20261112 through 20261141, N=4096,
B=128, n0=32, chi=4, N_eff=1024, p=1.5, four fixed candidates. K=41 at 95%
and K=36 at 90%; both have L_min=3, so the conservative radii coincide. Every
block and row was used. Known envelope only; nuisance/drift radii and coupling
failure probability were zero by the declared DGP.

| Nominal family level | Issued | Family covered | Wilson 95% uncertainty | Mean width | Vacuous intervals |
|---|---:|---:|---|---:|---:|
| 95% | 30/30 | 30/30 | [0.88649, 1.00000] | 30.7605 | 100% |
| 90% | 30/30 | 30/30 | [0.88649, 1.00000] | 30.7605 | 100% |

These are actual persisted measurements, not a claim of final nominal coverage.
Every interval contains the whole bounded-outcome target range; the result
demonstrates the conservativeness of this implementation, not useful precision.
The smoke runtime was about 3.91 seconds on local CPU. No dataset was downloaded
and no large design or 1000-replication experiment ran.

Saved artifacts in `results/smoke/`: `intervals.csv`, `intervals.json`,
`coverage.csv`, `coverage.json`, `coverage.md`, `example_log.json`,
`example_oracle_truth.json`, `resolved_config.json`, `run_metadata.json`.
Metadata records all seeds, resolved config hash, source-module SHA-256 hashes,
Python/platform and the actual run-time Git base/dirty status. The output was
generated before the delivery commits; hashes identify the exact code.

## Tests, failures and fixes

Final command `.venv/bin/python -m pytest -q`: **243 passed in 1.26s, 0 failed**.
Tests cover both DR identities/product remainder; support and normalized exact
slate exposure; clique edges/coloring; no oracle import/input; complete grouping,
K, budget and literal CI constant; mathematical counterexamples; corrected Le
Cam moments/TV/constants; unsupported model refusal; exact subgroup mass;
deterministic regenerated data and saved results; Wilson and abstention handling.
No unit-test failure occurred in the recorded runs.

Independent review found and fixed three concrete bugs before the final run:
six-digit policy IDs could collide and overwrite oracle targets; subnormal
propensities could produce infinite JSON diagnostics; and subtracting a dominant
Plackett–Luce weight could produce a zero remaining denominator. Regression tests
now cover lossless IDs, numerical refusal and stable denominator sums. Normalized
ESS also avoids squaring huge raw weights; nonfinite interval arithmetic refuses
certification instead of emitting invalid numbers.

The first installed CLI attempt **failed** with `ModuleNotFoundError: comet`.
Python verbose startup showed that this Mac skipped the editable installation's
hidden `.pth` file. Reinstalling normally with
`.venv/bin/python -m pip install --no-build-isolation --no-deps --force-reinstall .`
fixed the installed command, and the 30-replication run then exited 0. The failure
is preserved in `reports/smoke_initial_failure.txt`; final output and installation
log are in `reports/smoke_stdout.txt` and `reports/install.txt`.

## Handoff

Gates A+B are stable for this declared model. The next session can plan the
larger Gate C designs after reading the open proof gaps and acknowledging that
the current explicit bounds are vacuous at smoke sizes. Preserve the full-family
K calculation, known envelope and failure-probability accounting. Extend a proof
before exposing a new certified mode. Do not repurpose the smoke table as paper
evidence. No Gate C–F work was performed in this run.

Exact files and commands: `reports/modified_files.txt`, `reports/commands.md`.
Paper baseline diff: `reports/source_diff.patch`. Repository/server state:
`reports/sync_status.md` and `reports/access_diagnostics.md`.

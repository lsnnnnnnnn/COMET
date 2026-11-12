# Gate C command and failure log — C-PREFLIGHT only

Working directory: `/Users/shengenli/Documents/ChatGPT/COMET`.
The full `CODEX_COMET_GATE_C_MASTER.md` was read from the supplied ZIP; the
Chinese research decision and initial prompt were also read. Python `zipfile`
extracted only relative safe paths into `task_materials/gate_C`, with SHA-256
provenance. No instructions in later master phases authorize running them in
this C-PREFLIGHT-only task.

## Verified start and deterministic inspection

```sh
git status --short
git rev-parse HEAD
unzip -l /Users/shengenli/Downloads/COMET_Gate_C_Implementation_Package.zip
unzip -p /Users/shengenli/Downloads/COMET_Gate_C_Implementation_Package.zip CODEX_COMET_GATE_C_MASTER.md
.venv/bin/python -m pytest -q > /tmp/comet_C_preflight_baseline_pytest.txt 2>&1
git switch -c codex/gate-c-preflight 3f8902d1033f3c4eece9a3746912ac9f1d8904ef
```

Observed HEAD exactly matched the requested baseline and the initial worktree
was clean. Original **377 tests passed in 4.43s**; the log was copied to
`gate_C_logs/baseline_pytest.txt`. No original test or source was modified.
Read-only inspection used `rg`, `cat`, `sed`, `nl`, `git show/status/diff` and
Python CSV/JSON/rational arithmetic. One inventory probe used a nonexistent
`tests/test_gate_c_runner.py` path (actual file is `test_gate_c_preflight.py`),
so `rg` returned exit 2; this was not a test run or experiment failure.

```sh
.venv/bin/python experiments/reconcile_gate_c_baseline.py > reports/gate_C_logs/c0_reconciliation.txt 2>&1
.venv/bin/python -m experiments.gate_c_design_audit > reports/gate_C_logs/design_audit.txt 2>&1
```

The baseline reconciliation completed with 879,955 checks and zero
discrepancies, preserving all 152 baseline files. The design audit generated
486 candidate-level method/level rows without outcomes or oracle access.
An inline Fraction audit saved the exact mathematical probabilities and
ordinary float-complement representation differences in
`results/gate_C/preflight/numerical_probability_audit.json`.

## Tests before primary preflight outcomes

```sh
.venv/bin/python -m pytest tests/test_gate_c_model.py -q > reports/gate_C_logs/model_pytest.txt 2>&1
.venv/bin/python -m pytest tests/test_gate_c_methods.py tests/test_gate_c_statistics.py -q
.venv/bin/python -m pytest tests/test_gate_c_preflight.py -q > reports/gate_C_logs/runner_initial_tests.txt 2>&1
.venv/bin/python -m pytest -q > reports/gate_C_logs/pytest_before_freeze.txt 2>&1
git diff --name-only 3f8902d
git diff --check
```

Model tests: 34 passed. Methods/statistics: initially 55 passed, then 57 after
the diagnostic metadata and empty-intersection regression; both actual logs
are preserved as `methods_statistics_initial_pytest.txt` and
`methods_statistics_final_pytest.txt`. Runner tests: 4 passed. Full suite:
**472 passed in 5.70s**, including every unchanged prior test. No pytest run
failed. The undercoverage issue was found by review and fixed before the
primary run: an applicable empty confidence set remains a failure in the
exact-binomial diagnostic rather than suppressing the p-value.

Tiny unit-test draws live only in temporary fixtures and are not primary
preflight or confirmatory replications. The root test verifies crash/resume,
unchanged completed-checkpoint bytes, no repeated completed run IDs, refusal
of changed source/configuration or corrupted payloads, and reproducible seed
namespaces. No test asserts stochastic coverage exceeds its nominal level.

## Frozen files and reproduction

The authoritative input files are `configs/gate_C_frozen.json` and its hashed
`configs/gate_C_seed_manifest.json`. The latter stores 12 preflight and 6,000
reserved confirmatory entries with seven separate mechanism seeds each.
`comet/gate_c_seeds.py` reproduces the seed manifest algorithm. The generation
of these lists produced no outcomes. The model, known-moment proof, protocol
and tests are committed before the first primary preflight log.

The runner imports checked-out code as a module. Existing
`requirements-gate-C0.txt` gives the working pinned test/plot dependencies;
new runtime modules use only the Python standard library. Each actual batch
manifest records all installed distribution versions, Python, OS/CPU,
source/config/seed hashes, Git SHA and starting Git status. Numerical theory
uses the known randomization law with ordinary floating-point computation;
there is no claim of a bit-level outward-rounded interval proof.

Actual primary execution, fault/recovery outputs, resource measurements and
final commits are appended below after those operations complete. No
confirmatory, secondary, power/discovery/repair campaign, real-data download,
GPU job or paper edit is authorized in this run.

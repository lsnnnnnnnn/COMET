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

## Actual frozen commit and primary checkpoint-resume execution

The freeze commit is `ab4c74fbf1ae84c0e5ffd72d77ce5b48d3fba8cb`:

```sh
git -c user.name='COMET Research' -c user.email='comet-research@users.noreply.github.com' commit -m 'Freeze Gate C preflight model proofs protocol seeds and checkpoint tests'
/usr/bin/time -l .venv/bin/python -m experiments.gate_c_preflight --config configs/gate_C_frozen.json --output results/gate_C/preflight/batch --crash-after-completed 1 > reports/gate_C_logs/preflight_injected_crash.txt 2>&1
/usr/bin/time -l .venv/bin/python -m experiments.gate_c_preflight --config configs/gate_C_frozen.json --output results/gate_C/preflight/batch --resume > reports/gate_C_logs/preflight_resume.txt 2>&1
.venv/bin/python -m experiments.gate_c_preflight --config configs/gate_C_frozen.json --output results/gate_C/preflight/batch --resume > reports/gate_C_logs/preflight_idempotent_resume.txt 2>&1
```

The first command deliberately exited 1 after saving exactly A/0000. Its
checkpoint SHA-256 was recorded before recovery. The next invocation generated
11 remaining logs, skipped A/0000 and wrote BATCH_COMPLETE plus all outputs.
Both external `time -l` wrappers then reported sandbox-denied
`sysctl kern.clockrate`; the resume wrapper exited 1 despite the completed
Python batch. Its failure is not hidden or described as shell success. The
third direct command exited **0**, skipped all 12 completed runs, regenerated
no outcomes, and reproduced the exported scientific records from checkpoints.
The completed A/0000 bytes stayed identical through both resumes.

`execution_invocation.json` preserves the actual 11-log resume resources before
`last_invocation.json` is updated by the zero-new-log idempotency check. Internal
perf_counter/process_time/getrusage measurements were available and saved; no
resource number is inferred from a failed monitor. The Apple M1 CPU-brand query
`sysctl -n machdep.cpu.brand_string` was initially sandbox-denied (exit 1), then
succeeded with read-only sandbox escalation (exit 0). No code or input changes
were made to obtain a favorable run.

## Post-run read-only audit and presentation

```sh
git diff ab4c74f --name-only -- comet experiments configs tests theory/gate_c_heavy_tail_contract.md
git diff --check
```

The first diff is empty. The independent read-only audit checked 127,613
invariants with zero failures: 12 distinct preflight IDs, all 2,268 records,
84 summaries, statuses/coverage/Wilson/17-way Holm/widths/decisions, 26 frozen
source hashes, both input files and all 152 baseline files. Its actual command
was `python3 /tmp/comet_gate_c_final_readonly_audit.py`; the exact source and
source hash are embedded in `results/gate_C/preflight/final_audit.json` for
reproduction without adding a new module to the frozen scientific source set.
One audit inventory probe guessed a nonexistent `interval_diagnostics.py` and
returned exit 2; `informativeness.py` was then located and read. No audit check
or pytest failed.

Inline standard-library CSV/JSON scripts derived `marginal_coverage.csv` and
`gate_C_statistical_summary.md` from the saved checkpoints/summary files, and
recorded the before/after checkpoint hashes. They generated no outcomes. Full
reports, exact path inventory and synchronization are committed separately
from the frozen code. No confirmatory command, external dataset download, GPU
job, manuscript write or later-phase experiment was executed.

## Result commit and synchronization

```sh
git add reports/gate_C_commands.md reports/gate_C_logs reports/gate_C_report.md reports/gate_C_statistical_summary.md reports/gate_C_modified_files.txt results/gate_C
git -c user.name='COMET Research' -c user.email='comet-research@users.noreply.github.com' commit -m 'Record twelve-log Gate C preflight resume evidence and scoped GO decision'
GIT_TERMINAL_PROMPT=0 git -c http.proxy=http://proxy-dku.oit.duke.edu:3128 -c http.lowSpeedLimit=1 -c http.lowSpeedTime=30 push --set-upstream origin codex/gate-c-preflight
GIT_TERMINAL_PROMPT=0 git -c http.proxy=http://proxy-dku.oit.duke.edu:3128 -c http.lowSpeedLimit=1 -c http.lowSpeedTime=10 ls-remote origin refs/heads/codex/gate-c-preflight
GIT_TERMINAL_PROMPT=0 git -c http.proxy=http://proxy-dku.oit.duke.edu:3128 -c http.lowSpeedLimit=1 -c http.lowSpeedTime=10 ls-remote origin refs/heads/codex/gate-c0-informativeness refs/heads/codex/gates-a-b
GIT_TERMINAL_PROMPT=0 git -c http.proxy=http://proxy-dku.oit.duke.edu:3128 -c http.lowSpeedLimit=1 -c http.lowSpeedTime=10 ls-remote overleaf refs/heads/codex/gates-a-b
```

Commit and push exited 0; the C-PREFLIGHT remote result SHA was
`b17ad86a97a06617a15f890e0dcbcbde5d341360`. Prior branch SHAs remained
3f8902d, d11a36f and df70f48 as recorded in `gate_C_sync_status.md`. This
metadata-only audit is committed next; its own final SHA and remote/clean-state
verification are provided in the final response. No force-push or paper change.

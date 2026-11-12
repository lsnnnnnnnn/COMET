# Gate C0 commands and provenance

Working directory: `/Users/shengenli/Documents/ChatGPT/COMET`. This records
executed research/build commands; read-only inspection also used `rg`, `cat`,
`sed`, `nl`, `git show/status/diff`, `head`, `tail`, and SHA-256 checks. No
dataset download, GPU job, 1,000-replication run, or server experiment ran.

## Baseline and supplied task

The entire supplied `COMET_GATE_C0_CODEX_TASK.md` was read. Python's `zipfile`
extracted the task ZIP into `task_materials/gate_C0`; its Markdown task was
byte-compared with the separately supplied task. The manifest records input
hashes. Attachment instructions were applied only within the user's C0 scope.
All A+B reports and implementation were inspected before changes.

```sh
git rev-parse HEAD
git status --short
git switch -c codex/gate-c0-informativeness d11a36f3b967165f4e0cdf56bf6a262d178e41bd
.venv/bin/python -m pytest -q
```

The original 243 tests passed; the captured baseline log is
`gate_C0_logs/baseline_pytest.txt`. Original paper commit remains
`df70f486fc08139057436e2781c212ad741ef646`.

## Deterministic forensics, algebra and testing

```sh
.venv/bin/python experiments/forensic_c0.py
MPLCONFIGDIR=/tmp/comet-c0-matplotlib .venv/bin/python experiments/nonvacuity_budget.py
MPLCONFIGDIR=/tmp/comet-c0-matplotlib .venv/bin/python -m pytest tests/test_nonvacuity_budget.py -q
.venv/bin/python -m pytest tests/test_exact_binomial_mom.py -q
.venv/bin/python -m pytest tests/test_core.py tests/test_exact_binomial_mom.py -q
.venv/bin/python -m pytest tests/test_bounded_variance.py -q
.venv/bin/python -m pytest -q > reports/gate_C0_logs/pytest_before_pilot.txt 2>&1
.venv/bin/python -m pytest -q > reports/gate_C0_logs/pytest_preregistration.txt 2>&1
git diff --check
git diff d11a36f --name-only -- paper results/smoke reports/gate_A_report.md reports/gate_B_report.md tests/test_core.py tests/test_lower_bound.py
```

The last preservation diff printed nothing. Forensics replayed only historical
logging assignments to recover weight quantiles; no new outcomes were generated.
The independent budget script imports neither certifier nor simulator/truth.
The PNG/PDF budget plot was visually inspected. A temporary standalone article
wrapper for `gate_C0_paper_patch_suggestion.tex` compiled successfully with
`pdflatex`; the temporary wrapper/build files were removed. No manuscript-wide
patch or new manuscript compilation is claimed.

There was one failing budget-test run (1 failed, 12 passed): an incorrectly
transcribed expected rational fraction in the test, corrected to
`166583/4194304` for the familywise bound. The preserved diagnostic in
`gate_C0_budget_initial_failure.txt` is explicitly identified as an excerpt
reconstructed from the actual tool result, not a full stdout capture. That
suite subsequently passed all 13 tests. No failure is concealed by later runs.
The full suite passed 357 tests, then 377 after tiny-delta refusal regressions.
Review-found fixes before the pilot include conservative-K overflow handling
and checking block feasibility before huge integer diagnostics. Normal baseline
outputs are checked field-for-field against the saved original evaluation log.

## Preregistration before outcomes

```sh
git add comet configs/gate_C0_pilot.json experiments reports/gate_C0_budget_initial_failure.txt reports/gate_C0_forensic.md reports/gate_C0_logs reports/gate_C0_paper_patch_suggestion.tex results/gate_C0 task_materials/gate_C0 tests/test_bounded_variance.py tests/test_c0_integration.py tests/test_c0_pilot.py tests/test_exact_binomial_mom.py tests/test_nonvacuity_budget.py theory/bounded_graph_variance.md theory/exact_binomial_mom.md
git -c user.name='COMET Research' -c user.email='comet-research@users.noreply.github.com' commit -m 'Prove Gate C0 bounds and preregister 210-cell informativeness pilot'
git rev-parse HEAD
```

Preregistered source/config commit:
`15af1842dff7dddf89bbad1c98e8b3ac7a8de3b0`. All mathematical code, 377 passing
tests and the seven-cell configuration were committed before the following
outcome-generation command. Unit tests use small temporary fixtures for
reproducibility and guard checks; they are not extra scientific pilot cells.

## CPU pilot

```sh
.venv/bin/python -m experiments.gate_c0_pilot --config configs/gate_C0_pilot.json --output results/gate_C0 --workers 2 > reports/gate_C0_logs/pilot_stdout.txt 2>&1
```

The driver is run as a module so the checked-out source is used, rather than a
possibly stale installed console entry point. The archived run manifest records
the actual source/config hashes, Python version, seeds, elapsed time and HEAD.
There are 210 independent generated logs, paired across all four methods and
both confidence levels (420 level evaluations, not 420 independent logs).
No configuration was selected or changed using observed coverage or oracle truth.
Timing is intentionally excluded from deterministic byte equality; tests check
raw data summaries, intervals, status, CSV/JSON and PNG/PDF reproducibility.

Final result/audit commit and synchronization are recorded in
`gate_C0_sync_status.md`; exact changed paths are in `gate_C0_modified_files.txt`.

## Post-run audit

The pilot command completed successfully (exit 0). Saved summaries/CSV were
read to construct the report; no new outcomes were generated. A Python audit
compared every pre-existing paper/report/result/test/theory file with
`git show d11a36f:<path>`: all 78 were byte-identical. Another independent audit
checks raw CSV counts, summary denominators, radii, and preregistered hashes;
its artifact is `results/gate_C0/pilot_audit.json`. Both plots were visually
inspected. The negative-control command and its complete output are linked
from `gate_C0_negative_controls.md`.

```sh
git diff HEAD --name-only -- comet experiments configs/gate_C0_pilot.json tests
git diff --check
```

The first command printed nothing after the pilot: mathematical code, tests
and configuration stayed frozen. A process-monitoring `ps` call was denied
by the local sandbox; this did not affect the run. Checking for final output
files while the runner was still active correctly reported them absent; the
driver writes its artifacts after all cells complete. Neither was a failed
experiment or a test failure.

The independent audit also initially used invalid inline Python syntax
(`==not`), producing a SyntaxError before execution; it was corrected and the
final audit exited 0. An initial inventory probe requested `run_metadata.json`
instead of the existing `run_manifest.json`; the corrected read succeeded.
These read-only audit mistakes generated no outcomes and changed no result.

## Reproduction on a fresh checkout (instructions, not an additional run)

`requirements-gate-C0.txt` records the actual working package versions, also
saved with Python/platform metadata in `results/gate_C0/environment.json`.
Use Python 3.12.2 and install that file in a fresh virtual environment before
the module commands above. Matplotlib is needed for the new plotting tests;
the original package's minimal `[test]` extra alone does not include it.
No additional package installation was performed during C0. Reproducing plots
byte-for-byte is tested in the recorded environment; rendering bytes can vary
across platforms or font-library versions. Statistical tables and seeds are
the portable scientific artifacts.

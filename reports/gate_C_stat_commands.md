# C-STAT commands and failures

All paths below are relative to `/Users/shengenli/Documents/ChatGPT/COMET`
unless a server path is explicit. Commands run on 2026-11-13/14 Asia/Shanghai;
JSON event timestamps use UTC. No frozen scientific file is changed.

## Read, audit and freeze

The three members of the supplied ZIP were read; the master was read in full.
`zipfile` extracted them to `task_materials/gate_C_stat/`, recording SHA-256.
Initial `git status --short` was empty and HEAD was 06a39b89.

```sh
git switch -c codex/gate-c-stat
GIT_TERMINAL_PROMPT=0 git -c http.proxy=http://proxy-dku.oit.duke.edu:3128 ls-remote origin refs/heads/codex/gate-c-preflight
.venv/bin/python -m pytest -q > reports/gate_C_stat_logs/baseline_pytest.txt 2>&1
.venv/bin/python -m experiments.audit_gate_c_scientific_lock > reports/gate_C_stat_logs/scientific_lock_audit.txt 2>&1
.venv/bin/python reports/gate_C_stat_audit/check_frozen_science.py > reports/gate_C_stat_audit/independent_proof_checks.json
.venv/bin/python -m experiments.gate_d_design_only > reports/gate_C_stat_logs/D_design_only.txt 2>&1
```

These completed successfully: baseline472 tests; lock328 checks; independent
proof22837 checks. D computation generated design-only tables and no outcomes.
A source inventory guessed nonexistent `comet/exact_mom.py`; `rg` reported it
missing (exit2), the correct `comet/robust_mean.py` was located before execution,
and the new design-only script import was corrected before its first run.
No existing code or experimental setting was changed to resolve that typo.

The new launcher and tests were committed with the audits and future protocols:

```sh
git -c user.name='COMET Research' -c user.email='comet-research@users.noreply.github.com' commit -m 'Lock C-STAT launcher against unchanged scientific freeze and preregister future D proposals'
git bundle create /tmp/COMET_cstat_input.bundle codex/gate-c-stat
```

Commit: `5f9a221062e67af492f1145dfd7ed3bec050de15`. Runner SHA-256:
`1628b05f843975ee19f3fd48cf5868717c67f0646a3f927ea8fa4cab860865ed`.
The scientific freeze remains ab4c74f. Only new files were committed.

## Historical-only compatibility and tests

```sh
.venv/bin/python -m pytest tests/test_gate_c_confirmatory.py -q
.venv/bin/python -m experiments.gate_c_confirmatory --compatibility-only --output results/gate_C/stat_lock/compatibility_local
.venv/bin/python -m experiments.gate_c_confirmatory --compatibility-only --output results/gate_C/stat_lock/compatibility_local_final
.venv/bin/python -m pytest -q > reports/gate_C_stat_logs/launcher_full_pytest.txt 2>&1
MPLCONFIGDIR=/tmp/comet-matplotlib .venv/bin/python reports/gate_C_stat_audit/validate_confirmatory.py --input results/gate_C/preflight/batch --output results/gate_C/stat_lock/independent_preflight --phase preflight --figures
.venv/bin/python -m pytest tests/test_gate_c_independent_validation.py -q
```

Launcher tests: 9 passed. The first compatibility output is retained but its
launcher hash was superseded by the requested extra denominator and resume-test
validation. The second used the final committed runner: all12 historical seeds
matched bytewise scientifically and all84 summary rows matched exactly, exit0.
Both output trees and stdout logs are saved. The full prelaunch suite passed481
in10.73s. Four later analysis-only validator tests also passed. These additional
tests do not alter science, launch readiness or draw confirmation outcomes.
A filesystem readiness probe ran before `compatibility_local_final` finished;
its `ls .../compatibility_result.json` returned1. The completed report was then
read and verified before any confirmatory launch. It is not a failed fixture.

## Server inspection and failed compatibility

```sh
ssh -o BatchMode=yes -o ConnectTimeout=10 10.200.13.23 'hostname && python3 --version && nproc && free -m && df -h /data1/shengen && uptime'
scp /tmp/COMET_cstat_input.bundle 10.200.13.23:/data1/shengen/COMET_cstat_input_20261113.bundle
ssh -o BatchMode=yes 10.200.13.23 'test ! -e /data1/shengen/COMET_C_STAT_20261113 && git clone -b codex/gate-c-stat /data1/shengen/COMET_cstat_input_20261113.bundle /data1/shengen/COMET_C_STAT_20261113 && cd /data1/shengen/COMET_C_STAT_20261113 && mkdir -p reports/gate_C_stat_logs && python3 -m experiments.gate_c_confirmatory --compatibility-only --output results/gate_C/stat_lock/compatibility_server > reports/gate_C_stat_logs/compatibility_server.txt 2>&1'
rsync -a 10.200.13.23:/data1/shengen/COMET_C_STAT_20261113/results/gate_C/stat_lock/compatibility_server/ results/gate_C/stat_lock/compatibility_server/
scp 10.200.13.23:/data1/shengen/COMET_C_STAT_20261113/reports/gate_C_stat_logs/compatibility_server.txt reports/gate_C_stat_logs/compatibility_server.txt
```

Inspection succeeded: host amax, Python3.12.3,256 CPUs, about476GiB available
memory and6.7TiB disk available at inspection. These are environment observations,
not resources consumed by C-STAT. Clone/copy succeeded. The server compatibility
command exited1 at F/0000 after the ten A–E fixtures matched; its mismatch and
traceback are preserved. No confirmatory ID was drawn on the server. The strict
bytewise comparison was not weakened. The local final compatibility passed, so
execution uses the local environment. Detailed difference diagnosis is separate.

## Authorized confirmation launch

Readiness artifact `results/gate_C/stat_lock/readiness_decision.json` records
GO_LOCAL_ONLY,0 confirmatory draws before the gate, final runner/science/input
hashes, 481 prelaunch tests and12 matching historical seeds. The already
authorized6000-ID batch was then launched with six CPU worker processes:

```sh
.venv/bin/python -m experiments.gate_c_confirmatory --confirmatory --compatibility-report results/gate_C/stat_lock/compatibility_local_final/compatibility_result.json --workers 6 --output results/gate_C/confirmatory > reports/gate_C_stat_logs/confirmatory_local.txt 2>&1
GIT_TERMINAL_PROMPT=0 git -c http.proxy=http://proxy-dku.oit.duke.edu:3128 push --set-upstream origin codex/gate-c-stat
```

No seed subset, outcome-based early stop, radius change or analysis change was
introduced. Progress inspection reads completed-ID counts/resource metadata,
not intermediate coverage to select settings. Final execution status, resources,
independent validation, plots, resume and result synchronization are appended
when completed. No D-stage experiment or independent Overleaf write was run.

Independent review found a label issue in the new future D1 proposal table:
`ceil(bound)+1` is sufficient but is not always the minimum integer N. The new
column was renamed `sufficient_integer_N_for_abs_gap_gt_2r` and design-only
export rerun (exit0; `D_design_only_label_correction.txt`). No bound, frozen
C-STAT source, selected design, outcome or primary analysis changed. This is a
future-proposal column clarification, not a defect in the frozen experiment.

Final analysis-test run:

```sh
.venv/bin/python -m pytest -q > reports/gate_C_stat_logs/final_pytest.txt 2>&1
```

Exit0:485 passed in20.18s, including all472 baseline tests. No pytest failure.
An optional `ps ... | rg ... && pmset -g batt` monitoring probe was denied by
the filesystem sandbox at `ps`, exit1; pmset did not execute. No process-control
or science change followed. The runner's own portable resource measurements
remain the authoritative observations.
`git diff --check` flagged the new D1 CSV header's standard CRLF ending after
its column rename (exit2). Only the two new D-proposal CSV exports were made LF
and their new exporter given `lineterminator='\n'`; numerical cells are unchanged.
All frozen CSV files retain their original bytes. The next diff check passed.

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

Inspection succeeded: host amax, Python3.12.3,256 CPUs, 476,385 MiB available (about 465 GiB)
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

Resource-only read checks during the long batch used escalated read-only
`ps -o pid,ppid,%cpu,rss,etime,command -ax | rg 'gate_c_confirmatory|spawn_main|resource_tracker'`,
`man taskpolicy | col -b`, the SDK's PRIO constants, and
`ps -o pid,stat,nice,pri,command -p 49062,49071,49072,49073,49074,49075,49076`.
The six workers were running with NI0/PRI31. No priority, worker count,
scientific setting or scheduling policy was changed after these observations.
A read-only monitoring process prints completed-ID/failure counts every50s;
it does not inspect coverage for selection and consumes no random streams.
A transient `caffeinate -i -w 49062` assertion keeps idle system sleep from
interrupting the active local batch and ends when that batch process exits.
It does not change scientific code, settings or permanent power configuration.

A local storage check (`df -h .` and `du -sh results/gate_C/confirmatory`,
exit0) recorded86GiB available and64MiB partial outputs in `local_disk_space.txt`.
The future D1 proposal clarifies that its gap labels a predeclared probe and
other candidate truths derive from one common potential-outcome model; D2
clarifies context-graph degree versus the stochastic conflict graph. These are
outcome-blind proposal clarifications, with no new draws or C-STAT change.
The nontriviality heatmap labels POINT_ONLY/F-graph cells N/A while retaining
the frozen numeric metrics; the no-certified-decision panel correctly retains
100% for those methods. This presentation change does not change an endpoint.

Two reporting-only inspection errors occurred while the batch continued:
`cat reports/gate_C_stat_audit/methods_validation.md` exited1 because that
report lives under the independent-validation output directory, not the script
directory. A subsequent log-append patch failed its context check and made no
change; the corrected patch succeeded. Neither error ran an experiment or
affected a checkpoint, statistic, source lock, or test result.

Final delivery check:

```sh
.venv/bin/python -m pytest -q > reports/gate_C_stat_logs/delivery_pytest.txt 2>&1
```

Exit0: **485 passed in23.20s**. No pytest run failed. The main confirmatory
process subsequently exited0 with all6,000 logs complete. Its immutable
run-manifest/candidate provenance is launch commit `5f9a221062e67af492f1145dfd7ed3bec050de15`.
The invocation JSON's `git_sha` is sampled at completion and therefore records
`3542853df786f32cce5d1b49ae7b7910919a76d3`, after new reporting/proposal commits.
The actual runner SHA and all26 scientific source hashes stayed unchanged;
this is a metadata timestamp distinction, not a scientific code revision.

## Completed confirmation, recovery and independent analysis

The main command exited0. The completion-gated controller then ran these
commands, each with exit0; exact subprocess argument arrays and log filenames
are saved in `gate_C_stat_logs/postprocessing_commands.jsonl`:

```sh
.venv/bin/python -m experiments.gate_c_confirmatory --confirmatory --resume --aggregate-only --compatibility-report results/gate_C/stat_lock/compatibility_local_final/compatibility_result.json --workers 6 --output results/gate_C/confirmatory
MPLCONFIGDIR=/tmp/comet-matplotlib .venv/bin/python reports/gate_C_stat_audit/validate_confirmatory.py --input results/gate_C/confirmatory --output results/gate_C/confirmatory/independent_validation --phase confirmatory --figures
.venv/bin/python reports/gate_C_stat_audit/finalize_reports.py
```

The resume skipped all6,000 assigned IDs, drew zero new logs, and preserved
every completed checkpoint byte. The independent analysis passed28,884,898
checks over1,134,000 candidate records and all84 summaries, including exactly17
primary Holm diagnostics. All222 files present at the starting evidence commit
and all26 science modules remain byte-identical. The original12 preflight logs
are outside every confirmatory numerator and denominator.

Main invocation:10,389.879 wall seconds,55,394.379 combined parent/child CPU
seconds. Zero-draw resume:288.065 wall seconds,282.354 CPU seconds. The total
recorded invocation cost is10,677.944 wall seconds and55,676.733 CPU seconds.
Parent peak RSS211.500MiB and maximum child peak116.828MiB are separate process
high-water marks, not summed concurrent memory. The independent statistical
validation measured87.861s wall and86.030s CPU before export/figure rendering;
its measured peak at that point was112,590,848 bytes. No per-method memory was
inferred from these measurements.

After reviewing the completed outputs, report presentation was regenerated
with the following command (exit0; separate log preserves the original run):

```sh
.venv/bin/python reports/gate_C_stat_audit/finalize_reports.py > reports/gate_C_stat_logs/confirmatory_report_presentation.txt 2>&1
```

It states the actual successful resume, distinguishes launch/finish provenance,
and displays the inapplicable F graph nontriviality cell as NA. The frozen CSV
metric, statistics, plots and checkpoints did not change. All five actual
figures were visually reviewed; their companion captions and ten export hashes
are preserved in the figure-review artifacts. No D-stage outcomes were drawn.

Final resource-caption clarification used the same report renderer (exit0),
with output saved separately as `confirmatory_report_resource_caption.txt`.
It now explicitly labels the combined main-plus-resume total. The manuscript
proposal was rebuilt with separate main/resume costs and refreshed provenance;
all five TeX/BibTeX commands and `git apply --check` exited0. All nine pages
were reviewed, including the corrected resource paragraph, and all45 original
paper files remained unchanged.

Packaging computed SHA-256 for127 completed export/analysis files in
`export_checksums.json`; checkpoint hashes remain in the complete checkpoint
index. No file is50MiB or larger. A complete new-path inventory is saved as
`reports/gate_C_stat_modified_files.tsv`; every starting file is unchanged.

`git diff --check` with CR-at-EOL allowed exited2 only on two blank context
lines encoded inside the reviewable unified patch (lines554 and559). Those
spaces are patch syntax and were retained; the patch applicability check
exited0. The source/prose check excluding that literal patch file exited0:

```sh
git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --check -- . ':(exclude)paper/rewrite_proposals/cstat/paper_rewrite_diff.patch'
git apply --check paper/rewrite_proposals/cstat/paper_rewrite_diff.patch
```

These inspection/presentation issues did not alter scientific outputs or
produce any failed confirmatory log. All485 pytest tests passed.

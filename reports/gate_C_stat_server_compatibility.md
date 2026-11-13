# Server compatibility failure: historical Pareto arithmetic

**Decision: server C-STAT execution is BLOCKED; use the historical-compatible local environment only.** This is an execution-environment compatibility failure. The investigation found no new mismatch between the frozen mathematical model, estimator formula, confidence denominator or oracle separation. The existing distinction between exact-real proofs and ordinary floating-point evaluation still applies; this diagnostic does not establish exact finite-precision coverage.

The server compatibility run reproduced A–E exactly, then stopped at the historical `gate-c-v1/preflight/F/0000`. It did not draw any of the 6,000 confirmatory IDs. No tolerance, sampler, estimator or scientific configuration was changed to make the server pass. F/0001 was not reached by this failed compatibility invocation. The local final compatibility invocation passed all twelve historical seeds and reproduced all 84 historical summary rows byte for byte.

## Exact discrepancy

The failed scientific-payload comparison has 225 unequal leaves: the top-level `observed_data_sha256` and the same hash repeated in all 224 candidate records. Every other compared field—including all estimates, radii, endpoints, truths, coverage indicators, statuses, decisions, extrema and diagnostic quantiles—was identical. Equality of these aggregate quantities does not excuse unequal input observations.

| Quantity | Exact result |
|---|---:|
| Historical logged rows compared | 32,768 |
| Potential-outcome primitive draws compared | 16,384 |
| Differing `uniform ** (-1 / alpha)` evaluations | 20 |
| Largest power difference | 1 ULP of the local value |
| Differing potential-outcome values after multiplication and addition | 13 |
| Differing observed independent clusters | 7 |
| Differing copied observed rows | 28 |
| Largest absolute observed-reward difference | 2.220446049250313e-16 |
| Largest observed-reward difference / local ULP | 16 |

The 16-ULP figure concerns a small resulting reward after adding the conditional mean to signed noise. It is not a 16-ULP discrepancy in the power primitive. All primitive uniform values, signs, exponents and conditional means are identical. The first arithmetic difference occurs in the power evaluation; platform/Python/libm differences therefore explain the observed mismatch at that expression. This experiment does not isolate a particular library implementation as the sole cause.

- Local: Python 3.12.2, conda-forge / Clang 16.0.6, `macOS-27.2-arm64-arm-64bit`.
- Server: Python 3.12.3 / GCC 13.3.0, `Linux-5.15.0-136-generic-x86_64-with-glibc2.39`.
- Identical frozen sampler SHA-256: `60c7d2bf5b3dfd68974784306f48d846858257cc75aff5ee0c30c817203cb1c8`.
- Local observed-data digest: `a059470a5e004089ecaff45180c6fac9b1c7c7f5e0ff730b8d6bdb90f35ae794`.
- Server observed-data digest: `976df42468de97458204f2a8294833c7b695a306ce11be3b3bef7fa5cc14b117`.

The location is `comet/gate_c_simulation.py:39`, reached by `_symmetric_pareto` and the frozen potential-outcome loop. That source remains unchanged. Historical seed reruns for this diagnosis use only F/0000 and cannot enter confirmatory numerators or denominators.

## Preserved evidence and reproduction

- `results/gate_C/stat_lock/compatibility_server/compatibility_checks.json`: A–E pass and F/0000 failure.
- `results/gate_C/stat_lock/compatibility_server/mismatch.json`: complete expected and actual scientific payloads.
- `results/gate_C/stat_lock/platform_diagnostic_local_F0000.json.gz` and `platform_diagnostic_server_F0000.json.gz`: all logged rows plus all primitive floating-point hexadecimal traces.
- `results/gate_C/stat_lock/server_platform_diagnosis.json`: every differing row/primitive/field, counts, maxima, source/evidence hashes and executed commands.
- `reports/gate_C_stat_logs/platform_diagnostic_local.log` and `platform_diagnostic_server.log`: actual environment and observed-data digests.
- `reports/gate_C_stat_audit/diagnose_platform_pareto.py`: historical-only, unchanged-sampler diagnostic; it refuses to overwrite existing evidence.
- `reports/gate_C_stat_audit/compare_platform_pareto.py`: exact comparison and machine-report regeneration.

Executed diagnostic commands all returned exit code 0:

```sh
.venv/bin/python reports/gate_C_stat_audit/diagnose_platform_pareto.py --output results/gate_C/stat_lock/platform_diagnostic_local_F0000.json.gz
ssh -o BatchMode=yes 10.200.13.23 'cd /data1/shengen/COMET_C_STAT_20261113 && python3 - --output results/gate_C/stat_lock/platform_diagnostic_server_F0000.json.gz' < reports/gate_C_stat_audit/diagnose_platform_pareto.py
scp -o BatchMode=yes 10.200.13.23:/data1/shengen/COMET_C_STAT_20261113/results/gate_C/stat_lock/platform_diagnostic_server_F0000.json.gz results/gate_C/stat_lock/platform_diagnostic_server_F0000.json.gz
.venv/bin/python /tmp/compare_cstat_platform.py
.venv/bin/python reports/gate_C_stat_audit/compare_platform_pareto.py
```

The final comparison program is preserved in `reports/gate_C_stat_audit/compare_platform_pareto.py` and can be run from the repository root. Regenerating the source diagnostic requires a new output filename, preserving the original evidence. The server is not admitted by suppressing the data digest or widening an equality tolerance.

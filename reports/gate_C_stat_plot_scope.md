# C-STAT reporting-only plot adjustment

Before reading any completed confirmatory corpus, the error-to-radius figure in
`reports/gate_C_stat_audit/validate_confirmatory.py` was adjusted to mark the
observed maximum for every eligible cell/method with an open diamond and to
set the vertical axis to include every maximum. The existing box represents
the IQR/median with min/P90 whiskers, and zeros remain included. Thus rare
large errors are visible rather than hidden by omission of boxplot fliers.

This changes presentation only. It changes no frozen scientific source,
simulation, estimator, confidence budget, seed, endpoint or statistical summary
calculation. The adjustment was checked by regenerating only the twelve
historical preflight records; zero confirmatory outcomes were read or generated
for this change. Confirmatory figures will use the same reporting code only
once the full 6,000-log allocation is complete.

```sh
MPLCONFIGDIR=/tmp/comet-matplotlib .venv/bin/python reports/gate_C_stat_audit/validate_confirmatory.py --input results/gate_C/preflight/batch --output results/gate_C/stat_lock/independent_preflight --phase preflight --figures
```

The actual rerun log is `reports/gate_C_stat_logs/independent_preflight_maximum_markers.txt`.

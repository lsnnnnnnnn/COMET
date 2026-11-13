# C-STAT execution and resource record

**C-STAT execution PASS:** all 6,000 assigned independent logs completed; all 1,134,000 candidate records retained. Independent statistical validation passed. No preflight observations enter these denominators.

Scientific freeze: `ab4c74fbf1ae84c0e5ffd72d77ce5b48d3fba8cb`. Launcher run-manifest commit: `5f9a221062e67af492f1145dfd7ed3bec050de15`. Runner SHA-256: `1628b05f843975ee19f3fd48cf5868717c67f0646a3f927ea8fa4cab860865ed`. Final delivery commit is recorded separately to avoid a self-referential file hash.

The immutable run manifest and candidate records retain the launch commit. Invocation `git_sha` is sampled when the invocation finishes; it can name a later commit containing only new reporting/proposal files. The frozen scientific sources, inputs and actual launcher bytes stayed unchanged throughout. These two provenance timestamps are not interchangeable.

## Assigned work and outputs

Exactly 1,000 logs in each A–F cell, all seven methods and both levels paired. A contributes14,000 records; B–F each contribute224,000. Complete IDs are in `run_manifest.json` and per-ID input/payload/file hashes in `checkpoint_index.json`. Every checkpoint is an atomic gzip JSON; all raw metric columns are also exported in six compressed CSV shards. There are84 summaries and17 prespecified primary tests.

Actual invocation count: 2. Saved confirmatory execution-error files: 0. Detailed event order is in `events.jsonl`; no failed or incomplete ID is silently excluded.

|Invocation|Status|New completed|Skipped|Wall s|Parent CPU s|Children CPU s|Parent peak MiB|Max child peak MiB|
|---|---|---:|---:|---:|---:|---:|---:|---:|
|1794585752277625000|COMPLETE|6000|0|10389.879|234.795|55159.584|211.500|116.828|
|1794596154274708000|COMPLETE|0|6000|288.065|282.354|0.000|206.703|5.000|

Total recorded invocation wall: 10677.944s; parent+children CPU: 55676.733s. Maximum parent RSS: 211.500MiB; maximum child process peak: 116.828MiB. The runner wall/CPU timer starts after initial source, configuration and environment setup; it then includes checkpoint scanning, computation and aggregation. RSS is cumulative process high-water including startup, not summed concurrent memory or standalone per-method allocations. Per-method/level timings are family-call costs; copies in candidate rows must not be added repeatedly. Parallel per-log wall sums are not elapsed batch time.

The local CPU environment passed all12 strict historical-seed checks. The server drew zero confirmatory logs: historical F data differed at floating-point power rounding, so strict compatibility rejected it. Failure traceback and primitive-level diagnosis remain in stat_lock and the server-compatibility report. No tolerance, simulation law, interval or scientific budget was changed.

The launcher fixture verified failure→resume→idempotent operation using mocked historical payloads, including immutable completed bytes and retained failures. The actual complete-batch resume then passed: zero new outcome logs, all 6,000 completed IDs skipped, and every checkpoint byte unchanged. Its resources are listed separately above and its verification is saved in `resume_integrity.json`.

Final preservation check: all 222 baseline files and all26 scientific sources remain byte-identical. No original manuscript or independent Overleaf file was changed. D1–D5 contain design-only proposals, with zero D-stage outcomes.

Commands, test exits, monitored resource probes, the server failure and synchronization history are in `reports/gate_C_stat_commands.md`. The full final pytest log reports485 passing tests; no pytest failed.

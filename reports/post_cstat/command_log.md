# New-workstream execution log

All commands here belong to the post-C-STAT workstream. No historical outcome
generator, historical runner, or full historical validator has been invoked.

- Startup: clean `codex/gate-c-stat` at `254a482d4f82c79ba8ed9c0e57c886611a681ade`;
  delivery `ca5bb878cf9635fac4381d03281df0bc8a900daa` is an ancestor.
- `git switch -c codex/query-specific-graph-auditing`: first sandbox attempt
  could not create the `.git` ref lock; the authorized escalated retry succeeded.
  No reset, checkout of an older tree, or file replacement occurred.
- Disk: approximately 80 GiB available; psutil available RAM approximately
  2.72 GiB at startup. Scientific worker concurrency remains zero at this stage.
- `.venv/bin/python -m pytest -q tests/test_source_graph_queries.py`: 14 passed.
- First combined new deterministic suite: 33 passed, 1 failed. The failure was
  pytest refusing a nested Python list in `pytest.approx`, before any comparison.
  Replaced the expected fixture with a NumPy array; no scientific formula or
  tolerance changed. This is a new test-harness failure, not a historical test
  or confirmatory-log failure. Rerun results are recorded with the final checks.

The default Matplotlib home cache was not writable; subsequent figure commands
use a workstream-local MPLCONFIGDIR. No global configuration is modified.

- Combined initial new implementation suite: 85 passed in 1.23s. Additional
  paired-contrast/runner/pipeline checks are run and recorded after integration.
- Analytic design command:
  `.venv/bin/python -m experiments.post_cstat_design --multipliers .25,.5,1,2,4 --output results/post_cstat/design_v0`.
  Produced 216 fixed-overlap and 216 declining-overlap rows; new outcomes 0.
- Figure command:
  `MPLCONFIGDIR=/private/tmp/comet-post-cstat-mpl .venv/bin/python -m experiments.post_cstat_figures`.
  Produced three actual analytic figures in PNG and SVG; new outcomes 0.
- New local `pdflatex` builds 1–3 all exited 0. After two concrete layout
  repairs (a branch-name text box and an inline lower-bound expression), build
  3 had no overfull box or undefined reference. Final post-review build and
  rendered-page inspection are recorded separately.
- E6 download: initial curl exited 6 (DNS); authorized same-URL network retry
  exited 56 (HTTP 403). No archive downloaded, no fallback dataset selected.
  Both commands finished and no download process remains.

- 2026-11-14T08:59:44.287932+00:00 E1 completed: original144 + fast resume11856 =12000; failedunits0. Fast invocation4802.6598s wall/4559.2765s CPU; original interrupted invocation382.733s wall/329.123s CPU retained. E1 analysis completed96primarydiagnostics, all1000/1000coverage, falseclaim0; newanalysisdraws0.
- E2 completed1800units, failedunits0; analysis60primarydiagnostics, all300/300coverage; matchedgenericwidthdifference0. E3 active session10347; E5 active25733, one synchronous worker each. No third scientificworker.
- Negative controls source/config committed e6f61a9;100supplementary IDs frozen fingerprint43dedc67e060653d60b7b96f7032633c29b4e06882df5473ec4d9a19b314cdf9, no draws yet.
- New negative/offlineE6/detailed diagnostic fixture test group:49passed in1.13s, scientificdraws0.
- Reconciled design_v1:216fixed+216declining algebraic rows, exact49grid, newdraws0; six PNG/SVG outputs generated. Historical A remains analytic only.

- 2026-11-14T09:24:41.106896+00:00 E2 independent diagnostics completed 1800 verified checkpoints, zero mismatches. E5 original invocation ended at an observed checkpoint boundary:197complete/0failed,1326.730s wall/1285.408s CPU. Firstunfinished0197 resumes with the same ID and seed. Five complete-fixture cache tests establish canonical scientific byte equality; launcher commit5e84bda leaves frozen f07 science unchanged. Fastresume session39732. All197 earlier compressed checkpoint SHA values still match. At most one incomplete E5 operational attempt, plus at most one in E1; no independent ID is excluded.
- ANCHORS:34tests passed in3.02s; source3f71389, protocolccbb088, fingerprint44440532c1238832e2d356967d96ab9e6aabc7282b7d7355e988e8fb4ab6cfb6. Exact nontrivial e1=.25 was chosen before any anchor outcome; target/gap/budget unchanged.
- E6 data-gated runner, finite-population oracle, analyzer and tests committed e9b4a54. Agent recorded35fixture tests passing. Actual official archive unavailable: no E6freeze orMC.

- 2026-11-14T09:58:03.062424+00:00 E3 complete3600/0failed in4088.333s wall/3952.311s CPU. Final analysis108primary comparisons all300/300familycoverage, nofalseclaims. Direct contrast positiveimprovement300/300 onlyfullsupport/moderate/bounded vsjointlevels0/300; otherCOMETcells0/300. E4 active25200; E5fast39732.
- E5posthoc diagnostic7fixturetests passed0.51s; E5shard3fixturetests passed4.68s. Only operational time/warmup counters excluded from shard comparisons; dispatch grid/multiplier and all science compared. Noactualshardstarted.
- Independentboundedreview found one lower-bound wording ambiguity (response moment vs IPWmoment), repairedinpaper; nofrozenarithmeticchanges. Neighboring LTT/HCPI original sources verified and kept separate from direct eligible graphbaselines.
- Local progress build wrapper initially used a root-relative .venv path from paper/post_cstat and exited127 before TeX. Corrected to absolute interpreter path; no scientific file or result was affected.

- 2026-11-14T10:07:00.899617+00:00 Consolidated NEW-only deterministic suite: git-diff-added29testfiles;354passed in39.00s. No historical test suite, old sample generator or C-STAT rerun. Currentfull-source/historical-source preservation checks pass; E1first144 andE5first197compressedbytes unchanged.
- Serial queue waiting supervisor v1 stopped before any child to add full-stage status gates; exit130 and originalstderr/state retained. v2 session90731 waitsforE4complete thenrunsone child atatime; no scientific trial interrupted by this supervisor repair.

- 2026-11-14T10:25:00.557042+00:00 E6sameofficialZIP bounded standard-UA retry exited56/HTTP403,zero bytes; noarchivefile andzeroE6trials. AccessremainsDATA_BLOCKED; syntheticworkerscontinued.

- 2026-11-15T04:16:55.230370+00:00 Reconnected; E4 COMPLETE7200/0failed. Local sleeping serial supervisor90731 stopped before any child (exit130) for user server/tmux steering. E5 remains original host; no mixed environments. Server tmux available, isolated directory not yet created; supplementary suites have zero outcomes and will receive versioned environment-only pre-outcome amendments. Old protocols preserved.

- 2026-11-15T04:30:24.504693+00:00 Server supplementary admission completed: explicit fixture comparison22413 numeric/23255 exact leaves, zero mismatches under unchanged tolerances; each platform data digest verified against its own512-row fixture arrays. Existing6digest differences and failed ±.1 primitive input retained. Pre-outcome environment config abdeab0; snapshot f5ba837; server-v2 protocol fprints8ffce7eb/d21665e9. tmux comet-post-cstat-20261115 running one supplementary child after local details completed. Original local E4 closed7200/0fail, primary192all300/300; E1/E3/E4 independent details allzero mismatches. Only E5 remains local scientificworker. Actual four E1-E4 scientific plots generated and visually inspected; no extra scientific draws.

- Local documentation commands that initially used the wrong working-directory-relative interpreter, a file rather than directory for ledger --output, and a shadowed path variable in the fixture comparator failed before affecting scientific outputs; corrected commands succeeded. All scientific configuration/source hashes remain unchanged.

- 2026-11-15T04:44:39.246852+00:00 Server tmux serial queue COMPLETE, pane dead1/exit0: ANCHORS1600 + negative100, no unitfailures, original analyses complete. All1718returned files match compressedbytes SHA (25,676,424bytes). Local fullE5fastworker stopped gracefully after3033cumulative units (fast2836,0fail); preserved all3033bytes in E5_before_shards_snapshot.json. Its runner-reported monotonic elapsed11002.658s, CPU10756.485s; processpselapsed differs and is not presented as uninterrupted calendar compute. Atmostone more partial operational attempt, total<=3. Two tested exclusive full-frozen-IDmod2 shards65251/70298 started in original environment, no server computation left.

- 2026-11-15T04:48:47.703972+00:00 Clarification of server completion status: ANCHORS invocation failed_units=1 counts one COMPLETE_WITH_CONFIDENCE_FAILURE secondary90% IID-bounded scalar-betting log; analysis execution-failed_units=0. All1600 units retained:1599COMPLETE+1confidencefailure. All68primary95% comparisons200/200, secondary betting199/200. Do not interpret earlier no-unitfailure shorthand as zero empirical misses acrossbothlevels. Negative100allCOMPLETE. Strong IIDbounded DR-EB narrower thanCOMET; IIDheavyCatoni narrower, bothheavy detection0.

- 2026-11-15T05:44:42.208409+00:00 FINAL: all30300newIDs complete (28600primary+1700supplementary), E6reserved1000unfrozen onlyremaining. E5fullanalysis4000/0unknown; independent reconstruction12000families/64000frames0mismatches. All3033pre-shardcompressedbytes unchanged; atmost3partialattempts. Servertmuxpane dead1 exit0; alllocalMC/analysis/supervisorPIDs absent. Old6000compressedbytesSHAallmatch; oldconfirmedconfigs/ninepageproposalbyte-diffempty. Final24pagePDF two-passclean andallpagesrendered/visuallyreviewed; finaldeliverycopy SHA59fed09dccecba4c25920a44784c706d8c53d438ae0fcb77cf98bca17c892943. E5plotv1/v2 layoutdrafts retained, finalv3percentannotationspreserve0.2%events; no science changed. One later wrong-CWD draftcompile exitedbeforeinput sections; correctreleasebuildclean. NoOverleafsync/push, noactivebackgroundscientificwork.

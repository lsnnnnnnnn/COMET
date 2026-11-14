# Negative controls v1: pre-freeze design

Status: configuration prepared and validated; no freeze and no scientific draw
was performed for this task. Commit the new configuration and its scientific
sources before invoking the existing freeze CLI.

This is a supplementary 100-unit study: four controls, 25 independent complete
logs each, N=32,768, one frozen coordinate, and threshold .6. The .05/.10 levels
and three engines share every log. The study consumes 100 of the <=400 negative
control allowance and the global 32,000 cap; it adds zero primary comparisons
and does not change E0, its 17 tests, or the new primary diagnostic families.

|Control|True moment|Prespecified diagnostic mechanism|
|---|---:|---|
|Hidden shared shock|.45|All rows share a single ±.25 shock; false edgeless declaration. The actual N-clique is represented analytically, never allocated.|
|Wrong propensity|.68|Actual e1=1/5, declared .5; the incorrectly weighted DR expectation is .5.|
|Missing clipping bias|.8|Fixed tau=.01, p=1.5; clipped expectation .4901, exact bias .3099; the heuristic omits the bias debit.|
|Evaluation nuisance leak|.68|Both nuisance states copy their own observed Y; the resulting expectation is .32, with no fabricated cross-row dependence.|

The spike residual p-moment is 5.07400300800637; the
proved worst-case clipping-bias debit is 19.5298466836097. The valid
bias-corrected branch can therefore be vacuous and must remain in the results.
The project 49-point grid is recorded as reference metadata only: this
diagnostic's fixed tau=.01 was explicitly prescribed and is not optimized.

Every intentionally invalid interval is exported as
HEURISTIC_INTENTIONALLY_INVALID_ASSUMPTIONS. Honest false declarations return
ASSUMPTION_UNVERIFIED with no interval; an all-refusal arm supplies no observed
zero-error certification evidence. Correct references use the actual e and a
fixed nuisance, the full clipping debit, or the deterministic [0,1] range when
the true graph is complete. No favorable/error outcome affects retention.

Raw rep0000 for each control and every numerical/coverage failure are retained.
One immutable checkpoint is one unit; engines and levels are not extra units.
The runner checks the global results/post_cstat artifact and unit totals, uses
one synchronous CPU worker, and relies on the coordinator for the <=2 total
scientific-worker limit. All known .2/.005 probabilities use exact finite
uniform denominators 5/200; float interval arithmetic retains declared padding.

Only EXPERIMENT_BLUEPRINT.json remains unavailable. The explicit user waiver
is recorded in task_materials/post_cstat/INPUT_RESOLUTION.md; the other actual
planning inputs and that receipt were checked without inventing a blueprint.

Provenance before freeze:

- Configuration SHA-256: `6a3619005da4a58dc16422576faaf6e757977a68773024c7041dc59f307e6057`.
- Negative-control source SHA-256: `605b5a74f0b5b41dfc8ff9c14fff1877a6a89ebe80bdc10b9f9041e0f54b3343`.
- Master seed: `2026111408`; domain: `comet-post-cstat-v1/negative-controls/v1`.
- This note is an analytic design record, not observed performance.

After committing the configuration/science, freeze and run from the repository
root (at most two scientific workers active in total):

```sh
.venv/bin/python -m experiments.negative_controls --freeze --config configs/post_cstat/negative_controls_v1.json
.venv/bin/python -m experiments.negative_controls --run
.venv/bin/python -m experiments.negative_controls --status --list-ids
.venv/bin/python -m experiments.negative_controls --analyze --output results/post_cstat/negative_controls_analysis_v1
```

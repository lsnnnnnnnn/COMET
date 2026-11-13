# C-STAT scientific lock audit

Starting experiment commit: `06a39b89e579aef57d14ae51e86d74ecf9b6b768`,
verified against GitHub `refs/heads/codex/gate-c-preflight` before changes.
Scientific freeze: `ab4c74fbf1ae84c0e5ffd72d77ce5b48d3fba8cb`.
New work is on `codex/gate-c-stat`. No previous file is edited and no Overleaf
operation is authorized or performed in this phase.

The new supplied master was read completely, including the stop-on-mismatch
rule, 6,000-run definition, 17 primary tests, future D1–D5 and proposal-only paper
instructions. Its ZIP is extracted verbatim in `task_materials/gate_C_stat/`
with SHA-256. This user request authorizes C-STAT after readiness; the older
preflight-only JSON and entry point remain byte-identical and are not relabeled.
A new launcher records separate phase authority and schema.

## Executed audit evidence

- `experiments/audit_gate_c_scientific_lock.py`: **328 checks, zero failures**;
  all **222** tracked files at the evidence commit are unchanged. Exact
  per-file before/after hashes are in
  `results/gate_C/stat_lock/scientific_lock_audit.json`.
- All **26** frozen scientific modules match both the original preflight manifest
  and the freeze commit. Their canonical digest is
  `ccb98ce6b62fedabab850325e118d5160021ca88080c70742c0e35ce441d0cd0`.
- Frozen config SHA-256:
  `b834e7b409bb008ba0d2b6e591515873831f87d036fdc53ed0392d0b94012ff4`.
  The checks compare actual file bytes with the freeze.
- Frozen seed manifest SHA-256:
  `9d04a99066a7c8c0234f226f4dddfa33e9c0171fdb6f3486c30452389c667eab`.
  All 6,012 IDs and seven role seeds per ID reproduce; 12 preflight and 6,000
  confirmatory IDs are disjoint; each cell has exactly 1,000 confirmations.
- Twelve saved checkpoints retain their original payload and file hashes. All
  2,268 candidate records are retained; all 84 preflight summary dictionaries
  recompute bytewise exactly with frozen statistics. Preflight is never added
  to a confirmatory numerator or denominator.
- **472 original tests passed in 5.68s** before launcher additions. None of those
  test files changed. This is implementation evidence, not a coverage theorem.
- Independent proof audit: **22,837 checks, zero failures** in
  `reports/gate_C_stat_audit/independent_proof_checks.json`; full derivation and
  source references are in `gate_C_stat_independent_proof_audit.md`.

## Model and theorem decision

No new theorem-to-code discrepancy was found. Conditional on exogenous D, the
registered binary assignments and independent cluster potential draws produce
independent macro-blocks and sufficient complete-clique score graphs. Repeated
context patterns give common block targets for MOM. Fixed (.5,.5) nuisance and
exact known logging identify the fixed-window target without fitting bias.
Known conditional p-moment envelopes are supplied by the declared bounded or
Pareto location class; no sample tail estimate enters a radius. The oracle is
called only after all seven methods at both levels finish for a log.

The historical MOM uses 32^(1/p) and its original K rule; exact MOM uses the
same group moment bound with fixed eta=1/8 and exact rational binomial selection.
Graph mean uses the separately proved sqrt(mV/alpha) bound, with F strictly
NOT_APPLICABLE. IPS/DM/DR remain POINT_ONLY. Full feasible range is the known
conditional-mean-class benchmark, including F, not a bounded-Y assertion.
Each method/level has its own family confidence statement. There is no
post-observation shortest-method selection or cross-method joint 95% claim.

Ordinary floating-point score/radius arithmetic and the moment-dominated finite
Pareto grid are already declared in the frozen model. This audit does not
upgrade them to an outward-rounded machine proof or claim a finite machine law
literally has infinite variance. It also does not prove arbitrary adaptive
histories, mutual cross-fitting, hidden cross-block shocks, sparse-graph
sharpness or deployment safety.

An unexpected refused/inapplicable status among the 17 eligible primary
comparisons must retain its outcome/checkpoint and fail the launcher, not become
an omitted coverage denominator. An applicable empty intersection remains a
coverage failure. Negative controls distinguish these cases.

## Compatibility and launch gate

The separate runner uses a strict 26-file allowlist; newly added operational
modules have their own launcher hash. This avoids changing old preflight
fingerprints. Compatibility must regenerate the same twelve historical seeds
and compare canonical scientific bytes, excluding only documented execution
metadata (phase/schema/provenance/timing/RSS), plus exact partitioned-summary
agreement. It must run on the actual execution environment. No confirmatory
ID may be drawn for tuning this test. Passing evidence, final runner hash,
execution commit and launch decision are appended after completion.

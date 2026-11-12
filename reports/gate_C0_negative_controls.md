# Gate C0 negative controls and independent pilot review

Scope: C0 working tree over the completed Gate A+B baseline. These are deterministic guard/algebra checks and tiny runner fixtures, not estimates of failure rates or coverage. Actual targeted execution: **24 passed in 1.89s, no failures**, logged in `reports/gate_C0_logs/negative_controls_pytest.txt`.

The six required controls are accounted for below. **Model-tag refusals are honest declared controls:** they test rejection of a declared unsupported model. They do not demonstrate statistical detection of a hidden violation in mislabeled data. Both certifiers reject any unsupported tag as `UNVERIFIED_ASSUMPTION / UNSUPPORTED_PROOF_MODEL`, with no interval (`comet/certification.py:18–20`, reused at `comet/bounded_variance.py:79`). Their theorem requires the registered generator's assumptions, not merely the string label.

| Required negative control | Exact test locations | Observed/asserted outcome and limitation |
|---|---|---|
| Permanent shared shock across evaluation blocks | `tests/test_c0_integration.py:83–91`; `tests/test_bounded_variance.py:149–155` | The `hidden_permanent_shared_shock` declaration returns `UNVERIFIED_ASSUMPTION`, `lo=None` in both methods. No claim that empirical correlations diagnose a hidden shock. A common Rademacher shock makes the variance of a sum of B identical block values B², versus B under independent unit-variance blocks. Such data mislabeled as independent may pass structural guards. |
| False dependency graph with missing edges | `tests/test_bounded_variance.py:45–69`; declared tags at `tests/test_c0_integration.py:83–91` and `tests/test_bounded_variance.py:149–155` | Four copies of one Rademacher have sum variance 16; a falsely supplied edgeless graph gives the arithmetic bound 4. The test explicitly records this assumption failure. A syntactically invalid coloring is rejected as `INVALID_COLORING`; declared false-graph models get `UNVERIFIED_ASSUMPTION`. The certifier exposes no arbitrary-graph argument. A proper coloring proves consistency with the supplied edges, not that all stochastic dependencies were included. |
| Nuisance trained on evaluation outcomes | `tests/test_core.py:38–43`, `tests/test_core.py:200–209`; `tests/test_bounded_variance.py:158–163`; declared tags above | The exact counterexample has Y=S, logger probability 1/2, q(1)=0.9 and fitted means both equal to observed Y: expected DR score is 0.5 instead of target 0.9. Changing a logged nuisance away from the registered fixed fit returns `UNVERIFIED_ASSUMPTION / FIXED_NUISANCE_OR_REFERENCE_MISMATCH`, no interval. Hidden training provenance cannot be reconstructed from coincidentally matching fitted values. |
| Target puts positive mass on a zero-probability exposure | `tests/test_core.py:46–52`; `tests/test_bounded_variance.py:35–42`, `tests/test_bounded_variance.py:164–166` | Score and variance helpers raise `SupportError / NONIDENTIFIABLE_TARGET_SUPPORT`; common q=e=0 states remain allowed by the helpers. The registered synthetic configuration refuses e=0 as `NOT_CERTIFIABLE / SYNTHETIC_LOGGING_REQUIRES_BOTH_EXPOSURES_SUPPORTED`, no interval. No artificial denominator clipping repairs identification. |
| Failure of the asserted finite p-moment bound | Declared `p_moment_violation` at `tests/test_c0_integration.py:83–91` and `tests/test_bounded_variance.py:149–155`; concrete out-of-range reward at `tests/test_bounded_variance.py:158–163` | The declared violation returns `UNVERIFIED_ASSUMPTION`. An observed Y=2 returns `NOT_CERTIFIABLE / REGISTERED_BERNOULLI_REWARD_REQUIRED`, no interval. The latter detects violation of this API's bounded-Bernoulli model; it is not a test for infinite p-moments. With bounded Y, fixed bounded nuisance and fixed strictly positive finite-state e, the registered score has finite moments. An infinite-moment DGP is outside this model and cannot be certified by retaining its label. |
| Outcome-selected K or cap without adjustment | `tests/test_c0_integration.py:67–80`, `tests/test_c0_integration.py:83–91`; `tests/test_bounded_variance.py:149–155` | Caller arguments `K`, `eta`, `clipping_cap` raise `TypeError`; `mom_majority_rule='outcome_selected'` returns `NOT_CERTIFIABLE`; declared outcome-selected K/c models return `UNVERIFIED_ASSUMPTION`. K is computed from family size, confidence budget and B; eta is fixed. There is no clipped certifier in C0. Selecting among the reported methods after seeing outcomes is not a new certified procedure. |

Additional tested refusals cover future-outcome-conditioned design and uncontrolled between-block dependence. Every listed model-tag test asserts absence of an interval. Tests deliberately do not assert an empirical undercoverage threshold.

Independent review of `experiments/gate_c0_pilot.py` found no oracle-based selection in the implemented pilot:

- Settings fix each family, p, method list and threshold; both MOM variants and graph Chebyshev are computed at lines 82–94, and the support-only benchmark at lines 95–107. Oracle truth is first joined for reporting at line 115, after every certificate for that log/confidence level is complete. Observed ESS and tail summaries at lines 69–81 are diagnostics, never radius inputs.
- Coverage is grouped by independent replication at lines 154–170. A family succeeds only when every candidate covers. Full-range intervals remain in the coverage denominator; candidate rows and methods are not treated as independent Monte Carlo draws. `coverage_given_issued` is descriptive conditional coverage, not the theorem's unconditional guarantee; `issued_and_covers_rate` retains all replications. An empty support intersection is unissued and cannot certify safety.
- Width summaries at lines 165–179 describe issued, nonempty candidate intervals; nontriviality rates include every candidate/family. Constraint decisions use the predeclared threshold at lines 118–130. False-safe means an issued upper endpoint certifies the constraint while the joined oracle truth exceeds that threshold. This is a fixed-window numerator constraint, not deployment safety.
- `tests/test_c0_pilot.py:14–22` checks repeated-run CSV/JSON/table/plot equality using a two-replication fixture. `tests/test_c0_pilot.py:25–32` checks that infeasible MOM output yields zero issued families, undefined conditional coverage, zero issued-and-covered rate and full abstention. Both passed. Runtime measurements are intentionally excluded from byte equality.

The targeted command, run from the repository root, was:

```sh
.venv/bin/python -m pytest -vv \
  tests/test_c0_integration.py::test_declared_negative_controls_cannot_receive_a_certificate \
  tests/test_c0_integration.py::test_exact_mom_switch_uses_actual_family_and_declared_eta_only \
  tests/test_bounded_variance.py::test_variance_refuses_inapplicable_declared_models \
  tests/test_bounded_variance.py::test_missing_edges_are_an_assumption_violation_not_observationally_detectable \
  tests/test_bounded_variance.py::test_graph_variance_rejects_an_unverified_smaller_coloring \
  tests/test_bounded_variance.py::test_variance_refuses_changed_nuisance_future_features_and_unbounded_reward \
  tests/test_bounded_variance.py::test_variance_support_failure_and_common_zero \
  tests/test_core.py::test_evaluation_outcome_leak_breaks_dr_identity \
  tests/test_core.py::test_support_failure_is_never_clipped_and_common_zero_is_allowed \
  tests/test_core.py::test_frozen_design_and_timing_and_propensity_checks \
  tests/test_c0_pilot.py > reports/gate_C0_logs/negative_controls_pytest.txt 2>&1
```

No core or pilot code was changed by this independent review. These controls support the stated API restrictions. They do not establish robustness to hidden shared shocks, omitted graph edges, unknown training provenance, unknown tail moments, or outcome-driven procedure selection.

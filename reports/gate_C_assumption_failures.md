# Gate C assumption failures and strict method status — C-PREFLIGHT

This document maps the eight master-required failure controls to deterministic
tests and theorem/status behavior. It is not an empirical undercoverage study.
Model labels disclose a control's intended violation; their rejection does not
demonstrate that hidden mislabeled violations can always be detected from one
observed log. The status tests and model tests have actual passing logs at
`gate_C_logs/methods_statistics_final_pytest.txt` (57 tests) and
`gate_C_logs/model_pytest.txt` (34 tests). The phase report records the combined
final suite and any earlier failures.

References below are to the new Gate C source frozen for this preflight and to
unchanged C0 tests/proofs. `comet/gate_c_contract.py:127–166` supplies structural
checks; `comet/gate_c_methods.py:123–126,198–227` maps applicability/errors to
explicit rows with absent intervals. Actual law assumptions still carry the
proof: passing those structural checks alone does not manufacture a guarantee.

| Required control | Test and code evidence | Status / scientific interpretation |
|---|---|---|
| 1. Permanent latent shock across blocks | `tests/test_gate_c_methods.py:139–145` declares `permanent_cross_block_shock`; `tests/test_gate_c_model.py:216–221` checks disclosed hidden-model refusal. | UNVERIFIED_ASSUMPTION; no interval. A common unit-variance Rademacher shock makes the variance of a sum of B identical block values B², whereas block-independence additivity would give B. The current certifier cannot infer from one log that such a hidden shock is absent. The control is an assumption-violating model, not a certified scenario. |
| 2. Missing shared-shock graph edges | `tests/test_gate_c_methods.py:139–145` declares `graph_missing_edges`; preserved `tests/test_bounded_variance.py:57–69` explicitly contrasts four copies' sum variance 16 with the false edgeless arithmetic bound 4 and rejects invalid coloring. | Disclosed wrong model: UNVERIFIED_ASSUMPTION, no interval. Primary code constructs the declared complete-clique graph and verifies coloring (`comet/gate_c_methods.py:203–205`). A proper coloring certifies only the supplied graph's combinatorics; stochastic sufficiency is a separate model fact. |
| 3. Misspecified propensity or zero support | `tests/test_gate_c_methods.py:148–162`; `tests/test_gate_c_model.py:202–213,226–229`; preserved `comet/dr_scores.py:15–24`. | Changed logged e: UNVERIFIED_ASSUMPTION / EXACT_LOGGING_PROPENSITY_MISMATCH. A zero-e primary design: NOT_CERTIFIABLE / SYNTHETIC_LOGGING_REQUIRES_BOTH_EXPOSURES_SUPPORTED. The generic score support check raises NONIDENTIFIABLE_TARGET_SUPPORT when q>0=e. No propensity clipping repairs identification. |
| 4. Nuisance trained on evaluation outcomes | `tests/test_gate_c_methods.py:148–153`; `tests/test_gate_c_model.py:216–223`. Arbitrarily misspecified but fixed fits are separately validated at `tests/test_gate_c_model.py:87–109` and `tests/test_gate_c_methods.py:88–100`. | Changed logged fit: UNVERIFIED_ASSUMPTION / FIXED_NUISANCE_OR_REFERENCE_MISMATCH. Declared evaluation-trained nuisance: UNVERIFIED_ASSUMPTION / GATE_C_FIXED_NUISANCE_REQUIRED. Misspecification of a permissible frozen fit is allowed; hidden training provenance is not identified by numerical fit values alone. No mutual-cross-fit theorem is claimed. |
| 5. Required p-moment is infinite or unknown | `tests/test_gate_c_model.py:129–136`; `tests/test_gate_c_methods.py:156–162` sets p at the Pareto tail exponent. Unknown-conditional-moment model label is covered at lines 139–145. | For p>=a, NOT_APPLICABLE / P_MOMENT_NOT_FINITE_FOR_DECLARED_TAIL, no interval. This is a mathematically known tail-domain violation, not a test of an empirical sample moment. The cell-level validator refuses the malformed declaration; this does not claim that every possible point estimator is undefined. An unknown envelope is UNVERIFIED_ASSUMPTION, not estimated into validity. |
| 6. Outcome-selected q/h or shortest interval | `tests/test_gate_c_methods.py:139–145` declares `outcome_selected_q_h` and `outcome_selected_shortest_interval`; immutable family checks are `comet/gate_c_contract.py:137–138`. No oracle import is allowed in the certifier's transitive code (`tests/test_gate_c_methods.py:182–195`). | Disclosed selection: UNVERIFIED_ASSUMPTION, no interval. Separate nominal intervals across methods do not certify a post-hoc shortest interval. Hidden external selection is not automatically detectable; it needs an independent split, legitimate design-only selection proof, or simultaneous adjustment. No selected-method guarantee is exposed. |
| 7. Stable-target MOM on drifting blocks | `tests/test_gate_c_model.py:75–84` verifies actual alternating exogenous mean drift and correct odd-B target averaging; `tests/test_gate_c_methods.py:131–136` checks applicability. | Both MOM rules: NOT_APPLICABLE / MOM_REQUIRES_COMMON_BLOCK_TARGET_OR_PROVED_DRIFT. Bounded graph mean remains CERTIFIED because heterogeneous exogenous block means are allowed by its separate proof. No unproved drift radius is supplied. Primary cells remain stable. |
| 8. Giant positive q/e and vacuous intervals | `tests/test_gate_c_methods.py:165–170` uses strictly positive e1=(1e-8,2e-8). | All three applicable methods remain CERTIFIED, but raw intervals cover the entire known target range; width fraction is 1 and constraint decision ABSTAIN. This is a valid but uninformative result, not an assumption failure or a successful narrow interval. CI issuance and decision abstention are distinct. |

The new heavy-tail F also has a mandatory **inapplicable comparison**, not an
assumption violation: bounded graph Chebyshev is NOT_APPLICABLE under the
declared unbounded reward law. `tests/test_gate_c_methods.py:66–72` replaces all
observed rewards by .5 and confirms that this bounded-looking realization
still cannot change the theorem status. A finite sample range cannot establish
a population residual bound. Conversely, fixed conditional means in [0,1]
justify the full-target-range reference even for F; that is not a bounded-Y
variance certificate (`tests/test_gate_c_methods.py:47–63,198–205`).

IPS, DM and DR point baselines stay POINT_ONLY in valid cells. They have no raw
or clipped confidence endpoints, no width, no certified level and no certified
decision (`tests/test_gate_c_methods.py:75–85`). The summary retains them and
the F inapplicable rows in method/applicability counts, with coverage undefined
instead of zero or one (`tests/test_gate_c_statistics.py:103–121`). Empty
intersections and unissued intervals cannot certify safe/violating decisions
(`tests/test_gate_c_methods.py:173–179`); a coverage failure is not silently
removed from the undercoverage diagnostic
(`tests/test_gate_c_statistics.py:128–139`).

All primary constraints use the fixed threshold .2*pi_h. The preflight can
record false-safe, false-violation, detection and abstention bookkeeping for
that one threshold, but it does not implement the later null/alternative gap
sweep, hidden-subgroup discovery or pessimistic policy-repair campaign. No
power, adaptive-deployment or real-data conclusion follows from these tests.
Any unexpected code/proof status mismatch must block C-STAT even if observed
preflight coverage happens to be high.

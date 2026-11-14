"""Deterministic direct-vs-level contrast checks; no Monte Carlo draws."""

import numpy as np
import pytest

from comet.paired_contrasts import (
    make_joint_level_family_plans, make_level_difference_plans,
    make_paired_queries, subtract_level_certificates,
)
from comet.residual_truncation import AssumptionContract, CertificatePlan, make_plan
from comet.source_graph import SourceGraph


def inputs(n=64):
    return (
        np.full((n, 2), 0.5), np.full((n, 2), 0.5), np.full((n, 2), 0.25),
        SourceGraph.from_sources([{("row", row)} for row in range(n)]),
        AssumptionContract(True, True, True, True, True, True, True,
                           "independent primitives", "bounded midpoint", "fixed design"),
    )


def plans(m=4, q1=(0.3, 0.7), q0=(0.5, 0.5), n=64):
    paired = make_paired_queries("contrast", np.tile(q1, (n, 1)), np.tile(q0, (n, 1)), 1)
    base = inputs(n)
    difference = make_level_difference_plans(*paired, *base, p=2, delta=0.05,
        contrast_count=m, multipliers=(0.5, 1, 2), method="generic_matched",
        outcome_bounds=(0, 1), mean_bounds=(0, 1))
    return paired, base, difference


def evaluate(plan):
    n = plan.direct_query.n_rows
    return plan.evaluate(np.arange(n, dtype=np.int64) % 2, np.full(n, 0.5),
                         data_digest="same-log", seed_namespace="deterministic-fixture",
                         code_hash="new-code", config_hash="new-config")


def test_two_level_family_pays_twice_the_actual_contrast_count():
    _, _, difference = plans(m=4)
    assert difference.family_size == 8
    assert difference.coordinate_delta == 0.05 / 8
    for level in (difference.level1_plan, difference.level0_plan):
        assert level.family_size == 8
        assert level.coordinate_delta == 0.05 / 8
    result = evaluate(difference)
    assert result["nominal_delta"] == 0.05
    assert result["contrast_failure_allocation"] == 0.05 / 4
    assert result["family_size"] == 8


def test_subtraction_has_actual_interval_endpoints_and_adds_all_components():
    _, _, difference = plans(m=1)
    n = difference.direct_query.n_rows
    metadata = dict(data_digest="same-log", seed_namespace="deterministic-fixture",
                    code_hash="new-code", config_hash="new-config")
    actions = np.arange(n, dtype=np.int64) % 2
    outcomes = np.full(n, 0.5)
    first = difference.level1_plan.evaluate(actions, outcomes, **metadata)
    baseline = difference.level0_plan.evaluate(actions, outcomes, **metadata)
    result = subtract_level_certificates(difference.direct_query, first, baseline,
        contrast_count=1, delta=0.05)  # no extra known-range intersection here
    assert result["lo"] == first["lo"] - baseline["hi"]
    assert result["hi"] == first["hi"] - baseline["lo"]
    assert result["raw_lo"] == first["raw_lo"] - baseline["raw_hi"]
    for field in ("radius", "bias", "concentration", "range_contribution", "numerical_guard"):
        assert result[field] == first[field] + baseline[field]


def test_two_separate_95_percent_levels_are_not_a_95_percent_contrast():
    _, _, difference = plans(m=1)
    n = difference.direct_query.n_rows
    metadata = dict(data_digest="same", seed_namespace="fixture", code_hash="code", config_hash="config")
    first = difference.level1_plan.evaluate(np.zeros(n, dtype=int), np.full(n, 0.5), **metadata)
    baseline = difference.level0_plan.evaluate(np.zeros(n, dtype=int), np.full(n, 0.5), **metadata)
    first["coordinate_delta"] = 0.05
    with pytest.raises(ValueError, match="delta/\\(2m\\)"):
        subtract_level_certificates(difference.direct_query, first, baseline, contrast_count=1, delta=0.05)


def test_direct_known_range_is_signed_not_difference_of_independent_ranges():
    paired, _, difference = plans(m=1, q1=(0.49, 0.51))
    result = evaluate(difference)
    # The signed contrast is at most .01 in absolute value under mu in [0,1],
    # even though separately bounded policy levels each range over [0,1].
    assert result["lo"] >= -0.01 - 1e-15
    assert result["hi"] <= 0.01 + 1e-15
    assert result["raw_hi"] - result["raw_lo"] > 0.02
    assert paired[0].offset.sum() == 0


def test_small_policy_change_direct_radius_avoids_unrelated_level_uncertainty():
    paired, base, difference = plans(m=1, q1=(0.49, 0.51))
    direct = make_plan(paired[0], *base, p=2, delta=0.05, family_size=1,
                       multipliers=(0.5, 1, 2), method="generic_matched",
                       outcome_bounds=(0, 1), mean_bounds=(0, 1))
    # One fixed design comparison, not a measured power result or another
    # stochastic scaling grid. The strong comparator receives identical info.
    assert direct.radius < difference.radius / 10


def test_empty_level_is_retained_even_if_naive_subtraction_would_look_nonempty():
    _, _, difference = plans(m=1)
    n = difference.direct_query.n_rows
    metadata = dict(data_digest="same", seed_namespace="fixture", code_hash="code", config_hash="config")
    first = difference.level1_plan.evaluate(np.zeros(n, dtype=int), np.full(n, 0.5), **metadata)
    baseline = difference.level0_plan.evaluate(np.zeros(n, dtype=int), np.full(n, 0.5), **metadata)
    first.update(lo=0.6, hi=0.5, empty_intersection=True)
    baseline.update(lo=0, hi=1)
    result = subtract_level_certificates(difference.direct_query, first, baseline, contrast_count=1, delta=0.05)
    assert result["lo"] <= result["hi"]
    assert result["empty_intersection"] and result["constituent_empty"]


def test_zero_direct_contrast_can_be_identified_when_both_levels_are_unsupported():
    paired = make_paired_queries("zero", np.full((8, 2), 0.5), np.full((8, 2), 0.5), 1)
    exposure, fit, moments, graph, contract = inputs(8)
    exposure[:] = [1, 0]
    paired[0].validate_support(exposure)
    with pytest.raises(ValueError, match="NONIDENTIFIED"):
        make_level_difference_plans(*paired, exposure, fit, moments, graph, contract,
            p=2, delta=0.05, contrast_count=1, multipliers=(1,), outcome_bounds=(0, 1))


def test_wrong_signed_contrast_or_nonprobability_policies_refuse():
    paired, base, _ = plans(m=1)
    other = make_paired_queries("other", np.tile([0.1, 0.9], (64, 1)),
                                np.full((64, 2), 0.5), 1)[0]
    with pytest.raises(ValueError, match="signed difference"):
        make_level_difference_plans(other, paired[1], paired[2], *base, p=2,
            delta=0.05, contrast_count=1, multipliers=(1,))
    with pytest.raises(ValueError, match="probability distribution"):
        make_paired_queries("bad", np.ones((8, 2)), np.full((8, 2), 0.5), 1)


def test_e3_shared_baselines_use_actual_twenty_level_family_and_one_evaluation_each(monkeypatch):
    from experiments.suite_designs import build_contrast_design
    suite = build_contrast_design(n=128, changed_fraction=1.0)
    pairs = tuple((direct, *levels) for direct, levels in
                  zip(suite.queries, suite.metadata["level_pairs"]))
    joint = make_joint_level_family_plans(pairs, **suite.certifier_inputs,
        delta=0.05, multipliers=(0.5, 1, 2), method="generic_matched")
    assert joint.underlying_family_size == 20  # 16 new + 4 shared baseline
    assert joint.direct_family.family_size == 16
    assert joint.coordinate_delta == 0.05 / 20
    assert len(joint.family.aliases) == 32
    assert all(plan.family_size == 20 for plan in joint.level_plans.values())
    calls = []
    original = CertificatePlan.evaluate
    def observed(self, *args, **kwargs):
        calls.append(self.query_id)
        return original(self, *args, **kwargs)
    monkeypatch.setattr(CertificatePlan, "evaluate", observed)
    output = joint.evaluate(np.arange(128, dtype=np.int64) % 2, np.full(128, 0.5),
        data_digest="one-deterministic-log", seed_namespace="fixture",
        code_hash="code", config_hash="config")
    assert len(calls) == len(set(calls)) == 20
    assert len(output["contrasts"]) == 16
    assert output["derived_family_failure_delta"] == 0.05
    for record in output["contrasts"].values():
        assert record["underlying_family_size"] == 20
        assert record["contrast_failure_allocation"] == 2 * 0.05 / 20
        assert record["no_additional_contrast_union_charge"]
        assert record["derived_family_failure_delta"] == 0.05


def test_zero_change_deduplicates_more_than_shared_baseline_case():
    n = 32
    base = inputs(n)
    auditor_values = [np.ones(n), np.arange(n) < n // 2,
                      np.arange(n) % 2 == 0, np.arange(n) >= n // 2]
    q = np.full((n, 2), 0.5)
    pairs = [make_paired_queries(f"policy{policy}/auditor{auditor}", q, q, h)
             for policy in range(4) for auditor, h in enumerate(auditor_values)]
    joint = make_joint_level_family_plans(pairs, *base, p=2, delta=0.05,
        multipliers=(0.5, 1, 2), outcome_bounds=(0, 1), mean_bounds=(0, 1))
    assert joint.underlying_family_size == 4
    assert joint.direct_family.family_size == 1
    output = joint.evaluate(np.zeros(n, dtype=int), np.full(n, 0.5),
        data_digest="same", seed_namespace="fixture", code_hash="code", config_hash="config")
    assert len(output["level_certificates"]) == 4
    for record in output["contrasts"].values():
        assert record["lo"] == record["hi"] == 0
        assert record["contrast_failure_allocation"] == 0.05 / 4


def test_deduplicated_level_budget_strengthens_shared_baseline_instead_of_penalizing_it():
    from experiments.suite_designs import build_contrast_design
    suite = build_contrast_design(n=64, changed_fraction=1.0)
    pairs = tuple((direct, *levels) for direct, levels in
                  zip(suite.queries, suite.metadata["level_pairs"]))
    common = dict(**suite.certifier_inputs, delta=0.05,
                  multipliers=(0.5, 1, 2), method="generic_matched")
    joint = make_joint_level_family_plans(pairs, **common)
    conservative = make_level_difference_plans(*pairs[0], contrast_count=16, **common)
    canonical = joint.family.canonical_id(pairs[0][1].query_id)
    assert joint.level_plans[canonical].coordinate_delta > conservative.level1_plan.coordinate_delta
    assert joint.level_plans[canonical].radius < conservative.level1_plan.radius


def test_joint_comet_and_fully_matched_generic_use_same_numeric_bound():
    paired, base, _ = plans(m=1)
    kwargs = dict(p=2, delta=0.05, multipliers=(0.5, 1, 2),
                  outcome_bounds=(0, 1), mean_bounds=(0, 1))
    comet = make_joint_level_family_plans([paired], *base, method="comet_local", **kwargs)
    generic = make_joint_level_family_plans([paired], *base, method="generic_matched", **kwargs)
    metadata = dict(data_digest="same", seed_namespace="fixture", code_hash="code", config_hash="config")
    direct_comet = make_plan(paired[0], *base, family_size=1, method="comet_local", **kwargs)
    direct_generic = make_plan(paired[0], *base, family_size=1, method="generic_matched", **kwargs)
    assert direct_comet.radius == direct_generic.radius
    assert direct_comet.evaluate(np.zeros(64, dtype=int), np.full(64, 0.5), **metadata)["estimate"] == direct_generic.evaluate(
        np.zeros(64, dtype=int), np.full(64, 0.5), **metadata)["estimate"]
    left = comet.evaluate(np.zeros(64, dtype=int), np.full(64, 0.5), **metadata)["contrasts"]["contrast"]
    right = generic.evaluate(np.zeros(64, dtype=int), np.full(64, 0.5), **metadata)["contrasts"]["contrast"]
    for field in ("estimate", "lo", "hi", "radius", "bias", "concentration", "range_contribution"):
        assert left[field] == right[field]

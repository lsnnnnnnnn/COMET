"""Deterministic explicit-primitive E5 fixtures, not scientific trial draws."""

import inspect

import numpy as np
import pytest

from comet.policy_update import select_policy
from comet.post_cstat_statistics import WholeTrialSummary
from experiments.pipeline_dgp import (
    DRAFT, build_pipeline_design, evaluate_pipeline, fit_and_freeze_pipeline,
    generate_pipeline_from_primitives, pipeline_cells, policy_known_constraints,
    pipeline_role_seed, pipeline_trial_record,
)
from experiments.core_graph_dgp import WORD_GRID


def fixture_log(split, *, invert=False):
    words = np.where(np.arange(split.n) % 2 == 0, 0, WORD_GRID - 1).astype(np.uint64)
    primitives = {channel: {source: (-1.0 if (index + int(invert)) % 2 else 1.0)
                             for index, source in enumerate(split.channel_source_ids[channel])}
                  for channel in ("risk", "utility")}
    return generate_pipeline_from_primitives(split, words, primitives)


@pytest.fixture
def pipeline():
    design = build_pipeline_design(split_sizes={"training": 128, "discovery": 256, "certification": 256})
    logs = {name: fixture_log(split) for name, split in design.splits.items()}
    frozen = fit_and_freeze_pipeline(design, logs["training"], logs["discovery"])
    return design, logs, frozen


def test_eight_cells_and_independent_split_sources(pipeline):
    design, _, _ = pipeline
    assert len(pipeline_cells()) == 8
    assert all(cell["status"] == DRAFT for cell in pipeline_cells())
    sets = [split.source_ids for split in design.splits.values()]
    assert all(left.isdisjoint(right) for i, left in enumerate(sets) for right in sets[i + 1:])
    assert design.source_separation["status"] == "DECLARED_SOURCE_SETS_DISJOINT"
    role_keys = [pipeline_role_seed(split, 7, role) for split in design.splits.values()
                 for role in ("logging", "risk", "utility")]
    assert len(set(role_keys)) == 9


def test_distinct_channels_action_zero_and_graph(pipeline):
    design, logs, _ = pipeline
    split, log = design.splits["certification"], logs["certification"]
    assert set(split.channel_source_ids["risk"]).isdisjoint(split.channel_source_ids["utility"])
    assert not np.array_equal(log.outcomes["risk"], log.outcomes["utility"])
    for response in log.outcomes.values():
        assert np.all(response[log.actions == 0] == 0)
        assert np.all((response >= 0) & (response <= 1))
    assert split.graph.color_count >= 2
    assert 1 in split.graph.adjacency[0]
    assert split.row_sources[0] & split.row_sources[1]


def test_fitted_nuisance_and_complete_risk_utility_family(pipeline):
    _, _, frozen = pipeline
    assert frozen.status == DRAFT
    assert len(frozen.candidates) == 8
    assert len(frozen.auditors) == 4
    assert frozen.family.family_size > 16
    assert sum(query.channel == "utility" for query in frozen.family.queries) == 7
    assert {query.channel for query in frozen.family.queries} == {"risk", "utility"}
    for candidate in frozen.candidates:
        assert len(candidate.risk_query_ids) == 5
        for query_id in candidate.risk_query_ids:
            assert query_id in frozen.risk_thresholds
            assert frozen.family.canonical_id(query_id)
    for channel in ("risk", "utility"):
        inputs = frozen.certifier_inputs(channel)
        assert not any("truth" in key or "location" in key for key in inputs)
        assert np.all(inputs["nuisance"][:, 0] == 0)
        assert np.all(inputs["residual_moments"][:, 0] == 0)
        assert np.all((inputs["nuisance"] >= 0) & (inputs["nuisance"] <= 1))
        assert np.allclose(inputs["residual_moments"][:, 1],
                           np.maximum(inputs["nuisance"][:, 1], 1-inputs["nuisance"][:, 1])**2)


def test_candidates_do_not_accept_certification_outcomes(pipeline):
    design, logs, frozen = pipeline
    signature = inspect.signature(fit_and_freeze_pipeline)
    assert "certification_log" not in signature.parameters
    assert "_pipeline_locations" not in inspect.getsource(fit_and_freeze_pipeline)
    # Alternate certification signs change data, not an input to discovery.
    alternate = fixture_log(design.splits["certification"], invert=True)
    assert alternate.data_digest != logs["certification"].data_digest
    repeated = fit_and_freeze_pipeline(design, logs["training"], logs["discovery"])
    assert repeated.family_digest == frozen.family_digest
    assert repeated.family.digest == frozen.family.digest
    assert all(rule.mask(design.splits["certification"].x).mean() >= 0.02 for rule in frozen.auditors)


def test_split_mismatch_and_primitive_mismatch_refuse(pipeline):
    design, logs, _ = pipeline
    with pytest.raises(ValueError, match="source split"):
        fit_and_freeze_pipeline(design, logs["training"], logs["training"])
    split = design.splits["training"]
    with pytest.raises(ValueError, match="primitive"):
        generate_pipeline_from_primitives(split, np.zeros(split.n, dtype=np.uint64), {"risk": {}})


def test_reject_all_fails_known_service_constraint():
    known = policy_known_constraints(np.zeros(32))
    assert known["service"] == 0
    assert known["eligible"] is False
    assert policy_known_constraints(np.full(32, 0.35))["eligible"] is True


def test_oracle_join_requires_completed_methods_and_abstention_is_not_useful(pipeline):
    _, _, frozen = pipeline
    with pytest.raises(ValueError, match="after all methods"):
        evaluate_pipeline(frozen, {}, {"returned": False})
    metrics = evaluate_pipeline(frozen, {}, {"returned": False}, methods_finished=True)
    assert metrics["returned"] is False
    assert metrics["return_and_safe_and_useful"] is False
    assert metrics["return_and_unsafe"] is False
    assert metrics["unsafe_given_return_denominator"] == 0
    assert metrics["family_covered"] is False
    assert metrics["all_coordinates_certified"] is False


def test_analytic_fixture_selection_and_full_budget(pipeline):
    _, _, frozen = pipeline
    truth = evaluate_pipeline(frozen, {}, {"returned": False}, methods_finished=True)["targets"]
    # Oracle-centered intervals are evaluator-only algebra fixtures, never
    # passed off as estimator output or used by candidate construction.
    certificates = {query.query_id: dict(
        query_id=query.query_id, channel=query.channel, normalizer=query.normalizer,
        family_size=frozen.family.family_size, nominal_delta=0.05,
        coordinate_delta=0.05/frozen.family.family_size,
        status="CERTIFIED_UNDER_DECLARED_ASSUMPTIONS", lo=truth[query.query_id]-1e-9,
        hi=truth[query.query_id]+1e-9, radius=1e-9,
    ) for query in frozen.family.queries}
    decision = select_policy(frozen.candidates, frozen.family, certificates, frozen.risk_thresholds,
                             utility_margin=frozen.design.utility_margin,
                             service_floor=frozen.design.service_floor,
                             capacity_ceiling=frozen.design.capacity_ceiling)
    metrics = evaluate_pipeline(frozen, certificates, decision, methods_finished=True)
    assert metrics["family_covered"] is True
    assert metrics["any_false_claim"] is False
    assert metrics["return_and_unsafe"] is False
    assert metrics["returned"] is True
    assert metrics["return_and_safe_and_useful"] is True
    assert metrics["robust_slack_comparator_value"] is not None
    record = pipeline_trial_record(metrics, run_id="deterministic-fixture",
        cell="E5-fixture", method="analytic-fixture", delta=.05,
        certificates=certificates, coverage_applicable=True)
    summary = WholeTrialSummary()
    summary.add(record)
    result = summary.result()
    assert result["independent_trials"] == 1
    assert result["family_coverage"]["hits"] == 1
    assert result["endpoints"]["return_safe_useful"]["hits"] == 1
    assert result["endpoints"]["return_unsafe"]["hits"] == 0
    assert record["return_and_utility_noninferior"] is True
    assert record["return_and_service_feasible"] is True
    failed = {key: dict(value) for key, value in certificates.items()}
    failed[next(iter(failed))].update(status="NUMERICAL_FAILURE", lo=None, hi=None)
    failed_metrics = evaluate_pipeline(frozen, failed, {"returned": False}, methods_finished=True)
    summary.add(pipeline_trial_record(failed_metrics, run_id="failed-fixture",
        cell="E5-fixture", method="analytic-fixture", delta=.05,
        certificates=failed, coverage_applicable=True))
    result = summary.result()
    assert result["independent_trials"] == 2
    assert result["family_coverage"]["hits"] == 1
    assert result["endpoints"]["return_safe_useful"]["rate"] == .5
    assert result["status_counts"]["NUMERICAL_FAILURE"] == 1

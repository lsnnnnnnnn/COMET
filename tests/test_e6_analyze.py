"""Handwritten E6 checkpoint fixtures; no real ACS, logging RNG or MC trials."""

import gzip
import json

import numpy as np
import pytest

from comet.checkpoint_store import CheckpointStore, NAMESPACE, REQUIRED_INPUTS, freeze_protocol
from comet.post_cstat_statistics import EVENTS
from experiments.pipeline_runner import ARMS, CERTIFIED_ARMS
import experiments.e6_analyze as analyzer


CELL = "moderate-loggerindependent"


@pytest.fixture(autouse=True)
def forbid_logging_rng(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("handwritten E6 analysis test called RNG")
    monkeypatch.setattr(np.random, "default_rng", forbidden)


def protocol_fixture(tmp_path, *, all_primary=False):
    from experiments.e6_runner import primary_e6_comparisons
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    for name in REQUIRED_INPUTS:
        (inputs / name).write_text("HANDWRITTEN E6 ANALYSIS TEST FIXTURE ONLY: " + name)
    source = tmp_path / "fixture_source.py"
    source.write_text("fixture_only=True\n")
    ids = [f"{NAMESPACE}/E6/{CELL}/{rep:04d}" for rep in range(2)]
    config = dict(namespace=NAMESPACE, suite="DETERMINISTIC_E6_FIXTURE",
        legacy_new_outcome_draws=0, primary_units=0, total_unit_cap=32000, workers=1,
        planned_run_ids=ids, arms=list(ARMS), certified_arms=list(CERTIFIED_ARMS),
        levels=[0.05, 0.1], analysis_bootstrap_seed=19, analysis_bootstrap_resamples=0,
        dataset_population_digest="handwritten-fixture-not-ACS-population",
        archive_sha256="handwritten-fixture-not-official-archive",
        primary_comparisons=primary_e6_comparisons() if all_primary else [[CELL, arm] for arm in CERTIFIED_ARMS])
    path = tmp_path / "protocol.json"
    manifest = freeze_protocol(path, config, [source], inputs)
    return path, manifest, source, ids


def frame(run_id, arm, delta, *, returned=None, unsafe=False, useful=None, family_size=47):
    if returned is None:
        returned = arm not in ("independent_global", "abstain_reference")
    if useful is None:
        useful = returned and not unsafe
    discovery = arm not in ("fixed_slice", "abstain_reference", "status_quo_reference")
    record = dict(run_id=run_id, cell=CELL, method=arm, delta=delta,
        coverage_applicable=arm in CERTIFIED_ARMS, family_covered=arm in CERTIFIED_ARMS,
        failure_status=None, metrics_assessable=True, mean_coordinate_width=0.1,
        return_endpoint_applicable=True, discovery_endpoint_applicable=discovery,
        actual_family_size=31 if arm == "fixed_slice" else family_size,
        **{event: False for event in EVENTS})
    record.update(returned=bool(returned), return_unsafe=bool(returned and unsafe),
        return_safe_useful=bool(returned and useful and not unsafe),
        discovered_and_certified=bool(discovery and arm in CERTIFIED_ARMS),
        return_and_infeasible=bool(returned and (unsafe or not useful)),
        return_and_risk_safe=bool(returned and not unsafe),
        return_and_utility_noninferior=bool(returned and useful),
        return_and_service_feasible=bool(returned), any_false_utility_claim=False,
        returned_baseline=bool(returned and arm == "status_quo_reference"),
        true_utility=0.5 if returned else None, utility_gain=0.02 if returned else None,
        expected_service=0.35 if returned else 0.0, expected_capacity=0.35 if returned else 0.0,
        maximum_true_risk_violation=0.1 if unsafe else (0.0 if returned else None),
        oracle_best_feasible_candidate_value=0.55, robust_slack_comparator_value=0.45,
        discovery_best_planted_iou=None)
    return record


def complete_result(manifest, run_id):
    config = manifest["config"]
    return dict(status="COMPLETE", suite="E6", cell=CELL,
        dataset_population_digest=config["dataset_population_digest"], archive_sha256=config["archive_sha256"],
        new_scientific_units=0, legacy_new_outcome_draws=0,
        trials=[frame(run_id, arm, delta,
                      unsafe=arm in ("fixed_slice", "status_quo_reference", "point_constraint"))
                for arm in ARMS for delta in (0.05, 0.1)])


def rows_by_key(summary):
    return {(row["method"], row["delta"]): row for row in summary["summaries"]}


def test_complete_trial_reports_return_safe_useful_family_sizes_and_no_causal_claim(tmp_path):
    protocol, manifest, _, ids = protocol_fixture(tmp_path)
    root, output = tmp_path / "results", tmp_path / "analysis"
    store = CheckpointStore(root, manifest)
    store.complete(ids[0], complete_result(manifest, ids[0]))
    summary = analyzer.analyze_e6(protocol, root, output)
    assert summary["status"] == "PARTIAL" and summary["completed_units"] == 1
    assert summary["reported_new_scientific_units"] == summary["analysis_new_outcome_draws"] == 0
    assert summary["primary_comparison_count"] == 4
    assert summary["dataset_population_digest"] == manifest["config"]["dataset_population_digest"]
    assert summary["archive_sha256"] == manifest["config"]["archive_sha256"]
    assert not summary["E5_primary_family_modified"] and not summary["historical_primary_families_modified"]
    assert "not" in summary["sampling_scope"] and "intervention" in summary["sampling_scope"]
    rows = rows_by_key(summary)
    assert len(rows) == 16
    comet = rows["comet_local", 0.05]
    assert comet["independent_trials"] == 1
    assert comet["endpoints"]["return_safe_useful"]["rate"] == 1
    assert comet["pipeline_metrics"]["actual_family_size_counts"] == {"47": 1}
    assert comet["primary_return_guarantee_applicable"]
    planted = comet["pipeline_metrics"]["numeric_metrics"]["discovery_best_planted_iou"]
    assert not planted["applicable"] and planted["mean"] is None
    fixed = rows["fixed_slice", 0.05]
    assert fixed["family_coverage"]["denominator"] == 1
    assert not fixed["primary_return_guarantee_applicable"]
    assert fixed["endpoints"]["return_unsafe"]["rate"] == 1
    assert fixed["pipeline_metrics"]["actual_family_size_counts"] == {"31": 1}
    reference = rows["status_quo_reference", 0.05]
    assert reference["family_coverage"] is None
    assert not reference["primary_return_guarantee_applicable"]
    assert reference["endpoints"]["return_unsafe"]["rate"] == 1
    abstain = rows["abstain_reference", 0.05]
    assert abstain["endpoints"]["returned"]["rate"] == 0
    assert abstain["endpoints"]["return_safe_useful"]["rate"] == 0
    assert abstain["unsafe_given_return_descriptive"]["rate"] is None
    assert (output / "summary.csv").is_file() and (output / "manifest.json").is_file()
    with pytest.raises(FileExistsError, match="immutable"):
        analyzer.analyze_e6(protocol, root, output)


def test_empty_failure_keeps_all_arms_levels_and_unknown_return_denominators(tmp_path):
    protocol, manifest, _, ids = protocol_fixture(tmp_path)
    store = CheckpointStore(tmp_path / "results", manifest)
    store.complete(ids[0], complete_result(manifest, ids[0]))
    store.complete(ids[1], dict(status="UNIT_FAILURE", suite="E6", cell=CELL,
        trials=[], unassessable_whole_trial=True, new_scientific_units=0, legacy_new_outcome_draws=0))
    summary = analyzer.analyze_e6(protocol, store.root, tmp_path / "analysis")
    assert summary["status"] == "COMPLETE" and summary["completed_units"] == 2
    assert summary["failed_units"] == summary["unassessable_units"] == 1
    rows = rows_by_key(summary)
    for arm in ARMS:
        for delta in (0.05, 0.1):
            row = rows[arm, delta]
            assert row["independent_trials"] == 2
            if arm in CERTIFIED_ARMS:
                assert row["family_coverage"]["denominator"] == 2
                assert row["family_coverage"]["hits"] == 1
            else:
                assert row["family_coverage"] is None
            returned = row["endpoints"]["returned"]
            assert returned["denominator"] == 2 and returned["unknown_trials"] == 1
            assert returned["rate"] is returned["wilson95"] is None
            assert row["endpoints"]["any_false_claim"]["unknown_trials"] == 1
    assert all(value["status"] == "UNASSESSABLE_FULL_PAIR_SET" for value in summary["paired_safe_useful_differences"])
    assert all(value["bootstrap_pointwise95"] is None for value in summary["paired_safe_useful_differences"])


def test_missing_single_frame_is_unknown_without_erasing_other_arms(tmp_path):
    protocol, manifest, _, ids = protocol_fixture(tmp_path)
    store = CheckpointStore(tmp_path / "results", manifest)
    result = complete_result(manifest, ids[0])
    result["trials"] = [value for value in result["trials"]
                        if not (value["method"] == "generic_matched" and value["delta"] == 0.05)]
    store.complete(ids[0], result)
    summary = analyzer.analyze_e6(protocol, store.root, tmp_path / "analysis")
    rows = rows_by_key(summary)
    missing = rows["generic_matched", 0.05]
    assert missing["family_coverage"]["denominator"] == 1 and missing["family_coverage"]["hits"] == 0
    assert missing["endpoints"]["return_safe_useful"]["unknown_trials"] == 1
    assert rows["comet_local", 0.05]["family_coverage"]["hits"] == 1
    assert rows["generic_matched", 0.1]["family_coverage"]["hits"] == 1


@pytest.mark.parametrize("violation", ["duplicate", "population", "planted", "applicability"])
def test_duplicate_changed_population_planted_recovery_or_applicability_refuse(tmp_path, violation):
    protocol, manifest, _, ids = protocol_fixture(tmp_path)
    store = CheckpointStore(tmp_path / "results", manifest)
    result = complete_result(manifest, ids[0])
    if violation == "duplicate":
        result["trials"].append(result["trials"][0])
    elif violation == "population":
        result["dataset_population_digest"] = "different-people"
    elif violation == "planted":
        result["trials"][0]["discovery_best_planted_iou"] = 0.9
    else:
        result["trials"][0]["coverage_applicable"] = True
    store.complete(ids[0], result)
    with pytest.raises(ValueError):
        analyzer.analyze_e6(protocol, store.root, tmp_path / "analysis")


def test_all_sixteen_primary_comparisons_remain_when_other_cells_are_missing(tmp_path):
    protocol, manifest, _, ids = protocol_fixture(tmp_path, all_primary=True)
    store = CheckpointStore(tmp_path / "results", manifest)
    store.complete(ids[0], complete_result(manifest, ids[0]))
    summary = analyzer.analyze_e6(protocol, store.root, tmp_path / "analysis")
    assert summary["primary_comparison_count"] == len(summary["primary_diagnostics"]) == 16
    absent = [record for record in summary["primary_diagnostics"] if record["cell"] != CELL]
    assert len(absent) == 12
    assert all(record["undercoverage_p"] is record["holm_undercoverage_p"] is None for record in absent)
    assert summary["diagnostic_status"] == "PARTIAL_DESCRIPTIVE_DIAGNOSTIC_NOT_A_STOPPING_RULE"


def test_no_completed_trials_produces_no_fabricated_results(tmp_path):
    protocol, manifest, _, _ = protocol_fixture(tmp_path)
    summary = analyzer.analyze_e6(protocol, tmp_path / "empty", tmp_path / "analysis")
    assert summary["status"] == "NO_COMPLETED_UNITS"
    assert summary["summaries"] == [] and summary["paired_safe_useful_differences"] == []
    assert summary["completed_units"] == summary["reported_new_scientific_units"] == 0


def test_corrupt_checkpoint_and_changed_source_reject_analysis(tmp_path):
    protocol, manifest, source, ids = protocol_fixture(tmp_path)
    store = CheckpointStore(tmp_path / "results", manifest)
    store.complete(ids[0], complete_result(manifest, ids[0]))
    record = json.loads(gzip.decompress(store.path(ids[0]).read_bytes()))
    record["payload"]["result"]["cell"] = "corrupted"
    store.path(ids[0]).write_bytes(gzip.compress(json.dumps(record).encode()))
    with pytest.raises(ValueError, match="corrupt checkpoint"):
        analyzer.analyze_e6(protocol, store.root, tmp_path / "analysis")
    source.write_text("changed=True\n")
    with pytest.raises(ValueError, match="source changed"):
        analyzer.analyze_e6(protocol, store.root, tmp_path / "analysis")


def test_paired_bootstrap_receives_complete_full_trial_ids_not_people_or_selected_successes(tmp_path, monkeypatch):
    protocol, manifest, _, ids = protocol_fixture(tmp_path)
    store = CheckpointStore(tmp_path / "results", manifest)
    for index, run_id in enumerate(ids):
        result = complete_result(manifest, run_id)
        for value in result["trials"]:
            if value["method"] == "comet_local":
                value["return_safe_useful"] = index == 0
        store.complete(run_id, result)
    calls = []
    def exact_handwritten_bootstrap(left, right, *, bootstrap_seed, resamples):
        assert set(left) == set(right) == set(ids)
        assert resamples == 20
        calls.append((left, right, bootstrap_seed))
        difference = [float(left[key]) - float(right[key]) for key in ids]
        return dict(independent_pairs=len(ids), mean_difference=sum(difference) / len(ids),
            bootstrap_pointwise95=[min(difference), max(difference)], bootstrap_seed=bootstrap_seed,
            resamples=resamples, resampling_unit="complete_independent_trial")
    monkeypatch.setattr(analyzer, "paired_endpoint_difference", exact_handwritten_bootstrap)
    summary = analyzer.analyze_e6(protocol, store.root, tmp_path / "analysis", bootstrap_resamples=20)
    assert len(calls) == 14  # 7 paired comparator arms x 2 levels, same two trials
    assert all(value["independent_pairs"] == 2 for value in summary["paired_safe_useful_differences"])
    assert summary["bootstrap_resamples"] == 20

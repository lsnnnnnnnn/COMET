"""Handwritten deterministic checkpoints only; no scientific draws."""

import csv
import gzip
import json

import pytest

from comet.checkpoint_store import CheckpointStore, NAMESPACE, REQUIRED_INPUTS, freeze_protocol
from comet.post_cstat_statistics import EVENTS
from experiments.post_cstat_analyze import analyze_e1


CELL = "independent-moderate-bounded"
METHODS = ("comet_local", "generic_matched")


def fixture(tmp_path, reps=3, registered=None):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    for name in REQUIRED_INPUTS:
        (inputs / name).write_text("DETERMINISTIC ANALYSIS FIXTURE ONLY: " + name)
    source = tmp_path / "source.py"
    source.write_text("fixture_source = True\n")
    ids = [f"{NAMESPACE}/E1/{CELL}/{index:04d}" for index in range(reps)]
    config = dict(namespace=NAMESPACE, suite="DETERMINISTIC_RUNNER_FIXTURE",
        legacy_new_outcome_draws=0, primary_units=0, total_unit_cap=max(reps, 1), workers=1,
        planned_run_ids=ids, levels=[.05, .1],
        primary_comparisons=registered or [[CELL, method] for method in METHODS])
    protocol = tmp_path / "protocol.json"
    manifest = freeze_protocol(protocol, config, [source], inputs)
    root = tmp_path / "results"
    return protocol, root, CheckpointStore(root, manifest), source, ids


def trial(run_id, method, delta, covered=True, false=False):
    record = dict(run_id=run_id, cell=CELL, method=method, delta=delta,
        coverage_applicable=True, family_covered=covered, failure_status=None,
        return_endpoint_applicable=False, discovery_endpoint_applicable=False,
        mean_coordinate_width=.2)
    record.update({event: False for event in EVENTS})
    record["any_false_claim"] = false
    record["any_false_safe"] = false
    return record


def complete(store, run_id, *, status="COMPLETE", trials=None, unassessable=False):
    if trials is None:
        trials = [trial(run_id, method, delta) for method in METHODS for delta in (.05, .1)]
    store.complete(run_id, dict(cell=CELL, status=status, trials=trials,
        unassessable_whole_trial=unassessable, new_scientific_units=0, legacy_new_outcome_draws=0))


def test_empty_failure_trials_keep_whole_log_denominators_and_unknown_false_claims(tmp_path):
    protocol, root, store, _, ids = fixture(tmp_path)
    complete(store, ids[0])
    complete(store, ids[1], status="ORACLE_FAILURE", trials=[], unassessable=True)
    summary = analyze_e1(protocol, root, tmp_path / "analysis")
    assert summary["status"] == "PARTIAL"
    assert summary["completed_units"] == 2 and summary["remaining_units"] == 1
    assert summary["unassessable_units"] == summary["failed_units"] == 1
    assert summary["unknown_method_level_records"] == 4
    assert summary["analysis_new_outcome_draws"] == summary["legacy_new_outcome_draws"] == 0
    for row in summary["summaries"]:
        assert row["independent_trials"] == 2
        assert row["family_coverage"]["denominator"] == 2
        assert row["family_coverage"]["hits"] == 1
        event = row["endpoints"]["any_false_claim"]
        assert event["unknown_trials"] == 1 and event["denominator"] == 2
        assert event["rate"] is None and event["wilson95"] is None
        assert event["realized_frequency_bounds"] == [0, .5]
        assert not row["endpoints"]["returned"]["applicable"]
        assert row["endpoints"]["returned"]["hits"] is None
        assert not row["endpoints"]["discovered_and_certified"]["applicable"]
    with (tmp_path / "analysis/summary.csv").open(newline="") as stream:
        csv_rows = list(csv.DictReader(stream))
    assert len(csv_rows) == 4
    assert all(row["any_false_claim_rate"] == "" for row in csv_rows)
    assert all(row["returned_applicable"] == "False" for row in csv_rows)


def test_missing_method_level_record_is_failure_not_a_smaller_denominator(tmp_path):
    protocol, root, store, _, ids = fixture(tmp_path, reps=1)
    records = [trial(ids[0], method, delta) for method in METHODS for delta in (.05, .1)]
    complete(store, ids[0], trials=records[:-1])
    summary = analyze_e1(protocol, root, tmp_path / "analysis")
    assert summary["status"] == "COMPLETE"
    assert summary["unknown_method_level_records"] == 1
    assert len(summary["summaries"]) == 4
    assert all(row["independent_trials"] == 1 for row in summary["summaries"])
    missing = next(row for row in summary["summaries"] if row["method"] == "generic_matched" and row["delta"] == .1)
    assert missing["family_coverage"]["hits"] == 0
    assert missing["endpoints"]["any_false_claim"]["unknown_trials"] == 1


def test_duplicate_wrong_cell_or_method_records_refuse(tmp_path):
    protocol, root, store, _, ids = fixture(tmp_path, reps=1)
    record = trial(ids[0], METHODS[0], .05)
    complete(store, ids[0], trials=[record, record])
    with pytest.raises(ValueError, match="duplicate method/level"):
        analyze_e1(protocol, root, tmp_path / "analysis")
    assert not (tmp_path / "analysis/summary.json").exists()


def test_missing_registered_comparison_is_retained_in_holm_family(tmp_path):
    registered = [[CELL, method] for method in METHODS] + [["not_started_cell", "comet_local"]]
    protocol, root, store, _, ids = fixture(tmp_path, reps=1, registered=registered)
    complete(store, ids[0])
    summary = analyze_e1(protocol, root, tmp_path / "analysis")
    assert summary["primary_comparison_count"] == 3
    absent = next(row for row in summary["primary_diagnostics"] if row["cell"] == "not_started_cell")
    assert absent["undercoverage_p"] is None and absent["holm_undercoverage_p"] is None
    assert not summary["historical_primary_family_modified"]
    assert all(row["holm_undercoverage_p"] is None for row in summary["summaries"] if row["delta"] == .1)


def test_no_completed_units_does_not_create_coverage_results(tmp_path):
    protocol, root, _, _, ids = fixture(tmp_path)
    summary = analyze_e1(protocol, root, tmp_path / "analysis")
    assert summary["status"] == "NO_COMPLETED_UNITS"
    assert summary["summaries"] == []
    assert summary["completed_units"] == 0 and summary["remaining_ids"] == ids
    assert summary["reported_new_scientific_units"] == 0


def test_outputs_are_immutable_and_changed_source_or_corrupt_checkpoint_refuses(tmp_path):
    protocol, root, store, source, ids = fixture(tmp_path, reps=1)
    complete(store, ids[0])
    output = tmp_path / "analysis"
    analyze_e1(protocol, root, output)
    original = (output / "summary.json").read_bytes()
    with pytest.raises(FileExistsError, match="immutable"):
        analyze_e1(protocol, root, output)
    assert (output / "summary.json").read_bytes() == original
    source.write_text("changed = True\n")
    with pytest.raises(ValueError, match="source changed"):
        analyze_e1(protocol, root, tmp_path / "changed_source_analysis")
    source.write_text("fixture_source = True\n")
    record = json.loads(gzip.decompress(store.path(ids[0]).read_bytes()))
    record["payload"]["result"]["cell"] = "corrupt"
    store.path(ids[0]).write_bytes(gzip.compress(json.dumps(record).encode()))
    with pytest.raises(ValueError, match="corrupt checkpoint"):
        analyze_e1(protocol, root, tmp_path / "corrupt_analysis")

"""Tiny deterministic callback fixtures; NEVER call the scientific draw path."""

import gzip
import json

import numpy as np
import pytest

from comet.checkpoint_store import CheckpointStore, NAMESPACE, REQUIRED_INPUTS, freeze_protocol
from comet.residual_truncation import CertificatePlan
from experiments.core_graph_dgp import evaluate_oracle, generate_from_primitives
import experiments.post_cstat_runner as runner


def resources(_):
    return dict(free_disk_bytes=10 * runner.GIB, available_ram_bytes=runner.GIB,
                worker_rss_bytes=128 * 2**20)


def protocol_fixture(tmp_path):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    for name in REQUIRED_INPUTS:
        (inputs / name).write_text("DETERMINISTIC RUNNER TEST FIXTURE ONLY: " + name)
    source = tmp_path / "fixture_source.py"
    source.write_text("deterministic_fixture = 1\n")
    cell = "cycle-moderate-bounded"
    ids = [f"{NAMESPACE}/E1/{cell}/{index:04d}" for index in range(2)]
    config = dict(namespace=NAMESPACE, suite="DETERMINISTIC_RUNNER_FIXTURE",
        legacy_new_outcome_draws=0, primary_units=0, total_unit_cap=2, workers=1,
        planned_run_ids=ids, N=8, family_size=16, levels=[0.05, 0.1],
        truncation_multipliers=[0.5, 1, 2], normalized_risk_threshold=0.4,
        numerical_guard=1e-10, master_seed=7, seed_domain=NAMESPACE + "/deterministic-fixture",
        raw_debug_run_ids=[ids[0]], git_sha="DETERMINISTIC_FIXTURE_NOT_SCIENCE")
    path = tmp_path / "fixture_protocol.json"
    manifest = freeze_protocol(path, config, [source], inputs)
    return path, manifest, source, ids


def deterministic_draw(design, seed):
    # Explicit words and primitive signs; no RNG, no sampled outcomes.
    return generate_from_primitives(design, np.zeros(design.n, dtype=np.uint32),
        {source: 1.0 for source in design.outcome_source_ids},
        seed_namespace=design.namespace + "/deterministic-fixture")


@pytest.fixture(autouse=True)
def forbid_scientific_draw(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("a deterministic test called draw_core_log")
    monkeypatch.setattr(runner, "draw_core_log", forbidden)


def test_e1_ids_and_primary_diagnostic_family_are_separate_from_e0(tmp_path):
    ids = runner.planned_e1_ids()
    assert len(ids) == len(set(ids)) == 12000
    assert len(runner.e1_cells()) == 12
    assert all(value.startswith(NAMESPACE + "/E1/") for value in ids)
    assert len(runner.primary_e1_comparisons()) == 96
    status = runner.protocol_status(tmp_path / "missing.json", tmp_path / "results", list_ids=True)
    assert status["status"] == "NOT_FROZEN"
    assert status["completed"] == status["legacy_new_outcome_draws"] == 0
    assert status["remaining_ids"] == ids
    assert "reserved proposed" in status["id_status"]


def test_actual_missing_planning_inputs_prevent_freeze_without_creating_protocol(tmp_path):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    for name in REQUIRED_INPUTS[:2]:
        (inputs / name).write_text("test fixture")
    path = tmp_path / "no_protocol.json"
    (tmp_path / "config.json").write_text("{}")
    with pytest.raises(FileNotFoundError, match="SCOPE_CN.md"):
        runner.freeze_e1(tmp_path / "config.json", inputs, path)
    assert not path.exists()


def test_shared_log_resume_preserves_bytes_and_oracle_follows_all_methods(tmp_path, monkeypatch):
    protocol, manifest, _, ids = protocol_fixture(tmp_path)
    root = tmp_path / "results"
    draws, evaluations = [], []
    original = CertificatePlan.evaluate
    def observed_evaluate(self, *args, **kwargs):
        evaluations.append(self.query_id)
        return original(self, *args, **kwargs)
    monkeypatch.setattr(CertificatePlan, "evaluate", observed_evaluate)
    def draw(design, seed):
        draws.append(seed)
        return deterministic_draw(design, seed)
    def oracle(design):
        # 10 eligible engines x 2 levels x 16 coordinates share ONE log.
        assert len(evaluations) == 10 * 2 * 16
        return evaluate_oracle(design)
    result = runner.run_e1(protocol, root, max_new_units=1, draw_callback=draw,
                           oracle_callback=oracle, resource_reader=resources)
    assert result["new_completed_units"] == 1
    assert result["remaining_ids"] == [ids[1]]
    assert not result["background_work_running"]
    assert len(draws) == 1
    store = CheckpointStore(root, manifest)
    before = store.path(ids[0]).read_bytes()
    payload = store.load(ids[0])["result"]
    assert payload["legacy_new_outcome_draws"] == payload["new_scientific_units"] == 0
    assert len(payload["trials"]) == 20
    assert len(payload["certificate_records"]) == 20
    assert all(len(frame["coordinates"]) == 16 for frame in payload["certificate_records"])
    assert "prespecified_raw_debug" in payload
    result = runner.run_e1(protocol, root, max_new_units=0, draw_callback=draw, resource_reader=resources)
    assert result["new_completed_units"] == 0 and len(draws) == 1
    assert store.path(ids[0]).read_bytes() == before
    status = runner.protocol_status(protocol, root, list_ids=True)
    assert status["completed_ids"] == [ids[0]] and status["remaining_ids"] == [ids[1]]


def test_numerical_failure_keeps_full_trial_denominator_and_actual_raw_fixture(tmp_path, monkeypatch):
    protocol, manifest, _, ids = protocol_fixture(tmp_path)
    original = CertificatePlan.evaluate
    def fail_one_coordinate(self, *args, **kwargs):
        if self.query_id == "policy0/all":
            raise ValueError("injected deterministic numerical failure")
        return original(self, *args, **kwargs)
    monkeypatch.setattr(CertificatePlan, "evaluate", fail_one_coordinate)
    root = tmp_path / "results"
    result = runner.run_e1(protocol, root, max_new_units=1,
        draw_callback=deterministic_draw, resource_reader=resources)
    record = CheckpointStore(root, manifest).load(ids[0])["result"]
    assert result["new_completed_units"] == result["failed_units"] == 1
    assert record["status"] == "COMPLETE_WITH_NUMERICAL_FAILURE"
    assert len(record["trials"]) == 20
    assert all(not trial["family_covered"] for trial in record["trials"])
    assert all(trial["coverage_applicable"] for trial in record["trials"])
    assert "failure_raw_debug" in record


def test_corrupt_checkpoint_and_changed_science_refuse_before_redrawing(tmp_path):
    protocol, manifest, source, ids = protocol_fixture(tmp_path)
    root = tmp_path / "results"
    runner.run_e1(protocol, root, max_new_units=1, draw_callback=deterministic_draw,
                  resource_reader=resources)
    store = CheckpointStore(root, manifest)
    record = json.loads(gzip.decompress(store.path(ids[0]).read_bytes()))
    record["payload"]["result"]["cell"] = "corrupted"
    store.path(ids[0]).write_bytes(gzip.compress(json.dumps(record).encode()))
    with pytest.raises(ValueError, match="corrupt checkpoint"):
        runner.protocol_status(protocol, root)
    source.write_text("changed = True\n")
    with pytest.raises(ValueError, match="source changed"):
        runner.run_e1(protocol, root, draw_callback=deterministic_draw, resource_reader=resources)


def test_resource_boundary_stops_before_any_new_draw(tmp_path):
    protocol, _, _, ids = protocol_fixture(tmp_path)
    calls = []
    snapshots = 0
    def reader(root):
        nonlocal snapshots
        snapshots += 1
        result = resources(root)
        if snapshots > 1:
            result["free_disk_bytes"] = runner.GIB
        return result
    def draw(*args):
        calls.append(True)
        return deterministic_draw(*args)
    result = runner.run_e1(protocol, tmp_path / "results", draw_callback=draw, resource_reader=reader)
    assert result["status"] == "RESOURCE_CHECKPOINTED"
    assert result["new_completed_units"] == 0 and calls == []
    assert result["remaining_ids"] == ids


def test_mid_invocation_source_change_keeps_completed_unit_then_blocks(tmp_path):
    protocol, manifest, source, ids = protocol_fixture(tmp_path)
    calls = []
    def draw(design, seed):
        calls.append(seed)
        result = deterministic_draw(design, seed)
        source.write_text("source_changed_after_first_fixture = True\n")
        return result
    root = tmp_path / "results"
    result = runner.run_e1(protocol, root, draw_callback=draw, resource_reader=resources)
    assert result["status"] == "SOURCE_OR_PROTOCOL_BLOCKED"
    assert result["new_completed_units"] == 1 and len(calls) == 1
    assert result["remaining_ids"] == [ids[1]]
    assert CheckpointStore(root, manifest, check_sources=False).load(ids[0]) is not None


def test_oracle_failure_is_saved_and_suspends_remaining_ids(tmp_path):
    protocol, manifest, _, ids = protocol_fixture(tmp_path)
    def failed_oracle(design):
        raise ValueError("injected analysis-only oracle failure")
    root = tmp_path / "results"
    result = runner.run_e1(protocol, root, draw_callback=deterministic_draw,
        oracle_callback=failed_oracle, resource_reader=resources)
    record = CheckpointStore(root, manifest).load(ids[0])["result"]
    assert result["status"] == "ERROR_CHECKPOINTED"
    assert result["new_completed_units"] == 1 and result["remaining_ids"] == [ids[1]]
    assert record["status"] == "ORACLE_FAILURE"
    assert record["full_family_failure"] and record["unassessable_whole_trial"]
    assert record["data_digest"] and record["failure_raw_debug"]
    assert len(record["certificate_records"]) == 20

"""Explicit deterministic fixtures for E2/E3/E4; never sample scientific logs."""

import json

import numpy as np
import pytest

from comet.checkpoint_store import CheckpointStore, NAMESPACE, REQUIRED_INPUTS, freeze_protocol
from comet.residual_truncation import CertificatePlan
from experiments.core_graph_dgp import CoreLog
from experiments.suite_designs import evaluate_suite_oracle, generate_suite_from_primitives
import experiments.extension_runner as runner


def resources(_):
    return dict(free_disk_bytes=10 * runner.GIB, available_ram_bytes=runner.GIB,
                worker_rss_bytes=128 * 2**20)


def fixture_config(suite, cell, n=64):
    ids = [f"{NAMESPACE}/{suite}/{cell}/{rep:04d}" for rep in range(2)]
    return dict(namespace=NAMESPACE, suite="DETERMINISTIC_EXTENSION_FIXTURE", target_suite=suite,
        legacy_new_outcome_draws=0, primary_units=0, total_unit_cap=32000, workers=1,
        planned_run_ids=ids, N=n, levels=[0.05, 0.1], truncation_multipliers=[0.5, 1, 2],
        normalized_risk_threshold=0.0 if suite == "E3" else 0.4, numerical_guard=1e-10,
        master_seed=9, seed_domain=NAMESPACE + "/" + suite + "-fixture",
        raw_debug_run_ids=[ids[0]], analysis_bootstrap_seed=3, analysis_bootstrap_resamples=0,
        primary_comparisons=[[cell, method] for method in runner.methods_for_extension_cell(suite, cell)],
        git_sha="DETERMINISTIC_FIXTURE_NOT_SCIENCE")


def protocol_fixture(tmp_path, suite="E2", cell="hub16-extreme1e-4", n=64):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    for name in REQUIRED_INPUTS:
        (inputs / name).write_text("DETERMINISTIC EXTENSION TEST ONLY: " + name)
    source = tmp_path / "fixture_source.py"
    source.write_text("fixture_only=1\n")
    config = fixture_config(suite, cell, n)
    protocol = tmp_path / "protocol.json"
    manifest = freeze_protocol(protocol, config, [source], inputs)
    return protocol, manifest, source


def deterministic_draw(design, seed):
    core = design.core
    return generate_suite_from_primitives(design, np.zeros(core.n, dtype=np.uint32),
        {source: 1.0 for source in core.outcome_source_ids})


@pytest.fixture(autouse=True)
def forbid_random_scientific_draw(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("deterministic test called draw_suite_log")
    monkeypatch.setattr(runner, "draw_suite_log", forbidden)


@pytest.mark.parametrize("suite,units,cells,comparisons", [
    ("E2", 1800, 6, 60), ("E3", 3600, 12, 108), ("E4", 7200, 24, 192)])
def test_exact_extension_identifiers_and_predeclared_families(suite, units, cells, comparisons):
    ids = runner.planned_extension_ids(suite)
    assert len(ids) == len(set(ids)) == units
    assert len(runner.suite_cells(suite)) == cells
    assert len(runner.primary_extension_comparisons(suite)) == comparisons
    assert all(value.startswith(NAMESPACE + "/" + suite + "/") for value in ids)


def test_production_config_requires_actual_note_grid_and_fixed_budget():
    config = fixture_config("E2", "hub1-moderate")
    config.pop("suite")
    config.pop("target_suite")
    config.pop("N")
    config.pop("planned_run_ids")
    config.pop("primary_units")
    config.pop("primary_comparisons")
    config.update(truncation_grid_source="THEORY_NOTE.md section 5",
        planning_inputs_reconciled=True, theorem_status="PROVED_UNDER_DECLARED_ASSUMPTIONS",
        raw_debug_run_ids=[], analysis_bootstrap_resamples=2000)
    with pytest.raises(ValueError, match="49 points"):
        runner._validate_config(config, "E2")
    config["truncation_multipliers"] = [2 ** (j / 4) for j in range(-24, 25)]
    result = runner._validate_config(config, "E2")
    assert result["primary_units"] == 1800 and result["N"] == 32768
    assert len(result["planned_run_ids"]) == 1800
    assert result["total_unit_cap"] == 32000


def test_E2_global_envelope_pays_for_unmasked_outside_policy_not_local_zero_weights():
    moderate = fixture_config("E2", "hub16-moderate")
    extreme = fixture_config("E2", "hub16-extreme1e-4")
    left, lplans, _, lextra = runner.build_extension_plans(moderate, "hub16-moderate")
    right, rplans, _, rextra = runner.build_extension_plans(extreme, "hub16-extreme1e-4")
    query_id = "E2/policy0/auditor1"
    index = [query.query_id for query in left.queries].index(query_id)
    assert lplans[(0.05, "truncated_local")][index].radius == rplans[(0.05, "truncated_local")][index].radius
    assert rextra["global_policy_envelope_maxima"][query_id] > 100 * lextra["global_policy_envelope_maxima"][query_id]
    assert rplans[(0.05, "truncated_global_envelope")][index].radius > lplans[(0.05, "truncated_global_envelope")][index].radius
    # Only the bound is made global; the actual estimator d is still local.
    assert np.all(rplans[(0.05, "truncated_global_envelope")][index].weights[right.n // 2:] == 0)
    first_id = moderate["planned_run_ids"][0]
    outside_id = first_id.replace("hub16-moderate", "hub64-extreme1e-4")
    assert runner._seed_for_run(moderate, first_id) == runner._seed_for_run(extreme, outside_id)


@pytest.mark.parametrize("suite,cell,n,frames", [
    ("E2", "hub16-extreme1e-4", 64, 20),
    ("E3", "support100-moderate-bounded", 64, 22),
    ("E4", "moderate-bounded-gapzero", 64, 20),
])
def test_resume_is_immutable_and_all_engines_share_one_deterministic_log(tmp_path, suite, cell, n, frames):
    protocol, manifest, _ = protocol_fixture(tmp_path, suite, cell, n)
    global_root, calls = tmp_path / "global", []
    root = global_root / suite
    def draw(design, seed):
        calls.append(seed)
        return deterministic_draw(design, seed)
    result = runner.run_extension(protocol, root, global_results_root=global_root,
        max_new_units=1, draw_callback=draw, resource_reader=resources, progress=False)
    assert result["new_completed_units"] == 1 and len(calls) == 1
    assert not result["background_work_running"]
    store = CheckpointStore(root, manifest)
    first_id = manifest["config"]["planned_run_ids"][0]
    record = store.load(first_id)["result"]
    original = store.path(first_id).read_bytes()
    assert record["legacy_new_outcome_draws"] == record["new_scientific_units"] == 0
    assert len(record["trials"]) == len(record["certificate_records"]) == frames
    assert all(not trial["return_endpoint_applicable"] for trial in record["trials"])
    if suite == "E3":
        assert record["family_size"] == 16
        baseline = [frame for frame in record["certificate_records"] if frame["method"] == runner.JOINT_LEVEL]
        assert all(frame["underlying_family_size"] == 20 for frame in baseline)
    runner.run_extension(protocol, root, global_results_root=global_root, max_new_units=0,
        draw_callback=draw, resource_reader=resources, progress=False)
    assert len(calls) == 1 and store.path(first_id).read_bytes() == original


def test_joint_level_methods_and_decisions_all_finish_before_oracle(tmp_path, monkeypatch):
    protocol, manifest, _ = protocol_fixture(tmp_path, "E3", "support100-moderate-bounded")
    count, original = [], CertificatePlan.evaluate
    def observed(self, *args, **kwargs):
        count.append(self.query_id)
        return original(self, *args, **kwargs)
    monkeypatch.setattr(CertificatePlan, "evaluate", observed)
    def oracle(design):
        assert len(count) == 2 * (10 * 16 + 20)
        return evaluate_suite_oracle(design)
    root = tmp_path / "global" / "E3"
    result = runner.run_extension(protocol, root, global_results_root=root.parent,
        max_new_units=1, draw_callback=deterministic_draw, oracle_callback=oracle,
        resource_reader=resources, progress=False)
    assert result["new_completed_units"] == 1


def test_gamma_zero_analytic_truth_is_exactly_threshold_and_false_violation_counted(tmp_path, monkeypatch):
    protocol, manifest, _ = protocol_fixture(tmp_path, "E4", "moderate-bounded-gapzero")
    original = CertificatePlan.evaluate
    def injected_violation(self, *args, **kwargs):
        record = original(self, *args, **kwargs)
        if self.query_id == "E4/policy0/auditor0":
            record.update(lo=0.41, hi=0.6, empty_intersection=False)
        return record
    monkeypatch.setattr(CertificatePlan, "evaluate", injected_violation)
    def rounded_oracle(design):
        truth = evaluate_suite_oracle(design)
        truth[design.metadata["planted_query_id"]] = 0.40000000000001
        return truth
    root = tmp_path / "global" / "E4"
    runner.run_extension(protocol, root, global_results_root=root.parent,
        max_new_units=1, draw_callback=deterministic_draw, oracle_callback=rounded_oracle,
        resource_reader=resources, progress=False)
    record = CheckpointStore(root, manifest).load(manifest["config"]["planned_run_ids"][0])["result"]
    assert record["truths"]["E4/policy0/auditor0"] == 0.4
    assert all(trial["primary_threshold"] == 0.4 for trial in record["trials"])
    assert all(trial["primary_false_violation"] for trial in record["trials"])


def test_nonfinite_observed_fixture_keeps_every_family_and_lossless_failure_class(tmp_path):
    protocol, manifest, _ = protocol_fixture(tmp_path)
    def draw(design, seed):
        log = deterministic_draw(design, seed)
        values = log.outcomes.copy()
        values[0] = np.nan
        return CoreLog(log.actions, values, "deliberately-invalid-fixture", log.seed_namespace)
    root = tmp_path / "global" / "E2"
    runner.run_extension(protocol, root, global_results_root=root.parent,
        max_new_units=1, draw_callback=draw, resource_reader=resources, progress=False)
    record = CheckpointStore(root, manifest).load(manifest["config"]["planned_run_ids"][0])["result"]
    assert len(record["trials"]) == 20
    assert all(not trial["family_covered"] for trial in record["trials"])
    assert record["failure_raw_debug"]["outcomes"][0] == "nan"


def test_global_unit_budget_counts_other_suites_before_any_draw(tmp_path):
    protocol, manifest, _ = protocol_fixture(tmp_path)
    # A test-only cap of two units, both already represented in another suite.
    config = dict(manifest["config"], total_unit_cap=2)
    body = {key: value for key, value in manifest.items() if key != "fingerprint"}
    body["config"] = config
    from comet.checkpoint_store import canonical_bytes, digest
    updated = dict(body, fingerprint=digest(body))
    protocol.write_bytes(canonical_bytes(updated))
    global_root = tmp_path / "global"
    foreign = global_root / "E1" / "checkpoints" / "E1" / "foreign-cell"
    foreign.mkdir(parents=True)
    for rep in range(2):
        (foreign / f"{rep:04d}.json.gz").write_bytes(b"deterministic foreign-unit budget fixture")
    calls = []
    def draw(*args):
        calls.append(True)
        return deterministic_draw(*args)
    result = runner.run_extension(protocol, global_root / "E2", global_results_root=global_root,
        draw_callback=draw, resource_reader=resources, progress=False)
    assert result["status"] == "RESOURCE_CHECKPOINTED"
    assert result["new_completed_units"] == 0 and calls == []
    assert result["global_new_checkpoint_units"] == 2


def test_midrun_source_change_blocks_new_draws_and_keeps_saved_unit(tmp_path):
    protocol, manifest, source = protocol_fixture(tmp_path)
    calls = []
    def draw(design, seed):
        calls.append(seed)
        result = deterministic_draw(design, seed)
        source.write_text("changed_after_fixture=True\n")
        return result
    root = tmp_path / "global" / "E2"
    result = runner.run_extension(protocol, root, global_results_root=root.parent,
        draw_callback=draw, resource_reader=resources, progress=False)
    assert result["status"] == "SOURCE_OR_MODEL_BLOCKED"
    assert result["new_completed_units"] == 1 and len(calls) == 1
    assert len(result["remaining_ids"]) == 1
    assert len(list(CheckpointStore(root, manifest, check_sources=False).iter_completed())) == 1

"""Finite enumeration/explicit primitives only; no production negative draws."""

import gzip
import json

import numpy as np
import pytest

from comet.checkpoint_store import CheckpointStore, NAMESPACE, REQUIRED_INPUTS, freeze_protocol
from comet.residual_truncation import CERTIFIED, clipping_bias_constant
import experiments.negative_controls as controls


@pytest.fixture(autouse=True)
def forbid_scientific_rng(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("deterministic negative-control test called production RNG")
    monkeypatch.setattr(controls, "draw_negative_log", forbidden)
    monkeypatch.setattr(np.random, "default_rng", forbidden)


def explicit_log(design, seed=0):
    denominator = 5 if controls.control_specs()[design.control]["actual_e1"] == 0.2 else 2
    action_codes = np.arange(design.n, dtype=np.int64) % denominator
    spike_codes = np.ones(design.n, dtype=np.uint16)
    if design.n:
        spike_codes[0] = 0
    return controls.generate_negative_from_primitives(design, action_codes,
        shared_sign=1, spike_codes=spike_codes)


def resources(_):
    return dict(free_disk_bytes=10 * controls.GIB, available_ram_bytes=controls.GIB,
                worker_rss_bytes=128 * 2**20)


def protocol_fixture(tmp_path, control="wrong_propensity"):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    for name in REQUIRED_INPUTS:
        (inputs / name).write_text("DETERMINISTIC NEGATIVE-CONTROL FIXTURE ONLY: " + name)
    source = tmp_path / "fixture_source.py"
    source.write_text("fixture_only=1\n")
    ids = [f"{NAMESPACE}/negative_controls/{control}/{rep:04d}" for rep in range(2)]
    config = dict(namespace=NAMESPACE, suite="DETERMINISTIC_NEGATIVE_FIXTURE",
        phase="negative_controls", controls=controls.control_specs(),
        legacy_new_outcome_draws=0, primary_units=0, total_unit_cap=32000, workers=1,
        planned_run_ids=ids, N=16, levels=[0.05, 0.1], master_seed=7,
        seed_domain=NAMESPACE + "/negative-controls-fixture", risk_threshold=0.6,
        numerical_guard=1e-10, raw_debug_run_ids=[ids[0]])
    path = tmp_path / "protocol.json"
    manifest = freeze_protocol(path, config, [source], inputs)
    return path, manifest, source, ids


def test_fixed_four_controls_and_one_hundred_whole_unit_ids():
    assert set(controls.control_specs()) == set(controls.CONTROLS)
    ids = controls.planned_negative_ids()
    assert len(ids) == len(set(ids)) == 100
    assert all(value.startswith(NAMESPACE + "/negative_controls/") for value in ids)
    assert all(sum("/" + control + "/" in value for value in ids) == 25 for control in controls.CONTROLS)
    spec = controls.control_specs()
    assert spec["missing_clipping_bias"]["tau"] == 0.01
    assert spec["wrong_propensity"]["actual_e1"] == 0.2
    assert spec["wrong_propensity"]["declared_e1"] == 0.5
    assert spec["hidden_shared_shock"]["shared_amplitude"] == 0.25


@pytest.mark.parametrize("control", controls.CONTROLS)
def test_honest_false_declaration_is_refused_without_an_interval(control):
    response = controls.declared_assumption_gate(**controls.honest_declarations(control))
    assert response["status"] == "ASSUMPTION_UNVERIFIED"
    assert response["interval"] is None
    accepted = controls.declared_assumption_gate()
    assert accepted["status"] == "ASSUMPTIONS_DECLARED_NOT_EMPIRICALLY_VERIFIED"
    assert accepted["status"] != CERTIFIED


def test_shared_shock_true_clique_is_only_analytic_metadata_not_dense_adjacency():
    n = 32768
    design = controls.build_negative_design("hidden_shared_shock", n)
    assert design.declared_graph.edge_count == 0
    assert design.declared_graph.color_count == 1
    actual = design.metadata["actual_source_graph"]
    assert actual["edge_count"] == n * (n - 1) // 2
    assert actual["verified_color_count"] == n
    assert not design.metadata["schema_detectability"]
    assert "adjacency" not in actual


def test_wrong_propensity_and_leaked_fit_fail_the_DR_identity_by_finite_enumeration():
    spec = controls.control_specs()["wrong_propensity"]
    q = np.array([1 - spec["q1"], spec["q1"]])
    actual = np.array([1 - spec["actual_e1"], spec["actual_e1"]])
    declared = np.array([1 - spec["declared_e1"], spec["declared_e1"]])
    mu = np.array([spec["mu0"], spec["mu1"]])
    fitted = np.full(2, spec["nuisance"])
    wrong_scores = np.sum(q * fitted) + q / declared * (mu - fitted)
    actual_scores = np.sum(q * fitted) + q / actual * (mu - fitted)
    target = float(np.dot(q, mu))
    assert target == pytest.approx(0.68)
    assert np.dot(actual, wrong_scores) == pytest.approx(0.5)
    assert np.dot(actual, actual_scores) == pytest.approx(target)
    # Each leaked fit is observed Y in both states: its residual is zero and
    # direct term equals that Y, so the expectation is the logger mean .32.
    assert np.dot(actual, mu) == pytest.approx(0.32)
    for control in ("wrong_propensity", "evaluation_nuisance_leak"):
        design = controls.build_negative_design(control, 20)
        assert design.metadata["actual_source_graph"]["edge_count"] == 0
        assert not design.metadata["schema_detectability"]


def test_fixed_tau_bias_and_raw_residual_moment_are_analytic_not_empirical():
    actual = controls.analytic_control_targets()["missing_clipping_bias"]
    p, tau = 1.5, 0.01
    residuals = np.array([-0.2, 99.8])
    probability = np.array([0.995, 0.005])
    raw = float(np.dot(probability, residuals))
    clipped = float(np.dot(probability, np.clip(residuals, -tau, tau)))
    moment = float(np.dot(probability, np.abs(residuals) ** p))
    assert raw + 0.5 == pytest.approx(0.8)
    assert clipped + 0.5 == pytest.approx(0.4901)
    assert raw - clipped == pytest.approx(0.3099)
    assert actual["expected_clipped"] == pytest.approx(0.4901)
    assert actual["exact_clipping_bias"] == pytest.approx(0.3099)
    assert actual["raw_residual_p_moment"] == pytest.approx(moment)
    pointwise = np.maximum(np.abs(residuals) - tau, 0)
    debit = clipping_bias_constant(p) * np.abs(residuals) ** p * tau ** (1 - p)
    assert np.all(pointwise <= debit)
    assert actual["proved_bias_bound"] >= abs(raw - clipped)
    assert actual["proved_bias_bound"] == pytest.approx(clipping_bias_constant(p) * moment * tau ** (1-p))
    assert controls.control_specs()["missing_clipping_bias"]["schema_detectability"]


@pytest.mark.parametrize("control", controls.CONTROLS)
def test_explicit_primitive_generation_is_bounded_where_declared_and_readonly(control):
    design = controls.build_negative_design(control, 20)
    first, second = explicit_log(design), explicit_log(design)
    assert first.data_digest == second.data_digest
    assert np.isfinite(first.outcomes).all()
    if control != "missing_clipping_bias":
        assert np.all((first.outcomes >= 0) & (first.outcomes <= 1))
    else:
        assert first.outcomes.max() > 1
    with pytest.raises(ValueError):
        first.outcomes[0] = 0
    with pytest.raises(ValueError, match="logging code"):
        controls.generate_negative_from_primitives(design, np.full(20, 5, dtype=np.int64))


@pytest.mark.parametrize("control", controls.CONTROLS)
def test_invalid_path_is_heuristic_and_honest_refusal_has_no_zero_error_evidence(control):
    design = controls.build_negative_design(control, 20)
    result = controls.evaluate_negative_unit(design, explicit_log(design))
    assert result["threshold"] == 0.6
    assert len(result["trials"]) == len(result["certificate_records"]) == 6
    assert result["negative_controls_not_primary"] and not result["primary_family_modified"]
    for trial in result["trials"]:
        assert not trial["primary_comparison"] and not trial["theorem_validity_test"]
        if trial["engine"] == "intentionally_invalid":
            assert trial["status"] == trial["guarantee_type"] == controls.HEURISTIC
            assert trial["interval_expected"] and trial["interval_issued"]
        elif trial["engine"] == "honest_refusal":
            assert trial["status"] == "ASSUMPTION_UNVERIFIED"
            assert not trial["interval_expected"] and not trial["interval_issued"]
            assert trial["any_false_claim"] is None
            assert trial["false_safe"] is None and trial["false_violation"] is None
            assert not trial["error_metrics_assessable"]
        else:
            assert trial["status"] == CERTIFIED
    invalid = [record["certificate"] for record in result["certificate_records"]
               if record["engine"] == "intentionally_invalid"]
    assert all(record["underlying_engine_declared_status"] == CERTIFIED for record in invalid)


def test_balanced_finite_exposure_fixture_separates_true_target_wrong_e_and_leak():
    for control, wrong_mean in (("wrong_propensity", 0.5), ("evaluation_nuisance_leak", 0.32)):
        design = controls.build_negative_design(control, 20)
        result = controls.evaluate_negative_unit(design, explicit_log(design))
        assert result["analytic_truth"] == 0.68
        valid = [entry["certificate"] for entry in result["certificate_records"]
                 if entry["engine"] == "valid_actual_model"]
        invalid = [entry["certificate"] for entry in result["certificate_records"]
                   if entry["engine"] == "intentionally_invalid"]
        assert all(entry["estimate"] == pytest.approx(0.68) for entry in valid)
        assert all(entry["estimate"] == pytest.approx(wrong_mean) for entry in invalid)


def test_fixed_tau_same_estimator_and_stochastic_terms_differ_only_by_bias_debit():
    design = controls.build_negative_design("missing_clipping_bias", 20)
    result = controls.evaluate_negative_unit(design, explicit_log(design))
    by_key = {(entry["delta"], entry["engine"]): entry["certificate"]
              for entry in result["certificate_records"]}
    for delta in (0.05, 0.1):
        valid = by_key[delta, "valid_actual_model"]
        invalid = by_key[delta, "intentionally_invalid"]
        assert valid["tau"] == invalid["tau"] == 0.01
        assert valid["estimate"] == invalid["estimate"]
        assert valid["concentration"] == invalid["concentration"]
        assert valid["range_contribution"] == invalid["range_contribution"]
        assert valid["bias"] > 0 and invalid["bias"] == 0
        assert valid["radius"] == pytest.approx(invalid["radius"] + valid["bias"])
        assert valid["lo"] <= 0.8 <= valid["hi"]


def test_numerical_refusal_is_preserved_for_every_expected_interval():
    from dataclasses import replace
    design = controls.build_negative_design("missing_clipping_bias", 16)
    ordinary = explicit_log(design)
    invalid = ordinary.outcomes.copy()
    invalid[0] = np.nan
    log = replace(ordinary, outcomes=invalid, data_digest="deliberately-nonfinite-fixture")
    result = controls.evaluate_negative_unit(design, log)
    assert result["status"] == "NUMERICAL_FAILURE_PRESERVED"
    assert len(result["trials"]) == 6
    for trial in result["trials"]:
        if trial["interval_expected"]:
            assert not trial["interval_covered"] and not trial["interval_issued"]
            assert trial["status"] == "NUMERICAL_FAILURE"
            assert trial["any_false_claim"] is None
    assert result["failure_raw_debug"]["outcomes"][0] == "nan"


def test_checkpoint_resume_keeps_completed_bytes_and_analyzes_no_refusal_risk_evidence(tmp_path):
    protocol, manifest, _, ids = protocol_fixture(tmp_path)
    global_root, calls = tmp_path / "global", []
    root = global_root / "negative_controls"
    def callback(design, seed):
        calls.append(seed)
        return explicit_log(design)
    result = controls.run_negative_controls(protocol, root, global_results_root=global_root,
        max_new_units=1, draw_callback=callback, resource_reader=resources, progress=False)
    assert result["new_completed_units"] == 1 and len(calls) == 1
    assert not result["background_work_running"] and result["remaining_ids"] == [ids[1]]
    store = CheckpointStore(root, manifest)
    before = store.path(ids[0]).read_bytes()
    record = store.load(ids[0])["result"]
    assert record["new_scientific_units"] == record["legacy_new_outcome_draws"] == 0
    assert len(record["trials"]) == 6 and "prespecified_raw_debug" in record
    resumed = controls.run_negative_controls(protocol, root, global_results_root=global_root,
        max_new_units=0, draw_callback=callback, resource_reader=resources, progress=False)
    assert resumed["new_completed_units"] == 0 and len(calls) == 1
    assert store.path(ids[0]).read_bytes() == before
    status = controls.negative_status(protocol, root, list_ids=True)
    assert status["completed_ids"] == [ids[0]] and status["remaining_ids"] == [ids[1]]
    output = tmp_path / "analysis"
    summary = controls.analyze_negative_controls(protocol, root, output)
    assert summary["status"] == "PARTIAL" and summary["completed_units"] == 1
    assert summary["reported_new_scientific_units"] == 0
    assert summary["primary_comparison_count"] == 0 and not summary["holm_applied"]
    assert not summary["primary_families_modified"]
    assert len(summary["summaries"]) == 6
    for row in summary["summaries"]:
        assert row["independent_units"] == 1
        if row["engine"] == "honest_refusal":
            assert row["issued_intervals"] == 0 and row["honest_refusals"] == 1
            assert row["interval_coverage"] is None
            assert row["false_claim"]["denominator"] == 0
            assert row["false_claim"]["rate"] is row["false_claim"]["wilson95"] is None
        else:
            assert row["interval_coverage"]["denominator"] == 1
    with pytest.raises(FileExistsError, match="immutable"):
        controls.analyze_negative_controls(protocol, root, output)


def test_empty_failed_unit_keeps_whole_unit_denominator_and_unknown_error_rates(tmp_path):
    protocol, manifest, _, ids = protocol_fixture(tmp_path)
    root = tmp_path / "global" / "negative_controls"
    controls.run_negative_controls(protocol, root, global_results_root=root.parent,
        max_new_units=1, draw_callback=explicit_log, resource_reader=resources, progress=False)
    store = CheckpointStore(root, manifest)
    store.complete(ids[1], dict(status="UNIT_FAILURE_PRESERVED", control="wrong_propensity",
        failure_reason="handwritten deterministic unknown unit", trials=[],
        unassessable_whole_trial=True, full_family_failure=True,
        new_scientific_units=0, legacy_new_outcome_draws=0))
    summary = controls.analyze_negative_controls(protocol, root, tmp_path / "analysis")
    assert summary["status"] == "COMPLETE" and summary["completed_units"] == 2
    assert summary["failed_units"] == 1
    for row in summary["summaries"]:
        assert row["independent_units"] == 2
        if row["engine"] != "honest_refusal":
            assert row["interval_coverage"]["denominator"] == 2
            assert row["numerical_failures"] == 1
            assert row["false_claim"]["unknown_units"] == 1
            assert row["false_claim"]["rate"] is row["false_claim"]["wilson95"] is None


def test_corrupt_payload_and_changed_science_reject_before_any_new_fixture(tmp_path):
    protocol, manifest, source, ids = protocol_fixture(tmp_path)
    root = tmp_path / "global" / "negative_controls"
    controls.run_negative_controls(protocol, root, global_results_root=root.parent,
        max_new_units=1, draw_callback=explicit_log, resource_reader=resources, progress=False)
    store = CheckpointStore(root, manifest)
    record = json.loads(gzip.decompress(store.path(ids[0]).read_bytes()))
    record["payload"]["result"]["data_digest"] = "corrupted"
    store.path(ids[0]).write_bytes(gzip.compress(json.dumps(record).encode()))
    with pytest.raises(ValueError, match="corrupt checkpoint"):
        controls.negative_status(protocol, root)
    source.write_text("source_changed=True\n")
    with pytest.raises(ValueError, match="source changed"):
        controls.run_negative_controls(protocol, root, global_results_root=root.parent,
            draw_callback=explicit_log, resource_reader=resources, progress=False)


def test_midrun_source_change_preserves_current_unit_and_blocks_remainder(tmp_path):
    protocol, manifest, source, ids = protocol_fixture(tmp_path)
    root, calls = tmp_path / "global" / "negative_controls", []
    def callback(design, seed):
        calls.append(seed)
        log = explicit_log(design)
        source.write_text("changed_after_first_explicit_fixture=True\n")
        return log
    result = controls.run_negative_controls(protocol, root, global_results_root=root.parent,
        draw_callback=callback, resource_reader=resources, progress=False)
    assert result["status"] == "SOURCE_OR_MODEL_BLOCKED"
    assert result["new_completed_units"] == 1 and len(calls) == 1
    assert result["remaining_ids"] == [ids[1]]
    assert CheckpointStore(root, manifest, check_sources=False).load(ids[0]) is not None


def test_global_cap_counts_foreign_suite_units_without_multiplying_engines(tmp_path):
    protocol, manifest, _, _ = protocol_fixture(tmp_path)
    from comet.checkpoint_store import canonical_bytes, digest
    config = dict(manifest["config"], total_unit_cap=2)
    body = {key: value for key, value in manifest.items() if key != "fingerprint"}
    body["config"] = config
    protocol.write_bytes(canonical_bytes(dict(body, fingerprint=digest(body))))
    global_root = tmp_path / "global"
    foreign = global_root / "E1" / "checkpoints" / "E1" / "foreign-fixture"
    foreign.mkdir(parents=True)
    for index in range(2):
        (foreign / f"{index:04d}.json.gz").write_bytes(b"handwritten foreign-unit accounting fixture")
    calls = []
    def callback(*args):
        calls.append(True)
        return explicit_log(*args)
    result = controls.run_negative_controls(protocol, global_root / "negative_controls",
        global_results_root=global_root, draw_callback=callback, resource_reader=resources, progress=False)
    assert result["status"] == "RESOURCE_CHECKPOINTED"
    assert result["new_completed_units"] == 0 and result["global_new_checkpoint_units"] == 2
    assert calls == []


def test_no_completed_units_is_not_invented_diagnostic_evidence(tmp_path):
    protocol, _, _, _ = protocol_fixture(tmp_path)
    result = controls.analyze_negative_controls(protocol, tmp_path / "empty", tmp_path / "analysis")
    assert result["status"] == "NO_COMPLETED_UNITS"
    assert result["completed_units"] == result["reported_new_scientific_units"] == 0
    assert result["summaries"] == []


def test_status_refuses_a_primary_suite_protocol_in_negative_namespace_view(tmp_path):
    protocol, manifest, _, _ = protocol_fixture(tmp_path)
    from comet.checkpoint_store import canonical_bytes, digest
    body = {key: value for key, value in manifest.items() if key != "fingerprint"}
    body["config"] = dict(body["config"], suite="E1")
    protocol.write_bytes(canonical_bytes(dict(body, fingerprint=digest(body))))
    with pytest.raises(ValueError, match="not a supplementary"):
        controls.negative_status(protocol, tmp_path / "global" / "negative_controls")

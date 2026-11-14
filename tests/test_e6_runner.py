"""Artificial covariate ZIPs and explicit logger words; no real ACS or RNG."""

import csv
from dataclasses import replace
import gzip
import hashlib
import io
import json
from zipfile import ZipFile

import numpy as np
import pytest

from comet.checkpoint_store import CheckpointStore, NAMESPACE, REQUIRED_INPUTS, canonical_bytes, digest, freeze_protocol
from comet.residual_truncation import CertificatePlan
from experiments.semisynthetic_selective_labels import ArchiveSpec, DatasetBlockedError, load_acs_archive, prepare_archive
import experiments.e6_runner as runner


def artificial_vault(tmp_path, n=40):
    columns = ["SERIALNO", "SPORDER", "ST", "YEAR", "AGEP", "PINCP", "WKHP", "PWGTP",
               "COW", "SCHL", "MAR", "OCCP", "POBP", "RELP", "SEX", "RAC1P"]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns)
    writer.writeheader()
    for index in range(n):
        writer.writerow(dict(SERIALNO=f"fixture-{index:04d}", SPORDER=1, ST="06", YEAR=2018,
            AGEP=17+index, PINCP=60000 if index % 2 else 30000, WKHP=20+index % 5,
            PWGTP=1, COW=1, SCHL=10+index % 6, MAR=1, OCCP=100, POBP=6, RELP=0,
            SEX=1+index % 2, RAC1P=1))
    archive = tmp_path / "artificial-fixture-not-real-ACS.zip"
    with ZipFile(archive, "w") as zipped:
        zipped.writestr("psam_p06.csv", stream.getvalue())
    sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    return load_acs_archive(archive, ArchiveSpec(sha, fixture=True)), archive, sha


def fixture_protocol(tmp_path, cell="moderate-loggercycle"):
    vault, archive, sha = artificial_vault(tmp_path)
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    for name in REQUIRED_INPUTS:
        (inputs / name).write_text("DETERMINISTIC E6 FIXTURE ONLY: " + name)
    source = tmp_path / "fixture_source.py"
    source.write_text("fixture_only=1\n")
    ids = [f"{NAMESPACE}/E6/{cell}/{rep:04d}" for rep in range(2)]
    config = dict(namespace=NAMESPACE, suite="DETERMINISTIC_E6_FIXTURE", workers=1,
        legacy_new_outcome_draws=0, primary_units=0, total_unit_cap=32000,
        planned_run_ids=ids, cells=[cell], split_sizes=dict(training=8, discovery=8, certification=16),
        levels=[0.05, 0.1], risk_threshold=0.32, utility_margin=0.01, service_floor=0.2,
        capacity_ceiling=0.6, ridge=1.0, max_rules=4, max_depth=4, minimum_mass=0.02,
        tradeoff_grid=list(runner.TRADEOFF_GRID), arms=list(runner.ARMS),
        certified_arms=list(runner.CERTIFIED_ARMS),
        primary_comparisons=[[cell, arm] for arm in runner.CERTIFIED_ARMS],
        truncation_multipliers=[0.5, 1.0, 2.0], numerical_guard=1e-10,
        master_seed=4, seed_domain=NAMESPACE + "/E6-fixture", raw_debug_run_ids=[ids[0]],
        analysis_bootstrap_seed=8, analysis_bootstrap_resamples=0,
        archive_sha256=sha, archive_path=str(archive),
        dataset_population_digest=vault.certifier_view.population_digest)
    protocol = tmp_path / "fixture_protocol.json"
    manifest = freeze_protocol(protocol, config, [source], inputs)
    return protocol, manifest, source, ids, vault


def explicit_draw(vault, split, seed):
    words = np.zeros(split.n, dtype=np.uint32)
    selectors = np.zeros(split.n, dtype=np.uint32) if split.graph_kind == "cycle" else None
    return vault.observe_from_words(split, words, selector_words=selectors,
                                    seed_namespace=split.namespace + "/explicit-fixture")


def resources(_):
    return dict(free_disk_bytes=10 * runner.GIB, available_ram_bytes=runner.GIB,
                worker_rss_bytes=128 * 2**20)


@pytest.fixture(autouse=True)
def forbid_rng(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("E6 deterministic test reached a random production driver")
    monkeypatch.setattr(runner, "draw_e6_split", forbidden)
    monkeypatch.setattr(np.random, "default_rng", forbidden)


def test_four_fixed_cells_one_thousand_ids_and_data_gated_status(tmp_path):
    assert len(runner.e6_cell_ids()) == 4
    ids = runner.planned_e6_ids()
    assert len(ids) == len(set(ids)) == 1000
    assert len(runner.primary_e6_comparisons()) == 16
    result = runner.e6_status(tmp_path / "no-protocol.json", tmp_path / "results", list_ids=True)
    assert result["status"] == "DATA_BLOCKED_OR_NOT_FROZEN"
    assert result["completed_units"] == 0 and result["remaining_units"] == 1000
    assert result["remaining_ids"] == ids


def test_absent_real_archive_prevents_protocol_freeze_before_source_commit(tmp_path):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    for name in REQUIRED_INPUTS:
        (inputs / name).write_text("planning fixture only")
    config = dict(archive_path=str(tmp_path / "missing-census-archive.zip"), archive_sha256="0"*64,
        prepared_directory=str(tmp_path / "missing-preparation"), master_seed=5,
        seed_domain=NAMESPACE + "/E6/v1", truncation_multipliers=[2**(j/4) for j in range(-24,25)],
        truncation_grid_source="THEORY_NOTE.md", planning_inputs_reconciled=True,
        theorem_status="PROVED_UNDER_DECLARED_ASSUMPTIONS", numerical_guard=1e-10,
        raw_debug_run_ids=[], analysis_bootstrap_seed=9, analysis_bootstrap_resamples=2000,
        production_environment=runner.environment_signature())
    path, protocol = tmp_path / "config.json", tmp_path / "must-not-exist.json"
    path.write_text(json.dumps(config))
    with pytest.raises(DatasetBlockedError, match="actual selected archive"):
        runner.freeze_e6(path, inputs, protocol)
    assert not protocol.exists()


def test_prepared_artificial_population_cannot_be_relabelled_production(tmp_path):
    _, archive, sha = artificial_vault(tmp_path)
    prepared = tmp_path / "prepared"
    prepare_archive(archive, sha, prepared, split_sizes=dict(training=8, discovery=8, certification=16), fixture=True)
    with pytest.raises(DatasetBlockedError, match="deterministic fixture"):
        runner.load_prepared_e6(dict(archive_path=str(archive),archive_sha256=sha,
            prepared_directory=str(prepared),seed_domain="fixture",split_sizes=dict(training=8,discovery=8,certification=16)))


@pytest.mark.parametrize("cell", ["moderate-loggerindependent", "moderate-loggercycle"])
def test_complete_three_split_trial_has_full_family_safety_usefulness_and_immutable_resume(tmp_path, cell):
    protocol, manifest, _, ids, vault = fixture_protocol(tmp_path, cell)
    calls = []
    def draw(v, split, seed):
        calls.append(split.name)
        return explicit_draw(v, split, seed)
    root = tmp_path / "global" / "E6"
    result = runner.run_e6(protocol, root, global_results_root=root.parent,
        max_new_units=1, vault=vault, draw_callback=draw, resource_reader=resources, progress=False)
    assert result["new_completed_units"] == 1 and calls == ["training", "discovery", "certification"]
    store = CheckpointStore(root, manifest)
    before = store.path(ids[0]).read_bytes()
    payload = store.load(ids[0])["result"]
    assert payload["suite"] == "E6" and payload["new_scientific_units"] == 0
    assert payload["legacy_new_outcome_draws"] == 0
    assert payload["dataset_population_digest"] == vault.certifier_view.population_digest
    assert len(payload["trials"]) == len(payload["certificate_records"]) == 16
    family = payload["proper_family"]
    assert family["actual_family_size"] == family["risk_coordinate_count"] + family["utility_coordinate_count"]
    assert family["utility_coordinate_count"] > 0
    for trial in payload["trials"]:
        assert trial["discovery_best_planted_iou"] is None
        assert not trial["planted_group_recovery_applicable"]
        if trial["return_safe_useful"]:
            assert trial["returned"] and not trial["return_unsafe"]
            assert trial["return_and_utility_noninferior"] and trial["return_and_service_feasible"]
    local = [frame for frame in payload["certificate_records"] if frame["method"] == "comet_local"]
    matched = [frame for frame in payload["certificate_records"] if frame["method"] == "generic_matched"]
    assert [frame["selection"] for frame in local] == [frame["selection"] for frame in matched]
    assert payload["coordinate_truths_by_family"]
    assert len(payload["source_split_digests"]) == 3
    assert payload["causal_intervention_claimed"] is False
    runner.run_e6(protocol, root, global_results_root=root.parent, max_new_units=0,
        vault=vault, draw_callback=draw, resource_reader=resources, progress=False)
    assert calls == ["training", "discovery", "certification"]
    assert store.path(ids[0]).read_bytes() == before


def test_finite_population_oracle_is_joined_after_every_certificate_and_decision(tmp_path, monkeypatch):
    protocol, _, _, _, vault = fixture_protocol(tmp_path)
    evaluations, boundary = [], []
    original_plan, original_oracle = CertificatePlan.evaluate, runner.evaluate_e6_pipeline
    def observed_plan(self, *args, **kwargs):
        evaluations.append(self.query_id)
        return original_plan(self, *args, **kwargs)
    def oracle(*args, **kwargs):
        assert evaluations
        if not boundary:
            boundary.append(len(evaluations))
        assert len(evaluations) == boundary[0]
        return original_oracle(*args, **kwargs)
    monkeypatch.setattr(CertificatePlan, "evaluate", observed_plan)
    monkeypatch.setattr(runner, "evaluate_e6_pipeline", oracle)
    root = tmp_path / "global" / "E6"
    result = runner.run_e6(protocol, root, global_results_root=root.parent,
        max_new_units=1, vault=vault, draw_callback=explicit_draw, resource_reader=resources, progress=False)
    assert result["new_completed_units"] == 1 and boundary


def test_oracle_failure_is_saved_with_three_observed_splits_and_unknown_full_trial(tmp_path, monkeypatch):
    protocol, manifest, _, ids, vault = fixture_protocol(tmp_path)
    def failed(*args, **kwargs):
        raise ValueError("injected finite-population oracle failure")
    monkeypatch.setattr(runner, "evaluate_e6_pipeline", failed)
    root = tmp_path / "global" / "E6"
    result = runner.run_e6(protocol, root, global_results_root=root.parent,
        vault=vault, draw_callback=explicit_draw, resource_reader=resources, progress=False)
    payload = CheckpointStore(root, manifest).load(ids[0])["result"]
    assert result["status"] == "ERROR_CHECKPOINTED" and result["new_completed_units"] == 1
    assert payload["unassessable_whole_trial"] and payload["trials"] == []
    assert len(payload["raw_debug"]) == len(payload["source_split_digests"]) == 3
    assert result["remaining_ids"] == [ids[1]]


def test_corrupt_payload_and_changed_source_refuse_before_any_new_trial(tmp_path):
    protocol, manifest, source, ids, vault = fixture_protocol(tmp_path)
    root = tmp_path / "global" / "E6"
    runner.run_e6(protocol, root, global_results_root=root.parent,
        max_new_units=1, vault=vault, draw_callback=explicit_draw, resource_reader=resources, progress=False)
    store = CheckpointStore(root, manifest)
    record = json.loads(gzip.decompress(store.path(ids[0]).read_bytes()))
    record["payload"]["result"]["archive_sha256"] = "corrupted"
    store.path(ids[0]).write_bytes(gzip.compress(json.dumps(record).encode()))
    with pytest.raises(ValueError, match="corrupt checkpoint"):
        runner.e6_status(protocol, root)
    source.write_text("changed=True\n")
    with pytest.raises(ValueError, match="source changed"):
        runner.run_e6(protocol, root, global_results_root=root.parent,
            vault=vault, draw_callback=explicit_draw, resource_reader=resources, progress=False)


def test_global_new_unit_cap_includes_other_suites_before_e6_draw(tmp_path):
    protocol, manifest, _, _, vault = fixture_protocol(tmp_path)
    body = {key:value for key,value in manifest.items() if key != "fingerprint"}
    body["config"] = dict(body["config"], total_unit_cap=2)
    updated = dict(body, fingerprint=digest(body))
    protocol.write_bytes(canonical_bytes(updated))
    global_root = tmp_path / "global"
    foreign = global_root / "E5" / "checkpoints" / "E5" / "foreign"
    foreign.mkdir(parents=True)
    for index in range(2):
        (foreign / f"{index:04d}.json.gz").write_bytes(b"foreign deterministic budget fixture")
    calls=[]
    def draw(*args):
        calls.append(True)
        return explicit_draw(*args)
    result = runner.run_e6(protocol, global_root / "E6", global_results_root=global_root,
        vault=vault, draw_callback=draw, resource_reader=resources, progress=False)
    assert result["status"] == "RESOURCE_CHECKPOINTED"
    assert result["new_completed_units"] == 0 and calls == []


def test_completed_artificial_trial_streams_into_e6_analysis_without_real_data(tmp_path):
    from experiments.e6_analyze import analyze_e6
    protocol, _, _, _, vault = fixture_protocol(tmp_path)
    root = tmp_path / "global" / "E6"
    runner.run_e6(protocol, root, global_results_root=root.parent, max_new_units=1,
        vault=vault, draw_callback=explicit_draw, resource_reader=resources, progress=False)
    summary = analyze_e6(protocol, root, tmp_path / "analysis", bootstrap_resamples=0)
    assert summary["completed_units"] == 1 and summary["remaining_units"] == 1
    assert summary["phase"] == "DETERMINISTIC_FIXTURE_NOT_REAL_ACS_OR_SCIENCE"
    assert len(summary["summaries"]) == 16
    assert summary["dataset_population_digest"] == vault.certifier_view.population_digest
    assert all(row["independent_trials"] == 1 for row in summary["summaries"])

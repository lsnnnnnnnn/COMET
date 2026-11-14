import gzip
import json

import pytest

from comet.checkpoint_store import (
    CheckpointStore, NAMESPACE, REQUIRED_INPUTS, freeze_protocol, planning_input_hashes,
)


def fixture(tmp_path):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    for name in REQUIRED_INPUTS:
        (inputs / name).write_text("DETERMINISTIC TEST FIXTURE: " + name)
    source = tmp_path / "science.py"
    source.write_text("test_only = True\n")
    ids = [NAMESPACE + "/deterministic/tiny/0000", NAMESPACE + "/deterministic/tiny/0001"]
    config = dict(namespace=NAMESPACE, legacy_new_outcome_draws=0, primary_units=0,
                  total_unit_cap=2, workers=1, planned_run_ids=ids)
    manifest = freeze_protocol(tmp_path / "protocol.json", config, [source], inputs)
    return manifest, source, inputs, ids


def test_completed_bytes_preserved_and_generator_never_called_on_resume(tmp_path):
    manifest, _, _, ids = fixture(tmp_path)
    store = CheckpointStore(tmp_path / "new_results", manifest)
    calls = []
    def generate(run_id):
        calls.append(run_id)
        return {"deterministic_value": 7, "scientific_outcome_draws": 0}
    _, first = store.resume_one(ids[0], generate)
    original = store.path(ids[0]).read_bytes()
    _, second = store.resume_one(ids[0], generate)
    assert first and not second and calls == [ids[0]]
    assert store.path(ids[0]).read_bytes() == original
    assert store.remaining_ids() == [ids[1]]
    assert len(list(store.iter_completed())) == 1
    with pytest.raises(FileExistsError):
        store.complete(ids[0], {})


def test_corruption_and_frozen_source_change_refused(tmp_path):
    manifest, source, _, ids = fixture(tmp_path)
    store = CheckpointStore(tmp_path / "new_results", manifest)
    store.complete(ids[0], {"deterministic_value": 7})
    record = json.loads(gzip.decompress(store.path(ids[0]).read_bytes()))
    record["payload"]["result"]["deterministic_value"] = 9
    store.path(ids[0]).write_bytes(gzip.compress(json.dumps(record).encode()))
    with pytest.raises(ValueError, match="corrupt checkpoint"):
        store.load(ids[0])
    source.write_text("changed=True\n")
    with pytest.raises(ValueError, match="source changed"):
        CheckpointStore(tmp_path / "new_results", manifest)


def test_missing_planning_inputs_and_legacy_namespace_cannot_freeze(tmp_path):
    config = dict(namespace=NAMESPACE, legacy_new_outcome_draws=0, primary_units=0,
                  total_unit_cap=1, workers=1, planned_run_ids=[])
    with pytest.raises(FileNotFoundError, match="planning inputs"):
        freeze_protocol(tmp_path / "protocol.json", config, [], tmp_path)
    assert not (tmp_path / "protocol.json").exists()
    config["namespace"] = "gate-c-v1"
    with pytest.raises(ValueError, match="E0 is closed"):
        freeze_protocol(tmp_path / "protocol.json", config, [], tmp_path)


def test_protocol_artifact_not_overwritten_and_ids_enforced(tmp_path):
    manifest, source, inputs, _ = fixture(tmp_path)
    with pytest.raises(FileExistsError):
        freeze_protocol(tmp_path / "protocol.json", manifest["config"], [source], inputs)
    store = CheckpointStore(tmp_path / "new_results", manifest)
    with pytest.raises(ValueError):
        store.load("gate-c-v1/confirmatory/A/0000")
    with pytest.raises(ValueError, match="not in the frozen"):
        store.load(NAMESPACE + "/E1/other/0000")


def test_explicit_missing_blueprint_waiver_is_recorded_without_fabricating_file(tmp_path):
    manifest,_,inputs,_=fixture(tmp_path)
    (inputs/'EXPERIMENT_BLUEPRINT.json').unlink()
    with pytest.raises(FileNotFoundError):
        planning_input_hashes(inputs,allowed_missing=('EXPERIMENT_BLUEPRINT.json',))
    (inputs/'INPUT_RESOLUTION.md').write_text('Explicit current user instruction: proceed without missing blueprint.')
    result=planning_input_hashes(inputs,allowed_missing=('EXPERIMENT_BLUEPRINT.json',))
    assert 'EXPERIMENT_BLUEPRINT.json' not in result
    assert result['explicitly_waived_missing_inputs']==['EXPERIMENT_BLUEPRINT.json']
    assert 'INPUT_RESOLUTION.md' in result

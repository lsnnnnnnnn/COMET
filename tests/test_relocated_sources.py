"""Offline source-content checks only: no draws, SSH, or estimators."""

import hashlib
import json
from pathlib import Path

import pytest

from comet import checkpoint_store as store
from experiments.relocated_sources import relocated_source_checks,main


REMOTE="/data1/shengen/COMET_POST_CSTAT_20261115"


def fixture_manifest(tmp_path):
    local=tmp_path/"local";local.mkdir()
    sources={}
    for relative,content in (("comet/core.py",b"frozen_science = True\n"),("configs/server.json",b'{"environment":"server"}\n')):
        path=local/relative;path.parent.mkdir(exist_ok=True);path.write_bytes(content)
        sources[REMOTE+"/"+relative]=hashlib.sha256(content).hexdigest()
    manifest=dict(schema="post-cstat-protocol-v1",config=dict(namespace=store.NAMESPACE,
        suite="negative_controls",legacy_new_outcome_draws=0,
        planned_run_ids=[store.NAMESPACE+"/negative_controls/wrong_propensity/0000"]),sources=sources)
    manifest["fingerprint"]=store.digest(manifest)
    return manifest,local


def resign(manifest):
    manifest.pop("fingerprint",None);manifest["fingerprint"]=store.digest(manifest)


def test_original_source_checks_pass_with_same_hashes_and_original_keys(tmp_path):
    manifest,local=fixture_manifest(tmp_path);before=store.canonical_bytes(manifest)
    original=store.file_hashes
    with pytest.raises(FileNotFoundError):store.CheckpointStore(tmp_path/"results",manifest)
    with relocated_source_checks(manifest,remote_prefix=REMOTE,local_prefix=local) as receipt:
        assert store.file_hashes(manifest["sources"])==manifest["sources"]
        checked=store.CheckpointStore(tmp_path/"results",manifest)
        assert checked.remaining_ids()==manifest["config"]["planned_run_ids"]
        run_id=manifest["config"]["planned_run_ids"][0]
        payload=checked.complete(run_id,dict(deterministic_fixture=True,new_scientific_units=0))
        checkpoint_before=checked.path(run_id).read_bytes()
        assert checked.load(run_id)==payload and payload["fingerprint"]==manifest["fingerprint"]
        assert not checked.remaining_ids() and checked.path(run_id).read_bytes()==checkpoint_before
        assert receipt["check_sources_skipped"] is False and receipt["source_count"]==2
        path=local/"comet/core.py"
        assert store.file_hashes([path])==original([path])
    assert store.file_hashes is original and store.canonical_bytes(manifest)==before


def test_changed_source_is_rejected_at_entry_and_after_entry_and_restored(tmp_path):
    manifest,local=fixture_manifest(tmp_path);original=store.file_hashes
    with pytest.raises(ValueError,match="source changed"):
        with relocated_source_checks(manifest,remote_prefix=REMOTE,local_prefix=local):
            (local/"comet/core.py").write_text("changed\n")
            store.CheckpointStore(tmp_path/"results",manifest)
    assert store.file_hashes is original
    with pytest.raises(ValueError,match="source differs"):
        with relocated_source_checks(manifest,remote_prefix=REMOTE,local_prefix=local):pass
    assert store.file_hashes is original


@pytest.mark.parametrize("bad",[REMOTE+"/../escape.py",REMOTE+"/comet/./core.py",REMOTE+"//comet/core.py","/another/repo/core.py"])
def test_traversal_or_outside_remote_prefix_is_refused(tmp_path,bad):
    manifest,local=fixture_manifest(tmp_path)
    digest=next(iter(manifest["sources"].values()))
    manifest["sources"]={bad:digest};resign(manifest)
    original=store.file_hashes
    with pytest.raises(ValueError):
        with relocated_source_checks(manifest,remote_prefix=REMOTE,local_prefix=local):pass
    assert store.file_hashes is original


def test_symlink_escape_unknown_remote_file_and_callback_failure_restore(tmp_path):
    manifest,local=fixture_manifest(tmp_path);original=store.file_hashes
    with pytest.raises(RuntimeError,match="explicit failure"):
        with relocated_source_checks(manifest,remote_prefix=REMOTE,local_prefix=local):
            with pytest.raises(ValueError,match="absent"):
                store.file_hashes([REMOTE+"/unknown.py"])
            raise RuntimeError("explicit failure")
    assert store.file_hashes is original
    outside=tmp_path/"outside.py";outside.write_text("external\n")
    (local/"comet/core.py").unlink();(local/"comet/core.py").symlink_to(outside)
    with pytest.raises(ValueError,match="escapes"):
        with relocated_source_checks(manifest,remote_prefix=REMOTE,local_prefix=local):pass
    assert store.file_hashes is original


def test_verify_cli_writes_immutable_receipt_without_changing_protocol(tmp_path):
    manifest,local=fixture_manifest(tmp_path);protocol=tmp_path/"protocol.json"
    before=store.canonical_bytes(manifest)+b"\n";protocol.write_bytes(before)
    receipt=tmp_path/"relocation.json"
    args=["--protocol",str(protocol),"--remote-prefix",REMOTE,"--local-prefix",str(local),"--receipt",str(receipt)]
    main(args)
    record=json.loads(receipt.read_bytes())
    assert record["action"]=="offline_source_verification_only" and record["status"]=="COMPLETE"
    assert record["unchanged_scientific_fingerprint"]==manifest["fingerprint"]
    assert record["execution_environment_adapted"] is False
    assert record["actual_offline_environment"]["python"]
    assert protocol.read_bytes()==before
    with pytest.raises(FileExistsError):main(args)


def test_negative_analysis_uses_original_analyzer_and_keeps_local_analysis_receipt(tmp_path):
    from experiments import negative_controls
    manifest,local=fixture_manifest(tmp_path)
    config_path=Path(negative_controls.REPOSITORY)/"configs/post_cstat/negative_controls_v1.json"
    manifest["config"]=negative_controls._validate_config(json.loads(config_path.read_bytes()))
    resign(manifest)
    protocol=tmp_path/"negative_server_protocol.json"
    before=store.canonical_bytes(manifest)+b"\n";protocol.write_bytes(before)
    output=tmp_path/"analysis";receipt=tmp_path/"analysis_relocation.json"
    main(["--protocol",str(protocol),"--remote-prefix",REMOTE,"--local-prefix",str(local),
        "--receipt",str(receipt),"--analyze-negative","--results",str(tmp_path/"empty_results"),"--output",str(output)])
    analysis=json.loads((output/"manifest.json").read_bytes())
    relocation=json.loads(receipt.read_bytes())
    assert analysis["source_sha256"]==hashlib.sha256(Path(negative_controls.__file__).read_bytes()).hexdigest()
    assert analysis["protocol_fingerprint"]==manifest["fingerprint"]
    assert relocation["analysis_status"]=="NO_COMPLETED_UNITS"
    assert relocation["analysis_manifest_sha256"]==hashlib.sha256((output/"manifest.json").read_bytes()).hexdigest()
    assert protocol.read_bytes()==before

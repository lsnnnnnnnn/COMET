"""Deterministic sharding fixtures, with no production logger or MC."""

import hashlib
import json

import pytest

from comet.checkpoint_store import CheckpointStore,canonical_bytes,digest
from experiments import pipeline_dgp as dgp
from experiments import pipeline_runner as runner
from experiments import pipeline_shard as shard
from test_pipeline_runner import fixture_protocol,resources,CELL
from test_pipeline_fast import explicit_split


def science_bytes(result):
    # Warm-up order changes operational graph-cache counters as well as timing.
    # Dispatch metadata (full grid and evaluated multiplier) stays compared.
    result=dict(result,operational=dict(result["operational"]))
    for key in ("wall_seconds","cpu_seconds"):
        result["operational"].pop(key)
    graph_cache=dict(result["operational"]["source_graph_cache"])
    for key in ("entries","trial_hits","trial_misses","trial_evictions"):
        graph_cache.pop(key)
    result["operational"]["source_graph_cache"]=graph_cache
    return canonical_bytes(result)


@pytest.fixture(autouse=True)
def no_draw(monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError("shard fixtures cannot invoke a production sampler")
    monkeypatch.setattr(runner,"draw_pipeline_split",forbidden)
    monkeypatch.setattr(dgp,"draw_pipeline_split",forbidden)


def test_fixed_full_id_partition_is_disjoint_complete_and_not_remaining_relative():
    ids=[f"comet-post-cstat-v1/E5/{CELL}/{i:04d}" for i in range(7)]
    left=shard.shard_ids(list(reversed(ids)),0)
    right=shard.shard_ids(ids,1)
    assert left==tuple(ids[::2]) and right==tuple(ids[1::2])
    assert not set(left)&set(right) and set(left)|set(right)==set(ids)
    for index,count in ((2,2),(0,1),(True,2)):
        with pytest.raises(ValueError):shard.shard_ids(ids,index,count)


def test_filter_exact_root_and_fingerprint_preserves_full_validation_and_restores(tmp_path):
    protocol,root,manifest,_,ids=fixture_protocol(tmp_path,count=4)
    target=CheckpointStore(root,manifest)
    other=CheckpointStore(root.parent/"another-root",manifest)
    before=canonical_bytes(manifest);original=CheckpointStore.remaining_ids
    with pytest.raises(RuntimeError,match="explicit interruption"):
        with shard.remaining_ids_for_shard(root,manifest["fingerprint"],shard.shard_ids(ids,1)):
            assert target.remaining_ids()==ids[1::2]
            assert other.remaining_ids()==ids
            assert target.planned==frozenset(ids)
            raise RuntimeError("explicit interruption")
    assert CheckpointStore.remaining_ids is original
    assert target.remaining_ids()==ids and canonical_bytes(manifest)==before


def test_both_shards_match_serial_science_and_resume_keeps_existing_bytes(tmp_path):
    protocol,root,manifest,source,ids=fixture_protocol(tmp_path,count=4)
    config=manifest["config"];before=protocol.read_bytes()
    graph,overlap,world=CELL.split("-")
    design=dgp.build_pipeline_design(graph,overlap,world,
        namespace=config["seed_domain"]+"/"+CELL,split_sizes=config["split_sizes"])
    cache=runner.CachedSupportGraph(design.splits["certification"].graph,max_entries=32)
    hashes=dict(config=digest(config),code=digest(manifest["sources"]),
        p2_grid_choice=runner.factorized_p2_grid_choice(config["truncation_multipliers"]))
    serial={run_id:runner._execute_trial(manifest,run_id,design,explicit_split(1),dgp.evaluate_pipeline,
        hashes,graph_cache=cache) for run_id in ids}
    original=CheckpointStore.remaining_ids
    first=shard.run_pipeline_shard(protocol,root,shard_index=0,max_new_units=1,
        draw_callback=explicit_split(1),resource_reader=resources)
    assert first["status"]=="SHARD_CHECKPOINTED_INCOMPLETE" and first["remaining_ids"]==[ids[2]]
    store=CheckpointStore(root,manifest);old_bytes=store.path(ids[0]).read_bytes()
    second=shard.run_pipeline_shard(protocol,root,shard_index=0,draw_callback=explicit_split(1),resource_reader=resources)
    assert second["status"]=="SHARD_COMPLETE" and not second["remaining_ids"]
    snapshot=json.loads(open(second["global_inventory_file"]).read())
    assert snapshot["status"]=="INCOMPLETE" and snapshot["remaining_ids"]==ids[1::2]
    third=shard.run_pipeline_shard(protocol,root,shard_index=1,draw_callback=explicit_split(1),resource_reader=resources)
    assert third["status"]=="SHARD_COMPLETE" and third["completion_scope"]=="SHARD_ONLY"
    inventory=json.loads(open(third["global_inventory_file"]).read())
    assert inventory["status"]=="COMPLETE" and not inventory["remaining_ids"]
    assert len(inventory["completed_checkpoint_filenames"])==4
    assert store.path(ids[0]).read_bytes()==old_bytes and protocol.read_bytes()==before
    assert CheckpointStore.remaining_ids is original
    for run_id in ids:
        result=store.load(run_id)["result"]
        assert science_bytes(result)==science_bytes(serial[run_id])
        assert result["new_scientific_units"]==result["legacy_new_outcome_draws"]==0
    receipts=[json.loads(path.read_text()) for path in (root/"operational_invocations").glob("*.shard-finished.json")]
    assert len(receipts)==3
    assert all(r["unchanged_scientific_fingerprint"]==manifest["fingerprint"] for r in receipts)
    assert all(r["status"].startswith("SHARD_") and r["operational_launcher_sha256"] for r in receipts)
    original_receipts={hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/"invocations").glob("*.json")}
    assert all(r["original_runner_invocation_sha256"] in original_receipts for r in receipts)
    # Startup source validation remains active even when this shard is complete.
    source.write_text("changed scientific fixture source\n")
    with pytest.raises(ValueError,match="source changed"):
        shard.run_pipeline_shard(protocol,root,shard_index=0,draw_callback=explicit_split(1),resource_reader=resources)
    assert CheckpointStore.remaining_ids is original and store.path(ids[0]).read_bytes()==old_bytes

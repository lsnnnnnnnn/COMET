"""Exact scientific-payload equivalence with explicit nonrandom callbacks."""

import hashlib
import json

import numpy as np
import pytest

from comet.checkpoint_store import NAMESPACE, REQUIRED_INPUTS, canonical_bytes, freeze_protocol
from comet.residual_truncation import CertificatePlan
from experiments.core_graph_dgp import evaluate_oracle, generate_from_primitives
from experiments import post_cstat_runner as runner
from experiments.post_cstat_fast import cached_manifest_digests, run_e1_fast


def config_fixture():
    cell="cycle-moderate-bounded"
    ids=[f"{NAMESPACE}/E1/{cell}/{i:04d}" for i in range(12000)]
    config=dict(namespace=NAMESPACE,suite="DETERMINISTIC_RUNNER_FIXTURE",N=8,
        family_size=16,levels=[.05,.1],truncation_multipliers=[.5,1,2],
        normalized_risk_threshold=.4,numerical_guard=1e-10,master_seed=7,
        seed_domain=NAMESPACE+"/deterministic-fast-fixture",raw_debug_run_ids=[ids[0]],
        planned_run_ids=ids,git_sha="DETERMINISTIC_FIXTURE",workers=1,
        legacy_new_outcome_draws=0,primary_units=0,total_unit_cap=32000)
    return config,cell,ids


def explicit_draw(design, seed):
    return generate_from_primitives(design,np.zeros(design.n,dtype=np.uint64),
        {source:1.0 for source in design.outcome_source_ids},seed_namespace="deterministic-fast-fixture")


@pytest.fixture(autouse=True)
def no_random_draw(monkeypatch):
    def forbidden(*args,**kwargs):
        raise AssertionError("fast launcher test invoked a scientific random draw")
    monkeypatch.setattr(runner,"draw_core_log",forbidden)


def test_same_scientific_bytes_and_actual_hash_fidelity_with_12000_id_config(monkeypatch):
    config,cell,ids=config_fixture()
    sources={"actual-frozen-source.py":hashlib.sha256(b"frozen scientific bytes\n").hexdigest()}
    manifest=dict(config=config,sources=sources,fingerprint="deterministic-fingerprint")
    expected_config=hashlib.sha256(canonical_bytes(config)).hexdigest()
    expected_sources=hashlib.sha256(canonical_bytes(sources)).hexdigest()
    config_before=canonical_bytes(config)
    design,plans=runner._build_cell(config,cell)
    original_digest=runner.digest
    digest_calls=[]
    def observed_digest(value):
        digest_calls.append(value)
        return original_digest(value)
    monkeypatch.setattr(runner,"digest",observed_digest)
    old=runner._execute_one(manifest,ids[0],cell,design,plans,explicit_draw,evaluate_oracle)
    old_calls=len(digest_calls)
    digest_calls.clear()
    original_evaluate=CertificatePlan.evaluate
    seen=[]
    def checked_evaluate(self,*args,**kwargs):
        assert kwargs["config_hash"]==expected_config
        assert kwargs["code_hash"]==expected_sources
        seen.append(self.query_id)
        return original_evaluate(self,*args,**kwargs)
    monkeypatch.setattr(CertificatePlan,"evaluate",checked_evaluate)
    with cached_manifest_digests() as stats:
        fast=runner._execute_one(manifest,ids[0],cell,design,plans,explicit_draw,evaluate_oracle)
        runner._execute_one(manifest,ids[1],cell,design,plans,explicit_draw,evaluate_oracle)
    assert len(digest_calls)==2
    assert old_calls==642
    assert len(seen)==640
    assert stats["cached_digest_hits"]==1284
    assert stats["original_metadata_digest_calls"]==2
    for value in (old,fast):
        value.pop("wall_seconds")
        value.pop("cpu_seconds")
    assert canonical_bytes(old)==canonical_bytes(fast)
    assert fast["config_sha256"]==expected_config and fast["code_sha256"]==expected_sources
    assert manifest["config"] is config and manifest["sources"] is sources
    assert canonical_bytes(config)==config_before
    assert runner.digest is observed_digest


def test_strict_identity_and_finally_restoration():
    config,cell,ids=config_fixture()
    manifest=dict(config=config,sources={"s":"abc"},fingerprint="fixture")
    design,plans=runner._build_cell(config,cell)
    original_execute,original_digest=runner._execute_one,runner.digest
    with pytest.raises(ValueError,match="identities"):
        with cached_manifest_digests():
            runner._execute_one(manifest,ids[0],cell,design,plans,explicit_draw,evaluate_oracle)
            equal_but_distinct=dict(manifest,config=dict(config))
            runner._execute_one(equal_but_distinct,ids[0],cell,design,plans,explicit_draw,evaluate_oracle)
    assert runner._execute_one is original_execute and runner.digest is original_digest
    def failed_draw(*args):
        raise RuntimeError("deterministic callback interruption")
    with pytest.raises(RuntimeError,match="interruption"):
        with cached_manifest_digests():
            runner._execute_one(manifest,ids[0],cell,design,plans,failed_draw,evaluate_oracle)
    assert runner._execute_one is original_execute and runner.digest is original_digest


def test_operational_sidecar_and_unchanged_original_resume(tmp_path):
    config,cell,ids=config_fixture()
    config["planned_run_ids"]=ids[:2]
    config["total_unit_cap"]=2
    inputs=tmp_path/"inputs"
    inputs.mkdir()
    for name in REQUIRED_INPUTS:
        (inputs/name).write_text("deterministic fast-launcher fixture")
    source=tmp_path/"source.py"
    source.write_text("unchanged = True\n")
    protocol=tmp_path/"protocol.json"
    manifest=freeze_protocol(protocol,config,[source],inputs)
    before=protocol.read_bytes()
    root=tmp_path/"results"
    resources=lambda _:dict(free_disk_bytes=10*runner.GIB,available_ram_bytes=runner.GIB,
                             worker_rss_bytes=128*2**20)
    result=run_e1_fast(protocol,root,max_new_units=1,draw_callback=explicit_draw,
                       resource_reader=resources)
    assert result["new_completed_units"]==1
    checkpoint=root/"checkpoints"/"E1"/cell/"0000.json.gz"
    checkpoint_before=checkpoint.read_bytes()
    run_e1_fast(protocol,root,max_new_units=0,draw_callback=explicit_draw,resource_reader=resources)
    assert checkpoint.read_bytes()==checkpoint_before and protocol.read_bytes()==before
    records=[json.loads(path.read_text()) for path in (root/"operational_invocations").glob("*.finished.json")]
    assert len(records)==2
    assert all(row["unchanged_scientific_fingerprint"]==manifest["fingerprint"] for row in records)
    assert all(row["operational_launcher_sha256"] for row in records)
    assert all(not row["scientific_parameters_changed"] for row in records)

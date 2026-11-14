"""Tiny explicit-primitive complete trials; no production sampler or MC."""

import json

import numpy as np
import pytest

from comet.checkpoint_store import canonical_bytes
from comet import residual_truncation as theory
from experiments import pipeline_dgp as dgp
from experiments import pipeline_runner as runner
from experiments.pipeline_fast import cached_trial_design_moments,run_pipeline_fast
from test_pipeline_runner import fixture_protocol,resources
from experiments.core_graph_dgp import WORD_GRID


def explicit_split(phase):
    def draw(split,seed):
        index=np.arange(split.n)
        words=np.where((index+phase)%3==0,0,WORD_GRID-1).astype(np.uint64)
        primitives={channel:{source:(-1. if (i+phase+offset)%3 else 1.)
            for i,source in enumerate(split.channel_source_ids[channel])}
            for offset,channel in enumerate(("risk","utility"))}
        return dgp.generate_pipeline_from_primitives(split,words,primitives,
            seed_namespace=f"explicit-fast-pipeline/{phase}/{split.name}")
    return draw


@pytest.fixture(autouse=True)
def forbid_sampler(monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError("operational tests cannot invoke a production sampler")
    monkeypatch.setattr(runner,"draw_pipeline_split",forbidden)
    monkeypatch.setattr(dgp,"draw_pipeline_split",forbidden)


def science_bytes(result):
    result=dict(result,operational=dict(result["operational"]))
    result["operational"].pop("wall_seconds")
    result["operational"].pop("cpu_seconds")
    return canonical_bytes(result)


@pytest.mark.parametrize("cell,phase",[("independent-moderate-null",0),
    ("cycle-weak-mixed",1),("cycle-moderate-mixed",2)])
def test_complete_payload_bytes_and_real_source_calls_match(tmp_path,monkeypatch,cell,phase):
    protocol,_,manifest,_,_=fixture_protocol(tmp_path)
    config=dict(manifest["config"])
    config["truncation_multipliers"]=[2**(j/4) for j in range(-24,25)]
    manifest=dict(manifest,config=config)
    run_id=f"comet-post-cstat-v1/E5/{cell}/0000"
    config["raw_debug_run_ids"]=[run_id]
    graph,overlap,world=cell.split("-")
    design=dgp.build_pipeline_design(graph,overlap,world,namespace="explicit-fast/"+cell,
        split_sizes=config["split_sizes"])
    hashes=dict(code="unchanged-frozen-code-hash",config="unchanged-frozen-config-hash",
        p2_grid_choice=runner.factorized_p2_grid_choice(config["truncation_multipliers"]))
    calls={"inputs":0,"bounded":0,"envelope":0}
    original_inputs=dgp.FrozenPipeline.certifier_inputs
    original_bounded=theory.bounded_residual_moments
    original_envelope=theory.residual_moment_envelope
    def inputs(*args,**kwargs):calls["inputs"]+=1;return original_inputs(*args,**kwargs)
    def bounded(*args,**kwargs):calls["bounded"]+=1;return original_bounded(*args,**kwargs)
    def envelope(*args,**kwargs):calls["envelope"]+=1;return original_envelope(*args,**kwargs)
    monkeypatch.setattr(dgp.FrozenPipeline,"certifier_inputs",inputs)
    monkeypatch.setattr(theory,"bounded_residual_moments",bounded)
    monkeypatch.setattr(theory,"residual_moment_envelope",envelope)
    before=canonical_bytes(config)
    old=runner._execute_trial(manifest,run_id,design,explicit_split(phase),dgp.evaluate_pipeline,hashes)
    original_calls=dict(calls)
    for key in calls:calls[key]=0
    with cached_trial_design_moments() as stats:
        fast=runner._execute_trial(manifest,run_id,design,explicit_split(phase),dgp.evaluate_pipeline,hashes)
    assert science_bytes(old)==science_bytes(fast)
    assert canonical_bytes(config)==before
    assert fast["source_split_digests"]==old["source_split_digests"]
    assert fast["new_scientific_units"]==fast["legacy_new_outcome_draws"]==0
    assert original_calls["inputs"]==12 and calls["inputs"]==4
    assert calls["bounded"]==2 and original_calls["bounded"]>calls["bounded"]*20
    assert original_calls["envelope"]>calls["envelope"]*2
    assert stats["envelope_hits"]>0 and stats["bounded_moment_hits"]>0
    assert dgp.FrozenPipeline.certifier_inputs is inputs
    assert theory.residual_moment_envelope is envelope
    assert theory.bounded_residual_moments is bounded


def test_every_wrapper_is_restored_after_callback_failure(tmp_path):
    _,_,manifest,_,ids=fixture_protocol(tmp_path)
    design=dgp.build_pipeline_design("cycle","moderate","mixed",namespace="explicit-failure",
        split_sizes=manifest["config"]["split_sizes"])
    originals=(runner._execute_trial,dgp.FrozenPipeline.certifier_inputs,
        theory.bounded_residual_moments,theory.residual_moment_envelope)
    def failed(*args):raise RuntimeError("explicit callback failure")
    with pytest.raises(RuntimeError,match="callback failure"):
        with cached_trial_design_moments():
            runner._execute_trial(manifest,ids[0],design,failed,dgp.evaluate_pipeline,{"code":"c","config":"d"})
    assert (runner._execute_trial,dgp.FrozenPipeline.certifier_inputs,
        theory.bounded_residual_moments,theory.residual_moment_envelope)==originals


def test_sidecar_resume_preserves_frozen_protocol_and_completed_checkpoint(tmp_path):
    protocol,root,manifest,_,ids=fixture_protocol(tmp_path)
    before=protocol.read_bytes()
    first=run_pipeline_fast(protocol,root,max_new_units=1,draw_callback=explicit_split(1),resource_reader=resources)
    assert first["new_completed_units"]==1
    from comet.checkpoint_store import CheckpointStore
    store=CheckpointStore(root,manifest);checkpoint=store.path(ids[0]).read_bytes()
    again=run_pipeline_fast(protocol,root,max_new_units=0,draw_callback=explicit_split(2),resource_reader=resources)
    assert again["new_completed_units"]==0
    assert protocol.read_bytes()==before and store.path(ids[0]).read_bytes()==checkpoint
    records=[json.loads(p.read_text()) for p in (root/"operational_invocations").glob("*.finished.json")]
    assert len(records)==2
    assert all(r["unchanged_scientific_fingerprint"]==manifest["fingerprint"] for r in records)
    assert all(r["operational_launcher_sha256"] and not r["scientific_parameters_changed"] for r in records)

"""Supplemental anchor fixtures use explicit words/signs, never a sampler."""

import json
import math

import numpy as np
import pytest

from comet.checkpoint_store import CheckpointStore,NAMESPACE,REQUIRED_INPUTS,freeze_protocol
from comet.residual_truncation import CertificatePlan
from experiments.core_graph_dgp import WORD_GRID
import experiments.anchor_runner as runner


def config_fixture(cell="iid-bounded",reps=2):
    ids=[f"{NAMESPACE}/ANCHORS/{cell}/{rep:04d}" for rep in range(reps)]
    config=dict(namespace=NAMESPACE,suite="DETERMINISTIC_ANCHOR_FIXTURE",workers=1,
        levels=[.05,.1],fixture_N=512,legacy_new_outcome_draws=0,primary_units=0,total_unit_cap=32000,
        planned_run_ids=ids,seed_domain=NAMESPACE+"/ANCHORS/deterministic-fixture",master_seed=7,
        truncation_multipliers=[.5,1,2],normalized_risk_threshold=.4,numerical_guard=1e-10,
        catoni_tau=.5,catoni_h=.9,ope2024_k=.5,ope2024_rho=1.,raw_debug_run_ids=[ids[0]],
        analysis_bootstrap_seed=7,analysis_bootstrap_resamples=0,
        primary_comparisons=[[cell,m] for m in runner.METHODS if runner.anchor_eligible(cell,m)])
    return config,ids


def explicit_draw(cell,seed):
    words=np.where(np.arange(cell.n)%2==0,WORD_GRID-1,0).astype(np.uint64)
    primitives={source:(-1. if index%2==0 else 1.) for index,source in enumerate(cell.core.outcome_source_ids)}
    return runner.anchor_from_primitives(cell,words,primitives)


def freeze_fixture(tmp_path,cell="iid-bounded"):
    config,ids=config_fixture(cell)
    inputs=tmp_path/"inputs";inputs.mkdir()
    for name in REQUIRED_INPUTS:(inputs/name).write_text("deterministic anchor fixture")
    source=tmp_path/"source.py";source.write_text("fixture = True\n")
    protocol=tmp_path/"protocol.json"
    manifest=freeze_protocol(protocol,config,[source],inputs)
    root=tmp_path/"all-results/ANCHORS"
    return protocol,root,manifest,ids,source


def resources(_):
    return dict(free_disk_bytes=10*runner.GIB,available_ram_bytes=runner.GIB,worker_rss_bytes=128*2**20)


@pytest.fixture(autouse=True)
def forbid_production_draw(monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError("anchor unit test invoked a production sampler")
    monkeypatch.setattr(runner,"draw_anchor_log",forbidden)
    monkeypatch.setattr(runner,"draw_core_log",forbidden)


def test_exact_combined_budget_and_frozen_applicability():
    ids=runner.planned_anchor_ids()
    assert len(ids)==len(set(ids))==1600
    assert len(runner.anchor_cells())==8
    assert len(runner.primary_anchor_comparisons())==68
    assert runner.anchor_eligible("iid-heavy",runner.CATONI)
    assert not runner.anchor_eligible("iid-heavy",runner.OPE24)
    assert not runner.anchor_eligible("scaling-N8192-bounded",runner.CATONI)


@pytest.mark.parametrize("outcome",["bounded","heavy"])
def test_genuine_iid_scalar_fixture_and_same_legal_information(outcome):
    config,_=config_fixture("iid-"+outcome)
    cell,plans=runner.build_anchor_plans(config,"iid-"+outcome)
    assert cell.iid and len(cell.core.queries)==1 and cell.core.graph.color_count==1
    assert np.all(cell.core.exposure==.5) and np.all(cell.core.queries[0].coefficients==.5)
    assert np.all(cell.core.nuisance==.5)
    log=explicit_draw(cell,0)
    assert np.mean(log.outcomes)==pytest.approx(.45)
    assert runner.anchor_truths(cell)=={"anchor/all":.45}
    bound=.25 if outcome=="bounded" else (.5+.1*7**(1/1.5))**1.5
    assert cell.centered_moment_bound==pytest.approx(bound)
    assert np.all(cell.core.residual_moments==bound)
    if outcome=="bounded":
        expected=math.sqrt(math.log(40)/(2*cell.n))
        assert plans[.05,"graph_hoeffding"][0].radius==pytest.approx(expected)
        assert np.allclose(log.outcomes,np.where(log.actions==1,.55,.35)+np.where(log.actions==1,.1,-.1))


def test_scaling_anchors_use_fixed_nested_auditors_and_no_iid_baseline_port():
    config,_=config_fixture()
    cell,_=runner.build_anchor_plans(config,"scaling-N131072-heavy")
    assert not cell.iid and len(cell.core.queries)==16
    for policy in range(4):
        for auditor,fraction in enumerate((1.,.5,.1,.02)):
            query=cell.core.queries[4*policy+auditor]
            assert query.n_rows==512
            assert query.active_mask.sum()==max(1,round(512*fraction))
    assert not runner.anchor_eligible(cell.cell_id,runner.OPE21)
    assert not runner.anchor_eligible(cell.cell_id,runner.OPE24)


def test_anchor_adapter_preserves_each_source_engine_endpoints_and_budget():
    config,_=config_fixture()
    cell,_=runner.build_anchor_plans(config,"iid-bounded")
    log=explicit_draw(cell,0)
    source_records={
        runner.CATONI:runner.catoni_iid(log.outcomes,p=2.,central_moment_bound=.25,
            delta=.05,tau=.5,h=.9,iid_declared=True),
        runner.OPE21:runner.ope_betting_iid(np.ones(cell.n),log.outcomes,wmax=1.,
            delta=.05,iid_declared=True),
        runner.OPE24:runner.ope_eb_independent(log.actions,log.outcomes,
            exposure=cell.core.exposure,target_policy=cell.core.queries[0].coefficients,
            nuisance=cell.core.nuisance,delta=.05,k=.5,rho=1.,
            independent_rows_declared=True,independent_nuisance_declared=True)}
    for method,source in source_records.items():
        adapted=runner._baseline_record(method,cell,log,.05,config)
        assert adapted["nominal_delta"]==adapted["coordinate_delta"]==.05
        assert adapted["family_size"]==1
        assert adapted["estimate"]==source["estimate"]
        guard=adapted["numerical_guard"]
        assert adapted["raw_lo"]==source.get("raw_lo",source["lo"])-guard
        assert adapted["raw_hi"]==source.get("raw_hi",source["hi"])+guard
        json.dumps(adapted,allow_nan=False)


def test_actual_runner_orders_oracle_after_every_engine_and_preserves_resume(tmp_path,monkeypatch):
    protocol,root,manifest,ids,_=freeze_fixture(tmp_path)
    calls=[];original=CertificatePlan.evaluate
    def evaluated(self,*args,**kwargs):calls.append(self.method);return original(self,*args,**kwargs)
    monkeypatch.setattr(CertificatePlan,"evaluate",evaluated)
    for name in ("catoni_iid","ope_betting_iid","ope_eb_independent"):
        function=getattr(runner,name)
        def observed(*args,_function=function,_name=name,**kwargs):
            calls.append(_name);return _function(*args,**kwargs)
        monkeypatch.setattr(runner,name,observed)
    def oracle(cell):
        assert len(calls)==26
        return runner.anchor_truths(cell)
    result=runner.run_anchors(protocol,root,global_results_root=root.parent,max_new_units=1,
        draw_callback=explicit_draw,oracle_callback=oracle,resource_reader=resources,progress=False)
    assert result["new_completed_units"]==1 and result["remaining_ids"]==[ids[1]]
    store=CheckpointStore(root,manifest);before=store.path(ids[0]).read_bytes()
    payload=store.load(ids[0])["result"]
    assert payload["new_scientific_units"]==payload["legacy_new_outcome_draws"]==0
    assert len(payload["trials"])==26
    runner.run_anchors(protocol,root,global_results_root=root.parent,max_new_units=0,
        draw_callback=explicit_draw,resource_reader=resources,progress=False)
    assert store.path(ids[0]).read_bytes()==before


def test_heavy_na_methods_remain_explicit_and_analysis_never_counts_them_as_zero_error(tmp_path):
    protocol,root,manifest,ids,_=freeze_fixture(tmp_path,"iid-heavy")
    runner.run_anchors(protocol,root,global_results_root=root.parent,max_new_units=1,
        draw_callback=explicit_draw,resource_reader=resources,progress=False)
    payload=CheckpointStore(root,manifest).load(ids[0])["result"]
    na=[t for t in payload["trials"] if t["method"]==runner.OPE24]
    assert len(na)==2 and all(t["coverage_applicable"] is False for t in na)
    summary=runner.analyze_anchors(protocol,root,root.parent/"analysis",bootstrap_resamples=0)
    assert summary["reported_new_scientific_units"]==0
    rows=[r for r in summary["summaries"] if r["method"]==runner.OPE24]
    assert all(r["family_coverage"] is None for r in rows)
    assert all(r["endpoints"]["any_false_claim"]["rate"] is None for r in rows)
    assert all(r["endpoints"]["any_false_claim"]["applicable"] is False for r in rows)


def test_failed_whole_log_keeps_all_eligible_denominators(tmp_path):
    protocol,root,manifest,ids,_=freeze_fixture(tmp_path,"iid-heavy")
    store=CheckpointStore(root,manifest)
    store.complete(ids[0],dict(suite="ANCHORS",cell="iid-heavy",status="UNIT_FAILURE",trials=[],
        unassessable_whole_trial=True,legacy_new_outcome_draws=0,new_scientific_units=0))
    summary=runner.analyze_anchors(protocol,root,root.parent/"analysis",bootstrap_resamples=0)
    for row in summary["summaries"]:
        if runner.anchor_eligible(row["cell"],row["method"]):
            assert row["family_coverage"]["denominator"]==1 and row["family_coverage"]["hits"]==0
            assert row["endpoints"]["any_false_claim"]["unknown_trials"]==1
            assert row["endpoints"]["any_false_claim"]["wilson95"] is None


def test_global_budget_stops_before_draw_and_no_unattended_claim(tmp_path):
    protocol,root,manifest,ids,_=freeze_fixture(tmp_path)
    # Two preexisting checkpoint path fixtures from another suite consume the cap.
    manifest["config"]["total_unit_cap"]=2
    manifest.pop("fingerprint")
    from comet.checkpoint_store import digest,canonical_bytes
    manifest["fingerprint"]=digest(manifest)
    protocol.write_bytes(canonical_bytes(manifest)+b"\n")
    other=root.parent/"E1/checkpoints"
    other.mkdir(parents=True)
    for i in range(2):(other/f"fixture{i}.json.gz").write_bytes(b"budget path fixture")
    calls=[]
    def draw(*args):calls.append(True);return explicit_draw(*args)
    result=runner.run_anchors(protocol,root,global_results_root=root.parent,draw_callback=draw,
        resource_reader=resources,progress=False)
    assert result["status"]=="RESOURCE_CHECKPOINTED" and not calls
    assert result["new_completed_units"]==0 and not result["background_work_running"]

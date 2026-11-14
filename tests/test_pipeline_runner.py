"""Tiny explicit-primitive E5 callbacks: zero stochastic scientific units."""

import json

import numpy as np
import pytest

from comet.checkpoint_store import CheckpointStore, NAMESPACE, REQUIRED_INPUTS, freeze_protocol
from comet.queries import SignedQuery
from comet.residual_truncation import AssumptionContract, make_plan
from comet.source_graph import SourceGraph
from experiments.core_graph_dgp import WORD_GRID
from experiments.pipeline_dgp import generate_pipeline_from_primitives, evaluate_pipeline
import experiments.pipeline_runner as runner


CELL = "cycle-moderate-mixed"


def resources(_):
    return dict(free_disk_bytes=10 * runner.GIB, available_ram_bytes=runner.GIB,
                worker_rss_bytes=128 * 2**20)


def fixture_protocol(tmp_path, count=2):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    for name in REQUIRED_INPUTS:
        (inputs / name).write_text("DETERMINISTIC PIPELINE TEST FIXTURE ONLY: " + name)
    source = tmp_path / "fixture_source.py"
    source.write_text("fixture = True\n")
    ids = [f"{NAMESPACE}/E5/{CELL}/{index:04d}" for index in range(count)]
    global_root = tmp_path / "results"
    config = dict(namespace=NAMESPACE, suite="DETERMINISTIC_PIPELINE_FIXTURE", workers=1,
        legacy_new_outcome_draws=0, primary_units=0, total_unit_cap=count,
        planned_run_ids=ids, cells=[CELL], split_sizes={"training":128,"discovery":128,"certification":128},
        levels=[.05,.1], arms=list(runner.ARMS), primary_comparisons=[[CELL,arm] for arm in runner.CERTIFIED_ARMS],
        risk_threshold=.32, utility_margin=.01, service_floor=.2, capacity_ceiling=.6,
        max_rules=4, max_depth=4, minimum_mass=.02, ridge=1.0, tradeoff_grid=[0,.25,.5,1,2,4,8],
        truncation_multipliers=[.5,1,2], numerical_guard=1e-10,
        master_seed=7, seed_domain=NAMESPACE+"/E5-deterministic-fixture",
        analysis_bootstrap_seed=11, analysis_bootstrap_resamples=0,
        raw_debug_run_ids=[ids[0]] if ids else [], global_results_root=str(global_root),
        git_sha="DETERMINISTIC_FIXTURE_NOT_SCIENCE")
    path = tmp_path / "protocol.json"
    manifest = freeze_protocol(path, config, [source], inputs)
    return path, global_root/"E5", manifest, source, ids


def explicit_split(split, seed):
    words = np.where(np.arange(split.n)%2 == 0, 0, WORD_GRID-1).astype(np.uint64)
    primitives = {channel:{source:(-1.0 if (index+offset)%2 else 1.0)
                          for index,source in enumerate(split.channel_source_ids[channel])}
                  for offset,channel in enumerate(("risk","utility"))}
    return generate_pipeline_from_primitives(split, words, primitives,
        seed_namespace="deterministic-fixture/"+split.name)


@pytest.fixture(autouse=True)
def no_scientific_draw(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("deterministic tests must not call draw_pipeline_split")
    monkeypatch.setattr(runner, "draw_pipeline_split", forbidden)


def test_eight_cells_4000_trials_and_actual_family_rule():
    assert len(runner.pipeline_cell_ids()) == 8
    assert len(set(runner.planned_pipeline_ids())) == 4000
    assert len(runner.primary_pipeline_comparisons()) == 32
    config = dict(master_seed=1, seed_domain=NAMESPACE+"/E5-v1",
        truncation_multipliers=[2**(j/4) for j in range(-24,25)], truncation_grid_source="THEORY_NOTE.md",
        planning_inputs_reconciled=True, theorem_status="PROVED_UNDER_DECLARED_ASSUMPTIONS",
        numerical_guard=1e-10, raw_debug_run_ids=[], analysis_bootstrap_seed=2, analysis_bootstrap_resamples=2000)
    frozen = runner._validate_config(config)
    assert frozen["primary_units"] == 4000
    assert frozen["split_sizes"] == {"training":4096,"discovery":8192,"certification":32768}
    assert frozen["risk_threshold"] == .32 and frozen["utility_margin"] == .01
    assert "actual deduplicated" in frozen["family_size_rule"]
    with pytest.raises(ValueError, match="fixed E5 design"):
        runner._validate_config(dict(config, risk_threshold=.4))


def test_complete_trial_uses_three_logs_for_all_arms_levels_and_oracle_follows_selection(tmp_path, monkeypatch):
    protocol, root, manifest, _, ids = fixture_protocol(tmp_path)
    draws, cert_calls = [], []
    original = runner._certify
    def observed_certify(*args, **kwargs):
        assert not any(query.provenance.startswith("HEURISTIC") for query in args[0].family.queries)
        cert_calls.append(args[3])
        return original(*args, **kwargs)
    monkeypatch.setattr(runner,"_certify",observed_certify)
    def draw(split,seed):
        draws.append(split.name)
        return explicit_split(split,seed)
    def oracle(*args, **kwargs):
        assert draws == ["training","discovery","certification"]
        assert len(cert_calls) == 6  # matched engine reused algebraically
        return evaluate_pipeline(*args, **kwargs)
    result = runner.run_pipeline(protocol,root,max_new_units=1,draw_callback=draw,
        oracle_callback=oracle,resource_reader=resources)
    assert result["new_completed_units"] == 1 and result["remaining_ids"] == [ids[1]]
    payload = CheckpointStore(root,manifest).load(ids[0])["result"]
    assert payload["legacy_new_outcome_draws"] == payload["new_scientific_units"] == 0
    assert len(payload["trials"]) == len(payload["certificate_records"]) == 16
    assert payload["proper_family"]["actual_family_size"] > 16
    assert payload["proper_family"]["utility_coordinate_count"] == 7
    assert payload["graph_cache_entries"] < 20
    frames = {(frame["method"],frame["delta"]):frame for frame in payload["certificate_records"]}
    for delta in (.05,.1):
        assert frames[("comet_local",delta)]["certificates"] == frames[("generic_matched",delta)]["certificates"]
        assert not frames[("status_quo_reference",delta)]["selection"]["safety_claim_certified"]
        for arm in ("point_constraint","in_sample_auditing"):
            assert "HEURISTIC" in frames[(arm,delta)]["selection"]["status"]
        abstain = next(row for row in payload["trials"] if row["method"]=="abstain_reference" and row["delta"]==delta)
        assert not abstain["returned"] and not abstain["return_safe_useful"]
    assert payload["raw_debug_reason"] in ("prespecified_run_ID","failure")
    before = CheckpointStore(root,manifest).path(ids[0]).read_bytes()
    repeated = runner.run_pipeline(protocol,root,max_new_units=0,draw_callback=draw,resource_reader=resources)
    assert repeated["new_completed_units"] == 0 and len(draws) == 3
    assert CheckpointStore(root,manifest).path(ids[0]).read_bytes() == before


def test_support_cache_is_scalar_plan_equivalent_and_preserves_validation():
    n=8
    graph=SourceGraph.from_sources([{("e",i),("e",(i+1)%n)} for i in range(n)])
    cached=runner.CachedSupportGraph(graph)
    mask=np.array([True,True,False,True,False,True,False,True])
    assert cached.induced(mask) is cached.induced(mask)
    assert cached.induced(mask).adjacency == graph.induced(mask).adjacency
    with pytest.raises(ValueError,match="boolean"):
        cached.induced(np.arange(n))
    query=SignedQuery("risk",np.column_stack((np.zeros(n),mask*.4)),0)
    contract=AssumptionContract(True,True,True,True,True,True,True,"source graph","bounded residual","fixed design")
    args=(query,np.full((n,2),.5),np.full((n,2),.5),np.full((n,2),.25))
    kwargs=dict(p=2,delta=.05,family_size=1,multipliers=(.5,1,2),method="comet_local",outcome_bounds=(0,1))
    first=make_plan(*args,graph,contract,**kwargs)
    second=make_plan(*args,cached,contract,**kwargs)
    assert first.radius == second.radius
    assert np.array_equal(first.weights,second.weights)
    assert first.selected_method == second.selected_method


def test_oracle_failure_retains_all_observed_split_data_and_analysis_unknown_denominators(tmp_path):
    protocol,root,manifest,_,ids=fixture_protocol(tmp_path)
    def fail(*args,**kwargs):
        raise ValueError("injected deterministic oracle failure")
    result=runner.run_pipeline(protocol,root,draw_callback=explicit_split,oracle_callback=fail,resource_reader=resources)
    assert result["status"] == "ERROR_CHECKPOINTED" and result["new_completed_units"] == 1
    payload=CheckpointStore(root,manifest).load(ids[0])["result"]
    assert payload["unassessable_whole_trial"] and payload["full_family_failure"]
    assert set(payload["raw_debug"]) == {"training","discovery","certification"}
    summary=runner.analyze_pipeline(protocol,root,tmp_path/"analysis",bootstrap_resamples=0)
    assert summary["completed_units"] == summary["failed_units"] == summary["unassessable_units"] == 1
    assert len(summary["summaries"]) == 16
    for row in summary["summaries"]:
        if row["method"] in runner.CERTIFIED_ARMS:
            assert row["family_coverage"]["denominator"] == 1
            assert row["family_coverage"]["hits"] == 0
        assert row["endpoints"]["return_unsafe"]["unknown_trials"] == 1
        assert row["endpoints"]["return_unsafe"]["rate"] is None
    assert all(row["status"] == "UNASSESSABLE_FULL_PAIRING" for row in summary["paired_safe_useful_differences"])


def test_numerical_coordinate_failure_cannot_drop_complete_trial(tmp_path,monkeypatch):
    protocol,root,manifest,_,ids=fixture_protocol(tmp_path,count=1)
    original=runner.make_plan
    def fail(query,*args,**kwargs):
        if query.query_id == "risk/policy0/all":
            raise ValueError("injected numerical fixture")
        return original(query,*args,**kwargs)
    monkeypatch.setattr(runner,"make_plan",fail)
    result=runner.run_pipeline(protocol,root,draw_callback=explicit_split,resource_reader=resources)
    assert result["new_completed_units"] == result["failed_units"] == 1
    payload=CheckpointStore(root,manifest).load(ids[0])["result"]
    assert len(payload["trials"]) == 16
    for row in payload["trials"]:
        if row["method"] in runner.CERTIFIED_ARMS:
            assert row["coverage_applicable"] and not row["family_covered"]
    summary=runner.analyze_pipeline(protocol,root,tmp_path/"analysis",bootstrap_resamples=0)
    assert summary["completed_units"] == 1
    assert all(row["independent_trials"] == 1 for row in summary["summaries"])
    with pytest.raises(FileExistsError):
        runner.analyze_pipeline(protocol,root,tmp_path/"analysis",bootstrap_resamples=0)


def test_source_change_and_global_trial_cap_refuse_new_draws(tmp_path):
    protocol,root,manifest,source,ids=fixture_protocol(tmp_path)
    other=root.parent/"other/checkpoints/E4/othercell"
    other.mkdir(parents=True)
    (other/"0000.json.gz").write_bytes(b"deterministic budget-count fixture")
    calls=[]
    def draw(split,seed):
        calls.append(split.name)
        return explicit_split(split,seed)
    result=runner.run_pipeline(protocol,root,draw_callback=draw,resource_reader=resources)
    assert result["status"] == "RESOURCE_CHECKPOINTED" and result["new_completed_units"] == 1
    assert calls == ["training","discovery","certification"]
    assert result["remaining_ids"] == [ids[1]]
    source.write_text("changed=True\n")
    with pytest.raises(ValueError,match="source changed"):
        runner.run_pipeline(protocol,root,draw_callback=draw,resource_reader=resources)
    assert len(calls) == 3

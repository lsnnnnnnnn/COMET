"""Handwritten immutable whole-log fixtures; no scientific sampler is called."""

import json

import pytest

from comet.checkpoint_store import CheckpointStore, NAMESPACE, REQUIRED_INPUTS, freeze_protocol
from comet.post_cstat_statistics import EVENTS
from experiments.extension_analyze import EXTRA_EVENTS, _registered_family, analyze_extension
from experiments.extension_runner import primary_extension_comparisons, suite_cells


def fixture(tmp_path, suite="E4", reps=3):
    directory=tmp_path/"inputs"
    directory.mkdir()
    for name in REQUIRED_INPUTS:
        (directory/name).write_text("deterministic analysis fixture")
    source=tmp_path/"fixture_source.py"
    source.write_text("fixture = True\n")
    cell=suite_cells(suite)[0]
    ids=[f"{NAMESPACE}/{suite}/{cell}/{index:04d}" for index in range(reps)]
    config=dict(namespace=NAMESPACE,suite="DETERMINISTIC_EXTENSION_FIXTURE",target_suite=suite,
        workers=1,legacy_new_outcome_draws=0,primary_units=0,total_unit_cap=32000,
        planned_run_ids=ids,levels=[.05,.1],analysis_bootstrap_seed=7,
        analysis_bootstrap_resamples=0,primary_comparisons=[[cell,"comet_local"],[cell,"generic_matched"]])
    protocol=tmp_path/"protocol.json"
    manifest=freeze_protocol(protocol,config,[source],directory)
    root=tmp_path/"results"
    return protocol,root,CheckpointStore(root,manifest),ids,cell


def frames(run_id,cell,suite):
    result=[]
    for method in ("comet_local","generic_matched"):
        for delta in (.05,.1):
            row=dict(run_id=run_id,cell=cell,method=method,delta=delta,coverage_applicable=True,
                family_covered=True,metrics_assessable=True,mean_coordinate_width=.2,
                failure_status=None,**{event:False for event in EVENTS})
            row.update({event:False for event in EXTRA_EVENTS.get(suite,())})
            if suite=="E4": row["primary_certified_safe"]=True
            result.append(row)
    return result


def complete(store,run_id,cell,suite,records,**updates):
    result=dict(suite=suite,cell=cell,status="COMPLETE",legacy_new_outcome_draws=0,
                new_scientific_units=0,trials=records)
    result.update(updates)
    store.complete(run_id,result)


def test_whole_failure_expands_every_frame_and_keeps_unknown_error_rates(tmp_path):
    protocol,root,store,ids,cell=fixture(tmp_path)
    complete(store,ids[0],cell,"E4",frames(ids[0],cell,"E4"))
    complete(store,ids[1],cell,"E4",[],status="UNIT_FAILURE",unassessable_whole_trial=True)
    summary=analyze_extension(protocol,root,tmp_path/"analysis",bootstrap_resamples=0)
    assert summary["status"]=="PARTIAL" and summary["completed_units"]==2
    assert summary["primary_comparison_count"]==2
    assert summary["unknown_method_level_records"]==4
    assert summary["reported_new_scientific_units"]==0
    for row in summary["summaries"]:
        assert row["family_coverage"]["hits"]==1 and row["family_coverage"]["denominator"]==2
        event=row["endpoints"]["any_false_claim"]
        assert event["unknown_trials"]==1 and event["rate"] is None and event["wilson95"] is None
        assert event["realized_frequency_bounds"]==[0,.5]
        assert row["endpoints"]["returned"]["applicable"] is False
        safe=row["extension_endpoints"]["primary_certified_safe"]
        assert safe["hits"]==1 and safe["unknown_trials"]==1 and safe["rate"] is None
    assert all(row["status"]=="UNASSESSABLE_COMPLETE_PAIR_SET" for row in summary["paired_width_differences"])
    assert set(summary["remaining_ids"])=={ids[2]}


def test_missing_frame_and_missing_extra_metric_remain_unknown(tmp_path):
    protocol,root,store,ids,cell=fixture(tmp_path,"E3",1)
    records=frames(ids[0],cell,"E3")
    records.pop()
    records[0].pop("contrast_false_improvement")
    complete(store,ids[0],cell,"E3",records)
    summary=analyze_extension(protocol,root,tmp_path/"analysis",bootstrap_resamples=0)
    assert summary["unknown_method_level_records"]==1
    row=next(row for row in summary["summaries"] if row["method"]=="comet_local" and row["delta"]==.05)
    assert row["extension_endpoints"]["contrast_false_improvement"]["unknown_trials"]==1
    assert row["extension_endpoints"]["contrast_false_improvement"]["wilson95"] is None
    assert row["extension_endpoints"]["primary_false_safe"]["applicable"] is False


@pytest.mark.parametrize("bad",["duplicate","unknown_method","wrong_id"])
def test_bad_frame_identity_refuses_without_outputs(tmp_path,bad):
    protocol,root,store,ids,cell=fixture(tmp_path,reps=1)
    records=frames(ids[0],cell,"E4")
    if bad=="duplicate": records.append(dict(records[0]))
    elif bad=="unknown_method": records[0]["method"]="invented"
    else: records[0]["run_id"]=ids[0]+"-wrong"
    complete(store,ids[0],cell,"E4",records)
    output=tmp_path/"analysis"
    with pytest.raises(ValueError): analyze_extension(protocol,root,output,bootstrap_resamples=0)
    assert not output.exists()


def test_complete_paired_widths_descriptive_and_irrelevant_endpoints_na(tmp_path):
    protocol,root,store,ids,cell=fixture(tmp_path,"E2",2)
    for run_id in ids: complete(store,run_id,cell,"E2",frames(run_id,cell,"E2"))
    summary=analyze_extension(protocol,root,tmp_path/"analysis",bootstrap_resamples=0)
    assert summary["status"]=="COMPLETE"
    assert len(summary["paired_width_differences"])==2
    for row in summary["paired_width_differences"]:
        assert row["mean_difference"]==0 and row["bootstrap_pointwise95"] is None
        assert row["status"]=="DESCRIPTIVE_BOOTSTRAP_DISABLED"
    for row in summary["summaries"]:
        assert all(not event["applicable"] for event in row["extension_endpoints"].values())
    csv=(tmp_path/"analysis/summary.csv").read_text()
    assert "primary_false_violation_unknown_trials" in csv


def test_complete_pair_bootstrap_is_reproducible_performance_resampling(tmp_path):
    protocol,root,store,ids,cell=fixture(tmp_path,"E2",2)
    for run_id in ids: complete(store,run_id,cell,"E2",frames(run_id,cell,"E2"))
    # Resample handwritten performance summaries, not scientific logs/outcomes.
    a=analyze_extension(protocol,root,tmp_path/"analysis_a",bootstrap_resamples=20)
    b=analyze_extension(protocol,root,tmp_path/"analysis_b",bootstrap_resamples=20)
    assert a["paired_width_differences"]==b["paired_width_differences"]
    for row in a["paired_width_differences"]:
        assert row["status"]=="PAIRED_POINTWISE_BOOTSTRAP"
        assert row["bootstrap_pointwise95"]==[0,0]
        assert row["independent_pairs"]==2


@pytest.mark.parametrize("suite,count",[("E2",60),("E3",108),("E4",192)])
def test_production_family_is_complete_and_isolated(suite,count):
    config=dict(suite=suite,levels=[.05,.1],primary_comparisons=primary_extension_comparisons(suite),
                analysis_bootstrap_seed=7,analysis_bootstrap_resamples=2000)
    _,fixture_flag,registered,_,_=_registered_family(config)
    assert not fixture_flag and len(registered)==count
    config["primary_comparisons"]=config["primary_comparisons"][:-1]
    with pytest.raises(ValueError,match="complete"):_registered_family(config)


def test_immutable_outputs_and_source_change(tmp_path):
    protocol,root,store,ids,cell=fixture(tmp_path,reps=1)
    complete(store,ids[0],cell,"E4",frames(ids[0],cell,"E4"))
    output=tmp_path/"analysis"
    analyze_extension(protocol,root,output,bootstrap_resamples=0)
    before={path.name:path.read_bytes() for path in output.iterdir()}
    with pytest.raises(FileExistsError):analyze_extension(protocol,root,output,bootstrap_resamples=0)
    assert before=={path.name:path.read_bytes() for path in output.iterdir()}
    (tmp_path/"fixture_source.py").write_text("changed = True\n")
    with pytest.raises(ValueError,match="source changed"):
        analyze_extension(protocol,root,tmp_path/"changed_analysis",bootstrap_resamples=0)

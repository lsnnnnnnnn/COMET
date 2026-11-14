"""Handwritten interval fixtures; no scientific sampler or RNG is imported."""

import copy
import csv
import gzip
import json

import pytest

from comet.checkpoint_store import CheckpointStore, NAMESPACE, REQUIRED_INPUTS, canonical_bytes, freeze_protocol
from experiments.detailed_diagnostics import NumericSamples, detailed_diagnostics


def fixture(tmp_path,suite="E2",method="comet_local",reps=2):
    inputs=tmp_path/"inputs"
    inputs.mkdir()
    for name in REQUIRED_INPUTS:
        (inputs/name).write_text("DETERMINISTIC DIAGNOSTIC TEST ONLY: "+name)
    source=tmp_path/"fixture_source.py"
    source.write_text("fixture=True\n")
    cell={"E1":"independent-moderate-bounded","E2":"hub16-moderate",
          "E3":"support010-moderate-bounded","E4":"moderate-bounded-gapzero"}[suite]
    ids=[f"{NAMESPACE}/{suite}/{cell}/{i:04d}" for i in range(reps)]
    config=dict(namespace=NAMESPACE,suite="DETERMINISTIC_EXTENSION_FIXTURE" if suite!="E1" else "DETERMINISTIC_RUNNER_FIXTURE",
        target_suite=suite,N=8,legacy_new_outcome_draws=0,primary_units=0,total_unit_cap=max(1,reps),workers=1,
        planned_run_ids=ids,primary_comparisons=[[cell,method]],levels=[.05])
    protocol=tmp_path/"protocol.json"
    manifest=freeze_protocol(protocol,config,[source],inputs)
    root=tmp_path/"results"
    store=CheckpointStore(root,manifest)
    qids=("E2/policy0/auditor1","E2/policy0/auditor0") if suite=="E2" else (
        ("E4/policy0/auditor0","E4/policy1/auditor1") if suite=="E4" else ("policy0/half","policy0/all"))
    masses={qids[0]:.5,qids[1]:1.0}
    normalizers={query_id:1.0 for query_id in qids}
    if suite=="E4":
        masses[qids[0]]=.125
        normalizers[qids[0]]=.125
    ranges={query_id:[0,1.0 if normalizers[query_id]!=1 else masses[query_id]] for query_id in qids}
    if suite=="E3":
        ranges={query_id:[-.3,.3] for query_id in qids}
    thresholds={query_id:(.4 if suite=="E4" else 0 if suite=="E3" else .4*masses[query_id]) for query_id in qids}
    plans=[]
    for query_id in qids:
        norm=normalizers[query_id]
        plans.append(dict(query_id=query_id,method="comet_local" if "joint_level" in method else method,
            delta=.05,n=8,normalizer=norm,target_lo=ranges[query_id][0],target_hi=ranges[query_id][1],
            active_rows=round(8*masses[query_id]),color_count=2,
            bias_piece=.01*norm,variance_piece=.02*norm,range_piece=.03*norm))
    metadata=dict(fingerprint=manifest["fingerprint"],cell=cell,raw_N=8,family_size=2,
        actual_family_size=2,coordinate_hashes={query_id:"fixture-hash" for query_id in qids},
        aliases={query_id:query_id for query_id in qids},graph_colors=2,subgroup_masses=masses,
        plans=plans,known_target_ranges=ranges,query_thresholds=thresholds)
    if suite=="E4":
        metadata["design_choices"]=dict(planted_query_id=qids[0],gap=0.0)
    if suite=="E1":
        metadata.pop("query_thresholds")
    path=root/"cell_designs"/(cell+".json.gz")
    path.parent.mkdir(parents=True)
    path.write_bytes(gzip.compress(canonical_bytes(metadata),mtime=0))
    return protocol,root,store,manifest,ids,qids,metadata,method


def result_fixture(ids,qids,metadata,method,run_index=0):
    run_id=ids[run_index]
    suite=run_id.split("/")[1]
    truths={qids[0]:.2,qids[1]:.3}
    if suite=="E4":
        truths[qids[0]]=.4
    if suite=="E3":
        truths={query_id:0.0 for query_id in qids}
    records=[]
    for query_id in qids:
        estimate=truths[query_id]+run_index*.01
        raw_lo,raw_hi=estimate-.06,estimate+.06
        known_lo,known_hi=metadata["known_target_ranges"][query_id]
        records.append(dict(query_id=query_id,status="CERTIFIED_UNDER_DECLARED_ASSUMPTIONS",estimate=estimate,
            radius=.06,bias=.01,concentration=.02,range_contribution=.03,
            raw_lo=raw_lo,raw_hi=raw_hi,lo=max(raw_lo,known_lo),hi=min(raw_hi,known_hi),empty_intersection=False))
    return pack_result(run_id,records,truths,metadata,method)


def pack_result(run_id,records,truths,metadata,method):
    thresholds=metadata.get("query_thresholds",{query_id:.4*mass for query_id,mass in metadata["subgroup_masses"].items()})
    decisions={record["query_id"]:("ABSTAIN" if record.get("empty_intersection",False) else
        "CERTIFIED_SAFE" if record["hi"]<=thresholds[record["query_id"]] else
        "CERTIFIED_VIOLATION" if record["lo"]>thresholds[record["query_id"]] else "ABSTAIN") for record in records}
    covered=all(not record.get("empty_intersection",False) and record["lo"]<=truths[record["query_id"]]<=record["hi"] for record in records)
    false_safe=any(decisions[query_id]=="CERTIFIED_SAFE" and truths[query_id]>thresholds[query_id] for query_id in truths)
    false_violation=any(decisions[query_id]=="CERTIFIED_VIOLATION" and truths[query_id]<=thresholds[query_id] for query_id in truths)
    detected=any(decisions[query_id]=="CERTIFIED_VIOLATION" and truths[query_id]>thresholds[query_id] for query_id in truths)
    widths=[None if record.get("empty_intersection",False) else record["hi"]-record["lo"] for record in records]
    nontrivial=[width is not None and width<metadata["known_target_ranges"][record["query_id"]][1]-metadata["known_target_ranges"][record["query_id"]][0]
                for record,width in zip(records,widths)]
    trial=dict(run_id=run_id,cell=run_id.split("/")[2],method=method,delta=.05,family_covered=covered,
        metrics_assessable=True,any_false_safe=false_safe,any_false_violation=false_violation,
        any_false_claim=false_safe or false_violation,true_violation_detected=detected,
        mean_coordinate_width=sum(widths)/len(widths) if all(width is not None for width in widths) else None,
        candidate_nontrivial_fraction=sum(nontrivial)/len(nontrivial),
        candidate_abstention_fraction=sum(value=="ABSTAIN" for value in decisions.values())/len(decisions))
    return dict(suite=run_id.split("/")[1],cell=run_id.split("/")[2],raw_N=8,family_size=2,
        status="COMPLETE",truths=truths,legacy_new_outcome_draws=0,new_scientific_units=0,trials=[trial],
        certificate_records=[dict(method=method,delta=.05,family_size=2,coordinates=records,decisions=decisions)])


def test_numeric_samples_exact_quartiles_and_explicit_infinite_counts():
    samples=NumericSamples()
    for value in (0,1,2,3,None):
        samples.add(value)
    result=samples.result()
    assert result["median"]==1.5 and result["q25"]==.75 and result["q75"]==2.25
    assert result["iqr"]==1.5 and result["p90"]==pytest.approx(2.7)
    assert result["undefined_count"]==1
    samples.add(float("inf"))
    assert samples.result()["positive_infinite_count"]==1 and samples.result()["max"] is None


def test_independent_checks_query_scope_quantiles_and_exactly_one_checkpoint_load(tmp_path,monkeypatch):
    protocol,root,store,manifest,ids,qids,metadata,method=fixture(tmp_path)
    for index,run_id in enumerate(ids):
        store.complete(run_id,result_fixture(ids,qids,metadata,method,index))
    calls={}
    original=CheckpointStore.load
    def observed(self,run_id):
        calls[run_id]=calls.get(run_id,0)+1
        return original(self,run_id)
    monkeypatch.setattr(CheckpointStore,"load",observed)
    summary=detailed_diagnostics(protocol,root,tmp_path/"analysis")
    assert summary["status"]=="COMPLETE_CHECKS_PASS" and summary["mismatch_count"]==0
    assert calls=={run_id:1 for run_id in ids}
    group=summary["group_summaries"][0]
    assert group["independent_trials"]==2 and group["family_coverage"]["hits"]==2
    assert group["family_all_nontrivial"]["hits"]==2
    assert group["metrics"]["raw_width"]["n"]==4
    assert group["metrics"]["raw_width"]["median"]==pytest.approx(.12)
    assert group["metrics"]["trial_max_error_radius_ratio"]["max"]==pytest.approx(1/6)
    local=next(row for row in summary["query_summaries"] if row["query_id"]==qids[0])
    assert local["query_scope"]=="audited_first_half" and local["normalizer"]==1
    assert local["known_feasible_diameter"]==.5
    assert local["metrics"]["normalized_radius"]["median"]==pytest.approx(.12)
    assert local["metrics"]["feasible_width_ratio"]["median"]==pytest.approx(.24)
    with (tmp_path/"analysis/query_summary.csv").open(newline="") as stream:
        rows=list(csv.DictReader(stream))
    assert {row["query_scope"] for row in rows}=={"global","audited_first_half"}
    assert json.loads((tmp_path/"analysis/manifest.json").read_text())["checked_counts"]["checkpoint_load_calls"]==2
    assert gzip.decompress((tmp_path/"analysis/mismatches.jsonl.gz").read_bytes())==b""
    assert summary["new_outcome_draws"]==summary["legacy_new_outcome_draws"]==0


def test_e1_threshold_is_mass_scaled_and_outputs_are_immutable(tmp_path):
    protocol,root,store,_,ids,qids,metadata,method=fixture(tmp_path,suite="E1",reps=1)
    store.complete(ids[0],result_fixture(ids,qids,metadata,method))
    output=tmp_path/"analysis"
    summary=detailed_diagnostics(protocol,root,output)
    assert summary["mismatch_count"]==0
    half=next(row for row in summary["query_summaries"] if row["query_id"]==qids[0])
    assert half["threshold"]==.2
    before=(output/"summary.json").read_bytes()
    with pytest.raises(FileExistsError,match="immutable"):
        detailed_diagnostics(protocol,root,output)
    assert (output/"summary.json").read_bytes()==before


def test_empty_confidence_set_stays_failure_not_zero_width(tmp_path):
    protocol,root,store,_,ids,qids,metadata,method=fixture(tmp_path,reps=1)
    result=result_fixture(ids,qids,metadata,method)
    first=result["certificate_records"][0]["coordinates"][0]
    first.update(estimate=.7,radius=.1,bias=.02,concentration=.04,range_contribution=.04,
                 raw_lo=.6,raw_hi=.8,lo=.6,hi=.5,empty_intersection=True)
    # The selected fixture's pre-outcome plan has these declared components.
    metadata["plans"][0].update(bias_piece=.02,variance_piece=.04,range_piece=.04)
    path=root/"cell_designs"/(ids[0].split("/")[2]+".json.gz")
    path.write_bytes(gzip.compress(canonical_bytes(metadata),mtime=0))
    result=pack_result(ids[0],result["certificate_records"][0]["coordinates"],result["truths"],metadata,method)
    store.complete(ids[0],result)
    summary=detailed_diagnostics(protocol,root,tmp_path/"analysis")
    assert summary["mismatch_count"]==0
    row=summary["group_summaries"][0]
    assert row["family_coverage"]["hits"]==0 and row["empty_coordinates"]==1
    assert row["metrics"]["intersected_width"]["n"]==1
    assert row["metrics"]["intersected_width"]["undefined_count"]==1
    assert row["metrics"]["raw_width"]["n"]==2
    assert row["metrics"]["trial_max_error_radius_ratio"]["max"]==pytest.approx(5)


def test_e3_derived_constituent_empty_can_have_ordered_endpoints_but_remains_empty(tmp_path):
    method="deduplicated_joint_level_difference"
    protocol,root,store,_,ids,qids,metadata,_=fixture(tmp_path,suite="E3",method=method,reps=1)
    result=result_fixture(ids,qids,metadata,method)
    first=result["certificate_records"][0]["coordinates"][0]
    first.update(estimate=.15,radius=.2,bias=.05,concentration=.1,range_contribution=.05,
        raw_lo=-.05,raw_hi=.35,lo=.1,hi=.2,empty_intersection=True)
    result=pack_result(ids[0],result["certificate_records"][0]["coordinates"],result["truths"],metadata,method)
    store.complete(ids[0],result)
    summary=detailed_diagnostics(protocol,root,tmp_path/"analysis")
    assert summary["mismatch_count"]==0
    assert summary["checked_counts"]["derived_constituent_empty_not_geometrically_reconstructible"]==1
    assert summary["group_summaries"][0]["family_coverage"]["hits"]==0
    assert summary["group_summaries"][0]["empty_coordinates"]==1


def test_e4_primary_uses_exact_analytic_target_and_normalization_once(tmp_path):
    protocol,root,store,_,ids,qids,metadata,method=fixture(tmp_path,suite="E4",reps=1)
    result=result_fixture(ids,qids,metadata,method)
    # Incorrect stored post-hoc truth must not redefine the frozen null gap.
    result["truths"][qids[0]]=.3
    result["certificate_records"][0]["coordinates"][0].update(estimate=.3,raw_lo=.24,raw_hi=.36,lo=.24,hi=.36)
    result=pack_result(ids[0],result["certificate_records"][0]["coordinates"],result["truths"],metadata,method)
    store.complete(ids[0],result)
    summary=detailed_diagnostics(protocol,root,tmp_path/"analysis")
    assert summary["mismatch_counts"]["ANALYTIC_PRIMARY_TRUTH_MISMATCH"]==1
    assert summary["mismatch_counts"]["SAVED_TRIAL_BOOLEAN_MISMATCH"]>=1
    primary=next(row for row in summary["query_summaries"] if row["query_id"]==qids[0])
    assert primary["normalizer"]==.125
    assert primary["metrics"]["normalized_radius"]["median"]==.06
    assert primary["metrics"]["absolute_error"]["median"]==pytest.approx(.1)
    assert summary["group_summaries"][0]["family_coverage"]["hits"]==0


def test_failed_empty_trial_records_expand_denominators_and_keep_unknown_errors(tmp_path):
    protocol,root,store,_,ids,_,_,_=fixture(tmp_path,reps=1)
    store.complete(ids[0],dict(status="UNIT_FAILURE",cell=ids[0].split("/")[2],raw_N=8,family_size=2,
        full_family_failure=True,unassessable_whole_trial=True,trials=[],certificate_records=[]))
    summary=detailed_diagnostics(protocol,root,tmp_path/"analysis")
    group=summary["group_summaries"][0]
    assert group["independent_trials"]==1 and group["expected_coordinate_records"]==2
    assert group["family_coverage"]["hits"]==0
    assert group["any_false_safe"]["unknown_trials"]==1
    assert group["any_false_safe"]["rate"] is None
    assert group["metrics"]["raw_width"]["undefined_count"]==2
    assert group["status_counts"]=={"MISSING_METHOD_LEVEL_FRAME":2}


def test_missing_fields_and_wrong_saved_booleans_are_retained_as_mismatch_records(tmp_path):
    protocol,root,store,_,ids,qids,metadata,method=fixture(tmp_path,reps=1)
    result=result_fixture(ids,qids,metadata,method)
    result["certificate_records"][0]["coordinates"][0].pop("radius")
    result["trials"][0]["family_covered"]=False
    result["raw_N"]=9
    store.complete(ids[0],result)
    summary=detailed_diagnostics(protocol,root,tmp_path/"analysis")
    assert summary["status"]=="MISMATCHES_FOUND"
    assert summary["mismatch_counts"]["MISSING_OR_INVALID_RADIUS"]==1
    assert summary["mismatch_counts"]["ACTUAL_N_MISMATCH"]==2
    assert summary["mismatch_counts"]["SAVED_TRIAL_BOOLEAN_MISMATCH"]==1
    records=[json.loads(line) for line in gzip.decompress((tmp_path/"analysis/mismatches.jsonl.gz").read_bytes()).splitlines()]
    assert len(records)==summary["mismatch_count"]
    assert all(record["run_id"]==ids[0] for record in records)


def test_corrupt_checkpoint_is_not_dropped_or_reinterpreted_as_missing(tmp_path):
    protocol,root,store,_,ids,qids,metadata,method=fixture(tmp_path,reps=1)
    store.complete(ids[0],result_fixture(ids,qids,metadata,method))
    record=json.loads(gzip.decompress(store.path(ids[0]).read_bytes()))
    record["payload"]["result"]["raw_N"]=99
    store.path(ids[0]).write_bytes(gzip.compress(json.dumps(record).encode()))
    summary=detailed_diagnostics(protocol,root,tmp_path/"analysis")
    assert summary["status"]=="CHECKPOINT_INTEGRITY_ERRORS"
    assert summary["completed_checkpoint_files"]==summary["corrupt_checkpoint_units"]==1
    assert summary["verified_checkpoint_units"]==summary["missing_units"]==0
    assert summary["group_summaries"][0]["family_coverage"]["denominator"]==1

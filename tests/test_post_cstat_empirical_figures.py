"""Explicit aggregate table fixtures only; no sampler or Monte Carlo driver."""

import csv
import gzip
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pytest

from comet.checkpoint_store import CheckpointStore,NAMESPACE,REQUIRED_INPUTS,canonical_bytes,freeze_protocol
from comet.metrics import wilson
from experiments.core_graph_dgp import build_core_design,generate_from_primitives
from experiments.post_cstat_empirical_figures import (
    _endpoint,_event_records,_load_summary,_point,_rate_text,
    prespecified_envelope_diagnostics,render_bundle,
)


def event(rate,n=100,*,unknown=0,applicable=True):
    hits=round(rate*n)
    return dict(hits=hits if applicable else None,denominator=n if applicable else 0,
        rate=rate if applicable and not unknown else None,unknown_trials=unknown,
        applicable=applicable,wilson95=list(wilson(hits,n)) if applicable and not unknown else None)


def row(cell,method,*,violation=.8,safe=.1):
    return dict(cell=cell,method=method,delta=.05,independent_trials=100,
        family_coverage=event(1),mean_per_trial_coordinate_width=.2,
        endpoints={"any_false_claim":event(0),"true_violation_detected":event(violation)},
        extension_endpoints={"primary_certified_violation":event(violation),"primary_certified_safe":event(safe)})


def summary_file(directory,suite,rows):
    directory.mkdir(parents=True)
    body=dict(suite=suite,status="COMPLETE",phase="DETERMINISTIC_FIXTURE_NOT_SCIENCE",completed_units=100,
              remaining_units=0,summaries=rows)
    payload=canonical_bytes(body)+b"\n"
    (directory/"summary.json").write_bytes(payload)
    (directory/"manifest.json").write_text(json.dumps(dict(outputs={"summary.json":hashlib.sha256(payload).hexdigest()})))
    return directory


def detailed_files(directory,groups,queries):
    directory.mkdir(parents=True)
    hashes={}
    for name,rows in (("group_summary.csv",groups),("query_summary.csv",queries)):
        fields=list(dict.fromkeys(key for record in rows for key in record)) or ["cell","method","delta"]
        stream=io.StringIO(newline="")
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
        payload=stream.getvalue().encode()
        (directory/name).write_bytes(payload);hashes[name]=hashlib.sha256(payload).hexdigest()
    (directory/"manifest.json").write_text(json.dumps(dict(mismatch_count=0,outputs=hashes)))
    return directory


def fixture_inputs(tmp_path):
    core_cell="independent-moderate-bounded"
    analyses={"E1":summary_file(tmp_path/"E1_analysis","E1",[row(core_cell,method) for method in ("comet_local","generic_matched","truncated_global_envelope","colorwise_truncation","graph_bernstein")])}
    groups=[]
    for method in ("comet_local","generic_matched","truncated_global_envelope","colorwise_truncation","graph_bernstein"):
        groups.append(dict(cell=core_cell,method=method,delta=.05,feasible_width_ratio_median=.4,
            feasible_width_ratio_q25=.3,feasible_width_ratio_q75=.5,family_any_nontrivial_rate=1,
            family_all_nontrivial_rate=.8,trial_max_error_radius_ratio_max=.4,trial_max_error_radius_ratio_p90=.2))
    details={"E1":detailed_files(tmp_path/"E1_detailed",groups,[])}
    locality=[]
    for overlap in ("moderate","extreme1e-4"):
        for hub in (1,16,64):
            for auditor in ("auditor0","auditor1"):
                for method in ("comet_local","truncated_global_graph","truncated_global_envelope","graph_bernstein"):
                    locality.append(dict(cell=f"hub{hub}-{overlap}",method=method,delta=.05,
                        query_id="E2/policy0/"+auditor,query_scope="global" if auditor=="auditor0" else "audited_first_half",
                        normalizer=1,known_feasible_diameter=1 if auditor=="auditor0" else .5,
                        normalized_radius_median=.1 if method=="comet_local" and auditor=="auditor1" else .1*hub))
    details["E2"]=detailed_files(tmp_path/"E2_detailed",[],locality)
    contrast=[]
    for outcome in ("bounded","heavy"):
        for overlap in ("moderate","weak"):
            for support in (2,10,100):
                for method in ("comet_local","deduplicated_joint_level_difference","truncated_global_envelope"):
                    contrast.append(dict(cell=f"support{support:03d}-{overlap}-{outcome}",method=method,delta=.05,
                        query_id="E3/policy0/auditor0",intersected_width_median=support/100*(.1 if method=="comet_local" else .2)))
    details["E3"]=detailed_files(tmp_path/"E3_detailed",[],contrast)
    powers=[];power_detail=[]
    for outcome in ("bounded","heavy"):
        for overlap in ("moderate","weak"):
            for gap in ("m010","zero","p010","p020"):
                cell=f"{overlap}-{outcome}-gap{gap}"
                for method in ("comet_local","generic_matched","truncated_global_envelope"):
                    powers.append(row(cell,method,violation=1 if gap.startswith("p") else 0,safe=1 if gap=="m010" else 0))
                power_detail.append(dict(cell=cell,method="comet_local",delta=.05,query_id="E4/policy0/auditor0",normalized_radius_median=.03))
    analyses["E4"]=summary_file(tmp_path/"E4_analysis","E4",powers)
    details["E4"]=detailed_files(tmp_path/"E4_detailed",[],power_detail)
    pipelines=[]
    for cell in ("independent-moderate-null","cycle-weak-mixed"):
        for method in ("point_constraint","in_sample_auditing","independent_global","comet_local","generic_matched","fixed_slice","abstain_reference","status_quo_reference"):
            returned=0 if method=="abstain_reference" else .8
            pipelines.append(dict(cell=cell,method=method,delta=.05,independent_trials=100,family_coverage=event(1),
                endpoints={"returned":event(returned),"return_unsafe":event(0),"return_safe_useful":event(returned)},
                pipeline_metrics={"joint_events":{"return_and_infeasible":event(0)},"numeric_metrics":{
                    "true_utility":dict(mean=.2 if returned else None,value_count=round(returned*100),whole_trials=100,
                        unassessable_trials=0,value_scope="returned policies only")}}))
    analyses["E5"]=summary_file(tmp_path/"E5_analysis","E5",pipelines)
    anchors=summary_file(tmp_path/"anchors","ANCHORS",[row("iid-bounded",method) for method in ("comet_local","graph_bernstein","bhatt2022_catoni_iid","author_one_dimensional_ope_betting","waudby_smith_2024_dr_eb_independent")])
    controls=summary_file(tmp_path/"controls","NEGATIVE_CONTROLS",[])
    body=json.loads((controls/"summary.json").read_text())
    body["summaries"]=[dict(control="wrong_propensity",engine=engine,delta=.05,independent_units=100,
        false_claim=event(0 if engine=="valid_actual_model" else .5),interval_coverage=event(1),guarantee_type="diagnostic")
        for engine in ("valid_actual_model","intentionally_invalid")]
    payload=canonical_bytes(body)+b"\n";(controls/"summary.json").write_bytes(payload)
    (controls/"manifest.json").write_text(json.dumps(dict(outputs={"summary.json":hashlib.sha256(payload).hexdigest()})))
    return analyses,details,anchors,controls


def test_render_all_panels_and_export_exact_event_counts(tmp_path):
    analyses,details,anchors,controls=fixture_inputs(tmp_path)
    output=tmp_path/"figures"
    manifest=render_bundle(output,analyses=analyses,detailed=details,anchors=anchors,controls=controls,formats=("png",))
    assert len(manifest["figures"])==6
    assert all((output/(name+".png")).stat().st_size>1000 for name in manifest["figures"])
    assert manifest["data_scope"]=="DETERMINISTIC_FIXTURE_NOT_SCIENCE"
    assert manifest["new_outcome_draws"]==manifest["legacy_new_outcome_draws"]==0
    assert all(check["status"]=="IDENTICAL_REPORTED_SUMMARIES" for check in manifest["equivalence_checks"])
    with (output/"empirical_events.csv").open(newline="") as stream:
        records=list(csv.DictReader(stream))
    error=next(record for record in records if record["suite"]=="E1" and record["endpoint"]=="any_false_claim")
    assert error["hits"]=="0" and error["denominator"]=="100"
    assert float(error["wilson95_hi"])>0
    assert "Matched generic (= COMET)" in (output/"empirical_events.tex").read_text()
    with pytest.raises(FileExistsError,match="immutable"):
        render_bundle(output,analyses=analyses,formats=("png",),only=("core",))


def test_unknown_or_unavailable_inputs_are_not_imputed_as_zero(tmp_path):
    record=row("example","comet_local")
    record["endpoints"]["return_unsafe"]=event(0,unknown=1)
    assert _point(_endpoint(record,"return_unsafe")) is None
    formatted=_rate_text(dict(applicable=True,unknown_trials=1,rate=None,hits=0,denominator=100))
    assert formatted=="NA (unknown 1)"
    output=tmp_path/"unavailable"
    manifest=render_bundle(output,analyses={"E5":tmp_path/"not_present"},formats=("png",),only=("pipeline",))
    assert manifest["availability"]["E5"]["status"]=="UNAVAILABLE"
    with (output/"empirical_events.csv").open() as stream:
        assert list(csv.DictReader(stream))==[]


def test_input_hash_mismatch_is_marked_and_not_plotted(tmp_path):
    path=summary_file(tmp_path/"analysis","E1",[row("example","comet_local")])
    (path/"summary.json").write_text('{}')
    data,state=_load_summary(path,"E1")
    assert data is None and state["status"]=="INPUT_HASH_MISMATCH"


def test_raw_envelope_reads_only_prespecified_saved_arrays_no_rng(tmp_path,monkeypatch):
    inputs=tmp_path/"inputs";inputs.mkdir()
    for name in REQUIRED_INPUTS:(inputs/name).write_text("DETERMINISTIC FIXTURE "+name)
    source=tmp_path/"source.py";source.write_text("fixture=True\n")
    cell="independent-moderate-bounded"
    run_id=f"{NAMESPACE}/E1/{cell}/0000"
    domain=NAMESPACE+"/E1-raw-fixture"
    config=dict(namespace=NAMESPACE,suite="DETERMINISTIC_RUNNER_FIXTURE",N=8,seed_domain=domain,
        legacy_new_outcome_draws=0,primary_units=0,total_unit_cap=1,workers=1,planned_run_ids=[run_id],raw_debug_run_ids=[run_id])
    protocol=tmp_path/"protocol.json";manifest=freeze_protocol(protocol,config,[source],inputs)
    root=tmp_path/"results";store=CheckpointStore(root,manifest)
    design=build_core_design(8,"independent","moderate","bounded",domain+"/"+cell)
    log=generate_from_primitives(design,np.zeros(8,dtype=np.uint32),{source:1 for source in design.outcome_source_ids})
    store.complete(run_id,dict(data_digest=log.data_digest,prespecified_raw_debug=dict(actions=log.actions.tolist(),outcomes=log.outcomes.tolist())))
    path=root/"cell_designs"/(cell+".json.gz");path.parent.mkdir(parents=True)
    metadata={key:hashlib.sha256(value.tobytes()).hexdigest() for key,value in (
        ("exposure_sha256",design.exposure),("common_nuisance_sha256",design.nuisance),("common_residual_moments_sha256",design.residual_moments))}
    path.write_bytes(gzip.compress(canonical_bytes(metadata),mtime=0))
    def forbidden(*args,**kwargs):raise AssertionError("no RNG or observation regeneration allowed")
    monkeypatch.setattr(np.random,"default_rng",forbidden)
    result=prespecified_envelope_diagnostics(protocol,root)
    assert result["status"]=="DESCRIPTIVE_ONLY" and len(result["rows"])==16
    assert result["new_outcome_draws"]==0 and not result["observations_regenerated"]
    assert not result["oracle_used"] and not result["radii_modified"]
    assert all(record["bounded_residual_range_violation_rows"]==0 for record in result["rows"])

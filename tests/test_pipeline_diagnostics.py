"""Read-only E5 reconstruction from hand-written records; zero scientific draws."""

import csv
import math

import numpy as np
import pytest

from comet.checkpoint_store import CheckpointStore, NAMESPACE, REQUIRED_INPUTS, freeze_protocol
from comet.metrics import wilson
from experiments import pipeline_diagnostics as diagnostic


CELL = "independent-moderate-null"
ARMS = ("point_constraint", "in_sample_auditing", "independent_global", "comet_local",
        "generic_matched", "fixed_slice", "abstain_reference", "status_quo_reference")
Q0 = math.floor(.35*2**32+.5)/2**32


@pytest.fixture(autouse=True)
def no_random_sources(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("diagnostics must not draw random sources")
    monkeypatch.setattr(np.random, "default_rng", forbidden)


def protocol_fixture(tmp_path, count=1):
    inputs = tmp_path/"inputs"
    inputs.mkdir()
    for name in REQUIRED_INPUTS:
        (inputs/name).write_text("ARTIFICIAL RECORD FIXTURE: "+name)
    source = tmp_path/"fixture_source.py"
    source.write_text("artificial_records = True\n")
    ids = [f"{NAMESPACE}/E5/{CELL}/{index:04d}" for index in range(count)]
    config = dict(namespace=NAMESPACE, suite="DETERMINISTIC_PIPELINE_FIXTURE", workers=1,
        legacy_new_outcome_draws=0, primary_units=0, total_unit_cap=count,
        planned_run_ids=ids, cells=[CELL], split_sizes=dict(training=4,discovery=4,certification=8),
        arms=list(ARMS), levels=[.05,.1], risk_threshold=.32, utility_margin=.01,
        service_floor=.2, capacity_ceiling=.6)
    protocol = tmp_path/"protocol.json"
    manifest = freeze_protocol(protocol,config,[source],inputs)
    root = tmp_path/"results"
    return protocol, root, manifest, source, ids


def scalar_context(n, world="null"):
    rows=[]
    for i in range(n):
        u=(i+.5)/n
        x=(2*u-1,math.sin(6*math.pi*u+.37),math.cos(10*math.pi*u+.19),math.sin(14*math.pi*u+.73))
        logistic=lambda v:1/(1+math.exp(-v))
        planted=x[0]>-.15 and x[1]>.1 and x[2]>-.05
        risk=.20+.06*logistic(1.3*x[0]-.8*x[1])+.025*x[2]
        utility=.45+.15*logistic(1.2*x[0]+.8*x[2])+.05*x[1]
        if world=="mixed":
            interaction=logistic(3*math.prod(x))
            risk+=.30*planted+.05*interaction
            utility+=.12*planted+.03*interaction
        rows.append((x,risk,utility,planted if world=="mixed" else False))
    return rows


def family_fixture(name):
    aliases={key:key for key in ("risk/policy0/all","risk/policy1/all","utility/policy1-minus-policy0")}
    return dict(family_digest=name,actual_family_size=3,risk_coordinate_count=2,utility_coordinate_count=1,
        aliases=aliases,fit_coefficients=dict(risk=[.2]+[0]*10,utility=[.5]+[0]*10),
        auditor_rules=[],policy_rules=[
            dict(policy_id="policy0",tradeoff=None,center=0,scale=1,intercept=0),
            dict(policy_id="policy1",tradeoff=0,center=.5,scale=1,intercept=0)],
        policy_known_service=dict(policy0=Q0,policy1=.5))


def complete_fixture(run_id):
    meanutility=sum(row[2] for row in scalar_context(8))/8
    trials,frames=[],[]
    for delta in (.05,.1):
        for arm in ARMS:
            point=arm in ("point_constraint","in_sample_auditing")
            certified=arm in diagnostic.CERTIFIED_ARMS
            returned=arm!="abstain_reference"
            baseline=arm=="status_quo_reference"
            q=Q0 if baseline else .5
            policy=None if not returned else ("policy0" if baseline else "policy1")
            row=dict(run_id=run_id,cell=CELL,method=arm,delta=delta,metrics_assessable=True,
                family_covered=certified,any_false_claim=False,any_false_safe=False,
                any_false_violation=False,any_false_utility_claim=False,true_violation_detected=False,
                discovered_and_certified=False,returned=returned,returned_baseline=baseline,
                return_unsafe=False,return_safe_useful=returned,return_and_infeasible=False,
                return_and_risk_safe=returned,return_and_utility_noninferior=returned,
                return_and_service_feasible=returned,true_utility=q*meanutility if returned else None,
                utility_gain=(q-Q0)*meanutility if returned else None,
                expected_service=q if returned else 0.,expected_capacity=q if returned else 0.,
                maximum_true_risk_violation=0. if returned else None,
                oracle_best_feasible_candidate_value=.5*meanutility,robust_slack_comparator_value=None,
                discovery_best_planted_iou=None)
            name="fixed" if arm=="fixed_slice" else "in_sample" if arm=="in_sample_auditing" else "proper"
            certificates=[dict(query_id=key,channel="utility" if key.startswith("utility") else "risk",
                normalizer=1.,status=diagnostic.CERTIFIED,empty_intersection=False,
                lo=.01 if key.startswith("utility") else 0.,hi=.2 if key.startswith("utility") else .3,
                radius=.095 if key.startswith("utility") else .15)
                for key in family_fixture(name)["aliases"]] if certified else []
            frame=dict(method=arm,delta=delta,family_digest=name,actual_family_size=3,
                coordinate_allocation=delta/3 if certified else None,
                selection=dict(returned=returned,policy_id=policy),certificates=certificates)
            if point:
                frame["point_estimates"]={"risk/policy0/all":.1,"risk/policy1/all":.12,
                    "utility/policy1-minus-policy0":.05}
            trials.append(row)
            frames.append(frame)
    return dict(suite="E5",cell=CELL,status="COMPLETE",split_sizes=dict(training=4,discovery=4,certification=8),
        exposed_labels=dict(training=2,discovery=3,certification=4),total_rows=16,
        proper_family=family_fixture("proper"),fixed_slice_family=family_fixture("fixed"),
        in_sample_family=family_fixture("in_sample"),trials=trials,certificate_records=frames,
        raw_debug={"training":{"actions":[0,1,0,1]},"discovery":{"actions":[1,1,0,1]},
            "certification":{"actions":[0,1,0,1,0,1,0,1]}})


def group(report, arm, delta=.05):
    return next(row for row in report["summaries"] if row["method"]==arm and row["delta"]==delta)


def test_independent_reconstruction_and_whole_trial_baseline_update_endpoints(tmp_path):
    protocol,root,manifest,_,ids=protocol_fixture(tmp_path)
    store=CheckpointStore(root,manifest)
    store.complete(ids[0],complete_fixture(ids[0]))
    before=store.path(ids[0]).read_bytes()
    report=diagnostic.diagnose_pipeline(protocol,root,tmp_path/"diagnostic")
    assert report["verification_status"]=="RECONSTRUCTED_RECORDS_MATCH",report["verification"]
    assert report["verification"]["reconstruction_counts"]["frames_reconstructed"]==16
    assert report["verification"]["mismatches"]=={}
    update=group(report,"comet_local")["endpoints"]
    baseline=group(report,"status_quo_reference")["endpoints"]
    abstain=group(report,"abstain_reference")["endpoints"]
    for key in ("return_nonbaseline_and_safe_and_useful","return_and_strict_positive_utility_gain"):
        assert update[key]["hits"]==1 and update[key]["denominator"]==1
        assert update[key]["wilson95"]==list(wilson(1,1))
        assert baseline[key]["hits"]==abstain[key]["hits"]==0
    assert baseline["return_baseline_and_safe_and_useful"]["hits"]==1
    assert baseline["returned_baseline"]["hits"]==1
    budget=report["data_budget"]
    assert budget["allocated_total_rows_for_checkpoint_ids"]==16
    assert budget["exposed_units_by_split"]["certification"]["known_sum"]==4
    assert budget["exposed_units_by_split"]["certification"]["observed_risk_and_utility_channel_values"]==8
    assert report["new_scientific_units"]==0 and not report["original_oracle_called"]
    assert store.path(ids[0]).read_bytes()==before
    rows=list(csv.DictReader((tmp_path/"diagnostic/endpoint_rates.csv").open()))
    assert len(rows)==16*len(diagnostic.ENDPOINTS)
    with pytest.raises(FileExistsError,match="fresh"):
        diagnostic.diagnose_pipeline(protocol,root,tmp_path/"diagnostic")


def test_failed_trial_retains_every_arm_level_and_known_partial_data_budget(tmp_path):
    protocol,root,manifest,_,ids=protocol_fixture(tmp_path,2)
    store=CheckpointStore(root,manifest)
    store.complete(ids[0],complete_fixture(ids[0]))
    store.complete(ids[1],dict(status="UNIT_FAILURE",unassessable_whole_trial=True,trials=[],
        raw_debug={"training":{"actions":[0,1,0,1]}}))
    report=diagnostic.diagnose_pipeline(protocol,root,tmp_path/"diagnostic")
    assert report["completed_units"]==2 and report["remaining_units"]==0
    assert report["verification_status"]=="RECONSTRUCTED_ASSESSABLE_RECORDS_WITH_UNKNOWNS"
    assert len(report["summaries"])==16
    for row in report["summaries"]:
        for endpoint in row["endpoints"].values():
            assert endpoint["denominator"]==2 and endpoint["unknown_trials"]==1
            assert endpoint["rate"] is None and endpoint["wilson95"] is None
    budget=report["data_budget"]
    assert budget["allocated_total_rows_for_checkpoint_ids"]==32
    assert budget["generated_split_rows"]["training"]==dict(known_sum=8,known_trial_ids=2,unknown_trial_ids=0)
    assert budget["generated_split_rows"]["certification"]==dict(known_sum=8,known_trial_ids=1,unknown_trial_ids=1)
    assert budget["exposed_units_by_split"]["training"]["known_sum"]==4
    assert budget["reported_generated_total_rows"]["unknown_trial_ids"]==1


def test_disagreement_reports_saved_choice_and_does_not_replace_it_with_optimal_choice(tmp_path):
    protocol,root,manifest,_,ids=protocol_fixture(tmp_path)
    result=complete_fixture(ids[0])
    frame=next(frame for frame in result["certificate_records"] if frame["method"]=="comet_local" and frame["delta"]==.05)
    frame["selection"]["policy_id"]="policy0"
    CheckpointStore(root,manifest).complete(ids[0],result)
    report=diagnostic.diagnose_pipeline(protocol,root,tmp_path/"diagnostic",maximum_examples=2)
    assert report["verification_status"]=="DISCREPANCIES_OR_UNVERIFIABLE_RECORDS"
    assert report["verification"]["mismatches"]["selection_policy_id"]==1
    assert len(report["verification"]["bounded_examples"])==2
    endpoints=group(report,"comet_local")["endpoints"]
    assert endpoints["returned_baseline"]["hits"]==1
    assert endpoints["return_nonbaseline_and_safe_and_useful"]["hits"]==0
    assert endpoints["return_and_strict_positive_utility_gain"]["hits"]==0


def test_mixed_world_subgroup_normalizer_and_planted_iou_are_rebuilt_without_oracle():
    family=family_fixture("mixed")
    family["auditor_rules"]=[dict(rule_id="positive_x0",literals=[(0,True)])]
    for policy in ("policy0","policy1"):
        key=f"risk/{policy}/positive_x0"
        family["aliases"][key]=key
    family["actual_family_size"]=5
    findings=diagnostic.Findings(5e-12,5e-13,3)
    result=diagnostic._reconstruct_family(family,diagnostic._context(8,"mixed"),findings,{})
    selected=[row for row in scalar_context(8,"mixed") if row[0][0]>0]
    expected=.5*sum(row[1] for row in selected)/len(selected)
    assert result["targets"]["risk/policy1/positive_x0"]==pytest.approx(expected,rel=5e-13)
    rows=scalar_context(8,"mixed")
    intersection=sum(row[0][0]>0 and row[3] for row in rows)
    union=sum(row[0][0]>0 or row[3] for row in rows)
    assert result["discovery_iou"]==intersection/union
    assert findings.mismatches=={}


def test_aliased_subgroup_keeps_logical_discovery_identity():
    description=family_fixture("alias")
    description["auditor_rules"]=[dict(rule_id="equivalent_all",literals=[])]
    for policy in ("policy0","policy1"):
        description["aliases"][f"risk/{policy}/equivalent_all"]=f"risk/{policy}/all"
    findings=diagnostic.Findings(5e-12,5e-13,3)
    family=diagnostic._reconstruct_family(description,diagnostic._context(8,"null"),findings,{})
    certificates=[dict(query_id=key,status=diagnostic.CERTIFIED,lo=.06,hi=.2,radius=.07)
                  for key in family["targets"]]
    frame=dict(certificates=certificates,selection=dict(returned=False,policy_id=None))
    config=dict(risk_threshold=.05,utility_margin=.01,service_floor=.2,capacity_ceiling=.6)
    metrics=diagnostic._reconstruct_metrics(family,family,frame,"comet_local",config)
    assert metrics["true_violation_detected"] and metrics["discovered_and_certified"]
    assert findings.mismatches=={}


def test_missing_frames_stay_unknown_and_source_changes_refuse_analysis(tmp_path):
    protocol,root,manifest,source,ids=protocol_fixture(tmp_path)
    result=complete_fixture(ids[0])
    result["certificate_records"]=[frame for frame in result["certificate_records"] if frame["method"]!="comet_local"]
    CheckpointStore(root,manifest).complete(ids[0],result)
    report=diagnostic.diagnose_pipeline(protocol,root,tmp_path/"diagnostic")
    assert group(report,"comet_local")["endpoints"]["returned"]["unknown_trials"]==1
    source.write_text("changed=True\n")
    with pytest.raises(ValueError,match="source changed"):
        diagnostic.diagnose_pipeline(protocol,root,tmp_path/"changed_source")


def test_no_checkpoints_keeps_all_reserved_ids_without_invented_rates(tmp_path):
    protocol,root,_,_,ids=protocol_fixture(tmp_path)
    report=diagnostic.diagnose_pipeline(protocol,root,tmp_path/"diagnostic")
    assert report["completed_units"]==0 and report["remaining_ids"]==ids
    assert report["verification_status"]=="NO_COMPLETED_UNITS" and report["summaries"]==[]

"""Independent, read-only interval diagnostics for frozen E1--E4 checkpoints.

No estimator, production statistic, sampler or oracle is imported. Saved
post-method truths and design metadata identify the comparisons. Boolean
coverage/decision checks use exact saved endpoints; the declared tolerance is
used only for redundant floating arithmetic, never to forgive undercoverage.
Candidate quantiles are descriptive. One complete log remains the independent
coverage/error unit, including missing and failed records.
"""

import argparse
from array import array
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import tempfile

from comet.checkpoint_store import CheckpointStore, canonical_bytes, digest, install_once


CERTIFIED = "CERTIFIED_UNDER_DECLARED_ASSUMPTIONS"
METRICS = ("raw_width", "intersected_width", "feasible_width_ratio", "raw_feasible_width_ratio",
    "normalized_width", "normalized_radius", "absolute_error", "normalized_absolute_error",
    "error_radius_ratio", "signed_error", "radius", "bias_piece", "concentration_piece", "range_piece")
TRIAL_METRICS = ("trial_max_error_radius_ratio", "trial_mean_intersected_width", "trial_mean_normalized_width")
REL_TOL, ABS_TOL = 5e-12, 5e-13
OUTPUTS = ("summary.json", "group_summary.csv", "query_summary.csv", "manifest.json", "mismatches.jsonl.gz")


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _all(values):
    return False if False in values else (None if None in values else True)


def _any(values):
    return True if True in values else (None if None in values else False)


def _quantile(sorted_values, probability):
    if not sorted_values:
        return None
    position = (len(sorted_values)-1)*probability
    left = math.floor(position)
    weight = position-left
    return sorted_values[left]*(1-weight) + sorted_values[min(left+1, len(sorted_values)-1)]*weight


class NumericSamples:
    def __init__(self):
        self.values = array("d")
        self.undefined = self.positive_infinite = self.negative_infinite = 0

    def add(self, value):
        if value is None or (isinstance(value, float) and math.isnan(value)):
            self.undefined += 1
        elif math.isinf(value):
            if value > 0:
                self.positive_infinite += 1
            else:
                self.negative_infinite += 1
        else:
            self.values.append(float(value))

    def extend(self, other):
        self.values.extend(other.values)
        self.undefined += other.undefined
        self.positive_infinite += other.positive_infinite
        self.negative_infinite += other.negative_infinite

    def result(self):
        ordered = sorted(self.values)
        q25, q75 = _quantile(ordered,.25), _quantile(ordered,.75)
        return dict(n=len(ordered), undefined_count=self.undefined,
            positive_infinite_count=self.positive_infinite, negative_infinite_count=self.negative_infinite,
            median=_quantile(ordered,.5), q25=q25, q75=q75,
            iqr=q75-q25 if ordered else None, p90=_quantile(ordered,.9),
            min=None if self.negative_infinite else (ordered[0] if ordered else None),
            max=None if self.positive_infinite else (ordered[-1] if ordered else None),
            finite_max=ordered[-1] if ordered else None,
            quantile_scope="finite defined values; undefined and infinite cases counted explicitly")


class BooleanCounts:
    def __init__(self):
        self.n = self.hits = self.unknown = 0

    def add(self, value):
        self.n += 1
        if value is None:
            self.unknown += 1
        else:
            self.hits += bool(value)

    def result(self):
        return dict(hits=self.hits, denominator=self.n, unknown_trials=self.unknown,
            rate=self.hits/self.n if self.n and not self.unknown else None,
            realized_frequency_bounds=[self.hits/self.n,(self.hits+self.unknown)/self.n] if self.n else None)


class MismatchLog:
    """Keep every discrepancy on disk; retain only a small example view in RAM."""
    def __init__(self, directory):
        directory.mkdir(parents=True,exist_ok=True)
        fd, path = tempfile.mkstemp(prefix=".pending-diagnostics-",dir=directory)
        self.path, self.target = Path(path), directory/"mismatches.jsonl.gz"
        self.raw = os.fdopen(fd,"wb")
        self.gz = gzip.GzipFile(filename="",fileobj=self.raw,mode="wb",mtime=0)
        self.counts, self.examples = Counter(), []

    def add(self, kind, *, run_id=None, cell=None, method=None, delta=None, query_id=None, **details):
        record=dict(kind=kind,run_id=run_id,cell=cell,method=method,delta=delta,query_id=query_id,**details)
        self.counts[kind] += 1
        self.gz.write(canonical_bytes(record)+b"\n")
        if len(self.examples)<20:
            self.examples.append(record)

    def finish(self):
        self.gz.close()
        self.raw.flush()
        os.fsync(self.raw.fileno())
        self.raw.close()
        os.link(self.path,self.target)
        self.path.unlink()

    def abort(self):
        self.gz.close()
        if not self.raw.closed:
            self.raw.close()
        self.path.unlink(missing_ok=True)


def _file_hash(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def _suite(config):
    declared=config.get("suite")
    value=(config.get("target_suite") if declared=="DETERMINISTIC_EXTENSION_FIXTURE"
           else "E1" if declared=="DETERMINISTIC_RUNNER_FIXTURE" else declared)
    if value not in ("E1","E2","E3","E4"):
        raise ValueError("detailed diagnostics support frozen E1--E4 only")
    return value


def _query_scope(suite,query_id):
    if suite!="E2":
        return "full_frozen_coordinate"
    for suffix,scope in (("auditor0","global"),("auditor1","audited_first_half"),
                         ("auditor2","audited_first_quarter"),("auditor3","outside_half")):
        if query_id.endswith("/"+suffix):
            return scope
    return "unrecognized_E2_scope"


class CellMetadata:
    def __init__(self,root,manifest,cell,mismatches):
        self.cell=cell
        self.file=Path(root)/"cell_designs"/(cell+".json.gz")
        self.content={}
        try:
            self.content=json.loads(gzip.decompress(self.file.read_bytes()))
            self.file_sha256=_file_hash(self.file)
        except (OSError,ValueError,EOFError) as exc:
            self.file_sha256=None
            mismatches.add("MISSING_OR_CORRUPT_CELL_METADATA",cell=cell,reason=str(exc)[:1000])
        meta=self.content
        if meta and meta.get("fingerprint")!=manifest["fingerprint"]:
            mismatches.add("CELL_METADATA_FINGERPRINT_MISMATCH",cell=cell)
        self.plans={}
        self.query_plans=defaultdict(list)
        for plan in meta.get("plans",[]):
            if not isinstance(plan,dict) or not isinstance(plan.get("query_id"),str):
                mismatches.add("INVALID_PLAN_METADATA",cell=cell)
                continue
            query_id=plan["query_id"]
            key=plan.get("method"),plan.get("delta"),query_id
            if key in self.plans:
                mismatches.add("DUPLICATE_PLAN_METADATA",cell=cell,method=key[0],delta=key[1],query_id=query_id)
            self.plans[key]=plan
            self.query_plans[query_id].append(plan)
        hashes=meta.get("coordinate_hashes",{})
        masses=meta.get("subgroup_masses",{})
        self.query_ids=tuple(hashes) if hashes else (tuple(masses) if masses else tuple(self.query_plans))
        self.family_size=meta.get("actual_family_size",meta.get("family_size"))
        if self.family_size is not None and len(self.query_ids)!=self.family_size:
            mismatches.add("CELL_METADATA_FAMILY_SIZE_MISMATCH",cell=cell,expected=self.family_size,observed=len(self.query_ids))
        self.raw_N=meta.get("raw_N")
        self.aliases=meta.get("aliases",{})

    def descriptor(self,suite,query_id,method,delta):
        plan=self.plans.get((method,delta,query_id),{})
        fallback=self.query_plans.get(query_id,[{}])[0]
        normalizer=plan.get("normalizer",fallback.get("normalizer"))
        known=self.content.get("known_target_ranges",{}).get(query_id)
        if known is None:
            known=(fallback.get("target_lo"),fallback.get("target_hi"))
        if not isinstance(known,(list,tuple)) or len(known)!=2:
            known=(None,None)
        lo,hi=known
        diameter=hi-lo if _finite(lo) and _finite(hi) and lo<=hi else None
        mass=self.content.get("subgroup_masses",{}).get(query_id)
        threshold=self.content.get("query_thresholds",{}).get(query_id)
        if suite=="E1" and _finite(mass):
            threshold=.4*mass
        return dict(query_id=query_id,query_scope=_query_scope(suite,query_id),normalizer=normalizer,
            declared_raw_N=self.raw_N,
            subgroup_mass=mass,known_target_lo=lo,known_target_hi=hi,known_feasible_diameter=diameter,
            threshold=threshold,active_rows=plan.get("active_rows",fallback.get("active_rows")),
            certificate_coloring_count=plan.get("color_count"),
            verified_cell_coloring_count=self.content.get("graph_colors"),plan=plan)

    def analytic_primary_truth(self,suite,query_id):
        choices=self.content.get("design_choices",{})
        original=choices.get("planted_query_id")
        primary=self.aliases.get(original,original)
        if suite=="E4" and query_id==primary and _finite(choices.get("gap")):
            return .4+choices["gap"]
        return None


def _new_query_state(descriptor):
    return dict(descriptor={key:value for key,value in descriptor.items() if key!="plan"},
        records=0,observed_records=0,status_counts=Counter(),empty_count=0,zero_diameter_count=0,
        metrics={name:NumericSamples() for name in METRICS})


def _new_group():
    return dict(independent_trials=0,observed_coordinate_records=0,expected_coordinate_records=0,
        missing_coordinates=0,duplicate_coordinates=0,unexpected_coordinates=0,status_counts=Counter(),
        empty_coordinates=0,unknown_empty_coordinates=0,missing_frames=0,
        family_coverage=BooleanCounts(),raw_family_coverage=BooleanCounts(),
        any_false_safe=BooleanCounts(),any_false_violation=BooleanCounts(),true_violation_detected=BooleanCounts(),
        family_any_nontrivial=BooleanCounts(),family_all_nontrivial=BooleanCounts(),
        metrics={name:NumericSamples() for name in TRIAL_METRICS},mismatch_start=0)


def _compare_float(mismatches,checks,context,name,observed,expected):
    if not _finite(observed) or not _finite(expected):
        checks["unknown_numeric_comparisons"]+=1
        return
    checks["numeric_comparisons"]+=1
    if not math.isclose(observed,expected,rel_tol=REL_TOL,abs_tol=ABS_TOL):
        mismatches.add("NUMERIC_FIELD_MISMATCH",**context,field=name,observed=observed,expected=expected)


def _coordinate(record,truth,descriptor,context,mismatches,checks):
    values={name:None for name in METRICS}
    status=record.get("status","MISSING_STATUS") if record else "MISSING_COORDINATE"
    certified=status==CERTIFIED
    lo,hi=(record.get("lo"),record.get("hi")) if record else (None,None)
    raw_lo,raw_hi=(record.get("raw_lo"),record.get("raw_hi")) if record else (None,None)
    endpoints=_finite(lo) and _finite(hi)
    raw_endpoints=_finite(raw_lo) and _finite(raw_hi)
    derived="joint_level" in context["method"] or "level_difference" in context["method"]
    saved_empty=record.get("empty_intersection") if record else None
    geometric_empty=lo>hi if endpoints else None
    if isinstance(saved_empty,bool) and geometric_empty is not None:
        checks["empty_flag_comparisons"]+=1
        if saved_empty!=geometric_empty:
            if derived and saved_empty and not geometric_empty:
                checks["derived_constituent_empty_not_geometrically_reconstructible"]+=1
            else:
                mismatches.add("EMPTY_FLAG_MISMATCH",**context,saved=saved_empty,recomputed=geometric_empty)
    elif certified:
        checks["unknown_empty_flag_comparisons"]+=1
    empty=bool(saved_empty is True or geometric_empty is True) if (isinstance(saved_empty,bool) or endpoints) else None
    valid=certified and endpoints and empty is False
    if certified and not endpoints:
        mismatches.add("CERTIFIED_NONFINITE_OR_MISSING_ENDPOINTS",**context)
    if certified and raw_endpoints and raw_lo>raw_hi:
        mismatches.add("REVERSED_RAW_INTERVAL",**context)
    known_lo,known_hi=descriptor["known_target_lo"],descriptor["known_target_hi"]
    if certified and raw_endpoints and _finite(known_lo) and _finite(known_hi):
        expected_lo,expected_hi=max(raw_lo,known_lo),min(raw_hi,known_hi)
        if endpoints and not derived:
            _compare_float(mismatches,checks,context,"support_intersection_lo",lo,expected_lo)
            _compare_float(mismatches,checks,context,"support_intersection_hi",hi,expected_hi)
        elif endpoints:
            checks["derived_interval_subset_checks"]+=1
            if lo<expected_lo-ABS_TOL-REL_TOL*abs(expected_lo) or hi>expected_hi+ABS_TOL+REL_TOL*abs(expected_hi):
                mismatches.add("DERIVED_INTERVAL_NOT_SUBSET_OF_RAW_AND_DIRECT_RANGE",**context)
    if _finite(truth) and _finite(known_lo) and _finite(known_hi):
        checks["truth_in_known_range_checks"]+=1
        if not known_lo<=truth<=known_hi:
            mismatches.add("TRUTH_OUTSIDE_DECLARED_TARGET_RANGE",**context,truth=truth,lo=known_lo,hi=known_hi)
    covered=(lo<=truth<=hi) if valid and _finite(truth) else (False if not valid else None)
    raw_covered=(raw_lo<=truth<=raw_hi) if certified and raw_endpoints and _finite(truth) else (False if not certified else None)
    threshold=descriptor["threshold"]
    decision=("CERTIFIED_SAFE" if hi<=threshold else "CERTIFIED_VIOLATION" if lo>threshold else "ABSTAIN") if valid and _finite(threshold) else ("ABSTAIN" if not valid else None)
    false_safe=(decision=="CERTIFIED_SAFE" and truth>threshold) if decision is not None and _finite(truth) and _finite(threshold) else None
    false_violation=(decision=="CERTIFIED_VIOLATION" and truth<=threshold) if decision is not None and _finite(truth) and _finite(threshold) else None
    detected=(decision=="CERTIFIED_VIOLATION" and truth>threshold) if decision is not None and _finite(truth) and _finite(threshold) else None
    diameter=descriptor["known_feasible_diameter"]
    nontrivial=(valid and diameter>0 and hi-lo<diameter) if _finite(diameter) else (False if not valid else None)
    if certified:
        if raw_endpoints and raw_lo<=raw_hi:
            values["raw_width"]=raw_hi-raw_lo
        if valid:
            values["intersected_width"]=hi-lo
        radius=record.get("radius")
        if _finite(radius) and radius>=0:
            values["radius"]=radius
        else:
            mismatches.add("MISSING_OR_INVALID_RADIUS",**context)
        for key,field in (("bias_piece","bias"),("concentration_piece","concentration"),("range_piece","range_contribution")):
            value=record.get(field)
            if _finite(value) and value>=0:
                values[key]=value
            else:
                mismatches.add("MISSING_OR_INVALID_RADIUS_COMPONENT",**context,field=field)
        pieces=[values[key] for key in ("bias_piece","concentration_piece","range_piece")]
        if all(value is not None for value in pieces):
            _compare_float(mismatches,checks,context,"radius_component_sum",radius,math.fsum(pieces))
        estimate=record.get("estimate")
        if _finite(estimate) and _finite(truth):
            error=estimate-truth
            values["signed_error"],values["absolute_error"]=error,abs(error)
            if _finite(radius) and radius>0:
                values["error_radius_ratio"]=abs(error)/radius
            elif radius==0:
                values["error_radius_ratio"]=0.0 if error==0 else math.inf
            for field,expected in (("signed_error",error),("absolute_error",abs(error)),("oracle_target",truth)):
                if field in record:
                    _compare_float(mismatches,checks,context,field,record[field],expected)
        elif not _finite(estimate):
            mismatches.add("MISSING_OR_NONFINITE_ESTIMATE",**context)
        if _finite(diameter) and diameter>0:
            for key,field in (("feasible_width_ratio","intersected_width"),("raw_feasible_width_ratio","raw_width")):
                if values[field] is not None:
                    values[key]=values[field]/diameter
        normalizer,mass=descriptor["normalizer"],descriptor["subgroup_mass"]
        divisor=mass if normalizer==1 else (1.0 if _finite(normalizer) and normalizer>0 else None)
        if _finite(divisor) and divisor>0:
            for key,field in (("normalized_width","intersected_width"),("normalized_radius","radius"),("normalized_absolute_error","absolute_error")):
                if values[field] is not None:
                    values[key]=values[field]/divisor
        for field,key in (("normalized_radius","normalized_radius"),("feasible_width_ratio","feasible_width_ratio")):
            if field in record:
                _compare_float(mismatches,checks,context,field,record[field],values[key])
        plan=descriptor["plan"]
        if plan and _finite(normalizer) and normalizer>0:
            for field,plan_field in (("bias","bias_piece"),("concentration","variance_piece"),("range_contribution","range_piece")):
                if _finite(plan.get(plan_field)):
                    _compare_float(mismatches,checks,context,"predeclared_"+field,record.get(field),plan[plan_field]/normalizer)
    return dict(status=status,empty=empty,covered=covered,raw_covered=raw_covered,
        false_safe=false_safe,false_violation=false_violation,detected=detected,
        nontrivial=nontrivial,decision=decision,values=values)


def _saved_checks(saved,recomputed,context,mismatches,checks):
    if not saved or saved.get("metrics_assessable",True) is False:
        checks["unassessable_saved_trial_records"]+=1
        return
    for name in ("family_covered","any_false_safe","any_false_violation","any_false_claim","true_violation_detected"):
        expected=recomputed.get(name)
        observed=saved.get(name)
        if expected is None or not isinstance(observed,bool):
            checks["unknown_boolean_comparisons"]+=1
            continue
        checks["boolean_comparisons"]+=1
        if observed!=expected:
            mismatches.add("SAVED_TRIAL_BOOLEAN_MISMATCH",**context,field=name,observed=observed,expected=expected)
    for name in ("mean_coordinate_width","candidate_nontrivial_fraction","candidate_abstention_fraction"):
        if name in saved and recomputed.get(name) is not None:
            _compare_float(mismatches,checks,context,name,saved[name],recomputed[name])


def _process_frame(suite,run_id,method,delta,frame,saved_trial,result,metadata,
                   groups,queries,mismatches,checks,*,registered=True,frame_problem=None):
    cell=run_id.split("/")[2]
    key=cell,method,delta
    group=groups.setdefault(key,_new_group())
    group["registered_group"]=registered
    group["independent_trials"]+=1
    group.setdefault("observed_N_counts",Counter())[str(result.get("raw_N","MISSING"))]+=1
    context=dict(run_id=run_id,cell=cell,method=method,delta=delta)
    coordinate_records=frame.get("coordinates",frame.get("coordinate_records",[])) if frame else []
    if not isinstance(coordinate_records,list):
        mismatches.add("INVALID_COORDINATE_RECORD_CONTAINER",**context)
        coordinate_records=[]
    if frame is None:
        group["missing_frames"]+=1
    group["observed_coordinate_records"]+=len(coordinate_records)
    by_id=defaultdict(list)
    for record in coordinate_records:
        if not isinstance(record,dict) or not isinstance(record.get("query_id"),str):
            mismatches.add("MISSING_OR_INVALID_COORDINATE_ID",**context)
        else:
            by_id[record["query_id"]].append(record)
    query_ids=metadata.query_ids
    verified_identity=bool(query_ids)
    if not query_ids:
        query_ids=tuple(result.get("truths",{})) or tuple(by_id)
        checks["frames_without_verified_family_identity"]+=1
    expected=set(query_ids)
    group["expected_coordinate_records"]+=len(expected)
    unexpected=set(by_id)-expected
    group["unexpected_coordinates"]+=sum(len(by_id[query_id]) for query_id in unexpected)
    for query_id in sorted(unexpected):
        mismatches.add("UNEXPECTED_COORDINATE_ID",**context,query_id=query_id,record_count=len(by_id[query_id]))
    for field,observed in (("frame_family_size",frame.get("family_size") if frame else None),
                           ("result_family_size",result.get("family_size"))):
        if observed is not None:
            checks["family_size_comparisons"]+=1
            if observed!=len(query_ids):
                mismatches.add("FAMILY_SIZE_MISMATCH",**context,field=field,observed=observed,expected=len(query_ids))
    truths=result.get("truths",{})
    if not isinstance(truths,dict):
        truths={}
        mismatches.add("INVALID_TRUTH_CONTAINER",**context)
    coordinate_results=[]
    for query_id in query_ids:
        descriptor=metadata.descriptor(suite,query_id,method,delta)
        query_key=cell,method,delta,query_id
        state=queries.setdefault(query_key,_new_query_state(descriptor))
        state["records"]+=1
        records=by_id.get(query_id,[])
        state["observed_records"]+=len(records)
        record=records[0] if len(records)==1 else None
        query_context=dict(context,query_id=query_id)
        if not records:
            group["missing_coordinates"]+=1
            if frame is not None:
                mismatches.add("MISSING_EXPECTED_COORDINATE",**query_context)
        elif len(records)>1:
            group["duplicate_coordinates"]+=len(records)-1
            mismatches.add("DUPLICATE_COORDINATE_ID",**query_context,record_count=len(records))
        truth=truths.get(query_id)
        analytic=metadata.analytic_primary_truth(suite,query_id)
        if analytic is not None:
            checks["analytic_primary_truth_checks"]+=1
            if not _finite(truth) or truth!=analytic:
                mismatches.add("ANALYTIC_PRIMARY_TRUTH_MISMATCH",**query_context,stored=truth,analytic=analytic)
            truth=analytic
        if not _finite(truth):
            checks["coordinates_with_missing_or_nonfinite_truth"]+=1
            truth=None
        item=_coordinate(record,truth,descriptor,query_context,mismatches,checks)
        if len(records)>1:
            item["status"]="DUPLICATE_COORDINATE"
        elif frame is None:
            item["status"]=frame_problem or "MISSING_METHOD_LEVEL_FRAME"
        state["status_counts"][item["status"]]+=1
        group["status_counts"][item["status"]]+=1
        checks["expected_coordinate_outcomes"]+=1
        if item["empty"] is True:
            state["empty_count"]+=1
            group["empty_coordinates"]+=1
        elif item["empty"] is None:
            group["unknown_empty_coordinates"]+=1
        state["zero_diameter_count"]+=descriptor["known_feasible_diameter"]==0
        for name,value in item["values"].items():
            state["metrics"][name].add(value)
        if frame:
            saved_decision=frame.get("decisions",{}).get(query_id) if isinstance(frame.get("decisions"),dict) else None
            if item["decision"] is not None and saved_decision is not None:
                checks["decision_comparisons"]+=1
                if saved_decision!=item["decision"]:
                    mismatches.add("SAVED_DECISION_MISMATCH",**query_context,observed=saved_decision,expected=item["decision"])
            else:
                checks["unknown_decision_comparisons"]+=1
        if record and "threshold" in record:
            _compare_float(mismatches,checks,query_context,"threshold",record["threshold"],descriptor["threshold"])
        coordinate_results.append(item)
    complete_identity=verified_identity and not unexpected and all(len(by_id.get(query_id,[]))==1 for query_id in query_ids)
    geometric_covered=_all([item["covered"] for item in coordinate_results]) if coordinate_results else None
    covered=False if frame is None or not complete_identity or result.get("full_family_failure",False) else geometric_covered
    if not verified_identity and frame is not None:
        covered=None
    group["family_coverage"].add(covered)
    group["raw_family_coverage"].add(_all([item["raw_covered"] for item in coordinate_results]) if coordinate_results else None)
    unassessable=bool(result.get("unassessable_whole_trial",False))
    safe=None if unassessable else _any([item["false_safe"] for item in coordinate_results]) if coordinate_results else None
    violate=None if unassessable else _any([item["false_violation"] for item in coordinate_results]) if coordinate_results else None
    detected=None if unassessable else _any([item["detected"] for item in coordinate_results]) if coordinate_results else None
    group["any_false_safe"].add(safe)
    group["any_false_violation"].add(violate)
    group["true_violation_detected"].add(detected)
    nontrivial=[item["nontrivial"] for item in coordinate_results]
    group["family_any_nontrivial"].add(_any(nontrivial) if nontrivial else None)
    group["family_all_nontrivial"].add(_all(nontrivial) if nontrivial else None)
    ratios=[item["values"]["error_radius_ratio"] for item in coordinate_results]
    max_ratio=max(ratios) if ratios and all(value is not None for value in ratios) else None
    group["metrics"]["trial_max_error_radius_ratio"].add(max_ratio)
    widths=[item["values"]["intersected_width"] for item in coordinate_results]
    normalized=[item["values"]["normalized_width"] for item in coordinate_results]
    mean_width=math.fsum(widths)/len(widths) if widths and all(value is not None for value in widths) else None
    normalized_mean=math.fsum(normalized)/len(normalized) if normalized and all(value is not None for value in normalized) else None
    group["metrics"]["trial_mean_intersected_width"].add(mean_width)
    group["metrics"]["trial_mean_normalized_width"].add(normalized_mean)
    recomputed=dict(family_covered=covered,any_false_safe=safe,any_false_violation=violate,
        any_false_claim=_any([safe,violate]),true_violation_detected=detected,mean_coordinate_width=mean_width,
        candidate_nontrivial_fraction=math.fsum(nontrivial)/len(nontrivial)
            if nontrivial and all(value is not None for value in nontrivial) else None,
        candidate_abstention_fraction=sum(item["decision"]=="ABSTAIN" for item in coordinate_results)/len(coordinate_results)
            if coordinate_results and all(item["decision"] is not None for item in coordinate_results) else None)
    _saved_checks(saved_trial,recomputed,context,mismatches,checks)


def _csv_bytes(rows,*,query=False):
    columns=["suite","cell","method","delta","query_id","query_scope","registered_group",
        "independent_trials","records","observed_records","declared_raw_N","normalizer","subgroup_mass",
        "known_target_lo","known_target_hi","known_feasible_diameter","threshold","active_rows",
        "certificate_coloring_count","verified_cell_coloring_count","empty_count","zero_diameter_count",
        "observed_coordinate_records","expected_coordinate_records","missing_coordinates",
        "duplicate_coordinates","unexpected_coordinates","empty_coordinates","unknown_empty_coordinates",
        "missing_frames","status_counts","observed_N_counts"]
    booleans=("family_coverage","raw_family_coverage","any_false_safe","any_false_violation",
              "true_violation_detected","family_any_nontrivial","family_all_nontrivial")
    for name in booleans:
        columns.extend(name+"_"+field for field in ("hits","denominator","unknown_trials","rate"))
    names=METRICS if query else METRICS+TRIAL_METRICS
    for name in names:
        columns.extend(name+"_"+field for field in ("n","undefined_count","positive_infinite_count",
            "median","q25","q75","iqr","p90","max","finite_max"))
    stream=io.StringIO(newline="")
    writer=csv.DictWriter(stream,fieldnames=columns)
    writer.writeheader()
    for row in rows:
        flat={key:row.get(key) for key in columns if key in row}
        for name in ("status_counts","observed_N_counts"):
            if name in flat:
                flat[name]=json.dumps(flat[name],sort_keys=True,separators=(",",":"))
        for name in booleans:
            if name in row:
                for field in ("hits","denominator","unknown_trials","rate"):
                    flat[name+"_"+field]=row[name][field]
        for name,value in row["metrics"].items():
            for field in ("n","undefined_count","positive_infinite_count","median","q25","q75","iqr","p90","max","finite_max"):
                flat[name+"_"+field]=value[field]
        writer.writerow(flat)
    return stream.getvalue().encode("utf-8")


def detailed_diagnostics(protocol_path,results_root,output_directory):
    """Load each planned checkpoint once and retain only numeric sample arrays."""
    protocol_path,root,output=Path(protocol_path),Path(results_root),Path(output_directory)
    if any((output/name).exists() for name in OUTPUTS):
        raise FileExistsError("detailed diagnostics are immutable; choose a new output directory")
    manifest=json.loads(protocol_path.read_text())
    config=manifest["config"]
    suite=_suite(config)
    store=CheckpointStore(root,manifest)
    methods=defaultdict(list)
    for cell,method in config["primary_comparisons"]:
        if method not in methods[cell]:
            methods[cell].append(method)
    levels=tuple(config["levels"])
    groups,queries,metadata_cache={},{},{}
    checks=Counter()
    completed,verified,missing,corrupt=[],[],[],[]
    checkpoint_statuses=Counter()
    inventory=hashlib.sha256()
    mismatches=MismatchLog(output)
    try:
        for run_id in sorted(store.planned):
            checks["checkpoint_load_calls"]+=1
            try:
                payload=store.load(run_id)
            except (OSError,ValueError,KeyError,EOFError) as exc:
                corrupt.append(run_id)
                completed.append(run_id)
                mismatches.add("CORRUPT_CHECKPOINT",run_id=run_id,reason=str(exc)[:1000])
                payload=dict(run_id=run_id,result=dict(status="CORRUPT_CHECKPOINT",cell=run_id.split("/")[2],
                    full_family_failure=True,unassessable_whole_trial=True,trials=[],certificate_records=[]))
                inventory.update((run_id+":CORRUPT\n").encode())
            else:
                if payload is None:
                    missing.append(run_id)
                    continue
                verified.append(run_id)
                completed.append(run_id)
                inventory.update((run_id+":"+digest(payload)+"\n").encode())
            result=payload["result"]
            cell=run_id.split("/")[2]
            if run_id.split("/")[1]!=suite or result.get("cell",cell)!=cell:
                mismatches.add("CHECKPOINT_SUITE_OR_CELL_MISMATCH",run_id=run_id,cell=cell)
            checkpoint_statuses[result.get("status","MISSING_STATUS")]+=1
            if cell not in metadata_cache:
                metadata_cache[cell]=CellMetadata(root,manifest,cell,mismatches)
            metadata=metadata_cache[cell]
            for field,expected in (("raw_N",metadata.raw_N),("config_N",config.get("N"))):
                if result.get("raw_N") is not None and expected is not None:
                    checks["actual_N_comparisons"]+=1
                    if result["raw_N"]!=expected:
                        mismatches.add("ACTUAL_N_MISMATCH",run_id=run_id,cell=cell,field=field,
                                       observed=result["raw_N"],expected=expected)
                elif field=="raw_N":
                    checks["units_with_unknown_actual_N"]+=1
            frames=result.get("certificate_records",result.get("coordinate_records",[]))
            trials=result.get("trials",[])
            if not isinstance(frames,list):
                mismatches.add("INVALID_FRAME_CONTAINER",run_id=run_id,cell=cell)
                frames=[]
            if not isinstance(trials,list):
                mismatches.add("INVALID_TRIAL_CONTAINER",run_id=run_id,cell=cell)
                trials=[]
            by_frame,by_trial=defaultdict(list),defaultdict(list)
            for record in frames:
                if not isinstance(record,dict) or not isinstance(record.get("method"),str):
                    mismatches.add("MISSING_FRAME_GROUP_FIELDS",run_id=run_id,cell=cell)
                    continue
                delta=record.get("delta")
                if not _finite(delta) or not 0<delta<1:
                    mismatches.add("INVALID_FRAME_DELTA",run_id=run_id,cell=cell,method=record["method"])
                    delta=None
                by_frame[(record["method"],delta)].append(record)
            for record in trials:
                if isinstance(record,dict):
                    by_trial[(record.get("method"),record.get("delta"))].append(record)
                    if record.get("run_id")!=run_id or record.get("cell")!=cell:
                        mismatches.add("SAVED_TRIAL_IDENTITY_MISMATCH",run_id=run_id,cell=cell,
                            method=record.get("method"),delta=record.get("delta"))
            expected={(method,delta) for method in methods.get(cell,()) for delta in levels}
            if not expected:
                mismatches.add("UNREGISTERED_CELL",run_id=run_id,cell=cell)
            keys=expected|set(by_frame)
            for method,delta in sorted(keys,key=lambda value:(str(value[0]),str(value[1]))):
                observed=by_frame.get((method,delta),[])
                if (method,delta) not in expected:
                    mismatches.add("UNREGISTERED_METHOD_LEVEL",run_id=run_id,cell=cell,method=method,delta=delta)
                if len(observed)>1:
                    mismatches.add("DUPLICATE_METHOD_LEVEL_FRAME",run_id=run_id,cell=cell,method=method,delta=delta,count=len(observed))
                trial_rows=by_trial.get((method,delta),[])
                if len(trial_rows)>1:
                    mismatches.add("DUPLICATE_SAVED_TRIAL_RECORD",run_id=run_id,cell=cell,method=method,delta=delta,count=len(trial_rows))
                _process_frame(suite,run_id,method,delta,observed[0] if len(observed)==1 else None,
                    trial_rows[0] if len(trial_rows)==1 else None,result,metadata,groups,queries,mismatches,checks,
                    registered=(method,delta) in expected,
                    frame_problem="DUPLICATE_METHOD_LEVEL_FRAME" if len(observed)>1 else "MISSING_METHOD_LEVEL_FRAME")
        query_rows=[]
        grouped_queries=defaultdict(list)
        for key,state in sorted(queries.items(),key=lambda item:(item[0][0],item[0][1],str(item[0][2]),item[0][3])):
            cell,method,delta,query_id=key
            row=dict(suite=suite,cell=cell,method=method,delta=delta,
                records=state["records"],observed_records=state["observed_records"],
                status_counts=dict(state["status_counts"]),empty_count=state["empty_count"],
                zero_diameter_count=state["zero_diameter_count"],**state["descriptor"],
                metrics={name:samples.result() for name,samples in state["metrics"].items()})
            query_rows.append(row)
            grouped_queries[key[:3]].append(state)
        group_rows=[]
        boolean_names=("family_coverage","raw_family_coverage","any_false_safe","any_false_violation",
            "true_violation_detected","family_any_nontrivial","family_all_nontrivial")
        for key,state in sorted(groups.items(),key=lambda item:(item[0][0],item[0][1],str(item[0][2]))):
            cell,method,delta=key
            pooled={name:NumericSamples() for name in METRICS}
            for query_state in grouped_queries[key]:
                for name,samples in query_state["metrics"].items():
                    pooled[name].extend(samples)
            metrics={name:samples.result() for name,samples in pooled.items()}
            metrics.update({name:samples.result() for name,samples in state["metrics"].items()})
            row=dict(suite=suite,cell=cell,method=method,delta=delta,metrics=metrics,
                **{name:value for name,value in state.items() if name not in ("metrics",)+boolean_names})
            row["status_counts"]=dict(row["status_counts"])
            row["observed_N_counts"]=dict(row["observed_N_counts"])
            row.update({name:state[name].result() for name in boolean_names})
            group_rows.append(row)
        mismatch_count=sum(mismatches.counts.values())
        status=("CHECKPOINT_INTEGRITY_ERRORS" if corrupt else "MISMATCHES_FOUND" if mismatch_count else
                "NO_COMPLETED_UNITS" if not completed else "COMPLETE_CHECKS_PASS" if not missing else "PARTIAL_CHECKS_PASS")
        summary=dict(schema="post-cstat-independent-detailed-diagnostics-v1",status=status,suite=suite,
            protocol_fingerprint=manifest["fingerprint"],completed_checkpoint_files=len(completed),
            verified_checkpoint_units=len(verified),corrupt_checkpoint_units=len(corrupt),missing_units=len(missing),
            completed_ids=completed,missing_ids=missing,corrupt_ids=corrupt,
            checkpoint_status_counts=dict(checkpoint_statuses),checked_counts=dict(checks),
            checkpoint_inventory_sha256=inventory.hexdigest(),mismatch_count=mismatch_count,
            mismatch_counts=dict(mismatches.counts),mismatch_examples=mismatches.examples,
            mismatch_records_path="mismatches.jsonl.gz",group_summaries=group_rows,query_summaries=query_rows,
            new_outcome_draws=0,legacy_new_outcome_draws=0,
            independent_unit="one complete log; methods/levels and coordinates are paired",
            numeric_scope="finite defined coordinate values only; failure/empty/undefined/infinite counts remain explicit",
            uncertainty_scope="candidate quantiles are descriptive; no candidate-level binomial or Wilson intervals",
            zero_radius_ratio_convention="error=radius=0 gives 0; nonzero error with radius=0 is positive infinite and separately counted",
            nontrivial_definition="strict width below positive known feasible diameter; zero-diameter exact coordinates counted separately",
            boolean_comparison="exact saved endpoints and exact inequalities; no tolerance in coverage or threshold decisions",
            redundant_numeric_comparison=dict(relative_tolerance=REL_TOL,absolute_tolerance=ABS_TOL,
                scope="redundant stored arithmetic only; does not alter any frozen scientific comparison"))
        mismatches.finish()
        contents={"summary.json":canonical_bytes(summary)+b"\n",
            "group_summary.csv":_csv_bytes(group_rows),"query_summary.csv":_csv_bytes(query_rows,query=True)}
        for name,content in contents.items():
            install_once(output/name,content)
        receipt=dict(schema="post-cstat-detailed-diagnostics-manifest-v1",status=status,suite=suite,
            input_protocol_path=str(protocol_path.resolve()),input_protocol_fingerprint=manifest["fingerprint"],
            input_scientific_source_hashes=manifest["sources"],
            analysis_code_sha256=_file_hash(__file__),checkpoint_inventory_sha256=inventory.hexdigest(),
            cell_metadata_sha256={cell:metadata.file_sha256 for cell,metadata in metadata_cache.items()},
            checked_counts=dict(checks),mismatch_count=mismatch_count,mismatch_counts=dict(mismatches.counts),
            mismatch_records_path="mismatches.jsonl.gz",new_outcome_draws=0,legacy_new_outcome_draws=0,
            outputs={name:_file_hash(output/name) for name in OUTPUTS if name!="manifest.json"})
        receipt["analysis_fingerprint"]=digest(receipt)
        install_once(output/"manifest.json",canonical_bytes(receipt)+b"\n")
        return summary
    except BaseException:
        if mismatches.path.exists():
            mismatches.abort()
        raise


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol",required=True,type=Path)
    parser.add_argument("--results",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args(argv)
    summary=detailed_diagnostics(args.protocol,args.results,args.output)
    print(json.dumps({name:summary[name] for name in ("status","suite","completed_checkpoint_files",
        "verified_checkpoint_units","missing_units","mismatch_count","new_outcome_draws","legacy_new_outcome_draws")},indent=2))


if __name__=="__main__":
    main()

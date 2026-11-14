"""Read-only supplementary E5 checks and baseline-versus-update endpoints.

No RNG, generator, fitted-model class or original oracle is called. Fixed X,
conditional response means and policy probabilities are reconstructed from the
version-bound model formula and saved fitted coefficients/policy rules. Saved
intervals are checked, not recomputed from observations. These diagnostics do
not replace a primary analysis or retroactively change its protocol.
"""

import argparse
from collections import Counter
import csv
from functools import lru_cache
import hashlib
import io
import itertools
import json
import math
from pathlib import Path

import numpy as np

from comet.checkpoint_store import CheckpointStore, canonical_bytes, digest, install_once
from comet.metrics import wilson


CERTIFIED = "CERTIFIED_UNDER_DECLARED_ASSUMPTIONS"
CERTIFIED_ARMS = ("independent_global", "comet_local", "generic_matched", "fixed_slice")
SUPPORTED_MODEL_SHA256 = "601ef13001966e4312f5ee21da9b7935ece7616f209f5428f169d4a01458a724"
SUPPORTED_X_SHA256 = "5aed2d11c55695415a8123b3a8277a5cfcf3ff81f09b313be1160340fd6ba921"
ENDPOINTS = ("returned", "returned_baseline", "returned_nonbaseline", "return_safe_useful",
             "return_baseline_and_safe_and_useful", "return_nonbaseline_and_safe_and_useful",
             "return_and_strict_positive_utility_gain", "return_nonbaseline_and_safe_and_strict_gain")
BOOLEAN_CHECKS = ("family_covered", "any_false_claim", "any_false_safe", "any_false_violation",
    "any_false_utility_claim", "true_violation_detected", "discovered_and_certified", "returned",
    "return_unsafe", "return_safe_useful", "return_and_infeasible", "return_and_risk_safe",
    "return_and_utility_noninferior", "return_and_service_feasible", "returned_baseline")
NUMERIC_CHECKS = ("true_utility", "utility_gain", "expected_service", "expected_capacity",
    "maximum_true_risk_violation", "oracle_best_feasible_candidate_value", "robust_slack_comparator_value",
    "discovery_best_planted_iou")


class Findings:
    def __init__(self, rtol, atol, maximum_examples):
        self.rtol, self.atol, self.maximum_examples = rtol, atol, maximum_examples
        self.comparisons, self.mismatches, self.examples = Counter(), Counter(), []

    def compare(self, field, reported, reconstructed, context):
        self.comparisons[field] += 1
        if isinstance(reconstructed, (bool, np.bool_)):
            equal = isinstance(reported, (bool, np.bool_)) and bool(reported) == bool(reconstructed)
        elif reconstructed is None:
            equal = reported is None
        elif isinstance(reconstructed, (int, float, np.number)):
            equal = (isinstance(reported, (int, float, np.number)) and not isinstance(reported, bool)
                     and math.isfinite(float(reported)) and math.isfinite(float(reconstructed))
                     and math.isclose(float(reported), float(reconstructed), rel_tol=self.rtol, abs_tol=self.atol))
        else:
            equal = reported == reconstructed
        if not equal:
            self.issue(field, dict(context, reported=reported, reconstructed=reconstructed))
        return equal

    def issue(self, field, context):
        self.mismatches[field] += 1
        if len(self.examples) < self.maximum_examples:
            self.examples.append(dict(field=field, **context))


def _sigmoid(value):
    return 1 / (1 + np.exp(-np.clip(value, -700, 700)))


@lru_cache(maxsize=4)
def _context(n, world):
    if type(n) is not int or n < 8 or world not in ("null", "mixed"):
        raise ValueError("unsupported saved E5 fixed-design context")
    u = (np.arange(n, dtype=float) + 0.5) / n
    x = np.column_stack((2*u-1, np.sin(6*np.pi*u+0.37),
                         np.cos(10*np.pi*u+0.19), np.sin(14*np.pi*u+0.73)))
    basis = np.column_stack((np.ones(n), x,
        *(x[:, left]*x[:, right] for left, right in itertools.combinations(range(4), 2))))
    planted = (x[:, 0] > -0.15) & (x[:, 1] > 0.1) & (x[:, 2] > -0.05)
    risk = 0.20 + 0.06*_sigmoid(1.3*x[:, 0]-0.8*x[:, 1]) + 0.025*x[:, 2]
    utility = 0.45 + 0.15*_sigmoid(1.2*x[:, 0]+0.8*x[:, 2]) + 0.05*x[:, 1]
    if world == "mixed":
        interaction = _sigmoid(3*np.prod(x, axis=1))
        risk = risk + 0.30*planted + 0.05*interaction
        utility = utility + 0.12*planted + 0.03*interaction
    else:
        planted = np.zeros(n, dtype=bool)
    return x, basis, risk, utility, planted


def _reconstruct_family(description, context, findings, where):
    x, basis, risk, utility, planted = context
    coefficients = description["fit_coefficients"]
    predictions = {}
    for channel in ("risk", "utility"):
        beta = np.asarray(coefficients[channel], dtype=float)
        if beta.shape != (basis.shape[1],) or not np.isfinite(beta).all():
            raise ValueError("invalid saved fitted coefficient vector")
        predictions[channel] = np.clip(basis @ beta, 0, 1)
    probabilities = {}
    for rule in description["policy_rules"]:
        policy_id = rule["policy_id"]
        if policy_id in probabilities:
            raise ValueError("duplicated saved policy ID")
        if rule["tradeoff"] is None:
            values = np.full(len(x), 0.35)
        else:
            if not math.isfinite(rule["scale"]) or rule["scale"] <= 0:
                raise ValueError("saved policy scale is not positive")
            score = (predictions["utility"]-rule["tradeoff"]*predictions["risk"]-rule["center"]) / rule["scale"]
            values = 0.05 + 0.9*_sigmoid(score+rule["intercept"])
        q = np.floor(values*2**32+0.5) / 2**32
        if not np.isfinite(q).all() or np.any(q < 0) or np.any(q > 1):
            raise ValueError("reconstructed policy is not a legal binary marginal")
        probabilities[policy_id] = q
        findings.compare("known_policy_service", description["policy_known_service"][policy_id], float(q.mean()), where)
    if "policy0" not in probabilities:
        raise ValueError("baseline policy0 absent from saved library")
    masks = {"all": np.ones(len(x), dtype=bool)}
    for rule in description["auditor_rules"]:
        mask = np.ones(len(x), dtype=bool)
        for feature, positive in rule["literals"]:
            if type(feature) is not int or not 0 <= feature < 4 or type(positive) is not bool:
                raise ValueError("unsupported saved auditor literal")
            mask &= x[:, feature] > 0 if positive else x[:, feature] <= 0
        masks[rule["rule_id"]] = mask
    aliases = description["aliases"]
    targets, risk_ids, utility_ids, subgroup_risk_ids = {}, {}, {}, set()
    for policy_id, q in probabilities.items():
        risk_ids[policy_id] = []
        for rule_id, mask in masks.items():
            if not np.any(mask):
                raise ValueError("saved family contains an empty subgroup")
            query_id = f"risk/{policy_id}/{rule_id}"
            canonical = aliases[query_id]
            value = float(np.mean(q[mask]*risk[mask]))
            if canonical in targets:
                findings.compare("aliased_target_identity", targets[canonical], value, where)
            targets[canonical] = value
            risk_ids[policy_id].append(canonical)
            if rule_id != "all":
                subgroup_risk_ids.add(canonical)
        utility_ids[policy_id] = None
        if policy_id != "policy0":
            canonical = aliases[f"utility/{policy_id}-minus-policy0"]
            value = float(np.mean((q-probabilities["policy0"])*utility))
            if canonical in targets:
                findings.compare("aliased_target_identity", targets[canonical], value, where)
            targets[canonical] = value
            utility_ids[policy_id] = canonical
    findings.compare("actual_family_size", description["actual_family_size"], len(targets), where)
    if set(aliases.values()) != set(targets):
        raise ValueError("saved aliases do not describe the reconstructed full family")
    values = {policy_id:float(np.mean(q*utility)) for policy_id, q in probabilities.items()}
    ious = [np.sum(mask & planted)/np.sum(mask | planted) for name, mask in masks.items()
            if name != "all" and np.any(mask | planted)]
    return dict(targets=targets, risk_ids=risk_ids, utility_ids=utility_ids,
        subgroup_risk_ids=subgroup_risk_ids,
        service={key:float(q.mean()) for key,q in probabilities.items()}, utility=values,
        discovery_iou=float(max(ious)) if ious else None, description=description)


def _bounds(certificates, query_id):
    value = certificates.get(query_id, {})
    lo, hi = value.get("lo"), value.get("hi")
    if (value.get("status") != CERTIFIED or value.get("empty_intersection", False)
        or lo is None or hi is None or not math.isfinite(lo) or not math.isfinite(hi) or lo > hi):
        return None
    return lo, hi


def _truth_feasibility(family, config):
    result = {}
    for policy in family["risk_ids"]:
        risk_gap = max(family["targets"][key]-config["risk_threshold"] for key in family["risk_ids"][policy])
        key = family["utility_ids"][policy]
        gain = 0.0 if key is None else family["targets"][key]
        service = family["service"][policy]
        risk_safe, utility_ok = risk_gap <= 0, gain >= -config["utility_margin"]
        service_ok = service >= config["service_floor"] and service <= config["capacity_ceiling"]
        result[policy] = dict(risk_safe=risk_safe, utility_ok=utility_ok, service_ok=service_ok,
            feasible=risk_safe and utility_ok and service_ok, gap=risk_gap, gain=gain, service=service)
    return result


def _expected_selection(family, frame, arm, config):
    if arm == "abstain_reference":
        return False, None
    if arm == "status_quo_reference":
        return True, "policy0"
    certificates = {value["query_id"]:value for value in frame.get("certificates", [])}
    estimates = frame.get("point_estimates", {})
    point = arm in ("point_constraint", "in_sample_auditing")
    if not point and set(certificates) != set(family["targets"]):
        raise ValueError("saved certified selection omits or changes its full coordinate family")
    eligible = []
    for policy in family["risk_ids"]:
        service = family["service"][policy]
        if service < config["service_floor"] or service > config["capacity_ceiling"]:
            continue
        risks = family["risk_ids"][policy]
        if point:
            if any(key not in estimates or not math.isfinite(estimates[key]) for key in risks):
                raise ValueError("missing/nonfinite saved point risk estimate")
            if any(estimates[key] > config["risk_threshold"] for key in risks):
                continue
        elif any(_bounds(certificates,key) is None or _bounds(certificates,key)[1] > config["risk_threshold"] for key in risks):
            continue
        key = family["utility_ids"][policy]
        if key is None:
            gain = 0.0
        elif point:
            if key not in estimates or not math.isfinite(estimates[key]):
                raise ValueError("missing/nonfinite point utility contrast")
            gain = estimates[key]
        else:
            if _bounds(certificates,key) is None:
                continue
            gain = _bounds(certificates,key)[0]
        if gain >= -config["utility_margin"]:
            eligible.append((gain, policy))
    chosen = min(eligible,key=lambda value:(-value[0],value[1]))[1] if eligible else None
    return chosen is not None, chosen


def _reconstruct_metrics(family, primary, frame, arm, config):
    certificates = {value["query_id"]:value for value in frame.get("certificates", [])}
    if len(certificates) != len(frame.get("certificates", [])):
        raise ValueError("duplicate saved certificate coordinate")
    targets = family["targets"]
    false_safe = false_violation = false_utility = detected = discovered = False
    point = arm in ("point_constraint", "in_sample_auditing")
    estimates = frame.get("point_estimates", {})
    if point and (set(estimates) != set(targets) or not all(math.isfinite(value) for value in estimates.values())):
        raise ValueError("point diagnostic omits or changes its full coordinate family")
    for policy, risks in family["risk_ids"].items():
        for key in risks:
            truth = targets[key]
            if point:
                if key not in estimates:
                    raise ValueError("missing point coordinate")
                false_safe |= estimates[key] <= config["risk_threshold"] < truth
                false_violation |= truth <= config["risk_threshold"] < estimates[key]
            elif _bounds(certificates,key) is not None:
                lo, hi = _bounds(certificates,key)
                false_safe |= hi <= config["risk_threshold"] < truth
                false_violation |= truth <= config["risk_threshold"] < lo
                hit = lo > config["risk_threshold"] and truth > config["risk_threshold"]
                detected |= hit
                discovered |= hit and key in family["subgroup_risk_ids"]
        key = family["utility_ids"][policy]
        if key is not None:
            lower = estimates.get(key) if point else (_bounds(certificates,key)[0] if _bounds(certificates,key) else None)
            if lower is not None:
                false_utility |= lower >= -config["utility_margin"] and targets[key] < -config["utility_margin"]
                false_utility |= lower > 0 and targets[key] <= 0
    selection = frame["selection"]
    returned = bool(selection["returned"])
    policy = selection.get("policy_id") if returned else None
    primary_feasible = _truth_feasibility(primary,config)
    if returned and policy not in primary_feasible:
        raise ValueError("saved selection returns an unknown policy")
    selected = primary_feasible.get(policy)
    covered = (set(certificates) == set(targets) and all(_bounds(certificates,key) is not None and
               _bounds(certificates,key)[0] <= truth <= _bounds(certificates,key)[1] for key,truth in targets.items()))
    robust = []
    if arm in CERTIFIED_ARMS and arm != "fixed_slice":
        for candidate, state in primary_feasible.items():
            if not state["feasible"]:
                continue
            good = True
            for key in family["risk_ids"][candidate]:
                radius = certificates.get(key,{}).get("radius")
                good &= (_bounds(certificates,key) is not None and radius is not None and math.isfinite(radius)
                         and radius >= 0 and targets[key]+2*radius <= config["risk_threshold"])
            key = family["utility_ids"][candidate]
            if key is not None:
                radius = certificates.get(key,{}).get("radius")
                good &= (_bounds(certificates,key) is not None and radius is not None and math.isfinite(radius)
                         and radius >= 0 and targets[key]-2*radius >= -config["utility_margin"])
            if good:
                robust.append(primary["utility"][candidate])
    result = dict(family_covered=bool(covered), any_false_claim=bool(false_safe or false_violation or false_utility),
        any_false_safe=bool(false_safe), any_false_violation=bool(false_violation),
        any_false_utility_claim=bool(false_utility), true_violation_detected=bool(detected),
        discovered_and_certified=bool(discovered), returned=returned,
        returned_baseline=returned and policy == "policy0",
        return_unsafe=bool(returned and not selected["risk_safe"]),
        return_safe_useful=bool(returned and selected["feasible"]),
        return_and_infeasible=bool(returned and not selected["feasible"]),
        return_and_risk_safe=bool(returned and selected["risk_safe"]),
        return_and_utility_noninferior=bool(returned and selected["utility_ok"]),
        return_and_service_feasible=bool(returned and selected["service_ok"]),
        true_utility=primary["utility"][policy] if returned else None,
        utility_gain=selected["gain"] if returned else None,
        expected_service=selected["service"] if returned else 0.0,
        expected_capacity=selected["service"] if returned else 0.0,
        maximum_true_risk_violation=max(0.0,selected["gap"]) if returned else None,
        oracle_best_feasible_candidate_value=max((primary["utility"][key] for key,state in primary_feasible.items() if state["feasible"]),default=None),
        robust_slack_comparator_value=max(robust,default=None),
        discovery_best_planted_iou=family["discovery_iou"])
    return result


class DataBudget:
    def __init__(self, config):
        self.sizes = config["split_sizes"]
        self.units = self.reported_total = self.reported_total_units = 0
        self.rows, self.row_units, self.exposed, self.exposed_units = Counter(), Counter(), Counter(), Counter()
        self.raw_verified = Counter()

    def add(self, result, findings, where):
        self.units += 1
        sizes = result.get("split_sizes", {})
        exposed = result.get("exposed_labels", {})
        raw = result.get("raw_debug", {})
        total = result.get("total_rows")
        if isinstance(total, int) and total >= 0:
            self.reported_total += total
            self.reported_total_units += 1
            findings.compare("total_rows", total, sum(self.sizes.values()), where)
        for name, expected in self.sizes.items():
            n, labels = sizes.get(name), exposed.get(name)
            actions = raw.get(name, {}).get("actions")
            if actions is not None:
                values = np.asarray(actions, dtype=float)
                if values.ndim == 1 and np.isfinite(values).all() and np.all((values == 0) | (values == 1)):
                    self.raw_verified[name] += 1
                    if n is not None:
                        findings.compare("raw_split_rows", n, len(values), dict(where, split=name))
                    else:
                        n = len(values)
                    if labels is not None:
                        findings.compare("raw_exposed_labels", labels, int(values.sum()), dict(where, split=name))
                    else:
                        labels = int(values.sum())
                else:
                    findings.issue("invalid_raw_actions", dict(where, split=name))
            if isinstance(n, int) and n >= 0:
                self.rows[name] += n
                self.row_units[name] += 1
                findings.compare("split_rows", n, expected, dict(where, split=name))
            if isinstance(labels, int) and labels >= 0 and labels <= (n if isinstance(n,int) else expected):
                self.exposed[name] += labels
                self.exposed_units[name] += 1
            elif labels is not None:
                findings.issue("invalid_exposed_label_count", dict(where, split=name, reported=labels))

    def result(self, arms):
        return dict(complete_checkpoint_trial_ids=self.units,
            allocated_rows_per_trial=dict(self.sizes),
            allocated_rows_for_checkpoint_ids={key:value*self.units for key,value in self.sizes.items()},
            allocated_total_rows_for_checkpoint_ids=sum(self.sizes.values())*self.units,
            reported_generated_total_rows=dict(known_sum=self.reported_total,
                known_trial_ids=self.reported_total_units, unknown_trial_ids=self.units-self.reported_total_units),
            generated_split_rows={name:dict(known_sum=self.rows[name], known_trial_ids=self.row_units[name],
                unknown_trial_ids=self.units-self.row_units[name]) for name in self.sizes},
            exposed_units_by_split={name:dict(known_sum=self.exposed[name], known_trial_ids=self.exposed_units[name],
                unknown_trial_ids=self.units-self.exposed_units[name],
                observed_risk_and_utility_channel_values=2*self.exposed[name]) for name in self.sizes},
            raw_debug_verified_trial_counts=dict(self.raw_verified),
            allocation_shared_by_arms=list(arms),
            counted_once="one training/discovery/certification log triple per complete trial ID; never times arms, levels or family size",
            in_sample_accounting="in_sample_auditing reuses certification labels for search and point decisions; it does not receive another independent certification sample",
            interpretation="allocated counts include failed trial IDs; generated/exposed counts are only reported or raw-debug-verified data, with unknowns retained",
            limit="saved aggregate data provenance cannot independently prove which arrays every engine consumed")


def _supported_model(manifest, fixture):
    if fixture:
        return True, "deterministic_fixture_no_production_provenance_claim"
    expected = {"experiments/pipeline_dgp.py":SUPPORTED_MODEL_SHA256,
                "experiments/core_graph_dgp.py":SUPPORTED_X_SHA256}
    for suffix, value in expected.items():
        matching = [actual for path, actual in manifest["sources"].items() if Path(path).as_posix().endswith(suffix)]
        if matching != [value]:
            return False, "unsupported frozen model/X hash; supplementary endpoints use reported assessable metrics only"
    return True, "supported frozen model and fixed-X source hashes"


def _endpoint_values(metrics, selection):
    returned = bool(metrics["returned"])
    baseline = returned and selection.get("policy_id") == "policy0"
    nonbaseline = returned and not baseline
    useful = bool(metrics["return_safe_useful"])
    gain = metrics.get("utility_gain")
    positive = returned and gain is not None and math.isfinite(gain) and gain > 0
    return dict(returned=returned, returned_baseline=baseline, returned_nonbaseline=nonbaseline,
        return_safe_useful=useful, return_baseline_and_safe_and_useful=baseline and useful,
        return_nonbaseline_and_safe_and_useful=nonbaseline and useful,
        return_and_strict_positive_utility_gain=bool(positive),
        return_nonbaseline_and_safe_and_strict_gain=bool(nonbaseline and useful and positive))


def _endpoint_summary(state):
    n = state["units"]
    values = {}
    for event in ENDPOINTS:
        hits, unknown = state["hits"][event], state["unknown"][event]
        values[event] = dict(hits=hits, denominator=n, unknown_trials=unknown,
            rate=hits/n if not unknown else None,
            wilson95=list(wilson(hits,n)) if not unknown else None,
            realized_frequency_bounds=[hits/n,(hits+unknown)/n])
    return values


def diagnose_pipeline(protocol_path, results_root, output_directory, *, rtol=5e-12,
                      atol=5e-13, maximum_examples=10):
    """Read each saved complete trial once, reconstructing conditional truths.

    Reported endpoints are never changed in place. On the supported model,
    supplementary endpoints use independently reconstructed truths and the
    actually saved selection, including when a reported boolean disagrees.
    Failed/missing/unreconstructable frames remain unknown in all denominators.
    """
    output = Path(output_directory)
    if any((output/name).exists() for name in ("diagnostics.json", "endpoint_rates.csv", "manifest.json")):
        raise FileExistsError("read-only diagnostics require a fresh output directory")
    if rtol < 0 or atol < 0 or maximum_examples < 0:
        raise ValueError("nonnegative explicit comparison tolerances and example bound required")
    manifest = json.loads(Path(protocol_path).read_text())
    config = manifest["config"]
    fixture = config.get("suite") == "DETERMINISTIC_PIPELINE_FIXTURE"
    if config.get("suite") not in ("E5", "DETERMINISTIC_PIPELINE_FIXTURE"):
        raise ValueError("these supplemental diagnostics implement the E5 synthetic pipeline only")
    store = CheckpointStore(results_root,manifest)
    supported, model_scope = _supported_model(manifest,fixture)
    findings = Findings(rtol,atol,maximum_examples)
    budget = DataBudget(config)
    groups, inventory, completed = {}, [], set()
    reconstructions, record_sources, unit_statuses = Counter(), Counter(), Counter()
    for payload in store.iter_completed():
        run_id, result = payload["run_id"], payload["result"]
        pieces = run_id.split("/")
        if pieces[1] != "E5":
            raise ValueError("a non-E5 checkpoint entered E5 supplementary analysis")
        cell, where = pieces[2], dict(run_id=run_id)
        completed.add(run_id)
        inventory.append([run_id,digest(payload)])
        unit_statuses[result.get("status","UNKNOWN")] += 1
        budget.add(result,findings,where)
        expected = {(arm,float(delta)) for arm in config["arms"] for delta in config["levels"]}
        rows, frames, duplicated = {}, {}, set()
        for row in result.get("trials",[]):
            key = row.get("method"),row.get("delta")
            if key not in expected or row.get("run_id") != run_id or row.get("cell") != cell:
                findings.issue("invalid_trial_frame_identity",where)
                continue
            if key in rows:
                duplicated.add(key)
            rows[key]=row
        for frame in result.get("certificate_records",[]):
            key=frame.get("method"),frame.get("delta")
            if key not in expected or key in frames:
                duplicated.add(key)
                findings.issue("duplicate_or_unknown_certificate_frame",where)
                continue
            frames[key]=frame
        reconstructed={}
        if supported and not result.get("unassessable_whole_trial",False):
            for name in ("proper_family","fixed_slice_family","in_sample_family"):
                try:
                    reconstructed[name]=_reconstruct_family(result[name],
                        _context(config["split_sizes"]["certification"],cell.rsplit("-",1)[1]),findings,dict(where,family=name))
                    reconstructions["families_reconstructed"]+=1
                except (KeyError,ValueError,TypeError) as exc:
                    reconstructions["families_unreconstructable"]+=1
                    findings.issue("family_reconstruction_unavailable",dict(where,family=name,reason=str(exc)[:300]))
        for arm,delta in sorted(expected):
            context=dict(where,method=arm,delta=delta)
            state=groups.setdefault((cell,arm,delta),dict(units=0,hits=Counter(),unknown=Counter(),sources=Counter()))
            state["units"]+=1
            row,frame=rows.get((arm,delta)),frames.get((arm,delta))
            values=None
            source="unknown_failed_or_missing_frame"
            assessable=(row is not None and frame is not None and (arm,delta) not in duplicated
                and row.get("metrics_assessable") is True and not result.get("unassessable_whole_trial",False))
            if assessable:
                if supported:
                    try:
                        family_name=("fixed_slice_family" if arm=="fixed_slice" else
                                     "in_sample_family" if arm=="in_sample_auditing" else "proper_family")
                        family,primary=reconstructed[family_name],reconstructed["proper_family"]
                        if frame["family_digest"] != family["description"]["family_digest"]:
                            raise ValueError("saved interval frame belongs to a different family")
                        findings.compare("frame_actual_family_size",frame.get("actual_family_size"),len(family["targets"]),context)
                        if arm in CERTIFIED_ARMS:
                            findings.compare("coordinate_failure_allocation",frame.get("coordinate_allocation"),delta/len(family["targets"]),context)
                        expected_return,expected_id=_expected_selection(family,frame,arm,config)
                        findings.compare("selection_returned",frame["selection"].get("returned"),expected_return,context)
                        findings.compare("selection_policy_id",frame["selection"].get("policy_id"),expected_id,context)
                        metrics=_reconstruct_metrics(family,primary,frame,arm,config)
                        for key in BOOLEAN_CHECKS+NUMERIC_CHECKS:
                            if key not in row:
                                findings.issue("missing_reported_metric",dict(context,metric=key))
                            else:
                                findings.compare(key,row[key],metrics[key],context)
                        values=_endpoint_values(metrics,frame["selection"])
                        source="independently_reconstructed_conditional_truth_and_saved_selection"
                        reconstructions["frames_reconstructed"]+=1
                    except (KeyError,ValueError,TypeError) as exc:
                        reconstructions["frames_unreconstructable"]+=1
                        findings.issue("frame_reconstruction_unavailable",dict(context,reason=str(exc)[:300]))
                else:
                    if all(key in row for key in ("returned","return_safe_useful","utility_gain")):
                        values=_endpoint_values(row,frame["selection"])
                        source="reported_assessable_metrics_unverified_model_version"
            state["sources"][source]+=1
            record_sources[source]+=1
            for endpoint in ENDPOINTS:
                if values is None:
                    state["unknown"][endpoint]+=1
                else:
                    state["hits"][endpoint]+=bool(values[endpoint])
    remaining=sorted(store.planned-completed)
    rows=[dict(cell=cell,method=arm,delta=delta,independent_trials=state["units"],
               endpoint_sources=dict(state["sources"]),endpoints=_endpoint_summary(state))
          for (cell,arm,delta),state in sorted(groups.items())]
    if not completed:
        verification="NO_COMPLETED_UNITS"
    elif not supported:
        verification="UNSUPPORTED_MODEL_REPORTED_ONLY"
    elif findings.mismatches:
        verification="DISCREPANCIES_OR_UNVERIFIABLE_RECORDS"
    elif record_sources["unknown_failed_or_missing_frame"]:
        verification="RECONSTRUCTED_ASSESSABLE_RECORDS_WITH_UNKNOWNS"
    else:
        verification="RECONSTRUCTED_RECORDS_MATCH"
    report=dict(schema="COMET-E5-supplementary-diagnostics-v1",suite="E5",
        status="NO_COMPLETED_UNITS" if not completed else ("PARTIAL" if remaining else "COMPLETE"),
        phase="DETERMINISTIC_FIXTURE_NOT_SCIENCE" if fixture else "posthoc_descriptive_read_only",
        completed_units=len(completed),remaining_units=len(remaining),remaining_ids=remaining,
        checkpoint_inventory_sha256=digest(inventory),protocol_fingerprint=manifest["fingerprint"],
        verification_status=verification,model_reconstruction_scope=model_scope,
        comparison_tolerances=dict(rtol=rtol,atol=atol),
        verification=dict(comparisons=dict(findings.comparisons),mismatches=dict(findings.mismatches),
            bounded_examples=findings.examples,reconstruction_counts=dict(reconstructions)),
        supplementary_endpoint_definitions=dict(
            return_nonbaseline_and_safe_and_useful="returned policy differs from policy0 AND satisfies all true primary risk, utility-NI and service/capacity conditions",
            return_and_strict_positive_utility_gain="returned policy true utility is strictly greater than policy0, regardless of safety",
            baseline_return="reported separately; baseline utility noninferiority is not a policy-repair improvement"),
        summaries=rows,data_budget=budget.result(config["arms"]),checkpoint_status_counts=dict(unit_statuses),
        primary_families_modified=False,primary_tests_added=0,new_scientific_units=0,legacy_new_outcome_draws=0,
        original_oracle_called=False,observations_regenerated=False,
        uncertainty="pointwise Wilson95 per fixed cell/arm/level with complete independent trial denominator; unknown rates/intervals are null",
        verification_limits=[
            "reconstructs saved learned policies/conditional targets for the supported fixed model; does not refit nuisances or replay any random source",
            "checks saved endpoints, decisions and feasibility; does not recompute interval arithmetic, prove assumptions from schema, or validate every saved observation",
            "data accounting uses saved per-trial row/exposure metadata, checked against raw debug where available; no multiplication by arms, levels or candidates",
            "supplementary posthoc repair/strict-gain endpoints do not replace frozen primary outcomes or turn Monte Carlo intervals into certificate guarantees"])
    text=canonical_bytes(report)+b"\n"
    buffer=io.StringIO(newline="")
    writer=csv.DictWriter(buffer,fieldnames=("cell","method","delta","independent_trials","endpoint","hits","denominator","unknown_trials","rate","wilson95_lo","wilson95_hi"))
    writer.writeheader()
    for row in rows:
        for endpoint,value in row["endpoints"].items():
            ci=value["wilson95"] or [None,None]
            writer.writerow(dict(cell=row["cell"],method=row["method"],delta=row["delta"],independent_trials=row["independent_trials"],
                endpoint=endpoint,**{key:value[key] for key in ("hits","denominator","unknown_trials","rate")},
                wilson95_lo=ci[0],wilson95_hi=ci[1]))
    csv_content=buffer.getvalue().encode()
    receipt=dict(schema="E5-supplementary-diagnostic-manifest-v1",protocol_fingerprint=manifest["fingerprint"],
        diagnostic_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),new_scientific_units=0,
        primary_families_modified=False,outputs={"diagnostics.json":hashlib.sha256(text).hexdigest(),
            "endpoint_rates.csv":hashlib.sha256(csv_content).hexdigest()})
    receipt["fingerprint"]=digest(receipt)
    install_once(output/"diagnostics.json",text)
    install_once(output/"endpoint_rates.csv",csv_content)
    install_once(output/"manifest.json",canonical_bytes(receipt)+b"\n")
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol",type=Path,required=True)
    parser.add_argument("--results",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args(argv)
    report=diagnose_pipeline(args.protocol,args.results,args.output)
    print(json.dumps({key:report[key] for key in ("status","completed_units","remaining_units","verification_status","new_scientific_units")},indent=2))


if __name__=="__main__":
    main()

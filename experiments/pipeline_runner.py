"""Frozen E5 discovery--certification--update execution and whole-trial analysis.

One immutable checkpoint is one source-separated training/discovery/certification
trial. All arms and both confidence levels share its three logs. Diagnostic
point selectors are separate HEURISTIC paths; no uncertified reference is
silently promoted to a certified safe fallback. Execution is synchronous.
"""

import argparse
from collections import Counter, OrderedDict, defaultdict
from dataclasses import replace
import hashlib
import itertools
import json
import math
from pathlib import Path
import shlex
import subprocess
import time
from types import MappingProxyType

import numpy as np

from comet.audit_pipeline import freeze_discovered_family
from comet.checkpoint_store import (CheckpointStore, NAMESPACE, canonical_bytes,
    digest, freeze_protocol, install_once, planning_input_hashes)
from comet.policy_update import PolicyCandidate, select_policy
from comet.post_cstat_statistics import (EVENTS, WholeTrialSummary,
    adjust_validity_family, paired_endpoint_difference)
from comet.queries import SignedQuery
from comet.residual_truncation import CERTIFIED, make_plan
from experiments.pipeline_dgp import (AuditorRule, SPLIT_SIZES, TRADEOFF_GRID,
    build_pipeline_design, draw_pipeline_split, evaluate_pipeline,
    fit_and_freeze_pipeline, pipeline_trial_record)
from experiments.post_cstat_runner import (GIB, LEVELS, REPOSITORY, SOURCE_NAMES,
    ResourceLimitError, _resource_check, _source_stamps, _verify_changed_sources,
    resource_snapshot, environment_signature)


ARMS = ("point_constraint", "in_sample_auditing", "independent_global",
        "comet_local", "generic_matched", "fixed_slice",
        "abstain_reference", "status_quo_reference")
CERTIFIED_ARMS = ("independent_global", "comet_local", "generic_matched", "fixed_slice")
EXTRA_SOURCES = ("comet/audit_pipeline.py", "comet/policy_update.py",
                 "experiments/pipeline_dgp.py", "experiments/pipeline_runner.py")
BOOLEAN_EXTRAS = ("return_and_infeasible", "return_and_risk_safe",
    "return_and_utility_noninferior", "return_and_service_feasible",
    "any_false_utility_claim", "returned_baseline")
NUMERIC_EXTRAS = ("true_utility", "utility_gain", "expected_service", "expected_capacity",
    "maximum_true_risk_violation", "oracle_best_feasible_candidate_value",
    "robust_slack_comparator_value", "discovery_best_planted_iou")


def pipeline_cell_ids():
    return [f"{graph}-{overlap}-{world}" for graph, overlap, world in itertools.product(
        ("independent", "cycle"), ("moderate", "weak"), ("null", "mixed"))]


def planned_pipeline_ids():
    return [f"{NAMESPACE}/E5/{cell}/{rep:04d}" for cell in pipeline_cell_ids() for rep in range(500)]


def primary_pipeline_comparisons():
    return [[cell, arm] for cell in pipeline_cell_ids() for arm in CERTIFIED_ARMS]


def _validate_config(config):
    required = ("master_seed", "seed_domain", "truncation_multipliers", "truncation_grid_source",
        "planning_inputs_reconciled", "theorem_status", "numerical_guard", "raw_debug_run_ids",
        "analysis_bootstrap_seed", "analysis_bootstrap_resamples")
    if any(key not in config for key in required):
        raise ValueError("explicit E5 configuration required: " + ", ".join(required))
    if config["truncation_multipliers"] != [2 ** (j / 4) for j in range(-24, 25)]:
        raise ValueError("E5 uses the reconciled 49-point THEORY_NOTE grid 2^(j/4)")
    if not config["truncation_grid_source"] or config["planning_inputs_reconciled"] is not True:
        raise ValueError("record reconciled planning inputs and truncation grid provenance")
    if config["theorem_status"] != "PROVED_UNDER_DECLARED_ASSUMPTIONS":
        raise ValueError("certified E5 engines require completed core proofs")
    if "production_environment" in config and config["production_environment"] != environment_signature():
        raise ValueError("selected E5 production environment differs from the current environment")
    if any(type(config[key]) is not int or config[key] < 0 for key in ("master_seed", "analysis_bootstrap_seed")):
        raise ValueError("nonnegative explicit generation and analysis seeds required")
    if config["analysis_bootstrap_resamples"] != 2000:
        raise ValueError("production paired performance analysis uses 2000 whole-trial resamples")
    if not isinstance(config["seed_domain"], str) or not config["seed_domain"].startswith(NAMESPACE + "/E5"):
        raise ValueError("use a new E5 seed domain")
    if not isinstance(config["numerical_guard"], (int, float)) or not math.isfinite(config["numerical_guard"]) or config["numerical_guard"] < 0:
        raise ValueError("declare a finite nonnegative numerical decision padding")
    fixed = dict(namespace=NAMESPACE, suite="E5", workers=1, cells=pipeline_cell_ids(),
        replications_per_cell=500, split_sizes=dict(SPLIT_SIZES), levels=list(LEVELS),
        risk_threshold=0.32, utility_margin=0.01, service_floor=0.2, capacity_ceiling=0.6,
        ridge=1.0, max_rules=4, max_depth=4, minimum_mass=0.02, tradeoff_grid=list(TRADEOFF_GRID),
        arms=list(ARMS), certified_arms=list(CERTIFIED_ARMS),
        primary_units=4000, total_primary_goal_units=29600, total_unit_cap=32000,
        legacy_new_outcome_draws=0, planned_run_ids=planned_pipeline_ids(),
        primary_comparisons=primary_pipeline_comparisons(),
        artifact_cap_bytes=int(1.5 * GIB), minimum_free_disk_bytes=2 * GIB,
        worker_memory_cap_bytes=4 * GIB,
        truncation_evaluation="THEORY_NOTE_section5_p2_kappa_argmin_on_original_full_grid",
        support_graph_cache_max_entries=32,
        family_size_rule="actual deduplicated risk AND utility coordinates after independent discovery",
        fixed_slice_evaluation="own fixed-slice family coverage; primary-discovered family return feasibility",
        global_results_root=str(REPOSITORY / "results/post_cstat"))
    for key, value in fixed.items():
        if key in config and config[key] != value:
            raise ValueError("fixed E5 design differs from pre-outcome choices: " + key)
    if not isinstance(config["raw_debug_run_ids"], list) or not set(config["raw_debug_run_ids"]) <= set(fixed["planned_run_ids"]):
        raise ValueError("raw debug IDs must be prespecified E5 IDs")
    return dict(config, **fixed)


def freeze_pipeline(config_path, input_directory, protocol_path):
    config_path = Path(config_path).resolve()
    config = _validate_config(json.loads(config_path.read_text()))
    planning_input_hashes(input_directory, allowed_missing=config.get("allowed_missing_planning_inputs", ()))
    sources = [REPOSITORY / name for name in dict.fromkeys(SOURCE_NAMES + EXTRA_SOURCES)] + [config_path]
    git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPOSITORY, text=True).strip()
    for path in sources:
        try:
            relative = path.relative_to(REPOSITORY)
        except ValueError as exc:
            raise ValueError("E5 executable config must be committed inside the repository") from exc
        if subprocess.check_output(["git", "status", "--porcelain", "--", str(relative)], cwd=REPOSITORY, text=True) or not path.is_file():
            raise ValueError("commit E5 code/config/theorem before freeze: " + str(relative))
    config.update(git_sha=git_sha,
        input_config_sha256=hashlib.sha256(config_path.read_bytes()).hexdigest(),
        equivalent_arms=[["comet_local", "generic_matched"]],
        E0_anchor="ca5bb878cf9635fac4381d03281df0bc8a900daa")
    return freeze_protocol(protocol_path, config, sources, input_directory)


def factorized_p2_grid_choice(multipliers):
    """THEORY_NOTE §5: exactly minimize the original finite design-only grid.

    For tau=c*(Vp/(chi*t))**(1/2), the common positive prefactor is
    sqrt(Vp*chi*t)/N and kappa_2(c)=1/(4c)+sqrt(2)+(2/3)c. Hence the
    minimizing c is independent of row moments, graph, support and outcomes.
    The original grid remains frozen/auditable; the core make_plan is unchanged.
    """
    factors = tuple(float(value) for value in multipliers)
    if not factors or any(not math.isfinite(value) or value <= 0 for value in factors):
        raise ValueError("a positive finite original truncation grid is required")
    return min(factors, key=lambda value:(0.25/value + math.sqrt(2) + (2/3)*value, value))


class CachedSupportGraph:
    """Cache only fixed-design induced graphs; no outcomes enter cache keys."""
    def __init__(self, graph, max_entries=32):
        if type(max_entries) is not int or max_entries < 1:
            raise ValueError("the source-support cache requires a positive entry limit")
        self.graph = graph
        self.cache = OrderedDict()
        self.max_entries = max_entries
        self.hits = self.misses = self.evictions = 0
        self.n_rows = graph.n_rows
        self.color_count = graph.color_count
        self.adjacency = graph.adjacency
        self.colors = graph.colors
        self.row_ids = graph.row_ids

    def induced(self, active):
        mask = np.asarray(active)
        if mask.shape != (self.n_rows,) or mask.dtype.kind != "b":
            raise ValueError("active_mask must contain one boolean per graph row")
        key = mask.tobytes()
        if key in self.cache:
            self.hits += 1
            self.cache.move_to_end(key)
        else:
            self.misses += 1
            if len(self.cache) >= self.max_entries:
                self.cache.popitem(last=False)
                self.evictions += 1
            self.cache[key] = self.graph.induced(mask)
        return self.cache[key]


def _rebuild_auditor_family(frozen, auditors, label):
    split = frozen.design.splits["certification"]
    masks = [("all", np.ones(split.n))] + [(rule.rule_id, rule.mask(split.x).astype(float)) for rule in auditors]
    queries, thresholds, candidates = [], {}, []
    baseline = frozen.policy_probabilities["policy0"]
    for rule in frozen.policy_rules:
        q1 = frozen.policy_probabilities[rule.policy_id]
        risk_ids = []
        for name, mask in masks:
            query_id = f"risk/{rule.policy_id}/{name}"
            queries.append(SignedQuery(query_id, np.column_stack((np.zeros(split.n), mask * q1)),
                0, channel="risk", normalizer=float(mask.mean()), provenance=label))
            risk_ids.append(query_id)
            thresholds[query_id] = frozen.design.risk_threshold
        utility_id = None
        if rule.policy_id != "policy0":
            utility_id = f"utility/{rule.policy_id}-minus-policy0"
            queries.append(SignedQuery(utility_id, np.column_stack((np.zeros(split.n), q1-baseline)),
                0, channel="utility", provenance=label))
        known = next(candidate for candidate in frozen.candidates if candidate.policy_id == rule.policy_id)
        candidates.append(PolicyCandidate(rule.policy_id, tuple(risk_ids), utility_id, known.service, known.capacity))
    family = freeze_discovered_family(queries)
    return replace(frozen, auditors=tuple(auditors), family=family, candidates=tuple(candidates),
        risk_thresholds=MappingProxyType(thresholds), pipeline_digest=digest({
            "parent": frozen.pipeline_digest, "family": family.digest, "construction": label}))


def _fixed_slice_family(frozen):
    rules = (AuditorRule(((0, True),), 0.0), AuditorRule(((1, True),), 0.0),
             AuditorRule(((2, True),), 0.0), AuditorRule(((0, True), (2, True)), 0.0))
    minimum = frozen.design.splits["certification"].n
    rules = tuple(rule for rule in rules if rule.mask(frozen.design.splits["certification"].x).sum() >= max(1, math.ceil(.02 * minimum)))
    return _rebuild_auditor_family(frozen, rules, "fixed_design_slice_baseline")


def _in_sample_family(frozen, certification_log, *, max_rules=4, max_depth=4, minimum_mass=.02):
    """Diagnostic outcome-dependent auditors; NEVER passed to make_plan/select_policy."""
    split = frozen.design.splits["certification"]
    fit = frozen.nuisance["risk"][:, 1]
    pseudo = fit + certification_log.actions / split.exposure[:, 1] * (certification_log.outcomes["risk"] - fit)
    scored = []
    for depth in range(1, max_depth + 1):
        for features in itertools.combinations(range(4), depth):
            for signs in itertools.product((False, True), repeat=depth):
                rule = AuditorRule(tuple(zip(features, signs)), 0.0)
                mask = rule.mask(split.x)
                if mask.mean() >= minimum_mass:
                    scored.append(AuditorRule(rule.literals, float(pseudo[mask].mean())))
    selected, seen = [], set()
    for rule in sorted(scored, key=lambda item: (-item.discovery_score, item.rule_id)):
        key = rule.mask(split.x).tobytes()
        if key not in seen:
            seen.add(key)
            selected.append(rule)
        if len(selected) == max_rules:
            break
    return _rebuild_auditor_family(frozen, selected, "HEURISTIC_outcome_selected_certification_auditors")


def _point_estimates(frozen, log):
    split = frozen.design.splits["certification"]
    rows = np.arange(split.n)
    estimates = {}
    for query in frozen.family.queries:
        fit = frozen.nuisance[query.channel]
        weights = np.divide(query.coefficients, split.exposure, out=np.zeros_like(query.coefficients), where=split.exposure > 0)
        residual = weights[rows, log.actions] * (log.outcomes[query.channel] - fit[rows, log.actions])
        estimates[query.query_id] = query.known_term(fit) + float(residual.mean()) / query.normalizer
    return estimates


def _point_select(frozen, estimates):
    """Explicit heuristic selector: no false certificate status or safe fallback."""
    eligible = []
    for candidate in frozen.candidates:
        if candidate.service < frozen.design.service_floor or candidate.capacity > frozen.design.capacity_ceiling:
            continue
        if any(estimates[frozen.family.canonical_id(query_id)] > frozen.risk_thresholds[query_id]
               for query_id in candidate.risk_query_ids):
            continue
        gain = 0.0 if candidate.utility_contrast_id is None else estimates[frozen.family.canonical_id(candidate.utility_contrast_id)]
        if gain >= -frozen.design.utility_margin:
            eligible.append((gain, candidate.policy_id))
    chosen = min(eligible, key=lambda value: (-value[0], value[1]))[1] if eligible else None
    return dict(status="HEURISTIC_POINT_CONSTRAINT_SELECTION", returned=chosen is not None,
                policy_id=chosen, safety_claim_certified=False)


def _certify(frozen, log, delta, method, config, hashes, graph_cache, *, factorized_grid=True):
    """The full-grid reference path remains available for deterministic audit."""
    certificates = {}
    full_grid = config["truncation_multipliers"]
    selected = hashes["p2_grid_choice"] if "p2_grid_choice" in hashes else factorized_p2_grid_choice(full_grid)
    multipliers = (selected,) if factorized_grid else full_grid
    channel_inputs = {channel: frozen.certifier_inputs(channel)
                      for channel in {query.channel for query in frozen.family.queries}}
    for inputs in channel_inputs.values():
        inputs["graph"] = graph_cache
    for query in frozen.family.queries:
        inputs = channel_inputs[query.channel]
        if inputs["p"] != 2.0:
            raise ValueError("the E5 analytic grid reduction is proved for its p=2 bounded model")
        try:
            plan = make_plan(query, **inputs, delta=delta, family_size=frozen.family.family_size,
                             multipliers=multipliers, method=method)
            certificate = plan.evaluate(log.actions, log.outcomes[query.channel],
                data_digest=log.data_digest, seed_namespace=log.seed_namespace,
                code_hash=hashes["code"], config_hash=hashes["config"], numerical_guard=config["numerical_guard"])
            # Release each outcome-free plan before constructing the next one.
            del plan
        except (ValueError, ArithmeticError) as exc:
            certificate = dict(query_id=query.query_id, status="NUMERICAL_FAILURE", reason=str(exc)[:2048],
                lo=None, hi=None, empty_intersection=True, family_size=frozen.family.family_size,
                nominal_delta=delta, coordinate_delta=delta/frozen.family.family_size,
                channel=query.channel, normalizer=query.normalizer)
        certificate["family_digest"] = frozen.family.digest
        certificates[query.query_id] = certificate
    selection = select_policy(frozen.candidates, frozen.family, certificates, frozen.risk_thresholds,
        utility_margin=frozen.design.utility_margin, service_floor=frozen.design.service_floor,
        capacity_ceiling=frozen.design.capacity_ceiling, delta=delta)
    return certificates, selection


def _family_description(frozen):
    return dict(family_digest=frozen.family.digest, pipeline_digest=frozen.pipeline_digest,
        actual_family_size=frozen.family.family_size,
        risk_coordinate_count=sum(query.channel == "risk" for query in frozen.family.queries),
        utility_coordinate_count=sum(query.channel == "utility" for query in frozen.family.queries),
        aliases=dict(frozen.family.aliases), fit_digest=frozen.fit.digest,
        fit_coefficients={channel: values.tolist() for channel, values in frozen.fit.coefficients.items()},
        auditor_rules=[dict(literals=list(rule.literals), rule_id=rule.rule_id, discovery_score=rule.discovery_score)
                       for rule in frozen.auditors],
        policy_rules=[dict(policy_id=rule.policy_id, tradeoff=rule.tradeoff, center=rule.center,
                           scale=rule.scale, intercept=rule.intercept) for rule in frozen.policy_rules],
        policy_known_service={candidate.policy_id: candidate.service for candidate in frozen.candidates},
        conditioning_scope=("HEURISTIC outcome-selected certification auditors" if any(
            query.provenance.startswith("HEURISTIC") for query in frozen.family.queries)
            else "independent training/discovery or fixed auditors plus fixed evaluation contexts"),
        source_separation=dict(frozen.design.source_separation))


def _diagnostic_claim_metrics(metrics, frozen, estimates):
    false_safe = false_violation = false_utility = False
    for candidate in frozen.candidates:
        for query_id in candidate.risk_query_ids:
            coordinate = frozen.family.canonical_id(query_id)
            truth, point = metrics["targets"][coordinate], estimates[coordinate]
            threshold = frozen.risk_thresholds[query_id]
            false_safe |= point <= threshold < truth
            false_violation |= truth <= threshold < point
        if candidate.utility_contrast_id is not None:
            coordinate = frozen.family.canonical_id(candidate.utility_contrast_id)
            truth, point = metrics["targets"][coordinate], estimates[coordinate]
            false_utility |= point >= -frozen.design.utility_margin and truth < -frozen.design.utility_margin
            false_utility |= point > 0 and truth <= 0
    metrics.update(any_false_safe=bool(false_safe), any_false_violation=bool(false_violation),
                   any_false_utility_claim=bool(false_utility),
                   any_false_claim=bool(false_safe or false_violation or false_utility))
    return metrics


def _compact_certificates(certificates):
    keys = ("query_id", "channel", "normalizer", "status", "estimate", "lo", "hi",
        "raw_lo", "raw_hi", "empty_intersection", "radius", "bias", "concentration",
        "range_contribution", "tau", "selected_method", "numerical_guard", "reason")
    return [{key: certificate[key] for key in keys if key in certificate} for certificate in certificates.values()]


def _execute_trial(manifest, run_id, design, draw_callback, oracle_callback, hashes, *, graph_cache=None):
    config = manifest["config"]
    seed = int.from_bytes(hashlib.sha256(f"{config['seed_domain']}\0{config['master_seed']}\0{run_id}".encode()).digest()[:8], "little")
    started, cpu_start = time.monotonic(), time.process_time()
    logs = {name: draw_callback(split, seed) for name, split in design.splits.items()}
    frozen = fit_and_freeze_pipeline(design, logs["training"], logs["discovery"],
        max_rules=config["max_rules"], max_depth=config["max_depth"], minimum_mass=config["minimum_mass"],
        ridge=config["ridge"], tradeoff_grid=config["tradeoff_grid"])
    fixed, in_sample = _fixed_slice_family(frozen), _in_sample_family(frozen, logs["certification"],
        max_rules=config["max_rules"], max_depth=config["max_depth"], minimum_mass=config["minimum_mass"])
    certification = logs["certification"]
    point = _point_estimates(frozen, certification)
    in_sample_points = _point_estimates(in_sample, certification)
    point_selection, in_sample_selection = _point_select(frozen, point), _point_select(in_sample, in_sample_points)
    cache = graph_cache if graph_cache is not None else CachedSupportGraph(design.splits["certification"].graph)
    if cache.graph is not design.splits["certification"].graph:
        raise ValueError("source-support cache belongs to a different fixed-design cell")
    cache_before = cache.hits, cache.misses, cache.evictions
    evaluated = []
    for delta in config["levels"]:
        evaluated.extend([
            (delta, "point_constraint", frozen, {}, point_selection, point),
            (delta, "in_sample_auditing", in_sample, {}, in_sample_selection, in_sample_points)])
        local = None
        for arm, engine, arm_family in (("independent_global", "truncated_global_envelope", frozen),
                ("comet_local", "comet_local", frozen), ("generic_matched", "generic_matched", frozen),
                ("fixed_slice", "comet_local", fixed)):
            if arm == "generic_matched":
                certificates = {key: dict(value, method="generic_matched", equivalence_partner="comet_local") for key, value in local[0].items()}
                selection = dict(local[1])
            else:
                certificates, selection = _certify(arm_family, certification, delta, engine, config, hashes, cache)
                if arm == "comet_local":
                    local = certificates, selection
            evaluated.append((delta, arm, arm_family, certificates, selection, None))
        evaluated.extend([
            (delta, "abstain_reference", frozen, {}, dict(status="REFERENCE_ABSTAIN", returned=False, policy_id=None), None),
            (delta, "status_quo_reference", frozen, {}, dict(status="REFERENCE_UNCERTIFIED", returned=True,
                policy_id="policy0", safety_claim_certified=False), None)])
    # All fitting, auditors, engines, and selection decisions are finished.
    trials, frames, failure = [], [], False
    for delta, arm, arm_family, certificates, selection, estimates in evaluated:
        metrics = oracle_callback(arm_family, certificates, selection, methods_finished=True)
        if estimates is not None:
            metrics = _diagnostic_claim_metrics(metrics, arm_family, estimates)
        if arm in ("fixed_slice", "in_sample_auditing"):
            primary = oracle_callback(frozen, {}, selection, methods_finished=True)
            for key in ("returned", "returned_policy_id", "returned_baseline", "return_and_unsafe",
                    "return_and_risk_safe", "return_and_utility_noninferior", "return_and_service_feasible",
                    "return_and_infeasible", "return_and_safe_and_useful", "unsafe_given_return_numerator",
                    "unsafe_given_return_denominator", "true_utility", "utility_gain", "expected_service",
                    "expected_capacity", "maximum_true_risk_violation", "oracle_best_feasible_candidate_value"):
                metrics[key] = primary[key]
            metrics["robust_slack_comparator_value"] = None
        record = pipeline_trial_record(
            metrics, run_id=run_id, cell=run_id.split("/")[2], method=arm, delta=delta,
            certificates=certificates, coverage_applicable=arm in CERTIFIED_ARMS)
        record.update(metrics_assessable=True, return_endpoint_applicable=True,
            protocol_stage="FROZEN_PRODUCTION_PROTOCOL" if config.get("suite") == "E5" else "DETERMINISTIC_FIXTURE",
            discovery_endpoint_applicable=arm not in ("fixed_slice", "abstain_reference", "status_quo_reference"),
            returned_baseline=metrics["returned_baseline"],
            claim_kind="CERTIFIED_FINITE_FAMILY" if arm in CERTIFIED_ARMS else (
                "HEURISTIC_POINT_COMPARISONS" if estimates is not None else "UNCERTIFIED_REFERENCE"),
            primary_return_guarantee_applicable=arm in ("independent_global", "comet_local", "generic_matched"),
            actual_family_size=arm_family.family.family_size)
        failure |= bool(record["failure_status"])
        trials.append(record)
        frame = dict(delta=delta, method=arm, family_digest=arm_family.family.digest,
            actual_family_size=arm_family.family.family_size, selection=selection,
            certificates=_compact_certificates(certificates),
            coordinate_allocation=delta/arm_family.family.family_size if arm in CERTIFIED_ARMS else None)
        if estimates is not None:
            frame["point_estimates"] = estimates
        frames.append(frame)
    result = dict(suite="E5", cell=run_id.split("/")[2], status="COMPLETE_WITH_NUMERICAL_FAILURE" if failure else "COMPLETE",
        seed=seed, seed_domain=config["seed_domain"], code_sha256=hashes["code"], config_sha256=hashes["config"],
        git_sha=config.get("git_sha"), legacy_new_outcome_draws=0,
        new_scientific_units=0 if config.get("suite") == "DETERMINISTIC_PIPELINE_FIXTURE" else 1,
        source_split_digests={name: log.data_digest for name, log in logs.items()},
        split_sizes={name: split.n for name, split in design.splits.items()},
        exposed_labels={name: int(log.actions.sum()) for name, log in logs.items()},
        total_rows=sum(split.n for split in design.splits.values()),
        independent_replication_unit="one complete trial containing three source-disjoint splits",
        proper_family=_family_description(frozen), fixed_slice_family=_family_description(fixed),
        in_sample_family=_family_description(in_sample), trials=trials, certificate_records=frames,
        generic_matched_equivalence="same algebra/endpoints as COMET; reused only to avoid duplicate compute",
        oracle_order="all arms and both levels selected before any oracle join",
        operational=dict(
            truncation_evaluation="THEORY_NOTE_section5_p2_kappa_argmin_on_original_full_grid",
            original_grid_size=len(config["truncation_multipliers"]),
            evaluated_grid_multiplier=factorized_p2_grid_choice(config["truncation_multipliers"]),
            source_graph_cache=dict(entries=len(cache.cache), max_entries=cache.max_entries,
                trial_hits=cache.hits-cache_before[0], trial_misses=cache.misses-cache_before[1],
                trial_evictions=cache.evictions-cache_before[2]),
            wall_seconds=time.monotonic()-started, cpu_seconds=time.process_time()-cpu_start))
    if failure or run_id in config["raw_debug_run_ids"]:
        result["raw_debug"] = {name: dict(actions=log.actions.tolist(),
            outcomes={channel: values.tolist() for channel, values in log.outcomes.items()}) for name, log in logs.items()}
        result["raw_debug_reason"] = "failure" if failure else "prespecified_run_ID"
    return result


def pipeline_status(protocol_path, results_root, *, list_ids=False):
    path = Path(protocol_path)
    if not path.exists():
        result = dict(status="NOT_FROZEN", suite="E5", completed_units=0, remaining_units=4000,
            legacy_new_outcome_draws=0, id_status="reserved proposed IDs, not consumed seeds")
        if list_ids:
            result.update(completed_ids=[], remaining_ids=planned_pipeline_ids())
        return result
    manifest = json.loads(path.read_text())
    store = CheckpointStore(results_root, manifest)
    remaining = store.remaining_ids()
    completed = sorted(store.planned - set(remaining))
    result = dict(status="COMPLETE" if not remaining else "INCOMPLETE", suite="E5",
        fingerprint=manifest["fingerprint"], completed_units=len(completed), remaining_units=len(remaining),
        legacy_new_outcome_draws=0)
    if list_ids:
        result.update(completed_ids=completed, remaining_ids=remaining)
    return result


def _global_usage(global_root):
    artifact_bytes, units = 0, set()
    root = Path(global_root)
    if root.exists():
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            artifact_bytes += path.stat().st_size
            if "checkpoints" in path.parts and path.name.endswith(".json.gz"):
                suffix = path.parts[path.parts.index("checkpoints") + 1:]
                if len(suffix) == 3:
                    units.add("/".join(suffix).removesuffix(".json.gz"))
    return artifact_bytes, len(units)


def _check_global_budget(global_root, config, reader, *, drawing=True):
    artifact_bytes, unique_units = _global_usage(global_root)
    snapshot = reader(global_root)
    _resource_check(snapshot, artifact_bytes, config)
    if drawing and unique_units >= config["total_unit_cap"]:
        raise ResourceLimitError("global 32,000-new-unit limit reached before another trial")
    return dict(snapshot, global_artifact_bytes=artifact_bytes, global_unique_completed_units=unique_units)


def run_pipeline(protocol_path, results_root, *, max_new_units=None, draw_callback=None,
                 oracle_callback=None, resource_reader=None):
    """One synchronous CPU worker; immutable completed IDs never call the logger."""
    manifest = json.loads(Path(protocol_path).read_text())
    config = manifest["config"]
    if config.get("suite") not in ("E5", "DETERMINISTIC_PIPELINE_FIXTURE") or config.get("workers") != 1:
        raise ValueError("this runner implements E5 with one synchronous worker")
    if config["suite"] == "DETERMINISTIC_PIPELINE_FIXTURE" and draw_callback is None:
        raise ValueError("deterministic fixtures require an explicit nonrandom split callback")
    if max_new_units is not None and (type(max_new_units) is not int or max_new_units < 0):
        raise ValueError("max_new_units must be a nonnegative integer")
    store = CheckpointStore(results_root, manifest)
    remaining_before = store.remaining_ids()
    global_root = Path(config["global_results_root"])
    if not Path(results_root).resolve().is_relative_to(global_root.resolve()):
        raise ValueError("E5 checkpoints must reside under the shared post-C-STAT artifact root")
    reader = resource_reader or resource_snapshot
    initial_resource = _check_global_budget(global_root, config, reader, drawing=bool(remaining_before))
    hashes = dict(code=digest(manifest["sources"]), config=digest(config),
                  p2_grid_choice=factorized_p2_grid_choice(config["truncation_multipliers"]))
    stamps = _source_stamps(manifest)
    by_cell = defaultdict(list)
    for run_id in remaining_before:
        by_cell[run_id.split("/")[2]].append(run_id)
    new_units, failed_units, status, stop_reason = 0, 0, "COMPLETE", None
    began, cpu_start = time.monotonic(), time.process_time()
    try:
        for cell, ids in sorted(by_cell.items()):
            if max_new_units is not None and new_units >= max_new_units:
                status = "CHECKPOINTED_INCOMPLETE"
                break
            graph, overlap, world = cell.split("-")
            design = build_pipeline_design(graph, overlap, world,
                namespace=config["seed_domain"] + "/" + cell, split_sizes=config["split_sizes"])
            # The graph is fixed within this cell. Each cached active mask is
            # measurable in design/independent pilots; no evaluation Y is read.
            shared_graph_cache = CachedSupportGraph(design.splits["certification"].graph, max_entries=32)
            for run_id in ids:
                if max_new_units is not None and new_units >= max_new_units:
                    status = "CHECKPOINTED_INCOMPLETE"
                    break
                stamps = _verify_changed_sources(manifest, stamps)
                _check_global_budget(global_root, config, reader)
                if store.load(run_id) is not None:
                    continue
                observed_logs = {}
                def tracked_draw(split, seed):
                    log = (draw_callback or draw_pipeline_split)(split, seed)
                    observed_logs[split.name] = log
                    return log
                try:
                    result = _execute_trial(manifest, run_id, design, tracked_draw,
                                            oracle_callback or evaluate_pipeline, hashes,
                                            graph_cache=shared_graph_cache)
                except Exception as exc:
                    result = dict(suite="E5", cell=cell, status="UNIT_FAILURE",
                        failure_reason=f"{type(exc).__name__}: {exc}"[:4096],
                        seed=int.from_bytes(hashlib.sha256(f"{config['seed_domain']}\0{config['master_seed']}\0{run_id}".encode()).digest()[:8], "little"),
                        seed_domain=config["seed_domain"], code_sha256=hashes["code"], config_sha256=hashes["config"],
                        legacy_new_outcome_draws=0, full_family_failure=True, unassessable_whole_trial=True,
                        family_covered=False, trials=[],
                        source_split_digests={name: log.data_digest for name, log in observed_logs.items()},
                        raw_debug={name: dict(actions=log.actions.tolist(),
                            outcomes={channel: values.tolist() for channel, values in log.outcomes.items()})
                            for name, log in observed_logs.items()},
                        new_scientific_units=0 if config["suite"] == "DETERMINISTIC_PIPELINE_FIXTURE" else 1)
                store.complete(run_id, result)
                new_units += 1
                failed_units += result["status"] != "COMPLETE"
                if result["status"] == "UNIT_FAILURE":
                    status, stop_reason = "ERROR_CHECKPOINTED", result["failure_reason"]
                    break
            del design, shared_graph_cache
            if status == "ERROR_CHECKPOINTED":
                break
    except ResourceLimitError as exc:
        status, stop_reason = "RESOURCE_CHECKPOINTED", str(exc)
    except KeyboardInterrupt:
        status, stop_reason = "INTERRUPTED", "synchronous invocation ended; no unattended continuation"
    except ValueError as exc:
        status, stop_reason = "SOURCE_OR_PROTOCOL_BLOCKED", str(exc)
    remaining = store.remaining_ids()
    if remaining and status == "COMPLETE":
        status = "CHECKPOINTED_INCOMPLETE"
    invocation = dict(suite="E5", status=status, stop_reason=stop_reason,
        new_completed_units=new_units, failed_units=failed_units, remaining_ids=remaining,
        legacy_new_outcome_draws=0, background_work_running=False, workers=1,
        fingerprint=manifest["fingerprint"], first_resource_snapshot=initial_resource,
        final_global_usage=dict(zip(("artifact_bytes", "unique_completed_units"), _global_usage(global_root))),
        wall_seconds=time.monotonic()-began, cpu_seconds=time.process_time()-cpu_start,
        execution_mode="one synchronous CPU worker; no GPU/paid resources",
        resume_command=".venv/bin/python -m experiments.pipeline_runner --run --protocol " +
            shlex.quote(str(Path(protocol_path))) + " --results " + shlex.quote(str(Path(results_root))))
    install_once(Path(results_root) / "invocations" / f"{time.time_ns()}.json", canonical_bytes(invocation) + b"\n")
    return invocation


def _unknown_pipeline_record(run_id, arm, delta, status):
    row = dict(run_id=run_id, cell=run_id.split("/")[2], method=arm, delta=delta,
        coverage_applicable=arm in CERTIFIED_ARMS, family_covered=False,
        metrics_assessable=False, failure_status=status, mean_coordinate_width=None,
        return_endpoint_applicable=True,
        discovery_endpoint_applicable=arm not in ("fixed_slice", "abstain_reference", "status_quo_reference"))
    row.update({event: False for event in EVENTS})
    return row


def _records_from_payload(payload, config):
    run_id, result = payload["run_id"], payload["result"]
    if run_id.split("/")[1] != "E5" or result.get("cell", run_id.split("/")[2]) != run_id.split("/")[2]:
        raise ValueError("pipeline checkpoint/run identity mismatch")
    expected = {(arm, delta) for arm in config["arms"] for delta in config["levels"]}
    records = result.get("trials", [])
    if not isinstance(records, list):
        raise ValueError("pipeline trials must be a list")
    found = {}
    for row in records:
        if row.get("run_id") != run_id or row.get("cell") != run_id.split("/")[2]:
            raise ValueError("pipeline method/level record has a different trial identity")
        key = row.get("method"), row.get("delta")
        if key not in expected or key in found:
            raise ValueError("duplicate or unregistered pipeline method/level record")
        if row.get("coverage_applicable") != (key[0] in CERTIFIED_ARMS):
            raise ValueError("pipeline coverage applicability changed after outcomes")
        found[key] = row
    for key in sorted(expected):
        if key not in found or result.get("unassessable_whole_trial", False):
            status = result.get("status", "MISSING_PIPELINE_RESULT")
            if status == "COMPLETE":
                status = "MISSING_PIPELINE_METHOD_LEVEL"
            yield _unknown_pipeline_record(run_id, *key, status)
        else:
            yield found[key]


def _extra_state():
    return dict(n=0, bool_hits=Counter(), bool_unknown=Counter(),
                numeric_sums=Counter(), numeric_counts=Counter(), numeric_unknown=Counter(), families=Counter())


def _add_extra(state, row):
    state["n"] += 1
    assessable = bool(row.get("metrics_assessable", True))
    for key in BOOLEAN_EXTRAS:
        value = row.get(key)
        if not assessable or not isinstance(value, (bool, np.bool_)):
            state["bool_unknown"][key] += 1
        else:
            state["bool_hits"][key] += bool(value)
    for key in NUMERIC_EXTRAS:
        value = row.get(key)
        if not assessable:
            state["numeric_unknown"][key] += 1
        elif value is not None:
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("nonfinite pipeline metric in a completed trial: " + key)
            state["numeric_sums"][key] += value
            state["numeric_counts"][key] += 1
    if row.get("actual_family_size") is not None:
        state["families"][str(row["actual_family_size"])] += 1


def _extra_result(state):
    from comet.metrics import wilson
    n = state["n"]
    booleans = {}
    for key in BOOLEAN_EXTRAS:
        hits, unknown = state["bool_hits"][key], state["bool_unknown"][key]
        booleans[key] = dict(hits=hits, denominator=n, unknown_trials=unknown,
            rate=hits/n if not unknown else None,
            wilson95=list(wilson(hits, n)) if not unknown else None,
            realized_frequency_bounds=[hits/n, (hits+unknown)/n])
    numbers = {}
    for key in NUMERIC_EXTRAS:
        count = state["numeric_counts"][key]
        numbers[key] = dict(mean=state["numeric_sums"][key]/count if count else None,
            value_count=count, whole_trials=n, unassessable_trials=state["numeric_unknown"][key],
            value_scope="returned policies only" if key in ("true_utility", "utility_gain", "maximum_true_risk_violation")
                        else "available evaluation-only values; service/capacity include zero on abstention")
    return dict(joint_events=booleans, numeric_metrics=numbers,
                actual_family_size_counts=dict(state["families"]))


def analyze_pipeline(protocol_path, results_root, output_directory, *, bootstrap_resamples=None):
    """Stream independent trials, preserve unknown failures, and pair by full ID."""
    from experiments.post_cstat_analyze import _csv_bytes
    import csv
    import io
    path, output = Path(protocol_path), Path(output_directory)
    if any((output / name).exists() for name in ("summary.json", "summary.csv", "manifest.json")):
        raise FileExistsError("analysis artifacts are immutable; use a new output directory")
    manifest = json.loads(path.read_text())
    config = manifest["config"]
    fixture = config.get("suite") == "DETERMINISTIC_PIPELINE_FIXTURE"
    if config.get("suite") not in ("E5", "DETERMINISTIC_PIPELINE_FIXTURE"):
        raise ValueError("pipeline analyzer requires E5")
    registered = tuple(tuple(value) for value in config["primary_comparisons"])
    if not fixture and registered != tuple(tuple(value) for value in primary_pipeline_comparisons()):
        raise ValueError("retain the frozen 32 certified E5 comparisons")
    if bootstrap_resamples is None:
        bootstrap_resamples = 0 if fixture else config["analysis_bootstrap_resamples"]
    if type(bootstrap_resamples) is not int or bootstrap_resamples < 0 or (not fixture and bootstrap_resamples != 2000):
        raise ValueError("production analysis uses its frozen 2000-resample setting")
    store = CheckpointStore(results_root, manifest)
    summaries, extra, paired = {}, {}, defaultdict(dict)
    completed, inventory = set(), []
    statuses, failed, unassessable = Counter(), 0, 0
    for payload in store.iter_completed():
        run_id, result = payload["run_id"], payload["result"]
        completed.add(run_id)
        inventory.append([run_id, digest(payload)])
        statuses[result.get("status", "STATUS_MISSING")] += 1
        unit_failed = unit_unknown = False
        for row in _records_from_payload(payload, config):
            key = row["cell"], row["method"], row["delta"]
            summaries.setdefault(key, WholeTrialSummary()).add(row)
            _add_extra(extra.setdefault(key, _extra_state()), row)
            assessable = bool(row.get("metrics_assessable", True))
            paired[key][run_id] = bool(row["return_safe_useful"]) if assessable else None
            unit_failed |= bool(row.get("failure_status"))
            unit_unknown |= not assessable
        failed += unit_failed
        unassessable += unit_unknown
    rows = []
    for key in sorted(summaries):
        row = summaries[key].result()
        row["pipeline_metrics"] = _extra_result(extra[key])
        row["primary_return_guarantee_applicable"] = row["method"] in ("independent_global", "comet_local", "generic_matched")
        rows.append(row)
    adjusted = adjust_validity_family(rows, registered)
    primary = {(row["cell"], row["method"]):row for row in rows if row["delta"] == .05}
    for row in rows:
        row["holm_undercoverage_p"] = adjusted.get((row["cell"], row["method"])) if row["delta"] == .05 else None
    diagnostics = [dict(cell=cell, method=arm,
        undercoverage_p=primary.get((cell, arm), {}).get("family_coverage", {}).get("undercoverage_p"),
        holm_undercoverage_p=adjusted[(cell, arm)]) for cell, arm in registered]
    differences = []
    for cell in sorted({key[0] for key in paired}):
        for delta in config["levels"]:
            left = paired.get((cell, "comet_local", delta), {})
            for arm in config["arms"]:
                if arm == "comet_local":
                    continue
                right = paired.get((cell, arm, delta), {})
                if not left and not right:
                    continue
                seed = int.from_bytes(hashlib.sha256(f"{config['analysis_bootstrap_seed']}\0{cell}\0{arm}\0{delta}".encode()).digest()[:8], "little")
                record = dict(cell=cell, delta=delta, left="comet_local", right=arm,
                    endpoint="return_safe_useful", pairing_unit="full independent trial run ID", bootstrap_seed=seed)
                if set(left) != set(right) or any(value is None for value in list(left.values()) + list(right.values())):
                    record.update(status="UNASSESSABLE_FULL_PAIRING", independent_pairs=len(set(left) | set(right)),
                        mean_difference=None, bootstrap_pointwise95=None)
                elif bootstrap_resamples:
                    record.update(paired_endpoint_difference(left, right, bootstrap_seed=seed, resamples=bootstrap_resamples),
                                  status="PAIRED_BOOTSTRAP_POINTWISE_NOT_SIMULTANEOUS")
                else:
                    record.update(status="DESCRIPTIVE_NO_BOOTSTRAP", independent_pairs=len(left),
                        mean_difference=float(np.mean([float(left[key])-float(right[key]) for key in sorted(left)])),
                        bootstrap_pointwise95=None, resamples=0)
                differences.append(record)
    remaining = sorted(store.planned - completed)
    status = "NO_COMPLETED_UNITS" if not completed else ("COMPLETE" if not remaining else "PARTIAL")
    summary = dict(schema="post-cstat-E5-analysis-v1", status=status, suite="E5",
        phase="DETERMINISTIC_FIXTURE_NOT_SCIENCE" if fixture else "confirmatory",
        protocol_fingerprint=manifest["fingerprint"], completed_units=len(completed),
        remaining_units=len(remaining), failed_units=failed, unassessable_units=unassessable,
        completed_ids=sorted(completed), remaining_ids=remaining, checkpoint_inventory_sha256=digest(inventory),
        checkpoint_status_counts=dict(statuses), summaries=rows,
        primary_comparison_count=len(registered), primary_diagnostics=diagnostics,
        paired_safe_useful_differences=differences, bootstrap_resamples=bootstrap_resamples,
        new_analysis_outcome_draws=0, legacy_new_outcome_draws=0,
        historical_primary_families_modified=False,
        unit="one complete three-split trial; arms and levels are paired, not independent replications",
        safety_scope="return_unsafe concerns primary discovered-family risks; return_and_infeasible also includes utility/service",
        applicability="only independent_global/COMET/matched guarantee primary-family feasible selection; fixed_slice covers its own coordinates",
        uncertainty="pointwise Monte Carlo Wilson and paired bootstrap; neither implies conditional-return-risk control",
        equivalent_arms=[["comet_local", "generic_matched"]])
    content = canonical_bytes(summary) + b"\n"
    base = csv.DictReader(io.StringIO(_csv_bytes(rows).decode()))
    fieldnames = list(base.fieldnames) + [key + "_" + suffix for key in BOOLEAN_EXTRAS for suffix in ("rate", "unknown_trials")]
    fieldnames += [key + "_mean" for key in NUMERIC_EXTRAS] + ["actual_family_size_counts"]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames)
    writer.writeheader()
    for flat, row in zip(base, rows):
        extra_row = row["pipeline_metrics"]
        for key, value in extra_row["joint_events"].items():
            flat[key + "_rate"] = value["rate"]
            flat[key + "_unknown_trials"] = value["unknown_trials"]
        for key, value in extra_row["numeric_metrics"].items():
            flat[key + "_mean"] = value["mean"]
        flat["actual_family_size_counts"] = json.dumps(extra_row["actual_family_size_counts"], sort_keys=True)
        writer.writerow(flat)
    csv_content = stream.getvalue().encode()
    receipt = dict(schema="post-cstat-E5-analysis-manifest-v1", status=status,
        protocol_fingerprint=manifest["fingerprint"], analysis_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        completed_units=len(completed), remaining_units=len(remaining), primary_family_sha256=digest(registered),
        new_analysis_outcome_draws=0, legacy_new_outcome_draws=0,
        outputs={"summary.json":hashlib.sha256(content).hexdigest(), "summary.csv":hashlib.sha256(csv_content).hexdigest()})
    receipt["analysis_fingerprint"] = digest(receipt)
    install_once(output / "summary.json", content)
    install_once(output / "summary.csv", csv_content)
    install_once(output / "manifest.json", canonical_bytes(receipt) + b"\n")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    for name in ("status", "freeze", "run", "analyze"):
        mode.add_argument("--"+name, action="store_true")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--inputs", type=Path, default=REPOSITORY / "task_materials/post_cstat")
    parser.add_argument("--protocol", type=Path, default=REPOSITORY / "results/post_cstat/E5_protocol.json")
    parser.add_argument("--results", type=Path, default=REPOSITORY / "results/post_cstat/E5")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-new-units", type=int)
    parser.add_argument("--list-ids", action="store_true")
    args = parser.parse_args(argv)
    if args.status:
        result = pipeline_status(args.protocol, args.results, list_ids=args.list_ids)
    elif args.freeze:
        if args.config is None:
            parser.error("--freeze requires an explicit --config")
        result = freeze_pipeline(args.config, args.inputs, args.protocol)
    elif args.run:
        if json.loads(args.protocol.read_text())["config"].get("suite") != "E5":
            raise ValueError("the CLI cannot run a deterministic test fixture")
        result = run_pipeline(args.protocol, args.results, max_new_units=args.max_new_units)
    else:
        if args.output is None:
            parser.error("--analyze requires a fresh --output directory")
        summary = analyze_pipeline(args.protocol, args.results, args.output)
        result = {key:summary[key] for key in ("status", "completed_units", "remaining_units", "failed_units", "unassessable_units")}
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()

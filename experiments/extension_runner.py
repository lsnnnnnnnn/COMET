"""Frozen, recoverable E2/E3/E4 execution, separate from the running E1 study.

One checkpoint is one whole logged data set; methods and both levels share it.
This file does not modify or import a historical experiment runner. E2 outside
variants share primitive streams by replicate, while E3/E4 use independent cell
streams. Discovery/policy-return endpoints do not apply to these audit suites.
"""

import argparse
from dataclasses import dataclass, replace
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import shlex
import subprocess
import time

import numpy as np

from comet.audit_pipeline import freeze_discovered_family
from comet.checkpoint_store import (
    CheckpointStore, NAMESPACE, canonical_bytes, digest, freeze_protocol,
    install_once, planning_input_hashes,
)
from comet.paired_contrasts import make_joint_level_family_plans, _signed_target_range
from comet.residual_truncation import (
    CERTIFIED, certified_decision, choose_truncation, make_plan, residual_moment_envelope,
)
from experiments.post_cstat_runner import (
    BOUNDED_METHODS, CORE_METHODS, GIB, LEVELS, REPOSITORY, SOURCE_NAMES,
    ResourceLimitError, _cell_metadata, _compact_record, _resource_check,
    _source_stamps, _verify_changed_sources, resource_snapshot, environment_signature,
)
from experiments.suite_designs import (
    build_contrast_design, build_gap_design, build_locality_design,
    draw_suite_log, evaluate_suite_oracle,
)


SUITE_REPS = {"E2": 300, "E3": 300, "E4": 300}
SUITE_UNITS = {"E2": 1800, "E3": 3600, "E4": 7200}
SUPPORTS = (("002", 0.02), ("010", 0.1), ("100", 1.0))
GAPS = (("m010", -0.1), ("m003", -0.03), ("zero", 0.0),
        ("p003", 0.03), ("p010", 0.1), ("p020", 0.2))
JOINT_LEVEL = "deduplicated_joint_level_difference"
EXTRA_SOURCE_NAMES = ("comet/audit_pipeline.py", "comet/paired_contrasts.py",
    "experiments/suite_designs.py", "experiments/extension_runner.py",
    "experiments/extension_analyze.py", "experiments/post_cstat_analyze.py")


def suite_cells(suite):
    if suite == "E2":
        return [f"hub{hub}-{overlap}" for hub in (1, 16, 64)
                for overlap in ("moderate", "extreme1e-4")]
    if suite == "E3":
        return [f"support{label}-{overlap}-{outcome}" for label, _ in SUPPORTS
                for overlap in ("moderate", "weak") for outcome in ("bounded", "heavy")]
    if suite == "E4":
        return [f"{overlap}-{outcome}-gap{label}" for overlap in ("moderate", "weak")
                for outcome in ("bounded", "heavy") for label, _ in GAPS]
    raise ValueError("only E2, E3 and E4 are implemented here")


def methods_for_extension_cell(suite, cell):
    if cell not in suite_cells(suite):
        raise ValueError("cell is outside the declared extension grid")
    bounded = suite == "E2" or "-bounded" in cell
    return CORE_METHODS + (BOUNDED_METHODS if bounded else ()) + ((JOINT_LEVEL,) if suite == "E3" else ())


def primary_extension_comparisons(suite):
    return [[cell, method] for cell in suite_cells(suite)
            for method in methods_for_extension_cell(suite, cell)]


def planned_extension_ids(suite):
    return [f"{NAMESPACE}/{suite}/{cell}/{rep:04d}"
            for cell in suite_cells(suite) for rep in range(SUITE_REPS[suite])]


def effective_suite(config):
    suite = config.get("target_suite") if config.get("suite") == "DETERMINISTIC_EXTENSION_FIXTURE" else config.get("suite")
    if suite not in SUITE_UNITS:
        raise ValueError("extension protocol must identify E2, E3 or E4")
    return suite


def _validate_config(config, suite):
    required = ("truncation_multipliers", "truncation_grid_source", "master_seed", "seed_domain",
        "normalized_risk_threshold", "planning_inputs_reconciled", "theorem_status",
        "numerical_guard", "raw_debug_run_ids", "analysis_bootstrap_seed", "analysis_bootstrap_resamples")
    if any(key not in config for key in required):
        raise ValueError("explicit extension configuration required: " + ", ".join(required))
    expected_grid = [2 ** (j / 4) for j in range(-24, 25)]
    if config["truncation_multipliers"] != expected_grid:
        raise ValueError("production grid must equal reconciled THEORY_NOTE 49 points 2^(j/4)")
    if not config["truncation_grid_source"] or config["planning_inputs_reconciled"] is not True:
        raise ValueError("record the actual reconciled planning source")
    if config["theorem_status"] != "PROVED_UNDER_DECLARED_ASSUMPTIONS":
        raise ValueError("certified extension paths require completed proofs")
    if "production_environment" in config and config["production_environment"] != environment_signature():
        raise ValueError("selected production environment differs from the current environment")
    if any(type(config[key]) is not int or config[key] < 0 for key in ("master_seed", "analysis_bootstrap_seed")):
        raise ValueError("explicit nonnegative generation and analysis seeds required")
    if config["analysis_bootstrap_resamples"] != 2000:
        raise ValueError("production paired performance analysis uses 2000 whole-replicate bootstrap resamples")
    if not isinstance(config["seed_domain"], str) or not config["seed_domain"].startswith(NAMESPACE + "/" + suite):
        raise ValueError("use the suite's new seed domain")
    threshold = 0.0 if suite == "E3" else 0.4
    if config["normalized_risk_threshold"] != threshold:
        raise ValueError("extension risk/contrast threshold differs from the declared design")
    if not math.isfinite(config["numerical_guard"]) or config["numerical_guard"] < 0:
        raise ValueError("a nonnegative conservative numerical guard is required")
    fixed = dict(namespace=NAMESPACE, suite=suite, N=32768, workers=1,
        cells=suite_cells(suite), replications_per_cell=SUITE_REPS[suite], levels=list(LEVELS),
        legacy_new_outcome_draws=0, primary_units=SUITE_UNITS[suite], total_unit_cap=32000,
        total_primary_goal_units=29600, planned_run_ids=planned_extension_ids(suite),
        primary_comparisons=primary_extension_comparisons(suite),
        artifact_cap_bytes=int(1.5 * GIB), minimum_free_disk_bytes=2 * GIB,
        worker_memory_cap_bytes=4 * GIB, family_size_rule="actual frozen deduplicated coordinates",
        E2_pairing="same_complete_replicate_primitive_streams_across_outside_variants" if suite == "E2" else "not_applicable",
        other_cell_pairing="none" if suite != "E2" else "declared_E2_pairing",
        E0_policy="closed; zero new historical draws")
    for key, value in fixed.items():
        if key in config and config[key] != value:
            raise ValueError("fixed extension protocol mismatch: " + key)
    if not isinstance(config["raw_debug_run_ids"], list) or not set(config["raw_debug_run_ids"]) <= set(fixed["planned_run_ids"]):
        raise ValueError("raw debug cases must be selected by frozen run IDs")
    return dict(config, **fixed)


def freeze_extension(config_path, input_directory, protocol_path, suite):
    config_path = Path(config_path).resolve()
    config = _validate_config(json.loads(config_path.read_text()), suite)
    planning_input_hashes(input_directory, allowed_missing=config.get("allowed_missing_planning_inputs", ()))
    names = tuple(dict.fromkeys(SOURCE_NAMES + EXTRA_SOURCE_NAMES))
    sources = [REPOSITORY / name for name in names] + [config_path]
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPOSITORY, text=True).strip()
    for path in sources:
        try:
            relative = path.relative_to(REPOSITORY)
        except ValueError as exc:
            raise ValueError("extension config must be committed inside the research repository") from exc
        status = subprocess.check_output(["git", "status", "--porcelain", "--", str(relative)],
                                         cwd=REPOSITORY, text=True)
        if status or not path.is_file():
            raise ValueError("commit executable config, source and theorem before freeze: " + str(relative))
    config.update(git_sha=sha, input_config_sha256=hashlib.sha256(config_path.read_bytes()).hexdigest(),
        E0_anchor="ca5bb878cf9635fac4381d03281df0bc8a900daa",
        equivalent_methods=[["comet_local", "generic_matched"]])
    return freeze_protocol(protocol_path, config, sources, input_directory)


@dataclass(frozen=True)
class ExtensionCell:
    suite_design: object
    family: object
    subgroup_masses: dict
    thresholds: dict
    feasible_ranges: dict

    @property
    def queries(self):
        return self.family.queries

    @property
    def n(self):
        return self.suite_design.core.n

    @property
    def graph(self):
        return self.suite_design.core.graph

    @property
    def exposure(self):
        return self.suite_design.core.exposure

    @property
    def nuisance(self):
        return self.suite_design.core.nuisance

    @property
    def residual_moments(self):
        return self.suite_design.core.residual_moments

    @property
    def certifier_inputs(self):
        return self.suite_design.certifier_inputs


def _design(config, cell):
    suite, n = effective_suite(config), config["N"]
    # Outside-only variants deliberately keep all base primitive IDs identical.
    namespace = config["seed_domain"] + ("/paired-outside-variants" if suite == "E2" else "/" + cell)
    if suite == "E2":
        hub, overlap = cell.split("-", 1)
        design = build_locality_design(n, int(hub.removeprefix("hub")), overlap, namespace)
    elif suite == "E3":
        support, overlap, outcome = cell.split("-")
        fraction = dict(SUPPORTS)[support.removeprefix("support")]
        design = build_contrast_design(n, fraction, overlap, outcome, namespace)
    else:
        overlap, outcome, gap = cell.split("-")
        design = build_gap_design(n, dict(GAPS)[gap.removeprefix("gap")], overlap, outcome, namespace)
    family = freeze_discovered_family(design.queries)
    masses, thresholds, feasible = {}, {}, {}
    for query in family.queries:
        if suite == "E3":
            auditor = int(query.query_id.rsplit("auditor", 1)[1])
            mass = float(design.core.queries[auditor].coefficients.sum(axis=1).mean())
        else:
            mass = float(query.coefficients.sum(axis=1).mean())
        masses[query.query_id] = mass
        thresholds[query.query_id] = (config["normalized_risk_threshold"] if suite == "E4" else
                                     config["normalized_risk_threshold"] * mass / query.normalizer)
        feasible[query.query_id] = _signed_target_range(query, (0.0, 1.0))
    return ExtensionCell(design, family, masses, thresholds, feasible)


def _global_policy_envelope_plan(config, cell, query, ordinary):
    """E2 ablation: pay the SAME policy's worst envelope outside the auditor.

    The estimator retains local signed d. Only the known envelope is coarsened:
    for binary h, its per-row moment is <= the full-policy global maximum.
    The source graph is global, so an outside source clique is also paid for.
    """
    policy = int(query.query_id.split("/policy", 1)[1].split("/", 1)[0])
    core = cell.suite_design.core
    full_q = core.queries[4 * policy].coefficients
    global_v = residual_moment_envelope(full_q, core.exposure, core.residual_moments, core.p)
    maximum = float(global_v.max())
    tau, pieces = choose_truncation(np.full(cell.n, maximum), core.p, core.graph.color_count,
        ordinary.coordinate_delta, cell.n, config["truncation_multipliers"])
    return replace(ordinary, method="truncated_global_envelope",
        selected_method="same_policy_global_envelope_global_graph", tau=tau,
        color_count=core.graph.color_count, bias_piece=pieces[0], variance_piece=pieces[1],
        range_piece=pieces[2]), maximum


def build_extension_plans(config, cell_id):
    cell = _design(config, cell_id)
    suite = effective_suite(config)
    direct_plans, joint_plans, extra = {}, {}, {"global_policy_envelope_maxima": {}}
    for delta in config["levels"]:
        for method in methods_for_extension_cell(suite, cell_id):
            if method == JOINT_LEVEL:
                pairs = [(query, *levels) for query, levels in zip(
                    cell.suite_design.queries, cell.suite_design.metadata["level_pairs"])]
                joint_plans[float(delta)] = make_joint_level_family_plans(pairs,
                    **cell.certifier_inputs, delta=float(delta),
                    multipliers=config["truncation_multipliers"], method="generic_matched")
                continue
            plans = []
            for query in cell.queries:
                ordinary = make_plan(query, **cell.certifier_inputs, delta=float(delta),
                    family_size=cell.family.family_size,
                    multipliers=config["truncation_multipliers"], method=method)
                if suite == "E2" and method == "truncated_global_envelope":
                    ordinary, maximum = _global_policy_envelope_plan(config, cell, query, ordinary)
                    extra["global_policy_envelope_maxima"][query.query_id] = maximum
                plans.append(ordinary)
            direct_plans[(float(delta), method)] = tuple(plans)
    return cell, direct_plans, joint_plans, extra


class GlobalBudget:
    """Count immutable new artifacts and whole-unit checkpoints across suites.

    Scans discover new atomic files from another concurrently running suite.
    Previously seen immutable file sizes are cached; no N-by-N structures or
    repeated decompression of other suites' scientific records are needed.
    """
    def __init__(self, root):
        self.root = Path(root)
        self.known = {}
        self.artifact_bytes = 0
        self.unit_paths = set()

    def scan(self):
        if self.root.exists():
            for directory, _, names in os.walk(self.root):
                for name in names:
                    if name.startswith(".pending-"):
                        continue
                    path = Path(directory) / name
                    if path in self.known:
                        continue
                    try:
                        size = path.stat().st_size
                    except FileNotFoundError:
                        continue  # an atomic writer's temporary name vanished
                    self.known[path] = size
                    self.artifact_bytes += size
                    if "checkpoints" in path.relative_to(self.root).parts and name.endswith(".json.gz"):
                        self.unit_paths.add(path)
        return self.artifact_bytes, len(self.unit_paths)


def _seed_for_run(config, run_id):
    suite = effective_suite(config)
    unit = run_id.rsplit("/", 1)[1] if suite == "E2" else run_id
    return int.from_bytes(hashlib.sha256(
        f"{config['seed_domain']}\0{config['master_seed']}\0{unit}".encode()).digest()[:8], "little")


def _save_cell_metadata(root, manifest, cell_id, cell, direct_plans, joint_plans, extra):
    metadata = _cell_metadata(manifest, cell_id, cell, direct_plans)
    metadata.update(suite=effective_suite(manifest["config"]),
        actual_family_size=cell.family.family_size, direct_family_digest=cell.family.digest,
        coordinate_hashes=dict(cell.family.coordinate_hashes), aliases=dict(cell.family.aliases),
        query_thresholds=cell.thresholds, known_target_ranges=cell.feasible_ranges, **extra)
    metadata["design_choices"] = {
        key: value for key, value in cell.suite_design.metadata.items()
        if isinstance(value, (str, int, float, bool)) or value is None
    }
    metadata["joint_level_families"] = {
        str(delta): dict(actual_underlying_levels=plan.underlying_family_size,
            level_coordinate_delta=plan.coordinate_delta, family_digest=plan.family.digest,
            coordinate_hashes=dict(plan.family.coordinate_hashes), aliases=dict(plan.family.aliases),
            derived_family_size=plan.direct_family.family_size,
            derived_joint_failure_delta=plan.delta,
            rule="one deduplicated simultaneous level event, not an extra union over contrasts")
        for delta, plan in joint_plans.items()
    }
    if effective_suite(manifest["config"]) == "E2":
        metadata["global_ablation_rule"] = "same policy's unmasked q across all N rows for max moment; local d retained in estimator"
    path = Path(root) / "cell_designs" / (cell_id + ".json.gz")
    content = canonical_bytes(metadata)
    if path.exists():
        if gzip.decompress(path.read_bytes()) != content:
            raise ValueError("extension cell metadata changed or is corrupt")
    else:
        install_once(path, gzip.compress(content, mtime=0))


def _failure_coordinate(query, reason):
    return dict(query_id=query.query_id, status="NUMERICAL_FAILURE", empty_intersection=True,
                reason=reason[:2048], channel=query.channel, normalizer=query.normalizer)


def _raw_debug(log):
    def encoded(array):
        return [float(value) if math.isfinite(float(value)) else str(float(value))
                for value in np.asarray(array).ravel()]
    return dict(actions=encoded(log.actions), outcomes=encoded(log.outcomes),
                nonfinite_encoding="nonfinite floats are explicit strings; no certified interval is issued from them")


def _metrics(run_id, cell_id, cell, delta, method, records, decisions, truths):
    suite = cell.suite_design.suite
    by_id = {record["query_id"]: record for record in records}
    covered, widths, nontrivial = [], [], []
    false_safe = false_violation = detected = improved = false_improved = noninferior = False
    primary_id = cell.suite_design.metadata.get("planted_query_id")
    primary_id = cell.family.canonical_id(primary_id) if primary_id is not None else None
    primary = None
    for query in cell.queries:
        record, truth = by_id[query.query_id], truths[query.query_id]
        boundary, decision = cell.thresholds[query.query_id], decisions[query.query_id]
        valid = record["status"] == CERTIFIED and not record.get("empty_intersection", False)
        covered.append(valid and record["lo"] <= truth <= record["hi"])
        false_safe |= decision == "CERTIFIED_SAFE" and truth > boundary
        false_violation |= decision == "CERTIFIED_VIOLATION" and truth <= boundary
        detected |= decision == "CERTIFIED_VIOLATION" and truth > boundary
        width = record["hi"] - record["lo"] if valid else None
        widths.append(width)
        lo, hi = cell.feasible_ranges[query.query_id]
        nontrivial.append(valid and hi > lo and width < hi - lo)
        if suite == "E3" and valid:
            # E3 is the risk-response contrast: negative is an improvement.
            improved |= record["hi"] < 0 and truth < 0
            false_improved |= record["hi"] < 0 and truth >= 0
            noninferior |= record["hi"] <= 0
        if query.query_id == primary_id:
            primary = dict(primary_target=truth, primary_threshold=boundary,
                primary_gap=cell.suite_design.metadata["gap"], primary_decision=decision,
                primary_certified_safe=decision == "CERTIFIED_SAFE",
                primary_certified_violation=decision == "CERTIFIED_VIOLATION",
                primary_false_safe=decision == "CERTIFIED_SAFE" and truth > boundary,
                primary_false_violation=decision == "CERTIFIED_VIOLATION" and truth <= boundary)
    numerical = any(record["status"] != CERTIFIED for record in records)
    empty = any(record.get("empty_intersection", False) for record in records)
    result = dict(run_id=run_id, cell=cell_id, method=method, delta=delta,
        family_size=cell.family.family_size, coverage_applicable=True,
        family_covered=bool(all(covered)), metrics_assessable=True,
        failure_status="NUMERICAL_FAILURE" if numerical else ("EMPTY_CONFIDENCE_SET" if empty else None),
        any_false_claim=bool(false_safe or false_violation), any_false_safe=bool(false_safe),
        any_false_violation=bool(false_violation), true_violation_detected=bool(detected),
        discovered_and_certified=False, returned=False, return_unsafe=False, return_safe_useful=False,
        return_endpoint_applicable=False, discovery_endpoint_applicable=False,
        endpoint_scope="fixed-family auditing; no discovery or policy-return experiment",
        mean_coordinate_width=None if any(width is None for width in widths) else float(np.mean(widths)),
        candidate_nontrivial_fraction=float(np.mean(nontrivial)),
        candidate_abstention_fraction=float(np.mean([value == "ABSTAIN" for value in decisions.values()])),
        contrast_improvement_detected=bool(improved), contrast_false_improvement=bool(false_improved),
        contrast_noninferiority_certified=bool(noninferior),
        contrast_endpoint_applicable=suite == "E3", primary_endpoint_applicable=suite == "E4",
        independent_replication_unit="one complete log shared by methods and both levels")
    if primary is not None:
        result.update(primary)
    return result


def extension_status(protocol_path, results_root, suite, *, list_ids=False):
    path = Path(protocol_path)
    if not path.exists():
        result = dict(status="NOT_FROZEN", suite=suite, completed=0,
            remaining=SUITE_UNITS[suite], legacy_new_outcome_draws=0,
            id_status="proposed identifiers only; no seeds allocated or drawn")
        if list_ids:
            result.update(completed_ids=[], remaining_ids=planned_extension_ids(suite))
        return result
    manifest = json.loads(path.read_text())
    if effective_suite(manifest["config"]) != suite:
        raise ValueError("requested suite differs from the immutable protocol")
    store = CheckpointStore(results_root, manifest)
    remaining = store.remaining_ids()
    completed = sorted(store.planned - set(remaining))
    result = dict(status="COMPLETE" if not remaining else "INCOMPLETE", suite=suite,
        fingerprint=manifest["fingerprint"], completed=len(completed), remaining=len(remaining),
        legacy_new_outcome_draws=0)
    if list_ids:
        result.update(completed_ids=completed, remaining_ids=remaining)
    return result


def run_extension(protocol_path, results_root, *, global_results_root=None,
                  max_new_units=None, draw_callback=None, oracle_callback=None,
                  resource_reader=None, progress=True):
    """Execute incomplete IDs synchronously; injected fixtures consume no science.

    The global root includes E1 and every new suite's checkpoint/artifact tree,
    so logs are counted once and method/level multiplicity cannot inflate units.
    """
    manifest = json.loads(Path(protocol_path).read_text())
    config, suite = manifest["config"], effective_suite(manifest["config"])
    fixture = config["suite"] == "DETERMINISTIC_EXTENSION_FIXTURE"
    if config.get("workers") != 1:
        raise ValueError("extension runner uses one synchronous CPU worker")
    if fixture and draw_callback is None:
        raise ValueError("deterministic fixture requires an explicit nonrandom callback")
    if not fixture:
        _validate_config(config, suite)
    if max_new_units is not None and (type(max_new_units) is not int or max_new_units < 0):
        raise ValueError("max_new_units must be a nonnegative integer")
    root = Path(results_root).resolve()
    global_root = Path(global_results_root or REPOSITORY / "results/post_cstat").resolve()
    if not root.is_relative_to(global_root):
        raise ValueError("global artifact root must include this suite's results directory")
    store = CheckpointStore(root, manifest)
    stamps, budget = _source_stamps(manifest), GlobalBudget(global_root)
    reader = resource_reader or resource_snapshot
    first_resource = reader(global_root)
    total_bytes, total_units = budget.scan()
    _resource_check(first_resource, total_bytes, config)
    remaining_start = store.remaining_ids()
    grouped = {}
    for run_id in remaining_start:
        parts = run_id.split("/")
        if parts[1] != suite or parts[2] not in suite_cells(suite):
            raise ValueError("run ID is outside the frozen extension suite")
        grouped.setdefault(parts[2], []).append(run_id)
    started, cpu_start = time.monotonic(), time.process_time()
    new, failed, status, reason = 0, 0, "COMPLETE", None
    try:
        for cell_id, run_ids in sorted(grouped.items()):
            if max_new_units is not None and new >= max_new_units:
                status = "CHECKPOINTED_INCOMPLETE"
                break
            cell, direct_plans, joint_plans, extra = build_extension_plans(config, cell_id)
            _save_cell_metadata(root, manifest, cell_id, cell, direct_plans, joint_plans, extra)
            for run_id in run_ids:
                if max_new_units is not None and new >= max_new_units:
                    status = "CHECKPOINTED_INCOMPLETE"
                    break
                stamps = _verify_changed_sources(manifest, stamps)
                total_bytes, total_units = budget.scan()
                _resource_check(reader(global_root), total_bytes, config)
                if total_units >= config.get("total_unit_cap", 32000):
                    raise ResourceLimitError("global new-unit cap reached; methods are not extra units")
                if store.load(run_id) is not None:
                    continue
                try:
                    result = _execute(manifest, run_id, cell_id, cell, direct_plans, joint_plans,
                                      draw_callback or draw_suite_log, oracle_callback or evaluate_suite_oracle)
                except Exception as exc:
                    result = dict(status="UNIT_FAILURE", suite=suite, cell=cell_id,
                        seed=_seed_for_run(config, run_id), seed_domain=config["seed_domain"],
                        legacy_new_outcome_draws=0, new_scientific_units=0 if fixture else 1,
                        full_family_failure=True, family_covered=False, unassessable_whole_trial=True,
                        failure_reason=f"{type(exc).__name__}: {exc}"[:4096], trials=[])
                store.complete(run_id, result)
                new += 1
                failed += result["status"] != "COMPLETE"
                total_bytes, total_units = budget.scan()
                if total_bytes > config.get("artifact_cap_bytes", int(1.5 * GIB)):
                    raise ResourceLimitError("global artifact cap reached after preserving the actual unit")
                if progress and new % 50 == 0:
                    print(json.dumps(dict(suite=suite, cell=cell_id, new_completed_units=new,
                        global_checkpoint_units=total_units, global_artifact_bytes=total_bytes)), flush=True)
                if result["status"] in ("ORACLE_FAILURE", "UNIT_FAILURE"):
                    status, reason = "ERROR_CHECKPOINTED", result["failure_reason"]
                    break
            # No outcome-dependent cache survives; one design cell at a time.
            del cell, direct_plans, joint_plans
            if status == "ERROR_CHECKPOINTED":
                break
    except ResourceLimitError as exc:
        status, reason = "RESOURCE_CHECKPOINTED", str(exc)
    except KeyboardInterrupt:
        status, reason = "INTERRUPTED", "execution stopped; no unattended continuation"
    except ValueError as exc:
        status, reason = "SOURCE_OR_MODEL_BLOCKED", str(exc)
    remaining = store.remaining_ids()
    if remaining and status == "COMPLETE":
        status = "CHECKPOINTED_INCOMPLETE"
    total_bytes, total_units = budget.scan()
    command = shlex.join([".venv/bin/python", "-m", "experiments.extension_runner", "--suite", suite,
        "--run", "--protocol", str(protocol_path), "--results", str(root),
        "--global-results", str(global_root)])
    invocation = dict(status=status, suite=suite, fingerprint=manifest["fingerprint"],
        new_completed_units=new, failed_units=failed, remaining_ids=remaining,
        legacy_new_outcome_draws=0, global_new_checkpoint_units=total_units,
        global_artifact_bytes=total_bytes, first_resource_snapshot=first_resource,
        stop_reason=reason, wall_seconds=time.monotonic() - started,
        cpu_seconds=time.process_time() - cpu_start, background_work_running=False,
        execution_mode="one synchronous CPU worker; other active suites require coordinator's <=2-worker total",
        resume_command=command)
    install_once(root / "invocations" / f"{time.time_ns()}.json", canonical_bytes(invocation) + b"\n")
    return invocation


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", required=True, choices=tuple(SUITE_UNITS))
    modes = parser.add_mutually_exclusive_group(required=True)
    for name in ("freeze", "run", "status", "analyze"):
        modes.add_argument("--" + name, action="store_true")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--inputs", type=Path, default=REPOSITORY / "task_materials/post_cstat")
    parser.add_argument("--protocol", type=Path)
    parser.add_argument("--results", type=Path)
    parser.add_argument("--global-results", type=Path, default=REPOSITORY / "results/post_cstat")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-new-units", type=int)
    parser.add_argument("--list-ids", action="store_true")
    args = parser.parse_args(argv)
    protocol = args.protocol or REPOSITORY / "results/post_cstat" / (args.suite + "_protocol.json")
    results = args.results or REPOSITORY / "results/post_cstat" / args.suite
    if args.freeze:
        if args.config is None:
            parser.error("--freeze requires --config")
        result = freeze_extension(args.config, args.inputs, protocol, args.suite)
    elif args.status:
        result = extension_status(protocol, results, args.suite, list_ids=args.list_ids)
    elif args.run:
        manifest = json.loads(protocol.read_text())
        if manifest["config"].get("suite") != args.suite:
            raise ValueError("CLI cannot execute a fixture or a different suite")
        result = run_extension(protocol, results, global_results_root=args.global_results,
                               max_new_units=args.max_new_units)
    else:
        if args.output is None:
            parser.error("--analyze requires a fresh --output directory")
        from experiments.extension_analyze import analyze_extension
        result = analyze_extension(protocol, results, args.output)
        result = {key: result[key] for key in ("status", "suite", "completed_units", "remaining_units")}
    print(json.dumps(result, indent=2, allow_nan=False))


def _execute(manifest, run_id, cell_id, cell, direct_plans, joint_plans,
             draw_callback, oracle_callback):
    config, suite = manifest["config"], effective_suite(manifest["config"])
    seed = _seed_for_run(config, run_id)
    started, cpu = time.monotonic(), time.process_time()
    log = draw_callback(cell.suite_design, seed)
    evaluated = []
    provenance = dict(data_digest=log.data_digest, seed_namespace=log.seed_namespace,
        code_hash=digest(manifest["sources"]), config_hash=digest(config),
        numerical_guard=config["numerical_guard"])
    for delta in config["levels"]:
        for method in methods_for_extension_cell(suite, cell_id):
            records = []
            if method == JOINT_LEVEL:
                try:
                    joint = joint_plans[float(delta)].evaluate(log.actions, log.outcomes, **provenance)
                    records = [joint["contrasts"][query.query_id] for query in cell.queries]
                except Exception as exc:
                    records = [_failure_coordinate(query, f"{type(exc).__name__}: {exc}") for query in cell.queries]
            else:
                for query, plan in zip(cell.queries, direct_plans[(float(delta), method)]):
                    try:
                        record = plan.evaluate(log.actions, log.outcomes, **provenance)
                        record["family_digest"] = cell.family.digest
                    except Exception as exc:
                        record = _failure_coordinate(query, f"{type(exc).__name__}: {exc}")
                    records.append(record)
            decisions = {record["query_id"]: certified_decision(record, cell.thresholds[record["query_id"]])
                         for record in records}
            evaluated.append((float(delta), method, records, decisions))
    # No certifier or decision engine has received oracle parameters.
    compact = []
    try:
        truths = oracle_callback(cell.suite_design)
        if suite == "E4":
            # The planted finite-design target is defined analytically as .4+gap.
            # Do not turn rounding of a trigonometric zero-sum into a true gap.
            original_id = cell.suite_design.metadata["planted_query_id"]
            truths[original_id] = 0.4 + cell.suite_design.metadata["gap"]
        truths = {query.query_id: float(truths[query.query_id]) for query in cell.queries}
        if not all(math.isfinite(value) for value in truths.values()):
            raise ValueError("nonfinite oracle target")
    except Exception as exc:
        return dict(status="ORACLE_FAILURE", suite=suite, cell=cell_id, seed=seed,
            seed_domain=config["seed_domain"], data_digest=log.data_digest,
            seed_namespace=log.seed_namespace, legacy_new_outcome_draws=0,
            new_scientific_units=0 if config["suite"] == "DETERMINISTIC_EXTENSION_FIXTURE" else 1,
            full_family_failure=True, family_covered=False, unassessable_whole_trial=True,
            failure_reason=f"{type(exc).__name__}: {exc}"[:4096], trials=[],
            certificate_records=[dict(delta=delta, method=method,
                coordinates=[_compact_record(record) for record in records], decisions=decisions)
                for delta, method, records, decisions in evaluated], failure_raw_debug=_raw_debug(log))
    trials = []
    extra_keys = ("family_size", "underlying_family_size", "coordinate_delta",
                  "contrast_failure_allocation", "derived_family_failure_delta")
    for delta, method, records, decisions in evaluated:
        trials.append(_metrics(run_id, cell_id, cell, delta, method, records, decisions, truths))
        coordinates = []
        for query, record in zip(cell.queries, records):
            coordinate = _compact_record(record)
            coordinate.update({key: record[key] for key in extra_keys if key in record})
            if record["status"] == CERTIFIED:
                error = record["estimate"] - truths[query.query_id]
                mass = cell.subgroup_masses[query.query_id]
                lo, hi = cell.feasible_ranges[query.query_id]
                coordinate.update(signed_error=error, absolute_error=abs(error),
                    normalized_error=error / mass if mass > 0 and query.normalizer == 1 else error,
                    normalized_radius=record["radius"] / mass if mass > 0 and query.normalizer == 1 else record["radius"],
                    feasible_width_ratio=((record["hi"] - record["lo"]) / (hi - lo))
                    if hi > lo and not record.get("empty_intersection", False) else None,
                    threshold=cell.thresholds[query.query_id], oracle_target=truths[query.query_id])
            coordinates.append(coordinate)
        compact.append(dict(delta=delta, method=method, family_size=cell.family.family_size,
            underlying_family_size=joint_plans[delta].underlying_family_size if method == JOINT_LEVEL else cell.family.family_size,
            coordinates=coordinates, decisions=decisions))
    numerical = any(trial["failure_status"] == "NUMERICAL_FAILURE" for trial in trials)
    coverage_failure = any(not trial["family_covered"] for trial in trials)
    status = "COMPLETE_WITH_NUMERICAL_FAILURE" if numerical else (
        "COMPLETE_WITH_CONFIDENCE_FAILURE" if coverage_failure else "COMPLETE")
    result = dict(status=status, suite=suite, cell=cell_id, seed=seed,
        seed_domain=config["seed_domain"], seed_namespace=log.seed_namespace,
        paired_replicate_id=f"{config['seed_domain']}/rep/{run_id.rsplit('/', 1)[1]}" if suite == "E2" else run_id,
        data_digest=log.data_digest, code_sha256=digest(manifest["sources"]),
        config_sha256=digest(config), git_sha=config.get("git_sha"),
        legacy_new_outcome_draws=0,
        new_scientific_units=0 if config["suite"] == "DETERMINISTIC_EXTENSION_FIXTURE" else 1,
        family_size=cell.family.family_size, family_digest=cell.family.digest,
        raw_N=cell.n, truths=truths, trials=trials, certificate_records=compact,
        oracle_order="all methods and decisions finished before oracle evaluation",
        E4_primary_truth_rule="analytic .4+gap, assigned after methods" if suite == "E4" else None,
        cell_design_metadata=f"cell_designs/{cell_id}.json.gz",
        wall_seconds=time.monotonic() - started, cpu_seconds=time.process_time() - cpu)
    if suite == "E2":
        half = cell.n // 2
        result["paired_audited_region_sha256"] = hashlib.sha256(
            log.actions[:half].tobytes() + log.outcomes[:half].astype("<f8").tobytes()).hexdigest()
    if run_id in config["raw_debug_run_ids"]:
        result["prespecified_raw_debug"] = _raw_debug(log)
    if numerical or coverage_failure:
        result["failure_raw_debug"] = _raw_debug(log)
    return result


if __name__ == "__main__":
    main()

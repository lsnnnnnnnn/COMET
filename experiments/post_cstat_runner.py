"""Recoverable E1 execution only; E2--E6 are not implemented by this runner.

No draw is possible from the CLI without a new frozen E1 protocol containing the
available planning inputs plus explicit user input-resolution receipts, explicit
tuning/seed/decision choices, committed
science and theorem hashes. E0 is closed and never imported or replayed here.
Run synchronously; an ended invocation never implies unattended continuation.
"""

import argparse
from dataclasses import fields
import gzip
import hashlib
import itertools
import json
import math
import platform
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time

import numpy as np

from comet.checkpoint_store import (
    CheckpointStore, NAMESPACE, canonical_bytes, digest, file_hashes,
    freeze_protocol, install_once, planning_input_hashes,
)
from comet.residual_truncation import CERTIFIED, certified_decision, make_plan
from experiments.core_graph_dgp import build_core_design, draw_core_log, evaluate_oracle


GRAPHS = ("independent", "cycle", "triangles")
OVERLAPS = ("moderate", "weak")
OUTCOMES = ("bounded", "heavy")
CORE_METHODS = ("comet_local", "generic_matched", "truncated_local",
                "truncated_global_graph", "truncated_global_envelope", "colorwise_truncation")
BOUNDED_METHODS = ("graph_hoeffding", "graph_bernstein",
                   "graph_hoeffding_global", "graph_bernstein_global")
LEVELS = (0.05, 0.10)
GIB = 2**30
UNIT_RESERVE = 8 * 2**20
REPOSITORY = Path(__file__).resolve().parents[1]
SOURCE_NAMES = (
    "comet/queries.py", "comet/source_graph.py", "comet/residual_truncation.py",
    "comet/checkpoint_store.py", "comet/post_cstat_statistics.py",
    "comet/metrics.py", "comet/gate_c_statistics.py",
    "experiments/core_graph_dgp.py", "experiments/post_cstat_runner.py",
    "theory/global_residual_truncation.md", "theory/query_specific_cost_lower_bound.md",
)


class ResourceLimitError(RuntimeError):
    pass


def environment_signature():
    return dict(python=platform.python_version(), implementation=platform.python_implementation(),
                numpy=np.__version__, machine=platform.machine(),
                platform=platform.platform(), byteorder=sys.byteorder)


def e1_cells():
    return [f"{graph}-{overlap}-{outcome}"
            for graph, overlap, outcome in itertools.product(GRAPHS, OVERLAPS, OUTCOMES)]


def planned_e1_ids():
    """Proposed identifiers; not allocated seeds until a protocol is frozen."""
    return [f"{NAMESPACE}/E1/{cell}/{rep:04d}" for cell in e1_cells() for rep in range(1000)]


def methods_for_cell(cell):
    return CORE_METHODS + (BOUNDED_METHODS if cell.endswith("-bounded") else ())


def primary_e1_comparisons():
    """New primary implementation-diagnostic family, distinct from old 17."""
    return [[cell, method] for cell in e1_cells() for method in methods_for_cell(cell)]


def _validate_e1_config(config):
    required = ("truncation_multipliers", "truncation_grid_source", "master_seed",
                "seed_domain", "normalized_risk_threshold", "planning_inputs_reconciled",
                "theorem_status", "numerical_guard", "raw_debug_run_ids")
    missing = [key for key in required if key not in config]
    if missing:
        raise ValueError("explicit E1 configuration fields required: " + ", ".join(missing))
    factors = config["truncation_multipliers"]
    if not factors or any(not isinstance(x, (int, float)) or not math.isfinite(x) or x <= 0 for x in factors):
        raise ValueError("an explicit positive truncation grid is required; no THEORY_NOTE grid is assumed")
    if not isinstance(config["truncation_grid_source"], str) or not config["truncation_grid_source"]:
        raise ValueError("name the reconciled planning source of the truncation grid")
    if config["planning_inputs_reconciled"] is not True:
        raise ValueError("all six planning inputs must be reconciled before freeze")
    if config["theorem_status"] != "PROVED_UNDER_DECLARED_ASSUMPTIONS":
        raise ValueError("the core theorem must be proved before certified E1 execution")
    if config.get("production_environment") != environment_signature():
        raise ValueError("freeze must name the actual selected production environment")
    if type(config["master_seed"]) is not int or config["master_seed"] < 0:
        raise ValueError("an explicit nonnegative new-study master seed is required")
    if not isinstance(config["seed_domain"], str) or not config["seed_domain"].startswith(NAMESPACE + "/"):
        raise ValueError("a new-workstream seed domain is required")
    if not 0 <= config["normalized_risk_threshold"] <= 1 or not math.isfinite(config["numerical_guard"]) or config["numerical_guard"] < 0:
        raise ValueError("finite declared decision threshold and numerical guard required")
    fixed = dict(namespace=NAMESPACE, suite="E1", N=32768, replications_per_cell=1000,
                 cells=e1_cells(), levels=list(LEVELS), family_size=16, workers=1,
                 legacy_new_outcome_draws=0, primary_units=12000,
                 total_primary_goal_units=29600, total_unit_cap=32000,
                 planned_run_ids=planned_e1_ids(), primary_comparisons=primary_e1_comparisons(),
                 artifact_cap_bytes=int(1.5 * GIB), minimum_free_disk_bytes=2 * GIB,
                 worker_memory_cap_bytes=4 * GIB,
                 implemented_suite_scope="E1 only; E2--E6 are not implemented here")
    for key, value in fixed.items():
        if key in config and config[key] != value:
            raise ValueError("E1 fixed protocol mismatch: " + key)
    if not isinstance(config["raw_debug_run_ids"], list) or not set(config["raw_debug_run_ids"]) <= set(fixed["planned_run_ids"]):
        raise ValueError("representative raw debug IDs must be prespecified E1 IDs")
    return dict(config, **fixed)


def freeze_e1(config_path, input_directory, protocol_path):
    """Freeze E1 only; missing inputs or uncommitted scientific sources refuse."""
    # Fail on missing actual files before any claim of a protocol freeze.
    config_path = Path(config_path).resolve()
    raw_config = json.loads(config_path.read_text())
    planning_input_hashes(input_directory,
        allowed_missing=raw_config.get("allowed_missing_planning_inputs", ()))
    config = _validate_e1_config(raw_config)
    sources = [REPOSITORY / name for name in SOURCE_NAMES] + [config_path]
    git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPOSITORY, text=True).strip()
    for source in sources:
        try:
            relative = source.relative_to(REPOSITORY)
        except ValueError as exc:
            raise ValueError("the executable E1 config must be committed inside the research repository") from exc
        status = subprocess.check_output(["git", "status", "--porcelain", "--", str(relative)],
                                         cwd=REPOSITORY, text=True)
        if status:
            raise ValueError("commit scientific/config/theorem sources before freeze: " + str(relative))
    config["git_sha"] = git_sha
    config["input_config_sha256"] = hashlib.sha256(config_path.read_bytes()).hexdigest()
    config["baseline_e0_anchor"] = "ca5bb878cf9635fac4381d03281df0bc8a900daa"
    config["equivalent_methods"] = [["comet_local", "generic_matched"]]
    return freeze_protocol(protocol_path, config, sources, input_directory)


def resource_snapshot(root):
    """Inspect disk/RAM/current RSS without allocating a resource test workload."""
    parent = Path(root)
    while not parent.exists():
        parent = parent.parent
    try:
        import psutil
        available = int(psutil.virtual_memory().available)
        rss = int(psutil.Process().memory_info().rss)
    except (ImportError, OSError) as exc:
        raise ResourceLimitError("cannot inspect free RAM/current RSS: " + str(exc)) from exc
    return dict(free_disk_bytes=int(shutil.disk_usage(parent).free),
                available_ram_bytes=available, worker_rss_bytes=rss,
                memory_scope="one synchronous worker RSS; no concurrent-peak sum inferred")


def _resource_check(snapshot, artifact_bytes, config):
    if snapshot["free_disk_bytes"] < config.get("minimum_free_disk_bytes", 2 * GIB) + UNIT_RESERVE:
        raise ResourceLimitError("less than the required 2 GiB free-disk reserve")
    if artifact_bytes + UNIT_RESERVE > config.get("artifact_cap_bytes", int(1.5 * GIB)):
        raise ResourceLimitError("new compressed-artifact cap has insufficient next-unit reserve")
    if snapshot["available_ram_bytes"] < 512 * 2**20:
        raise ResourceLimitError("less than 512 MiB currently available RAM; checkpoint before further draws")
    if snapshot["worker_rss_bytes"] > config.get("worker_memory_cap_bytes", 4 * GIB):
        raise ResourceLimitError("single worker exceeded the 4 GiB memory cap")


def _source_stamps(manifest):
    return {path: (Path(path).stat().st_size, Path(path).stat().st_mtime_ns)
            for path in manifest["sources"]}


def _verify_changed_sources(manifest, stamps):
    current = _source_stamps(manifest)
    changed = [path for path in current if current[path] != stamps[path]]
    if changed and any(value != manifest["sources"][path]
                       for path, value in file_hashes(changed).items()):
        raise ValueError("scientific source changed after freeze")
    return current


def _seed(config, run_id):
    payload = f"{config['seed_domain']}\0{config['master_seed']}\0{run_id}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "little")


def _build_cell(config, cell):
    graph, overlap, outcome = cell.split("-")
    design = build_core_design(config["N"], graph, overlap, outcome,
                               namespace=config["seed_domain"] + "/" + cell)
    if len(design.queries) != config["family_size"]:
        raise ValueError("the actual coordinate family differs from the frozen m")
    plans = {}
    for delta, method in itertools.product(config["levels"], methods_for_cell(cell)):
        plans[(float(delta), method)] = tuple(
            make_plan(query, **design.certifier_inputs, delta=float(delta),
                      family_size=len(design.queries), multipliers=config["truncation_multipliers"],
                      method=method)
            for query in design.queries
        )
    return design, plans


def _cell_metadata(manifest, cell, design, plans):
    excluded = {"weights", "nuisance", "supported_exposures", "row_thresholds", "assumptions"}
    exported = []
    for (delta, method), coordinate_plans in plans.items():
        for plan in coordinate_plans:
            record = {field.name: getattr(plan, field.name) for field in fields(plan)
                      if field.name not in excluded}
            record["assumptions"] = plan.assumptions.__dict__
            record["radius"] = plan.radius
            record["row_thresholds_sha256"] = (hashlib.sha256(plan.row_thresholds.tobytes()).hexdigest()
                                                if plan.row_thresholds is not None else None)
            record["delta"] = delta
            record["method"] = method
            exported.append(record)
    return dict(fingerprint=manifest["fingerprint"], cell=cell, raw_N=design.n,
        family_size=len(design.queries), source_graph_model="independent primitives projected by row-source intersection",
        graph_colors=design.graph.color_count, graph_edges=design.graph.edge_count,
        hidden_source_detection="not_claimed; source sufficiency is a model assumption",
        logging_law="exact 32-bit dyadic integer-cutoff Bernoulli per row",
        exposure_sha256=hashlib.sha256(design.exposure.tobytes()).hexdigest(),
        common_nuisance_sha256=hashlib.sha256(design.nuisance.tobytes()).hexdigest(),
        common_residual_moments_sha256=hashlib.sha256(design.residual_moments.tobytes()).hexdigest(),
        information_equality="all eligible methods receive identical e, nuisance, residual moments, source graph and support",
        equivalent_method_names=["comet_local", "generic_matched"],
        subgroup_masses=dict(design.subgroup_masses), plans=exported)


def _install_metadata(root, manifest, cell, design, plans):
    path = Path(root) / "cell_designs" / (cell + ".json.gz")
    expected = canonical_bytes(_cell_metadata(manifest, cell, design, plans))
    if path.exists():
        if gzip.decompress(path.read_bytes()) != expected:
            raise ValueError("saved cell design metadata changed or is corrupt")
        return 0
    content = gzip.compress(expected, mtime=0)
    install_once(path, content)
    return len(content)


def _trial_metrics(run_id, cell, delta, method, certificates, decisions, truths, design, threshold):
    by_id = {record["query_id"]: record for record in certificates}
    any_failure = any(record["status"] != CERTIFIED for record in certificates)
    empty = any(record.get("empty_intersection", False) for record in certificates)
    covered, false_safe, false_violation, detected = [], False, False, False
    widths, nontrivial = [], []
    for query in design.queries:
        record, truth = by_id[query.query_id], truths[query.query_id]
        mass = design.subgroup_masses[query.query_id]
        boundary = threshold * mass
        decision = decisions[query.query_id]
        valid = record["status"] == CERTIFIED and not record.get("empty_intersection", False)
        covered.append(valid and record["lo"] <= truth <= record["hi"])
        false_safe |= decision == "CERTIFIED_SAFE" and truth > boundary
        false_violation |= decision == "CERTIFIED_VIOLATION" and truth <= boundary
        detected |= decision == "CERTIFIED_VIOLATION" and truth > boundary
        width = record["hi"] - record["lo"] if valid else None
        widths.append(width)
        nontrivial.append(valid and mass > 0 and width < mass)
    return dict(run_id=run_id, cell=cell, method=method, delta=delta,
        coverage_applicable=True, family_covered=bool(all(covered)),
        failure_status="NUMERICAL_FAILURE" if any_failure else ("EMPTY_CONFIDENCE_SET" if empty else None),
        any_false_claim=bool(false_safe or false_violation), any_false_safe=bool(false_safe),
        any_false_violation=bool(false_violation), true_violation_detected=bool(detected),
        discovered_and_certified=False, returned=False, return_unsafe=False, return_safe_useful=False,
        return_endpoint_applicable=False, discovery_endpoint_applicable=False,
        endpoint_scope="E1 frozen-family auditing; no policy-return or discovery experiment",
        mean_coordinate_width=None if any(width is None for width in widths) else float(np.mean(widths)),
        candidate_nontrivial_fraction=float(np.mean(nontrivial)),
        candidate_abstention_fraction=float(np.mean([value == "ABSTAIN" for value in decisions.values()])),
        independent_replication_unit="one complete log shared by all methods and levels")


def _compact_record(record):
    keys = ("query_id", "status", "estimate", "lo", "hi", "raw_lo", "raw_hi",
            "empty_intersection", "radius", "bias", "concentration", "range_contribution",
            "numerical_guard", "selected_method", "reason")
    return {key: record[key] for key in keys if key in record}


def _execute_one(manifest, run_id, cell, design, plans, draw_callback, oracle_callback):
    config = manifest["config"]
    seed = _seed(config, run_id)
    began, cpu_start = time.monotonic(), time.process_time()
    log = draw_callback(design, seed)
    evaluated = []
    # Finish EVERY method and decision before requesting any oracle truth.
    for (delta, method), coordinate_plans in plans.items():
        certificates, decisions = [], {}
        for query, plan in zip(design.queries, coordinate_plans):
            try:
                record = plan.evaluate(log.actions, log.outcomes,
                    data_digest=log.data_digest, seed_namespace=log.seed_namespace,
                    code_hash=digest(manifest["sources"]), config_hash=digest(config),
                    numerical_guard=config["numerical_guard"])
                decision = certified_decision(record, config["normalized_risk_threshold"] *
                                               design.subgroup_masses[query.query_id])
            except (ValueError, ArithmeticError) as exc:
                record = dict(query_id=query.query_id, status="NUMERICAL_FAILURE", reason=str(exc)[:2048],
                              empty_intersection=True)
                decision = "ABSTAIN"
            certificates.append(record)
            decisions[query.query_id] = decision
        evaluated.append((delta, method, certificates, decisions))
    records = [dict(delta=delta, method=method, coordinates=[_compact_record(value) for value in certificates],
                    decisions=decisions) for delta, method, certificates, decisions in evaluated]
    try:
        truths = oracle_callback(design)
        if set(truths) != {query.query_id for query in design.queries} or not all(math.isfinite(value) for value in truths.values()):
            raise ValueError("missing or nonfinite analysis-only truths")
    except Exception as exc:
        return dict(status="ORACLE_FAILURE", suite="E1", cell=cell, seed=seed,
            seed_domain=config["seed_domain"], data_digest=log.data_digest,
            seed_namespace=log.seed_namespace, legacy_new_outcome_draws=0,
            failure_reason=f"{type(exc).__name__}: {exc}"[:4096], full_family_failure=True,
            unassessable_whole_trial=True, family_covered=False, trials=[],
            certificate_records=records,
            failure_raw_debug=dict(actions=log.actions.tolist(), outcomes=log.outcomes.tolist()),
            new_scientific_units=0 if config.get("suite") == "DETERMINISTIC_RUNNER_FIXTURE" else 1)
    trials = [_trial_metrics(run_id, cell, delta, method, certificates, decisions, truths, design,
                            config["normalized_risk_threshold"])
              for delta, method, certificates, decisions in evaluated]
    numerical_failure = any(t["failure_status"] == "NUMERICAL_FAILURE" for t in trials)
    confidence_failure = any(not t["family_covered"] for t in trials)
    status = "COMPLETE_WITH_NUMERICAL_FAILURE" if numerical_failure else (
        "COMPLETE_WITH_CONFIDENCE_FAILURE" if confidence_failure else "COMPLETE")
    result = dict(status=status,
        suite="E1", cell=cell, seed=seed, seed_domain=config["seed_domain"],
        data_digest=log.data_digest, seed_namespace=log.seed_namespace,
        code_sha256=digest(manifest["sources"]), config_sha256=digest(config),
        git_sha=config.get("git_sha"), legacy_new_outcome_draws=0,
        new_scientific_units=0 if config.get("suite") == "DETERMINISTIC_RUNNER_FIXTURE" else 1,
        family_size=len(design.queries), raw_N=design.n, truths=truths,
        trials=trials, certificate_records=records,
        oracle_order="all method intervals and decisions completed before oracle evaluation",
        cell_design_metadata=f"cell_designs/{cell}.json.gz",
        wall_seconds=time.monotonic() - began, cpu_seconds=time.process_time() - cpu_start)
    if run_id in config["raw_debug_run_ids"]:
        result["prespecified_raw_debug"] = dict(actions=log.actions.tolist(), outcomes=log.outcomes.tolist())
    if numerical_failure or confidence_failure:
        result["failure_raw_debug"] = dict(actions=log.actions.tolist(), outcomes=log.outcomes.tolist())
    return result


def protocol_status(protocol_path, results_root, *, list_ids=False):
    protocol_path = Path(protocol_path)
    if not protocol_path.exists():
        result = dict(status="NOT_FROZEN", scope="E1 only", completed=0, remaining=12000,
                      legacy_new_outcome_draws=0, other_suites_implemented=False,
                      id_status="reserved proposed identifiers; no seeds allocated or consumed")
        if list_ids:
            result.update(completed_ids=[], remaining_ids=planned_e1_ids())
        return result
    manifest = json.loads(protocol_path.read_text())
    store = CheckpointStore(results_root, manifest)
    remaining = store.remaining_ids()
    completed = sorted(store.planned - set(remaining))
    result = dict(status="COMPLETE" if not remaining else "INCOMPLETE", scope="E1 only",
                  fingerprint=manifest["fingerprint"], completed=len(completed), remaining=len(remaining),
                  legacy_new_outcome_draws=0, other_suites_implemented=False)
    if list_ids:
        result.update(completed_ids=completed, remaining_ids=remaining)
    return result


def run_e1(protocol_path, results_root, *, max_new_units=None, draw_callback=None,
           oracle_callback=None, resource_reader=None):
    """Resume incomplete IDs synchronously; completed bytes are only read.

    Callback injection is for deterministic test fixtures. CLI execution never
    supplies injected callbacks or accepts a deterministic-fixture protocol.
    """
    manifest = json.loads(Path(protocol_path).read_text())
    config = manifest["config"]
    if config.get("suite") not in ("E1", "DETERMINISTIC_RUNNER_FIXTURE") or config.get("workers") != 1:
        raise ValueError("this runner implements E1 with one synchronous CPU worker")
    if config.get("suite") == "E1" and config.get("production_environment") != environment_signature():
        raise ValueError("execution environment differs from the frozen production environment")
    if config["suite"] == "DETERMINISTIC_RUNNER_FIXTURE" and draw_callback is None:
        raise ValueError("deterministic fixtures require an explicit nonrandom draw callback")
    if max_new_units is not None and (type(max_new_units) is not int or max_new_units < 0):
        raise ValueError("max_new_units must be a nonnegative integer")
    store = CheckpointStore(results_root, manifest)
    stamps = _source_stamps(manifest)
    root = Path(results_root)
    artifact_bytes = sum(path.stat().st_size for path in root.rglob("*") if path.is_file()) if root.exists() else 0
    reader = resource_reader or resource_snapshot
    first_resource = reader(root)
    _resource_check(first_resource, artifact_bytes, config)
    initial = store.remaining_ids()
    by_cell = {}
    for run_id in initial:
        by_cell.setdefault(run_id.split("/")[2], []).append(run_id)
    new, failures, status, stop_reason = 0, 0, "COMPLETE", None
    started, cpu_start = time.monotonic(), time.process_time()
    try:
        for cell, ids in sorted(by_cell.items()):
            if max_new_units is not None and new >= max_new_units:
                status = "CHECKPOINTED_INCOMPLETE"
                break
            design, plans = _build_cell(config, cell)
            artifact_bytes += _install_metadata(root, manifest, cell, design, plans)
            for run_id in ids:
                if max_new_units is not None and new >= max_new_units:
                    status = "CHECKPOINTED_INCOMPLETE"
                    break
                stamps = _verify_changed_sources(manifest, stamps)
                _resource_check(reader(root), artifact_bytes, config)
                # Another completed ID can only be read, never redrawn.
                if store.load(run_id) is not None:
                    continue
                try:
                    result = _execute_one(manifest, run_id, cell, design, plans,
                        draw_callback or draw_core_log, oracle_callback or evaluate_oracle)
                except Exception as exc:
                    # The unit remains an immutable failed trial with its ID and
                    # seed. It is not removed or silently retried as new evidence.
                    result = dict(status="UNIT_FAILURE", suite="E1", cell=cell,
                        failure_reason=f"{type(exc).__name__}: {exc}"[:4096], seed=_seed(config, run_id),
                        seed_domain=config["seed_domain"], legacy_new_outcome_draws=0,
                        family_covered=False, full_family_failure=True,
                        unassessable_whole_trial=True, trials=[],
                        new_scientific_units=0 if config["suite"] == "DETERMINISTIC_RUNNER_FIXTURE" else 1)
                payload = store.complete(run_id, result)
                artifact_bytes += store.path(run_id).stat().st_size
                new += 1
                failures += result["status"] != "COMPLETE"
                if artifact_bytes > config.get("artifact_cap_bytes", int(1.5 * GIB)):
                    raise ResourceLimitError("artifact cap reached after preserving the completed unit")
                if result["status"] in ("UNIT_FAILURE", "ORACLE_FAILURE"):
                    status, stop_reason = "ERROR_CHECKPOINTED", result["failure_reason"]
                    break
            # Only one cell's outcome-free design/plan cache is retained.
            del design, plans
            if status == "ERROR_CHECKPOINTED":
                break
    except ResourceLimitError as exc:
        status, stop_reason = "RESOURCE_CHECKPOINTED", str(exc)
    except KeyboardInterrupt:
        status, stop_reason = "INTERRUPTED", "execution stopped; no unattended continuation"
    except ValueError as exc:
        status, stop_reason = "SOURCE_OR_PROTOCOL_BLOCKED", str(exc)
    remaining = store.remaining_ids()
    if remaining and status == "COMPLETE":
        status = "CHECKPOINTED_INCOMPLETE"
    invocation = dict(status=status, scope="E1 only", new_completed_units=new, failed_units=failures,
        remaining_ids=remaining, legacy_new_outcome_draws=0, fingerprint=manifest["fingerprint"],
        stop_reason=stop_reason, wall_seconds=time.monotonic() - started,
        cpu_seconds=time.process_time() - cpu_start, first_resource_snapshot=first_resource,
        artifact_bytes=artifact_bytes, background_work_running=False,
        execution_mode="one synchronous CPU worker; no GPU/paid compute",
        resume_command=f".venv/bin/python -m experiments.post_cstat_runner --run-E1 --protocol {Path(protocol_path)} --results {root}")
    name = f"{time.time_ns()}.json"
    install_once(root / "invocations" / name, canonical_bytes(invocation) + b"\n")
    return invocation


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--status", action="store_true")
    mode.add_argument("--freeze-E1", action="store_true")
    mode.add_argument("--run-E1", action="store_true")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--inputs", type=Path, default=REPOSITORY / "task_materials/post_cstat")
    parser.add_argument("--protocol", type=Path, default=REPOSITORY / "results/post_cstat/E1_protocol.json")
    parser.add_argument("--results", type=Path, default=REPOSITORY / "results/post_cstat/E1")
    parser.add_argument("--max-new-units", type=int)
    parser.add_argument("--list-ids", action="store_true")
    args = parser.parse_args(argv)
    if args.status:
        result = protocol_status(args.protocol, args.results, list_ids=args.list_ids)
    elif getattr(args, "freeze_E1"):
        if args.config is None:
            parser.error("--freeze-E1 requires an explicit --config")
        result = freeze_e1(args.config, args.inputs, args.protocol)
    else:
        manifest = json.loads(args.protocol.read_text())
        if manifest["config"].get("suite") != "E1":
            raise ValueError("the CLI cannot run a deterministic test-fixture protocol")
        result = run_e1(args.protocol, args.results, max_new_units=args.max_new_units)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()

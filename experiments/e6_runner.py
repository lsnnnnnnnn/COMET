"""Data-gated finite-population E6 driver; no alternate data or automatic run.

The ACS archive and exact household-protected population must exist and match a
prepared receipt before a production protocol can be frozen. All repeated
trials randomize source-separated selective logging/pipeline information over
the same fixed population; they are not new people or causal interventions.
The frozen E5 fitting/certification/selection controller is reused with an E6
logger and an independent finite-population evaluator, never its synthetic
response generator or oracle.
"""

import argparse
from collections import defaultdict
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
import shlex
import subprocess
import time

import numpy as np

from comet.checkpoint_store import (CheckpointStore, NAMESPACE, canonical_bytes,
    digest, freeze_protocol, install_once, planning_input_hashes)
from comet.residual_truncation import CERTIFIED
from experiments.extension_runner import GlobalBudget
from experiments.pipeline_dgp import TRADEOFF_GRID
from experiments.pipeline_runner import (ARMS, CERTIFIED_ARMS, CachedSupportGraph,
    _execute_trial, factorized_p2_grid_choice)
from experiments.post_cstat_runner import (GIB, LEVELS, REPOSITORY, SOURCE_NAMES,
    ResourceLimitError, _resource_check, _source_stamps, _verify_changed_sources,
    environment_signature, resource_snapshot)
from experiments.semisynthetic_selective_labels import (
    ArchiveSpec, AvailabilityBlockedError, DatasetBlockedError, DEFAULT_SPLIT_SIZES,
    LOGGER_AMENDMENT, OFFICIAL_URL, WORD_GRID, _file_sha256, build_semisynthetic_design,
    load_acs_archive,
)


EXTRA_SOURCES = ("comet/audit_pipeline.py", "comet/policy_update.py",
    "experiments/pipeline_dgp.py", "experiments/pipeline_runner.py",
    "experiments/extension_runner.py", "comet/paired_contrasts.py", "experiments/suite_designs.py",
    "experiments/semisynthetic_selective_labels.py", "experiments/e6_runner.py",
    "experiments/e6_analyze.py", "experiments/post_cstat_analyze.py")


def e6_cell_ids():
    return [f"{overlap}-logger{graph}" for overlap in ("moderate", "weak")
            for graph in ("independent", "cycle")]


def planned_e6_ids():
    return [f"{NAMESPACE}/E6/{cell}/{rep:04d}" for cell in e6_cell_ids() for rep in range(250)]


def primary_e6_comparisons():
    return [[cell, arm] for cell in e6_cell_ids() for arm in CERTIFIED_ARMS]


def _path(value):
    path = Path(value)
    return path.resolve() if path.is_absolute() else (REPOSITORY / path).resolve()


def _validate_config(config):
    required = ("archive_path", "archive_sha256", "prepared_directory", "master_seed", "seed_domain",
        "truncation_multipliers", "truncation_grid_source", "planning_inputs_reconciled",
        "theorem_status", "numerical_guard", "raw_debug_run_ids", "analysis_bootstrap_seed",
        "analysis_bootstrap_resamples", "production_environment")
    if any(key not in config for key in required):
        raise ValueError("explicit data-gated E6 configuration required: " + ", ".join(required))
    archive_spec = ArchiveSpec(config["archive_sha256"])
    config = dict(config, archive_sha256=archive_spec.expected_sha256)
    if config["truncation_multipliers"] != [2 ** (j / 4) for j in range(-24, 25)]:
        raise ValueError("E6 uses the reconciled 49-point THEORY_NOTE grid")
    if not config["truncation_grid_source"] or config["planning_inputs_reconciled"] is not True:
        raise ValueError("record the actually reconciled inputs and grid source")
    if config["theorem_status"] != "PROVED_UNDER_DECLARED_ASSUMPTIONS":
        raise ValueError("valid E6 certificate paths require completed proofs")
    if any(type(config[key]) is not int or config[key] < 0 for key in ("master_seed", "analysis_bootstrap_seed")):
        raise ValueError("nonnegative explicit generation and analysis seeds required")
    if not isinstance(config["seed_domain"], str) or not config["seed_domain"].startswith(NAMESPACE + "/E6"):
        raise ValueError("use a separate E6 seed domain")
    if config["analysis_bootstrap_resamples"] != 2000:
        raise ValueError("E6 performance analysis uses the frozen 2000 paired resamples")
    if not math.isfinite(config["numerical_guard"]) or config["numerical_guard"] < 0:
        raise ValueError("nonnegative finite numerical padding required")
    fixed = dict(namespace=NAMESPACE, suite="E6", workers=1, cells=e6_cell_ids(),
        replications_per_cell=250, split_sizes=dict(DEFAULT_SPLIT_SIZES), levels=list(LEVELS),
        risk_threshold=0.32, utility_margin=0.01, service_floor=0.2, capacity_ceiling=0.6,
        ridge=1.0, max_rules=4, max_depth=4, minimum_mass=0.02, tradeoff_grid=list(TRADEOFF_GRID),
        arms=list(ARMS), certified_arms=list(CERTIFIED_ARMS), primary_units=1000,
        total_primary_goal_units=29600, total_unit_cap=32000, legacy_new_outcome_draws=0,
        planned_run_ids=planned_e6_ids(), primary_comparisons=primary_e6_comparisons(),
        selected_dataset=dict(state="CA", year=2018, survey="1-Year", official_archive=OFFICIAL_URL),
        cycle_logger=LOGGER_AMENDMENT["main_cycle_logger"],
        source_selector_joint_law=LOGGER_AMENDMENT["neighbor_joint_law"],
        artifact_cap_bytes=int(1.5 * GIB), minimum_free_disk_bytes=2 * GIB,
        worker_memory_cap_bytes=4 * GIB,
        family_size_rule="actual deduplicated risk AND utility family after independent observed-label discovery",
        randomization_scope="fresh masks and pipeline information on one fixed population; not new individuals")
    for key, value in fixed.items():
        if key in config and config[key] != value:
            raise ValueError("E6 fixed pre-outcome choice differs: " + key)
    if not isinstance(config["raw_debug_run_ids"], list) or not set(config["raw_debug_run_ids"]) <= set(fixed["planned_run_ids"]):
        raise ValueError("raw cases must be declared E6 run IDs before outcomes")
    return dict(config, **fixed)


def load_prepared_e6(config):
    """Verify actual data and exact population availability; never substitute."""
    archive, prepared = _path(config["archive_path"]), _path(config["prepared_directory"])
    if not archive.is_file() or not (prepared / "manifest.json").is_file():
        raise DatasetBlockedError("DATA_BLOCKED: actual selected archive and prepared receipt are required before E6 freeze/run")
    receipt = json.loads((prepared / "manifest.json").read_text())
    metadata = receipt.get("metadata", {})
    if receipt.get("status") != "OFFLINE_PREPARED_NOT_E6_EXPERIMENT" or metadata.get("data_status") != "ARCHIVE_PREPARED_NOT_E6_EXPERIMENT":
        raise DatasetBlockedError("DATA_BLOCKED: a deterministic fixture or blocked receipt cannot become a real E6 population")
    if (metadata.get("source_url"), metadata.get("state"), metadata.get("year"), metadata.get("survey")) != (OFFICIAL_URL, "CA", 2018, "1-Year"):
        raise DatasetBlockedError("prepared population is not the selected official CA-2018 archive")
    if metadata.get("archive_sha256") != config["archive_sha256"]:
        raise DatasetBlockedError("prepared/archive source receipts disagree")
    data_paths = [archive, prepared / "manifest.json"]
    outputs = receipt.get("outputs", {})
    if not {"covariates.npz", "household_splits.json", "README.md"} <= set(outputs):
        raise DatasetBlockedError("prepared covariates and household registry are incomplete")
    for name in ("covariates.npz", "household_splits.json", "README.md"):
        path = prepared / name
        if not path.is_file() or _file_sha256(path) != outputs[name]:
            raise DatasetBlockedError("prepared data output is missing or corrupt: " + name)
        data_paths.append(path)
    vault = load_acs_archive(archive, ArchiveSpec(config["archive_sha256"]))
    view = vault.certifier_view
    if receipt.get("population_digest") != view.population_digest:
        raise DatasetBlockedError("prepared fixed-population digest differs from the actual archive")
    sizes = config.get("split_sizes", DEFAULT_SPLIT_SIZES)
    design = build_semisynthetic_design(view, "independent", "moderate",
        namespace=config["seed_domain"] + "/availability-check", split_sizes=sizes)
    registry = json.loads((prepared / "household_splits.json").read_text())
    expected_rows = {name: split.row_indices.tolist() for name, split in design.splits.items()}
    if (registry.get("population_digest") != view.population_digest or
        registry.get("split_rows") != expected_rows or registry.get("split_sizes") != sizes or
        receipt.get("split_sizes") != sizes or registry.get("people_duplicated") is not False or
        registry.get("households_cross_split") is not False or registry.get("labels_exported") is not False):
        raise AvailabilityBlockedError("AVAILABILITY_BLOCKED: exact household-protected split registry does not match the declared population")
    with np.load(prepared / "covariates.npz", allow_pickle=False) as arrays:
        if set(arrays.files) != {"features", "x", "SERIALNO", "SPORDER"}:
            raise DatasetBlockedError("prepared certifier view contains unexpected arrays, possibly labels")
        if not np.array_equal(arrays["features"], view.features) or not np.array_equal(arrays["x"], view.x):
            raise DatasetBlockedError("prepared fixed covariates differ from the source archive")
        if arrays["SERIALNO"].tolist() != [key[0] for key in view.person_keys] or arrays["SPORDER"].tolist() != [key[1] for key in view.person_keys]:
            raise DatasetBlockedError("prepared person identities differ from the source archive")
    return vault, receipt, data_paths


def freeze_e6(config_path, input_directory, protocol_path):
    path = Path(config_path).resolve()
    config = _validate_config(json.loads(path.read_text()))
    planning_input_hashes(input_directory, allowed_missing=config.get("allowed_missing_planning_inputs", ()))
    # This gate occurs before protocol installation or any seed consumption.
    vault, receipt, data_paths = load_prepared_e6(config)
    sources = [REPOSITORY / name for name in dict.fromkeys(SOURCE_NAMES + EXTRA_SOURCES)] + [path]
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPOSITORY, text=True).strip()
    for source in sources:
        try:
            relative = source.relative_to(REPOSITORY)
        except ValueError as exc:
            raise ValueError("commit code/config inside the repository; archive bytes remain separately hashed inputs") from exc
        if not source.is_file() or subprocess.check_output(["git", "status", "--porcelain", "--", str(relative)], cwd=REPOSITORY, text=True):
            raise ValueError("commit E6 code/config before freeze: " + str(relative))
    config.update(git_sha=sha, input_config_sha256=_file_sha256(path),
        prepared_population_digest=vault.certifier_view.population_digest,
        dataset_population_digest=vault.certifier_view.population_digest,
        prepared_eligible_rows=vault.certifier_view.n,
        resolved_archive_path=str(_path(config["archive_path"])),
        prepared_manifest_sha256=_file_sha256(_path(config["prepared_directory"]) / "manifest.json"),
        dataset_scope="finite-population policy-weighted selection outcomes; not causal selection effects",
        source_selector_amendment=dict(LOGGER_AMENDMENT))
    return freeze_protocol(protocol_path, config, sources + data_paths, input_directory)


def draw_e6_split(vault, split, seed):
    """Fresh product source words, with a separate role for private selectors."""
    def rng(role):
        key = hashlib.sha256(f"{split.namespace}\0{seed}\0{role}".encode()).digest()
        return np.random.default_rng(int.from_bytes(key, "little"))
    words = rng("uniform_Z").integers(0, WORD_GRID, size=split.n, dtype=np.uint64)
    selectors = (rng("private_selector_C").integers(0, WORD_GRID, size=split.n, dtype=np.uint64)
                 if split.graph_kind == "cycle" else None)
    return vault.observe_from_words(split, words, selector_words=selectors,
                                    seed_namespace=f"{split.namespace}/seed/{seed}")


def evaluate_e6_pipeline(vault, frozen, certificates, selection, *, methods_finished=False):
    """Join fixed labels after selection; no synthetic response means appear."""
    if methods_finished is not True:
        raise ValueError("E6 evaluator runs only after every method and decision")
    split = frozen.design.splits["certification"]
    targets = vault.oracle_targets(frozen.family, split, methods_finished=True)
    policy_values = vault.oracle_policy_values(frozen.policy_probabilities, split, methods_finished=True)
    candidates = {candidate.policy_id: candidate for candidate in frozen.candidates}

    def target(query_id):
        return targets[frozen.family.canonical_id(query_id)]

    def interval(query_id):
        certificate = certificates.get(frozen.family.canonical_id(query_id), {})
        lo, hi = certificate.get("lo"), certificate.get("hi")
        if certificate.get("status") != CERTIFIED or certificate.get("empty_intersection", False):
            return None
        if lo is None or hi is None or not np.isfinite(lo) or not np.isfinite(hi) or lo > hi:
            return None
        return lo, hi

    false_safe = false_violation = false_utility = discovered = detected = False
    for candidate in frozen.candidates:
        for query_id in candidate.risk_query_ids:
            bounds = interval(query_id)
            if bounds is not None:
                truth, threshold = target(query_id), frozen.risk_thresholds[query_id]
                false_safe |= bounds[1] <= threshold and truth > threshold
                false_violation |= bounds[0] > threshold and truth <= threshold
                hit = bounds[0] > threshold and truth > threshold
                detected |= hit
                discovered |= hit and query_id.rsplit("/", 1)[1] != "all"
        utility_id = candidate.utility_contrast_id
        if utility_id is not None and interval(utility_id) is not None:
            lower = interval(utility_id)[0]
            truth = target(utility_id)
            false_utility |= lower >= -frozen.design.utility_margin and truth < -frozen.design.utility_margin
            false_utility |= lower > 0 and truth <= 0
    covered = all(interval(query.query_id) is not None and
                  interval(query.query_id)[0] <= targets[query.query_id] <= interval(query.query_id)[1]
                  for query in frozen.family.queries)
    all_certified = all(interval(query.query_id) is not None for query in frozen.family.queries)
    risk_safe, utility_ok, service_ok, feasible, gaps = {}, {}, {}, {}, {}
    for candidate in frozen.candidates:
        key = candidate.policy_id
        gaps[key] = max(target(query_id)-frozen.risk_thresholds[query_id] for query_id in candidate.risk_query_ids)
        risk_safe[key] = gaps[key] <= 0
        gain = 0.0 if candidate.utility_contrast_id is None else target(candidate.utility_contrast_id)
        utility_ok[key] = gain >= -frozen.design.utility_margin
        service_ok[key] = candidate.service >= frozen.design.service_floor and candidate.capacity <= frozen.design.capacity_ceiling
        feasible[key] = risk_safe[key] and utility_ok[key] and service_ok[key]
    returned = bool(selection.get("returned", False))
    selected_id = selection.get("policy_id") if returned else None
    if returned and selected_id not in candidates:
        raise ValueError("selector returned an E6 policy outside its frozen finite family")
    selected = candidates.get(selected_id)
    baseline = policy_values["policy0"]["utility"]
    robust_values = []
    for candidate in frozen.candidates:
        if not feasible[candidate.policy_id]:
            continue
        slack = True
        for query_id in candidate.risk_query_ids:
            certificate = certificates.get(frozen.family.canonical_id(query_id), {})
            radius = certificate.get("radius")
            slack &= (interval(query_id) is not None and radius is not None and math.isfinite(radius)
                      and radius >= 0 and target(query_id)+2*radius <= frozen.risk_thresholds[query_id])
        query_id = candidate.utility_contrast_id
        if query_id is not None:
            certificate = certificates.get(frozen.family.canonical_id(query_id), {})
            radius = certificate.get("radius")
            slack &= (interval(query_id) is not None and radius is not None and math.isfinite(radius)
                      and radius >= 0 and target(query_id)-2*radius >= -frozen.design.utility_margin)
        if slack:
            robust_values.append(policy_values[candidate.policy_id]["utility"])
    return dict(status="FINITE_POPULATION_E6_EVALUATION", unit="one complete three-split logging/pipeline trial",
        family_size=frozen.family.family_size, family_covered=bool(covered),
        all_coordinates_certified=bool(all_certified), any_false_safe=bool(false_safe),
        any_false_violation=bool(false_violation), any_false_utility_claim=bool(false_utility),
        any_false_claim=bool(false_safe or false_violation or false_utility),
        true_violation_discovered_and_certified=bool(discovered), any_true_violation_certified=bool(detected),
        returned=returned, returned_policy_id=selected_id, returned_baseline=returned and selected_id == "policy0",
        return_and_unsafe=bool(returned and not risk_safe[selected_id]),
        return_and_risk_safe=bool(returned and risk_safe[selected_id]),
        return_and_utility_noninferior=bool(returned and utility_ok[selected_id]),
        return_and_service_feasible=bool(returned and service_ok[selected_id]),
        return_and_infeasible=bool(returned and not feasible[selected_id]),
        return_and_safe_and_useful=bool(returned and feasible[selected_id]),
        unsafe_given_return_numerator=int(returned and not risk_safe[selected_id]),
        unsafe_given_return_denominator=int(returned),
        true_utility=policy_values[selected_id]["utility"] if returned else None,
        utility_gain=policy_values[selected_id]["utility"]-baseline if returned else None,
        expected_service=selected.service if returned else 0.0,
        expected_capacity=selected.capacity if returned else 0.0,
        maximum_true_risk_violation=max(0.0, gaps[selected_id]) if returned else None,
        oracle_best_feasible_candidate_value=max((policy_values[key]["utility"] for key in feasible if feasible[key]), default=None),
        robust_slack_comparator_value=max(robust_values, default=None),
        robust_slack_definition="evaluation only: risk truth+2r<=threshold and utility contrast truth-2r>=-margin",
        discovery_best_planted_iou=None, planted_group_recovery_applicable=False, targets=targets,
        unsafe_definition="violation of a frozen true risk coordinate; service/utility reported separately",
        useful_definition="known service/capacity feasible AND true utility contrast>=-margin",
        scope="fixed finite-population selective-label benchmark; no causal effect on income or future-distribution safety")


def _sanitize_raw(value):
    if isinstance(value, dict):
        return {key: _sanitize_raw(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_raw(item) for item in value]
    if isinstance(value, (float, np.floating)) and not math.isfinite(value):
        return str(value)
    return value


def _run_trial(manifest, run_id, design, vault, draw_callback=None, *, graph_cache=None):
    config = manifest["config"]
    observed, joined_targets = {}, {}
    def draw(split, seed):
        log = draw_callback(vault, split, seed) if draw_callback is not None else draw_e6_split(vault, split, seed)
        observed[split.name] = log
        return log
    def oracle(frozen, certificates, selection, *, methods_finished=False):
        metrics = evaluate_e6_pipeline(vault, frozen, certificates, selection, methods_finished=methods_finished)
        joined_targets[frozen.family.digest] = metrics["targets"]
        return metrics
    hashes = dict(code=digest(manifest["sources"]), config=digest(config),
                  p2_grid_choice=factorized_p2_grid_choice(config["truncation_multipliers"]))
    try:
        result = _execute_trial(manifest, run_id, design, draw, oracle, hashes, graph_cache=graph_cache)
        # Controller reuse changes no numeric scientific output; E6 labels and
        # protocol phase are reported accurately instead of inheriting E5 tags.
        result["suite"] = "E6"
        for trial in result["trials"]:
            trial["status"] = "FINITE_POPULATION_E6"
            trial["protocol_stage"] = "DETERMINISTIC_FIXTURE" if config["suite"] == "DETERMINISTIC_E6_FIXTURE" else "FROZEN_E6_PRODUCTION"
            trial["planted_group_recovery_applicable"] = False
        if "raw_debug" in result:
            result["raw_debug"] = _sanitize_raw(result["raw_debug"])
        result["coordinate_truths_by_family"] = joined_targets
    except Exception as exc:
        result = dict(suite="E6", cell=run_id.split("/")[2], status="UNIT_FAILURE",
            failure_reason=f"{type(exc).__name__}: {exc}"[:4096], legacy_new_outcome_draws=0,
            full_family_failure=True, unassessable_whole_trial=True, family_covered=False, trials=[],
            source_split_digests={name: log.data_digest for name, log in observed.items()},
            raw_debug=_sanitize_raw({name:dict(actions=log.actions.tolist(),
                outcomes={channel: values.tolist() for channel, values in log.outcomes.items()})
                for name, log in observed.items()}))
    result.update(new_scientific_units=0 if config["suite"] == "DETERMINISTIC_E6_FIXTURE" else 1,
        legacy_new_outcome_draws=0, dataset_population_digest=vault.certifier_view.population_digest,
        archive_sha256=config["archive_sha256"], selected_dataset="CA2018_1Year_person_PUMS_only",
        population_scope="fixed labels; fresh source-separated logging randomness, not new people",
        cycle_logger=LOGGER_AMENDMENT["main_cycle_logger"],
        cohort_split_digest=digest({name: split.row_indices.tolist() for name, split in design.splits.items()}),
        planted_group_recovery_applicable=False, causal_intervention_claimed=False)
    return result


def e6_status(protocol_path, results_root, *, list_ids=False):
    if not Path(protocol_path).exists():
        result = dict(status="DATA_BLOCKED_OR_NOT_FROZEN", suite="E6", completed_units=0,
            remaining_units=1000, legacy_new_outcome_draws=0,
            selected_source=OFFICIAL_URL, data_gate="actual archive, source receipt, prepared population and exact household splits required",
            id_status="proposed identifiers only; no E6 seeds assigned here")
        if list_ids:
            result.update(completed_ids=[], remaining_ids=planned_e6_ids())
        return result
    manifest = json.loads(Path(protocol_path).read_text())
    if manifest["config"].get("suite") not in ("E6", "DETERMINISTIC_E6_FIXTURE"):
        raise ValueError("requested protocol is not E6")
    store = CheckpointStore(results_root, manifest)
    remaining = store.remaining_ids()
    result = dict(status="COMPLETE" if not remaining else "INCOMPLETE", suite="E6",
        completed_units=len(store.planned)-len(remaining), remaining_units=len(remaining),
        legacy_new_outcome_draws=0, fingerprint=manifest["fingerprint"],
        dataset_population_digest=manifest["config"].get("dataset_population_digest"))
    if list_ids:
        result.update(completed_ids=sorted(store.planned-set(remaining)), remaining_ids=remaining)
    return result


def run_e6(protocol_path, results_root, *, global_results_root=None, max_new_units=None,
           vault=None, draw_callback=None, resource_reader=None, progress=True):
    """Resume frozen E6 only; unavailable data cannot become a substitute trial.

    Synthetic vault/callback injection is confined to explicitly labeled test
    protocols. The CLI never accepts that protocol phase or a data override.
    """
    manifest = json.loads(Path(protocol_path).read_text())
    config = manifest["config"]
    fixture = config.get("suite") == "DETERMINISTIC_E6_FIXTURE"
    if config.get("suite") not in ("E6", "DETERMINISTIC_E6_FIXTURE") or config.get("workers") != 1:
        raise ValueError("E6 requires a single synchronous worker and its own protocol phase")
    if fixture:
        if vault is None or draw_callback is None or vault.certifier_view.metadata.get("data_status") != "DETERMINISTIC_FIXTURE_NOT_REAL_DATA":
            raise ValueError("fixture protocol requires an artificial labeled vault and explicit nonrandom callback")
    else:
        if vault is not None or draw_callback is not None:
            raise ValueError("production E6 cannot override its frozen archive or random-source driver")
        _validate_config(config)
        if config["production_environment"] != environment_signature():
            raise ValueError("production environment differs from the frozen E6 numerical contract")
    if max_new_units is not None and (type(max_new_units) is not int or max_new_units < 0):
        raise ValueError("max_new_units must be nonnegative")
    root = Path(results_root).resolve()
    global_root = Path(global_results_root or REPOSITORY / "results/post_cstat").resolve()
    if not root.is_relative_to(global_root):
        raise ValueError("shared artifact root must include all E6 checkpoints")
    store = CheckpointStore(root, manifest)
    if not fixture:
        vault, receipt, data_paths = load_prepared_e6(config)
        if vault.certifier_view.population_digest != config["dataset_population_digest"]:
            raise DatasetBlockedError("frozen population digest differs from the archive")
        external_data_bytes = sum(path.stat().st_size for path in data_paths if not path.resolve().is_relative_to(global_root))
    else:
        external_data_bytes = 0
        if config.get("dataset_population_digest") != vault.certifier_view.population_digest:
            raise ValueError("fixture population digest differs from its protocol")
    reader, budget = resource_reader or resource_snapshot, GlobalBudget(global_root)
    stamps = _source_stamps(manifest)
    artifact_bytes, unit_count = budget.scan()
    first_snapshot = reader(global_root)
    _resource_check(first_snapshot, artifact_bytes+external_data_bytes, config)
    grouped = defaultdict(list)
    for run_id in store.remaining_ids():
        parts = run_id.split("/")
        if parts[1] != "E6" or parts[2] not in e6_cell_ids():
            raise ValueError("frozen ID is outside the four E6 cells")
        grouped[parts[2]].append(run_id)
    began, cpu = time.monotonic(), time.process_time()
    new = failed = 0
    status, reason = "COMPLETE", None
    try:
        for cell, ids in sorted(grouped.items()):
            if max_new_units is not None and new >= max_new_units:
                status = "CHECKPOINTED_INCOMPLETE"
                break
            overlap, graph = cell.split("-logger")
            design = build_semisynthetic_design(vault.certifier_view, graph, overlap,
                namespace=config["seed_domain"]+"/"+cell, split_sizes=config["split_sizes"])
            design = replace(design, risk_threshold=config["risk_threshold"], utility_margin=config["utility_margin"],
                service_floor=config["service_floor"], capacity_ceiling=config["capacity_ceiling"])
            cache = CachedSupportGraph(design.splits["certification"].graph, max_entries=32)
            for run_id in ids:
                if max_new_units is not None and new >= max_new_units:
                    status = "CHECKPOINTED_INCOMPLETE"
                    break
                stamps = _verify_changed_sources(manifest, stamps)
                artifact_bytes, unit_count = budget.scan()
                _resource_check(reader(global_root), artifact_bytes+external_data_bytes, config)
                if unit_count >= config.get("total_unit_cap", 32000):
                    raise ResourceLimitError("global new-unit cap reached before another E6 trial")
                if store.load(run_id) is not None:
                    continue
                result = _run_trial(manifest, run_id, design, vault, draw_callback, graph_cache=cache)
                store.complete(run_id, result)
                new += 1
                failed += result["status"] != "COMPLETE"
                artifact_bytes, unit_count = budget.scan()
                if artifact_bytes+external_data_bytes > config.get("artifact_cap_bytes", int(1.5*GIB)):
                    raise ResourceLimitError("global artifact cap reached after preserving the current E6 trial")
                if progress and new % 25 == 0:
                    print(json.dumps(dict(suite="E6", cell=cell, new_completed_units=new,
                        global_checkpoint_units=unit_count)), flush=True)
                if result["status"] == "UNIT_FAILURE":
                    status, reason = "ERROR_CHECKPOINTED", result["failure_reason"]
                    break
            del design, cache
            if status == "ERROR_CHECKPOINTED":
                break
    except ResourceLimitError as exc:
        status, reason = "RESOURCE_CHECKPOINTED", str(exc)
    except KeyboardInterrupt:
        status, reason = "INTERRUPTED", "synchronous session ended; no background continuation"
    except ValueError as exc:
        status, reason = "SOURCE_DATA_OR_PROTOCOL_BLOCKED", str(exc)
    remaining = store.remaining_ids()
    if remaining and status == "COMPLETE":
        status = "CHECKPOINTED_INCOMPLETE"
    artifact_bytes, unit_count = budget.scan()
    result = dict(suite="E6", status=status, new_completed_units=new, failed_units=failed,
        remaining_ids=remaining, legacy_new_outcome_draws=0, fingerprint=manifest["fingerprint"],
        dataset_population_digest=vault.certifier_view.population_digest, archive_sha256=config["archive_sha256"],
        first_resource_snapshot=first_snapshot, global_new_checkpoint_units=unit_count,
        global_artifact_bytes=artifact_bytes, external_fixed_data_bytes=external_data_bytes,
        stop_reason=reason, wall_seconds=time.monotonic()-began, cpu_seconds=time.process_time()-cpu,
        background_work_running=False, execution_mode="one CPU worker; fresh logging randomness over fixed people",
        resume_command=shlex.join([".venv/bin/python", "-m", "experiments.e6_runner", "--run",
            "--protocol", str(protocol_path), "--results", str(root), "--global-results", str(global_root)]))
    install_once(root / "invocations" / f"{time.time_ns()}.json", canonical_bytes(result)+b"\n")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    for name in ("freeze", "run", "status", "analyze"):
        mode.add_argument("--"+name, action="store_true")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--inputs", type=Path, default=REPOSITORY / "task_materials/post_cstat")
    parser.add_argument("--protocol", type=Path, default=REPOSITORY / "results/post_cstat/E6_protocol.json")
    parser.add_argument("--results", type=Path, default=REPOSITORY / "results/post_cstat/E6")
    parser.add_argument("--global-results", type=Path, default=REPOSITORY / "results/post_cstat")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-new-units", type=int)
    parser.add_argument("--list-ids", action="store_true")
    args = parser.parse_args(argv)
    if args.status:
        result = e6_status(args.protocol, args.results, list_ids=args.list_ids)
    elif args.freeze:
        if args.config is None:
            parser.error("--freeze requires a committed --config")
        result = freeze_e6(args.config, args.inputs, args.protocol)
    elif args.run:
        manifest = json.loads(args.protocol.read_text())
        if manifest["config"].get("suite") != "E6":
            raise ValueError("CLI cannot run a deterministic E6 fixture")
        result = run_e6(args.protocol, args.results, global_results_root=args.global_results,
                        max_new_units=args.max_new_units)
    else:
        if args.output is None:
            parser.error("--analyze requires a fresh --output directory")
        from experiments.e6_analyze import analyze_e6
        summary = analyze_e6(args.protocol, args.results, args.output)
        result = {key:summary[key] for key in ("status", "completed_units", "remaining_units", "failed_units")}
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()

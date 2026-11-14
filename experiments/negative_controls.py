"""Prespecified invalid-assumption diagnostics, separate from primary studies.

Four controls x 25 independent whole logs = 100 supplementary units. No draw
occurs on import. Intentionally false declarations never turn an invalid path
into a scientific certificate: their exported guarantee/status is HEURISTIC.
Honest declarations of the violated premise are refused. A hidden premise
cannot generally be tested from the schema or one observed log.
"""

import argparse
from collections import Counter
import csv
from dataclasses import dataclass, replace
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import shlex
import subprocess
import time

import numpy as np

from comet.checkpoint_store import (CheckpointStore, NAMESPACE, canonical_bytes,
    digest, freeze_protocol, install_once, planning_input_hashes)
from comet.metrics import wilson
from comet.queries import SignedQuery
from comet.residual_truncation import (AssumptionContract, CERTIFIED, clipping_bias_constant,
    make_plan, residual_moment_envelope, truncation_components)
from comet.source_graph import SourceGraph
from experiments.extension_runner import GlobalBudget
from experiments.post_cstat_runner import (GIB, LEVELS, REPOSITORY, SOURCE_NAMES,
    ResourceLimitError, _resource_check, _source_stamps, _verify_changed_sources, resource_snapshot)


CONTROLS = ("hidden_shared_shock", "wrong_propensity", "missing_clipping_bias", "evaluation_nuisance_leak")
ENGINES = ("valid_actual_model", "intentionally_invalid", "honest_refusal")
HEURISTIC = "HEURISTIC_INTENTIONALLY_INVALID_ASSUMPTIONS"
EXTRA_SOURCES = ("experiments/extension_runner.py", "experiments/negative_controls.py",
    "comet/audit_pipeline.py", "comet/paired_contrasts.py", "experiments/suite_designs.py")


def control_specs():
    return {
        "hidden_shared_shock": dict(actual_e1=0.5, declared_e1=0.5, q1=0.5, nuisance=0.5,
            location=0.45, shared_amplitude=0.25, private_noise=0.0, p=2.0,
            actual_graph="complete_source_projection", declared_graph="edgeless",
            violated_premise="sufficient_source_graph", schema_detectability=False),
        "wrong_propensity": dict(actual_e1=0.2, declared_e1=0.5, q1=0.8, nuisance=0.5,
            mu0=0.2, mu1=0.8, private_noise=0.0, p=2.0,
            actual_graph="independent_rows", declared_graph="edgeless",
            violated_premise="exact_exposure", schema_detectability=False),
        "missing_clipping_bias": dict(actual_e1=0.5, declared_e1=0.5, q1=0.5, nuisance=0.5,
            location=0.3, spike=100.0, spike_probability=0.005, spike_denominator=200,
            tau=0.01, p=1.5, actual_graph="independent_rows", declared_graph="edgeless",
            violated_premise="include_clipping_bias", schema_detectability=True),
        "evaluation_nuisance_leak": dict(actual_e1=0.2, declared_e1=0.2, q1=0.8,
            nuisance=0.5, leaked_nuisance="both states equal own observed Y", mu0=0.2, mu1=0.8,
            private_noise=0.0, p=2.0, actual_graph="independent_rows", declared_graph="edgeless",
            violated_premise="independent_nuisance", schema_detectability=False),
    }


def spike_raw_residual_moment(p=1.5):
    """Known envelope input from the declared two-point class, not an oracle target."""
    return 0.995 * 0.2**p + 0.005 * 99.8**p


def analytic_control_targets():
    p, tau = 1.5, 0.01
    v = spike_raw_residual_moment(p)
    clipped = 0.5 + 0.995 * (-tau) + 0.005 * tau
    return dict(
        hidden_shared_shock=dict(target=0.45, positive_shock_mean=0.7, negative_shock_mean=0.2),
        wrong_propensity=dict(target=0.68, expected_wrong_DR=0.5),
        missing_clipping_bias=dict(target=0.8, expected_clipped=clipped,
            exact_clipping_bias=0.8 - clipped, raw_residual_p_moment=v,
            proved_bias_bound=clipping_bias_constant(p) * v * tau**(1-p)),
        evaluation_nuisance_leak=dict(target=0.68, expected_leaked_estimate=0.32),
    )


def planned_negative_ids():
    return [f"{NAMESPACE}/negative_controls/{control}/{rep:04d}" for control in CONTROLS for rep in range(25)]


def declared_assumption_gate(*, sufficient_source_graph=True, exact_exposure=True,
                             independent_nuisance=True, include_clipping_bias=True):
    claims = dict(sufficient_source_graph=sufficient_source_graph, exact_exposure=exact_exposure,
                  independent_nuisance=independent_nuisance, include_clipping_bias=include_clipping_bias)
    missing = [name for name, value in claims.items() if value is not True]
    if missing:
        return dict(status="ASSUMPTION_UNVERIFIED", interval=None,
                    reason="unsupported declared premise: " + ", ".join(missing))
    return dict(status="ASSUMPTIONS_DECLARED_NOT_EMPIRICALLY_VERIFIED", interval=None,
                reason="a true declaration is a model responsibility, not a schema-discovered fact")


def honest_declarations(control):
    if control not in CONTROLS:
        raise ValueError("unknown prespecified negative control")
    return {control_specs()[control]["violated_premise"]: False}


def _readonly(values, dtype=float):
    array = np.asarray(values, dtype=dtype)
    return np.frombuffer(array.tobytes(), dtype=array.dtype).reshape(array.shape)


def _contract():
    # For the invalid branch these labels are intentionally false; the result
    # is always reclassified HEURISTIC and never promoted as certified science.
    return AssumptionContract(True, True, True, True, True, True, True,
        "declared_independent_row_atoms", "declared_legal_residual_envelope",
        "declared_fixed_design_and_independent_fit")


@dataclass(frozen=True)
class NegativeDesign:
    control: str
    n: int
    namespace: str
    query: SignedQuery
    actual_exposure: np.ndarray
    declared_exposure: np.ndarray
    nuisance: np.ndarray
    declared_graph: object
    metadata: dict


def build_negative_design(control, n=32768, namespace="comet-post-cstat-v1/negative-controls"):
    if control not in CONTROLS or type(n) is not int or n < 1:
        raise ValueError("declare a valid negative control and positive integer N")
    spec = control_specs()[control]
    actual = np.tile([1-spec["actual_e1"], spec["actual_e1"]], (n, 1))
    declared = np.tile([1-spec["declared_e1"], spec["declared_e1"]], (n, 1))
    query = SignedQuery(control, np.tile([1-spec["q1"], spec["q1"]], (n, 1)), 0)
    # The declared graph is O(N). The actual shared-shock N-clique is represented
    # analytically only: allocating its N**2 adjacency would be incorrect here.
    graph = SourceGraph.from_sources([{(namespace, "declared_private", row)} for row in range(n)])
    actual_graph = dict(kind=spec["actual_graph"], n_rows=n,
        edge_count=n*(n-1)//2 if control == "hidden_shared_shock" else 0,
        verified_color_count=n if control == "hidden_shared_shock" else 1,
        construction="all rows share one shock; source projection is the complete graph" if control == "hidden_shared_shock"
        else "each row uses private assignment/spike primitives; leaked fits use only their own row")
    metadata = dict(control=control, parameters=spec, actual_source_graph=actual_graph,
        declared_source_graph=dict(kind="edgeless", n_rows=n, edge_count=0, verified_color_count=1),
        schema_detectability=spec["schema_detectability"],
        detectability_scope="explicitly omitted bias is auditable; false law/source/fit labels cannot generally be inferred from one numeric log",
        honest_declaration=honest_declarations(control), honest_response=declared_assumption_gate(**honest_declarations(control)),
        actual_logging_law="independent uniform integer 0..4 equals zero" if spec["actual_e1"] == 0.2
        else "independent uniform integer 0..1 equals zero",
        leakage_scope="row-local evaluation fit breaks the DR/conditioning premise, not a fabricated cross-row graph" if control == "evaluation_nuisance_leak" else None,
        scientific_role="supplementary intentionally invalid-assumption diagnostic; never a primary validity comparison")
    return NegativeDesign(control, n, namespace, query, _readonly(actual), _readonly(declared),
                           _readonly(np.full((n, 2), spec["nuisance"])), graph, metadata)


@dataclass(frozen=True)
class NegativeLog:
    actions: np.ndarray
    outcomes: np.ndarray
    data_digest: str
    seed_namespace: str
    primitive_summary: dict


def generate_negative_from_primitives(design, action_codes, *, shared_sign=1, spike_codes=None):
    spec, codes = control_specs()[design.control], np.asarray(action_codes)
    denominator = 5 if spec["actual_e1"] == 0.2 else 2
    if codes.shape != (design.n,) or codes.dtype.kind not in "iu" or np.any(codes < 0) or np.any(codes >= denominator):
        raise ValueError("supply one declared finite-uniform logging code per row")
    actions = (codes == 0).astype(np.uint8)
    summary = dict(logging_denominator=denominator, exposed_rows=int(actions.sum()))
    if design.control == "hidden_shared_shock":
        if shared_sign not in (-1, 1):
            raise ValueError("one shared Rademacher sign is required")
        outcomes = np.full(design.n, spec["location"] + spec["shared_amplitude"] * shared_sign)
        summary["shared_sign"] = int(shared_sign)
    elif design.control == "missing_clipping_bias":
        spikes = np.asarray(spike_codes)
        if spikes.shape != (design.n,) or spikes.dtype.kind not in "iu" or np.any(spikes < 0) or np.any(spikes >= 200):
            raise ValueError("supply one independent uniform 0..199 spike code per row")
        outcomes = spec["location"] + spec["spike"] * (spikes == 0)
        summary["spikes"] = int(np.sum(spikes == 0))
    else:
        outcomes = np.where(actions == 1, spec["mu1"], spec["mu0"])
    value = hashlib.sha256(actions.tobytes() + outcomes.astype("<f8").tobytes()).hexdigest()
    return NegativeLog(_readonly(actions, np.uint8), _readonly(outcomes), value,
                       design.namespace + "/explicit-primitives", summary)


def draw_negative_log(design, seed):
    """Production driver; called only after a committed frozen supplementary protocol."""
    def rng(role):
        key = hashlib.sha256(f"{design.namespace}\0{seed}\0{role}".encode()).digest()
        return np.random.default_rng(int.from_bytes(key, "little"))
    denominator = 5 if control_specs()[design.control]["actual_e1"] == 0.2 else 2
    codes = rng("logging").integers(0, denominator, size=design.n, dtype=np.uint8)
    sign = (1 if rng("shared_shock").integers(0, 2) else -1) if design.control == "hidden_shared_shock" else 1
    spikes = (rng("spikes").integers(0, 200, size=design.n, dtype=np.uint16)
              if design.control == "missing_clipping_bias" else None)
    log = generate_negative_from_primitives(design, codes, shared_sign=sign, spike_codes=spikes)
    return replace(log, seed_namespace=f"{design.namespace}/seed/{seed}")


def build_negative_plans(design, levels=LEVELS):
    """Static legitimate/false-declaration plans; never read an observed Y."""
    spec, plans = control_specs()[design.control], {}
    p = spec["p"]
    for delta in levels:
        common = dict(p=p, delta=delta, family_size=1, multipliers=(1.0,), mean_bounds=(0, 1))
        b = (np.full((design.n, 2), spike_raw_residual_moment(p))
             if design.control == "missing_clipping_bias" else np.full((design.n, 2), 0.25))
        if design.control == "missing_clipping_bias":
            valid = make_plan(design.query, design.actual_exposure, design.nuisance, b,
                design.declared_graph, _contract(), method="truncated_local", **common)
            v = residual_moment_envelope(design.query.coefficients, design.actual_exposure, b, p)
            pieces = truncation_components(v, spec["tau"], p, 1, delta, design.n)
            valid = replace(valid, method="fixed_tau_bias_corrected", selected_method="fixed_tau_bias_corrected",
                tau=spec["tau"], bias_piece=pieces[0], variance_piece=pieces[1], range_piece=pieces[2])
            invalid = replace(valid, method="intentional_missing_bias", selected_method="fixed_tau_without_bias",
                              bias_piece=0.0)
        else:
            valid = None if design.control == "hidden_shared_shock" else make_plan(
                design.query, design.actual_exposure, design.nuisance, b,
                design.declared_graph, _contract(), method="graph_hoeffding", outcome_bounds=(0, 1), **common)
            invalid = None if design.control == "evaluation_nuisance_leak" else make_plan(
                design.query, design.declared_exposure, design.nuisance, b,
                design.declared_graph, _contract(), method="graph_hoeffding", outcome_bounds=(0, 1), **common)
        plans[float(delta)] = valid, invalid
    return plans


def _range_reference(design, delta, log):
    return dict(query_id=design.query.query_id, status=CERTIFIED,
        guarantee_type="DETERMINISTIC_KNOWN_RANGE_REFERENCE", estimate=0.5,
        lo=0.0, hi=1.0, raw_lo=0.0, raw_hi=1.0, empty_intersection=False,
        radius=0.5, deterministic_range_halfwidth=0.5, bias=0.0,
        concentration=0.0, range_contribution=0.0,
        radius_interpretation="known [0,1] target range, not a concentration radius",
        numerical_guard=0.0, family_size=1, nominal_delta=delta, coordinate_delta=delta,
        channel="risk", normalizer=1.0, method="full_feasible_range",
        actual_color_count=design.n, adjacency_allocated=False, data_digest=log.data_digest,
        selected_method="deterministic_range_no_independence_needed")


def _interval_decision(record, threshold):
    if record.get("lo") is None or record.get("hi") is None or record.get("empty_intersection", False):
        return "NO_INTERVAL"
    if record["hi"] <= threshold:
        return "SAFE_CLAIM"
    if record["lo"] > threshold:
        return "VIOLATION_CLAIM"
    return "ABSTAIN"


def _raw(log):
    def values(array):
        return [float(value) if math.isfinite(float(value)) else str(float(value))
                for value in np.asarray(array).ravel()]
    return dict(actions=values(log.actions), outcomes=values(log.outcomes),
                nonfinite_encoding="explicit strings; no numerical refusal is dropped")


def evaluate_negative_unit(design, log, *, levels=LEVELS, numerical_guard=1e-10,
                           code_hash="fixture", config_hash="fixture", plans=None):
    plans = build_negative_plans(design, levels) if plans is None else plans
    evaluated = []
    metadata = dict(data_digest=log.data_digest, seed_namespace=log.seed_namespace,
                    code_hash=code_hash, config_hash=config_hash, numerical_guard=numerical_guard)
    for delta in levels:
        valid, invalid = plans[float(delta)]
        for engine in ENGINES:
            try:
                if engine == "honest_refusal":
                    record = dict(declared_assumption_gate(**honest_declarations(design.control)),
                        query_id=design.query.query_id, lo=None, hi=None, family_size=1,
                        nominal_delta=delta, coordinate_delta=delta,
                        guarantee_type="NO_CERTIFICATE_HONEST_UNSUPPORTED_REQUEST")
                elif engine == "valid_actual_model" and design.control == "hidden_shared_shock":
                    record = _range_reference(design, delta, log)
                else:
                    plan = valid if engine == "valid_actual_model" else invalid
                    if engine == "intentionally_invalid" and design.control == "evaluation_nuisance_leak":
                        leaked = np.repeat(np.asarray(log.outcomes)[:, None], 2, axis=1)
                        b = np.maximum(np.abs(leaked), np.abs(1-leaked))**2
                        plan = make_plan(design.query, design.actual_exposure, leaked, b,
                            design.declared_graph, _contract(), p=2, delta=delta, family_size=1,
                            multipliers=(1.0,), method="graph_hoeffding",
                            outcome_bounds=(0, 1), mean_bounds=(0, 1))
                    record = plan.evaluate(log.actions, log.outcomes, **metadata)
                    if engine == "intentionally_invalid":
                        record["underlying_engine_declared_status"] = record["status"]
                        record["status"] = HEURISTIC
                        record["guarantee_type"] = HEURISTIC
                        record["intentional_violated_premise"] = control_specs()[design.control]["violated_premise"]
                    else:
                        record["guarantee_type"] = CERTIFIED
                decision = _interval_decision(record, 0.6)
            except Exception as exc:
                record = dict(query_id=design.query.query_id, status="NUMERICAL_FAILURE",
                    guarantee_type="NO_NUMERICAL_INTERVAL", lo=None, hi=None,
                    reason=f"{type(exc).__name__}: {exc}"[:2048])
                decision = "NO_INTERVAL"
            evaluated.append((float(delta), engine, record, decision))
    # Only now are the analytic truths joined. They were not estimator inputs.
    truth = analytic_control_targets()[design.control]["target"]
    trials, scientific_records = [], []
    for delta, engine, record, decision in evaluated:
        expected = engine != "honest_refusal"
        issued = record.get("lo") is not None and record.get("hi") is not None
        nonempty = issued and not record.get("empty_intersection", False) and record["lo"] <= record["hi"]
        covered = nonempty and record["lo"] <= truth <= record["hi"]
        false_safe = decision == "SAFE_CLAIM" and truth > 0.6
        false_violation = decision == "VIOLATION_CLAIM" and truth <= 0.6
        trial = dict(control=design.control, engine=engine, delta=delta, family_size=1,
            interval_expected=expected, interval_issued=bool(issued), interval_covered=bool(covered),
            error_metrics_assessable=bool(issued), honest_refusal=not expected,
            false_safe=bool(false_safe) if issued else None,
            false_violation=bool(false_violation) if issued else None,
            any_false_claim=bool(false_safe or false_violation) if issued else None,
            true_violation_detected=bool(decision == "VIOLATION_CLAIM" and truth > 0.6) if issued else None,
            decision=decision, guarantee_type=record.get("guarantee_type"), status=record["status"],
            width=record["hi"] - record["lo"] if nonempty else None,
            nontrivial=bool(nonempty and record["hi"] - record["lo"] < 1),
            primary_comparison=False, theorem_validity_test=False,
            endpoint_scope="whole-log supplementary diagnostic; intentionally invalid claims are not certificates",
            refusal_interpretation="no interval means no zero-error validity evidence")
        trials.append(trial)
        scientific_records.append(dict(engine=engine, delta=delta, certificate=record, decision=decision))
    numerical = any(record["status"] == "NUMERICAL_FAILURE" for _, _, record, _ in evaluated)
    result = dict(status="NUMERICAL_FAILURE_PRESERVED" if numerical else "COMPLETE",
        control=design.control, raw_N=design.n, family_size=1, threshold=0.6,
        actual_vs_declared_model=design.metadata, analytic_truth=truth,
        analytic_mechanism=analytic_control_targets()[design.control],
        data_digest=log.data_digest, seed_namespace=log.seed_namespace,
        observed_primitive_summary=log.primitive_summary, trials=trials,
        certificate_records=scientific_records,
        oracle_order="all methods and decisions precede analytic truth join",
        retention_rule="all fixed units retained regardless of error or vacuity",
        primary_family_modified=False, negative_controls_not_primary=True,
        valid_guarantee_scope="per method and level separately; no joint claim over engines/levels")
    if numerical or any(trial["interval_expected"] and not trial["interval_covered"] for trial in trials):
        result["failure_raw_debug"] = _raw(log)
    return result


def _validate_config(config):
    required = ("controls", "master_seed", "seed_domain", "numerical_guard", "risk_threshold",
                "planning_inputs_reconciled", "theorem_status", "raw_debug_run_ids")
    if any(key not in config for key in required):
        raise ValueError("explicit supplementary config required: " + ", ".join(required))
    if config["controls"] != control_specs():
        raise ValueError("prespecified negative-control parameters cannot be tuned to outcomes")
    if type(config["master_seed"]) is not int or config["master_seed"] < 0:
        raise ValueError("a nonnegative new supplementary master seed is required")
    if not isinstance(config["seed_domain"], str) or not config["seed_domain"].startswith(NAMESPACE + "/negative-controls"):
        raise ValueError("use a separate new-workstream negative-control seed domain")
    if config["risk_threshold"] != 0.6 or not math.isfinite(config["numerical_guard"]) or config["numerical_guard"] < 0:
        raise ValueError("fixed .6 threshold and conservative numerical guard required")
    if config["planning_inputs_reconciled"] is not True or config["theorem_status"] != "PROVED_UNDER_DECLARED_ASSUMPTIONS":
        raise ValueError("reconcile inputs and the valid reference proofs before supplementary execution")
    fixed = dict(namespace=NAMESPACE, suite="negative_controls", phase="negative_controls",
        N=32768, family_size=1, workers=1, levels=list(LEVELS), replications_per_control=25,
        planned_run_ids=planned_negative_ids(), primary_units=0, supplementary_units=100,
        negative_control_budget=400, total_unit_cap=32000, total_primary_goal_units=29600,
        legacy_new_outcome_draws=0, primary_comparisons=[],
        invalid_arm_guarantee=HEURISTIC,
        raw_debug_run_ids=[f"{NAMESPACE}/negative_controls/{control}/0000" for control in CONTROLS],
        retention_rule="all fixed100 units; no filtering or stopping for errors, vacuity or desired counterexamples",
        logging_numerical_contract="exact finite-uniform denominators2/5 and spike denominator200; ordinary-float estimators with declared padding",
        artifact_cap_bytes=int(1.5 * GIB), minimum_free_disk_bytes=2 * GIB,
        worker_memory_cap_bytes=4 * GIB)
    for key, value in fixed.items():
        if key in config and config[key] != value:
            raise ValueError("fixed supplementary protocol mismatch: " + key)
    return dict(config, **fixed)


def freeze_negative_controls(config_path, input_directory, protocol_path):
    path = Path(config_path).resolve()
    config = _validate_config(json.loads(path.read_text()))
    planning_input_hashes(input_directory, allowed_missing=config.get("allowed_missing_planning_inputs", ()))
    sources = [REPOSITORY / name for name in dict.fromkeys(SOURCE_NAMES + EXTRA_SOURCES)] + [path]
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPOSITORY, text=True).strip()
    for source in sources:
        try:
            relative = source.relative_to(REPOSITORY)
        except ValueError as exc:
            raise ValueError("commit the supplementary config inside the research repository") from exc
        if not source.is_file() or subprocess.check_output(
                ["git", "status", "--porcelain", "--", str(relative)], cwd=REPOSITORY, text=True):
            raise ValueError("commit source/config/theorem before freeze: " + str(relative))
    config.update(git_sha=sha, input_config_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  analytic_mechanisms=analytic_control_targets())
    return freeze_protocol(protocol_path, config, sources, input_directory)


def _seed(config, run_id):
    key = f"{config['seed_domain']}\0{config['master_seed']}\0{run_id}".encode()
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "little")


def negative_status(protocol_path, results_root, *, list_ids=False):
    if not Path(protocol_path).exists():
        result = dict(status="NOT_FROZEN", suite="negative_controls", completed=0, remaining=100,
            primary_units=0, legacy_new_outcome_draws=0, identifier_status="proposed supplementary IDs, seeds unassigned")
        if list_ids:
            result.update(completed_ids=[], remaining_ids=planned_negative_ids())
        return result
    manifest = json.loads(Path(protocol_path).read_text())
    if manifest["config"].get("suite") not in ("negative_controls", "DETERMINISTIC_NEGATIVE_FIXTURE"):
        raise ValueError("the requested protocol is not a supplementary negative-control study")
    store = CheckpointStore(results_root, manifest)
    remaining = store.remaining_ids()
    result = dict(status="COMPLETE" if not remaining else "INCOMPLETE", suite="negative_controls",
        completed=len(store.planned)-len(remaining), remaining=len(remaining), legacy_new_outcome_draws=0,
        primary_units=0, fingerprint=manifest["fingerprint"])
    if list_ids:
        result.update(completed_ids=sorted(store.planned-set(remaining)), remaining_ids=remaining)
    return result


def run_negative_controls(protocol_path, results_root, *, global_results_root=None,
                          max_new_units=None, draw_callback=None, resource_reader=None,
                          progress=True):
    manifest = json.loads(Path(protocol_path).read_text())
    config = manifest["config"]
    fixture = config.get("suite") == "DETERMINISTIC_NEGATIVE_FIXTURE"
    if not fixture:
        _validate_config(config)
    if config.get("workers") != 1 or (fixture and draw_callback is None):
        raise ValueError("use one synchronous worker; deterministic fixtures require an explicit callback")
    if max_new_units is not None and (type(max_new_units) is not int or max_new_units < 0):
        raise ValueError("max_new_units must be nonnegative")
    root = Path(results_root).resolve()
    global_root = Path(global_results_root or REPOSITORY / "results/post_cstat").resolve()
    if not root.is_relative_to(global_root):
        raise ValueError("global resource root must include supplementary artifacts")
    store = CheckpointStore(root, manifest)
    stamps, budget = _source_stamps(manifest), GlobalBudget(global_root)
    reader = resource_reader or resource_snapshot
    total_bytes, total_units = budget.scan()
    first_snapshot = reader(global_root)
    _resource_check(first_snapshot, total_bytes, config)
    grouped = {}
    for run_id in store.remaining_ids():
        parts = run_id.split("/")
        if parts[1] != "negative_controls" or parts[2] not in CONTROLS:
            raise ValueError("supplementary protocol contains an unrelated run ID")
        grouped.setdefault(parts[2], []).append(run_id)
    new = failed = 0
    status, reason = "COMPLETE", None
    start, cpu = time.monotonic(), time.process_time()
    try:
        for control, ids in sorted(grouped.items()):
            if max_new_units is not None and new >= max_new_units:
                status = "CHECKPOINTED_INCOMPLETE"
                break
            design = build_negative_design(control, config["N"], config["seed_domain"] + "/" + control)
            plans = build_negative_plans(design, config["levels"])
            for run_id in ids:
                if max_new_units is not None and new >= max_new_units:
                    status = "CHECKPOINTED_INCOMPLETE"
                    break
                stamps = _verify_changed_sources(manifest, stamps)
                total_bytes, total_units = budget.scan()
                _resource_check(reader(global_root), total_bytes, config)
                if total_units >= config.get("total_unit_cap", 32000):
                    raise ResourceLimitError("global new-unit cap reached")
                if store.load(run_id) is not None:
                    continue
                seed = _seed(config, run_id)
                try:
                    log = (draw_callback or draw_negative_log)(design, seed)
                    result = evaluate_negative_unit(design, log, levels=config["levels"],
                        numerical_guard=config["numerical_guard"], code_hash=digest(manifest["sources"]),
                        config_hash=digest(config), plans=plans)
                    if run_id in config["raw_debug_run_ids"]:
                        result["prespecified_raw_debug"] = _raw(log)
                except Exception as exc:
                    result = dict(status="UNIT_FAILURE_PRESERVED", control=control,
                        failure_reason=f"{type(exc).__name__}: {exc}"[:4096], trials=[],
                        full_family_failure=True, unassessable_whole_trial=True)
                result.update(seed=seed, seed_domain=config["seed_domain"],
                    new_scientific_units=0 if fixture else 1, legacy_new_outcome_draws=0,
                    phase="supplementary_negative_controls_not_primary")
                store.complete(run_id, result)
                new += 1
                failed += result["status"] != "COMPLETE"
                total_bytes, total_units = budget.scan()
                if total_bytes > config.get("artifact_cap_bytes", int(1.5 * GIB)):
                    raise ResourceLimitError("global artifact cap reached after preserving the current unit")
                if progress and new % 25 == 0:
                    print(json.dumps(dict(control=control, new_completed_units=new,
                        global_checkpoint_units=total_units, scientific_role="supplementary")), flush=True)
                if result["status"] == "UNIT_FAILURE_PRESERVED":
                    status, reason = "ERROR_CHECKPOINTED", result["failure_reason"]
                    break
            del design, plans
            if status == "ERROR_CHECKPOINTED":
                break
    except ResourceLimitError as exc:
        status, reason = "RESOURCE_CHECKPOINTED", str(exc)
    except KeyboardInterrupt:
        status, reason = "INTERRUPTED", "no unattended continuation"
    except ValueError as exc:
        status, reason = "SOURCE_OR_MODEL_BLOCKED", str(exc)
    remaining = store.remaining_ids()
    if remaining and status == "COMPLETE":
        status = "CHECKPOINTED_INCOMPLETE"
    total_bytes, total_units = budget.scan()
    result = dict(status=status, scope="supplementary_negative_controls", new_completed_units=new,
        failed_units=failed, remaining_ids=remaining, primary_units=0, legacy_new_outcome_draws=0,
        global_new_checkpoint_units=total_units, global_artifact_bytes=total_bytes,
        first_resource_snapshot=first_snapshot, stop_reason=reason,
        fingerprint=manifest["fingerprint"], wall_seconds=time.monotonic()-start,
        cpu_seconds=time.process_time()-cpu, background_work_running=False,
        resume_command=shlex.join([".venv/bin/python", "-m", "experiments.negative_controls", "--run",
            "--protocol", str(protocol_path), "--results", str(root), "--global-results", str(global_root)]))
    install_once(root / "invocations" / f"{time.time_ns()}.json", canonical_bytes(result)+b"\n")
    return result


def _unknown_trial(control, engine, delta, reason):
    return dict(control=control, engine=engine, delta=delta, interval_expected=engine != "honest_refusal",
        interval_issued=False, interval_covered=False, error_metrics_assessable=False,
        honest_refusal=engine == "honest_refusal", false_safe=None, false_violation=None,
        any_false_claim=None, true_violation_detected=None, decision="NO_INTERVAL",
        status="UNASSESSABLE_UNIT_FAILURE", reason=reason, width=None, nontrivial=False,
        guarantee_type=HEURISTIC if engine == "intentionally_invalid" else None)


def analyze_negative_controls(protocol_path, results_root, output_directory):
    output = Path(output_directory)
    names = ("summary.json", "summary.csv", "manifest.json")
    if any((output / name).exists() for name in names):
        raise FileExistsError("supplementary analysis is immutable; select a fresh directory")
    manifest = json.loads(Path(protocol_path).read_text())
    config = manifest["config"]
    fixture = config.get("suite") == "DETERMINISTIC_NEGATIVE_FIXTURE"
    if not fixture:
        _validate_config(config)
    store = CheckpointStore(results_root, manifest)
    groups, completed, inventory = {}, set(), []
    unit_status = Counter()
    failed_units = scientific_units = 0
    for payload in store.iter_completed():
        run_id, result = payload["run_id"], payload["result"]
        parts = run_id.split("/")
        if parts[1] != "negative_controls" or parts[2] not in CONTROLS or result.get("control") != parts[2]:
            raise ValueError("negative-control checkpoint identity differs from its run ID")
        if result.get("legacy_new_outcome_draws", 0) != 0:
            raise ValueError("historical draws cannot enter supplementary diagnostics")
        if result.get("new_scientific_units", 0 if fixture else 1) != (0 if fixture else 1):
            raise ValueError("supplementary scientific-unit accounting disagrees with protocol phase")
        completed.add(run_id)
        inventory.append([run_id, digest(payload)])
        unit_status[result.get("status", "UNKNOWN")] += 1
        failed_units += result.get("status") != "COMPLETE"
        scientific_units += 0 if fixture else 1
        expected = {(engine, float(delta)) for engine in ENGINES for delta in config["levels"]}
        actual = {}
        for trial in result.get("trials", []):
            key = trial.get("engine"), trial.get("delta")
            if key not in expected or key in actual or trial.get("control") != parts[2]:
                raise ValueError("unexpected/duplicate negative diagnostic frame")
            if bool(trial.get("interval_expected")) != (key[0] != "honest_refusal"):
                raise ValueError("interval applicability changed after observing failures")
            actual[key] = trial
        for engine, delta in sorted(expected):
            trial = actual.get((engine, delta))
            if trial is None or result.get("unassessable_whole_trial", False):
                trial = _unknown_trial(parts[2], engine, delta, result.get("failure_reason", "missing diagnostic frame"))
            key = parts[2], engine, delta
            group = groups.setdefault(key, dict(n=0, issued=0, covered=0, refused=0,
                unknown_errors=0, numeric=0, false=0, false_safe=0, false_violation=0,
                detected=0, widths=[], nontrivial=0, statuses=Counter()))
            group["n"] += 1
            group["issued"] += bool(trial["interval_issued"])
            group["covered"] += bool(trial["interval_covered"])
            group["refused"] += trial["status"] == "ASSUMPTION_UNVERIFIED"
            group["numeric"] += trial["status"] in ("NUMERICAL_FAILURE", "UNASSESSABLE_UNIT_FAILURE")
            group["statuses"][trial["status"]] += 1
            group["nontrivial"] += bool(trial.get("nontrivial", False))
            assessable = bool(trial["error_metrics_assessable"])
            if engine != "honest_refusal":
                group["unknown_errors"] += not assessable
                for field, target in (("any_false_claim", "false"), ("false_safe", "false_safe"),
                                      ("false_violation", "false_violation"), ("true_violation_detected", "detected")):
                    if assessable and not isinstance(trial.get(field), bool):
                        raise ValueError("assessable diagnostic events must be booleans")
                    group[target] += bool(trial.get(field)) if assessable else 0
            width = trial.get("width")
            if width is not None:
                if not math.isfinite(width) or width < 0:
                    raise ValueError("invalid diagnostic interval width")
                group["widths"].append(float(width))
    rows = []
    for (control, engine, delta), group in sorted(groups.items()):
        n, expected = group["n"], engine != "honest_refusal"
        unknown = group["unknown_errors"]
        events = {}
        for source, name in (("false", "false_claim"), ("false_safe", "false_safe"),
                             ("false_violation", "false_violation"), ("detected", "true_violation_detected")):
            hits = group[source]
            events[name] = dict(hits=hits if expected else None, denominator=n if expected else 0,
                unknown_units=unknown if expected else 0, rate=hits/n if expected and not unknown else None,
                wilson95=list(wilson(hits, n)) if expected and not unknown else None,
                realized_frequency_bounds=[hits/n, (hits+unknown)/n] if expected else None)
        rows.append(dict(control=control, engine=engine, delta=delta, independent_units=n,
            issued_intervals=group["issued"], honest_refusals=group["refused"],
            numerical_failures=group["numeric"], status_counts=dict(group["statuses"]),
            guarantee_type=HEURISTIC if engine == "intentionally_invalid" else (
                "NO_CERTIFICATE_HONEST_UNSUPPORTED_REQUEST" if not expected else
                "DETERMINISTIC_KNOWN_RANGE_REFERENCE" if control == "hidden_shared_shock" else CERTIFIED),
            interval_coverage=dict(hits=group["covered"], denominator=n, rate=group["covered"]/n,
                wilson95=list(wilson(group["covered"], n)),
                interpretation="empirical invalid-interval diagnostic, not nominal-validity evidence" if engine == "intentionally_invalid"
                else "complete-unit coverage including failures; proof validity is established separately") if expected else None,
            mean_width=float(np.mean(group["widths"])) if group["widths"] else None,
            width_units=len(group["widths"]), nontrivial_units=group["nontrivial"], **events,
            refusal_interpretation="zero issued intervals supply no observed zero-error certification evidence",
            primary_comparison=False))
    remaining = sorted(store.planned-completed)
    status = "NO_COMPLETED_UNITS" if not completed else ("PARTIAL" if remaining else "COMPLETE")
    summary = dict(schema="COMET-negative-controls-analysis-v1", status=status,
        phase="DETERMINISTIC_FIXTURE_NOT_SCIENCE" if fixture else "supplementary_negative_controls",
        completed_units=len(completed), remaining_units=len(remaining), failed_units=failed_units,
        reported_new_scientific_units=scientific_units, analysis_new_outcome_draws=0,
        legacy_new_outcome_draws=0, primary_units=0, primary_comparison_count=0,
        primary_families_modified=False, holm_applied=False,
        verdict="diagnostic measurements, no outcome-based pass/success requirement",
        summaries=rows, completed_ids=sorted(completed), remaining_ids=remaining,
        checkpoint_status_counts=dict(unit_status), checkpoint_inventory_sha256=digest(inventory),
        protocol_fingerprint=manifest["fingerprint"], fixed_threshold=0.6,
        analytic_mechanisms=analytic_control_targets(), controls=control_specs(),
        uncertainty="pointwise whole-log Wilson intervals per fixed control/engine/level; not simultaneous",
        policy_return_endpoints="NOT_APPLICABLE", honest_refusal_is_not_zero_risk_evidence=True)
    buffer = io.StringIO(newline="")
    columns = ("control", "engine", "delta", "independent_units", "issued_intervals", "honest_refusals",
               "numerical_failures", "guarantee_type", "coverage_hits", "coverage_denominator", "coverage_rate",
               "false_claim_hits", "false_claim_denominator", "false_claim_unknown", "false_claim_rate", "mean_width")
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    for row in rows:
        coverage = row["interval_coverage"] or {}
        writer.writerow({**{key: row[key] for key in columns if key in row},
            "coverage_hits":coverage.get("hits"), "coverage_denominator":coverage.get("denominator"),
            "coverage_rate":coverage.get("rate"), "false_claim_hits":row["false_claim"]["hits"],
            "false_claim_denominator":row["false_claim"]["denominator"],
            "false_claim_unknown":row["false_claim"]["unknown_units"], "false_claim_rate":row["false_claim"]["rate"]})
    content, csv_content = canonical_bytes(summary)+b"\n", buffer.getvalue().encode()
    receipt = dict(schema="COMET-negative-analysis-manifest-v1", status=status,
        protocol_fingerprint=manifest["fingerprint"], source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        analysis_new_outcome_draws=0, primary_families_modified=False,
        outputs={"summary.json":hashlib.sha256(content).hexdigest(), "summary.csv":hashlib.sha256(csv_content).hexdigest()})
    receipt["fingerprint"] = digest(receipt)
    install_once(output / "summary.json", content)
    install_once(output / "summary.csv", csv_content)
    install_once(output / "manifest.json", canonical_bytes(receipt)+b"\n")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    for mode in ("freeze", "run", "status", "analyze"):
        modes.add_argument("--"+mode, action="store_true")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--inputs", type=Path, default=REPOSITORY / "task_materials/post_cstat")
    parser.add_argument("--protocol", type=Path, default=REPOSITORY / "results/post_cstat/negative_controls_protocol.json")
    parser.add_argument("--results", type=Path, default=REPOSITORY / "results/post_cstat/negative_controls")
    parser.add_argument("--global-results", type=Path, default=REPOSITORY / "results/post_cstat")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-new-units", type=int)
    parser.add_argument("--list-ids", action="store_true")
    args = parser.parse_args(argv)
    if args.freeze:
        if args.config is None:
            parser.error("--freeze requires --config")
        result = freeze_negative_controls(args.config, args.inputs, args.protocol)
    elif args.status:
        result = negative_status(args.protocol, args.results, list_ids=args.list_ids)
    elif args.run:
        manifest = json.loads(args.protocol.read_text())
        if manifest["config"].get("suite") != "negative_controls":
            raise ValueError("CLI cannot run a deterministic fixture protocol")
        result = run_negative_controls(args.protocol, args.results, global_results_root=args.global_results,
                                       max_new_units=args.max_new_units)
    else:
        if args.output is None:
            parser.error("--analyze requires a fresh --output directory")
        result = analyze_negative_controls(args.protocol, args.results, args.output)
        result = {key:result[key] for key in ("status", "completed_units", "remaining_units", "failed_units")}
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()

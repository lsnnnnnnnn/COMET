"""Whole-trial E6 analysis for a fixed ACS finite-population selection task.

This module never reads ACS rows, generates logging masks or runs a pipeline.
One input is one immutable complete three-split trial on the fixed population.
Unknown frames remain in applicable coverage denominators; unknown false-claim
and return endpoints are not reported as observed zeros. There is no planted
subgroup in this real-covariate task and no causal income-intervention claim.
"""

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re

import numpy as np

from comet.checkpoint_store import CheckpointStore, canonical_bytes, digest, file_hashes, install_once
from comet.post_cstat_statistics import EVENTS, WholeTrialSummary, adjust_validity_family, paired_endpoint_difference
from experiments.pipeline_runner import (
    ARMS, CERTIFIED_ARMS, BOOLEAN_EXTRAS, NUMERIC_EXTRAS,
    _extra_state, _add_extra, _extra_result,
)
from experiments.post_cstat_analyze import _csv_bytes


OUTPUT_NAMES = ("summary.json", "summary.csv", "manifest.json")
NO_DISCOVERY_ARMS = ("fixed_slice", "abstain_reference", "status_quo_reference")
PRIMARY_RETURN_ARMS = ("independent_global", "comet_local", "generic_matched")


def _registered_family(config):
    from experiments.e6_runner import e6_cell_ids, primary_e6_comparisons
    fixture = config.get("suite") == "DETERMINISTIC_E6_FIXTURE"
    if config.get("suite") not in ("E6", "DETERMINISTIC_E6_FIXTURE"):
        raise ValueError("E6 analysis requires its own fixed-population protocol")
    arms, levels = tuple(config.get("arms", ())), tuple(config.get("levels", ()))
    if arms != tuple(ARMS) or levels != (0.05, 0.1):
        raise ValueError("E6 keeps all eight arms and primary/secondary levels on each trial")
    if tuple(config.get("certified_arms", CERTIFIED_ARMS)) != tuple(CERTIFIED_ARMS):
        raise ValueError("E6 certified applicability cannot be changed after outcomes")
    registered = tuple(tuple(value) for value in config.get("primary_comparisons", ()))
    if not registered or any(len(value) != 2 or not all(isinstance(x, str) for x in value) for value in registered) or len(set(registered)) != len(registered):
        raise ValueError("freeze a nonempty unique E6 primary diagnostic family")
    cells = set(e6_cell_ids())
    if any(cell not in cells or arm not in CERTIFIED_ARMS for cell, arm in registered):
        raise ValueError("E6 primary comparison is outside its four cells/certified arms")
    if not fixture and registered != tuple(tuple(value) for value in primary_e6_comparisons()):
        raise ValueError("retain all sixteen frozen E6 certified comparisons")
    if type(config.get("analysis_bootstrap_seed")) is not int or config["analysis_bootstrap_seed"] < 0:
        raise ValueError("an explicit nonnegative E6 analysis seed is required")
    if not fixture and config.get("analysis_bootstrap_resamples") != 2000:
        raise ValueError("production E6 analysis freezes 2000 whole-trial bootstrap resamples")
    for key in ("dataset_population_digest", "archive_sha256"):
        value = config.get(key)
        if not isinstance(value, str) or not value or (not fixture and not re.fullmatch(r"[0-9a-f]{64}", value)):
            raise ValueError("pin the E6 fixed-population and archive identity: " + key)
    return fixture, registered, arms, levels, cells


def _unknown_record(run_id, arm, delta, status):
    record = dict(run_id=run_id, cell=run_id.split("/")[2], method=arm, delta=delta,
        coverage_applicable=arm in CERTIFIED_ARMS, family_covered=False,
        metrics_assessable=False, failure_status=status, mean_coordinate_width=None,
        return_endpoint_applicable=True, discovery_endpoint_applicable=arm not in NO_DISCOVERY_ARMS,
        discovery_best_planted_iou=None)
    record.update({event: False for event in EVENTS})
    return record


def _records(payload, config, arms, levels, cells):
    run_id, result = payload["run_id"], payload["result"]
    parts = run_id.split("/")
    if len(parts) != 4 or parts[1] != "E6" or parts[2] not in cells:
        raise ValueError("checkpoint is outside the fixed E6 source/overlap cells")
    if not isinstance(result, dict) or result.get("suite", "E6") != "E6" or result.get("cell", parts[2]) != parts[2]:
        raise ValueError("E6 checkpoint/run identity mismatch")
    if result.get("legacy_new_outcome_draws", 0) != 0:
        raise ValueError("historical E0 outcomes cannot enter E6")
    for key in ("dataset_population_digest", "archive_sha256"):
        if result.get(key, config[key]) != config[key]:
            raise ValueError("checkpoint uses a different fixed population/archive: " + key)
    expected = {(arm, float(delta)) for arm in arms for delta in levels}
    trials = result.get("trials", [])
    if not isinstance(trials, list):
        raise ValueError("E6 trials must be a list of whole-trial arm/level records")
    found = {}
    for trial in trials:
        if not isinstance(trial, dict) or trial.get("run_id") != run_id or trial.get("cell") != parts[2]:
            raise ValueError("E6 arm/level identity differs from its immutable trial")
        key = trial.get("method"), trial.get("delta")
        if key not in expected or key in found:
            raise ValueError("duplicate or unregistered E6 arm/level frame")
        if trial.get("coverage_applicable") != (key[0] in CERTIFIED_ARMS):
            raise ValueError("E6 certified applicability changed after a failed trial")
        if trial.get("return_endpoint_applicable", True) is not True:
            raise ValueError("E6 return endpoints remain applicable, including abstention")
        expected_discovery = key[0] not in NO_DISCOVERY_ARMS
        if trial.get("discovery_endpoint_applicable", expected_discovery) != expected_discovery:
            raise ValueError("discovery applicability differs from the frozen E6 arm")
        if trial.get("discovery_best_planted_iou") is not None:
            raise ValueError("E6 has no planted subgroup; planted-IoU must be N/A")
        found[key] = trial
    for arm, delta in sorted(expected):
        if (arm, delta) not in found or result.get("unassessable_whole_trial", False):
            status = result.get("status") or "MISSING_E6_FRAME"
            if status == "COMPLETE":
                status = "MISSING_E6_ARM_LEVEL"
            yield _unknown_record(run_id, arm, delta, status)
        else:
            record = dict(found[(arm, delta)])
            record.update(return_endpoint_applicable=True,
                discovery_endpoint_applicable=arm not in NO_DISCOVERY_ARMS,
                discovery_best_planted_iou=None)
            yield record


def _extras(state):
    result = _extra_result(state)
    result["numeric_metrics"]["discovery_best_planted_iou"] = dict(
        applicable=False, mean=None, value_count=0, whole_trials=state["n"], unassessable_trials=0,
        value_scope="NOT_APPLICABLE: real covariates/fixed labels have no planted subgroup")
    return result


def _paired_differences(paired, config, arms, levels, resamples):
    differences = []
    for cell in sorted({key[0] for key in paired}):
        for delta in levels:
            left = paired.get((cell, "comet_local", delta), {})
            for arm in arms:
                if arm == "comet_local":
                    continue
                right = paired.get((cell, arm, delta), {})
                if not left and not right:
                    continue
                seed = int.from_bytes(hashlib.sha256(
                    f"{config['analysis_bootstrap_seed']}\0E6\0{cell}\0{arm}\0{delta}".encode()).digest()[:8], "little")
                record = dict(cell=cell, delta=delta, left="comet_local", right=arm,
                    endpoint="return_safe_useful", pairing_unit="full independent logging/pipeline trial run ID",
                    bootstrap_seed=seed, independent_pairs=len(set(left) | set(right)),
                    mean_difference=None, bootstrap_pointwise95=None)
                if set(left) != set(right) or any(value is None for value in list(left.values()) + list(right.values())):
                    record["status"] = "UNASSESSABLE_FULL_PAIR_SET"
                elif resamples:
                    record.update(paired_endpoint_difference(left, right, bootstrap_seed=seed, resamples=resamples),
                                  status="PAIRED_BOOTSTRAP_POINTWISE_NOT_SIMULTANEOUS")
                else:
                    record.update(status="DESCRIPTIVE_NO_BOOTSTRAP", resamples=0,
                        mean_difference=float(np.mean([float(left[key])-float(right[key]) for key in sorted(left)])))
                differences.append(record)
    return differences


def _csv_content(rows):
    base = csv.DictReader(io.StringIO(_csv_bytes(rows).decode()))
    columns = list(base.fieldnames) + ["primary_return_guarantee_applicable", "actual_family_size_counts"]
    columns += [key + "_" + suffix for key in BOOLEAN_EXTRAS for suffix in ("rate", "unknown_trials")]
    columns += [key + "_mean" for key in NUMERIC_EXTRAS]
    columns += ["discovery_best_planted_iou_applicable"]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns)
    writer.writeheader()
    for flat, row in zip(base, rows):
        flat["primary_return_guarantee_applicable"] = row["primary_return_guarantee_applicable"]
        extra = row["pipeline_metrics"]
        flat["actual_family_size_counts"] = json.dumps(extra["actual_family_size_counts"], sort_keys=True)
        for key, value in extra["joint_events"].items():
            flat[key + "_rate"], flat[key + "_unknown_trials"] = value["rate"], value["unknown_trials"]
        for key, value in extra["numeric_metrics"].items():
            flat[key + "_mean"] = value["mean"]
        flat["discovery_best_planted_iou_applicable"] = False
        writer.writerow(flat)
    return stream.getvalue().encode()


def analyze_e6(protocol_path, results_root, output_directory, *, bootstrap_resamples=None):
    """Stream one complete trial at a time; do not pool people or coordinates."""
    path, root, output = Path(protocol_path), Path(results_root), Path(output_directory)
    if any((output / name).exists() for name in OUTPUT_NAMES):
        raise FileExistsError("E6 analysis artifacts are immutable; select a fresh directory")
    manifest = json.loads(path.read_text())
    config = manifest["config"]
    fixture, registered, arms, levels, cells = _registered_family(config)
    if bootstrap_resamples is None:
        bootstrap_resamples = config.get("analysis_bootstrap_resamples", 0 if fixture else 2000)
    if type(bootstrap_resamples) is not int or bootstrap_resamples < 0 or (not fixture and bootstrap_resamples != 2000):
        raise ValueError("production E6 uses its frozen 2000 whole-trial bootstrap resamples")
    store = CheckpointStore(root, manifest)
    summaries, extra, paired = {}, {}, defaultdict(dict)
    completed, inventory, statuses = set(), [], Counter()
    failed = unassessable = scientific_units = 0
    for payload in store.iter_completed():
        run_id, result = payload["run_id"], payload["result"]
        completed.add(run_id)
        inventory.append([run_id, digest(payload)])
        statuses[result.get("status", "STATUS_MISSING")] += 1
        unit_failed = unit_unknown = False
        for row in _records(payload, config, arms, levels, cells):
            key = row["cell"], row["method"], row["delta"]
            summaries.setdefault(key, WholeTrialSummary()).add(row)
            _add_extra(extra.setdefault(key, _extra_state()), row)
            assessable = bool(row.get("metrics_assessable", True))
            # Known algorithmic failures/abstention stay as actual False returns;
            # unknown trials invalidate a paired CI rather than select a subset.
            paired[key][run_id] = bool(row["return_safe_useful"]) if assessable else None
            unit_failed |= bool(row.get("failure_status"))
            unit_unknown |= not assessable
        failed += unit_failed
        unassessable += unit_unknown
        expected_units = 0 if fixture else 1
        if result.get("new_scientific_units", expected_units) != expected_units:
            raise ValueError("E6 scientific-unit accounting differs from protocol phase")
        scientific_units += expected_units
    rows = []
    for key in sorted(summaries):
        row = summaries[key].result()
        row["pipeline_metrics"] = _extras(extra[key])
        row["primary_return_guarantee_applicable"] = row["method"] in PRIMARY_RETURN_ARMS
        rows.append(row)
    adjusted = adjust_validity_family(rows, registered)
    primary = {(row["cell"], row["method"]): row for row in rows if row["delta"] == 0.05}
    for row in rows:
        row["holm_undercoverage_p"] = adjusted.get((row["cell"], row["method"])) if row["delta"] == 0.05 else None
    diagnostics = [dict(cell=cell, method=arm,
        undercoverage_p=(primary.get((cell, arm), {}).get("family_coverage") or {}).get("undercoverage_p"),
        holm_undercoverage_p=adjusted[cell, arm]) for cell, arm in registered]
    remaining = sorted(store.planned - completed)
    status = "NO_COMPLETED_UNITS" if not completed else ("COMPLETE" if not remaining else "PARTIAL")
    summary = dict(schema="post-cstat-E6-analysis-v1", status=status, suite="E6",
        phase="DETERMINISTIC_FIXTURE_NOT_REAL_ACS_OR_SCIENCE" if fixture else "confirmatory",
        protocol_fingerprint=manifest["fingerprint"], dataset_population_digest=config["dataset_population_digest"],
        archive_sha256=config["archive_sha256"], completed_units=len(completed), remaining_units=len(remaining),
        planned_units=len(store.planned), failed_units=failed, unassessable_units=unassessable,
        completed_ids=sorted(completed), remaining_ids=remaining, checkpoint_inventory_sha256=digest(inventory),
        checkpoint_status_counts=dict(statuses), summaries=rows, reported_new_scientific_units=scientific_units,
        primary_comparison_count=len(registered), primary_diagnostics=diagnostics,
        diagnostic_status="FINAL_FIXED_SAMPLE_DIAGNOSTIC" if completed and not remaining else "PARTIAL_DESCRIPTIVE_DIAGNOSTIC_NOT_A_STOPPING_RULE",
        paired_safe_useful_differences=_paired_differences(paired, config, arms, levels, bootstrap_resamples),
        analysis_bootstrap_seed=config["analysis_bootstrap_seed"], bootstrap_resamples=bootstrap_resamples,
        analysis_new_outcome_draws=0, legacy_new_outcome_draws=0,
        historical_primary_families_modified=False, E5_primary_family_modified=False,
        replication_unit="one independent three-split logging/pipeline trial on a fixed population; arms and levels share all three logs",
        sampling_scope="finite fixed CA2018 covariates/labels; not independent people resampled or a social intervention",
        safety_scope="return_unsafe is primary discovered-family risk; return_and_infeasible includes utility/service/capacity",
        applicability="three discovered-family certified engines guarantee primary-family return; fixed_slice covers only its own coordinates",
        uncertainty="pointwise Monte Carlo Wilson and paired bootstrap; no automatic unsafe-given-return or cross-arm/level guarantee",
        planted_subgroup="NOT_APPLICABLE; no planted group or planted-IoU recovery claim",
        equivalent_arms=[["comet_local", "generic_matched"]])
    content, csv_content = canonical_bytes(summary) + b"\n", _csv_content(rows)
    source_paths = [Path(__file__).resolve(), Path(__file__).with_name("e6_runner.py"),
        Path(__file__).with_name("semisynthetic_selective_labels.py"), Path(__file__).with_name("pipeline_runner.py"),
        Path(__file__).with_name("post_cstat_analyze.py")]
    source_paths += [Path(__file__).resolve().parents[1] / name for name in
        ("comet/post_cstat_statistics.py", "comet/checkpoint_store.py", "comet/metrics.py", "comet/gate_c_statistics.py")]
    receipt = dict(schema="post-cstat-E6-analysis-manifest-v1", status=status,
        protocol_path=str(path.resolve()), results_root=str(root.resolve()),
        protocol_fingerprint=manifest["fingerprint"], dataset_population_digest=config["dataset_population_digest"],
        archive_sha256=config["archive_sha256"], analysis_sources=file_hashes(source_paths),
        input_scientific_sources=manifest["sources"], primary_family_sha256=digest(registered),
        completed_units=len(completed), remaining_units=len(remaining), analysis_new_outcome_draws=0,
        outputs={"summary.json": hashlib.sha256(content).hexdigest(), "summary.csv": hashlib.sha256(csv_content).hexdigest()})
    receipt["analysis_fingerprint"] = digest(receipt)
    install_once(output / "summary.json", content)
    install_once(output / "summary.csv", csv_content)
    install_once(output / "manifest.json", canonical_bytes(receipt) + b"\n")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    summary = analyze_e6(args.protocol, args.results, args.output)
    print(json.dumps({key: summary[key] for key in ("suite", "status", "completed_units", "remaining_units",
        "failed_units", "unassessable_units", "primary_comparison_count", "analysis_new_outcome_draws")}, indent=2))


if __name__ == "__main__":
    main()

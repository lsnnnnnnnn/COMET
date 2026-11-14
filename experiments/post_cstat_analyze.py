"""Stream immutable E1 checkpoints into complete-log performance summaries.

No data are generated. Missing method/level results and wholly unassessable
failed checkpoints remain in every applicable coverage denominator. Unknown
false-claim endpoints remain unknown, rather than becoming observed zeros.
E1 is an auditing experiment: policy-return and discovery endpoints are N/A.
"""

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path

from comet.checkpoint_store import (
    CheckpointStore, canonical_bytes, digest, file_hashes, install_once,
)
from comet.post_cstat_statistics import EVENTS, WholeTrialSummary, adjust_validity_family
from experiments.post_cstat_runner import LEVELS, primary_e1_comparisons


OUTPUT_NAMES = ("summary.json", "summary.csv", "manifest.json")


def _registered_family(config):
    if config.get("suite") not in ("E1", "DETERMINISTIC_RUNNER_FIXTURE"):
        raise ValueError("this analyzer only implements E1")
    registered = tuple(tuple(item) for item in config.get("primary_comparisons", ()))
    if not registered or any(len(item) != 2 or not all(isinstance(value, str) for value in item)
                             for item in registered) or len(set(registered)) != len(registered):
        raise ValueError("freeze a nonempty unique E1 primary comparison family")
    if config["suite"] == "E1" and registered != tuple(tuple(item) for item in primary_e1_comparisons()):
        raise ValueError("production E1 must retain its complete frozen 96-comparison family")
    levels = tuple(config.get("levels", ()))
    if levels != LEVELS:
        raise ValueError("E1 requires primary .05 and secondary .10 on the same logs")
    methods = defaultdict(list)
    for cell, method in registered:
        methods[cell].append(method)
    return registered, levels, methods


def _unknown_trial(run_id, cell, method, delta, status):
    trial = dict(run_id=run_id, cell=cell, method=method, delta=delta,
        coverage_applicable=True, family_covered=False, failure_status=status,
        metrics_assessable=False, mean_coordinate_width=None,
        return_endpoint_applicable=False, discovery_endpoint_applicable=False,
        endpoint_scope="E1 auditing only; failed whole-log decision endpoints are unknown")
    trial.update({event: False for event in EVENTS})
    return trial


def _checkpoint_trials(payload, config, levels, methods):
    """Yield exactly one record per expected method/level for this whole log."""
    run_id = payload["run_id"]
    parts = run_id.split("/")
    if len(parts) != 4 or parts[1] != "E1" or parts[2] not in methods:
        raise ValueError("checkpoint is outside the frozen E1 comparison cells")
    cell, result = parts[2], payload["result"]
    if not isinstance(result, dict) or result.get("cell", cell) != cell:
        raise ValueError("checkpoint result cell does not match its immutable run ID")
    if result.get("legacy_new_outcome_draws", 0) != 0:
        raise ValueError("E0 additional outcomes cannot enter the E1 analysis")
    records = result.get("trials", [])
    if not isinstance(records, list):
        raise ValueError("checkpoint trials must be a list of whole-log records")
    expected = {(method, delta) for method in methods[cell] for delta in levels}
    by_key = {}
    for trial in records:
        if not isinstance(trial, dict) or trial.get("run_id") != run_id or trial.get("cell") != cell:
            raise ValueError("method/level trial identity does not match its checkpoint")
        key = (trial.get("method"), trial.get("delta"))
        if key not in expected:
            raise ValueError("method/level trial is outside the frozen E1 applicability family")
        if key in by_key:
            raise ValueError("duplicate method/level record in one complete log")
        if trial.get("coverage_applicable") is not True:
            raise ValueError("E1 certified applicability cannot disappear after a failure")
        if any(trial.get(event, False) for event in ("returned", "return_unsafe", "return_safe_useful", "discovered_and_certified")):
            raise ValueError("E1 contains no policy-return or discovery experiment")
        by_key[key] = trial
    whole_unassessable = bool(result.get("unassessable_whole_trial", False))
    for method, delta in sorted(expected):
        key = method, delta
        if key not in by_key or whole_unassessable:
            status = result.get("status") or "MISSING_METHOD_LEVEL_RESULT"
            if status == "COMPLETE":
                status = "MISSING_METHOD_LEVEL_RESULT"
            yield _unknown_trial(run_id, cell, method, delta, status)
        else:
            trial = dict(by_key[key])
            trial["return_endpoint_applicable"] = False
            trial["discovery_endpoint_applicable"] = False
            yield trial


def _csv_bytes(rows):
    columns = ["cell", "method", "delta", "independent_trials", "coverage_hits",
               "coverage_denominator", "coverage_rate", "coverage_wilson95_lo",
               "coverage_wilson95_hi", "undercoverage_p", "holm_undercoverage_p",
               "mean_per_trial_coordinate_width", "width_trials", "status_counts"]
    for event in EVENTS:
        columns.extend(event + "_" + suffix for suffix in (
            "applicable", "hits", "denominator", "unknown_trials", "rate",
            "wilson95_lo", "wilson95_hi", "realized_frequency_lo", "realized_frequency_hi"))
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns)
    writer.writeheader()
    for row in rows:
        coverage = row["family_coverage"] or {}
        coverage_wilson = coverage.get("wilson95") or [None, None]
        flat = dict(cell=row["cell"], method=row["method"], delta=row["delta"],
            independent_trials=row["independent_trials"], coverage_hits=coverage.get("hits"),
            coverage_denominator=coverage.get("denominator"), coverage_rate=coverage.get("rate"),
            coverage_wilson95_lo=coverage_wilson[0], coverage_wilson95_hi=coverage_wilson[1],
            undercoverage_p=coverage.get("undercoverage_p"), holm_undercoverage_p=row["holm_undercoverage_p"],
            mean_per_trial_coordinate_width=row["mean_per_trial_coordinate_width"],
            width_trials=row["width_trials"],
            status_counts=json.dumps(row["status_counts"], sort_keys=True, separators=(",", ":")))
        for event, value in row["endpoints"].items():
            for key in ("applicable", "hits", "denominator", "unknown_trials", "rate"):
                flat[event + "_" + key] = value[key]
            uncertainty = value["wilson95"] or [None, None]
            bounds = value["realized_frequency_bounds"] or [None, None]
            flat[event + "_wilson95_lo"], flat[event + "_wilson95_hi"] = uncertainty
            flat[event + "_realized_frequency_lo"], flat[event + "_realized_frequency_hi"] = bounds
        writer.writerow(flat)
    return stream.getvalue().encode("utf-8")


def analyze_e1(protocol_path, results_root, output_directory):
    """Analyze one checkpoint at a time; no candidate or log pooling in RAM."""
    protocol_path, results_root, output = Path(protocol_path), Path(results_root), Path(output_directory)
    if any((output / name).exists() for name in OUTPUT_NAMES):
        raise FileExistsError("analysis artifacts are immutable; select a fresh output directory")
    manifest = json.loads(protocol_path.read_text())
    config = manifest["config"]
    registered, levels, methods = _registered_family(config)
    store = CheckpointStore(results_root, manifest)
    summaries, completed, inventory = {}, set(), []
    checkpoint_statuses = Counter()
    failed_units = unassessable_units = unknown_records = reported_scientific_units = 0
    for payload in store.iter_completed():
        run_id, result = payload["run_id"], payload["result"]
        completed.add(run_id)
        inventory.append([run_id, digest(payload)])
        checkpoint_statuses[result.get("status", "STATUS_MISSING")] += 1
        failed, unassessable = False, False
        for trial in _checkpoint_trials(payload, config, levels, methods):
            key = trial["cell"], trial["method"], trial["delta"]
            summaries.setdefault(key, WholeTrialSummary()).add(trial)
            failed |= bool(trial.get("failure_status"))
            unknown = not bool(trial.get("metrics_assessable", True))
            unassessable |= unknown
            unknown_records += unknown
        failed_units += failed
        unassessable_units += unassessable
        declared_units = result.get("new_scientific_units", 0 if config["suite"] == "DETERMINISTIC_RUNNER_FIXTURE" else 1)
        if declared_units != (0 if config["suite"] == "DETERMINISTIC_RUNNER_FIXTURE" else 1):
            raise ValueError("checkpoint scientific-unit accounting does not match its protocol phase")
        reported_scientific_units += declared_units
    rows = [summaries[key].result() for key in sorted(summaries)]
    holm = adjust_validity_family(rows, registered)
    for row in rows:
        row["holm_undercoverage_p"] = holm[(row["cell"], row["method"])] if row["delta"] == .05 else None
    remaining = sorted(store.planned - completed)
    diagnostics = []
    primary_rows = {(row["cell"], row["method"]): row for row in rows if row["delta"] == .05}
    for cell, method in registered:
        coverage = primary_rows.get((cell, method), {}).get("family_coverage")
        diagnostics.append(dict(cell=cell, method=method,
            undercoverage_p=coverage["undercoverage_p"] if coverage else None,
            holm_undercoverage_p=holm[(cell, method)]))
    status = "NO_COMPLETED_UNITS" if not completed else ("COMPLETE" if not remaining else "PARTIAL")
    summary = dict(schema="post-cstat-E1-analysis-v1", status=status, suite="E1",
        phase="DETERMINISTIC_FIXTURE_NOT_SCIENCE" if config["suite"] == "DETERMINISTIC_RUNNER_FIXTURE" else "confirmatory",
        protocol_fingerprint=manifest["fingerprint"], completed_units=len(completed),
        planned_units=len(store.planned), remaining_units=len(remaining), failed_units=failed_units,
        unassessable_units=unassessable_units, unknown_method_level_records=unknown_records,
        reported_new_scientific_units=reported_scientific_units,
        analysis_new_outcome_draws=0, legacy_new_outcome_draws=0,
        checkpoint_status_counts=dict(checkpoint_statuses), completed_ids=sorted(completed), remaining_ids=remaining,
        checkpoint_inventory_sha256=digest(inventory), summaries=rows,
        primary_comparison_count=len(registered), primary_diagnostics=diagnostics,
        diagnostic_status="FINAL_FIXED_SAMPLE_DIAGNOSTIC" if completed and not remaining else "PARTIAL_DESCRIPTIVE_DIAGNOSTIC_NOT_A_STOPPING_RULE",
        historical_primary_family_modified=False,
        uncertainty="pointwise Monte Carlo Wilson intervals per fixed cell/method; unknown endpoint rates and Wilson intervals are null",
        method_level_event_scope="separate simultaneous coordinate event for each method and level; no joint claim over engines or levels",
        replication_unit="one complete independent log, shared by all methods and both levels",
        failed_coverage_rule="all applicable failures stay in the coverage denominator; unassessable decision metrics remain unknown",
        E1_return_and_discovery="NOT_APPLICABLE; E1 does not measure pipeline usefulness")
    content = canonical_bytes(summary) + b"\n"
    csv_content = _csv_bytes(rows)
    analysis_sources = [Path(__file__).resolve(),
        Path(__file__).resolve().parents[1] / "comet/post_cstat_statistics.py",
        Path(__file__).resolve().parents[1] / "comet/checkpoint_store.py",
        Path(__file__).resolve().parents[1] / "comet/metrics.py",
        Path(__file__).resolve().parents[1] / "comet/gate_c_statistics.py",
        Path(__file__).resolve().parents[1] / "experiments/post_cstat_runner.py"]
    receipt = dict(schema="post-cstat-E1-analysis-manifest-v1", status=status,
        protocol_path=str(protocol_path.resolve()), protocol_fingerprint=manifest["fingerprint"],
        results_root=str(results_root.resolve()), analysis_sources=file_hashes(analysis_sources),
        input_scientific_sources=manifest["sources"], completed_units=len(completed),
        remaining_units=len(remaining), primary_comparison_count=len(registered),
        primary_family_sha256=digest(registered), analysis_new_outcome_draws=0,
        outputs={"summary.json": hashlib.sha256(content).hexdigest(),
                 "summary.csv": hashlib.sha256(csv_content).hexdigest()})
    receipt["analysis_fingerprint"] = digest(receipt)
    install_once(output / "summary.json", content)
    install_once(output / "summary.csv", csv_content)
    install_once(output / "manifest.json", canonical_bytes(receipt) + b"\n")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path,
                        help="new analysis directory; existing analysis artifacts are never overwritten")
    args = parser.parse_args(argv)
    summary = analyze_e1(args.protocol, args.results, args.output)
    print(json.dumps({key: summary[key] for key in (
        "status", "phase", "completed_units", "remaining_units", "failed_units",
        "unassessable_units", "primary_comparison_count", "analysis_new_outcome_draws",
        "legacy_new_outcome_draws")}, indent=2))


if __name__ == "__main__":
    main()

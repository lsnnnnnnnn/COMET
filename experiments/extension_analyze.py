"""Immutable whole-log E2/E3/E4 analysis; no scientific outcomes are drawn.

Unknown method/level frames retain their full coverage denominators. Unknown
decision metrics are not observed zeros. Return/discovery are N/A in these
audit suites. Performance bootstrap units are complete paired replicate IDs.
"""

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path

import numpy as np

from comet.checkpoint_store import CheckpointStore, canonical_bytes, digest, file_hashes, install_once
from comet.metrics import wilson
from comet.post_cstat_statistics import (
    EVENTS, WholeTrialSummary, adjust_validity_family, paired_endpoint_difference,
)
from experiments.post_cstat_analyze import _csv_bytes
from experiments.extension_runner import (
    JOINT_LEVEL, effective_suite, methods_for_extension_cell, primary_extension_comparisons, suite_cells,
)


OUTPUT_NAMES = ("summary.json", "summary.csv", "manifest.json")
EXTRA_EVENTS = {
    "E4": ("primary_certified_safe", "primary_certified_violation", "primary_false_safe", "primary_false_violation"),
    "E3": ("contrast_improvement_detected", "contrast_false_improvement", "contrast_noninferiority_certified"),
}
ALL_EXTRA_EVENTS = tuple(event for events in EXTRA_EVENTS.values() for event in events)
WIDTH_COMPARATORS = ("generic_matched", "truncated_global_graph", "truncated_global_envelope", JOINT_LEVEL)


def _registered_family(config):
    suite = effective_suite(config)
    fixture = config.get("suite") == "DETERMINISTIC_EXTENSION_FIXTURE"
    if not fixture and config.get("suite") != suite:
        raise ValueError("production analysis requires the declared E2/E3/E4 suite")
    registered = tuple(tuple(value) for value in config.get("primary_comparisons", ()))
    if (not registered or any(len(value) != 2 or not all(isinstance(x, str) for x in value)
                              for value in registered)
            or len(set(registered)) != len(registered)):
        raise ValueError("freeze a nonempty unique suite-specific primary family")
    if not fixture and registered != tuple(tuple(value) for value in primary_extension_comparisons(suite)):
        raise ValueError("production extension must retain its complete suite-specific primary family")
    for cell, method in registered:
        if cell not in suite_cells(suite) or method not in methods_for_extension_cell(suite, cell):
            raise ValueError("primary cell/method is outside this suite's eligible grid")
    levels = tuple(config.get("levels", ()))
    if levels != (.05, .1):
        raise ValueError("primary .05 and secondary .10 must share the same complete logs")
    seed = config.get("analysis_bootstrap_seed")
    if type(seed) is not int or seed < 0:
        raise ValueError("an explicit nonnegative analysis bootstrap seed is required")
    if not fixture and config.get("analysis_bootstrap_resamples") != 2000:
        raise ValueError("production analysis must explicitly freeze 2000 bootstrap resamples")
    methods = defaultdict(list)
    for cell, method in registered:
        methods[cell].append(method)
    return suite, fixture, registered, levels, methods


def _unknown_trial(run_id, cell, method, delta, status):
    return dict(run_id=run_id, cell=cell, method=method, delta=delta,
        coverage_applicable=True, family_covered=False, failure_status=status,
        metrics_assessable=False, mean_coordinate_width=None,
        return_endpoint_applicable=False, discovery_endpoint_applicable=False,
        **{event: False for event in EVENTS})


def _checkpoint_trials(payload, suite, levels, methods):
    run_id = payload["run_id"]
    parts = run_id.split("/")
    if len(parts) != 4 or parts[1] != suite or parts[2] not in methods:
        raise ValueError("checkpoint ID is outside the frozen extension suite/cells")
    cell, result = parts[2], payload["result"]
    if not isinstance(result, dict) or result.get("cell", cell) != cell or result.get("suite", suite) != suite:
        raise ValueError("checkpoint result identity does not match its immutable run ID")
    if result.get("legacy_new_outcome_draws", 0) != 0:
        raise ValueError("legacy E0 outcomes cannot enter extension analysis")
    records = result.get("trials", [])
    if not isinstance(records, list):
        raise ValueError("trials must contain complete-log method/level frames")
    expected = {(method, delta) for method in methods[cell] for delta in levels}
    by_key = {}
    for record in records:
        if not isinstance(record, dict) or record.get("run_id") != run_id or record.get("cell") != cell:
            raise ValueError("trial identity differs from its immutable checkpoint")
        key = record.get("method"), record.get("delta")
        if key not in expected:
            raise ValueError("unknown method/level frame outside frozen applicability")
        if key in by_key:
            raise ValueError("duplicate method/level frame in one complete log")
        if record.get("coverage_applicable") is not True:
            raise ValueError("certified applicability cannot disappear after a failed trial")
        if any(record.get(event, False) for event in ("returned", "return_unsafe", "return_safe_useful", "discovered_and_certified")):
            raise ValueError("extension audit suites contain no return or discovery experiment")
        by_key[key] = record
    for method, delta in sorted(expected):
        if (method, delta) not in by_key or result.get("unassessable_whole_trial", False):
            status = result.get("status") or "MISSING_METHOD_LEVEL_RESULT"
            if status == "COMPLETE":
                status = "MISSING_METHOD_LEVEL_RESULT"
            yield _unknown_trial(run_id, cell, method, delta, status)
        else:
            trial = dict(by_key[(method, delta)])
            trial.update(return_endpoint_applicable=False, discovery_endpoint_applicable=False)
            yield trial


def _extra_result(suite, n, counts, unknown):
    result = {}
    for event in ALL_EXTRA_EVENTS:
        applicable = event in EXTRA_EVENTS.get(suite, ())
        hits, missing = counts[event], unknown[event]
        result[event] = dict(applicable=applicable, hits=hits if applicable else None,
            denominator=n if applicable else 0, unknown_trials=missing if applicable else 0,
            rate=hits/n if applicable and not missing else None,
            wilson95=list(wilson(hits, n)) if applicable and not missing else None,
            realized_frequency_bounds=[hits/n, (hits+missing)/n] if applicable else None)
    return result


def _width_comparisons(widths, seed, resamples):
    results = []
    for cell, method, delta in sorted(widths):
        if method != "comet_local":
            continue
        left = widths[cell, method, delta]
        for comparator in WIDTH_COMPARATORS:
            right = widths.get((cell, comparator, delta))
            if right is None:
                continue
            keys = set(left) | set(right)
            unknown = sum(left.get(key) is None or right.get(key) is None for key in keys)
            record = dict(cell=cell, delta=delta, left_method=method, right_method=comparator,
                independent_pairs=len(keys), unknown_or_failed_pairs=unknown,
                resampling_unit="complete_independent_log_ID; methods share observations",
                mean_difference=None, bootstrap_pointwise95=None)
            if set(left) != set(right) or unknown:
                results.append(dict(record, status="UNASSESSABLE_COMPLETE_PAIR_SET"))
                continue
            mean = float(sum(left[key]-right[key] for key in sorted(keys))/len(keys))
            if resamples == 0:
                results.append(dict(record, status="DESCRIPTIVE_BOOTSTRAP_DISABLED", mean_difference=mean))
                continue
            label = f"{seed}\0{cell}\0{comparator}\0{delta}".encode()
            role_seed = int.from_bytes(hashlib.sha256(label).digest()[:8], "little")
            result = paired_endpoint_difference(left, right, bootstrap_seed=role_seed, resamples=resamples)
            results.append(dict(record, **result, status="PAIRED_POINTWISE_BOOTSTRAP"))
    return results


def _extension_csv(rows, suite):
    base = csv.DictReader(io.StringIO(_csv_bytes(rows).decode()))
    columns = list(base.fieldnames) + ["suite"]
    for event in ALL_EXTRA_EVENTS:
        columns.extend(event + "_" + suffix for suffix in
            ("applicable", "hits", "denominator", "unknown_trials", "rate", "wilson95_lo", "wilson95_hi"))
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns)
    writer.writeheader()
    for flat, row in zip(base, rows):
        flat["suite"] = suite
        for event, value in row["extension_endpoints"].items():
            for key in ("applicable", "hits", "denominator", "unknown_trials", "rate"):
                flat[event+"_"+key] = value[key]
            interval = value["wilson95"] or [None, None]
            flat[event+"_wilson95_lo"], flat[event+"_wilson95_hi"] = interval
        writer.writerow(flat)
    return stream.getvalue().encode()


def analyze_extension(protocol_path, results_root, output_directory, *, bootstrap_resamples=None):
    protocol_path, root, output = Path(protocol_path), Path(results_root), Path(output_directory)
    if any((output/name).exists() for name in OUTPUT_NAMES):
        raise FileExistsError("analysis outputs are immutable; use a fresh directory")
    manifest = json.loads(protocol_path.read_text())
    config = manifest["config"]
    suite, fixture, registered, levels, methods = _registered_family(config)
    resamples = config.get("analysis_bootstrap_resamples", 0 if fixture else 2000) if bootstrap_resamples is None else bootstrap_resamples
    if type(resamples) is not int or resamples < 0 or (not fixture and resamples != 2000):
        raise ValueError("production resamples are fixed at 2000; fixture resamples may be zero")
    store = CheckpointStore(root, manifest)
    summaries, extras, extra_unknown = {}, defaultdict(Counter), defaultdict(Counter)
    widths, inventory, completed, statuses = defaultdict(dict), [], set(), Counter()
    failed_units = unassessable_units = unknown_records = scientific_units = 0
    for payload in store.iter_completed():
        run_id, result = payload["run_id"], payload["result"]
        if run_id in completed:
            raise ValueError("duplicate checkpoint independent ID")
        completed.add(run_id)
        inventory.append([run_id, digest(payload)])
        statuses[result.get("status", "STATUS_MISSING")] += 1
        failed = unassessable = False
        for trial in _checkpoint_trials(payload, suite, levels, methods):
            key = trial["cell"], trial["method"], trial["delta"]
            summaries.setdefault(key, WholeTrialSummary()).add(trial)
            assessable = bool(trial.get("metrics_assessable", True))
            failed |= bool(trial.get("failure_status"))
            unknown_records += not assessable
            unassessable |= not assessable
            for event in EXTRA_EVENTS.get(suite, ()):
                value = trial.get(event)
                if not assessable or value is None:
                    extra_unknown[key][event] += 1
                elif isinstance(value, (bool, np.bool_)):
                    extras[key][event] += bool(value)
                else:
                    raise ValueError("applicable extension endpoint must be boolean or explicitly unknown")
            width = trial.get("mean_coordinate_width")
            widths[key][run_id] = float(width) if assessable and not trial.get("failure_status") and width is not None else None
        failed_units += failed
        unassessable_units += unassessable
        expected_units = 0 if fixture else 1
        if result.get("new_scientific_units", expected_units) != expected_units:
            raise ValueError("scientific unit count does not match the protocol phase")
        scientific_units += expected_units
    rows = []
    for key in sorted(summaries):
        row = summaries[key].result()
        row["extension_endpoints"] = _extra_result(suite, row["independent_trials"], extras[key], extra_unknown[key])
        rows.append(row)
    holm = adjust_validity_family(rows, registered)
    for row in rows:
        row["holm_undercoverage_p"] = holm[row["cell"], row["method"]] if row["delta"] == .05 else None
    primary = {(row["cell"], row["method"]): row for row in rows if row["delta"] == .05}
    diagnostics = [dict(cell=cell, method=method,
        undercoverage_p=(primary.get((cell, method), {}).get("family_coverage") or {}).get("undercoverage_p"),
        holm_undercoverage_p=holm[cell, method]) for cell, method in registered]
    remaining = sorted(store.planned-completed)
    status = "NO_COMPLETED_UNITS" if not completed else ("PARTIAL" if remaining else "COMPLETE")
    summary = dict(schema="post-cstat-extension-analysis-v1", suite=suite, status=status,
        phase="DETERMINISTIC_FIXTURE_NOT_SCIENCE" if fixture else "confirmatory",
        protocol_fingerprint=manifest["fingerprint"], completed_units=len(completed), planned_units=len(store.planned),
        remaining_units=len(remaining), failed_units=failed_units, unassessable_units=unassessable_units,
        unknown_method_level_records=unknown_records, reported_new_scientific_units=scientific_units,
        analysis_new_outcome_draws=0, legacy_new_outcome_draws=0,
        completed_ids=sorted(completed), remaining_ids=remaining, checkpoint_status_counts=dict(statuses),
        checkpoint_inventory_sha256=digest(inventory), summaries=rows,
        primary_comparison_count=len(registered), primary_diagnostics=diagnostics,
        historical_primary_family_modified=False, E1_primary_family_modified=False,
        diagnostic_status="FINAL_FIXED_SAMPLE_DIAGNOSTIC" if completed and not remaining else "PARTIAL_DESCRIPTIVE_DIAGNOSTIC_NOT_A_STOPPING_RULE",
        analysis_bootstrap_seed=config["analysis_bootstrap_seed"], analysis_bootstrap_resamples=resamples,
        paired_width_differences=_width_comparisons(widths, config["analysis_bootstrap_seed"], resamples),
        return_and_discovery="NOT_APPLICABLE; these suites do not measure pipeline usefulness",
        replication_unit="one complete independent log shared by methods/levels; E2 outside variants retain paired replicate IDs",
        uncertainty="pointwise Wilson/paired-bootstrap Monte Carlo uncertainty; unknown rates and Wilson intervals remain null",
        method_level_event_scope="separate simultaneous family event per method and level; no joint theorem over engines/levels",
        failed_coverage_rule="every applicable failed frame remains in the complete-log coverage denominator")
    content, csv_content = canonical_bytes(summary)+b"\n", _extension_csv(rows, suite)
    sources = [Path(__file__).resolve(), Path(__file__).with_name("extension_runner.py"),
               Path(__file__).with_name("post_cstat_analyze.py")]
    sources += [Path(__file__).resolve().parents[1]/name for name in
                ("comet/post_cstat_statistics.py", "comet/checkpoint_store.py", "comet/metrics.py", "comet/gate_c_statistics.py")]
    receipt = dict(schema="post-cstat-extension-analysis-manifest-v1", suite=suite, status=status,
        protocol_path=str(protocol_path.resolve()), results_root=str(root.resolve()),
        protocol_fingerprint=manifest["fingerprint"], analysis_sources=file_hashes(sources),
        input_scientific_sources=manifest["sources"], primary_comparison_count=len(registered),
        primary_family_sha256=digest(registered), completed_units=len(completed), remaining_units=len(remaining),
        analysis_new_outcome_draws=0, outputs={"summary.json":hashlib.sha256(content).hexdigest(),
                                             "summary.csv":hashlib.sha256(csv_content).hexdigest()})
    receipt["analysis_fingerprint"] = digest(receipt)
    install_once(output/"summary.json", content)
    install_once(output/"summary.csv", csv_content)
    install_once(output/"manifest.json", canonical_bytes(receipt)+b"\n")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = analyze_extension(args.protocol, args.results, args.output)
    print(json.dumps({key: result[key] for key in ("suite", "status", "completed_units", "remaining_units",
        "failed_units", "unassessable_units", "primary_comparison_count", "analysis_new_outcome_draws")}, indent=2))


if __name__ == "__main__":
    main()

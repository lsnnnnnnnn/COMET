"""C-PREFLIGHT only: frozen seeds, incremental atomic checkpoints, honest resume.

This entry point has no confirmatory-run mode. The 1000-replication lists are
reserved in the preregistration and never selected by this runner.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time
import traceback

from comet.gate_c_contract import cell_from_dict
from comet.gate_c_methods import evaluate_method
from comet.gate_c_seeds import seed_streams, run_id, SEED_VERSION, STREAM_NAMES
from comet.gate_c_simulation import generate_evaluation
from comet.gate_c_statistics import summarize_records

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "gate-c-preflight-record-v1"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+".tmp")
    with temporary.open("w") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+"\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def read_json(path):
    return json.loads(Path(path).read_text())


def source_checksums():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ("comet", "experiments") for p in sorted((ROOT/folder).glob("*.py"))}


def peak_rss_bytes():
    # Darwin reports bytes; Linux reports KiB. This is process high-water RSS,
    # not an isolated allocation estimate for an individual method.
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value*1024)


def environment():
    return dict(python=sys.version, platform=platform.platform(), machine=platform.machine(),
                processor=platform.processor(), cpu_count=os.cpu_count(), gpu_used=False,
                packages={dist.metadata["Name"]:dist.version for dist in importlib.metadata.distributions()
                          if dist.metadata["Name"]},
                rss_convention="process cumulative high-water RSS in bytes; Darwin byte/Linux KiB conversion")


def git_sha():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def load_inputs(config_path):
    config_path = Path(config_path).resolve()
    config = read_json(config_path)
    if config["phase_authorized"] != "preflight":
        raise ValueError("This entry point authorizes C-PREFLIGHT only")
    seedpath = Path(config["seed_manifest_path"])
    if not seedpath.is_absolute():
        seedpath = ROOT/seedpath
    seed_bytes = seedpath.read_bytes()
    if hashlib.sha256(seed_bytes).hexdigest() != config["seed_manifest_sha256"]:
        raise ValueError("Frozen seed manifest hash mismatch")
    seeds = json.loads(seed_bytes)
    if seeds["algorithm"] != SEED_VERSION or seeds["stream_names"] != list(STREAM_NAMES):
        raise ValueError("Seed algorithm version mismatch")
    cells = {raw["cell_id"]:cell_from_dict(raw) for raw in config["cells"]}
    if len(cells) != len(config["cells"]):
        raise ValueError("Duplicate cell IDs")
    for cell in cells.values():
        cell.validate()
    all_runs = seeds["runs"]
    all_ids = [entry["run_id"] for entry in all_runs]
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("Duplicate run IDs")
    stream_values = []
    for entry in all_runs:
        if (entry["cell_id"] not in cells or entry["run_id"] !=
                run_id(entry["phase"], entry["cell_id"], entry["replicate"])):
            raise ValueError("Frozen run identity mismatch")
        expected = seed_streams(seeds["master_seed"], entry["phase"], entry["cell_id"], entry["replicate"])
        if entry["streams"] != expected:
            raise ValueError("Frozen seed stream mismatch")
        stream_values.extend(entry["streams"].values())
    if len(set(stream_values)) != len(stream_values):
        raise ValueError("Duplicate allocated stream seeds")
    for cell_id in cells:
        confirmatory = [e for e in all_runs if e["cell_id"]==cell_id and e["phase"]=="confirmatory"]
        if sorted(e["replicate"] for e in confirmatory) != list(range(config["confirmatory_reps_per_cell"])):
            raise ValueError("Reserved confirmatory seed manifest mismatch")
    # Explicit selection is confined to the preregistered preflight phase.
    entries = [entry for entry in all_runs if entry["phase"] == "preflight"]
    for cell_id in cells:
        matching = [e for e in entries if e["cell_id"] == cell_id]
        if sorted(e["replicate"] for e in matching) != list(range(config["preflight_reps_per_cell"])):
            raise ValueError("Preflight replication manifest mismatch")
    if len(entries) != len(cells)*config["preflight_reps_per_cell"]:
        raise ValueError("Unexpected preflight entries")
    return config, cells, entries, hashlib.sha256(config_path.read_bytes()).hexdigest()


def checkpoint_path(output, entry):
    return Path(output)/"runs"/entry["cell_id"]/f"{entry['replicate']:04d}.json"


def event(output, name, **fields):
    entry = dict(event=name, utc=datetime.now(timezone.utc).isoformat(), **fields)
    with (Path(output)/"events.jsonl").open("a") as stream:
        stream.write(canonical(entry)+"\n")
        stream.flush()
        os.fsync(stream.fileno())


def evaluate_run(cell, entry, settings, provenance):
    started, cpu_started = time.perf_counter(), time.process_time()
    log = generate_evaluation(cell, entry["streams"], entry["run_id"])
    raw_digest = hashlib.sha256()
    for row in log.rows:
        raw_digest.update(canonical([row.unit_id, row.block_id, row.cluster_id,
                                      row.context, row.observed_exposure_s, row.reward_y]).encode()+b"\n")
    records, timings = [], []
    # Finish every method at both levels before obtaining any oracle value.
    for alpha in settings["alphas"]:
        for method in settings["methods"]:
            tick, cpu_tick = time.perf_counter(), time.process_time()
            certificates = evaluate_method(method, log, cell, alpha=alpha,
                                           threshold_per_mass=settings["constraint_per_subgroup_mass"])
            wall, cpu = time.perf_counter()-tick, time.process_time()-cpu_tick
            memory = peak_rss_bytes()
            timings.append(dict(method=method, alpha=alpha, wall_seconds=wall,
                                cpu_seconds=cpu, process_peak_rss_bytes=memory))
            for cert in certificates:
                cert.update(schema_version=SCHEMA, cell_id=cell.cell_id, run_id=entry["run_id"],
                            replicate=entry["replicate"], phase="preflight", nominal_delta=alpha,
                            seed=entry["streams"]["logging_exposure"],
                            git_sha=provenance["git_sha"], config_hash=provenance["config_hash"],
                            source_hash=provenance["source_hash"], seed_manifest_hash=settings["seed_manifest_sha256"],
                            observed_data_sha256=raw_digest.hexdigest(),
                            family_call_wall_seconds=wall, family_call_cpu_seconds=cpu,
                            process_peak_rss_bytes=memory,
                            cost_scope="per-method/level family call; repeated across candidate rows")
                records.append(cert)
    # Oracle import/use belongs solely to evaluation, outside certified inputs.
    from comet.gate_c_truth import exact_targets
    truths = exact_targets(cell)
    for record in records:
        truth = truths[record["candidate_id"]]
        estimate, lo, hi = record.get("estimate"), record.get("raw_lo"), record.get("raw_hi")
        issued = record.get("decision_issuable", False)
        record.update(true_target=truth,
                      signed_error=None if estimate is None else estimate-truth,
                      absolute_error=None if estimate is None else abs(estimate-truth),
                      raw_covered=None if lo is None or hi is None else lo <= truth <= hi,
                      covered=None if not issued else record["clipped_lo"] <= truth <= record["clipped_hi"],
                      true_violation=truth > settings["constraint_per_subgroup_mass"]*record["subgroup_mass"])
        record["false_safe"] = record["decision"] == "CERTIFIED_SAFE" and record["true_violation"]
        record["false_violation"] = record["decision"] == "CERTIFIED_VIOLATION" and not record["true_violation"]
    return dict(run_id=entry["run_id"], cell_id=cell.cell_id, phase="preflight",
                seed_streams=entry["streams"], records=records, timings=timings,
                observed_data_sha256=raw_digest.hexdigest(), raw_N=len(log.rows),
                observed_reward_min=min(r.reward_y for r in log.rows),
                observed_reward_max=max(r.reward_y for r in log.rows),
                observed_rewards_outside_0_1=sum(not 0<=r.reward_y<=1 for r in log.rows),
                wall_seconds=time.perf_counter()-started, cpu_seconds=time.process_time()-cpu_started,
                process_peak_rss_bytes=peak_rss_bytes())


def csv_write(path, rows):
    fields = sorted(set().union(*(r.keys() for r in rows))) if rows else []
    with Path(path).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k:canonical(v) if isinstance(v,(dict,list,tuple)) else v for k,v in r.items()}
                        for r in rows)


def run(config_path, output, resume=False, crash_after_completed=None):
    settings, cells, entries, config_hash = load_inputs(config_path)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    source = source_checksums()
    fingerprint = digest(dict(schema=SCHEMA, config_hash=config_hash, sources=source))
    manifest_path = output/"run_manifest.json"
    current_sha = git_sha()
    if manifest_path.exists():
        if not resume:
            raise ValueError("Existing run requires explicit --resume; no overwrite")
        manifest = read_json(manifest_path)
        if manifest["fingerprint"] != fingerprint:
            raise ValueError("Resume refused: frozen configuration/source changed")
        event(output, "RESUME_STARTED", current_git_sha=current_sha)
    else:
        if resume:
            raise ValueError("Cannot resume absent run manifest")
        manifest = dict(schema_version=SCHEMA, fingerprint=fingerprint,
                        git_sha=current_sha, config_hash=config_hash, source_hash=digest(source),
                        source_checksums=source, environment=environment(),
                        git_status_porcelain_at_start=subprocess.check_output(
                            ["git","status","--porcelain"],cwd=ROOT,text=True),
                        seed_manifest_hash=settings["seed_manifest_sha256"],
                        planned_run_ids=[entry["run_id"] for entry in entries],
                        config=settings, confirmatory_outcomes_authorized=False)
        atomic_json(manifest_path, manifest)
        event(output, "BATCH_STARTED", git_sha=current_sha, planned_logs=len(entries))
    started, cpu_started = time.perf_counter(), time.process_time()
    completed, skipped = [], []
    for entry in entries:
        path = checkpoint_path(output, entry)
        if path.exists():
            wrapper = read_json(path)
            if (wrapper["fingerprint"] != fingerprint or wrapper["run_id"] != entry["run_id"]
                    or digest(wrapper["payload"]) != wrapper["payload_sha256"]):
                raise ValueError("Completed checkpoint mismatch; refusing silent replacement")
            skipped.append(entry["run_id"])
            event(output, "RUN_SKIPPED_COMPLETED", run_id=entry["run_id"], payload_sha256=wrapper["payload_sha256"])
            continue
        event(output, "RUN_STARTED", run_id=entry["run_id"])
        try:
            payload = evaluate_run(cells[entry["cell_id"]], entry, settings, manifest)
            wrapper = dict(run_id=entry["run_id"], fingerprint=fingerprint,
                           payload_sha256=digest(payload), payload=payload)
            atomic_json(path, wrapper)
        except Exception as error:
            failure = dict(run_id=entry["run_id"], error=repr(error), traceback=traceback.format_exc())
            stamp=time.time_ns()
            atomic_json(output/"failures"/f"{entry['cell_id']}_{entry['replicate']}_{stamp}.json",failure)
            event(output,"RUN_FAILED",**failure)
            raise
        completed.append(entry["run_id"])
        event(output, "RUN_COMPLETED", run_id=entry["run_id"], payload_sha256=wrapper["payload_sha256"])
        print(f"completed {entry['run_id']}", flush=True)
        if crash_after_completed is not None and len(completed) == crash_after_completed:
            failure=dict(reason="INTENTIONAL_CHECKPOINT_RESUME_TEST", completed_run_id=entry["run_id"],
                         completed_checkpoint_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            atomic_json(output/"failures"/f"injected_crash_{time.time_ns()}.json",failure)
            event(output,"INJECTED_CRASH_AFTER_CHECKPOINT",**failure)
            raise RuntimeError("INTENTIONAL_CHECKPOINT_RESUME_TEST")
    payloads=[read_json(checkpoint_path(output,entry))["payload"] for entry in entries]
    records=[record for payload in payloads for record in payload["records"]]
    summaries=summarize_records(records, primary_comparisons=settings["primary_comparisons"])
    csv_write(output/"preflight_intervals.csv", records)
    csv_write(output/"preflight_summary.csv", summaries)
    atomic_json(output/"preflight_summary.json", summaries)
    atomic_json(output/"data_summaries.json", [{k:v for k,v in p.items() if k not in ("records","timings")}
                                              for p in payloads])
    csv_write(output/"timings.csv",[dict(run_id=p["run_id"],cell_id=p["cell_id"],**t)
                                    for p in payloads for t in p["timings"]])
    invocation=dict(new_completed_logs=len(completed), skipped_completed_logs=len(skipped),
                    total_completed_logs=len(payloads), candidate_records=len(records),
                    wall_seconds=time.perf_counter()-started, cpu_seconds=time.process_time()-cpu_started,
                    process_peak_rss_bytes=peak_rss_bytes(), current_git_sha=current_sha,
                    no_confirmatory_outcomes=True)
    atomic_json(output/"last_invocation.json", invocation)
    event(output,"BATCH_COMPLETE",**invocation)
    return summaries


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/gate_C_frozen.json")
    parser.add_argument("--output", default="results/gate_C/preflight/batch")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--crash-after-completed", type=int, default=None,
                        help="Intentional crash after an atomic checkpoint, solely for resume testing")
    args=parser.parse_args()
    run(args.config,args.output,args.resume,args.crash_after_completed)


if __name__=="__main__":
    main()

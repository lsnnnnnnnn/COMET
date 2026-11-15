"""Write an execution inventory and exact unfinished IDs, without sampling."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from contextlib import nullcontext
from experiments.relocated_sources import DEFAULT_REMOTE_PREFIX, relocated_source_checks

from comet.checkpoint_store import CheckpointStore, NAMESPACE


ROOT=Path(__file__).resolve().parents[1]
SUITES=("E1","E2","E3","E4","E5","E6","ANCHORS","negative_controls")
COMMANDS={
    "E1":".venv/bin/python -m experiments.post_cstat_fast --run-E1 --protocol results/post_cstat/E1_protocol.json --results results/post_cstat/E1",
    "E2":".venv/bin/python -m experiments.extension_runner --suite E2 --run",
    "E3":".venv/bin/python -m experiments.extension_runner --suite E3 --run",
    "E4":".venv/bin/python -m experiments.extension_runner --suite E4 --run",
    "E5":".venv/bin/python -m experiments.pipeline_fast --run-E5 --protocol results/post_cstat/E5_protocol.json --results results/post_cstat/E5",
    "E6":".venv/bin/python -m experiments.e6_runner --status --list-ids",
    "ANCHORS":".venv/bin/python -m experiments.anchor_runner --run",
    "negative_controls":".venv/bin/python -m experiments.negative_controls --run"}


def sha(path):
    path=Path(path)
    if path.is_absolute() and str(path).startswith(DEFAULT_REMOTE_PREFIX+'/'):
        path=ROOT/path.relative_to(DEFAULT_REMOTE_PREFIX)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot():
    suites={}; source_conflicts=[]; sources={}; completed=primary=remaining=0
    for name in SUITES:
        path=ROOT/f"results/post_cstat/{name}_protocol.json"
        server_path=ROOT/f"results/post_cstat/{name}_server_v2_protocol.json"
        if name in ("ANCHORS","negative_controls") and server_path.is_file():path=server_path
        if not path.is_file():
            if name=="E6":
                from experiments.e6_runner import planned_e6_ids
                ids=planned_e6_ids()
                suites[name]=dict(status="DATA_BLOCKED_NOT_FROZEN",planned=1000,completed=0,
                    remaining=1000,remaining_ids=ids,ids_status="PROPOSED_RESERVED_NOT_FROZEN_SEEDS_UNCONSUMED",
                    resume_command=COMMANDS[name],prerequisite="official archive SHA and prepared exact household splits; commit actual config then freeze before logging")
                remaining+=1000
            else:
                suites[name]=dict(status="NOT_FROZEN",completed=0,resume_command=COMMANDS[name])
            continue
        manifest=json.loads(path.read_text())
        remote=any(key.startswith(DEFAULT_REMOTE_PREFIX+'/') for key in manifest["sources"])
        with relocated_source_checks(manifest) if remote else nullcontext():
            store=CheckpointStore(ROOT/f"results/post_cstat/{name}",manifest)
        # Atomic install makes a present file a completed checkpoint; full payload
        # integrity remains the job of the streamed suite analyses, not this count.
        absent=[run_id for run_id in sorted(store.planned) if not store.path(run_id).is_file()]
        n=len(store.planned)-len(absent);completed+=n;remaining+=len(absent)
        if name.startswith("E"):primary+=n
        suites[name]=dict(status="COMPLETE_FILES_PRESENT" if not absent else "INCOMPLETE",
            protocol_fingerprint=manifest["fingerprint"],protocol_sha256=sha(path),
            planned=len(store.planned),completed=n,remaining=len(absent),remaining_ids=absent,
            resume_command=("ssh -o BatchMode=yes 10.200.13.23 'cd "+DEFAULT_REMOTE_PREFIX+" && OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -m "+("experiments.anchor_runner" if name=="ANCHORS" else "experiments.negative_controls")+" --run --protocol results/post_cstat/"+name+"_server_v2_protocol.json'" if remote else COMMANDS[name]),
            actual_protocol_path=str(path),production_location="server" if remote else "original_local_host",
            payload_verification="streamed analysis receipt; not repeated by this filename inventory")
        for source,value in manifest["sources"].items():
            if source in sources and sources[source]!=value:source_conflicts.append(source)
            sources[source]=value
    startup=json.loads((ROOT/"reports/post_cstat/startup_and_preservation.json").read_text())
    old=json.loads((ROOT/"results/gate_C/confirmatory/run_manifest.json").read_text())
    preservation={str(path):sha(ROOT/path)==value for path,value in
        dict(startup["context_file_sha256"],**old["science_sources"]).items()}
    cache_preservation={}
    for name in ("E1_operational_interrupt.json","E5_before_operational_optimization.json","E5_before_shards_snapshot.json"):
        path=ROOT/"reports/post_cstat"/name
        if path.exists():
            saved=json.loads(path.read_text()).get("completed_checkpoint_hashes",{})
            cache_preservation[name]=dict(checked=len(saved),all_unchanged=all(sha(ROOT/p)==h for p,h in saved.items()))
    artifacts=sum(p.stat().st_size for p in (ROOT/"results/post_cstat").rglob("*") if p.is_file())
    return dict(schema="COMET-execution-inventory-v2",timestamp_utc=datetime.now(timezone.utc).isoformat(),
        status="PROGRESS_SNAPSHOT_NOT_A_BACKGROUND_SERVICE",new_outcome_draws_by_inventory=0,
        E0_new_draws=0,E0_historical_logs=6000,E0_historical_records=1134000,
        completed_new_program_units=completed,completed_primary_units=primary,remaining_program_units=remaining,
        total_new_unit_cap=32000,planned_primary_units=29600,planned_supplementary_units=1700,
        possible_operational_partial_attempts_at_most=3,
        count_scope="budget units; E2 comprises300 independent paired vectors across six condition logs; E5 comprises complete three-split trials",
        suites=suites,all_current_frozen_source_hashes_match=all(sha(p)==h for p,h in sources.items()),
        frozen_source_conflicts=source_conflicts,historical_source_and_context_checks=preservation,
        all_historical_source_and_context_checks_pass=all(preservation.values()),
        completed_checkpoint_byte_preservation=cache_preservation,
        persistent_result_bytes=artifacts,persistent_result_cap_bytes=int(1.5*2**30),
        free_disk_bytes=shutil.disk_usage(ROOT).free,
        scheduler_rule="at most two scientific CPU workers; do not run all resume commands concurrently",
        background_work_running="consult live local sessions AND server tmux receipt; final handoff must report actual process state")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=ROOT/"reports/post_cstat/remaining_run_ids.json")
    args=parser.parse_args();data=snapshot();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps({k:data[k] for k in ("completed_new_program_units","remaining_program_units",
        "all_current_frozen_source_hashes_match","all_historical_source_and_context_checks_pass","persistent_result_bytes")}))


if __name__=="__main__":main()

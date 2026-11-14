"""Deterministic two-way ID filtering around the unchanged E5 fast launcher.

Each invocation remains one synchronous worker. Start shard 0/1 only after any
unsharded E5 worker has checkpointed and stopped; the coordinator enforces two
workers and the shared resource budget. This module never launches workers.
"""

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import shlex
import time

from comet.checkpoint_store import CheckpointStore,canonical_bytes,install_once
from experiments.pipeline_fast import run_pipeline_fast


def shard_ids(planned_run_ids,shard_index,shards=2):
    if shards!=2 or type(shard_index) is not int or shard_index not in (0,1):
        raise ValueError("exactly two shards with integer index 0 or 1 are required")
    ordered=sorted(planned_run_ids)
    if len(ordered)!=len(set(ordered)):raise ValueError("frozen IDs must be unique")
    return tuple(run_id for index,run_id in enumerate(ordered) if index%2==shard_index)


@contextmanager
def remaining_ids_for_shard(results_root,fingerprint,allowed_ids):
    """Filter only the exact root/fingerprint after the original integrity scan."""
    root=Path(results_root).resolve();allowed=frozenset(allowed_ids)
    original=CheckpointStore.remaining_ids
    def remaining(store):
        full=original(store)  # still loads/verifies every frozen planned ID
        if Path(store.root).resolve()!=root:return full
        if store.manifest["fingerprint"]!=fingerprint:
            raise ValueError("E5 shard root has a different scientific fingerprint")
        return [run_id for run_id in full if run_id in allowed]
    CheckpointStore.remaining_ids=remaining
    try:yield
    finally:CheckpointStore.remaining_ids=original


def run_pipeline_shard(protocol_path,results_root,*,shard_index,shards=2,**kwargs):
    protocol_path,root=Path(protocol_path),Path(results_root).resolve()
    protocol_bytes=protocol_path.read_bytes();manifest=json.loads(protocol_bytes)
    if manifest["config"].get("suite") not in ("E5","DETERMINISTIC_PIPELINE_FIXTURE"):
        raise ValueError("sharding requires an E5 protocol")
    assigned=shard_ids(manifest["config"]["planned_run_ids"],shard_index,shards)
    # The original constructor verifies the complete manifest and source hashes.
    store=CheckpointStore(root,manifest)
    invocation_id=str(time.time_ns());directory=root/"operational_invocations"
    inventory_path=directory/(invocation_id+".global-inventory.json")
    record=dict(schema="post-cstat-operational-E5-shard-v1",operational_invocation_id=invocation_id,
        operational_launcher=str(Path(__file__).resolve()),
        operational_launcher_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        protocol_file_sha256=hashlib.sha256(protocol_bytes).hexdigest(),
        unchanged_scientific_fingerprint=manifest["fingerprint"],shard_index=shard_index,shards=shards,
        shard_predicate="index in sorted(full frozen planned_run_ids) % 2 == shard_index",
        assigned_ids=list(assigned),completion_scope="SHARD_ONLY; original runner COMPLETE means assigned shard complete",
        global_inventory_file=str(inventory_path),workers_this_invocation=1,
        global_budget="unchanged original checks; coordinator limits total active workers to two",
        scientific_parameters_changed=False,legacy_new_outcome_draws=0,background_work_running=False)
    install_once(directory/(invocation_id+".shard-started.json"),canonical_bytes(record)+b"\n")
    result,error=None,None
    try:
        with remaining_ids_for_shard(root,manifest["fingerprint"],assigned):
            result=run_pipeline_fast(protocol_path,root,**kwargs)
        return dict(result,status="SHARD_"+result["status"],original_runner_status=result["status"],
            completion_scope="SHARD_ONLY",shard_index=shard_index,shards=shards,
            global_inventory_file=str(inventory_path))
    except BaseException as exc:
        error=f"{type(exc).__name__}: {exc}";raise
    finally:
        # The filter is restored before this full, integrity-checked inventory.
        remaining=store.remaining_ids();completed=sorted(store.planned-set(remaining))
        inventory=dict(schema="post-cstat-E5-global-checkpoint-inventory-v1",
            unchanged_scientific_fingerprint=manifest["fingerprint"],scope="FULL_FROZEN_E5_PROTOCOL",
            status="INCOMPLETE" if remaining else "COMPLETE",captured_time_ns=time.time_ns(),planned_units=len(store.planned),
            completed_ids=completed,remaining_ids=remaining,
            completed_checkpoint_filenames=[str(store.path(run_id).relative_to(root)) for run_id in completed],
            scientific_parameters_changed=False,legacy_new_outcome_draws=0)
        install_once(inventory_path,canonical_bytes(inventory)+b"\n")
        finished=dict(record,status="SHARD_"+result["status"] if result else "SHARD_EXITED_WITH_EXCEPTION",
            original_runner_status=result["status"] if result else None,error=error,
            original_runner_invocation_sha256=(hashlib.sha256(canonical_bytes(result)+b"\n").hexdigest()
                if result else None),
            new_completed_units=result.get("new_completed_units") if result else None,
            shard_remaining_ids=result.get("remaining_ids") if result else None,
            global_remaining_units=len(remaining),global_completed_units=len(completed),
            shard_resume_command=shlex.join([".venv/bin/python","-m","experiments.pipeline_shard","--run-E5",
                "--protocol",str(protocol_path),"--results",str(root),"--shard-index",str(shard_index),"--shards","2"]))
        install_once(directory/(invocation_id+".shard-finished.json"),canonical_bytes(finished)+b"\n")


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-E5",action="store_true",required=True)
    parser.add_argument("--protocol",type=Path,required=True)
    parser.add_argument("--results",type=Path,required=True)
    parser.add_argument("--shard-index",type=int,choices=(0,1),required=True)
    parser.add_argument("--shards",type=int,choices=(2,),default=2)
    parser.add_argument("--max-new-units",type=int)
    args=parser.parse_args(argv)
    if json.loads(args.protocol.read_text())["config"].get("suite")!="E5":
        raise ValueError("CLI requires the existing frozen E5 scientific protocol")
    print(json.dumps(run_pipeline_shard(args.protocol,args.results,shard_index=args.shard_index,
        shards=args.shards,max_new_units=args.max_new_units),indent=2,allow_nan=False))


if __name__=="__main__":main()

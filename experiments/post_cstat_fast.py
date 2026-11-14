"""Operational digest cache around the unchanged frozen synchronous E1 runner.

No score, radius, method, data, ID or scientific fingerprint is changed. The
frozen runner reads config/sources without mutation; cache keys are their exact
object identities in that invocation. Its source checks remain in place.
"""

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import time

from comet.checkpoint_store import canonical_bytes, install_once
from experiments import post_cstat_runner as runner


@contextmanager
def cached_manifest_digests():
    """Cache only the two frozen metadata objects inside _execute_one.

    This is an operational optimization for the one synchronous worker, not a
    general mutation-detecting cache or a concurrent/global cache. Other digest
    inputs use the original function. Both replaced functions are restored even
    when generation/evaluation raises or the user interrupts execution.
    """
    original_execute, original_digest = runner._execute_one, runner.digest
    memo = {}
    stats = dict(manifests=0, cached_digest_hits=0, passthrough_digest_calls=0,
                 original_metadata_digest_calls=0, executed_units=0)

    def execute(manifest, *args, **kwargs):
        config, sources = manifest["config"], manifest["sources"]
        if not memo:
            memo.update(manifest=manifest, config=config, sources=sources,
                        config_hash=original_digest(config), sources_hash=original_digest(sources))
            stats.update(manifests=1, original_metadata_digest_calls=2,
                         config_sha256=memo["config_hash"], code_sha256=memo["sources_hash"])
        elif (manifest is not memo["manifest"] or config is not memo["config"]
              or sources is not memo["sources"]):
            raise ValueError("operational digest cache requires the same frozen manifest object identities")

        def dispatch(value):
            if value is memo["config"]:
                stats["cached_digest_hits"] += 1
                return memo["config_hash"]
            if value is memo["sources"]:
                stats["cached_digest_hits"] += 1
                return memo["sources_hash"]
            stats["passthrough_digest_calls"] += 1
            return original_digest(value)

        runner.digest = dispatch
        try:
            result = original_execute(manifest, *args, **kwargs)
            stats["executed_units"] += 1
            return result
        finally:
            runner.digest = original_digest

    runner._execute_one = execute
    try:
        yield stats
    finally:
        runner.digest = original_digest
        runner._execute_one = original_execute


def run_e1_fast(protocol_path, results_root, **kwargs):
    """Resume using the unchanged runner and separate operational provenance."""
    protocol_path, root = Path(protocol_path), Path(results_root)
    protocol_bytes = protocol_path.read_bytes()
    manifest = json.loads(protocol_bytes)
    invocation_id = str(time.time_ns())
    launcher_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    record = dict(schema="post-cstat-operational-digest-cache-v1",
        operational_invocation_id=invocation_id,
        operational_launcher_sha256=launcher_sha,
        operational_launcher=str(Path(__file__).resolve()),
        protocol_file_sha256=hashlib.sha256(protocol_bytes).hexdigest(),
        unchanged_scientific_fingerprint=manifest["fingerprint"],
        cache_scope="same frozen config/sources object identities; one synchronous worker",
        source_checks="unchanged original runner startup/per-unit checks",
        scientific_parameters_changed=False, legacy_new_outcome_draws=0,
        background_work_running=False)
    directory = root / "operational_invocations"
    install_once(directory / (invocation_id + ".started.json"), canonical_bytes(record) + b"\n")
    stats, result, error = {}, None, None
    try:
        with cached_manifest_digests() as stats:
            result = runner.run_e1(protocol_path, root, **kwargs)
        return result
    except BaseException as exc:
        error = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        finished = dict(record, cache_statistics=dict(stats),
            status=result["status"] if result is not None else "EXITED_WITH_EXCEPTION",
            error=error, new_completed_units=result.get("new_completed_units") if result else None,
            remaining_ids=result.get("remaining_ids") if result else None,
            fast_resume_command=f".venv/bin/python -m experiments.post_cstat_fast --run-E1 --protocol {protocol_path} --results {root}")
        install_once(directory / (invocation_id + ".finished.json"), canonical_bytes(finished) + b"\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-E1", action="store_true", required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--max-new-units", type=int)
    args = parser.parse_args(argv)
    manifest = json.loads(args.protocol.read_text())
    if manifest["config"].get("suite") != "E1":
        raise ValueError("CLI execution requires the existing frozen E1 scientific protocol")
    print(json.dumps(run_e1_fast(args.protocol, args.results,
                                max_new_units=args.max_new_units), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()

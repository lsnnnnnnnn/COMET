"""Versioned domain-separated seeds; no outcome or oracle inputs."""
from hashlib import sha256

SEED_VERSION = "COMET-GATE-C-SHA256-128-v1"
STREAM_NAMES = (
    "design_context", "graph_shocks", "logging_exposure", "potential_outcomes",
    "nuisance_discovery_pilot", "evaluation_outcomes", "truth_mc",
)


def run_id(phase, cell_id, replicate):
    if phase not in ("preflight", "confirmatory"):
        raise ValueError("Unknown frozen phase")
    if type(replicate) is not int or replicate < 0:
        raise ValueError("Replication index must be nonnegative")
    return f"gate-c-v1/{phase}/{cell_id}/{replicate:04d}"


def seed_streams(master_seed, phase, cell_id, replicate):
    identity = run_id(phase, cell_id, replicate)
    return {name: int.from_bytes(sha256(
        f"{SEED_VERSION}|{master_seed}|{identity}|{name}".encode()).digest()[:16], "big")
        for name in STREAM_NAMES}


def build_seed_manifest(master_seed, cell_ids, preflight_reps, confirmatory_reps):
    runs = []
    for phase, count in (("preflight", preflight_reps), ("confirmatory", confirmatory_reps)):
        for cell in cell_ids:
            for replicate in range(count):
                runs.append(dict(run_id=run_id(phase, cell, replicate), phase=phase,
                                 cell_id=cell, replicate=replicate,
                                 streams=seed_streams(master_seed, phase, cell, replicate)))
    return dict(schema_version="gate-c-seeds-v1", algorithm=SEED_VERSION,
                master_seed=master_seed, stream_names=list(STREAM_NAMES), runs=runs)

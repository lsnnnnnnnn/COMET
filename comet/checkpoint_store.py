"""Immutable, resumable checkpoints for NEW post-C-STAT units only.

This module never imports or invokes the historical runner. A completed unit
is loaded and integrity-checked before its generator can be called again.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


NAMESPACE = "comet-post-cstat-v1"
REQUIRED_INPUTS = ("POST_CSTAT_OVERRIDE.md", "CODEX_MASTER_GOAL.md", "SCOPE_CN.md",
                   "THEORY_NOTE.md", "EXPERIMENT_BLUEPRINT.json", "CLAIM_EVIDENCE.csv")


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_hashes(paths):
    return {str(p): hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}


def planning_input_hashes(directory, *, allowed_missing=()):
    base = Path(directory)
    allowed = set(allowed_missing)
    if not allowed <= set(REQUIRED_INPUTS):
        raise ValueError("unknown planning input exemption")
    missing = [name for name in REQUIRED_INPUTS if not (base / name).is_file() and name not in allowed]
    if missing:
        raise FileNotFoundError("Specified planning inputs not yet reconciled: " + ", ".join(missing))
    result = {name: hashlib.sha256((base / name).read_bytes()).hexdigest()
              for name in REQUIRED_INPUTS if (base / name).is_file()}
    if allowed:
        receipt = base / "INPUT_RESOLUTION.md"
        if not receipt.is_file():
            raise FileNotFoundError("explicit user input-resolution receipt required")
        result["INPUT_RESOLUTION.md"] = hashlib.sha256(receipt.read_bytes()).hexdigest()
        result["explicitly_waived_missing_inputs"] = sorted(
            name for name in allowed if not (base / name).is_file())
    return result


def install_once(path, content):
    """Atomic create; an existing scientific artifact is never overwritten."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(tmp_name, path)
    finally:
        Path(tmp_name).unlink(missing_ok=True)


def freeze_protocol(path, config, source_paths, input_directory):
    """Create a new protocol only after all specified planning inputs exist.

    This does not assert that a theorem is proved: config must identify the
    actual reviewed theorem and method applicability. No outcomes are drawn.
    """
    if config.get("namespace") != NAMESPACE:
        raise ValueError("new namespace required; E0 is closed")
    if config.get("legacy_new_outcome_draws") != 0:
        raise ValueError("E0 additional outcome draws must equal zero")
    if not 0 <= config.get("primary_units", -1) <= 29600:
        raise ValueError("primary unit cap exceeded")
    if not 0 <= config.get("total_unit_cap", -1) <= 32000:
        raise ValueError("total unit cap exceeded")
    if not 1 <= config.get("workers", 0) <= 2:
        raise ValueError("worker limit exceeded")
    ids = tuple(config.get("planned_run_ids", ()))
    if len(ids) > config["total_unit_cap"] or len(set(ids)) != len(ids):
        raise ValueError("invalid planned IDs")
    for run_id in ids:
        validate_run_id(run_id)
    manifest = dict(schema="post-cstat-protocol-v1", config=config,
                    sources=file_hashes(source_paths),
                    planning_inputs=planning_input_hashes(input_directory,
                        allowed_missing=config.get("allowed_missing_planning_inputs", ())))
    manifest["fingerprint"] = digest(manifest)
    install_once(path, canonical_bytes(manifest) + b"\n")
    return manifest


def validate_run_id(run_id):
    if not isinstance(run_id, str) or not re.fullmatch(
            NAMESPACE + r"/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+/[0-9]{4,6}", run_id):
        raise ValueError("invalid new-workstream run ID")


class CheckpointStore:
    def __init__(self, root, manifest, *, check_sources=True):
        self.root = Path(root)
        self.manifest = manifest
        body = {k: v for k, v in manifest.items() if k != "fingerprint"}
        if digest(body) != manifest["fingerprint"]:
            raise ValueError("corrupt protocol fingerprint")
        config = manifest["config"]
        if config["namespace"] != NAMESPACE or config["legacy_new_outcome_draws"] != 0:
            raise ValueError("historical units cannot enter the new store")
        self.planned = frozenset(config["planned_run_ids"])
        for run_id in self.planned:
            validate_run_id(run_id)
        if check_sources and file_hashes(manifest["sources"]) != manifest["sources"]:
            raise ValueError("scientific source changed after freeze")

    def path(self, run_id):
        validate_run_id(run_id)
        if run_id not in self.planned:
            raise ValueError("run ID not in the frozen protocol")
        return self.root / "checkpoints" / (run_id.removeprefix(NAMESPACE + "/") + ".json.gz")

    def load(self, run_id):
        path = self.path(run_id)
        if not path.exists():
            return None
        record = json.loads(gzip.decompress(path.read_bytes()))
        payload = record["payload"]
        if record["payload_sha256"] != digest(payload):
            raise ValueError("corrupt checkpoint scientific payload: " + run_id)
        if payload["run_id"] != run_id or payload["fingerprint"] != self.manifest["fingerprint"]:
            raise ValueError("checkpoint input mismatch: " + run_id)
        return payload

    def complete(self, run_id, result):
        if self.load(run_id) is not None:
            raise FileExistsError("completed unit is immutable: " + run_id)
        payload = dict(run_id=run_id, fingerprint=self.manifest["fingerprint"], result=result)
        record = dict(payload=payload, payload_sha256=digest(payload))
        install_once(self.path(run_id), gzip.compress(canonical_bytes(record), mtime=0))
        return payload

    def resume_one(self, run_id, generate):
        existing = self.load(run_id)
        if existing is not None:
            return existing, False
        result = generate(run_id)
        return self.complete(run_id, result), True

    def remaining_ids(self):
        return [run_id for run_id in sorted(self.planned) if self.load(run_id) is None]

    def iter_completed(self):
        """Stream one complete independent trial at a time, never pooled rows."""
        for run_id in sorted(self.planned):
            payload = self.load(run_id)
            if payload is not None:
                yield payload

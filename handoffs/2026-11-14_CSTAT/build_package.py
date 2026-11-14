"""Build the reading handoff from the pinned completed delivery, without draws."""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = "ca5bb878cf9635fac4381d03281df0bc8a900daa"
NAME = "COMET_NEXT_CHAT_20261114.zip"
SKIP_PREFIXES = (
    "results/gate_C/confirmatory/run_checkpoints/",
    "results/gate_C/confirmatory/raw_shards/",
    "results/gate_C/confirmatory/aggregation_spool/",
)
SKIP_FILES = {"results/gate_C/confirmatory/.execution.lock"}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    tree = subprocess.check_output(
        ["git", "ls-tree", "-r", "-z", BASE], cwd=ROOT
    )
    included, omitted, payloads = [], [], []
    for record in tree.split(b"\0"):
        if not record:
            continue
        metadata, raw_name = record.split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        name = raw_name.decode()
        assert kind == "blob" and mode in ("100644", "100755"), name
        if name.startswith(SKIP_PREFIXES) or name in SKIP_FILES:
            omitted.append({"path": name, "git_blob_sha1": oid})
            continue
        data = (ROOT / name).read_bytes()
        actual_blob = hashlib.sha1(
            b"blob " + str(len(data)).encode() + b"\0" + data
        ).hexdigest()
        assert actual_blob == oid, f"Working file differs from pinned baseline: {name}"
        archive_name = "repo/" + name
        included.append({"archive_path": archive_name, "source_path": name,
                         "bytes": len(data), "sha256": sha256(data),
                         "git_blob_sha1": oid})
        payloads.append((archive_name, data))
    handoff = []
    for name in ("README_HANDOFF.md", "NEXT_CHAT_PROMPT.md", "build_package.py"):
        data = (HERE / name).read_bytes()
        handoff.append({"archive_path": name, "bytes": len(data),
                        "sha256": sha256(data)})
        payloads.append((name, data))
    manifest = {
        "kind": "COMET_NEXT_CHAT_READING_HANDOFF",
        "date": "2026-11-14",
        "timezone": "Asia/Shanghai",
        "baseline_commit": BASE,
        "branch": "codex/gate-c-stat",
        "result_commit": "dd59ec61a08b72cf241e87bcf575f9ce5ae585a7",
        "repo_url": "https://github.com/lsnnnnnnnn/COMET",
        "local_repo": str(ROOT),
        "complete_raw_confirmation_included": False,
        "repository_files_included": len(included),
        "repository_files_omitted": len(omitted),
        "omission_reason": "Compact reading handoff. Complete immutable outcomes remain in the pinned Git repository; no outcomes were deleted or regenerated.",
        "new_experiments_authorized": False,
        "included_files": included,
        "handoff_files": handoff,
        "omitted_files": omitted,
        "manifest_self_hash": "Excluded to avoid self-reference; ZIP digest is in the external .sha256 file.",
    }
    manifest_data = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
    (HERE / "PACKAGE_MANIFEST.json").write_bytes(manifest_data)
    payloads.append(("PACKAGE_MANIFEST.json", manifest_data))
    output = HERE / NAME
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6) as archive:
        for name, data in sorted(payloads):
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 14, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == {name for name, _ in payloads}
        for item in included + handoff:
            assert sha256(archive.read(item["archive_path"])) == item["sha256"]
    digest = sha256(output.read_bytes())
    (HERE / (NAME + ".sha256")).write_text(f"{digest}  {NAME}\n")
    print(json.dumps({"status": "PASS", "baseline_commit": BASE,
                      "repository_files_included": len(included),
                      "repository_files_omitted": len(omitted),
                      "archive_entries": len(payloads), "zip_bytes": output.stat().st_size,
                      "zip_sha256": digest, "new_outcomes": 0}, indent=2))


if __name__ == "__main__":
    main()

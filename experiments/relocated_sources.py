"""Offline source-path relocation checks for unchanged remote protocol bytes.

This maps only source file reads, retaining the protocol's original absolute
keys, hashes and fingerprint. It does not adapt execution environments, draws,
source-stat calls or estimator behavior. Server ANCHORS analysis stays on the
server because its frozen validator requires the actual execution environment.
"""

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path,PurePosixPath
import re

from comet import checkpoint_store


DEFAULT_REMOTE_PREFIX="/data1/shengen/COMET_POST_CSTAT_20261115"
REPOSITORY=Path(__file__).resolve().parents[1]


def _remote_path(value):
    if (not isinstance(value,str) or "\\" in value or not value.startswith("/")
            or any(part in (".","..") for part in value.split("/"))
            or str(PurePosixPath(value))!=value):
        raise ValueError("a canonical absolute POSIX source path without traversal is required")
    return PurePosixPath(value)


@contextmanager
def relocated_source_checks(manifest,*,remote_prefix=DEFAULT_REMOTE_PREFIX,local_prefix=REPOSITORY):
    """Verify every declared remote source locally, then retain original keys.

    Only checkpoint_store.file_hashes is temporarily wrapped. Its normal source
    checks remain enabled. Unknown remote files are refused; unrelated local
    calls pass through the original function. The manifest is never changed.
    """
    remote=_remote_path(str(remote_prefix));local=Path(local_prefix).resolve(strict=True)
    if not local.is_dir():raise ValueError("local source prefix must be a directory")
    sources=manifest.get("sources")
    if not isinstance(sources,dict) or not sources:raise ValueError("a nonempty frozen source map is required")
    body={key:value for key,value in manifest.items() if key!="fingerprint"}
    if checkpoint_store.digest(body)!=manifest.get("fingerprint"):
        raise ValueError("corrupt protocol fingerprint")
    original=checkpoint_store.file_hashes
    mapping={};rows=[]
    for source,expected in sorted(sources.items()):
        path=_remote_path(source)
        try:relative=path.relative_to(remote)
        except ValueError as exc:raise ValueError("source is outside the declared remote prefix: "+source) from exc
        if not isinstance(expected,str) or re.fullmatch(r"[0-9a-f]{64}",expected) is None:
            raise ValueError("invalid frozen source SHA-256")
        resolved=local.joinpath(*relative.parts).resolve(strict=True)
        if not resolved.is_relative_to(local) or not resolved.is_file():
            raise ValueError("source mapping escapes the local repository or is not a file")
        actual=original([resolved])[str(resolved)]
        if actual!=expected:raise ValueError("relocated scientific source differs: "+source)
        mapping[source]=resolved
        rows.append(dict(remote_path=source,local_path=str(resolved),sha256=actual))

    def checked_hashes(paths):
        result={}
        for path in paths:
            key=str(path)
            if key in mapping:
                actual=original([mapping[key]])[str(mapping[key])]
                if actual!=sources[key]:raise ValueError("relocated scientific source changed: "+key)
                result[key]=actual
            else:
                if key==str(remote) or key.startswith(str(remote)+"/"):
                    _remote_path(key)
                    raise ValueError("remote source is absent from the frozen source map: "+key)
                try:under_remote=_remote_path(key).is_relative_to(remote)
                except ValueError:under_remote=False
                if under_remote:raise ValueError("remote source is absent from the frozen source map: "+key)
                result.update(original([path]))
        return result

    receipt=dict(schema="post-cstat-offline-source-relocation-v1",
        unchanged_scientific_fingerprint=manifest["fingerprint"],remote_prefix=str(remote),local_prefix=str(local),
        source_mapping=rows,source_count=len(rows),check_sources_skipped=False,
        manifest_config_or_fingerprint_modified=False,analysis_new_outcome_draws=0,
        execution_environment_adapted=False)
    checkpoint_store.file_hashes=checked_hashes
    try:yield receipt
    finally:checkpoint_store.file_hashes=original


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol",type=Path,required=True)
    parser.add_argument("--remote-prefix",default=DEFAULT_REMOTE_PREFIX)
    parser.add_argument("--local-prefix",type=Path,default=REPOSITORY)
    parser.add_argument("--receipt",type=Path,required=True)
    parser.add_argument("--analyze-negative",action="store_true")
    parser.add_argument("--results",type=Path)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args(argv)
    if args.analyze_negative and (args.results is None or args.output is None):
        parser.error("--analyze-negative requires --results and a fresh --output directory")
    if args.receipt.exists():raise FileExistsError("immutable relocation receipt already exists")
    protocol_bytes=args.protocol.read_bytes();manifest=json.loads(protocol_bytes)
    if args.analyze_negative and manifest["config"].get("suite")!="negative_controls":
        raise ValueError("offline analysis CLI supports negative_controls only; run ANCHORS analysis on its declared server environment")
    with relocated_source_checks(manifest,remote_prefix=args.remote_prefix,local_prefix=args.local_prefix) as receipt:
        if args.analyze_negative:
            from experiments.negative_controls import analyze_negative_controls
            summary=analyze_negative_controls(args.protocol,args.results,args.output)
            receipt.update(action="original_negative_control_analysis",analysis_status=summary["status"],
                analysis_manifest=str(args.output/"manifest.json"),
                analysis_manifest_sha256=hashlib.sha256((args.output/"manifest.json").read_bytes()).hexdigest())
        else:receipt["action"]="offline_source_verification_only"
    if args.protocol.read_bytes()!=protocol_bytes:raise ValueError("protocol file changed during offline verification")
    from experiments.post_cstat_runner import environment_signature
    receipt.update(protocol_file_sha256=hashlib.sha256(protocol_bytes).hexdigest(),
        relocation_tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        actual_offline_environment=environment_signature(),status="COMPLETE")
    checkpoint_store.install_once(args.receipt,checkpoint_store.canonical_bytes(receipt)+b"\n")
    print(json.dumps({key:receipt[key] for key in ("status","action","source_count","unchanged_scientific_fingerprint")},indent=2))


if __name__=="__main__":main()

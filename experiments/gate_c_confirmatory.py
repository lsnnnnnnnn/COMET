"""C-STAT launcher: unmodified frozen science, separately authorized phase.

No confirmatory outcomes are generated without explicit --confirmatory. The
compatibility mode uses only the twelve already drawn preflight seeds.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
import csv
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import time
import traceback

from experiments import gate_c_preflight as frozen
from comet.gate_c_statistics import summarize_records, holm_adjust

ROOT = Path(__file__).resolve().parents[1]
SCIENCE_FREEZE = "ab4c74fbf1ae84c0e5ffd72d77ce5b48d3fba8cb"
EVIDENCE_COMMIT = "06a39b89e579aef57d14ae51e86d74ecf9b6b768"
SCHEMA = "gate-c-confirmatory-record-v1"
CONFIG_SHA256 = "b834e7b409bb008ba0d2b6e591515873831f87d036fdc53ed0392d0b94012ff4"
SEED_SHA256 = "9d04a99066a7c8c0234f226f4dddfa33e9c0171fdb6f3486c30452389c667eab"
SCIENCE_SOURCES = {'comet/__init__.py': 'f98b3783ffe62b437d6b78f8884bc0549eb2dd69623899b90d273c439db6ef6f', 'comet/bounded_variance.py': '664679cff996764a8f6ede378c7e17da9d89e8db18e87deb0a8fce2ab29c0898', 'comet/certification.py': '06daf4d4f745de7a076358e4e11ae9a258aa7532b5e01ac15aa2466fe46448f5', 'comet/conflict_graph.py': 'a25e354954357793dea8b75b1350e983a97a18a82af00a4948d05b1365d1cb3d', 'comet/dr_scores.py': '6d0704b4b908543fea3b6956b6cd60c1381ec879d261f9392fe7aba7879b3a5a', 'comet/exposure.py': '7c273f08c67d5d5255a156079e7f7e42436300d9439a2813324d9971e886fa0c', 'comet/gate_c_contract.py': 'a27107cfdbf7c6587451d4ec092575a33b0baecca60a815b6ee14858fae96b9e', 'comet/gate_c_methods.py': 'b100c3f7dc1f7c1a3a28d98927bd4d73b3f996690c3f9ae41ec090bc5e4ae9e2', 'comet/gate_c_seeds.py': 'b168612af82b9c5007323bef5d4900054d4e195b9c71740dffde6fae6477e3bd', 'comet/gate_c_simulation.py': '60c7d2bf5b3dfd68974784306f48d846858257cc75aff5ee0c30c817203cb1c8', 'comet/gate_c_statistics.py': 'd93057c75410e96657ebfce9b5e266252f73f78c46e7277a3218803e3cffa386', 'comet/gate_c_truth.py': 'b9687f49ebb76cdccc3d735581dfaa68d1611e344f50fc561d12ed5dd6312d54', 'comet/informativeness.py': '5ce983ee47f33dca0408d4fea8170bfa8d1dc6e8402f6a274c528f9abc50f87e', 'comet/metrics.py': 'c669acdae63f4c358d92d2a70bb6d0c4c320c355c8fa860ccfe0243b85a7fdae', 'comet/robust_mean.py': '2094a96ebe2c1ae5c3e2c97ec8bd1bf0eb5c627ebb9d000940f5dc374078b4a4', 'comet/schema.py': '89a4b3eaebb90c3af91f7d7338f9b616795d0f47d0520fe93a5ab61a4e468c8a', 'comet/smoke.py': '52e73e650ee40401e6f2ca151389a4e897d82c3ca4479fc555b615470560578f', 'comet/synthetic.py': 'd98dbb4c5f50c254f814c60d194e6116ca34d398b2d0aef07437545a8feb3a53', 'comet/truth.py': '32ef47d780df447f00dc60403950c0ddb01c4c601449c74fcc9b5d9b35557db5', 'experiments/__init__.py': '5028dedb5d2c6ae820b137fe6e8d3a5d10cdeb4c965388f208dda0d70ed2550a', 'experiments/forensic_c0.py': 'd72f437d92f53b65fa880d8702c5ba7fcce1f5a7b5f39cf0ecdff20924c10a64', 'experiments/gate_c0_pilot.py': '8f5b64ee65590750aadf1c4488be6a80fc2642db6899565666a3cce51bb5bd95', 'experiments/gate_c_design_audit.py': '406af00d2bf58e46f1c0c6b711b27c9d8ae42e115826f4895f7aa4947acb1b51', 'experiments/gate_c_preflight.py': '0b725704b11e788d59426c401a4c196296582b613380abd96d6054c3b4dad4f0', 'experiments/nonvacuity_budget.py': 'a1c217b92d52c79ff460a124b1f5393711d0d4b9d60159a5764a89946fdd5f88', 'experiments/reconcile_gate_c_baseline.py': 'a7d772802045f833156c8eb0103739c7a95d1b81cfc6717600738177f23d4923'}

canonical, digest, read_json, atomic_json = (frozen.canonical, frozen.digest,
                                          frozen.read_json, frozen.atomic_json)
# Only execution metadata is excluded in bytewise compatibility. Everything
# concerning observations, oracle, estimators, intervals and statuses remains.
RECORD_EXECUTION_FIELDS = frozenset((
    'schema_version', 'phase', 'git_sha', 'source_hash',
    'family_call_wall_seconds', 'family_call_cpu_seconds', 'process_peak_rss_bytes'))
PAYLOAD_EXECUTION_FIELDS = frozenset((
    'phase', 'timings', 'wall_seconds', 'cpu_seconds', 'process_peak_rss_bytes'))
SUMMARY_FIELDS = frozenset((
    'cell_id','nominal_delta','method','run_id','candidate_id','family_size',
    'certificate_applicable','decision_issuable','covered','status','raw_covered',
    'width_fraction','raw_radius','absolute_error','signed_error','decision',
    'true_violation','false_safe','false_violation','is_nontrivial','raw_N','N_eff',
    'chi_max','B','n0','K','L_min','L_max','p_declared'))


def scientific_payload(payload):
    result = {k:v for k,v in payload.items() if k not in PAYLOAD_EXECUTION_FIELDS}
    result['records'] = [{k:v for k,v in row.items() if k not in RECORD_EXECUTION_FIELDS}
                         for row in payload['records']]
    return result


def check_scientific_lock(root=ROOT):
    root = Path(root)
    actual = {name:hashlib.sha256((root/name).read_bytes()).hexdigest()
              for name in SCIENCE_SOURCES}
    changed = [name for name in SCIENCE_SOURCES if actual[name] != SCIENCE_SOURCES[name]]
    if changed:
        raise ValueError('BLOCKED: frozen science hash mismatch: '+', '.join(changed))
    for name, expected in (('configs/gate_C_frozen.json',CONFIG_SHA256),
                           ('configs/gate_C_seed_manifest.json',SEED_SHA256)):
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != expected:
            raise ValueError('BLOCKED: frozen input hash mismatch: '+name)
    return dict(science_freeze_git_sha=SCIENCE_FREEZE, science_sources=actual,
                source_hash=digest(actual), config_hash=CONFIG_SHA256,
                seed_manifest_hash=SEED_SHA256,
                runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


def load_frozen_inputs():
    lock = check_scientific_lock()
    # This unchanged validator verifies the old phase and every allocated stream.
    settings,cells,preflight,config_hash = frozen.load_inputs(ROOT/'configs/gate_C_frozen.json')
    seed_manifest = read_json(ROOT/'configs/gate_C_seed_manifest.json')
    entries = [entry for entry in seed_manifest['runs'] if entry['phase']=='confirmatory']
    if (len(entries)!=6000 or Counter(e['cell_id'] for e in entries)!=dict.fromkeys('ABCDEF',1000)
            or len(preflight)!=12 or config_hash!=CONFIG_SHA256):
        raise ValueError('BLOCKED: registered phase/denominator mismatch')
    if settings['alphas'] != [.05,.1] or len(settings['methods'])!=7 or len(settings['primary_comparisons'])!=17:
        raise ValueError('BLOCKED: confidence/method family mismatch')
    # Dataclass validation checks known support, p range, fixed nuisance, cliques
    # and frozen stable targets. Its original source is included in the lock.
    for cell in cells.values():
        cell.validate()
    return settings,cells,entries,preflight,lock


def evaluate_frozen(cell, entry, settings, provenance, phase):
    """Reuse scientific routine verbatim, changing execution labels only."""
    if entry['phase']!=phase or phase not in ('preflight','confirmatory'):
        raise ValueError('entry phase mismatch')
    result = frozen.evaluate_run(cell,entry,settings,provenance)
    result['phase'] = phase
    for row in result['records']:
        row['phase'] = phase
        row['schema_version'] = SCHEMA
    return result


def checkpoint_path(output,entry):
    return Path(output)/'run_checkpoints'/entry['cell_id']/f"{entry['replicate']:04d}.json.gz"


def atomic_gzip_json(path,value):
    path = Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    with temporary.open('wb') as raw:
        with gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as stream:
            stream.write(canonical(value).encode()+b'\n')
        raw.flush(); os.fsync(raw.fileno())
    temporary.replace(path)


def load_checkpoint(path,entry,fingerprint):
    with gzip.open(path,'rt') as stream:
        wrapper=json.load(stream)
    if (wrapper['fingerprint']!=fingerprint or wrapper['run_id']!=entry['run_id']
            or wrapper['input_sha256']!=digest(entry)
            or wrapper['payload_sha256']!=digest(wrapper['payload'])):
        raise ValueError('Completed checkpoint mismatch; refusing replacement: '+str(path))
    payload=wrapper['payload']
    if payload['run_id']!=entry['run_id'] or payload['phase']!=entry['phase']:
        raise ValueError('Checkpoint payload identity mismatch')
    return wrapper


def append_event(output,name,**fields):
    frozen.event(output,name,**fields)


def validate_payload(payload,entry,settings):
    """No applicable primary family may silently turn into an NA denominator."""
    cell_raw=next(c for c in settings['cells'] if c['cell_id']==entry['cell_id'])
    expected_ids={c.candidate_id for c in frozen.cell_from_dict(cell_raw).design.family}
    expected_size=len(expected_ids)
    groups=defaultdict(list)
    for row in payload['records']:
        if row['run_id']!=entry['run_id'] or row['cell_id']!=entry['cell_id'] or row['phase']!=entry['phase']:
            raise ValueError('BLOCKED: scientific row identity mismatch')
        groups[(row['method'],row['nominal_delta'])].append(row)
        if row['method'] in ('ips','dm','dr'):
            expected_status,applicable='POINT_ONLY',False
        elif entry['cell_id']=='F' and row['method']=='bounded_graph_chebyshev':
            expected_status,applicable='NOT_APPLICABLE',False
        else:
            expected_status,applicable='CERTIFIED',True
        if row['status']!=expected_status or row['certificate_applicable']!=applicable:
            raise ValueError('BLOCKED: unexpected theorem status/applicability; payload retained')
    expected_groups={(method,alpha) for method in settings['methods'] for alpha in settings['alphas']}
    if set(groups)!=expected_groups:
        raise ValueError('BLOCKED: missing/extra method-level family')
    for rows in groups.values():
        if (len(rows)!=expected_size or {r['candidate_id'] for r in rows}!=expected_ids
                or any(r['family_size']!=expected_size for r in rows)):
            raise ValueError('BLOCKED: changed or incomplete candidate family')


def _worker(job):
    cell,entry,settings,manifest,output = job
    try:
        payload=evaluate_frozen(cell,entry,settings,manifest,'confirmatory')
        wrapper=dict(schema_version=SCHEMA,run_id=entry['run_id'],fingerprint=manifest['fingerprint'],
                     input_sha256=digest(entry),payload_sha256=digest(payload),payload=payload)
        path=checkpoint_path(output,entry)
        if path.exists():
            raise ValueError('Worker refuses to replace existing checkpoint')
        atomic_gzip_json(path,wrapper)
        validate_payload(payload,entry,settings)
        return dict(run_id=entry['run_id'],payload_sha256=wrapper['payload_sha256'],
                    wall_seconds=payload['wall_seconds'],cpu_seconds=payload['cpu_seconds'],
                    process_peak_rss_bytes=payload['process_peak_rss_bytes'])
    except BaseException as error:
        failure=dict(kind='ACTUAL_EXECUTION_ERROR',run_id=entry['run_id'],
                     error=repr(error),traceback=traceback.format_exc(),utc=datetime.now(timezone.utc).isoformat())
        atomic_json(Path(output)/'failures'/f"{entry['cell_id']}_{entry['replicate']}_{time.time_ns()}.json",failure)
        raise


def _csv_row(row):
    return {k:canonical(v) if isinstance(v,(dict,list,tuple)) else v for k,v in row.items()}


def aggregate(output,entries,manifest,settings,phase='confirmatory'):
    """Stream complete logs; freeze statistics operate on at most 16k rows.

    Scientific statistics are computed by the original summarizer. Temporary
    summary projections keep all of its input fields; complete raw rows are in
    immutable compressed checkpoints and per-cell compressed CSV shards.
    """
    output=Path(output); shards=output/'raw_shards'; shards.mkdir(exist_ok=True)
    spool=output/'aggregation_spool'; spool.mkdir(exist_ok=True)
    group_paths={}; handles={}; summaries=[]; data=[]; timing_rows=[]
    counts=Counter(); checkpoint_index=[]
    try:
        for cell_id in sorted({e['cell_id'] for e in entries}):
            path=shards/f'{cell_id}.csv.gz'
            with gzip.open(path,'wt',newline='') as raw:
                writer=None
                for entry in (e for e in entries if e['cell_id']==cell_id):
                    checkpoint=checkpoint_path(output,entry)
                    wrapper=load_checkpoint(checkpoint,entry,manifest['fingerprint'])
                    payload=wrapper['payload']
                    validate_payload(payload,entry,settings)
                    checkpoint_index.append(dict(run_id=entry['run_id'],cell_id=cell_id,
                        path=str(checkpoint.relative_to(output)),input_sha256=wrapper['input_sha256'],
                        payload_sha256=wrapper['payload_sha256'],
                        file_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest()))
                    if writer is None:
                        fields=sorted(set().union(*(r.keys() for r in payload['records'])))
                        writer=csv.DictWriter(raw,fieldnames=fields); writer.writeheader()
                    for row in payload['records']:
                        writer.writerow(_csv_row(row));counts[cell_id]+=1
                        key=(cell_id,row['nominal_delta'],row['method'])
                        if key not in handles:
                            target=spool/f'{cell_id}_{row["nominal_delta"]}_{row["method"]}.jsonl'
                            group_paths[key]=target;handles[key]=target.open('w')
                        handles[key].write(canonical({k:v for k,v in row.items() if k in SUMMARY_FIELDS})+'\n')
                    data.append({k:v for k,v in payload.items() if k not in ('records','timings')})
                    timing_rows.extend(dict(run_id=entry['run_id'],cell_id=cell_id,**r) for r in payload['timings'])
    finally:
        for stream in handles.values(): stream.close()
    for key,path in sorted(group_paths.items()):
        with path.open() as stream: rows=[json.loads(line) for line in stream]
        summaries.extend(summarize_records(rows,phase=phase,primary_comparisons=settings['primary_comparisons']))
    primary={(r['cell_id'],r['method']):r for r in summaries if r['alpha']==.05}
    keys=[(r['cell_id'],r['method']) for r in settings['primary_comparisons']]
    adjusted=holm_adjust({key:primary.get(key,{}).get('undercoverage_pvalue') for key in keys})
    for key,pvalue in adjusted.items():
        if key in primary:
            primary[key]['undercoverage_holm_pvalue']=pvalue
            primary[key]['holm_declared_comparisons']=len(keys)
    summaries.sort(key=lambda r:(r['cell_id'],r['alpha'],r['method']))
    atomic_json(output/'summary.json',summaries);frozen.csv_write(output/'summary.csv',summaries)
    frozen.csv_write(output/'timings.csv',timing_rows)
    atomic_json(output/'data_summaries.json',data)
    atomic_json(output/'checkpoint_index.json',checkpoint_index)
    inventory=dict(completed_logs=len(entries),candidate_records=sum(counts.values()),
                   records_by_cell=dict(counts),summary_rows=len(summaries),
                   planned_logs=len(manifest['planned_run_ids']),
                   phase=phase,all_planned_ids_complete=set(e['run_id'] for e in entries)==set(manifest['planned_run_ids']))
    atomic_json(output/'aggregation_inventory.json',inventory)
    # Intermediate spools are derived projections, not outcomes/checkpoints.
    # Keep them compressed for independent audit; never modify raw checkpoints.
    for path in group_paths.values():
        with path.open('rb') as source,gzip.open(path.with_suffix('.jsonl.gz'),'wb') as target:
            while block:=source.read(1024*1024): target.write(block)
        path.unlink()
    lines=['# Frozen C-STAT summary','',
           'Each row uses independent whole-log families. Wilson intervals are descriptive; nonrejection does not prove validity.','',
           '|Cell|Method|Level|Covered/allocated|Wilson 95%|Median width/diameter|Nontrivial candidates|No certified decision|Holm p (95%)|',
           '|---|---|---:|---:|---|---:|---:|---:|---:|']
    def fmt(x): return 'NA' if x is None else f'{x:.6g}'
    for r in summaries:
        lines.append('|'+ '|'.join((r['cell_id'],r['method'],fmt(r['nominal_level']),
            f"{r['covered_families']}/{r['replications']}",f"[{fmt(r['wilson_lo'])}, {fmt(r['wilson_hi'])}]",
            fmt(r['median_width_fraction']),fmt(r['marginal_nontrivial_fraction']),
            fmt(r['no_certified_decision_fraction']),fmt(r['undercoverage_holm_pvalue'])))+'|')
    (output/'summary.md').write_text('\n'.join(lines)+'\n')
    return inventory,summaries


def compatibility(output):
    """Twelve historical seeds only. Never selects a confirmatory outcome."""
    settings,cells,_,entries,lock=load_frozen_inputs()
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    provenance=dict(lock,git_sha=frozen.git_sha())
    fingerprint=digest(dict(lock=lock,phase='preflight_compatibility'))
    manifest=dict(provenance,fingerprint=fingerprint,planned_run_ids=[e['run_id'] for e in entries])
    checks=[];all_records=[]
    for entry in entries:
        expected=frozen.read_json(frozen.checkpoint_path(ROOT/'results/gate_C/preflight/batch',entry))['payload']
        actual=evaluate_frozen(cells[entry['cell_id']],entry,settings,provenance,'preflight')
        left,right=canonical(scientific_payload(expected)),canonical(scientific_payload(actual))
        match=left==right
        check=dict(run_id=entry['run_id'],identical=match,expected_sha256=hashlib.sha256(left.encode()).hexdigest(),
                   actual_sha256=hashlib.sha256(right.encode()).hexdigest())
        checks.append(check)
        atomic_json(output/'compatibility_checks.json',checks)
        if not match:
            atomic_json(output/'mismatch.json',dict(run_id=entry['run_id'],expected=scientific_payload(expected),actual=scientific_payload(actual)))
            raise ValueError('BLOCKED: bytewise scientific compatibility failed: '+entry['run_id'])
        all_records.extend(actual['records'])
        atomic_gzip_json(checkpoint_path(output,entry),dict(run_id=entry['run_id'],fingerprint=fingerprint,
            input_sha256=digest(entry),payload_sha256=digest(actual),payload=actual))
        print('compatible '+entry['run_id'],flush=True)
    expected_summary=summarize_records(all_records,phase='preflight',primary_comparisons=settings['primary_comparisons'])
    inventory,actual_summary=aggregate(output,entries,manifest,settings,phase='preflight')
    if canonical(expected_summary)!=canonical(actual_summary):
        raise ValueError('BLOCKED: partitioned aggregation differs from original summarizer')
    historic=frozen.read_json(ROOT/'results/gate_C/preflight/batch/preflight_summary.json')
    if canonical(historic)!=canonical(actual_summary):
        raise ValueError('BLOCKED: regenerated summary differs from historical preflight')
    result=dict(status='PASS',phase='preflight_compatibility',confirmatory_draws=0,
                science_lock=lock,environment=frozen.environment(),checks=checks,
                partitioned_summary_bytewise_equal=True,historical_summary_bytewise_equal=True,
                inventory=inventory,execution_fields_excluded=dict(record=sorted(RECORD_EXECUTION_FIELDS),payload=sorted(PAYLOAD_EXECUTION_FIELDS)))
    atomic_json(output/'compatibility_result.json',result)
    return result


def run(output,confirmatory=False,resume=False,workers=1,compatibility_report=None,aggregate_only=False):
    if not confirmatory:
        raise ValueError('Explicit --confirmatory is required; no draws permitted')
    if workers<1:
        raise ValueError('workers must be positive')
    settings,cells,entries,_,lock=load_frozen_inputs()
    if compatibility_report is None:
        raise ValueError('Passing twelve-seed compatibility report is required')
    report=read_json(compatibility_report)
    if (report.get('status')!='PASS' or report.get('confirmatory_draws')!=0
            or report.get('science_lock')!=lock or len(report.get('checks',[]))!=12
            or not all(r['identical'] for r in report['checks'])):
        raise ValueError('Compatibility report does not match this locked launcher/science')
    # Cross-platform execution requires the compatibility fixture on this host.
    if report['environment']['python']!=frozen.environment()['python'] or report['environment']['platform']!=frozen.environment()['platform']:
        raise ValueError('Run compatibility fixture on the actual execution environment')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    with (output/'.execution.lock').open('a') as execution_lock:
        try: fcntl.flock(execution_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise ValueError('Another invocation owns this output directory')
        fingerprint=digest(dict(schema=SCHEMA,lock=lock,phase='confirmatory',planned_entries=entries))
        manifest_path=output/'run_manifest.json'
        if manifest_path.exists():
            if not resume: raise ValueError('Existing run requires explicit --resume')
            manifest=read_json(manifest_path)
            if manifest['fingerprint']!=fingerprint: raise ValueError('Resume refused: science/inputs/launcher changed')
        else:
            if resume or aggregate_only: raise ValueError('Cannot resume/aggregate absent manifest')
            manifest=dict(lock,schema_version=SCHEMA,fingerprint=fingerprint,git_sha=frozen.git_sha(),
                phase='confirmatory',planned_run_ids=[e['run_id'] for e in entries],
                canonical_inputs_sha256=digest(entries),planned_logs=6000,planned_candidate_records=1134000,
                within_method_confidence_levels=settings['alphas'],methods=settings['methods'],
                preflight_in_confirmatory_denominator=False,config=settings,
                phase_authority='COMET_CODEX_GATE_C_STAT_AND_REWRITE.md + user C-STAT authorization',
                compatibility_report_sha256=hashlib.sha256(Path(compatibility_report).read_bytes()).hexdigest())
            atomic_json(manifest_path,manifest)
            atomic_json(output/'source_and_environment.json',dict(lock=lock,environment=frozen.environment(),
                git_sha=frozen.git_sha(),git_status_porcelain=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)))
        invocation_id=str(time.time_ns());started=time.perf_counter();cpu=time.process_time()
        children_before=resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime+resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime
        completed=[];skipped=[];pending=[];status='RUNNING';error_info=None
        append_event(output,'INVOCATION_STARTED',invocation_id=invocation_id,workers=workers,aggregate_only=aggregate_only)
        try:
            for entry in entries:
                path=checkpoint_path(output,entry)
                if path.exists():
                    saved=load_checkpoint(path,entry,fingerprint)
                    validate_payload(saved['payload'],entry,settings)
                    skipped.append(entry['run_id'])
                else: pending.append(entry)
            if aggregate_only and pending:
                raise ValueError('Cannot aggregate incomplete allocation: '+str(len(pending))+' IDs missing')
            if pending:
                worker_provenance={key:manifest[key] for key in ('git_sha','config_hash','source_hash','fingerprint')}
                jobs=iter((cells[e['cell_id']],e,settings,worker_provenance,str(output)) for e in pending)
                with ProcessPoolExecutor(max_workers=workers) as pool:
                    futures={}
                    def submit_next():
                        job=next(jobs,None)
                        if job is None: return False
                        append_event(output,'RUN_DISPATCHED',invocation_id=invocation_id,run_id=job[1]['run_id'])
                        futures[pool.submit(_worker,job)]=job[1]['run_id']
                        return True
                    for _ in range(workers): submit_next()
                    try:
                        while futures:
                            done,_=wait(futures,return_when=FIRST_COMPLETED)
                            for future in done:
                                futures.pop(future)
                                result=future.result();completed.append(result['run_id'])
                                append_event(output,'RUN_COMPLETED',invocation_id=invocation_id,**result)
                                print(f"completed {len(completed)+len(skipped)}/6000 {result['run_id']}",flush=True)
                                submit_next()
                    except BaseException:
                        for future in futures: future.cancel()
                        # Only up to workers already dispatched jobs can remain;
                        # they retain their checkpoints/errors. Nothing further
                        # is submitted, and the invocation remains FAILED.
                        raise
            inventory,_=aggregate(output,entries,manifest,settings)
            if inventory['completed_logs']!=6000 or inventory['candidate_records']!=1134000:
                raise ValueError('BLOCKED: complete allocation count mismatch')
            status='COMPLETE'
            return inventory
        except BaseException as error:
            status='FAILED';error_info=dict(error=repr(error),traceback=traceback.format_exc())
            atomic_json(output/'failures'/f'invocation_{invocation_id}.json',dict(kind='ACTUAL_INVOCATION_ERROR',**error_info))
            append_event(output,'INVOCATION_FAILED',invocation_id=invocation_id,**error_info)
            raise
        finally:
            child=resource.getrusage(resource.RUSAGE_CHILDREN)
            resources=dict(invocation_id=invocation_id,status=status,workers=workers,
                new_completed_logs=len(completed),skipped_completed_logs=len(skipped),
                completed_run_ids=completed,skipped_run_ids=skipped,wall_seconds=time.perf_counter()-started,
                parent_cpu_seconds=time.process_time()-cpu,
                child_cpu_seconds=child.ru_utime+child.ru_stime-children_before,
                parent_peak_rss_bytes=frozen.peak_rss_bytes(),
                child_max_peak_rss_bytes=int(child.ru_maxrss if os.uname().sysname=='Darwin' else child.ru_maxrss*1024),
                memory_scope='parent cumulative high-water; maximum child process high-water, not summed concurrent RSS or standalone method memory',
                git_sha=frozen.git_sha(),error=error_info)
            atomic_json(output/'invocations'/f'{invocation_id}.json',resources)
            append_event(output,'INVOCATION_FINISHED',**resources)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--confirmatory',action='store_true')
    mode.add_argument('--compatibility-only',action='store_true')
    parser.add_argument('--output',default='results/gate_C/confirmatory')
    parser.add_argument('--compatibility-report')
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--aggregate-only',action='store_true')
    parser.add_argument('--workers',type=int,default=1)
    args=parser.parse_args()
    if args.compatibility_only: compatibility(args.output)
    else: run(args.output,args.confirmatory,args.resume,args.workers,args.compatibility_report,args.aggregate_only)


if __name__=='__main__': main()

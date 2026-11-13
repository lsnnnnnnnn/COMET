"""Launcher tests use frozen metadata and historical outcomes only."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from experiments import gate_c_confirmatory as runner
from experiments import gate_c_preflight as original
from comet.gate_c_statistics import summarize_records

ROOT=Path(__file__).resolve().parents[1]


def historical(cell='A',replicate=0):
    seeds=original.read_json(ROOT/'configs/gate_C_seed_manifest.json')
    entry=next(e for e in seeds['runs'] if e['phase']=='preflight' and e['cell_id']==cell and e['replicate']==replicate)
    payload=original.read_json(original.checkpoint_path(ROOT/'results/gate_C/preflight/batch',entry))['payload']
    return entry,payload


def test_lock_allows_new_launcher_but_no_changes_in_26_frozen_sources(tmp_path):
    lock=runner.check_scientific_lock()
    assert len(lock['science_sources'])==26
    assert 'experiments/gate_c_confirmatory.py' not in lock['science_sources']
    for name in [*runner.SCIENCE_SOURCES,'configs/gate_C_frozen.json','configs/gate_C_seed_manifest.json']:
        dest=tmp_path/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
    assert runner.check_scientific_lock(tmp_path)==lock
    (tmp_path/'comet/gate_c_truth.py').write_text('# changed scientific source\n')
    with pytest.raises(ValueError,match='BLOCKED: frozen science hash mismatch'):
        runner.check_scientific_lock(tmp_path)


def test_allocated_6000_ids_are_exact_and_exclude_preflight():
    settings,cells,entries,preflight,lock=runner.load_frozen_inputs()
    assert len(entries)==6000 and len(preflight)==12
    assert set(e['run_id'] for e in entries).isdisjoint(e['run_id'] for e in preflight)
    assert {e['phase'] for e in entries}=={'confirmatory'}
    for cell in 'ABCDEF':
        assert sorted(e['replicate'] for e in entries if e['cell_id']==cell)==list(range(1000))
    assert len(settings['primary_comparisons'])==17


def test_no_explicit_confirmatory_flag_fails_before_generation(tmp_path,monkeypatch):
    monkeypatch.setattr(runner,'load_frozen_inputs',lambda:pytest.fail('must refuse before inputs/generation'))
    with pytest.raises(ValueError,match='Explicit --confirmatory'):
        runner.run(tmp_path)
    result=subprocess.run([sys.executable,'-m','experiments.gate_c_confirmatory'],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==2 and 'required' in result.stderr


def test_no_compatibility_report_refuses_before_generation(tmp_path,monkeypatch):
    monkeypatch.setattr(runner,'evaluate_frozen',lambda *a:pytest.fail('generation prohibited'))
    with pytest.raises(ValueError,match='compatibility report is required'):
        runner.run(tmp_path,confirmatory=True)
    assert not (tmp_path/'run_manifest.json').exists()


def test_execution_field_filter_preserves_every_scientific_value():
    entry,payload=historical()
    changed=deepcopy(payload)
    changed['wall_seconds']=123;changed['phase']='confirmatory'
    for row in changed['records']:
        row['phase']='confirmatory';row['git_sha']='new';row['source_hash']='new'
        row['schema_version']='new';row['process_peak_rss_bytes']=123
        row['family_call_wall_seconds']=123;row['family_call_cpu_seconds']=123
    assert runner.canonical(runner.scientific_payload(changed))==runner.canonical(runner.scientific_payload(payload))
    changed['records'][0]['raw_radius']+=.01
    assert runner.canonical(runner.scientific_payload(changed))!=runner.canonical(runner.scientific_payload(payload))


def test_atomic_checkpoint_is_immutable_on_read_and_detects_corruption(tmp_path):
    entry,payload=historical();path=runner.checkpoint_path(tmp_path,entry)
    wrapper=dict(run_id=entry['run_id'],fingerprint='frozen',input_sha256=runner.digest(entry),
                 payload_sha256=runner.digest(payload),payload=payload)
    runner.atomic_gzip_json(path,wrapper);before=path.read_bytes()
    assert runner.load_checkpoint(path,entry,'frozen')==wrapper
    assert path.read_bytes()==before
    with pytest.raises(ValueError,match='checkpoint mismatch'):
        runner.load_checkpoint(path,entry,'changed')
    wrapper['payload']['raw_N']=1;runner.atomic_gzip_json(path,wrapper)
    with pytest.raises(ValueError,match='checkpoint mismatch'):
        runner.load_checkpoint(path,entry,'frozen')


def test_applicability_failure_cannot_disappear_from_denominator():
    entry,payload=historical();settings=original.read_json(ROOT/'configs/gate_C_frozen.json')
    runner.validate_payload(payload,entry,settings)
    bad=deepcopy(payload);bad['records'][0]['certificate_applicable']=False
    with pytest.raises(ValueError,match='unexpected theorem status'):
        runner.validate_payload(bad,entry,settings)
    bad=deepcopy(payload);bad['records'].pop()
    with pytest.raises(ValueError,match='missing/extra method-level family'):
        runner.validate_payload(bad,entry,settings)
    empty=deepcopy(payload);empty['records'][0].update(decision_issuable=False,covered=False,is_empty=True)
    runner.validate_payload(empty,entry,settings)  # Applicable empty intersection stays a failure.
    entry,payload=historical('F');runner.validate_payload(payload,entry,settings)


def test_partitioned_aggregation_equals_frozen_statistics_with_all_12_historical_logs(tmp_path):
    settings,cells,_,entries,lock=runner.load_frozen_inputs()
    manifest=dict(fingerprint='fixture',planned_run_ids=[e['run_id'] for e in entries])
    all_records=[]
    for entry in entries:
        payload=original.read_json(original.checkpoint_path(ROOT/'results/gate_C/preflight/batch',entry))['payload']
        all_records.extend(payload['records'])
        runner.atomic_gzip_json(runner.checkpoint_path(tmp_path,entry),dict(run_id=entry['run_id'],
            fingerprint='fixture',input_sha256=runner.digest(entry),payload_sha256=runner.digest(payload),payload=payload))
    before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (tmp_path/'run_checkpoints').rglob('*.gz')}
    inventory,actual=runner.aggregate(tmp_path,entries,manifest,settings,phase='preflight')
    expected=summarize_records(all_records,phase='preflight',primary_comparisons=settings['primary_comparisons'])
    assert runner.canonical(actual)==runner.canonical(expected)
    assert inventory['completed_logs']==12 and inventory['candidate_records']==2268
    assert inventory['all_planned_ids_complete']
    assert len(actual)==84
    assert before=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (tmp_path/'run_checkpoints').rglob('*.gz')}
    assert len(list((tmp_path/'raw_shards').glob('*.csv.gz')))==6


def test_orchestration_failure_resume_keeps_checkpoint_and_never_redraws(tmp_path,monkeypatch):
    """Mock two infrastructure jobs; no simulator and no allocated C-STAT ID."""
    from concurrent.futures import Future
    settings,cells,_,_,lock=runner.load_frozen_inputs()
    entries=[];payloads={}
    for replicate in (0,1):
        entry,payload=historical('A',replicate)
        entry=deepcopy(entry);payload=deepcopy(payload)
        entry.update(phase='confirmatory',run_id=f'unit-fixture-only/A/{replicate}')
        payload.update(phase='confirmatory',run_id=entry['run_id'])
        for row in payload['records']: row.update(phase='confirmatory',run_id=entry['run_id'])
        entries.append(entry);payloads[entry['run_id']]=payload
    monkeypatch.setattr(runner,'load_frozen_inputs',lambda:(settings,cells,entries,[],lock))
    class InlinePool:
        def __init__(self,**kwargs): pass
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def submit(self,fn,*args):
            future=Future()
            try: future.set_result(fn(*args))
            except BaseException as error: future.set_exception(error)
            return future
    monkeypatch.setattr(runner,'ProcessPoolExecutor',InlinePool)
    calls=[];fail_once=[True]
    def no_simulation(cell,entry,*args):
        calls.append(entry['run_id'])
        if entry['replicate']==1 and fail_once[0]:
            fail_once[0]=False
            raise RuntimeError('INJECTED_UNIT_TEST_EXECUTION_FAILURE')
        return deepcopy(payloads[entry['run_id']])
    monkeypatch.setattr(runner,'evaluate_frozen',no_simulation)
    report=dict(status='PASS',confirmatory_draws=0,science_lock=lock,
                checks=[dict(identical=True) for _ in range(12)],environment=original.environment())
    report_path=tmp_path/'test_compatibility.json';original.atomic_json(report_path,report)
    output=tmp_path/'mock_execution'
    # This mock only substitutes the final production-sized completion gate;
    # actual checkpoint contents/identity/digests remain checked by real code.
    def mock_aggregate(output,entries,manifest,settings):
        assert len(entries)==2
        for entry in entries:
            runner.load_checkpoint(runner.checkpoint_path(output,entry),entry,manifest['fingerprint'])
        return dict(completed_logs=6000,candidate_records=1134000),[]
    monkeypatch.setattr(runner,'aggregate',mock_aggregate)
    with pytest.raises(RuntimeError,match='INJECTED_UNIT_TEST_EXECUTION_FAILURE'):
        runner.run(output,confirmatory=True,compatibility_report=report_path)
    first=runner.checkpoint_path(output,entries[0]);original_bytes=first.read_bytes()
    assert len(list((output/'failures').glob('*.json')))==2
    runner.run(output,confirmatory=True,resume=True,compatibility_report=report_path)
    assert first.read_bytes()==original_bytes
    assert calls==[entries[0]['run_id'],entries[1]['run_id'],entries[1]['run_id']]
    before=list(calls)
    runner.run(output,confirmatory=True,resume=True,compatibility_report=report_path)
    assert calls==before and first.read_bytes()==original_bytes
    invocations=[original.read_json(p) for p in sorted((output/'invocations').glob('*.json'))]
    assert [i['status'] for i in invocations]==['FAILED','COMPLETE','COMPLETE']
    assert invocations[-1]['new_completed_logs']==0 and invocations[-1]['skipped_completed_logs']==2

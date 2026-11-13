"""Read-only scientific-lock audit; never generates outcomes or changes the freeze."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
from collections import Counter
from experiments.gate_c_preflight import canonical, digest, load_inputs
from comet.gate_c_statistics import summarize_records

ROOT = Path(__file__).resolve().parents[1]
BASE = '06a39b89e579aef57d14ae51e86d74ecf9b6b768'
FREEZE = 'ab4c74fbf1ae84c0e5ffd72d77ce5b48d3fba8cb'


def audit():
    failures=[]
    checks=0
    def check(ok, message):
        nonlocal checks
        checks+=1
        if not ok: failures.append(message)
    def blob(commit,path):
        return subprocess.check_output(['git','show',f'{commit}:{path}'],cwd=ROOT)
    paths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    hashes={}
    for path in paths:
        old=hashlib.sha256(blob(BASE,path)).hexdigest()
        current=hashlib.sha256((ROOT/path).read_bytes()).hexdigest() if (ROOT/path).exists() else None
        hashes[path]={'baseline':old,'current':current}
        check(old==current,f'baseline changed: {path}')
    manifest=json.loads((ROOT/'results/gate_C/preflight/batch/run_manifest.json').read_text())
    science={}
    for path,expected in manifest['source_checksums'].items():
        frozen=hashlib.sha256(blob(FREEZE,path)).hexdigest()
        current=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
        science[path]=current
        check(expected==frozen==current,f'science hash: {path}')
    settings,cells,entries,confighash=load_inputs(ROOT/'configs/gate_C_frozen.json')
    check(confighash==manifest['config_hash'],'config hash')
    for path in ('configs/gate_C_frozen.json','configs/gate_C_seed_manifest.json'):
        check((ROOT/path).read_bytes()==blob(FREEZE,path),f'freeze input bytes: {path}')
    seeds=json.loads((ROOT/'configs/gate_C_seed_manifest.json').read_text())
    counts=Counter((r['phase'],r['cell_id']) for r in seeds['runs'])
    check(len(seeds['runs'])==6012,'6012 allocated IDs')
    for cell in cells:
        check(counts['confirmatory',cell]==1000,f'{cell} confirmatory count')
        check(counts['preflight',cell]==2,f'{cell} preflight count')
    records=[]; checkpoints=[]
    for entry in entries:
        path=ROOT/'results/gate_C/preflight/batch/runs'/entry['cell_id']/f"{entry['replicate']:04d}.json"
        wrapper=json.loads(path.read_text()); payload=wrapper['payload']
        check(digest(payload)==wrapper['payload_sha256'],f'checkpoint payload {entry["run_id"]}')
        check(wrapper['fingerprint']==manifest['fingerprint'],f'fingerprint {entry["run_id"]}')
        check(payload['run_id']==entry['run_id'] and payload['phase']=='preflight','preflight identity')
        check(payload['seed_streams']==entry['streams'],'preflight streams')
        check(len(payload['records'])==len(cells[entry['cell_id']].design.family)*14,'record count')
        records.extend(payload['records'])
        checkpoints.append({'run_id':entry['run_id'],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    saved=json.loads((ROOT/'results/gate_C/preflight/batch/preflight_summary.json').read_text())
    recomputed=summarize_records(records,primary_comparisons=settings['primary_comparisons'])
    check(canonical(saved)==canonical(recomputed),'all 84 frozen summaries exactly recomputed')
    check(len(records)==2268 and len(saved)==84,'preflight output dimensions')
    check(len(settings['primary_comparisons'])==17,'17 primary comparisons')
    check(all(r['family_coverage']==1 for r in saved if r['applicable_families']==2),'preflight family coverage reconciliation')
    result=dict(status='PASS' if not failures else 'BLOCKED',checks=checks,failures=failures,
        baseline_git_sha=BASE,scientific_freeze_git_sha=FREEZE,
        current_git_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        git_status=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True),
        baseline_files_unchanged=len(paths),baseline_file_checksums=hashes,
        science_source_allowlist=science,science_digest=digest(science),config_sha256=confighash,
        seed_manifest_sha256=settings['seed_manifest_sha256'],preflight_checkpoints=checkpoints,
        allocated_confirmatory_ids=6000,generated_confirmatory_logs=0,
        scope='static lock and preflight artifact recomputation only; no outcome generation')
    return result

if __name__=='__main__':
    result=audit()
    output=ROOT/'results/gate_C/stat_lock/scientific_lock_audit.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists(): raise SystemExit('Refuse overwriting saved audit')
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k in ('status','checks','failures','baseline_files_unchanged','science_digest')}))
    raise SystemExit(bool(result['failures']))

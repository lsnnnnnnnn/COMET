"""Wait for the authorized batch; verify idempotent resume and run fixed reports.

No scientific parameters or selected IDs are changed. No outcomes are generated
by the audit/report steps; the resume must have zero incomplete IDs.
"""
from pathlib import Path
import fcntl,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/gate_C/confirmatory'
LOG=ROOT/'reports/gate_C_stat_logs'
PYTHON=str(ROOT/'.venv/bin/python')
def read(p):return json.loads(p.read_text())
def hashes():return {str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((OUT/'run_checkpoints').glob('*/*.json.gz'))}
def command(args,log):
 with (LOG/log).open('w') as f:r=subprocess.run(args,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'MPLCONFIGDIR':'/tmp/comet-matplotlib'})
 with (LOG/'postprocessing_commands.jsonl').open('a') as f:f.write(json.dumps({'command':args,'exit_code':r.returncode,'log':log})+'\n')
 if r.returncode:raise SystemExit(r.returncode)
 print('completed '+log,flush=True)
def main():
 marker=OUT/'postprocessing_started.json'
 while True:
  finished=[read(p) for p in sorted((OUT/'invocations').glob('*.json'))]
  if finished:
   if finished[-1]['status']!='COMPLETE':raise SystemExit('BLOCKED: batch invocation failed; inspect preserved failure')
   with (OUT/'.execution.lock').open('a') as lock:
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:pass
    else:break
  time.sleep(20)
 if marker.exists():raise SystemExit('Postprocessing already started; do not silently repeat')
 before=hashes();assert len(before)==6000
 marker.write_text(json.dumps({'checkpoint_count_before_resume':len(before),'before_sha256':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),'source':str(Path(__file__).relative_to(ROOT))},indent=2)+'\n')
 (OUT/'before_resume_checkpoint_hashes.json').write_text(json.dumps(before,sort_keys=True,indent=2)+'\n')
 command([PYTHON,'-m','experiments.gate_c_confirmatory','--confirmatory','--resume','--aggregate-only','--compatibility-report','results/gate_C/stat_lock/compatibility_local_final/compatibility_result.json','--workers','6','--output','results/gate_C/confirmatory'],'confirmatory_idempotent_resume.txt')
 after=hashes();assert before==after,'Completed checkpoint bytes changed'
 latest=read(sorted((OUT/'invocations').glob('*.json'))[-1]);assert latest['new_completed_logs']==0 and latest['skipped_completed_logs']==6000
 (OUT/'resume_integrity.json').write_text(json.dumps({'status':'PASS','completed_checkpoint_files':6000,'all_checkpoint_bytes_unchanged':True,'new_outcome_logs':0,'skipped_completed_logs':6000,'invocation_id':latest['invocation_id'],'checkpoint_inventory_sha256':hashlib.sha256(json.dumps(after,sort_keys=True).encode()).hexdigest(),'derived_exports':'regenerated from immutable checkpoints; gzip header times may differ, scientific rows unchanged'},indent=2)+'\n')
 command([PYTHON,'reports/gate_C_stat_audit/validate_confirmatory.py','--input','results/gate_C/confirmatory','--output','results/gate_C/confirmatory/independent_validation','--phase','confirmatory','--figures'],'confirmatory_independent_validation.txt')
 command([PYTHON,'reports/gate_C_stat_audit/finalize_reports.py'],'confirmatory_report_generation.txt')
 print('POSTPROCESSING COMPLETE: root must review reports and plots before final delivery',flush=True)
if __name__=='__main__':main()

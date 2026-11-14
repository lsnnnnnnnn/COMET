"""Current-task serial queue: wait for E4, then use its freed CPU slot.

E5 is the only other scientific worker. This supervisor does not spawn any
parallel stages, edit protocols, sample E0, or launch E5 shards. Stop it if the
active task/session must end; it is not a background service.
"""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]
os.chdir(ROOT)
PY=str(ROOT/'.venv/bin/python')
REPORT=ROOT/'reports/post_cstat'
def now():return datetime.now(timezone.utc).isoformat()
def module(name,*args):return [PY,'-m',name,*args]
stages=[
 ('E4_analysis',module('experiments.extension_runner','--suite','E4','--analyze','--output','results/post_cstat/E4_analysis_v1')),
 ('E1_detailed',module('experiments.detailed_diagnostics','--protocol','results/post_cstat/E1_protocol.json','--results','results/post_cstat/E1','--output','results/post_cstat/E1_detailed_v1')),
 ('E3_detailed',module('experiments.detailed_diagnostics','--protocol','results/post_cstat/E3_protocol.json','--results','results/post_cstat/E3','--output','results/post_cstat/E3_detailed_v1')),
 ('E4_detailed',module('experiments.detailed_diagnostics','--protocol','results/post_cstat/E4_protocol.json','--results','results/post_cstat/E4','--output','results/post_cstat/E4_detailed_v1')),
 ('ANCHORS_run',module('experiments.anchor_runner','--run')),
 ('ANCHORS_analysis',module('experiments.anchor_runner','--analyze','--output','results/post_cstat/ANCHORS_analysis_v1')),
 ('negative_run',module('experiments.negative_controls','--run')),
 ('negative_analysis',module('experiments.negative_controls','--analyze','--output','results/post_cstat/negative_controls_analysis_v1')),
]
state=dict(status='WAITING_FOR_E4_RECEIPT',supervisor_pid=os.getpid(),started_utc=now(),completed_stages=[],
           scope='serial child only; E5 separate; no unattended service')
def save():
 (REPORT/'serial_queue_state.json').write_text(json.dumps(state,indent=2)+'\n')
save()
expected=json.loads((ROOT/'results/post_cstat/E4_protocol.json').read_text())['fingerprint']
while True:
 receipts=sorted((ROOT/'results/post_cstat/E4/invocations').glob('*.json'))
 if receipts:
  receipt=json.loads(receipts[-1].read_text())
  if receipt['fingerprint']!=expected or receipt['status']!='COMPLETE':
   state.update(status='E4_NOT_COMPLETE',receipt=receipt);save();raise SystemExit('E4 receipt requires coordinator attention')
  break
 time.sleep(2)
print('E4 complete; starting one serial child at a time',flush=True)
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
try:
 for name,command in stages:
  state.update(status='RUNNING',active_stage=name,command=command,stage_started_utc=now());save()
  print(name+' started '+now(),flush=True)
  with (REPORT/f'queue_{name}_stdout.txt').open('x') as out,(REPORT/f'queue_{name}_stderr.txt').open('x') as err:
   child=subprocess.Popen(command,stdout=out,stderr=err,env=env)
   state['child_pid']=child.pid;save();code=child.wait()
  if code:
   state.update(status='STAGE_FAILED',exit_code=code);save();raise SystemExit(code)
  if '--output' in command:
   output=ROOT/command[command.index('--output')+1]/'summary.json'
   summary=json.loads(output.read_text())
   if summary['status'] not in ('COMPLETE','COMPLETE_CHECKS_PASS'):
    state.update(status='INCOMPLETE_STAGE_REQUIRES_ATTENTION',stage_summary_status=summary['status']);save();raise SystemExit(5)
  if name.endswith('_run'):
   suite='ANCHORS' if name=='ANCHORS_run' else 'negative_controls'
   receipt_paths=sorted((ROOT/'results/post_cstat'/suite/'invocations').glob('*.json'))
   run_receipt=json.loads(receipt_paths[-1].read_text())
   if run_receipt['status']!='COMPLETE' or run_receipt.get('remaining_ids'):
    state.update(status='RUN_REQUIRES_ATTENTION',run_receipt=run_receipt);save();raise SystemExit(6)
  if name.endswith('_detailed'):
   result=json.loads((REPORT/f'queue_{name}_stdout.txt').read_text())
   if result['status']!='COMPLETE_CHECKS_PASS':
    state.update(status='DIAGNOSTIC_REQUIRES_ATTENTION',diagnostic=result);save();raise SystemExit(3)
  if name=='E4_analysis':
   result=json.loads((ROOT/'results/post_cstat/E4_analysis_v1/summary.json').read_text())
   if any(row.get('holm_undercoverage_p') is not None and row['holm_undercoverage_p']<.01 for row in result['primary_diagnostics']):
    state.update(status='VALIDITY_FLAG_REQUIRES_ATTENTION');save();raise SystemExit(4)
  state['completed_stages'].append(name);save();print(name+' finished '+now(),flush=True)
 state.update(status='COMPLETE',finished_utc=now(),child_pid=None);save()
except KeyboardInterrupt:
 if 'child' in globals() and child.poll() is None:
  child.send_signal(2);child.wait()
 state.update(status='INTERRUPTED',finished_utc=now(),child_pid=None);save();raise

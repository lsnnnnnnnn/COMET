"""One server scientific child at a time; restart by inspecting immutable receipts."""
from pathlib import Path
from datetime import datetime,timezone
import json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2];os.chdir(ROOT)
REPORT=ROOT/'reports/post_cstat';RESULT=ROOT/'results/post_cstat'
state={'status':'STARTING','supervisor_pid':os.getpid(),'stages':[],'started_utc':datetime.now(timezone.utc).isoformat(),'maximum_scientific_children':1,'local_primary_worker':'E5 original host; coordinator enforces two globally','E0_new_draws':0}
def save():
 (REPORT/'server_queue_state.json').write_text(json.dumps(state,indent=2)+'\n')
def run_stage(name,args):
 token=str(time.time_ns());state.update(status='RUNNING',active_stage=name,command=args,stage_token=token);save()
 with (REPORT/f'server_{name}_{token}_stdout.txt').open('x') as out,(REPORT/f'server_{name}_{token}_stderr.txt').open('x') as err:
  child=subprocess.Popen([sys.executable,'-m',*args],stdout=out,stderr=err,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1'))
  state['child_pid']=child.pid;save();code=child.wait()
 if code:raise RuntimeError(name+' returned '+str(code))
 state['child_pid']=None
try:
 for suite,module in [('ANCHORS','experiments.anchor_runner'),('negative_controls','experiments.negative_controls')]:
  protocol=RESULT/(suite+'_server_v2_protocol.json');root=RESULT/suite
  manifest=json.loads(protocol.read_text());expected=manifest['fingerprint']
  receipts=sorted((root/'invocations').glob('*.json'))
  complete=False
  if receipts:
   receipt=json.loads(receipts[-1].read_text())
   if receipt['fingerprint']!=expected:raise RuntimeError('wrong existing fingerprint')
   complete=receipt['status']=='COMPLETE' and not receipt.get('remaining_ids')
  if not complete:run_stage(suite+'_run',[module,'--run','--protocol',str(protocol),'--results',str(root),'--global-results',str(RESULT)])
  receipt=json.loads(sorted((root/'invocations').glob('*.json'))[-1].read_text())
  if receipt['status']!='COMPLETE' or receipt.get('remaining_ids'):raise RuntimeError('incomplete run; preserve all checkpoints')
  state['stages'].append(suite+'_run');save()
  output=RESULT/(suite+'_server_v2_analysis_v1')
  if not (output/'summary.json').is_file():run_stage(suite+'_analysis',[module,'--analyze','--protocol',str(protocol),'--results',str(root),'--output',str(output)])
  summary=json.loads((output/'summary.json').read_text())
  if summary['status']!='COMPLETE':raise RuntimeError('incomplete analysis; inspect retained output')
  state['stages'].append(suite+'_analysis');save()
 state.update(status='COMPLETE',finished_utc=datetime.now(timezone.utc).isoformat(),child_pid=None);save()
except BaseException as exc:
 state.update(status='STOPPED_REQUIRES_COORDINATOR',reason=repr(exc),finished_utc=datetime.now(timezone.utc).isoformat());save();raise

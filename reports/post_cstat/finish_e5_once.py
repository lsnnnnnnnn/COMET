"""Current-task finite supervisor; no new outcomes and no persistent service."""
from pathlib import Path
from datetime import datetime,timezone
import json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2];os.chdir(ROOT)
REPORT=ROOT/'reports/post_cstat';state={'status':'WAITING_FOR_BOTH_E5_SHARDS','pid':os.getpid(),'new_outcome_draws':0}
def save(): (REPORT/'finish_e5_state.json').write_text(json.dumps(state,indent=2)+'\n')
save();child=None
try:
 while True:
  results=[]
  for i in (0,1):
   try: results.append(json.loads((REPORT/f'E5_shard{i}_stdout.json').read_text()))
   except json.JSONDecodeError:break
  if len(results)==2:
   if any(r['status']!='SHARD_COMPLETE' for r in results):raise RuntimeError('shards need coordinator attention')
   break
  time.sleep(2)
 from comet.checkpoint_store import CheckpointStore
 manifest=json.loads((ROOT/'results/post_cstat/E5_protocol.json').read_text());store=CheckpointStore(ROOT/'results/post_cstat/E5',manifest)
 if store.remaining_ids():raise RuntimeError('full E5 inventory not complete')
 for name,args in [('analysis',['experiments.pipeline_runner','--analyze','--output','results/post_cstat/E5_analysis_v1']),('diagnostics',['experiments.pipeline_diagnostics','--protocol','results/post_cstat/E5_protocol.json','--results','results/post_cstat/E5','--output','reports/post_cstat/E5_diagnostics_v1'])]:
  state.update(status='RUNNING',active_stage=name);save()
  with (REPORT/f'E5_final_{name}_stdout.json').open('x') as out,(REPORT/f'E5_final_{name}_stderr.txt').open('x') as err:
   child=subprocess.Popen([sys.executable,'-m',*args],stdout=out,stderr=err,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1'))
   state['child_pid']=child.pid;save();code=child.wait()
  if code:raise RuntimeError(name+' failed '+str(code))
 state.update(status='COMPLETE',finished_utc=datetime.now(timezone.utc).isoformat(),child_pid=None);save()
except BaseException as exc:
 if child is not None and child.poll() is None:child.send_signal(2);child.wait()
 state.update(status='STOPPED_REQUIRES_COORDINATOR',reason=repr(exc),child_pid=None);save();raise

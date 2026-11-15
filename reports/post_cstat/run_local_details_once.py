from pathlib import Path
from datetime import datetime, timezone
import json, os, subprocess, sys
root=Path(__file__).resolve().parents[2];os.chdir(root)
state={'status':'RUNNING','stages':[],'pid':os.getpid(),'new_outcome_draws':0}
out=root/'reports/post_cstat/local_details_v2_state.json'
for suite in ['E1','E3','E4']:
 state['active_stage']=suite;out.write_text(json.dumps(state,indent=2)+'\n')
 cmd=[sys.executable,'-m','experiments.detailed_diagnostics','--protocol',f'results/post_cstat/{suite}_protocol.json','--results',f'results/post_cstat/{suite}','--output',f'results/post_cstat/{suite}_detailed_v1']
 with (root/f'reports/post_cstat/{suite}_detailed_v2_stdout.txt').open('x') as stdout,(root/f'reports/post_cstat/{suite}_detailed_v2_stderr.txt').open('x') as stderr:
  p=subprocess.run(cmd,stdout=stdout,stderr=stderr)
 if p.returncode:state.update(status='FAILED',exit_code=p.returncode);out.write_text(json.dumps(state,indent=2));sys.exit(p.returncode)
 s=json.loads((root/f'results/post_cstat/{suite}_detailed_v1/summary.json').read_text())
 if s['status']!='COMPLETE_CHECKS_PASS':raise RuntimeError('diagnostic mismatch; preserve outputs')
 state['stages'].append(suite)
state.update(status='COMPLETE',finished_utc=datetime.now(timezone.utc).isoformat());out.write_text(json.dumps(state,indent=2)+'\n')

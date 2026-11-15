"""Read-only cross-platform fixture comparison with fixed predeclared tolerances."""
from pathlib import Path
import json,math,hashlib
r=Path(__file__).resolve().parent
left=r/'server_fixture_local_v3.json';right=r/'server_fixture_linux_v3.json'
a=json.loads(left.read_text());b=json.loads(right.read_text());counts={'numeric':0,'exact':0};mismatches=[];largest_abs=0.
def visit(x,y,path='fixture_values'):
 global largest_abs
 if isinstance(x,bool) or isinstance(x,str) or x is None or isinstance(x,int):
  counts['exact']+=1
  if type(x)!=type(y) or x!=y:mismatches.append({'path':path,'local':x,'server':y})
 elif isinstance(x,float):
  counts['numeric']+=1
  if not isinstance(y,(int,float)) or isinstance(y,bool) or not math.isfinite(y) or not math.isclose(x,y,rel_tol=5e-12,abs_tol=5e-13):mismatches.append({'path':path,'local':x,'server':y})
  else:largest_abs=max(largest_abs,abs(x-y))
 elif isinstance(x,dict):
  if set(x)!=set(y):mismatches.append({'path':path,'keys_differ':True});return
  for k in x:visit(x[k],y[k],path+'.'+k)
 elif isinstance(x,list):
  if len(x)!=len(y):mismatches.append({'path':path,'lengths':[len(x),len(y)]});return
  for i,(xx,yy) in enumerate(zip(x,y)):visit(xx,yy,path+f'[{i}]')
 else:raise TypeError(type(x))
hash_differences=[]
for env in (a,b):
 for name,record in env['fixture_values'].items():
  if 'explicit_observations' not in record:continue
  import numpy as np
  obs=record['explicit_observations']
  actual=hashlib.sha256(np.array(obs['actions'],dtype=np.uint8).tobytes()+np.array(obs['outcomes'],dtype='<f8').tobytes()).hexdigest()
  if actual!=record['data_digest']:raise ValueError('self-hash mismatch '+name)
for name in a['fixture_values']:
 x=a['fixture_values'][name];y=b['fixture_values'][name]
 if 'explicit_observations' in x:
  hash_differences.append({'condition':name,'local':x.pop('data_digest'),'server':y.pop('data_digest'),'role':'within-host immutable checksum; cross-host compares exposed observations numerically'})
visit(a['fixture_values'],b['fixture_values'])
s={'status':'PASS' if not mismatches else 'FAIL','scope':'12 explicit deterministic fixture conditions; production samplers forbidden; not empirical evidence or general cross-platform exactness','counts':counts,'mismatch_count':len(mismatches),'mismatches':mismatches,'largest_absolute_numeric_difference':largest_abs,'rtol':5e-12,'atol':5e-13,'status_decision_coverage_equality':'exact','local_environment':a['environment'],'server_environment':b['environment'],'new_scientific_draws':0,'within_host_data_hashes':hash_differences,'input_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [left,right]}}
p=r/'server_fixture_comparison_v2.json'
with p.open('x') as f:f.write(json.dumps(s,indent=2)+'\n')
print(json.dumps({k:s[k] for k in ['status','counts','mismatch_count','largest_absolute_numeric_difference']}))
if mismatches:raise SystemExit(1)

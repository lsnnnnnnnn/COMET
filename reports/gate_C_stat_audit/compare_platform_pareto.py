import gzip,json,math,collections,hashlib,pathlib,struct
root=pathlib.Path('.')
def read(name):
 with gzip.open(root/name,'rt') as f:return json.load(f)
local=read('results/gate_C/stat_lock/platform_diagnostic_local_F0000.json.gz')
server=read('results/gate_C/stat_lock/platform_diagnostic_server_F0000.json.gz')
rowdiff=[]
for x,y in zip(local['rows'],server['rows']):
 assert x[:-1]==y[:-1]
 if x[-1]!=y[-1]:
  a,b=x[-1],y[-1]
  rowdiff.append(dict(unit_id=x[0],block_id=x[1],cluster_id=x[2],context=x[3],exposure=x[4],local=a,server=b,local_hex=a.hex(),server_hex=b.hex(),absolute_difference=abs(a-b),difference_over_local_ulp=abs(a-b)/math.ulp(a)))
tracecounts=collections.Counter();tracediffs=[]
for a,b in zip(local['primitive_traces'],server['primitive_traces']):
 assert a.keys()==b.keys()
 d={}
 for key in a:
  if a[key]!=b[key]:
   tracecounts[key]+=1
   assert key in ('power_hex','noise_hex','outcome_hex')
   x,y=float.fromhex(a[key]),float.fromhex(b[key])
   d[key]=dict(local=a[key],server=b[key],absolute_difference=abs(x-y),difference_over_local_ulp=abs(x-y)/math.ulp(x))
 if d:tracediffs.append(dict(cluster_id=a['cluster_id'],exposure=a['exposure'],uniform_hex=a['uniform_hex'],sign=a['sign'],exponent_hex=a['exponent_hex'],differences=d))
mismatch=json.load(open('results/gate_C/stat_lock/compatibility_server/mismatch.json'))
leafdiff=[]
def compare(a,b,path=''):
 assert type(a)==type(b)
 if isinstance(a,dict):
  assert a.keys()==b.keys()
  for k in a: compare(a[k],b[k],path+'.'+k)
 elif isinstance(a,list):
  assert len(a)==len(b)
  for i,(x,y) in enumerate(zip(a,b)):compare(x,y,f'{path}[{i}]')
 elif a!=b:leafdiff.append(dict(path=path,expected=a,actual=b))
compare(mismatch['expected'],mismatch['actual'])
assert all(d['path'].endswith('.observed_data_sha256') for d in leafdiff)
assert local['observed_data_sha256']==mismatch['expected']['observed_data_sha256']
assert server['observed_data_sha256']==mismatch['actual']['observed_data_sha256']
result=dict(status='SERVER_COMPATIBILITY_BLOCKED_LOCAL_ONLY',diagnosis='floating_point_power_evaluation_differs_across_verified_execution_environments',
 run_id=local['run_id'],confirmatory_draws=0,local_environment=local['environment'],server_environment=server['environment'],
 sampler_source_identical=local['sampler_sha256']==server['sampler_sha256'],sampler_sha256=local['sampler_sha256'],
 primitive_draws=16384,primitive_rng_uniform_sign_exponent_mean_identical=True,primitive_difference_counts=dict(tracecounts),
 raw_rows=32768,differing_reward_rows=len(rowdiff),differing_independent_clusters=len(set(r['cluster_id'] for r in rowdiff)),
 max_reward_absolute_difference=max(r['absolute_difference'] for r in rowdiff),max_reward_difference_over_local_ulp=max(r['difference_over_local_ulp'] for r in rowdiff),
 max_power_difference_over_local_ulp=max(d['differences'].get('power_hex',{}).get('difference_over_local_ulp',0) for d in tracediffs),
 local_observed_data_sha256=local['observed_data_sha256'],server_observed_data_sha256=server['observed_data_sha256'],
 mismatched_scientific_payload_leaves=len(leafdiff),all_payload_leaf_differences_only_observed_data_hash=True,
 all_reported_estimates_intervals_truth_status_decisions_metrics_identical=True,record_count=224,
 row_differences=rowdiff,primitive_differences=tracediffs,payload_differences=leafdiff,
 response='No tolerance relaxed; no scientific source or floating-point formula changed; server rejected for C-STAT; historical-compatible local environment only.',
 theorem_scope='No new theorem/model/formula discrepancy found. Existing exact-real theorem and acknowledged ordinary floating-point implementation convention remain unchanged. This diagnostic does not establish exact finite-precision coverage.',
 evidence_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in ['results/gate_C/stat_lock/platform_diagnostic_local_F0000.json.gz','results/gate_C/stat_lock/platform_diagnostic_server_F0000.json.gz','results/gate_C/stat_lock/compatibility_server/mismatch.json','reports/gate_C_stat_audit/diagnose_platform_pareto.py']})
result['commands']=[
 dict(command='.venv/bin/python reports/gate_C_stat_audit/diagnose_platform_pareto.py --output results/gate_C/stat_lock/platform_diagnostic_local_F0000.json.gz',exit_code=0),
 dict(command="ssh -o BatchMode=yes 10.200.13.23 'cd /data1/shengen/COMET_C_STAT_20261113 && python3 - --output results/gate_C/stat_lock/platform_diagnostic_server_F0000.json.gz' < reports/gate_C_stat_audit/diagnose_platform_pareto.py",exit_code=0),
 dict(command='scp -o BatchMode=yes 10.200.13.23:/data1/shengen/COMET_C_STAT_20261113/results/gate_C/stat_lock/platform_diagnostic_server_F0000.json.gz results/gate_C/stat_lock/platform_diagnostic_server_F0000.json.gz',exit_code=0),
 dict(command='.venv/bin/python /tmp/compare_cstat_platform.py',exit_code=0,note='Initial comparison before adding command provenance to the preserved program.'),
 dict(command='.venv/bin/python reports/gate_C_stat_audit/compare_platform_pareto.py',exit_code=0)]
result['comparison_script_sha256']=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()
(root/'results/gate_C/stat_lock/server_platform_diagnosis.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['row_differences','primitive_differences','payload_differences']},indent=2))

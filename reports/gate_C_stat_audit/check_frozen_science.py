"""Read-only deterministic proof/code audit; generates no evaluation outcomes."""
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
FREEZE='ab4c74fbf1ae84c0e5ffd72d77ce5b48d3fba8cb'
checks=0

def check(value, message):
    global checks
    checks+=1
    if not value:
        raise AssertionError(message)

def close(actual,expected,label):
    check(math.isclose(actual,expected,rel_tol=2e-13,abs_tol=2e-13),label)

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)

def sha(value):
    return hashlib.sha256(value).hexdigest()

def tail(k):
    return Fraction(sum(math.comb(k,j)*7**(k-j) for j in range((k+1)//2,k+1)),8**k)

manifest=json.loads((ROOT/'results/gate_C/preflight/batch/run_manifest.json').read_text())
hashes={}
for name,expected in manifest['source_checksums'].items():
    raw=(ROOT/name).read_bytes()
    check(sha(raw)==expected,'saved source hash '+name)
    check(raw==subprocess.check_output(['git','show',FREEZE+':'+name],cwd=ROOT),'freeze source '+name)
    hashes[name]=sha(raw)
for name in ('configs/gate_C_frozen.json','configs/gate_C_seed_manifest.json',
             'theory/theorem_to_code_contract.md','theory/exact_binomial_mom.md',
             'theory/bounded_graph_variance.md','theory/gate_c_heavy_tail_contract.md',
             'theory/lower_bound.md'):
    raw=(ROOT/name).read_bytes()
    check(raw==subprocess.check_output(['git','show',FREEZE+':'+name],cwd=ROOT),'freeze input/proof '+name)
    hashes[name]=sha(raw)
config=json.loads((ROOT/'configs/gate_C_frozen.json').read_text())
seeds=json.loads((ROOT/'configs/gate_C_seed_manifest.json').read_text())
check(sha((ROOT/'configs/gate_C_seed_manifest.json').read_bytes())==config['seed_manifest_sha256'],'seed manifest hash')
check(len([x for x in seeds['runs'] if x['phase']=='confirmatory'])==6000,'6000 reserved IDs')
check(len(config['primary_comparisons'])==17,'17 comparisons')
cells={x['cell_id']:x for x in config['cells']}
rows=0
primary={}
paths=sorted((ROOT/'results/gate_C/preflight/batch/runs').glob('*/*.json'))
check(len(paths)==12,'12 existing logs')
for path in paths:
    wrapper=json.loads(path.read_text()); payload=wrapper['payload']
    check(sha(canonical(payload).encode())==wrapper['payload_sha256'],'checkpoint digest')
    cell=cells[payload['cell_id']]; d=cell['design']; p=cell['p']; m=len(d['q_probs'])*len(d['auditors'])
    N=d['B']*d['n0']; chi=d['chi']
    check(len(payload['records'])==14*m,'complete paired families')
    for r in payload['records']:
        rows+=1
        qtext,auditor=r['candidate_id'].split('__'); q1=float(qtext[1:]); q=(1-q1,q1)
        mass=1 if auditor=='all' else .5
        close(r['true_target'],.025+.425*q1 if auditor=='all' else .05+.225*q1,'analytic target')
        close(r['subgroup_mass'],mass,'fixed mass')
        close(r['constraint_threshold'],.2*mass,'threshold')
        close(r['N_eff'],N/chi,'N/chi')
        check(r['diagnostics_enter_certified_radius'] is False,'diagnostic-only scale')
        check(r['nuisance_radius']==r['drift_radius']==r['coupling_failure_epsilon']==0,'zero extra budgets')
        method=r['method']; alpha=r['nominal_delta']
        if method in ('ips','dm','dr'):
            check(r['status']=='POINT_ONLY' and r['raw_lo'] is None and r['raw_hi'] is None,'point status')
            continue
        if method=='bounded_graph_chebyshev' and cell['cell_id']=='F':
            check(r['status']=='NOT_APPLICABLE' and r['raw_lo'] is None,'F graph refused')
            continue
        check(r['certificate_applicable'] and r['status']=='CERTIFIED','expected eligible status')
        if method=='full_feasible_range':
            close(r['raw_lo'],-mass*.25,'range lower'); close(r['raw_hi'],mass*.75,'range upper')
        elif method in ('orig_mom','exact_binomial_mom'):
            K=(math.ceil(8*math.log(2*m/alpha)) if method=='orig_mom' else
               next(k for k in range(1,d['B']//2+1,2) if m*tail(k)<=Fraction(str(alpha))))
            check(r['K']==K and r['L_min']==d['B']//K,'MOM K and grouping')
            check(sum(r['group_sizes'])==d['B'] and min(r['group_sizes'])>=2,'all blocks retained feasible')
            check(m*tail(K)<=Fraction(str(alpha)),'exact family failure budget')
            envelopes=[]
            for e1 in d['e_by_context']:
                J=sum(qs**p*es**(1-p) for qs,es in zip(q,(1-e1,e1)))
                multiplier=1 if cell['outcome_family']=='bernoulli' else 2**(p-1)*(1+cell['tail_alpha']*cell['tail_scale']**p/(cell['tail_alpha']-p))
                envelopes.append(2**(2*p-1)*(1+multiplier*J))
            envelope=max(envelopes)
            close(r['known_centered_p_envelope'],envelope,'known conditional p envelope')
            radius=(32*envelope)**(1/p)*(chi/(r['L_min']*d['n0']))**((p-1)/p)
            close(r['raw_radius'],radius,'MOM conservative radius')
        else:
            v=[]
            for x,e1 in enumerate(d['e_by_context']):
                h=1 if auditor=='all' else x
                v.append(h*h*sum(qs*qs/es for qs,es in zip(q,(1-e1,e1))))
            variance=chi*sum(v)/(2*N)
            close(r['variance_bound'],variance,'known graph variance')
            close(r['raw_radius'],math.sqrt(m*variance/alpha),'Chebyshev radius and multiplicity')
        if method!='full_feasible_range' and alpha==.05:
            key=(cell['cell_id'],method,payload['run_id'])
            primary.setdefault(key,[]).append(r['decision_issuable'] and r['covered'])
        check(r['false_safe']==(r['decision']=='CERTIFIED_SAFE' and r['true_violation']),'false safe definition')
        check(r['false_violation']==(r['decision']=='CERTIFIED_VIOLATION' and not r['true_violation']),'false violation definition')
check(rows==2268,'all preflight candidate rows')
check(len(primary)==34 and all(all(v) for v in primary.values()),'17 comparisons x2 paired families')
print(json.dumps(dict(verdict='PASS_NO_NEW_THEOREM_CODE_MISMATCH_FOUND',checks=checks,
                     read_only=True,outcomes_generated=0,preflight_checkpoints=12,candidate_rows=rows,
                     frozen_source_commit=FREEZE,exact_source_and_input_sha256=hashes,
                     arithmetic_scope='ordinary floating-point implementation as explicitly preregistered; no exact final-bit CI claim'),indent=2,sort_keys=True))

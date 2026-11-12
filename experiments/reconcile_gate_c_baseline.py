"""Read-only scientific reconciliation of C0; never generates evaluation draws.

Run from the repository root: python -m experiments.reconcile_gate_c_baseline
Only the new C-PREFLIGHT audit JSON is written. Source references use the fixed
Gate A+B+C0 delivery commit, even after a later branch adds new files.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
from fractions import Fraction
from hashlib import sha256
import json
from math import ceil, comb, isclose, log, sqrt
from pathlib import Path
from statistics import NormalDist, mean, median
import subprocess

BASE = '3f8902d1033f3c4eece9a3746912ac9f1d8904ef'
ROOT = Path(__file__).resolve().parents[1]


def _typed(value):
    if value == '':
        return None
    if value in ('True', 'False'):
        return value == 'True'
    try:
        return float(value)
    except ValueError:
        return value


def _q(values, probability):
    ordered = sorted(values)
    position = probability*(len(ordered)-1)
    low = int(position)
    return ordered[low]+(ordered[min(low+1,len(ordered)-1)]-ordered[low])*(position-low)


def _weighted_q(pairs, probability):
    pairs = sorted(pairs)
    position = probability*(sum(count for _,count in pairs)-1)
    low = int(position)
    def item(index):
        for value,count in pairs:
            if index < count:
                return value
            index -= count
        raise AssertionError('weighted quantile index')
    return item(low)+(item(min(low+1,sum(n for _,n in pairs)-1))-item(low))*(position-low)


def _wilson(hits, total):
    z = NormalDist().inv_cdf(.975)
    den = 1+z*z/total
    center = (hits/total+z*z/(2*total))/den
    half = z*sqrt(hits/total*(1-hits/total)/total+z*z/(4*total*total))/den
    return max(0.,center-half),min(1.,center+half)


def _tail(k):
    return sum((Fraction(comb(k,j)*7**(k-j),8**k)
                for j in range((k+1)//2,k+1)),Fraction())


def run(output=ROOT/'results/gate_C/preflight/c0_reconciliation.json'):
    directory = ROOT/'results/gate_C0'
    rows = [{key:_typed(value) for key,value in r.items()}
            for r in csv.DictReader((directory/'pilot.csv').open())]
    saved = json.loads((directory/'pilot_summary.json').read_text())
    settings = json.loads((directory/'preregistered_config.json').read_text())
    manifest = json.loads((directory/'run_manifest.json').read_text())
    counts = {(r['cell_id'],r['replicate_id']):r
              for r in json.loads((directory/'data_summaries.json').read_text())}
    cells = {c['cell_id']:c for c in settings['cells']}
    failures = []
    checks = Counter()
    def verify(condition, description, category):
        checks[category] += 1
        if not condition:
            failures.append(description)
    def close(actual,expected,description,category='record_numeric'):
        verify(isclose(actual,expected,rel_tol=1e-11,abs_tol=1e-11),description,category)

    source_hashes = {}
    for path,expected in manifest['source_sha256'].items():
        archived = subprocess.check_output(['git','show',manifest['git_head']+':'+path],cwd=ROOT)
        current = (ROOT/path).read_bytes()
        source_hashes[path] = sha256(current).hexdigest()
        verify(source_hashes[path]==expected==sha256(archived).hexdigest(),path,'source_hash')
    verify(sha256((ROOT/'configs/gate_C0_pilot.json').read_bytes()).hexdigest()==manifest['config_sha256'],
           'C0 config hash','source_hash')
    verify(settings==json.loads((ROOT/'configs/gate_C0_pilot.json').read_text()),'config copy','source_hash')

    preserved = []
    paths = subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    for path in paths:
        archived = subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
        current = (ROOT/path).read_bytes()
        unchanged = archived == current
        verify(unchanged,path,'baseline_preservation')
        preserved.append(dict(path=path,sha256=sha256(current).hexdigest(),unchanged=unchanged))

    unique_runs = {(r['cell_id'],int(r['replicate_id']),int(r['seed'])) for r in rows}
    verify(len(rows)==19680 and len(unique_runs)==210 and len(counts)==210,'pilot cardinality','layout')
    verify(len({seed for _,_,seed in unique_runs})==210,'distinct seeds','layout')
    verify(len(saved)==56 and len(cells)==7,'summary cardinality','layout')
    for cell,replicate,seed in unique_runs:
        verify(seed==cells[cell]['base_seed']+replicate,'seed definition','layout')
        verify(seed==counts[cell,replicate]['seed'],'counts seed','layout')
    diagnostics = {}
    for row in rows:
        cell = cells[row['cell_id']]
        cfg = cell['synthetic']
        n = cfg['B']*cfg['n0']
        q1 = float(row['candidate_id'].split('__')[0][1:])
        auditor = row['candidate_id'].split('__')[1]
        q = (1-q1,q1)
        h = (1,1) if auditor=='all' else (0,1)
        mass = sum(h)/2
        true_mu = ((.2,.6),(.35,.8))
        truth = sum(h[x]*(sum(q[s]*true_mu[x][s] for s in (0,1))-cfg['reference']) for x in (0,1))/2
        close(row['exact_oracle_truth'],truth,'analytic target')
        close(row['subgroup_mass'],mass,'known subgroup mass')
        verify(row['status']=='CERTIFIED','registered status','record_flags')
        verify(row['raw_N']==row['retained_N']==n,'row retention','record_flags')
        verify(row['discarded_rows']==row['discarded_blocks']==0,'no discarded rows','record_flags')
        verify(row['nuisance_radius']==row['drift_radius']==row['coupling_failure_epsilon']==0,
               'zero extra budgets','record_flags')
        close(row['feasible_lo'],-mass*cfg['reference'],'support lower')
        close(row['feasible_hi'],mass*(1-cfg['reference']),'support upper')
        close(row['feasible_diameter'],mass,'support diameter')
        method,alpha,m = row['method'],row['nominal_delta'],int(row['family_size'])
        if method in ('conservative_hoeffding','exact_binomial'):
            if method=='conservative_hoeffding':
                k = ceil(8*log(2*m/alpha))
            else:
                k = next(k for k in range(1,cfg['B']//2+1,2) if m*_tail(k)<=Fraction(str(alpha)))
            l = cfg['B']//k
            moment = max(2**(2*cell['p']-1)*(1+sum(q[s]**cell['p']*e[s]**(1-cell['p']) for s in (0,1)))
                         for e in [(1-e1,e1) for e1 in cfg['e_by_context']])
            nu = moment**(1/cell['p'])
            radius = 32**(1/cell['p'])*nu*(cfg['chi']/(l*cfg['n0']))**((cell['p']-1)/cell['p'])
            verify(row['K']==k and row['L_min']==l and row['L_max']==ceil(cfg['B']/k),'K/L','record_flags')
            close(row['nu_p'],nu,'known conditional scale')
            close(row['binomial_familywise_failure_bound'],float(m*_tail(k)),'exact majority bound')
        elif method=='bounded_graph_chebyshev':
            variance = cfg['chi']/n*sum(h[x]**2*sum(q[s]**2/e[s] for s in (0,1))
                                       for x,e in enumerate((1-e1,e1) for e1 in cfg['e_by_context']))/2
            radius = sqrt(m*variance/alpha)
            close(row['variance_bound'],variance,'known graph variance')
            verify(row['K'] is None and row['L_min'] is None,'mean has no MOM grouping','record_flags')
        else:
            verify(method=='trivial_support','recognized method','record_flags')
            radius = mass/2
        close(row['raw_radius'],radius,'raw radius')
        close(row['raw_lo'],row['raw_estimate']-radius,'raw lower')
        close(row['raw_hi'],row['raw_estimate']+radius,'raw upper')
        lo=max(row['raw_lo'],row['feasible_lo']); hi=min(row['raw_hi'],row['feasible_hi'])
        close(row['clipped_lo'],lo,'clipped lower'); close(row['clipped_hi'],hi,'clipped upper')
        width=max(0.,hi-lo)
        close(row['clipped_width'],width,'clipped width');close(row['width_fraction'],width/mass,'width fraction')
        close(row['informativeness_fraction'],1-width/mass,'information fraction')
        verify(row['is_empty']==(lo>hi),'empty flag','record_flags')
        verify(row['is_full_range']==(lo<=hi and width>=mass-1e-12),'full flag','record_flags')
        verify(row['is_nontrivial']==(lo<=hi and width<mass-1e-12),'nontrivial flag','record_flags')
        verify(row['raw_covered']==(row['raw_lo']<=truth<=row['raw_hi']),'raw coverage','record_flags')
        verify(row['covered']==(lo<=truth<=hi),'clipped coverage','record_flags')
        close(row['absolute_error'],abs(row['raw_estimate']-truth),'absolute error')
        threshold=.2*mass
        close(row['safety_threshold'],threshold,'fixed constraint')
        safe=lo<=hi and hi<=threshold; unsafe=lo<=hi and lo>threshold
        verify(row['safe_certified']==safe and row['unsafe_certified']==unsafe,'constraint decision','record_flags')
        verify(row['decision_unresolved']==(not(safe or unsafe)),'unresolved decision','record_flags')
        verify(row['false_safe']==(safe and truth>threshold),'false safe','record_flags')
        key=(row['cell_id'],int(row['replicate_id']),row['candidate_id'])
        if key not in diagnostics:
            score_pairs,weight_pairs=[],[]
            for count in counts[key[0],key[1]]['observed_counts']:
                x,s,y,num=count['context'],count['exposure'],count['reward'],count['count']
                e1=cfg['e_by_context'][x];e=(1-e1,e1)
                w=q[s]/e[s]
                z=h[x]*(sum(q[t]*cfg['mu_hat'][t] for t in (0,1))-cfg['reference']+w*(y-cfg['mu_hat'][s]))
                score_pairs.append((z,num));weight_pairs.append((w,num))
            diag={}
            for name,prob in [('min',0),('median',.5),('p90',.9),('p95',.95),('p99',.99),('max',1)]:
                diag['abs_score_'+name]=_weighted_q([(abs(z),num) for z,num in score_pairs],prob)
                diag['observed_q_over_e_'+name]=_weighted_q(weight_pairs,prob)
            diag['importance_ess_diagnostic']=sum(w*num for w,num in weight_pairs)**2/sum(w*w*num for w,num in weight_pairs)
            diag['score_empirical_p_moment_diagnostic']=sum(abs(z)**cell['p']*num for z,num in score_pairs)/n
            diagnostics[key]=(diag,sum(z*num for z,num in score_pairs)/n)
        diag,scoremean=diagnostics[key]
        for field,value in diag.items():
            close(row[field],value,field,'counts_diagnostics')
        if method=='bounded_graph_chebyshev':
            close(row['raw_estimate'],scoremean,'sample mean from persisted counts','counts_diagnostics')
        verify(row['raw_data_sha256']==counts[key[0],key[1]]['raw_data_sha256'],'paired data digest','record_flags')

    grouped=defaultdict(list)
    for r in rows:
        grouped[r['cell_id'],r['nominal_delta'],r['method']].append(r)
    independent=[]
    for key,records in sorted(grouped.items()):
        byrep=defaultdict(list)
        for r in records:byrep[int(r['replicate_id'])].append(r)
        expected_ids={f'q{float(q)!r}__{h}' for q in cells[key[0]]['synthetic']['q_probs'] for h in cells[key[0]]['synthetic']['auditors']}
        for group in byrep.values():
            verify(len(group)==len(expected_ids) and {r['candidate_id'] for r in group}==expected_ids,'complete paired family','layout')
        issued=sum(all(r['issued'] for r in group) for group in byrep.values())
        hits=sum(all(r['covered'] for r in group) for group in byrep.values())
        rawhits=sum(all(r['raw_covered'] for r in group) for group in byrep.values())
        n=len(byrep); wl,wh=_wilson(hits,issued)
        widths=[r['width_fraction'] for r in records]
        recalculated=dict(cell_id=key[0],alpha=key[1],method=key[2],replications=n,
             issued_families=issued,covered_families=hits,raw_family_coverage=rawhits/n,
             issued_and_covers_rate=hits/n,coverage_given_issued=hits/issued,wilson_lo=wl,wilson_hi=wh,
             unresolved_or_abstention_fraction=1-issued/n,
             familywise_nontrivial_some=mean(any(r['is_nontrivial'] for r in group) for group in byrep.values()),
             familywise_nontrivial_all=mean(all(r['is_nontrivial'] for r in group) for group in byrep.values()),
             marginal_nontrivial_rate=mean(r['is_nontrivial'] for r in records),
             median_width_fraction=median(widths),p90_width_fraction=_q(widths,.9),
             median_informativeness=median(r['informativeness_fraction'] for r in records),
             median_raw_radius=median(r['raw_radius'] for r in records),
             median_radius_over_diameter=median(r['raw_radius']/r['feasible_diameter'] for r in records),
             median_absolute_error=median(r['absolute_error'] for r in records),
             safe_certifications=sum(r['safe_certified'] for r in records),
             unsafe_certifications=sum(r['unsafe_certified'] for r in records),
             constraint_unresolved_fraction=mean(r['decision_unresolved'] for r in records),
             false_safe_count=sum(r['false_safe'] for r in records),
             false_safe_family_count=sum(any(r['false_safe'] for r in group) for group in byrep.values()),
             N=records[0]['raw_N'],N_eff=records[0]['N_eff'],chi=records[0]['chi_max'],
             family_size=len(expected_ids),p=records[0]['cell_moment_order'],K=records[0]['K'],L_min=records[0]['L_min'])
        saved_row=next(r for r in saved if (r['cell_id'],r['alpha'],r['method'])==key)
        for field,value in recalculated.items():
            if isinstance(value,(int,float)):
                close(saved_row[field],value,field,'summary_numeric')
            else:
                verify(saved_row[field]==value,field,'summary_identity')
        independent.append(recalculated)
    index={(r['cell_id'],r['alpha'],r['method']):r for r in independent}
    methods=['conservative_hoeffding','exact_binomial','bounded_graph_chebyshev','trivial_support']
    report=(ROOT/'reports/gate_C0_report.md').read_text()
    for cell in settings['cells']:
        for alpha in settings['alphas']:
            expected='| '+cell['cell_id']+f' | {1-alpha:.0%} | '+' | '.join(f'{index[cell["cell_id"],alpha,m]["median_width_fraction"]:.5f}' for m in methods)+' |'
            verify(expected in report,'report width row '+cell['cell_id'],'markdown')
    table=(directory/'pilot_table.md').read_text()
    for r in independent:
        expected=(f"| {r['cell_id']} | {1-r['alpha']:.0%} | {r['method']} | {r['covered_families']}/{r['issued_families']} | "
                  f"[{r['wilson_lo']:.3f}, {r['wilson_hi']:.3f}] | {r['median_width_fraction']:.3f} / {r['p90_width_fraction']:.3f} | "
                  f"{r['familywise_nontrivial_some']:.0%} / {r['familywise_nontrivial_all']:.0%} | "
                  f"{r['unresolved_or_abstention_fraction']:.0%} / {r['constraint_unresolved_fraction']:.0%} | {r['false_safe_count']} |")
        verify(expected in table,'pilot Markdown '+r['cell_id']+r['method'],'markdown')
    timing=defaultdict(list)
    for r in csv.DictReader((directory/'timings.csv').open()):timing[r['method']].append(float(r['seconds']))
    runtime={method:dict(calls=len(values),median_seconds=median(values),sum_seconds=sum(values))
             for method,values in sorted(timing.items())}
    for method,r in runtime.items():
        expected=f'| {method} | {r["calls"]} | {r["median_seconds"]:.6f} | {r["sum_seconds"]:.3f} |'
        verify(expected in report,'runtime Markdown '+method,'markdown')

    result=dict(schema_version='comet_gate_c_c0_reconciliation_v1',baseline_commit=BASE,
        new_outcomes_generated=0,passed=not failures,failures=failures,checks=dict(checks),
        candidate_records=len(rows),independent_replication_cells=len(unique_runs),summaries=len(independent),
        source_hashes=source_hashes,config_sha256=manifest['config_sha256'],
        prior_files=preserved,prior_files_checked=len(preserved),
        baseline_test_files=[p for p in paths if p.startswith('tests/test_')],
        c0_elapsed_seconds=manifest['elapsed_seconds'],c0_method_runtime=runtime,
        c0_all_family_coverage_counts=sorted(set((r['covered_families'],r['issued_families']) for r in independent)),
        c0_95_easy={m:index['iid_single_8192',.05,m] for m in methods},
        recomputed_summaries=independent,
        reconciliations=[
            'All 56 summaries and their displayed Markdown values agree with the saved CSV within 1e-11 numerical tolerance and stated rounding.',
            'The original m=4/p=1.5 smoke K41->7 is a different design from C0 easy m=1/p=2 K30->3 and the m=16 fixture K52->9.',
            'C0 finite_p15 cell remains bounded Bernoulli; it is not genuine unbounded heavy-tail evidence.',
            'CI issuance abstention differs from unresolved constraint decisions; both remain separately defined.',
            'Support-only construction was not separately timed, and C0 recorded no peak memory; these values cannot be retroactively inferred.',
            'C0 has no checkpoint/resume mechanism and only two active RNG streams; C-PREFLIGHT must supply the new contract.',
            'C0 run source SHA15af184 is the preregistered ancestor of result/delivery SHA3f8902d, not a conflicting source version.'
        ],
        limits='Read-only audit; no outcome sequence regenerated. Aggregated counts verify sample means, weight/score diagnostics, and digest consistency, but cannot reconstruct MOM point estimates or row-order digests. Their persisted endpoints/radii and source provenance are checked.')
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps(dict(passed=not failures,checks=sum(checks.values()),failures=len(failures),prior_files=len(preserved),rows=len(rows),summaries=len(independent))))
    if failures:
        raise AssertionError(failures[:10])
    return result


if __name__=='__main__':
    run()

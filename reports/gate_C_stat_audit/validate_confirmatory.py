"""Independent streaming checkpoint audit and C-STAT figure regeneration.

No imports from comet or the experiment runner; no observations are generated.
Reads one complete checkpoint at a time and retains only compact numeric arrays.
"""
from __future__ import annotations
import argparse
from array import array
from collections import Counter, defaultdict
import csv
from fractions import Fraction
from functools import lru_cache
import gzip
import hashlib
import json
import math
from pathlib import Path
import resource
import statistics
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
METHODS=('orig_mom','exact_binomial_mom','bounded_graph_chebyshev','ips','dm','dr','full_feasible_range')
PRIMARY=tuple((c,m) for c in 'ABCDEF' for m in METHODS[:3] if (c,m)!=('F',METHODS[2]))
CONFIG_HASH='b834e7b409bb008ba0d2b6e591515873831f87d036fdc53ed0392d0b94012ff4'
SEED_HASH='9d04a99066a7c8c0234f226f4dddfa33e9c0171fdb6f3486c30452389c667eab'
CHECKS=0


def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(x): return hashlib.sha256(canonical(x).encode()).hexdigest()
def read(path):
    opener=gzip.open if str(path).endswith('.gz') else open
    with opener(path,'rt') as f: return json.load(f)
def check(condition,message):
    global CHECKS
    CHECKS+=1
    if not condition: raise AssertionError(message)
def near(a,b,message):
    if a is None or b is None: check(a is b,message)
    else: check(math.isclose(a,b,rel_tol=5e-12,abs_tol=5e-13),message)
def write_json(path,value):
    Path(path).write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')
def write_csv(path,rows):
    with Path(path).open('w',newline='') as f:
        fields=sorted(set().union(*(r.keys() for r in rows))) if rows else []
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rows: w.writerow({k:canonical(v) if isinstance(v,(dict,list,tuple)) else v for k,v in r.items()})
def wilson(k,n):
    if not n:return None,None
    z=statistics.NormalDist().inv_cdf(.975);p=k/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return max(0.,center-half),min(1.,center+half)
@lru_cache(None)
def lower_exact(k,n,nominal):
    p=Fraction(str(nominal));a,b=p.numerator,p.denominator
    return Fraction(sum(math.comb(n,j)*a**j*(b-a)**(n-j) for j in range(k+1)),b**n)
def upper_float(x):
    out=float(x)
    return math.nextafter(out,math.inf) if Fraction.from_float(out)<x else out
def holm(values):
    running=0.;result={}
    for rank,key in enumerate(sorted(values,key=lambda k:(values[k],str(k)))):
        running=max(running,min(1.,(len(values)-rank)*values[key]));result[key]=running
    return result
def quantile(values,q):
    if not values:return None
    xs=sorted(values);p=(len(xs)-1)*q;i=int(p)
    return xs[i]+(xs[min(i+1,len(xs)-1)]-xs[i])*(p-i)
def median(values):return statistics.median(values) if values else None


class Accumulator:
    def __init__(self,cell,alpha,method):
        self.cell,self.alpha,self.method=cell,alpha,method
        self.count=Counter();self.status=Counter();self.decision=Counter()
        self.values={k:array('d') for k in ('width','radius','error','signed','ratio','raw_width','clipped_width')}
        self.first=None;self.marginal=defaultdict(Counter)
    def add(self,family):
        if self.first is None:self.first={k:family[0].get(k) for k in ('family_size','raw_N','N_eff','chi_max','B','n0','K','L_min','L_max','p_declared')}
        c=self.count;c['n']+=1;c['rows']+=len(family)
        c['applicable']+=all(r['certificate_applicable'] for r in family)
        c['issued']+=all(r['decision_issuable'] for r in family)
        c['hits']+=all(r['decision_issuable'] and r['covered'] for r in family)
        c['raw_hits']+=all(r['status']=='CERTIFIED' and r['raw_covered'] for r in family)
        c['na']+=any(r['status']=='NOT_APPLICABLE' for r in family)
        c['nontrivial_some']+=any(r['is_nontrivial'] for r in family)
        c['nontrivial_all']+=all(r['is_nontrivial'] for r in family)
        c['false_safe_any']+=any(r['false_safe'] for r in family)
        c['false_violation_any']+=any(r['false_violation'] for r in family)
        c['false_any']+=any(r['false_safe'] or r['false_violation'] for r in family)
        c['violation_detected_any']+=any(r['true_violation'] and r['decision']=='CERTIFIED_VIOLATION' for r in family)
        c['true_violation_any']+=any(r['true_violation'] for r in family)
        c['abstain_any']+=any(r['decision']=='ABSTAIN' for r in family)
        c['no_decision_any']+=any(r['decision'] not in ('CERTIFIED_SAFE','CERTIFIED_VIOLATION') for r in family)
        for r in family:
            self.status[r['status']]+=1;self.decision[r['decision']]+=1
            c['nontrivial']+=r['is_nontrivial'];c['true_violation']+=r['true_violation']
            c['power']+=r['true_violation'] and r['decision']=='CERTIFIED_VIOLATION'
            c['false_safe']+=r['false_safe'];c['false_violation']+=r['false_violation']
            for target,source in (('width','width_fraction'),('radius','raw_radius'),('error','absolute_error'),('signed','signed_error'),('clipped_width','clipped_width')):
                if r.get(source) is not None:self.values[target].append(r[source])
            if r.get('absolute_error') is not None and r.get('raw_radius') not in (None,0):self.values['ratio'].append(r['absolute_error']/r['raw_radius'])
            if r['raw_lo'] is not None:self.values['raw_width'].append((r['raw_hi']-r['raw_lo'])/r['feasible_diameter'])
            mc=self.marginal[r['candidate_id']];mc['n']+=1;mc['applicable']+=r['certificate_applicable'];mc['issued']+=r['decision_issuable'];mc['hits']+=bool(r['decision_issuable'] and r['covered']);mc['raw_hits']+=bool(r['raw_covered']);mc['false_safe']+=r['false_safe'];mc['false_violation']+=r['false_violation']
    def finish(self,phase):
        c=self.count;n=c['n'];z=c['rows'];defined=c['applicable']==n and n>0
        wl,wh=wilson(c['hits'],n) if defined else (None,None)
        cl,ch=wilson(c['hits'],c['issued'])
        v=self.values;lo,hi=quantile(v['width'],.25),quantile(v['width'],.75)
        s=dict(phase=phase,cell_id=self.cell,alpha=self.alpha,nominal_level=1-self.alpha,method=self.method,
            replications=n,candidate_records=z,family_size=self.first['family_size'],status_counts=dict(sorted(self.status.items())),
            applicable_families=c['applicable'],applicability_fraction=c['applicable']/n,issued_families=c['issued'],
            covered_families=c['hits'] if defined else None,family_coverage=c['hits']/n if defined else None,
            raw_family_coverage=c['raw_hits']/n if defined else None,wilson_lo=wl,wilson_hi=wh,
            issued_and_covers_rate=c['hits']/n if defined else None,coverage_given_issued=c['hits']/c['issued'] if c['issued'] else None,
            conditional_wilson_lo=cl,conditional_wilson_hi=ch,interval_absent_fraction=1-c['issued']/n,
            not_applicable_families=c['na'],family_nontrivial_some=c['nontrivial_some']/n,family_nontrivial_all=c['nontrivial_all']/n,
            marginal_nontrivial_fraction=c['nontrivial']/z,median_width_fraction=median(v['width']),q25_width_fraction=lo,q75_width_fraction=hi,
            p90_width_fraction=quantile(v['width'],.9),iqr_width_fraction=hi-lo if lo is not None else None,
            median_raw_radius=median(v['radius']),median_absolute_error=median(v['error']),median_absolute_error_over_radius=median(v['ratio']),
            signed_bias=statistics.mean(v['signed']) if v['signed'] else None,
            rmse=math.sqrt(statistics.mean(e*e for e in v['error'])) if v['error'] else None,
            decision_counts=dict(sorted(self.decision.items())),constraint_abstention_fraction=self.decision['ABSTAIN']/z,
            no_certified_decision_fraction=1-(self.decision['CERTIFIED_SAFE']+self.decision['CERTIFIED_VIOLATION'])/z,
            true_violating_count=c['true_violation'],true_nonviolating_count=z-c['true_violation'],
            violation_power=c['power']/c['true_violation'] if c['true_violation'] and defined else None,
            false_safe_count=c['false_safe'],false_violation_count=c['false_violation'],
            undercoverage_pvalue=upper_float(lower_exact(c['hits'],n,1-self.alpha)) if defined and self.method in METHODS[:3] else None,
            undercoverage_holm_pvalue=None,undercoverage_test='exact_lower_tail_H0_coverage_ge_nominal',
            undercoverage_interpretation='debugging_only_not_confirmatory' if phase=='preflight' else 'nonrejection_does_not_prove_nominal_coverage')
        for k,val in self.first.items():s[k]=val
        return s
    def extras(self):
        c=self.count;n=c['n'];out=dict(cell_id=self.cell,alpha=self.alpha,method=self.method,allocated_logs=n)
        for event in ('false_safe_any','false_violation_any','false_any','violation_detected_any','true_violation_any','abstain_any','no_decision_any'):
            lo,hi=wilson(c[event],n);out.update({event+'_logs':c[event],event+'_rate':c[event]/n,event+'_wilson_lo':lo,event+'_wilson_hi':hi})
        for key in ('raw_width','clipped_width','ratio'):
            for label,q in (('q25',.25),('median',.5),('q75',.75),('p90',.9)):out[key+'_'+label]=quantile(self.values[key],q)
        out['ratio_zero_count']=sum(x==0 for x in self.values['ratio'])
        out['candidate_power_is_not_family_power']=True
        return out


def expected_candidates(cell):
    return {f"q{float(q)!r}__{h}" for q in cell['design']['q_probs'] for h in cell['design']['auditors']}

def audit_record(r,entry,cell,phase,observed_digest):
    label=entry['run_id']+'/'+r['method']+'/'+r['candidate_id']
    check(r['run_id']==entry['run_id'] and r['cell_id']==entry['cell_id'] and r['replicate']==entry['replicate'] and r['phase']==phase,'identity '+label)
    check(r['observed_data_sha256']==observed_digest,'pairing '+label)
    check(r['config_hash']==CONFIG_HASH and r['seed_manifest_hash']==SEED_HASH,'frozen inputs '+label)
    check(r['seed']==entry['streams']['logging_exposure'],'logging seed '+label)
    method=r['method'];alpha=r['nominal_delta'];applicable=method not in ('ips','dm','dr') and not (entry['cell_id']=='F' and method=='bounded_graph_chebyshev')
    status='CERTIFIED' if applicable else 'POINT_ONLY' if method in ('ips','dm','dr') else 'NOT_APPLICABLE'
    check(r['status']==status and r['certificate_applicable']==applicable,'theorem status '+label)
    qtext,auditor=r['candidate_id'].split('__');q1=float(qtext[1:]);mass=1. if auditor=='all' else .5
    target=.025+.425*q1 if auditor=='all' else .05+.225*q1
    near(r['true_target'],target,'analytic truth '+label);near(r['subgroup_mass'],mass,'known mass '+label)
    near(r['constraint_threshold'],.2*mass,'threshold '+label)
    near(r['N_eff'],cell['design']['B']*cell['design']['n0']/cell['design']['chi'],'N_eff '+label)
    check(r['true_violation']==(r['true_target']>r['constraint_threshold']),'true violation '+label)
    check(r['false_safe']==(r['decision']=='CERTIFIED_SAFE' and r['true_violation']),'false-safe '+label)
    check(r['false_violation']==(r['decision']=='CERTIFIED_VIOLATION' and not r['true_violation']),'false-violation '+label)
    near(r['absolute_error'],None if r['estimate'] is None else abs(r['estimate']-r['true_target']),'absolute error '+label)
    near(r['signed_error'],None if r['estimate'] is None else r['estimate']-r['true_target'],'signed error '+label)
    near(r['feasible_lo'],-.25*mass,'range lower '+label);near(r['feasible_hi'],.75*mass,'range upper '+label)
    if not applicable:
        check(r['raw_lo'] is None and r['raw_hi'] is None and r['raw_radius'] is None and not r['decision_issuable'],'no fabricated CI '+label)
        check(r['covered'] is None and r['raw_covered'] is None,'no fabricated coverage '+label)
        check(r['decision']==('POINT_ONLY' if status=='POINT_ONLY' else 'ABSTAIN'),'inapplicable decision '+label)
    else:
        check(all(math.isfinite(r[k]) for k in ('raw_lo','raw_hi','raw_radius','estimate')),'finite CI '+label)
        near(r['raw_lo'],r['estimate']-r['raw_radius'],'radius lower '+label)
        near(r['raw_hi'],r['estimate']+r['raw_radius'],'radius upper '+label)
        lo=max(r['raw_lo'],r['feasible_lo']);hi=min(r['raw_hi'],r['feasible_hi']);issued=lo<=hi
        check(r['decision_issuable']==issued and r['is_empty']==(not issued),'empty intersection '+label)
        near(r['clipped_lo'],lo,'intersection lower '+label);near(r['clipped_hi'],hi,'intersection upper '+label)
        check(r['raw_covered']==(r['raw_lo']<=r['true_target']<=r['raw_hi']),'raw coverage '+label)
        check(r['covered']==(lo<=r['true_target']<=hi) if issued else r['covered'] in (False,None),'coverage '+label)
        near(r['width_fraction'],(hi-lo)/mass if issued else None,'width '+label)
        expected_decision=('ABSTAIN' if not issued else 'CERTIFIED_SAFE' if hi<=.2*mass else 'CERTIFIED_VIOLATION' if lo>.2*mass else 'ABSTAIN')
        check(r['decision']==expected_decision,'decision '+label)
        check(r['is_nontrivial']==(issued and hi-lo<mass-1e-12),'nontriviality '+label)


def compare_summary(actual,reference):
    amap={(x['cell_id'],x['alpha'],x['method']):x for x in actual}
    rmap={(x['cell_id'],x['alpha'],x['method']):x for x in reference}
    check(amap.keys()==rmap.keys(),'summary group allocation')
    for key,expected in rmap.items():
        own=amap[key];check(own.keys()==expected.keys(),'summary fields '+str(key))
        for field,value in expected.items():
            if isinstance(value,float):near(own[field],value,'summary '+str(key)+'/'+field)
            else:check(own[field]==value,'summary '+str(key)+'/'+field)


def figures(output,groups,summary,resource_rows,invocations,phase):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    folder=output/'figures';folder.mkdir(exist_ok=True)
    labels={'orig_mom':'Original MOM','exact_binomial_mom':'Exact MOM','bounded_graph_chebyshev':'Graph mean','full_feasible_range':'Full range','ips':'IPS','dm':'DM','dr':'DR'}
    colors=['#0072B2','#D55E00','#009E73','#777777']
    subtitle='C-STAT: 1,000 independent logs per cell' if phase=='confirmatory' else 'Preflight fixture only: 2 logs per cell'
    def save(fig,name):
        for ext in ('png','pdf'):fig.savefig(folder/(name+'.'+ext),dpi=180,bbox_inches='tight',facecolor='white')
        plt.close(fig)
    sm={(r['cell_id'],r['alpha'],r['method']):r for r in summary}
    fig,axes=plt.subplots(2,3,figsize=(13,7),constrained_layout=True)
    for ax,cell in zip(axes.flat,'ABCDEF'):
        for j,alpha in enumerate((.05,.1)):
            for i,method in enumerate(METHODS[:3]):
                row=sm[cell,alpha,method]
                if row['family_coverage'] is None:continue
                value=row['family_coverage'];x=i+(j-.5)*.16
                ax.errorbar(x,value,yerr=[[max(0,value-row['wilson_lo'])],[max(0,row['wilson_hi']-value)]],fmt='o' if j==0 else 's',color=colors[i],capsize=3,label=f'{1-alpha:.0%}' if i==0 else None)
            ax.axhline(1-alpha,color='black',linestyle='--' if j==0 else ':',linewidth=.8)
        lower=min([.88]+[sm[cell,a,m]['wilson_lo']-.02 for a in (.05,.1) for m in METHODS[:3] if sm[cell,a,m]['wilson_lo'] is not None])
        ax.set(title='Cell '+cell,xticks=range(3),xticklabels=['Original','Exact','Graph'],ylim=(max(0,lower),1.003) if phase=='confirmatory' else (0,1.05))
        if cell=='F':ax.text(2,.93 if phase=='confirmatory' else .5,'N/A',ha='center')
        ax.set_ylabel('Family coverage; Wilson 95%');ax.legend(fontsize=8)
    fig.suptitle(subtitle+'\nCoverage by method and nominal level (separate guarantees)');save(fig,'01_family_coverage')
    fig,axes=plt.subplots(2,3,figsize=(13,7),constrained_layout=True)
    cert_methods=METHODS[:3]+('full_feasible_range',)
    for ax,cell in zip(axes.flat,'ABCDEF'):
        for i,method in enumerate(cert_methods):
            values=groups[cell,.05,method].values['width']
            if values:
                box=ax.boxplot([values],positions=[i],widths=.6,showfliers=False,whis=(0,90),patch_artist=True)
                box['boxes'][0].set(facecolor=colors[i],alpha=.55)
            else:ax.text(i,.5,'N/A',ha='center')
        ax.set(title='Cell '+cell,xticks=range(4),xticklabels=['Original','Exact','Graph','Range'],ylim=(-.02,1.04),ylabel='Clipped width / feasible diameter')
    fig.suptitle(subtitle+'\n95% intervals: boxes=IQR, line=median, whiskers=min/P90');save(fig,'02_width_distributions')
    fig,axes=plt.subplots(1,2,figsize=(14,5),constrained_layout=True)
    for ax,field,title in zip(axes,('marginal_nontrivial_fraction','no_certified_decision_fraction'),('Nontrivial candidate intervals','No certified decision (includes point-only / N/A)')):
        values=np.array([[sm[c,.05,m][field] for m in METHODS] for c in 'ABCDEF'])
        im=ax.imshow(values,cmap='cividis',vmin=0,vmax=1,aspect='auto')
        for row in range(6):
            for col in range(7):
                no_interval=(METHODS[col] in ('ips','dm','dr') or (row==5 and METHODS[col]=='bounded_graph_chebyshev'))
                annotation='N/A' if field=='marginal_nontrivial_fraction' and no_interval else f'{values[row,col]:.2f}'
                ax.text(col,row,annotation,ha='center',va='center',color='white' if values[row,col]<.5 else 'black',fontsize=9)
        ax.set(xticks=range(7),xticklabels=[labels[m] for m in METHODS],yticks=range(6),yticklabels=list('ABCDEF'),title=title)
        plt.setp(ax.get_xticklabels(),rotation=40,ha='right');fig.colorbar(im,ax=ax,shrink=.8)
    fig.suptitle(subtitle+'\nCandidate fractions; N/A = point-only or inapplicable interval; those methods have 100% no certified decision');save(fig,'03_nontriviality_abstention')
    fig,axes=plt.subplots(2,3,figsize=(13,7),constrained_layout=True)
    for ax,cell in zip(axes.flat,'ABCDEF'):
        observed_max=0.
        for i,method in enumerate(METHODS[:3]):
            values=groups[cell,.05,method].values['ratio']
            if values:
                box=ax.boxplot([values],positions=[i],widths=.6,showfliers=False,whis=(0,90),patch_artist=True);box['boxes'][0].set(facecolor=colors[i],alpha=.55)
                maximum=max(values);observed_max=max(observed_max,maximum)
                ax.scatter([i],[maximum],marker='D',s=36,facecolors='none',edgecolors=colors[i],zorder=4)
            else:ax.text(i,.1,'N/A',ha='center')
        ax.axhline(1,color='black',ls='--',lw=.8);ax.set_yscale('symlog',linthresh=.001)
        ax.set(title='Cell '+cell,xticks=range(3),xticklabels=['Original','Exact','Graph'],ylabel='Absolute error / raw radius',ylim=(0,1.2*max(1.,observed_max)))
    fig.suptitle(subtitle+'\nError/radius: IQR / median, min/P90; diamonds = observed maxima; zeros retained');save(fig,'04_error_radius')
    fig,axes=plt.subplots(1,3,figsize=(14,4.5),constrained_layout=True)
    for ax,field,label in zip(axes[:2],('wall_seconds','cpu_seconds'),('Whole-log wall seconds','Whole-log CPU seconds')):
        ax.boxplot([[r[field] for r in resource_rows if r['cell_id']==c] for c in 'ABCDEF'],labels=list('ABCDEF'),showfliers=False,whis=(0,90));ax.set(ylabel=label,xlabel='Cell')
    axes[2].bar(list('ABCDEF'),[max(r['process_peak_rss_bytes'] for r in resource_rows if r['cell_id']==c)/(1024**2) for c in 'ABCDEF'],color='#0072B2')
    axes[2].set(ylabel='Maximum worker process peak RSS (MiB)',xlabel='Cell; cumulative process high-water')
    fig.suptitle(subtitle+'\nActual resource measurements; RSS is not per-method allocation');save(fig,'05_resources')


def validate(input_dir,output,phase,make_figures=False):
    started=time.perf_counter();cpu=time.process_time();input_dir=Path(input_dir);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    config=read(ROOT/'configs/gate_C_frozen.json');seeds=read(ROOT/'configs/gate_C_seed_manifest.json')
    check(hashlib.sha256((ROOT/'configs/gate_C_frozen.json').read_bytes()).hexdigest()==CONFIG_HASH,'config hash')
    check(hashlib.sha256((ROOT/'configs/gate_C_seed_manifest.json').read_bytes()).hexdigest()==SEED_HASH,'seed hash')
    cells={c['cell_id']:c for c in config['cells']};entries=[e for e in seeds['runs'] if e['phase']==phase]
    n=1000 if phase=='confirmatory' else 2
    check(len(entries)==6*n and Counter(e['cell_id'] for e in entries)==dict.fromkeys('ABCDEF',n),'planned allocation')
    manifest=read(input_dir/'run_manifest.json') if (input_dir/'run_manifest.json').exists() else None
    if manifest:
        check(set(manifest['planned_run_ids'])=={e['run_id'] for e in entries},'manifest planned IDs')
        check(manifest['config_hash']==CONFIG_HASH and manifest['seed_manifest_hash']==SEED_HASH,'manifest input hash')
    groups={};checkpoint_index=[];resource_rows=[];count=0
    compressed=(input_dir/'run_checkpoints').exists()
    source_root=input_dir/('run_checkpoints' if compressed else 'runs')
    paths=set(source_root.glob('*/*.json.gz' if compressed else '*/*.json'))
    expected_paths={source_root/e['cell_id']/(f"{e['replicate']:04d}.json.gz" if compressed else f"{e['replicate']:04d}.json") for e in entries}
    check(paths==expected_paths,'all assigned checkpoints present, no extras')
    for number,e in enumerate(entries,1):
        path=source_root/e['cell_id']/(f"{e['replicate']:04d}.json.gz" if compressed else f"{e['replicate']:04d}.json")
        wrapper=read(path);payload=wrapper['payload'];cell=cells[e['cell_id']]
        check(wrapper['run_id']==e['run_id'] and payload['run_id']==e['run_id'],'checkpoint identity')
        check(digest(payload)==wrapper['payload_sha256'],'payload hash '+e['run_id'])
        if compressed:check(wrapper['input_sha256']==digest(e),'canonical input digest '+e['run_id'])
        if manifest:check(wrapper['fingerprint']==manifest['fingerprint'],'frozen checkpoint fingerprint')
        check(payload['phase']==phase and payload['seed_streams']==e['streams'],'payload phase/streams')
        check(payload['raw_N']==cell['design']['B']*cell['design']['n0'],'raw N')
        check(len(payload['timings'])==14,'14 method/level timings')
        families=defaultdict(list);expected=expected_candidates(cell)
        check(len(payload['records'])==len(expected)*14,'complete record allocation')
        for r in payload['records']:
            check(r['method'] in METHODS and r['nominal_delta'] in (.05,.1),'method/level membership')
            check(r['candidate_id'] in expected and r['family_size']==len(expected),'candidate membership')
            audit_record(r,e,cell,phase,payload['observed_data_sha256'])
            families[r['nominal_delta'],r['method']].append(r);count+=1
        check(len(families)==14,'complete families')
        for (alpha,method),family in families.items():
            check(len(family)==len(expected) and {r['candidate_id'] for r in family}==expected,'intact family')
            key=e['cell_id'],alpha,method
            if key not in groups:groups[key]=Accumulator(*key)
            groups[key].add(family)
        checkpoint_index.append(dict(run_id=e['run_id'],file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),payload_sha256=wrapper['payload_sha256']))
        resource_rows.append({k:payload[k] for k in ('run_id','cell_id','wall_seconds','cpu_seconds','process_peak_rss_bytes','raw_N','observed_reward_min','observed_reward_max','observed_rewards_outside_0_1')})
        if number%100==0:print(f'audited {number}/{len(entries)} complete logs',flush=True)
    check(count==1134000 if phase=='confirmatory' else count==2268,'all candidate records')
    summary=[g.finish(phase) for _,g in sorted(groups.items())]
    primary={(r['cell_id'],r['method']):r for r in summary if r['alpha']==.05 and (r['cell_id'],r['method']) in PRIMARY}
    check(set(primary)==set(PRIMARY),'exact17 primary comparisons')
    adjusted=holm({k:r['undercoverage_pvalue'] for k,r in primary.items()})
    for k,p in adjusted.items():primary[k]['undercoverage_holm_pvalue']=p;primary[k]['holm_declared_comparisons']=17
    reference=input_dir/('summary.json' if compressed else 'preflight_summary.json')
    compare_summary(summary,read(reference))
    marginal=[]
    for key,g in sorted(groups.items()):
        for candidate,c in sorted(g.marginal.items()):
            defined=c['applicable']==c['n'];wl,wh=wilson(c['hits'],c['n']) if defined else (None,None)
            marginal.append(dict(cell_id=g.cell,alpha=g.alpha,method=g.method,candidate_id=candidate,replications=c['n'],applicable=c['applicable'],issued=c['issued'],covered=c['hits'] if defined else None,coverage=c['hits']/c['n'] if defined else None,wilson_lo=wl,wilson_hi=wh,false_safe=c['false_safe'],false_violation=c['false_violation']))
    extras=[g.extras() for _,g in sorted(groups.items())]
    primary_rows=[]
    for key,r in sorted(primary.items()):
        exact=lower_exact(r['covered_families'],r['replications'],.95)
        primary_rows.append({**{k:r[k] for k in ('cell_id','method','covered_families','replications','family_coverage','wilson_lo','wilson_hi','undercoverage_pvalue','undercoverage_holm_pvalue')},'exact_p_numerator':str(exact.numerator),'exact_p_denominator':str(exact.denominator),'holm_reject_05':r['undercoverage_holm_pvalue']<=.05})
    invocations=[read(p) for p in sorted((input_dir/'invocations').glob('*.json'))]
    report=dict(status='PASS',phase=phase,checks=CHECKS,independent_logs=len(entries),candidate_records=count,summary_rows=len(summary),primary_tests=17,
                no_outcomes_generated=True,preflight_excluded_from_confirmatory=True,independent_aggregation_matches_frozen=True,
                code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),config_sha256=CONFIG_HASH,seed_manifest_sha256=SEED_HASH,
                input_directory=str(input_dir.resolve()),checkpoint_inventory_sha256=digest(checkpoint_index),
                numeric_comparison='exact discrete identities; floating summary tolerance rel5e-12 abs5e-13',
                memory_algorithm='one complete checkpoint plus array(double) numeric summaries; never all full candidate dictionaries',
                resource_convention='RSS is cumulative process high-water; individual worker peaks are not summed simultaneous RSS',
                invocations=invocations,wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,
                process_peak_rss_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)))
    write_json(output/'validation.json',report);write_json(output/'independent_summary.json',summary);write_csv(output/'independent_summary.csv',summary)
    write_json(output/'validated_checkpoint_hashes.json',checkpoint_index);write_csv(output/'primary_holm_diagnostics.csv',primary_rows)
    write_csv(output/'independent_marginal_coverage.csv',marginal);write_csv(output/'family_decisions_and_widths.csv',extras)
    write_csv(output/'whole_log_resources.csv',resource_rows)
    lines=['# Independent C-STAT methods validation','',f'**PASS ({phase})**: {len(entries):,} complete independent logs, {count:,} candidate records, 84 cell/method/level summaries, exactly 17 primary Holm comparisons. No outcomes generated by this script.','',
           f'All {CHECKS:,} checks passed. The independent aggregation matches every field of the frozen summary (discrete fields exactly, floating fields to relative 5e-12 / absolute 5e-13).','',
           'Checkpoint payload/input hashes, exact assigned IDs, seed streams, candidate families, paired observations, expected statuses, analytic truth, support intersections, coverage, errors and decisions were independently checked. Empty confidence intersections remain coverage failures. Point-only and F graph-inapplicable records have no fabricated intervals.','',
           'Primary uncertainty uses one whole log per family. Marginal candidate fractions are separately reported; they are not independent-log power estimates. Holm uses exactly the registered 17 tests; 90% diagnostics remain secondary. Nonrejection does not prove validity.','',
           '|Cell|Method|Covered / logs|Family coverage|Wilson 95%|Exact lower-tail p|Holm p|','|---|---|---:|---:|---|---:|---:|']
    for r in primary_rows:lines.append(f"|{r['cell_id']}|{r['method']}|{r['covered_families']}/{r['replications']}|{r['family_coverage']:.6g}|[{r['wilson_lo']:.6g}, {r['wilson_hi']:.6g}]|{r['undercoverage_pvalue']:.6g}|{r['undercoverage_holm_pvalue']:.6g}|")
    lines.extend(['','Additional family-level any-false-certification and any-detection events, Wilson descriptive uncertainty, candidate fractions, raw/support widths and error/radius quantiles are in `family_decisions_and_widths.csv`.','',f'Regeneration: `.venv/bin/python reports/gate_C_stat_audit/validate_confirmatory.py --input {input_dir} --output {output} --phase {phase} --figures`',''])
    (output/'methods_validation.md').write_text('\n'.join(lines))
    if make_figures:figures(output,groups,summary,resource_rows,invocations,phase)
    print(canonical({k:report[k] for k in ('status','phase','checks','independent_logs','candidate_records','wall_seconds','process_peak_rss_bytes')}),flush=True)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True);parser.add_argument('--output',required=True)
    parser.add_argument('--phase',choices=('preflight','confirmatory'),required=True)
    parser.add_argument('--figures',action='store_true')
    args=parser.parse_args();validate(args.input,args.output,args.phase,args.figures)
if __name__=='__main__':main()

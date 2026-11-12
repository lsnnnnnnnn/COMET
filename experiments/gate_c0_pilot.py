"""Predeclared CPU Gate C0 diagnostic; never selects methods from oracle truth."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import csv
import hashlib
import json
from pathlib import Path
import platform
from statistics import mean, median
import subprocess
import time

from comet.bounded_variance import certify_bounded_graph
from comet.certification import certify, _registered_scores, _validate_registered_log
from comet.informativeness import add_support_bounds
from comet.metrics import wilson
from comet.schema import SyntheticConfig
from comet.synthetic import generate_evaluation


def quantiles(values):
    ordered = sorted(values)
    def at(q):
        pos = q*(len(ordered)-1)
        low = int(pos)
        return ordered[low]+(ordered[min(low+1,len(ordered)-1)]-ordered[low])*(pos-low)
    return dict(min=ordered[0],median=at(.5),p90=at(.9),p95=at(.95),p99=at(.99),max=ordered[-1])


def dump_json(path, value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')


def dump_csv(path, rows):
    fields = sorted(set().union(*(row.keys() for row in rows)))
    with path.open('w',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _configuration(raw):
    raw = dict(raw)
    for key in ('e_by_context','mu_hat','q_probs','auditors'):
        raw[key] = tuple(raw[key])
    return SyntheticConfig(**raw)


def run_cell(cell, settings):
    """One cell, all methods/levels paired on each generated evaluation log."""
    config = _configuration(cell['synthetic'])
    records, data_summaries, timings = [], [], []
    for replicate in range(cell['replications']):
        seed = cell['base_seed']+replicate
        log, oracle = generate_evaluation(config,seed)
        _validate_registered_log(log)
        counts = Counter((r.context,r.observed_exposure_s,r.reward_y) for r in log.rows)
        raw_digest = hashlib.sha256()
        for r in log.rows:
            raw_digest.update(f'{r.unit_id},{r.context},{r.observed_exposure_s},{r.reward_y}\n'.encode())
        data_summaries.append(dict(cell_id=cell['cell_id'],replicate_id=replicate,seed=seed,
                                   raw_data_sha256=raw_digest.hexdigest(),
                                   observed_counts=[dict(context=x,exposure=s,reward=y,count=n)
                                                    for (x,s,y),n in sorted(counts.items())]))
        diagnostics = {}
        for candidate in log.family:
            scores = _registered_scores(log,candidate)
            weights = [candidate.q_vector[r.observed_exposure_s]/r.e_s_logged for r in log.rows]
            qs, tails = quantiles(weights), quantiles([abs(z) for z in scores])
            max_weight = max(weights)
            normalized = [w/max_weight for w in weights] if max_weight else []
            diagnostics[candidate.candidate_id] = {
                **{'observed_q_over_e_'+k:v for k,v in qs.items()},
                **{'abs_score_'+k:v for k,v in tails.items()},
                'score_empirical_p_moment_diagnostic':mean(abs(z)**cell['p'] for z in scores),
                'importance_ess_diagnostic':sum(normalized)**2/sum(w*w for w in normalized) if normalized else 0.,
                'raw_data_sha256':raw_digest.hexdigest()}
        for alpha in settings['alphas']:
            methods = []
            for rule in settings['mom_rules']:
                start = time.perf_counter()
                certificates = certify(log,alpha=alpha,p=cell['p'],mom_majority_rule=rule)
                timings.append(dict(cell_id=cell['cell_id'],replicate_id=replicate,alpha=alpha,
                                    method=rule,seconds=time.perf_counter()-start))
                methods.append((rule,certificates))
            start = time.perf_counter()
            variance_certificates = certify_bounded_graph(log,alpha=alpha)
            timings.append(dict(cell_id=cell['cell_id'],replicate_id=replicate,alpha=alpha,
                                method='bounded_graph_chebyshev',seconds=time.perf_counter()-start))
            methods.append(('bounded_graph_chebyshev',variance_certificates))
            # Support-only benchmark is justified by the same known reward range.
            # Its midpoint is merely a declared point prediction, not a fitted mean.
            trivial = []
            for candidate in log.family:
                mass = sum(candidate.h(r.context) for r in log.rows)/len(log.rows)
                low, high = -mass*config.reference,mass*(1-config.reference)
                trivial.append(dict(candidate_id=candidate.candidate_id,status='CERTIFIED',
                    estimate=(low+high)/2,lo=low,hi=high,stochastic_radius=(high-low)/2,
                    subgroup_mass=mass,reason='KNOWN_BOUNDED_OUTCOME_SUPPORT_ONLY',
                    nominal_delta=alpha,certified_level=1.0,raw_N=len(log.rows),retained_N=len(log.rows),
                    B=config.B,n0=config.n0,chi_max=config.chi,N_eff=len(log.rows)/config.chi,
                    nuisance_radius=0.,drift_radius=0.,coupling_failure_epsilon=0.))
            methods.append(('trivial_support',trivial))
            # All certificates above are complete before any oracle value is joined.
            for method, certificates in methods:
                for certificate in certificates:
                    candidate = next(c for c in log.family if c.candidate_id==certificate['candidate_id'])
                    mass = sum(candidate.h(r.context) for r in log.rows)/len(log.rows)
                    support = (-mass*config.reference,mass*(1-config.reference))
                    augmented = add_support_bounds(certificate,*support)
                    truth = oracle.moments[candidate.candidate_id]
                    raw_covered = (certificate['lo'] <= truth <= certificate['hi']) if certificate['lo'] is not None else False
                    issued = augmented['decision_issuable']
                    threshold = settings['constraint_per_subgroup_mass']*mass
                    safe = issued and augmented['clipped_hi'] <= threshold
                    unsafe = issued and augmented['clipped_lo'] > threshold
                    row = dict(cell_id=cell['cell_id'],replicate_id=replicate,seed=seed,
                        method=method,nominal_delta=alpha,nominal_level=1-alpha,
                        candidate_id=candidate.candidate_id,family_size=len(log.family),
                        status=certificate['status'],reason=certificate['reason'],
                        cell_moment_order=cell['p'],bound_moment_order=certificate.get('p_declared'),
                        exact_oracle_truth=truth,raw_covered=raw_covered,issued=issued,
                        covered=issued and augmented['clipped_lo']<=truth<=augmented['clipped_hi'],
                        absolute_error=abs(certificate['estimate']-truth) if certificate['estimate'] is not None else None,
                        safety_threshold=threshold,safe_certified=safe,unsafe_certified=unsafe,
                        decision_unresolved=not (safe or unsafe),false_safe=safe and truth>threshold,
                        subgroup_mass=mass,discarded_rows=0,discarded_blocks=0,
                        nu_p_source=certificate.get('nu_p_source'),
                        variance_source=certificate.get('variance_source'),
                        proof_scope='registered_exogenous_independent_bounded_reward_model')
                    for key in ('raw_estimate','raw_radius','raw_lo','raw_hi','feasible_lo','feasible_hi',
                                'clipped_lo','clipped_hi','clipped_width','feasible_diameter','width_fraction',
                                'informativeness_fraction','is_empty','is_full_range','is_nontrivial'):
                        row[key] = augmented[key]
                    for key in ('raw_N','retained_N','N_eff','B','n0','K','L_min','chi_max','nu_p','C_p_used',
                                'eta','binomial_familywise_failure_bound','variance_bound','delta_stat',
                                'nuisance_radius','drift_radius','coupling_failure_epsilon','graph_nodes','graph_edges'):
                        row[key] = certificate.get(key)
                    group_sizes = certificate.get('group_sizes',[])
                    row['L_max'] = max(group_sizes) if group_sizes else None
                    row.update(diagnostics[candidate.candidate_id])
                    records.append(row)
    return records,data_summaries,timings


def summarize(records):
    summaries = []
    def med(values):
        return median(values) if values else None
    keys = sorted({(r['cell_id'],r['nominal_delta'],r['method']) for r in records})
    for cell,alpha,method in keys:
        rows = [r for r in records if (r['cell_id'],r['nominal_delta'],r['method'])==(cell,alpha,method)]
        groups = [[r for r in rows if r['replicate_id']==rep] for rep in sorted({r['replicate_id'] for r in rows})]
        n = len(groups)
        issued = sum(all(r['issued'] for r in group) for group in groups)
        hits = sum(all(r['covered'] for r in group) for group in groups)
        raw_hits = sum(all(r['raw_covered'] for r in group) for group in groups)
        nontrivial_all = sum(all(r['is_nontrivial'] for r in group) for group in groups)
        nontrivial_some = sum(any(r['is_nontrivial'] for r in group) for group in groups)
        wl,wh = wilson(hits,issued)
        widths = [r['width_fraction'] for r in rows if r['width_fraction'] is not None]
        radii = [r['raw_radius'] for r in rows if r['raw_radius'] is not None]
        widthq = quantiles(widths) if widths else {}
        summaries.append(dict(cell_id=cell,alpha=alpha,method=method,replications=n,
            raw_family_coverage=raw_hits/n,issued_families=issued,covered_families=hits,
            issued_and_covers_rate=hits/n,coverage_given_issued=hits/issued if issued else None,
            wilson_lo=wl,wilson_hi=wh,unresolved_or_abstention_fraction=1-issued/n,
            familywise_nontrivial_some=nontrivial_some/n,familywise_nontrivial_all=nontrivial_all/n,
            marginal_nontrivial_rate=mean(r['is_nontrivial'] for r in rows),
            median_width_fraction=widthq.get('median'),p90_width_fraction=widthq.get('p90'),
            median_informativeness=med([r['informativeness_fraction'] for r in rows
                                        if r['informativeness_fraction'] is not None]),
            median_raw_radius=median(radii) if radii else None,
            median_radius_over_diameter=med([r['raw_radius']/r['feasible_diameter'] for r in rows
                                             if r['raw_radius'] is not None and r['feasible_diameter']>0]),
            median_absolute_error=med([r['absolute_error'] for r in rows if r['absolute_error'] is not None]),
            safe_certifications=sum(r['safe_certified'] for r in rows),
            unsafe_certifications=sum(r['unsafe_certified'] for r in rows),
            constraint_unresolved_fraction=mean(r['decision_unresolved'] for r in rows),
            false_safe_count=sum(r['false_safe'] for r in rows),
            false_safe_family_count=sum(any(r['false_safe'] for r in group) for group in groups),
            N=rows[0]['raw_N'],N_eff=rows[0]['N_eff'],chi=rows[0]['chi_max'],
            family_size=rows[0]['family_size'],p=rows[0]['cell_moment_order'],
            K=rows[0]['K'],L_min=rows[0]['L_min']))
    return summaries


def render_plot(summaries, output):
    import os
    os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[1]/'build/mpl'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    styles = {'conservative_hoeffding':('#777777','o','MOM: old K'),
              'exact_binomial':('#0072B2','s','MOM: exact binomial'),
              'bounded_graph_chebyshev':('#009E73','^','Graph Chebyshev'),
              'trivial_support':('#D55E00','x','Support only')}
    fig,axes = plt.subplots(1,2,figsize=(12,4.6),constrained_layout=True)
    cells = list(dict.fromkeys(r['cell_id'] for r in summaries))
    for method,(color,marker,label) in styles.items():
        rows = [r for r in summaries if r['alpha']==.05 and r['method']==method]
        positions=[cells.index(r['cell_id']) for r in rows]
        axes[0].plot(positions,[r['median_width_fraction'] for r in rows],
                     marker=marker,color=color,label=label,lw=1)
        axes[1].scatter([r['N_eff'] for r in rows],[r['median_informativeness'] for r in rows],
                        marker=marker,color=color,label=label,s=55,alpha=.8)
    axes[0].set(xticks=range(len(cells)),xticklabels=[c.replace('_family16','').replace('_32768','\n32k').replace('_8192','\n8k') for c in cells],
                ylabel='Median clipped width / feasible diameter',ylim=(-.03,1.04),title='Validity and usefulness are separate')
    axes[0].tick_params(axis='x',labelrotation=35,labelsize=8)
    axes[1].set(xscale='log',xlabel='Effective sample size N / chi',ylabel='Median informativeness: 1 − width fraction',
                ylim=(-.03,1.04),title='Sample / graph cost vs informativeness')
    for ax in axes:
        ax.grid(alpha=.2)
    axes[1].legend(fontsize=8,loc='lower right')
    fig.suptitle('Gate C0: 95% family intervals, 30 paired debugging replications per cell',fontsize=11)
    fig.savefig(output/'informativeness.png',dpi=200)
    fig.savefig(output/'informativeness.pdf',metadata={'CreationDate':None,'ModDate':None})
    plt.close(fig)


def run(config_path, output, workers=1):
    settings = json.loads(Path(config_path).read_text())
    total = sum(c['replications'] for c in settings['cells'])
    if total>400 or total!=settings['planned_new_replication_cells']:
        raise ValueError('Gate C0 replication budget mismatch')
    output = Path(output); output.mkdir(parents=True,exist_ok=True)
    started = time.perf_counter()
    if workers==1:
        outputs = [run_cell(cell,settings) for cell in settings['cells']]
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures=[pool.submit(run_cell,cell,settings) for cell in settings['cells']]
            outputs=[]
            for cell,future in zip(settings['cells'],futures):
                outputs.append(future.result())
                print(f"completed {cell['cell_id']}: {cell['replications']} replications",flush=True)
    records=[r for data,_,_ in outputs for r in data]
    data_summaries=[r for _,data,_ in outputs for r in data]
    timings=[r for _,_,data in outputs for r in data]
    summaries=summarize(records)
    dump_csv(output/'pilot.csv',records)
    dump_json(output/'pilot_summary.json',summaries)
    dump_csv(output/'pilot_summary.csv',summaries)
    dump_json(output/'data_summaries.json',data_summaries)
    dump_csv(output/'timings.csv',timings)
    dump_json(output/'preregistered_config.json',settings)
    lines=['# Gate C0 pilot — coverage AND informativeness', '',
           f'{total} predeclared DGP replication-cells; both confidence levels and all four methods reuse each log. '
           'CPU-only debugging, not final empirical coverage evidence.', '',
           '| Cell | Level | Method | Family hits / issued | Wilson 95% | Median / p90 width fraction | Any / all family nontrivial | Abstention / constraint unresolved | False-safe |',
           '|---|---|---|---:|---|---|---|---:|---:|']
    for r in summaries:
        def fmt(value):
            return 'undefined' if value is None else f'{value:.3f}'
        lines.append(f"| {r['cell_id']} | {1-r['alpha']:.0%} | {r['method']} | {r['covered_families']}/{r['issued_families']} | "
                     f"[{fmt(r['wilson_lo'])}, {fmt(r['wilson_hi'])}] | {fmt(r['median_width_fraction'])} / {fmt(r['p90_width_fraction'])} | "
                     f"{r['familywise_nontrivial_some']:.0%} / {r['familywise_nontrivial_all']:.0%} | "
                     f"{r['unresolved_or_abstention_fraction']:.0%} / {r['constraint_unresolved_fraction']:.0%} | {r['false_safe_count']} |")
    lines+=['','Full-range intervals remain in every coverage denominator. Width fraction 1 means vacuous. '
            'Each Wilson denominator is independent replications, not candidate rows. No pooling across '
            'candidates or methods for uncertainty. Safety means the predeclared fixed-design numerator '
            'is at most 0.2 times subgroup mass, not future deployment safety. No outcome-driven selection '
            'of the best method is certified. The p=1.5 stress cell has bounded Y; its finite variance is '
            'known separately, so graph Chebyshev remains applicable.','']
    (output/'pilot_table.md').write_text('\n'.join(lines))
    render_plot(summaries,output)
    root=Path(__file__).resolve().parents[1]
    source={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ('comet','experiments') for p in sorted((root/folder).glob('*.py'))}
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    dump_json(output/'run_manifest.json',dict(
        scope='Gate C0 only; paired debugging, not final coverage evidence',
        new_replication_cells=total,confidence_evaluations=2*total,workers=workers,
        elapsed_seconds=time.perf_counter()-started,python=platform.python_version(),
        git_head=head,source_sha256=source,
        config_sha256=hashlib.sha256(Path(config_path).read_bytes()).hexdigest(),
        seed_manifest=[dict(cell_id=c['cell_id'],seeds=list(range(c['base_seed'],c['base_seed']+c['replications']))) for c in settings['cells']],
        oracle_use='joined after all method certificates; exact conditional expectation',
        data_downloads=0,gpu_used=False))
    return summaries


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default='configs/gate_C0_pilot.json')
    parser.add_argument('--output',default='results/gate_C0')
    parser.add_argument('--workers',type=int,choices=(1,2),default=2)
    args=parser.parse_args()
    run(args.config,args.output,args.workers)


if __name__=='__main__':
    main()

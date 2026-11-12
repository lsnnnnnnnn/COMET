"""Outcome-free audit of the frozen Gate C design and known radii."""
import csv
import hashlib
import json
from pathlib import Path

from comet.gate_c_contract import cell_from_dict, known_centered_envelope, pareto_absolute_moment
from comet.gate_c_statistics import quantile
from comet.bounded_variance import row_variance_envelope
from comet.conflict_graph import clique_graph, greedy_coloring, is_proper_coloring
from comet.robust_mean import required_groups, exact_binomial_groups, partition_blocks, mom_radius


def audit(config_path, output):
    config=json.loads(Path(config_path).read_text());output=Path(output);output.mkdir(parents=True,exist_ok=True)
    records=[]
    for raw in config['cells']:
        cell=cell_from_dict(raw);d=cell.design
        graph=clique_graph(d.n0,d.chi); colors=greedy_coloring(graph)
        assert is_proper_coloring(graph,colors) and max(colors)+1==d.chi
        clusters=d.n0//d.chi
        for candidate in d.family:
            ratios=[q/e for e1 in d.e_by_context for q,e in zip(candidate.q_vector,(1-e1,e1))]
            mass=sum(candidate.h(c%2) for c in range(clusters))/clusters
            envelopes=[known_centered_envelope(cell,candidate.q_vector,(1-e1,e1),cell.p) for e1 in d.e_by_context]
            nu=max(envelopes)**(1/cell.p)
            for alpha in config['alphas']:
                for method in ('orig_mom','exact_binomial_mom','bounded_graph_chebyshev'):
                    row=dict(cell_id=cell.cell_id,candidate_id=candidate.candidate_id,method=method,
                             alpha=alpha,N=d.B*d.n0,B=d.B,n0=d.n0,chi=d.chi,N_eff=d.B*clusters,
                             family_size=len(d.family),p=cell.p,subgroup_mass=mass,
                             feasible_diameter=mass,min_logging_e=min(min(e,1-e) for e in d.e_by_context),
                             q_over_e_quantile_population='equal_weight_context_exposure_states_not_observed_logs',
                             **{f'design_q_over_e_{label}':quantile(ratios,q) for label,q in
                                [('min',0),('median',.5),('p95',.95),('p99',.99),('max',1)]},
                             conditional_centered_p_envelope=max(envelopes),known_nu_p=nu,
                             noise_absolute_p_moment=None if cell.outcome_family=='bernoulli' else
                                pareto_absolute_moment(cell.tail_alpha,cell.tail_scale,cell.p),
                             K=None,L_min=None,L_max=None,variance_bound=None,raw_radius=None,
                             method_applicable=True,status='DESIGN_ASSUMPTIONS_VERIFIED_NOT_AN_OUTCOME_CERTIFICATE')
                    if method=='bounded_graph_chebyshev':
                        if cell.outcome_family!='bernoulli':
                            row.update(method_applicable=False,status='NOT_APPLICABLE')
                        else:
                            mean_v=sum(row_variance_envelope(candidate.q_vector,
                                (1-d.e_by_context[c%2],d.e_by_context[c%2]),candidate.h(c%2))
                                for c in range(clusters))/clusters
                            v=d.chi*mean_v/(d.B*d.n0)
                            row.update(variance_bound=v,raw_radius=(len(d.family)*v/alpha)**.5)
                    else:
                        K=required_groups(len(d.family),alpha) if method=='orig_mom' else exact_binomial_groups(len(d.family),alpha,d.B)['K']
                        groups=partition_blocks(d.B,K);L=min(map(len,groups))
                        row.update(K=K,L_min=L,L_max=max(map(len,groups)),raw_radius=mom_radius(cell.p,nu,d.chi,d.n0,L))
                    records.append(row)
    path=output/'design_only_diagnostics.csv'
    with path.open('w',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=sorted(records[0]));w.writeheader();w.writerows(records)
    manifest=dict(config_sha256=hashlib.sha256(Path(config_path).read_bytes()).hexdigest(),
                  new_outcomes_generated=0,candidate_level_comparisons=len(records),
                  all_primary_support_positive=all(r['min_logging_e']>0 for r in records),
                  all_graph_colorings_verified=True,source='pre_outcome_design_and_proved_known_envelopes',
                  forbidden_inputs=['outcomes','oracle_true_targets','estimated_tail_scales'])
    (output/'design_only_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps(manifest,sort_keys=True))
    return records


if __name__=='__main__':
    audit('configs/gate_C_frozen.json','results/gate_C/preflight')

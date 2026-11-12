import json

from experiments.gate_c0_pilot import run, run_cell, summarize


def fixture_config():
    return dict(planned_new_replication_cells=2,alphas=[.05,.1],
                mom_rules=['conservative_hoeffding','exact_binomial'],constraint_per_subgroup_mass=.2,
                cells=[dict(cell_id='deterministic_test',replications=2,base_seed=71,p=2,
                            synthetic=dict(B=128,n0=8,chi=1,e_by_context=[.5,.5],mu_hat=[.5,.5],
                                           reference=.25,q_probs=[.5],auditors=['all']))])


def test_pilot_scientific_outputs_and_plots_reproduce(tmp_path):
    settings=fixture_config()
    config=tmp_path/'config.json'; config.write_text(json.dumps(settings))
    run(config,tmp_path/'one',workers=1)
    run(config,tmp_path/'two',workers=1)
    for name in ('pilot.csv','pilot_summary.json','pilot_summary.csv','data_summaries.json',
                 'preregistered_config.json','pilot_table.md','informativeness.png','informativeness.pdf'):
        assert (tmp_path/'one'/name).read_bytes()==(tmp_path/'two'/name).read_bytes(),name
    # Runtime and manifest elapsed time are intentionally excluded from equality.


def test_unissued_intervals_are_not_assigned_coverage_one():
    settings=fixture_config()
    settings['cells'][0]['synthetic']['B']=2
    records,_,_=run_cell(settings['cells'][0],settings)
    rows=[r for r in summarize(records) if r['method'] in settings['mom_rules']]
    assert all(r['issued_families']==0 and r['coverage_given_issued'] is None for r in rows)
    assert all(r['issued_and_covers_rate']==0 and r['unresolved_or_abstention_fraction']==1 for r in rows)
    assert all(r['median_raw_radius'] is None for r in rows)

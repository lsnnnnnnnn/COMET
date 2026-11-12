"""Deterministic theorem/status invariants, not empirical coverage thresholds."""
import ast
from dataclasses import replace
from pathlib import Path

import pytest

from comet.bounded_variance import certify_bounded_graph
from comet.certification import certify
from comet.dr_scores import dr_score
from comet.gate_c_contract import GateCCell, STREAM_NAMES
from comet.gate_c_methods import (METHODS, POINT_METHODS, certify_methods,
                                  constraint_decision, evaluate_method)
from comet.gate_c_simulation import generate_evaluation
from comet.gate_c_truth import exact_targets
from comet.schema import SyntheticConfig


def fixture(outcome='bernoulli', stable=True, **design_changes):
    design = replace(SyntheticConfig(B=128,n0=8,chi=2), **design_changes)
    cell = GateCCell('A',design,p=1.5 if outcome=='symmetric_pareto' else 2.,
                     outcome_family=outcome,stable_targets=stable)
    streams = {name:71+index for index,name in enumerate(STREAM_NAMES)}
    return cell,generate_evaluation(cell,streams,'unit-fixture-A')


@pytest.mark.parametrize('alpha',[.05,.1])
def test_bounded_methods_reuse_c0_theorem_numeric_answers(alpha):
    cell,log = fixture()
    comparators = {
        'orig_mom':certify(log,alpha,p=cell.p),
        'exact_binomial_mom':certify(log,alpha,p=cell.p,mom_majority_rule='exact_binomial'),
        'bounded_graph_chebyshev':certify_bounded_graph(log,alpha),
    }
    for method,baseline in comparators.items():
        actual = evaluate_method(method,log,cell,alpha)
        for old,new in zip(baseline,actual):
            assert new['status']=='CERTIFIED'
            assert new['estimate']==pytest.approx(old['estimate'],abs=1e-14)
            assert new['raw_radius']==pytest.approx(old['stochastic_radius'],abs=1e-14)
            assert new['chi_max']==old['chi_max']==cell.design.chi
            assert new['nuisance_radius']==new['drift_radius']==new['coupling_failure_epsilon']==0
            assert new['family_size']==len(cell.design.family)
            assert new['raw_N']==new['retained_N']==len(log.rows)


def test_pareto_has_only_finite_p_statistical_certificates():
    cell,log = fixture('symmetric_pareto')
    records = certify_methods(log,cell)
    for row in records:
        if row['method']=='bounded_graph_chebyshev':
            assert row['status']=='NOT_APPLICABLE'
            assert row['raw_lo'] is row['raw_hi'] is row['raw_radius'] is None
            assert not row['certificate_applicable']
        elif row['method'] in POINT_METHODS:
            assert row['status']=='POINT_ONLY'
            assert row['estimate'] is not None and row['raw_lo'] is None
            assert row['certified_level'] is None
        else:
            assert row['status']=='CERTIFIED'
            assert not row['target_range_is_outcome_support']
            assert row['target_range_source']=='declared_conditional_response_mean_class_[0,1]'
    assert len(records)==len(METHODS)*len(log.family)


def test_apparent_bounded_sample_cannot_change_heavy_tail_method_applicability():
    cell,log = fixture('symmetric_pareto')
    # Structural validation permits this possible-looking finite realization;
    # it cannot justify a bounded outcome theorem for the declared heavy law.
    bounded_looking=replace(log,rows=tuple(replace(r,reward_y=.5) for r in log.rows))
    assert all(r['status']=='NOT_APPLICABLE' for r in
               evaluate_method('bounded_graph_chebyshev',bounded_looking,cell))


def test_point_baselines_have_no_intervals_or_certified_decisions():
    cell,log=fixture()
    records=certify_methods(log,cell,methods=POINT_METHODS)
    for row in records:
        assert row['status']=='POINT_ONLY' and row['decision']=='POINT_ONLY'
        assert row['estimate'] is not None and row['raw_estimate']==row['estimate']
        assert row['raw_lo'] is row['raw_hi'] is row['clipped_lo'] is row['width_fraction'] is None
        assert not row['certificate_applicable'] and not row['decision_issuable']
    for row in records:
        if row['method']=='dm':
            assert row['estimate']==pytest.approx(.25*row['subgroup_mass'])


def test_unbiased_exact_e_dr_and_ips_with_arbitrary_frozen_nuisance():
    for q in ((.2,.8),(.9,.1)):
        for muhat in ((0.,1.),(.8,.1),(.5,.5)):
            e,mu=(.75,.25),(.3,.8)
            expected_dr=expected_ips=0.
            for s in (0,1):
                for y in (0,1):
                    probability=e[s]*(mu[s] if y else 1-mu[s])
                    expected_dr+=probability*dr_score(y,s,q,e,muhat,.4,.25)
                    expected_ips+=probability*.4*(q[s]/e[s]*y-.25)
            truth=.4*(sum(qs*mus for qs,mus in zip(q,mu))-.25)
            assert expected_dr==pytest.approx(truth,abs=1e-15)
            assert expected_ips==pytest.approx(truth,abs=1e-15)


def test_graph_variance_has_actual_family_bonferroni_and_verified_chi():
    cell,log=fixture(chi=4,n0=16)
    for row,candidate in zip(evaluate_method('bounded_graph_chebyshev',log,cell),cell.design.family):
        N=len(log.rows)
        v=sum(candidate.h(r.context)**2*sum(q*q/e for q,e in zip(candidate.q_vector,r.e_vector))
              for r in log.rows)
        assert row['variance_bound']==pytest.approx(4*v/N**2)
        assert row['raw_radius']**2==pytest.approx(len(log.family)*row['variance_bound']/.05)
        assert row['graph_edges']==cell.design.B*cell.design.n0*(cell.design.chi-1)//2


def test_all_blocks_retained_with_unequal_exact_groups():
    cell,log=fixture(B=129)
    for row in evaluate_method('exact_binomial_mom',log,cell):
        assert sum(row['group_sizes'])==129
        assert max(row['group_sizes'])-min(row['group_sizes'])==1
        assert row['L_min']>=2 and row['K']%2==1
        assert row['binomial_familywise_failure_bound']<=.05


def test_infeasible_k_abstains_without_using_partial_block_set():
    cell,log=fixture(B=2)
    for method in ('orig_mom','exact_binomial_mom'):
        rows=evaluate_method(method,log,cell)
        assert all(r['status']=='NOT_CERTIFIABLE' and r['estimate'] is None for r in rows)
        assert all(r['decision']=='ABSTAIN' and r['subgroup_mass']>0 for r in rows)


def test_drifting_exogenous_targets_refuse_mom_but_permit_graph_mean():
    cell,log=fixture(stable=False)
    for method in ('orig_mom','exact_binomial_mom'):
        rows=evaluate_method(method,log,cell)
        assert all(r['status']=='NOT_APPLICABLE' and r['raw_lo'] is None for r in rows)
    assert all(r['status']=='CERTIFIED' for r in evaluate_method('bounded_graph_chebyshev',log,cell))


@pytest.mark.parametrize('model',[
    'permanent_cross_block_shock','graph_missing_edges','outcome_selected_shortest_interval',
    'outcome_selected_q_h','mutually_trained_cross_fit','unknown_conditional_p_moment'])
def test_declared_assumption_violations_never_receive_an_interval(model):
    cell,log=fixture()
    rows=certify_methods(replace(log,proof_model=model),cell)
    assert all(r['status']=='UNVERIFIED_ASSUMPTION' and r['raw_lo'] is None for r in rows)


@pytest.mark.parametrize('field,value',[
    ('e_s_logged',.123),('mu_hat',(.1,.9)),('features_available_at',1),('reward_y',2.)])
def test_observable_propensity_nuisance_timing_reward_violations_refuse(field,value):
    cell,log=fixture()
    bad=replace(log,rows=(replace(log.rows[0],**{field:value}),)+log.rows[1:])
    assert all(r['status']!='CERTIFIED' and r['raw_lo'] is None for r in certify_methods(bad,cell))


def test_zero_support_and_infinite_declared_p_moment_are_not_certified():
    cell,log=fixture()
    zero=replace(cell,design=replace(cell.design,e_by_context=(0.,.4)))
    assert all(r['status']!='CERTIFIED' and r['raw_lo'] is None for r in certify_methods(log,zero))
    heavy,heavylog=fixture('symmetric_pareto')
    bad=replace(heavy,p=heavy.tail_alpha)
    assert all(r['status']=='NOT_APPLICABLE' and r['raw_lo'] is None for r in certify_methods(heavylog,bad))


def test_extreme_positive_overlap_can_be_valid_and_vacuous():
    cell,log=fixture(e_by_context=(1e-8,2e-8))
    for method in ('orig_mom','exact_binomial_mom','bounded_graph_chebyshev'):
        for row in evaluate_method(method,log,cell):
            assert row['status']=='CERTIFIED' and row['is_full_range']
            assert row['decision']=='ABSTAIN' and row['width_fraction']==1


def test_constraint_threshold_boundaries_and_empty_refusal():
    base=dict(status='CERTIFIED',decision_issuable=True,clipped_lo=.1,clipped_hi=.2)
    assert constraint_decision(base,.2)=='CERTIFIED_SAFE'
    assert constraint_decision(base,.1)=='ABSTAIN'
    assert constraint_decision(base,.099)=='CERTIFIED_VIOLATION'
    assert constraint_decision(dict(base,decision_issuable=False),.2)=='ABSTAIN'
    assert constraint_decision(dict(base,status='POINT_ONLY'),.2)=='POINT_ONLY'


def test_no_oracle_import_in_certifier_transitive_code():
    root=Path(__file__).resolve().parents[1]/'comet'
    todo=['gate_c_methods']; visited=set()
    while todo:
        module=todo.pop()
        if module in visited:
            continue
        visited.add(module)
        assert module not in ('gate_c_truth','gate_c_simulation','truth','synthetic')
        tree=ast.parse((root/(module+'.py')).read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom) and node.level==1 and node.module:
                todo.append(node.module)
    assert 'gate_c_contract' in visited


def test_known_target_range_contains_all_analytical_targets_without_using_them():
    for outcome in ('bernoulli','symmetric_pareto'):
        cell,log=fixture(outcome)
        rows=evaluate_method('full_feasible_range',log,cell)
        # This oracle access occurs only after all method records exist.
        truths=exact_targets(cell)
        assert all(r['raw_lo']<=truths[r['candidate_id']]<=r['raw_hi'] for r in rows)
        assert all(r['width_fraction']==1 and not r['is_nontrivial'] for r in rows)


def test_tail_diagnostics_are_recorded_but_cannot_tune_radius(monkeypatch):
    import comet.gate_c_methods as methods
    cell,log=fixture('symmetric_pareto')
    before=evaluate_method('exact_binomial_mom',log,cell)
    assert before[0]['known_noise_p_moment_upper_bound']==pytest.approx(7*.1**1.5)
    assert before[0]['q_over_e_design_equal_context_state_quantiles']['max']>1
    assert not before[0]['diagnostics_enter_certified_radius']
    assert 'p99' in before[0]['absolute_dr_score_quantiles']
    monkeypatch.setattr(methods,'_diagnostics',lambda *args:{'diagnostic_mutation_test':True})
    after=evaluate_method('exact_binomial_mom',log,cell)
    for original,mutated in zip(before,after):
        for key in ('estimate','raw_radius','K','nu_p','status','raw_lo','raw_hi'):
            assert original[key]==mutated[key]

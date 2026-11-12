"""Deterministic checks of the variance proof and its supported API."""

from dataclasses import replace
from itertools import product
from math import sqrt

import pytest

from comet.bounded_variance import (certify_bounded_graph, graph_variance_bound,
                                    row_variance_envelope)
from comet.conflict_graph import clique_graph
from comet.dr_scores import dr_score
from comet.exposure import marginalize_exposure, plackett_luce_slates
from comet.schema import CertificationError, SupportError, SyntheticConfig
from comet.synthetic import generate_evaluation


def enumerate_score(q, e, actual_mu, fitted_mu, h=1.0, reference=0.0):
    return [(e[s]*(actual_mu[s] if y else 1-actual_mu[s]),
             dr_score(y, s, q, e, fitted_mu, h, reference))
            for s in range(len(q)) for y in (0, 1)]


@pytest.mark.parametrize('fitted_mu', [(0, 0), (1, 1), (0.9, 0.05)])
@pytest.mark.parametrize('h', [-0.7, 0, 1])
def test_exact_e_mean_and_variance_with_wrong_fixed_regression(fitted_mu, h):
    q, e, mu, f = (0.2, 0.8), (0.7, 0.3), (0.1, 0.9), 0.2
    states = enumerate_score(q, e, mu, fitted_mu, h, f)
    expectation = sum(prob*z for prob, z in states)
    variance = sum(prob*(z-expectation)**2 for prob, z in states)
    assert expectation == pytest.approx(h*(sum(qs*mus for qs,mus in zip(q,mu))-f))
    assert variance <= row_variance_envelope(q, e, h)+1e-12


def test_variance_support_failure_and_common_zero():
    with pytest.raises(SupportError, match='NONIDENTIFIABLE_TARGET_SUPPORT'):
        row_variance_envelope((0.5, 0.5), (1, 0))
    assert row_variance_envelope((1, 0), (1, 0)) == 1
    with pytest.raises(CertificationError, match='PROBABILITIES_DO_NOT_SUM'):
        row_variance_envelope((0.5, 0.6), (0.5, 0.5))
    with pytest.raises(CertificationError, match='BOUNDED_PREACTION'):
        row_variance_envelope((0.5, 0.5), (0.5, 0.5), h=2)


def test_clique_and_edgeless_variance_fixtures_and_actual_color_count():
    assert graph_variance_bound([1]*4, clique_graph(4, 1)) == (4, 1)
    assert graph_variance_bound([1]*4, clique_graph(4, 4)) == (16, 4)
    assert sum((4*r)**2/2 for r in (-1,1)) == 16
    independent_variance = sum(sum(r)**2/16 for r in product((-1,1), repeat=4))
    assert independent_variance == 4
    with pytest.raises(CertificationError, match='INVALID_UNDIRECTED_GRAPH'):
        graph_variance_bound([1, 1], ((1,), ()))
    with pytest.raises(CertificationError, match='INVALID_GRAPH_VARIANCE_INPUT'):
        graph_variance_bound([1], clique_graph(4, 1))


def test_missing_edges_are_an_assumption_violation_not_observationally_detectable():
    # Declaring independent copies when they are identical makes the stochastic
    # premise false. Arithmetic on the edge list cannot discover that premise.
    claimed, _ = graph_variance_bound([1]*4, clique_graph(4, 1))
    assert claimed < 16  # actual variance of the four-copy Rademacher sum
    import inspect
    assert 'graph' not in inspect.signature(certify_bounded_graph).parameters


def test_graph_variance_rejects_an_unverified_smaller_coloring(monkeypatch):
    monkeypatch.setattr('comet.bounded_variance.greedy_coloring', lambda _: (0,0,0,0))
    with pytest.raises(CertificationError, match='INVALID_COLORING'):
        graph_variance_bound([1]*4, clique_graph(4,4))


def test_sample_mean_targets_heterogeneous_conditional_means_without_mom_drift():
    # The theorem permits nonidentical row means; runtime remains narrower.
    mu0, mu1 = 0.1, 0.9
    states = [((mu0 if a else 1-mu0)*(mu1 if b else 1-mu1), (a+b)/2)
              for a,b in product((0,1), repeat=2)]
    target = (mu0+mu1)/2
    assert sum(prob*z for prob,z in states) == pytest.approx(target)
    actual_variance = sum(prob*(z-target)**2 for prob,z in states)
    block_bound0, _ = graph_variance_bound([1], clique_graph(1,1))
    block_bound1, _ = graph_variance_bound([1], clique_graph(1,1))
    assert actual_variance <= (block_bound0+block_bound1)/4


def test_joint_slate_exposure_probabilities_enter_variance_on_same_space():
    joint_e = plackett_luce_slates((1,2,3),2)
    joint_q = plackett_luce_slates((3,2,1),2)
    mapping = lambda slate: (int(0 in slate), int(1 in slate))
    e_map, q_map = marginalize_exposure(joint_e,mapping), marginalize_exposure(joint_q,mapping)
    states = sorted(set(e_map)|set(q_map))
    e, q = tuple(e_map.get(s,0) for s in states), tuple(q_map.get(s,0) for s in states)
    assert sum(e) == pytest.approx(1) and sum(q) == pytest.approx(1)
    assert row_variance_envelope(q,e) == pytest.approx(sum(qs*qs/es for qs,es in zip(q,e)))
    assert e_map[(1,1)] == pytest.approx(1/15+1/12)


def test_clipped_bias_product_and_variance_are_proved_not_ignored():
    e, q, mu, fitted = (0.8,0.2), (0.2,0.8), (0.1,0.9), (0.7,0.2)
    c, f = 1.5, 0.3
    states = [(e[s]*(mu[s] if y else 1-mu[s]),
               sum(qs*ms for qs,ms in zip(q,fitted))-f
               +min(q[s]/e[s],c)*(y-fitted[s]))
              for s in (0,1) for y in (0,1)]
    target = sum(qs*ms for qs,ms in zip(q,mu))-f
    expectation = sum(prob*z for prob,z in states)
    bias = sum(max(q[s]-c*e[s],0)*(fitted[s]-mu[s]) for s in (0,1))
    bias_bound = sum(max(qs-c*es,0) for qs,es in zip(q,e))
    variance_bound = sum(es*min(qs/es,c)**2 for qs,es in zip(q,e))
    variance = sum(prob*(z-expectation)**2 for prob,z in states)
    assert target == pytest.approx(.44)
    assert expectation == pytest.approx(.09)
    assert expectation-target == pytest.approx(bias) == pytest.approx(-.35)
    assert abs(bias) <= bias_bound == pytest.approx(.5)
    assert variance <= variance_bound == pytest.approx(.5)


@pytest.fixture
def small_log():
    return generate_evaluation(SyntheticConfig(B=4,n0=8,chi=2), 70)[0]


def test_chebyshev_uses_all_rows_with_no_mom_k_feasibility(small_log):
    records = certify_bounded_graph(small_log)
    for candidate, record in zip(small_log.family, records):
        assert record['status'] == 'CERTIFIED'
        assert record['estimator'] == 'bounded_graph_chebyshev'
        assert record['raw_N'] == record['retained_N'] == 32
        assert record['K'] is None and record['L_min'] is None
        assert record['chi_max'] == 2 and record['N_eff'] == 16
        expected_v = sum(row_variance_envelope(candidate.q_vector,row.e_vector,candidate.h(row.context))
                         for row in small_log.rows)*2/32**2
        assert record['variance_bound'] == pytest.approx(expected_v)
        assert record['stochastic_radius'] == pytest.approx(sqrt(4*expected_v/.05))
        assert record['certified_level'] == pytest.approx(.95)
        assert record['nuisance_radius'] == record['drift_radius'] == record['coupling_failure_epsilon'] == 0


def test_easy_design_has_nontrivial_width_without_outcome_or_oracle_selection():
    config = SyntheticConfig(B=128,n0=64,chi=1,e_by_context=(.2,.2),q_probs=(.2,),auditors=('all',))
    log, _ = generate_evaluation(config, 7201)
    record, = certify_bounded_graph(log)
    assert record['status'] == 'CERTIFIED'
    assert record['variance_bound'] == pytest.approx(1/8192)
    assert record['stochastic_radius'] == pytest.approx(sqrt(1/(.05*8192)))
    assert record['hi']-record['lo'] == pytest.approx(0.09882117688026186)
    assert record['hi']-record['lo'] < .25  # known design implication, not a coverage test


@pytest.mark.parametrize('model', ['evaluation_trained_nuisance', 'future_outcome_conditioned_design',
                                  'hidden_permanent_shared_shock', 'missing_conflict_edges',
                                  'uncontrolled_between_block_dependence', 'p_moment_violation',
                                  'outcome_selected_K_or_cap'])
def test_variance_refuses_inapplicable_declared_models(small_log, model):
    records = certify_bounded_graph(replace(small_log,proof_model=model))
    assert all(r['status']=='UNVERIFIED_ASSUMPTION' and r['lo'] is None for r in records)


def test_variance_refuses_changed_nuisance_future_features_and_unbounded_reward(small_log):
    for bad in (replace(small_log.rows[0],mu_hat=(0,1)),
                replace(small_log.rows[0],features_available_at=2),
                replace(small_log.rows[0],reward_y=2)):
        records = certify_bounded_graph(replace(small_log,rows=(bad,)+small_log.rows[1:]))
        assert all(r['status']!='CERTIFIED' and r['lo'] is None for r in records)
    config = replace(small_log.config,e_by_context=(0,.4))
    records = certify_bounded_graph(replace(small_log,config=config))
    assert all(r['status']=='NOT_CERTIFIABLE' and r['lo'] is None for r in records)


def test_variance_zero_auditor_and_numerical_overflow_abstention():
    log, _ = generate_evaluation(SyntheticConfig(B=2,n0=4,chi=4),9)
    group = [r for r in certify_bounded_graph(log) if r['candidate_id'].endswith('group1')]
    assert all(r['variance_bound']==r['stochastic_radius']==0 for r in group)
    assert all(r['lo']==r['hi']==0 for r in group)
    log, _ = generate_evaluation(SyntheticConfig(B=2,n0=4,chi=4,e_by_context=(5e-324,.4)),9)
    records = certify_bounded_graph(log)
    assert all(r['status']=='NOT_CERTIFIABLE' and r['lo'] is None for r in records)


def test_variance_api_has_no_oracle_and_reproduces_same_seed():
    config = SyntheticConfig(B=4,n0=8,chi=2)
    log, oracle = generate_evaluation(config,901)
    changed_oracle = replace(oracle,moments={key:1e9 for key in oracle.moments})
    assert changed_oracle != oracle
    again, _ = generate_evaluation(config,901)
    assert certify_bounded_graph(log) == certify_bounded_graph(again)
    assert all('oracle_truth' not in r for r in certify_bounded_graph(log))


def test_nonrepresentable_multiplier_abstains_even_for_zero_variance():
    import json
    config = SyntheticConfig(B=2,n0=4,chi=4,q_probs=(.25,),auditors=('group1',))
    log, _ = generate_evaluation(config,901)
    records = certify_bounded_graph(log, alpha=5e-324)
    assert all(r['status']=='NOT_CERTIFIABLE' and r['lo'] is None for r in records)
    assert all(r['reason']=='VARIANCE_MULTIPLIER_EXCEEDS_FLOAT_RANGE' for r in records)
    json.dumps(records, allow_nan=False)


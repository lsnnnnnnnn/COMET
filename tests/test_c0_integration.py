from dataclasses import replace
import json
from pathlib import Path

import pytest

from comet.certification import certify, _registered_scores
from comet.dr_scores import dr_score
from comet.informativeness import add_support_bounds
from comet.schema import SyntheticConfig, LoggedEvaluation, LoggedRow
from comet.synthetic import generate_evaluation


def test_original_saved_smoke_certificate_fields_remain_bitwise_unchanged():
    root = Path(__file__).resolve().parents[1]
    saved = json.loads((root/'results/smoke/example_log.json').read_text())
    cfg = dict(saved['config'])
    for key in ('e_by_context', 'mu_hat', 'q_probs', 'auditors'):
        cfg[key] = tuple(cfg[key])
    config = SyntheticConfig(**cfg)
    rows = []
    for row in saved['rows']:
        row['e_vector'], row['mu_hat'] = tuple(row['e_vector']), tuple(row['mu_hat'])
        rows.append(LoggedRow(**row))
    log = LoggedEvaluation(config, config.family, tuple(rows), saved['seed'])
    archived = json.loads((root/'results/smoke/intervals.json').read_text())
    for alpha in (.05, .1):
        prior = {r['candidate_id']: r for r in archived
                 if r['replicate_id'] == 0 and r['nominal_delta'] == alpha}
        for record in certify(log, alpha=alpha):
            old = prior[record['candidate_id']]
            for key in old.keys()-{'oracle_truth','covered','vacuous','replicate_id'}:
                assert record[key] == old[key], key


def test_reused_binary_scores_equal_individual_score_calls():
    log, _ = generate_evaluation(SyntheticConfig(B=2, n0=8, chi=2), 19)
    for candidate in log.family:
        direct = [dr_score(r.reward_y, r.observed_exposure_s, candidate.q_vector,
                           r.e_vector, r.mu_hat, candidate.h(r.context), r.reference_f)
                  for r in log.rows]
        assert _registered_scores(log, candidate) == direct


def test_support_clipping_preserves_raw_interval_and_classifies_vacuity():
    record = dict(status='CERTIFIED', estimate=.2, stochastic_radius=14., lo=-13.8, hi=14.2)
    result = add_support_bounds(record, -.25, .75)
    assert (result['raw_lo'], result['raw_hi']) == (-13.8, 14.2)
    assert (result['clipped_lo'], result['clipped_hi']) == (-.25, .75)
    assert result['width_fraction'] == 1 and result['informativeness_fraction'] == 0
    assert result['is_full_range'] and not result['is_nontrivial']
    narrow = add_support_bounds(dict(record,lo=.1,hi=.3,stochastic_radius=.1), -.25,.75)
    assert narrow['informativeness_fraction'] == pytest.approx(.8)
    assert narrow['is_nontrivial'] and narrow['decision_issuable']


def test_empty_or_zero_diameter_is_not_reported_as_useful_information():
    empty = add_support_bounds(dict(status='CERTIFIED', estimate=3, lo=2, hi=4,
                                    stochastic_radius=1), 0, 1)
    assert empty['is_empty'] and not empty['is_nontrivial']
    assert not empty['decision_issuable'] and empty['informativeness_fraction'] is None
    point = add_support_bounds(dict(status='CERTIFIED',estimate=0,lo=-1,hi=1,
                                    stochastic_radius=1), 0, 0)
    assert point['width_fraction'] is None and not point['is_nontrivial']


def test_exact_mom_switch_uses_actual_family_and_declared_eta_only():
    log, _ = generate_evaluation(SyntheticConfig(), 3)
    for alpha, expected_k in ((.05,7),(.1,5)):
        exact = certify(log, alpha=alpha, mom_majority_rule='exact_binomial')
        old = certify(log, alpha=alpha)
        for new, baseline in zip(exact, old):
            assert new['status'] == 'CERTIFIED' and new['K'] == expected_k
            assert new['eta'] == .125 and new['binomial_familywise_failure_bound'] <= alpha
            assert sum(new['group_sizes']) == log.config.B
            assert new['stochastic_radius'] < baseline['stochastic_radius']
    for keyword in ('K','eta','clipping_cap'):
        with pytest.raises(TypeError):
            certify(log, **{keyword: 1})
    assert all(r['status']=='NOT_CERTIFIABLE' for r in certify(log, mom_majority_rule='outcome_selected'))


@pytest.mark.parametrize('invalid_model', [
    'hidden_permanent_shared_shock', 'false_graph_missing_edges',
    'evaluation_trained_nuisance', 'future_outcome_conditioned_design',
    'p_moment_violation', 'outcome_selected_K_without_adjustment',
    'varying_block_targets_without_drift_bound'])
def test_declared_negative_controls_cannot_receive_a_certificate(invalid_model):
    log, _ = generate_evaluation(SyntheticConfig(B=16,n0=8,chi=2), 8)
    result = certify(replace(log,proof_model=invalid_model),mom_majority_rule='exact_binomial')
    assert all(r['status']=='UNVERIFIED_ASSUMPTION' and r['lo'] is None for r in result)

"""Deterministic model/target identities; no empirical coverage assertions."""

from dataclasses import asdict, replace
from fractions import Fraction
import inspect
import math

import pytest

from comet.dr_scores import dr_score
from comet.gate_c_contract import (GateCCell, STREAM_NAMES, cell_from_dict,
                                   known_centered_envelope, pareto_absolute_moment,
                                   validate_evaluation, validate_stream_seeds)
from comet.gate_c_simulation import (_draw_bernoulli, _shared_bernoulli_potentials,
                                    _pareto_from_unit, _response_location,
                                    generate_evaluation)
from comet.gate_c_truth import exact_targets
from comet.schema import CertificationError, SyntheticConfig


def cell(**changes):
    base = GateCCell("fixture", SyntheticConfig(B=3, n0=8, chi=2,
        q_probs=(.1,.5,.9), auditors=("all","group1")))
    return replace(base, **changes)


def seeds(offset=0):
    return {name: 100+offset+i for i,name in enumerate(STREAM_NAMES)}


def test_integer_lottery_matches_declared_float_probability_exactly():
    class FixedLottery:
        def __init__(self,draw):
            self.draw,self.denominator=draw,None
        def randrange(self,denominator):
            assert 0<=self.draw<denominator
            self.denominator=denominator
            return self.draw
    for probability in (.01,.02,.4,.5,.6):
        numerator,denominator=probability.as_integer_ratio()
        below,at=FixedLottery(numerator-1),FixedLottery(numerator)
        assert _draw_bernoulli(below,probability)==1
        assert _draw_bernoulli(at,probability)==0
        assert below.denominator==at.denominator==denominator
        assert Fraction(numerator,denominator)==Fraction(probability)
    # Full exact enumeration of a small common dyadic space.
    pairs=[_shared_bernoulli_potentials(FixedLottery(i),(.25,.75)) for i in range(4)]
    assert pairs==[(1,1),(0,1),(0,1),(0,0)]
    assert tuple(sum(row[s] for row in pairs)/4 for s in (0,1))==(.25,.75)


@pytest.mark.parametrize("family,p", [("bernoulli",2), ("symmetric_pareto",1.5)])
def test_analytic_oracle_is_exact_conditional_window_expectation(family,p):
    c = cell(outcome_family=family,p=p)
    truth = exact_targets(c)
    for candidate in c.design.family:
        q = candidate.q1
        expected = .025+.425*q if candidate.auditor=="all" else .05+.225*q
        assert truth[candidate.candidate_id] == pytest.approx(expected,abs=1e-15)
    # The target does not depend on a logging draw, on fitted nuisance accuracy,
    # or on how often one seed happened to observe an exposure.
    changed = replace(c,design=replace(c.design,e_by_context=(.01,.02),mu_hat=(0.,1.)))
    assert exact_targets(changed) == truth


def test_fixed_design_context_counts_do_not_become_population_prevalence():
    c = cell(design=SyntheticConfig(B=2,n0=6,chi=2,q_probs=(.25,),auditors=("all","group1")))
    truth = exact_targets(c)
    assert truth['q0.25__all'] == pytest.approx(float(Fraction(5,48)))
    assert truth['q0.25__group1'] == pytest.approx(float(Fraction(17,240)))
    # Three clusters contain two context-0 and one context-1 clusters, not 50/50.
    assert truth['q0.25__all'] != pytest.approx(.025+.425*.25)


def test_exogenous_drift_oracle_uses_all_blocks_and_row_weights():
    stable = cell()
    drifting = replace(stable,stable_targets=False)
    stable_truth, drift_truth = exact_targets(stable), exact_targets(drifting)
    for candidate in stable.design.family:
        mass = 1 if candidate.auditor=='all' else .5
        assert drift_truth[candidate.candidate_id]-stable_truth[candidate.candidate_id] == pytest.approx(mass/60)
    log = generate_evaluation(drifting,seeds(),'drift-fixture')
    validate_evaluation(drifting,log)
    assert log.proof_model != generate_evaluation(stable,seeds(),'stable-fixture').proof_model


@pytest.mark.parametrize("mu_hat", [(0.,0.),(1.,0.),(.01,.99),(.5,.5)])
@pytest.mark.parametrize("h", [0.,.5,1.])
def test_exact_logging_dr_identity_with_arbitrary_fixed_nuisance(mu_hat,h):
    q,e,mu,f = (.3,.7),(.9,.1),(.2,.8),.25
    expected = sum(e[s]*(mu[s]*dr_score(1,s,q,e,mu_hat,h,f)
                    +(1-mu[s])*dr_score(0,s,q,e,mu_hat,h,f)) for s in (0,1))
    target = h*(sum(qs*ms for qs,ms in zip(q,mu))-f)
    assert expected == pytest.approx(target,abs=1e-15)


def test_heavy_dr_identity_and_centered_envelope_by_finite_enumeration():
    c = cell(outcome_family='symmetric_pareto',p=1.5)
    q,e,mu,fit = (.3,.7),(.8,.2),(.2,.8),(.9,.1)
    # This centered, symmetric residual fixture has a smaller known 1.5-moment
    # than the Pareto envelope; it verifies the score algebra independently.
    noise = (-.25,-.1,.1,.25)
    target = sum(qs*ms for qs,ms in zip(q,mu))-.25
    expectation = sum(e[s]*dr_score(mu[s]+z,s,q,e,fit,1,.25)/4
                      for s in (0,1) for z in noise)
    centered_p = sum(e[s]*abs(dr_score(mu[s]+z,s,q,e,fit,1,.25)-target)**1.5/4
                     for s in (0,1) for z in noise)
    assert expectation == pytest.approx(target)
    assert centered_p <= known_centered_envelope(c,q,e,1.5)


def test_pareto_moment_integral_and_positive_grid_bound():
    p,alpha,scale = 1.5,1.75,.1
    known = pareto_absolute_moment(alpha,scale,p)
    assert known == pytest.approx(7*.1**1.5)
    # Integral alpha*sigma^p*int_1^inf t^(p-alpha-1)dt.
    assert alpha-p == .25
    for grid in (2,8,128):
        discrete = sum(abs(_pareto_from_unit(j/grid,1,alpha,scale))**p
                       for j in range(1,grid+1))/grid
        assert discrete <= known  # decreasing-function right Riemann sum
    for k in (1,10,50,100):
        positive = _pareto_from_unit(2.**(-k),1,alpha,scale)
        negative = _pareto_from_unit(2.**(-k),-1,alpha,scale)
        assert positive == -negative
    assert _pareto_from_unit(2.**(-50),1,alpha,scale)>1e6


@pytest.mark.parametrize("p", [1.75,2.0])
def test_invalid_p_moment_is_not_certified(p):
    c = cell(outcome_family='symmetric_pareto',p=p)
    with pytest.raises(CertificationError,match='P_MOMENT_NOT_FINITE') as error:
        c.validate()
    assert error.value.status=='NOT_APPLICABLE'
    with pytest.raises(CertificationError):
        pareto_absolute_moment(1.75,.1,p)


def test_heavy_envelope_uses_only_declared_design_and_noise_bound():
    c = cell(outcome_family='symmetric_pareto',p=1.5)
    bound = known_centered_envelope(c,(.5,.5),(.5,.5),1.5)
    assert bound == pytest.approx(4*(1+math.sqrt(2)*(1+7*.1**1.5)))
    assert c.known_conditional_mean_bounds==(0.,1.)
    # Neither the actual oracle locations nor fitted-value accuracy narrows it.
    other = replace(c,design=replace(c.design,mu_hat=(.01,.99)))
    assert known_centered_envelope(other,(.5,.5),(.5,.5),1.5)==bound
    import comet.gate_c_contract as contract
    source=inspect.getsource(contract)
    assert 'import gate_c_truth' not in source and 'from .gate_c_truth' not in source
    assert 'from .gate_c_simulation' not in source
    assert 'exact_targets(' not in source


def test_frozen_json_conversion_and_real_family_cardinality():
    c=cell(design=replace(cell().design,q_probs=(.1,.2,.3,.4,.6,.7,.8,.9)))
    raw=asdict(c)
    raw['description']='metadata only'
    restored=cell_from_dict(raw)
    assert restored==c and len(restored.design.family)==16
    assert len({candidate.candidate_id for candidate in restored.design.family})==16
    truth=exact_targets(restored)
    assert len(set(truth.values()))==16
    with pytest.raises(CertificationError,match='UNKNOWN_CELL_FIELDS'):
        cell_from_dict(dict(raw,oracle_tuned=True))


def test_all_seven_streams_are_distinct_and_reproducible():
    c=cell(design=replace(cell().design,B=2,n0=64,chi=1))
    original=generate_evaluation(c,seeds(),'repeat')
    assert original==generate_evaluation(c,seeds(),'repeat')
    changed=dict(seeds(),logging_exposure=901)
    new_log=generate_evaluation(c,changed,'different-logging')
    assert any(a.observed_action!=b.observed_action for a,b in zip(original.rows,new_log.rows))
    for a,b in zip(original.rows,new_log.rows):
        if a.observed_action==b.observed_action:
            assert a.reward_y==b.reward_y
    changed=dict(seeds(),potential_outcomes=902)
    new_outcome=generate_evaluation(c,changed,'different-potential-outcomes')
    assert [r.observed_action for r in original.rows]==[r.observed_action for r in new_outcome.rows]
    assert any(a.reward_y!=b.reward_y for a,b in zip(original.rows,new_outcome.rows))
    # These roles are genuinely deterministic/unused in this preflight model.
    reserved=dict(seeds())
    for name in ('design_context','graph_shocks','nuisance_discovery_pilot','evaluation_outcomes','truth_mc'):
        reserved[name]+=1000
    assert generate_evaluation(c,reserved,'reserved')==original
    with pytest.raises(CertificationError,match='DISTINCT'):
        validate_stream_seeds({name:1 for name in STREAM_NAMES})


@pytest.mark.parametrize("family,p", [('bernoulli',2),('symmetric_pareto',1.5)])
def test_model_records_exact_clique_copies_without_oracle_payload(family,p):
    c=cell(outcome_family=family,p=p)
    log=generate_evaluation(c,seeds(),'cliques')
    validate_evaluation(c,log)
    for first in range(0,len(log.rows),c.design.chi):
        copies=log.rows[first:first+c.design.chi]
        assert len({(r.observed_action,r.reward_y,r.context,r.cluster_id) for r in copies})==1
    payload=asdict(log)
    assert not any('truth' in name or 'potential' in name or 'response_mean' in name for name in payload)


@pytest.mark.parametrize("mutation,reason", [
    (dict(e_s_logged=.99),'EXACT_LOGGING_PROPENSITY_MISMATCH'),
    (dict(mu_hat=(0.,0.)),'FIXED_NUISANCE_OR_REFERENCE_MISMATCH'),
    (dict(features_available_at=1),'PREACTION_OR_EXPOSURE_PROVENANCE_MISMATCH'),
    (dict(reward_y=2),'REGISTERED_BERNOULLI_REWARD_REQUIRED'),
    (dict(observed_exposure_s=0.5),'EXPOSURE_SPACE_MISMATCH'),
])
def test_observable_model_violations_refuse(mutation,reason):
    c=cell(); log=generate_evaluation(c,seeds(),'bad-row')
    bad=replace(log,rows=(replace(log.rows[0],**mutation),)+log.rows[1:])
    with pytest.raises(CertificationError,match=reason):
        validate_evaluation(c,bad)


def test_disclosed_hidden_models_and_nuisance_training_refuse():
    c=cell(); log=generate_evaluation(c,seeds(),'declared-bad-model')
    for label in ('permanent_shared_shock','missing_graph_edges','outcome_selected_q_h'):
        with pytest.raises(CertificationError,match='DECLARED_MODEL_MISMATCH') as error:
            validate_evaluation(c,replace(log,proof_model=label))
        assert error.value.status=='UNVERIFIED_ASSUMPTION'
    with pytest.raises(CertificationError,match='FIXED_NUISANCE_REQUIRED'):
        replace(c,nuisance_source='trained_on_evaluation').validate()


def test_zero_support_is_identification_failure():
    c=cell(design=replace(cell().design,e_by_context=(0.,.5)))
    with pytest.raises(CertificationError,match='BOTH_EXPOSURES_SUPPORTED'):
        c.validate()


def test_oracle_is_not_called_by_generator_or_known_envelope(monkeypatch):
    import comet.gate_c_truth as truth
    def forbidden(*args,**kwargs):
        raise AssertionError('oracle must not be called')
    monkeypatch.setattr(truth,'exact_targets',forbidden)
    c=cell(outcome_family='symmetric_pareto',p=1.5)
    log=generate_evaluation(c,seeds(),'oracle-separation')
    validate_evaluation(c,log)
    assert known_centered_envelope(c,(.5,.5),(.5,.5),1.5)>0

"""Deterministic source-formula and filtration checks; no Monte Carlo."""

import math

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.special import gammainc, gammaln, hyp1f1

from comet.ope_2024 import dr_pseudo_outcomes, eb_log_mixture, eb_variance, ope_eb_independent


def test_statewise_capped_dr_identity_by_finite_enumeration():
    e, q, fit, means = np.array([[.9,.1]]), np.array([[.3,.7]]), np.array([[.2,.8]]), [.25,.75]
    expected_lower = expected_upper = 0.0
    for action in (0,1):
        for reward in (0.0,1.0):
            probability=e[0,action]*(means[action] if reward else 1-means[action])
            lower, upper, _ = dr_pseudo_outcomes(np.array([action]), [reward], e, q, fit, k=.5)
            expected_lower += probability*lower[0]
            expected_upper += probability*upper[0]
            assert lower[0] >= -.5 and upper[0] >= -.5
    truth=float(q[0]@means)
    assert expected_lower == pytest.approx(truth)
    assert expected_upper == pytest.approx(1-truth)


@pytest.mark.parametrize("s,v,rho",[(0.,0.,1.),(.1,3.,.5),(4.,20.,1.),(10.,100.,2.)])
def test_gamma_formula_matches_kummer_and_positive_integral(s,v,rho):
    c = rho*math.log(rho)-rho-gammaln(rho)-math.log(gammainc(rho,rho))
    kummer=c-math.log(v+rho)+math.log(hyp1f1(1,v+rho+1,s+v+rho))
    assert eb_log_mixture(s,v,rho) == pytest.approx(kummer,abs=1e-10)
    # lambda=1-exp(-t) removes the integrable endpoint singularity.
    norm=rho*math.log(rho)-gammaln(rho)-math.log(gammainc(rho,rho))
    integral,_=quad(lambda t: math.exp((1-math.exp(-t))*(s+v)
        -v*t + norm-rho*math.exp(-t)-rho*t),0,np.inf,epsabs=1e-10)
    assert math.exp(eb_log_mixture(s,v,rho)) == pytest.approx(integral,rel=1e-9)


def test_variance_predictor_uses_only_past_data():
    total, variance=eb_variance([0.,1.,0.],k=0,initial_prediction=.5)
    assert total==1
    assert variance==pytest.approx(.25+1+.25)


def anchor(n):
    actions=np.arange(n,dtype=np.int64)%2
    rewards=np.tile([0.,1.,1.,0.],n//4)
    e=np.full((n,2),.5)
    return actions,rewards,dict(exposure=e,target_policy=e,nuisance=e,
        independent_rows_declared=True,independent_nuisance_declared=True,k=.5,rho=1.)


def test_eb_anchor_and_mirrored_bounds_are_informative():
    a,y,kwargs=anchor(256)
    r=ope_eb_independent(a,y,**kwargs)
    s=ope_eb_independent(a,1-y,**kwargs)
    assert r["status"]=="CERTIFIED_UNDER_DECLARED_ASSUMPTIONS"
    assert r["lo"]<=.5<=r["hi"]
    assert r["hi"]-r["lo"]<.4
    assert r["lo"]==pytest.approx(1-s["hi"])
    assert r["hi"]==pytest.approx(1-s["lo"])
    assert r["uses_history_interval_intersection"] is False
    a,y,kwargs=anchor(1024)
    bigger=ope_eb_independent(a,y,**kwargs)
    assert bigger["hi"]-bigger["lo"]<r["hi"]-r["lo"]


def test_independent_heterogeneous_row_means_are_not_rejected_as_non_iid():
    n=256
    a=np.arange(n,dtype=np.int64)%2
    y=np.linspace(.1,.9,n)
    e=np.column_stack((np.linspace(.2,.8,n),np.linspace(.8,.2,n)))
    q=np.column_stack((np.linspace(.3,.7,n),np.linspace(.7,.3,n)))
    fit=np.column_stack((np.linspace(.1,.5,n),np.linspace(.5,.9,n)))
    r=ope_eb_independent(a,y,exposure=e,target_policy=q,nuisance=fit,
        independent_rows_declared=True,independent_nuisance_declared=True)
    assert r["status"]=="CERTIFIED_UNDER_DECLARED_ASSUMPTIONS"
    assert "heterogeneous" in r["estimand"]


def test_missing_independence_and_outcome_tuning_have_no_certificate():
    a,y,kwargs=anchor(32)
    kwargs["independent_rows_declared"]=False
    r=ope_eb_independent(a,y,**kwargs)
    assert r["status"]=="ASSUMPTION_UNVERIFIED" and r["lo"] is None
    kwargs["independent_rows_declared"]=True
    r=ope_eb_independent(a,y,**kwargs,tuning="evaluation_outcomes")
    assert r["status"]=="HEURISTIC" and r["lo"] is None


def test_family_budget_and_support():
    a,y,kwargs=anchor(256)
    single=ope_eb_independent(a,y,**kwargs,family_size=1)
    family=ope_eb_independent(a,y,**kwargs,family_size=16)
    assert family["coordinate_delta"]==.05/16
    assert family["lo"]<=single["lo"] and family["hi"]>=single["hi"]
    with pytest.raises(ValueError,match="NONIDENTIFIED"):
        dr_pseudo_outcomes(np.array([0]),[.5],[[1.,0]],[[.5,.5]],[[.5,.5]],k=1)

from copy import deepcopy
from fractions import Fraction
from math import comb

import pytest

from comet.gate_c_statistics import (PRIMARY_COMPARISONS, exact_binomial_lower,
                                     exact_binomial_upper, holm_adjust, quantile,
                                     summarize_records, undercoverage_pvalue)
from comet.metrics import wilson


def test_exact_binomial_inclusive_hand_fixtures():
    assert exact_binomial_lower(1,4,Fraction(1,2))==Fraction(5,16)
    assert exact_binomial_upper(3,4,Fraction(1,2))==Fraction(5,16)
    assert exact_binomial_lower(0,2,.95)==Fraction(1,400)
    assert exact_binomial_upper(2,2,.95)==Fraction(361,400)
    assert undercoverage_pvalue(1,2,.95)==pytest.approx(.0975)
    assert undercoverage_pvalue(2,2,.95)==1
    assert undercoverage_pvalue(0,0,.95) is None


@pytest.mark.parametrize('n',[1,2,7])
@pytest.mark.parametrize('p',[Fraction(0),Fraction(1,8),Fraction(19,20),Fraction(1)])
def test_lower_upper_tail_complement_includes_shared_atom(n,p):
    for k in range(n+1):
        pmf=comb(n,k)*p**k*(1-p)**(n-k)
        assert exact_binomial_lower(k,n,p)+exact_binomial_upper(k,n,p)==1+pmf


def test_exact_tail_remains_positive_at_confirmatory_underflow_scale():
    exact=exact_binomial_lower(0,1000,Fraction(19,20))
    assert exact==Fraction(1,20**1000)
    assert exact>0 and undercoverage_pvalue(0,1000,.95)>0


@pytest.mark.parametrize('args',[(-1,2,.95),(3,2,.95),(0,-1,.95),(0,2,-.1),(0,2,1.1)])
def test_invalid_exact_tail_inputs_refused(args):
    with pytest.raises(ValueError):
        exact_binomial_lower(*args)


def test_holm_stepdown_monotone_fixture_and_missing_comparisons():
    actual=holm_adjust({'a':.01,'b':.04,'c':.03,'d':.2})
    assert actual==pytest.approx({'a':.04,'b':.09,'c':.09,'d':.2})
    assert holm_adjust({'a':.01,'b':None,'c':.2})=={'a':.03,'b':None,'c':.4}
    assert len(PRIMARY_COMPARISONS)==17
    assert ('F','bounded_graph_chebyshev') not in PRIMARY_COMPARISONS
    assert not any(m in ('full_feasible_range','ips','dm','dr') for _,m in PRIMARY_COMPARISONS)


def test_wilson_uses_replication_denominator_and_empty_is_undefined():
    assert wilson(0,0)==(None,None)
    low,high=wilson(30,30)
    assert low==pytest.approx(.8864866068260314)
    assert high==1
    assert wilson(1,2)[0]==pytest.approx(1-wilson(1,2)[1])


def records_fixture(method='exact_binomial_mom',status='CERTIFIED',cell='A'):
    widths=[.2,.4,.6,1.]
    decisions=['CERTIFIED_SAFE','CERTIFIED_VIOLATION','CERTIFIED_SAFE','ABSTAIN']
    result=[]
    for index in range(4):
        certified=status=='CERTIFIED'
        result.append(dict(cell_id=cell,method=method,nominal_delta=.05,
            run_id=f'run{index//2}',candidate_id=f'q{index%2}',family_size=2,
            status=status,certificate_applicable=certified,decision_issuable=certified,
            covered=index!=2 if certified else None,raw_covered=index!=2 if certified else None,
            width_fraction=widths[index] if certified else None,
            raw_radius=.2 if certified else None,is_nontrivial=certified and index<3,
            signed_error=(-1)**index*.1,absolute_error=.1,true_target=.2,
            true_violation=index in (1,2),
            decision=decisions[index] if certified else 'POINT_ONLY' if status=='POINT_ONLY' else 'ABSTAIN',
            false_safe=certified and index==2,false_violation=False))
    return result


def test_summary_preserves_family_and_candidate_denominators():
    row=summarize_records(records_fixture(),primary_comparisons=[('A','exact_binomial_mom')])[0]
    assert row['replications']==2 and row['candidate_records']==4
    assert row['family_coverage']==.5 and row['covered_families']==1
    assert (row['wilson_lo'],row['wilson_hi'])==wilson(1,2)
    assert row['marginal_nontrivial_fraction']==.75
    assert row['family_nontrivial_some']==1 and row['family_nontrivial_all']==.5
    assert row['median_width_fraction']==.5
    assert row['p90_width_fraction']==pytest.approx(.88)
    assert row['iqr_width_fraction']==pytest.approx(.35)
    assert row['undercoverage_pvalue']==pytest.approx(.0975)
    assert row['undercoverage_holm_pvalue']==pytest.approx(.0975)
    assert row['violation_power']==.5 and row['false_safe_count']==1
    assert row['constraint_abstention_fraction']==.25


def test_primary_holm_keeps_frozen_seventeen_and_accepts_manifest_dicts():
    summary=summarize_records(records_fixture())[0]
    assert summary['holm_declared_comparisons']==17
    assert summary['undercoverage_holm_pvalue']==1
    dictionary=[dict(cell_id=c,method=m,alpha=.05) for c,m in PRIMARY_COMPARISONS]
    assert summarize_records(records_fixture(),primary_comparisons=dictionary)==summarize_records(records_fixture())


@pytest.mark.parametrize('method,status,cell',[
    ('dr','POINT_ONLY','A'),('bounded_graph_chebyshev','NOT_APPLICABLE','F')])
def test_nonapplicable_and_point_rows_are_not_fake_coverage(method,status,cell):
    summary=summarize_records(records_fixture(method,status,cell))[0]
    assert summary['replications']==2 and summary['candidate_records']==4
    assert summary['applicability_fraction']==0 and summary['interval_absent_fraction']==1
    assert summary['family_coverage'] is summary['covered_families'] is summary['wilson_lo'] is None
    assert summary['coverage_given_issued'] is summary['undercoverage_pvalue'] is None
    assert summary['median_width_fraction'] is None
    assert summary['not_applicable_families']==(2 if status=='NOT_APPLICABLE' else 0)


def test_refusal_stays_in_allocation_counts_without_conditional_coverage_claim():
    records=records_fixture()
    for row in records[2:]:
        row.update(status='NOT_CERTIFIABLE',certificate_applicable=False,
                   decision_issuable=False,decision='ABSTAIN',covered=None,raw_covered=None,
                   width_fraction=None,raw_radius=None,is_nontrivial=False,false_safe=False)
    summary=summarize_records(records)[0]
    assert summary['replications']==2 and summary['applicable_families']==1
    assert summary['issued_families']==1 and summary['coverage_given_issued']==1
    assert summary['family_coverage'] is summary['undercoverage_pvalue'] is None
    assert summary['interval_absent_fraction']==.5


def test_empty_intersection_failure_is_counted_in_undercoverage_diagnostic():
    rows=records_fixture()
    for row in rows:
        row.update(decision_issuable=False,decision='ABSTAIN',covered=False,raw_covered=False,
                   width_fraction=None,raw_radius=.2,is_nontrivial=False,false_safe=False,
                   is_empty=True)
    result=summarize_records(rows)[0]
    assert result['applicable_families']==2 and result['issued_families']==0
    assert result['covered_families']==0 and result['family_coverage']==0
    assert result['coverage_given_issued'] is None
    assert result['undercoverage_pvalue']==pytest.approx(.0025)
    assert result['undercoverage_holm_pvalue']==pytest.approx(17*.0025)


@pytest.mark.parametrize('mutation',['drop','duplicate','change_family'])
def test_incomplete_or_changed_family_cannot_silently_pass_summary(mutation):
    rows=deepcopy(records_fixture())
    if mutation=='drop':
        rows.pop()
    elif mutation=='duplicate':
        rows[-1]['candidate_id']=rows[-2]['candidate_id']
    else:
        rows[-1]['candidate_id']='posthoc_selected_auditor'
    with pytest.raises(ValueError):
        summarize_records(rows)


def test_quantile_empty_and_exact_linear_interpolation():
    assert quantile([],.5) is None
    assert quantile([0,1,2,3],.25)==.75
    assert quantile([0,1,2,3],.75)==2.25

"""Reporting-only checks: no confirmatory seed is generated or consumed."""
from copy import deepcopy
from fractions import Fraction
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('independent_cstat_validation',ROOT/'reports/gate_C_stat_audit/validate_confirmatory.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


def test_independent_exact_binomial_and_holm_hand_calculation():
    assert audit.lower_exact(1,2,.95)==Fraction(39,400)
    assert audit.lower_exact(0,1000,.95)==Fraction(1,20**1000)
    assert audit.upper_float(audit.lower_exact(0,1000,.95))>0
    assert audit.holm({'a':.01,'b':.04,'c':.03,'d':.2})=={'a':.04,'c':.09,'b':.09,'d':.2}


def test_independent_family_failure_is_one_log_not_candidate_count():
    wrapper=audit.read(ROOT/'results/gate_C/preflight/batch/runs/B/0000.json')
    family=deepcopy([r for r in wrapper['payload']['records'] if r['method']=='exact_binomial_mom' and r['nominal_delta']==.05])
    assert len(family)==16
    # One candidate's false-safe event makes exactly one family failure.
    family[-1].update(covered=False,raw_covered=False,false_safe=True,true_violation=True,decision='CERTIFIED_SAFE')
    accumulator=audit.Accumulator('B',.05,'exact_binomial_mom');accumulator.add(family)
    row=accumulator.finish('preflight');extra=accumulator.extras()
    assert row['replications']==1 and row['candidate_records']==16
    assert row['covered_families']==0 and row['family_coverage']==0
    assert row['false_safe_count']==1
    assert extra['false_any_logs']==1 and extra['false_any_rate']==1
    assert row['undercoverage_pvalue']==audit.upper_float(Fraction(1,20))


def test_independent_empty_intersection_is_failure_not_missing_family():
    wrapper=audit.read(ROOT/'results/gate_C/preflight/batch/runs/A/0000.json')
    family=deepcopy([r for r in wrapper['payload']['records'] if r['method']=='exact_binomial_mom' and r['nominal_delta']==.05])
    family[0].update(covered=None,raw_covered=False,decision_issuable=False,decision='ABSTAIN',width_fraction=None,is_nontrivial=False)
    accumulator=audit.Accumulator('A',.05,'exact_binomial_mom');accumulator.add(family)
    row=accumulator.finish('preflight')
    assert row['applicable_families']==1 and row['issued_families']==0
    assert row['covered_families']==0 and row['family_coverage']==0
    assert row['coverage_given_issued'] is None
    assert row['undercoverage_pvalue']==audit.upper_float(Fraction(1,20))


def test_point_only_and_f_graph_never_get_coverage_denominators():
    wrapper=audit.read(ROOT/'results/gate_C/preflight/batch/runs/F/0000.json')
    for method in ('ips','dm','dr','bounded_graph_chebyshev'):
        family=[r for r in wrapper['payload']['records'] if r['method']==method and r['nominal_delta']==.05]
        accumulator=audit.Accumulator('F',.05,method);accumulator.add(family)
        row=accumulator.finish('preflight')
        assert row['replications']==1 and row['candidate_records']==16
        assert row['covered_families'] is row['family_coverage'] is row['undercoverage_pvalue'] is None
        assert row['no_certified_decision_fraction']==1

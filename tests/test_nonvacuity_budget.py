import ast
from fractions import Fraction
from pathlib import Path

import pytest

from experiments.nonvacuity_budget import (binomial_tail_fraction,budget_rows,plot_budget,
                                         radius,required_sample_size,select_K)


@pytest.mark.parametrize('p,expected',[
    (1.2,[8.0,7.127189745122715,6.349604207872798,5.656854249492381]),
    (1.5,[2.0,1.5874010519681994,1.2599210498948732,1.0]),
    (2.0,[.5,.3535533905932738,.25,.1767766952966369])])
def test_all_twelve_hand_derived_task_fixtures(p,expected):
    K=select_K(16,.05,128,'conservative_hoeffding')
    assert K==52
    for N,target in zip((8192,16384,32768,65536),expected):
        assert radius(p,1,1,N//128,128//K)==pytest.approx(target)


def test_independent_exact_tail_and_k_fixture():
    tail=binomial_tail_fraction(9)
    assert 16*tail==Fraction(166583,4194304)
    assert float(16*tail)==pytest.approx(.039716482162475586)
    assert select_K(16,.05,128,'exact_binomial')==9
    assert 16*binomial_tail_fraction(7)>Fraction(1,20)


@pytest.mark.parametrize('rule',['conservative_hoeffding','exact_binomial'])
@pytest.mark.parametrize('p',[1.2,1.5,2.0])
def test_exact_inversion_rounds_to_complete_cliques_and_meets_radius(p,rule):
    B,chi,nu,m=128,4,4.0,16
    K=select_K(m,.05,B,rule)
    result=required_sample_size(p,nu,chi,B,K)
    n0=result['required_n0']
    assert n0%chi==0 and result['required_N']==B*n0
    assert radius(p,nu,chi,n0,B//K)<=.25*(1+1e-12)
    assert n0==chi or radius(p,nu,chi,n0-chi,B//K)>=.25*(1-1e-12)


def test_sample_budget_is_not_identification_or_subgroup_support():
    zero=required_sample_size(2,1,1,128,9,diameter=0,subgroup_mass=0)
    missing=required_sample_size(2,1,1,128,9,support_positive=False)
    assert zero['required_N'] is None and missing['required_N'] is None
    large=required_sample_size(2,1,1,128,9,diameter=.5,subgroup_mass=.5)
    small=required_sample_size(2,1,1,128,9,diameter=.01,subgroup_mass=.01)
    assert small['required_N']>large['required_N']


def test_independent_calculator_has_no_data_or_oracle_imports():
    source=Path(__file__).resolve().parents[1]/'experiments/nonvacuity_budget.py'
    tree=ast.parse(source.read_text())
    for node in ast.walk(tree):
        if isinstance(node,ast.ImportFrom):
            assert not (node.module or '').startswith('comet')
        if isinstance(node,ast.Import):
            assert all(not a.name.startswith('comet') for a in node.names)


def test_budget_csv_inputs_and_plots_reproduce_without_outcomes(tmp_path):
    first=budget_rows(); second=budget_rows()
    assert first==second and len(first)==200
    plot_budget(first,tmp_path/'a')
    plot_budget(second,tmp_path/'b')
    for name in ('theoretical_sample_need.png','theoretical_sample_need.pdf'):
        assert (tmp_path/'a'/name).read_bytes()==(tmp_path/'b'/name).read_bytes()

"""Exact confidence-budget and group-majority invariants, never MC coverage."""

from decimal import Decimal, ROUND_CEILING, localcontext
from fractions import Fraction
from itertools import product
from math import ceil, comb, log, nextafter

import pytest

from comet.certification import certify
from comet.robust_mean import (binomial_majority_tail, binomial_majority_tail_fraction,
                               exact_binomial_groups, mom_estimate, mom_radius,
                               partition_blocks, required_groups)
from comet.schema import CertificationError, SyntheticConfig
from comet.synthetic import generate_evaluation


def test_literal_exact_nine_group_fixture_and_old_baseline():
    result = exact_binomial_groups(16, 0.05, 128)
    assert result['K'] == 9
    assert result['eta'] == 0.125
    assert result['eta_exact'] == '1/8'
    assert binomial_majority_tail_fraction(9) == Fraction(166583, 67108864)
    assert result['binomial_familywise_failure_bound'] == pytest.approx(0.039716482162475586)
    assert Fraction(int(result['binomial_familywise_numerator']),
                    int(result['binomial_familywise_denominator'])) <= Fraction(1, 20)
    assert 16*binomial_majority_tail_fraction(7) == Fraction(3271, 32768)
    assert required_groups(16, 0.05) == 52


@pytest.mark.parametrize('family_size', [1, 4, 16, 100])
@pytest.mark.parametrize('delta', [0.1, 0.05, 0.001, 1e-20])
def test_conservative_group_count_preserves_original_finite_arithmetic(family_size, delta):
    assert required_groups(family_size, delta) == ceil(8*log(2*family_size/delta))


@pytest.mark.parametrize('delta', [1e-320, nextafter(0.0, 1.0)])
def test_conservative_group_count_handles_tiny_positive_budget(delta):
    with localcontext() as context:
        context.prec = 90
        expected = (8*(Decimal(32)/Decimal.from_float(delta)).ln()).to_integral_value(
            rounding=ROUND_CEILING)
    assert required_groups(16, delta) == int(expected)


@pytest.mark.parametrize('kwargs', [{}, {'mom_majority_rule': 'conservative_hoeffding'}])
def test_conservative_certificate_abstains_for_tiny_budget_instead_of_overflowing(kwargs):
    evaluation, _ = generate_evaluation(SyntheticConfig(B=2, n0=4, chi=4), seed=1)
    records = certify(evaluation, alpha=1e-320, **kwargs)
    assert records
    for record in records:
        assert record['status'] == 'NOT_CERTIFIABLE'
        assert record['reason'] == 'INSUFFICIENT_BLOCKS_B_LT_2K'
        assert record['estimate'] is None
        assert record['lo'] is None and record['hi'] is None
        assert record['stochastic_radius'] is None


@pytest.mark.parametrize('K', [1, 2, 3, 4, 7, 9, 20, 51])
@pytest.mark.parametrize('eta', [Fraction(1, 8), Fraction(1, 10), Fraction(1, 3)])
def test_rational_tail_against_independent_decimal_probability_convolution(K, eta):
    # Independent algorithm: repeated Bernoulli convolution, no comb/recurrence.
    with localcontext() as context:
        context.prec = 90
        probability = Decimal(eta.numerator)/Decimal(eta.denominator)
        distribution = [Decimal(1)]
        for _ in range(K):
            updated = [Decimal(0)]*(len(distribution)+1)
            for successes, mass in enumerate(distribution):
                updated[successes] += mass*(1-probability)
                updated[successes+1] += mass*probability
            distribution = updated
        expected = sum(distribution[(K+1)//2:])
        actual = binomial_majority_tail_fraction(K, eta)
        actual_decimal = Decimal(actual.numerator)/Decimal(actual.denominator)
        assert abs(expected-actual_decimal) < Decimal('1e-85')


@pytest.mark.parametrize('family_size', [1, 4, 16, 100])
@pytest.mark.parametrize('delta', [0.1, 0.05, 0.001, 1e-20])
def test_selector_minimality_and_exact_confidence_budget(family_size, delta):
    result = exact_binomial_groups(family_size, delta, 1024)
    K = result['K']
    assert K % 2 == 1 and 2*K <= 1024
    assert family_size*binomial_majority_tail_fraction(K) <= Fraction(str(delta))
    for smaller in range(1, K, 2):
        assert family_size*binomial_majority_tail_fraction(smaller) > Fraction(str(delta))


def test_exact_threshold_acceptance_and_immediately_below_refusal_for_that_k():
    threshold = 16*binomial_majority_tail_fraction(9)
    assert exact_binomial_groups(16, threshold, 128)['K'] == 9
    assert exact_binomial_groups(16, threshold-Fraction(1, 10**30), 128)['K'] == 11


def test_small_delta_selector_does_not_underflow_or_change_target():
    result = exact_binomial_groups(16, 1e-100, 2048)
    exact_bound = Fraction(int(result['binomial_familywise_numerator']),
                           int(result['binomial_familywise_denominator']))
    assert exact_bound > 0 and exact_bound <= Fraction(1, 10**100)
    assert Fraction.from_float(result['binomial_familywise_failure_bound']) >= exact_bound
    # Here the exact tail is smaller than the least positive float; its
    # diagnostic rounds upward instead of becoming misleading zero.
    underflow_tail = binomial_majority_tail_fraction(2001)
    assert 0 < underflow_tail < Fraction.from_float(nextafter(0.0, 1.0))
    assert binomial_majority_tail(2001) == nextafter(0.0, 1.0)


@pytest.mark.parametrize('eta', [0, -0.1, 0.5, 1, float('nan'), float('inf')])
def test_invalid_group_failure_probability_is_rejected(eta):
    with pytest.raises(CertificationError):
        exact_binomial_groups(16, 0.05, 128, eta=eta)


@pytest.mark.parametrize('m,delta,B', [(0, .05, 128), (1, 0, 128), (1, 1, 128),
                                      (1, float('nan'), 128), (1, .05, 0)])
def test_invalid_selector_inputs_are_rejected(m, delta, B):
    with pytest.raises(CertificationError):
        exact_binomial_groups(m, delta, B)


def test_infeasible_group_count_abstains_and_does_not_reduce_k():
    with pytest.raises(CertificationError, match='EXACT_BINOMIAL_NO_FEASIBLE_K'):
        exact_binomial_groups(16, .05, 17)
    assert exact_binomial_groups(16, .05, 18)['K'] == 9
    with pytest.raises(CertificationError, match='EXACT_BINOMIAL_NO_FEASIBLE_K'):
        exact_binomial_groups(1, .05, 1)


def test_complete_unequal_groups_keep_stable_target_and_explicit_radius_gain():
    old_K, new_K = required_groups(16, .05), exact_binomial_groups(16, .05, 128)['K']
    groups = partition_blocks(128, new_K)
    assert sorted(map(len, groups)) == [14]*7+[15]*2
    assert [b for group in groups for b in group] == list(range(128))
    assert mom_estimate([7.0]*128, groups) == 7.0
    for p in (1.2, 1.5, 2):
        old = mom_radius(p, 1, 1, 64, 128//old_K)
        new = mom_radius(p, 1, 1, 64, 128//new_K)
        assert new/old == pytest.approx(7**(-(p-1)/p))


def test_independent_heterogeneous_bad_indicators_are_binomial_dominated():
    probabilities = [Fraction(0), Fraction(1, 32), Fraction(1, 16), Fraction(1, 8), Fraction(1, 10)]
    probability_of_bad_majority = Fraction()
    for indicators in product((0, 1), repeat=5):
        mass = Fraction(1)
        for indicator, probability in zip(indicators, probabilities):
            mass *= probability if indicator else 1-probability
        if sum(indicators) >= 3:
            probability_of_bad_majority += mass
    assert probability_of_bad_majority <= binomial_majority_tail_fraction(5)


def test_even_median_requires_tie_failure_event_and_new_selector_is_odd():
    # Two bad values can pull the average of two central statistics out of
    # [-1,1]; the valid sufficient even-K event is bad count >=K/2.
    values = [0, 0, 10, 10]
    assert mom_estimate(values, ((0,), (1,), (2,), (3,))) > 1
    assert binomial_majority_tail_fraction(4) == sum(
        (Fraction(comb(4, j)*7**(4-j), 8**4) for j in range(2, 5)), Fraction())
    assert exact_binomial_groups(1, .05, 128)['K'] % 2 == 1

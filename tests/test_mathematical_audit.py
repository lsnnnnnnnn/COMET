"""Exact finite-space checks for the disputed proof steps, not coverage claims."""
from itertools import product
from statistics import mean, median

import pytest


def test_false_centering_inequality_counterexample():
    e, p = 0.1, 1.5
    centered = (1-e)*e**p + e*(1-e)**p
    assert centered == pytest.approx(0.11384199576606167)
    assert centered > e  # raw p-moment of Bernoulli(e)
    assert centered <= 2**p * e  # the valid general centering bound


@pytest.mark.parametrize('p', [1.01, 1.2, 1.5, 2.0])
@pytest.mark.parametrize('n', [1, 2, 17, 256, 2048])
@pytest.mark.parametrize('nu', [0.2, 1.0, 4.0])
@pytest.mark.parametrize('chi', [1, 4, 16])
def test_corrected_lecam_construction_all_constants(p, n, nu, chi):
    epsilon = 1/(2*n)
    a = nu*(2*epsilon)**(-1/p)
    delta = epsilon*a
    centered = (1-epsilon)*delta**p + epsilon*abs(a-delta)**p
    overlap = (1-epsilon)**n
    assert centered <= nu**p*(1+1e-12)
    assert 2*epsilon*a**p == pytest.approx(nu**p)
    assert delta == pytest.approx(nu/2*n**(-(p-1)/p))
    assert overlap >= 0.5-1e-12
    # Direct common-measure Le Cam: max risk >= delta*overlap/2.
    n_rows = n*chi
    explicit_lower_bound = nu/8*(chi/n_rows)**((p-1)/p)
    assert delta*overlap/2 >= explicit_lower_bound*(1-1e-12)


@pytest.mark.parametrize('n', [1, 2, 4, 8])
def test_lecam_product_total_variation_by_complete_enumeration(n):
    e = 1/(2*n)
    total_variation = 0.0
    total_probability = 0.0
    for sample in product((0, 1), repeat=n):
        p1 = e**sum(sample)*(1-e)**(n-sum(sample))
        p0 = float(not any(sample))
        total_probability += p1
        total_variation += abs(p0-p1)/2
    assert total_probability == pytest.approx(1)
    assert total_variation == pytest.approx(1-(1-e)**n)
    assert total_variation <= 0.5 + 1e-12


def test_crossfit_joint_conditioning_counterexample():
    samples = list(product((-1, 1), repeat=3))
    conditioned = [y for y in samples if (y[1]*y[2], y[0]*y[2], y[0]*y[1]) == (1, 1, 1)]
    assert len(conditioned) == 2
    assert mean(y[0] for y in conditioned) == mean(y[1] for y in conditioned) == 0
    assert mean(y[0]*y[1] for y in conditioned) == 1
    assert mean(y[0] == 1 and y[1] == 1 for y in conditioned) == 0.5
    # Each fit is independently trained relative to its own evaluation row.
    for own_value in (-1, 1):
        fits = [y[1]*y[2] for y in samples if y[0] == own_value]
        assert mean(fits) == 0


def test_mutual_crossfit_scores_are_correlated_and_self_leak_is_biased():
    score_pairs = [(s2+2*s1*(1-s2), s1+2*s2*(1-s1))
                   for s1, s2 in product((0, 1), repeat=2)]
    assert mean(z[0] for z in score_pairs) == mean(z[1] for z in score_pairs) == 1
    assert mean(z[0]*z[1] for z in score_pairs)-1 == 0.25
    leaky_scores = [s+2*s*(1-s) for s in (0, 1)]
    assert mean(leaky_scores) == 0.5  # target under q(1)=1 is 1


def test_adaptive_context_changes_conditional_centering():
    samples = [(u, u+v) for u, v in product((-1, 1), repeat=2)]
    assert mean(z1 for z1, _ in samples) == mean(z2 for _, z2 in samples) == 0
    assert mean(z1*z2 for z1, z2 in samples) == 1
    assert mean(z1 for z1, _ in samples if z1 == 1) == 1
    # On path U=1, the predictable target (0+U)/2 differs from
    # the target after conditioning on the future-derived design X2=U.
    assert 0.5 != mean((z1+z2)/2 for z1, z2 in samples if z1 == 1)


def test_martingale_difference_bad_indicators_need_not_be_independent():
    draws = [(u, abs(u)*v) for u, v in product((-2, -1, 1, 2), (-1, 1))]
    for u in (-2, -1, 1, 2):
        assert mean(z2 for z1, z2 in draws if z1 == u) == 0
    assert all((abs(z1)>1.5) == (abs(z2)>1.5) for z1, z2 in draws)


def test_finite_beta_integrated_moment_does_not_bound_conditional_moment():
    # e~Beta(a,1), S|e~Bernoulli(e), R symmetric +/-1, Z=S*R/e.
    # Integrating the exact conditional moment gives a/(a+1-p).
    p, a = 1.5, 1.0
    integrated = a/(a+1-p)
    conditional = 1e-12*(1/1e-12)**p
    assert integrated == 2
    assert conditional == pytest.approx(1e6)
    assert conditional > integrated
    # At a=p-1 the truncated integral diverges logarithmically.
    from math import log
    a_boundary = p-1
    assert a_boundary*log(1/1e-12) > a_boundary*log(1/1e-6)


def test_average_moment_and_oracle_moment_are_insufficient():
    p, n = 1.5, 16
    row_moments = [n]+[0]*(n-1)
    assert mean(row_moments) == 1 and max(row_moments) == n
    c = 3
    implemented = [c*(1-2*s) for s in (0, 1)]
    assert mean(implemented) == 0
    assert mean(abs(z)**p for z in implemented) == pytest.approx(c**p)
    assert c**p > 0  # oracle score is identically zero when all Y(s)=0


def test_window_average_nuisance_bias_does_not_control_mom_bias():
    # Repeat each deterministic group into complete blocks: B>=2K.
    group_biases = [0, 1, 1]
    blocks = [bias for bias in group_biases for _ in range(2)]
    assert len(blocks) == 2*len(group_biases)
    assert median(group_biases) > mean(abs(x) for x in blocks)
    assert median([0, 0, 3]) != mean([0, 0, 3])


def test_pairwise_independence_is_not_a_dependency_graph():
    samples = [(u, v, u*v) for u, v in product((-1, 1), repeat=2)]
    for i, j in ((0, 1), (1, 2), (0, 2)):
        assert mean(z[i]*z[j] for z in samples) == 0
    assert mean(z[0]*z[1]*z[2] for z in samples) == 1


def test_conditioning_on_coupling_success_can_destroy_independence():
    independent = list(product((-1, 1), repeat=2))
    assert mean(a*b for a, b in independent) == 0
    event = [(a,b) for a,b in independent if a == b]
    assert mean(a*b for a,b in event) == 1



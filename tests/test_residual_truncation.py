"""Deterministic proof/code fixtures; these draw no scientific outcomes."""
import itertools
import math

import numpy as np
import pytest

from comet.queries import SignedQuery
from comet.source_graph import SourceGraph
from comet.residual_truncation import (
    AssumptionContract, NonidentifiedError, bounded_residual_moments,
    certified_decision, clipping_bias_constant, make_plan,
    pareto_source_residual_moments, residual_moment_envelope,
    truncation_components,
)


GRID = (.25, .5, 1., 2., 4.)  # A test grid, not the missing blueprint's freeze.
CONTRACT = AssumptionContract(True, True, True, True, True, True, True,
    "test independent primitive probability space", "analytic fixture",
    "deterministic exogenous design; no fitted nuisance")


def plan(d, *, n=None, p=2., e=None, fit=None, b=None, graph=None,
         method="truncated_local", offset=0., normalizer=1., bounded=False):
    d = np.asarray(d, dtype=float)
    n = len(d)
    e = np.full_like(d, .5) if e is None else np.asarray(e)
    fit = np.full_like(d, .5) if fit is None else np.asarray(fit)
    b = bounded_residual_moments(0, 1, fit, p) if b is None else b
    graph = graph or SourceGraph.from_sources([{i} for i in range(n)])
    return make_plan(SignedQuery("fixture", d, offset, normalizer=normalizer),
        e, fit, b, graph, CONTRACT, p=p, delta=.05, family_size=1,
        multipliers=GRID, method=method,
        outcome_bounds=(0, 1) if bounded else None, mean_bounds=(0, 1))


def evaluate(frozen, actions, y):
    return frozen.evaluate(np.array(actions, dtype=int), y, data_digest="fixture",
        seed_namespace="deterministic-test", code_hash="test", config_hash="test")


@pytest.mark.parametrize("p", [1.000001, 1.1, 1.5, 2.])
def test_sharp_bias_and_truncated_second_moment(p):
    cp = clipping_bias_constant(p)
    # Includes the equality point p/(p-1), and tests both residual signs.
    xs = np.r_[np.logspace(-4, 8, 500), p / (p - 1)]
    assert np.all(np.maximum(xs - 1, 0) <= cp * xs ** p * (1 + 2e-14))
    assert abs((p / (p - 1) - 1) / (p / (p - 1)) ** p - cp) < 1e-14
    assert np.all(np.minimum(xs, 1) ** 2 <= xs ** p * (1 + 1e-14))
    assert np.max(np.abs(np.clip(np.r_[xs, -xs], -1, 1) - .3)) <= 2


def test_bias_domain_is_not_silently_extended():
    assert min(.1, 1) ** 2 > .1 ** 3
    with pytest.raises(ValueError):
        clipping_bias_constant(3.)


def test_finite_enumeration_dr_signed_contrast_identity():
    e = np.array([[.8, .2], [.3, .7]])
    mu = np.array([[.2, .9], [.7, .1]])
    fit = np.array([[.9, .1], [.2, .8]])  # deliberately wrong fixed fit
    d = np.array([[.4, -.4], [-.2, .2]])
    offset = np.array([.1, -.05])
    for i in range(2):
        expected = 0.
        for s in range(2):
            for y in (0, 1):
                prob = e[i, s] * (mu[i, s] if y else 1 - mu[i, s])
                z = (d[i] * fit[i]).sum() - offset[i] + d[i, s] / e[i, s] * (y - fit[i, s])
                expected += prob * z
        assert expected == pytest.approx((d[i] * mu[i]).sum() - offset[i])


def test_historical_A_hoeffding_is_analytic_not_new_empirical_power():
    n = 8192
    frozen = plan(np.full((n, 2), .5), method="graph_hoeffding",
                  offset=.25, bounded=True)
    radius = math.sqrt(math.log(40) / (2 * n))
    assert frozen.radius == pytest.approx(0.015005043614373761)
    assert frozen.radius == pytest.approx(radius)
    target, threshold = .2375, .2
    gamma = target - threshold
    assert gamma == pytest.approx(.0375)
    assert gamma > 2 * radius
    # The worst estimate on the coverage event still certifies a violation.
    assert target - 2 * radius > threshold
    assert math.sqrt(16) * radius > radius  # no transfer of m=1 to m=16


def test_same_actual_residual_range_and_variance_for_bounded_methods():
    fit = np.array([[.5, .5], [.2, .8]])
    b = bounded_residual_moments(0, 1, fit, 2)
    assert b == pytest.approx(np.array([[.25, .25], [.64, .64]]))
    d = np.full((2, 2), .5)
    local = plan(d, fit=fit, method="comet_local", bounded=True)
    matched = plan(d, fit=fit, method="generic_matched", bounded=True)
    assert local.radius == matched.radius
    assert local.selected_method == matched.selected_method
    assert evaluate(local, [0, 1], [.1, .6])["estimate"] == evaluate(
        matched, [0, 1], [.1, .6])["estimate"]


def test_heterogeneous_means_and_unequal_colors_keep_raw_row_target():
    graph = SourceGraph.from_sources([{"a"}, {"a", "b"}, {"b"}, {"private"}])
    d = np.full((4, 2), .5)
    frozen = plan(d, graph=graph, method="graph_hoeffding", bounded=True)
    result = evaluate(frozen, [0, 0, 0, 0], [.1, .3, .6, .9])
    assert result["estimate"] == pytest.approx((.1 + .3 + .6 + .9) / 4)
    assert frozen.n == 4 and frozen.active_rows == 4
    assert result["raw_N"] == 4


def test_query_locality_omits_outside_difficulty_without_losing_shared_edges():
    graph = SourceGraph.from_sources([{"shared"}, {"shared"}, {"hub"}, {"hub"}, {"hub"}])
    d = np.array([[.5, .5], [.5, .5], [0, 0], [0, 0], [0, 0]])
    e = np.array([[.5, .5], [.5, .5], [.9999, .0001], [.9999, .0001], [.9999, .0001]])
    local = plan(d, e=e, graph=graph)
    assert local.active_rows == 2 and local.color_count == 2
    assert graph.color_count == 3
    e[2:] = [.5, .5]
    unchanged = plan(d, e=e, graph=graph)
    assert local.radius == unchanged.radius


@pytest.mark.parametrize("method", ["truncated_local", "graph_hoeffding", "graph_bernstein",
                                   "colorwise_truncation", "comet_local"])
def test_paired_small_step_scales_signal_and_radius(method):
    d = np.array([[-.2, .2], [.1, -.1], [-.4, .4], [.2, -.2]])
    base = plan(d, method=method, bounded=True)
    for eta in (.1, .25, .5, 1.):
        scaled = plan(eta * d, method=method, bounded=True)
        assert scaled.radius == pytest.approx(eta * base.radius)
        expected = evaluate(base, [0, 1, 0, 1], [.2, .7, .4, .9])["estimate"]
        assert evaluate(scaled, [0, 1, 0, 1], [.2, .7, .4, .9])["estimate"] == pytest.approx(eta * expected)
    zero = plan(np.zeros_like(d), method=method, bounded=True)
    assert zero.radius == 0.


def test_support_refusal_zero_normalizer_and_tuning_boundary():
    with pytest.raises(NonidentifiedError):
        plan([[0, 1]], e=[[1, 0]])
    d = np.array([[1., 0.]])
    assert residual_moment_envelope(d, [[1, 0]], [[.25, .25]], 2) == pytest.approx([.25])
    with pytest.raises(ValueError):
        SignedQuery("zero_mass", d, 0, normalizer=0)
    q = SignedQuery("q", [[.5, .5]], 0)
    graph = SourceGraph.from_sources([{"one"}])
    with pytest.raises(ValueError, match="outcome-based tuning"):
        make_plan(q, [[.5, .5]], [[.5, .5]], [[.25, .25]], graph, CONTRACT,
            p=2, delta=.05, family_size=1, multipliers=GRID, tuning="outcome")


def test_query_cannot_expand_rows_by_broadcast_and_observed_support_is_checked():
    q = SignedQuery("one_row", [[1., 0.]], .3)
    graph = SourceGraph.from_sources([{0}, {1}])
    with pytest.raises(ValueError, match="cannot change query"):
        make_plan(q, [[1., 0.], [1., 0.]], [[.5, .5]], [[.25, .25]],
            graph, CONTRACT, p=2, delta=.05, family_size=1, multipliers=GRID)
    frozen = plan([[1., 0.]], e=[[1., 0.]])
    with pytest.raises(ValueError, match="zero probability"):
        evaluate(frozen, [1], [0.])


def test_coloring_holder_mgf_by_complete_primitive_enumeration():
    # X0=A, X1=(A+B)/2, X2=B. Nonadjacent endpoints share no source.
    # Color classes {0,2}, {1}; means differ after deterministic offsets.
    for lam in (.01, .1, .3):
        values = [np.array([a, (a+b)/2, b]) for a,b in itertools.product((-1., 1.), repeat=2)]
        exact_mgf = np.mean([math.exp(lam * x.sum()) for x in values])
        chi, v_sum, max_centered_bound = 2, 3., 2.
        log_bound = chi * v_sum * lam**2 / (2 * (1 - chi * max_centered_bound * lam / 3))
        assert math.log(exact_mgf) <= log_bound
        # Deterministic unequal means cancel by centering, without equal-block targets.
        offsets = np.array([.1, .7, -.4])
        assert all(np.sum((x + offsets) - offsets) == pytest.approx(np.sum(x)) for x in values)


def test_heavy_source_envelope_and_moment_domain():
    fit = np.full((3, 2), .5)
    b = pareto_source_residual_moments(0, 1, fit, 1.5, 1.75,
                                     np.full((3, 2), .05))
    expected = (.5 + .1 * 7 ** (1 / 1.5)) ** 1.5
    assert b == pytest.approx(np.full((3, 2), expected))
    with pytest.raises(ValueError, match="diverges"):
        pareto_source_residual_moments(0, 1, fit, 2, 1.75, [.1])


def test_bias_is_present_and_empty_intersection_cannot_issue_safe_claim():
    frozen = plan([[.5, .5]])
    assert frozen.bias_piece > 0
    result = evaluate(frozen, [1], [1e6])
    result.update(lo=2., hi=1., empty_intersection=True)
    assert certified_decision(result, 1.5) == "ABSTAIN"
    assert set(("bias", "concentration", "range_contribution", "data_digest",
                "code_hash", "config_hash", "coloring_count", "normalizer")) <= result.keys()


def test_gamma_greater_than_r_is_not_nominal_power_condition():
    r, gamma = .1, .15
    assert gamma > r and not gamma > 2 * r
    assert gamma - 2 * r < 0  # at an admissible coverage-event estimate, LCB fails

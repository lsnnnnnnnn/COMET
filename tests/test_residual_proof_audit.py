"""Independent finite-enumeration proof fixtures; no random draws or E0 replay."""
import itertools
import math

import numpy as np
import pytest

from comet.queries import SignedQuery
from comet.source_graph import SourceGraph
from comet.residual_truncation import AssumptionContract, make_plan


CONTRACT = AssumptionContract(True, True, True, True, True, True, True,
    "enumerated independent primitive space", "finite exact envelope",
    "fixed deterministic fixture")
GRID = (.25, .5, 1., 2., 4.)  # Test-only; no scientific protocol is frozen here.


def test_clipped_heterogeneous_connected_cycle_mgf_by_complete_enumeration():
    # One connected cycle, with distinct means, not independent macro-blocks.
    sources = np.array(list(itertools.product((-1., 1.), repeat=4)))
    locations = np.array([-.7, .1, .8, -.2])
    residual = locations + .2 * sources + .4 * np.roll(sources, -1, axis=1)
    p, tau, chi = 1.5, .55, 2
    v = np.mean(np.abs(residual) ** p, axis=0)
    clipped = np.clip(residual, -tau, tau)
    centered = clipped - np.mean(clipped, axis=0)
    assert len(np.unique(np.mean(residual, axis=0))) == 4
    assert np.max(np.abs(centered)) <= 2 * tau
    assert np.all(np.mean(clipped ** 2, axis=0) <= v * tau ** (2 - p))
    graph = SourceGraph.from_sources([{i, (i + 1) % 4} for i in range(4)])
    assert graph.edge_count == 4 and graph.color_count == chi
    total_variance_proxy = float(np.sum(v * tau ** (2 - p)))
    for lam in (-.7, -.3, -.01, .01, .3, .7):
        log_mgf = math.log(float(np.mean(np.exp(lam * centered.sum(axis=1)))))
        bound = chi * lam ** 2 * total_variance_proxy / (
            2 * (1 - 2 * chi * tau * abs(lam) / 3))
        assert log_mgf <= bound + 1e-14


def test_raw_moment_is_essential_even_when_centered_variance_is_zero():
    # A deterministic raw residual can have nonzero clipping bias.
    tau, p, raw = 1.3, 2., 2.6
    clipped = min(raw, tau)
    cp = (p - 1) ** (p - 1) / p ** p
    bias = raw - clipped
    raw_moment = raw ** p
    centered_moment = 0.
    assert bias == pytest.approx(cp * raw_moment * tau ** (1 - p))
    assert bias > cp * centered_moment * tau ** (1 - p)


def test_colorwise_unequal_sizes_and_normalizer_match_scalar_proof():
    graph = SourceGraph.from_sources([
        {"a"}, {"a", "b"}, {"b", "c"}, {"c"}, {"private"}])
    d = np.array([[.3, -.1], [-.2, .4], [.1, .2], [-.3, .1], [.2, -.4]])
    e = np.array([[.2, .8], [.4, .6], [.7, .3], [.6, .4], [.3, .7]])
    fit = np.array([[.2, .6], [.8, .1], [.4, .7], [.5, .3], [.1, .8]])
    offset = np.array([.1, -.2, .05, .3, -.1])
    norm, p, delta, family = .37, 1.5, .05, 3
    moments = np.maximum(np.abs(fit), np.abs(1 - fit)) ** p
    query = SignedQuery("unequal_color_signed", d, offset, normalizer=norm)
    plan = make_plan(query, e, fit, moments, graph, CONTRACT, p=p,
        delta=delta, family_size=family, multipliers=GRID,
        method="colorwise_truncation")
    actions = np.array([0, 1, 0, 1, 0], dtype=int)
    outcome = np.array([.1, .9, .3, .7, .2])
    result = plan.evaluate(actions, outcome, data_digest="enumerated",
        seed_namespace="deterministic-proof-test", code_hash="test", config_hash="test")
    direct = sum(float(np.dot(d[i], fit[i])) - offset[i] for i in range(5)) / 5
    stochastic = 0.
    for i in range(5):
        raw = d[i, actions[i]] / e[i, actions[i]] * (outcome[i] - fit[i, actions[i]])
        tau = plan.row_thresholds[i]
        stochastic += min(max(raw, -tau), tau)
    assert result["estimate"] == pytest.approx((direct + stochastic / 5) / norm)
    colors = graph.induced(np.ones(5, dtype=bool)).colors
    assert len(set(np.bincount(colors))) > 1  # color sizes actually differ
    chi = len(np.unique(colors))
    t = math.log(2 * family * chi / delta)
    cp = (p - 1) ** (p - 1) / p ** p
    v = np.sum(np.abs(d) ** p * e ** (1 - p) * moments, axis=1)
    pieces = np.zeros(3)
    for color in np.unique(colors):
        idx = np.flatnonzero(colors == color)
        thresholds = plan.row_thresholds[idx]
        assert np.all(thresholds == thresholds[0])
        tau = thresholds[0]
        pieces += [cp * float(v[idx].sum()) * tau ** (1 - p) / 5,
                   math.sqrt(2 * t * float(v[idx].sum()) * tau ** (2 - p)) / 5,
                   2 * tau * t / (3 * 5)]
    assert [plan.bias_piece, plan.variance_piece, plan.range_piece] == pytest.approx(pieces)
    assert plan.radius == pytest.approx(float(pieces.sum()) / norm)


def test_thinned_clique_lower_bound_common_mass_and_absolute_risk_constant():
    n, epsilon, p, nu, cap = 3, .4, 1.5, .3, .4
    t = min(1., 1 / (2 * n * epsilon))
    a = min(cap / t, nu * t ** (-1 / p))
    separation = a * t  # means are b +/- separation; their distance is twice it
    laws = []
    for sign in (-1, 1):
        values = [(0, 0., 1 - epsilon), (1, 0., epsilon * (1 - t)),
                  (1, sign * a, epsilon * t)]
        law = {}
        for rows in itertools.product(values, repeat=n):
            observation = tuple((row[0], row[1]) for row in rows)
            probability = math.prod(row[2] for row in rows)
            law[observation] = law.get(observation, 0.) + probability
        assert sum(law.values()) == pytest.approx(1.)
        laws.append(law)
    all_observations = set(laws[0]) | set(laws[1])
    common = sum(min(laws[0].get(x, 0.), laws[1].get(x, 0.)) for x in all_observations)
    tv = 1 - common
    assert tv == pytest.approx(1 - (1 - epsilon * t) ** n)
    assert tv <= .5
    assert a ** p * t <= nu ** p * (1 + 1e-14)
    assert separation <= cap
    # On shared observations, any T obeys |T-d|+|T+d| >= 2d.
    for estimate in (-2., -.1, 0., .1, 2.):
        assert (abs(estimate - separation) + abs(estimate + separation)) * common >= 2 * separation * common - 1e-14
    # Divide the risk-sum bound by two, then use common>=.5.
    assert separation * common >= separation / 2

"""Explicit primitive fixtures only: these tests consume no Monte Carlo units."""

import numpy as np
import pytest

from experiments.core_graph_dgp import (
    TAIL_EXPONENT, WORD_GRID, build_core_design, dyadic_probabilities,
    evaluate_oracle, generate_from_primitives,
)


def fixture(design, sign=1, action=1):
    words = np.full(design.n, 0 if action else WORD_GRID - 1, dtype=np.uint64)
    primitives = {source: float(sign) for source in design.outcome_source_ids}
    return generate_from_primitives(design, words, primitives)


@pytest.mark.parametrize("graph_kind,colors,edges", [
    ("independent", 1, 0), ("cycle", 2, 16), ("triangles", 3, 29),
])
def test_graphs_follow_whole_source_incidence_without_copying(graph_kind, colors, edges):
    design = build_core_design(16, graph_kind=graph_kind, namespace="fixture")
    assert design.graph.color_count == colors
    assert design.graph.edge_count == edges
    assert len(design.queries) == 16
    assert design.x.shape == (16, 4)
    assert np.all(np.abs(design.x) <= 1)
    assert np.all(design.exposure.sum(axis=1) == 1)
    assert np.all(design.nuisance == 0.5)
    assert np.all(design.residual_moments == 0.25)
    assert np.all(np.sum(np.abs(design.outcome_source_coefficients), axis=1) <= 0.1 + 1e-15)
    if graph_kind != "independent":
        reached, frontier = {0}, [0]
        while frontier:
            row = frontier.pop()
            for neighbor in design.graph.adjacency[row] - reached:
                reached.add(neighbor)
                frontier.append(neighbor)
        assert len(reached) == design.n
    # Private sources and varying locations prevent exact replicated records.
    assert len({frozenset(row) for row in design.row_sources}) == design.n
    log = fixture(design)
    assert np.ptp(log.outcomes) > 0.01


def test_dyadic_rounding_and_integer_actions_define_the_actual_exact_e():
    cutoffs, values = dyadic_probabilities(np.array([0, 0.5, 1, 0.123]))
    assert cutoffs.tolist()[:3] == [0, 2**31, WORD_GRID]
    assert np.all(values * WORD_GRID == cutoffs)
    design = build_core_design(8, overlap="weak")
    assert np.all((design.exposure[:, 1] >= 0.005) & (design.exposure[:, 1] <= 0.05))
    words = design.logging_cutoffs.copy()
    words[::2] -= 1
    log = generate_from_primitives(design, words,
        {source: 1 for source in design.outcome_source_ids})
    assert log.actions.tolist() == [1, 0] * 4
    with pytest.raises(ValueError, match="32-bit-range"):
        generate_from_primitives(design, np.full(8, WORD_GRID),
            {source: 1 for source in design.outcome_source_ids})


def test_certifier_dictionary_has_no_locations_truth_or_outcomes():
    design = build_core_design(8, graph_kind="cycle", outcome="heavy")
    allowed = {"exposure", "nuisance", "residual_moments", "graph", "contract", "p", "outcome_bounds", "mean_bounds"}
    assert set(design.certifier_inputs) == allowed
    assert design.certifier_inputs["outcome_bounds"] is None
    design.certifier_inputs["contract"].require()
    assert design.p == 1.5
    assert np.isfinite(design.residual_moments).all()
    assert np.all(design.residual_moments > 0.5**1.5)
    assert not hasattr(design, "mu") and not hasattr(design, "oracle")


def test_explicit_sign_enumeration_recovers_heterogeneous_mean_target():
    design = build_core_design(8, graph_kind="triangles")
    # Four deterministic assignments of source signs and action words recover
    # both potential means. This is a finite identity check, not a trial.
    response_means = np.column_stack([
        (fixture(design, 1, action).outcomes + fixture(design, -1, action).outcomes) / 2
        for action in (0, 1)
    ])
    assert np.all((response_means >= 0) & (response_means <= 1))
    assert np.ptp(response_means[:, 0]) > 0.01
    truth = evaluate_oracle(design)
    for query in design.queries:
        assert query.target(response_means) == pytest.approx(truth[query.query_id])
        query.validate_support(design.exposure)
    for sign in (-1, 1):
        for action in (0, 1):
            log = fixture(design, sign, action)
            assert np.all((log.outcomes >= 0) & (log.outcomes <= 1))


def test_source_namespaces_separate_whole_primitive_pools():
    training = build_core_design(8, namespace="training")
    certification = build_core_design(8, namespace="certification")
    assert training.source_ids.isdisjoint(certification.source_ids)
    same_namespace = build_core_design(8, namespace="training")
    assert training.source_ids == same_namespace.source_ids


def test_finite_pareto_midpoint_grid_moment_domination_is_not_infinite_variance():
    p = 1.5
    # Deterministic midpoint sums: convexity/Jensen bounds each by the ideal
    # integral. The same argument applies to the production 2**32 grid.
    ideal = TAIL_EXPONENT / (TAIL_EXPONENT - p)
    for count in (8, 32, 128):
        u = (np.arange(count) + 0.5) / count
        assert np.mean(u ** (-p / TAIL_EXPONENT)) < ideal
    design = build_core_design(8, outcome="heavy")
    log = fixture(design, -1, 0)
    assert np.isfinite(log.outcomes).all()
    with pytest.raises(ValueError, match="Pareto support"):
        generate_from_primitives(design, np.zeros(8, dtype=np.uint32),
            {source: 0.5 for source in design.outcome_source_ids})


def test_fixture_digest_and_observed_arrays_are_deterministic_and_readonly():
    design = build_core_design(8)
    first, second = fixture(design), fixture(design)
    assert first.data_digest == second.data_digest
    assert first.data_digest != fixture(design, -1).data_digest
    with pytest.raises(ValueError):
        first.outcomes[0] = 0
    with pytest.raises(ValueError):
        design.exposure.setflags(write=True)

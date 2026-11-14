"""Deterministic graph/query fixtures for the heterogeneous global model."""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from comet.queries import SignedQuery
from comet.source_graph import SourceGraph, greedy_coloring, verify_coloring


def test_shared_star_source_projects_to_clique_not_domain_star():
    graph = SourceGraph.from_sources([{"central", f"private-{i}"} for i in range(4)])
    assert graph.edge_count == 6
    assert graph.color_count == 4
    with pytest.raises(ValueError, match="share a color"):
        verify_coloring(graph.adjacency, [0, 1, 1, 1])


def test_induced_support_keeps_retained_shared_source_edge_and_row_ids():
    graph = SourceGraph.from_sources([{"x"}, {"x", "y"}, {"x", "z"}, {"z"}])
    active = graph.induced([True, False, True, True])
    assert active.row_ids == (0, 2, 3)
    assert active.adjacency == (frozenset({1}), frozenset({0, 2}), frozenset({1}))
    assert active.color_count == 2
    assert active.induced([False, True, True]).row_ids == (2, 3)


def test_cycle_is_connected_and_not_replicated_cliques():
    n = 8
    graph = SourceGraph.from_sources([{("shock", i), ("shock", (i + 1) % n)} for i in range(n)])
    assert graph.edge_count == n
    assert all(len(row) == 2 for row in graph.adjacency)
    assert graph.color_count == 2
    assert verify_coloring(graph.adjacency, graph.colors) == 2
    assert np.array_equal(greedy_coloring(graph.adjacency), graph.colors)


def test_induced_keeps_better_available_restricted_coloring_than_new_greedy():
    # Crown K3,3 minus a matching in interleaved order: degree-first greedy
    # uses three colors, while this already verified bipartition uses two.
    adjacency = tuple(frozenset(j for j in range(6)
                                if i % 2 != j % 2 and i // 2 != j // 2)
                      for i in range(6))
    graph = SourceGraph(adjacency, np.array([7, 9, 7, 9, 7, 9]), tuple(range(6)))
    assert len(np.unique(greedy_coloring(adjacency))) == 3
    assert graph.induced(np.ones(6, dtype=bool)).color_count == 2
    assert set(graph.colors) == {0, 1}


def test_empty_graph_and_source_free_rows():
    empty = SourceGraph.from_sources([])
    assert empty.n_rows == empty.color_count == empty.edge_count == 0
    assert empty.induced(np.array([], dtype=bool)).row_ids == ()
    graph = SourceGraph.from_sources([set(), set()])
    assert graph.color_count == 1
    assert graph.edge_count == 0
    assert graph.induced([False, False]).color_count == 0


def test_clique64_sparse_adjacency_and_invalid_graphs():
    graph = SourceGraph.from_sources([{"one-source"}] * 64)
    assert graph.color_count == 64
    assert graph.edge_count == 64 * 63 // 2
    with pytest.raises(ValueError, match="symmetric"):
        greedy_coloring([{1}, set()])
    with pytest.raises(ValueError, match="boolean"):
        graph.induced(np.arange(64))
    with pytest.raises(ValueError, match="one nonnegative integer"):
        verify_coloring(graph.adjacency, np.zeros(64))


def test_arrays_and_dataclasses_are_immutable_and_copy_inputs():
    d = np.array([[0.3, -0.3], [0.1, -0.1]])
    query = SignedQuery("contrast", d, np.zeros(2))
    d[:] = 9
    assert query.coefficients[0, 0] == 0.3
    with pytest.raises(ValueError):
        query.coefficients[0, 0] = 0
    with pytest.raises(ValueError):
        query.coefficients.setflags(write=True)
    with pytest.raises(FrozenInstanceError):
        query.normalizer = 2
    graph = SourceGraph.from_sources([{"a"}, {"a"}])
    with pytest.raises(ValueError):
        graph.colors.setflags(write=True)


def test_signed_and_zero_contrast_targets_preserve_all_row_weights():
    means = np.array([[0.1, 0.7], [0.4, 0.6], [0.2, 0.9]])
    d = np.array([[-0.2, 0.2], [0, 0], [-0.6, 0.6]])
    query = SignedQuery("paired", d, 0, normalizer=2 / 3)
    expected = (0.2 * (0.7 - 0.1) + 0.6 * (0.9 - 0.2)) / 3 / (2 / 3)
    assert query.target(means) == pytest.approx(expected)
    assert query.active_mask.tolist() == [True, False, True]
    assert query.n_rows == 3 and query.n_states == 2
    assert SignedQuery("zero", np.zeros((3, 2)), 0).known_term(means) == 0
    assert not SignedQuery("zero", np.zeros((3, 2)), 0).active_mask.any()


def test_nonzero_deterministic_offset_is_kept_on_inactive_rows():
    query = SignedQuery("fixed", np.zeros((3, 2)), np.array([1.0, 2.0, 6.0]))
    assert query.known_term(np.full((3, 2), 0.5)) == -3
    assert not query.active_mask.any()


def test_support_is_signed_coefficient_specific_and_missing_support_refuses():
    e = np.array([[1.0, 0.0], [0.25, 0.75]])
    good = SignedQuery("supported", np.array([[0.2, 0.0], [-0.4, 0.4]]), 0)
    good.validate_support(e)
    bad = SignedQuery("unsupported", np.array([[0.0, -0.2], [0.0, 0.0]]), 0)
    with pytest.raises(ValueError, match="NONIDENTIFIED"):
        bad.validate_support(e)
    with pytest.raises(ValueError, match="distribution"):
        good.validate_support(e / 2)


@pytest.mark.parametrize("normalizer", [0, -1, float("nan"), float("inf")])
def test_zero_mass_and_invalid_normalizers_refuse(normalizer):
    with pytest.raises(ValueError, match="normalizer"):
        SignedQuery("invalid", np.ones((2, 2)), 0, normalizer=normalizer)


def test_shapes_and_nonfinite_values_refuse():
    with pytest.raises(ValueError, match="nonempty N by S"):
        SignedQuery("bad", np.ones(2), 0)
    with pytest.raises(ValueError, match="one value per row"):
        SignedQuery("bad", np.ones((2, 2)), np.zeros(3))
    with pytest.raises(ValueError, match="finite"):
        SignedQuery("bad", np.array([[np.nan, 0]]), 0)

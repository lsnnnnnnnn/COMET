"""Source-incidence dependency graphs for the new heterogeneous-row model.

Conditional sufficiency follows when the declared primitives are jointly
independent and each row is measurable in its listed primitives and the fixed
design.  These routines verify the combinatorial construction, not that an
unobserved data-generating mechanism obeys that declaration.
"""

from dataclasses import dataclass
from typing import Hashable, Iterable, Sequence

import numpy as np


def _readonly_int(values: Sequence[int]) -> np.ndarray:
    array = np.asarray(values, dtype=np.int64)
    return np.frombuffer(array.tobytes(), dtype=np.int64)


def _validated_adjacency(adjacency: Sequence[Iterable[int]]) -> tuple[frozenset[int], ...]:
    neighbors = tuple(frozenset(row) for row in adjacency)
    n = len(neighbors)
    for row, adjacent in enumerate(neighbors):
        for other in adjacent:
            if not isinstance(other, (int, np.integer)) or not 0 <= other < n:
                raise ValueError("graph neighbor is not a valid row index")
            if other == row or row not in neighbors[other]:
                raise ValueError("adjacency must be symmetric and have no self edges")
    return neighbors


def verify_coloring(adjacency: Sequence[Iterable[int]], colors: Sequence[int]) -> int:
    """Return the number of used colors, raising on an improper coloring."""
    neighbors = _validated_adjacency(adjacency)
    values = np.asarray(colors)
    if values.shape != (len(neighbors),) or values.dtype.kind not in "iu":
        raise ValueError("coloring must contain one nonnegative integer per row")
    if np.any(values < 0):
        raise ValueError("coloring must contain nonnegative integers")
    for row, adjacent in enumerate(neighbors):
        if any(values[row] == values[other] for other in adjacent):
            raise ValueError("adjacent rows share a color")
    return len(np.unique(values))


def greedy_coloring(adjacency: Sequence[Iterable[int]]) -> np.ndarray:
    """Deterministic degree-first proper coloring; no optimality claim."""
    neighbors = _validated_adjacency(adjacency)
    colors = np.full(len(neighbors), -1, dtype=np.int64)
    for row in sorted(range(len(neighbors)), key=lambda i: (-len(neighbors[i]), i)):
        used = {int(colors[other]) for other in neighbors[row] if colors[other] >= 0}
        color = 0
        while color in used:
            color += 1
        colors[row] = color
    verify_coloring(neighbors, colors)
    return _readonly_int(colors)


@dataclass(frozen=True, eq=False)
class SourceGraph:
    """A sparse row-intersection graph with a verified available coloring.

    Vertices always use compact local indices. ``row_ids`` retains the original
    row identities through repeated support restrictions.
    """

    adjacency: tuple[frozenset[int], ...]
    colors: np.ndarray
    row_ids: tuple[int, ...]

    def __post_init__(self) -> None:
        adjacency = _validated_adjacency(self.adjacency)
        verify_coloring(adjacency, self.colors)
        row_ids = tuple(self.row_ids)
        if len(row_ids) != len(adjacency) or len(set(row_ids)) != len(row_ids):
            raise ValueError("row_ids must uniquely identify every graph vertex")
        _, compact_colors = np.unique(np.asarray(self.colors), return_inverse=True)
        object.__setattr__(self, "adjacency", adjacency)
        object.__setattr__(self, "colors", _readonly_int(compact_colors))
        object.__setattr__(self, "row_ids", row_ids)

    @classmethod
    def from_sources(cls, row_sources: Iterable[Iterable[Hashable]]) -> "SourceGraph":
        """Join all rows sharing any listed primitive, including whole cliques."""
        source_rows: dict[Hashable, list[int]] = {}
        neighbors: list[set[int]] = []
        for row, sources in enumerate(row_sources):
            neighbors.append(set())
            for source in frozenset(sources):
                source_rows.setdefault(source, []).append(row)
        for rows in source_rows.values():
            for position, row in enumerate(rows):
                for other in rows[position + 1 :]:
                    neighbors[row].add(other)
                    neighbors[other].add(row)
        adjacency = tuple(frozenset(row) for row in neighbors)
        return cls(adjacency, greedy_coloring(adjacency), tuple(range(len(adjacency))))

    @property
    def n_rows(self) -> int:
        return len(self.adjacency)

    @property
    def color_count(self) -> int:
        return len(np.unique(self.colors))

    @property
    def edge_count(self) -> int:
        return sum(map(len, self.adjacency)) // 2

    def induced(self, active_mask: Sequence[bool]) -> "SourceGraph":
        """Restrict vertices, never erase edges between retained shared sources."""
        active = np.asarray(active_mask)
        if active.shape != (self.n_rows,) or active.dtype.kind != "b":
            raise ValueError("active_mask must contain one boolean per graph row")
        rows = np.flatnonzero(active)
        new_index = {int(row): index for index, row in enumerate(rows)}
        adjacency = tuple(
            frozenset(new_index[other] for other in self.adjacency[row] if other in new_index)
            for row in rows
        )
        # Restricting a valid coloring remains valid. A fresh greedy pass can
        # use MORE colors, so retain the better of these two available proofs.
        _, restricted = np.unique(self.colors[rows], return_inverse=True)
        fresh = greedy_coloring(adjacency)
        restricted_count = verify_coloring(adjacency, restricted)
        fresh_count = verify_coloring(adjacency, fresh)
        colors = restricted if restricted_count <= fresh_count else fresh
        return SourceGraph(adjacency, colors, tuple(self.row_ids[row] for row in rows))

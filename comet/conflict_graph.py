"""Sufficient chi-clique graphs for the registered replication DGP."""

from .schema import CertificationError


def clique_graph(n, chi):
    if type(n) is not int or type(chi) is not int or n <= 0 or chi <= 0 or n % chi:
        raise CertificationError("INCOMPLETE_CLIQUE")
    return tuple(tuple(j for j in range((i // chi)*chi, (i // chi+1)*chi) if j != i)
                 for i in range(n))


def greedy_coloring(graph):
    """Deterministic increasing-node greedy order; return actual colors used."""
    n = len(graph)
    for i, neighbors in enumerate(graph):
        for j in neighbors:
            if j < 0 or j >= n or j == i or i not in graph[j]:
                raise CertificationError("INVALID_UNDIRECTED_GRAPH")
    colors = []
    for neighbors in graph:
        used = {colors[j] for j in neighbors if j < len(colors)}
        color = 0
        while color in used:
            color += 1
        colors.append(color)
    return tuple(colors)


def is_proper_coloring(graph, colors):
    return len(colors) == len(graph) and all(colors[i] != colors[j]
        for i, neighbors in enumerate(graph) for j in neighbors)


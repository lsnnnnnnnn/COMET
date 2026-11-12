"""ORACLE ONLY. Never imported by score, graph, robust-mean or certification code."""

from dataclasses import dataclass

RESPONSE_MEANS = ((0.2, 0.6), (0.35, 0.8))


@dataclass(frozen=True)
class OracleTruth:
    moments: dict
    response_means_by_context: tuple
    potential_outcomes: tuple
    target_definition: str = "fixed_design_conditional_expectation_not_realized_potential_mean"


def exact_moments(config):
    """Analytic conditional expectations, never a Monte Carlo truth approximation."""
    clusters = config.n0 // config.chi
    result = {}
    for candidate in config.family:
        values = []
        for cluster in range(clusters):
            x = cluster % 2
            response = sum(q*m for q, m in zip(candidate.q_vector, RESPONSE_MEANS[x]))
            values.append(candidate.h(x) * (response-config.reference))
        result[candidate.candidate_id] = sum(values)/clusters
    return result


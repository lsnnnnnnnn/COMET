"""ORACLE ONLY: exact conditional-window target for final metrics and tests.

No estimator, known-moment calculation or method selector imports this module.
The potential-outcome generator supplies the response location; its target
average is evaluated here, after all candidate certificates are complete.
"""

from math import fsum

from .gate_c_simulation import _response_location


def exact_targets(cell):
    """Return E-based finite-window truth, never realized potential means."""
    cell.validate()
    config = cell.design
    clusters = config.n0 // config.chi
    result = {}
    for candidate in config.family:
        values = []
        for block in range(config.B):
            for cluster in range(clusters):
                context = cluster % 2
                mean = fsum(q*_response_location(context, s, block, cell.stable_targets)
                            for s, q in enumerate(candidate.q_vector))
                values.append(candidate.h(context)*(mean-config.reference))
        # Every cluster has the same chi copies, so this equals raw-row average.
        result[candidate.candidate_id] = fsum(values)/(config.B*clusters)
    return result

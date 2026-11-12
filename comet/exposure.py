"""Exact small-slate probabilities on a common complete-assignment space."""

from itertools import permutations
from math import factorial, fsum, isfinite

from .dr_scores import validate_distribution
from .schema import CertificationError


def plackett_luce_slates(weights, k, uniform_mix=0.0):
    """Ordered sampling without replacement, mixed with UNIFORM COMPLETE slates."""
    if not weights or any(not isfinite(w) or w <= 0 for w in weights):
        raise CertificationError("POSITIVE_PL_WEIGHTS_REQUIRED")
    if type(k) is not int or not 1 <= k <= len(weights):
        raise CertificationError("INVALID_SLATE_SIZE")
    if not isfinite(uniform_mix) or not 0 <= uniform_mix <= 1:
        raise CertificationError("INVALID_COMPLETE_SLATE_MIXTURE")
    uniform = factorial(len(weights)-k) / factorial(len(weights))
    result = {}
    for slate in permutations(range(len(weights)), k):
        probability, selected = 1.0, set()
        for item in slate:
            # Subtracting a dominant weight can round the remaining mass to zero.
            remaining = fsum(weight for j, weight in enumerate(weights) if j not in selected)
            probability *= weights[item] / remaining
            selected.add(item)
        result[slate] = (1-uniform_mix)*probability + uniform_mix*uniform
    validate_distribution(tuple(result.values()))
    return result


def marginalize_exposure(assignments, exposure_map):
    """Sum complete-assignment probability over preimages of g(A)."""
    validate_distribution(tuple(assignments.values()))
    result = {}
    for assignment, probability in assignments.items():
        state = exposure_map(assignment)
        result[state] = result.get(state, 0.0) + probability
    return result


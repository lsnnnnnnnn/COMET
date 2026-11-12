"""Explicit finite-sample constants; see theory/theorem_to_code_contract.md."""

from math import ceil, isfinite, log
from statistics import median

from .schema import CertificationError


def confidence_budget(alpha, epsilon_coup=0.0, delta_aux=0.0):
    """Probability bookkeeping only: this function proves no coupling model."""
    if not all(isfinite(x) for x in (alpha, epsilon_coup, delta_aux)):
        raise CertificationError("NONFINITE_FAILURE_BUDGET")
    if not 0 < alpha < 1 or epsilon_coup < 0 or delta_aux < 0:
        raise CertificationError("INVALID_FAILURE_BUDGET")
    delta_stat = alpha - epsilon_coup - delta_aux
    if delta_stat <= 0:
        raise CertificationError("EXHAUSTED_FAILURE_BUDGET")
    return delta_stat


def required_groups(family_size, delta_stat):
    if type(family_size) is not int or family_size < 1:
        raise CertificationError("EMPTY_OR_INVALID_FAMILY")
    if not isfinite(delta_stat) or not 0 < delta_stat < 1:
        raise CertificationError("INVALID_STATISTICAL_BUDGET")
    return ceil(8 * log(2 * family_size / delta_stat))


def partition_blocks(B, K):
    if type(B) is not int or type(K) is not int or K <= 0 or B < 2*K:
        raise CertificationError("INSUFFICIENT_BLOCKS_B_LT_2K")
    small, extra = divmod(B, K)
    groups, start = [], 0
    for g in range(K):
        size = small + int(g < extra)
        groups.append(tuple(range(start, start + size)))
        start += size
    return tuple(groups)


def mom_estimate(block_means, groups):
    indices = [i for group in groups for i in group]
    if sorted(indices) != list(range(len(block_means))) or any(not group for group in groups):
        raise CertificationError("GROUPS_MUST_USE_EVERY_BLOCK_EXACTLY_ONCE")
    return median(sum(block_means[i] for i in group) / len(group) for group in groups)


def mom_radius(p, nu_p, chi, n0, L_min):
    if not isfinite(p) or not 1 < p <= 2 or not isfinite(nu_p) or nu_p < 0:
        raise CertificationError("INVALID_KNOWN_MOMENT_ENVELOPE")
    if any(type(v) is not int or v <= 0 for v in (chi, n0, L_min)) or chi > n0:
        raise CertificationError("INVALID_RADIUS_DESIGN")
    return 32**(1/p) * nu_p * (chi/(L_min*n0))**((p-1)/p)


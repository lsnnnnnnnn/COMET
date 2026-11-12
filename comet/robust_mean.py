"""Explicit finite-sample constants; see theory/theorem_to_code_contract.md."""

from fractions import Fraction
from math import ceil, comb, isfinite, log, nextafter
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
    try:
        quotient = 2 * family_size / delta_stat
    except OverflowError:
        quotient = float("inf")
    # Preserve the original arithmetic for all finite quotients. For a tiny
    # positive budget the quotient can overflow even though its logarithm and
    # the required integer group count are finite.
    log_quotient = (log(quotient) if isfinite(quotient)
                    else log(2) + log(family_size) - log(delta_stat))
    return ceil(8 * log_quotient)


def _probability_fraction(value, reason):
    """Interpret a supplied decimal probability exactly, or preserve Fraction."""
    try:
        probability = value if isinstance(value, Fraction) else Fraction(str(value))
    except (ValueError, TypeError, ZeroDivisionError) as error:
        raise CertificationError(reason) from error
    if not 0 < probability < 1:
        raise CertificationError(reason)
    return probability


def _upward_float(value):
    """A float upper bound, including positive tails below float underflow."""
    rounded = float(value)
    if Fraction.from_float(rounded) < value:
        rounded = nextafter(rounded, float("inf"))
    return rounded


def binomial_majority_tail_fraction(K, eta=0.125):
    """Exact P[Bin(K,eta)>=ceil(K/2)]; even-K threshold is conservative.

    This is a probability calculation, not an independence/model validator.
    The certified C0 comparison fixes eta=1/8; other eta values need the
    matching (4/eta)^(1/p) radius and a legitimate pre-outcome selection rule.
    """
    if type(K) is not int or K <= 0:
        raise CertificationError("K_MUST_BE_A_POSITIVE_INTEGER")
    probability = _probability_fraction(eta, "INVALID_GROUP_FAILURE_PROBABILITY")
    if probability >= Fraction(1, 2):
        raise CertificationError("ETA_MUST_BE_LESS_THAN_ONE_HALF")
    r, s = probability.numerator, probability.denominator
    first = (K+1)//2
    # Terms share denominator s**K. The recurrence is integer-exact and avoids
    # repeatedly computing binomial coefficients or tiny floating-point powers.
    term = comb(K, first) * r**first * (s-r)**(K-first)
    numerator = term
    for j in range(first, K):
        term = term * (K-j) * r // ((j+1)*(s-r))
        numerator += term
    return Fraction(numerator, s**K)


def binomial_majority_tail(K, eta=0.125):
    """Upward-rounded float diagnostic of the exact rational majority tail."""
    return _upward_float(binomial_majority_tail_fraction(K, eta))


def exact_binomial_groups(family_size, delta_stat, B, eta=0.125):
    """Minimal feasible odd K selected entirely from pre-outcome inputs.

    Exact rational comparison prevents tail underflow or rounding from
    accepting an invalid confidence budget. All B blocks can then be assigned
    by partition_blocks; B>=2K guarantees L_min>=2. See the full conditional
    proof in theory/exact_binomial_mom.md. This function does not verify the
    stable-target or independent-block assumptions.
    """
    if type(family_size) is not int or family_size < 1:
        raise CertificationError("EMPTY_OR_INVALID_FAMILY")
    if type(B) is not int or B < 1:
        raise CertificationError("B_MUST_BE_A_POSITIVE_INTEGER")
    delta = _probability_fraction(delta_stat, "INVALID_STATISTICAL_BUDGET")
    probability = _probability_fraction(eta, "INVALID_GROUP_FAILURE_PROBABILITY")
    if probability >= Fraction(1, 2):
        raise CertificationError("ETA_MUST_BE_LESS_THAN_ONE_HALF")
    for K in range(1, B//2+1, 2):
        tail = binomial_majority_tail_fraction(K, probability)
        family_tail = family_size * tail
        if family_tail <= delta:
            return {
                "K": K,
                "eta": float(probability),
                "eta_exact": str(probability),
                "binomial_failure_bound": _upward_float(tail),
                "binomial_familywise_failure_bound": _upward_float(family_tail),
                "binomial_tail_numerator": str(tail.numerator),
                "binomial_tail_denominator": str(tail.denominator),
                "binomial_familywise_numerator": str(family_tail.numerator),
                "binomial_familywise_denominator": str(family_tail.denominator),
                "delta_stat_exact": str(delta),
            }
    raise CertificationError("EXACT_BINOMIAL_NO_FEASIBLE_K")


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


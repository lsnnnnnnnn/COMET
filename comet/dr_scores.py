"""DR algebra and pre-action, bounded-reward moment envelopes."""

from math import isclose, isfinite

from .schema import CertificationError, SupportError


def validate_distribution(probabilities):
    if not probabilities or any(not isfinite(v) or v < 0 for v in probabilities):
        raise CertificationError("INVALID_PROBABILITY_VECTOR")
    if not isclose(sum(probabilities), 1.0, rel_tol=0, abs_tol=1e-12):
        raise CertificationError("PROBABILITIES_DO_NOT_SUM_TO_ONE")


def validate_support(q, e):
    validate_distribution(q)
    validate_distribution(e)
    if len(q) != len(e):
        raise CertificationError("EXPOSURE_SPACE_MISMATCH")
    if any(qs > 0 and es == 0 for qs, es in zip(q, e)):
        raise SupportError("NONIDENTIFIABLE_TARGET_SUPPORT")


def dr_score(y, exposure, q, e, mu_hat, h=1.0, reference=0.0):
    """Fixed-nuisance score; algebra alone does not certify learned nuisances."""
    validate_support(q, e)
    if len(mu_hat) != len(q) or type(exposure) is not int or not 0 <= exposure < len(q):
        raise CertificationError("EXPOSURE_SPACE_MISMATCH")
    if e[exposure] <= 0:
        raise SupportError("OBSERVED_ZERO_PROBABILITY_EXPOSURE")
    if any(not isfinite(v) for v in (y, h, reference, *mu_hat)):
        raise CertificationError("NONFINITE_SCORE_INPUT")
    augmentation = q[exposure] / e[exposure] * (y - mu_hat[exposure])
    score = h * (sum(qs * mus for qs, mus in zip(q, mu_hat)) + augmentation - reference)
    if not isfinite(score):
        raise CertificationError("NONFINITE_NUMERICAL_SCORE")
    return score


def centered_bounded_envelope(q, e, p):
    """Return nu^p, known before Y: 2^(2p-1)(1+sum q^p e^(1-p))."""
    validate_support(q, e)
    if not isfinite(p) or not 1 < p <= 2:
        raise CertificationError("P_MUST_BE_IN_1_2")
    try:
        importance_moment = sum(qs**p * es**(1-p) for qs, es in zip(q, e) if qs > 0)
        envelope = 2**(2*p-1) * (1 + importance_moment)
    except OverflowError as error:
        raise CertificationError("MOMENT_ENVELOPE_EXCEEDS_FLOAT_RANGE") from error
    if not isfinite(envelope):
        raise CertificationError("MOMENT_ENVELOPE_EXCEEDS_FLOAT_RANGE")
    return envelope


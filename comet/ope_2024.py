"""Waudby-Smith et al., arXiv:2210.10768v3, Theorem 2 DR/EB anchor.

This API implements the independent-row fixed-design submodel, permitting
heterogeneous row means. It does not port the sequential theorem to arbitrary
source-graph data. The source theorem has a more general filtration contract.
Only ordinary floating arithmetic with a declared numerical debit is claimed.
"""

import math

import numpy as np
from scipy.optimize import brentq
from scipy.special import gammainc, gammaln


SOURCE = "https://arxiv.org/html/2210.10768"
CERTIFIED = "CERTIFIED_UNDER_DECLARED_ASSUMPTIONS"


def dr_pseudo_outcomes(actions, rewards, exposure, target_policy, nuisance, *, k):
    """Statewise predictor truncation, equations (10) and (11).

    The cap in the direct expectation is evaluated at each action's q/e. It
    must not be the realized action's cap reused for all counterfactual states.
    The same exact e and nuisance available to other engines are used here.
    """
    a = np.asarray(actions)
    y, e, q, fit = (np.asarray(value, dtype=float)
                     for value in (rewards, exposure, target_policy, nuisance))
    if (e.ndim != 2 or e.shape[0] == 0 or q.shape != e.shape or fit.shape != e.shape
            or a.shape != (len(e),) or a.dtype.kind not in "iu" or y.shape != (len(e),)):
        raise ValueError("N rewards/actions and matching N by S design arrays are required")
    if not np.isfinite(k) or k < 0:
        raise ValueError("a finite nonnegative design-only k is required for Theorem 2")
    if not all(np.isfinite(value).all() for value in (y, e, q, fit)):
        raise ValueError("OPE design and observations must be finite")
    if np.any(a < 0) or np.any(a >= e.shape[1]):
        raise ValueError("action index outside the declared exposure space")
    if (np.any(e < 0) or np.any(e > 1) or np.any(q < 0) or np.any(q > 1)
            or not np.allclose(e.sum(axis=1), 1, rtol=0, atol=1e-12)
            or not np.allclose(q.sum(axis=1), 1, rtol=0, atol=1e-12)):
        raise ValueError("exact logging and target rows must be distributions")
    if np.any((q > 0) & (e == 0)):
        raise ValueError("NONIDENTIFIED: target exposure is unsupported")
    if np.any(y < 0) or np.any(y > 1) or np.any(fit < 0) or np.any(fit > 1):
        raise ValueError("Theorem 2 anchor requires rewards and fits in [0,1]")
    rows = np.arange(len(e))
    if np.any(e[rows, a] == 0):
        raise ValueError("an observed action has zero declared logging probability")
    weights = np.divide(q, e, out=np.zeros_like(q), where=e > 0)
    cap = np.divide(k, weights, out=np.full_like(weights, np.inf), where=weights > 0)
    lower_fit = np.minimum(fit, cap)
    upper_fit = np.minimum(1 - fit, cap)
    observed_weight = weights[rows, a]
    lower = observed_weight * (y - lower_fit[rows, a]) + np.sum(q * lower_fit, axis=1)
    upper = observed_weight * (1 - y - upper_fit[rows, a]) + np.sum(q * upper_fit, axis=1)
    point = observed_weight * (y - fit[rows, a]) + np.sum(q * fit, axis=1)
    if not all(np.isfinite(value).all() for value in (lower, upper, point)):
        raise ValueError("NUMERICAL_FAILURE: nonfinite DR pseudo-outcomes")
    return lower, upper, point


def eb_variance(pseudo_outcomes, *, k, initial_prediction=None):
    """Equation (25), including a genuinely predictable past-only predictor."""
    phi = np.asarray(pseudo_outcomes, dtype=float)
    if phi.ndim != 1 or not len(phi) or not np.isfinite(phi).all():
        raise ValueError("finite nonempty pseudo-outcome vector required")
    if not np.isfinite(k) or k < 0:
        raise ValueError("finite nonnegative k required")
    upper = 1 / (1 + k)
    initial = upper / 2 if initial_prediction is None else initial_prediction
    if not np.isfinite(initial) or not 0 <= initial <= upper:
        raise ValueError("initial scaled predictor must lie in [0,1/(1+k)]")
    xi = phi / (1 + k)
    past = np.empty(len(xi))
    past[0] = initial
    past[1:] = np.minimum(np.cumsum(xi[:-1]) / np.arange(1, len(xi)), upper)
    variance = float(np.sum((xi - past) ** 2))
    if not np.isfinite(variance):
        raise ValueError("NUMERICAL_FAILURE: nonfinite EB variance process")
    return float(np.sum(xi)), variance


def eb_log_mixture(s, v, rho):
    """Equation (26), stable positive-deviation form from Remark 5.

    Only s>=0 is needed when inverting a lower tail: if s<=0 the mixture is
    at most one and cannot cross the alpha threshold. Then z=s+v+rho>0, so
    the real incomplete-gamma representation has no negative-z ambiguity.
    """
    if not all(math.isfinite(t) for t in (s, v, rho)) or s < 0 or v < 0 or rho <= 0:
        raise ValueError("s,v must be finite nonnegative and rho finite positive")
    shape = v + rho
    z = shape + s
    log_normalizer = rho * math.log(rho) - gammaln(rho) - math.log(gammainc(rho, rho))
    value = (log_normalizer + gammaln(shape) + math.log(gammainc(shape, z))
             - shape * math.log(z) + s + v)
    if not math.isfinite(value):
        raise ValueError("NUMERICAL_FAILURE: nonfinite gamma-mixture evaluation")
    return float(value)


def _eb_boundary(v, rho, alpha):
    threshold = math.log(1 / alpha)
    upper = max(1.0, math.sqrt(2 * (v + 1) * threshold) + threshold)
    while eb_log_mixture(upper, v, rho) < threshold:
        upper *= 2
        if not math.isfinite(upper):
            raise ValueError("NUMERICAL_FAILURE: no finite EB root bracket")
    xtol, rtol = 1e-11, 4 * np.finfo(float).eps
    root = float(brentq(lambda s: eb_log_mixture(s, v, rho) - threshold,
                        0.0, upper, xtol=xtol, rtol=rtol))
    # Predeclared conservative engineering padding; not a claim of a formal
    # special-function rounding-error enclosure or machine-verified arithmetic.
    debit = xtol + rtol * abs(root) + 1e-9 * (1 + abs(root) + math.sqrt(v))
    return root + debit, debit


def ope_eb_independent(actions, rewards, *, exposure, target_policy, nuisance,
                       delta=0.05, family_size=1, k=1.0, rho=1.0,
                       independent_rows_declared=False, independent_nuisance_declared=False,
                       tuning="design_only"):
    """Terminal value of Theorem 2's DR/empirical-Bernstein CS.

    Conditional on legitimate fixed D, independent heterogeneous rows have
    nu_t=E_pi[Y_t|D], so the source's average conditional target equals M_D.
    A connected source graph does not satisfy this API's independent-row
    declaration merely because each row has a correct marginal propensity.
    No past-interval intersection is taken for this potentially varying target.
    """
    if (not math.isfinite(delta) or not 0 < delta < 1
            or type(family_size) is not int or family_size < 1
            or not math.isfinite(rho) or rho <= 0):
        raise ValueError("valid family confidence budget and positive design-only rho required")
    result = dict(method="waudby_smith_2024_dr_eb_independent", source=SOURCE,
                  source_version="arXiv:2210.10768v3 (15 Aug 2024), Theorem 2",
                  status="ASSUMPTION_UNVERIFIED", nominal_delta=delta,
                  family_size=family_size, coordinate_delta=delta/family_size,
                  k=k, rho=rho, estimate=None, radius=None, lo=None, hi=None,
                  empty_intersection=False,
                  estimand="average fixed-design policy value; heterogeneous independent rows allowed",
                  time_uniform_under_declared_model=True,
                  uses_history_interval_intersection=False,
                  arithmetic="ordinary_float_with_declared_EB_root_debit; not outward-rounded proof")
    if independent_rows_declared is not True or independent_nuisance_declared is not True:
        return dict(result, reason="independent evaluation rows and independent/fixed nuisance not declared")
    if tuning != "design_only":
        return dict(result, status="HEURISTIC", reason="outcome-tuned k/rho has no certified path here")
    lower, upper, point = dr_pseudo_outcomes(actions, rewards, exposure,
                                             target_policy, nuisance, k=k)
    try:
        sums, variances, boundaries, debits = [], [], [], []
        for phi in (lower, upper):
            total, variance = eb_variance(phi, k=k)
            boundary, debit = _eb_boundary(variance, rho, delta/(2*family_size))
            sums.append(total)
            variances.append(variance)
            boundaries.append(boundary)
            debits.append(debit)
        n = len(point)
        raw_lo = (1+k) * (sums[0] - boundaries[0]) / n
        raw_hi = 1 - (1+k) * (sums[1] - boundaries[1]) / n
        lo, hi = max(0.0, raw_lo), min(1.0, raw_hi)
        estimate = float(np.mean(point))
        if not np.isfinite([estimate, raw_lo, raw_hi, lo, hi]).all():
            raise ValueError("nonfinite EB endpoints")
    except (ValueError, RuntimeError, OverflowError) as exc:
        return dict(result, status="NUMERICAL_FAILURE", reason=str(exc))
    return dict(result, status=CERTIFIED, n=n, estimate=estimate, lo=lo, hi=hi,
                raw_lo=raw_lo, raw_hi=raw_hi, empty_intersection=lo > hi,
                radius=max(abs(estimate-lo), abs(hi-estimate)) if lo <= hi else None,
                scaled_variance_lower=variances[0], scaled_variance_upper=variances[1],
                intrinsic_boundary_lower=boundaries[0], intrinsic_boundary_upper=boundaries[1],
                numerical_boundary_debits=debits, predictor_truncation_bias=0.0,
                reason="source Theorem 2 and mirroring under the independent-row fixed-design submodel")

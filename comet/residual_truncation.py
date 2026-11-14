"""Fixed-design heterogeneous graph certificates (separate from frozen E0).

The conditional probability model, not a passing schema check, supplies graph
sufficiency and residual-moment validity. See theory/global_residual_truncation.md.
Plans use no evaluation outcome or oracle mean. NumPy is a new-workstream
dependency; none of the historical estimators import this module.
"""
from dataclasses import dataclass, field
import math

import numpy as np


CERTIFIED = "CERTIFIED_UNDER_DECLARED_ASSUMPTIONS"


class NonidentifiedError(ValueError):
    """An active signed coefficient has zero exposure support."""


@dataclass(frozen=True)
class AssumptionContract:
    exogenous_design: bool
    exact_exposure: bool
    conditional_randomization: bool
    independent_nuisance: bool
    frozen_family: bool
    sufficient_source_graph: bool
    valid_residual_moments: bool
    graph_provenance: str
    moment_provenance: str
    conditioning_provenance: str

    def require(self):
        for name in ("exogenous_design", "exact_exposure", "conditional_randomization",
                     "independent_nuisance", "frozen_family", "sufficient_source_graph",
                     "valid_residual_moments"):
            if getattr(self, name) is not True:
                raise ValueError("ASSUMPTION_UNVERIFIED: " + name)
        if not all((self.graph_provenance, self.moment_provenance,
                    self.conditioning_provenance)):
            raise ValueError("ASSUMPTION_UNVERIFIED: missing provenance")


def clipping_bias_constant(p):
    """Sharp sup_{x>tau} (x-tau) / (x**p tau**(1-p))."""
    if not 1 < p <= 2:
        raise ValueError("moment order must be in (1,2]")
    return math.exp((p - 1) * math.log(p - 1) - p * math.log(p))


def bounded_residual_moments(lower, upper, nuisance, p):
    """The SAME legal |Y-muhat| bound is available to every bounded baseline."""
    clipping_bias_constant(p)
    fit = np.asarray(nuisance, dtype=float)
    lo, hi = np.broadcast_arrays(np.asarray(lower, dtype=float),
                                 np.asarray(upper, dtype=float))
    if np.any(lo > hi) or not np.isfinite([lo, hi]).all():
        raise ValueError("invalid outcome bounds")
    return np.maximum(np.abs(lo - fit), np.abs(hi - fit)) ** p


def pareto_source_residual_moments(mean_lower, mean_upper, nuisance, p,
                                   tail_exponent, coefficients):
    """Minkowski envelope for a location plus sums of symmetric Pareto sources.

    Each source has scale equal to the absolute coefficient, exponent a, and
    zero expectation. Source independence is not needed for this moment bound.
    Its sufficiency for the score graph is a separate model obligation.
    """
    clipping_bias_constant(p)
    if not tail_exponent > p:
        raise ValueError("NOT_APPLICABLE: Pareto moment diverges")
    coeff = np.asarray(coefficients, dtype=float)
    if not np.isfinite(coeff).all():
        raise ValueError("nonfinite source coefficient")
    noise_lp = np.sum(np.abs(coeff), axis=-1) * (
        tail_exponent / (tail_exponent - p)) ** (1 / p)
    fit = np.asarray(nuisance, dtype=float)
    location_lp = np.maximum(np.abs(np.asarray(mean_lower) - fit),
                             np.abs(np.asarray(mean_upper) - fit))
    return (location_lp + np.asarray(noise_lp)[..., None]) ** p


def residual_moment_envelope(coefficients, exposure, residual_moments, p):
    """v_u=sum_s |d_us|**p e_us**(1-p) b_us, with exact support refusal."""
    clipping_bias_constant(p)
    d, e, b = np.broadcast_arrays(np.asarray(coefficients, dtype=float),
                                   np.asarray(exposure, dtype=float),
                                   np.asarray(residual_moments, dtype=float))
    if d.ndim != 2 or not np.isfinite([d, e, b]).all():
        raise ValueError("finite N by S inputs required")
    if np.any(e < 0) or np.any(b < 0) or not np.allclose(e.sum(axis=1), 1,
                                                           rtol=0, atol=1e-13):
        raise ValueError("invalid exposure law or moment envelope")
    if np.any((d != 0) & (e == 0)):
        raise NonidentifiedError("NONIDENTIFIED: nonzero d with e=0")
    safe_e = np.where(e > 0, e, 1.)
    v = np.sum(np.abs(d) ** p * safe_e ** (1 - p) * b, axis=1)
    if not np.isfinite(v).all():
        raise ValueError("NUMERICAL_FAILURE: residual moment overflow")
    return v


def truncation_components(v, tau, p, color_count, coordinate_delta, n):
    """Raw-row (not subgroup-normalized) bias, deviation and range pieces."""
    v = np.asarray(v, dtype=float)
    if not 0 < coordinate_delta < 1 or n < 1 or color_count < 0:
        raise ValueError("invalid confidence, row or color count")
    clipping_bias_constant(p)
    if np.any(v < 0) or not np.isfinite(v).all():
        raise ValueError("invalid moment envelope")
    if not np.any(v):
        return (0., 0., 0.)
    if not np.isfinite(tau) or tau <= 0 or color_count < 1:
        raise ValueError("positive finite tau and coloring required")
    t = math.log(2 / coordinate_delta)
    bias = clipping_bias_constant(p) * float(v.sum()) * tau ** (1 - p) / n
    variance = math.sqrt(2 * color_count * t * float(v.sum()) * tau ** (2 - p)) / n
    range_piece = (2 / 3) * color_count * tau * t / n
    return bias, variance, range_piece


def choose_truncation(v, p, color_count, coordinate_delta, n, multipliers):
    """Design-only finite-grid selection. No union charge over fixed D choices."""
    factors = tuple(float(x) for x in multipliers)
    if not factors or any(not np.isfinite(x) or x <= 0 for x in factors):
        raise ValueError("explicit positive threshold multiplier grid required")
    total = float(np.sum(v))
    if total == 0:
        return 0., (0., 0., 0.)
    scale = (total / (color_count * math.log(2 / coordinate_delta))) ** (1 / p)
    candidates = [(scale * factor, truncation_components(
        v, scale * factor, p, color_count, coordinate_delta, n)) for factor in factors]
    return min(candidates, key=lambda item: (sum(item[1]), item[0]))


def _readonly(value):
    result = np.array(value, dtype=float, copy=True)
    return np.frombuffer(result.tobytes(), dtype=float).reshape(result.shape)


@dataclass(frozen=True)
class CertificatePlan:
    query_id: str
    channel: str
    method: str
    selected_method: str
    n: int
    normalizer: float
    family_size: int
    nominal_delta: float
    coordinate_delta: float
    p: float
    active_rows: int
    color_count: int
    direct_term: float
    tau: float | None
    bias_piece: float
    variance_piece: float
    range_piece: float
    target_lo: float | None
    target_hi: float | None
    assumptions: AssumptionContract
    weights: np.ndarray = field(repr=False, compare=False)
    nuisance: np.ndarray = field(repr=False, compare=False)
    supported_exposures: np.ndarray = field(repr=False, compare=False)
    # A colorwise comparator clips each color at its own design-only threshold.
    row_thresholds: np.ndarray | None = field(default=None, repr=False, compare=False)

    @property
    def radius(self):
        return (self.bias_piece + self.variance_piece + self.range_piece) / self.normalizer

    def evaluate(self, actions, outcomes, *, data_digest, seed_namespace,
                 code_hash, config_hash, family_digest="", numerical_guard=1e-10):
        """Evaluate a frozen plan; truth is intentionally absent from this API."""
        a, y = np.asarray(actions), np.asarray(outcomes, dtype=float)
        if a.shape != (self.n,) or y.shape != (self.n,) or a.dtype.kind not in 'iu':
            raise ValueError("one integer action and outcome per retained row required")
        if np.any(a < 0) or np.any(a >= self.weights.shape[1]):
            raise ValueError("invalid action")
        if np.any(~self.supported_exposures[np.arange(self.n), a]):
            raise ValueError("observed action has zero probability under declared e")
        if not np.isfinite(y).all() or numerical_guard < 0:
            raise ValueError("NUMERICAL_FAILURE: invalid observed outcome or guard")
        rows = np.arange(self.n)
        residual = self.weights[rows, a] * (y - self.nuisance[rows, a])
        if self.row_thresholds is not None:
            residual = np.clip(residual, -self.row_thresholds, self.row_thresholds)
        elif self.tau is not None:
            residual = np.clip(residual, -self.tau, self.tau)
        estimate = (self.direct_term + float(residual.sum()) / self.n) / self.normalizer
        radius = self.radius
        # A declared decision padding, not a claim of machine-verified outward rounding.
        guard = numerical_guard * (1 + abs(estimate) + radius)
        lo, hi = estimate - radius - guard, estimate + radius + guard
        lower = lo if self.target_lo is None else max(lo, self.target_lo)
        upper = hi if self.target_hi is None else min(hi, self.target_hi)
        if not np.isfinite([estimate, radius, lo, hi]).all():
            raise ValueError("NUMERICAL_FAILURE: nonfinite certificate")
        return dict(query_id=self.query_id, estimand="fixed_design_signed_moment",
                    channel=self.channel, method=self.method,
                    selected_method=self.selected_method, estimate=estimate,
                    lo=lower, hi=upper, raw_lo=lo, raw_hi=hi,
                    empty_intersection=lower > upper, radius=radius,
                    bias=self.bias_piece / self.normalizer,
                    concentration=self.variance_piece / self.normalizer,
                    range_contribution=self.range_piece / self.normalizer,
                    tau=self.tau, nominal_delta=self.nominal_delta,
                    coordinate_delta=self.coordinate_delta,
                    family_size=self.family_size, raw_N=self.n,
                    family_digest=family_digest,
                    active_rows=self.active_rows, coloring_count=self.color_count,
                    normalizer=self.normalizer, p=self.p, status=CERTIFIED,
                    known_target_lo=self.target_lo, known_target_hi=self.target_hi,
                    assumptions=self.assumptions.__dict__, data_digest=data_digest,
                    seed_namespace=seed_namespace, code_hash=code_hash,
                    config_hash=config_hash, numerical_guard=guard,
                    arithmetic="ordinary_float_not_outward_verified")


def make_plan(query, exposure, nuisance, residual_moments, graph, contract, *,
              p, delta, family_size, multipliers, method="comet_local",
              outcome_bounds=None, mean_bounds=None, tuning="design_only"):
    """Build a design-only plan with a single truncation threshold per query.

    `residual_moments` controls raw |Y(s)-muhat(s)|**p, not a centered moment.
    Methods all share these arrays; bounded ranges are not weakened for baselines.
    A fixed/independent fit is a model assumption even when all shapes validate.
    """
    contract.require()
    if tuning != "design_only":
        raise ValueError("HEURISTIC: outcome-based tuning has no certified path")
    if type(family_size) is not int or family_size < 1 or not 0 < delta < 1:
        raise ValueError("invalid complete family confidence budget")
    d, e, fit = np.broadcast_arrays(np.asarray(query.coefficients, dtype=float),
                                     np.asarray(exposure, dtype=float),
                                     np.asarray(nuisance, dtype=float))
    if d.ndim != 2 or d.shape[0] < 1 or not np.isfinite(fit).all():
        raise ValueError("finite nonempty N by S design required")
    if d.shape != query.coefficients.shape:
        raise ValueError("exposure or nuisance broadcasting cannot change query rows/states")
    n = len(d)
    if graph.n_rows != n:
        raise ValueError("source graph and retained design differ")
    normalizer = float(query.normalizer)
    if not np.isfinite(normalizer) or normalizer <= 0:
        raise NonidentifiedError("NONIDENTIFIED: nonpositive known normalizer")
    v = residual_moment_envelope(d, e, residual_moments, p)
    active = np.any(d != 0, axis=1)
    local_graph = graph.induced(active)
    chi_local = local_graph.color_count
    chi = chi_local
    coordinate_delta = delta / family_size
    weights = np.divide(d, e, out=np.zeros_like(d), where=e > 0)
    direct = float(np.sum(d * fit) - np.sum(query.offset)) / n
    target_lo = target_hi = None
    if mean_bounds is not None:
        mean_lo, mean_hi = (np.broadcast_to(np.asarray(x, dtype=float), d.shape)
                            for x in mean_bounds)
        if np.any(mean_lo > mean_hi) or not np.isfinite([mean_lo, mean_hi]).all():
            raise ValueError("invalid known conditional mean class")
        target_lo = float(np.sum(np.where(d >= 0, d * mean_lo, d * mean_hi))
                          - np.sum(query.offset)) / (n * normalizer)
        target_hi = float(np.sum(np.where(d >= 0, d * mean_hi, d * mean_lo))
                          - np.sum(query.offset)) / (n * normalizer)
    tau = None
    row_thresholds = None
    selected = method
    if method in ("comet_local", "generic_matched", "truncated_local",
                  "truncated_global_graph", "truncated_global_envelope"):
        if method in ("truncated_global_graph", "truncated_global_envelope"):
            chi = graph.color_count if np.any(active) else 0
        if method == "truncated_global_envelope":
            # Deliberate component ablation: same legal information, coarser use.
            v = np.full(n, float(v.max())) if np.any(active) else np.zeros(n)
        tau, pieces = choose_truncation(v, p, chi, coordinate_delta, n, multipliers)
        if method in ("comet_local", "generic_matched") and outcome_bounds is not None:
            options = [(sum(pieces), "truncated_local", tau, pieces)]
            for branch in ("graph_hoeffding", "graph_bernstein"):
                alternative = make_plan(query, e, fit, residual_moments, graph,
                    contract, p=p, delta=delta, family_size=family_size,
                    multipliers=multipliers, method=branch,
                    outcome_bounds=outcome_bounds, mean_bounds=mean_bounds)
                alternatives = (alternative.bias_piece, alternative.variance_piece,
                                alternative.range_piece)
                options.append((sum(alternatives), branch, None, alternatives))
            _, selected, tau, pieces = min(options, key=lambda item: (item[0], item[1]))
    elif method == "colorwise_truncation":
        colors = np.asarray(local_graph.colors)
        row_thresholds = np.zeros(n)
        pieces = np.zeros(3)
        active_positions = np.flatnonzero(active)
        for color in range(chi):
            positions = active_positions[colors == color]
            threshold, color_pieces = choose_truncation(v[positions], p, 1,
                coordinate_delta / chi, n, multipliers)
            row_thresholds[positions] = threshold
            pieces += np.asarray(color_pieces)
        pieces = tuple(float(x) for x in pieces)
        row_thresholds = _readonly(row_thresholds)
    elif method in ("graph_hoeffding", "graph_bernstein",
                    "graph_hoeffding_global", "graph_bernstein_global"):
        if outcome_bounds is None:
            raise ValueError("NOT_APPLICABLE: outcome bounds required")
        if method.endswith("_global"):
            chi = graph.color_count if np.any(active) else 0
        lower_y, upper_y = (np.broadcast_to(np.asarray(x, dtype=float), d.shape)
                            for x in outcome_bounds)
        if np.any(lower_y > upper_y) or not np.isfinite([lower_y, upper_y]).all():
            raise ValueError("invalid outcome support")
        left = weights * (lower_y - fit)
        right = weights * (upper_y - fit)
        # Include every supported exposure, even if its coefficient is zero.
        row_lo = np.min(np.where(e > 0, np.minimum(left, right), np.inf), axis=1)
        row_hi = np.max(np.where(e > 0, np.maximum(left, right), -np.inf), axis=1)
        span = row_hi - row_lo
        t = math.log(2 / coordinate_delta)
        hoeffding = math.sqrt(chi * t * float(np.sum(span ** 2)) / 2) / n
        if method.startswith("graph_hoeffding"):
            pieces = (0., hoeffding, 0.)
        else:
            # Bounded branch uses p=2 directly even if the caller declared p<2.
            b2 = bounded_residual_moments(lower_y, upper_y, fit, 2.)
            v2 = np.minimum(residual_moment_envelope(d, e, b2, 2.), span ** 2 / 4)
            pieces = (0., math.sqrt(2 * chi * t * float(v2.sum())) / n,
                      chi * float(span.max()) * t / (3 * n))
    else:
        raise ValueError("unknown certified method: " + method)
    if not np.isfinite(pieces).all():
        raise ValueError("NUMERICAL_FAILURE: nonfinite planned radius")
    return CertificatePlan(query.query_id, query.channel, method, selected, n,
        normalizer, family_size, delta, coordinate_delta, p, int(active.sum()),
        chi, direct, tau, *pieces, target_lo, target_hi, contract,
        _readonly(weights), _readonly(fit), np.frombuffer((e > 0).tobytes(),
            dtype=np.bool_).reshape(e.shape), row_thresholds)


def certified_decision(certificate, threshold):
    """An empty confidence set is retained as a failure and never a decision."""
    if certificate["empty_intersection"] or certificate["status"] != CERTIFIED:
        return "ABSTAIN"
    if certificate["hi"] <= threshold:
        return "CERTIFIED_SAFE"
    if certificate["lo"] > threshold:
        return "CERTIFIED_VIOLATION"
    return "ABSTAIN"

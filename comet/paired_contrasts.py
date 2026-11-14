"""Direct signed contrasts and honest joint-budget subtraction of two levels.

This module never creates a new confidence guarantee by subtracting two
separately 95% intervals. The preferred joint-family API deduplicates shared
level coordinates before assigning the SAME total delta. The simple pair API
also retains a conservative 2m-slot construction for distinct prespecified pairs.
"""

from dataclasses import dataclass
import math
from types import MappingProxyType

import numpy as np

from comet.queries import SignedQuery
from comet.audit_pipeline import freeze_discovered_family
from comet.residual_truncation import CERTIFIED, make_plan


def make_paired_queries(query_id, q1, q0, auditor, *, channel="risk", normalizer=1.0):
    """Return direct, policy-1 level and policy-0 level queries on the same rows.

    The caller must separately establish compatibility of any constrained joint
    assignment policies. Valid row marginal distributions alone do not prove
    implementability under slate or network constraints.
    """
    first, baseline = np.asarray(q1, dtype=float), np.asarray(q0, dtype=float)
    if first.ndim != 2 or first.shape != baseline.shape or 0 in first.shape:
        raise ValueError("paired policies must share a nonempty N by S design")
    for policy in (first, baseline):
        if not np.isfinite(policy).all() or np.any(policy < 0) or not np.allclose(policy.sum(axis=1), 1, rtol=0, atol=1e-12):
            raise ValueError("every policy row must be a probability distribution")
    h = np.asarray(auditor, dtype=float)
    if h.ndim == 0:
        h = np.full(len(first), float(h))
    if h.shape != (len(first),) or not np.isfinite(h).all() or np.any(np.abs(h) > 1):
        raise ValueError("auditor must contain one finite weight in [-1,1] per row")
    common = dict(channel=channel, normalizer=normalizer,
                  provenance="fixed_or_independently_discovered_paired_policy_family")
    direct = SignedQuery(query_id, h[:, None] * (first - baseline), 0, **common)
    level1 = SignedQuery(query_id + "/level1", h[:, None] * first, 0, **common)
    level0 = SignedQuery(query_id + "/level0", h[:, None] * baseline, 0, **common)
    return direct, level1, level0


def _signed_target_range(query, mean_bounds):
    if mean_bounds is None:
        return None, None
    lower, upper = (np.broadcast_to(np.asarray(value, dtype=float), query.coefficients.shape)
                    for value in mean_bounds)
    if not np.isfinite([lower, upper]).all() or np.any(lower > upper):
        raise ValueError("known response-mean bounds must be finite and ordered")
    d = query.coefficients
    lo = (np.sum(np.where(d >= 0, d * lower, d * upper)) - np.sum(query.offset)) / (query.n_rows * query.normalizer)
    hi = (np.sum(np.where(d >= 0, d * upper, d * lower)) - np.sum(query.offset)) / (query.n_rows * query.normalizer)
    return float(lo), float(hi)


def subtract_level_certificates(direct_query, level1, level0, *, contrast_count,
                                delta, mean_bounds=None, underlying_family_size=None,
                                joint_level_family_digest=None):
    """Subtract jointly certified levels, preserving all bias/range contributions.

    Both inputs must belong to one prespecified simultaneous level budget. The
    direct signed-coordinate mean class may tighten the difference interval.
    Any empty constituent remains an empty/failing confidence outcome, even
    when naive endpoint arithmetic would otherwise produce an ordered pair.
    """
    if type(contrast_count) is not int or contrast_count < 1 or not 0 < delta < 1:
        raise ValueError("a positive declared contrast count and total delta are required")
    family_size = 2 * contrast_count if underlying_family_size is None else underlying_family_size
    if type(family_size) is not int or not 1 <= family_size <= 2 * contrast_count:
        raise ValueError("underlying_family_size must be the positive actual level coordinate count")
    for level in (level1, level0):
        if level.get("status") != CERTIFIED:
            raise ValueError("level subtraction requires two certified level constructions")
        if level.get("family_size") != family_size:
            raise ValueError("level subtraction requires the complete underlying level family")
        nominal, coordinate = level.get("nominal_delta"), level.get("coordinate_delta")
        if not isinstance(nominal, (float, int)) or not 0 < nominal <= delta + 1e-14:
            raise ValueError("level nominal budget exceeds total contrast-comparator delta")
        if not isinstance(coordinate, (float, int)) or not 0 < coordinate <= delta / family_size + 1e-14:
            raise ValueError("each level must spend at most delta/(2m) or delta/(actual unique level count)")
        if joint_level_family_digest is not None and level.get("family_digest") != joint_level_family_digest:
            raise ValueError("levels must belong to the declared deduplicated simultaneous family")
        if level.get("channel") != direct_query.channel or level.get("normalizer") != direct_query.normalizer:
            raise ValueError("levels and direct contrast must share response channel and normalization")
        for field in ("estimate", "lo", "hi", "raw_lo", "raw_hi", "radius",
                      "bias", "concentration", "range_contribution", "numerical_guard"):
            if not isinstance(level.get(field), (float, int)) or not math.isfinite(level[field]):
                raise ValueError("NUMERICAL_FAILURE: level certificate contains nonfinite quantities")
    for field in ("data_digest", "seed_namespace", "code_hash", "config_hash"):
        if field not in level1 or level1[field] != level0.get(field):
            raise ValueError("paired levels must use the same logged data and frozen provenance")
    estimate = level1["estimate"] - level0["estimate"]
    raw_lo = level1["raw_lo"] - level0["raw_hi"]
    raw_hi = level1["raw_hi"] - level0["raw_lo"]
    lo, hi = level1["lo"] - level0["hi"], level1["hi"] - level0["lo"]
    target_lo, target_hi = _signed_target_range(direct_query, mean_bounds)
    if target_lo is not None:
        lo, hi = max(lo, target_lo), min(hi, target_hi)
    constituent_empty = (level1.get("empty_intersection", False) or
                         level0.get("empty_intersection", False) or
                         level1["lo"] > level1["hi"] or level0["lo"] > level0["hi"])
    distinct_levels = 1 if level1["query_id"] == level0["query_id"] else 2
    return {
        "query_id": direct_query.query_id,
        "estimand": "fixed_design_signed_moment",
        "channel": direct_query.channel,
        "normalizer": direct_query.normalizer,
        "method": "joint_level_difference",
        "selected_method": "subtract_two_jointly_certified_levels",
        "estimate": estimate, "lo": lo, "hi": hi,
        "raw_lo": raw_lo, "raw_hi": raw_hi,
        "radius": level1["radius"] + level0["radius"],
        "bias": level1["bias"] + level0["bias"],
        "concentration": level1["concentration"] + level0["concentration"],
        "range_contribution": level1["range_contribution"] + level0["range_contribution"],
        "numerical_guard": level1["numerical_guard"] + level0["numerical_guard"],
        "empty_intersection": bool(constituent_empty or lo > hi),
        "constituent_empty": bool(constituent_empty),
        "nominal_delta": delta, "family_size": family_size,
        "underlying_family_size": family_size,
        "underlying_family_digest": joint_level_family_digest,
        "contrast_count": contrast_count,
        "coordinate_delta": delta / family_size,
        "coordinate_delta_scope": "constituent level; derived contrast uses contrast_failure_allocation",
        "contrast_failure_allocation": min(delta, distinct_levels * delta / family_size),
        "derived_family_failure_delta": delta,
        "no_additional_contrast_union_charge": True,
        "confidence_accounting": ("actual deduplicated levels at delta/k; all derived contrasts inherit one level-family event"
                                  if underlying_family_size is not None else
                                  "2m prespecified level slots at delta/(2m); shared levels should use the deduplicated family API"),
        "level_query_ids": [level1["query_id"], level0["query_id"]],
        "level_selected_methods": [level1["selected_method"], level0["selected_method"]],
        "raw_N": direct_query.n_rows,
        "active_rows": int(direct_query.active_mask.sum()),
        "coloring_count": None,
        "level_coloring_counts": [level1.get("coloring_count"), level0.get("coloring_count")],
        "tau": [level1.get("tau"), level0.get("tau")],
        "p": level1.get("p"), "status": CERTIFIED,
        "assumptions": {"level1": level1.get("assumptions"), "level0": level0.get("assumptions")},
        "data_digest": level1["data_digest"], "seed_namespace": level1["seed_namespace"],
        "code_hash": level1["code_hash"], "config_hash": level1["config_hash"],
        "arithmetic": "ordinary_float_not_outward_verified",
    }


@dataclass(frozen=True)
class LevelDifferencePlan:
    direct_query: SignedQuery
    level1_plan: object
    level0_plan: object
    contrast_count: int
    delta: float
    mean_bounds: object

    @property
    def family_size(self):
        return 2 * self.contrast_count

    @property
    def coordinate_delta(self):
        return self.delta / self.family_size

    @property
    def radius(self):
        return self.level1_plan.radius + self.level0_plan.radius

    def evaluate(self, actions, outcomes, *, data_digest, seed_namespace,
                 code_hash, config_hash, numerical_guard=1e-10):
        metadata = dict(data_digest=data_digest, seed_namespace=seed_namespace,
                        code_hash=code_hash, config_hash=config_hash,
                        numerical_guard=numerical_guard)
        first = self.level1_plan.evaluate(actions, outcomes, **metadata)
        baseline = self.level0_plan.evaluate(actions, outcomes, **metadata)
        return subtract_level_certificates(self.direct_query, first, baseline,
            contrast_count=self.contrast_count, delta=self.delta, mean_bounds=self.mean_bounds)


def make_level_difference_plans(direct, level1, level0, exposure, nuisance,
                                residual_moments, graph, contract, *, p, delta,
                                contrast_count, multipliers, method="generic_matched",
                                outcome_bounds=None, mean_bounds=None):
    """Use one legal graph engine for two levels at delta/(2m), never delta/m."""
    if type(contrast_count) is not int or contrast_count < 1:
        raise ValueError("contrast_count must be a positive integer")
    _validate_pair(direct, level1, level0)
    common = dict(p=p, delta=delta, family_size=2 * contrast_count,
                  multipliers=multipliers, method=method,
                  outcome_bounds=outcome_bounds, mean_bounds=mean_bounds)
    first = make_plan(level1, exposure, nuisance, residual_moments, graph, contract, **common)
    baseline = make_plan(level0, exposure, nuisance, residual_moments, graph, contract, **common)
    return LevelDifferencePlan(direct, first, baseline, contrast_count, delta, mean_bounds)


def _validate_pair(direct, level1, level0):
    if not (direct.coefficients.shape == level1.coefficients.shape == level0.coefficients.shape):
        raise ValueError("paired queries must share rows and exposure states")
    if any(query.channel != direct.channel or query.normalizer != direct.normalizer
           for query in (level1, level0)):
        raise ValueError("paired queries must share channel and normalization")
    # Multiplication/subtraction of noninteger auditor weights can differ in
    # the last float bit; this check is an ordinary-arithmetic consistency
    # check, not a machine-verified equality proof.
    if not np.allclose(direct.coefficients, level1.coefficients - level0.coefficients,
                       rtol=1e-13, atol=1e-15) or not np.allclose(
                       direct.offset, level1.offset - level0.offset, rtol=1e-13, atol=1e-15):
        raise ValueError("direct query is not the signed difference of the two levels")


@dataclass(frozen=True)
class JointLevelFamilyPlan:
    """One simultaneous event for unique levels, reused by every contrast."""

    family: object
    direct_family: object
    level_plans: object
    pairs: tuple
    delta: float
    mean_bounds: object

    @property
    def underlying_family_size(self):
        return self.family.family_size

    @property
    def coordinate_delta(self):
        return self.delta / self.underlying_family_size

    def evaluate(self, actions, outcomes, *, data_digest, seed_namespace,
                 code_hash, config_hash, numerical_guard=1e-10):
        """Evaluate each unique level once; subtraction pays no second union."""
        metadata = dict(data_digest=data_digest, seed_namespace=seed_namespace,
                        code_hash=code_hash, config_hash=config_hash,
                        numerical_guard=numerical_guard)
        levels = {}
        for query_id, plan in self.level_plans.items():
            certificate = plan.evaluate(actions, outcomes, **metadata)
            certificate["family_digest"] = self.family.digest
            levels[query_id] = certificate
        contrasts = {}
        for direct, first_id, baseline_id in self.pairs:
            certificate = subtract_level_certificates(
                direct, levels[first_id], levels[baseline_id], contrast_count=len(self.pairs),
                delta=self.delta, mean_bounds=self.mean_bounds,
                underlying_family_size=self.family.family_size,
                joint_level_family_digest=self.family.digest,
            )
            certificate["derived_direct_family_size"] = self.direct_family.family_size
            certificate["derived_direct_family_digest"] = self.direct_family.digest
            contrasts[direct.query_id] = certificate
        return {
            "method": "deduplicated_joint_level_difference",
            "nominal_delta": self.delta,
            "underlying_family_size": self.underlying_family_size,
            "underlying_family_digest": self.family.digest,
            "level_coordinate_delta": self.coordinate_delta,
            "declared_contrast_count": len(self.pairs),
            "derived_direct_family_size": self.direct_family.family_size,
            "derived_family_failure_delta": self.delta,
            "level_aliases": dict(self.family.aliases),
            "direct_aliases": dict(self.direct_family.aliases),
            "level_certificates": levels,
            "contrasts": contrasts,
            "confidence_accounting": "one actual unique-level simultaneous event; no additional union over derived contrasts",
        }


def make_joint_level_family_plans(paired_queries, exposure, nuisance, residual_moments,
                                  graph, contract, *, p, delta, multipliers,
                                  method="generic_matched", outcome_bounds=None,
                                  mean_bounds=None):
    """Freeze/deduplicate every level used by a whole family of paired queries.

    ``paired_queries`` contains (direct, policy1_level, baseline_level) triples.
    For example, 16 new-policy/auditor levels with four shared baseline/auditor
    levels cost k=20, not 32. At delta=.05, every unique level spends .05/20;
    every derived contrast has a marginal failure upper bound 2*.05/20 (or
    smaller if its levels coincide). ALL derived contrasts jointly inherit the
    SAME probability>=1-.05 event; no new union bound over their count is used.
    """
    pairs = tuple(paired_queries)
    if not pairs:
        raise ValueError("at least one paired query is required")
    if any(len(pair) != 3 for pair in pairs):
        raise ValueError("paired_queries must contain direct, level1, level0 triples")
    if len({pair[0].query_id for pair in pairs}) != len(pairs):
        raise ValueError("derived contrast IDs must be unique")
    for direct, first, baseline in pairs:
        _validate_pair(direct, first, baseline)
    family = freeze_discovered_family(level for _, first, baseline in pairs for level in (first, baseline))
    direct_family = freeze_discovered_family(direct for direct, _, _ in pairs)
    plans = {
        query.query_id: make_plan(query, exposure, nuisance, residual_moments, graph, contract,
            p=p, delta=delta, family_size=family.family_size, multipliers=multipliers,
            method=method, outcome_bounds=outcome_bounds, mean_bounds=mean_bounds)
        for query in family.queries
    }
    resolved = tuple((direct, family.canonical_id(first.query_id), family.canonical_id(baseline.query_id))
                     for direct, first, baseline in pairs)
    return JointLevelFamilyPlan(family, direct_family, MappingProxyType(plans), resolved, delta, mean_bounds)

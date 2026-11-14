"""Finite eventwise policy selection and affine interval propagation.

The selector has no oracle input. Source independence, truthful known-design
service/capacity, and compatibility of joint assignment policies are model
obligations, not facts inferred from favorable observed certificates.
"""

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

import numpy as np

from comet.audit_pipeline import FrozenFamily


CERTIFIED = "CERTIFIED_UNDER_DECLARED_ASSUMPTIONS"


@dataclass(frozen=True)
class PolicyCandidate:
    policy_id: str
    risk_query_ids: tuple[str, ...]
    utility_contrast_id: str | None
    service: float
    capacity: float

    def __post_init__(self) -> None:
        if not isinstance(self.policy_id, str) or not self.policy_id:
            raise ValueError("policy_id must be a nonempty string")
        risks = tuple(self.risk_query_ids)
        if not risks or any(not isinstance(value, str) or not value for value in risks):
            raise ValueError("each policy must declare its complete nonempty risk coordinate list")
        if self.utility_contrast_id is not None and (not isinstance(self.utility_contrast_id, str) or not self.utility_contrast_id):
            raise ValueError("utility contrast must be a coordinate ID or None for the baseline")
        if not all(math.isfinite(value) and 0 <= value <= 1 for value in (self.service, self.capacity)):
            raise ValueError("known-design service and capacity must be finite fractions")
        object.__setattr__(self, "risk_query_ids", risks)


def _family_certificates(family: FrozenFamily, certificates: Mapping[str, dict], delta: float) -> dict:
    if not 0 < delta < 1:
        raise ValueError("delta must be in (0,1)")
    expected = {query.query_id for query in family.queries}
    query_by_id = {query.query_id: query for query in family.queries}
    if set(certificates) != expected:
        raise ValueError("supply every canonical coordinate of the complete frozen family")
    total_spent = 0.0
    for query_id, certificate in certificates.items():
        if certificate.get("query_id") != query_id:
            raise ValueError("certificate query identity does not match frozen family")
        query = query_by_id[query_id]
        if certificate.get("channel") != query.channel or certificate.get("normalizer") != query.normalizer:
            raise ValueError("certificate channel or normalization changes the frozen estimand")
        if certificate.get("family_size") != family.family_size:
            raise ValueError("certificate family_size omits or changes frozen risk/utility coordinates")
        nominal = certificate.get("nominal_delta")
        coordinate = certificate.get("coordinate_delta")
        if not isinstance(nominal, (int, float)) or not 0 < nominal <= delta + 1e-14:
            raise ValueError("certificate nominal confidence budget exceeds the selection budget")
        if not isinstance(coordinate, (int, float)) or not 0 < coordinate <= nominal / family.family_size + 1e-14:
            raise ValueError("certificate coordinate budget does not pay for the complete family")
        if certificate.get("family_digest", family.digest) != family.digest:
            raise ValueError("certificate frozen-family digest does not match")
        total_spent += coordinate
    if total_spent > delta + 1e-14:
        raise ValueError("combined coordinate confidence budget exceeds delta")
    return dict(certificates)


def _eligible(certificate: dict) -> bool:
    lo, hi = certificate.get("lo"), certificate.get("hi")
    return (
        certificate.get("status") == CERTIFIED
        and not certificate.get("empty_intersection", False)
        and isinstance(lo, (float, int)) and isinstance(hi, (float, int))
        and math.isfinite(lo) and math.isfinite(hi) and lo <= hi
    )


def select_policy(
    candidates: Sequence[PolicyCandidate],
    family: FrozenFamily,
    certificates: Mapping[str, dict],
    risk_thresholds: Mapping[str, float],
    *,
    utility_margin: float = 0.0,
    service_floor: float = 0.2,
    capacity_ceiling: float = 0.6,
    delta: float = 0.05,
) -> dict:
    """Return a certified feasible candidate or ABSTAIN, never an unsafe fallback.

    A unique candidate with ``utility_contrast_id=None`` denotes the baseline:
    its contrast to itself is the known zero, while all its risks still require
    certificates. Other candidates supply a frozen baseline utility contrast.
    Utility ties use lexicographic policy IDs. All risk thresholds and known
    service constraints must be fixed before evaluation.
    """
    if not math.isfinite(utility_margin) or utility_margin < 0:
        raise ValueError("utility_margin must be finite and nonnegative")
    if not 0 <= service_floor <= 1 or not 0 <= capacity_ceiling <= 1:
        raise ValueError("service and capacity limits must be fractions")
    if len({candidate.policy_id for candidate in candidates}) != len(candidates):
        raise ValueError("candidate policy IDs must be unique")
    if sum(candidate.utility_contrast_id is None for candidate in candidates) > 1:
        raise ValueError("only the unique baseline may omit its utility contrast")
    certs = _family_certificates(family, certificates, delta)
    query_by_id = {query.query_id: query for query in family.queries}
    accepted = []
    exclusions: dict[str, list[str]] = {}
    for candidate in candidates:
        reasons = []
        if candidate.service < service_floor:
            reasons.append("SERVICE_FLOOR")
        if candidate.capacity > capacity_ceiling:
            reasons.append("CAPACITY_CEILING")
        for declared_id in candidate.risk_query_ids:
            query_id = family.canonical_id(declared_id)
            if query_by_id[query_id].channel != "risk":
                raise ValueError("risk constraints must name risk-channel coordinates")
            if declared_id not in risk_thresholds or not math.isfinite(risk_thresholds[declared_id]):
                raise ValueError("every declared risk coordinate needs its fixed finite threshold")
            certificate = certs[query_id]
            if not _eligible(certificate):
                reasons.append(f"RISK_UNCERTIFIED:{declared_id}")
            elif certificate["hi"] > risk_thresholds[declared_id]:
                reasons.append(f"RISK_NOT_FEASIBLE:{declared_id}")
        utility_lower = 0.0
        if candidate.utility_contrast_id is not None:
            query_id = family.canonical_id(candidate.utility_contrast_id)
            if query_by_id[query_id].channel != "utility":
                raise ValueError("utility selection must name utility-channel coordinates")
            certificate = certs[query_id]
            if not _eligible(certificate):
                reasons.append("UTILITY_UNCERTIFIED")
            else:
                utility_lower = certificate["lo"]
                if utility_lower < -utility_margin:
                    reasons.append("UTILITY_NONINFERIORITY")
        if reasons:
            exclusions[candidate.policy_id] = reasons
        else:
            accepted.append((utility_lower, candidate.policy_id, candidate))
    common = {
        "family_digest": family.digest,
        "family_size": family.family_size,
        "nominal_delta": delta,
        "excluded_candidates": exclusions,
        "claim": "eventwise feasibility under declared assumptions; no conditional-unsafe-given-return guarantee",
    }
    if not accepted:
        return dict(common, status="ABSTAIN", returned=False, policy_id=None,
                    useful_claim=False, reason="NO_CERTIFIED_FEASIBLE_USEFUL_CANDIDATE")
    utility_lower, _, chosen = min(accepted, key=lambda item: (-item[0], item[1]))
    return dict(common, status="RETURN_CERTIFIED", returned=True, policy_id=chosen.policy_id,
                utility_lower_bound=utility_lower, service=chosen.service, capacity=chosen.capacity,
                useful_claim=True)


def propagate_affine_mixture(
    certificates: Sequence[dict],
    weights: Sequence[float],
    *,
    compatible_joint_policy: bool,
    affine_moment: bool,
) -> dict:
    """Propagate one common simultaneous event, including outcome-chosen weights.

    No mixed score is clipped again. Compatibility and affine target structure
    must have a separate design proof. Ordinary simultaneous base-coordinate
    intervals then hold for every convex combination on the same event.
    """
    if compatible_joint_policy is not True or affine_moment is not True:
        raise ValueError("mixture requires affine moments and a compatible joint-policy construction")
    values = np.asarray(weights, dtype=float)
    if not certificates or values.shape != (len(certificates),):
        raise ValueError("one weight per nonempty base-certificate list is required")
    if not np.isfinite(values).all() or np.any(values < 0) or not math.isclose(float(values.sum()), 1, abs_tol=1e-12, rel_tol=0):
        raise ValueError("mixture weights must be finite, nonnegative and sum to one")
    if not all(_eligible(certificate) for certificate in certificates):
        raise ValueError("every base coordinate must have a nonempty certified interval")
    # These fields bind base intervals to a single method/log/frozen-family
    # event; different certificate engines cannot be chosen after seeing widths.
    event_fields = ("family_digest", "family_size", "nominal_delta", "method",
                    "data_digest", "seed_namespace", "code_hash", "config_hash")
    first = certificates[0]
    for field in event_fields:
        if field not in first or any(certificate.get(field) != first[field] for certificate in certificates):
            raise ValueError(f"base certificates do not share a declared simultaneous event: {field}")
    if any(certificate.get("channel") != first.get("channel") or
           certificate.get("normalizer") != first.get("normalizer") for certificate in certificates):
        raise ValueError("mixture coordinates must have the same channel and normalization")
    if first.get("channel") is None or first.get("normalizer") is None:
        raise ValueError("mixture coordinates need explicit channel and normalization")
    return {
        "status": CERTIFIED,
        "method": "affine_interval_propagation",
        "lo": float(sum(weight * certificate["lo"] for weight, certificate in zip(values, certificates))),
        "hi": float(sum(weight * certificate["hi"] for weight, certificate in zip(values, certificates))),
        "weights": values.tolist(),
        "base_query_ids": [certificate["query_id"] for certificate in certificates],
        "channel": first["channel"],
        "normalizer": first["normalizer"],
        "family_digest": first["family_digest"],
        "family_size": first["family_size"],
        "nominal_delta": first["nominal_delta"],
        "empty_intersection": False,
        "construction": "convex propagation of base intervals; no mixed-score recertification",
    }

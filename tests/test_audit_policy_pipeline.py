"""Deterministic complete-family policy and source-separation checks."""

import numpy as np
import pytest

from comet.audit_pipeline import check_source_separation, freeze_discovered_family
from comet.policy_update import PolicyCandidate, propagate_affine_mixture, select_policy
from comet.queries import SignedQuery


def queries():
    return [SignedQuery("risk0", np.array([[0.5, 0.5], [0.5, 0.5]]), 0),
            SignedQuery("risk1", np.array([[0.2, 0.8], [0.2, 0.8]]), 0),
            SignedQuery("gain1", np.array([[-0.3, 0.3], [-0.3, 0.3]]), 0, channel="utility")]


def certificates(family):
    result = {}
    for query in family.queries:
        lo, hi = (0.02, 0.08) if query.channel == "utility" else (0.1, 0.3)
        result[query.query_id] = dict(query_id=query.query_id,
            status="CERTIFIED_UNDER_DECLARED_ASSUMPTIONS", lo=lo, hi=hi,
            empty_intersection=False, family_size=family.family_size,
            nominal_delta=0.05, coordinate_delta=0.05 / family.family_size,
            family_digest=family.digest, channel=query.channel,
            normalizer=query.normalizer, method="comet_local", data_digest="one-log",
            seed_namespace="new:E5:0001", code_hash="code", config_hash="config")
    return result


def policies():
    return [PolicyCandidate("baseline", ("risk0",), None, 0.3, 0.3),
            PolicyCandidate("improved", ("risk1",), "gain1", 0.4, 0.4)]


def test_source_splits_use_full_qualified_ids_and_reject_leakage():
    split = {name: {(name, 0), (name, 1)} for name in ("training", "discovery", "certification")}
    result = check_source_separation(split)
    assert result["status"] == "DECLARED_SOURCE_SETS_DISJOINT"
    assert result["source_counts"]["certification"] == 2
    split["certification"].add(("discovery", 0))
    with pytest.raises(ValueError, match="SOURCE_LEAKAGE"):
        check_source_separation(split)
    with pytest.raises(ValueError, match="declare training"):
        check_source_separation({"training": set()})


def test_family_deduplicates_equivalent_coordinates_but_keeps_utility_and_normalization():
    original = queries()[0]
    alias = SignedQuery("risk-alias", original.coefficients, original.offset)
    utility = SignedQuery("utility-copy", original.coefficients, original.offset, channel="utility")
    normalized = SignedQuery("normalized", original.coefficients, original.offset, normalizer=0.5)
    family = freeze_discovered_family([original, alias, utility, normalized])
    assert family.family_size == 3
    assert family.aliases["risk-alias"] == "risk0"
    assert len(family.coordinate_hashes) == 3
    assert family.digest == freeze_discovered_family([original, alias, utility, normalized]).digest
    with pytest.raises(TypeError):
        family.aliases["other"] = "risk0"


def test_family_rejects_conflicting_ids_and_empty_family():
    with pytest.raises(ValueError, match="two different"):
        freeze_discovered_family([queries()[0], SignedQuery("risk0", np.ones((2, 2)), 0)])
    with pytest.raises(ValueError, match="at least one"):
        freeze_discovered_family([])


def test_complete_family_includes_utility_budget_and_selector_uses_lower_bound():
    family = freeze_discovered_family(queries())
    certs = certificates(family)
    decision = select_policy(policies(), family, certs, {"risk0": 0.4, "risk1": 0.4})
    assert family.family_size == decision["family_size"] == 3
    assert decision["returned"] and decision["policy_id"] == "improved"
    assert decision["useful_claim"]
    certs["gain1"]["lo"] = -0.02
    decision = select_policy(policies(), family, certs, {"risk0": 0.4, "risk1": 0.4})
    assert decision["policy_id"] == "baseline"
    assert decision["excluded_candidates"]["improved"] == ["UTILITY_NONINFERIORITY"]


def test_omitted_utility_or_wrong_m_cannot_buy_selection_budget():
    family = freeze_discovered_family(queries())
    certs = certificates(family)
    certs.pop("gain1")
    with pytest.raises(ValueError, match="every canonical"):
        select_policy(policies(), family, certs, {"risk0": 0.4, "risk1": 0.4})
    certs = certificates(family)
    certs["gain1"]["family_size"] = 2
    with pytest.raises(ValueError, match="family_size"):
        select_policy(policies(), family, certs, {"risk0": 0.4, "risk1": 0.4})
    certs = certificates(family)
    certs["gain1"]["coordinate_delta"] = 0.05
    with pytest.raises(ValueError, match="coordinate budget"):
        select_policy(policies(), family, certs, {"risk0": 0.4, "risk1": 0.4})


def test_no_uncertified_fallback_and_abstention_is_not_useful_return():
    family = freeze_discovered_family(queries())
    certs = certificates(family)
    certs["risk0"]["status"] = "POINT_ONLY"
    certs["risk1"]["status"] = "ASSUMPTION_UNVERIFIED"
    decision = select_policy(policies(), family, certs, {"risk0": 0.4, "risk1": 0.4})
    assert decision["status"] == "ABSTAIN"
    assert decision["policy_id"] is None
    assert not decision["returned"] and not decision["useful_claim"]


def test_service_capacity_and_risk_thresholds_are_jointly_required():
    family = freeze_discovered_family(queries())
    certs = certificates(family)
    candidates = [PolicyCandidate("reject-all", ("risk0",), None, 0.0, 0.0),
                  PolicyCandidate("too-large", ("risk1",), "gain1", 0.7, 0.7)]
    decision = select_policy(candidates, family, certs, {"risk0": 0.4, "risk1": 0.4})
    assert not decision["returned"]
    assert "SERVICE_FLOOR" in decision["excluded_candidates"]["reject-all"]
    assert "CAPACITY_CEILING" in decision["excluded_candidates"]["too-large"]
    certs["risk0"]["hi"] = 0.4000001
    decision = select_policy(policies()[:1], family, certs, {"risk0": 0.4})
    assert not decision["returned"]


def test_empty_confidence_intersections_cannot_create_policy_feasibility():
    family = freeze_discovered_family(queries())
    certs = certificates(family)
    for query_id in ("risk0", "risk1"):
        certs[query_id].update(lo=0.5, hi=0.3, empty_intersection=True)
    assert not select_policy(policies(), family, certs, {"risk0": 0.4, "risk1": 0.4})["returned"]


def test_certificate_normalization_cannot_change_at_selection():
    family = freeze_discovered_family(queries())
    certs = certificates(family)
    certs["risk1"]["normalizer"] = 0.5
    with pytest.raises(ValueError, match="normalization changes"):
        select_policy(policies(), family, certs, {"risk0": 0.4, "risk1": 0.4})


def test_aliases_use_one_coordinate_and_ties_are_deterministic():
    family = freeze_discovered_family(queries() + [SignedQuery("alias", queries()[1].coefficients, 0)])
    certs = certificates(family)
    candidates = [PolicyCandidate("z", ("alias",), "gain1", 0.4, 0.4),
                  PolicyCandidate("a", ("risk1",), "gain1", 0.4, 0.4)]
    decision = select_policy(candidates, family, certs, {"alias": 0.4, "risk1": 0.4})
    assert decision["policy_id"] == "a"


def test_affine_mixture_uses_base_simultaneous_intervals_and_same_normalization():
    family = freeze_discovered_family(queries())
    certs = certificates(family)
    certs["risk1"].update(lo=0.2, hi=0.4)
    mixture = propagate_affine_mixture([certs["risk0"], certs["risk1"]], [0.25, 0.75],
                                      compatible_joint_policy=True, affine_moment=True)
    assert mixture["lo"] == pytest.approx(0.175)
    assert mixture["hi"] == pytest.approx(0.375)
    assert "no mixed-score" in mixture["construction"]
    with pytest.raises(ValueError, match="channel and normalization"):
        propagate_affine_mixture([certs["risk0"], certs["gain1"]], [0.5, 0.5],
                                 compatible_joint_policy=True, affine_moment=True)
    certs["risk1"]["normalizer"] = 0.5
    with pytest.raises(ValueError, match="channel and normalization"):
        propagate_affine_mixture([certs["risk0"], certs["risk1"]], [0.5, 0.5],
                                 compatible_joint_policy=True, affine_moment=True)


@pytest.mark.parametrize("weights", [[-0.1, 1.1], [0.5, 0.6], [float("nan"), 0.0]])
def test_invalid_mixture_weights_refuse(weights):
    family = freeze_discovered_family(queries())
    certs = certificates(family)
    with pytest.raises(ValueError, match="weights"):
        propagate_affine_mixture([certs["risk0"], certs["risk1"]], weights,
                                 compatible_joint_policy=True, affine_moment=True)


def test_mixture_requires_compatible_affine_policy_and_common_event():
    family = freeze_discovered_family(queries())
    certs = certificates(family)
    with pytest.raises(ValueError, match="affine moments"):
        propagate_affine_mixture([certs["risk0"]], [1], compatible_joint_policy=False, affine_moment=True)
    certs["risk1"]["method"] = "other-engine"
    with pytest.raises(ValueError, match="simultaneous event"):
        propagate_affine_mixture([certs["risk0"], certs["risk1"]], [0.5, 0.5],
                                 compatible_joint_policy=True, affine_moment=True)

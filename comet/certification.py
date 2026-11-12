"""The sole certified path: registered fixed-design synthetic bounded rewards.

Stochastic assumptions come from the registered DGP, never from empirical
correlations or a provenance label on arbitrary external data. No oracle input.
"""

from math import isfinite, nextafter, inf
from fractions import Fraction

from .conflict_graph import clique_graph, greedy_coloring, is_proper_coloring
from .dr_scores import centered_bounded_envelope, dr_score
from .robust_mean import (confidence_budget, mom_estimate, mom_radius, partition_blocks,
                          required_groups, exact_binomial_groups,
                          binomial_majority_tail_fraction, binomial_majority_tail)
from .schema import CertificationError, EXPOSURE_PROVENANCE, PROOF_MODEL


def _validate_registered_log(log):
    if log.proof_model != PROOF_MODEL:
        raise CertificationError("UNSUPPORTED_PROOF_MODEL", "UNVERIFIED_ASSUMPTION")
    config = log.config
    config.validate()
    if type(log.rows) is not tuple or type(log.family) is not tuple or log.family != config.family:
        raise CertificationError("FROZEN_REGISTERED_FAMILY_REQUIRED", "UNVERIFIED_ASSUMPTION")
    if len(log.rows) != config.B*config.n0:
        raise CertificationError("INCOMPLETE_OR_EXTRA_ROWS")
    clusters = config.n0 // config.chi
    for i, row in enumerate(log.rows):
        block, within = divmod(i, config.n0)
        cluster_local = within // config.chi
        cluster_id, x = block*clusters+cluster_local, cluster_local % 2
        expected_e = (1-config.e_by_context[x], config.e_by_context[x])
        if (row.unit_id, row.block_id, row.round_t, row.cluster_id,
            row.entity_id, row.slate_id, row.context, row.subgroup_pre_action) != (
                i, block, block+1, cluster_id, cluster_id, cluster_id, x, x):
            raise CertificationError("REGISTERED_EXOGENOUS_DESIGN_MISMATCH", "UNVERIFIED_ASSUMPTION")
        if row.features_available_at != 0 or row.exposure_provenance != EXPOSURE_PROVENANCE:
            raise CertificationError("PREACTION_OR_EXPOSURE_PROVENANCE_MISMATCH", "UNVERIFIED_ASSUMPTION")
        if type(row.observed_exposure_s) is not int or row.observed_exposure_s not in (0, 1) or row.observed_action != row.observed_exposure_s:
            raise CertificationError("EXPOSURE_SPACE_MISMATCH")
        if row.e_vector != expected_e or row.e_s_logged != expected_e[row.observed_exposure_s]:
            raise CertificationError("EXACT_LOGGING_PROPENSITY_MISMATCH", "UNVERIFIED_ASSUMPTION")
        if row.mu_hat != config.mu_hat or row.reference_f != config.reference:
            raise CertificationError("FIXED_NUISANCE_OR_REFERENCE_MISMATCH", "UNVERIFIED_ASSUMPTION")
        if not isfinite(row.reward_y) or row.reward_y not in (0, 1):
            raise CertificationError("REGISTERED_BERNOULLI_REWARD_REQUIRED")
        first = log.rows[i-within % config.chi]
        if (row.observed_exposure_s, row.reward_y) != (first.observed_exposure_s, first.reward_y):
            raise CertificationError("EXACT_CLIQUE_REPLICATION_MISMATCH", "UNVERIFIED_ASSUMPTION")


def _base(log, candidate, alpha, p):
    return {
        "estimand_id": "fixed_design_conditional_moment_v1:"+candidate.candidate_id,
        "candidate_id": candidate.candidate_id,
        "estimator": "graph_block_MOM_fixed_nuisance",
        "estimate": None, "lo": None, "hi": None,
        "nominal_delta": alpha, "certified_level": None,
        "status": "NOT_CERTIFIABLE", "reason": None,
        "proof_model": log.proof_model, "p_declared": p,
        "nu_p": None, "nu_p_source": "known_bounded_reward_preaction_envelope",
        "C_p_used": None, "stochastic_radius": None,
        "nuisance_radius": 0.0, "drift_radius": 0.0,
        "coupling_failure_epsilon": 0.0, "delta_stat": None,
        "subgroup_mass": None, "overlap_metrics": {}, "effective_support_metrics": {},
        "raw_N": len(log.rows), "retained_N": 0, "N_eff": None,
        "B": log.config.B, "n0": log.config.n0, "K": None,
        "L_min": None, "group_sizes": [], "chi_max": None,
        "chi_by_block": [], "graph_nodes": 0, "graph_edges": 0,
        "guard_exclusions": 0, "assumption_audit": {}, "seed": log.seed,
    }


def _registered_scores(log, candidate):
    """Reuse identical score arithmetic after full registered-design validation.

    Only eight (context, exposure, binary outcome) states exist per candidate.
    Row order and the arithmetic of every individual score remain unchanged.
    """
    cache, scores = {}, []
    for row in log.rows:
        key = (row.context, row.observed_exposure_s, row.reward_y)
        if key not in cache:
            cache[key] = dr_score(row.reward_y, row.observed_exposure_s,
                                  candidate.q_vector, row.e_vector, row.mu_hat,
                                  candidate.h(row.context), row.reference_f)
        scores.append(cache[key])
    return scores


def certify(log, alpha=0.05, p=1.5, mom_majority_rule="conservative_hoeffding"):
    """Simultaneous intervals over log.family, under the registered model.

    No empirical tail scale, learned nuisance, drift or coupling knobs exist.
    Unsupported/infeasible inputs return status records without intervals.
    """
    records = [_base(log, candidate, alpha, p) for candidate in log.family]
    try:
        _validate_registered_log(log)
        if not isfinite(p) or not 1 < p <= 2:
            raise CertificationError("P_MUST_BE_IN_1_2")
        delta_stat = confidence_budget(alpha)
        config = log.config
        family_size = len(log.family)
        if mom_majority_rule == "conservative_hoeffding":
            K = required_groups(family_size, delta_stat)
        elif mom_majority_rule == "exact_binomial":
            K = exact_binomial_groups(family_size, delta_stat, config.B)["K"]
        else:
            raise CertificationError("UNSUPPORTED_MOM_MAJORITY_RULE")
        for record in records:
            record.update(K=K, delta_stat=delta_stat, eta=0.125,
                          mom_majority_rule=mom_majority_rule)
        # Refuse infeasible designs before computing potentially huge exact
        # tail diagnostics (e.g. a subnormal positive confidence budget).
        groups = partition_blocks(config.B, K)
        tail = binomial_majority_tail_fraction(K)
        family_tail = family_size*tail
        family_tail_float = float(family_tail)
        if Fraction.from_float(family_tail_float) < family_tail:
            family_tail_float = nextafter(family_tail_float, inf)
        for record in records:
            record.update(K=K, delta_stat=delta_stat, eta=0.125,
                          mom_majority_rule=mom_majority_rule,
                          binomial_failure_bound=binomial_majority_tail(K),
                          binomial_familywise_failure_bound=family_tail_float,
                          binomial_familywise_failure_numerator=str(family_tail.numerator),
                          binomial_familywise_failure_denominator=str(family_tail.denominator))
        L_min = min(map(len, groups))
        graph = clique_graph(config.n0, config.chi)
        colors = greedy_coloring(graph)
        if not is_proper_coloring(graph, colors):
            raise CertificationError("INVALID_COLORING")
        chi = max(colors)+1
        N = len(log.rows)
        for candidate, record in zip(log.family, records):
            scores = _registered_scores(log, candidate)
            block_means = [sum(scores[b*config.n0:(b+1)*config.n0])/config.n0
                           for b in range(config.B)]
            if not all(isfinite(value) for value in block_means):
                raise CertificationError("NONFINITE_NUMERICAL_BLOCK_MEAN")
            estimate = mom_estimate(block_means, groups)
            # All contexts and e are exogenous. No score/outcome or truth appears here.
            envelope = max(centered_bounded_envelope(candidate.q_vector, (1-e1, e1), p)
                           for e1 in config.e_by_context)
            nu_p = envelope**(1/p)
            radius = mom_radius(p, nu_p, chi, config.n0, L_min)
            if not all(isfinite(value) for value in (estimate, radius, estimate-radius, estimate+radius)):
                raise CertificationError("NONFINITE_NUMERICAL_INTERVAL")
            h_values = [candidate.h(row.context) for row in log.rows]
            mass = sum(h_values)/N
            weights = [candidate.q_vector[row.observed_exposure_s]/row.e_s_logged
                       for row in log.rows]
            max_ratio = max(q/e for row in log.rows for q, e in zip(candidate.q_vector, row.e_vector))
            if not isfinite(max_ratio):
                raise CertificationError("IMPORTANCE_RATIO_EXCEEDS_FLOAT_RANGE")
            # Normalize before squaring to keep the diagnostic finite for finite weights.
            max_weight = max(weights)
            normalized_weights = [w/max_weight for w in weights] if max_weight else []
            importance_ess = (sum(normalized_weights)**2 / sum(w*w for w in normalized_weights)
                              if normalized_weights else 0.0)
            record.update(
                estimate=estimate, lo=estimate-radius, hi=estimate+radius,
                certified_level=1-alpha, status="CERTIFIED", reason="REGISTERED_DGP_THEOREM_A",
                nu_p=nu_p, C_p_used=32**(1/p), stochastic_radius=radius,
                subgroup_mass=mass, retained_N=N, N_eff=N/chi,
                L_min=L_min, group_sizes=list(map(len, groups)), chi_max=chi,
                chi_by_block=[chi]*config.B, graph_nodes=N,
                graph_edges=config.B*sum(map(len, graph))//2,
                overlap_metrics={"min_e": min(min(row.e_vector) for row in log.rows),
                                 "max_q_over_e": max_ratio,
                                 "max_observed_weight": max(weights)},
                effective_support_metrics={"subgroup_rows": sum(h_values),
                                           "subgroup_independent_clusters": sum(h_values)/chi,
                                           "importance_ess_diagnostic": importance_ess},
                assumption_audit={
                    "independent_macro_blocks": "registered_DGP_construction",
                    "sufficient_graph": "independent_clusters_replicated_in_exact_cliques",
                    "stable_block_targets": "same_exogenous_context_pattern_and_response_law",
                    "nuisance": "predeclared_fixed_bounded_values",
                    "moment_envelope": "proved_bounded_reward_formula_from_preaction_e_and_q",
                    "family": "frozen_before_evaluation",
                    "logging": "exact_binary_cluster_randomization",
                    "oracle_inputs": "none",
                    "scope": "single_fixed_design_window_no_closed_loop_claim",
                })
        return records
    except CertificationError as error:
        for record in records:
            record.update(status=error.status, reason=error.reason,
                          estimate=None, lo=None, hi=None, certified_level=None,
                          stochastic_radius=None)
        return records


def subgroup_ratio_bound(certificate):
    """Absolute numerator/mass bound for this fixed-design observed subgroup."""
    if certificate["status"] != "CERTIFIED":
        return {"status": certificate["status"], "upper": None, "mass_radius": 0.0}
    mass = certificate["subgroup_mass"]
    if mass <= 0:
        return {"status": "NOT_CERTIFIABLE", "reason": "ZERO_SUBGROUP_MASS",
                "upper": None, "mass_radius": 0.0}
    return {"status": "CERTIFIED", "upper": (abs(certificate["estimate"])+
             certificate["stochastic_radius"])/mass, "mass_radius": 0.0}


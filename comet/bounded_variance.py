"""Known bounded-reward graph variance and a separate Chebyshev certificate.

See theory/bounded_graph_variance.md. Independence is supplied by the registered
exogenous DGP, never inferred from observed correlations or model labels alone.
"""

from math import fsum, isfinite, sqrt

from .certification import _base, _registered_scores, _validate_registered_log
from .conflict_graph import clique_graph, greedy_coloring, is_proper_coloring
from .dr_scores import validate_support
from .robust_mean import confidence_budget
from .schema import CertificationError


def row_variance_envelope(q, e, h=1.0):
    """Known Var(Z|D) upper bound for fixed mu_hat and Y in [0,1].

    This helper does not establish the model's stochastic assumptions.
    Common q=e=0 states contribute zero; target mass on e=0 is nonidentified.
    """
    validate_support(q, e)
    if not isfinite(h) or abs(h) > 1:
        raise CertificationError("BOUNDED_PREACTION_AUDITOR_REQUIRED")
    if h == 0:
        return 0.0
    try:
        # Ratio first avoids underflow in q*q when q and e are both small.
        terms = [qs*(qs/es) for qs, es in zip(q, e) if qs > 0]
        bound = h*h*fsum(terms)
    except OverflowError as error:
        raise CertificationError("VARIANCE_ENVELOPE_EXCEEDS_FLOAT_RANGE") from error
    if not isfinite(bound) or bound <= 0:
        raise CertificationError("VARIANCE_ENVELOPE_EXCEEDS_FLOAT_RANGE")
    return bound


def graph_variance_bound(row_envelopes, graph):
    """Return (chi_used*sum(v_u), chi_used) for a sufficient graph.

    Colors are computed and checked, not supplied as a smaller caller-chosen
    number. Graph sufficiency remains a stochastic model condition.
    """
    if (not graph or len(row_envelopes) != len(graph)
            or any(not isfinite(v) or v < 0 for v in row_envelopes)):
        raise CertificationError("INVALID_GRAPH_VARIANCE_INPUT")
    colors = greedy_coloring(graph)
    if not is_proper_coloring(graph, colors):
        raise CertificationError("INVALID_COLORING")
    chi = max(colors)+1
    try:
        bound = chi*fsum(row_envelopes)
    except OverflowError as error:
        raise CertificationError("VARIANCE_ENVELOPE_EXCEEDS_FLOAT_RANGE") from error
    if not isfinite(bound):
        raise CertificationError("VARIANCE_ENVELOPE_EXCEEDS_FLOAT_RANGE")
    return bound, chi


def certify_bounded_graph(log, alpha=0.05):
    """Simultaneous fixed-design sample-mean CI under the registered model.

    No empirical scale, oracle, clipping cap or adaptive-nuisance inputs exist.
    The mean theorem permits heterogeneous block means, but this API retains the
    narrower existing registered synthetic model.
    """
    records = [_base(log, candidate, alpha, 2.0) for candidate in log.family]
    for record in records:
        record.update(
            estimator="bounded_graph_chebyshev",
            nu_p_source="not_used_known_conditional_variance",
            variance_source="known_bounded_residual_design_envelope",
            variance_bound=None, variance_multiplier=None,
            proof_reference="theory/bounded_graph_variance.md",
            family_size=len(log.family), mom_majority_rule=None,
            eta=None, binomial_familywise_failure_bound=None,
        )
    try:
        _validate_registered_log(log)
        delta = confidence_budget(alpha)
        config, N, m = log.config, len(log.rows), len(log.family)
        variance_multiplier = m/delta
        if not isfinite(variance_multiplier):
            raise CertificationError("VARIANCE_MULTIPLIER_EXCEEDS_FLOAT_RANGE")
        graph = clique_graph(config.n0, config.chi)
        _, chi = graph_variance_bound([0.0]*config.n0, graph)
        edges = config.B*sum(map(len, graph))//2
        for candidate, record in zip(log.family, records):
            scores = _registered_scores(log, candidate)
            estimate = sum(scores)/N
            envelope_by_context = {
                x: row_variance_envelope(candidate.q_vector, (1-e1, e1), candidate.h(x))
                for x, e1 in enumerate(config.e_by_context)
            }
            row_envelopes = [envelope_by_context[row.context] for row in log.rows]
            # Identical registered graph shape/colors in all blocks. The known
            # design variances, not observed scores, enter this calculation.
            variance_bound = fsum(chi*fsum(row_envelopes[b*config.n0:(b+1)*config.n0])
                                  for b in range(config.B)) / (N*N)
            radius = sqrt(m*variance_bound/delta)
            if not all(isfinite(x) for x in (estimate, variance_bound, radius,
                                             estimate-radius, estimate+radius)):
                raise CertificationError("NONFINITE_NUMERICAL_VARIANCE_INTERVAL")
            h_values = [candidate.h(row.context) for row in log.rows]
            mass = sum(h_values)/N
            design_ratios = [q/e for e1 in config.e_by_context
                             for q, e in zip(candidate.q_vector, (1-e1, e1))]
            if not all(isfinite(x) for x in design_ratios):
                raise CertificationError("IMPORTANCE_RATIO_EXCEEDS_FLOAT_RANGE")
            weights = [candidate.q_vector[row.observed_exposure_s]/row.e_s_logged
                       for row in log.rows]
            max_weight = max(weights)
            scaled = [w/max_weight for w in weights] if max_weight else []
            ess = sum(scaled)**2/sum(w*w for w in scaled) if scaled else 0.0
            record.update(
                estimate=estimate, lo=estimate-radius, hi=estimate+radius,
                certified_level=1-alpha, status="CERTIFIED",
                reason="REGISTERED_DGP_BOUNDED_GRAPH_VARIANCE_THEOREM",
                stochastic_radius=radius, variance_bound=variance_bound,
                variance_multiplier=variance_multiplier, delta_stat=delta,
                subgroup_mass=mass, retained_N=N, N_eff=N/chi,
                chi_max=chi, chi_by_block=[chi]*config.B,
                graph_nodes=N, graph_edges=edges,
                overlap_metrics={
                    "min_e": min(min(1-e1, e1) for e1 in config.e_by_context),
                    "max_q_over_e": max(design_ratios),
                    "max_observed_weight": max_weight,
                },
                effective_support_metrics={
                    "subgroup_rows": sum(h_values),
                    "subgroup_independent_clusters": sum(h_values)/chi,
                    "importance_ess_diagnostic": ess,
                },
                assumption_audit={
                    "independent_macro_blocks": "registered_DGP_construction",
                    "sufficient_graph": "independent_clusters_replicated_in_exact_cliques",
                    "nuisance": "predeclared_fixed_bounded_values",
                    "reward_bound": "registered_Bernoulli_rewards_in_0_1",
                    "variance_envelope": "h_squared_sum_q_squared_over_exact_e",
                    "target": "raw_row_fixed_design_conditional_expectation",
                    "stable_block_targets": "not_needed_by_mean_theorem_but_registered_model_is_stable",
                    "family": "frozen_before_evaluation",
                    "logging": "exact_binary_cluster_randomization",
                    "oracle_inputs": "none",
                    "scope": "single_fixed_design_window_no_closed_loop_claim",
                },
            )
        return records
    except (CertificationError, OverflowError) as error:
        status = error.status if isinstance(error, CertificationError) else "NOT_CERTIFIABLE"
        reason = error.reason if isinstance(error, CertificationError) else "VARIANCE_ENVELOPE_EXCEEDS_FLOAT_RANGE"
        for record in records:
            record.update(status=status, reason=reason, estimate=None, lo=None,
                          hi=None, certified_level=None, stochastic_radius=None,
                          variance_bound=None, variance_multiplier=None)
        return records


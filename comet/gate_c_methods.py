"""Gate C procedures with explicit theorem applicability and no oracle input.

The bounded implementation reuses the C0 graph/radius algebra. The unbounded
path uses only the independently proved, known conditional envelope in
gate_c_contract. Neither a response mean nor a fitted tail estimate enters here.
"""
from math import fsum, isfinite, sqrt

from .bounded_variance import graph_variance_bound, row_variance_envelope
from .conflict_graph import clique_graph
from .gate_c_contract import (known_centered_envelope, pareto_absolute_moment,
                              validate_evaluation)
from .informativeness import add_support_bounds
from .robust_mean import (binomial_majority_tail, confidence_budget,
                          exact_binomial_groups, mom_estimate, mom_radius,
                          partition_blocks, required_groups)
from .schema import CertificationError


METHODS = ('orig_mom', 'exact_binomial_mom', 'bounded_graph_chebyshev',
           'ips', 'dm', 'dr', 'full_feasible_range')
MOM_METHODS = ('orig_mom', 'exact_binomial_mom')
POINT_METHODS = ('ips', 'dm', 'dr')
CERTIFIED_STATUSES = ('CERTIFIED', 'CERTIFIED_UNDER_DECLARED_ASSUMPTIONS')


def constraint_decision(record, threshold):
    """A single frozen inequality; family simultaneity comes from its CI event."""
    if record['status'] == 'POINT_ONLY':
        return 'POINT_ONLY'
    if not record.get('decision_issuable'):
        return 'ABSTAIN'
    if record['clipped_hi'] <= threshold:
        return 'CERTIFIED_SAFE'
    if record['clipped_lo'] > threshold:
        return 'CERTIFIED_VIOLATION'
    return 'ABSTAIN'


def _base(method, log, cell, candidate, alpha):
    cfg = cell.design
    return dict(method=method, estimator=method, candidate_id=candidate.candidate_id,
                estimand_id='fixed_design_conditional_moment_v1:'+candidate.candidate_id,
                family_size=len(cfg.family), nominal_delta=alpha, certified_level=None,
                status='NOT_CERTIFIABLE', reason=None, certificate_applicable=False,
                estimate=None, lo=None, hi=None, stochastic_radius=None,
                nuisance_radius=0., drift_radius=0., coupling_failure_epsilon=0.,
                delta_stat=None, B=cfg.B, n0=cfg.n0, raw_N=len(log.rows), retained_N=0,
                N_eff=None, chi_max=None, graph_nodes=None, graph_edges=None,
                K=None, L_min=None, L_max=None, group_sizes=[], eta=None,
                binomial_familywise_failure_bound=None, p_declared=None,
                nu_p=None, nu_p_source=None, known_centered_p_envelope=None,
                C_p_used=None, variance_bound=None, variance_source=None,
                subgroup_mass=None, proof_model=log.proof_model, proof_reference=None,
                target_range_source='declared_conditional_response_mean_class_[0,1]',
                target_range_is_outcome_support=cell.outcome_family == 'bernoulli',
                assumptions=dict(design='exogenous_before_evaluation',
                    blocks='conditionally_independent',
                    graph='independent_clusters_copied_in_complete_chi_cliques',
                    propensity='exact_binary_exposure_S_equals_A',
                    nuisance='fixed_predeclared_bounded_values',
                    family='frozen_before_evaluation',
                    target='conditional_raw_row_window_moment',
                    outcome_family=cell.outcome_family,
                    stable_block_targets=cell.stable_targets,
                    oracle_inputs='none',scope='single_window_not_adaptive_deployment'))


def _score_arrays(log, candidate):
    """Exact DR/IPS/DM arithmetic after validation of every logged field."""
    q = candidate.q_vector
    cfg = log.config
    direct = fsum(qs*mu for qs, mu in zip(q, cfg.mu_hat))
    coefficients = {}
    for x, e1 in enumerate(cfg.e_by_context):
        h = candidate.h(x)
        coefficients[x] = (h, h*(direct-cfg.reference),
                           (q[0]/(1-e1), q[1]/e1))
    dr, ips, dm = [], [], []
    for row in log.rows:
        h, direct_score, weights = coefficients[row.context]
        s, y = row.observed_exposure_s, row.reward_y
        dr.append(direct_score+h*weights[s]*(y-cfg.mu_hat[s]))
        ips.append(h*(weights[s]*y-cfg.reference))
        dm.append(direct_score)
    if any(not isfinite(z) for array in (dr, ips, dm) for z in array):
        raise CertificationError('NONFINITE_NUMERICAL_SCORE')
    return {'dr': dr, 'ips': ips, 'dm': dm}


def _quantiles(values):
    ordered = sorted(values)
    def at(q):
        position=q*(len(ordered)-1)
        low=int(position)
        return ordered[low]+(ordered[min(low+1,len(ordered)-1)]-ordered[low])*(position-low)
    return {name:at(q) for name,q in (('min',0),('median',.5),('p95',.95),('p99',.99),('max',1))}


def _diagnostics(log, cell, candidate, arrays):
    """Descriptive tails only. No returned field feeds a certified radius."""
    q=candidate.q_vector
    design=[qs/es for e1 in cell.design.e_by_context for qs,es in zip(q,(1-e1,e1))]
    observed=[q[row.observed_exposure_s]/row.e_s_logged for row in log.rows]
    result=dict(q_over_e_design_equal_context_state_quantiles=_quantiles(design),
                q_over_e_observed_quantiles=_quantiles(observed),
                absolute_dr_score_quantiles=_quantiles([abs(z) for z in arrays['dr']]),
                diagnostics_enter_certified_radius=False,
                known_noise_p_moment_upper_bound=None,
                known_noise_p_moment_source=None)
    if cell.outcome_family=='symmetric_pareto':
        result.update(known_noise_p_moment_upper_bound=pareto_absolute_moment(cell.tail_alpha,cell.tail_scale,cell.p),
                      known_noise_p_moment_source='ideal_Pareto_integral_also_dominates_right_grid_noise')
    return result


def _one(method, log, cell, alpha, candidates, arrays, graph_info):
    cfg, N, m = cell.design, len(log.rows), len(candidates)
    chi, edges = graph_info
    delta = confidence_budget(alpha)
    if method not in METHODS:
        raise CertificationError('UNSUPPORTED_GATE_C_METHOD')
    if method in MOM_METHODS and not cell.stable_targets:
        raise CertificationError('MOM_REQUIRES_COMMON_BLOCK_TARGET_OR_PROVED_DRIFT', 'NOT_APPLICABLE')
    if method == 'bounded_graph_chebyshev' and cell.outcome_family != 'bernoulli':
        raise CertificationError('BOUNDED_Y_VARIANCE_THEOREM_NOT_APPLICABLE', 'NOT_APPLICABLE')
    groups, K = (), None
    if method in MOM_METHODS:
        K = (required_groups(m, delta) if method == 'orig_mom'
             else exact_binomial_groups(m, delta, cfg.B)['K'])
        groups = partition_blocks(cfg.B, K)
    records = []
    for candidate in candidates:
        record = _base(method, log, cell, candidate, alpha)
        h_values = [candidate.h(row.context) for row in log.rows]
        mass = fsum(h_values)/N
        record.update(delta_stat=delta, retained_N=N, N_eff=N/chi, chi_max=chi,
                      graph_nodes=N, graph_edges=edges, subgroup_mass=mass)
        score = arrays[candidate.candidate_id]
        if method in POINT_METHODS:
            record.update(status='POINT_ONLY', reason='NO_CONFIDENCE_INTERVAL_THEOREM_CLAIMED',
                          estimate=fsum(score[method])/N,
                          proof_reference='DR_or_IPS_expectation_identity;_DM_is_a_misspecified_point_baseline')
        elif method == 'full_feasible_range':
            lo, hi = -mass*cfg.reference, mass*(1-cfg.reference)
            record.update(status='CERTIFIED', reason='KNOWN_CONDITIONAL_MEAN_CLASS_ONLY',
                          certificate_applicable=True, certified_level=1.,
                          estimate=(lo+hi)/2, lo=lo, hi=hi, stochastic_radius=(hi-lo)/2,
                          proof_reference='theory/gate_c_heavy_tail_contract.md#known-target-range')
        elif method in MOM_METHODS:
            scores = score['dr']
            blocks = [sum(scores[b*cfg.n0:(b+1)*cfg.n0])/cfg.n0 for b in range(cfg.B)]
            estimate = mom_estimate(blocks, groups)
            envelope = max(known_centered_envelope(cell, candidate.q_vector, (1-e1,e1), cell.p)
                           for e1 in cfg.e_by_context)
            nu = envelope**(1/cell.p)
            L_min = min(map(len, groups))
            radius = mom_radius(cell.p, nu, chi, cfg.n0, L_min)
            record.update(status='CERTIFIED', reason='KNOWN_CONDITIONAL_P_MOMENT_AND_STABLE_BLOCK_TARGET',
                          certificate_applicable=True, certified_level=1-alpha,
                          estimate=estimate, lo=estimate-radius, hi=estimate+radius,
                          stochastic_radius=radius, p_declared=cell.p, nu_p=nu,
                          known_centered_p_envelope=envelope,
                          nu_p_source='known_conditional_DGP_envelope_not_estimated',
                          C_p_used=32**(1/cell.p), K=K, L_min=L_min,
                          L_max=max(map(len, groups)), group_sizes=list(map(len, groups)),
                          eta=.125, binomial_familywise_failure_bound=m*binomial_majority_tail(K),
                          proof_reference=('theory/theorem_to_code_contract.md;'
                              'theory/exact_binomial_mom.md;theory/gate_c_heavy_tail_contract.md'))
        else:
            v_by_context = {x: row_variance_envelope(candidate.q_vector, (1-e1,e1), candidate.h(x))
                            for x,e1 in enumerate(cfg.e_by_context)}
            variance = chi*fsum(v_by_context[row.context] for row in log.rows)/(N*N)
            radius = sqrt(m*variance/delta)
            estimate = fsum(score['dr'])/N
            record.update(status='CERTIFIED', reason='KNOWN_BOUNDED_RESIDUAL_GRAPH_VARIANCE',
                          certificate_applicable=True, certified_level=1-alpha,
                          estimate=estimate, lo=estimate-radius, hi=estimate+radius,
                          stochastic_radius=radius, p_declared=2., variance_bound=variance,
                          variance_source='h_squared_sum_q_squared_over_exact_e',
                          proof_reference='theory/bounded_graph_variance.md')
        numeric = [record[k] for k in ('estimate','lo','hi','stochastic_radius') if record[k] is not None]
        if not all(isfinite(z) for z in numeric):
            raise CertificationError('NONFINITE_NUMERICAL_INTERVAL')
        records.append(record)
    return records


def certify_methods(log, cell, alpha=.05, methods=METHODS, threshold_per_mass=.2):
    """Compare predeclared methods; no post-outcome selected-method guarantee.

    All methods use the identical log. Each method has a separate simultaneous
    guarantee over cell.design.family; alpha is not a joint guarantee over the
    collection of methods or levels. Return refusals without fabricated bounds.
    """
    candidates = cell.design.family
    records = []
    try:
        if not isfinite(threshold_per_mass):
            raise CertificationError('NONFINITE_CONSTRAINT_THRESHOLD')
        validate_evaluation(cell, log)
        confidence_budget(alpha)
        graph = clique_graph(cell.design.n0, cell.design.chi)
        _, chi = graph_variance_bound([0.]*cell.design.n0, graph)
        graph_info = chi, cell.design.B*sum(map(len, graph))//2
        arrays = {candidate.candidate_id:_score_arrays(log,candidate) for candidate in candidates}
        diagnostics = {candidate.candidate_id:_diagnostics(log,cell,candidate,arrays[candidate.candidate_id])
                       for candidate in candidates}
        for method in methods:
            try:
                records.extend(_one(method,log,cell,alpha,candidates,arrays,graph_info))
            except (CertificationError, OverflowError) as error:
                status = error.status if isinstance(error,CertificationError) else 'NOT_CERTIFIABLE'
                reason = error.reason if isinstance(error,CertificationError) else 'NUMERICAL_RANGE_EXCEEDED'
                records.extend(dict(_base(method,log,cell,candidate,alpha),status=status,reason=reason)
                               for candidate in candidates)
        for record in records:
            record.update(diagnostics[record['candidate_id']])
            # Geometry remains known for inapplicable methods such as the
            # bounded-Y certificate in F; an interval is still absent.
            record.update(N_eff=len(log.rows)/chi, chi_max=chi,
                          graph_nodes=len(log.rows),graph_edges=graph_info[1])
    except (CertificationError, OverflowError) as error:
        status = error.status if isinstance(error,CertificationError) else 'NOT_CERTIFIABLE'
        reason = error.reason if isinstance(error,CertificationError) else 'NUMERICAL_RANGE_EXCEEDED'
        records = [dict(_base(method,log,cell,candidate,alpha),status=status,reason=reason)
                   for method in methods for candidate in candidates]
    output = []
    for record in records:
        candidate = next(c for c in candidates if c.candidate_id == record['candidate_id'])
        # The support is determined by the frozen exogenous context layout,
        # not by a response mean or an observed-outcome statistic.
        clusters = cell.design.n0//cell.design.chi
        mass = sum(candidate.h(c%2) for c in range(clusters))/clusters
        record['subgroup_mass'] = mass
        low, high = -mass*cell.design.reference, mass*(1-cell.design.reference)
        record = add_support_bounds(record, low, high)
        record['constraint_threshold'] = threshold_per_mass*mass
        record['decision'] = constraint_decision(record, record['constraint_threshold'])
        record['abstention_reason'] = (record['reason'] if not record['decision_issuable']
                                      else 'INTERVAL_STRADDLES_FROZEN_THRESHOLD' if record['decision']=='ABSTAIN'
                                      else None)
        output.append(record)
    return output


def evaluate_method(method, log, cell, alpha=.05, threshold_per_mass=.2):
    return certify_methods(log,cell,alpha,(method,),threshold_per_mass)

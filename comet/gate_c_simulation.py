"""Gate C logging and potential-outcome simulation; does not evaluate truth.

Design, graph structure and fixed nuisance are deterministic. Only logging and
potential-outcome streams are consumed; reserved streams remain separate.
"""

from random import Random

from .gate_c_contract import validate_stream_seeds
from .schema import CertificationError, LoggedEvaluation, LoggedRow


def _response_location(context, exposure, block, stable_targets):
    """DGP parameter, never an estimator input or tail-envelope input."""
    numerator = ((4, 12), (7, 16))[context][exposure]
    if not stable_targets:
        numerator += 1 if block % 2 == 0 else -1
    return numerator/20


def _draw_bernoulli(rng, probability):
    """Exact integer lottery for the supplied floating-point probability."""
    numerator, denominator = float(probability).as_integer_ratio()
    return int(rng.randrange(denominator) < numerator)


def _shared_bernoulli_potentials(rng, probabilities):
    """Exact marginal means with one common dyadic uniform per cluster."""
    ratios = [float(p).as_integer_ratio() for p in probabilities]
    denominator = max(d for _, d in ratios)  # float denominators are powers of 2
    draw = rng.randrange(denominator)
    return tuple(int(draw < n*(denominator//d)) for n,d in ratios)


def _pareto_from_unit(uniform, sign, alpha, scale):
    """Inverse CDF of a symmetric Pareto; no clipping or empirical scaling."""
    if not 0 < uniform <= 1 or sign not in (-1, 1):
        raise CertificationError("INVALID_PARETO_BASE_DRAW")
    return sign*scale*uniform**(-1/alpha)


def _symmetric_pareto(rng, alpha, scale):
    # A right-endpoint grid avoids U=0 without censoring extreme rewards.
    # Its absolute p-moment is bounded by the ideal continuous integral.
    uniform = (rng.getrandbits(53)+1) / 2**53
    sign = 1 if rng.getrandbits(1) else -1
    return _pareto_from_unit(uniform, sign, alpha, scale)


def generate_evaluation(cell, stream_seeds, run_id):
    """Return observed logs only; the independent oracle is called elsewhere."""
    cell.validate()
    validate_stream_seeds(stream_seeds)
    if not isinstance(run_id, str) or not run_id:
        raise CertificationError("GATE_C_RUN_ID_REQUIRED")
    config = cell.design
    logging_rng = Random(stream_seeds["logging_exposure"])
    outcome_rng = Random(stream_seeds["potential_outcomes"])
    rows = []
    clusters = config.n0 // config.chi
    for block in range(config.B):
        for cluster in range(clusters):
            cluster_id, context = block*clusters+cluster, cluster % 2
            e1 = config.e_by_context[context]
            e = (1-e1, e1)
            exposure = _draw_bernoulli(logging_rng, e1)
            means = tuple(_response_location(context, s, block, cell.stable_targets) for s in (0, 1))
            if cell.outcome_family == "bernoulli":
                # A common uniform couples the two potential outcomes of one
                # cluster; different clusters and blocks use fresh draws.
                potentials = _shared_bernoulli_potentials(outcome_rng, means)
            else:
                potentials = tuple(mean+_symmetric_pareto(outcome_rng, cell.tail_alpha, cell.tail_scale)
                                   for mean in means)
            for copy in range(config.chi):
                rows.append(LoggedRow(
                    unit_id=block*config.n0+cluster*config.chi+copy,
                    round_t=block+1, block_id=block, cluster_id=cluster_id,
                    entity_id=cluster_id, slate_id=cluster_id, context=context,
                    subgroup_pre_action=context, features_available_at=0,
                    observed_action=exposure, observed_exposure_s=exposure,
                    e_s_logged=e[exposure], e_vector=e, reward_y=potentials[exposure],
                    reference_f=config.reference, mu_hat=config.mu_hat))
    return LoggedEvaluation(config, config.family, tuple(rows),
                            stream_seeds["logging_exposure"], cell.proof_model)


"""Independent cluster draws and fresh macro-blocks; fixed exogenous design."""

from hashlib import sha256
from random import Random

from .schema import LoggedEvaluation, LoggedRow
from .truth import OracleTruth, RESPONSE_MEANS, exact_moments


def _stream(seed, name):
    digest = sha256(f"COMET-v1:{seed}:{name}".encode()).digest()
    return Random(int.from_bytes(digest, "big"))


def generate_evaluation(config, seed):
    config.validate()
    logging_rng, outcome_rng = _stream(seed, "logging"), _stream(seed, "potential-outcomes")
    rows, potential_outcomes = [], []
    clusters = config.n0 // config.chi
    for b in range(config.B):
        for c in range(clusters):
            cluster_id, x = b*clusters+c, c % 2
            e1 = config.e_by_context[x]
            e = (1-e1, e1)
            exposure = int(logging_rng.random() < e1)
            # Shared U couples two potential outcomes, independently of assignment.
            u = outcome_rng.random()
            outcomes = tuple(int(u < mu) for mu in RESPONSE_MEANS[x])
            potential_outcomes.append((cluster_id, *outcomes))
            for copy in range(config.chi):
                rows.append(LoggedRow(
                    unit_id=b*config.n0+c*config.chi+copy, round_t=b+1,
                    block_id=b, cluster_id=cluster_id, entity_id=cluster_id,
                    slate_id=cluster_id, context=x, subgroup_pre_action=x,
                    features_available_at=0, observed_action=exposure,
                    observed_exposure_s=exposure, e_s_logged=e[exposure],
                    e_vector=e, reward_y=outcomes[exposure],
                    reference_f=config.reference, mu_hat=config.mu_hat))
    log = LoggedEvaluation(config, config.family, tuple(rows), seed)
    truth = OracleTruth(exact_moments(config), RESPONSE_MEANS, tuple(potential_outcomes))
    return log, truth


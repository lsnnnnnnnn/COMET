"""Gate C pre-outcome model contract; no simulator or oracle imports.

Schema validation checks declared inputs, not hidden stochastic assumptions.
The model proof is in theory/gate_c_heavy_tail_contract.md.
"""

from dataclasses import dataclass, fields
from math import isfinite

from .dr_scores import centered_bounded_envelope, validate_support
from .schema import (CertificationError, EXPOSURE_PROVENANCE, PROOF_MODEL,
                     SyntheticConfig)

STREAM_NAMES = (
    "design_context", "graph_shocks", "logging_exposure", "potential_outcomes",
    "nuisance_discovery_pilot", "evaluation_outcomes", "truth_mc",
)
ACTIVE_STREAMS = ("logging_exposure", "potential_outcomes")
GATE_C_MODEL_VERSION = "gate_c_exogenous_replicated_cliques_v1"


@dataclass(frozen=True)
class GateCCell:
    cell_id: str
    design: SyntheticConfig
    p: float = 2.0
    outcome_family: str = "bernoulli"
    tail_alpha: float = 1.75
    tail_scale: float = 0.1
    stable_targets: bool = True
    nuisance_source: str = "fixed_predeclared"

    @property
    def proof_model(self):
        # The bounded stable construction has exactly the original C0 law.
        if self.outcome_family == "bernoulli" and self.stable_targets:
            return PROOF_MODEL
        stability = "stable" if self.stable_targets else "exogenous_alternating_drift"
        return f"{GATE_C_MODEL_VERSION}:{self.outcome_family}:{stability}"

    @property
    def known_conditional_mean_bounds(self):
        # A model-class restriction, not the oracle response locations.
        return (0.0, 1.0)

    def validate(self):
        if not isinstance(self.cell_id, str) or not self.cell_id:
            raise CertificationError("GATE_C_CELL_ID_REQUIRED")
        if not isinstance(self.design, SyntheticConfig):
            raise CertificationError("GATE_C_FROZEN_DESIGN_REQUIRED")
        self.design.validate()
        if type(self.stable_targets) is not bool:
            raise CertificationError("GATE_C_STABILITY_FLAG_MUST_BE_BOOL")
        if self.nuisance_source != "fixed_predeclared":
            raise CertificationError("GATE_C_FIXED_NUISANCE_REQUIRED", "UNVERIFIED_ASSUMPTION")
        if self.outcome_family not in ("bernoulli", "symmetric_pareto"):
            raise CertificationError("GATE_C_UNSUPPORTED_OUTCOME_FAMILY", "NOT_APPLICABLE")
        if not isfinite(self.p) or not 1 < self.p <= 2:
            raise CertificationError("P_MUST_BE_IN_1_2", "NOT_APPLICABLE")
        if self.outcome_family == "symmetric_pareto":
            if (not isfinite(self.tail_alpha) or self.tail_alpha <= 1
                    or not isfinite(self.tail_scale) or self.tail_scale <= 0):
                raise CertificationError("GATE_C_INVALID_PARETO_PARAMETERS", "NOT_APPLICABLE")
            if self.p >= self.tail_alpha:
                raise CertificationError("P_MOMENT_NOT_FINITE_FOR_DECLARED_TAIL", "NOT_APPLICABLE")


def cell_from_dict(raw):
    """Convert the explicit frozen JSON cell; description is metadata only."""
    raw = dict(raw)
    raw.pop("description", None)
    allowed = {f.name for f in fields(GateCCell)}
    if set(raw) - allowed:
        raise CertificationError("GATE_C_UNKNOWN_CELL_FIELDS")
    design = dict(raw["design"])
    for key in ("e_by_context", "mu_hat", "q_probs", "auditors"):
        design[key] = tuple(design[key])
    raw["design"] = SyntheticConfig(**design)
    cell = GateCCell(**raw)
    cell.validate()
    return cell


def validate_stream_seeds(stream_seeds):
    if set(stream_seeds) != set(STREAM_NAMES):
        raise CertificationError("GATE_C_SEVEN_NAMED_STREAMS_REQUIRED")
    if any(type(seed) is not int or seed < 0 for seed in stream_seeds.values()):
        raise CertificationError("GATE_C_STREAM_SEEDS_MUST_BE_NONNEGATIVE_INTEGERS")
    if len(set(stream_seeds.values())) != len(STREAM_NAMES):
        raise CertificationError("GATE_C_STREAM_SEEDS_MUST_BE_DISTINCT")


def pareto_absolute_moment(alpha, scale, p):
    """Known E|epsilon|^p for the ideal symmetric Pareto noise, p<alpha."""
    if (not all(isfinite(x) for x in (alpha, scale, p))
            or alpha <= 1 or scale <= 0 or p <= 0 or p >= alpha):
        raise CertificationError("P_MOMENT_NOT_FINITE_FOR_DECLARED_TAIL", "NOT_APPLICABLE")
    value = alpha * scale**p / (alpha-p)
    if not isfinite(value):
        raise CertificationError("MOMENT_ENVELOPE_EXCEEDS_FLOAT_RANGE")
    return value


def known_centered_envelope(cell, q, e, p):
    """Known conditional centered score p-moment bound, without outcome data.

    For Pareto rewards use location-class [0,1], fixed bounded nuisance and
    known noise moment; no true response location or empirical tail is read.
    """
    cell.validate()
    validate_support(q, e)
    if not isfinite(p) or not 1 < p <= 2:
        raise CertificationError("P_MUST_BE_IN_1_2", "NOT_APPLICABLE")
    if cell.outcome_family == "bernoulli":
        return centered_bounded_envelope(q, e, p)
    noise_p = pareto_absolute_moment(cell.tail_alpha, cell.tail_scale, p)
    try:
        importance_p = sum(qs**p * es**(1-p) for qs, es in zip(q, e) if qs > 0)
        value = 2**(2*p-1) * (1 + 2**(p-1)*(1+noise_p)*importance_p)
    except OverflowError as error:
        raise CertificationError("MOMENT_ENVELOPE_EXCEEDS_FLOAT_RANGE") from error
    if not isfinite(value):
        raise CertificationError("MOMENT_ENVELOPE_EXCEEDS_FLOAT_RANGE")
    return value


def validate_evaluation(cell, log):
    """Validate observable consistency with the explicitly declared DGP.

    A hidden shock or falsely asserted training provenance cannot generally be
    detected from these structural checks. The theorem requires the actual law.
    """
    cell.validate()
    if log.config != cell.design or log.proof_model != cell.proof_model:
        raise CertificationError("GATE_C_DECLARED_MODEL_MISMATCH", "UNVERIFIED_ASSUMPTION")
    config = cell.design
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
        if (type(row.observed_exposure_s) is not int or row.observed_exposure_s not in (0, 1)
                or row.observed_action != row.observed_exposure_s):
            raise CertificationError("EXPOSURE_SPACE_MISMATCH")
        if row.e_vector != expected_e or row.e_s_logged != expected_e[row.observed_exposure_s]:
            raise CertificationError("EXACT_LOGGING_PROPENSITY_MISMATCH", "UNVERIFIED_ASSUMPTION")
        if row.mu_hat != config.mu_hat or row.reference_f != config.reference:
            raise CertificationError("FIXED_NUISANCE_OR_REFERENCE_MISMATCH", "UNVERIFIED_ASSUMPTION")
        if not isfinite(row.reward_y):
            raise CertificationError("NONFINITE_REWARD")
        if cell.outcome_family == "bernoulli" and row.reward_y not in (0, 1):
            raise CertificationError("REGISTERED_BERNOULLI_REWARD_REQUIRED")
        first = log.rows[i-within % config.chi]
        if (row.observed_exposure_s, row.reward_y) != (first.observed_exposure_s, first.reward_y):
            raise CertificationError("EXACT_CLIQUE_REPLICATION_MISMATCH", "UNVERIFIED_ASSUMPTION")


"""Immutable inputs. A registered DGP supplies assumptions; data checks do not."""

from dataclasses import dataclass
from math import isfinite

PROOF_MODEL = "independent_blocks_exact_chi_cliques_fixed_design_v1"
EXPOSURE_PROVENANCE = "binary_cluster_randomization:S=A"


class CertificationError(ValueError):
    def __init__(self, reason, status="NOT_CERTIFIABLE"):
        super().__init__(reason)
        self.reason = reason
        self.status = status


class SupportError(CertificationError):
    """q puts mass on an exposure unidentifiable under the logger."""


@dataclass(frozen=True)
class Candidate:
    q1: float
    auditor: str

    @property
    def candidate_id(self):
        # repr is round-trip safe; :g silently merges nearby policy probabilities.
        return f"q{float(self.q1)!r}__{self.auditor}"

    @property
    def q_vector(self):
        return (1.0 - self.q1, self.q1)

    def h(self, context):
        if self.auditor == "all":
            return 1
        if self.auditor == "group1":
            return int(context == 1)
        raise CertificationError("UNSUPPORTED_AUDITOR")


@dataclass(frozen=True)
class SyntheticConfig:
    B: int = 128
    n0: int = 32
    chi: int = 4
    e_by_context: tuple = (0.2, 0.4)
    mu_hat: tuple = (0.5, 0.5)
    reference: float = 0.25
    q_probs: tuple = (0.25, 0.75)
    auditors: tuple = ("all", "group1")

    @property
    def family(self):
        return tuple(Candidate(q, h) for q in self.q_probs for h in self.auditors)

    def validate(self):
        if any(type(v) is not int or v <= 0 for v in (self.B, self.n0, self.chi)):
            raise CertificationError("B_N0_CHI_MUST_BE_POSITIVE_INTEGERS")
        if self.n0 % self.chi:
            raise CertificationError("INCOMPLETE_CLIQUE")
        if any(type(v) is not tuple for v in
               (self.e_by_context, self.mu_hat, self.q_probs, self.auditors)):
            raise CertificationError("DESIGN_SEQUENCES_MUST_BE_IMMUTABLE_TUPLES")
        if len(self.e_by_context) != 2 or len(self.mu_hat) != 2:
            raise CertificationError("BINARY_CONTEXT_AND_EXPOSURE_REQUIRED")
        if any(not isfinite(x) or not 0 < x < 1 for x in self.e_by_context):
            raise SupportError("SYNTHETIC_LOGGING_REQUIRES_BOTH_EXPOSURES_SUPPORTED")
        if any(not isfinite(x) or not 0 <= x <= 1
               for x in (*self.mu_hat, self.reference, *self.q_probs)):
            raise CertificationError("BOUNDED_FIXED_DESIGN_VALUES_REQUIRED")
        if not self.q_probs or not self.auditors:
            raise CertificationError("EMPTY_FAMILY")
        if len(set(self.q_probs)) != len(self.q_probs) or len(set(self.auditors)) != len(self.auditors):
            raise CertificationError("DUPLICATE_CANDIDATES")
        if any(h not in ("all", "group1") for h in self.auditors):
            raise CertificationError("UNSUPPORTED_AUDITOR")


@dataclass(frozen=True)
class LoggedRow:
    unit_id: int
    round_t: int
    block_id: int
    cluster_id: int
    entity_id: int
    slate_id: int
    context: int
    subgroup_pre_action: int
    features_available_at: int
    observed_action: int
    observed_exposure_s: int
    e_s_logged: float
    e_vector: tuple
    reward_y: float
    reference_f: float
    mu_hat: tuple
    exposure_provenance: str = EXPOSURE_PROVENANCE


@dataclass(frozen=True)
class LoggedEvaluation:
    config: SyntheticConfig
    family: tuple
    rows: tuple
    seed: int
    proof_model: str = PROOF_MODEL


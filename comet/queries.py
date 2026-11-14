"""Frozen signed moment queries, including direct paired policy contrasts."""

from dataclasses import dataclass

import numpy as np


def _readonly_float(values: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    return np.frombuffer(array.tobytes(), dtype=np.float64).reshape(array.shape)


@dataclass(frozen=True, eq=False)
class SignedQuery:
    """The target is mean(sum_s d[u,s] mu[u,s] - offset[u])/normalizer.

    Coefficients and offsets already include auditor weights. A level query has
    d=h*q; a paired contrast has d=h*(q-q0). The positive normalizer must be a
    known fixed-design quantity, such as subgroup mass; this API does not
    certify estimated denominators. ``provenance`` is a declaration, not a
    statistical test of independence from evaluation outcomes.
    """

    query_id: str
    coefficients: np.ndarray
    offset: np.ndarray
    channel: str = "risk"
    normalizer: float = 1.0
    provenance: str = "fixed_design"

    def __post_init__(self) -> None:
        coefficients = np.asarray(self.coefficients, dtype=np.float64)
        if coefficients.ndim != 2 or 0 in coefficients.shape:
            raise ValueError("coefficients must be a nonempty N by S array")
        offset = np.asarray(self.offset, dtype=np.float64)
        if offset.ndim == 0:
            offset = np.full(coefficients.shape[0], float(offset))
        if offset.shape != (coefficients.shape[0],):
            raise ValueError("offset must contain one value per row")
        if not np.all(np.isfinite(coefficients)) or not np.all(np.isfinite(offset)):
            raise ValueError("query coefficients and offsets must be finite")
        if not np.isfinite(self.normalizer) or self.normalizer <= 0:
            raise ValueError("normalizer must be a positive finite known design quantity")
        if not isinstance(self.query_id, str) or not self.query_id:
            raise ValueError("query_id must be a nonempty string")
        if not isinstance(self.channel, str) or not self.channel:
            raise ValueError("channel must be a nonempty string")
        if not isinstance(self.provenance, str) or not self.provenance:
            raise ValueError("query provenance must be declared")
        object.__setattr__(self, "coefficients", _readonly_float(coefficients))
        object.__setattr__(self, "offset", _readonly_float(offset))
        object.__setattr__(self, "normalizer", float(self.normalizer))

    @property
    def n_rows(self) -> int:
        return self.coefficients.shape[0]

    @property
    def n_states(self) -> int:
        return self.coefficients.shape[1]

    @property
    def active_mask(self) -> np.ndarray:
        active = np.any(self.coefficients != 0, axis=1)
        return np.frombuffer(active.tobytes(), dtype=np.bool_)

    def validate_support(self, exposure_probabilities: np.ndarray) -> None:
        """Check supplied exact-law dimensions and query support, not truth of e."""
        e = np.asarray(exposure_probabilities, dtype=np.float64)
        if e.shape != self.coefficients.shape or not np.all(np.isfinite(e)):
            raise ValueError("exposure probabilities must be a finite N by S array")
        if np.any(e < 0) or np.any(e > 1) or not np.allclose(e.sum(axis=1), 1, rtol=0, atol=1e-12):
            raise ValueError("each exposure probability row must be a distribution")
        if np.any((self.coefficients != 0) & (e == 0)):
            raise ValueError("NONIDENTIFIED: a nonzero query coefficient has zero exposure support")

    def known_term(self, nuisance: np.ndarray) -> float:
        fit = np.asarray(nuisance, dtype=np.float64)
        if fit.shape != self.coefficients.shape or not np.all(np.isfinite(fit)):
            raise ValueError("nuisance must be a finite N by S array")
        return float(np.mean(np.sum(self.coefficients * fit, axis=1) - self.offset) / self.normalizer)

    def target(self, mean_response: np.ndarray) -> float:
        """Evaluation helper; estimation must not be supplied oracle means."""
        return self.known_term(mean_response)

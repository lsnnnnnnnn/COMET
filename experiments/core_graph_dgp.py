"""Design and generator for the post-C-STAT E1 core, not a frozen protocol.

The conditional law has independent logging words and independent symmetric
outcome primitives. Shared primitive incidence, rather than a domain network,
determines the sufficient graph of the whole score vector. Locations vary by
row, so a connected graph never means replicated observations or equal targets.

The certifier-facing dictionary deliberately excludes response locations and
oracle targets. ``evaluate_oracle`` belongs to analysis after all methods and
decisions have finished. Defining a draw function here does not authorize or
record any scientific replication; the final protocol remains separately frozen.
"""

from dataclasses import dataclass
import hashlib
from typing import Hashable, Mapping

import numpy as np

from comet.queries import SignedQuery
from comet.residual_truncation import AssumptionContract
from comet.source_graph import SourceGraph


WORD_GRID = 2**32
TAIL_EXPONENT = 1.75


def _readonly(values, dtype=float):
    array = np.asarray(values, dtype=dtype)
    return np.frombuffer(array.tobytes(), dtype=array.dtype).reshape(array.shape)


def dyadic_probabilities(probabilities):
    """Nearest 32-bit dyadic probabilities, with exact-half ties rounded upward.

    The declared logging law is the returned dyadic value, not the unrounded
    sigmoid. Uniform integers K in {0,...,2**32-1} expose action 1 iff K<cutoff.
    """
    probabilities = np.asarray(probabilities, dtype=float)
    if not np.isfinite(probabilities).all() or np.any(probabilities < 0) or np.any(probabilities > 1):
        raise ValueError("probabilities must lie in [0,1]")
    cutoffs = np.floor(probabilities * WORD_GRID + 0.5).astype(np.uint64)
    return _readonly(cutoffs, np.uint64), _readonly(cutoffs / WORD_GRID)


def fixed_features(n):
    if type(n) is not int or n < 8:
        raise ValueError("the four-feature core design requires integer N>=8")
    u = (np.arange(n, dtype=float) + 0.5) / n
    return _readonly(np.column_stack((
        2 * u - 1,
        np.sin(6 * np.pi * u + 0.37),
        np.cos(10 * np.pi * u + 0.19),
        np.sin(14 * np.pi * u + 0.73),
    )))


def _response_locations(x):
    n = len(x)
    u = (np.arange(n, dtype=float) + 0.5) / n
    return np.column_stack((
        0.35 + 0.1 * np.sin(2 * np.pi * u) + 0.05 * x[:, 0],
        0.55 + 0.1 * x[:, 1] + 0.05 * np.sin(4 * np.pi * u),
    ))


def _sigmoid(values):
    return 1 / (1 + np.exp(-np.asarray(values, dtype=float)))


def _noise_sources(n, graph_kind, namespace):
    rows = []
    for row in range(n):
        private = (namespace, "outcome", "private", row)
        if graph_kind == "independent":
            sources = [(private, 0.1)]
        elif graph_kind == "cycle":
            sources = [(private, 0.04),
                       ((namespace, "outcome", "cycle", row), 0.03),
                       ((namespace, "outcome", "cycle", (row + 1) % n), 0.03)]
        elif graph_kind == "triangles":
            # Factor j influences j,j+1,j+2: the resulting graph is a
            # connected chain of overlapping triangles, not disjoint cliques.
            sources = [(private, 0.025)] + [
                ((namespace, "outcome", "triangle", factor), 0.025)
                for factor in range(max(0, row - 2), min(row, n - 3) + 1)
            ]
        else:
            raise ValueError("graph_kind must be independent, cycle or triangles")
        rows.append(tuple(sources))
    return tuple(rows)


@dataclass(frozen=True)
class CoreGraphDesign:
    n: int
    graph_kind: str
    overlap: str
    outcome: str
    namespace: str
    x: np.ndarray
    logging_cutoffs: np.ndarray
    exposure: np.ndarray
    nuisance: np.ndarray
    queries: tuple[SignedQuery, ...]
    subgroup_masses: Mapping[str, float]
    row_sources: tuple[frozenset[Hashable], ...]
    outcome_source_ids: tuple[Hashable, ...]
    outcome_source_indices: np.ndarray
    outcome_source_coefficients: np.ndarray
    graph: SourceGraph
    residual_moments: np.ndarray
    p: float

    @property
    def source_ids(self):
        return frozenset(source for row in self.row_sources for source in row)

    @property
    def certifier_inputs(self):
        """Arguments accepted by make_plan; no location, truth or outcome."""
        return {
            "exposure": self.exposure,
            "nuisance": self.nuisance,
            "residual_moments": self.residual_moments,
            "graph": self.graph,
            "contract": AssumptionContract(
                exogenous_design=True, exact_exposure=True,
                conditional_randomization=True, independent_nuisance=True,
                frozen_family=True, sufficient_source_graph=True,
                valid_residual_moments=True,
                graph_provenance="independent_primitive_intersection:" + self.graph_kind,
                moment_provenance=("bounded_[0,1]_midpoint_residual_0.5" if self.outcome == "bounded"
                                   else "declared_[0,1]_location_class_and_symmetric_Pareto_Minkowski"),
                conditioning_provenance="fixed_features_and_midpoint_before_all_logging_and_outcomes",
            ),
            "p": self.p,
            "outcome_bounds": (0.0, 1.0) if self.outcome == "bounded" else None,
            "mean_bounds": (0.0, 1.0),
        }


def build_core_design(n=32768, graph_kind="independent", overlap="moderate",
                      outcome="bounded", namespace="COMET-new-core-design"):
    """Build one declared E1 design without sampling any outcome or assignment.

    The four policies and four auditors produce sixteen distinct raw moment
    coordinates. Subgroup masses are retained separately for normalized-width
    analysis. All policies are compatible independent binary assignment laws.
    """
    if not isinstance(namespace, str) or not namespace:
        raise ValueError("a nonempty new-study source namespace is required")
    if overlap not in ("moderate", "weak") or outcome not in ("bounded", "heavy"):
        raise ValueError("unsupported overlap or outcome regime")
    x = fixed_features(n)
    tendency = _sigmoid(x[:, 0] - x[:, 1])
    e1 = 0.2 + 0.6 * tendency if overlap == "moderate" else 0.005 + 0.045 * tendency
    cutoffs, e1 = dyadic_probabilities(e1)
    exposure = _readonly(np.column_stack((1 - e1, e1)))
    nuisance = _readonly(np.full((n, 2), 0.5))
    policy_values = (
        np.full(n, 0.5),
        _sigmoid(0.4 + 0.8 * x[:, 0] - 0.5 * x[:, 1]),
        _sigmoid(-0.3 + 0.6 * x[:, 1] + 0.4 * x[:, 2]),
        _sigmoid(0.1 + 0.5 * x[:, 0] * x[:, 2] - 0.4 * x[:, 3]),
    )
    auditors = (
        ("all", np.ones(n)),
        ("x1_positive", (x[:, 0] > 0).astype(float)),
        ("x2_positive", (x[:, 1] > 0).astype(float)),
        ("x1_x3_positive", ((x[:, 0] > 0) & (x[:, 2] > 0)).astype(float)),
    )
    queries = []
    masses = {}
    for policy, q1 in enumerate(policy_values):
        # The target binary law is also explicitly finite/dyadic.
        _, q1 = dyadic_probabilities(q1)
        q = np.column_stack((1 - q1, q1))
        for auditor, h in auditors:
            query_id = f"policy{policy}/{auditor}"
            queries.append(SignedQuery(query_id, h[:, None] * q, 0,
                                       provenance="fixed_design:" + namespace))
            masses[query_id] = float(h.mean())
    rows = _noise_sources(n, graph_kind, namespace)
    unique_sources = {}
    max_sources = max(map(len, rows))
    indices = np.zeros((n, max_sources), dtype=np.int64)
    coefficients = np.zeros((n, max_sources))
    row_sources = []
    for row, sources in enumerate(rows):
        for column, (source, coefficient) in enumerate(sources):
            if source not in unique_sources:
                unique_sources[source] = len(unique_sources)
            indices[row, column] = unique_sources[source]
            coefficients[row, column] = coefficient
        row_sources.append(frozenset(
            [(namespace, "logging", row)] + [source for source, _ in sources]
        ))
    graph = SourceGraph.from_sources(row_sources)
    p = 2.0 if outcome == "bounded" else 1.5
    if outcome == "bounded":
        # Exactly the same declared residual range is supplied to every method.
        residual_moments = np.full((n, 2), 0.5**p)
    else:
        # ||sum_j c_j Z_j||_p <= sum_j |c_j| (a/(a-p))**(1/p).
        # Add the declared location-class deviation from the midpoint nuisance.
        noise_lp = np.sum(np.abs(coefficients), axis=1) * (
            TAIL_EXPONENT / (TAIL_EXPONENT - p)) ** (1 / p)
        residual_moments = np.repeat((0.5 + noise_lp[:, None]) ** p, 2, axis=1)
    return CoreGraphDesign(
        n, graph_kind, overlap, outcome, namespace, x, cutoffs, exposure, nuisance,
        tuple(queries), masses, tuple(row_sources), tuple(unique_sources),
        _readonly(indices, np.int64), _readonly(coefficients), graph,
        _readonly(residual_moments), p,
    )


@dataclass(frozen=True)
class CoreLog:
    actions: np.ndarray
    outcomes: np.ndarray
    data_digest: str
    seed_namespace: str


def _log_from_arrays(design, action_words, primitive_values, seed_namespace):
    words = np.asarray(action_words)
    values = np.asarray(primitive_values, dtype=float)
    if words.shape != (design.n,) or words.dtype.kind not in "iu" or np.any(words < 0) or np.any(words >= WORD_GRID):
        raise ValueError("one unsigned 32-bit-range logging word per row is required")
    if values.shape != (len(design.outcome_source_ids),) or not np.isfinite(values).all():
        raise ValueError("one finite outcome primitive per declared source is required")
    if design.outcome == "bounded" and np.any((values != -1) & (values != 1)):
        raise ValueError("bounded primitive fixtures must be Rademacher signs")
    if design.outcome == "heavy" and np.any(np.abs(values) < 1):
        raise ValueError("heavy primitive fixtures must lie on symmetric Pareto support")
    actions = (words.astype(np.uint64) < design.logging_cutoffs).astype(np.uint8)
    noise = np.sum(values[design.outcome_source_indices] * design.outcome_source_coefficients, axis=1)
    locations = _response_locations(design.x)
    outcomes = locations[np.arange(design.n), actions] + noise
    digest = hashlib.sha256(actions.tobytes() + outcomes.astype("<f8").tobytes()).hexdigest()
    return CoreLog(_readonly(actions, np.uint8), _readonly(outcomes), digest, seed_namespace)


def generate_from_primitives(design, action_words, outcome_primitives: Mapping[Hashable, float],
                             *, seed_namespace=None):
    """Transparent deterministic fixture path, with no RNG or oracle export."""
    if set(outcome_primitives) != set(design.outcome_source_ids):
        raise ValueError("primitive fixture keys must equal the declared outcome-source set")
    values = np.array([outcome_primitives[source] for source in design.outcome_source_ids])
    return _log_from_arrays(design, action_words, values,
                            seed_namespace or design.namespace + "/explicit-primitives")


def _role_rng(design, seed, role):
    payload = f"{design.namespace}\0{seed}\0{role}".encode()
    return np.random.default_rng(int.from_bytes(hashlib.sha256(payload).digest(), "little"))


def draw_core_log(design, seed):
    """Draw one NEW-study log; callers must freeze and account for its run ID.

    Symmetric Pareto magnitudes use midpoint dyadic U=(K+.5)/2**32. In exact
    arithmetic its p-moment is <=a/(a-p): u**(-p/a) is convex and the midpoint
    sum is below its integral. Sign words are independent. The resulting finite
    grid has finite variance; it is not literally an infinite-variance machine
    law. Ordinary float powers are not outward-rounded machine proofs.
    """
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    logging = _role_rng(design, seed, "logging")
    outcomes = _role_rng(design, seed, "outcome-primitives")
    words = logging.integers(0, WORD_GRID, size=design.n, dtype=np.uint64)
    count = len(design.outcome_source_ids)
    signs = np.where(outcomes.integers(0, 2, size=count, dtype=np.uint8) == 0, -1.0, 1.0)
    if design.outcome == "bounded":
        primitives = signs
    else:
        magnitude_words = outcomes.integers(0, WORD_GRID, size=count, dtype=np.uint64)
        u = (magnitude_words.astype(float) + 0.5) / WORD_GRID
        primitives = signs * u ** (-1 / TAIL_EXPONENT)
    return _log_from_arrays(design, words, primitives, f"{design.namespace}/seed/{seed}")


def evaluate_oracle(design):
    """Analysis-only truths; call after estimators and selectors have finished."""
    means = _response_locations(design.x)
    return {query.query_id: query.target(means) for query in design.queries}

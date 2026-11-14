"""Draft E5 source-separated discovery, certification and policy-update model.

All choices in this module are DRAFT_INPUT_RECONCILIATION_PENDING. The missing
blueprint is not claimed as read. Constructors and primitive-fixture functions
make no random draws. Analytical means occur only in the logger/evaluator path,
never in nuisance fitting, discovered-family construction or selection inputs.
"""

from dataclasses import dataclass
import hashlib
import itertools
import json
from types import MappingProxyType

import numpy as np

from comet.audit_pipeline import check_source_separation, freeze_discovered_family
from comet.policy_update import PolicyCandidate
from comet.queries import SignedQuery
from comet.residual_truncation import AssumptionContract
from comet.source_graph import SourceGraph
from experiments.core_graph_dgp import WORD_GRID, dyadic_probabilities, fixed_features


DRAFT = "DRAFT_INPUT_RECONCILIATION_PENDING"
SPLIT_SIZES = {"training": 4096, "discovery": 8192, "certification": 32768}
TRADEOFF_GRID = (0.0, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0)


def _readonly(values, dtype=float):
    x = np.asarray(values, dtype=dtype)
    return np.frombuffer(x.tobytes(), dtype=x.dtype).reshape(x.shape)


def _sigmoid(x):
    return 1 / (1 + np.exp(-np.clip(x, -700, 700)))


def pipeline_cells():
    """The proposed eight design cells, with no simulated trials."""
    return tuple(dict(graph_kind=g, overlap=e, world=w, status=DRAFT)
                 for g, e, w in itertools.product(
                     ("independent", "cycle"), ("moderate", "weak"), ("null", "mixed")))


def _planted_mask(x):
    # The literal search uses zero thresholds, so this three-way region is not
    # provided as a feature and is not exactly an elementary searched rule.
    return (x[:, 0] > -0.15) & (x[:, 1] > 0.1) & (x[:, 2] > -0.05)


def _pipeline_locations(x, world):
    """Generator/evaluator only: action zero has known zero response."""
    planted = _planted_mask(x).astype(float)
    smooth_fourway = _sigmoid(3 * np.prod(x, axis=1))
    risk = 0.20 + 0.06 * _sigmoid(1.3 * x[:, 0] - 0.8 * x[:, 1]) + 0.025 * x[:, 2]
    utility = 0.45 + 0.15 * _sigmoid(1.2 * x[:, 0] + 0.8 * x[:, 2]) + 0.05 * x[:, 1]
    if world == "mixed":
        risk = risk + 0.30 * planted + 0.05 * smooth_fourway
        utility = utility + 0.12 * planted + 0.03 * smooth_fourway
    return {
        "risk": np.column_stack((np.zeros(len(x)), risk)),
        "utility": np.column_stack((np.zeros(len(x)), utility)),
    }


def _basis(x):
    # A training-only nuisance model with main and pairwise terms; it does not
    # contain the planted three-way threshold or the smooth four-way response.
    return np.column_stack((np.ones(len(x)), x,
                            *(x[:, j] * x[:, k] for j, k in itertools.combinations(range(4), 2))))


@dataclass(frozen=True)
class PipelineSplitDesign:
    name: str
    namespace: str
    graph_kind: str
    overlap: str
    world: str
    x: np.ndarray
    logging_cutoffs: np.ndarray
    exposure: np.ndarray
    row_sources: tuple
    channel_source_ids: object
    source_indices: np.ndarray
    source_coefficients: np.ndarray
    graph: SourceGraph
    status: str = DRAFT

    @property
    def n(self):
        return len(self.x)

    @property
    def source_ids(self):
        return frozenset(source for row in self.row_sources for source in row)


@dataclass(frozen=True)
class PipelineDesign:
    splits: object
    namespace: str
    source_separation: object
    risk_threshold: float = 0.32
    utility_margin: float = 0.01
    service_floor: float = 0.2
    capacity_ceiling: float = 0.6
    status: str = DRAFT


def _build_split(name, n, graph_kind, overlap, world, namespace):
    x = fixed_features(n)
    propensity = _sigmoid(x[:, 0] - x[:, 1])
    e1 = 0.2 + 0.6 * propensity if overlap == "moderate" else 0.005 + 0.045 * propensity
    cutoffs, e1 = dyadic_probabilities(e1)
    exposure = _readonly(np.column_stack((1 - e1, e1)))
    namespace = namespace + "/" + name
    indices = np.zeros((n, 1 if graph_kind == "independent" else 3), dtype=np.int64)
    coefficients = np.zeros(indices.shape, dtype=float)
    source_ids = {channel: {} for channel in ("risk", "utility")}
    row_sources = []
    for row in range(n):
        primitive_positions = (("private", row, 0.1),) if graph_kind == "independent" else (
            ("private", row, 0.04), ("cycle", row, 0.03), ("cycle", (row + 1) % n, 0.03))
        row_ids = {(namespace, "logging", row)}
        for channel in ("risk", "utility"):
            for column, (kind, primitive, coefficient) in enumerate(primitive_positions):
                source = (namespace, channel, kind, primitive)
                if source not in source_ids[channel]:
                    source_ids[channel][source] = len(source_ids[channel])
                indices[row, column] = source_ids[channel][source]
                coefficients[row, column] = coefficient
                row_ids.add(source)
        # Both channels have identical incidence positions, but distinct atom
        # names and independent source values. Logging is shared across channels.
        row_sources.append(frozenset(row_ids))
    return PipelineSplitDesign(
        name, namespace, graph_kind, overlap, world, x, cutoffs, exposure,
        tuple(row_sources), MappingProxyType({c: tuple(ids) for c, ids in source_ids.items()}),
        _readonly(indices, np.int64), _readonly(coefficients),
        SourceGraph.from_sources(row_sources),
    )


def build_pipeline_design(graph_kind="cycle", overlap="moderate", world="mixed",
                          namespace="COMET-E5-draft", split_sizes=None):
    """No sampled outcomes: build three globally source-disjoint fixed designs."""
    if graph_kind not in ("independent", "cycle") or overlap not in ("moderate", "weak"):
        raise ValueError("unsupported E5 dependence/overlap cell")
    if world not in ("null", "mixed") or not isinstance(namespace, str) or not namespace:
        raise ValueError("declare null/mixed world and a nonempty new namespace")
    sizes = SPLIT_SIZES if split_sizes is None else split_sizes
    if set(sizes) != set(SPLIT_SIZES):
        raise ValueError("training, discovery and certification split sizes are all required")
    splits = {name: _build_split(name, sizes[name], graph_kind, overlap, world, namespace)
              for name in SPLIT_SIZES}
    separation = check_source_separation({name: split.source_ids for name, split in splits.items()})
    return PipelineDesign(MappingProxyType(splits), namespace, MappingProxyType(separation))


@dataclass(frozen=True)
class PipelineLog:
    actions: np.ndarray
    outcomes: object
    data_digest: str
    source_namespace: str
    seed_namespace: str


def _pipeline_log_from_arrays(split, action_words, channel_values, seed_namespace):
    words = np.asarray(action_words)
    if words.shape != (split.n,) or words.dtype.kind not in "iu" or np.any(words < 0) or np.any(words >= WORD_GRID):
        raise ValueError("supply one unsigned-32-bit-range logging word per row")
    if set(channel_values) != {"risk", "utility"}:
        raise ValueError("distinct risk and utility primitive collections are required")
    actions = (words.astype(np.uint64) < split.logging_cutoffs).astype(np.uint8)
    locations = _pipeline_locations(split.x, split.world)
    outcomes = {}
    for channel in ("risk", "utility"):
        values = np.asarray(channel_values[channel], dtype=float)
        if (values.shape != (len(split.channel_source_ids[channel]),)
                or not np.isfinite(values).all() or np.any((values != -1) & (values != 1))):
            raise ValueError("bounded source primitives must be Rademacher signs")
        noise = np.sum(values[split.source_indices] * split.source_coefficients, axis=1)
        # Unserved outcomes are structurally known zero, rather than an
        # unobserved response guessed from a nuisance model.
        response = actions * (locations[channel][:, 1] + noise)
        if np.any(response < 0) or np.any(response > 1):
            raise ValueError("generator violated its analytically bounded response class")
        outcomes[channel] = _readonly(response)
    digest = hashlib.sha256()
    digest.update(actions.tobytes())
    for channel in ("risk", "utility"):
        digest.update(outcomes[channel].astype("<f8").tobytes())
    return PipelineLog(_readonly(actions, np.uint8), MappingProxyType(outcomes),
                       digest.hexdigest(), split.namespace, seed_namespace or split.namespace)


def generate_pipeline_from_primitives(split, action_words, channel_primitives, *, seed_namespace=None):
    """Explicit words/signs only; no RNG. Source signs are symmetric in the law.

    Fixtures supply one value per declared independent Rademacher atom. The
    actual stochastic driver must draw those atoms independently; this schema
    cannot establish that fact from a realized collection of signs.
    """
    if set(channel_primitives) != {"risk", "utility"}:
        raise ValueError("distinct risk and utility primitive collections are required")
    channel_values = {}
    for channel in ("risk", "utility"):
        mapping = channel_primitives[channel]
        if set(mapping) != set(split.channel_source_ids[channel]):
            raise ValueError("primitive keys do not match the channel's declared source set")
        channel_values[channel] = np.array([mapping[source] for source in split.channel_source_ids[channel]])
    return _pipeline_log_from_arrays(split, action_words, channel_values, seed_namespace)


def pipeline_role_seed(split, seed, role):
    """Deterministic role key; calling this function consumes no RNG stream."""
    if type(seed) is not int or seed < 0 or role not in ("logging", "risk", "utility"):
        raise ValueError("declare a nonnegative trial seed and logging/risk/utility role")
    payload = f"{split.namespace}\0{seed}\0{role}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest(), "little")


def draw_pipeline_split(split, seed):
    """Define the future frozen driver; no draw occurs unless called.

    Logging words and the two response channels use separate source-qualified
    role streams; training/discovery/certification have disjoint namespaces.
    All signs/words are generated as arrays, without a per-run source dictionary.
    The physical random-source independence is a declared model, not something
    the seed hashes or observed signs empirically prove.
    """
    logging = np.random.default_rng(pipeline_role_seed(split, seed, "logging"))
    words = logging.integers(0, WORD_GRID, size=split.n, dtype=np.uint64)
    values = {}
    for channel in ("risk", "utility"):
        rng = np.random.default_rng(pipeline_role_seed(split, seed, channel))
        values[channel] = np.where(rng.integers(0, 2,
            size=len(split.channel_source_ids[channel]), dtype=np.uint8) == 0, -1.0, 1.0)
    return _pipeline_log_from_arrays(split, words, values, f"{split.namespace}/seed/{seed}")


def _check_log(split, log):
    if log.source_namespace != split.namespace or log.actions.shape != (split.n,):
        raise ValueError("log belongs to a different source split or design")
    if set(log.outcomes) != {"risk", "utility"}:
        raise ValueError("both response channels are required")


@dataclass(frozen=True)
class TrainingFit:
    coefficients: object
    source_namespace: str
    data_digest: str
    digest: str

    def predict(self, x):
        features = _basis(x)
        return MappingProxyType({
            channel: _readonly(np.column_stack((np.zeros(len(x)),
                                               np.clip(features @ coefficients, 0, 1))))
            for channel, coefficients in self.coefficients.items()
        })


def fit_nuisance(training_design, training_log, *, ridge=1.0):
    """Fit each bounded channel once on training exposures; no oracle input."""
    if training_design.name != "training":
        raise ValueError("nuisance fitting requires the independent training split")
    _check_log(training_design, training_log)
    if not np.isfinite(ridge) or ridge <= 0:
        raise ValueError("ridge must be a predeclared positive finite value")
    phi = _basis(training_design.x)
    observed = training_log.actions == 1
    coefficients = {}
    for channel in ("risk", "utility"):
        if np.any(observed):
            matrix = phi[observed]
            fitted = np.linalg.solve(matrix.T @ matrix + ridge * np.eye(matrix.shape[1]),
                                     matrix.T @ training_log.outcomes[channel][observed])
        else:
            fitted = np.zeros(phi.shape[1])
            fitted[0] = 0.5
        coefficients[channel] = _readonly(fitted)
    digest = hashlib.sha256(training_log.data_digest.encode())
    digest.update(float(ridge).hex().encode())
    for channel in ("risk", "utility"):
        digest.update(coefficients[channel].astype("<f8").tobytes())
    return TrainingFit(MappingProxyType(coefficients), training_design.namespace,
                       training_log.data_digest, digest.hexdigest())


@dataclass(frozen=True)
class AuditorRule:
    literals: tuple
    discovery_score: float

    @property
    def rule_id(self):
        return "&".join(f"x{feature + 1}{'>' if positive else '<='}0"
                        for feature, positive in self.literals)

    def mask(self, x):
        result = np.ones(len(x), dtype=bool)
        for feature, positive in self.literals:
            result &= x[:, feature] > 0 if positive else x[:, feature] <= 0
        return result


def discover_auditors(discovery_design, discovery_log, fit, certification_x, *,
                      max_depth=4, max_rules=4, minimum_mass=0.02):
    """Rank a finite shallow-conjunction search using discovery residuals only."""
    if discovery_design.name != "discovery":
        raise ValueError("auditor search requires the independent discovery split")
    _check_log(discovery_design, discovery_log)
    if not 1 <= max_depth <= 4 or not 1 <= max_rules <= 4 or not 0 < minimum_mass <= 1:
        raise ValueError("draft search permits depth<=4, at most four rules and positive mass")
    if fit.source_namespace == discovery_design.namespace:
        raise ValueError("training and discovery sources must be distinct")
    nuisance = fit.predict(discovery_design.x)["risk"][:, 1]
    pseudo_response = (nuisance + discovery_log.actions / discovery_design.exposure[:, 1]
                       * (discovery_log.outcomes["risk"] - nuisance))
    scored = []
    for depth in range(1, max_depth + 1):
        for features in itertools.combinations(range(4), depth):
            for signs in itertools.product((False, True), repeat=depth):
                rule = AuditorRule(tuple(zip(features, signs)), 0.0)
                mask = rule.mask(discovery_design.x)
                if mask.mean() < minimum_mass or rule.mask(certification_x).mean() < minimum_mass:
                    continue
                score = float(np.mean(pseudo_response[mask]))
                scored.append(AuditorRule(rule.literals, score))
    # All ties are fixed by lexical literal codes. Duplicate certification masks
    # do not consume an auditor slot or inflate the family size.
    selected, masks = [], set()
    for rule in sorted(scored, key=lambda value: (-value.discovery_score, value.rule_id)):
        mask_bytes = rule.mask(certification_x).tobytes()
        if mask_bytes not in masks:
            masks.add(mask_bytes)
            selected.append(rule)
        if len(selected) == max_rules:
            break
    return tuple(selected)


@dataclass(frozen=True)
class PolicyRule:
    policy_id: str
    tradeoff: float | None
    center: float
    scale: float
    intercept: float
    fit: TrainingFit

    def probabilities(self, x):
        if self.tradeoff is None:
            values = np.full(len(x), 0.35)
        else:
            predictions = self.fit.predict(x)
            score = (predictions["utility"][:, 1] - self.tradeoff * predictions["risk"][:, 1]
                     - self.center) / self.scale
            values = 0.05 + 0.9 * _sigmoid(score + self.intercept)
        return dyadic_probabilities(values)[1]


def generate_policy_rules(fit, discovery_x, *, tradeoff_grid=TRADEOFF_GRID):
    """At most eight deployable product-Bernoulli policies, baseline included."""
    if len(tradeoff_grid) > 7 or len(set(tradeoff_grid)) != len(tradeoff_grid):
        raise ValueError("at most seven distinct tradeoff values accompany the baseline")
    if not all(np.isfinite(value) and value >= 0 for value in tradeoff_grid):
        raise ValueError("tradeoff grid must be finite and nonnegative")
    predictions = fit.predict(discovery_x)
    rules = [PolicyRule("policy0", None, 0, 1, 0, fit)]
    for index, tradeoff in enumerate(tradeoff_grid, 1):
        score = predictions["utility"][:, 1] - tradeoff * predictions["risk"][:, 1]
        center, scale = float(score.mean()), max(0.05, float(score.std()))
        standardized = (score - center) / scale
        left, right = -50.0, 50.0
        # Design/training-only calibration to expected discovery service .45.
        for _ in range(60):
            midpoint = (left + right) / 2
            if np.mean(0.05 + 0.9 * _sigmoid(standardized + midpoint)) < 0.45:
                left = midpoint
            else:
                right = midpoint
        rules.append(PolicyRule(f"policy{index}", float(tradeoff), center, scale,
                                (left + right) / 2, fit))
    return tuple(rules)


def policy_known_constraints(probabilities, *, service_floor=0.2, capacity_ceiling=0.6):
    q = np.asarray(probabilities, dtype=float)
    if q.ndim != 1 or not len(q) or not np.isfinite(q).all() or np.any(q < 0) or np.any(q > 1):
        raise ValueError("a finite policy probability per row is required")
    service = float(q.mean())
    return dict(service=service, capacity=service,
                eligible=service >= service_floor and service <= capacity_ceiling)


@dataclass(frozen=True)
class FrozenPipeline:
    design: PipelineDesign
    fit: TrainingFit
    auditors: tuple
    policy_rules: tuple
    policy_probabilities: object
    candidates: tuple
    family: object
    risk_thresholds: object
    nuisance: object
    discovery_digest: str
    pipeline_digest: str
    candidate_source_splits: tuple = ("training", "discovery", "fixed certification contexts")
    status: str = DRAFT

    @property
    def family_digest(self):
        return self.family.digest

    def certifier_inputs(self, channel):
        """No truths: independent fitted nuisance plus actual residual ranges."""
        if channel not in ("risk", "utility"):
            raise ValueError("unknown response channel")
        split = self.design.splits["certification"]
        nuisance = self.nuisance[channel]
        residual_bound = np.maximum(np.abs(nuisance), np.abs(1 - nuisance))
        residual_bound[:, 0] = 0.0  # structural action-zero response/nuisance
        return {
            "exposure": split.exposure, "nuisance": nuisance,
            "residual_moments": residual_bound**2, "graph": split.graph, "p": 2.0,
            "outcome_bounds": (0.0, 1.0), "mean_bounds": (0.0, 1.0),
            "contract": AssumptionContract(
                exogenous_design=True, exact_exposure=True, conditional_randomization=True,
                independent_nuisance=True, frozen_family=True, sufficient_source_graph=True,
                valid_residual_moments=True,
                graph_provenance="split_disjoint_independent_atoms/" + split.graph_kind,
                moment_provenance="bounded_[0,1]_actual_fitted_residual_range; action0_known_zero",
                conditioning_provenance="independent training/discovery plus fixed certification X",
            ),
        }


def fit_and_freeze_pipeline(design, training_log, discovery_log, *, max_rules=4,
                            max_depth=4, minimum_mass=0.02, ridge=1.0,
                            tradeoff_grid=TRADEOFF_GRID):
    """Freeze every risk and utility coordinate without certification labels.

    This freezes a trial's selected family algebraically. It does not freeze a
    scientific protocol or authorize a confirmatory run. Configuration status
    remains DRAFT_INPUT_RECONCILIATION_PENDING.
    """
    training, discovery, certification = (design.splits[name] for name in SPLIT_SIZES)
    check_source_separation({name: split.source_ids for name, split in design.splits.items()})
    _check_log(training, training_log)
    _check_log(discovery, discovery_log)
    fit = fit_nuisance(training, training_log, ridge=ridge)
    auditors = discover_auditors(discovery, discovery_log, fit, certification.x,
                                 max_depth=max_depth, max_rules=max_rules,
                                 minimum_mass=minimum_mass)
    policy_rules = generate_policy_rules(fit, discovery.x, tradeoff_grid=tradeoff_grid)
    probabilities = {rule.policy_id: rule.probabilities(certification.x) for rule in policy_rules}
    masks = [("all", np.ones(certification.n))] + [
        (rule.rule_id, rule.mask(certification.x).astype(float)) for rule in auditors]
    baseline = probabilities["policy0"]
    queries, candidates, thresholds = [], [], {}
    for rule in policy_rules:
        q1 = probabilities[rule.policy_id]
        risk_ids = []
        for rule_id, mask in masks:
            query_id = f"risk/{rule.policy_id}/{rule_id}"
            coefficients = np.column_stack((np.zeros(certification.n), mask * q1))
            queries.append(SignedQuery(query_id, coefficients, 0, channel="risk",
                                       normalizer=float(mask.mean()),
                                       provenance="source-independent-discovery:" + discovery_log.data_digest))
            risk_ids.append(query_id)
            thresholds[query_id] = design.risk_threshold
        utility_id = None
        if rule.policy_id != "policy0":
            utility_id = f"utility/{rule.policy_id}-minus-policy0"
            queries.append(SignedQuery(utility_id,
                                       np.column_stack((np.zeros(certification.n), q1 - baseline)),
                                       0, channel="utility", provenance="independent training/discovery"))
        known = policy_known_constraints(q1, service_floor=design.service_floor,
                                         capacity_ceiling=design.capacity_ceiling)
        candidates.append(PolicyCandidate(rule.policy_id, tuple(risk_ids), utility_id,
                                           known["service"], known["capacity"]))
    family = freeze_discovered_family(queries)
    nuisance = fit.predict(certification.x)
    digest = hashlib.sha256(json.dumps({
        "family": family.digest, "training": fit.digest, "discovery": discovery_log.data_digest,
        "status": DRAFT, "max_rules": max_rules, "max_depth": max_depth,
        "minimum_mass": minimum_mass, "tradeoff_grid": list(tradeoff_grid),
        "constraints": [design.risk_threshold, design.utility_margin,
                        design.service_floor, design.capacity_ceiling],
    }, sort_keys=True).encode()).hexdigest()
    return FrozenPipeline(design, fit, auditors, policy_rules, MappingProxyType(probabilities),
                          tuple(candidates), family, MappingProxyType(thresholds), nuisance,
                          discovery_log.data_digest, digest)


def evaluate_pipeline(frozen, certificates, selection, *, methods_finished=False):
    """Oracle join after all engines/selection. One output is one whole trial."""
    if methods_finished is not True:
        raise ValueError("oracle metrics may be joined only after all methods and decisions finish")
    split = frozen.design.splits["certification"]
    locations = _pipeline_locations(split.x, split.world)
    targets = {query.query_id: query.target(locations[query.channel]) for query in frozen.family.queries}
    candidates = {candidate.policy_id: candidate for candidate in frozen.candidates}
    thresholds = frozen.risk_thresholds

    def target(query_id):
        return targets[frozen.family.canonical_id(query_id)]

    def interval(query_id):
        certificate = certificates.get(frozen.family.canonical_id(query_id), {})
        lo, hi = certificate.get("lo"), certificate.get("hi")
        if certificate.get("status") != "CERTIFIED_UNDER_DECLARED_ASSUMPTIONS":
            return None
        if lo is None or hi is None or not np.isfinite(lo) or not np.isfinite(hi) or lo > hi:
            return None
        return lo, hi

    false_safe = false_violation = true_detected = any_true_detected = False
    for candidate in frozen.candidates:
        for query_id in candidate.risk_query_ids:
            bounds = interval(query_id)
            if bounds is None:
                continue
            truth, threshold = target(query_id), thresholds[query_id]
            false_safe |= bounds[1] <= threshold and truth > threshold
            false_violation |= bounds[0] > threshold and truth <= threshold
            detected = bounds[0] > threshold and truth > threshold
            any_true_detected |= detected
            true_detected |= detected and query_id.rsplit("/", 1)[1] != "all"
    false_utility_claim = False
    for candidate in frozen.candidates:
        query_id = candidate.utility_contrast_id
        if query_id is not None and interval(query_id) is not None:
            lo, _ = interval(query_id)
            truth = target(query_id)
            false_utility_claim |= (lo >= -frozen.design.utility_margin and truth < -frozen.design.utility_margin)
            false_utility_claim |= lo > 0 and truth <= 0
    covered = all(interval(query.query_id) is not None
                  and interval(query.query_id)[0] <= targets[query.query_id] <= interval(query.query_id)[1]
                  for query in frozen.family.queries)
    all_eligible = all(interval(query.query_id) is not None for query in frozen.family.queries)
    values, feasible, risk_safe, utility_noninferior, service_feasible, gaps = {}, {}, {}, {}, {}, {}
    for candidate in frozen.candidates:
        q = frozen.policy_probabilities[candidate.policy_id]
        values[candidate.policy_id] = float(np.mean(q * locations["utility"][:, 1]))
        gaps[candidate.policy_id] = max(target(query_id) - thresholds[query_id]
                                        for query_id in candidate.risk_query_ids)
        risk_safe[candidate.policy_id] = gaps[candidate.policy_id] <= 0
        utility_gain = 0 if candidate.utility_contrast_id is None else target(candidate.utility_contrast_id)
        utility_noninferior[candidate.policy_id] = utility_gain >= -frozen.design.utility_margin
        service_feasible[candidate.policy_id] = (
            candidate.service >= frozen.design.service_floor
            and candidate.capacity <= frozen.design.capacity_ceiling)
        feasible[candidate.policy_id] = (risk_safe[candidate.policy_id]
            and utility_noninferior[candidate.policy_id] and service_feasible[candidate.policy_id])
    returned = bool(selection.get("returned", False))
    selected_id = selection.get("policy_id") if returned else None
    if returned and selected_id not in candidates:
        raise ValueError("selection returned a policy outside the frozen family")
    safe_useful = returned and feasible[selected_id]
    selected = candidates.get(selected_id)
    baseline_value = values["policy0"]
    robust_values = []
    for candidate in frozen.candidates:
        if not feasible[candidate.policy_id]:
            continue
        risk_slack = True
        for query_id in candidate.risk_query_ids:
            certificate = certificates.get(frozen.family.canonical_id(query_id), {})
            radius = certificate.get("radius")
            if (interval(query_id) is None or radius is None or not np.isfinite(radius)
                    or radius < 0 or target(query_id) + 2 * radius > thresholds[query_id]):
                risk_slack = False
                break
        utility_slack = True
        if candidate.utility_contrast_id is not None:
            query_id = candidate.utility_contrast_id
            certificate = certificates.get(frozen.family.canonical_id(query_id), {})
            radius = certificate.get("radius")
            utility_slack = (interval(query_id) is not None and radius is not None
                             and np.isfinite(radius) and radius >= 0
                             and target(query_id) - 2 * radius >= -frozen.design.utility_margin)
        if risk_slack and utility_slack:
            robust_values.append(values[candidate.policy_id])
    planted = _planted_mask(split.x) if split.world == "mixed" else np.zeros(split.n, dtype=bool)
    ious = [np.sum(rule.mask(split.x) & planted) / np.sum(rule.mask(split.x) | planted)
            for rule in frozen.auditors if np.any(rule.mask(split.x) | planted)]
    return {
        "status": DRAFT, "unit": "one_independent_complete_pipeline_trial",
        "family_size": frozen.family.family_size, "family_covered": bool(covered),
        "all_coordinates_certified": bool(all_eligible),
        "any_false_safe": bool(false_safe), "any_false_violation": bool(false_violation),
        "any_false_utility_claim": bool(false_utility_claim),
        "any_false_claim": bool(false_safe or false_violation or false_utility_claim),
        "true_violation_discovered_and_certified": bool(true_detected),
        "any_true_violation_certified": bool(any_true_detected),
        "returned": returned, "returned_policy_id": selected_id,
        "returned_baseline": returned and selected_id == "policy0",
        "return_and_unsafe": returned and not risk_safe[selected_id],
        "return_and_risk_safe": returned and risk_safe[selected_id],
        "return_and_utility_noninferior": returned and utility_noninferior[selected_id],
        "return_and_service_feasible": returned and service_feasible[selected_id],
        "return_and_infeasible": returned and not feasible[selected_id],
        "return_and_safe_and_useful": bool(safe_useful),
        "unsafe_given_return_numerator": int(returned and not risk_safe[selected_id]),
        "unsafe_given_return_denominator": int(returned),
        "true_utility": values[selected_id] if returned else None,
        "utility_gain": values[selected_id] - baseline_value if returned else None,
        "expected_service": selected.service if returned else 0.0,
        "expected_capacity": selected.capacity if returned else 0.0,
        "maximum_true_risk_violation": max(0.0, gaps[selected_id]) if returned else None,
        "oracle_best_feasible_candidate_value": max((values[key] for key in values if feasible[key]), default=None),
        "robust_slack_comparator_value": max(robust_values, default=None),
        "robust_slack_definition": "evaluation-only: every risk truth+2r<=threshold and utility contrast truth-2r>=-margin",
        "discovery_best_planted_iou": max(ious, default=None),
        "targets": targets,
        "unsafe_definition": "violation of any frozen true risk constraint; utility/service feasibility reported separately",
        "useful_definition": "known service/capacity feasible AND true utility contrast>=-prespecified margin",
        "scope": "finite-design synthetic decision evidence; no long-term or conditional-return-risk theorem",
    }


def pipeline_trial_record(metrics, *, run_id, cell, method, delta, certificates,
                          coverage_applicable, failure_status=None):
    """Map already-evaluated metrics to WholeTrialSummary, without oracle work.

    ``coverage_applicable`` is determined by the frozen method/model contract,
    not by success on this trial. Missing/numerically failed coordinates remain
    in the whole-trial denominator of an eligible engine. Risk safety and joint
    useful return retain distinct definitions.
    """
    mapping = {
        "any_false_claim": "any_false_claim", "any_false_safe": "any_false_safe",
        "any_false_violation": "any_false_violation",
        "true_violation_detected": "any_true_violation_certified",
        "discovered_and_certified": "true_violation_discovered_and_certified",
        "returned": "returned", "return_unsafe": "return_and_unsafe",
        "return_safe_useful": "return_and_safe_and_useful",
    }
    events = {}
    for destination, source in mapping.items():
        value = metrics[source]
        if not isinstance(value, (bool, np.bool_)):
            raise ValueError("pipeline joint-event metrics must be booleans")
        events[destination] = bool(value)
    if type(coverage_applicable) is not bool:
        raise ValueError("method/model coverage applicability must be predeclared as a boolean")
    failures = set()
    if failure_status:
        failures.add(str(failure_status))
    widths = []
    expected = metrics["family_size"]
    if coverage_applicable and len(certificates) != expected:
        failures.add("INCOMPLETE_FAMILY")
    for certificate in certificates.values():
        status = certificate.get("status")
        lo, hi = certificate.get("lo"), certificate.get("hi")
        if coverage_applicable and status != "CERTIFIED_UNDER_DECLARED_ASSUMPTIONS":
            failures.add(status or "MISSING_COORDINATE_STATUS")
        if certificate.get("empty_intersection", False) or (
                lo is not None and hi is not None and lo > hi):
            failures.add("EMPTY_INTERSECTION")
        if lo is not None and hi is not None and np.isfinite(lo) and np.isfinite(hi):
            if lo <= hi:
                widths.append(float(hi - lo))
        elif coverage_applicable and status == "CERTIFIED_UNDER_DECLARED_ASSUMPTIONS":
            failures.add("NUMERICAL_FAILURE")
    row = dict(run_id=run_id, cell=cell, method=method, delta=delta,
               coverage_applicable=coverage_applicable,
               family_covered=bool(metrics["family_covered"]) and not failures,
               failure_status="|".join(sorted(failures)) if failures else None,
               family_size=expected, **events)
    row["mean_coordinate_width"] = float(np.mean(widths)) if len(widths) == expected and not failures else None
    for key in ("return_and_risk_safe", "return_and_utility_noninferior", "return_and_service_feasible",
                "return_and_infeasible", "any_false_utility_claim", "true_utility", "utility_gain",
                "expected_service", "expected_capacity", "maximum_true_risk_violation",
                "oracle_best_feasible_candidate_value", "robust_slack_comparator_value",
                "discovery_best_planted_iou", "unsafe_definition", "useful_definition"):
        row[key] = metrics.get(key)
    row["status"] = DRAFT
    return row

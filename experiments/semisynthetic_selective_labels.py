"""Offline CA-2018 ACSIncome-style fixed-population selective-label preparation.

No downloader or random driver is included. A missing official archive remains
DATA_BLOCKED; it never triggers a different dataset or fabricated E6 trial.
The only randomness in the eventual experiment is a declared logging mask over
a fixed finite population. Selection utility is A*Y and risk is A*(1-Y); neither
quantity is the causal effect of selection on income. Household protection is
a split-design rule, not a claim that households identify all real dependence.

For cycle logging, independent uniform 32-bit words Z_i and independent private
fair coins C_i give U_i=Z_i when C_i=0 and U_i=Z_(i+1) otherwise. Each U_i is
exactly uniform. For N>=3, neighbors share a chosen Z with probability 1/4,
so P(A_i=A_(i+1)=1)=min(e_i,e_(i+1))/4+3*e_i*e_(i+1)/4. Source-disjoint
row collections have independent complete score vectors conditional on the
fixed population and independent training/discovery masks. The source argument
establishes graph sufficiency; covariance alone does not. There is no causal
spillover claim. This is a design amendment before any E6 data or trial, not a
response to an empirical result.
"""

import argparse
import csv
from dataclasses import dataclass, replace
import hashlib
import io
import json
import math
from pathlib import Path
import re
import shlex
from types import MappingProxyType
from zipfile import ZipFile

import numpy as np

from comet.audit_pipeline import check_source_separation
from comet.checkpoint_store import canonical_bytes, digest, install_once
from comet.source_graph import SourceGraph
from experiments.core_graph_dgp import WORD_GRID, dyadic_probabilities


OFFICIAL_URL = "https://www2.census.gov/programs-surveys/acs/data/pums/2018/1-Year/csv_pca.zip"
FEATURE_NAMES = ("AGEP", "COW", "SCHL", "MAR", "OCCP", "POBP", "RELP", "WKHP", "SEX", "RAC1P")
DESIGN_FEATURE_NAMES = ("AGEP", "SCHL", "WKHP", "SEX")
DEFAULT_SPLIT_SIZES = {"training": 4096, "discovery": 8192, "certification": 16384}
REPOSITORY = Path(__file__).resolve().parents[1]
MAX_ARCHIVE_BYTES = 512 * 2**20
FILTER_TEXT = "AGEP>16 AND PINCP>100 AND WKHP>0 AND PWGTP>=1"
LOGGER_AMENDMENT = dict(
    status="DESIGN_ONLY_BEFORE_E6_DATA_OR_TRIALS",
    previous_draft="32-bit modular-sum cycle logger",
    main_cycle_logger="independent_source_selector_32bit_v1",
    reason="modular-sum neighbors can be pairwise independent; source selection supplies explicit nonzero local dependence without copied clusters",
    E6_data_used=False, E6_trials_used=0,
    uniform_sources="independent uniform32 Z_i",
    selectors="independent private uniform32 selector_words; C_i is their LSB, not a bit of Z_i",
    marginal_exposure="exact declared 32-bit-dyadic e_i",
    neighbor_joint_law="min(e_i,e_j)/4+3*e_i*e_j/4 for N>=3",
    neighbor_covariance="(min(e_i,e_j)-e_i*e_j)/4; correlation .25 at equal e=.5",
    sufficiency="row incidence {Z_i,Z_next,C_i}; source-disjoint row collections are independent",
)
README_TEXT = """# E6 offline dataset preparation

The selected dataset is California 2018 ACS one-year person PUMS only. The
ACSIncome filters are AGEP>16, PINCP>100, WKHP>0 and PWGTP>=1, with label
PINCP>50000 and ten declared covariates. Missing feature values are replaced
by -1 after eligibility, matching the declared ACSIncome-style preprocessing.
PWGTP is an eligibility input; this is an unweighted fixed-population target.

The archive bytes are hashed against a supplied source receipt. This local
check does not independently authenticate a download or infer its survey year
from a CSV without a YEAR column. State 06 is checked on every row; year/source
are bound to the supplied official-archive metadata and optional YEAR column.

Prepared covariate files and split registries contain no PINCP or benchmark
labels. The logger/evaluator vault retains fixed labels and reveals a label
only when the simulated action is 1; both unserved response channels are known
zero. The eventual estimand is finite-population selection utility/risk, not
the effect of selection on income or a population-level social intervention.

Households remain intact between training/discovery/certification. Exact-size
availability failure is reported before any logging randomness, with no row
duplication. The source-overlap graph comes from the simulated logging words,
not a claim that real household IDs describe all stochastic dependence.

The main cycle logger now uses independent uniform32 Z_i plus independent
private fair selectors C_i: U_i=Z_i if C_i=0, else Z_next. A separate selector
word argument supplies C_i by its least significant bit; no bit of Z_i is used
as that coin. Every U_i remains exactly uniform. Neighbors choose the same Z
with probability 1/4, giving covariance (min(e_i,e_j)-e_i*e_j)/4 (correlation
.25 at equal e=.5). The row-source graph includes both Z sources and the
private selector. Its sufficiency follows from source independence, not from
this covariance calculation.

This replaces the unrun modular-sum draft for model quality: its neighboring
masks could be pairwise independent and provide a weak dependence contrast.
The amendment uses no E6 data or observed results; zero E6 trials have run.

No E6 trial is run by preparation. A separate committed/frozen E6 protocol,
independent source driver, complete selection/evaluation runner and 1,000
declared trials are still required. Download failure does not block synthetic
experiments, proofs or manuscript work. No alternate dataset is substituted.
"""


class DatasetBlockedError(ValueError):
    pass


class AvailabilityBlockedError(ValueError):
    pass


def _readonly(values, dtype=float):
    array = np.asarray(values, dtype=dtype)
    return np.frombuffer(array.tobytes(), dtype=array.dtype).reshape(array.shape)


def _file_sha256(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(2**20), b""):
            value.update(block)
    return value.hexdigest()


@dataclass(frozen=True)
class ArchiveSpec:
    expected_sha256: str
    state: str = "CA"
    year: int = 2018
    survey: str = "1-Year"
    source_url: str = OFFICIAL_URL
    fixture: bool = False

    def __post_init__(self):
        if (self.state, self.year, self.survey, self.source_url) != ("CA", 2018, "1-Year", OFFICIAL_URL):
            raise ValueError("E6 is fixed to the single official CA-2018 one-year person archive")
        if not isinstance(self.expected_sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", self.expected_sha256):
            raise ValueError("a supplied SHA-256 archive receipt is required before CSV loading")
        object.__setattr__(self, "expected_sha256", self.expected_sha256.lower())


@dataclass(frozen=True)
class FixedCovariateView:
    """Label-free view; membership belongs to the fixed benchmark population."""

    person_keys: tuple
    household_ids: tuple
    features: np.ndarray
    x: np.ndarray
    metadata: object
    population_digest: str

    @property
    def n(self):
        return len(self.person_keys)


def _numeric(row, name):
    value = row[name].strip()
    if not value:
        return float("nan")
    try:
        number = float(value)
    except ValueError as exc:
        raise DatasetBlockedError("non-numeric ACS column: " + name) from exc
    if not math.isfinite(number):
        raise DatasetBlockedError("nonfinite ACS column: " + name)
    return number


def _design_x(features):
    columns = [FEATURE_NAMES.index(name) for name in DESIGN_FEATURE_NAMES]
    raw = features[:, columns]
    lower, upper = raw.min(axis=0), raw.max(axis=0)
    span = upper - lower
    scaled = np.divide(raw - lower, span, out=np.full_like(raw, 0.5), where=span > 0)
    return _readonly(2 * scaled - 1), lower.tolist(), upper.tolist()


class PopulationVault:
    """Logger/evaluator dataflow boundary, not a Python security sandbox.

    Only ``certifier_view`` is given to fitting/certification code. The private
    fixed label array is used by observe_from_words and the guarded oracle.
    """
    def __init__(self, view, labels):
        self.certifier_view = view
        self._labels = _readonly(labels, np.uint8)

    def _rows(self, split):
        if split.population_digest != self.certifier_view.population_digest:
            raise ValueError("split belongs to another fixed population")
        rows = np.asarray(split.row_indices)
        if rows.dtype.kind not in "iu" or np.any(rows < 0) or np.any(rows >= self.certifier_view.n):
            raise ValueError("split row indices are outside the fixed population")
        if len(np.unique(rows)) != len(rows):
            raise ValueError("a split cannot duplicate fixed-population people")
        return rows

    def observe_from_words(self, split, primitive_words, *, selector_words=None, seed_namespace=None):
        """Reveal labels using explicit uniform sources and separate private coins.

        Cycle selectors must be generated independently of all Z words and of
        other splits. Requiring a distinct argument catches omitted/aliased
        source arrays; it cannot infer statistical independence from numbers.
        Independent logging uses only Z and needs no selector words.
        """
        rows = self._rows(split)
        words = np.asarray(primitive_words)
        if words.shape != (split.n,) or words.dtype.kind not in "iu" or np.any(words < 0) or np.any(words >= WORD_GRID):
            raise ValueError("one unsigned-32-bit-range independent primitive per split row is required")
        if split.graph_kind == "cycle":
            if selector_words is None:
                raise ValueError("cycle source-selector logging requires independently generated selector_words")
            selectors = np.asarray(selector_words)
            if selectors.shape != (split.n,) or selectors.dtype.kind not in "iu" or np.any(selectors < 0) or np.any(selectors >= WORD_GRID):
                raise ValueError("supply one separate unsigned-32-bit-range selector word per row")
            if selector_words is primitive_words or np.shares_memory(selectors, words):
                raise ValueError("private selector words must not alias the Z source array")
            private_coins = selectors.astype(np.uint64) & np.uint64(1)
            uniform = np.where(private_coins == 0, words, np.roll(words, -1)).astype(np.uint64)
        else:
            uniform = words.astype(np.uint64)
        actions = (uniform < split.logging_cutoffs).astype(np.uint8)
        labels = self._labels[rows]
        outcomes = MappingProxyType({
            "utility": _readonly(actions * labels),
            "risk": _readonly(actions * (1 - labels)),
        })
        observed = np.where(actions == 1, labels.astype(float), np.nan)
        value = hashlib.sha256(actions.tobytes())
        for channel in ("risk", "utility"):
            value.update(outcomes[channel].astype("<f8").tobytes())
        return SelectiveLog(_readonly(actions, np.uint8), outcomes, _readonly(observed),
            value.hexdigest(), split.namespace, seed_namespace or split.namespace + "/explicit-words")

    def oracle_targets(self, family, certification_split, *, methods_finished=False):
        if methods_finished is not True:
            raise ValueError("join evaluator labels only after all methods and decisions finish")
        labels = self._labels[self._rows(certification_split)].astype(float)
        locations = {
            "utility": np.column_stack((np.zeros(len(labels)), labels)),
            "risk": np.column_stack((np.zeros(len(labels)), 1 - labels)),
        }
        return {query.query_id: query.target(locations[query.channel]) for query in family.queries}

    def oracle_policy_values(self, probabilities, certification_split, *, methods_finished=False):
        if methods_finished is not True:
            raise ValueError("policy oracle requires the completed-methods boundary")
        labels = self._labels[self._rows(certification_split)].astype(float)
        result = {}
        for policy_id, values in probabilities.items():
            q = np.asarray(values, dtype=float)
            if q.shape != labels.shape or not np.isfinite(q).all() or np.any(q < 0) or np.any(q > 1):
                raise ValueError("one legal policy probability per certification row is required")
            result[policy_id] = dict(utility=float(np.mean(q * labels)), risk=float(np.mean(q * (1 - labels))),
                                     service=float(q.mean()), capacity=float(q.mean()))
        return result


def load_acs_archive(path, spec, *, max_archive_bytes=MAX_ARCHIVE_BYTES):
    """Hash compressed bytes, then stream only the declared person CSV member."""
    path = Path(path)
    if not path.is_file():
        raise DatasetBlockedError("DATA_BLOCKED: the selected official archive is absent")
    if path.stat().st_size > max_archive_bytes:
        raise DatasetBlockedError("DATA_BLOCKED: selected compressed archive exceeds the 512 MiB limit")
    actual_hash = _file_sha256(path)
    if actual_hash != spec.expected_sha256:
        raise DatasetBlockedError("archive SHA-256 differs from the supplied CA-2018 source receipt")
    persons, labels, feature_rows, seen = [], [], [], set()
    raw_rows = excluded = missing_features = 0
    required = set(FEATURE_NAMES) | {"SERIALNO", "SPORDER", "ST", "PINCP", "PWGTP"}
    with ZipFile(path) as archive:
        members = [name for name in archive.namelist() if Path(name).name == "psam_p06.csv"]
        if len(members) != 1:
            raise DatasetBlockedError("archive must contain exactly one CA person member psam_p06.csv")
        member = members[0]
        with archive.open(member) as binary, io.TextIOWrapper(binary, encoding="utf-8-sig", newline="") as text:
            reader = csv.DictReader(text)
            if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames) or not required <= set(reader.fieldnames):
                raise DatasetBlockedError("missing or duplicate required ACS person CSV columns")
            for row in reader:
                raw_rows += 1
                if None in row or any(row.get(name) is None for name in required):
                    raise DatasetBlockedError("malformed ACS person CSV row")
                serial = row["SERIALNO"].strip()
                order = _numeric(row, "SPORDER")
                if not serial or not math.isfinite(order) or not order.is_integer() or order < 1:
                    raise DatasetBlockedError("invalid person key SERIALNO+SPORDER")
                key = serial, int(order)
                if key in seen:
                    raise DatasetBlockedError("duplicate person key SERIALNO+SPORDER")
                seen.add(key)
                if _numeric(row, "ST") != 6:
                    raise DatasetBlockedError("row state is not California (ST=06)")
                if "YEAR" in row and _numeric(row, "YEAR") != 2018:
                    raise DatasetBlockedError("row YEAR does not match the bound 2018 archive metadata")
                age, income, hours, weight = (_numeric(row, name) for name in ("AGEP", "PINCP", "WKHP", "PWGTP"))
                if not (age > 16 and income > 100 and hours > 0 and weight >= 1):
                    excluded += 1
                    continue
                features = [_numeric(row, name) for name in FEATURE_NAMES]
                missing_features += sum(math.isnan(value) for value in features)
                feature_rows.append([-1.0 if math.isnan(value) else value for value in features])
                persons.append(key)
                labels.append(int(income > 50000))
    if not persons:
        raise AvailabilityBlockedError("AVAILABILITY_BLOCKED: no rows pass the fixed ACSIncome filters")
    order = sorted(range(len(persons)), key=persons.__getitem__)
    features = _readonly(np.asarray(feature_rows)[order])
    labels = _readonly(np.asarray(labels)[order], np.uint8)
    keys = tuple(persons[index] for index in order)
    x, minimum, maximum = _design_x(features)
    metadata = dict(dataset="ACSIncome-style CA-2018 fixed-population selection benchmark",
        source_url=spec.source_url, state=spec.state, state_fips="06", year=spec.year, survey=spec.survey,
        archive_path=str(path.resolve()), archive_member=member, archive_sha256=actual_hash,
        archive_bytes=path.stat().st_size, archive_hash_check="matches supplied source receipt; not independent remote authentication",
        year_check="source receipt and optional YEAR field; year is not inferred from unlabeled CSV data",
        feature_names=list(FEATURE_NAMES), design_feature_names=list(DESIGN_FEATURE_NAMES),
        design_minima=minimum, design_maxima=maximum, design_scaling="all eligible fixed X only; no labels used",
        eligibility=FILTER_TEXT, label_definition="PINCP>50000",
        missing_feature_rule="empty numeric covariates become -1 after eligibility",
        missing_feature_entries=missing_features, raw_person_rows=raw_rows, excluded_rows=excluded,
        eligible_rows=len(keys), duplicate_persons=0, weight_use="eligibility only; unweighted finite-population moments",
        data_status="DETERMINISTIC_FIXTURE_NOT_REAL_DATA" if spec.fixture else "ARCHIVE_PREPARED_NOT_E6_EXPERIMENT",
        task_source_url="https://raw.githubusercontent.com/socialfoundations/folktables/main/folktables/acs.py",
        terms_url="https://www.census.gov/data/developers/about/terms-of-service.html",
        open_data_url="https://www.census.gov/topics/research/research-transparency-public-access/open-data.html",
        estimand="finite-population policy-weighted selection outcomes; not intervention effect on income")
    metadata["logging_design_amendment"] = dict(LOGGER_AMENDMENT)
    identity = {key: metadata[key] for key in ("state", "year", "survey", "archive_sha256",
        "archive_member", "eligibility", "feature_names", "label_definition")}
    value = hashlib.sha256(canonical_bytes(dict(identity=identity, person_keys=keys)))
    value.update(features.astype("<f8").tobytes())
    value.update(labels.tobytes())
    view = FixedCovariateView(keys, tuple(key[0] for key in keys), features, x,
                             MappingProxyType(metadata), value.hexdigest())
    return PopulationVault(view, labels)


def household_split_indices(view, split_sizes=None):
    """D-only exact-size allocation, reserving single-person groups for remainders."""
    sizes = DEFAULT_SPLIT_SIZES if split_sizes is None else split_sizes
    if set(sizes) != set(DEFAULT_SPLIT_SIZES) or any(type(value) is not int or value < 1 for value in sizes.values()):
        raise ValueError("declare three positive integer household-protected split sizes")
    if view.n < sum(sizes.values()):
        raise AvailabilityBlockedError("AVAILABILITY_BLOCKED: fewer eligible people than the declared disjoint split sizes")
    groups = {}
    for row, household in enumerate(view.household_ids):
        groups.setdefault(household, []).append(row)
    ordered = sorted(groups, key=lambda key: (hashlib.sha256(("COMET-E6-household-v1\0" + key).encode()).digest(), key))
    singletons = [key for key in ordered if len(groups[key]) == 1]
    remaining_groups = [key for key in ordered if len(groups[key]) != 1]
    result, singleton_position = {}, 0
    for name in DEFAULT_SPLIT_SIZES:
        need, selected, leftover = sizes[name], [], []
        for key in remaining_groups:
            if len(groups[key]) <= need:
                selected.extend(groups[key])
                need -= len(groups[key])
            else:
                leftover.append(key)
        remaining_groups = leftover
        if need > len(singletons) - singleton_position:
            raise AvailabilityBlockedError("AVAILABILITY_BLOCKED: exact household packing failed; amend sizes before outcomes, never duplicate people")
        for key in singletons[singleton_position:singleton_position + need]:
            selected.extend(groups[key])
        singleton_position += need
        result[name] = _readonly(sorted(selected), np.int64)
    return MappingProxyType(result)


@dataclass(frozen=True)
class SelectiveSplitView:
    name: str
    namespace: str
    graph_kind: str
    overlap: str
    row_indices: np.ndarray
    x: np.ndarray
    exposure: np.ndarray
    logging_cutoffs: np.ndarray
    row_sources: tuple
    graph: SourceGraph
    population_digest: str

    @property
    def n(self):
        return len(self.row_indices)

    @property
    def source_ids(self):
        return frozenset(source for row in self.row_sources for source in row)


@dataclass(frozen=True)
class SemisyntheticDesign:
    splits: object
    namespace: str
    source_separation: object
    population_digest: str
    risk_threshold: float = 0.32
    utility_margin: float = 0.01
    service_floor: float = 0.2
    capacity_ceiling: float = 0.6
    status: str = "OFFLINE_PREPARED_NOT_PROTOCOL_FROZEN"


def build_semisynthetic_design(view, graph_kind="cycle", overlap="moderate",
                              namespace="comet-post-cstat-v1/E6-offline", split_sizes=None):
    """Construct label-free design and sufficient logging graph; draw nothing."""
    if graph_kind not in ("independent", "cycle") or overlap not in ("moderate", "weak"):
        raise ValueError("declare one of the four E6 dependence/overlap cells")
    if not isinstance(namespace, str) or not namespace:
        raise ValueError("a nonempty E6 source namespace is required")
    indices = household_split_indices(view, split_sizes)
    splits = {}
    for name, rows in indices.items():
        n, source_namespace = len(rows), namespace + "/" + name
        if graph_kind == "cycle" and n < 3:
            raise AvailabilityBlockedError("source-selector cycle logging requires at least three rows in every split")
        x = _readonly(view.x[rows])
        tendency = 1 / (1 + np.exp(-(x[:, 0] - x[:, 1])))
        probabilities = 0.2 + 0.6 * tendency if overlap == "moderate" else 0.005 + 0.045 * tendency
        cutoffs, probabilities = dyadic_probabilities(probabilities)
        exposure = _readonly(np.column_stack((1 - probabilities, probabilities)))
        sources = tuple(frozenset({(source_namespace, "logging-uniform", row)} if graph_kind == "independent" else
            {(source_namespace, "logging-uniform", row), (source_namespace, "logging-uniform", (row + 1) % n),
             (source_namespace, "logging-selector", row)})
            for row in range(n))
        splits[name] = SelectiveSplitView(name, source_namespace, graph_kind, overlap,
            rows, x, exposure, cutoffs, sources, SourceGraph.from_sources(sources), view.population_digest)
    separation = check_source_separation({name: split.source_ids for name, split in splits.items()})
    return SemisyntheticDesign(MappingProxyType(splits), namespace,
        MappingProxyType(separation), view.population_digest)


@dataclass(frozen=True)
class SelectiveLog:
    actions: np.ndarray
    outcomes: object
    observed_labels: np.ndarray
    data_digest: str
    source_namespace: str
    seed_namespace: str


def fit_and_freeze_e6(design, training_log, discovery_log, **choices):
    """Reuse E5 fitting/discovery/selector inputs, with no synthetic oracle.

    This freezes the discovered coordinate family inside a trial, not a study
    protocol and not a completed E6 replication. Only source-separated observed
    training/discovery labels enter the reused routines.
    """
    from experiments.pipeline_dgp import fit_and_freeze_pipeline
    frozen = fit_and_freeze_pipeline(design, training_log, discovery_log, **choices)
    return replace(frozen, status="OFFLINE_E6_ADAPTER_NOT_PROTOCOL_FROZEN")


def dataset_status(archive_path=None, expected_sha256=None):
    path = Path(archive_path) if archive_path is not None else REPOSITORY / "data/acs_ca2018/csv_pca.zip"
    present = path.is_file()
    return dict(status="ARCHIVE_PRESENT_UNVERIFIED" if present else "DATA_BLOCKED", suite="E6",
        source_url=OFFICIAL_URL, state="CA", year=2018, survey="1-Year",
        archive_path=str(path.resolve()), archive_present=present,
        archive_bytes=path.stat().st_size if present else 0,
        supplied_sha256=expected_sha256, archive_content_verified=False,
        actual_eligible_rows=None, prepared_splits=None, E6_completed_trials=0,
        remaining_primary_units=1000, remaining_id_status="unfrozen proposed E6 identifiers; no seeds assigned here",
        new_scientific_units=0, legacy_new_outcome_draws=0, alternate_dataset_selected=False,
        default_split_sizes=dict(DEFAULT_SPLIT_SIZES),
        scope="offline preparation only; no E6 logging driver or confirmatory runner is executed",
        proposed_cycle_logger=dict(LOGGER_AMENDMENT),
        known_download_history="same official URL previously failed DNS then HTTP403; no background transfer claimed",
        resume_prepare_command=shlex.join([".venv/bin/python", "-m", "experiments.semisynthetic_selective_labels",
            "--prepare", "--archive", str(path), "--sha256", expected_sha256 or "SUPPLY_VERIFIED_SOURCE_RECEIPT_SHA256",
            "--output", "results/post_cstat/E6_data_v1"]))


def prepare_archive(archive_path, expected_sha256, output_directory, *, split_sizes=None, fixture=False):
    """Prepare metadata, X and split registry only; do not write labels or log masks."""
    output = Path(output_directory)
    if any((output / name).exists() for name in ("manifest.json", "covariates.npz", "household_splits.json", "README.md")):
        raise FileExistsError("offline preparation outputs are immutable; select a fresh directory")
    if not Path(archive_path).is_file():
        receipt = dataset_status(archive_path, expected_sha256)
        receipt["module_sha256"] = _file_sha256(__file__)
        install_once(output / "README.md", README_TEXT.encode())
        install_once(output / "manifest.json", canonical_bytes(receipt) + b"\n")
        return receipt
    if expected_sha256 is None:
        raise DatasetBlockedError("archive is present but a supplied official-source SHA-256 receipt is required")
    vault = load_acs_archive(archive_path, ArchiveSpec(expected_sha256, fixture=fixture))
    view = vault.certifier_view
    try:
        rows = household_split_indices(view, split_sizes)
    except AvailabilityBlockedError as exc:
        receipt = dict(dataset_status(archive_path, expected_sha256), status="AVAILABILITY_BLOCKED",
            archive_content_verified=True, actual_eligible_rows=view.n,
            reason=str(exc), metadata=dict(view.metadata), module_sha256=_file_sha256(__file__))
        install_once(output / "README.md", README_TEXT.encode())
        install_once(output / "manifest.json", canonical_bytes(receipt) + b"\n")
        return receipt
    registry = dict(population_digest=view.population_digest,
        split_rows={name: value.tolist() for name, value in rows.items()},
        split_sizes={name: len(value) for name, value in rows.items()},
        split_rule="whole households; deterministic source-independent order; singleton remainder reserve",
        households_cross_split=False, people_duplicated=False, labels_exported=False)
    buffer = io.BytesIO()
    np.savez_compressed(buffer, features=view.features, x=view.x,
        SERIALNO=np.array([key[0] for key in view.person_keys]),
        SPORDER=np.array([key[1] for key in view.person_keys], dtype=np.int64))
    covariates = buffer.getvalue()
    registry_bytes = canonical_bytes(registry) + b"\n"
    receipt = dict(status="DETERMINISTIC_OFFLINE_FIXTURE_NOT_E6_DATA" if fixture else "OFFLINE_PREPARED_NOT_E6_EXPERIMENT",
        suite="E6", metadata=dict(view.metadata),
        population_digest=view.population_digest, split_sizes=registry["split_sizes"],
        E6_completed_trials=0, new_scientific_units=0, legacy_new_outcome_draws=0,
        fixed_population_selection_not_causal_intervention=True, labels_exported=False,
        proposed_cycle_logger=dict(LOGGER_AMENDMENT),
        module_sha256=_file_sha256(__file__), outputs={"covariates.npz":hashlib.sha256(covariates).hexdigest(),
        "household_splits.json":hashlib.sha256(registry_bytes).hexdigest(),
        "README.md":hashlib.sha256(README_TEXT.encode()).hexdigest()},
        remaining="freeze actual E6 protocol and implement complete trial driver/evaluation; 1000 trials unrun")
    install_once(output / "covariates.npz", covariates)
    install_once(output / "household_splits.json", registry_bytes)
    install_once(output / "README.md", README_TEXT.encode())
    install_once(output / "manifest.json", canonical_bytes(receipt) + b"\n")
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--status", action="store_true")
    mode.add_argument("--prepare", action="store_true")
    parser.add_argument("--archive", type=Path, default=REPOSITORY / "data/acs_ca2018/csv_pca.zip")
    parser.add_argument("--sha256")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.status:
        receipt = dataset_status(args.archive, args.sha256)
    else:
        if args.output is None:
            parser.error("--prepare requires a fresh --output directory")
        receipt = prepare_archive(args.archive, args.sha256, args.output)
    print(json.dumps(receipt, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()

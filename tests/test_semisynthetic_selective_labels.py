"""Artificial CSV ZIPs and explicit words only; no real data, RNG or MC units."""

import csv
from dataclasses import replace
from fractions import Fraction
import hashlib
import io
import itertools
import json
from zipfile import ZipFile

import numpy as np
import pytest

from comet.audit_pipeline import freeze_discovered_family
from comet.queries import SignedQuery
from experiments.semisynthetic_selective_labels import (
    ArchiveSpec, AvailabilityBlockedError, DatasetBlockedError, FEATURE_NAMES,
    LOGGER_AMENDMENT, WORD_GRID, build_semisynthetic_design, dataset_status, fit_and_freeze_e6,
    household_split_indices, load_acs_archive, prepare_archive,
)


HEADERS = ("SERIALNO", "SPORDER", "ST", "YEAR", "AGEP", "PINCP", "WKHP", "PWGTP",
           "COW", "SCHL", "MAR", "OCCP", "POBP", "RELP", "SEX", "RAC1P")


def row(index, *, household=None, order=1, income=None, **changes):
    value = dict(SERIALNO=household or f"fixture-{index:04d}", SPORDER=str(order), ST="06", YEAR="2018",
        AGEP=str(17 + index), PINCP=str(60000 if index % 2 else 30000) if income is None else str(income),
        WKHP=str(20 + index % 5), PWGTP="1", COW="1", SCHL=str(10 + index % 6), MAR="1",
        OCCP="100", POBP="6", RELP="0", SEX=str(1 + index % 2), RAC1P="1")
    value.update({key: str(data) for key, data in changes.items()})
    return value


def fixture_zip(tmp_path, rows, *, member="psam_p06.csv", name="fixture.zip"):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=HEADERS)
    writer.writeheader()
    writer.writerows(rows)
    path = tmp_path / name
    with ZipFile(path, "w") as archive:
        archive.writestr(member, stream.getvalue())
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    return path, ArchiveSpec(sha, fixture=True)


def fixture_population(tmp_path, n=16, *, paired_households=False):
    rows = [row(index, household=f"household-{index // 2:03d}" if paired_households else None,
                order=index % 2 + 1 if paired_households else 1) for index in range(n)]
    path, spec = fixture_zip(tmp_path, rows)
    return load_acs_archive(path, spec), path, spec


@pytest.fixture(autouse=True)
def forbid_rng(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("offline semisynthetic fixture called a random driver")
    monkeypatch.setattr(np.random, "default_rng", forbidden)


def test_exact_income_filters_features_and_threshold_label(tmp_path):
    rows = [row(0, income=50000), row(1, income=50001),
            row(2, AGEP=16), row(3, income=100), row(4, WKHP=0), row(5, PWGTP=0.5)]
    path, spec = fixture_zip(tmp_path, rows)
    vault = load_acs_archive(path, spec)
    view = vault.certifier_view
    assert view.n == 2
    assert view.features.shape == (2, 10) and view.x.shape == (2, 4)
    assert view.metadata["feature_names"] == list(FEATURE_NAMES)
    assert view.metadata["excluded_rows"] == 4
    assert view.metadata["archive_sha256"] == spec.expected_sha256
    assert view.metadata["data_status"] == "DETERMINISTIC_FIXTURE_NOT_REAL_DATA"
    assert "PINCP" not in FEATURE_NAMES
    assert not hasattr(view, "labels") and not hasattr(view, "outcomes")
    assert np.all(np.abs(view.x) <= 1)


def test_missing_covariates_are_imputed_after_eligibility_not_dropped(tmp_path):
    values = row(0)
    values["COW"], values["SCHL"] = "", ""
    path, spec = fixture_zip(tmp_path, [values, row(1)])
    view = load_acs_archive(path, spec).certifier_view
    assert view.n == 2
    assert view.features[0, FEATURE_NAMES.index("COW")] == -1
    assert view.features[0, FEATURE_NAMES.index("SCHL")] == -1
    assert view.metadata["missing_feature_entries"] == 2


def test_archive_receipt_state_year_member_and_duplicates_are_strict(tmp_path):
    path, spec = fixture_zip(tmp_path, [row(0)])
    with pytest.raises(DatasetBlockedError, match="SHA-256"):
        load_acs_archive(path, ArchiveSpec("0" * 64, fixture=True))
    for kwargs in ({"year": 2019}, {"state": "OR"}, {"source_url": "https://example.invalid/not-census.zip"}):
        with pytest.raises(ValueError, match="CA-2018"):
            ArchiveSpec(spec.expected_sha256, **kwargs)
    for changes, match in [({"ST": 41}, "state"), ({"YEAR": 2019}, "YEAR")]:
        path, spec = fixture_zip(tmp_path, [row(0, **changes)], name="wrong.zip")
        with pytest.raises(DatasetBlockedError, match=match):
            load_acs_archive(path, spec)
    path, spec = fixture_zip(tmp_path, [row(0)], member="psam_p41.csv", name="member.zip")
    with pytest.raises(DatasetBlockedError, match="psam_p06.csv"):
        load_acs_archive(path, spec)
    duplicate = row(0, income=100)  # even a filtered duplicate is refused
    path, spec = fixture_zip(tmp_path, [row(0), duplicate], name="duplicate.zip")
    with pytest.raises(DatasetBlockedError, match="duplicate person"):
        load_acs_archive(path, spec)


def test_exact_household_splits_have_no_people_or_groups_in_common(tmp_path):
    vault, _, _ = fixture_population(tmp_path, 16, paired_households=True)
    view = vault.certifier_view
    sizes = dict(training=2, discovery=2, certification=4)
    rows = household_split_indices(view, sizes)
    assert {name: len(values) for name, values in rows.items()} == sizes
    persons, households = [], []
    for indices in rows.values():
        persons.append(set(indices.tolist()))
        households.append({view.household_ids[index] for index in indices})
    for first in range(3):
        for second in range(first + 1, 3):
            assert persons[first].isdisjoint(persons[second])
            assert households[first].isdisjoint(households[second])
    with pytest.raises(AvailabilityBlockedError, match="fewer eligible"):
        household_split_indices(view)
    with pytest.raises(AvailabilityBlockedError, match="packing"):
        household_split_indices(view, dict(training=1, discovery=1, certification=4))


def test_source_split_and_dependency_graph_are_logging_mask_constructions(tmp_path):
    vault, _, _ = fixture_population(tmp_path, 16, paired_households=True)
    design = build_semisynthetic_design(vault.certifier_view, "cycle", "weak",
        split_sizes=dict(training=4, discovery=4, certification=4))
    split = design.splits["certification"]
    assert split.graph.edge_count == 4 and split.graph.color_count == 2
    assert np.all(split.exposure.sum(axis=1) == 1)
    assert np.all(split.exposure[:, 1] * WORD_GRID == split.logging_cutoffs)
    assert design.splits["training"].source_ids.isdisjoint(split.source_ids)
    assert design.splits["discovery"].source_ids.isdisjoint(split.source_ids)
    for index, sources in enumerate(split.row_sources):
        assert sources == frozenset({(split.namespace, "logging-uniform", index),
            (split.namespace, "logging-uniform", (index + 1) % split.n),
            (split.namespace, "logging-selector", index)})
    assert len(split.source_ids) == 2 * split.n
    assert split.row_sources[0].isdisjoint(split.row_sources[2])
    independent = build_semisynthetic_design(vault.certifier_view, "independent", "moderate",
        split_sizes=dict(training=2, discovery=2, certification=4))
    assert independent.splits["certification"].graph.edge_count == 0


def test_exact_source_selector_explicit_words_and_separate_private_coins(tmp_path):
    vault, _, _ = fixture_population(tmp_path, 16)
    design = build_semisynthetic_design(vault.certifier_view, "cycle", "moderate",
        split_sizes=dict(training=4, discovery=4, certification=4))
    split = replace(design.splits["certification"],
        logging_cutoffs=np.full(4, WORD_GRID // 2, dtype=np.uint64), exposure=np.full((4, 2), 0.5))
    words = np.array([0, WORD_GRID - 1, 1, WORD_GRID // 2], dtype=np.uint64)
    selectors = np.array([2, 8, 3, 5], dtype=np.uint32)  # LSB: 0,0,1,1
    with pytest.raises(ValueError, match="independently generated selector_words"):
        vault.observe_from_words(split, words)
    with pytest.raises(ValueError, match="must not alias"):
        vault.observe_from_words(split, words, selector_words=words)
    log = vault.observe_from_words(split, words, selector_words=selectors)
    assert log.actions.tolist() == [1, 0, 0, 1]
    assert np.isnan(log.observed_labels[log.actions == 0]).all()
    assert np.all(log.outcomes["risk"] + log.outcomes["utility"] == log.actions)
    assert np.all(log.outcomes["risk"][log.actions == 0] == 0)
    assert np.all(log.outcomes["utility"][log.actions == 0] == 0)
    assert np.isin(log.observed_labels[log.actions == 1], [0, 1]).all()


@pytest.mark.parametrize("left_cutoff,right_cutoff", [(1, 3), (2, 2), (3, 1)])
def test_complete_finite_grid_enumeration_proves_exact_marginals_and_neighbor_joint_law(tmp_path, left_cutoff, right_cutoff):
    vault, _, _ = fixture_population(tmp_path, 16)
    design = build_semisynthetic_design(vault.certifier_view, "cycle", "moderate",
        split_sizes=dict(training=4, discovery=4, certification=4))
    modulus, step = 4, WORD_GRID // 4
    probabilities = np.array([left_cutoff / modulus, right_cutoff / modulus, 0.5, 0.5])
    split = replace(design.splits["certification"],
        logging_cutoffs=(probabilities * WORD_GRID).astype(np.uint64),
        exposure=np.column_stack((1 - probabilities, probabilities)))
    first = second = both = total = 0
    # Three independent neighboring Z bins and two independent private coins.
    # Each bin has exactly 2**30 full 32-bit words. Thus this finite enumeration
    # is exact for these dyadic thresholds, rather than a Monte Carlo estimate.
    for z0, z1, z2, c0, c1 in itertools.product(range(modulus), range(modulus),
                                              range(modulus), range(2), range(2)):
        words = np.array([z0 * step, z1 * step, z2 * step, 0], dtype=np.uint64)
        selectors = np.array([c0, c1, 0, 0], dtype=np.uint32)
        log = vault.observe_from_words(split, words, selector_words=selectors)
        left, right = (int(value) for value in log.actions[:2])
        first += left
        second += right
        both += left * right
        total += 1
    e_left, e_right = Fraction(left_cutoff, modulus), Fraction(right_cutoff, modulus)
    joint = Fraction(1, 4) * min(e_left, e_right) + Fraction(3, 4) * e_left * e_right
    assert Fraction(first, total) == e_left
    assert Fraction(second, total) == e_right
    assert Fraction(both, total) == joint
    covariance = joint - e_left * e_right
    assert covariance == (min(e_left, e_right) - e_left * e_right) / 4
    assert covariance > 0
    if e_left == e_right == Fraction(1, 2):
        assert covariance / Fraction(1, 4) == Fraction(1, 4)


def test_cycle_amendment_is_explicitly_design_only_and_requires_three_rows(tmp_path):
    assert LOGGER_AMENDMENT["status"] == "DESIGN_ONLY_BEFORE_E6_DATA_OR_TRIALS"
    assert LOGGER_AMENDMENT["E6_trials_used"] == 0 and not LOGGER_AMENDMENT["E6_data_used"]
    vault, _, _ = fixture_population(tmp_path, 16)
    with pytest.raises(AvailabilityBlockedError, match="at least three"):
        build_semisynthetic_design(vault.certifier_view, "cycle", "moderate",
            split_sizes=dict(training=2, discovery=2, certification=4))


def test_oracle_is_guarded_and_uses_finite_population_selection_targets(tmp_path):
    vault, _, _ = fixture_population(tmp_path, 16)
    design = build_semisynthetic_design(vault.certifier_view, "independent", "moderate",
        split_sizes=dict(training=2, discovery=2, certification=4))
    split = design.splits["certification"]
    coefficients = np.tile([0.0, 1.0], (split.n, 1))
    family = freeze_discovered_family([
        SignedQuery("utility", coefficients, 0, channel="utility"),
        SignedQuery("risk", coefficients, 0, channel="risk"),
    ])
    with pytest.raises(ValueError, match="after all methods"):
        vault.oracle_targets(family, split)
    truth = vault.oracle_targets(family, split, methods_finished=True)
    assert truth["utility"] + truth["risk"] == 1
    values = vault.oracle_policy_values({"half": np.full(split.n, 0.5)}, split, methods_finished=True)
    assert values["half"]["utility"] + values["half"]["risk"] == 0.5
    assert values["half"]["service"] == values["half"]["capacity"] == 0.5
    bad = replace(split, row_indices=np.array([split.row_indices[0]] * split.n))
    with pytest.raises(ValueError, match="duplicate"):
        vault.observe_from_words(bad, np.zeros(split.n, dtype=np.uint32))


def test_E5_fit_and_discovery_adapter_receives_only_revealed_channels(tmp_path):
    vault, _, _ = fixture_population(tmp_path, 40)
    design = build_semisynthetic_design(vault.certifier_view, "independent", "moderate",
        split_sizes=dict(training=8, discovery=8, certification=16))
    observed = {name: vault.observe_from_words(split, np.zeros(split.n, dtype=np.uint32))
                for name, split in design.splits.items()}
    frozen = fit_and_freeze_e6(design, observed["training"], observed["discovery"],
        max_rules=2, max_depth=2, minimum_mass=0.05, tradeoff_grid=(0.0, 0.5))
    assert frozen.status == "OFFLINE_E6_ADAPTER_NOT_PROTOCOL_FROZEN"
    assert {query.channel for query in frozen.family.queries} == {"risk", "utility"}
    assert frozen.family.family_size == len(frozen.family.queries)
    assert frozen.fit.source_namespace == design.splits["training"].namespace
    frozen.certifier_inputs("utility")["contract"].require()


def test_preparation_exports_covariates_and_split_ids_without_labels(tmp_path):
    vault, path, spec = fixture_population(tmp_path, 16)
    output = tmp_path / "prepared"
    receipt = prepare_archive(path, spec.expected_sha256, output,
        split_sizes=dict(training=2, discovery=2, certification=4), fixture=True)
    assert receipt["status"] == "DETERMINISTIC_OFFLINE_FIXTURE_NOT_E6_DATA"
    assert receipt["E6_completed_trials"] == receipt["new_scientific_units"] == 0
    assert not receipt["labels_exported"]
    with np.load(output / "covariates.npz") as arrays:
        assert set(arrays.files) == {"features", "x", "SERIALNO", "SPORDER"}
        assert arrays["features"].shape == vault.certifier_view.features.shape
    registry = json.loads((output / "household_splits.json").read_text())
    assert not registry["households_cross_split"] and not registry["people_duplicated"]
    with pytest.raises(FileExistsError, match="immutable"):
        prepare_archive(path, spec.expected_sha256, output, fixture=True)


def test_absent_archive_stays_data_blocked_and_never_selects_substitute(tmp_path):
    archive = tmp_path / "missing-official-archive.zip"
    state = dataset_status(archive)
    assert state["status"] == "DATA_BLOCKED"
    assert not state["archive_content_verified"] and not state["alternate_dataset_selected"]
    assert state["new_scientific_units"] == state["legacy_new_outcome_draws"] == 0
    assert state["remaining_primary_units"] == 1000
    assert state["proposed_cycle_logger"]["main_cycle_logger"] == "independent_source_selector_32bit_v1"
    receipt = prepare_archive(archive, None, tmp_path / "blocked")
    assert receipt["status"] == "DATA_BLOCKED"
    assert not (tmp_path / "blocked" / "covariates.npz").exists()

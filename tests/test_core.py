from dataclasses import FrozenInstanceError, replace
from itertools import product
from math import ceil, log
from random import Random

import pytest

from comet.certification import certify, subgroup_ratio_bound
from comet.conflict_graph import clique_graph, greedy_coloring, is_proper_coloring
from comet.dr_scores import centered_bounded_envelope, dr_score, validate_distribution
from comet.exposure import marginalize_exposure, plackett_luce_slates
from comet.robust_mean import confidence_budget, mom_estimate, mom_radius, partition_blocks, required_groups
from comet.schema import CertificationError, SupportError, SyntheticConfig
from comet.synthetic import generate_evaluation


def expected_score(true_mu, true_e, fitted_mu, fitted_e, q):
    return sum(true_e[s] * probability * dr_score(y, s, q, fitted_e, fitted_mu)
               for s in range(2) for y, probability in ((0, 1-true_mu[s]), (1, true_mu[s])))


@pytest.mark.parametrize("true_e", [(0.8, 0.2), (0.1, 0.9)])
@pytest.mark.parametrize("q", [(0.7, 0.3), (0.0, 1.0)])
def test_dr_identity_exact_e_wrong_fixed_mu(true_e, q):
    mu = (0.2, 0.75)
    assert expected_score(mu, true_e, (0.9, 0.1), true_e, q) == pytest.approx(sum(qs*ms for qs, ms in zip(q, mu)))


def test_dr_identity_correct_fixed_mu_wrong_e_and_product_remainder():
    mu, e, q = (0.1, 0.8), (0.7, 0.3), (0.25, 0.75)
    ehat, mhat = (0.4, 0.6), (0.2, 0.3)
    target = sum(qs*ms for qs, ms in zip(q, mu))
    assert expected_score(mu, e, mu, ehat, q) == pytest.approx(target)
    remainder = sum(q[s]*(mhat[s]-mu[s])*(ehat[s]-e[s])/ehat[s] for s in range(2))
    assert expected_score(mu, e, mhat, ehat, q)-target == pytest.approx(remainder)


def test_evaluation_outcome_leak_breaks_dr_identity():
    # Y=S, logger=.5; setting every fitted response to observed Y makes psi=Y.
    estimate_expectation = sum(0.5*dr_score(s, s, (0.1, 0.9), (0.5, 0.5), (s, s))
                               for s in (0, 1))
    assert estimate_expectation == pytest.approx(0.5)
    assert estimate_expectation != pytest.approx(0.9)


def test_support_failure_is_never_clipped_and_common_zero_is_allowed():
    with pytest.raises(SupportError, match="NONIDENTIFIABLE_TARGET_SUPPORT"):
        dr_score(1, 0, (0, 1), (1, 0), (0.5, 0.5))
    assert dr_score(1, 0, (1, 0), (1, 0), (0.5, 0.5)) == pytest.approx(1)
    assert centered_bounded_envelope((1, 0), (1, 0), 2) == pytest.approx(16)
    with pytest.raises(SupportError, match="OBSERVED_ZERO"):
        dr_score(1, 1, (1, 0), (1, 0), (0.5, 0.5))


@pytest.mark.parametrize("bad", [(0.5, 0.6), (-0.1, 1.1), (float("nan"), 0.5), ()])
def test_probability_normalization_refuses_invalid_inputs(bad):
    with pytest.raises(CertificationError):
        validate_distribution(bad)


def test_exact_joint_slate_and_marginal_exposure():
    distribution = plackett_luce_slates((1, 2, 3), 2)
    assert sum(distribution.values()) == pytest.approx(1)
    assert distribution[(0, 1)] == pytest.approx((1/6)*(2/5))
    assert distribution[(1, 0)] == pytest.approx((2/6)*(1/4))
    assert distribution[(0, 1)] != pytest.approx((1/6)*(2/6))
    # Joint state: item0 shown and item1 shown; assignments are without replacement.
    exposure = marginalize_exposure(distribution, lambda slate: (int(0 in slate), int(1 in slate)))
    assert sum(exposure.values()) == pytest.approx(1)
    assert exposure[(1, 1)] == pytest.approx(1/15+1/12)
    assert exposure.get((0, 0), 0) == 0
    mixed = plackett_luce_slates((1, 2, 3), 2, uniform_mix=0.3)
    assert mixed[(0, 1)] == pytest.approx(0.7/15+0.3/6)
    uniform = plackett_luce_slates((1, 2, 3), 2, uniform_mix=1)
    assert set(round(v, 12) for v in uniform.values()) == {round(1/6, 12)}


def test_slate_sampler_frequencies_match_enumerated_joint_law():
    # A seeded diagnostic, not a confidence-coverage assertion.
    rng, n, count = Random(17), 12000, 0
    for _ in range(n):
        first = rng.choices(range(3), weights=(1, 2, 3))[0]
        remaining = [i for i in range(3) if i != first]
        second = rng.choices(remaining, weights=[(1, 2, 3)[i] for i in remaining])[0]
        count += (first, second) == (0, 1)
    assert abs(count/n-plackett_luce_slates((1, 2, 3), 2)[(0, 1)]) < 0.015


@pytest.mark.parametrize("n,chi", [(8, 1), (12, 2), (32, 4), (16, 16)])
def test_clique_graph_complete_sufficient_and_properly_colored(n, chi):
    graph = clique_graph(n, chi)
    colors = greedy_coloring(graph)
    assert len(graph) == n
    assert sum(map(len, graph))//2 == n*(chi-1)//2
    assert max(colors)+1 == chi
    assert is_proper_coloring(graph, colors)
    for i, j in product(range(n), repeat=2):
        assert (j in graph[i]) == (i != j and i//chi == j//chi)


def test_invalid_graph_and_improper_coloring_rejected():
    with pytest.raises(CertificationError):
        clique_graph(7, 2)
    with pytest.raises(CertificationError):
        greedy_coloring(((1,), ()))
    assert not is_proper_coloring(clique_graph(4, 2), (0, 0, 1, 1))


def test_exact_k_and_no_dropped_remainder_blocks():
    K = required_groups(4, 0.05)
    assert K == 41 == ceil(8*log(160))
    assert required_groups(4, 0.1) == 36
    groups = partition_blocks(128, K)
    assert [i for group in groups for i in group] == list(range(128))
    assert sorted(map(len, groups)) == [3]*36+[4]*5
    assert mom_estimate([7.0]*128, groups) == 7.0
    with pytest.raises(CertificationError, match="B_LT_2K"):
        partition_blocks(81, 41)
    with pytest.raises(CertificationError, match="EVERY_BLOCK"):
        mom_estimate([1, 2, 3], ((0,), (1,)))


def test_even_group_median_and_radius_literal_fixture():
    assert mom_estimate([1, 1, 2, 2, 3, 3, 4, 4], partition_blocks(8, 4)) == 2.5
    # p=2, nu=3, chi=4, n0=16, L=2 => sqrt(32)*3*sqrt(1/8)=6.
    assert mom_radius(2, 3, 4, 16, 2) == pytest.approx(6.0)
    assert mom_radius(2, 6, 4, 16, 2) == pytest.approx(12.0)
    assert centered_bounded_envelope((0.5, 0.5), (0.5, 0.5), 2) == 16.0


def test_probability_budget_not_an_additive_radius():
    delta = confidence_budget(0.05, epsilon_coup=0.01, delta_aux=0.005)
    assert delta == pytest.approx(0.035)
    assert required_groups(4, delta) > required_groups(4, 0.05)
    for args in ((0.05, 0.05, 0), (0, 0, 0), (1, 0, 0), (0.05, -0.1, 0)):
        with pytest.raises(CertificationError):
            confidence_budget(*args)


@pytest.mark.parametrize("p", [1.1, 1.5, 2])
def test_analytically_known_envelope_bounds_actual_centered_score(p):
    q, e, muhat, actual_mu = (0.25, 0.75), (0.9, 0.1), (0.8, 0.1), (0.2, 0.7)
    outcomes = [(e[s]*(actual_mu[s] if y else 1-actual_mu[s]),
                 dr_score(y, s, q, e, muhat, reference=0.3))
                for s in (0, 1) for y in (0, 1)]
    mean = sum(prob*z for prob, z in outcomes)
    centered = sum(prob*abs(z-mean)**p for prob, z in outcomes)
    assert centered <= centered_bounded_envelope(q, e, p)


@pytest.fixture
def evaluation():
    return generate_evaluation(SyntheticConfig(), 73001)


def test_registered_certificates_include_truth_free_design_metadata(evaluation):
    log, oracle = evaluation
    for alpha in (0.05, 0.1):
        certificates = certify(log, alpha=alpha)
        assert len(certificates) == 4
        for record in certificates:
            assert record["status"] == "CERTIFIED"
            assert record["certified_level"] == pytest.approx(1-alpha)
            assert record["retained_N"] == record["raw_N"] == 4096
            assert record["graph_nodes"] == 4096
            assert record["graph_edges"] == 6144
            assert record["N_eff"] == 1024
            assert sum(record["group_sizes"]) == 128
            assert record["L_min"] == 3
            assert record["nuisance_radius"] == record["drift_radius"] == record["coupling_failure_epsilon"] == 0
            assert record["hi"]-record["estimate"] == pytest.approx(record["stochastic_radius"])
            assert record["lo"] == pytest.approx(record["estimate"]-record["stochastic_radius"])
            assert "truth" not in record
            expected_mass = 0.5 if record["candidate_id"].endswith("group1") else 1.0
            assert record["subgroup_mass"] == expected_mass
            assert subgroup_ratio_bound(record)["mass_radius"] == 0


def test_infeasible_block_design_returns_no_interval():
    log, _ = generate_evaluation(SyntheticConfig(B=16), 2)
    records = certify(log)
    assert all(r["status"] == "NOT_CERTIFIABLE" and r["lo"] is None and r["hi"] is None for r in records)
    assert all(r["reason"] == "INSUFFICIENT_BLOCKS_B_LT_2K" for r in records)


@pytest.mark.parametrize("model", ["adaptive_pathwise", "mutually_crossfit", "estimated_nu", "unknown_drift", "persistent_entity_shock", "unproved_coupling"])
def test_uncertified_models_are_refused(evaluation, model):
    log, _ = evaluation
    records = certify(replace(log, proof_model=model))
    assert all(r["status"] == "UNVERIFIED_ASSUMPTION" and r["lo"] is None for r in records)


@pytest.mark.parametrize("alpha,p", [(0, 1.5), (1, 1.5), (0.05, 1), (0.05, 2.1), (0.05, float("nan"))])
def test_invalid_confidence_or_p_returns_no_interval(evaluation, alpha, p):
    log, _ = evaluation
    records = certify(log, alpha=alpha, p=p)
    assert all(r["status"] == "NOT_CERTIFIABLE" and r["lo"] is None for r in records)


def test_frozen_design_and_timing_and_propensity_checks(evaluation):
    log, _ = evaluation
    with pytest.raises(FrozenInstanceError):
        log.config.B = 10
    for bad_row in (replace(log.rows[0], e_vector=(0.5, 0.5)),
                    replace(log.rows[0], features_available_at=2),
                    replace(log.rows[0], mu_hat=(log.rows[0].reward_y,)*2),
                    replace(log.rows[0], entity_id=-1)):
        records = certify(replace(log, rows=(bad_row,)+log.rows[1:]))
        assert all(r["status"] == "UNVERIFIED_ASSUMPTION" and r["lo"] is None for r in records)
    assert all(r["status"] == "NOT_CERTIFIABLE" for r in certify(replace(log, rows=log.rows[:-1])))


def test_regeneration_exactly_reproducible_and_fresh_streams(evaluation):
    log, oracle = evaluation
    log2, oracle2 = generate_evaluation(log.config, log.seed)
    assert log == log2
    assert oracle == oracle2
    assert certify(log) == certify(log2)
    log3, oracle3 = generate_evaluation(log.config, log.seed+1)
    assert log.rows != log3.rows
    assert oracle.moments == oracle3.moments
    assert oracle.potential_outcomes != oracle3.potential_outcomes


def test_zero_subgroup_mass_ratio_abstains():
    # One context-0 clique in every block; group1 has exactly zero design mass.
    log, _ = generate_evaluation(SyntheticConfig(n0=4, chi=4), 2)
    groups = [r for r in certify(log) if r["candidate_id"].endswith("group1")]
    assert all(r["subgroup_mass"] == 0 for r in groups)
    assert all(subgroup_ratio_bound(r)["status"] == "NOT_CERTIFIABLE" for r in groups)


def test_numerical_envelope_overflow_refuses_whole_family_without_partial_intervals():
    config = SyntheticConfig(e_by_context=(1e-308, 0.4), q_probs=(0.0, 0.75))
    log, _ = generate_evaluation(config, 7)
    records = certify(log, p=2)
    assert all(r["status"] == "NOT_CERTIFIABLE" for r in records)
    assert all(r["lo"] is None and r["hi"] is None and r["certified_level"] is None for r in records)
    assert all(r["reason"] == "MOMENT_ENVELOPE_EXCEEDS_FLOAT_RANGE" for r in records)


def test_close_policy_probabilities_keep_distinct_lossless_ids_and_truths():
    config = SyntheticConfig(q_probs=(0.12345671, 0.12345672), auditors=("all",))
    log, oracle = generate_evaluation(config, 7)
    identifiers = [candidate.candidate_id for candidate in log.family]
    assert identifiers == ["q0.12345671__all", "q0.12345672__all"]
    assert len(set(identifiers)) == len(oracle.moments) == 2
    assert oracle.moments[identifiers[0]] != oracle.moments[identifiers[1]]
    assert [record["candidate_id"] for record in certify(log)] == identifiers


def test_subnormal_propensity_cannot_emit_infinite_ratio_diagnostic():
    import json
    config = SyntheticConfig(e_by_context=(5e-324, 0.4), q_probs=(0.0, 0.75))
    log, _ = generate_evaluation(config, 7)
    records = certify(log, p=1.5)
    assert all(r["status"] == "NOT_CERTIFIABLE" and r["lo"] is None for r in records)
    assert all(r["reason"] == "IMPORTANCE_RATIO_EXCEEDS_FLOAT_RANGE" for r in records)
    json.dumps(records, allow_nan=False)


def test_plackett_luce_recomputes_remaining_mass_after_dominant_item():
    distribution = plackett_luce_slates((1.0, 1e-20, 1e-20), 2)
    assert sum(distribution.values()) == pytest.approx(1.0)
    assert distribution[(0, 1)] == pytest.approx(0.5)
    assert distribution[(0, 2)] == pytest.approx(0.5)


def test_finite_extreme_observed_weights_have_finite_scaled_ess():
    import json
    config = SyntheticConfig(e_by_context=(1e-200, 0.4))
    log, _ = generate_evaluation(config, 7)
    # A rare but supported complete-clique assignment, not a rowwise model violation.
    rare_cluster = tuple(replace(row, observed_action=1, observed_exposure_s=1,
                                e_s_logged=1e-200, reward_y=1)
                         for row in log.rows[:config.chi])
    records = certify(replace(log, rows=rare_cluster+log.rows[config.chi:]))
    assert all(record["status"] == "CERTIFIED" for record in records)
    assert all(record["effective_support_metrics"]["importance_ess_diagnostic"] == pytest.approx(4)
               for record in records)
    json.dumps(records, allow_nan=False)


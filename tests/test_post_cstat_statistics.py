import pytest

from comet.post_cstat_statistics import (EVENTS, WholeTrialSummary,
    paired_endpoint_difference, adjust_validity_family)


def trial(run_id, **updates):
    result = dict(run_id=run_id, cell="tiny", method="fixture", delta=.05,
                  coverage_applicable=True, family_covered=True,
                  candidate_count=1000000, **{k: False for k in EVENTS})
    result.update(updates)
    return result


def test_streaming_whole_trial_counts_match_small_direct_summary():
    summary = WholeTrialSummary()
    rows = [trial("a", returned=True, return_safe_useful=True),
            trial("b", returned=True, return_unsafe=True), trial("c")]
    for row in rows:
        summary.add(row)
    result = summary.result()
    assert result["independent_trials"] == 3
    assert result["endpoints"]["returned"]["rate"] == pytest.approx(2/3)
    assert result["endpoints"]["return_unsafe"]["rate"] == pytest.approx(1/3)
    assert result["unsafe_given_return_descriptive"]["rate"] == .5
    assert result["endpoints"]["return_safe_useful"]["rate"] == pytest.approx(1/3)
    assert result["family_coverage"]["denominator"] == 3
    with pytest.raises(ValueError, match="duplicate"):
        summary.add(rows[0])


def test_numerical_or_empty_failure_cannot_disappear_from_coverage():
    summary = WholeTrialSummary()
    summary.add(trial("a", family_covered=True))
    summary.add(trial("b", failure_status="NUMERICAL_FAILURE"))
    summary.add(trial("c", family_covered=False, failure_status="EMPTY_INTERSECTION"))
    result = summary.result()
    assert result["family_coverage"]["hits"] == 1
    assert result["family_coverage"]["denominator"] == 3


def test_all_abstain_is_not_safe_useful_success_and_point_methods_no_coverage():
    summary = WholeTrialSummary()
    summary.add(trial("a", coverage_applicable=False, family_covered=False))
    result = summary.result()
    assert result["family_coverage"] is None
    assert result["endpoints"]["return_safe_useful"]["rate"] == 0
    assert result["unsafe_given_return_descriptive"]["rate"] is None


def test_bootstrap_pairs_complete_trials_and_equal_engines_equal():
    values = {str(i): i % 2 for i in range(10)}
    result = paired_endpoint_difference(values, values, bootstrap_seed=12, resamples=20)
    assert result["independent_pairs"] == 10
    assert result["mean_difference"] == 0
    assert result["bootstrap_pointwise95"] == [0., 0.]
    with pytest.raises(ValueError, match="matching"):
        paired_endpoint_difference(values, {"only_one": 0}, bootstrap_seed=12)


def test_unassessable_failure_is_neither_dropped_nor_a_zero_false_claim():
    summary=WholeTrialSummary()
    summary.add(trial("a"))
    summary.add(trial("b",metrics_assessable=False,failure_status="ORACLE_FAILURE"))
    result=summary.result()
    assert result["independent_trials"]==2
    false_claim=result["endpoints"]["any_false_claim"]
    assert false_claim["unknown_trials"]==1
    assert false_claim["rate"] is None and false_claim["wilson95"] is None
    assert false_claim["realized_frequency_bounds"]==[0.,.5]


def test_nonpipeline_scope_has_no_invented_return_rate():
    summary=WholeTrialSummary()
    summary.add(trial("a",return_endpoint_applicable=False,discovery_endpoint_applicable=False))
    result=summary.result()
    assert result["endpoints"]["return_safe_useful"]["rate"] is None
    assert not result["endpoints"]["return_safe_useful"]["applicable"]


def test_rejected_record_does_not_mutate_summary_and_duplicate_pvalues_refuse():
    summary=WholeTrialSummary()
    broken=trial("a");del broken["any_false_claim"]
    with pytest.raises(ValueError): summary.add(broken)
    assert not summary.ids and summary.signature is None
    summary.add(trial("a"))
    row=summary.result()
    assert len(adjust_validity_family([row], [["tiny","fixture"]]))==1
    with pytest.raises(ValueError,match="duplicate primary"):
        adjust_validity_family([row,row],[["tiny","fixture"]])

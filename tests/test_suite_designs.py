import numpy as np
import pytest

from comet.residual_truncation import make_plan
from experiments.core_graph_dgp import WORD_GRID
from experiments.suite_designs import (build_locality_design, build_contrast_design,
    build_gap_design, evaluate_suite_oracle, generate_suite_from_primitives)


def test_outside_hub_and_weak_exposure_leave_local_law_and_radius_unchanged():
    a=build_locality_design(128,1,"moderate",namespace="paired")
    b=build_locality_design(128,64,"extreme1e-4",namespace="paired")
    for x,y in zip(a.queries,b.queries):
        assert np.array_equal(x.coefficients,y.coefficients)
    assert np.array_equal(a.core.exposure[:64],b.core.exposure[:64])
    assert a.core.graph.color_count < b.core.graph.color_count
    q_a=a.queries[1];q_b=b.queries[1]
    pa=make_plan(q_a,**a.certifier_inputs,delta=.05,family_size=16,
                 multipliers=(.5,1,2),method="generic_matched")
    pb=make_plan(q_b,**b.certifier_inputs,delta=.05,family_size=16,
                 multipliers=(.5,1,2),method="generic_matched")
    assert pa.radius==pb.radius
    assert pa.color_count==pb.color_count


@pytest.mark.parametrize("gap",[-.1,-.03,0.,.03,.1,.2])
def test_gap_is_planted_as_normalized_target_without_changing_threshold(gap):
    design=build_gap_design(128,gap)
    truths=evaluate_suite_oracle(design)
    assert truths[design.metadata["planted_query_id"]]==pytest.approx(.4+gap)
    assert design.metadata["risk_threshold"]==.4
    assert design.family.family_size==16
    for action in (0,1):
        for sign in (-1,1):
            log=generate_suite_from_primitives(design,
                np.full(128,0 if action else WORD_GRID-1,dtype=np.uint64),
                {source:sign for source in design.core.outcome_source_ids})
            assert np.all((log.outcomes>=0)&(log.outcomes<=1))


def test_contrasts_restrict_only_changed_support_and_retain_all_rows():
    design=build_contrast_design(128,.1,"weak","heavy")
    changed=design.metadata["changed_mask"]
    assert changed.sum()==13
    assert all(q.n_rows==128 for q in design.queries)
    for direct,(new,base) in zip(design.queries,design.metadata["level_pairs"]):
        assert np.array_equal(direct.coefficients,new.coefficients-base.coefficients)
        assert not np.any(direct.coefficients[~changed])
    assert set(design.certifier_inputs)==set(design.core.certifier_inputs)
    assert design.certifier_inputs["outcome_bounds"] is None


def test_changed_support_permutation_is_valid_for_non_power_of_two_N():
    design=build_contrast_design(4051,.02)
    assert design.metadata["changed_mask"].sum()==round(4051*.02)
    assert design.metadata["support_permutation_multiplier"] != 4051

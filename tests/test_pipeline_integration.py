"""Read-only integration checks of explicit designs; no random experiment."""

import numpy as np

from experiments.core_graph_dgp import WORD_GRID
from experiments.suite_designs import build_locality_design, generate_suite_from_primitives


def test_outside_only_change_preserves_exact_audited_primitive_fixture():
    small = build_locality_design(128, 1, "moderate", namespace="paired-explicit")
    large = build_locality_design(128, 64, "extreme1e-4", namespace="paired-explicit")
    words = (np.arange(128, dtype=np.uint64) * 63547913) % WORD_GRID
    assert small.core.outcome_source_ids == large.core.outcome_source_ids
    primitives = {source: (-1.0 if i % 2 else 1.0)
                  for i, source in enumerate(small.core.outcome_source_ids)}
    left = generate_suite_from_primitives(small, words, primitives)
    right = generate_suite_from_primitives(large, words, primitives)
    assert np.array_equal(left.actions[:64], right.actions[:64])
    assert np.array_equal(left.outcomes[:64], right.outcomes[:64])
    assert not np.array_equal(left.actions[64:], right.actions[64:])

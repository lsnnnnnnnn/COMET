"""Executable draft E2/E3/E4 designs, with NO protocol freeze or implicit runs.

These implement the master/override's explicit mechanisms. Chosen coefficients
must still be reconciled against the four missing planning inputs before any
scientific outcome is drawn. Generator/oracle code is separate from estimators.
"""
from dataclasses import dataclass, replace
import hashlib
import math

import numpy as np

from comet.audit_pipeline import freeze_discovered_family
from comet.queries import SignedQuery
from comet.source_graph import SourceGraph
from experiments.core_graph_dgp import (
    CoreLog, _readonly, _response_locations, build_core_design,
    draw_core_log, dyadic_probabilities, generate_from_primitives,
)


DRAFT = "DRAFT_INPUT_RECONCILIATION_PENDING"


@dataclass(frozen=True)
class SuiteDesign:
    suite: str
    core: object
    queries: tuple
    metadata: dict

    @property
    def certifier_inputs(self):
        return self.core.certifier_inputs

    @property
    def family(self):
        return freeze_discovered_family(self.queries)


def _auditor_from_level(query):
    # A policy level sums to its binary auditor; all original normalizers are 1.
    return query.coefficients.sum(axis=1)


def build_locality_design(n=32768, hub_size=16, outside_overlap="moderate",
                          namespace="E2-paired-design"):
    """One connected cycle plus an outside-only shared-source clique.

    All variants keep the first half's law unchanged. They must use the same
    replicate seed/namespace if compared as paired outside-only mechanisms.
    """
    if hub_size not in (1, 16, 64) or outside_overlap not in ("moderate", "extreme1e-4"):
        raise ValueError("unsupported E2 draft cell")
    if n < 2 * hub_size:
        raise ValueError("hub must fit strictly in the unaudited half")
    core = build_core_design(n, "cycle", "moderate", "bounded", namespace)
    hub_rows = np.arange(n-hub_size, n)
    new_source = (namespace, "outcome", "outside-hub")
    ids = core.outcome_source_ids + (new_source,)
    index = np.column_stack((core.outcome_source_indices, np.zeros(n, dtype=int)))
    coefficients = np.column_stack((core.outcome_source_coefficients, np.zeros(n)))
    coefficients[hub_rows, :-1] *= .8
    index[hub_rows, -1] = len(ids)-1
    coefficients[hub_rows, -1] = .02
    sources = [set(row) for row in core.row_sources]
    for row in hub_rows:
        sources[row].add(new_source)
    graph = SourceGraph.from_sources(sources)
    e1 = core.exposure[:, 1].copy()
    if outside_overlap == "extreme1e-4":
        e1[n//2:] = .0001
    cutoffs, e1 = dyadic_probabilities(e1)
    exposure = _readonly(np.column_stack((1-e1, e1)))
    core = replace(core, logging_cutoffs=cutoffs, exposure=exposure,
        outcome_source_ids=ids, outcome_source_indices=_readonly(index, int),
        outcome_source_coefficients=_readonly(coefficients),
        row_sources=tuple(frozenset(row) for row in sources), graph=graph)
    i = np.arange(n)
    auditors = (np.ones(n), (i < n//2).astype(float),
                (i < n//4).astype(float), (i >= n//2).astype(float))
    queries = []
    for policy in range(4):
        q = core.queries[4*policy].coefficients
        for auditor, h in enumerate(auditors):
            queries.append(SignedQuery(f"E2/policy{policy}/auditor{auditor}",
                h[:, None]*q, 0, provenance="fixed_design:"+namespace))
    return SuiteDesign("E2", core, tuple(queries), dict(status=DRAFT,
        hub_size=hub_size, outside_overlap=outside_overlap,
        audited_region="first_half", local_query_suffix="auditor1",
        pairing="same_complete_replicate_across_outside_variants",
        primary_units_per_cell=300))


def build_contrast_design(n=32768, changed_fraction=.1, overlap="moderate",
                          outcome="bounded", namespace="E3-paired-design"):
    if changed_fraction not in (.02, .1, 1.):
        raise ValueError("unsupported E3 changed-support fraction")
    core = build_core_design(n, "cycle", overlap, outcome, namespace)
    multiplier = 4051
    while math.gcd(multiplier, n) != 1:
        multiplier += 2
    changed = ((np.arange(n, dtype=np.int64)*multiplier) % n) < max(1, round(n*changed_fraction))
    baseline = np.full((n, 2), .5)
    queries, level_pairs = [], []
    for policy in range(4):
        new_q = core.queries[4*policy].coefficients.copy()
        if policy == 0:
            _, q1 = dyadic_probabilities(np.full(n, .7))
            new_q[:] = np.column_stack((1-q1, q1))
        new_q[~changed] = baseline[~changed]
        for auditor in range(4):
            h = _auditor_from_level(core.queries[auditor])
            name = f"E3/policy{policy}/auditor{auditor}"
            direct = SignedQuery(name, h[:, None]*(new_q-baseline), 0,
                                 provenance="fixed_design:"+namespace)
            queries.append(direct)
            level_pairs.append((SignedQuery(name+"/new",h[:,None]*new_q,0),
                                SignedQuery(name+"/base",h[:,None]*baseline,0)))
    return SuiteDesign("E3", core, tuple(queries), dict(status=DRAFT,
        changed_fraction_requested=changed_fraction,
        support_permutation_multiplier=multiplier,
        changed_fraction_actual=float(changed.mean()), changed_mask=changed,
        baseline_policy=baseline, level_pairs=tuple(level_pairs),
        level_difference_budget="delta/number_of_distinct_levels; deduplicate_shared_base_levels; same_total_delta",
        primary_units_per_cell=300))


def build_gap_design(n=32768, gap=.03, overlap="moderate", outcome="bounded",
                     namespace="E4-fixed-gap-design"):
    if gap not in (-.1, -.03, 0., .03, .1, .2):
        raise ValueError("gap is outside the prespecified master grid")
    core = build_core_design(n, "cycle", overlap, outcome, namespace)
    group = np.arange(n) < max(1, round(.1*n))
    auditors = [group.astype(float)] + [
        _auditor_from_level(core.queries[i]) for i in (0, 1, 3)]
    queries = []
    for policy in range(4):
        q = core.queries[4*policy].coefficients
        if policy == 0:
            q = np.column_stack((np.zeros(n),np.ones(n)))
        for auditor, h in enumerate(auditors):
            if h.mean() == 0:
                raise ValueError("draft auditor has zero design mass")
            queries.append(SignedQuery(f"E4/policy{policy}/auditor{auditor}",
                h[:,None]*q,0,normalizer=float(h.mean()),provenance="fixed_design:"+namespace))
    return SuiteDesign("E4", core, tuple(queries), dict(status=DRAFT, gap=gap,
        risk_threshold=.4, planted_normalized_target=.4+gap,
        planted_query_id="E4/policy0/auditor0", group_mask=group,
        subgroup_mass=float(group.mean()), primary_units_per_cell=300))


def _suite_response_locations(design):
    """Generator/evaluator only; never included in certifier_inputs."""
    means = _response_locations(design.core.x)
    if design.suite == "E4":
        group = design.metadata["group_mask"]
        positions = np.arange(int(group.sum()),dtype=float)
        variation = .025*np.sin(2*np.pi*(positions+.5)/len(positions))
        variation -= variation.mean()
        means[group,1] = design.metadata["planted_normalized_target"]+variation
        means[group,0] = .45+.02*np.cos(2*np.pi*(positions+.5)/len(positions))
    return means


def _adjust_generated_log(design, log):
    if design.suite != "E4":
        return log
    rows = np.arange(design.core.n)
    delta = _suite_response_locations(design)-_response_locations(design.core.x)
    outcomes = log.outcomes+delta[rows,log.actions]
    data_digest=hashlib.sha256(log.actions.tobytes()+outcomes.astype('<f8').tobytes()).hexdigest()
    return CoreLog(log.actions,_readonly(outcomes),data_digest,log.seed_namespace)


def generate_suite_from_primitives(design, words, primitives):
    return _adjust_generated_log(design,generate_from_primitives(design.core,words,primitives))


def draw_suite_log(design, seed):
    """Defined for later frozen execution; does not draw until explicitly called."""
    return _adjust_generated_log(design,draw_core_log(design.core,seed))


def evaluate_suite_oracle(design):
    means=_suite_response_locations(design)
    return {q.query_id:q.target(means) for q in design.queries}

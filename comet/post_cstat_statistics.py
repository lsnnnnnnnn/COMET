"""Whole-trial Monte Carlo summaries for the new workstream.

Intervals here describe simulation performance, not uncertainty certificates
for logged outcomes. Each input is one complete independent trial for one
fixed cell/method/level. Candidate counts never increase its replication count.
"""
from collections import Counter
import math

import numpy as np

from .metrics import wilson
from .gate_c_statistics import holm_adjust, undercoverage_pvalue


EVENTS = ("any_false_claim", "any_false_safe", "any_false_violation",
          "true_violation_detected", "discovered_and_certified", "returned",
          "return_unsafe", "return_safe_useful")


class WholeTrialSummary:
    """Streaming count/endpoint aggregation, with no candidate pooling."""
    def __init__(self):
        self.ids = set()
        self.counts = Counter()
        self.coverage_applicable = None
        self.failure_statuses = Counter()
        self.sum_width = 0.
        self.width_count = 0
        self.signature = None
        self.applicabilities = None
        self.event_unknown = Counter()

    def add(self, trial):
        run_id = trial["run_id"]
        if run_id in self.ids:
            raise ValueError("duplicate independent trial ID")
        signature = tuple(trial[k] for k in ("cell", "method", "delta"))
        applicability = {event: (bool(trial.get("return_endpoint_applicable", True))
                        if event in ("returned", "return_unsafe", "return_safe_useful")
                        else bool(trial.get("discovery_endpoint_applicable", True))
                        if event == "discovered_and_certified" else True) for event in EVENTS}
        for event in EVENTS:
            if event not in trial:
                raise ValueError("missing required whole-trial endpoint: " + event)
            if not isinstance(trial[event], (bool, np.bool_)):
                raise ValueError("whole-trial endpoints must be booleans")
        if trial["return_unsafe"] and not trial["returned"]:
            raise ValueError("unsafe return must include return")
        if trial["return_safe_useful"] and (not trial["returned"] or trial["return_unsafe"]):
            raise ValueError("safe-and-useful return is a joint event")
        width = trial.get("mean_coordinate_width")
        if width is not None and (not math.isfinite(float(width)) or float(width) < 0):
            raise ValueError("invalid per-trial width summary")
        if self.signature is None:
            self.signature = signature
            self.coverage_applicable = bool(trial["coverage_applicable"])
            self.applicabilities = applicability
        if signature != self.signature or bool(trial["coverage_applicable"]) != self.coverage_applicable:
            raise ValueError("a summary requires one fixed cell/method/level/applicability")
        if applicability != self.applicabilities:
            raise ValueError("endpoint applicability cannot change after failures")
        self.ids.add(run_id)
        self.counts["trials"] += 1
        if self.coverage_applicable:
            # A numerical/empty-set failure is not silently removed.
            covered = bool(trial.get("family_covered", False)) and not bool(trial.get("failure_status"))
            self.counts["family_covered"] += covered
        self.failure_statuses[trial.get("failure_status") or "COMPLETE"] += 1
        assessable = bool(trial.get("metrics_assessable", True))
        for event in EVENTS:
            self.counts[event] += bool(trial[event]) if assessable else 0
            self.event_unknown[event] += (not assessable) and applicability[event]
        if width is not None:
            self.sum_width += float(width)
            self.width_count += 1

    def result(self):
        if not self.ids:
            raise ValueError("no complete trial observations")
        n = self.counts["trials"]
        cell, method, delta = self.signature
        result = dict(cell=cell, method=method, delta=delta, independent_trials=n,
            uncertainty="pointwise_Wilson95_per_fixed_cell_method_not_simultaneous",
            status_counts=dict(self.failure_statuses), endpoints={})
        for event in EVENTS:
            hits = self.counts[event]
            applicable = self.applicabilities[event]
            unknown = self.event_unknown[event]
            result["endpoints"][event] = dict(hits=hits if applicable else None,
                denominator=n if applicable else 0, unknown_trials=unknown,
                applicable=applicable, rate=hits/n if applicable and not unknown else None,
                wilson95=list(wilson(hits, n)) if applicable and not unknown else None,
                realized_frequency_bounds=[hits/n,(hits+unknown)/n] if applicable else None)
        returned = self.counts["returned"]
        unsafe = self.counts["return_unsafe"]
        return_unknown = self.event_unknown["returned"]
        result["unsafe_given_return_descriptive"] = dict(hits=unsafe, denominator=returned,
            unknown_trials=return_unknown,
            rate=unsafe/returned if returned and not return_unknown else None,
            wilson95=list(wilson(unsafe, returned)) if not return_unknown else None,
            interpretation="not_automatically_controlled_at_delta")
        result["family_coverage"] = None
        if self.coverage_applicable:
            hits = self.counts["family_covered"]
            result["family_coverage"] = dict(hits=hits, denominator=n, rate=hits/n,
                wilson95=list(wilson(hits, n)),
                undercoverage_p=undercoverage_pvalue(hits, n, 1-delta),
                interpretation="nonrejection_is_not_a_coverage_proof")
        result["mean_per_trial_coordinate_width"] = (
            self.sum_width/self.width_count if self.width_count else None)
        result["width_trials"] = self.width_count
        return result


def adjust_validity_family(summaries, registered_comparisons):
    """Keep the NEW frozen diagnostic family distinct from historical 17 tests."""
    registered = tuple(tuple(item) for item in registered_comparisons)
    if any(len(item) != 2 for item in registered):
        raise ValueError("comparison keys must contain cell and method")
    if len(set(registered)) != len(registered):
        raise ValueError("duplicate registered comparison")
    available = {}
    for row in summaries:
        if row["delta"] != .05:
            continue
        key = (row["cell"], row["method"])
        if key in available:
            raise ValueError("duplicate primary cell-method summary")
        available[key] = row
    pvalues = {}
    for key in registered:
        coverage = available.get(key, {}).get("family_coverage")
        pvalues[key] = coverage["undercoverage_p"] if coverage else None
    return holm_adjust(pvalues)


def paired_endpoint_difference(left, right, *, bootstrap_seed, resamples=2000):
    """Paired replicate bootstrap of one performance endpoint.

    Inputs map independent replicate IDs to per-trial values (not coordinates).
    For paired design variants the caller must retain their common replicate
    identifier; it must not treat variants as additional independent logs.
    """
    if set(left) != set(right) or not left:
        raise ValueError("complete matching independent replicate IDs required")
    keys = sorted(left)
    difference = np.array([float(left[k])-float(right[k]) for k in keys])
    if not np.isfinite(difference).all() or resamples < 1:
        raise ValueError("invalid paired summary input")
    rng = np.random.default_rng(bootstrap_seed)
    samples = np.array([np.mean(difference[rng.integers(0, len(keys), len(keys))])
                        for _ in range(resamples)])
    return dict(independent_pairs=len(keys), mean_difference=float(difference.mean()),
                bootstrap_pointwise95=np.quantile(samples, [.025, .975]).tolist(),
                bootstrap_seed=int(bootstrap_seed), resamples=resamples,
                resampling_unit="complete_independent_trial")

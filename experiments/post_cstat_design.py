"""Deterministic evidence-cost maps. Generates ZERO random outcomes.

The multiplier grid is an explicit argument, because the referenced final
THEORY_NOTE/blueprint was not present at startup. Outputs are marked provisional
until those planning inputs are reconciled; they are not empirical findings.
"""
import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np

from comet.residual_truncation import choose_truncation


LABEL = "PROVISIONAL_DESIGN_CALCULATION_NOT_BLUEPRINT_FREEZE"


def radius_row(n, nominal_pi, epsilon, p, chi, multipliers, *, m=16, delta=.05):
    active = max(1, round(n * nominal_pi))
    pi = active / n
    q = np.array([.5, .5])
    e = np.array([1 - epsilon, epsilon])
    if not 0 < epsilon < 1 or chi > active:
        raise ValueError("invalid supported design or coloring")
    if p == 2:
        b = .25
        family = "bounded_[0,1]_midpoint_nuisance"
    else:
        # Known location class [0,1], midpoint fit, sum |noise coefficients|=.1.
        b = (.5 + .1 * (1.75 / (1.75 - p)) ** (1 / p)) ** p
        family = "symmetric_pareto_sources_a1.75_total_scale.1"
    row_v = float(np.sum(q ** p * e ** (1 - p) * b))
    tau, pieces = choose_truncation(np.array([active * row_v]), p, chi,
                                    delta / m, n, multipliers)
    bias, variance, range_piece = (x / pi for x in pieces)
    truncated = bias + variance + range_piece
    hoeffding = bernstein = None
    if p == 2:
        span = float(np.max(q / e))  # residual endpoints ±.5*q/e
        t = math.log(2 * m / delta)
        hoeffding = math.sqrt(chi * active * span ** 2 * t / 2) / active
        bounded_variance = min(row_v, span ** 2 / 4)
        bernstein = (math.sqrt(2 * chi * active * bounded_variance * t)
                     + chi * span * t / 3) / active
    selected_radius = min(x for x in (truncated, hoeffding, bernstein) if x is not None)
    return dict(label=LABEL, N=n, active_rows=active, pi=pi,
                requested_pi=nominal_pi, epsilon=epsilon, p=p, chi_verified=chi,
                mean_class="[0,1]", family_size=m, delta=delta,
                outcome_model=family, residual_p_moment=b,
                weighted_row_p_moment=row_v, tau=tau, bias=bias,
                concentration=variance, range_contribution=range_piece,
                normalized_truncation_radius=truncated,
                normalized_hoeffding_radius=hoeffding,
                normalized_bernstein_radius=bernstein,
                design_selected_radius=selected_radius,
                sufficient_normalized_gap_strictly_above=2 * selected_radius,
                information_lower_bound="not_this_procedure_sufficient_radius")


def write_csv(path, rows):
    with path.open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--multipliers", required=True,
                        help="explicit comma-separated design-only test grid")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reconciled-theory-note", type=Path)
    args = parser.parse_args()
    multipliers = tuple(float(x) for x in args.multipliers.split(","))
    args.output.mkdir(parents=True, exist_ok=True)
    grid = [radius_row(*values, multipliers) for values in itertools.product(
        (8192, 32768, 131072), (.02, .1, .5), (.002, .02, .2), (1.5, 2.), (1, 2, 3, 64))]
    declining = []
    for n, pi, p, chi, beta in itertools.product(
            (8192, 32768, 131072), (.02, .1, .5), (1.5, 2.), (1, 2, 3, 64), (0., .5, 1.)):
        row = radius_row(n, pi, .2 * (n / 8192) ** (-beta), p, chi, multipliers)
        row["declining_propensity_beta"] = beta
        declining.append(row)
    write_csv(args.output / "fixed_overlap_costs.csv", grid)
    write_csv(args.output / "declining_overlap_costs.csv", declining)
    a_r = math.sqrt(math.log(40) / (2 * 8192))
    analytic_a = dict(label="DETERMINISTIC_ANALYTIC_HISTORICAL_DESIGN_CHECK",
        new_outcome_draws=0, legacy_primary_family_modified=False, N=8192,
        m=1, delta=.05, score="Z=Y-.25", residual_range=[-.5, .5],
        target=.2375, threshold=.2, gamma=.0375, hoeffding_radius=a_r,
        twice_radius=2 * a_r, gamma_strictly_above_twice_radius=.0375 > 2 * a_r,
        inference="at_least_.95_theoretical_detection_on_coverage_event_not_measured_power")
    (args.output / "historical_A_analytic_check.json").write_text(
        json.dumps(analytic_a, indent=2) + "\n")
    outputs = {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
               for f in sorted(args.output.iterdir()) if f.is_file() and f.name != "manifest.json"}
    manifest = dict(status=LABEL, new_outcome_draws=0, legacy_new_outcome_draws=0,
        fixed_overlap_rows=len(grid), declining_overlap_rows=len(declining),
        multipliers=multipliers, source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        outputs=outputs, prerequisite="reconcile_missing_planning_inputs_before_freeze")
    if args.reconciled_theory_note is not None:
        expected=tuple(2**(j/4) for j in range(-24,25))
        if len(multipliers)!=49 or not np.allclose(multipliers,expected,rtol=1e-14,atol=0):
            raise ValueError("the reconciled THEORY_NOTE grid must have its specified 49 multipliers")
        label="DETERMINISTIC_RECONCILED_DESIGN_CALCULATION_NOT_EMPIRICAL"
        for row in grid+declining:
            row['label']=label
        write_csv(args.output / "fixed_overlap_costs.csv",grid)
        write_csv(args.output / "declining_overlap_costs.csv",declining)
        manifest.update(status=label,prerequisite=None,
            theory_note_sha256=hashlib.sha256(args.reconciled_theory_note.read_bytes()).hexdigest())
        manifest['outputs']={f.name:hashlib.sha256(f.read_bytes()).hexdigest()
            for f in sorted(args.output.iterdir()) if f.is_file() and f.name!='manifest.json'}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k:v for k,v in manifest.items() if k != "outputs"}, indent=2))


if __name__ == "__main__":
    main()

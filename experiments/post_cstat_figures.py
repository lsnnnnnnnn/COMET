"""Render actual deterministic design calculations; no outcome generation."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


COLORS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7"]


def read(path):
    rows = []
    with path.open() as src:
        for raw in csv.DictReader(src):
            row = {}
            for key, value in raw.items():
                try:
                    row[key] = float(value)
                except (ValueError, TypeError):
                    row[key] = value
            rows.append(row)
    return rows


def save(fig, destination, name):
    fig.savefig(destination / (name + ".png"), dpi=300, bbox_inches="tight")
    fig.savefig(destination / (name + ".svg"), bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("results/post_cstat/design_v0"))
    parser.add_argument("--output", type=Path, default=Path("paper/post_cstat/figures"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    fixed = read(args.input / "fixed_overlap_costs.csv")
    declining = read(args.input / "declining_overlap_costs.csv")
    input_manifest = json.loads((args.input / "manifest.json").read_text())
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
        "axes.spines.top": False, "axes.spines.right": False,
        "svg.fonttype": "none", "axes.titleweight": "normal"})

    fig, axes = plt.subplots(1, 2, figsize=(8, 3.1), constrained_layout=True)
    for ax, p in zip(axes, (2., 1.5)):
        for color, epsilon in zip(COLORS, (.2, .02, .002)):
            rows = sorted([r for r in fixed if r["p"] == p and r["chi_verified"] == 2
                and r["requested_pi"] == .1 and r["epsilon"] == epsilon], key=lambda r:r["N"])
            ax.loglog([r["N"] for r in rows], [r["design_selected_radius"] for r in rows],
                "o-", color=color, label=f"e(1)={epsilon:g}")
        ax.axhline(.5, color=".5", linestyle=":", label="half mean-class diameter")
        ax.set(xlabel="Retained rows N", ylabel="Normalized certificate radius",
            title=f"{'Bounded' if p == 2 else 'Finite moment'}, p={p:g}")
        ax.legend(frameon=False, fontsize=7)
    save(fig, args.output, "analytic_evidence_cost")

    fig, axes = plt.subplots(1, 2, figsize=(8, 3.1), constrained_layout=True)
    for ax, p in zip(axes, (2., 1.5)):
        for color, beta, marker in zip(COLORS, (0., .5, 1.), ("o", "s", "^")):
            rows = sorted([r for r in declining if r["p"] == p and r["chi_verified"] == 2
                and r["requested_pi"] == .1 and r["declining_propensity_beta"] == beta],
                key=lambda r:r["N"])
            ax.loglog([r["N"] for r in rows], [r["design_selected_radius"] for r in rows],
                marker=marker, color=color, label=f"beta={beta:g}")
        ax.set(xlabel="Retained rows N", ylabel="Normalized certificate radius",
               title=f"p={p:g}, e(1)=0.2 (N/8192)^(-beta)")
        ax.legend(frameon=False, fontsize=8)
    save(fig, args.output, "analytic_declining_overlap")

    rows = [r for r in fixed if r["N"] == 32768 and r["requested_pi"] == .1
            and r["chi_verified"] == 2]
    rows.sort(key=lambda r:(-r["p"], -r["epsilon"]))
    fig, ax = plt.subplots(figsize=(7.5, 3.1), constrained_layout=True)
    bottom = np.zeros(len(rows))
    for key, label, color in zip(("bias", "concentration", "range_contribution"),
            ("Clipping bias", "Graph concentration", "Bounded range term"), COLORS):
        values = np.array([r[key] for r in rows])
        ax.bar(np.arange(len(rows)), values, bottom=bottom, color=color, label=label)
        bottom += values
    ax.set_xticks(np.arange(len(rows)), [f"p={r['p']:g}\ne={r['epsilon']:g}" for r in rows])
    ax.set(ylabel="Normalized residual-truncation radius", xlabel="Known design conditions")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    save(fig, args.output, "analytic_radius_components")

    manifest = dict(status="DETERMINISTIC_DESIGN_FIGURES_NOT_EMPIRICAL_RESULTS",
        source_directory=str(args.input), new_outcome_draws=0,
        grid_status=input_manifest["status"],
        error_bars="not_applicable_to_deterministic_algebraic_bounds",
        files={f.name:hashlib.sha256(f.read_bytes()).hexdigest()
               for f in sorted(args.output.iterdir()) if f.suffix in (".png", ".svg")})
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"figures":len(manifest["files"]), "new_outcome_draws":0}))


if __name__ == "__main__":
    main()

# D1–D5 future preregistration proposals — no experiments run

These are separate future protocols, prepared without consulting C-STAT confirmation outcomes.
No D-stage outcome, fitted model, pilot, or seed draw has been generated. The
only computations are deterministic feasibility algebra in
`experiments/gate_d_design_only.py`. Each document must become a separately
reviewed, committed scientific freeze before its own pilot/confirmation phase.
C-STAT settings and 6,000 IDs are unaffected.

| Study | Standalone proposal | Main unresolved gate | Data budget now |
|---|---|---|---:|
| D1 | `D_preregistrations/D1_power.md` | feasible signed gaps and candidate library | 0 |
| D2 | `D_preregistrations/D2_discovery.md` | planted interaction and pilot-only selection implementation | 0 |
| D3 | `D_preregistrations/D3_repair.md` | multi-channel simultaneous event and competing utility/cost | 0 |
| D4 | `D_preregistrations/D4_dependency.md` | joint-policy compatibility and strong graph proof | 0 |
| D5 | `D_preregistrations/D5_overlap_tails_pilot.md` | new method proofs; affordable informative tail design | 0 |

## Common future governance

Fresh domain strings are `COMET-D1-v1`, ..., `COMET-D5-v1`; none uses
`COMET-GATE-C-SHA256-128-v1`. Proposed master seed 2026111305 is domain-separated
by study, scientific-version, phase (pilot/confirmation), cell, replication,
and mechanism (design, joint assignment, primitive outcomes, nuisance,
discovery, evaluation, oracle-only Monte Carlo). Hash with SHA-256, retain the
first 128 bits, validate collisions across the full allocated manifest, and
commit the exact manifest before any draw. These are proposals, not allocated
or consumed random streams. A changed law/method requires a new version/domain.

Use one independent complete log as the coverage/error/decision sampling unit;
retain complete families and fixed denominator even when intervals are vacuous,
methods are inapplicable, or decisions abstain. Use Wilson intervals for binary
replication endpoints; candidate-specific endpoints are separate. Freeze the
primary comparison list and Holm family before outcomes. Report every planned
cell, including failures. Ordinary point/SNIPS/clipped comparators remain
uncertified unless separately proved. A proposal for 1,000 replications yields
Wilson full-success lower bound about .9962 and about .0135 half-width at a
.95 rate; these are binomial design calculations, not D-stage measurements.
Actual replication counts, time cap and allocation must be frozen after
proof/design-only feasibility and a separate engineering pilot, never based on
C-STAT oracle outcomes or the future confirmatory sample.

## Design-only feasibility artifacts and interpretation

`results/gate_D_proposals/D1_feasibility.csv` has 648 rows crossing raw signed
gaps, mass, chi, family size and overlap. A raw numerator gap cannot be freely
crossed with tiny subgroup mass: with f=.25, threshold=.2*pi and mean class
[0,1], its allowable range is [-.45*pi,.55*pi]. Impossible cells are explicitly
flagged rather than silently changing the meaning of gamma. The proposal also
includes a separate, clearly named conditional-gap axis and all-population
cells to cover the requested large raw gaps.

For q1=.5 and constant known e, J=.25/e+.25/(1-e), a sufficient bounded-graph
radius is r=sqrt(m*chi*pi*J/(alpha*N)). On the simultaneous event, a true signed
raw gap with |gap|>2r yields the correct strict decision (excluding equality
and distinguishing safe boundary conventions). Inverting this inequality gives
N>4*m*chi*pi*J/(alpha*gap^2). It is a sufficient theorem-based condition, not
an exact finite-sample power calculation. Set gap/r=.5,1,2,4 using D-measurable
radii before draws, and retain or reject cells solely by mean-class feasibility.

`D5_F_radius_inversion.csv` keeps the original F model unchanged and computes
strict r<pi/2 at B=128, K=9, chi=4, p=1.5 by increasing balanced n0 only. It is a
sufficient raw-width criterion, not a claim that all intersections are vacuous
below that N. The all-auditor requirements are roughly 38–55 million rows;
group1 requires eight times as many because its target diameter halves while
the frozen worst-row moment envelope does not shrink. This calculation argues
for a separate proof/method gate before expensive D5 outcomes, not alteration
of C-STAT F.

A linear memory extrapolation from preflight's 118.44 MiB at N=32768 is shown
in the D5 table. It is an explicitly rough implementation estimate, not a
measurement or upper bound; the current row-object implementation is unsuitable
for these sizes without separately verified streaming engineering. For ordinary
N=32768 designs, preflight indicates order 5 CPU seconds/log and 120 MiB process
peak locally. Full future grids can multiply to millions of CPU seconds; budget
and prune only by predefined design feasibility before allocating confirmation.
No D-stage resource number is presented as actual execution.

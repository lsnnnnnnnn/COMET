# D1 — violation magnitude and certification power (UNRUN PROPOSAL)

Fresh domain: `COMET-D1-v1`. Freeze independently; C-STAT outcomes do not select
these settings. Purpose: separate useful decisions from simultaneous coverage.

Use independent exogenous blocks and bounded potential outcomes, exact binary
assignment, a sufficient replicated-clique graph, fixed or independently fitted
bounded nuisance, and a frozen finite family. Propose B=128, raw N chosen by
radius inversion, chi in {1,4,8}, group masses {.02,.05,.10,.20}, family sizes
{1,16,64}, strong e=.5 and weak e=.01. Choose integer cluster counts consistent
with each mass; exact masses .02/.05 require cluster counts divisible by 100/20.
Every candidate must be substantively defined in a committed design rather than
padding the library with duplicates to change the multiplicity.

Raw signed gap is M_D-.2*pi, with grid {0,±.025,±.05,±.10,±.20}. Keep impossible
raw-gap/mass crossings in the design inventory as INFEASIBLE_BEFORE_DRAW. Add
all-population pi=1 cells to realize the whole raw gap grid. Separately register
conditional gaps (M_D-.2*pi)/pi on that grid for the small-mass settings; never
label them raw gamma. Set response means from these design targets within [0,1].
An additional axis uses signed raw gamma/r in {±.5,±1,±2,±4}, with design-only
r from the proved method; feasibility is checked before random draws. Gamma=0
is the boundary null, and all-null/strict-safe families are mandatory.

Primary per-log endpoints: any correctly certified violation, any false-safe,
any false-violation, all abstain, and family coverage. Secondary: candidate-level
power, false decisions, subgroup mass, raw/intersected width and all/some
nontriviality. A boundary target is nonviolating under the strict > definition.
Point-only comparators never count as certified decisions. Use Wilson intervals
on independent logs, not on pooled candidates. Freeze multiplicity across the
final primary cell/method endpoint list before confirmation.

Sample plan: start with design-only N inversion and a separate engineering
pilot. Propose 1,000 independent confirmations per feasible final cell; the final
allocation and null/alternative sampling list require an explicit resource
freeze. At m=64, pi=.02 and weak overlap, the sufficient sample requirement may
be prohibitively large; record that result rather than using pilot oracle power
to hide the cell. No D1 data are authorized or generated in C-STAT.

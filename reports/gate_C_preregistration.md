# Gate C frozen preregistration v1 — C-PREFLIGHT scope

Baseline: `3f8902d1033f3c4eece9a3746912ac9f1d8904ef`. The user's current
authorization is **C-PREFLIGHT only**. The full supplied master has been read;
its later C-STAT, C-DECISION, real-data and optional theory stages are deferred.
Machine inputs are `configs/gate_C_frozen.json` and
`configs/gate_C_seed_manifest.json`. These files, the model/proofs and tests
will be committed before any of the twelve primary preflight logs are drawn.
The exact freeze SHA is recorded in the batch manifest and phase report.

## Primary cells and method family

All cells use B=128 independent exogenous macro-blocks, complete replicated
cliques, fixed mu_hat=(.5,.5), f=.25, and binary exposure S=A. Contexts alternate
by independent cluster, with the same balanced pattern in every block.

| Cell | N / n0 | chi | e(1) at contexts 0,1 | q(1), auditors | Outcome / MOM p |
|---|---|---:|---|---|---|
| A | 8192 / 64 | 1 | .5,.5 | .5 × all (m=1) | Bernoulli / 2 |
| B | 32768 / 256 | 1 | .4,.6 | eight q × all,group1 (m=16) | Bernoulli / 2 |
| C | 32768 / 256 | 4 | .4,.6 | same m=16 | Bernoulli / 2 |
| D | 32768 / 256 | 1 | .01,.02 | same m=16 | Bernoulli / 2 |
| E | 32768 / 256 | 4 | .01,.02 | same m=16 | Bernoulli / 2 |
| F | 32768 / 256 | 4 | .4,.6 | same m=16 | symmetric Pareto location model / 1.5 |

The eight q probabilities are .1,.2,.3,.4,.6,.7,.8,.9. This is eight distinct
policies crossed with two meaningful auditors, not sixteen duplicated auditors.
The group1 auditor selects exactly half the fixed rows. Each policy distribution
and exact logging distribution sums to one on the same binary exposure space.
Positive but weak support in D/E is distinct from the zero-support test control.
Design-only q/e spectra, scales, group feasibility and radii are archived
separately before outcomes. No observed ESS replaces graph N_eff=N/chi.

Methods are `orig_mom`, `exact_binomial_mom`, `bounded_graph_chebyshev`, `ips`,
`dm`, `dr`, and `full_feasible_range`. The first three carry their separate
proved guarantees where applicable. IPS/DM/DR are `POINT_ONLY`, with no interval
or certified decision. Graph Chebyshev is `NOT_APPLICABLE` in F. The range
benchmark uses known conditional-mean-class bounds, including in F; it is not
a concentration result. C0's clipping proof did not expose a clipped API, so
no clipped method is included. Optional heuristics and new Bernstein bounds
are omitted. There is no outcome-based shortest-interval selection.

## Heavy-tail choice, known scales and oracle

F uses Y(s)=mu_s(X)+epsilon_s with independent symmetric Pareto noises of
scale .1 and exponent a=1.75. Its ideal law has mean-zero noise,
E|epsilon|^p=a*.1^p/(a-p), finite at p=1.5 and infinite at p=2. This meets the
master's genuine unbounded-reward requirement; Student t was an example, not
a required distribution. The choice was made from analytic tractability before
Gate C outcomes. The finite-precision sampler's positive 53-bit right-endpoint
inverse-CDF grid has a moment bounded by that integral and exact sign symmetry;
it is a numerical approximation, not a literally infinite-variance finite
machine distribution. It does not clip observed Y to [0,1].

Known conditional centered score p-moment envelopes come only from exogenous
q/e, p, bounded fixed nuisance, known location class [0,1], and the analytic
noise moment. No true response location or empirical tail scale is a radius
input. The proof is `theory/gate_c_heavy_tail_contract.md`. For A–E the C0
bounded envelope remains unchanged. No nuisance/drift radius or coupling
failure allowance is invented: all are zero under the actual registered model.

The oracle is the conditional finite-window mean
M_D=N^-1 sum_u h_u[sum_s q_u(s)mu_u(s)-f]. It is evaluated analytically only
after every method at both levels has finished. It is not the realized
potential-outcome average or a deployment target. With the balanced stable
design, M_all=.025+.425*q(1) and M_group1=.05+.225*q(1). These expressions
are deterministic test fixtures, not estimator inputs. Conditional means
mu_s(x) lie in [0,1] even in F, so the known target class is
[-pi_h*f,pi_h*(1-f)]; this bound does **not** assert bounded heavy-tail rewards.

## Seeds, pairing and stopping

The frozen manifest contains all 6,000 confirmatory run IDs (1,000 per cell)
and twelve separate preflight IDs (two per cell). The versioned SHA-256
algorithm derives independent domain-separated 128-bit seeds from master seed
2026111203, phase, cell, replicate and mechanism. All allocated seeds are
checked for distinctness. This seed domain is different from Gate A+B+C0.
Preflight logs will never enter confirmatory denominators.

Seven streams are allocated: design_context, graph_shocks, logging_exposure,
potential_outcomes, nuisance_discovery_pilot, evaluation_outcomes, truth_mc.
Only logging_exposure and potential_outcomes are consumed in this deterministic
design/fixed-nuisance model. The other five remain explicitly reserved: graph
and contexts are fixed, no fit/discovery is performed, consistency reveals
Y(S) without a second observation draw, and truth is analytic. Reserving these
streams does not fabricate a pilot or imply its independence was empirically
verified. Cluster draws are fresh across cliques and blocks.

90% and 95% intervals and all methods share each logged replicate. Exactly
twelve preflight logs are planned, at the full declared N. Two per cell is a
small integration budget chosen under the user's C-PREFLIGHT-only instruction;
the master's 50–100 example is not silently treated as mandatory or executed.
It cannot estimate nominal coverage or power. Unit-test fixtures are separate
temporary computational checks, not added scientific cells.

The runner atomically checkpoints each completed `(cell,replicate)` and records
its data digest, payload hash and input/source fingerprint. A deliberate crash
after the first committed checkpoint will test recovery; resume must skip that
record without changing its bytes. Other crashes stop the batch, preserve a
failure entry and traceback, and permit retry of incomplete IDs only. Completed
data are never overwritten. No outcome-dependent stopping or failed-run removal
is allowed. Configuration or scientific-source changes invalidate resume.
The entry point exposes no confirmatory execution mode.

## Endpoints, comparisons and denominators

Primary future confirmatory endpoint: 95% simultaneous coverage of every
eligible member of a frozen cell-method family. Secondary level: 90%, using
the same logs. Report raw coverage, issued-and-covers, issuance, applicable
denominators, Wilson 95% intervals, and marginal coverage. Full-range intervals
remain in coverage denominators. Inapplicable and point-only methods remain
visible in applicability totals, with coverage undefined rather than fabricated.
Conditional coverage among issued families is descriptive and separate from
the unconditional certificate event. Empty intersections cannot issue decisions.

For each of 17 primary cell-method comparisons (three proved nontrivial methods
in A–E, two MOM methods in F), the future undercoverage diagnostic is
P_{Bin(n,.95)}(X<=observed successes), testing H0: coverage>=.95 against lower
coverage. Holm step-down controls the 17-test family at .05. The range and point
baselines are excluded from that confirmatory family. 90% diagnostics are
secondary and do not inherit a joint confirmatory FWER guarantee. A missing or
unissued comparison is not dropped to shrink multiplicity. Failure to reject
does not prove coverage; the theorem does. Preflight displays the same
arithmetic as a debugging diagnostic only.

Additional metrics: median/IQR/p90 raw and clipped width divided by known
target diameter; family-any, family-all and marginal nontriviality; signed error,
absolute error, RMSE and |error|/radius; subgroup mass; exact q/e quantiles;
N, chi, N_eff, B, K, L_min and feasibility; p, scale source and analytic noise
moment; statuses, assumptions and refusal reasons; actual wall/CPU time and
process peak RSS. Observed score moments or tail quantiles are diagnostics only.
The exact centered score moment need not be available: a rigorous declared
envelope is reported without relabeling it as the true moment.

The fixed diagnostic constraint is M_D<=.2*pi_h. A simultaneous upper bound
below the threshold certifies safe; a lower bound strictly above certifies a
violation; otherwise abstain. False-safe, false-violation and planted-gap power
are distinguished. These preflight decisions test bookkeeping at this one
fixed threshold; they do not implement or replace the later C.2 gap sweep,
C.3 discovery or C.4 policy-repair experiment. No data-driven threshold tuning.

## Phase decision and deferred work

C-PREFLIGHT passes only with all 377 baseline tests preserved, new deterministic
oracle/theorem/status tests passing, positive primary support, a known valid
F envelope, a frozen manifest, and an actual successful checkpoint resume.
Any code/proof inconsistency blocks C-STAT regardless of observed coverage.
A preflight PASS only permits planning/executing the separately authorized
next stage; this run stops before any confirmatory log is generated.

No paper edits, real datasets, GPU jobs, secondary grids, discovery/repair
campaign, optional Bernstein or adaptive-martingale theory are part of this
phase. Fully adaptive histories, mutual cross-fitting, unknown scales, hidden
shared shocks and long-run deployment remain outside the certificate scope.

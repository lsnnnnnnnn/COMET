# Post-C-STAT novelty and strong-baseline source audit

Read date: 2026-11-14 (Asia/Shanghai). New research branch:
`codex/query-specific-graph-auditing`. This audit reads actual public source
text; it does not rerun E0 or constitute an experimental result. The supplied
override and master goal were read, followed by the subsequently supplied
`SCOPE_CN.md`, `THEORY_NOTE.md`, and `CLAIM_EVIDENCE.csv` in
`task_materials/post_cstat/`. `EXPERIMENT_BLUEPRINT.json` remains unavailable;
the user authorized continuation without the missing input. Its contents are
not represented as read. Protocol choices must be recorded from the actual
available instructions rather than attributed to an unseen blueprint.

## Primary source map

| Source | Text actually inspected | Valid comparison domain | Consequence for COMET |
|---|---|---|---|
| Svante Janson (2004), *Large deviations for sums of partly dependent random variables*, Random Structures & Algorithms 24(3):234–248, DOI 10.1002/rsa.20008 | [Publisher metadata](https://onlinelibrary.wiley.com/doi/10.1002/rsa.20008); [author preprint](https://api.newton.ac.uk/website/v0/events/preprints/NI02024), Section 2, Theorem 2.1; Section 3 | Bounded summands with a justified independent-set cover; heterogeneous ranges and means are permitted. Any verified proper coloring supplies an integral cover. | Graph-coloring concentration is established machinery. Neither using a coloring nor applying a finite-family union bound alone establishes a new estimator. A computed coloring count need not be the chromatic number. |
| Sujay Bhatt, Guanhua Fang, Ping Li, Gennady Samorodnitsky (2022), *Nearly Optimal Catoni’s M-estimator for Infinite Variance*, ICML, PMLR 162:1925–1944 | [Publisher record](https://proceedings.mlr.press/v162/bhatt22b.html); [paper](https://proceedings.mlr.press/v162/bhatt22b/bhatt22b.pdf), paper p.4, Lemma 3.1, Theorem 3.2, equations (3)–(5) | I.i.d. observations, common mean and known upper bound on the centered p-moment, 1<p≤2. The theorem has an explicit sample-size condition. | Implement on a genuinely homogeneous independent anchor. Independent heterogeneous rows do not satisfy the stated i.i.d. theorem. A raw moment cannot silently replace a centered-moment upper bound. |
| Nikos Karampatziakis, Paul Mineiro, Aaditya Ramdas (2021), *Off-Policy Confidence Sequences*, ICML, PMLR 139:5301–5310 | [Publisher record](https://proceedings.mlr.press/v139/karampatziakis21a.html); [paper](https://proceedings.mlr.press/v139/karampatziakis21a/karampatziakis21a.pdf), Theorems 1–3 and Algorithms 1–2 | Bounded rewards and importance weights, appropriate target conditional moments and predictable nonnegative betting factors; original contextual-bandit target V(π). | Use a matched bounded homogeneous independent anchor at the same horizon/error budget. Its time-uniform guarantee is stronger than a fixed-window guarantee. Do not port the martingale to arbitrary graph-dependent row order or heterogeneous fixed-design average without another proof. |
| Ian Waudby-Smith, Lili Wu, Aaditya Ramdas, Nikos Karampatziakis, Paul Mineiro, *Anytime-valid off-policy inference for contextual bandits*, arXiv:2210.10768v3 (15 August 2024; initial preprint 2022) | [Version metadata](https://arxiv.org/abs/2210.10768); [actual text](https://arxiv.org/html/2210.10768), Theorem 2, equations (10)–(11), (24)–(28), Appendix A.3; §3.1 | Bounded rewards, supported exact logging, predictable fits, and the source filtration contract; Theorem 2 allows changing conditional means. | Implemented DR/EB on independent fixed-design rows, including heterogeneous means. Graph dependence needs another target/filtration argument. Direct policy differences are prior work. The publisher endpoint returned 403; this record cites the verified arXiv version rather than inventing journal metadata. |
| Minkyoung Kim, Hyunjung Byun, Beakcheol Jang (2026), *Bias-Aware Guardrail Selection Under Network Interference* (ESGuard), arXiv:2610.36702v1, 27 October 2026 | [Actual full HTML](https://arxiv.org/html/2610.36702v1), Sections 4.2–4.4, equations (4)–(8), Theorem 1 | Randomized rounds; correct exposure mapping; valid curvature/slope bounds; independent rounds plus covariance, kurtosis and non-dominance regularity for selection guarantee | Finite-sample smoothing-bias bound and asymptotic unsafe-selection control are distinct. Training-fitted derivative rules are not automatically true derivative envelopes. This is an interference/smoothing comparator, not a directly eligible finite-sample p-moment graph certificate. No dominance claim follows from the differing assumptions. |

The listed primary sources were located and inspected. No unavailable recent
paper is being inferred from its title. This is a source/applicability audit,
not a claim of exhaustive novelty search.

## Implemented finite-moment Catoni anchor

The following is a compact transcription of Bhatt et al. Theorem 3.2. Set
ε=p−1 and use the convention 0^0=1 at ε=1:

```
C = (ε/(1+ε))^((1+ε)/2) ((1−ε)/ε)^((1−ε)/2)
ψ(x) = sign(x) log(1+abs(x)+C abs(x)^p)
a = ε^(1/p) (h^(−ε) C v)^(-1/p) (log(2/δ)/n)^(1/p)
sum_i ψ(a (X_i−estimate)) = 0
r = (1+τ) sqrt(1+ε) (1−ε)^(1/p−1/2)
    (h^(−ε) v)^(1/p) (log(2/δ)/n)^(ε/p)
n >= (1−h)^(-1) ((1+ε)/ε) (1+τ)^(p/ε)
     τ^(−1/ε) C^(1/ε) log(2/δ)
```

Here τ>0, 0<h<1 and v bounds E|X−EX|^p. Check the sample-size condition
before producing this radius. The monotone estimating equation permits a
deterministic bracket/root solve. The source permits an influence function
between its two logarithmic envelopes; the displayed odd function is one
such choice. `comet/independent_anchors.py::catoni_iid` implements this formula,
including the sample-size gate and a deterministic Brent root solve. The
reported radius includes the declared root-solver error debit. This is an
ordinary-floating implementation, not an outward-rounded machine proof.

## OPE implementation reference

The public [author repository](https://github.com/n17s/mope) contains
[`opebet.py`](https://raw.githubusercontent.com/n17s/mope/main/opebet.py)
and [`opebetrp.py`](https://raw.githubusercontent.com/n17s/mope/main/opebetrp.py).
Its [MIT license](https://raw.githubusercontent.com/n17s/mope/main/LICENSE)
allows reuse with the copyright and permission notice retained. The code
contains one-dimensional betting, two-dimensional optimization, and reward
prediction variants. The paper's basic process is

```
K_t(v) = product_i [1 + lambda1_i (w_i−1)
                       + lambda2_i (w_i r_i−v)] .
```

The bets must be predictable and make every factor nonnegative on the legal
support. Inverting K_t(v)≤1/δ gives the stated confidence sequence. Algorithm 2
uses quadratic lower bounds and constrained bets; calling an arbitrary Wald
interval “MOPE” would not implement it. The implemented anchor uses the
eligible bounded support and is checked against the selected author-code path;
its label identifies the one-dimensional instance.
`comet/independent_anchors.py::ope_betting_iid` adapts the author's one-dimensional
`wealth_lb_1d` path with its MIT notice retained. It uses stable quadratic roots
and a predeclared root padding; it preserves empty confidence intersections
instead of cross-clamping the two sides. It is explicitly named an author
one-dimensional betting instance, not a reproduction of the full
two-dimensional MOPE algorithm. Both engines refuse an absent i.i.d. declaration.

Implementation checks: `.venv/bin/python -m pytest -q tests/test_independent_anchors.py`
finished with **13 passed**. Checks include deterministic finite IID-Bernoulli
enumeration and agreement with transparent author-code arithmetic on a fixed
fixture; no Monte Carlo sample was generated. The first run had **1 failed,
10 passed**: a stable quadratic adaptation chose the lower root, making a
constant-response interval uninformative. Selecting the upper root for its
concave quadratic corrected the implementation; the next run had 11 passed,
and the final expanded arithmetic/numerical checks had 13 passed. This is a
preserved implementation failure, not a failed scientific trial.

## Implemented 2024 DR/empirical-Bernstein anchor

`comet/ope_2024.py::ope_eb_independent` implements the source's Theorem 2:
statewise truncated predictors retain unbiased DR pseudo-outcomes; mirrored
streams spend δ/(2m) each. A past-only predictor supplies the variance process,
and the gamma-mixture boundary is inverted at the requested horizon. Independent
heterogeneous rows identify the average fixed-design value. Past confidence
intervals are not intersected when their targets differ. Ordinary floating
arithmetic has a declared numerical debit. Ten deterministic tests passed,
including gamma/Kummer/integral agreement; no Monte Carlo was run by this audit.
The 2021 scalar-betting path remains a separate comparator.

## Matched-information baseline contract and equality

These are workstream-specific derivations/implementation requirements, rather
than claims imported from a paper:

1. All eligible engines receive the same signed query coefficients d, exact e,
   nuisance, response class, source graph, query support and total family error
   budget. For bounded Y∈[L,U], the residual magnitude envelope is
   max(|L−muhat|,|U−muhat|), including 1/2 for midpoint fits on [0,1].
2. Let R=d(S)(Y−muhat(S))/e(S). For actual row residual ranges [l_u,u_u],
   Janson's bounded-summand result yields the two-sided family radius
   `sqrt(chi*log(2m/delta)*sum_u (u_u-l_u)^2/2)/N`.
   A variance-sensitive graph Bernstein route must use a legal variance upper
   bound and actual centered range; neither oracle variance nor observed range
   is substituted for the declared bound.
3. A fully matched generic bias-corrected residual-truncated graph mean using
   the same R, thresholds, moments, coloring and union budget is algebraically
   the same estimator and radius as that COMET configuration. Test equality;
   report identical performance as equality, not a win against a new method.
4. Global-envelope/global-coloring and local-moment/global-coloring variants
   are component ablations. They do not establish superiority over a fully
   informed query-local comparator.
5. Colorwise truncation may independently bound each color sum with an explicit
   failure split, then sum the bounds and divide by the original N. Retain all
   color weights and heterogeneous targets. Independence between color sums
   is unnecessary for this union argument and must not be assumed.
6. A level-difference comparator must jointly cover both levels with the same
   total budget spent by a direct contrast. A contrast-aware generic engine
   receives the signed difference directly. When d is multiplied by η>0 and
   thresholds scale by η, estimate, target and all radius terms scale by η;
   a small update has no automatic sign-certification advantage.

Any remaining contribution must be supported as target-specific formulation,
analysis, evidence-cost characterization or decision workflow. Universal
new-estimator superiority is not established by these standard components.

## E6 data source readiness (metadata only)

The single default candidate is California 2018 ACS one-year person PUMS.
The [official directory](https://www2.census.gov/programs-surveys/acs/data/pums/2018/1-Year/)
lists [`csv_pca.zip`](https://www2.census.gov/programs-surveys/acs/data/pums/2018/1-Year/csv_pca.zip)
at **64M** (directory-rounded size, not an exact byte count). This is below the
512 MiB compressed allowance. The archive was not downloaded by this audit;
download success, exact hash and usable row count remain unverified.

The [Folktables task source](https://raw.githubusercontent.com/socialfoundations/folktables/main/folktables/acs.py)
defines ACSIncome using PINCP>50,000, after AGEP>16, PINCP>100, WKHP>0 and
PWGTP≥1 filtering; its ten features are AGEP, COW, SCHL, MAR, OCCP, POBP,
RELP, WKHP, SEX and RAC1P. The
[datasheet](https://raw.githubusercontent.com/socialfoundations/folktables/main/datasheet.md)
separates the MIT-licensed loading code from Census-governed data terms and
warns against re-identification and substantive conclusions from a benchmark.
The referenced [Census terms](https://www.census.gov/data/developers/about/terms-of-service.html)
were inspected; they prohibit identifying respondents and require accurate
attribution/no implied endorsement for API-based products. The
[Census open-data page](https://www.census.gov/topics/research/research-transparency-public-access/open-data.html)
describes public data access. This is a provenance record, not legal advice.

E6 should freeze its actual finite population and disjoint splits before
pipeline randomness. Fixed labels and synthetic logging identify a
finite-population policy-weighted outcome, not the causal effect of selection
on income. A source-correlated logger needs its own proven graph. Dataset
access failure should be recorded as DATA_BLOCKED while synthetic/theory work
continues; no silent alternate dataset is selected here.

# Two neighboring selection results: primary-source check

This bounded check covers two papers only. It adds no experiments or changes
to frozen parameters, and is not an exhaustive state-of-the-art assessment.

## Learn then Test

Angelopoulos, Bates, Candès, Jordan and Lei; published in *The Annals of Applied
Statistics* **19**(2):1641–1662 (2025), DOI
[10.1214/24-AOAS1998](https://doi.org/10.1214/24-AOAS1998).
Publication metadata is corroborated by the
[IMS issue record](https://www.imstat.org/publications/aoas/aoas_19_2/aoas_19_2.pdf)
and [author's institutional record](https://www.gsb.stanford.edu/faculty-research/publications/learn-then-test-calibrating-predictive-algorithms-achieve-risk).
The publisher PDF timed out; theorem inspection used
[arXiv:2110.01052v5](https://arxiv.org/pdf/2110.01052v5), revised 29 September
2022, whose title page says 3 October 2022. Versions are not conflated.

Section 1.1 specifies i.i.d. calibration observations for a pretrained predictor.
Theorem 1 derives simultaneous risk control of the returned set from valid
null p-values and FWER control. Those p-values need not be mutually independent.
Proposition 6 treats multiple risks; Proposition 7 already derives selection
from uniform upper bounds. Appendix D learns a testing order on an extra split
before fresh testing. Its testing graph is not a score-dependency graph.
The generic selection reduction is relevant here; its i.i.d. calibration bounds
are not automatically valid on heterogeneous graph-dependent rows.

## High Confidence Policy Improvement

Thomas, Theocharous and Ghavamzadeh; ICML 2015, PMLR **37**:2380–2388,
verified on the [publisher page](https://proceedings.mlr.press/v37/thomas15.html).
Actual text: [author-hosted conference PDF](https://people.cs.umass.edu/~pthomas/papers/Thomas2015b.pdf).

Section 2.2 uses independent importance-weighted trajectory returns with a
common expectation in an MDP/POMDP model; the concentration branch in Section
2.3 requires nonnegative variables. Section 4 and Algorithm 4 search using
training data, then test one candidate on held-out data, returning a policy or
abstaining. Section 3 controls proposing a below-threshold policy; it does not
guarantee frequent improvement. The paper distinguishes its finite-sample
concentration branch from the explicitly semi-safe t-test/bootstrap branches.
These assumptions do not establish our global conditional-graph model.
The [author's 2017 erratum](https://people.cs.umass.edu/~pthomas/papers/Thomas2015bErrata.pdf)
corrects the incremental k-test union bound to `min(1,k*delta)`; it is not `2*delta`.

## Suggested related-work paragraph

```latex
Independent construction followed by risk-controlled selection is established.
Learn then Test turns valid tests into risk control of a returned
set~\cite{angelopoulos2025ltt}, and high-confidence policy improvement separates
candidate search from a held-out safety test~\cite{thomas2015hcpi}.
We use this selection logic rather than claim it as new. Our analysis concerns
heterogeneous fixed-design signed moments, valid residual envelopes and a
sufficient global conditional graph, with query-specific evidence costs,
paired contrasts and a scoped thinning lower bound. Fully matched generic
graph truncation is identical; the experiments therefore assess detection
and useful-return limits rather than separate estimator superiority.
```

## Concise bibliography entries

```latex
\bibitem{angelopoulos2025ltt}
A. N. Angelopoulos, S. Bates, E. J. Cand\`es, M. I. Jordan, and L. Lei.
Learn then test: Calibrating predictive algorithms to achieve risk control.
\emph{The Annals of Applied Statistics}, 19(2):1641--1662, 2025.
\href{https://doi.org/10.1214/24-AOAS1998}{doi:10.1214/24-AOAS1998}.

\bibitem{thomas2015hcpi}
P. Thomas, G. Theocharous, and M. Ghavamzadeh.
High Confidence Policy Improvement.
In \emph{Proceedings of ICML}, PMLR 37:2380--2388, 2015.
\href{https://proceedings.mlr.press/v37/thomas15.html}{Publisher record}.
```

No implementation or new baseline outcome is claimed for either neighboring
procedure by this check.

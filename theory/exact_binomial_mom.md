# Gate C0: exact binomial majority control for the existing MOM theorem

Status: **proved under the same independent-exogenous-block, stable-target
model as Gate A**. This changes the sufficient choice of group count, not the
estimand, identification assumptions, graph sufficiency, moment assumption or
nuisance-learning requirements. It does not establish arbitrary adaptive-path
or mutual-cross-fit validity.

Baseline source references below are to `d11a36f`. The old rule is
`comet/robust_mean.py:21–26`, complete-block partition is at lines 29–38,
median convention is at lines 41–45, and the radius is at lines 48–53.
`comet/certification.py:79–93` verifies the registered model and sets the
partition, while lines 105–109 construct the known envelope and radius.
`comet/dr_scores.py:40–52` computes the bounded-reward envelope. The complete
Gate A theorem and proof are in `paper/sections/gate_a_certificate.tex` and
`theory/theorem_to_code_contract.md`. All previous results remain unchanged.

## Conditional model and group-moment bound

Let D contain only an exogenous design fixed before evaluation randomness and,
optionally, a nuisance pilot independent of all evaluation blocks conditional
on the exogenous design. A finite family Theta, of size m, is frozen given D.
All probabilities and moments below are conditional on D. No conditioning on
future outcome-derived contexts or the collection of mutually trained fits is
permitted merely to assert independence.

There are B independent evaluation macro-blocks, each with n0 retained rows.
Within block b a sufficient conditional dependency graph has a proper coloring
with at most chi colors. In particular, each color class consists of mutually
independent variables; uncorrelatedness or pairwise independence is insufficient.
The score Z_bi(theta), computed with a fixed permissible nuisance and exact e,
has conditional mean m_bi(theta). Require a common block target

    (1/n0) sum_i m_bi(theta) = M_D(theta)  for every b,

and known finite, D-measurable envelopes

    E[|Z_bi(theta)-m_bi(theta)|^p | D] <= nu_theta^p,   1<p<=2.

For X_bi=Z_bi-m_bi, the conditional von Bahr–Esseen inequality with constant
at most 2 applies inside each independent color class. Deterministic convexity
across the at most chi color sums yields

    E[|bar Z_b(theta)-M_D(theta)|^p | D]
      <= 2 nu_theta^p (chi/n0)^(p-1).

Partition all complete blocks deterministically into K disjoint groups. If group
g contains L_g blocks, their conditional independence and a second use of the
same inequality give

    E[|T_g(theta)-M_D(theta)|^p | D]
      <= 4 nu_theta^p (chi/(L_g n0))^(p-1).

This establishes A_p=4 for precisely this model; it is not an estimated tuning
constant. Use the existing balanced partition, with
L_g in {floor(B/K),ceil(B/K)} and L_min=floor(B/K). Every group target remains
M_D because the block targets are equal, even though the group sizes differ.
All blocks and rows are retained. Enforce B>=2K, preserving Gate A's
L_min>=2 feasibility requirement. The grouping is chosen before outcomes.

## Lemma: independent Bernoulli domination

Fix theta and let eta satisfy 0<eta<1/2. Set

    a_theta = (4/eta)^(1/p) nu_theta
              (chi/(L_min n0))^((p-1)/p).

If nu_theta=0, every centered row score vanishes almost surely and the result is
immediate. Otherwise Markov's inequality and the preceding moment bound imply

    P(|T_g(theta)-M_D(theta)| > a_theta | D) <= eta.

Write I_g for the indicated failure. Conditional on D, the I_g are independent
because each is a measurable function of a disjoint collection of independent
macro-blocks and of fixed design information. Different L_g may produce
different failure probabilities p_g; identical distributions are not required.

To prove stochastic domination, introduce independent uniforms U_g on an
auxiliary probability space conditional on D. The vector
I'_g=1{U_g<=p_g} has the same conditional joint law as I_g. Since p_g<=eta,
I'_g<=J_g=1{U_g<=eta} pointwise. Thus, for every integer k,

    P(sum_g I_g >= k | D) <= P(Bin(K,eta) >= k).

This is a comparison of conditional laws, not an assumption that actual score
failures can be inferred from their sample realizations. Neither the exact
unknown p_g nor the true target is used by the implementation.

## Exact-majority theorem

For odd K, use the unique middle order statistic as the median. If at most
(K-1)/2 groups are bad, at least (K+1)/2 group estimates lie in
[M_D-a_theta,M_D+a_theta]; the median must be in that interval. Therefore

    P(|MOM(theta)-M_D(theta)| > a_theta | D)
      <= t(K,eta)
      := sum_{j=(K+1)/2}^K choose(K,j) eta^j (1-eta)^(K-j).

Union bounding over the frozen family, without requiring independence between
candidates, proves

    P(exists theta: |MOM(theta)-M_D(theta)| > a_theta | D)
      <= m t(K,eta).

Choose the smallest odd K satisfying both B>=2K and
m t(K,eta)<=delta_stat. If there is none, return `NOT_CERTIFIABLE` rather than
weakening the requested confidence level. Then all reported intervals are
simultaneously valid with conditional probability at least 1-delta_stat.
Integrating over a legitimate random D gives the corresponding unconditional
coverage. The implemented independent model has epsilon_coup=0 and no nuisance
or drift radius; a different model would need its own justified budgets.

For completeness, the old even-K median is the average of the two middle
order statistics. Fewer than K/2 bad groups suffice to keep both central order
statistics in the interval. Hence its failure is contained in
{sum I_g>=K/2}; the threshold ceil(K/2) is valid but conservative for even K.
The new exact selector restricts to odd K so this distinction cannot be hidden.
The existing conservative rule and even-median convention remain unchanged.

## Exact arithmetic and fixed-eta implementation

The first C0 comparison fixes eta=1/8. Then a_theta is exactly the same
theoretical `32^(1/p)` expression as before; only K and thus L_min change.
The selector evaluates t(K,eta) with rational arithmetic, not a floating-point
approximation to a tiny tail. For eta=r/s,

    t(K,r/s) = [sum_{j=ceil(K/2)}^K choose(K,j) r^j(s-r)^(K-j)] / s^K.

Python integers and `fractions.Fraction` represent this exactly. Decimal input
probabilities are interpreted through their printed decimal value; callers can
pass a Fraction to specify an exact rational directly. The decision compares
the exact rational m*t to the exact rational delta. The reported float tail is
rounded upward when nearest floating-point conversion would round below the
exact value. Numerator and denominator strings are also recorded, so the
comparison can be audited independently and underflow cannot create a false
successful confidence check. These numerical precautions concern the binomial
tail selection; ordinary floating-point score/radius arithmetic is retained
from Gate A and rejects nonfinite values.

Hand-check fixture: with m=16, delta=.05, eta=1/8, the old rule chooses
ceil(8 log(640))=52. The exact rule chooses K=9; K=7 does not meet the budget.
Explicitly, `t(9,1/8)=166583/67108864`, so the familywise bound is
`0.039716482162475586`; `16*t(7,1/8)=3271/32768=0.099822998046875`.
At B=128, balanced grouping changes L_min from 2 to 14. Thus the radius ratio
new/old is `(2/14)^((p-1)/p)`, independent of nu, chi and n0. At p=2 it is
1/sqrt(7); at p=1.5 it is 7^(-1/3). This improvement does not guarantee that an
otherwise enormous envelope becomes useful.

For the original m=4 smoke design, the exact selector is applied with its actual
family size, not the m=16 illustration. `reports/gate_C0_report.md` reports the
resulting K/radius alongside the preserved original outputs. The forensic
report describes the original certificates; the separate design-only budget
grid uses m=1 and m=16.

## Scope of deterministic selection and deferred optimization

Selecting K by this rule costs no further union bound: conditional on D, the
inputs m, delta, eta and B and hence the selected K and partition are already
fixed, and the proof applies to that selected construction. The same argument
would justify a *predeclared deterministic* optimization over eta and odd K
using only known D-measurable p, nu, chi, B and n0, if each selected pair satisfies
its exact confidence budget. A deterministic tie-breaking rule is needed.
This would select a valid conditional theorem, not select from observed
coverage. It is not implemented or tuned in the first fixed-eta C0 comparison.

Outcome-driven K/eta selection, oracle-truth tuning, choosing a preferred
method after examining coverage, or adapting the family after evaluation do not
inherit this argument. They require an independent pilot or an explicit
simultaneous guarantee across the considered procedures. Even a design-only
choice is invalid if D contains future evaluation information and no longer
supports the conditional independence and centering statements above.

For varying block means, balanced groups may have different target means.
An exact binomial count cannot repair that miscentering. Gate A's registered
stable DGP remains mandatory for this MOM implementation; any varying-target
extension needs a proved group drift bound or a different estimator.

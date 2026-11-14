# Query-specific evidence cost: a scoped observation-thinning lower bound

Status: independently proved two-point result for an explicit clique-replicated
subclass of the new global conditional-graph model. It is not a theorem for each
sparse graph, not a simultaneous-confidence logarithmic optimum, and not a
claim about the fixed Pareto DGP used in an experiment. The unavailable
`THEORY_NOTE.md` was not read; equivalence to its proposed construction is unknown.

## 1. Observable experiment and parameter regime

Fix total row count N, subgroup mass pi with g=N*pi a positive integer, clique
size chi dividing g, and n=g/chi subgroup cliques. Let epsilon in (0,1] be the
known rare exposure probability, p>1, a residual p-norm bound nu>0, and a
conditional-mean deviation cap B>0. All are fixed design quantities. Outside
the subgroup all distributions agree and may be deterministic. Their data
provide no information about the sign parameter below.

For each independent clique j, independently draw logging exposure
A_j~Bernoulli(epsilon) and a latent spike indicator V_j~Bernoulli(t). Copy these
variables within the chi rows of that clique. Potential responses are

    Y_j(0)=b,
    Y_j(1)=b+sigma*a*V_j,    sigma in {-1,+1}.

A and V are independent. Observe A_j and Y_j(A_j), equivalently the copied row
observations. The logger's full joint law is explicit: independent Bernoulli
clique assignments. The target joint policy puts action 1 on subgroup rows,
so it is compatible. Use known nuisance b. A sufficient graph is the disjoint
union of subgroup cliques, with chi colors. The observed clique copies are not
independent observations; there are n independent primitive units.

Let

    t = min(1, 1/(2*n*epsilon)),
    a = min(B/t, nu*t^(-1/p)),
    d = a*t = min(B, nu*t^((p-1)/p)).

Then the action-1 mean is b+sigma*d and the known residual moment satisfies

    E|Y(1)-b|^p = a^p*t <= nu^p.

If means must belong to [0,1], choose b=.5 and B<=.5. Outcomes need not be
bounded: rare spike amplitudes a can exceed B, while the conditional means
remain in the declared location class. This is the finite-moment subclass.
For a bounded-outcome lower bound one would need a separate amplitude cap and
would obtain a different regime. No bounded-response rate is inferred here.

The normalized subgroup target is theta_sigma=b+sigma*d. The raw moment is
pi*theta_sigma. The IPW raw-residual envelope is exactly bounded by
`epsilon^(1-p)*nu^p`; the exposure probability is known, not estimated.
The choice of t depends on sample size, as is permitted for a minimax subclass.
It is not a fixed-DGP asymptotic power prediction.

## 2. Observable total variation and absolute risk

The two observable laws differ only if some clique has A_j=V_j=1. Under both
signs this event has probability

    TV(P_plus,P_minus) = 1-(1-epsilon*t)^n <= n*epsilon*t <= 1/2.

On its complement the joint observable distributions, including the exposed
assignment pattern, have identical densities; the positive and negative spike
events have disjoint values. Let an arbitrary measurable estimator T have risks
R_plus=E_plus|T-theta_plus| and R_minus=E_minus|T-theta_minus|. Integrating over
the common part of the two probability measures and using the triangle
inequality gives

    R_plus+R_minus >= 2*d*(1-TV),
    max(R_plus,R_minus) >= d*(1-TV) >= d/2.

Thus

    inf_T sup_{sigma} E_sigma|T-theta_sigma|
      >= (1/2) min{B, nu*min(1,(1/(2*n*epsilon))^((p-1)/p))}.

For a raw subgroup moment multiply this expression by pi. In the unsaturated
regime, the normalized scale is

    nu * (chi/(N*pi*epsilon))^((p-1)/p),

up to the explicit factor `2^(-1-(p-1)/p)`. The corresponding raw scale is
`nu*pi^(1/p)*(chi/(N*epsilon))^((p-1)/p)`, with the same constant. In low effective
sample or tightly bounded-mean regimes the displayed minimum records
saturation rather than extrapolating an unbounded error rate.

All integer and observational requirements matter: g=N*pi must be integral,
chi must divide g, and the independent units are cliques, not N separate rows.
This subclass lies inside a model allowing heterogeneous connected graphs, but
does not prove sharpness for an arbitrary given connected graph. Outside rows
can have heterogeneous fixed means without changing the lower-bound argument.

## 3. A non-sharp confidence-width consequence

Suppose an interval I has coverage at least 1-alpha under each sign. Change of
measure and a union bound under P_plus imply

    P_plus(theta_plus and theta_minus both belong to I)
      >= 1-2*alpha-TV >= 1/2-2*alpha.

Therefore under P_plus the interval has diameter at least 2d with probability
at least max(0,1/2-2alpha). The same conclusion holds symmetrically. This is a
simple two-point obstruction, not a sharp high-confidence theorem and not a
matching log(m/delta) lower bound. It includes no claim of exact optimality for
every sparse graph or every procedure.

## 4. Sufficient decision boundary and analytic budgets

For an upper-risk threshold a0, let M=a0+gamma and suppose a certificate has
symmetric radius r and a coverage event |Mhat-M|<=r. If gamma>2r then

    Mhat-r >= M-2r > a0,

so the certificate reports a true violation on that event. A negative gap
with -gamma>2r similarly certifies safety by its upper endpoint. Gamma>r alone
does not imply this: on the allowed event Mhat=M-r the lower endpoint is M-2r.
This is the sufficient nominal-power argument used by analytic radius maps.
It is not a necessary information bound, and it is not measured power.

For a one-threshold finite-moment certificate, v includes the actual support,
weights, exposure and residual scale. The graph Bernstein trade-off balances
bias decreasing as tau^(1-p) against square-root and linear range terms growing
with tau. In the homogeneous schematic `sum v=N*vbar`, choosing
`tau` of order `(N*vbar/(chi*log(2/delta_theta)))^(1/p)` gives scale

    vbar^(1/p) * (chi*log(2/delta_theta)/N)^((p-1)/p),

up to constants and the exact chosen threshold grid. This is only a descriptive
order calculation; executable budgets must evaluate the **complete** explicit
radius and normalizer, including the bias and range terms. Query-specific
support and v change this cost, and a deteriorating propensity schedule can
prevent it from shrinking.

For the subgroup subclass, normalized evidence cost depends on N*pi*epsilon/chi.
In the unsaturated regime a necessary expected-risk scale no larger than a
specified target eta requires this effective count to grow at least on the
order `(nu/eta)^(p/(p-1))`. A procedure-specific sufficient certificate budget
usually adds its own confidence/family logarithms and constants. Do not label
the sufficient budget information-theoretically necessary or claim matching
logarithms from the two-point result.

Analytic maps, including declining epsilon_N, draw no outcomes. Fixed-grid
Monte Carlo rate studies sample different designs and remain descriptive. The
ideal sampler's Pareto exponent controls existence of moments; it is different
from the legal p supplied to a procedure. Every p used in a finite-moment
certificate must be strictly below the declared Pareto exponent, with a known
finite envelope. Machine finite-grid tails are not literally infinite-variance
random variables.

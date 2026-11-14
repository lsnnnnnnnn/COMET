# Optional predictable fixed-horizon extension: proof status

**Status: DERIVED_NOT_IMPLEMENTED.** The fixed-horizon result below has a complete
conditional-MGF proof. There is no implementation, numerical validation or new
Monte Carlo evidence for this extension. It is not part of the main fixed-design
claim or its experimental protocol, and it does not delay the heterogeneous
fixed-design core. No historical C-STAT computation was changed or repeated.

This memo proves a statement about a **realized predictable conditional-mean
sum**. It does not turn that random target into the fixed-design `M_D` of the
main paper, a retrospective value of a final fitted policy on all earlier data,
or a guarantee for future policy deployment.

## 1. Filtration and fixed horizon

Fix a deterministic horizon T and a filtration

    F_0 subset F_1 subset ... subset F_T.

F_{t-1} contains the complete information genuinely available before round t:
previous rounds, exogenous current contexts revealed before that round, and
permitted independent training/discovery information. All row counts N_t,
response channels, coefficients d[t,u,s,theta], offsets f[t,u,theta], nuisance
fits muhat[t,u,s,theta], exact exposure probabilities e[t,u,s], source graphs,
thresholds tau[t,u,theta] and moment envelopes are F_{t-1}-measurable. A fit may
use the past; it cannot use outcomes of its own or a future round.

There are finitely many coordinate labels theta in a family Theta fixed at
F_0. The algorithm producing each coordinate's subsequent predictable queries
is also specified at F_0. A label may describe an updating query sequence, but
its inferential target is the cumulative sequence actually used before each
round. A policy chosen at time T cannot be retroactively substituted into the
coefficients of rounds 1,...,T.

All guarantees below condition on F_0. The horizon, confidence allocations and
budget bounds called deterministic may equivalently be fixed F_0-measurable
quantities. For simplicity the moment order p is fixed in (1,2].

## 2. Roundwise identification and conditional graph assumptions

For each supported exposure define the pre-round conditional mean

    mu[t,u,s,theta]
      = E[Y[t,u,theta] | S[t,u]=s, F_{t-1}].

A counterfactual interpretation requires the full roundwise exposure
sufficiency/assignment identity, not merely an array named propensity. Every
nonzero d requires exact e>0. Define the observable raw residual

    R[t,u,theta]
      = d[t,u,S[t,u],theta]/e[t,u,S[t,u]]
        * (Y[t,u,theta]-muhat[t,u,S[t,u],theta]).

The model must supply **pathwise legal conditional raw moments**:

    E[|Y[t,u,theta]-muhat[t,u,s,theta]|^p
      | S[t,u]=s,F_{t-1}] <= b[t,u,s,theta]^p

almost surely on every permitted history. Thus

    v[t,u,theta]
      = sum_s |d[t,u,s,theta]|^p e[t,u,s]^(1-p)
                                            b[t,u,s,theta]^p

bounds E[|R[t,u,theta]|^p | F_{t-1}]. A fitted past-only nuisance does not,
by itself, prove the supplied future residual moment bound. A conditional scale
may depend on the past only when the declared probability model justifies that
bound on every history; an unverified empirical tail-scale estimate is not
sufficient.

Given F_{t-1}, the whole row residual vector in round t has a sufficient strong
dependency graph. Use its design-active induced graph and a verified proper
coloring count chi[t,theta]. All source dependencies of that round, including
logging and every retained channel, must be included. Independent fresh
primitive sources conditional on the past are one sufficient construction.
The theorem does not infer conditional independence from an unchanged graph
label when persistent shared latent randomness is present.

No independence between rounds is assumed. Their effects are represented by
the filtration and the conditional assumptions above.

## 3. Target and observable estimator

Let Bstar[theta]>0 be a deterministic normalizer, and put

    K[t,theta] = sum_{u,s} d[t,u,s,theta]*muhat[t,u,s,theta]
                - sum_u f[t,u,theta].

This is a known pre-round numerator. The target is

    Mpred[T,theta]
      = 1/Bstar[theta] * sum_{t=1}^T
          (K[t,theta] + sum_u E[R[t,u,theta] | F_{t-1}])
      = 1/Bstar[theta] * sum_{t=1}^T
          (sum_{u,s}d[t,u,s,theta]*mu[t,u,s,theta]
           - sum_u f[t,u,theta]).

Both equality and the residual moment formula follow by finite enumeration
over each conditional exposure law. The target is generally random because
its conditional means and policies may depend on realized past data.

For clip_tau(x)=sign(x)*min(|x|,tau), the estimator is

    Mhat[T,theta]
      = 1/Bstar[theta] * sum_{t=1}^T
          (K[t,theta] + sum_u clip_tau[t,u,theta](R[t,u,theta])).

The implementation would use only observable residuals and known direct terms.
Unknown conditional expectations below are proof variables, not inputs.

## 4. Predictable bias and deterministic fluctuation budgets

With c_p=(p-1)^(p-1)/p^p, define pre-round bounds

    beta[t,theta] = c_p * sum_u v[t,u,theta]*tau[t,u,theta]^(1-p),
    V[t,theta] = chi[t,theta]
                 * sum_u v[t,u,theta]*tau[t,u,theta]^(2-p),
    c[t,theta] = (2/3)*chi[t,theta]*max_u tau[t,u,theta].

Zero-random-residual rounds contribute zero to all three bounds. The conditional
clipping bias in each round has absolute numerator at most beta[t,theta]. The
sum of these predictable quantities is an observable bound along the actual
path, not an estimate of its unknown signed bias.

Assume deterministic constants Vstar[theta]>=0 and cstar[theta]>=0 satisfy

    sum_{t=1}^T V[t,theta] <= Vstar[theta],
    max_{1<=t<=T} c[t,theta] <= cstar[theta]

almost surely on every permitted history. These must be established by the
protocol/model before outcomes. It is not valid simply to observe a small
realized sum V and substitute it for Vstar in a fixed-budget tail formula.
A random self-normalized replacement needs a separately proved boundary.
A deterministic beta-star bound may also be used, but is unnecessary because
the summed clipping bias bound is pathwise.

## 5. Conditional MGF proof

Write

    X[t,theta] = sum_u (clip_tau(R[t,u,theta])
                       - E[clip_tau(R[t,u,theta]) | F_{t-1}]).

Conditionally on F_{t-1}, each centered clipped row has variance at most
v*tau^(2-p) and absolute magnitude at most 2*tau. The proper-coloring/Hölder
calculation from the core proof is valid conditionally even with heterogeneous
conditional means. For |lambda|*cstar[theta]<1 it gives

    log E[exp(lambda*X[t,theta]) | F_{t-1}]
      <= lambda^2*V[t,theta]/(2*(1-c[t,theta]*|lambda|))
      <= lambda^2*V[t,theta]/(2*(1-cstar[theta]*|lambda|)).

For either sign of a fixed lambda define

    Z[k,theta] = exp(lambda*sum_{t<=k}X[t,theta]
       - lambda^2*sum_{t<=k}V[t,theta]
                         /(2*(1-cstar[theta]*|lambda|))).

Each V[t,theta] is predictable. The conditional MGF inequality and the tower
property show E[Z[k,theta] | F_{k-1}]<=Z[k-1,theta], with Z[0,theta]=1.
Therefore E[Z[T,theta] | F_0]<=1. The deterministic cumulative bound implies

    E[exp(lambda*sum_{t<=T}X[t,theta]) | F_0]
      <= exp(lambda^2*Vstar[theta]
                         /(2*(1-cstar[theta]*|lambda|))).

Applying Chernoff to both signs yields, for x>0,

    P(|sum_{t<=T}X[t,theta]|
       > sqrt(2*Vstar[theta]*x)+cstar[theta]*x | F_0)
       <= 2*exp(-x).

For Vstar>0 one may choose
lambda=sqrt(2*x/Vstar)/(1+cstar*sqrt(2*x/Vstar)); the degenerate Vstar=0 case
has zero centered increments almost surely. This proof is a fixed-T
consequence. Although a supermartingale is used in the derivation, this memo
does not state an optional-stopping or time-uniform theorem.

## 6. Fixed-horizon confidence statement

For coordinate error delta[theta], let x[theta]=log(2/delta[theta]). Then,
with conditional probability at least 1-delta[theta],

    |Mhat[T,theta]-Mpred[T,theta]|
       <= (sum_{t<=T} beta[t,theta]
           + sqrt(2*Vstar[theta]*x[theta])
           + cstar[theta]*x[theta]) / Bstar[theta].

The signed conditional clipping bias may vary with history; summing its
absolute bounds is what makes this conclusion valid. If deterministic budgets
beta-star are required, replace the sum of beta by an a.s. upper bound proved
in advance. For a finite family with sum_theta delta[theta]<=delta, a union
bound gives simultaneous fixed-horizon coverage. Selecting a coordinate label
after T is permitted on that simultaneous event for its own accumulated
predictable-sequence target. It does not identify a different final-query
retrospective target.

## 7. Why this is not the main fixed-design theorem

Take one Rademacher variable Z and set R[t]=Z in every round, with F_0 trivial
and F_t=sigma(Z) for t>=1. The unconditional mean of every R[t] is zero, yet
the observed average equals Z and never concentrates around zero. The
predictable conditional-mean average is ((T-1)/T)*Z, because the first
conditional mean is zero and all later conditional means equal the revealed
Z. The average's deviation from this different target is only Z/T.

This example shows why a valid predictable-mean theorem cannot be relabelled
as concentration around the unconditional mean, a fixed exogenous-design
moment, or a final policy's retrospective value. A sequential causal or
feedback interpretation additionally requires the corresponding conditional
identification model, not merely predictable notation.

## 8. Remaining obligations before any implementation or experiment

The result is mathematically derived, but no optional experiment is authorized
by this memo alone beyond the user's overall capped program. An implementation
would need its own explicit filtration/source model, full finite coordinate
family, a.s. deterministic cumulative budget derivations, exact conditional
exposures, pathwise valid residual moment envelopes, conservative numerical
rules and deterministic proof-to-code tests. It would need an isolated versioned
protocol and new IDs within the total resource cap. No such optional IDs have
been allocated or drawn here.

The main paper continues to concern heterogeneous exogenous fixed-design
moments. Optional adaptive wording, future safety, mutual evaluation-trained
cross-fitting, learned unknown graphs/scales and arbitrary stopping remain
outside its claims.

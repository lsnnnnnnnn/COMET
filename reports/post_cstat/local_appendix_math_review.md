# Local appendix mathematics review

Scope: only the added two-state i.i.d. anchor centered-moment argument,
the zero-exposure canceling contrast example, and the zero-support
nonidentification paragraph. The review read the corresponding sections of
`paper/post_cstat/sections/proofs.tex` and `theory.tex`,
`comet/independent_anchors.py`, and the relevant plan/generator/baseline paths
in `experiments/anchor_runner.py`. No experiment, test suite or random sampler
was run, and no frozen source or manuscript was changed.

**Conclusion: no substantive mathematical inconsistency found in these local
additions or their stated anchor information conditions.**

## Special two-state anchor envelope

For q=(1/2,1/2), midpoint nuisance, exact e=(3/4,1/4), set
w_s=q_s/e_s in {2/3,2}, delta_s=mu_s-1/2 and
m=(delta_0+delta_1)/2. The score is X=1/2+w_S(Y-1/2), and EX=1/2+m=.45
for the declared locations (.35,.55). Observed Y alone has the logger-weighted
mean, a different target.

For each state s, the location-class maximum is exactly

    max_{delta_0,delta_1 in [-1/2,1/2]} |w_s*delta_s-m|
      = (|w_s-1/2|+1/2)/2 = w_s/2,

because w_s>=1/2. Thus, conditional on the selected state, Minkowski and the
legal noise p-norm K give

    ||X-EX | S=s||_p <= w_s*(1/2+K),
    E|X-EX|^p <= (1/2+K)^p * sum_s e_s*w_s^p.

The implementation's `centered_moment_bound` is precisely this last quantity.
It uses the declared location class, fixed q/e/nuisance and known noise law,
not oracle point means or a moment estimated from the sampled log. For bounded
p=2, Var(X)=Var(R)<=E[R^2] independently justifies the stated bound. The heavy
anchor uses p=1.5 and K=.1*(1.75/(1.75-p))^(1/p), with the already stated
finite-grid/ordinary-arithmetic qualifications.

The i.i.d. generator sets constant response locations, uses one private outcome
source per row, and separate logging randomness. The same distribution and
independence conditions are therefore substantive construction assumptions.
The Catoni call receives the full DR score, checks its sample-size condition,
and retains the root-solver debit. It does not receive unavailable centering
means. Scaling cells remain ineligible for this i.i.d. baseline.

The equality of this envelope with a raw residual envelope is specific to the
balanced two-state target, midpoint fit and location class. It is not a general
raw-to-centered moment inequality for 1<p<2, nor a justification for applying
an i.i.d. theorem to heterogeneous independent or graph-dependent data.

## Unsupported levels with a supported paired contrast

With e=(0,1/2,1/2), q0=(1/5,3/10,1/2) and q1=(1/5,1/2,3/10), each policy is a
valid categorical distribution. Each level contains the unknown term mu0/5.
Varying mu0 while keeping the supported-state laws fixed produces identical
observations but changes both levels, establishing their nonidentification
without additional structural information.

Their contrast equals (mu1-mu2)/5. Its signed coefficients are
(0,1/5,-1/5), so the unsupported contribution cancels exactly. The query needs
conditional identification only on supported states with nonzero coefficients.
The zero coefficient is implemented without forming 0/0. This example does
not identify either level and does not relax positivity for a nonzero signed
coefficient. No interference or capacity constraint is imposed in this simple
categorical example; a more constrained policy space would still require its
own compatible joint-law argument.

At exactly zero informative exposure, the separate two-point construction
Y(1)=b +/- min(H,nu), Y(0)=b has identical observable laws, legal unweighted
moment at most nu^p, and normalized subgroup means separated by 2*min(H,nu).
The common-measure absolute-risk bound is therefore min(H,nu), as stated.
A raw subgroup moment scales that risk by pi. This nonidentification statement
concerns a nonzero unsupported target coefficient and is consistent with the
canceling contrast example.

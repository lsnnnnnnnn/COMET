# Corrected clique-replication lower bound

Status: **proved** for the stated exact-replication subclass; no claim of sharpness for every sparse graph. All “original” line references below refer to source commit `58ad7bd` (the supplied ZIP), so they remain meaningful after patches.

The invalid step is `paper/sections/appendix.tex:191–192` and `paper/sections/full/appendix.tex:191–192`. For $X\sim\operatorname{Bernoulli}(0.1)$ and $p=1.5$,

\[
E|X|^{1.5}=0.1,
\qquad E|X-EX|^{1.5}=0.9(0.1)^{1.5}+0.1(0.9)^{1.5}
=0.11384199576606167>0.1.
\]

Centering does minimize squared loss, but not generally absolute $p$-power loss at the arithmetic mean for $1<p<2$. A generally valid alternative is $E|X-EX|^p\le2^pE|X|^p$, by the two-term convexity inequality and Jensen. The corrected construction below uses its exact centered moment instead, with a better constant.

Let $n=N/\chi\ge1$, $1<p\le2$, and $\nu_p>0$. Define

\[
\epsilon=\frac1{2n},\quad a=\nu_p(2\epsilon)^{-1/p}
=\nu_p n^{1/p},\quad P_0=\delta_0,\quad
P_1=(1-\epsilon)\delta_0+\epsilon\delta_a.
\]

The means are $m_0=0$ and $m_1=\Delta=\epsilon a=(\nu_p/2)n^{-(p-1)/p}$. Both laws satisfy the centered-moment constraint:

\[
E_1|X-m_1|^p
=a^p\big[(1-\epsilon)\epsilon^p+\epsilon(1-\epsilon)^p\big]
\le a^p(\epsilon^p+\epsilon)
\le2\epsilon a^p=\nu_p^p.
\]

Here $\epsilon^p\le\epsilon$ since $0<\epsilon\le1/2$; the $P_0$ centered moment is zero. The raw $P_1$ moment is $\epsilon a^p=\nu_p^p/2$. These are distinct quantities.

Since $P_0^n$ is supported on the all-zero sample,

\[
\operatorname{TV}(P_0^n,P_1^n)=1-(1-\epsilon)^n
\le n\epsilon=\tfrac12.
\]

The bound holds for **every** $n\ge1$, including $n=1$. Equivalently, the common mass $c=(1-\epsilon)^n\ge1/2$. No “small $n$ absorbed into a constant” argument is needed.

For any possibly randomized estimator $T$, integrate its randomization using the same auxiliary law under both hypotheses. Let $Q=P_0^n\wedge P_1^n$, a common subprobability measure of mass $c$. Then

\[
R_0(T)+R_1(T)
\ge\int\{|T|+|T-\Delta|\}\,dQ
\ge\Delta c.
\]

Thus

\[
\inf_T\max(R_0(T),R_1(T))
\ge\frac{\Delta c}{2}\ge\frac{\Delta}{4}
=\frac{\nu_p}{8}\left(\frac\chi N\right)^{(p-1)/p}.
\]

This direct common-measure form of Le Cam proves that the existing unspecified $c_p$ may be taken to be $1/8$, uniformly over $1<p\le2$. It is a conservative explicit constant, not an assertion of the optimal minimax constant.

To transfer to $N$ rows, draw $X_1,\dots,X_n$ independently and repeat each exactly $\chi$ times. Replication is an injective deterministic map of the sample, with a deterministic inverse obtained by selecting one row per cluster. It preserves statistical information and total variation. The sufficient dependency graph is the disjoint union of $n$ complete $\chi$-vertex graphs; both its chromatic and clique numbers equal $\chi$. The parameter is the distributional mean, not the realized sample average. The theorem applies to this subclass and any larger class containing it.

The theorem statements at original `paper/sections/04_theory.tex:44–55` and `paper/sections/full/04_theory.tex:60–75` already name this subclass and need no numerical or estimand change. The two appendix proofs are patched. The prose “matching” must be read only as a worst-case rate comparison within a containing class: an expected absolute-risk lower bound does not establish a lower bound for a specified 95% simultaneous confidence radius, does not match its logarithmic factor, and does not give a graph-specific lower bound for each sparse graph. This is the same scope required by `paper/RESEARCH_TODO.md:49–59`.

The family depends on $n$. It is a minimax construction rather than a fixed heavy-tail distribution; its two-point laws have all finite moments. A fixed Student-t or Pareto simulation need not attain the worst-case exponent determined by the available moment order $p$.

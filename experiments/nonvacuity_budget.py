"""Outcome-free radius/sample budget for the proved MOM expressions.

This independent calculator imports neither COMET estimators, data generators,
nor oracle modules. Requirements are sufficient for this bound, not minimax
sample-complexity lower bounds. The fixed eta=1/8 comparison precedes any eta
optimization. Reference nu values are declared envelopes, not estimates.
"""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
from itertools import product
from math import ceil, comb, isfinite, log
from pathlib import Path

ETA = Fraction(1, 8)
P_GRID = (1.2, 1.5, 2.0)


def binomial_tail_fraction(K, eta=ETA):
    """Exact rational probability of at least ceil(K/2) bad groups."""
    eta = Fraction(eta)
    if type(K) is not int or K < 1 or not 0 < eta < Fraction(1,2):
        raise ValueError('invalid K or eta')
    threshold = (K+1)//2
    return sum((Fraction(comb(K,j))*eta**j*(1-eta)**(K-j)
                for j in range(threshold,K+1)),Fraction())


def select_K(m, delta, B, rule):
    if type(m) is not int or m < 1 or type(B) is not int or B < 2:
        raise ValueError('invalid family/block count')
    delta_exact = Fraction(str(delta))
    if not 0 < delta_exact < 1:
        raise ValueError('invalid failure budget')
    if rule == 'conservative_hoeffding':
        K = ceil(8*(log(2*m)-log(delta)))
        if B < 2*K:
            raise ValueError('no feasible conservative K with L_min>=2')
        return K
    if rule == 'exact_binomial':
        for K in range(1,B//2+1,2):
            if m*binomial_tail_fraction(K) <= delta_exact:
                return K
        raise ValueError('no feasible odd exact-binomial K with L_min>=2')
    raise ValueError('unknown majority rule')


def radius(p, nu, chi, n0, L_min, eta=ETA):
    if not all(isfinite(x) for x in (p,nu)) or not 1<p<=2 or nu<0:
        raise ValueError('invalid declared moment envelope')
    if any(type(x) is not int or x<1 for x in (chi,n0,L_min)) or n0%chi:
        raise ValueError('invalid clique/block layout')
    eta=Fraction(eta)
    if not 0<eta<Fraction(1,2):
        raise ValueError('invalid eta')
    return (4/float(eta))**(1/p)*nu*(chi/(L_min*n0))**((p-1)/p)


def required_sample_size(p, nu, chi, B, K, diameter=1, fraction=.25,
                         subgroup_mass=1, support_positive=True):
    """Exact rational inversion on p in {1.2,1.5,2}; round n0 up to chi.

    For a subgroup ratio, diameter is its numerator's feasible diameter=mass;
    dividing both radius and diameter by mass leaves the requested fraction.
    Zero mass and unsupported targets abstain independently of radius size.
    """
    if not support_positive:
        return {'budget_status':'NOT_CERTIFIABLE_TARGET_SUPPORT','required_n0':None,'required_N':None}
    if subgroup_mass <= 0 or diameter <= 0:
        return {'budget_status':'NOT_CERTIFIABLE_ZERO_SUBGROUP_MASS','required_n0':None,'required_N':None}
    pf=Fraction(str(p))
    if pf not in (Fraction(6,5),Fraction(3,2),Fraction(2)):
        raise ValueError('exact inversion supports the declared C0 p grid only')
    if not isfinite(nu) or nu<0 or not 0<fraction<1:
        raise ValueError('invalid scale or target radius fraction')
    if any(type(x) is not int or x<1 for x in (chi,B,K)) or B<2*K:
        raise ValueError('infeasible group layout')
    L=B//K
    # n0 >= chi/L * (4/eta)^(1/(p-1)) * (nu/(fraction*D))^(p/(p-1)).
    # Both exponents are integers for this grid, so no floating inversion can
    # round down an astronomical requirement.
    exact = Fraction(chi,L)
    exact *= (Fraction(4,1)/ETA)**int(1/(pf-1))
    exact *= (Fraction(str(nu))/(Fraction(str(fraction))*Fraction(str(diameter))))**int(pf/(pf-1))
    n0 = max(chi, chi*ceil(exact/chi))
    return {'budget_status':'SUFFICIENT_FOR_THIS_BOUND','required_n0':n0,'required_N':B*n0}


def budget_rows():
    rows=[]
    for p,nu,chi,m,rule in product(P_GRID,(1.0,4.0),(1,4),(1,16),
                                  ('conservative_hoeffding','exact_binomial')):
        B,delta=128,.05
        K=select_K(m,delta,B,rule)
        requirement=required_sample_size(p,nu,chi,B,K)
        for N in (8192,16384,32768,65536):
            n0=N//B
            rows.append(dict(category='reference_envelope_grid',p=p,nu_p=nu,chi=chi,family_size=m,
                delta_stat=delta,eta=float(ETA),mom_majority_rule=rule,B=B,K=K,L_min=B//K,
                L_max=ceil(B/K),n0=n0,raw_N=N,retained_N=N,N_eff=N/chi,
                nu_source='declared_known_reference_envelope_not_estimated',
                raw_radius=radius(p,nu,chi,n0,B//K),feasible_diameter=1.0,
                target_radius_fraction=.25,subgroup_mass=1.0,support_positive=True,
                familywise_binomial_bound=float(m*binomial_tail_fraction(K)),
                **requirement))
    # Subgroup ratio precision and identification are distinct from point support.
    for mass,supported in ((.5,True),(.01,True),(0.0,True),(.5,False)):
        p,nu,chi,m,B,delta=2.0,1.0,1,16,128,.05
        for rule in ('conservative_hoeffding','exact_binomial'):
            K=select_K(m,delta,B,rule)
            requirement=required_sample_size(p,nu,chi,B,K,diameter=mass,
                                             subgroup_mass=mass,support_positive=supported)
            rows.append(dict(category='subgroup_ratio_budget',p=p,nu_p=nu,chi=chi,family_size=m,
                delta_stat=delta,eta=float(ETA),mom_majority_rule=rule,B=B,K=K,L_min=B//K,
                L_max=ceil(B/K),n0=64,raw_N=8192,retained_N=8192,N_eff=8192,
                nu_source='declared_known_reference_envelope_not_estimated',
                raw_radius=radius(p,nu,chi,64,B//K) if supported and mass>0 else None,
                feasible_diameter=mass,target_radius_fraction=.25,subgroup_mass=mass,
                support_positive=supported,familywise_binomial_bound=float(m*binomial_tail_fraction(K)),
                **requirement))
    return rows


def plot_budget(rows, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import LogLocator, LogFormatterMathtext
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42,
                         'axes.spines.top':False,'axes.spines.right':False})
    combinations=list(product((1.0,4.0),(1,4),(1,16)))
    fig,axes=plt.subplots(1,3,figsize=(12.6,5.5),sharey=True,constrained_layout=True)
    colors={'conservative_hoeffding':'#0072B2','exact_binomial':'#D55E00'}
    labels={'conservative_hoeffding':'Conservative K','exact_binomial':'Exact-binomial K'}
    for ax,p in zip(axes,P_GRID):
        for index,(nu,chi,m) in enumerate(combinations):
            selected=[r for r in rows if r['category']=='reference_envelope_grid' and
                      r['p']==p and r['nu_p']==nu and r['chi']==chi and
                      r['family_size']==m and r['raw_N']==8192]
            ys=[r['required_N'] for r in selected]
            ax.plot([index,index],ys,color='#999999',linewidth=1,zorder=1)
            for r in selected:
                rule=r['mom_majority_rule']
                ax.scatter(index,r['required_N'],color=colors[rule],s=38,zorder=2,
                           marker='o' if rule=='conservative_hoeffding' else '^',
                           label=labels[rule] if index==0 else None)
        ax.set_yscale('log')
        ax.set_title(f'Available moment order p={p:g}',fontweight='bold')
        ax.set_xticks(range(len(combinations)),[f'{nu:g}, {chi}, {m}' for nu,chi,m in combinations],rotation=55,ha='right')
        ax.set_xlabel('Known ν, clique χ, family size m')
        ax.grid(axis='y',which='major',alpha=.25)
        ax.yaxis.set_major_locator(LogLocator(base=10,numticks=9))
        ax.yaxis.set_major_formatter(LogFormatterMathtext())
    axes[0].set_ylabel('Sufficient raw N for radius ≤ 0.25 × feasible diameter')
    axes[-1].legend(loc='upper right',frameon=False)
    fig.suptitle('Design-only MOM sample budget — no outcomes or oracle truth',fontsize=14,fontweight='bold')
    fig.supxlabel('B=128, δ=0.05, η=1/8, diameter=1; n₀ rounded up to complete χ-cliques.\n'
                  'These are sufficient requirements for this bound, not minimax lower bounds.',fontsize=10)
    output.mkdir(parents=True,exist_ok=True)
    fig.savefig(output/'theoretical_sample_need.png',dpi=200,metadata={'Software':'COMET Gate C0'})
    fig.savefig(output/'theoretical_sample_need.pdf',metadata={'Creator':'COMET Gate C0','CreationDate':None,'ModDate':None})
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='results/gate_C0')
    args=parser.parse_args()
    output=Path(args.output)
    output.mkdir(parents=True,exist_ok=True)
    rows=budget_rows()
    with (output/'theoretical_radius_budget.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    plot_budget(rows,output)
    print(f'Saved {len(rows)} deterministic budget rows and PNG/PDF; no outcomes used.')


if __name__=='__main__':
    main()

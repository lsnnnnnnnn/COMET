"""Gate C reporting statistics; evidence summaries never confer validity."""
from collections import Counter, defaultdict
from fractions import Fraction
from math import comb, isfinite, nextafter, sqrt
from statistics import mean, median

from .metrics import wilson


PRIMARY_METHODS = ('orig_mom','exact_binomial_mom','bounded_graph_chebyshev')
PRIMARY_COMPARISONS = tuple((cell,method) for cell in 'ABCDEF' for method in PRIMARY_METHODS
                            if (cell,method) != ('F','bounded_graph_chebyshev'))


def _binomial_tail(hits, total, probability, lower):
    if type(hits) is not int or type(total) is not int or not 0 <= hits <= total:
        raise ValueError('invalid binomial counts')
    p = probability if isinstance(probability,Fraction) else Fraction(str(probability))
    if not 0 <= p <= 1:
        raise ValueError('invalid binomial probability')
    r,s = p.numerator,p.denominator
    indices = range(hits+1) if lower else range(hits,total+1)
    return Fraction(sum(comb(total,j)*r**j*(s-r)**(total-j) for j in indices),s**total)


def exact_binomial_lower(hits, total, probability):
    """Exact inclusive P[Bin(total,probability)<=hits]."""
    return _binomial_tail(hits,total,probability,True)


def exact_binomial_upper(hits, total, probability):
    """Exact inclusive P[Bin(total,probability)>=hits]."""
    return _binomial_tail(hits,total,probability,False)


def _upper_float(value):
    result = float(value)
    return nextafter(result,float('inf')) if Fraction.from_float(result) < value else result


def undercoverage_pvalue(hits, total, nominal):
    """One-sided H0: coverage>=nominal; supremum attained at nominal.

    No observations means no test. Nonrejection is not a proof of coverage.
    The returned float is rounded upward from the exact rational tail.
    """
    if total == 0:
        if hits != 0:
            raise ValueError('invalid binomial counts')
        return None
    return _upper_float(exact_binomial_lower(hits,total,nominal))


def holm_adjust(pvalues):
    """Holm adjusted p-values for a predeclared comparison mapping.

    None is retained in output and conservatively occupies one comparison at
    p=1 during adjustment. Thus missing/inapplicable comparisons are never
    dropped opportunistically to reduce multiplicity.
    """
    values = dict(pvalues)
    for p in values.values():
        if p is not None and (not isfinite(p) or not 0 <= p <= 1):
            raise ValueError('invalid p-value')
    ordered = sorted(values,key=lambda key:(1. if values[key] is None else values[key],str(key)))
    adjusted, running = {}, 0.
    for rank,key in enumerate(ordered):
        p = 1. if values[key] is None else values[key]
        running = max(running,min(1.,(len(ordered)-rank)*p))
        adjusted[key] = None if values[key] is None else running
    return {key:adjusted[key] for key in values}


def quantile(values, q):
    if not 0 <= q <= 1:
        raise ValueError('invalid quantile')
    xs = sorted(values)
    if not xs:
        return None
    position = q*(len(xs)-1)
    lower = int(position)
    return xs[lower]+(xs[min(lower+1,len(xs)-1)]-xs[lower])*(position-lower)


def _med(values):
    return median(values) if values else None


def summarize_records(records, phase='preflight', primary_comparisons=PRIMARY_COMPARISONS):
    """Summarize complete paired families, retaining all applicability rows.

    The runner joins oracle metrics only after all methods are complete.
    Expected fields are documented by tests. Coverage is familywise; width and
    decision fractions are marginal candidate summaries with explicit counts.
    No stochastic acceptance threshold is applied to a preflight batch.
    """
    if primary_comparisons is None:
        primary_comparisons = PRIMARY_COMPARISONS
    primary_comparisons = tuple((item['cell_id'],item['method']) if isinstance(item,dict)
                                else tuple(item) for item in primary_comparisons)
    if len(set(primary_comparisons)) != len(primary_comparisons):
        raise ValueError('duplicate preregistered primary comparisons')
    grouped = defaultdict(list)
    for row in records:
        alpha = row.get('nominal_delta',row.get('alpha'))
        grouped[row['cell_id'],alpha,row['method']].append(row)
    summaries = []
    for (cell,alpha,method),rows in sorted(grouped.items()):
        runs = defaultdict(list)
        for row in rows:
            runs[row['run_id']].append(row)
        expected = None
        families = []
        for run_id,family in sorted(runs.items()):
            candidate_ids = {r['candidate_id'] for r in family}
            sizes = {r['family_size'] for r in family}
            if len(sizes)!=1 or len(family)!=next(iter(sizes)) or len(candidate_ids)!=len(family):
                raise ValueError('incomplete or duplicated candidate family: '+run_id)
            if expected is None:
                expected = candidate_ids
            elif candidate_ids != expected:
                raise ValueError('family changed between independent replications')
            families.append(family)
        n = len(families)
        applicable = sum(all(r['certificate_applicable'] for r in f) for f in families)
        issued = sum(all(r['decision_issuable'] for r in f) for f in families)
        hits = sum(all(r['decision_issuable'] and r.get('covered',False) for r in f) for f in families)
        raw_hits = sum(all(r['status'] in ('CERTIFIED','CERTIFIED_UNDER_DECLARED_ASSUMPTIONS')
                           and r.get('raw_covered',False) for r in f) for f in families)
        # Non-applicable/point procedures have no coverage denominator; their
        # allocated replication count and absence of intervals remain explicit.
        coverage_defined = applicable == n and n > 0
        wl,wh = wilson(hits,n) if coverage_defined else (None,None)
        cwl,cwh = wilson(hits,issued)
        widths = [r['width_fraction'] for r in rows if r.get('width_fraction') is not None]
        raw_radii = [r['raw_radius'] for r in rows if r.get('raw_radius') is not None]
        errors = [r['absolute_error'] for r in rows if r.get('absolute_error') is not None]
        signed = [r['signed_error'] for r in rows if r.get('signed_error') is not None]
        ratios = [r['absolute_error']/r['raw_radius'] for r in rows
                  if r.get('absolute_error') is not None and r.get('raw_radius') not in (None,0)]
        decisions = Counter(r['decision'] for r in rows)
        true_violating = sum(bool(r.get('true_violation')) for r in rows)
        power_hits = sum(bool(r.get('true_violation')) and r['decision']=='CERTIFIED_VIOLATION' for r in rows)
        # A valid raw CI with empty support intersection is a coverage failure,
        # not a reason to suppress the test. Inapplicable/feasibility-refused
        # methods have certificate_applicable=False and remain outside it.
        pvalue = (undercoverage_pvalue(hits,n,1-alpha)
                  if coverage_defined and method in PRIMARY_METHODS else None)
        summary = dict(phase=phase,cell_id=cell,alpha=alpha,nominal_level=1-alpha,method=method,
            replications=n,candidate_records=len(rows),family_size=len(expected),
            status_counts=dict(sorted(Counter(r['status'] for r in rows).items())),
            applicable_families=applicable,applicability_fraction=applicable/n,
            issued_families=issued,covered_families=hits if coverage_defined else None,
            family_coverage=hits/n if coverage_defined else None,
            raw_family_coverage=raw_hits/n if coverage_defined else None,
            wilson_lo=wl,wilson_hi=wh,
            issued_and_covers_rate=hits/n if coverage_defined else None,
            coverage_given_issued=hits/issued if issued else None,
            conditional_wilson_lo=cwl,conditional_wilson_hi=cwh,
            interval_absent_fraction=1-issued/n,
            not_applicable_families=sum(any(r['status']=='NOT_APPLICABLE' for r in f) for f in families),
            family_nontrivial_some=sum(any(r.get('is_nontrivial',False) for r in f) for f in families)/n,
            family_nontrivial_all=sum(all(r.get('is_nontrivial',False) for r in f) for f in families)/n,
            marginal_nontrivial_fraction=sum(r.get('is_nontrivial',False) for r in rows)/len(rows),
            median_width_fraction=_med(widths),q25_width_fraction=quantile(widths,.25),
            q75_width_fraction=quantile(widths,.75),p90_width_fraction=quantile(widths,.9),
            iqr_width_fraction=(quantile(widths,.75)-quantile(widths,.25)) if widths else None,
            median_raw_radius=_med(raw_radii),median_absolute_error=_med(errors),
            median_absolute_error_over_radius=_med(ratios),
            signed_bias=mean(signed) if signed else None,
            rmse=sqrt(mean(e*e for e in errors)) if errors else None,
            decision_counts=dict(sorted(decisions.items())),
            constraint_abstention_fraction=decisions['ABSTAIN']/len(rows),
            no_certified_decision_fraction=1-(decisions['CERTIFIED_SAFE']+decisions['CERTIFIED_VIOLATION'])/len(rows),
            true_violating_count=true_violating,true_nonviolating_count=len(rows)-true_violating,
            violation_power=power_hits/true_violating if true_violating and applicable==n else None,
            false_safe_count=sum(bool(r.get('false_safe')) for r in rows),
            false_violation_count=sum(bool(r.get('false_violation')) for r in rows),
            undercoverage_pvalue=pvalue,undercoverage_holm_pvalue=None,
            undercoverage_test='exact_lower_tail_H0_coverage_ge_nominal',
            undercoverage_interpretation=('debugging_only_not_confirmatory' if phase=='preflight'
                                         else 'nonrejection_does_not_prove_nominal_coverage'))
        for key in ('raw_N','N_eff','chi_max','B','n0','K','L_min','L_max','p_declared'):
            summary[key] = rows[0].get(key)
        summaries.append(summary)
    primary = {(r['cell_id'],r['method']):r for r in summaries if r['alpha']==.05}
    pvalues = {comparison:primary.get(comparison,{}).get('undercoverage_pvalue')
               for comparison in primary_comparisons}
    adjusted = holm_adjust(pvalues)
    for comparison,pvalue in adjusted.items():
        if comparison in primary:
            primary[comparison]['undercoverage_holm_pvalue'] = pvalue
            primary[comparison]['holm_declared_comparisons'] = len(primary_comparisons)
    return summaries

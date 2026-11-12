"""Known-support intersection and honest informativeness accounting."""
from math import isfinite


def add_support_bounds(record, feasible_lo, feasible_hi, tolerance=1e-12):
    """Intersect a CI with known target support, never clip scores/weights.

    Coverage is preserved since the target lies in the support surely. Empty
    intersections are not reported as useful or allowed to trigger safety
    decisions. A singleton target has zero diameter and no width fraction.
    """
    if not all(isfinite(x) for x in (feasible_lo, feasible_hi)) or feasible_lo > feasible_hi:
        raise ValueError('invalid known target support')
    result = dict(record)
    diameter = feasible_hi-feasible_lo
    result.update(raw_estimate=record.get('estimate'), raw_radius=record.get('stochastic_radius'),
                  raw_lo=record.get('lo'), raw_hi=record.get('hi'),
                  feasible_lo=feasible_lo, feasible_hi=feasible_hi, feasible_diameter=diameter,
                  clipped_lo=None, clipped_hi=None, clipped_width=None,
                  width_fraction=None, informativeness_fraction=None,
                  is_empty=False, is_full_range=None, is_nontrivial=False,
                  decision_issuable=False)
    if record.get('status') not in ('CERTIFIED', 'CERTIFIED_UNDER_DECLARED_ASSUMPTIONS'):
        return result
    lo, hi = record['lo'], record['hi']
    if lo is None or hi is None or not all(isfinite(x) for x in (lo, hi)) or lo > hi:
        raise ValueError('certified record must have finite ordered raw endpoints')
    lower, upper = max(lo, feasible_lo), min(hi, feasible_hi)
    empty = lower > upper
    width = max(0.0, upper-lower)
    tol = tolerance*max(1.0, diameter)
    result.update(clipped_lo=lower, clipped_hi=upper, clipped_width=width,
                  is_empty=empty, decision_issuable=not empty,
                  is_full_range=not empty and width >= diameter-tol)
    if diameter > 0 and not empty:
        result.update(width_fraction=width/diameter,
                      informativeness_fraction=1-width/diameter,
                      is_nontrivial=width < diameter-tol)
    return result

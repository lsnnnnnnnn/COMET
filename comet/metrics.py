"""Monte Carlo debugging summaries; these do not prove coverage."""
from __future__ import annotations

from math import sqrt
from statistics import NormalDist, mean


def wilson(successes: int, total: int, level: float = 0.95):
    """Wilson score interval; no observations means undefined, never 100%."""
    if not 0 <= successes <= total or not 0 < level < 1:
        raise ValueError("invalid binomial count or confidence level")
    if total == 0:
        return None, None
    z = NormalDist().inv_cdf((1 + level) / 2)
    phat = successes / total
    denominator = 1 + z * z / total
    center = (phat + z * z / (2 * total)) / denominator
    half = z * sqrt(phat * (1 - phat) / total + z * z / (4 * total**2)) / denominator
    return max(0.0, center - half), min(1.0, center + half)


def _summary(alpha, candidate, events, widths, vacuous):
    total = len(events)
    issued = sum(e[0] for e in events)
    hits = sum(e[0] and e[1] for e in events)
    lo, hi = wilson(hits, issued)
    ulo, uhi = wilson(hits, total)
    return dict(alpha=alpha, nominal_level=1-alpha, candidate_id=candidate,
                replications=total, issued=issued, hits=hits,
                issuance_rate=issued / total if total else None,
                conditional_coverage=hits / issued if issued else None,
                wilson_lo=lo, wilson_hi=hi,
                issued_and_covers_rate=hits / total if total else None,
                unconditional_wilson_lo=ulo, unconditional_wilson_hi=uhi,
                mean_interval_width=mean(widths) if widths else None,
                vacuous_fraction=mean(vacuous) if vacuous else None)


def coverage_summary(records):
    """Familywise denominators are independent replications, not candidate rows."""
    result = []
    for alpha in sorted({r['nominal_delta'] for r in records}):
        level_rows = [r for r in records if r['nominal_delta'] == alpha]
        candidates = sorted({r['candidate_id'] for r in level_rows})
        families = []
        all_widths, all_vacuous = [], []
        for rep in sorted({r['replicate_id'] for r in level_rows}):
            rows = [r for r in level_rows if r['replicate_id'] == rep]
            if len(rows) != len(candidates) or {r['candidate_id'] for r in rows} != set(candidates):
                raise ValueError('incomplete or duplicated candidate family in results')
            issued = all(r['status'] == 'CERTIFIED' for r in rows)
            families.append((issued, issued and all(r['covered'] for r in rows)))
            all_widths.extend(r['hi']-r['lo'] for r in rows if r['status'] == 'CERTIFIED')
            all_vacuous.extend(r['vacuous'] for r in rows if r['status'] == 'CERTIFIED')
        result.append(_summary(alpha, 'SIMULTANEOUS_FAMILY', families, all_widths, all_vacuous))
        for candidate in candidates:
            rows = [r for r in level_rows if r['candidate_id'] == candidate]
            issued = [r for r in rows if r['status'] == 'CERTIFIED']
            events = [(r['status'] == 'CERTIFIED', bool(r['covered'])) for r in rows]
            result.append(_summary(alpha, candidate, events,
                                   [r['hi']-r['lo'] for r in issued],
                                   [r['vacuous'] for r in issued]))
    return result

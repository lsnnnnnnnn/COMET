"""Strong inference anchors restricted to declared homogeneous independent data.

These procedures do not certify a heterogeneous fixed-design graph average.
The i.i.d./moment declarations are assumptions, not facts inferred from a schema.
Ordinary floating arithmetic is used; this is not outward-rounded verification.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.optimize import brentq


CERTIFIED = "CERTIFIED_UNDER_DECLARED_ASSUMPTIONS"
CATONI_SOURCE = "https://proceedings.mlr.press/v162/bhatt22b/bhatt22b.pdf#page=4"
OPE_SOURCE = "https://proceedings.mlr.press/v139/karampatziakis21a/karampatziakis21a.pdf"


def _vector(values, name):
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or len(x) == 0 or not np.isfinite(x).all():
        raise ValueError(f"{name} must be a nonempty finite one-dimensional array")
    return x


def _delta(delta):
    if not math.isfinite(delta) or not 0 < delta < 1:
        raise ValueError("delta must lie strictly between zero and one")


def catoni_iid(values, *, p, central_moment_bound, delta=0.05, tau=0.5,
               h=0.9, iid_declared=False):
    """Bhatt et al. (2022), Theorem 3.2, with its actual feasibility gate.

    ``central_moment_bound`` bounds E|X-EX|**p, not E|X|**p. The returned
    mathematical radius is enlarged by the declared root-solver tolerance.
    An absent i.i.d. declaration or insufficient n produces no confidence set.
    """
    x = _vector(values, "values")
    _delta(delta)
    if not math.isfinite(p) or not 1 < p <= 2:
        raise ValueError("p must be in (1,2]")
    if not math.isfinite(central_moment_bound) or central_moment_bound < 0:
        raise ValueError("the known centered moment bound must be finite and nonnegative")
    if not math.isfinite(tau) or tau <= 0 or not math.isfinite(h) or not 0 < h < 1:
        raise ValueError("tau must be positive and h must be in (0,1)")
    result = dict(method="bhatt2022_catoni_iid", source=CATONI_SOURCE,
                  n=len(x), p=float(p), delta=float(delta), tau=float(tau),
                  h=float(h), central_moment_bound=float(central_moment_bound),
                  assumption="i.i.d.; common distribution; known centered p-moment",
                  iid_declared=bool(iid_declared), estimate=None, radius=None,
                  lo=None, hi=None, empty=False,
                  arithmetic="ordinary_float_with_root_tolerance_debit")
    if not iid_declared:
        return dict(result, status="ASSUMPTION_UNVERIFIED", reason="i.i.d. model not declared")
    eps = p - 1
    log_c = (p / 2) * math.log(eps / p)
    if eps < 1:
        log_c += ((1 - eps) / 2) * math.log((1 - eps) / eps)
    c = math.exp(log_c)
    ell = math.log(2 / delta)
    log_min_n = (-math.log1p(-h) + math.log(p / eps)
                 + p / eps * math.log1p(tau) - math.log(tau) / eps
                 + log_c / eps + math.log(ell))
    min_n = math.exp(log_min_n) if log_min_n < 709 else math.inf
    result.update(influence_constant=c, minimum_n=min_n,
                  sample_size_condition_met=len(x) >= min_n)
    if central_moment_bound == 0:
        if not np.all(x == x[0]):
            return dict(result, status="NUMERICAL_FAILURE",
                        reason="zero centered-moment envelope conflicts with unequal observations")
        return dict(result, status=CERTIFIED, estimate=float(x[0]), radius=0.0,
                    mathematical_radius=0.0, root_error_debit=0.0,
                    lo=float(x[0]), hi=float(x[0]),
                    reason="zero moment implies a degenerate common distribution")
    if len(x) < min_n:
        return dict(result, status="NOT_APPLICABLE",
                    reason="Theorem 3.2 sample-size condition fails")
    v = central_moment_bound
    log_logn = math.log(ell / len(x))
    log_a = (math.log(eps) + eps * math.log(h) - log_c - math.log(v) + log_logn) / p
    log_r = (math.log1p(tau) + math.log(p) / 2
             + (-eps * math.log(h) + math.log(v)) / p
             + eps / p * log_logn)
    if eps < 1:
        log_r += (1 / p - 0.5) * math.log1p(-eps)
    try:
        a, radius = math.exp(log_a), math.exp(log_r)
    except OverflowError:
        return dict(result, status="NUMERICAL_FAILURE", reason="nonfinite tuning or radius")
    if not 0 < a < math.inf or not math.isfinite(radius):
        return dict(result, status="NUMERICAL_FAILURE", reason="nonfinite tuning or radius")

    def score(theta):
        y = a * (x - theta)
        ay = np.abs(y)
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            psi = np.sign(y) * np.logaddexp(np.log1p(ay), log_c + p * np.log(ay))
        return float(np.sum(psi))

    xtol, rtol = 1e-12, 4 * np.finfo(float).eps
    left, right = float(np.min(x)), float(np.max(x))
    if left == right:
        estimate, root_debit = left, 0.0
    else:
        try:
            estimate = float(brentq(score, left, right, xtol=xtol, rtol=rtol))
        except (ValueError, RuntimeError, OverflowError) as exc:
            return dict(result, status="NUMERICAL_FAILURE", reason=f"root solve failed: {exc}")
        root_debit = xtol + rtol * abs(estimate)
    reported_radius = radius + root_debit
    if not all(math.isfinite(t) for t in
               (estimate - reported_radius, estimate + reported_radius)):
        return dict(result, status="NUMERICAL_FAILURE", reason="nonfinite interval endpoints")
    return dict(result, status=CERTIFIED, estimate=estimate,
                radius=reported_radius, mathematical_radius=radius,
                root_error_debit=root_debit, tuning=a,
                lo=estimate - reported_radius, hi=estimate + reported_radius,
                reason="Bhatt et al. Theorem 3.2 under declared i.i.d. assumptions")


# One-dimensional author-code path adapted from n17s/mope/opebet.py (2021).
# MIT License
# Copyright (c) 2021 The author
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


def _bet_update(stats, weight, reward, bet):
    f = math.log1p(-bet) + bet
    z = weight * reward
    stats["c"] += bet * z
    stats["s"] += bet
    stats["q"] += f * z * z
    stats["t"] += f * z
    stats["u"] += f
    stats["n"] += 1
    stats["z"] += z
    stats["y"] += z * z


def _bet_lower(stats, delta):
    a = stats["u"]
    if a == 0:
        return 0.0
    b = -(2 * stats["t"] + stats["s"])
    c = stats["q"] + stats["c"] - math.log(2 / delta)
    discriminant = b * b - 4 * a * c
    if discriminant < 0:
        return 0.0
    # Stable quadratic evaluation instead of subtracting nearly equal numbers.
    q = -0.5 * (b + math.copysign(math.sqrt(discriminant), b))
    if q == 0:
        return -b / (2 * a)
    # a<0: the upper quadratic root is the lower confidence endpoint.
    return max(q / a, c / q)


def _next_bet(stats, v):
    s = stats["z"] - stats["n"] * v
    q = stats["n"] * v * v + stats["y"] - 2 * v * stats["z"]
    return max(0.0, min(0.9, s / (s + q))) if q > 0 and s + q > 0 else 0.0


def ope_betting_iid(weights, rewards, *, wmax, delta=0.05, iid_declared=False):
    """Author one-dimensional OPE betting path, not full two-dimensional MOPE.

    Requires an i.i.d. OPE anchor, E[w]=1, bounded w and reward, and the target
    E[w*r]. The expectation declaration cannot be verified from one sample.
    Bets use only previous observations. Both one-sided streams share delta
    via log(2/delta). Empty intersections are retained, never forced nonempty.
    """
    w, y = _vector(weights, "weights"), _vector(rewards, "rewards")
    _delta(delta)
    if len(w) != len(y):
        raise ValueError("weights and rewards must have equal length")
    if not math.isfinite(wmax) or wmax < 1:
        raise ValueError("wmax must be finite and at least one")
    if np.any(w < 0) or np.any(w > wmax) or np.any(y < 0) or np.any(y > 1):
        raise ValueError("observations violate the declared bounded OPE support")
    result = dict(method="author_one_dimensional_ope_betting", source=OPE_SOURCE,
                  code_source="https://github.com/n17s/mope/blob/main/opebet.py",
                  n=len(w), wmax=float(wmax), delta=float(delta),
                  iid_declared=bool(iid_declared), lo=None, hi=None,
                  estimate=None, radius=None, empty=False,
                  assumption="i.i.d. bounded OPE anchor; exact weights; E[w]=1",
                  stronger_guarantee="time_uniform_under_anchor_assumptions",
                  implementation="author wealth_lb_1d path with stable roots; no cross-clamping",
                  arithmetic="ordinary_float_with_declared_root_padding")
    if not iid_declared:
        return dict(result, status="ASSUMPTION_UNVERIFIED", reason="i.i.d. OPE model not declared")
    stats = [{k: 0.0 for k in ("c", "s", "q", "t", "u", "n", "z", "y")}
             for _ in range(2)]
    bets, bounds = [0.0, 0.0], [0.0, 0.0]
    for wi, yi in zip(w, y):
        for side, reward in enumerate((yi, 1 - yi)):
            _bet_update(stats[side], float(wi), float(reward), bets[side])
            if not all(math.isfinite(t) for t in stats[side].values()):
                return dict(result, status="NUMERICAL_FAILURE", reason="nonfinite betting statistics")
            raw = _bet_lower(stats[side], delta)
            if not math.isfinite(raw):
                return dict(result, status="NUMERICAL_FAILURE", reason="nonfinite betting root")
            padding = 1e-12 * (1 + abs(raw))
            bounds[side] = max(bounds[side], raw - padding)
            # Clipping here controls only future bets; it never repairs output.
            bets[side] = _next_bet(stats[side], min(1.0, bounds[side]))
    lo, hi = bounds[0], 1 - bounds[1]
    return dict(result, status=CERTIFIED, lo=lo, hi=hi, empty=lo > hi,
                estimate=(lo + hi) / 2, radius=(hi - lo) / 2 if lo <= hi else None,
                point_estimate=float(np.mean(w * y)),
                reason="source-verified one-dimensional betting confidence sequence at fixed horizon")

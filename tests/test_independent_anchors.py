"""Deterministic strong-baseline anchor checks; no Monte Carlo draws."""

import itertools
import math

import numpy as np
import pytest

from comet.independent_anchors import CERTIFIED, catoni_iid, ope_betting_iid


@pytest.mark.parametrize("p", [1.2, 1.5, 2.0])
def test_catoni_root_symmetry_and_translation(p):
    x = np.tile(np.array([-2.0, -0.5, 0.5, 2.0]), 128)
    a = catoni_iid(x, p=p, central_moment_bound=4, tau=1, h=0.5, iid_declared=True)
    b = catoni_iid(x + 7, p=p, central_moment_bound=4, tau=1, h=0.5, iid_declared=True)
    assert a["status"] == b["status"] == CERTIFIED
    assert a["estimate"] == pytest.approx(0, abs=1e-11)
    assert b["estimate"] == pytest.approx(7, abs=1e-11)
    assert a["mathematical_radius"] == b["mathematical_radius"]
    assert b["lo"] <= 7 <= b["hi"]


def test_catoni_p2_constant_and_theorem_radius():
    r = catoni_iid(np.zeros(1000), p=2, central_moment_bound=0.25,
                   tau=0.5, h=0.9, iid_declared=True)
    assert r["status"] == CERTIFIED
    assert r["influence_constant"] == pytest.approx(0.5)
    assert r["mathematical_radius"] == pytest.approx(
        1.5 * math.sqrt(2) * math.sqrt(0.25 / 0.9) * math.sqrt(math.log(40) / 1000))
    assert r["tuning"] == pytest.approx(math.sqrt(2 * 0.9 * math.log(40) / (1000 * 0.25)))


def test_catoni_declared_model_and_sample_condition_are_required():
    common = dict(p=1.5, central_moment_bound=1)
    assert catoni_iid([1, 2], **common)["status"] == "ASSUMPTION_UNVERIFIED"
    r = catoni_iid([1, 2], **common, iid_declared=True)
    assert r["status"] == "NOT_APPLICABLE"
    assert r["lo"] is None and r["hi"] is None
    assert not r["sample_size_condition_met"]


def test_catoni_zero_moment_and_invalid_domain():
    r = catoni_iid([3, 3], p=1.5, central_moment_bound=0, iid_declared=True)
    assert r["status"] == CERTIFIED and r["lo"] == r["hi"] == 3
    r = catoni_iid([3, 4], p=1.5, central_moment_bound=0, iid_declared=True)
    assert r["status"] == "NUMERICAL_FAILURE" and r["lo"] is None
    for p in (1, 0.5, 2.1, math.inf):
        with pytest.raises(ValueError):
            catoni_iid([1], p=p, central_moment_bound=1, iid_declared=True)


def test_catoni_positive_scaling():
    x = np.tile([-2.0, 0, 1.0], 256)
    r = catoni_iid(x, p=1.5, central_moment_bound=8, tau=1, h=0.5, iid_declared=True)
    s = catoni_iid(3 * x, p=1.5, central_moment_bound=8 * 3**1.5,
                   tau=1, h=0.5, iid_declared=True)
    assert r["status"] == s["status"] == CERTIFIED
    assert s["estimate"] == pytest.approx(3 * r["estimate"])
    assert s["mathematical_radius"] == pytest.approx(3 * r["mathematical_radius"])


def test_ope_predictability_first_row_and_reward_symmetry():
    r = ope_betting_iid([1], [1], wmax=1, iid_declared=True)
    assert r["lo"] == 0 and r["hi"] == 1
    y = np.tile([0, 0, 1.0], 128)
    a = ope_betting_iid(np.ones(len(y)), y, wmax=1, iid_declared=True)
    b = ope_betting_iid(np.ones(len(y)), 1 - y, wmax=1, iid_declared=True)
    assert a["lo"] == pytest.approx(1 - b["hi"])
    assert a["hi"] == pytest.approx(1 - b["lo"])
    assert a["status"] == CERTIFIED


def test_ope_constant_response_is_informative():
    a = ope_betting_iid(np.ones(256), np.ones(256), wmax=1, iid_declared=True)
    assert a["lo"] > 0.95 and a["hi"] == 1
    b = ope_betting_iid(np.ones(256), np.zeros(256), wmax=1, iid_declared=True)
    assert b["hi"] < 0.05 and b["lo"] == 0


def test_ope_absent_iid_and_illegal_support_refuse():
    assert ope_betting_iid([1], [0.5], wmax=1)["status"] == "ASSUMPTION_UNVERIFIED"
    with pytest.raises(ValueError):
        ope_betting_iid([2], [0.5], wmax=1, iid_declared=True)
    with pytest.raises(ValueError):
        ope_betting_iid([1], [1.1], wmax=1, iid_declared=True)


def test_ope_exact_finite_iid_bernoulli_enumeration():
    # All 256 equiprobable IID Bernoulli(.5) samples, not a random pilot.
    n, failures = 8, 0
    for y in itertools.product((0.0, 1.0), repeat=n):
        r = ope_betting_iid(np.ones(n), y, wmax=1, delta=0.1, iid_declared=True)
        failures += not r["lo"] <= 0.5 <= r["hi"]
    assert failures / 2**n <= 0.1


def test_ope_stable_arithmetic_matches_transparent_author_fixture():
    # Original author update/root formulas, evaluated on a fixed arithmetic
    # fixture to check this adaptation, not an empirical coverage experiment.
    from collections import defaultdict

    def direct_author(w, y):
        stats = [defaultdict(float), defaultdict(float)]
        v, bets = [0.0, 0.0], [0.0, 0.0]
        for wi, yi in zip(w, y):
            for k, reward in enumerate((yi, 1 - yi)):
                d, t = stats[k], bets[k]
                f = np.log1p(-t) + t
                for key, increment in {
                    "c": t * wi * reward, "s": t, "q": f * wi**2 * reward**2,
                    "t": f * wi * reward, "u": f, "n": 1,
                    "z": wi * reward, "y": wi**2 * reward**2,
                }.items():
                    d[key] += increment
                a, b, c = d["u"], -(2 * d["t"] + d["s"]), d["q"] + d["c"] - np.log(40)
                disc = b*b - 4*a*c
                root = (-b - np.sqrt(disc))/(2*a) if a != 0 and disc >= 0 else 0
                v[k] = max(v[k], root)
                s = d["z"] - d["n"]*v[k]
                q = d["n"]*v[k]**2 + d["y"] - 2*v[k]*d["z"]
                bets[k] = max(0, min(0.9, s/(s+q))) if q > 0 else 0
        return v[0], 1-v[1]

    w = np.tile([0.4, 1.6, 1.0, 1.0], 64)
    y = np.tile([0.0, 1.0, 0.25, 0.75], 64)
    lo, hi = direct_author(w, y)
    r = ope_betting_iid(w, y, wmax=1.6, iid_declared=True)
    assert r["lo"] == pytest.approx(lo, abs=1e-9)
    assert r["hi"] == pytest.approx(hi, abs=1e-9)


def test_ope_numerical_overflow_is_not_a_certificate():
    r = ope_betting_iid([1e200], [1], wmax=1e200, iid_declared=True)
    assert r["status"] == "NUMERICAL_FAILURE" and r["lo"] is None

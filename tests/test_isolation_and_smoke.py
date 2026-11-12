import ast
from dataclasses import asdict, fields, replace
import inspect
import json
from pathlib import Path

import pytest

from comet.certification import certify
from comet.metrics import coverage_summary, wilson
from comet.schema import SyntheticConfig
from comet.smoke import run
from comet.synthetic import generate_evaluation


def test_oracle_is_separate_and_cannot_change_certificates():
    log, oracle = generate_evaluation(SyntheticConfig(B=128, n0=8, chi=2), 55)
    before = certify(log)
    wrong_oracle = replace(oracle, moments={k: 1e9 for k in oracle.moments})
    assert wrong_oracle.moments != oracle.moments
    assert before == certify(log)
    assert 'truth' not in inspect.signature(certify).parameters
    assert not {'truth', 'oracle', 'potential_outcomes', 'response_means_by_context'} & {f.name for f in fields(log)}
    assert all('oracle_truth' not in result for result in before)


def test_estimation_dependency_closure_has_no_oracle_import():
    root = Path(__file__).resolve().parents[1] / 'comet'
    visited = set()
    def inspect_module(name):
        if name in visited:
            return
        assert name not in {'truth', 'synthetic', 'smoke'}
        visited.add(name)
        tree = ast.parse((root/f'{name}.py').read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ''
                if node.level == 1:
                    inspect_module(module)
                elif module.startswith('comet.'):
                    inspect_module(module.split('.')[1])
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith('comet.'):
                        inspect_module(alias.name.split('.')[1])
    inspect_module('certification')
    assert 'schema' in visited


def test_wilson_numeric_fixture_and_no_issuance_denominator():
    low, high = wilson(30, 30)
    assert low == pytest.approx(0.8864866068260312)
    assert high == pytest.approx(1)
    assert wilson(0, 0) == (None, None)
    records = [dict(nominal_delta=.05, candidate_id='x', replicate_id=i,
                    status='NOT_CERTIFIABLE', covered=None, lo=None, hi=None, vacuous=None)
               for i in range(3)]
    summary = coverage_summary(records)[0]
    assert summary['conditional_coverage'] is None
    assert summary['issued_and_covers_rate'] == 0
    assert summary['replications'] == 3 and summary['issued'] == 0


def test_smoke_same_seed_reproduces_persisted_scientific_results(tmp_path):
    settings = dict(replications=2, base_seed=113, alphas=[.05,.1], p=1.5,
                    synthetic=asdict(SyntheticConfig(B=128,n0=8,chi=2)))
    config = tmp_path/'config.json'
    config.write_text(json.dumps(settings))
    run(config, tmp_path/'first')
    run(config, tmp_path/'second')
    for filename in ('intervals.json', 'intervals.csv', 'coverage.json', 'coverage.csv',
                     'coverage.md', 'example_log.json', 'example_oracle_truth.json', 'resolved_config.json'):
        assert (tmp_path/'first'/filename).read_bytes() == (tmp_path/'second'/filename).read_bytes()
    rows = json.loads((tmp_path/'first'/'coverage.json').read_text())
    family_rows = [r for r in rows if r['candidate_id'] == 'SIMULTANEOUS_FAMILY']
    assert len(family_rows) == 2
    assert all(r['replications'] == 2 for r in family_rows)
    assert all(0 <= r['issued'] <= 2 for r in family_rows)

"""Small CPU-only Gate B debugger. Oracle truth is joined after certification."""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time

from .certification import certify
from .metrics import coverage_summary
from .schema import SyntheticConfig
from .synthetic import generate_evaluation


def _json(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + '\n')


def _csv(path, records, fields=None):
    if not records:
        raise ValueError('empty result table')
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(records[0]), extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)


def run(config_path, output, replications=None):
    config_path, output = Path(config_path), Path(output)
    settings = json.loads(config_path.read_text())
    if replications is not None:
        settings['replications'] = replications
    reps = settings['replications']
    if not isinstance(reps, int) or not 1 <= reps <= 100:
        raise ValueError('Gate B smoke is limited to 1–100 debugging replications')
    if len(set(settings['alphas'])) != len(settings['alphas']):
        raise ValueError('duplicate confidence level')
    design = dict(settings['synthetic'])
    for key in ('e_by_context', 'mu_hat', 'q_probs', 'auditors'):
        if key in design:
            design[key] = tuple(design[key])
    config = SyntheticConfig(**design)
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    records = []
    for replicate in range(reps):
        seed = settings['base_seed'] + replicate
        log, oracle = generate_evaluation(config, seed)
        for alpha in settings['alphas']:
            certificates = certify(log, alpha=alpha, p=settings['p'])
            # Nothing in the estimator receives this separate oracle object.
            for certificate in certificates:
                truth = oracle.moments[certificate['candidate_id']]
                issued = certificate['status'] == 'CERTIFIED'
                mass = certificate.get('subgroup_mass')
                vacuous = None
                if issued:
                    vacuous = (certificate['lo'] <= -mass*config.reference and
                               certificate['hi'] >= mass*(1-config.reference))
                records.append({**certificate, 'replicate_id': replicate,
                                'oracle_truth': truth,
                                'covered': certificate['lo'] <= truth <= certificate['hi'] if issued else None,
                                'vacuous': vacuous})
        if replicate == 0:
            _json(output / 'example_log.json', asdict(log))
            _json(output / 'example_oracle_truth.json', asdict(oracle))
    summaries = coverage_summary(records)
    _json(output / 'resolved_config.json', settings)
    _json(output / 'intervals.json', records)
    _csv(output / 'intervals.csv', records, [
        'replicate_id', 'seed', 'candidate_id', 'nominal_delta', 'certified_level',
        'status', 'reason', 'estimate', 'lo', 'hi', 'oracle_truth', 'covered', 'vacuous',
        'p_declared', 'nu_p', 'C_p_used', 'stochastic_radius', 'nuisance_radius',
        'drift_radius', 'coupling_failure_epsilon', 'delta_stat', 'subgroup_mass',
        'raw_N', 'retained_N', 'N_eff', 'B', 'n0', 'K', 'L_min', 'chi_max'])
    _json(output / 'coverage.json', summaries)
    _csv(output / 'coverage.csv', summaries)
    lines = ['# Gate B smoke coverage — debugging only', '',
             f'{reps} independent replications; fixed configuration; CPU only. '
             'This small smoke run is not statistical evidence of final nominal coverage.', '',
             'Wilson intervals below are 95% Monte Carlo uncertainty intervals, separate '
             'from the estimator’s nominal 90%/95% family confidence level. Each family '
             'row has one Bernoulli event per independent replication. Candidate rows '
             'share replications and are not independent observations.', '',
             '| Nominal | Candidate | Issued / total | Covered / issued | Conditional coverage (Wilson 95%) | Issued and covers / total | Mean width | Vacuous |',
             '|---|---|---:|---:|---|---:|---:|---:|']
    for row in summaries:
        conditional = 'undefined (no issuance)' if row['conditional_coverage'] is None else (
            f"{row['conditional_coverage']:.3f} [{row['wilson_lo']:.3f}, {row['wilson_hi']:.3f}]")
        width = 'NA' if row['mean_interval_width'] is None else f"{row['mean_interval_width']:.4f}"
        vacuous = 'NA' if row['vacuous_fraction'] is None else f"{row['vacuous_fraction']:.1%}"
        lines.append(f"| {row['nominal_level']:.0%} | {row['candidate_id']} | "
                     f"{row['issued']}/{row['replications']} | {row['hits']}/{row['issued']} | "
                     f"{conditional} | {row['hits']}/{row['replications']} | {width} | {vacuous} |")
    lines += ['', '“Issued and covers” counts abstentions as unsuccessful issuance, not as coverage. '
              'Unconditional Wilson bounds are in coverage.csv/json. A vacuous interval '
              'contains the entire bounded-outcome feasible target range. Family width '
              'and vacuity summarize all issued candidate intervals. No clipping of '
              'intervals to the feasible range is performed.', '']
    (output / 'coverage.md').write_text('\n'.join(lines))
    root = Path(__file__).resolve().parents[1]
    hashes = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in sorted((root / 'comet').glob('*.py'))}
    git = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True, text=True)
    status = subprocess.run(['git', 'status', '--porcelain'], cwd=root, capture_output=True, text=True)
    _json(output / 'run_metadata.json', dict(
        purpose='debugging_only_not_final_coverage_evidence', python=platform.python_version(),
        platform=platform.platform(), elapsed_seconds=time.perf_counter()-started,
        git_head=git.stdout.strip() if git.returncode == 0 else None,
        git_dirty=bool(status.stdout.strip()), source_sha256=hashes,
        config_sha256=hashlib.sha256(json.dumps(settings,sort_keys=True).encode()).hexdigest(),
        seeds=list(range(settings['base_seed'],settings['base_seed']+reps)),
        oracle_use='exact conditional expectation, joined only after certify returned',
        external_datasets_used=False))
    return summaries


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='configs/smoke.json')
    parser.add_argument('--output', default='results/smoke')
    parser.add_argument('--replications', type=int)
    args = parser.parse_args(argv)
    summaries = run(args.config, args.output, args.replications)
    for row in summaries:
        if row['candidate_id'] == 'SIMULTANEOUS_FAMILY':
            print(f"nominal={row['nominal_level']:.0%}: issued={row['issued']}/{row['replications']}, "
                  f"family hits={row['hits']}/{row['issued']}; debugging only")
    print(f'Artifacts: {Path(args.output).resolve()}')


if __name__ == '__main__':
    main()

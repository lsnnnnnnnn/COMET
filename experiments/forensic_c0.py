"""Deterministic forensic analysis of preserved Gate A+B artifacts.

No new outcomes or oracle targets are generated. Historical logging assignments
are replayed only to recover q/e quantiles omitted from the saved intervals.
All source references and source hashes use the exact d11a36f baseline.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from math import isclose
from pathlib import Path
from random import Random
from statistics import median
import subprocess

BASELINE = 'd11a36f3b967165f4e0cdf56bf6a262d178e41bd'
TOLERANCE = 1e-12


def quantile(values, probability):
    ordered = sorted(values)
    index = (len(ordered)-1)*probability
    low = int(index)
    high = min(low+1, len(ordered)-1)
    return ordered[low] + (index-low)*(ordered[high]-ordered[low])


def quantiles(values, prefix):
    return {f'{prefix}_{label}': quantile(values, probability)
            for label, probability in [('min',0),('median',.5),('p95',.95),('p99',.99),('max',1)]}


def save_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows({key: json.dumps(value, separators=(',',':')) if isinstance(value,(list,dict)) else value
                          for key,value in row.items()} for row in rows)


def historical_logging(config, seed):
    """Exact copy of baseline logging RNG, without any potential-outcome draws."""
    digest = hashlib.sha256(f'COMET-v1:{seed}:logging'.encode()).digest()
    rng = Random(int.from_bytes(digest, 'big'))
    rows = []
    for _ in range(config['B']):
        for cluster in range(config['n0']//config['chi']):
            x = cluster % 2
            e1 = config['e_by_context'][x]
            exposure = int(rng.random() < e1)
            rows.extend([(x, exposure, (1-e1, e1))]*config['chi'])
    return rows


def analyze(root, output, report):
    source = root/'results/smoke'
    saved = json.loads((source/'intervals.json').read_text())
    settings = json.loads((source/'resolved_config.json').read_text())
    config = settings['synthetic']
    example = json.loads((source/'example_log.json').read_text())
    meta = json.loads((source/'run_metadata.json').read_text())
    expected_count = settings['replications']*len(settings['alphas'])*len(example['family'])
    assert len(saved) == expected_count == 240
    source_hashes = {}
    for name, expected in meta['source_sha256'].items():
        original = subprocess.check_output(['git','show',f'{BASELINE}:{name}'],cwd=root)
        actual = hashlib.sha256(original).hexdigest()
        assert actual == expected, name
        source_hashes[name] = actual
    old_report_names = subprocess.check_output(
        ['git','ls-tree','-r','--name-only',BASELINE,'reports'],cwd=root,text=True).splitlines()
    report_hashes = {}
    for name in old_report_names:
        content = (root/name).read_bytes()
        assert content == subprocess.check_output(['git','show',f'{BASELINE}:{name}'],cwd=root), name
        report_hashes[name] = hashlib.sha256(content).hexdigest()
    logging = {seed: historical_logging(config,seed) for seed in meta['seeds']}
    assert [s for _,s,_ in logging[example['seed']]] == [row['observed_exposure_s'] for row in example['rows']]
    candidate_map = {f"q{float(c['q1'])!r}__{c['auditor']}": c for c in example['family']}
    rows = []
    for record in saved:
        candidate = candidate_map[record['candidate_id']]
        q = (1-candidate['q1'], candidate['q1'])
        observed_weights = [q[s]/e[s] for _,s,e in logging[record['seed']]]
        state_weights = [q[s]/e[s] for _,_,e in logging[record['seed']] for s in (0,1)]
        max_weight = max(observed_weights)
        assert isclose(max_weight,record['overlap_metrics']['max_observed_weight'],rel_tol=1e-12)
        scaled = [w/max_weight for w in observed_weights]
        ess = sum(scaled)**2/sum(w*w for w in scaled)
        assert isclose(ess, record['effective_support_metrics']['importance_ess_diagnostic'],rel_tol=1e-12)
        p, chi, L, n0 = record['p_declared'], record['chi_max'], record['L_min'], record['n0']
        calculated_radius = 32**(1/p)*record['nu_p']*(chi/(L*n0))**((p-1)/p)
        assert isclose(calculated_radius, record['stochastic_radius'],rel_tol=1e-14)
        assert isclose(record['lo'],record['estimate']-calculated_radius,rel_tol=1e-14)
        assert isclose(record['hi'],record['estimate']+calculated_radius,rel_tol=1e-14)
        mass = record['subgroup_mass']
        feasible_lo, feasible_hi = -mass*config['reference'], mass*(1-config['reference'])
        diameter = feasible_hi-feasible_lo
        issued = record['status'] == 'CERTIFIED'
        lo, hi = max(record['lo'],feasible_lo), min(record['hi'],feasible_hi)
        empty = lo > hi
        width = max(0,hi-lo)
        tol = TOLERANCE*max(1,diameter)
        full_range = issued and not empty and width >= diameter-tol
        nontrivial = issued and diameter>0 and not empty and width < diameter-tol
        truth = record['oracle_truth']
        assert feasible_lo <= truth <= feasible_hi
        raw_covered = record['lo'] <= truth <= record['hi']
        clipped_covered = not empty and lo <= truth <= hi
        assert raw_covered == clipped_covered == record['covered']
        assert sum(record['group_sizes']) == record['B']
        rows.append(dict(
            nominal_level=1-record['nominal_delta'], nominal_delta=record['nominal_delta'],
            candidate_id=record['candidate_id'], replicate_id=record['replicate_id'], seed=record['seed'],
            status=record['status'], reason=record['reason'], issued=issued,
            raw_estimate=record['estimate'], raw_radius=record['stochastic_radius'],
            raw_lo=record['lo'], raw_hi=record['hi'], feasible_lo=feasible_lo, feasible_hi=feasible_hi,
            clipped_lo=lo, clipped_hi=hi, clipped_width=width, feasible_diameter=diameter,
            informativeness_fraction=1-width/diameter if diameter>0 else None,
            width_fraction=width/diameter if diameter>0 else None,
            raw_radius_fraction=record['stochastic_radius']/diameter if diameter>0 else None,
            is_full_range=full_range, is_nontrivial=nontrivial, is_empty_intersection=empty,
            tolerance=tol, raw_N=record['raw_N'], retained_N=record['retained_N'], B=record['B'],
            K=record['K'], L_min=L, L_max=max(record['group_sizes']), group_sizes=record['group_sizes'],
            discarded_rows=record['raw_N']-record['retained_N'],
            discarded_blocks=record['B']-sum(record['group_sizes']), n0=n0,
            chi_b=record['chi_by_block'], chi_max=chi, N_eff=record['N_eff'],
            minimum_group_N_eff=L*n0/chi, p=p, nu_p=record['nu_p'], C_p=record['C_p_used'],
            conditional_moment_bound_valid=True, nu_p_source=record['nu_p_source'],
            delta_stat=record['delta_stat'], epsilon_coup=record['coupling_failure_epsilon'],
            nuisance_radius=record['nuisance_radius'], drift_radius=record['drift_radius'],
            subgroup_prevalence=mass, graph_nodes=record['graph_nodes'],graph_edges=record['graph_edges'],
            subgroup_rows=record['effective_support_metrics']['subgroup_rows'],
            subgroup_independent_clusters=record['effective_support_metrics']['subgroup_independent_clusters'],
            importance_ess_diagnostic=ess, **quantiles(observed_weights,'observed_q_over_e'),
            **quantiles(state_weights,'all_state_q_over_e'),
            oracle_truth=truth, raw_covered=raw_covered, support_clipped_covered=clipped_covered,
            false_safe_certification=None, false_safe_reason='NOT_APPLICABLE_NO_SAFETY_THRESHOLD_OR_REPAIR_RULE'))
    candidates, families = [], []
    for alpha in sorted({r['nominal_delta'] for r in rows}):
        level = [r for r in rows if r['nominal_delta']==alpha]
        ids = sorted({r['candidate_id'] for r in level})
        for candidate in ids:
            group = [r for r in level if r['candidate_id']==candidate]
            first = group[0]
            item = {key:first[key] for key in ['nominal_level','nominal_delta','candidate_id','status','raw_radius',
                    'feasible_lo','feasible_hi','clipped_lo','clipped_hi','clipped_width','feasible_diameter',
                    'raw_N','retained_N','B','K','L_min','L_max','discarded_rows','discarded_blocks','n0','chi_max',
                    'N_eff','p','nu_p','C_p','delta_stat','epsilon_coup','nuisance_radius','drift_radius',
                    'subgroup_prevalence','graph_nodes','graph_edges','subgroup_rows','subgroup_independent_clusters']}
            item.update(replications=len(group), issued=sum(r['issued'] for r in group),
                        median_raw_estimate=median(r['raw_estimate'] for r in group),
                        min_raw_estimate=min(r['raw_estimate'] for r in group),
                        max_raw_estimate=max(r['raw_estimate'] for r in group),
                        median_raw_lo=median(r['raw_lo'] for r in group),median_raw_hi=median(r['raw_hi'] for r in group),
                        marginal_coverage=sum(r['raw_covered'] for r in group)/len(group),
                        marginal_nontrivial_rate=sum(r['is_nontrivial'] for r in group)/len(group),
                        full_range_rate=sum(r['is_full_range'] for r in group)/len(group),
                        median_width_fraction=median(r['width_fraction'] for r in group),
                        median_raw_radius_fraction=median(r['raw_radius_fraction'] for r in group),
                        informativeness_fraction=median(r['informativeness_fraction'] for r in group),
                        median_importance_ess_diagnostic=median(r['importance_ess_diagnostic'] for r in group))
            item.update({f'median_{key}':median(r[key] for r in group)
                         for key in first if key.startswith(('observed_q_over_e_','all_state_q_over_e_'))})
            candidates.append(item)
        events = []
        for rep in sorted({r['replicate_id'] for r in level}):
            group = [r for r in level if r['replicate_id']==rep]
            assert len(group)==len(ids)
            issued = all(r['issued'] for r in group)
            events.append((issued,all(r['raw_covered'] for r in group),
                           any(r['is_nontrivial'] for r in group),all(r['is_nontrivial'] for r in group)))
        count, issued = len(events), sum(e[0] for e in events)
        families.append(dict(nominal_level=1-alpha, nominal_delta=alpha, replications=count,
            family_size=len(ids), family_issued=issued, family_issuance_rate=issued/count,
            familywise_coverage=sum(e[1] for e in events)/count,
            familywise_coverage_given_issued=sum(e[0] and e[1] for e in events)/issued if issued else None,
            issued_and_family_covered_rate=sum(e[0] and e[1] for e in events)/count,
            familywise_nontrivial_rate_some=sum(e[2] for e in events)/count,
            familywise_nontrivial_rate_all=sum(e[3] for e in events)/count,
            marginal_nontrivial_rate=sum(r['is_nontrivial'] for r in level)/len(level),
            median_width_fraction=median(r['width_fraction'] for r in level),
            median_raw_radius_fraction=median(r['raw_radius_fraction'] for r in level),
            abstention_rate=1-issued/count, false_safe_certification=None,
            false_safe_reason='NOT_APPLICABLE_NO_SAFETY_THRESHOLD_OR_REPAIR_RULE'))
    output.mkdir(parents=True,exist_ok=True)
    for name, data in [('intervals',rows),('candidates',candidates),('family',families)]:
        save_csv(output/f'forensic_{name}.csv',data)
        (output/f'forensic_{name}.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    provenance=dict(baseline=BASELINE,input_records=len(saved),source_module_sha256=source_hashes,
                    original_report_sha256=report_hashes,
                    saved_run_git_head=meta['git_head'],saved_run_git_dirty=meta['git_dirty'],
                    saved_source_hashes_match_finalized_baseline=True,
                    saved_interval_sha256=hashlib.sha256((source/'intervals.json').read_bytes()).hexdigest(),
                    logging_replay='historical seeds only; no outcome draws; seed 0 full assignment equality verified',
                    new_outcomes_generated=0,new_replication_cells=0)
    (output/'forensic_provenance.json').write_text(json.dumps(provenance,indent=2,sort_keys=True)+'\n')
    write_report(report,candidates,families)
    print(f'Forensic complete: {len(rows)} saved intervals, {len(candidates)} candidate/level rows; 0 new outcomes.')


def write_report(path,candidates,families):
    lines = [
        '# Gate C0 forensic audit of the preserved Gate A+B smoke', '',
        f'Baseline: `{BASELINE}`. All source line references below are to that exact commit, not later C0 edits. '
        'The original artifacts were opened; no previous measurement is inferred from a task description. '
        'All original report bytes and saved source hashes are checked by `experiments/forensic_c0.py`. '
        'The analysis uses all 240 saved intervals (30 replications × two levels × four candidates). '
        'The saved smoke metadata honestly records a dirty precursor checkout at `58ad7bdf8965418cb8c3b48b2214fbc2aadd2a56`; '
        'every saved Python module SHA-256 matches the finalized d11a36f baseline. The finalized '
        'commit is therefore the line-reference anchor, not a claim that the smoke was executed '
        'with that later HEAD.', '',
        '## Confirmed diagnosis', '',
        '**The dominant cause is the conservative general finite-p moment/Markov conversion applied to a bounded-reward problem.** '
        'At p=1.5 it combines C_p=32^(2/3)=10.07937 with a loose, valid centered envelope '
        'nu_p=4.04808 or 4.75493. The current majority rule leaves only L_min=3 blocks per group, '
        'so the effective group size is L_min*n0/chi=24. The resulting radii are 14.14529 and '
        '16.61524, against feasible diameters 1 and 0.5. This is not caused by support clipping, '
        'an added coupling radius, a hidden bias budget, dropped rows, or a coding double-count of corrections.', '',
        'The causal arithmetic is explicit: r = 10.07937 × nu_p × 24^(-1/3). '
        'As a design-only diagnostic, even the hypothetical largest possible group L=128 (K=1) '
        'with the **same** moment/Markov formula gives r=nu_p=4.04808 or 4.75493, still larger '
        'than the entire feasible range. K=1 is not claimed to satisfy the family confidence budget. '
        'This proves that reducing K alone cannot make this original smoke design informative. '
        'The old grouping adds a factor (128/3)^(1/3)=3.49432 over that already-vacuous lower '
        'limit of the same formula. All h=0 rows are conservatively ignored by the envelope maximum, '
        'so subgroup moments receive the same raw radius while their feasible diameter halves.', '',
        '## Exact path through the baseline code', '',
        '| Stage | Verified source lines | Actual behavior |',
        '|---|---|---|',
        '| Frozen settings | `configs/smoke.json:2–14`; `comet/schema.py:43–78` | R=30, p=1.5, B=128, n0=32, chi=4, e1=(.2,.4), fixed mu_hat=(.5,.5), f=.25, q1=(.25,.75), h=all/group1; m=4 |',
        '| CLI / timing | `comet/smoke.py:33–68` | Configuration precedes generation; certify is called before oracle truth is joined |',
        '| DGP | `comet/synthetic.py:10–41`; `comet/truth.py:5–27` | Separate logging/outcome RNG streams; independent cluster records replicated four times; repeated exogenous context pattern; analytic conditional expectation truth |',
        '| Model guard | `comet/certification.py:15–46` | Checks registered design, exact e, fixed nuisance, binary Y, clique duplication; cannot discover an unreported hidden common shock from these checks alone |',
        '| DR | `comet/dr_scores.py:15–37` | Exact same-state e/q, no numerical clipping; known support |',
        '| Moment scale | `comet/dr_scores.py:40–52`; `comet/certification.py:105–109` | nu^p=max_context 2^(2p-1)[1+sum q^p e^(1-p)]; valid conditional bound, no outcome/oracle estimate |',
        '| K and grouping | `comet/robust_mean.py:21–45`; `comet/certification.py:82–104` | K=ceil(8 log(2m/delta)); B>=2K; all blocks assigned once in groups differing by at most one; median of complete-block means |',
        '| Raw radius/status | `comet/robust_mean.py:48–53`; `comet/certification.py:124–148` | r=32^(1/p)nu(chi/(L_min*n0))^((p-1)/p); raw endpoints estimate±r; CERTIFIED under registered DGP; nuisance/drift/coupling zero |',
        '| Existing feasible-range treatment | `comet/smoke.py:60–68,100–104` | Only a vacuity flag; **no support clipping occurred** in saved results |',
        '| Existing export/coverage | `comet/smoke.py:73–105`; `comet/metrics.py:39–63` | Full-range intervals retained in coverage; family denominators are replications, not candidate rows |', '',
        'For each binary h, the known feasible target interval is [-pi_h f, pi_h(1-f)], '
        'where pi_h is exactly 1 or .5. This forensic pass stores the additional intersection '
        'with that range without modifying the original interval files. Such intersection preserves '
        'coverage because the target belongs to the range. It cannot create information when the '
        'raw interval already contains that whole range. Nontriviality uses tolerance '
        '`1e-12*max(1, feasible_diameter)` and excludes empty intersections.', '',
        '## Each nominal level and candidate', '',
        'All point estimates/endpoints below are medians over the 30 original records; radii, '
        'feasible/clipped ranges, and design quantities are constant within each row. Full '
        'per-replication raw values are saved in `results/gate_C0/forensic_intervals.csv` and JSON.', '',
        '| Level | Candidate | Median estimate | Radius | Median raw [lo, hi] | Feasible = clipped [lo, hi] | Clipped width / diameter | Information | Nontrivial |',
        '|---|---|---:|---:|---|---|---:|---:|---:|']
    for r in candidates:
        lines.append(f"| {r['nominal_level']:.0%} | {r['candidate_id']} | {r['median_raw_estimate']:.6f} | "
                     f"{r['raw_radius']:.6f} | [{r['median_raw_lo']:.6f}, {r['median_raw_hi']:.6f}] | "
                     f"[{r['feasible_lo']:.3f}, {r['feasible_hi']:.3f}] | {r['median_width_fraction']:.3f} | "
                     f"{r['informativeness_fraction']:.3f} | {r['marginal_nontrivial_rate']:.0%} |")
    lines += ['', 'Both levels: raw_N=retained_N=4096, B=128, n0=32, chi_b=4 for every block, '
              'chi_max=4, N_eff=1024, graph nodes=4096, edges=6144. No rows or blocks discarded. '
              '95% uses K=41 (five groups of four blocks and 36 of three); 90% uses K=36 '
              '(20 groups of four and 16 of three). Both L_min=3 and L_max=4, explaining identical '
              'radii despite different levels and sometimes different point estimates. '
              'delta_stat=.05/.10 respectively; epsilon_coup=0, nuisance_radius=drift_radius=0. '
              'Every original record has status CERTIFIED, justified only by the specified '
              'independent-block synthetic model.', '',
              '## Coverage, informativeness and abstention', '',
              '| Level | Issued families | Family coverage | Coverage given issued | Some nontrivial | All nontrivial | Marginal nontrivial | Median clipped width / diameter | Median raw radius / diameter |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in families:
        lines.append(f"| {r['nominal_level']:.0%} | {r['family_issued']}/{r['replications']} | "
                     f"{r['familywise_coverage']:.0%} | {r['familywise_coverage_given_issued']:.0%} | "
                     f"{r['familywise_nontrivial_rate_some']:.0%} | {r['familywise_nontrivial_rate_all']:.0%} | "
                     f"{r['marginal_nontrivial_rate']:.0%} | {r['median_width_fraction']:.3f} | "
                     f"{r['median_raw_radius_fraction']:.6f} |")
    lines += ['', 'No full-range interval was omitted. Each level has zero abstention and 100% full-range '
              'intervals; the 30/30 family coverage has Wilson 95% uncertainty [0.88649,1], as in '
              'the preserved table. It is debugging output, not coverage evidence for a final paper. '
              'False-safe certification is **not applicable**, not zero: this smoke defined no '
              'safety threshold or policy-selection rule.', '',
              '## q/e and support accounting', '',
              'The interval artifact retained only maxima/ESS, and only seed 20261112 has a full saved '
              'log. To recover every replication’s missing quantiles, the script replays **only the '
              'historical logging assignment stream** from the saved seeds and baseline algorithm; '
              'it generates no outcomes, no new truths and no new replication-cells. The first saved seed’s '
              'assignments agree exactly with its saved log; all 30 replays agree with saved maximum '
              'observed weights and ESS. The q/e columns distinguish realized observed exposures '
              'from all row/exposure states given equal state weight. The latter is not the logging '
              'probability-weighted distribution. Linear empirical quantiles are used.', '',
              '| Policy q1 | Observed q/e min, median, p95, p99, max (median across seeds) | All-state q/e min, median, p95, p99, max | Median importance ESS |',
              '|---|---|---|---:|']
    for r in candidates:
        if r['nominal_delta'] != .05 or not r['candidate_id'].endswith('__all'):
            continue
        observed=', '.join(f"{r['median_observed_q_over_e_'+k]:.5f}" for k in ['min','median','p95','p99','max'])
        states=', '.join(f"{r['median_all_state_q_over_e_'+k]:.5f}" for k in ['min','median','p95','p99','max'])
        lines.append(f"| {r['candidate_id'].split('__')[0]} | {observed} | {states} | {r['median_importance_ess_diagnostic']:.3f} |")
    lines += ['', 'The all auditor has 4096 rows / 1024 independent clusters and prevalence 1; '
              'group1 has 2048 rows / 512 independent clusters and prevalence .5. Minimum logging '
              'probability is .2. There is no support failure. ESS is diagnostic, not substituted '
              'for the theorem’s graph effective sample size. Neither positive subgroup mass nor '
              'moderate importance ratios rescues the large certified radius.', '',
              '## Reproducibility and unchanged prior records', '',
              'Run `.venv/bin/python experiments/forensic_c0.py`. The script checks original source '
              'hashes against d11a36f, checks every original report byte against the same commit, '
              'checks all 240 radius/endpoints/coverage records, and writes separate C0 files. '
              '`forensic_intervals.csv/json` contains every requested per-record design/radius/status '
              'quantity including full chi_b and group_sizes; `forensic_candidates.csv/json` and '
              '`forensic_family.csv/json` contain the compact summaries. '
              '`forensic_provenance.json` records hashes and the zero-new-outcome replay statement. '
              'No original report, test, source result, or failed-run log is removed or overwritten.', '']
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text('\n'.join(lines))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='results/gate_C0')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    analyze(root,root/args.output,root/'reports/gate_C0_forensic.md')


if __name__=='__main__':
    main()

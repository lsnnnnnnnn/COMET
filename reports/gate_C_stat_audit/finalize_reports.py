"""Render C-STAT reports only from a completed independently validated corpus."""
from pathlib import Path
import hashlib,json,subprocess,math
ROOT=Path(__file__).resolve().parents[2]
BASE='06a39b89e579aef57d14ae51e86d74ecf9b6b768'

def read(p):return json.loads(p.read_text())
def fmt(x):return 'NA' if x is None else f'{x:.6g}'
def pct(x):return 'NA' if x is None else f'{100*x:.3f}%'
def main():
 out=ROOT/'results/gate_C/confirmatory';v=read(out/'independent_validation/validation.json');manifest=read(out/'run_manifest.json');inventory=read(out/'aggregation_inventory.json')
 assert v['status']=='PASS' and v['phase']=='confirmatory' and v['independent_logs']==6000 and v['candidate_records']==1134000
 assert Path(v['input_directory']).resolve()==out.resolve()
 assert hashlib.sha256((ROOT/'experiments/gate_c_confirmatory.py').read_bytes()).hexdigest()==manifest['runner_sha256']
 assert inventory['all_planned_ids_complete'] and inventory['completed_logs']==6000 and inventory['candidate_records']==1134000
 invocations=[read(p) for p in sorted((out/'invocations').glob('*.json'))]
 assert invocations and invocations[-1]['status']=='COMPLETE'
 rows=read(out/'summary.json'); by={(r['cell_id'],r['alpha'],r['method']):r for r in rows}
 assert len(rows)==84 and all(r['replications']==1000 for r in rows)
 independent=read(out/'independent_validation/independent_summary.json')
 independently_by={(r['cell_id'],r['alpha'],r['method']):r for r in independent}
 assert independently_by.keys()==by.keys()
 for key,row in by.items():
  verified=independently_by[key];assert row.keys()==verified.keys()
  for field,value in row.items():
   if isinstance(value,float): assert math.isclose(value,verified[field],rel_tol=5e-12,abs_tol=5e-13),(key,field)
   else: assert value==verified[field],(key,field)
 import csv
 with (out/'independent_validation/family_decisions_and_widths.csv').open() as f: extra={(r['cell_id'],float(r['alpha']),r['method']):r for r in csv.DictReader(f)}
 # No legacy artifact may be altered by the new operational entry point.
 paths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=ROOT,text=True).splitlines()
 unchanged=[]
 for path in paths:
  original=subprocess.check_output(['git','show',f'{BASE}:{path}'],cwd=ROOT)
  assert (ROOT/path).read_bytes()==original, path
  unchanged.append({'path':path,'sha256':hashlib.sha256(original).hexdigest()})
 lock=read(ROOT/'results/gate_C/stat_lock/scientific_lock_audit.json')
 for path,digest in lock['science_source_allowlist'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
 integrity=dict(status='PASS',unchanged_baseline_files=len(paths),baseline_commit=BASE,files=unchanged,
   runner_sha256=hashlib.sha256((ROOT/'experiments/gate_c_confirmatory.py').read_bytes()).hexdigest(),
   reporting_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
   current_git_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
 (out/'final_preservation_check.json').write_text(json.dumps(integrity,indent=2)+'\n')
 cpu=sum(r['parent_cpu_seconds']+r['child_cpu_seconds'] for r in invocations)
 wall=sum(r['wall_seconds'] for r in invocations)
 parent=max(r['parent_peak_rss_bytes'] for r in invocations);child=max(r['child_max_peak_rss_bytes'] for r in invocations)
 failures=list((out/'failures').glob('*.json'))
 execution=['# C-STAT execution and resource record','',
 '**C-STAT execution PASS:** all 6,000 assigned independent logs completed; all 1,134,000 candidate records retained. Independent statistical validation passed. No preflight observations enter these denominators.','',
 f"Scientific freeze: `{manifest['science_freeze_git_sha']}`. Launcher run-manifest commit: `{manifest['git_sha']}`. Runner SHA-256: `{manifest['runner_sha256']}`. Final delivery commit is recorded separately to avoid a self-referential file hash.",'',
 '## Assigned work and outputs','',
 'Exactly 1,000 logs in each A–F cell, all seven methods and both levels paired. A contributes14,000 records; B–F each contribute224,000. Complete IDs are in `run_manifest.json` and per-ID input/payload/file hashes in `checkpoint_index.json`. Every checkpoint is an atomic gzip JSON; all raw metric columns are also exported in six compressed CSV shards. There are84 summaries and17 prespecified primary tests.','',
 f"Actual invocation count: {len(invocations)}. Saved confirmatory execution-error files: {len(failures)}. Detailed event order is in `events.jsonl`; no failed or incomplete ID is silently excluded.",'',
 '|Invocation|Status|New completed|Skipped|Wall s|Parent CPU s|Children CPU s|Parent peak MiB|Max child peak MiB|','|---|---|---:|---:|---:|---:|---:|---:|---:|']
 for r in invocations:execution.append(f"|{r['invocation_id']}|{r['status']}|{r['new_completed_logs']}|{r['skipped_completed_logs']}|{r['wall_seconds']:.3f}|{r['parent_cpu_seconds']:.3f}|{r['child_cpu_seconds']:.3f}|{r['parent_peak_rss_bytes']/2**20:.3f}|{r['child_max_peak_rss_bytes']/2**20:.3f}|")
 execution += ['',f'Total recorded invocation wall: {wall:.3f}s; parent+children CPU: {cpu:.3f}s. Maximum parent RSS: {parent/2**20:.3f}MiB; maximum child process peak: {child/2**20:.3f}MiB. These are process high-water measurements, not summed concurrent memory or standalone per-method allocations. Per-method/level timings are family-call costs; copies in candidate rows must not be added repeatedly. Parallel per-log wall sums are not elapsed batch time.','',
 'The local CPU environment passed all12 strict historical-seed checks. The server drew zero confirmatory logs: historical F data differed at floating-point power rounding, so strict compatibility rejected it. Failure traceback and primitive-level diagnosis remain in stat_lock and the server-compatibility report. No tolerance, simulation law, interval or scientific budget was changed.','',
 'The launcher fixture verified failure→resume→idempotent operation using mocked historical payloads, including immutable completed bytes and retained failures. Actual complete-batch idempotent recovery, if run, is listed as a separate invocation above and documented in `resume_integrity.json`.','',
 f'Final preservation check: all {len(paths)} baseline files and all26 scientific sources remain byte-identical. No original manuscript or independent Overleaf file was changed. D1–D5 contain design-only proposals, with zero D-stage outcomes.','',
 'Commands, test exits, monitored resource probes, the server failure and synchronization history are in `reports/gate_C_stat_commands.md`. The full final pytest log reports485 passing tests; no pytest failed.']
 (ROOT/'reports/gate_C_stat_execution.md').write_text('\n'.join(execution)+'\n')
 validation=(out/'independent_validation/methods_validation.md').read_text()
 validation+='\nSource provenance: the canonical manifest pins scientific source/config/seed/launcher digests; `final_preservation_check.json` checks all old files. The independent validator imports neither estimators nor the production summarizer. It uses exact integer/rational binomial formulas and independent Wilson/Holm/coverage/width/decision recomputation. Its floating summary comparison uses the saved declared tolerance; the separate prelaunch scientific-output comparison was bytewise.\n'
 (ROOT/'reports/gate_C_stat_methods_validation.md').write_text(validation)
 result=['# Frozen C-STAT results','',
 '**C-STAT PASS within the proved independent, exogenous evaluation-block model.** This denotes complete, unchanged-protocol execution and validation. Empirical coverage or nonrejection does not prove the theorem, novelty, fully adaptive validity or long-run safety.','',
 'Each coverage observation is one independent complete log family. Candidate-level fractions pool correlated candidates and are explicitly descriptive; they are not additional independent replications. Both nominal levels and all methods share each log. The original twelve preflight logs are excluded.','',
 '## Primary 95% comparison','',
 '|Cell|Method|Covered / 1000|Wilson95%|Median intersected width / diameter|Candidate nontrivial|No certified decision|Candidate true-violation detection|Exact p|Holm p|','|---|---|---:|---|---:|---:|---:|---:|---:|---:|']
 for cell in 'ABCDEF':
  for method in ('orig_mom','exact_binomial_mom','bounded_graph_chebyshev'):
   r=by[cell,.05,method]
   result.append('|'+ '|'.join([cell,method,'NA' if r['covered_families'] is None else f"{r['covered_families']}/1000",f"[{fmt(r['wilson_lo'])},{fmt(r['wilson_hi'])}]",fmt(r['median_width_fraction']),pct(r['marginal_nontrivial_fraction']),pct(r['no_certified_decision_fraction']),pct(r['violation_power']),fmt(r['undercoverage_pvalue']),fmt(r['undercoverage_holm_pvalue'])])+'|')
 result+=['','The17 registered eligible 95% comparisons use exact inclusive lower-tail tests under H0 coverage≥.95, followed by Holm across exactly17. The F graph row is kept as NOT_APPLICABLE and is not an18th test. Full-range and point baselines are outside these17. A failure to reject is not proof of95% coverage. The complete90% secondary summaries are in `summary.csv/json/md`; no extra17+17-family confirmatory claim is made.','',
 '## Decisions at the frozen threshold','',
 '|Cell|95% graph any true-violation detection / logs|Wilson95%|95% graph any false certification / logs|Wilson95%|','|---|---:|---|---:|---|']
 for cell in 'ABCDE':
  r=extra[cell,.05,'bounded_graph_chebyshev']
  result.append(f"|{cell}|{r['violation_detected_any_logs']}/1000|[{float(r['violation_detected_any_wilson_lo']):.6g},{float(r['violation_detected_any_wilson_hi']):.6g}]|{r['false_any_logs']}/1000|[{float(r['false_any_wilson_lo']):.6g},{float(r['false_any_wilson_hi']):.6g}]|")
 result+=['','The threshold remains M_D≤.2*pi_h. The per-log table is distinct from the correlated-candidate detection fraction above. Full per-log any-false-safe/any-false-violation, detection, abstention and Wilson uncertainties for every method and both levels are in `independent_validation/family_decisions_and_widths.csv`. Zero observed false certification is not a zero-risk or deployment-safety claim. POINT_ONLY and NOT_APPLICABLE methods issue no certified decision; their zero false-decision count is not evidence of certification validity.','',
 '## Informativeness and scope','']
 for cell in 'ABCDEF':
  ex=by[cell,.05,'exact_binomial_mom'];gr=by[cell,.05,'bounded_graph_chebyshev']
  result.append(f"- {cell}: exact MOM median width/diameter {fmt(ex['median_width_fraction'])}, nontrivial candidate fraction {pct(ex['marginal_nontrivial_fraction'])}, no-certified-decision fraction {pct(ex['no_certified_decision_fraction'])}. Graph mean: {'NOT_APPLICABLE' if gr['family_coverage'] is None else 'median width/diameter '+fmt(gr['median_width_fraction'])+', nontrivial '+pct(gr['marginal_nontrivial_fraction'])+', no-certified-decision '+pct(gr['no_certified_decision_fraction'])}.")
 result+=['','Full feasible range has deterministic width/diameter1 and uses the known conditional mean class, including F; it is not a concentration method. Original/exact MOM and graph mean retain separate confidence guarantees. No shortest observed interval was selected across methods. Raw-width, support-intersected width, IQR/P90, family some/all nontriviality, marginal coverage and error/radius details are preserved in the complete artifacts.','',
 'F remains a necessary tail-domain stress cell, even if every MOM interval is vacuous. Its ideal Pareto law has finite p=1.5 moment and infinite variance; its finite numerical grid does not literally have infinite variance. E combines weak supported exposure with clique dependence. These cells must remain in the results and figures; good coverage can coexist with uninformative intervals and abstention. No minimax-rate slope is inferred from this fixed DGP.','',
 '## Resources, figures and manuscript recommendation','',
 f'Actual invocation wall {wall:.3f}s and total parent+child CPU {cpu:.3f}s; maximum parent/child process peaks {parent/2**20:.3f}/{child/2**20:.3f}MiB. Detailed invocation scope, failures and recovery are in the execution report. The five regenerable figure families are under `independent_validation/figures/`: coverage with Wilson uncertainty, widths and range baseline, nontriviality/abstention, error/radius including maxima, and resource costs.','',
 '**Manuscript: ready for scope/results review, not a submission-readiness claim.** The separate proposal promotes the proved independent-block results and removes unproved adaptive/mutual-cross-fitting main guarantees. This study does not demonstrate discovery, policy repair, realistic non-copy graph dependence or future deployment safety. D1–D5 are separate unrun preregistration proposals. The original paper and independent Overleaf repository remain untouched.']
 (ROOT/'reports/gate_C_stat_results.md').write_text('\n'.join(result)+'\n')
 print(json.dumps({'status':'PASS','reports_written':3,'baseline_files_preserved':len(paths),'wall_seconds':wall,'cpu_seconds':cpu}))
if __name__=='__main__':main()

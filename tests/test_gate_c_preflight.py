from hashlib import sha256
import json
from pathlib import Path

import pytest

from comet.gate_c_seeds import build_seed_manifest, seed_streams, STREAM_NAMES
from experiments import gate_c_preflight as runner


def frozen_fixture(tmp_path):
    seeds=build_seed_manifest(71,['A'],2,3)
    seedfile=tmp_path/'seeds.json'; seedfile.write_text(json.dumps(seeds))
    cell=dict(cell_id='A',design=dict(B=16,n0=8,chi=1,e_by_context=[.5,.5],
              mu_hat=[.5,.5],reference=.25,q_probs=[.5],auditors=['all']),p=2.)
    config=dict(phase_authorized='preflight',cells=[cell],methods=[
        'orig_mom','exact_binomial_mom','bounded_graph_chebyshev','ips','dm','dr','full_feasible_range'],
        alphas=[.05,.1],preflight_reps_per_cell=2,confirmatory_reps_per_cell=3,
        constraint_per_subgroup_mass=.2,seed_manifest_path=str(seedfile),
        seed_manifest_sha256=sha256(seedfile.read_bytes()).hexdigest(),
        primary_comparisons=[dict(cell_id='A',method=m,alpha=.05)
                             for m in ['orig_mom','exact_binomial_mom','bounded_graph_chebyshev']])
    path=tmp_path/'config.json';path.write_text(json.dumps(config))
    return path


def test_frozen_seeds_are_disjoint_across_phase_replication_and_mechanism():
    seeds=build_seed_manifest(2026111203,['A','B'],2,3)
    values=[s for r in seeds['runs'] for s in r['streams'].values()]
    assert len(values)==len(set(values))
    assert seed_streams(2026111203,'preflight','A',0)==seed_streams(2026111203,'preflight','A',0)
    assert set(seed_streams(1,'preflight','A',0))==set(STREAM_NAMES)
    assert all('confirmatory' in r['run_id'] for r in seeds['runs'] if r['phase']=='confirmatory')


def test_checkpoint_crash_resume_preserves_completed_bytes_and_never_repeats(tmp_path, monkeypatch):
    path=frozen_fixture(tmp_path); output=tmp_path/'results'
    real=runner.evaluate_run; calls=[]
    def counted(cell,entry,settings,provenance):
        calls.append(entry['run_id'])
        return real(cell,entry,settings,provenance)
    monkeypatch.setattr(runner,'evaluate_run',counted)
    with pytest.raises(RuntimeError,match='INTENTIONAL_CHECKPOINT_RESUME_TEST'):
        runner.run(path,output,crash_after_completed=1)
    first=output/'runs/A/0000.json'; original=first.read_bytes()
    assert len(list((output/'failures').glob('*.json')))==1
    runner.run(path,output,resume=True)
    assert first.read_bytes()==original
    assert calls==['gate-c-v1/preflight/A/0000','gate-c-v1/preflight/A/0001']
    csv_bytes=(output/'preflight_intervals.csv').read_bytes()
    summary_bytes=(output/'preflight_summary.json').read_bytes()
    runner.run(path,output,resume=True)
    assert len(calls)==2
    assert (output/'preflight_intervals.csv').read_bytes()==csv_bytes
    assert (output/'preflight_summary.json').read_bytes()==summary_bytes
    events=[json.loads(line)['event'] for line in (output/'events.jsonl').read_text().splitlines()]
    assert events.count('RUN_COMPLETED')==2 and events.count('RUN_SKIPPED_COMPLETED')==3
    assert 'INJECTED_CRASH_AFTER_CHECKPOINT' in events
    manifest=runner.read_json(output/'run_manifest.json')
    assert not manifest['confirmatory_outcomes_authorized']
    assert runner.read_json(output/'last_invocation.json')['new_completed_logs']==0


def test_resume_refuses_changed_configuration_and_corrupt_checkpoint(tmp_path):
    path=frozen_fixture(tmp_path); output=tmp_path/'results'
    runner.run(path,output)
    config=json.loads(path.read_text());config['constraint_per_subgroup_mass']=.3
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError,match='configuration/source changed'):
        runner.run(path,output,resume=True)
    config['constraint_per_subgroup_mass']=.2;path.write_text(json.dumps(config))
    checkpoint=output/'runs/A/0000.json'
    payload=json.loads(checkpoint.read_text());payload['payload']['raw_N']=9
    checkpoint.write_text(json.dumps(payload))
    with pytest.raises(ValueError,match='checkpoint mismatch'):
        runner.run(path,output,resume=True)


def test_primary_manifest_has_six_cells_and_only_twelve_preflight_draws():
    root=Path(__file__).resolve().parents[1]
    settings,cells,entries,_=runner.load_inputs(root/'configs/gate_C_frozen.json')
    assert list(cells)==list('ABCDEF') and len(entries)==12
    assert len(settings['primary_comparisons'])==17
    assert settings['confirmatory_reps_per_cell']==1000
    assert all(e['phase']=='preflight' for e in entries)
    assert [c.design.B*c.design.n0 for c in cells.values()]==[8192]+[32768]*5

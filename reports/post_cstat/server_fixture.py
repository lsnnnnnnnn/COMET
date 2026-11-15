"""Explicit arithmetic portability fixture. No production RNG or run IDs drawn."""
import json
from pathlib import Path
import numpy as np
import experiments.anchor_runner as a
import experiments.negative_controls as c
from experiments.core_graph_dgp import WORD_GRID
from experiments.post_cstat_runner import environment_signature

def forbidden(*args,**kwargs):raise AssertionError('portability fixture invoked a sampler')
a.draw_anchor_log=forbidden;a.draw_core_log=forbidden;c.draw_negative_log=forbidden
np.random.default_rng=forbidden

def explicit(cell,seed):
    words=np.where(np.arange(cell.n)%2==0,WORD_GRID-1,0).astype(np.uint64)
    primitives={s:(-1. if j%2==0 else 1.) for j,s in enumerate(cell.core.outcome_source_ids)}
    return a.anchor_from_primitives(cell,words,primitives,seed_namespace='explicit-portability-fixture-only')

cfg=json.loads(Path('configs/post_cstat/ANCHORS_server_v2.json').read_text())
cfg.update(suite='DETERMINISTIC_ANCHOR_FIXTURE',fixture_N=512,levels=[.05,.1],raw_debug_run_ids=[],git_sha='explicit-portability-fixture',master_seed=7,seed_domain='comet-post-cstat-v1/ANCHORS/deterministic-portability')
outputs={}
for cell_id in a.anchor_cells():
    cell,plans=a.build_anchor_plans(cfg,cell_id)
    result=a._execute({'config':cfg},'comet-post-cstat-v1/ANCHORS/'+cell_id+'/0000',cell,plans,explicit,a.anchor_truths,{'code':'fixture-only','config':'fixture-only'})
    for key in ('wall_seconds','cpu_seconds'):result.pop(key,None)
    log=explicit(cell,0)
    result['explicit_observations']={'actions':log.actions.tolist(),'outcomes':log.outcomes.tolist()}
    outputs[cell_id]=result
for control in c.CONTROLS:
    d=c.build_negative_design(control,128,namespace='explicit-portability-negative')
    denom=5 if c.control_specs()[control]['actual_e1']==.2 else 2
    codes=np.arange(d.n,dtype=np.int64)%denom
    spikes=np.ones(d.n,dtype=np.uint16);spikes[0]=0
    log=c.generate_negative_from_primitives(d,codes,shared_sign=1,spike_codes=spikes)
    outputs[control]=c.evaluate_negative_unit(d,log,numerical_guard=1e-10)
print(json.dumps(dict(environment=environment_signature(),new_scientific_draws=0,fixture_values=outputs),sort_keys=True,allow_nan=False))

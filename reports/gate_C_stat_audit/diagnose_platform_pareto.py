"""Historical F0000 platform diagnostic only; never draws confirmatory IDs.

Run from the repository root. The frozen sampler is used unchanged; a separate
trace of its primitive draws locates machine-arithmetic differences.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import platform
from random import Random
import sys

sys.path.insert(0,str(Path.cwd()))
from comet.gate_c_contract import cell_from_dict
from comet.gate_c_simulation import generate_evaluation


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    config=json.loads(Path('configs/gate_C_frozen.json').read_text())
    cell=cell_from_dict(next(c for c in config['cells'] if c['cell_id']=='F'))
    manifest=json.loads(Path('configs/gate_C_seed_manifest.json').read_text())
    entry=next(e for e in manifest['runs'] if e['phase']=='preflight' and e['cell_id']=='F' and e['replicate']==0)
    assert entry['run_id']=='gate-c-v1/preflight/F/0000'
    log=generate_evaluation(cell,entry['streams'],entry['run_id'])
    rows=[[r.unit_id,r.block_id,r.cluster_id,r.context,r.observed_exposure_s,r.reward_y] for r in log.rows]
    digest=hashlib.sha256(b''.join(canonical(r).encode()+b'\n' for r in rows)).hexdigest()
    rng=Random(entry['streams']['potential_outcomes'])
    traces=[]
    for cluster in range(cell.design.B*cell.design.n0//cell.design.chi):
        context=cluster%2
        for exposure in (0,1):
            uniform=(rng.getrandbits(53)+1)/2**53
            sign=1 if rng.getrandbits(1) else -1
            power=uniform**(-1/cell.tail_alpha)
            noise=sign*cell.tail_scale*power
            mean=((4,12),(7,16))[context][exposure]/20
            outcome=mean+noise
            traces.append(dict(cluster_id=cluster,exposure=exposure,uniform_hex=uniform.hex(),sign=sign,
                exponent_hex=(-1/cell.tail_alpha).hex(),power_hex=power.hex(),noise_hex=noise.hex(),
                mean_hex=mean.hex(),outcome_hex=outcome.hex()))
    for row in log.rows:
        trace=traces[2*row.cluster_id+row.observed_exposure_s]
        assert float.fromhex(trace['outcome_hex'])==row.reward_y
    result=dict(run_id=entry['run_id'],phase='historical_preflight_diagnostic',confirmatory_draws=0,
        environment=dict(python=sys.version,platform=platform.platform(),machine=platform.machine()),
        sampler_sha256=hashlib.sha256(Path('comet/gate_c_simulation.py').read_bytes()).hexdigest(),
        observed_data_sha256=digest,rows=rows,primitive_traces=traces)
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists(): raise ValueError('Refusing to replace diagnostic evidence')
    with gzip.open(target,'wt') as stream: stream.write(canonical(result)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','primitive_traces')},indent=2))

if __name__=='__main__': main()

"""Trial-local design-moment memoization around the unchanged frozen E5 runner.

The audited E5 path never mutates its frozen coefficient/exposure/nuisance
arrays or the private moment arrays created by certifier_inputs/moment helpers.
Only those inputs are memoized. Evaluation labels, graph calls, plans, intervals,
selectors, IDs and frozen fingerprints follow the original code unchanged.
"""

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import shlex
import time

import numpy as np

from comet.checkpoint_store import canonical_bytes, install_once
from comet import residual_truncation as theory
from experiments import pipeline_dgp as dgp
from experiments import pipeline_runner as runner


@contextmanager
def cached_trial_design_moments():
    """One synchronous worker; every cache is discarded after one whole trial.

    First calls use the original validators and algebra. Repeated calls require
    identical immutable array objects (or identical immutable scalar bounds).
    Private newly derived moment arrays are retained only on this audited path,
    whose callers read them without modification. No array flags/types change.
    Returning a dict copy preserves _certify's per-arm graph substitution.
    """
    original_execute=runner._execute_trial
    original_inputs=dgp.FrozenPipeline.certifier_inputs
    original_bounded=theory.bounded_residual_moments
    original_envelope=theory.residual_moment_envelope
    stats=dict(executed_trials=0,certifier_input_hits=0,certifier_input_misses=0,
        bounded_moment_hits=0,bounded_moment_misses=0,envelope_hits=0,envelope_misses=0)

    def execute(*args,**kwargs):
        input_cache,bounded_cache,envelope_cache,owned={},{},{},{}

        def immutable(array):
            return (isinstance(array,np.ndarray) and (not array.flags.writeable
                    or owned.get(id(array)) is array))

        def inputs(frozen,channel):
            key=id(frozen),channel
            if key in input_cache:
                saved,values=input_cache[key]
                if saved is not frozen:raise ValueError("trial design cache identity mismatch")
                stats["certifier_input_hits"]+=1
            else:
                values=original_inputs(frozen,channel)
                # FrozenPipeline's method depends only on immutable split/fit;
                # this private result is never mutated by the original caller.
                owned[id(values["residual_moments"])]=values["residual_moments"]
                input_cache[key]=(frozen,values)
                stats["certifier_input_misses"]+=1
            return dict(values)

        def bound_key(value):
            if np.isscalar(value) and np.isfinite(value):return ("scalar",type(value),float(value).hex())
            if isinstance(value,np.ndarray) and not value.flags.writeable:
                # Original make_plan broadcasts immutable scalar bounds to d.shape.
                # Every element then is that exact scalar; no content hash/scan.
                if value.size and all(stride==0 for stride in value.strides):
                    scalar=value.flat[0]
                    if np.isfinite(scalar):return ("broadcast_scalar",value.dtype.str,value.shape,float(scalar).hex())
                return ("array_identity",id(value))
            return None

        def bounded(lower,upper,nuisance,p):
            lower_key,upper_key=bound_key(lower),bound_key(upper)
            if lower_key is None or upper_key is None or not immutable(nuisance):
                stats["bounded_moment_misses"]+=1
                return original_bounded(lower,upper,nuisance,p)
            key=lower_key,upper_key,id(nuisance),p
            if key in bounded_cache:
                saved_lower,saved_upper,saved_fit,result=bounded_cache[key]
                if saved_fit is not nuisance:raise ValueError("trial moment cache identity mismatch")
                stats["bounded_moment_hits"]+=1
                return result
            result=original_bounded(lower,upper,nuisance,p)
            owned[id(result)]=result
            bounded_cache[key]=(lower,upper,nuisance,result)
            stats["bounded_moment_misses"]+=1
            return result

        def envelope(coefficients,exposure,residual_moments,p):
            arrays=coefficients,exposure,residual_moments
            if not all(immutable(value) for value in arrays):
                stats["envelope_misses"]+=1
                return original_envelope(*arrays,p)
            key=tuple(id(value) for value in arrays)+(p,)
            if key in envelope_cache:
                saved,result=envelope_cache[key]
                if not all(left is right for left,right in zip(saved,arrays)):
                    raise ValueError("trial envelope cache identity mismatch")
                stats["envelope_hits"]+=1
                return result
            result=original_envelope(*arrays,p)
            envelope_cache[key]=(arrays,result)
            stats["envelope_misses"]+=1
            return result

        dgp.FrozenPipeline.certifier_inputs=inputs
        theory.bounded_residual_moments=bounded
        theory.residual_moment_envelope=envelope
        try:
            result=original_execute(*args,**kwargs)
            stats["executed_trials"]+=1
            return result
        finally:
            dgp.FrozenPipeline.certifier_inputs=original_inputs
            theory.bounded_residual_moments=original_bounded
            theory.residual_moment_envelope=original_envelope

    runner._execute_trial=execute
    try:yield stats
    finally:
        runner._execute_trial=original_execute
        dgp.FrozenPipeline.certifier_inputs=original_inputs
        theory.bounded_residual_moments=original_bounded
        theory.residual_moment_envelope=original_envelope


def run_pipeline_fast(protocol_path,results_root,**kwargs):
    protocol_path,root=Path(protocol_path),Path(results_root)
    protocol_bytes=protocol_path.read_bytes();manifest=json.loads(protocol_bytes)
    invocation_id=str(time.time_ns())
    record=dict(schema="post-cstat-operational-trial-moment-cache-v1",
        operational_invocation_id=invocation_id,operational_launcher=str(Path(__file__).resolve()),
        operational_launcher_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        protocol_file_sha256=hashlib.sha256(protocol_bytes).hexdigest(),
        unchanged_scientific_fingerprint=manifest["fingerprint"],
        cache_scope="identical immutable design inputs within one synchronous complete E5 trial",
        source_checks="unchanged original startup and per-unit checks",
        scientific_parameters_changed=False,legacy_new_outcome_draws=0,background_work_running=False)
    directory=root/"operational_invocations"
    install_once(directory/(invocation_id+".started.json"),canonical_bytes(record)+b"\n")
    stats,result,error={},None,None
    try:
        with cached_trial_design_moments() as stats:
            result=runner.run_pipeline(protocol_path,root,**kwargs)
        return result
    except BaseException as exc:
        error=f"{type(exc).__name__}: {exc}";raise
    finally:
        finished=dict(record,cache_statistics=dict(stats),error=error,
            status=result["status"] if result else "EXITED_WITH_EXCEPTION",
            new_completed_units=result.get("new_completed_units") if result else None,
            remaining_ids=result.get("remaining_ids") if result else None,
            fast_resume_command=shlex.join([".venv/bin/python","-m","experiments.pipeline_fast","--run-E5",
                "--protocol",str(protocol_path),"--results",str(root)]))
        install_once(directory/(invocation_id+".finished.json"),canonical_bytes(finished)+b"\n")


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-E5",action="store_true",required=True)
    parser.add_argument("--protocol",type=Path,required=True)
    parser.add_argument("--results",type=Path,required=True)
    parser.add_argument("--max-new-units",type=int)
    args=parser.parse_args(argv)
    if json.loads(args.protocol.read_text())["config"].get("suite")!="E5":
        raise ValueError("CLI requires the existing frozen E5 protocol")
    print(json.dumps(run_pipeline_fast(args.protocol,args.results,max_new_units=args.max_new_units),indent=2,allow_nan=False))


if __name__=="__main__":main()

"""Eight supplemental strong-baseline/scaling anchors, 200 logs each.

This is the combined 1,600-unit allowance, not another primary-study grid.
Each immutable whole-log checkpoint shares data across methods and levels.
E0 is never regenerated. CLI production requires a committed frozen protocol.
"""

import argparse
from collections import Counter
from dataclasses import dataclass, replace
import gzip
import hashlib
import json
import math
from pathlib import Path
import shlex
import subprocess
import time

import numpy as np

from comet.checkpoint_store import (CheckpointStore, NAMESPACE, canonical_bytes, digest,
    file_hashes, freeze_protocol, install_once, planning_input_hashes)
from comet.independent_anchors import catoni_iid, ope_betting_iid
from comet.ope_2024 import ope_eb_independent
from comet.post_cstat_statistics import EVENTS, WholeTrialSummary, adjust_validity_family, paired_endpoint_difference
from comet.queries import SignedQuery
from comet.residual_truncation import CERTIFIED, certified_decision, make_plan
from experiments.core_graph_dgp import (CoreLog, TAIL_EXPONENT, WORD_GRID, _readonly,
    build_core_design, draw_core_log, dyadic_probabilities, evaluate_oracle, generate_from_primitives)
from experiments.extension_runner import GlobalBudget
from experiments.post_cstat_analyze import _csv_bytes
from experiments.post_cstat_runner import (BOUNDED_METHODS, CORE_METHODS, GIB, LEVELS,
    REPOSITORY, SOURCE_NAMES, ResourceLimitError, _cell_metadata, _compact_record,
    _resource_check, _source_stamps, _trial_metrics, _verify_changed_sources,
    environment_signature, resource_snapshot)


CATONI = "bhatt2022_catoni_iid"
OPE21 = "author_one_dimensional_ope_betting"
OPE24 = "waudby_smith_2024_dr_eb_independent"
METHODS = CORE_METHODS + BOUNDED_METHODS + (CATONI, OPE21, OPE24)
EXTRA_SOURCES = ("comet/independent_anchors.py", "comet/ope_2024.py",
    "comet/audit_pipeline.py", "comet/paired_contrasts.py", "experiments/suite_designs.py",
    "experiments/anchor_runner.py", "experiments/extension_runner.py",
    "experiments/post_cstat_analyze.py")
IID_DESIGN_AMENDMENT = {
    "stage":"pre-freeze; zero anchor outcomes observed",
    "previous_logging_e":[.5,.5], "final_logging_e":[.75,.25],
    "target_q":[.5,.5], "nuisance":.5,
    "reason":"nontrivial OPE weights with exact 32-bit integer cutoffs; no outcome-driven tuning",
    "unchanged":"locations (.35,.55), target .45, threshold .4, true gap .05, 1600-unit budget"}


def anchor_cells():
    return ["iid-bounded", "iid-heavy"] + [f"scaling-N{n}-{outcome}"
        for n in (8192, 32768, 131072) for outcome in ("bounded", "heavy")]


def anchor_eligible(cell, method):
    if cell not in anchor_cells() or method not in METHODS:
        raise ValueError("unknown anchor cell or method")
    if method in (CATONI, OPE21, OPE24):
        return cell.startswith("iid-") and (method == CATONI or cell.endswith("bounded"))
    return method not in BOUNDED_METHODS or cell.endswith("bounded")


def primary_anchor_comparisons():
    return [[cell, method] for cell in anchor_cells() for method in METHODS if anchor_eligible(cell, method)]


def planned_anchor_ids():
    return [f"{NAMESPACE}/ANCHORS/{cell}/{rep:04d}" for cell in anchor_cells() for rep in range(200)]


def _validate_config(config):
    required = ("truncation_multipliers", "truncation_grid_source", "master_seed", "seed_domain",
        "numerical_guard", "normalized_risk_threshold", "raw_debug_run_ids", "analysis_bootstrap_seed",
        "analysis_bootstrap_resamples", "planning_inputs_reconciled", "theorem_status",
        "production_environment", "catoni_tau", "catoni_h", "ope2024_k", "ope2024_rho",
        "allowed_missing_planning_inputs")
    if any(key not in config for key in required):
        raise ValueError("explicit anchor config required: " + ", ".join(required))
    if config["truncation_multipliers"] != [2**(j/4) for j in range(-24,25)]:
        raise ValueError("anchors require the reconciled 49-point THEORY_NOTE grid")
    if not config["truncation_grid_source"] or config["planning_inputs_reconciled"] is not True:
        raise ValueError("record reconciled inputs and the actual truncation-grid source")
    if config["theorem_status"] != "PROVED_UNDER_DECLARED_ASSUMPTIONS":
        raise ValueError("certified anchor methods require their proved contracts")
    if config["production_environment"] != environment_signature():
        raise ValueError("production environment differs from the selected local environment")
    if any(type(config[key]) is not int or config[key] < 0 for key in ("master_seed", "analysis_bootstrap_seed")):
        raise ValueError("explicit nonnegative generation/analysis seeds required")
    if not str(config["seed_domain"]).startswith(NAMESPACE+"/ANCHORS/"):
        raise ValueError("a separate new anchor seed domain is required")
    if (not math.isfinite(config["numerical_guard"]) or config["numerical_guard"] < 0
            or config["normalized_risk_threshold"] != .4 or config["analysis_bootstrap_resamples"] != 2000):
        raise ValueError("freeze the .4 threshold, nonnegative numerical guard and 2000 bootstrap resamples")
    if (not math.isfinite(config["catoni_tau"]) or config["catoni_tau"] <= 0
            or not 0 < config["catoni_h"] < 1 or not math.isfinite(config["ope2024_k"])
            or config["ope2024_k"] < 0 or not math.isfinite(config["ope2024_rho"]) or config["ope2024_rho"] <= 0):
        raise ValueError("invalid pre-outcome Catoni/OPE tuning")
    for p in (1.5,2.):
        eps=p-1;log_c=(p/2)*math.log(eps/p)
        if eps<1:log_c+=(1-eps)/2*math.log((1-eps)/eps)
        log_min=(-math.log1p(-config["catoni_h"])+math.log(p/eps)
            +p/eps*math.log1p(config["catoni_tau"])-math.log(config["catoni_tau"])/eps
            +log_c/eps+math.log(math.log(40)))
        if log_min>math.log(32768):raise ValueError("frozen Catoni tuning fails the IID anchor sample-size condition")
    fixed = dict(namespace=NAMESPACE, suite="ANCHORS", cells=anchor_cells(), workers=1,
        levels=list(LEVELS), replications_per_cell=200, iid_N=32768,
        scaling_N=[8192,32768,131072], anchor_units=1600, primary_units=0,
        unit_category="supplementary anchors within combined 1600 allowance",
        total_primary_goal_units=29600, total_unit_cap=32000, legacy_new_outcome_draws=0,
        planned_run_ids=planned_anchor_ids(), methods=list(METHODS),
        primary_comparisons=primary_anchor_comparisons(),
        method_applicability={cell:{method:anchor_eligible(cell,method) for method in METHODS} for cell in anchor_cells()},
        artifact_cap_bytes=int(1.5*GIB), minimum_free_disk_bytes=2*GIB, worker_memory_cap_bytes=4*GIB,
        iid_locations=[.35,.55], iid_exact_e=[.75,.25], iid_target_q=[.5,.5],
        iid_fixed_nuisance=.5, iid_known_mean_class=[0.,1.], bounded_residual_bound=.5,
        iid_design_amendment=IID_DESIGN_AMENDMENT,
        tail_exponent=1.75, tail_scale=.1, p_heavy=1.5,
        scaling_auditor_fractions=[1.,.5,.1,.02], scaling_interpretation="descriptive fixed-DGP, not a minimax proof")
    for key,value in fixed.items():
        if key in config and config[key] != value:
            raise ValueError("anchor fixed design mismatch: "+key)
    if not isinstance(config["raw_debug_run_ids"],list) or not set(config["raw_debug_run_ids"]) <= set(fixed["planned_run_ids"]):
        raise ValueError("debug IDs must be prespecified anchor IDs")
    return dict(config,**fixed)


def freeze_anchors(config_path, input_directory, protocol_path):
    config_path=Path(config_path).resolve()
    config=_validate_config(json.loads(config_path.read_text()))
    planning_input_hashes(input_directory,allowed_missing=config["allowed_missing_planning_inputs"])
    paths=[REPOSITORY/name for name in dict.fromkeys(SOURCE_NAMES+EXTRA_SOURCES)]+[config_path]
    for path in paths:
        try: relative=path.relative_to(REPOSITORY)
        except ValueError as exc: raise ValueError("anchor config must be committed in the research repository") from exc
        if not path.is_file() or subprocess.check_output(["git","status","--porcelain","--",str(relative)],cwd=REPOSITORY,text=True):
            raise ValueError("commit scientific sources/config before anchor freeze: "+str(relative))
    config.update(git_sha=subprocess.check_output(["git","rev-parse","HEAD"],cwd=REPOSITORY,text=True).strip(),
        input_config_sha256=hashlib.sha256(config_path.read_bytes()).hexdigest(),
        E0_anchor="ca5bb878cf9635fac4381d03281df0bc8a900daa")
    return freeze_protocol(protocol_path,config,paths,input_directory)


@dataclass(frozen=True)
class AnchorCell:
    cell_id: str
    core: object
    iid: bool
    centered_moment_bound: float | None

    @property
    def n(self): return self.core.n


def build_anchor_plans(config,cell_id):
    if cell_id not in anchor_cells(): raise ValueError("unknown anchor cell")
    iid=cell_id.startswith("iid-")
    n=config.get("fixture_N",512) if config.get("suite")=="DETERMINISTIC_ANCHOR_FIXTURE" else (
        config["iid_N"] if iid else int(cell_id.split("-N")[1].split("-")[0]))
    outcome=cell_id.rsplit("-",1)[1]
    core=build_core_design(n,"independent" if iid else "cycle","moderate",outcome,
                           namespace=config["seed_domain"]+"/"+cell_id)
    if iid:
        cutoffs,e1=dyadic_probabilities(np.full(n,.25))
        q=np.full((n,2),.5)
        raw_moment=.5**2 if outcome=="bounded" else (.5+.1*7**(1/1.5))**1.5
        moment=raw_moment*float(np.sum(.5**core.p*np.array([.75,.25])**(1-core.p)))
        query=SignedQuery("anchor/all",q,0,provenance="fixed homogeneous IID anchor")
        core=replace(core,logging_cutoffs=cutoffs,exposure=_readonly(np.column_stack((1-e1,e1))),
            queries=(query,),subgroup_masses={query.query_id:1.},
            residual_moments=_readonly(np.full((n,2),raw_moment)))
    else:
        queries=[];masses={}
        for policy in range(4):
            q=core.queries[4*policy].coefficients
            for index,fraction in enumerate((1.,.5,.1,.02)):
                mask=(np.arange(n)<max(1,round(n*fraction))).astype(float)
                query=SignedQuery(f"scaling/policy{policy}/auditor{index}",mask[:,None]*q,0,
                                   provenance="fixed design-selected scaling anchor")
                queries.append(query);masses[query.query_id]=float(mask.mean())
        core=replace(core,queries=tuple(queries),subgroup_masses=masses)
        moment=None
    cell=AnchorCell(cell_id,core,iid,moment)
    plans={}
    for delta in config["levels"]:
        for method in CORE_METHODS+BOUNDED_METHODS:
            if anchor_eligible(cell_id,method):
                plans[float(delta),method]=tuple(make_plan(query,**core.certifier_inputs,
                    delta=float(delta),family_size=len(core.queries),multipliers=config["truncation_multipliers"],
                    method=method) for query in core.queries)
    return cell,plans


def anchor_from_primitives(cell,words,primitives,*,seed_namespace="explicit-anchor-fixture"):
    if not cell.iid:
        return generate_from_primitives(cell.core,words,primitives,seed_namespace=seed_namespace)
    core=cell.core;words=np.asarray(words)
    if words.shape!=(core.n,) or words.dtype.kind not in "iu" or np.any(words<0) or np.any(words>=WORD_GRID):
        raise ValueError("one logging word per anchor row required")
    if set(primitives)!=set(core.outcome_source_ids): raise ValueError("wrong anchor primitive keys")
    values=np.array([primitives[source] for source in core.outcome_source_ids],dtype=float)
    if (not np.isfinite(values).all() or (core.outcome=="bounded" and np.any(np.abs(values)!=1))
            or (core.outcome=="heavy" and np.any(np.abs(values)<1))):
        raise ValueError("invalid bounded/Pareto primitive fixture")
    actions=(words.astype(np.uint64)<core.logging_cutoffs).astype(np.uint8)
    noise=np.sum(values[core.outcome_source_indices]*core.outcome_source_coefficients,axis=1)
    outcomes=np.where(actions==1,.55,.35)+noise
    data_hash=hashlib.sha256(actions.tobytes()+outcomes.astype('<f8').tobytes()).hexdigest()
    return CoreLog(_readonly(actions,np.uint8),_readonly(outcomes),data_hash,seed_namespace)


def draw_anchor_log(cell,seed):
    """Production sampler; never called by deterministic tests without freeze."""
    if not cell.iid: return draw_core_log(cell.core,seed)
    def rng(role):
        key=f"{cell.core.namespace}\0{seed}\0{role}".encode()
        return np.random.default_rng(int.from_bytes(hashlib.sha256(key).digest(),"little"))
    logging,outcomes=rng("logging"),rng("outcome-primitives")
    words=logging.integers(0,WORD_GRID,size=cell.n,dtype=np.uint64)
    count=len(cell.core.outcome_source_ids)
    values=np.where(outcomes.integers(0,2,size=count,dtype=np.uint8)==0,-1.,1.)
    if cell.core.outcome=="heavy":
        magnitude_words=outcomes.integers(0,WORD_GRID,size=count,dtype=np.uint64)
        values=values*((magnitude_words.astype(float)+.5)/WORD_GRID)**(-1/TAIL_EXPONENT)
    return anchor_from_primitives(cell,words,dict(zip(cell.core.outcome_source_ids,values)),
                                  seed_namespace=f"{cell.core.namespace}/seed/{seed}")


def anchor_truths(cell):
    return {cell.core.queries[0].query_id:.45} if cell.iid else evaluate_oracle(cell.core)


def _seed(config,run_id):
    return int.from_bytes(hashlib.sha256(f"{config['seed_domain']}\0{config['master_seed']}\0{run_id}".encode()).digest()[:8],"little")


def _baseline_record(method,cell,log,delta,config):
    weights=cell.core.queries[0].coefficients/cell.core.exposure
    observed_weights=weights[np.arange(cell.n),log.actions]
    if method==CATONI:
        # This balanced-q/midpoint-fit anchor has a proved centered envelope
        # for the full DR score; observed Y has the logging-law target instead.
        score=.5+observed_weights*(log.outcomes-.5)
        record=catoni_iid(score,p=cell.core.p,central_moment_bound=cell.centered_moment_bound,
            delta=delta,tau=config["catoni_tau"],h=config["catoni_h"],iid_declared=True)
    elif method==OPE21:
        record=ope_betting_iid(observed_weights,log.outcomes,wmax=float(weights.max()),delta=delta,iid_declared=True)
    else:
        record=ope_eb_independent(log.actions,log.outcomes,exposure=cell.core.exposure,
            target_policy=cell.core.queries[0].coefficients,nuisance=cell.core.nuisance,
            delta=delta,k=config["ope2024_k"],rho=config["ope2024_rho"],
            independent_rows_declared=True,independent_nuisance_declared=True)
    record=dict(record,query_id=cell.core.queries[0].query_id,channel="risk",normalizer=1.,
        family_size=1,nominal_delta=delta,coordinate_delta=delta,selected_method=method,
        empty_intersection=record.get("empty_intersection",record.get("empty",False)))
    if record["status"]==CERTIFIED:
        raw_lo,raw_hi=record.get("raw_lo",record["lo"]),record.get("raw_hi",record["hi"])
        radius=record.get("radius")
        guard=config["numerical_guard"]*(1+abs(record["estimate"])+(radius or 0))
        raw_lo,raw_hi=raw_lo-guard,raw_hi+guard
        record.update(raw_lo=raw_lo,raw_hi=raw_hi,lo=max(0.,raw_lo),hi=min(1.,raw_hi),
            empty_intersection=max(0.,raw_lo)>min(1.,raw_hi),numerical_guard=guard)
    # Engine root arithmetic can return NumPy scalars.  Checkpoint JSON retains
    # the identical values, with native scalar types for its immutable payload.
    return {key:(value.item() if isinstance(value,np.generic) else value)
            for key,value in record.items()}


def _execute(manifest,run_id,cell,plans,draw,oracle,hashes):
    config=manifest["config"];seed=_seed(config,run_id)
    began,cpu=time.monotonic(),time.process_time()
    log=draw(cell,seed);evaluated=[]
    provenance=dict(data_digest=log.data_digest,seed_namespace=log.seed_namespace,
        code_hash=hashes["code"],config_hash=hashes["config"],numerical_guard=config["numerical_guard"])
    for delta in config["levels"]:
        for method in METHODS:
            records=[];decisions={};eligible=anchor_eligible(cell.cell_id,method)
            for index,query in enumerate(cell.core.queries):
                if not eligible:
                    record=dict(query_id=query.query_id,status="NOT_APPLICABLE",empty_intersection=False,
                        reason="method requires bounded outcomes and/or homogeneous independent rows")
                else:
                    try:
                        record=(_baseline_record(method,cell,log,float(delta),config) if method in (CATONI,OPE21,OPE24)
                                else plans[float(delta),method][index].evaluate(log.actions,log.outcomes,**provenance))
                    except (ValueError,ArithmeticError,RuntimeError) as exc:
                        record=dict(query_id=query.query_id,status="NUMERICAL_FAILURE",empty_intersection=True,reason=str(exc)[:2048])
                decisions[query.query_id]=certified_decision(record,.4*cell.core.subgroup_masses[query.query_id])
                records.append(record)
            evaluated.append((float(delta),method,eligible,records,decisions))
    frames=[dict(delta=d,method=m,method_applicable=a,coordinates=[_compact_record(r) for r in records],
                 decisions=decisions) for d,m,a,records,decisions in evaluated]
    try:
        truths=oracle(cell)
        if set(truths)!={q.query_id for q in cell.core.queries} or not all(math.isfinite(v) for v in truths.values()):
            raise ValueError("missing/nonfinite analysis-only anchor truths")
    except Exception as exc:
        return dict(suite="ANCHORS",cell=cell.cell_id,status="ORACLE_FAILURE",failure_reason=str(exc)[:2048],
            unassessable_whole_trial=True,trials=[],certificate_records=frames,
            legacy_new_outcome_draws=0,new_scientific_units=0 if config["suite"]=="DETERMINISTIC_ANCHOR_FIXTURE" else 1,
            failure_raw_debug=dict(actions=log.actions.tolist(),outcomes=log.outcomes.tolist()))
    trials=[]
    for delta,method,eligible,records,decisions in evaluated:
        if eligible:
            trial=_trial_metrics(run_id,cell.cell_id,delta,method,records,decisions,truths,cell.core,.4)
            trial.update(method_applicable=True,metrics_assessable=True)
        else:
            trial=dict(run_id=run_id,cell=cell.cell_id,method=method,delta=delta,
                coverage_applicable=False,method_applicable=False,family_covered=False,
                failure_status=None,metrics_assessable=False,mean_coordinate_width=None,
                return_endpoint_applicable=False,discovery_endpoint_applicable=False,
                **{event:False for event in EVENTS})
        trial["endpoint_scope"]="supplementary auditing anchor; return/discovery N/A"
        trials.append(trial)
    numerical=any(t.get("failure_status")=="NUMERICAL_FAILURE" for t in trials)
    failed=any(t["coverage_applicable"] and not t["family_covered"] for t in trials)
    result=dict(suite="ANCHORS",cell=cell.cell_id,status="COMPLETE_WITH_NUMERICAL_FAILURE" if numerical else (
        "COMPLETE_WITH_CONFIDENCE_FAILURE" if failed else "COMPLETE"),seed=seed,
        seed_domain=config["seed_domain"],data_digest=log.data_digest,seed_namespace=log.seed_namespace,
        code_sha256=hashes["code"],config_sha256=hashes["config"],git_sha=config.get("git_sha"),
        legacy_new_outcome_draws=0,new_scientific_units=0 if config["suite"]=="DETERMINISTIC_ANCHOR_FIXTURE" else 1,
        raw_N=cell.n,family_size=len(cell.core.queries),truths=truths,trials=trials,certificate_records=frames,
        oracle_order="all method/level intervals and decisions precede oracle join",
        interpretation="genuine iid strong-baseline anchor" if cell.iid else "descriptive fixed-DGP scaling; not minimax evidence",
        wall_seconds=time.monotonic()-began,cpu_seconds=time.process_time()-cpu)
    if failed or run_id in config["raw_debug_run_ids"]:
        result["raw_debug"]=dict(actions=log.actions.tolist(),outcomes=log.outcomes.tolist())
    return result


def _metadata(root,manifest,cell,plans):
    data=_cell_metadata(manifest,cell.cell_id,cell.core,plans)
    data.update(suite="ANCHORS",iid=cell.iid,centered_moment_bound=cell.centered_moment_bound,
        raw_residual_moment=float(cell.core.residual_moments.max()),
        iid_centered_envelope_proof=(
            "Special q=(.5,.5), fit=.5, mu_s in [0,1] only: let delta_s=mu_s-.5, "
            "w_s=.5/e_s>=.5 and R=w_A(Y-.5). ER=.5(delta_0+delta_1). "
            "max over delta corners |w_s delta_s-ER|=.5(|w_s-.5|+.5)=.5w_s. "
            "Conditional Minkowski adds w_s K; hence E|R-ER|^p <= "
            "(.5+K)^p sum_s e_s w_s^p = raw residual envelope v. "
            "For bounded p=2, Var(R)<=E[R^2]<=v also suffices. "
            "This is not a general raw-to-centered moment inequality." if cell.iid else None),
        iid_design_amendment=IID_DESIGN_AMENDMENT if cell.iid else None,
        method_applicability={m:anchor_eligible(cell.cell_id,m) for m in METHODS},
        supplementary_budget="8 cells x 200; shared methods/levels; combined 1600 allowance",
        baseline_tuning={k:manifest["config"][k] for k in ("catoni_tau","catoni_h","ope2024_k","ope2024_rho")})
    path=Path(root)/"cell_designs"/(cell.cell_id+".json.gz")
    content=canonical_bytes(data)
    if path.exists():
        if gzip.decompress(path.read_bytes())!=content: raise ValueError("anchor metadata changed/corrupt")
    else: install_once(path,gzip.compress(content,mtime=0))


def anchor_status(protocol_path,results_root,*,list_ids=False):
    if not Path(protocol_path).exists():
        result=dict(status="NOT_FROZEN",completed=0,remaining=1600,legacy_new_outcome_draws=0)
        if list_ids:result.update(completed_ids=[],remaining_ids=planned_anchor_ids())
        return result
    manifest=json.loads(Path(protocol_path).read_text())
    if manifest["config"].get("suite") not in ("ANCHORS","DETERMINISTIC_ANCHOR_FIXTURE"):
        raise ValueError("anchor status requires an anchor protocol")
    store=CheckpointStore(results_root,manifest)
    remaining=store.remaining_ids();completed=sorted(store.planned-set(remaining))
    result=dict(status="COMPLETE" if not remaining else "INCOMPLETE",suite="ANCHORS",
        fingerprint=manifest["fingerprint"],completed=len(completed),remaining=len(remaining),legacy_new_outcome_draws=0)
    if list_ids:result.update(completed_ids=completed,remaining_ids=remaining)
    return result


def run_anchors(protocol_path,results_root,*,global_results_root=None,max_new_units=None,
                draw_callback=None,oracle_callback=None,resource_reader=None,progress=True):
    manifest=json.loads(Path(protocol_path).read_text());config=manifest["config"]
    fixture=config.get("suite")=="DETERMINISTIC_ANCHOR_FIXTURE"
    if config.get("workers")!=1 or config.get("suite") not in ("ANCHORS","DETERMINISTIC_ANCHOR_FIXTURE"):
        raise ValueError("one-worker frozen anchor protocol required")
    if fixture and draw_callback is None:raise ValueError("fixtures require a nonrandom callback")
    if not fixture:_validate_config(config)
    if max_new_units is not None and (type(max_new_units) is not int or max_new_units<0):raise ValueError("invalid max-new-units")
    root=Path(results_root).resolve();global_root=Path(global_results_root or REPOSITORY/"results/post_cstat").resolve()
    if not root.is_relative_to(global_root):raise ValueError("global result root must contain anchors")
    store=CheckpointStore(root,manifest);stamps=_source_stamps(manifest);budget=GlobalBudget(global_root)
    hashes=dict(config=digest(config),code=digest(manifest["sources"]))
    reader=resource_reader or resource_snapshot;first=reader(global_root)
    total_bytes,total_units=budget.scan();_resource_check(first,total_bytes,config)
    grouped={}
    for run_id in store.remaining_ids():
        parts=run_id.split("/")
        if parts[1]!="ANCHORS" or parts[2] not in anchor_cells():raise ValueError("wrong anchor run ID")
        grouped.setdefault(parts[2],[]).append(run_id)
    began,cpu=time.monotonic(),time.process_time();new=failed=0;status="COMPLETE";reason=None
    try:
        for cell_id,ids in sorted(grouped.items()):
            if max_new_units is not None and new>=max_new_units:status="CHECKPOINTED_INCOMPLETE";break
            cell,plans=build_anchor_plans(config,cell_id);_metadata(root,manifest,cell,plans)
            for run_id in ids:
                if max_new_units is not None and new>=max_new_units:status="CHECKPOINTED_INCOMPLETE";break
                stamps=_verify_changed_sources(manifest,stamps)
                total_bytes,total_units=budget.scan();_resource_check(reader(global_root),total_bytes,config)
                if total_units>=config.get("total_unit_cap",32000):raise ResourceLimitError("global new-unit cap reached")
                if store.load(run_id) is not None:continue
                try:result=_execute(manifest,run_id,cell,plans,draw_callback or draw_anchor_log,
                                     oracle_callback or anchor_truths,hashes)
                except Exception as exc:
                    result=dict(suite="ANCHORS",cell=cell_id,status="UNIT_FAILURE",failure_reason=f"{type(exc).__name__}: {exc}"[:4096],
                        trials=[],unassessable_whole_trial=True,legacy_new_outcome_draws=0,
                        new_scientific_units=0 if fixture else 1,seed=_seed(config,run_id))
                store.complete(run_id,result);new+=1;failed+=result["status"]!="COMPLETE"
                total_bytes,total_units=budget.scan()
                if total_bytes>config.get("artifact_cap_bytes",int(1.5*GIB)):raise ResourceLimitError("global artifact cap reached after checkpoint")
                if progress and new%25==0:print(json.dumps(dict(suite="ANCHORS",cell=cell_id,new_completed_units=new,global_new_units=total_units)),flush=True)
                if result["status"] in ("UNIT_FAILURE","ORACLE_FAILURE"):
                    status,reason="ERROR_CHECKPOINTED",result["failure_reason"];break
            del cell,plans
            if status=="ERROR_CHECKPOINTED":break
    except ResourceLimitError as exc:status,reason="RESOURCE_CHECKPOINTED",str(exc)
    except KeyboardInterrupt:status,reason="INTERRUPTED","no unattended continuation"
    except ValueError as exc:status,reason="SOURCE_OR_MODEL_BLOCKED",str(exc)
    remaining=store.remaining_ids()
    if remaining and status=="COMPLETE":status="CHECKPOINTED_INCOMPLETE"
    total_bytes,total_units=budget.scan()
    invocation=dict(suite="ANCHORS",status=status,fingerprint=manifest["fingerprint"],new_completed_units=new,
        failed_units=failed,remaining_ids=remaining,legacy_new_outcome_draws=0,background_work_running=False,
        global_new_checkpoint_units=total_units,global_artifact_bytes=total_bytes,first_resource_snapshot=first,
        wall_seconds=time.monotonic()-began,cpu_seconds=time.process_time()-cpu,stop_reason=reason,
        execution_mode="one worker; coordinator controls <=2 total workers and combined RAM",
        resume_command=shlex.join([".venv/bin/python","-m","experiments.anchor_runner","--run","--protocol",str(protocol_path),"--results",str(root),"--global-results",str(global_root)]))
    install_once(root/"invocations"/f"{time.time_ns()}.json",canonical_bytes(invocation)+b"\n")
    return invocation


def analyze_anchors(protocol_path,results_root,output_directory,*,bootstrap_resamples=None):
    output=Path(output_directory)
    if any((output/name).exists() for name in ("summary.json","summary.csv","manifest.json")):raise FileExistsError("immutable analysis outputs; choose fresh directory")
    manifest=json.loads(Path(protocol_path).read_text());config=manifest["config"]
    fixture=config.get("suite")=="DETERMINISTIC_ANCHOR_FIXTURE"
    if config.get("suite") not in ("ANCHORS","DETERMINISTIC_ANCHOR_FIXTURE"):
        raise ValueError("anchor analysis requires an anchor protocol")
    if not fixture:_validate_config(config)
    registered=tuple(tuple(x) for x in config["primary_comparisons"])
    if len(set(registered))!=len(registered) or (not fixture and registered!=tuple(tuple(x) for x in primary_anchor_comparisons())):
        raise ValueError("anchor diagnostic family must be complete and unique")
    resamples=config.get("analysis_bootstrap_resamples",0) if bootstrap_resamples is None else bootstrap_resamples
    if type(resamples) is not int or resamples<0 or (not fixture and resamples!=2000):raise ValueError("invalid frozen bootstrap count")
    store=CheckpointStore(results_root,manifest);summaries={};widths={};completed=set();inventory=[];statuses=Counter()
    unknown_records=failed_units=0
    for payload in store.iter_completed():
        run_id=payload["run_id"];parts=run_id.split("/")
        if len(parts)!=4 or parts[1]!="ANCHORS" or parts[2] not in anchor_cells():raise ValueError("wrong anchor checkpoint ID")
        cell_id=parts[2];result=payload["result"]
        if (not isinstance(result,dict) or result.get("suite")!="ANCHORS"
                or result.get("cell",cell_id)!=cell_id or result.get("legacy_new_outcome_draws",0)!=0):
            raise ValueError("anchor result identity mismatch")
        completed.add(run_id);inventory.append([run_id,digest(payload)]);statuses[result.get("status","MISSING")]+=1
        expected={(m,float(d)) for m in METHODS for d in config["levels"]};by_key={}
        trial_records=result.get("trials",[])
        if not isinstance(trial_records,list):raise ValueError("anchor trials must be a list")
        for trial in trial_records:
            if not isinstance(trial,dict):raise ValueError("anchor trial frame must be an object")
            key=trial.get("method"),trial.get("delta")
            if key not in expected or key in by_key or trial.get("run_id")!=run_id or trial.get("cell")!=cell_id:raise ValueError("duplicate/unknown/wrong-ID anchor frame")
            if trial.get("coverage_applicable") is not anchor_eligible(cell_id,key[0]):raise ValueError("anchor applicability cannot change after outcomes")
            by_key[key]=trial
        failed=False
        for method,delta in sorted(expected):
            eligible=anchor_eligible(cell_id,method)
            if (method,delta) not in by_key or result.get("unassessable_whole_trial",False):
                trial=dict(run_id=run_id,cell=cell_id,method=method,delta=delta,coverage_applicable=eligible,
                    family_covered=False,metrics_assessable=False,mean_coordinate_width=None,
                    failure_status=(result.get("status") if result.get("status")!="COMPLETE" else "MISSING_METHOD_LEVEL_RESULT") if eligible else None,
                    **{event:False for event in EVENTS})
            else:trial=dict(by_key[method,delta])
            trial.update(return_endpoint_applicable=False,discovery_endpoint_applicable=False)
            if any(trial[event] for event in ("returned","return_unsafe","return_safe_useful","discovered_and_certified")):raise ValueError("anchor audits have no policy-return/discovery endpoints")
            key=cell_id,method,delta;summaries.setdefault(key,WholeTrialSummary()).add(trial)
            unknown_records+=eligible and not trial.get("metrics_assessable",True);failed|=bool(trial.get("failure_status"))
            width=trial.get("mean_coordinate_width")
            widths.setdefault(key,{})[run_id]=width if eligible and trial.get("metrics_assessable",True) and not trial.get("failure_status") else None
        failed_units+=failed
        if result.get("new_scientific_units",0 if fixture else 1)!=(0 if fixture else 1):raise ValueError("anchor unit accounting mismatch")
    rows=[summaries[key].result() for key in sorted(summaries)];holm=adjust_validity_family(rows,registered)
    for row in rows:
        eligible=anchor_eligible(row["cell"],row["method"]);row["method_applicable"]=eligible
        row["holm_undercoverage_p"]=holm.get((row["cell"],row["method"])) if row["delta"]==.05 else None
        if not eligible:
            row["applicability_reason"]="NOT_APPLICABLE: bounded and/or homogeneous independent-row theorem required"
            for endpoint in row["endpoints"].values():endpoint.update(applicable=False,hits=None,denominator=0,unknown_trials=0,rate=None,wilson95=None,realized_frequency_bounds=None)
    comparisons=[]
    for (cell_id,method,delta),left in sorted(widths.items()):
        if method!="comet_local":continue
        for other in METHODS:
            if other==method or not anchor_eligible(cell_id,other):continue
            right=widths.get((cell_id,other,delta),{})
            unknown=set(left)!=set(right) or any(left[k] is None or right.get(k) is None for k in left)
            record=dict(cell=cell_id,delta=delta,left_method=method,right_method=other,independent_pairs=len(left),
                bootstrap_pointwise95=None,mean_difference=None)
            if unknown:record["status"]="UNASSESSABLE_COMPLETE_PAIR_SET"
            elif not resamples:record.update(status="DESCRIPTIVE_BOOTSTRAP_DISABLED",mean_difference=float(np.mean([left[k]-right[k] for k in left])))
            else:
                seed=int.from_bytes(hashlib.sha256(f"{config['analysis_bootstrap_seed']}\0{cell_id}\0{other}\0{delta}".encode()).digest()[:8],"little")
                record.update(paired_endpoint_difference(left,right,bootstrap_seed=seed,resamples=resamples),status="PAIRED_POINTWISE_BOOTSTRAP")
            comparisons.append(record)
    remaining=sorted(store.planned-completed)
    summary=dict(schema="post-cstat-anchor-analysis-v1",suite="ANCHORS",status="NO_COMPLETED_UNITS" if not completed else ("PARTIAL" if remaining else "COMPLETE"),
        phase="DETERMINISTIC_FIXTURE_NOT_SCIENCE" if fixture else "supplementary_confirmatory_anchors",
        completed_units=len(completed),remaining_units=len(remaining),planned_units=len(store.planned),failed_units=failed_units,
        unknown_method_level_records=unknown_records,reported_new_scientific_units=0 if fixture else len(completed),
        primary_comparison_count=len(registered),summaries=rows,paired_width_differences=comparisons,
        completed_ids=sorted(completed),remaining_ids=remaining,checkpoint_status_counts=dict(statuses),
        checkpoint_inventory_sha256=digest(inventory),protocol_fingerprint=manifest["fingerprint"],
        analysis_new_outcome_draws=0,legacy_new_outcome_draws=0,analysis_bootstrap_resamples=resamples,
        E0_or_E1_primary_family_modified=False,scaling_interpretation="descriptive fixed-DGP rate anchors, not minimax validation",
        method_level_scope="one whole independent log per anchor; paired methods and levels are not extra replications",
        diagnostic_status="FINAL_FIXED_SAMPLE_DIAGNOSTIC" if completed and not remaining else "PARTIAL_DESCRIPTIVE_NOT_STOPPING_RULE")
    data=canonical_bytes(summary)+b"\n";csv_data=_csv_bytes(rows)
    receipt=dict(schema="post-cstat-anchor-analysis-manifest-v1",protocol_fingerprint=manifest["fingerprint"],
        sources=file_hashes([Path(__file__).resolve(),REPOSITORY/"comet/post_cstat_statistics.py",REPOSITORY/"experiments/post_cstat_analyze.py"]),
        primary_family_sha256=digest(registered),input_science_sources=manifest["sources"],analysis_new_outcome_draws=0,
        outputs={"summary.json":hashlib.sha256(data).hexdigest(),"summary.csv":hashlib.sha256(csv_data).hexdigest()})
    receipt["analysis_fingerprint"]=digest(receipt)
    for name,content in (("summary.json",data),("summary.csv",csv_data),("manifest.json",canonical_bytes(receipt)+b"\n")):install_once(output/name,content)
    return summary


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);mode=parser.add_mutually_exclusive_group(required=True)
    for name in ("freeze","run","status","analyze"):mode.add_argument("--"+name,action="store_true")
    parser.add_argument("--config",type=Path);parser.add_argument("--inputs",type=Path,default=REPOSITORY/"task_materials/post_cstat")
    parser.add_argument("--protocol",type=Path,default=REPOSITORY/"results/post_cstat/ANCHORS_protocol.json")
    parser.add_argument("--results",type=Path,default=REPOSITORY/"results/post_cstat/ANCHORS")
    parser.add_argument("--global-results",type=Path,default=REPOSITORY/"results/post_cstat")
    parser.add_argument("--output",type=Path);parser.add_argument("--max-new-units",type=int);parser.add_argument("--list-ids",action="store_true")
    args=parser.parse_args(argv)
    if args.freeze:
        if args.config is None:parser.error("--freeze requires --config")
        result=freeze_anchors(args.config,args.inputs,args.protocol)
    elif args.status:result=anchor_status(args.protocol,args.results,list_ids=args.list_ids)
    elif args.analyze:
        if args.output is None:parser.error("--analyze requires a fresh --output")
        result=analyze_anchors(args.protocol,args.results,args.output)
        result={k:result[k] for k in ("status","completed_units","remaining_units","failed_units","primary_comparison_count")}
    else:
        if json.loads(args.protocol.read_text())["config"].get("suite")!="ANCHORS":raise ValueError("CLI cannot run deterministic fixtures")
        result=run_anchors(args.protocol,args.results,global_results_root=args.global_results,max_new_units=args.max_new_units)
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__=="__main__":main()

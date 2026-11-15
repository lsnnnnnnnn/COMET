"""Build the review ledger from completed analysis receipts; draw no outcomes."""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def suite_record(name):
    protocol = ROOT / f"results/post_cstat/{name}_protocol.json"
    analysis = ROOT / f"results/post_cstat/{name}_analysis_v1/summary.json"
    server_protocol = ROOT / f"results/post_cstat/{name}_server_v2_protocol.json"
    if name in ("ANCHORS","negative_controls") and server_protocol.exists():
        protocol=server_protocol
        analysis=ROOT/f"results/post_cstat/{name}_server_v2_analysis_v1/summary.json"
    detailed = ROOT / f"results/post_cstat/{name}_detailed_v1/summary.json"
    result = dict(suite=name, protocol=str(protocol.relative_to(ROOT)),
                  protocol_status="FROZEN" if protocol.exists() else "NOT_FROZEN",
                  completed_analysis=None, detailed_analysis=None)
    if protocol.exists():
        manifest = json.loads(protocol.read_text())
        result.update(protocol_fingerprint=manifest["fingerprint"],
                      planned_units=len(manifest["config"]["planned_run_ids"]))
    for path, field in ((analysis,"completed_analysis"),(detailed,"detailed_analysis")):
        if path.exists():
            data = json.loads(path.read_text())
            result[field] = dict(path=str(path.relative_to(ROOT)), sha256=sha(path),
                status=data["status"], completed_units=data.get("completed_units",data.get("completed_checkpoint_files")),
                primary_comparisons=data.get("primary_comparison_count"),
                failed_units=data.get("failed_units"), mismatch_count=data.get("mismatch_count"))
    return result


def build():
    suites = {name:suite_record(name) for name in ("E1","E2","E3","E4","E5","E6","ANCHORS","negative_controls")}
    claims = []

    def add(claim_id, claim, level, math_status, code, proof, experiments, limits, *, evidence_status=None):
        files = list(dict.fromkeys(code+proof))
        evidence = {name:suites[name] for name in experiments}
        if evidence_status is None:
            complete = all(suites[name]["completed_analysis"] and suites[name]["completed_analysis"]["status"] == "COMPLETE" for name in experiments)
            evidence_status = "COMPLETED_ANALYSES_AVAILABLE" if complete and experiments else "EMPIRICAL_EVIDENCE_INCOMPLETE" if experiments else "DETERMINISTIC_OR_THEORETICAL"
        claims.append(dict(claim_id=claim_id,claim=claim,claim_level=level,
            mathematical_status=math_status,implementation_status="IMPLEMENTED" if code else "NOT_IMPLEMENTED_OR_NOT_REQUIRED",
            evidence_status=evidence_status,proof=proof,code=code,experiments=evidence,
            source_sha256={name:sha(ROOT/name) if (ROOT/name).is_file() else None for name in files},limits=limits))

    add("H0","Preserved independent-block C-STAT baseline","established historical baseline",
        "ESTABLISHED_WITHIN_OLD_MODEL",[],["reports/gate_C_stat_delivery.md"],[],
        "6000 logs and1134000 records preserved; no new E0 draws or additions to old17.",evidence_status="PRESERVED_COMPLETED_HISTORICAL_EVIDENCE")
    add("C1","Heterogeneous global conditional-graph residual certificate","required core","PROVED_UNDER_DECLARED_ASSUMPTIONS",
        ["comet/residual_truncation.py","comet/queries.py","comet/source_graph.py"],
        ["theory/global_residual_truncation.md","reports/post_cstat/theory_note_reconciliation.md"],["E1"],
        "Exact supported e, legal raw residual moments, legitimate conditioning, sufficient whole-score graph,1<p<=2; real arithmetic. Coverage does not establish informativeness.")
    add("C2","Query-specific support, moment and available-coloring costs","required core","PROVED",
        ["comet/residual_truncation.py","comet/source_graph.py","experiments/suite_designs.py"],
        ["theory/global_residual_truncation.md"],["E2"],
        "Source sufficiency is an assumption/construction, not inferred from one log. Matched generic methods receive identical local information.")
    add("C3","Direct signed paired contrasts and step-size control","required core","PROVED",
        ["comet/paired_contrasts.py","experiments/suite_designs.py"],["theory/global_residual_truncation.md"],["E3"],
        "16 direct contrasts versus20 deduplicated joint levels under same totaldelta; eta scales signal and radius together, not automatic sign-power gain.")
    add("C4","Subgroup/exposure/clique obstruction and2r sufficient power boundary","required scoped core","PROVED_SCOPED_SUBCLASS",
        ["experiments/post_cstat_design.py"],["theory/query_specific_cost_lower_bound.md"],["E4"],
        "Expected absolute-risk lower bound with saturation/integer restrictions; no graph-by-graph or confidence-log sharpness. Maps are deterministic sufficient bounds, not empirical trials.")
    add("C5","Independently discovered finite-family certification","required core","PROVED",
        ["comet/audit_pipeline.py","experiments/pipeline_dgp.py","experiments/pipeline_runner.py"],
        ["theory/global_residual_truncation.md"],["E5"],
        "Disjoint primitive pools; actual full risk+utility family; finite returned family, not infinite-class fairness. E6 external replication remains separate.")
    add("C6","Constrained return with risk, utility and service requirements","required application","PROVED_EVENTWISE_GUARANTEE",
        ["comet/policy_update.py","experiments/pipeline_runner.py"],["theory/global_residual_truncation.md"],["E5"],
        "Controls return AND unsafe under the declared family. Useful return must be observed separately; no automatic conditional unsafe-given-return or future safety guarantee.")
    add("C7","Real-covariate fixed-population selective-label validation","required empirical extension","SOURCE_SELECTOR_GRAPH_PROVED_NOT_EMPIRICALLY_VALIDATED",
        ["experiments/semisynthetic_selective_labels.py","experiments/e6_runner.py","experiments/e6_analyze.py"],["reports/post_cstat/E6_dataset_choice.md"],["E6"],
        "Official ACS CA2018 archive unavailable: DNS,HTTP403,browser timeout; zero E6 draws. No substitute or causal-income claim.",evidence_status="DATA_BLOCKED")
    add("O1","Predictable fixed-horizon extension","optional","DERIVED_NOT_IMPLEMENTED",[],
        ["theory/predictable_fixed_horizon_status.md"],[],
        "Nonblocking optional memo; no implementation/experiment, optional stopping, realized random-budget substitution or future-distribution claim.")
    add("O2","Interference/slate empirical application","optional","NOT_CLAIMED",[],[],[],
        "Conditional policy-compatibility discussion only; shared noise is not interference. No experimental spillover claim.",evidence_status="NOT_PROMOTED")
    add("B1","Strong bounded graph Hoeffding/Bernstein branches","comparison","PROVED",
        ["comet/residual_truncation.py"],["theory/global_residual_truncation.md"],["E1","E4"],
        "Same actual residual ranges, support, graph, nuisance and budget. Eligible bounded outcomes only.")
    add("B2","Fully matched generic truncation equals COMET configuration","comparison","ALGEBRAIC_IDENTITY",
        ["comet/residual_truncation.py"],["theory/global_residual_truncation.md"],["E1","E2","E3","E4","E5"],
        "Identical procedures are not independent algorithms or evidence of COMET estimator superiority.")
    add("B3","Finite-moment Catoni and strong OPE eligible anchors","comparison","PRIMARY_SOURCES_CHECKED_ELIGIBILITY_EXPLICIT",
        ["comet/independent_anchors.py","comet/ope_2024.py","experiments/anchor_runner.py"],
        ["reports/novelty_and_baseline_matrix.md"],["ANCHORS"],
        "Catoni iid/common mean/known centeredmoment/sample gate;2021scalar author betting notfull2DMOPE;2024DR/EB permits independent heterogeneous averages, not arbitrary graph dependence.")
    add("A","Historical A Hoeffding radius and2r analytic guarantee","analytic motivation","DETERMINISTIC_PROOF",
        ["experiments/post_cstat_design.py"],["theory/global_residual_truncation.md"],[],
        "r=.015005043614373761,gamma=.0375>2r; no new empirical power and no insertion into old17.")
    add("N","Incorrect-assumption and omitted-bias negative controls","diagnostic","VALID_REFERENCES_ONLY",
        ["experiments/negative_controls.py"],["reports/post_cstat/negative_controls_prefreeze_design.md"],["negative_controls"],
        "Intentionally invalid outputs remain HEURISTIC; unobservable hidden dependence/wrong e/nuisance leakage cannot be detected automatically from schema.")
    return dict(schema="COMET-proof-code-experiment-ledger-v2",new_outcome_draws=0,
        authority="Available supplied documents plus explicit user missing-blueprint waiver",
        claim_evidence_input_sha256=sha(ROOT/"task_materials/post_cstat/CLAIM_EVIDENCE.csv"),
        claims=claims,suites=suites,
        interpretation="Analysis availability is not an endorsement of practical usefulness or novelty; see research_verdict.md.")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=ROOT/"reports/post_cstat")
    args=parser.parse_args();data=build();args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"claim_ledger.json").write_text(json.dumps(data,indent=2)+"\n")
    stream=io.StringIO(newline="")
    fields=["claim_id","claim","claim_level","mathematical_status","implementation_status","evidence_status","proof","code","experiments","limits"]
    writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
    for row in data["claims"]:
        flat={key:row[key] for key in fields}
        for key in ("proof","code","experiments"):flat[key]=";".join(flat[key])
        writer.writerow(flat)
    (args.output/"claim_ledger.csv").write_text(stream.getvalue())
    print(json.dumps(dict(claims=len(data["claims"]),new_outcome_draws=0)))


if __name__=="__main__":main()

"""Publication figures and numeric tables from existing post-C-STAT analyses.

No Monte Carlo trial, sampler, certifier or bootstrap is run. Missing summaries
are visibly unavailable, never zero-filled. Primary plots use delta=.05;
complete supplied methods and both levels remain in the exported tables.
Matched generic and COMET are explicitly the same algebraic procedure.
"""

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import tempfile
from contextvars import ContextVar

os.environ.setdefault("MPLCONFIGDIR",str(Path(tempfile.gettempdir())/"comet-empirical-matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


SUITES=("E1","E2","E3","E4","E5","E6")
BLUE,ORANGE,GREEN,PURPLE,RED="#0072B2","#E69F00","#009E73","#CC79A7","#D55E00"
LABELS={"comet_local":"COMET / matched generic","generic_matched":"Matched generic (= COMET)",
    "truncated_global_envelope":"Global envelope + graph","truncated_global_graph":"Local moments, global graph",
    "truncated_local":"Local truncation","colorwise_truncation":"Colorwise truncation",
    "graph_hoeffding":"Graph Hoeffding","graph_bernstein":"Graph Bernstein",
    "graph_hoeffding_global":"Global graph Hoeffding","graph_bernstein_global":"Global graph Bernstein",
    "deduplicated_joint_level_difference":"Joint levels (deduplicated)",
    "independent_global":"Independent discovery + global","point_constraint":"Point constraints (heuristic)",
    "in_sample_auditing":"In-sample search (heuristic)","fixed_slice":"Fixed slices (restricted)",
    "abstain_reference":"Always abstain","status_quo_reference":"Status quo (uncertified)",
    "bhatt2022_catoni_iid":"Bhatt et al. Catoni (IID)",
    "author_one_dimensional_ope_betting":"OPE betting (author code)",
    "waudby_smith_2024_dr_eb_independent":"DR empirical Bernstein (independent)"}
COLORS={"comet_local":BLUE,"generic_matched":BLUE,"truncated_global_envelope":ORANGE,
    "truncated_global_graph":PURPLE,"truncated_local":GREEN,"graph_bernstein":GREEN,"colorwise_truncation":RED,
    "deduplicated_joint_level_difference":PURPLE,"independent_global":ORANGE}
STYLE={"font.family":"DejaVu Sans","font.size":8.5,"axes.labelsize":9,"axes.titlesize":9,
    "xtick.labelsize":7.5,"ytick.labelsize":7.5,"legend.fontsize":7,
    "axes.spines.top":False,"axes.spines.right":False,"axes.titleweight":"normal",
    "pdf.fonttype":42,"svg.fonttype":"none","lines.linewidth":1.4,"lines.markersize":3.8}
FIXTURE_RENDERING=ContextVar("COMET_fixture_rendering",default=False)


def _finite(value):
    try:
        return value is not None and math.isfinite(float(value))
    except (ValueError,TypeError):
        return False


def _number(value):
    return float(value) if _finite(value) else None


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read_csv(path):
    with Path(path).open(newline="") as stream:
        return list(csv.DictReader(stream))


def _load_summary(path,name):
    if path is None:
        return None,dict(name=name,status="UNAVAILABLE",reason="no analysis supplied")
    path=Path(path)
    source=path/"summary.json" if path.is_dir() else path
    if not source.is_file():
        return None,dict(name=name,status="UNAVAILABLE",path=str(source),reason="summary is not present")
    data=json.loads(source.read_text())
    receipt=source.parent/"manifest.json"
    if receipt.is_file():
        expected=json.loads(receipt.read_text()).get("outputs",{}).get(source.name)
        if expected is not None and expected!=_sha(source):
            return None,dict(name=name,status="INPUT_HASH_MISMATCH",path=str(source))
    return data,dict(name=name,status=data.get("status","AVAILABLE"),path=str(source),sha256=_sha(source),
        phase=data.get("phase"),completed_units=data.get("completed_units"),remaining_units=data.get("remaining_units"))


def _load_detailed(path,name):
    if path is None:
        return dict(groups=[],queries=[]),dict(name=name,status="UNAVAILABLE",reason="no detailed diagnostics supplied")
    path=Path(path)
    receipt=path/"manifest.json"
    if receipt.is_file():
        metadata=json.loads(receipt.read_text())
        if metadata.get("mismatch_count",0):
            return dict(groups=[],queries=[]),dict(name=name,status="DIAGNOSTIC_MISMATCHES",path=str(path),mismatch_count=metadata["mismatch_count"])
    else:
        metadata={}
    result={}
    sources={}
    for key,name_csv in (("groups","group_summary.csv"),("queries","query_summary.csv")):
        source=path/name_csv
        if not source.is_file():
            result[key]=[]
            continue
        expected=metadata.get("outputs",{}).get(name_csv)
        if expected is not None and expected!=_sha(source):
            return dict(groups=[],queries=[]),dict(name=name,status="INPUT_HASH_MISMATCH",path=str(source))
        result[key]=_read_csv(source)
        sources[str(source)]=_sha(source)
    return result,dict(name=name,status="AVAILABLE" if any(result.values()) else "UNAVAILABLE",sources=sources)


def _rows(analysis):
    return [row for row in (analysis or {}).get("summaries",[]) if _number(row.get("delta"))==.05]


def _detail(rows):
    return [row for row in rows if _number(row.get("delta"))==.05]


def _metric(row,name,stat="median"):
    if not row:
        return None
    if "metrics" in row:
        return _number(row["metrics"].get(name,{}).get(stat))
    return _number(row.get(name+"_"+stat))


def _endpoint(row,name):
    if name=="family_coverage":
        return row.get("family_coverage")
    return row.get("endpoints",{}).get(name) or row.get("extension_endpoints",{}).get(name) or row.get("pipeline_metrics",{}).get("joint_events",{}).get(name)


def _point(endpoint):
    if not endpoint or endpoint.get("applicable",True) is False or not _finite(endpoint.get("rate")):
        return None
    ci=endpoint.get("wilson95")
    rate=float(endpoint["rate"])
    return rate,ci if isinstance(ci,(list,tuple)) and len(ci)==2 and all(_finite(x) for x in ci) else None


def _unavailable(ax,reason):
    ax.set_axis_off()
    ax.text(.5,.5,reason+"\nNo empirical values plotted.",ha="center",va="center",transform=ax.transAxes,color=".35",fontsize=9)


def _finish_axes(axes):
    for i,ax in enumerate(np.asarray(axes,dtype=object).ravel()):
        ax.text(-.12,1.03,chr(65+i),fontweight="bold",transform=ax.transAxes,va="bottom")


def _save(fig,output,name,formats):
    if FIXTURE_RENDERING.get():
        fig.text(.5,.5,"DETERMINISTIC TEST FIXTURE",ha="center",va="center",rotation=25,
                 fontsize=20,color=".4",alpha=.16,zorder=1000)
    for extension in formats:
        metadata={"CreationDate":None,"ModDate":None,"Creator":"COMET empirical figures"} if extension=="pdf" else ({"Date":None,"Creator":"COMET empirical figures"} if extension=="svg" else {"Software":"COMET empirical figures"})
        fig.savefig(output/(name+"."+extension),dpi=300,bbox_inches="tight",metadata=metadata)
    plt.close(fig)


def _errorbar(ax,x,endpoint,*,color,marker="o",label=None,**kwargs):
    value=_point(endpoint)
    if value is None:
        return False
    rate,ci=value
    uncertainty=None if ci is None else [[max(0,rate-float(ci[0]))],[max(0,float(ci[1])-rate)]]
    ax.errorbar([x],[rate],yerr=uncertainty,color=color,marker=marker,linestyle="none",capsize=2,label=label,**kwargs)
    return True


def _plot_core(analysis,detail,output,formats):
    rows=_rows(analysis)
    cells=sorted({row["cell"] for row in rows})
    fig,axes=plt.subplots(2,2,figsize=(7.2,5.8),constrained_layout=True)
    if not cells:
        for ax in axes.ravel():_unavailable(ax,"E1 analysis unavailable")
    else:
        method_order=("comet_local","truncated_global_envelope","colorwise_truncation","graph_bernstein")
        lookup={(row["cell"],row["method"]):row for row in rows}
        detailed={(row["cell"],row["method"]):row for row in _detail(detail["groups"])}
        for index,method in enumerate(method_order):
            color=COLORS[method]
            for x,cell in enumerate(cells):
                row=lookup.get((cell,method))
                if row:
                    _errorbar(axes[0,0],x+(index-1.5)*.12,_endpoint(row,"family_coverage"),
                        color=color,label=LABELS[method] if x==0 else None)
                record=detailed.get((cell,method))
                median=_metric(record,"feasible_width_ratio")
                if median is not None:
                    q25,q75=_metric(record,"feasible_width_ratio","q25"),_metric(record,"feasible_width_ratio","q75")
                    axes[0,1].errorbar(x+(index-1.5)*.12,median,
                        yerr=None if q25 is None or q75 is None else [[median-q25],[q75-median]],
                        fmt="o",color=color,capsize=2)
        axes[0,0].axhline(.95,color=".4",linestyle="--",linewidth=.8)
        coverages=[_endpoint(row,"family_coverage") for row in rows]
        lower=[float(ep["wilson95"][0]) for ep in coverages if ep and ep.get("wilson95") and _finite(ep["wilson95"][0])]
        axes[0,0].set_ylim(max(0,min(lower+[.95])-.03),1.01)
        axes[0,0].set_ylabel("Complete-family coverage")
        axes[0,0].set_title("Pointwise Wilson 95% intervals")
        axes[0,0].legend(frameon=False,loc="lower left")
        if detailed:
            axes[0,1].axhline(1,color=".5",linestyle=":",linewidth=.8)
            axes[0,1].set(ylabel="CI width / known diameter",title="Candidate median and IQR (descriptive)")
            any_values,all_values,max_values,p90_values=[],[],[],[]
            for cell in cells:
                row=detailed.get((cell,"comet_local"),{})
                any_values.append(_number(row.get("family_any_nontrivial_rate")))
                all_values.append(_number(row.get("family_all_nontrivial_rate")))
                max_values.append(_metric(row,"trial_max_error_radius_ratio","max"))
                p90_values.append(_metric(row,"trial_max_error_radius_ratio","p90"))
            for values,label,marker,color in ((any_values,"Any nontrivial coordinate","o",BLUE),
                    (all_values,"All coordinates nontrivial","s",GREEN)):
                axes[1,0].plot(range(len(cells)),[np.nan if value is None else value for value in values],marker=marker,color=color,label=label)
            detection=[]
            for x,cell in enumerate(cells):
                endpoint=_endpoint(lookup.get((cell,"comet_local"),{}),"true_violation_detected")
                point=_point(endpoint)
                detection.append(np.nan if point is None else point[0])
                _errorbar(axes[1,0],x,endpoint,color=RED,marker="^")
            axes[1,0].plot(range(len(cells)),detection,"^-",color=RED,label="True violation certified (Wilson 95%)")
            axes[1,0].set(ylim=(-.03,1.03),ylabel="Complete-log frequency",title="COMET / matched generic")
            axes[1,0].legend(frameon=False,loc="best")
            axes[1,1].plot(range(len(cells)),[np.nan if value is None else value for value in p90_values],"o-",color=BLUE,label="90th percentile of trial maxima")
            axes[1,1].plot(range(len(cells)),[np.nan if value is None else value for value in max_values],"s--",color=RED,label="Maximum over complete trials")
            axes[1,1].axhline(1,color=".4",linestyle=":")
            axes[1,1].set_yscale("symlog",linthresh=.01)
            axes[1,1].set(ylabel="Whole-trial max |error| / radius",title="COMET error/radius diagnostic")
            axes[1,1].legend(frameon=False,loc="best")
        else:
            for ax in (axes[0,1],axes[1,0],axes[1,1]):_unavailable(ax,"E1 detailed diagnostics unavailable")
        short=[cell.replace("independent","ind").replace("triangles","tri").replace("moderate","mod").replace("bounded","bnd").replace("heavy","tail") for cell in cells]
        for ax in axes.ravel():
            if ax.axison:
                ax.set_xticks(range(len(cells)),short,rotation=70,ha="right")
    _finish_axes(axes)
    _save(fig,output,"fig1_core_validity_informativeness",formats)


def _plot_locality(detail,output,formats):
    rows=_detail(detail["queries"])
    fig,axes=plt.subplots(2,2,figsize=(7.2,5.4),constrained_layout=True)
    methods=("comet_local","truncated_global_graph","truncated_global_envelope","truncated_local")
    for i,overlap in enumerate(("moderate","extreme1e-4")):
        for j,(auditor,title) in enumerate((("auditor1","Audited first half"),("auditor0","Global query"))):
            ax=axes[i,j]
            any_plotted=False
            for method in methods:
                selected=[row for row in rows if row.get("method")==method and row.get("query_id")=="E2/policy0/"+auditor
                          and str(row.get("cell","")).endswith("-"+overlap)]
                selected.sort(key=lambda row:int(row["cell"].split("-")[0].removeprefix("hub")))
                x=[int(row["cell"].split("-")[0].removeprefix("hub")) for row in selected]
                y=[_metric(row,"normalized_radius") for row in selected]
                if any(value is not None for value in y):
                    ax.plot(x,[np.nan if value is None else value for value in y],"o-",color=COLORS[method],label=LABELS[method])
                    any_plotted=True
            if any_plotted:
                ax.set(xscale="log",yscale="log",xlabel="Outside source-clique size",ylabel="Subgroup-normalized radius",
                    title=title+"; outside "+("moderate" if overlap=="moderate" else "e(1)=10^-4"))
                ax.set_xticks([1,16,64],["1","16","64"])
                ax.legend(frameon=False,loc="best")
            else:_unavailable(ax,"E2 per-query diagnostics unavailable")
    _finish_axes(axes)
    _save(fig,output,"fig2_query_locality",formats)


def _plot_contrasts(detail,output,formats):
    rows=_detail(detail["queries"])
    fig,axes=plt.subplots(2,2,figsize=(7.2,5.3),constrained_layout=True)
    methods=("comet_local","deduplicated_joint_level_difference","truncated_global_envelope")
    for i,outcome in enumerate(("bounded","heavy")):
        for j,overlap in enumerate(("moderate","weak")):
            ax=axes[i,j]
            any_plotted=False
            for method in methods:
                selected=[row for row in rows if row.get("method")==method and row.get("query_id")=="E3/policy0/auditor0"
                          and str(row.get("cell","")).endswith("-"+overlap+"-"+outcome)]
                selected.sort(key=lambda row:int(row["cell"].split("-")[0].removeprefix("support")))
                x=[int(row["cell"].split("-")[0].removeprefix("support"))/100 for row in selected]
                y=[_metric(row,"intersected_width") for row in selected]
                if any(value is not None for value in y):
                    ax.plot(x,[np.nan if value is None else value for value in y],"o-",color=COLORS[method],label=LABELS[method])
                    any_plotted=True
            if any_plotted:
                ax.set(xscale="log",xlabel="Fraction of rows with policy change",ylabel="Median contrast CI width",
                    title=overlap+" overlap, "+outcome)
                ax.set_xticks([.02,.1,1],["0.02","0.10","1.00"])
                ax.legend(frameon=False,loc="best")
            else:_unavailable(ax,"E3 per-query diagnostics unavailable")
    _finish_axes(axes)
    _save(fig,output,"fig3_paired_contrasts",formats)


GAPS={"m010":-.1,"m003":-.03,"zero":0.,"p003":.03,"p010":.1,"p020":.2}


def _gap(cell):
    return GAPS.get(str(cell).rsplit("gap",1)[-1])


def _plot_power(analysis,detail,output,formats):
    rows=_rows(analysis)
    detailed=_detail(detail["queries"])
    fig,axes=plt.subplots(2,2,figsize=(7.2,5.5),constrained_layout=True)
    for i,outcome in enumerate(("bounded","heavy")):
        for j,overlap in enumerate(("moderate","weak")):
            ax=axes[i,j]
            any_plotted=False
            choices=(("comet_local","primary_certified_violation",BLUE,"o","COMET / matched: certify violation"),
                ("comet_local","primary_certified_safe",GREEN,"s","COMET / matched: certify safe"),
                ("truncated_global_envelope","primary_certified_violation",ORANGE,"^","Global: certify violation"))
            for method,event,color,marker,label in choices:
                selected=sorted([row for row in rows if row["method"]==method and row["cell"].startswith(overlap+"-"+outcome+"-")],key=lambda row:_gap(row["cell"]))
                xx,yy=[],[]
                for row in selected:
                    value=_point(_endpoint(row,event))
                    if value is not None:
                        x=_gap(row["cell"])
                        xx.append(x);yy.append(value[0])
                        _errorbar(ax,x,_endpoint(row,event),color=color,marker=marker)
                if xx:
                    ax.plot(xx,yy,color=color,linestyle="--" if event.endswith("safe") else "-",label=label)
                    any_plotted=True
            if any_plotted:
                ax.axvspan(-.11,0,color=".94",zorder=-5)
                ax.axvline(0,color=".7",linewidth=.7)
                radius=[_metric(row,"normalized_radius") for row in detailed if row.get("method")=="comet_local"
                        and row.get("query_id")=="E4/policy0/auditor0" and row.get("cell","").startswith(overlap+"-"+outcome+"-")]
                radius=[value for value in radius if value is not None]
                if radius:
                    boundary=2*max(radius)
                    if -.11<=boundary<=.21:
                        ax.axvline(boundary,color=PURPLE,linestyle=":",label="Sufficient boundary 2r")
                    else:
                        ax.text(.98,.53,f"2r={boundary:.3g}\n(outside shown gaps)",ha="right",va="center",transform=ax.transAxes,color=PURPLE,fontsize=7)
                ax.set(xlim=(-.11,.21),ylim=(-.03,1.03),xlabel="True normalized gap gamma",ylabel="Primary-query certification probability",
                    title=overlap+" overlap, "+outcome)
                ax.legend(frameon=False,loc="best",fontsize=6.8)
            else:_unavailable(ax,"E4 analysis unavailable")
    _finish_axes(axes)
    _save(fig,output,"fig4_gap_power_boundary",formats)


PIPELINE_ARMS=("point_constraint","in_sample_auditing","independent_global","comet_local","generic_matched","fixed_slice","abstain_reference","status_quo_reference")
PIPELINE_SHORT=("Point","In-sample","Global","COMET","Matched","Fixed","Abstain","Status quo")


def _plot_pipeline(analysis,output,formats,name="fig5_safe_useful_return"):
    rows=_rows(analysis)
    fig,axes=plt.subplots(2,2,figsize=(7.2,6.7),constrained_layout=True)
    cells=sorted({row["cell"] for row in rows})
    lookup={(row["cell"],row["method"]):row for row in rows}
    for ax,event,title in zip(axes.ravel(),("returned","return_unsafe","return_and_infeasible","return_safe_useful"),
            ("Return","Return AND unsafe (risk)","Return AND infeasible (all constraints)","Return AND safe AND useful")):
        if not cells:
            _unavailable(ax,"Pipeline analysis unavailable")
            continue
        values=np.full((len(cells),len(PIPELINE_ARMS)),np.nan)
        for i,cell in enumerate(cells):
            for j,method in enumerate(PIPELINE_ARMS):
                endpoint=_endpoint(lookup.get((cell,method),{}),event)
                point=_point(endpoint)
                if point is not None:values[i,j]=point[0]
        cmap=plt.get_cmap("cividis").copy()
        cmap.set_bad(".88")
        image=ax.imshow(np.ma.masked_invalid(values),aspect="auto",vmin=0,vmax=1,cmap=cmap)
        for i in range(len(cells)):
            for j in range(len(PIPELINE_ARMS)):
                value=values[i,j]
                ax.text(j,i,"NA" if not math.isfinite(value) else f"{value:.2f}",ha="center",va="center",
                        fontsize=6.5,color="white" if math.isfinite(value) and value<.45 else "black")
        ax.set_xticks(range(len(PIPELINE_ARMS)),PIPELINE_SHORT,rotation=65,ha="right")
        ax.set_yticks(range(len(cells)),[cell.replace("independent","ind").replace("moderate","mod") for cell in cells])
        ax.set_title(title)
        fig.colorbar(image,ax=ax,fraction=.025,pad=.02,ticks=[0,.5,1])
    _finish_axes(axes)
    _save(fig,output,name,formats)


def _plot_appendix(anchors,controls,output,formats):
    fig,grid=plt.subplots(2,2,figsize=(7.2,5.8),constrained_layout=True)
    axes=grid.ravel()
    rows=_rows(anchors)
    selected=[row for row in rows if str(row["cell"]).startswith("iid-")]
    if selected:
        methods=("comet_local","graph_bernstein","bhatt2022_catoni_iid","author_one_dimensional_ope_betting","waudby_smith_2024_dr_eb_independent")
        for i,cell in enumerate(("iid-bounded","iid-heavy")):
            for j,method in enumerate(methods):
                row=next((row for row in selected if row["cell"]==cell and row["method"]==method),None)
                if row:
                    _errorbar(axes[0],i+(j-2)*.12,_endpoint(row,"family_coverage"),color=(BLUE,GREEN,PURPLE,ORANGE,RED)[j],
                        label=LABELS[method] if i==0 else None)
        axes[0].axhline(.95,color=".5",linestyle="--",linewidth=.8)
        axes[0].set(xticks=[0,1],xticklabels=["IID bounded","IID finite moment"],ylabel="Family coverage",ylim=(0,1.03),title="Theorem-compatible strong anchors")
        axes[0].legend(frameon=False,fontsize=6.2,loc="best")
        for index,(cell,color) in enumerate((("iid-bounded",BLUE),("iid-heavy",RED))):
            widths=[]
            for method in methods:
                record=next((row for row in selected if row["cell"]==cell and row["method"]==method),{})
                widths.append(_number(record.get("mean_per_trial_coordinate_width")))
            axes[2].plot(range(len(methods)),[np.nan if value is None else value for value in widths],"o-",color=color,label=cell)
        axes[2].set_xticks(range(len(methods)),["COMET\n= generic","Bernstein","Catoni","OPE\nbetting","DR EB"],rotation=35,ha="right")
        axes[2].set(ylabel="Mean raw CI width",title="IID anchors: widths and coverage together")
        axes[2].legend(frameon=False,fontsize=7)
    else:_unavailable(axes[0],"Strong-anchor analysis unavailable")
    if not selected:_unavailable(axes[2],"Strong-anchor width data unavailable")
    control_rows=[row for row in (controls or {}).get("summaries",[]) if _number(row.get("delta"))==.05]
    cells=sorted({row["control"] for row in control_rows})
    if cells:
        for i,control in enumerate(cells):
            for j,(engine,color,label) in enumerate((("valid_actual_model",BLUE,"Valid actual model"),("intentionally_invalid",RED,"Intentionally invalid (heuristic)"))):
                row=next((row for row in control_rows if row["control"]==control and row["engine"]==engine),None)
                if row:_errorbar(axes[1],i+(j-.5)*.18,row.get("false_claim"),color=color,label=label if i==0 else None)
        axes[1].set_xticks(range(len(cells)),[cell.replace("_"," ") for cell in cells],rotation=55,ha="right")
        axes[1].set(ylabel="Any false claim per whole log",ylim=(-.03,1.03),title="Invalid assumptions are diagnostic")
        axes[1].legend(frameon=False,fontsize=6.8,loc="best")
    else:_unavailable(axes[1],"Negative-control analysis unavailable")
    scaling=[row for row in rows if row["cell"].startswith("scaling-N")]
    if scaling:
        for method,line in (("comet_local","-"),("truncated_global_envelope","--")):
            for outcome,color in (("bounded",BLUE),("heavy",RED)):
                chosen=sorted([row for row in scaling if row["method"]==method and row["cell"].endswith("-"+outcome)],
                    key=lambda row:int(row["cell"].split("-N")[1].split("-")[0]))
                xx=[int(row["cell"].split("-N")[1].split("-")[0]) for row in chosen]
                yy=[_number(row.get("mean_per_trial_coordinate_width")) for row in chosen]
                axes[3].plot(xx,[np.nan if value is None else value for value in yy],"o"+line,color=color,
                    label=outcome+", "+("local" if method=="comet_local" else "global"))
        axes[3].set(xscale="log",xlabel="Retained rows N",ylabel="Mean raw coordinate CI width",title="Fixed-DGP scaling (descriptive)")
        axes[3].legend(frameon=False,fontsize=7)
    else:_unavailable(axes[3],"Scaling-anchor analysis unavailable")
    _finish_axes(grid)
    _save(fig,output,"appendix_anchors_controls",formats)


def _csv_bytes(rows,default_fields=()):
    fields=list(default_fields)
    for row in rows:
        for key in row:
            if key not in fields:fields.append(key)
    stream=io.StringIO(newline="")
    writer=csv.DictWriter(stream,fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _event_records(analyses,anchors,controls):
    records=[]
    supplied=dict(analyses)
    if anchors:supplied["ANCHORS"]=anchors
    for suite,data in supplied.items():
        for row in (data or {}).get("summaries",[]):
            base=dict(suite=suite,cell=row["cell"],method=row["method"],method_label=LABELS.get(row["method"],row["method"]),
                delta=row["delta"],independent_trials=row["independent_trials"],
                equivalence_group="COMET=matched_generic" if row["method"] in ("comet_local","generic_matched") else "",
                input_status=data.get("status"),input_phase=data.get("phase"))
            events=dict(row.get("endpoints",{}))
            events.update(row.get("extension_endpoints",{}))
            events.update(row.get("pipeline_metrics",{}).get("joint_events",{}))
            events["family_coverage"]=row.get("family_coverage")
            for name,value in events.items():
                value=value or {}
                ci=value.get("wilson95") or [None,None]
                records.append(dict(base,endpoint=name,applicable=value.get("applicable",bool(value)),
                    hits=value.get("hits"),denominator=value.get("denominator",0),
                    unknown_trials=value.get("unknown_trials",0),rate=value.get("rate"),
                    wilson95_lo=ci[0],wilson95_hi=ci[1],
                    uncertainty="pointwise whole-trial Wilson 95%; not simultaneous"))
    for row in (controls or {}).get("summaries",[]):
        for name in ("interval_coverage","false_claim","false_safe","false_violation","true_violation_detected"):
            value=row.get(name) or {}
            ci=value.get("wilson95") or [None,None]
            records.append(dict(suite="NEGATIVE_CONTROLS",cell=row["control"],method=row["engine"],
                method_label=row["engine"],delta=row["delta"],independent_trials=row["independent_units"],
                equivalence_group="",input_status=controls.get("status"),input_phase=controls.get("phase"),
                endpoint=name,applicable=bool(value) and value.get("denominator",0)>0,
                hits=value.get("hits"),denominator=value.get("denominator",0),
                unknown_trials=value.get("unknown_units",0),rate=value.get("rate"),
                wilson95_lo=ci[0],wilson95_hi=ci[1],guarantee_type=row.get("guarantee_type"),
                uncertainty="pointwise whole-log diagnostic Wilson 95%; not validity evidence for invalid branches"))
    return records


def _pipeline_value_records(analyses):
    rows=[]
    for suite in ("E5","E6"):
        for row in (analyses.get(suite) or {}).get("summaries",[]):
            for metric,value in row.get("pipeline_metrics",{}).get("numeric_metrics",{}).items():
                rows.append(dict(suite=suite,cell=row["cell"],method=row["method"],delta=row["delta"],
                    metric=metric,mean=value.get("mean"),value_count=value.get("value_count"),
                    whole_trials=value.get("whole_trials"),unassessable_trials=value.get("unassessable_trials"),
                    value_scope=value.get("value_scope"),uncertainty="no uncomputed numeric confidence interval supplied"))
    return rows


def _paired_records(analyses,anchors):
    records=[]
    supplied=dict(analyses)
    if anchors:supplied["ANCHORS"]=anchors
    for suite,data in supplied.items():
        for key in ("paired_width_differences","paired_safe_useful_differences"):
            for row in (data or {}).get(key,[]):
                record=dict(row,suite=suite,comparison_type=key)
                for name,value in record.items():
                    if isinstance(value,(list,dict)):
                        record[name]=json.dumps(value,separators=(",",":"))
                records.append(record)
    return records


def _latex_escape(value):
    replacements={"\\":r"\textbackslash{}","&":r"\&","%":r"\%","$":r"\$","#":r"\#","_":r"\_",
                  "{":r"\{","}":r"\}","~":r"\textasciitilde{}","^":r"\textasciicircum{}"}
    return "".join(replacements.get(char,char) for char in str(value))


def _rate_text(record):
    if record.get("applicable") is False:
        return "NA"
    if record.get("unknown_trials",0):
        return "NA (unknown "+str(record["unknown_trials"])+")"
    if not _finite(record.get("rate")):
        return "NA"
    ci=(record.get("wilson95_lo"),record.get("wilson95_hi"))
    return f"{record['rate']:.3f}"+(f" [{ci[0]:.3f}, {ci[1]:.3f}]" if all(_finite(value) for value in ci) else " (CI NA)")


def _latex_events(records):
    lines=[r"% Generated from supplied immutable analysis summaries; requires booktabs and longtable.",
        r"\begingroup\small\setlength{\tabcolsep}{3pt}",
        r"\begin{longtable}{p{.04\linewidth}p{.18\linewidth}p{.19\linewidth}p{.16\linewidth}r p{.21\linewidth}}",
        r"\caption{Observed complete-trial events. Brackets are pointwise 95\% Wilson intervals, not simultaneous bounds. Candidate coordinates do not increase the replication count.}\\",
        r"\toprule Suite & Cell & Method & Event ($\delta$) & Events/$n$ & Rate [95\% CI]\\\midrule\endfirsthead",
        r"\toprule Suite & Cell & Method & Event ($\delta$) & Events/$n$ & Rate [95\% CI]\\\midrule\endhead"]
    for row in records:
        count="NA" if row.get("hits") is None else f"{row['hits']}/{row['denominator']}"
        lines.append(" & ".join(_latex_escape(value) for value in (
            row["suite"],row["cell"],row["method_label"],row["endpoint"]+f" ({row['delta']:g})",count,_rate_text(row)))+r"\\")
    if not records:lines.append(r"\multicolumn{6}{l}{No empirical summaries supplied; no numeric results generated.}\\")
    lines.extend([r"\bottomrule\end{longtable}\endgroup",""])
    return "\n".join(lines).encode("utf-8")


def _equivalence_checks(analyses):
    checks=[]
    for suite,data in analyses.items():
        rows={(row["cell"],row["method"],row["delta"]):row for row in (data or {}).get("summaries",[])}
        for (cell,method,delta),left in rows.items():
            if method!="comet_local":continue
            right=rows.get((cell,"generic_matched",delta))
            if right is None:continue
            fields=("family_coverage","endpoints","mean_per_trial_coordinate_width")
            same=all(left.get(field)==right.get(field) for field in fields)
            checks.append(dict(suite=suite,cell=cell,delta=delta,status="IDENTICAL_REPORTED_SUMMARIES" if same else "SUMMARY_DIFFERENCE_REQUIRES_REVIEW",
                interpretation="algebraically equivalent matched configurations; not an independent superiority comparison"))
    return checks


CAPTIONS={
    "fig1_core_validity_informativeness":"E1, primary 95% level. Coverage and detection error bars are pointwise Wilson intervals over complete independent logs, not simultaneous bounds. Width medians/IQR are descriptive coordinate quantiles; nontriviality is distinct from a useful certified decision. The final panel uses maxima within each complete trial, and retains uninformative cells. COMET and the fully matched generic method are algebraically identical; their separate rows remain in the tables.",
    "fig2_query_locality":"E2 mechanism, predeclared constant policy 0. Audited-first-half and global queries are shown separately, across every outside hub/overlap condition. Three pure residual-truncation layers isolate the costs: global envelope/global graph, local moments/global graph, and local moments/induced-support graph. COMET / matched generic additionally dispatches to sharp bounded certificates; its improvement over pure local truncation at the same coloring is a bounded-branch benefit, not a graph-localization benefit. The vertical coordinate is a design-determined normalized radius, not Monte Carlo uncertainty. No average over outside/global auditors is substituted for locality. All methods, four policies and auditors remain in empirical_coordinates.csv.",
    "fig3_paired_contrasts":"E3, primary 95% level, constant changed-policy anchor and all-row auditor. Direct signed contrasts and subtraction of simultaneously certified, deduplicated unique levels share the same total error budget and logged data. Shown widths are descriptive per-query medians; reducing a policy change also changes its signal and feasible range, and does not by itself establish improved sign-certification power.",
    "fig4_gap_power_boundary":"E4 whole-trial probabilities of certifying the primary query safe or violating its threshold. Shaded gamma<=0 points are null/safe settings, not positive-gap power. Error bars are pointwise Wilson 95% intervals. The 2r line is a design-only sufficient boundary on the coverage event; an off-axis boundary is reported numerically, not clipped into an apparent successful regime. All false-safe/false-violation counts and intervals remain in empirical_events.csv.",
    "fig5_safe_useful_return":"E5 complete independent three-split trials. Four different joint events are reported; zero false-return counts do not mean zero risk. Gray/NA denotes unavailable or unassessable input, never an imputed zero. Point and in-sample arms are heuristic, status quo is an uncertified reference, and abstention cannot count as useful return. Fixed-slice coverage concerns its restricted family; return feasibility is evaluated against the primary independently discovered constraints. Every risk and utility coordinate used for selection is included in the actual family budget. Pointwise Wilson intervals and denominators are in empirical_events.csv.",
    "appendix_anchors_controls":"Supplementary theorem-compatible strong baselines and prespecified invalid-assumption diagnostics. Ineligible IID/OPE anchors are not fabricated. Intentionally invalid controls are heuristic, and an honest refusal is not evidence of zero certification error. Wilson intervals use whole independent units. Fixed-DGP scaling is descriptive, not a minimax theorem.",
    "appendix_real_covariates":"Real-covariate pipeline results, if actually supplied. The finite-population selective-label task is not randomized evidence about a social intervention. Missing data are explicitly unavailable rather than replaced by synthetic numbers."}


def render_bundle(output_directory,*,analyses=None,detailed=None,anchors=None,controls=None,
                  formats=("pdf","png"),only=None,raw_envelope=None):
    output=Path(output_directory)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("figure bundles are immutable; choose a new output directory")
    formats=tuple(formats)
    if not formats or not set(formats)<={"pdf","png","svg"}:
        raise ValueError("choose PDF, PNG or SVG figure formats")
    output.mkdir(parents=True,exist_ok=True)
    input_analyses,input_detailed=analyses or {},detailed or {}
    data,detail,availability={}, {}, {}
    for suite in SUITES:
        data[suite],availability[suite]=_load_summary(input_analyses.get(suite),suite)
        detail[suite],availability[suite+"_detailed"]=_load_detailed(input_detailed.get(suite),suite+"_detailed")
    anchor_data,availability["ANCHORS"]=_load_summary(anchors,"ANCHORS")
    control_data,availability["NEGATIVE_CONTROLS"]=_load_summary(controls,"NEGATIVE_CONTROLS")
    selected=set(only or ("core","locality","contrasts","power","pipeline","appendix"))
    allowed={"core","locality","contrasts","power","pipeline","appendix","real_covariates"}
    if not selected<=allowed:raise ValueError("unknown figure selection")
    figure_names=[]
    fixture=any("FIXTURE" in str(value.get("phase","")) for value in availability.values())
    fixture_token=FIXTURE_RENDERING.set(fixture)
    try:
      with plt.rc_context(dict(STYLE,**{"svg.hashsalt":"COMET-post-CSTAT"})):
        for key,call,name in (
            ("core",lambda:_plot_core(data["E1"],detail["E1"],output,formats),"fig1_core_validity_informativeness"),
            ("locality",lambda:_plot_locality(detail["E2"],output,formats),"fig2_query_locality"),
            ("contrasts",lambda:_plot_contrasts(detail["E3"],output,formats),"fig3_paired_contrasts"),
            ("power",lambda:_plot_power(data["E4"],detail["E4"],output,formats),"fig4_gap_power_boundary"),
            ("pipeline",lambda:_plot_pipeline(data["E5"],output,formats),"fig5_safe_useful_return"),
            ("appendix",lambda:_plot_appendix(anchor_data,control_data,output,formats),"appendix_anchors_controls"),
            ("real_covariates",lambda:_plot_pipeline(data["E6"],output,formats,"appendix_real_covariates"),"appendix_real_covariates")):
            if key in selected:
                call();figure_names.append(name)
    finally:
        FIXTURE_RENDERING.reset(fixture_token)
    events=_event_records(data,anchor_data,control_data)
    coordinates=[dict(row,suite=suite) for suite,record in detail.items() for row in record["queries"]]
    widths=[dict(row,suite=suite) for suite,record in detail.items() for row in record["groups"]]
    values=_pipeline_value_records(data)
    anchor_widths=[dict(suite="ANCHORS",cell=row["cell"],method=row["method"],delta=row["delta"],
        independent_trials=row["independent_trials"],mean_raw_coordinate_width=row.get("mean_per_trial_coordinate_width"),
        width_trials=row.get("width_trials"),coverage_applicable=row.get("family_coverage") is not None,
        interpretation="fixed-DGP descriptive width; no invented mean-width CI") for row in (anchor_data or {}).get("summaries",[])]
    (output/"empirical_events.csv").write_bytes(_csv_bytes(events,("suite","cell","method","delta","endpoint","hits","denominator","rate","wilson95_lo","wilson95_hi")))
    (output/"empirical_coordinates.csv").write_bytes(_csv_bytes(coordinates,("suite","cell","method","delta","query_id","query_scope","normalizer","known_feasible_diameter")))
    (output/"empirical_widths.csv").write_bytes(_csv_bytes(widths,("suite","cell","method","delta","independent_trials")))
    (output/"pipeline_values.csv").write_bytes(_csv_bytes(values,("suite","cell","method","delta","metric","mean","value_count","value_scope")))
    (output/"anchor_widths.csv").write_bytes(_csv_bytes(anchor_widths,("suite","cell","method","delta","independent_trials","mean_raw_coordinate_width","width_trials","coverage_applicable")))
    (output/"paired_comparisons.csv").write_bytes(_csv_bytes(_paired_records(data,anchor_data),("suite","cell","delta","left","right","mean_difference","bootstrap_pointwise95")))
    (output/"empirical_events.tex").write_bytes(_latex_events(events))
    captions="\n\n".join("### "+name+"\n\n"+CAPTIONS[name] for name in figure_names)
    (output/"captions.md").write_text(captions+"\n")
    if raw_envelope is not None:
        protocol,root=raw_envelope
        envelope=prespecified_envelope_diagnostics(protocol,root)
        (output/"prespecified_envelope_diagnostics.csv").write_bytes(_csv_bytes(envelope["rows"],("run_id","cell","query_id","observed_p_moment_over_envelope")))
        (output/"prespecified_envelope_diagnostics.json").write_text(json.dumps(envelope,indent=2,allow_nan=False)+"\n")
    manifest=dict(schema="post-cstat-empirical-figures-v1",status="ACTUAL_SUPPLIED_SUMMARIES_ONLY",
        data_scope="DETERMINISTIC_FIXTURE_NOT_SCIENCE" if fixture else "ACTUAL_SUPPLIED_ANALYSIS_ARTIFACTS",
        availability=availability,figures=figure_names,formats=formats,
        new_outcome_draws=0,legacy_new_outcome_draws=0,raw_checkpoints_replayed=False,
        equivalence_checks=_equivalence_checks(data),
        candidate_uncertainty="coordinate quantiles are descriptive; no candidate pooling for binomial uncertainty",
        errorbars="pointwise whole-trial Wilson intervals supplied by analysis; not simultaneous bands",
        code_sha256=_sha(__file__),outputs={path.name:_sha(path) for path in sorted(output.iterdir()) if path.is_file()})
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2,allow_nan=False)+"\n")
    return manifest


def prespecified_envelope_diagnostics(protocol_path,results_root):
    """Descriptive realized residual moments on frozen raw-debug IDs only.

    Rebuilds design arrays, never observations or oracle means. An observed
    moment/envelope ratio can exceed one under a legal moment bound: this is
    neither a moment test nor a certified estimate of an unknown tail scale.
    No returned number is supplied to an estimation radius.
    """
    from comet.checkpoint_store import CheckpointStore
    from experiments.core_graph_dgp import build_core_design
    manifest=json.loads(Path(protocol_path).read_text())
    config=manifest["config"]
    if config.get("suite") not in ("E1","DETERMINISTIC_RUNNER_FIXTURE"):
        raise ValueError("raw-envelope diagnostics currently support E1 only")
    store=CheckpointStore(results_root,manifest)
    rows,missing,failed=[],[],[]
    for run_id in config.get("raw_debug_run_ids",[]):
        payload=store.load(run_id)
        if payload is None:
            missing.append(run_id);continue
        result=payload["result"]
        raw=result.get("prespecified_raw_debug")
        if raw is None:
            missing.append(run_id);continue
        cell=run_id.split("/")[2]
        graph,overlap,outcome=cell.split("-")
        design=build_core_design(config["N"],graph,overlap,outcome,config["seed_domain"]+"/"+cell)
        actions=np.asarray(raw.get("actions"),dtype=np.uint8)
        outcomes=np.asarray(raw.get("outcomes"),dtype=float)
        if actions.shape!=(design.n,) or outcomes.shape!=(design.n,) or not np.isfinite(outcomes).all() or np.any(actions>1):
            failed.append(dict(run_id=run_id,status="INVALID_PRESPECIFIED_RAW_ARRAYS"));continue
        actual_hash=hashlib.sha256(actions.tobytes()+outcomes.astype("<f8").tobytes()).hexdigest()
        if actual_hash!=result.get("data_digest"):
            failed.append(dict(run_id=run_id,status="RAW_DATA_HASH_MISMATCH"));continue
        metadata=json.loads(gzip.decompress((Path(results_root)/"cell_designs"/(cell+".json.gz")).read_bytes()))
        array_checks=(("exposure_sha256",design.exposure),("common_nuisance_sha256",design.nuisance),
                      ("common_residual_moments_sha256",design.residual_moments))
        if any(metadata.get(key)!=hashlib.sha256(values.tobytes()).hexdigest() for key,values in array_checks):
            failed.append(dict(run_id=run_id,status="FROZEN_DESIGN_ARRAY_HASH_MISMATCH"));continue
        indices=np.arange(design.n)
        observed_e=design.exposure[indices,actions]
        if np.any(observed_e<=0):
            failed.append(dict(run_id=run_id,status="UNSUPPORTED_OBSERVED_EXPOSURE"));continue
        raw_residual=outcomes-design.nuisance[indices,actions]
        for query in design.queries:
            d=query.coefficients
            declared=np.sum(np.abs(d)**design.p*design.exposure**(1-design.p)*design.residual_moments,axis=1)
            residual=d[indices,actions]/observed_e*raw_residual
            observed=float(np.sum(np.abs(residual)**design.p))
            envelope=float(declared.sum())
            rows.append(dict(run_id=run_id,cell=cell,query_id=query.query_id,p=design.p,raw_N=design.n,
                observed_mean_abs_weighted_residual_p=observed/design.n,
                declared_mean_weighted_residual_p_envelope=envelope/design.n,
                observed_p_moment_over_envelope=observed/envelope if envelope>0 else None,
                maximum_observed_abs_unweighted_residual=float(np.max(np.abs(raw_residual))),
                bounded_residual_range_violation_rows=int(np.sum(np.abs(raw_residual)>.5)) if outcome=="bounded" else None,
                sample_scope="frozen prespecified raw-debug IDs only, not the full Monte Carlo study",
                inference_scope="observed descriptive ratio; not moment certification, tail-scale fitting or a radius input"))
    return dict(schema="prespecified-raw-envelope-diagnostics-v1",status="READ_FAILURES" if failed else "DESCRIPTIVE_ONLY",
        protocol_fingerprint=manifest["fingerprint"],prespecified_ids=config.get("raw_debug_run_ids",[]),
        missing_raw_ids=missing,failed_raw_ids=failed,rows=rows,new_outcome_draws=0,
        observations_regenerated=False,oracle_used=False,radii_modified=False,
        interpretation="a realized moment ratio above one need not violate a moment envelope; these few predeclared cases cannot certify an unknown scale")


def _path_mapping(values):
    result={}
    for value in values:
        if "=" not in value:raise ValueError("use SUITE=PATH for each analysis/detailed input")
        suite,path=value.split("=",1)
        if suite not in SUITES or suite in result:raise ValueError("use each E1--E6 suite at most once")
        result[suite]=Path(path)
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis",action="append",default=[],metavar="E1=PATH")
    parser.add_argument("--detailed",action="append",default=[],metavar="E1=PATH")
    parser.add_argument("--anchors",type=Path)
    parser.add_argument("--controls",type=Path)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--formats",default="pdf,png")
    parser.add_argument("--only",help="optional comma-separated subset: core,locality,contrasts,power,pipeline,appendix,real_covariates")
    parser.add_argument("--raw-envelope-protocol",type=Path)
    parser.add_argument("--raw-envelope-results",type=Path)
    args=parser.parse_args(argv)
    if bool(args.raw_envelope_protocol)!=bool(args.raw_envelope_results):
        parser.error("supply both raw-envelope protocol and results paths")
    result=render_bundle(args.output,analyses=_path_mapping(args.analysis),detailed=_path_mapping(args.detailed),
        anchors=args.anchors,controls=args.controls,formats=args.formats.split(","),
        only=args.only.split(",") if args.only else None,
        raw_envelope=(args.raw_envelope_protocol,args.raw_envelope_results) if args.raw_envelope_protocol else None)
    print(json.dumps(dict(status=result["status"],figures=result["figures"],new_outcome_draws=0,
        legacy_new_outcome_draws=0,availability=result["availability"]),indent=2))


if __name__=="__main__":
    main()

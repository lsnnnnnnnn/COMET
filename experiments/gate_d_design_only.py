"""Future D-stage feasibility algebra only. No RNG, simulator or oracle calls."""
from pathlib import Path
import csv
import json
from math import ceil
from comet.gate_c_contract import cell_from_dict,known_centered_envelope
from comet.robust_mean import exact_binomial_groups

ROOT=Path(__file__).resolve().parents[1]

def export():
    out=ROOT/'results/gate_D_proposals';out.mkdir(parents=True,exist_ok=True)
    # Bernoulli conditional means in [0,1], f=.25, threshold=.2*pi.
    rows=[]
    gaps=[0,.025,-.025,.05,-.05,.1,-.1,.2,-.2]
    for pi in (.02,.05,.1,.2):
      for chi in (1,4,8):
       for m in (1,16,64):
        for overlap,e in (('strong',.5),('weak',.01)):
         # Declared q1=.5; J=sum q^2/e. Candidate family size is a budget
         # design input here, not a claim that all candidates are duplicates.
         J=.25/e+.25/(1-e)
         for gap in gaps:
          mean=.45+gap/pi
          radius=(m*chi*pi*J/(.05*32768))**.5
          # Strict gap>2r gives a sufficient decision condition on the valid
          # simultaneous event. This is NOT an exact power calculation.
          needed=None if gap==0 else ceil(4*m*chi*pi*J/(.05*gap*gap))+1
          rows.append(dict(study='D1',pi=pi,chi=chi,family_size=m,overlap=overlap,e1=e,q1=.5,
            signed_raw_gap=gap,implied_target_mean=mean,mean_class_feasible=0<=mean<=1,
            N_reference=32768,design_radius=radius,minimum_integer_N_for_abs_gap_gt_2r=needed,
            eligible_for_run=False,reason='proposal_only; impossible means excluded before draws' if not 0<=mean<=1 else 'proposal_only; no outcomes'))
    with (out/'D1_feasibility.csv').open('w',newline='') as f:
      w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    settings=json.loads((ROOT/'configs/gate_C_frozen.json').read_text())
    cell=cell_from_dict(settings['cells'][-1]);d=cell.design
    # Fixed B=128,K=9,Lmin=14 from the registered exact-binomial calculation.
    # Use direct exact budget output through its public selector when available.
    K=exact_binomial_groups(len(d.family),.05,d.B)["K"]; L=d.B//K
    rows=[]
    for candidate in d.family:
      nu=max(known_centered_envelope(cell,candidate.q_vector,(1-e,e),cell.p) for e in d.e_by_context)**(1/cell.p)
      mass=1 if candidate.auditor=='all' else .5
      r=32**(1/cell.p)*nu*(d.chi/(L*d.n0))**((cell.p-1)/cell.p)
      # Raw diameter < feasible diameter suffices for every center to avoid
      # containing the entire feasible range. Necessary N is strict > bound.
      target=mass/2
      n0bound=d.n0*(r/target)**(cell.p/(cell.p-1))
      n0=(int(n0bound)//(2*d.chi)+1)*(2*d.chi)
      rows.append(dict(study='D5',candidate_id=candidate.candidate_id,p=cell.p,nu=nu,B=d.B,K=K,L_min=L,chi=d.chi,
        current_N=d.B*d.n0,current_radius=r,known_target_diameter=mass,
        strict_radius_goal=target,minimum_balanced_n0=n0,required_N=d.B*n0,
        idealized_memory_MiB_at_preflight_bytes_per_row=118.44*(d.B*n0)/32768,
        run_authorized=False))
    with (out/'D5_F_radius_inversion.csv').open('w',newline='') as f:
      w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    (out/'manifest.json').write_text(json.dumps(dict(status='UNRUN_DESIGN_ONLY',new_outcome_draws=0,
      scope='Analytic feasibility, not confirmed power or allocated samples',D1_rows=648,D5_rows=len(rows),
      memory_note='Linear extrapolation from preflight process peak, not a measured D-stage resource or a tight bound'),indent=2)+'\n')
    print('Design-only tables written; no outcomes generated.')

if __name__=='__main__':export()

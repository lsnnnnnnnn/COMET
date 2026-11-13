# D2 — discover, freeze, certify (UNRUN PROPOSAL)

Fresh domain: `COMET-D2-v1`. Construct at least four exogenous pre-action features
G, degree, new_user and Z. Define degree's q80 from the fixed design, before
outcomes. A variable degree covariate may come from a separate fixed context
graph; it must not be substituted for the sufficient stochastic conflict graph. Plant the interaction 1{G=1, degree>q80, new_user=1, Z=high}; explicitly
allocate its mass through a fixed feature table repeated across independent
blocks. Do not obtain the interaction from evaluation residuals. Define
intervention-dependent mean shifts, bounded in [0,1], for null and alternative
settings, and preserve independent block-local assignment/outcome primitives.

Use two independent datasets: discovery/pilot blocks and certification blocks.
Discovery trains bounded nuisance and searches a preregistered finite rule class
using pilot logs only. Freeze search grammar, loss, deterministic tie rule,
minimum mass, thresholds, policy library and top L in {1,5,10}. Conditional on
the entire pilot, the held-out design/target and proved certificate remain valid
if its stochastic assumptions hold. Oracle subgroup labels and all certification
outcomes are inaccessible to discovery. Freeze selected candidates in a hashed
artifact before revealing the held-out data.

Pay the actual policy × selected auditor × constraint multiplicity on each
held-out log. Use graph mean for bounded rewards and stable-target MOM only
where the held-out construction satisfies its common-block-target assumption.
Comparators: coarse frozen slices; in-sample discovery with explicit UNCERTIFIED
status; independent split with naive iid CI, labeled invalid under chi>1; and
valid graph-aware certification. Never promote a comparator because its
observed coverage is attractive.

Primary held-out endpoints: familywise false violation under the global null,
any true certified violation under the alternative, and abstention. Secondary:
subgroup IoU/precision/recall against planted membership, recovered mass, width,
family coverage and separate pilot/certification cost. Recovery truth is
available only to final evaluation. Preregister 1,000 complete independent
pilot+heldout pairs per final cell, with fresh stream domains for both halves.
Pilot/evaluation block counts are selected by design-only radii plus an
independent engineering budget and frozen before confirmation. D2 is unrun.

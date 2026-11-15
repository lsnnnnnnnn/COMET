# E6 single-dataset choice before pipeline randomness

Selected source: California 2018 ACS one-year person PUMS, the master default.
No existing TGB/Folktables/ACS semi-synthetic implementation or data was found
in this workspace at selection. No alternate dataset is selected concurrently.

Official archive:
https://www2.census.gov/programs-surveys/acs/data/pums/2018/1-Year/csv_pca.zip

The official directory's rounded size is 64M, below the authorized 512 MiB
compressed download limit. Task filters, source terms and attribution references
were inspected and recorded in `reports/post_cstat_reference_sources.json`.
Downloading an existing finite population is distinct from generating a new
simulation trial. No training/discovery/certification random sources, new study
seeds, or outcomes are consumed at this choice step.

The fixed-population selection benchmark does not estimate an intervention's
causal effect on income. Full labels must remain outside certification inputs
except where revealed by the declared selective logger. The eventual fixed
population, source-disjoint splits and the 16,384 certification-row availability
check must be specified before E6 simulated logging/pipeline randomness. Any
unavailable dataset will be reported DATA_BLOCKED without a silent substitute.

The scope, theory and claim inputs have since been recovered and read. The user
waived the missing EXPERIMENT_BLUEPRINT.json input; the receipt is saved in
task_materials/post_cstat/INPUT_RESOLUTION.md. The final E6 protocol still
requires the actual archive hash and available row count. This source choice
is not a protocol freeze.

## Actual download outcome

Status: **DATA_BLOCKED**, zero bytes downloaded and zero E6 trials generated.

1. Sandbox `curl --fail --location --max-time 90 .../csv_pca.zip` exited 6:
   `Could not resolve host: www2.census.gov`.
2. Authorized network retry of the same official URL exited 56:
   `The requested URL returned error: 403`.

The second command finished; it is not running in the background. The source
metadata remain verified, while archive hash, actual row count and population
availability remain unverified. The failure does not establish that the source
is unavailable in the user's own environment. No different dataset was fetched.

A subsequent attempt to open the same official directory in the in-app browser
timed out after approximately 36 seconds before a readable page or download was
obtained. It supplied no archive or row-count evidence. The external data path
remains DATA_BLOCKED while the synthetic suites continue.

A final bounded retry of the identical official archive used a standard browser
User-Agent, HTTPS-only redirects,60-second timeout and512MiB size cap. It
again returned HTTP403 (curl exit56), size_download=0. No archive or partial
data file was obtained. See E6_same_source_retry_stdout/stderr.txt. The client
change did not resolve access; source/data choice and E6 trial count remain
unchanged. No further automatic alternate-source attempt is scheduled.


## Final same-source server check (15 November 2026)

The same official ACS CA2018 ZIP was attempted once on amax in the isolated server project with a60-second/512MiB limit. It returned HTTP403/curl22 after1.429s;4861bytes were an error body, not aZIP. No preparation, freeze, replacement dataset orE6 trial followed. Receipt: `E6_server_download_20261115T042857Z/receipt.json`. E6 remainsDATA_BLOCKED_NOT_FROZEN with1000reserved IDs.

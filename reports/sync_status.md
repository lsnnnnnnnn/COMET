# Gate A+B source synchronization

Both GitHub pushes succeeded and remote refs were verified by `git ls-remote`.
No main branch was overwritten and no force push was used.

| Artifact | Repository and branch | Audited source commit |
|---|---|---|
| Original imported ZIP sources | local baseline | `58ad7bdf8965418cb8c3b48b2214fbc2aadd2a56` |
| Gate A theory/manuscript | COMET history | `5d93b1f` |
| Gate B code, tests and saved smoke | [COMET, codex/gates-a-b](https://github.com/lsnnnnnnnn/COMET/tree/codex/gates-a-b) | `eae88a4ceb5b65dd370def0a508e8840881ef00a` |
| Manuscript-only subtree | [COMET_overleaf, codex/gates-a-b](https://github.com/lsnnnnnnnn/COMET_overleaf/tree/codex/gates-a-b) | `df70f486fc08139057436e2781c212ad741ef646` |

The experiment branch also receives a final reporting-only commit containing
this record and `modified_files.txt`. Its code and results remain those of
`eae88a4`; the manuscript subtree does not change. Use `git log --oneline -4`
or the branch URL to identify the final delivery head without a self-referential
commit hash in this file.

Actual commit and synchronization commands:

```sh
git add README.md comet configs pyproject.toml tests reports results
git -c user.name='COMET Research' -c user.email='comet-research@users.noreply.github.com' commit -m 'Complete Gate B certified package tests and 30-replication CPU smoke'
git remote add origin https://github.com/lsnnnnnnnn/COMET.git
git remote add overleaf https://github.com/lsnnnnnnnn/COMET_overleaf.git
git subtree split --prefix=paper -b codex/overleaf-gates-a-b
git -c http.proxy=http://proxy-dku.oit.duke.edu:3128 push -u origin codex/gates-a-b
git -c http.proxy=http://proxy-dku.oit.duke.edu:3128 push overleaf codex/overleaf-gates-a-b:codex/gates-a-b
git -c http.proxy=http://proxy-dku.oit.duke.edu:3128 ls-remote origin refs/heads/codex/gates-a-b
git -c http.proxy=http://proxy-dku.oit.duke.edu:3128 ls-remote overleaf refs/heads/codex/gates-a-b
```

`reports/source_diff.patch` includes every paper change relative to the original
baseline, including new source files. `reports/modified_files.txt` lists all 56
changed or added files in this run relative to that baseline. Source ZIP imports
themselves are preserved in the separate baseline commit.

## Server state

SSH to `shengen@10.200.13.23` succeeded after the user loaded the existing key.
Host `amax`, `/data1/shengen` present, Python 3.12.3. The proposed new directory
`/data1/shengen/COMET_gate_AB_20261112` was checked and did not exist. No remote
experiment was necessary or started; all smoke measurements are local CPU runs.

The server's direct `git ls-remote` timed out after 15 seconds. Through the system
proxy it reached GitHub but failed with `could not read Username ... terminal
prompts disabled`: the server lacks the local Mac's GitHub credential. This is
separate from SSH authentication. The already completed Mac-to-GitHub pushes
are unaffected. No personal access token/private key was copied to the server.

For the next session's remote experiments, use authorized server-side GitHub
authentication or transfer a Git bundle of the already-published commit and
verify its commit ID, keeping GitHub as the synchronization source. Do not start
large runs until the future design and relevant proof assumptions are settled.

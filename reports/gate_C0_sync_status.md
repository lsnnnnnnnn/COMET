# Gate C0 source and synchronization status

The result-bearing C0 commit was pushed successfully (exit 0), then verified
with `git ls-remote`. No branch was force-pushed and no A+B history was changed.

| Repository / role | Branch | Exact verified SHA |
|---|---|---|
| COMET / preserved A+B | codex/gates-a-b | d11a36f3b967165f4e0cdf56bf6a262d178e41bd |
| COMET / preregistered code, proofs, config | codex/gate-c0-informativeness (ancestor) | 15af1842dff7dddf89bbad1c98e8b3ac7a8de3b0 |
| COMET / actual C0 results and decision | codex/gate-c0-informativeness | f2b4e4c70d5837296e73709cf3ac547c6f46f116 |
| COMET_overleaf / unchanged paper | codex/gates-a-b | df70f486fc08139057436e2781c212ad741ef646 |

The result-bearing SHA above is the commit containing all scientific results.
This synchronization note and final command-log additions form a subsequent
metadata-only audit commit. Its exact SHA and final remote-tip/clean-worktree
verification are reported in the final response; a committed file cannot
contain its own future content hash. No scientific source or result changed
after f2b4e4c. No manuscript was modified in C0, so there is no new Overleaf
commit to push. The TeX patch is a suggestion stored in the experiment repo.

Experiment repository: https://github.com/lsnnnnnnnn/COMET

Paper repository: https://github.com/lsnnnnnnnn/COMET_overleaf

Git operations used the working per-command proxy
`http://proxy-dku.oit.duke.edu:3128`. No global Git/SSH configuration was changed,
and no credentials were stored in the repository. The C0 pilot ran locally on
CPU. No server job, dataset download or full Gate C campaign was started.

The final changed-file inventory contains 57 paths (two modified existing
Python files, all others new). A+B preservation and pilot/source audit artifacts
are `results/gate_C0/baseline_preservation.json` and
`results/gate_C0/pilot_audit.json`. The final full test result is 377 passed;
the scientific code and tests remained frozen after preregistration.

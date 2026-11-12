# C-PREFLIGHT provenance and synchronization

The C-PREFLIGHT result commit was pushed successfully and verified with a
remote ref read. No force-push, prior-branch rewrite or paper modification was
performed. The repository work follows the explicitly limited preflight phase.

| Role | Repository / branch | Exact SHA |
|---|---|---|
| Preserved A+B | COMET / codex/gates-a-b | d11a36f3b967165f4e0cdf56bf6a262d178e41bd |
| Preserved A+B+C0 baseline | COMET / codex/gate-c0-informativeness | 3f8902d1033f3c4eece9a3746912ac9f1d8904ef |
| Code/proof/config/seed freeze before primary outcomes | COMET / codex/gate-c-preflight ancestor | ab4c74fbf1ae84c0e5ffd72d77ce5b48d3fba8cb |
| Actual preflight results and PASS/GO report | COMET / codex/gate-c-preflight | b17ad86a97a06617a15f890e0dcbcbde5d341360 |
| Untouched Overleaf paper | COMET_overleaf / codex/gates-a-b | df70f486fc08139057436e2781c212ad741ef646 |

All preserved branch SHAs were checked with `git ls-remote`; the scientific
batch manifest records the freeze SHA and unchanged source/config hashes.
All 152 prior tracked files remain byte-identical. The final path inventory
contains 70 new files relative to the baseline, with no changes to old files.

This note and the completed command log form a metadata-only follow-up commit.
Its exact delivery SHA, final remote-tip verification and clean status are
reported in the final response; a committed file cannot contain its own future
hash. No scientific code, frozen settings or numeric results changed after
the result commit above.

The working per-command proxy was `http://proxy-dku.oit.duke.edu:3128`; no global
Git/SSH settings or credentials were changed or stored. Twelve local CPU
preflight logs were completed with a tested crash/resume path. Zero
confirmatory, secondary or later-phase logs were generated. No server/GPU job,
large dataset download or manuscript update was performed.

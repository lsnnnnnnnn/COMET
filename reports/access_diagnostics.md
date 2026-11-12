# Access diagnosis (2026-11-12)

These are observations from this Codex session, not a claim that the user's
normal terminal/browser cannot connect.

- GitHub connector metadata queries for both requested repositories returned
  HTTP 404. Connector permissions are separate from local Git credentials.
- Sandboxed direct Git initially failed DNS resolution. Escalated direct Git
  timed out connecting to GitHub port 443.
- macOS system configuration declares HTTP/HTTPS proxy
  `proxy-dku.oit.duke.edu:3128`. Running Git with the one-command option
  `-c http.proxy=http://proxy-dku.oit.duke.edu:3128` made `git ls-remote` succeed
  (exit 0) for both `lsnnnnnnnn/COMET` and `lsnnnnnnnn/COMET_overleaf`.
  Neither returned refs at this check. No global Git/proxy configuration was changed.
- A separate curl connectivity check succeeded. The difference between these
  command routes is sufficient to explain why blanket “GitHub unreachable”
  would have been inaccurate; the exact direct-Git routing cause is unresolved.
- SSH TCP connection and host-key verification for `shengen@10.200.13.23`
  succeeded. The server accepted the public key offered from `~/.ssh/id_ed25519`.
  `ssh-add -l` reported an empty agent. Noninteractive authentication failed.
  `ssh-add --apple-use-keychain ~/.ssh/id_ed25519` requested the private-key
  passphrase and exited without loading it when no input was supplied.
  No private key or passphrase was read, exported, or stored in this repository.
- The user chose to complete local commits/results first. No remote experiment
  or dataset download is necessary for Gates A+B.

To enable the existing key for this agent, the user can run the same `ssh-add`
command in their own terminal and enter the passphrase locally. There is no need
to provide the passphrase in chat or change server authorization.

The user subsequently loaded the key in their own terminal. A repeat
`ssh -o BatchMode=yes -o ConnectTimeout=10 10.200.13.23` succeeded: host `amax`,
`/data1/shengen` present, Python 3.12.3. Both Git repository access and SSH
access are therefore operational; no credential was requested in chat.

The initial default Python lacked pytest. Package installation attempts failed
through the network/package proxy. The local environment was successfully built
with `/opt/anaconda3/bin/python -m venv --clear --system-site-packages .venv`,
using installed pytest 7.4.4, setuptools 69.5.1, wheel 0.43.0, and Python 3.12.2.
Only the repository's virtual environment was modified.

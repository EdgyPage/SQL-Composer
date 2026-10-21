# Code audit (2026-10-21)

The user (2026-10-21): "Create a plan to scan the codebase for any malicious code or patterns. No
connections to anything on the Web." Decided with the user: the scan reaches the repo, every
branch and tag's history, `.git/` and `.venv`; it leaves a dated report and lasting checks that
pytest holds. The approved plan is in the ticket.

## Notes

- The offline policy (`tools/offline_policy.py`, ADR 0004) asks whether anything reaches the
  network, starts a process or runs code it can't see. The audit asks what that leaves out, in a
  reader of its own, `tools/code_audit.py`, which reuses the policy's `Finding` and skip list.
- The user OK'd (2026-10-21) two `ALLOWED` entries, `tools/how_to_page.py`'s `stand_ins_of`
  loading a how-to by its path, and the offline hook judging every checkout by the project's own
  policy.
- Anything that looks truly malicious stops the work: report it to the user first.

## Tickets

- [01 Scan for malicious code](issues/01-scan-for-malicious-code.md)

## Decisions so far

- [01 Scan for malicious code](issues/01-scan-for-malicious-code.md): nothing malicious; the
  audit's kinds, the policy's new loaders and page patterns, and the hook's fix are in.

## Not yet specified

- Nothing.

## Out of scope

- Checking installed wheels against PyPI, which needs the network; the user's machine outside
  the repo and its `.venv`.

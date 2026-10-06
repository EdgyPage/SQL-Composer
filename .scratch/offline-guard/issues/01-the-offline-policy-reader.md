# The offline policy reader

Type: task
Status: open
Blocked by: nothing
Size: M

## Question

Plan steps 1 and 3 (without the hook test): `tools/offline_policy.py`, the AST and page scanner with its scopes and `ALLOWED` allowlist, its command line, and `tests/repo/test_offline_policy.py`; the three page tests call its HTML check.

## Done when

- The repo scans clean; every forbidden form in plan step 3 is caught; an allowlisted socket off 127.0.0.1 and a stale entry fail.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).

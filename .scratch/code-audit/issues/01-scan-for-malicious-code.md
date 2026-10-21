# Scan for malicious code

Type: task
Status: claimed
Size: M

## Question

Scan the repo for malicious code or patterns, reaching nothing on the web: every file, every
branch and tag's history, `.git/` and `.venv`. Leave a dated report and lasting checks.

## Done when

- `tools/code_audit.py` reads the repo for hidden text, text that isn't UTF-8, encoded payloads,
  reaches for credentials or the home folder, config that runs or fetches code, and notebooks
  that were run; `tests/repo/test_code_audit.py` holds the repo clean and shows each kind found.
- The offline policy also finds code loaded from a file or from bytes (pickle, marshal, shelve,
  zipimport, `importlib.util`'s loaders) and the page references it missed (forms, `javascript:`
  and `data:` URIs, `window.open`, `location =`, meta refresh, `eval` in a page).
- The offline hook judges every checkout by the project's own policy.
- `docs/code-audit.md` records what was read, how, each finding and its verdict, and what is out
  of scope; `docs/offline-audit.md` and CLAUDE.md point to it.
- The pytest runs pass, the code-review skill has run with this ticket as its spec, and its
  drift items are closed.

## Answer

Built 2026-10-21 on branch `code-audit/scan`. See `docs/code-audit.md`. Nothing malicious was
found.

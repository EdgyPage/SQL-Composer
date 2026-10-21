# Scan for malicious code

Type: task
Status: resolved
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

### Reviews

- Spec (2026-10-21):
  - `--root` now runs the offline policy too, so a planted `pickle` exits 1.
  - `atexit`, `sys.addaudithook`, `settrace` and `setprofile` are a new kind, hook, and system
    and startup paths are found.
  - A workflow with no `permissions:` is found, and so is `-p` anywhere in `pyproject.toml`.
  - The test file's reviewed entry is narrowed to its string samples.
  - Answered in the report's "What the lasting checks leave out": relative links, `exec_module`,
    hook files git may not track, and line-level config reads. Its "How the sweeps were run"
    gives the commands.
  - The hook's "checkout without the policy" line led to a second bypass, now closed and
    tested: a worktree that deleted its policy passed every edit.
- Standards (2026-10-21):
  - The docstring matches `main`, which now uses a plain `if`.
  - `auth` is gone from the secret names (it matched `AUTHOR`).
  - The audit reuses the policy's folder skip, now public as `offline_policy.not_read`.
  - `audit` and `stale` share `everything_found`; `files` is `read_files`; "rules" is "what it
    looks for"; the hook's docstring is re-wrapped.
  - Answered: `(kind, what)` pairs and kind strings stay plain, as the policy's `Finding.kind`
    is; `config_findings` picks by file name as the policy picks by suffix; `dill`,
    `cloudpickle` and the credential stores are listed because a planted file would bring them,
    not the repo.

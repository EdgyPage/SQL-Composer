# Retire v1 from `dev` and carry over the salvage

Type: task
Status: claimed
Blocked by: 13

## Question

Clear the v1 first draft out of `dev` so the Toolbox core can be built on an empty floor, without
losing what the map's Notes list as salvage.

- **Remove:** `sqlcomposer/`, `declarations/`, `tools/`, `docs/design/`, `docs/lineage/`, the v1
  tests and v1's `README.md`. Also remove whatever of `pyproject.toml` and `requirements.txt` the
  `dev` setup decided in "What does `dev` enforce, and which maintainer agents does it carry?"
  replaces.
- **Keep:** `docs/adr/0001-sqlglot-over-sqlalchemy.md`, `CONTEXT.md`, `docs/agents/`, and the
  escaping test matrix (`tests/test_escaping.py`). Keep the matrix as cases for the Toolbox's tests
  to adopt, not as code that imports v1.
- **Record:** which files went, where the salvage now lives, and which checks from the
  `dev`-enforcement ticket are in place, so that "Build the Toolbox core" starts from a known
  state.

`main` is not touched. It keeps v1 until the export script exists.

## Comments

**From "What does `dev` enforce, and which maintainer agents does it carry?" (2026-09-25).** This
ticket sets up everything `dev` enforces that doesn't need the Toolbox:

- **Development files:** replace `pyproject.toml` with pytest and ruff settings only (no
  packaging section, ruff `target-version = "py311"`, C901 at most 10), and replace
  `requirements.txt` with `requirements-dev.txt` pinning sqlglot 30.19.0, pandas, numpy, pytest
  and ruff. networkx and duckdb go.
- **`.gitignore`:** add `.claude/worktrees/` and `.claude/settings.local.json`.
- **CI:** a GitHub Actions workflow on `dev` that runs `pytest` twice on Python 3.11, once with
  sqlglot 25.24.2 and once with 30.19.0.
- **Hooks,** in a tracked `.claude/settings.json`:
  - one that refuses commits and edits while `main` is checked out, unless the export script is
    running;
  - the drift reviewer, which runs after a commit touching `sql_composer/`, the README template,
    `CONTEXT.md`, `CLAUDE.md`, `docs/` or `requirements-dev.txt`, and records findings in
    `.scratch/drift.md`;
  - one that won't let a session end while an item it opened is still open.

  Start with an empty `.scratch/drift.md`. The six kinds of drift and the `No-drift:` waiver are
  in that ticket's answer.
- **Agents and docs:**
  - `docs/agents/standards.md`, holding only what no test can enforce, for the `code-review`
    skill;
  - `.claude/agents/beginner-reader.md`, which only advises;
  - the new `CLAUDE.md`, with the definition of done.
- **The pointer test:** every file path named in `CLAUDE.md`, `docs/agents/` and the README
  template exists.

**Progress (2026-09-25), not yet resolved.**

Done and committed on `dev`:

- `pyproject.toml` holds only pytest and ruff settings; `requirements-dev.txt` pins sqlglot
  30.19.0, pandas, numpy, pytest and ruff; `.gitignore` ignores `.claude/worktrees/` and
  `.claude/settings.local.json`.
- CI: `.github/workflows/dev.yml` runs `pytest` on Python 3.11 with sqlglot 25.24.2 and 30.19.0.
- The escaping matrix is salvaged as plain cases in `tests/escaping_cases.py` (no v1 import),
  and `tests/test_escaping_cases.py` checks them against sqlglot alone (49 tests). The cases
  that are about the Toolbox's own code (sneaky numbers, non-finite numbers, one place that
  generates SQL) are kept as cases and notes for the core build to adopt.
- `docs/agents/standards.md`, `.claude/agents/beginner-reader.md`, `tests/test_pointers.py`
  and an empty `.scratch/drift.md`.

Waiting on the user, because the agent's auto mode refused them:

- **Removing v1** (`sqlcomposer/`, `declarations/`, `tools/`, `docs/design/`, `docs/lineage/`,
  the v1 tests, `README.md`, `requirements.txt`): refused as local destruction.
- **The drift-review and session-end hooks**, and so `.claude/settings.json`: refused as the
  agent modifying its own controls. `.claude/hooks/protect_main.py` and
  `.claude/hooks/drift_list.py` are written but uncommitted; `drift_review.py`, `drift_stop.py`,
  the reviewer's brief and `settings.json` are not written.
- **The new `CLAUDE.md`** is written but uncommitted, since it describes the hooks as in place.

The hook design, for whoever finishes it:

- **Protecting `main`:** PreToolUse on `Edit|Write|NotebookEdit` and on `Bash|PowerShell` with
  `if: "Bash(git *)"` / `"PowerShell(git *)"`; denies a file edit in a checkout of `main`, and a
  commit-making git command there (or one that switches to `main` and commits); a command running
  `tools/export_clean.py` always passes.
- **Drift reviewer:** PostToolUse after `git *`. If the new commit touches the watched paths, or
  carries `No-drift:`, it records `<commit> <session id>` in a file inside `.git` and adds
  context telling the session to start a subagent on the reviewer's brief. The review happens in
  that subagent, so `.claude/agents/` keeps only the beginner reader. The reviewer appends item
  lines (`- [ ] D3 | <commit> | <kind> | <finding>`) and one "Reviewed commits" line to
  `.scratch/drift.md`.
- **Session end:** a Stop hook blocks once while this session's requested reviews are unrun or
  its items are open. It lets a second stop through (`stop_hook_active`) so the session can ask
  the user, for example whether to raise the Toolbox version.

For "Build the Clean-branch export": the README template's path joins the drift reviewer's
watched paths and the pointer test's `STANDING_DOCS`.

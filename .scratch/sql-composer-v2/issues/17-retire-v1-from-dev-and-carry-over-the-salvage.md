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

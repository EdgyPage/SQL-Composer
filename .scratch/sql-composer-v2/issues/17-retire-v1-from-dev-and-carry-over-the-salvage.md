# Retire v1 from `dev` and carry over the salvage

Type: task
Status: open
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

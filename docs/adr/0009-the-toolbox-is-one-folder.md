# The Toolbox is one folder, sqlglot_composer

Status: accepted; supersedes ADR 0003

ADR 0003 split the Toolbox into `composer_core/`, every file both Editions ran, written once, and
an Edition's folder holding only what was its own: `writing.py`, `engine.py` and its pages. The
split existed so two Editions could share one core. ADR 0008 dropped Spark Composer, so in 6.0
the core's files move into `sqlglot_composer/`, and a user copies one folder, as the user asked
(2026-10-20).

What went with the split:

- `composer_core/edition.py`, the seam the core reached the plugged-in Edition's writing and
  engine through. The core's files now import `writing.py` and `engine.py` directly: nothing
  `writing.py` imports (`refusals.py`, `trees.py`) imports it back, so the package loads in one
  order, `checks`, `engine`, `writing`, then the rest.
- The import self-check of a second folder: `check_together`, the stops for a missing or wrong
  `composer_core`, and the second-Edition refusal. The one folder still stops on a file from
  another version, export or Toolbox folder, such as an old `composer_core` file pasted in.
- `tools/editions.py`, the registry of two folders and their Editions. `tools/toolbox_registry.py`
  keeps what is left: the folder's name, its files and pages, and what each file may import.
- `CHANGES.md` moves out of the Toolbox's folder to the repo's top, and ships at `main`'s top
  beside the README.
- On `main`, the Example projects and the Templates sit at the paths dev has them, not one folder
  deeper per Edition, so a project's `PYTHONPATH=../..` holds on both branches.

## Considered options

- **Keep `composer_core/` and copy it with `sqlglot_composer/`.** Rejected: with one Edition the
  split protects nothing, and every update and every import stop had a second folder to explain.
- **Keep `edition.py` as a seam.** Rejected: it only chose an Edition; direct imports are plainer
  and the import order holds without it.

# One folder, version 6.0

Type: task
Status: open
Blocked by: 02
Size: L

## Question

Map Notes, "Spark and the one Toolbox". Move every `composer_core/` file into
`sqlglot_composer/` (imports become relative within the one package; `edition.py`'s indirection
folds into its callers where it only chose an Edition). Remove `tools/editions.py` and what
reads it, the name swap, and the tests that held two Editions alike. Raise `TOOLBOX_VERSION` to
`6.0` in every file, start CHANGES.md's `## 6.0`, and ship CHANGES.md at main's top. Update
CLAUDE.md (one pytest run, two CI jobs, no Editions section, the toolbox-6 map), CONTEXT.md
(drop Edition and Composer core; Toolbox is one folder; Clean branch and Toolbox version
reworded), and `.claude/hooks/drift-reviewer.md` (no parity kind). Write the ADR that supersedes
0003.

## Done when

- `from sqlglot_composer import *` works from a Project holding only `sqlglot_composer/`.
- The export builds main from the one folder.
- The pytest runs pass, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).

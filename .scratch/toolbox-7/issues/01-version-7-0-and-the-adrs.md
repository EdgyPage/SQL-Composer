# Version 7.0 and the ADRs

Type: task
Status: open
Blocked by: -
Size: S

## Question

The user (2026-10-21) named the version: "v7". Two decisions grilled that day are hard to
reverse and would surprise a reader of the 6.x code, and were drafted with the map:
`docs/adr/0011-tables-have-no-days.md` and `docs/adr/0012-query-and-execute.md`.

## Done when

- `TOOLBOX_VERSION` is `"7.0"` in every file of `sqlglot_composer/`, the `__init__.py` doctest
  shows it, and everything that names the current version says 7.0, as ticket 01 of 6.1 lists
  (CONTEXT.md's Toolbox version, the clean-branch README, the tools' docstrings and pages, the
  Example projects' lineage footers, regenerated with `tools/example_project.py`).
- CHANGES.md has a `## 7.0`, a major version as `## 6.0` is: a "To update from 6.x" part, which
  the later tickets fill, and nothing yet under it but what this ticket changes.
- ADRs 0011 and 0012 are committed as drafted, or as the review leaves them. ADR 0004's Status
  says it is amended by 0012; ADR 0005's and 0007's say which parts 0011 supersedes.
- The pytest run passes, the code-review skill has run with this ticket as its spec, and its
  drift items are closed (CLAUDE.md's Definition of done). Nothing a beginner sees changes but
  the version, so no beginner read.

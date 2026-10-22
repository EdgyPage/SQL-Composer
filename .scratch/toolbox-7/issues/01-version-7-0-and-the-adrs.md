# Version 7.0 and the ADRs

Type: task
Status: resolved
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

## Answer

Built 2026-10-21 on dev (011d947).

- `TOOLBOX_VERSION = "7.0"` in every file of the folder and in `__init__.py`'s doctest;
  CONTEXT.md's Toolbox version says `7.0`. The gallery, the how-to page and both Example
  projects are regenerated: only the version changed in them. Example stamps naming an older
  version (`checks.py`, `tools/export_clean.py`, the README's `5.1` and "From 4.x to 6.0") stay,
  as 6.1 left them; ticket 07 rewrites the README.
- CHANGES.md `## 7.0`: a "To update from 6.x" part, holding only the copy-and-restart step,
  which tickets 02 to 08 fill.
- ADRs 0011 and 0012 committed with the map (b064afe; D222's fix, 69369ef). ADR 0004's Status
  says it is amended by 0012; 0005's and 0007's say which parts 0011 supersedes.

## Reviews

- Standards (2026-10-21): no breach. Answered: the `## 7.0` intro promises changes the later
  tickets add, as the map plans, and 7.0 isn't exported before they land; the glossary's Key and
  Date partition are ticket 03's, which holds their words; the per-file `TOOLBOX_VERSION` is the
  repo's own design.
- Spec (2026-10-21): nothing missing or wrong. Answered: the copy-and-restart bullet stays,
  since every 7.0 update starts with it; the README's "From 4.x to 6.0" example is ticket 07's.
- Drift: 011d947 clean.

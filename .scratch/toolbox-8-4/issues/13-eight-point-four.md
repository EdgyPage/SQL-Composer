# 8.4: the Upgrade step and the raise

Type: task
Status: open
Blocked by: 12, 14
Size: M

## Question

The user named 8.4 (2026-11-05). Every raise ships an Upgrade step and freezes the Example
projects as the version before left them.

## Done when

- `sqlglot_composer/version.txt` says 8.4, and `upgrades.py`'s `to_8_4` writes the Workflow
  notebooks again where 8.4 changed them, keeping each name given and each cell written in,
  as `to_8_3` does. Text answers in `TAGS` stay as they are: nothing is converted again.
- `tests/upgrade_from/8.3/` freezes both Example projects as 8.3 left them, without Lineage
  pages; `tests/test_upgrades.py` passes, 11's chain test among it.
- CHANGES.md's `## 8.4` is complete, with "To update from 8.3"; CLAUDE.md names 8.4. CI's job
  passes; the export is the user's call.

## Answer
Built 2026-11-05.

- **The raise**: `sqlglot_composer/version.txt` says "sqlglot Composer 8.4", the version the
  user named; `TOOLBOX_VERSION`'s example, `project.upgrade()`'s, how-to 28's outputs, the
  Copilot files, the Example projects' `admin/project_version.txt` and their Lineage pages are
  written again with it.
- **The Upgrade step**, `upgrades.to_8_4`, in `STEPS`:
  - each Workflow notebook written again, each name given and each step cell written in kept,
    for the `project.check()` cell under each decision step (14) and the decisions cell's
    text;
  - in each table 8.3 converted, each Script tag in a string, `TAGS["NAME"]` itself, written
    `tag_text(TAGS["NAME"])`, or with `quoted=False` for a tag the Table reference's TAGS says
    stood bare, tag_text imported, the notebook kept as it was in `admin/removed/`: the same
    Hive for every answer 8.3 took, and a Run value's function may answer it now;
  - a seed() 8.3 wrote stays as it was, copying every Partition: CHANGES says to convert again
    to limit it.
- **Found and fixed on the way**: writing a Workflow notebook again lost what an earlier step
  had marked on its first lines (8.3's mark of a tagged batch, at the top of the convert
  notebook) and the decisions cell you answered in; `_workflow_cells_with_yours` now keeps
  both (`_marks_on_top`, `_decisions_cell_answered`).
- **The frozen copy**: `tests/upgrade_from/8.3/` holds both Example projects as dev 2cf593e,
  which 8.3 was exported from, left them, without Lineage pages. The chain test (11) now runs
  from 8.3 by itself, straight to 8.4.
- **CHANGES.md's `## 8.4`**: "To update from 8.3" says the Upgrade writes the Workflow
  notebooks again with the check cells, writes an 8.3 table's tags in strings through
  tag_text, and leaves its seed copying everything.
- **Tests**: `test_8_4_reads_a_tag_8_3_wrote_in_a_string_through_tag_text`; the 7.1 Upgrade
  test names 8.3's step and 8.4's.
- D422, the version item, closes with this commit. CI and the export are the user's: `main`
  and the push stay theirs.
- **A seed() 8.3 wrote is marked** (`_mark_a_seed_copying_everything`): it copies every
  Partition as `unchecked_hive(...)`, so the mark says to convert the batch again, as a new one
  with RENAME, for one SEED limits. The upgrade journeys hold it: their Project, as 8.3 left
  it, has such a table, and the Workflow's mark step answers the mark.

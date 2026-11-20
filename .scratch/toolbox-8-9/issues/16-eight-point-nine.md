# 8.9: the Upgrade step and the raise

Type: task
Status: resolved
Blocked by: 01, 02, 03, 04, 05, 06, 07, 08, 09, 11, 12, 13, 15, 17
Size: S

## Question

The version the user named, and the Upgrade step every raise ships (round 4, Q5).

## Done when

- **`upgrades.to_8_9`, in `STEPS`**, with nothing to change in a Project; it touches nothing
  under `scheduled_runs/<name>/`, which
  `test_an_upgrade_keeps_every_scheduled_run_file_at_its_path` holds.
- **The Example projects are frozen at 8.8** in `tests/upgrade_from/8.8/`, without their
  Lineage pages, and `tests/test_upgrades.py` passes.
- `sqlglot_composer/version.txt` reads 8.9.
- **CHANGES.md's `## 8.9`** has "What's new" and "To update from 8.8".

## Answer

Built 2026-11-19, from dev's 1c8a39d6 (tickets 01 to 13 and 17), beside tickets 14 and 15.

- **The user's OK:** "you have my ok for ticket 16 now" (2026-11-19, in chat), for the raise
  to 8.9.
- **`upgrades.to_8_9`, in `STEPS`:**
  - writes the convert Workflow's notebook, `admin/workflows/convert/convert.ipynb`, again
    (`_write_one_workflow_notebook_again(upgrade, "convert")`): ticket 07's `FILES` naming a
    workbook and step 1's goal, each name given, each step cell written in and an answered
    decisions cell kept, the notebook as it was in `admin/removed/`, the checklist's "rewrote
    ..." line. It isn't a file a record of promote or convert names, so no record is rehashed.
  - No Template and no other admin or Workflow notebook changed since 63050726: the Example
    projects at 1c8a39d6 differ from 63050726's in the two convert notebooks alone, and
    `project_templates.py` and `notebooks.py` are as they were; tickets 08 and 09 changed none.
    So nothing is marked, and nothing of the user's is lost.
  - Last, the Lineage state recorded as the Upgrade's (`_record_the_lineage_state`, 8.8's
    `_record_the_first_lineage_state` renamed, its `RECORDED_BY_8_8` now
    `RECORDED_BY = "project.upgrade() to {version}"`): each change it finds, such as a column
    whose `VAR_SAMP` 8.9 writes differently, marked `toolbox` (ADR 0015). It needs no
    connection and sends nothing.
  - Nothing under `scheduled_runs/<name>/` is touched; nothing is sent.
- **The freeze:** `tests/upgrade_from/8.8/`, the Example projects at 63050726 (8.8, the last
  commit before the 8.9 plan), 118 files, without their Lineage pages: each `lineage/` folder's
  `.html` and `.md` taken out, the Lineage difference's too; `admin/lineage/lineage_state.csv`
  kept, as it is the state an 8.8 Project holds, which 8.9's recording adds to.
- **`tests/test_upgrades.py`:** `AWAITING_ITS_STEP` empty; the 7.1 test names 8.8's step; the
  8.8 recording's test reads `RECORDED_BY`; three new tests: the convert notebook written again
  with a name given kept and the old one archived, the recording marking a change `toolbox`,
  and an 8.8 Project changed in nothing but its convert notebook (and its version).
- **The raise:** `version.txt` reads 8.9; CHANGES.md's `## 8.9` ("To update from 8.8": copy
  the folder in, restart the kernel, run `project.upgrade()`; and "What's new": a workbook
  converted in code or through Copilot files 15, 11, 12, 20, 21 and 22, a pivot one table at
  its finest grain with its totals named in the checklist (the user, 2026-11-19), the Pivot
  filter Decision, the Workbook check, lean Hive in the docs, `VAR_SAMP` and `VAR_POP` written
  right); how-to 28 upgrades to 8.9, its ten steps; the docstrings of `TOOLBOX_VERSION` and
  `project.upgrade()` show 8.9; the Example projects, the pages in `docs/main/` and the Copilot
  files written again at 8.9; `tests/snapshot/known.txt` knows the new texts, with the
  `var_samp` and `var_pop` texts bd788cff left out.
- **The upgrade journey** (`tests/journeys/test_workflow_journeys.py`) starts from the newest
  version whose Upgrade leaves a mark, as its step 2 makes each one: 8.9's marks nothing
  (`MARKS_NOTHING`), so it starts from 8.7, as it did at 8.8.
- **Left for the merge:** the README's Update has no "If your Project was at 8.8" line yet
  (`docs/clean-branch-readme.md` is ticket 15's); `known.txt` still holds the 8.8 texts no
  test makes now, which a whole-suite run with `SNAPSHOT_WRITE=1` takes out.

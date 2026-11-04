# 8.3: the Upgrade step and the raise

Type: task
Status: resolved
Blocked by: 07
Size: M

## Question

The user named 8.3 (2026-11-04, Q16). Every raise ships an Upgrade step and freezes the Example
projects as the version before left them.

## Done when

- `sqlglot_composer/version.txt` says 8.3, and `upgrades.py`'s `to_8_3` gives a Project's
  convert notebook its `PARTITION` input and step 7's new cell, keeping each name the user gave
  and each cell they wrote in, as `to_8_1` does.
- A table converted before 8.3 is left as it is (Q25): CHANGES.md's "To update from 8.2" says
  to convert a batch whose scripts hold Script tags again under a new name.
- `tests/upgrade_from/8.2/` freezes both Example projects as 8.2 left them, without Lineage
  pages; `tests/test_upgrades.py` passes.
- CHANGES.md's `## 8.3` is complete; CLAUDE.md names 8.3. CI's two jobs pass; the export is
  the user's call.

## Answer
Built 2026-11-04.

- **The raise**: `sqlglot_composer/version.txt` says "sqlglot Composer 8.3", the version the
  user named; the Copilot files, the Example projects' `admin/project_version.txt` and their
  Lineage pages are written again with it.
- **The Upgrade step**, `upgrades.to_8_3`, in `STEPS`: each Workflow notebook written again
  through `_write_workflow_notebooks_again`, as 8.1's and 8.2's do, each name given and each
  step cell written in kept, so the convert notebook gains PARTITION, step 7's cell passing
  it, and step 2's and the decisions cell's new text. A table converted before 8.3 is left as
  it is (Q25).
- **CHANGES.md**: `## 8.3` opens with what 8.3 is, then "To update from 8.2": copy in the
  folder and run `project.upgrade()`; the Workflow notebooks written again; a batch converted
  before 8.3 whose scripts hold Script tags converted again under a new name, the old copy
  removed once the new one's compare passes (a bare tag's table an Unchecked statement, a
  quoted one's writing the tag as text, as 07's drift review noted).
- **The frozen copy**: `tests/upgrade_from/8.2/` holds both Example projects as dev 1db77d4,
  which 8.2 was exported from, left them, without Lineage pages; `GAINED_BY_HAND` is empty, as
  8.3's Example projects gained nothing by hand, and `notebooks_and_hive`, which only filled
  it, is gone. `tests/test_upgrades.py` passes, the 7.1 Upgrade naming 8.2's step and 8.3's.
- **CLAUDE.md** names 8.3, its map's line since the charting. The export and CI are the
  user's: `main` and the push stay theirs. D409 closes with this commit.
- **The Copilot evaluation**, which 8.2's raise recorded for each Copilot file it changed, no
  test asks for; files 07 and 13 changed (07), and their held-out evaluation is the user's to
  run, as docs/copilot-eval.md says.
- **Code review** (review-spec, with standards, on sonnet). Fixed: how-to 28 hard-coded 8.2,
  so after the raise its example upgraded nothing: it starts from 8.3 and lists four steps,
  8.3's among them; `TOOLBOX_VERSION`'s and `project.upgrade()`'s docstring examples say 8.3;
  the 7.1 Upgrade test names 8.2's and 8.3's steps; the upgrade journeys' fixture gains a
  tagged batch, as 8.3's step marks one where 8.2's marked a changed Template.
- **Beginner reader**: [its report](../reports/08-beginner-reader.md). The costliest: a batch
  converted again makes the same dev table, and the Upgrade said nothing was left to do. So
  `to_8_3` now marks each batch whose kept scripts hold `<PARM`, at the top of the convert
  notebook, listed in admin/upgrade_8.3.md, saying to convert them again with a new name for
  each table in RENAME and to remove the old table once the new one's compare passes;
  CHANGES' To update says the same, with the step 7 cell and step 3's refusal. Tests: a
  tagged batch is marked; an 8.2 Project with none has nothing for you to do.

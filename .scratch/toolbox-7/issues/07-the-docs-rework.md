# The docs rework

Type: task
Status: open
Blocked by: 06
Size: XL

## Question

The user (2026-10-21): "Most importantly, we need to rework the howto and example sections
alongside making stronger templates ... the guide appeared a bit internally inconsistent with no
flow to it." They "did not get too far in to the very long guide", couldn't find how to select a
column from a Table, and had to read the code for what `send` expected. The map's "The docs"
holds what they chose.

What exists (2026-10-21), from the audit that day:
- The README has 8 steps. There are 21 Getting started how-tos and 19 Intermediate ones, and
  the steps never link how-tos 8, 9, 18 or 20.
- Only how-tos 1, 2, 3, 11, 16, 17 and 26 work inside a Project. The rest build `Table(...)`
  inline, with "at work, keep this in a file".
- The same table is made two ways (11, then 12 and 13), and `mart.job_day` has different
  columns in 3, 25 and 26.
- How-tos 11, 16 and 17 edit files with `Path.write_text`.
- README step 6 names `admin.drop_days` before the admin module is taught. Step 8 says "Level"
  before Levels are taught.
- How-to numbers are hard-coded at README:179, `project.py:94` and `lineage.py:370`.
- These tests pin the current shape:
  - `how_to_page.GROUPS` (1–21 and 22–40)
  - `tests/repo/test_export_clean.py:380`
  - `tests/repo/test_readme_shape.py`
  - `tests/test_how_tos.py`
  - `tests/test_project_templates.py:195`

This ticket may split in two when it is claimed: the README and the Getting started how-tos,
then the Intermediate how-tos.

## Done when

- **The file map**: README step 2 has a table of every file of a Project. Each row gives its
  path, the Project action that makes it, and what the user fills in. The only rows made by
  hand are the Project folder and the copied `sqlglot_composer` folder. Both Example projects'
  READMEs show the same map, filled in.
- **The chain of types**:
  - README step 3 and the top of the how-to page show Table, Column, Condition, Clause,
    Statement, the Hive `str` and the DataFrame, each with the call that makes the next:
    `ops.jobs`, `ops.jobs.job_id`, `equals(...)`, `SELECT(...)` and the others,
    `statement(...)`, `to_hive(...)`, and `run(..., query=query)`.
  - Every how-to labels the type of each value its steps make, in the type hints' names.
- **One story**:
  - README step N is Getting started how-to N, the same in title, order and number.
  - Each one goes on from the Starter Example project as the step before left it.
  - Every how-to works inside a Project. No inline `Table(...)` is followed by "keep this in a
    file".
  - Nothing is used before a how-to has taught it.
  - Intermediate how-tos are a menu, each starting from the Intermediate Example project and
    saying which Getting started how-tos it needs.
- **About 25 how-tos**, one way to do each job. These merge:
  - 1 and 4
  - 10 to 13
  - 13 and 26
  - 14 to 16
  - 2 and 3, with describing a table by hand made Intermediate
  - the day how-tos (12, 13, 22 to 25), into "Rewrite some partitions"

  Every how-to uses `query` and `execute`, the partitions of 03, Databases, `new_block` and
  `check_references`. "Hand-written Hive with your Table references" shows the f-string of 05.
- **Edits**: a step that edits a file shows the file as it is after the edit, under a heading
  naming its path. The how-to test applies the edit out of sight. No `Path.write_text` and no
  notebook JSON on the page.
- **Links by name**: no prose, docstring or message names a how-to by its number.
  `how_to_page.GROUPS` and the tests that pin the shape follow the new list.
- **Docstrings**: every public name's docstring opens with an example call. A refusal of a wrong
  argument names the arguments its function takes.
- **The README** links the Example gallery. Its group blurbs match the how-to page's. Its
  Templates part names only the Templates there are.
- CLAUDE.md's Definition of done. The beginner reader runs on the README, every Getting started
  how-to and the Starter Example project, read in order as one story. Its report is linked from
  this ticket.

## Inputs from the reviews of 03 to 08 (2026-10-21)

- Starter project: one Table notebook is the saved_table Template filled in and nothing else,
  and the others use READS as the Template does (none uses a DAY the Template hasn't); a
  filled-in notebook and its Table reference shown side by side; what to give `<LOCATION>`.
- Show `from references import ops` in use: a Statement and an f-string with
  `ops.job_runs.status`; say when the per-file import is needed (Aliases).
- Show a Guard, a Warning and the Load limit on ops.region_budgets and ops.team_notes.
- How-tos 10 and 12: a Key names a row of the table, not of a day; the partition column goes
  anywhere in SELECT, the Toolbox puts it last; the days wording throughout.
- How-to 26 and others: no "each write is a function of the day it writes".
- How-to 41 / a Python step in a Table notebook: show the notebook (write() giving the step,
  the cell that pulls, changes and saves), and that tables written after it read what it held.
- The README's description of the intermediate project.


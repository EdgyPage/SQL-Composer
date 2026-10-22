# The docs rework

Type: task
Status: resolved
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

## Answer

Built 2026-10-22 on dev (45a687f; review fixes c748de7 and the polish after it), by parallel
helpers: the how-to machinery first, then four writers, a docstring pass and the README.

- 26 how-tos where there were 41. Getting started 1-8 are the README's eight steps, same
  titles and order, one story through the Starter Example project (each opens with where the
  last left the Project); Intermediate 9-26 are a menu, each starting from the Intermediate
  Example project and naming the Getting started how-tos it needs. Groups come from each
  how-to's `For:` line; numbering is checked to be 1..n with Getting started first.
- The file map is in README step 1, Start a Project, beside how-to 1's list (the ticket said
  step 2, written when step 2 was Start a Project): every file, the Project action that makes it,
  what you fill in. By hand: the Project folder, the copied sqlglot_composer, and the notebook you
  run start() from (three, not two: the notebook is real).
- The chain of types in README step 3 and atop the how-to page; every how-to labels each value's
  type in the hints' public names (`# -> Statement`; `# -> the notebook's functions` for
  project.load, whose class isn't public).
- File blocks: "The file `p`, after you ...:" is written by the tool and the test at that point;
  "The file `p`, as project.new_table wrote it:" is checked against the file. No
  Path.write_text or notebook JSON on a page. The tool imports a Project's own modules as a
  notebook in its folder does (project_on_the_path) and clears Python's import caches after
  writing a file.
- Links by name only; every public docstring opens with an example call (116 names); a
  refusal of an argument the Toolbox catches lists the arguments, read from the signature
  (elsewhere Python's TypeError names the unexpected one, as CHANGES says).
- Also carried here: ticket 06's beginner fixes, with project.start() run again completing a
  Project (writing over nothing, leaving a 6.x send.py for check() to report).

## Reviews

- Spec (2026-10-22): the file map's step (answered above); three things by hand (answered);
  how-to 10's slug against its title (file renamed 10_latest_row_of_each_group.py); the
  narrower refusal rule (CHANGES says what the code does).
- Standards (2026-10-22): the send= refusal for a function taking neither call ("Pass 
  instead": now "Leave send= out", drift D242); a bare dict hint; non-public names in type
  labels (relabelled); a patched Toolbox function in the Example project tool (now mock.patch,
  restored).
- Beginner reader (2026-10-22): the four complaints answered (selecting a column, what query
  and execute are; files from Project actions; the story mostly carrying through). Costliest
  stops fixed: query changing name from how-to 5 on, the Starter project's differences unsaid,
  the Template never shown before it is filled, when a Saved table joins `from references import
  mart`, type labels. A second read confirmed those six, and its remaining stops (Lineage file
  names and folders, the notebook's first cell in how-to 1, the Table reference as written)
  went into a final polish.
- Drift: 45a687f opened D241-D245, closed by c748de7.


# The docs

Type: task
Status: resolved
Blocked by: 08, 09, 12, 17
Size: M

## Question

Where a person reads about converting a workbook (round 4, Q3).

## Done when

- **An Intermediate how-to, "Convert an Excel workbook"**, run on the Example database, its
  workbook from ticket 02's tool: a Table with formulas, a query, and a pivot with a slicer
  reading them; the Pivot filter Decision answered; the Workbook check's report.
- **The intermediate Example project** gains that batch; the Example projects page shows it.
- **The README's Excel steps** and **the Workflows overview** show both ways into convert.
- **The beginner reader** runs on all of it, and its report is linked here.

## Answer

Built 2026-11-19 on dev's d43fa9a5. No Toolbox code changed: `sqlglot_composer/` and `copilot/`
are untouched.

**The workbook.** One workbook serves the how-to and the Example project: `job_hours.xlsx`,
built by `tools/example_project.py`'s `job_hours_workbook()` with `tools/formula_workbook.py`
and `tools/pivot_tables.py`, its times pinned (`pinned_workbook`) so it is the same bytes on
every computer. It holds a Table, job_events, of ops.job_events' rows with a formula column,
`hours = [@minutes]/60`; a Table, job_owners; a Power Query, run_hours, on its Power Query
sheet, keeping each finish event and joining job_owners on job_id and dt for the team; and a
PivotTable over run_hours on sheet Teams, keeping Excel's default name PivotTable1, the Sum of
hours by job_id, with a slicer on team keeping data and its Grand Total off. It samples the
intermediate Example project's own tables. A first build sampled ops.job_runs and ops.jobs, with
a site slicer, but that put two Table references into the intermediate project that how-tos 12,
22, 24 and 27 add themselves, so the team stands where the sites stood in the which-to-pick line
("to tab through each team ... "fold" keeps every team"). Job 3 moving from data to finance on
2026-09-18 shows what "fold" keeps.

**1. How-to 33, "Convert an Excel workbook"**
(`worked_examples/how_to/33_convert_an_excel_workbook.py`, Intermediate), run on the Example
database. Its steps:

1. Start from the Starter Example project: the Intermediate one holds this batch finished.
2. Add the Table references of ops.job_events and ops.job_owners, each proposed Key accepted,
   so the join convert checks has its Keys.
3. Save the workbook: `example_workbook("job_hours.xlsx")`, a name the page gives the steps as
   it gives `example_project` (`tools/how_to_page.py`, `given_names`), copying the Intermediate
   Example project's workbook. What the workbook holds is told in prose.
4. Convert it: `project.convert("job_hours", files=["job_hours.xlsx"], query=query,
   database="ops")`, its report printed up to "Next:".
5. Read the Hive kept in scripts/ (the formula, the query and the pivot, the slicer marked
   `/* Pivot filter: slicer team */`) and the Workbook check, from batch.md: every cell matches,
   2 cells compared.
6. Read the open Decisions: check()'s three lines (location, name, pivot_filters) and the
   checklist's Pivot filter note, with its "Which to pick".
7. Answer them: `"location"`, `"name": "job_hours"` and `"pivot_filters": {"team": "fold"}`,
   each answer explained, "fold" as the which-to-pick line says for tabbing through each team.
8. Write them in: the rename to mart.job_hours, and the logic written again for "fold".
9. See the table now: its Hive and preview(), a row for each job and team.
10. Create, write and compare it in dev (the compare can't read a dev table here, as in how-to
    09).
11. Or have Copilot write the Hive, shown and not run: `python copilot/workbook_text.py`; files
    15, 11, 12 and 20 attached with the .txt; the reply's `-- Pivot filter: slicer team`; the
    query saved as job_hours.hql and converted into the same batch beside the workbook,
    `files=["job_hours.xlsx", "job_hours.hql"]`; the Workbook check then checks Copilot's Hive.
    I ran this path in a scratch test after step 8: the .hql stands for the final, the answers
    are kept (fresh copies written), and the check says "job_hours.hql, Copilot's Hive of
    PivotTable "PivotTable1": every cell matches the workbook".

When you'd use it names Copilot file 21 for growing the table later. Common mistakes: a formula
outside a Table, "tables" for a field of many values, changing the workbook after converting,
and a Copilot .hql named for nothing.

**Why location is answered, not placed: a Toolbox bug, for the lead.** The how-to and the
Example project answer `"location"` because of a bug in `sqlglot_composer/`, so not fixed here.
With DEV's `location_root` filled in, a converted table's location is placed as
`<root>/mart.db/teams_pivot`, and the NAME answer's rename keeps that folder, so mart.job_hours
would live in `.../teams_pivot`. Worse, in one kernel, where check() or convert loaded
mart.teams_pivot before the rename, loading mart.job_hours is refused: "Table('mart.job_hours')
would be at /data/dev/mart.db/teams_pivot, the same folder as mart.teams_pivot", as
`tables._FOLDERS` still holds the old table. The convert notebook's "Run up to your Decisions"
then "Run the rest", in one kernel, hits it. A rename should place a placed location again under
the new name.

**2. The intermediate Example project gains the batch** (`tools/example_project.py`'s
`WORKBOOK_CONVERSIONS` and `_add_workbook_conversions`). The workbook is saved beside the
convert notebook, converted, and answered as the how-to answers it. Its proposed Key,
`["job_id", "team"]`, is accepted, its `# CONVERSION:` marks deleted and its two TODO lines
filled in (its docstring's Why and how, `CONVERTED_HOW`). It is then compared (`_same_rows` now
takes no original), which finishes it in `admin/workflows/convert/finished/job_hours/`.

- New files: the workbook; the finished batch (batch.md with the Workbook check,
  `scripts/job_hours.hql`, renamed with the table, written.json); `tables/mart__job_hours/`;
  `references/mart__job_hours.py`; and `admin/removed/`, where the rename moved
  mart.teams_pivot's files.
- Its README (`tools/example_project_sources/intermediate/README.md`) gives the batch a
  paragraph and five rows of the file map.
- `tools/example_projects_page.py` shows a `.xlsx` as `copilot/workbook_text.py`'s text,
  folded, and `docs/main/example_projects.html` is written again.
- `tests/test_example_projects.py` compares a workbook byte for byte
  (`example_project.BINARY_SUFFIXES`, which `_tidy` leaves alone).
- `tests/test_upgrades.py`: `AWAITING_ITS_STEP` lists the batch's files, the registry, mart.py,
  the Reference sheet and the README, for ticket 16 to move into `GAINED_BY_HAND["8.9"]` for
  the intermediate. `hive_files` keeps to the Table folders the frozen 8.1 copy has.

**3. The README template and the Workflows overview.**

- `docs/clean-branch-readme.md`: the Excel steps give both ways in. Step 1 fills in the
  workbook; step 2 converts the workbook itself (FILES, the Workbook check); steps 3 to 6 are
  the Copilot path (files 15, 11, 12, and 20 for a PivotTable; the .hql saved beside the
  workbook in one batch stands for its final); step 7 answers the Decisions, with the four Pivot
  filter answers. A closing paragraph names file 21 for growing a converted pivot. The Copilot
  section names 15, 11, 12, 20 and 21, and the Intermediate how-tos' line (with
  `tools/how_to_page.py`'s Group text, which a test holds to it) and the intermediate Example
  project's line name the workbook.
- `tools/workflow_graph.py`'s `EXCEL_FLOW` (the README's excel chart and steps, and the
  overview's Excel steps) draws both ways, the Workbook check and the Decisions.
- `tools/workflows_page.py`: the Excel box says "a workbook, in code or by Copilot" and links
  how-to 33. Its hand-off names the workbook itself or Copilot's .hql, EXCEL_ABOUT gives both
  ways, and new tripping points cover FILES, the Workbook check, the Pivot filter, and files 15,
  11, 12, 20 and 21. `tests/test_workflows_page.py` lists the new Excel steps.
- `docs/main/workflows.html`, `docs/workflows.md` and `docs/main/how_to.html` are written again.

**Other how-tos.** The intermediate project's new table and batch change the printed reports in
how-tos 10, 20, 21, 26 and 32 (check()'s "Done" lines, mart.py's list, the Reference sheet's
counts). Their expected outputs follow; no lesson changed.

**What `copilot/` still needs (the lead's):**

- `copilot/workbook_text.py`'s docstring says "with Copilot files 15, 11 and 12": add 20 for a
  PivotTable.
- The Formula workbook's Steps sheet, from line 176 of `tools/formula_workbook.py` ("Copilot
  files 15, 11 and 12 loaded"), which writes `copilot/formula_workbook.xlsx`.
- `tools/formula_workbook_examples.py` (lines 9, 134, 140), which writes `copilot/examples/`.

Each of these writes a file in `copilot/`, so I left them. Two splits in other worktrees, not
on dev yet, would change the lists again: ticket 12's worktree has file 21 split into 21 and
22 (Pivot filters at scale), and a sibling's note says ticket 14 makes the Excel files 23 and
24 too, "left to ticket 15". The README's Excel steps, `EXCEL_FLOW` and the overview's
tripping points name "15, 11, 12 and 20" and "21" as dev has them now; when those land, these
lines want the new numbers.

**Every text a beginner sees that changed** (for the beginner reader, the lead's to run):

- how-to 33, whole, on `docs/main/how_to.html`; the page's header line naming
  `example_workbook(...)`; its Intermediate group's line;
- the expected outputs of how-tos 10, 20, 21, 26 and 32 (one more batch and table listed);
- the README template's Excel section: the chart and its 7 steps, the 7 bold steps after it,
  the closing paragraph and the checklist; the Copilot section's first paragraph; the how-tos'
  Intermediate group line; and the intermediate Example project's line;
- the Workflows overview's Excel box, its hand-off, its about line, its 7 steps and its
  tripping points;
- the Example projects page: the intermediate project's README (its new paragraph and file-map
  rows); the workbook shown as text; the batch's batch.md, scripts/job_hours.hql and
  written.json; mart.job_hours's notebook, Table reference, checklist, scan, compare and
  pivot_filters.json; admin/removed/; and every notebook whose output names the new table
  (check_project, run_tables, the Reference sheet's).

**Tests** (`-n 6`): `tests/test_how_tos.py`, `tests/test_example_projects.py`,
`tests/test_example_projects_page.py`, `tests/test_upgrades.py`, `tests/test_workflows_page.py`,
`tests/test_readme.py`, `tests/repo/`, `tests/journeys` and `tests/test_convert_workbooks.py`:
1,810 passed. Not the whole suite. `tests/snapshot/known.txt`: dev's plus the 56 hashes these
runs made that it didn't hold. The hashes the old outputs made (how-tos 10, 20, 21, 26 and 32,
the intermediate's pages and the journeys that copy it) are left for the lead, as tickets 07
and 09 left theirs.

**After the user's decision of 2026-11-19 (ticket 18).** The decision: a pivot becomes one table at
its finest grain, and its totals are named in the checklist rather than converted.

- How-to 33's step 4 says a PivotTable becomes one table of its rows, each Row and Column field
  a column and each value a column. It says its Grand Totals and subtotals are not converted,
  each named in the table's checklist with the GROUP BY that gives it, and that this workbook's
  Grand Total is off.
- The README's step 2 says the same.
- `EXCEL_FLOW`'s example `.hql` is `region_budgets.hql` now, not `budget_by_region.hql`, which
  read like a total level's table.
- No page shows or promises a `<pivot>_grand_total` or `<pivot>_by_<field>` table.

**What runs today.** The workbook's PivotTable has `grand_total_row=False`, so today's code
makes no total table here. No output of this ticket shows one, and nothing has to be
regenerated to take one out.

**What ticket 18 regenerates.** Its checklist note naming the totals reaches
`tables/mart__teams_pivot/conversion/checklist.md`, which how-to 33 prints one line of (the
Pivot filter's). It also reaches the intermediate's `tables/mart__job_hours/conversion/checklist.md`,
so ticket 18 rewrites:

- `example_projects/intermediate/`;
- `docs/main/example_projects.html`;
- `docs/main/how_to.html`, if how-to 33's printed lines change.

Ticket 18 may also want to turn the PivotTable's Grand Total on, as Excel's default, in
`job_hours_workbook()` (`tools/example_project.py`). Then the checklist has a total to name, and
how-to 33's "has its Grand Total turned off" sentence goes. That change rewrites:

- the workbook, the intermediate Example project and its page;
- the Workbook check's cell count in how-to 33 (2 cells, plus 1);
- how-to 33's outputs.

Until ticket 18 lands, the how-to's sentence about totals being named in the checklist
describes the code after it, not today's: today a Grand Total that is on still makes a
`_grand_total` table.

# Toolbox 8.8: the Lineage state and the Lineage difference

Label: wayfinder:map

The user (2026-11-17), with 8.7 shipped: "this is 8.8. I want to implement a lineage difference
capability. It often happens that changes in one upstream table in some calculated column
affects the effective logic of a downstream table. I want to be able to generate difference
files or some other capability that shows when effective logic changed (the sql remains the
same but the table columns upstream may have changed inducing a difference in effective
downstream logic) to highlight when and where changes occured. Every time I change a table or
reference, a lineage file would have to be generated. A lineage state table may have to be
implemented to make analysis easier without having to parse html files." Grilled the same day
in four rounds, Q1 to Q25, every answer "as recommended".

## Notes

### What is there today (8.7 at 0510f5d1)

- **A Statement's Lineage** (`lineage.py`'s `Graph`) traces each output column within its own
  Statement, down to the columns of the tables it reads, with its "Rows that count" (WHERE,
  JOIN ON) and "One value for each" (GROUP BY). A Saved table it reads is a leaf: nothing
  follows `mart.team_failures.fails` up into that table's own write.
- **Project lineage** (`project_lineage.py`) draws table by table, no columns.
- **Past Lineage.** Each Table notebook's cell 4, `export_lineage(write())`, adds a timestamped
  pair to its folder's `lineage/`. Nothing compares two of them.
- **A Table notebook** ends with cell 4 (Lineage), cell 5 `export_hive()` (its `.hql`, "from the
  logic as last saved") and cell 6 (its Reference sheet rows).
- **A prod copy** has a Table folder and Table reference of its own (`project.promote`).
- **`admin/sent.csv`** logs each send to the warehouse: `time,kind,tables,script`.
- **Building every table** is done already by `export_project_lineage`, through `project.load`,
  and each Scheduled run as its Build cell builds it with its parameters' defaults; a Run value
  is worked out as each Statement is built, so one reading the warehouse needs `connect`.
- The standard library is open to every Toolbox file (`tools/toolbox_registry.py`).

### Effective logic (Q1 to Q4)

- **A column's Effective logic** is its own logic and the rows that count for it (WHERE, JOIN
  ON, GROUP BY, HAVING), with each Saved table's column it reads replaced by that column's
  Effective logic, down to the tables the Project doesn't write (Q1, "(b)").
- **What counts as a change** (Q2): the Hive the Toolbox writes for the column and its rows
  that count, compared with:
  - table aliases replaced by table names (`e` renamed `ev` is no change);
  - each Run value as its function and what it was given, never its value, so
    `latest_partition("ops.job_events")` reads the same each day;
  - a Hivevar by its name; a Script tag's answer as its text.
- **Opaque steps** (Q3): an Unchecked statement's or Unchecked derived table's text, or a Python
  step's function source, is one fingerprint; a change to it changes every column it writes,
  shown as "opaque: the whole step changed".
- **What is recorded** (Q4): each Saved table's `write()` columns, each Scheduled run's
  Statements (its SELECTs named `<run>.<result>`), and each Table reference's columns and types
  for the tables the Project doesn't write, the roots. A Table notebook's other logic
  functions, such as `week_totals(...)`, are recorded only through a Scheduled run that uses
  them.

### The Lineage state (Q5 to Q7, Q11 to Q13, Q19, Q23, Q25)

- **One file**, `admin/lineage/lineage_state.csv`, added to, never rewritten (Q7: a CSV, like
  `registry.csv` and `reference_sheet.csv`, for Excel, `pandas.read_csv` and git).
- **Each recording covers the whole Project**, since one upstream change changes what reads it,
  and adds a row only for what changed since the last (Q5). The first recording writes every
  column as `first`, so the CSV replays to any point (Q11).
- **It never reaches the warehouse** (Q6): each Statement is built with each Run value given a
  stand-in, never called, so it needs no `connect(...)`. ADR 0015.
- **Its columns** (Q11):
  `recorded_at, commit, recorded_by, toolbox_version, table, column, kind, change, type,
  own_logic, reads, rows_that_count, own_hash, effective_hash, because`
  - `kind`: `saved_table`, `scheduled_run` or `reference`;
  - `change`: `first`, `added`, `removed`, `own`, `inherited`, `retyped`, `opaque` or `toolbox`;
  - `own_logic`: the column's Hive as compared (Q2); `reads`: the columns it reads,
    `;`-separated, to follow upstream in pandas;
  - `because`: for an inherited change, the root columns whose Own change it comes from; for an
    own change that came with a Building block's change, `building_block:<name>` (Q25);
  - `recorded_by`: the call, such as `project.convert` or
    `tables/mart__x/mart__x.ipynb export_hive()`;
  - `commit`: the Project's commit, as `lineage.scripts_commit` reads it, blank outside git.
  - The expanded Effective logic isn't stored as text: it is rebuilt by following `reads`.
- **A Table reference's change** (Q12): a column added, removed or retyped counts, and a
  retyped root passes an Inherited change to every column reading it. A description, an Alias
  (its Hive change shows in the Statements that use it), the Key, the Partitions and the
  location don't.
- **Renames** (Q13) are a removal and an addition upstream and an Own change downstream; no
  rename is guessed.
- **A table or run that doesn't build** (Q19), a logic cell that doesn't load or a `<...>` left,
  is not recorded: its last rows stand, never `removed`, and the printed line and the difference
  page name it with why. Only `remove_table` and `remove_scheduled_run` record `removed`.
- **Building blocks** (Q25): each recording keeps each Building block file's hash; a table's Own
  change in the same recording as a change to a block it imports names that block in
  `because`, and the difference groups those tables under it.
- **A Toolbox rewrite** (Q23): each row carries `toolbox_version`, and the recording an Upgrade
  makes marks each change it finds `toolbox`, never `own` or `inherited`. ADR 0015.

### When it records (Q5, Q14, Q17, Q21)

- **Every Project action that changes a table or Table reference** records at its end: making
  or removing a Table folder or Scheduled run, adding Table references, converting, promoting,
  refreshing the Reference sheet, and the `change_a_saved_table` Workflow's last step.
- **A Table notebook's `export_hive()`** (cell 5) records, and prints one line, such as
  "Lineage state: 3 columns changed (1 own, 2 inherited): project.export_lineage_difference()
  shows them." Cell 4's `export_lineage` doesn't (Q14).
- **By hand**: `project.record_lineage_state()`, from `admin/lineage.ipynb` (Q15).
- **The Upgrade** records (Q17).
- **Never a Scheduled run** (8.6's Q17: "waste of compute"), and never `check()`: `check()`
  reports "N columns' logic differs from the last recording", naming the tables and the cell
  that records, and records nothing (Q21).

### The Lineage difference (Q8, Q16, Q20, Q22)

- **`project.export_lineage_difference(since=None, tables=None)`** (Q22) writes
  `admin/lineage/<time>-difference.html` and its Markdown twin `.md`.
  - `since=` takes a time or a commit; left out, the newest recording against the one before.
  - `tables=` takes one name or a list: the page shows only those tables and the chains that
    reach them ("why did `mart.team_report` change?").
- **For each changed table** (Q8): its columns with an Own change, before and after; those with
  an Inherited change only, each with its chain down to its root, such as
  "`mart.team_report.fail_rate` ← `mart.team_failures.fails`, own change 2026-11-20 at
  1a2b3c4"; columns added, removed and retyped; and opaque steps marked.
- **When the data changed** (Q20): each changed table's first write since the change, read from
  `sent.csv` ("first written with this logic: 2026-11-21 06:00"), or "not written since".
- **Toolbox rewrites** are folded apart, under "rewritten by the Toolbox's upgrade to <version>".
- **The drawing** (Q16): the Project's tables, table by table as the Project lineage draws them,
  from the shared page module: Own changes in one colour, Inherited only in another, unchanged
  faded; clicking a table opens the side panel with its changed columns, each chain and its
  before and after. The Markdown twin holds the lists. The Project lineage page doesn't change.
- **Both record and difference are Project actions**, in the Admin log. Neither changes the
  warehouse.
- **Past Lineage stays as it is** (Q9).

### `admin/lineage.ipynb` (Q15)

A new admin notebook, owned by no one Workflow, like `check_project.ipynb`: a cell that records
(`project.record_lineage_state()`) and a cell with `project.export_lineage_difference(since=...,
tables=...)`. `admin/scheduled_runs.ipynb` keeps its Project lineage cell.

### The Example project, docs and usability (Q18)

- **The intermediate Example project**: `tools/example_project.py` records its first state,
  then makes one real change, the Building block `events_per_job` counting a retry as a run,
  so `mart.job_day_facts.runs` has an Own change and `mart.team_days.runs` an Inherited one
  (nothing reads `mart.team_failures`, the first choice); it records again and exports the
  difference, which the Example projects page shows. The change stays.
- **Docs**: a how-to, "Find what changed a column"; a README step; CHANGES.md's `## 8.8`; the
  Workflows overview naming `admin/lineage.ipynb`. No new Copilot file.
- **Usability**: one new dev scenario, W10, a stand-in user told a number moved who finds why
  from the difference page.

### The version

8.8, named by the user. Its Upgrade step adds `admin/lineage.ipynb` and makes the Project's
first recording, and touches nothing under `scheduled_runs/<name>/`. It freezes the Example
projects at 8.7 in `tests/upgrade_from/8.7/`. Only ticket 10 changes `version.txt`.

### Words

- **Effective logic**, **Lineage state**, **Lineage difference**, **Own change** and
  **Inherited change** (CONTEXT.md, 2026-11-17, Q10). _Avoid_: full lineage, snapshot, diff,
  induced change.
- **ADR 0015**: the Lineage state compares logic, never values, and a Toolbox rewrite is never
  an Own change (Q2, Q6, Q23).

## Tickets

- [01 Effective logic](issues/01-effective-logic.md)
- [02 The Lineage state](issues/02-lineage-state.md)
- [03 Where it records](issues/03-where-it-records.md)
- [04 check() and an unrecorded change](issues/04-check-unrecorded.md)
- [05 The Lineage difference](issues/05-lineage-difference.md)
- [06 The difference page's drawing](issues/06-difference-drawing.md)
- [07 admin/lineage.ipynb](issues/07-lineage-notebook.md)
- [08 The Example project's change](issues/08-example-project.md)
- [09 The docs](issues/09-the-docs.md)
- [10 8.8: the Upgrade step and the raise](issues/10-eight-point-eight.md)
- [11 The usability round](issues/11-the-usability-round.md)

One at a time, by number, the user's habit; 03, 04 and 05 can run side by side once 02 is
done. The real dependencies are in each ticket's `Blocked by:`.

## Records this changes

- **`sqlglot_composer/`:**
  - a new `lineage_state.py`, Effective logic and the Lineage state (01, 02);
  - a new page builder for the difference, on `html_page.py` (05, 06);
  - `lineage.py`, for what the trace reuses (01);
  - `project.py`: `record_lineage_state`, `export_lineage_difference`, each Project action's
    recording, `check()` (02 to 05); `workflows.py`, `change_a_saved_table`'s last step (03);
  - `project_templates.py`, cell 5's line, and `admin/lineage.ipynb` (03, 07);
  - `public.py` (02, 05); `upgrades.py` and `version.txt` (10).
- **`tools/`:** `toolbox_registry.py` (the new files); `example_project.py` and the Example
  projects page (08); `workflows_page.py` (09); `usability_scenario_files.py` (11).
- **Tests:** new tests for each ticket; `tests/journeys/` (08); `tests/test_upgrades.py` and
  `tests/upgrade_from/8.7/` (10).
- **Docs:** a how-to, the README, the Workflows overview (09); CHANGES.md's `## 8.8` (10);
  `docs/usability-loop.md` (11).
- **CONTEXT.md:** the five words (already, 2026-11-17). **ADR 0015** (already, 2026-11-17).
- **CLAUDE.md:** this map; `admin/lineage.ipynb` and `lineage_state.csv` in "A Project's admin
  folder" (07).

## Decisions so far

- [01 Effective logic](issues/01-effective-logic.md): `effective_logic.project_logic(root)`,
  each column's own logic in `<db>.<table>.<column>` terms with Derived tables written out,
  Run values given stand-ins by `run_values.stand_ins()`, an Unchecked step reading
  `<db>.<table>.*`, and an effective hash over every column upstream.
- [02 The Lineage state](issues/02-lineage-state.md): `project.record_lineage_state()` and
  `lineage_state.record`, `read_rows`, `columns_at`; Building block hashes as rows of kind
  `building_block` in the same CSV; removed only by the registry; an Upgrade's changes
  `toolbox`. Merged 2026-11-17 with a lazy import (the two modules import each other's
  neighbours) and a whole-table read followed to each of its table's columns.

## Not yet specified

## Out of scope

- Checking the warehouse's own table definitions (DESCRIBE) against the Table references (Q24).
- Comparing rows or numbers before and after a change (Q24).
- Alerting or emailing on a change (Q24).
- A recording from a Scheduled run (Q24, 8.6's Q17).
- Lineage outside a Project, such as a bare `export_lineage` in a loose notebook (Q24).
- Guessing renames (Q13).
- Colouring the Project lineage page by change (Q16).
- Changing past Lineage (Q9).

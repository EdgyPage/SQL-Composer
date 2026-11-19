# The convert Workflow reads a workbook

Type: task
Status: resolved
Blocked by: 05, 06
Size: L

## Question

How a user gives a workbook to a Conversion, and what it makes (round 1, Q1; CONTEXT.md's
Conversion).

## Done when

- **`project.convert(..., files=[...])` takes an `.xlsx`** beside `.hql` scripts; the convert
  Workflow's notebook says so. A batch of one workbook converts it alone.
- **Each final's Hive** is kept in the Conversion folder, as Hive given as text is, and
  converted as every batch's Hive is: Table folders, Table references, the checklist,
  `# CONVERSION:` marks and Unchecked pieces (ADR 0014).
- **Each mark, refusal and thing left alone** from tickets 04 to 06 is in the table's
  checklist; a pivot's default name is a Decision.
- **The Copilot path's mark**: a `-- Pivot filter: <kind> <field>` comment above a condition in
  an `.hql` is read into the same Decision ticket 08 makes, so both paths reach it.
- `public.py`, the docstring and its Worked example; a refusal for a workbook the reader
  refuses, such as one with a loop.
- Tests: a workbook of each kind converted end to end on the Example database; a Copilot-style
  `.hql` with the mark gives the same Decision as the workbook does.

## Answer

Built 2026-11-19. **No new public name**: the user's call is `project.convert`, as before,
whose `files=` (and `file=`) now take an `.xlsx` (or `.xlsm`).

**What it does.** `project.convert("runs", files=["runs.xlsx"], query=query,
database="ops")`, or a workbook beside `.hql` scripts in one batch, or `file="runs.xlsx"`:

- The workbook is read where it is, never copied, as a script file is. Each final, as
  `workbook_hive(workbook, database=DATABASE)` gives it (convert's `database=` fills
  `<database>`, as it names a batch's unqualified tables), is written as Hive (`hive_texts`)
  and kept in the batch's `scripts/` as `<table>.hql`, as Hive given as text is. Each is then a
  script of the batch, a query alone, converted as every batch's Hive is: Table folder, Table
  reference (from DESCRIBE of the sources through `query`), checklist, `# CONVERSION:` marks,
  Unchecked pieces, seed, compare (with its query, as any query alone is). A batch holding a
  workbook names every query alone for its file (`batch_statements(..., named_for_files=True)`),
  so a workbook with one final isn't named for the batch.
- **Names** (`workbook_conversion.final_table_names`): a Table's or a pivot's own name in snake
  case (PN1); a pivot keeping Excel's default name `<sheet>_pivot` (PN2, `pivot_table_names`);
  a final named as a database table the batch reads, as a Table with formula columns over its
  own rows is, `<name>_report` (the batch would refuse it otherwise, "a query alone named as a
  table the batch reads"); a total level or a Total Row is its pivot's or Table's table name and
  the level in snake case: `pivot_pivot_by_job_id`, `pivot_pivot_grand_total`,
  `job_runs_report_total_row`; a `_2` where two would share one.
- **The name Decision, as built:** a proposed name (PN2, `_report`) is used as it is, as 8.5's
  proposals are, and said twice: a checklist note ("Its name, pivot_pivot, is proposed:
  PivotTable1 is Excel's default name, so it is named for its sheet, Pivot. If you want
  another, give it in RENAME ... and convert again ...") and a report line ("Named as proposed,
  each in its checklist: ..."). It is answered in the convert notebook's names cell, `RENAME`,
  by the final's name in the workbook, `{"PivotTable1": "runs_by_job"}` (its levels follow; a
  level's own name renames it alone), then convert again, as STAGING's choice is. A name given
  must be a plain lowercase name, or it is refused. **For the lead:** it isn't a Decision
  `check()` lists or that blocks promotion, since a table's name decides every file it has;
  making it one answered in DECISIONS would mean write_decisions renaming a converted table,
  which ticket 08 may want for its "table per value" anyway. Say if it should move there.
- **The map, table by table:** each Note (WRITTEN_IN, TYPED_OVER, MARK, REFUSED, LEFT_ALONE,
  TO_FILL_IN) goes to each final it is about: one about the piece the final is, or any piece it
  reads at any depth (by the Note's `where`, `job_runs[hours]`, `Power Query "x"`, a pivot's or a
  level's name), and a `<...>` its Hive holds. Each is a checklist note in plain words, "From the
  workbook, marked (rule F6): job_runs[next_month]: ..." (`note_said`). A Note about no final (a
  chart, cells outside a Table, a pivot refused with no final) is listed in batch.md under "## The
  workbook runs.xlsx", and the report says how many.
- **A final whose Hive holds a `<...>`** (a pivot over a plain range, `<runs>`; a Table or
  column named otherwise than plainly, N2) can't be read by sqlglot, so it isn't converted: it is
  skipped, named with why in the report and batch.md, its Hive kept in `scripts/` to fill in. If
  every final of a batch of workbooks holds one, convert refuses.
- **Refusals** (three parts, through `refusals.refuse`): a workbook whose pieces read each other
  in a loop (the reader's LoopError, its three parts kept); a workbook with nothing to convert
  (naming what was refused, if anything); a file named `.xlsx` that isn't one; an `.xls`; a
  workbook that isn't there; a final named as another script of the batch; a rename that isn't a
  plain name; every final holding a `<...>`.
- **The convert Workflow's notebook:** FILES says it takes `["runs.xlsx"]`, RENAME a final by
  its name in the workbook, and step 1's goal says each final of a workbook. The Example projects'
  convert notebooks and `docs/main/example_projects.html` are written again from it;
  `tests/test_upgrades.py`'s `AWAITING_ITS_STEP` lists `admin/workflows/convert/convert.ipynb`
  until ticket 16's Upgrade step writes the convert notebook again (`_write_one_workflow_
  notebook_again(upgrade, "convert")`).
- `project.convert`'s docstring has a paragraph for the workbook (its Worked example is as it
  was: the Toolbox ships no workbook writer to make one in a doctest). CONTEXT.md's Conversion,
  Batch and Conversion folder say a workbook's finals are kept in scripts/.

**The Pivot filter record, for ticket 08.** Both paths give `workbook_pivot_hive.
ConvertedPivotFilter(final, kind, field, values, field_values, ranked_by, bottom)`, its `final`
the **Saved table in dev** it ends up in (not the workbook's pivot name):

- the workbook path: `pivot_filters(workbook)`, each given to every final whose rows go
  through it (the pivot's own final, each of its levels, and a Table reading it through
  GETPIVOTDATA), `final` replaced by that table;
- the Copilot path: `converting.pivot_filters_in(text, table)` reads each `-- Pivot filter:
  <kind> <field>` above a condition, or `/* Pivot filter: ... */` after it as the code path
  writes it; kind and field from the mark, values from the condition (`=`/`IN`/`IS NULL` kept;
  `<>`/`NOT IN`/`NOT IS NULL` dropped, `IS NULL OR` a blank kept; BETWEEN's days as datetimes;
  a value filter's `<= n`, its RANK's ORDER BY as Excel's default caption, "Sum of
  duration_mins", ASC as `bottom`); a mark above an AND, or one sqlglot drops (above a `NOT`),
  is matched by field and kind. **`field_values` is `()` on this path**: Hive holds no pivot
  cache, so ticket 08 has no "at least" counts for a Copilot `.hql` alone (it could take them
  from the workbook when the batch holds it, as ticket 09's check does, or count the column in
  the warehouse). Every other field equals the workbook's, as the tests hold.
- Each batch keeps them in its `written.json` under `"pivot_filters"`, by table (only when a
  table has one), each a dict of the record's fields, a date `{"day": ...}`, a datetime
  `{"time": ...}`; `project.pivot_filters_of_batch(root, name)` reads them back as the same
  records (a finished batch's too).
- Each is in its table's checklist: the workbook's PF Note ("From the workbook, marked (rule
  PF3): PivotTable1: Pivot filter: slicer status, FAILED and SUCCESS kept: a Decision of its
  table."), or for a script "Pivot filter: slicer status, FAILED and SUCCESS kept, as its Hive
  marks it: a Decision of its table." (`workbook_pivot_hive.pivot_filter_said`, now shared).

**Files.** New `sqlglot_composer/workbook_conversion.py` (no sqlglot of its own; in the
registry's `PYTHON_FILES`): `is_workbook`, `converted_workbook`, `ConvertedWorkbook`,
`WorkbookFinal`, `every_final`, `final_table_names`, `note_said`, `name_note`,
`to_fill_in_said`, `filters_of`, `pivot_filter_record`, `pivot_filter_of_record`,
`refuse_an_old_workbook`. `project.py`: `convert`, `_scripts_and_workbooks`, the batch's
`_BatchFiles.workbooks`/`finals`/`pivot_filters`, batch.md's `_scripts_where` and
`_workbook_lines`, the report's `_scripts_counted` and `_workbook_report_lines`,
`_note_pivot_filters_and_workbook`, `pivot_filters_of_batch`. `converting.py`:
`batch_statements(named_for_files=)`, `pivot_filters_in` and its helpers.
`workbook_pivot_hive.py`: `pivot_filter_said`. `workflows.py`: the convert notebook's texts.

**Tests:** `tests/test_convert_workbooks.py` (45): a workbook of each kind (formulas only, a
Power Query, a Total Row, a pivot, a pivot with a slicer, a mix of a formula Table, a query and
a pivot over it) converted end to end on the Example database, each table's `preview()` run on
it; scripts/ and batch.md; beside a script; `file=`; the marks; the map's notes in checklists and
batch.md; names, proposals and RENAME; the record from the workbook, kept and read back (a
Timeline's days), from the code path's Hive (fixtures 05, 08, 10 and a Top filter), from a
Copilot `.hql` (the same record but `field_values`), each kind of mark above a condition and
marks joined by AND; each refusal. 171 new hashes in `tests/snapshot/known.txt`.

**Left.** The code-review skill and the beginner reader haven't run (the lead runs them). The
name Decision's place (above). `FILES = []` still reads only `.hql` files beside the notebook,
not a workbook. A Data Model pivot over a query loading only the Data Model (ticket 06's Left)
still has no source.

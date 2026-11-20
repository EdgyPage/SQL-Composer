# Every source Table's warehouse table, a Decision

Type: task
Status: resolved
Blocked by: 07, 15
Size: M

## Question

The beginner reader on ticket 15's how-to 33, as a person with Excel skills: "Nothing says convert
matches a Table to a warehouse table by its name. My Tables are called Table1 or SalesData.
Should I rename them? And what if they come from two databases?" Asked (2026-11-19), the user
chose: each source Table's warehouse table is a Decision of the converted table, proposed as
`<database>.<table name>` and answered in the convert notebook, as a plain range's already is
(ticket 07's SOURCES kind).

## Done when

- **Every source** a converted table reads (a Table of typed rows, a query's source Table, a
  range) has a SOURCES Decision in its Table reference, proposed `<database>.<table name in snake
  case>`, listed by `check()` until answered, answered as `"sources": {"ops.table1":
  "ops.job_runs"}`; answering repoints the logic and the kept Hive as a range's does (ticket 07).
  Two sources may answer different databases. A source whose proposed table DESCRIBE finds
  stays proposed, open, as every Decision is (8.5: the person accepts a proposal).
- **The Workbook check** still runs the Hive over the workbook's own Tables, matched by the
  Table, whatever the answer names.
- **How-to 33 and the README** say it plainly: a Table's name needn't match the warehouse;
  each source is a Decision proposed from its name.
- **The beginner reader's other stops on how-to 33** (its report:
  `.scratch/toolbox-8-9/reports/beginner-reader-2026-11-19-ticket-15.md`), and the reviews'
  findings on ticket 15, fixed.
- Tests: a workbook whose Table is `Table1` converts, its SOURCES Decision proposed and answered,
  the rows right on the Example database; two sources in two databases.

## Answer

Built 2026-11-19 on dev's 3d7e8834 (ticket 16 merged, 8.9). No new public name.

**The Decision.** Every source a converted workbook final reads now has a SOURCES line in its
table's Table reference, the `decisions.SOURCE` kind ticket 07 made for a plain range:

- `workbook_conversion.sources_of` gives each final its sources: each Table whose typed rows
  stand for a database table (a plain name, not Parameters or Keys, rows neither a summary's
  nor a query's: `_stands_for_a_database_table`), at any depth, a query's source Table
  included, and each plain range a pivot reads; kept only where the final's Hive names it, in
  the order it first does. `RangeSource` is now `WorkbookSource(table, where, columns)`.
- A Table's source is proposed as `<database>.<its name in lower case>`, `Table1` as
  `ops.table1`: the name convert's Hive reads (it lowercases), and the snake case of every name
  Excel gives a Table that is plain (a name with a period or other mark is still N2's `<...>`,
  which skips its final, as before). Its line reads `"ops.table1": "ops.table1",  # TODO:
  proposed: the database table Table1 of runs.xlsx samples`; a range's is as it was.
- It is open until answered, check() and the pasted DECISIONS list it, and a source DESCRIBE
  finds stays proposed, open, as every Decision is. Where DESCRIBE finds no table of the
  proposed name, its Table reference is written from the Table's typed columns, each type a
  guess (`project._write_source_references`, was `_write_range_references`), so the final
  converts; the report says "Wrote ... from the rows of the workbook's Tables and cells, each
  type a guess, ...".
- Answered `"sources": {"ops.table1": "ops.job_runs"}`, it repoints the logic and the kept Hive
  as a range's did. Two fixes for it: the Hive files are rewritten in any case
  (`_qualified_name_renamed(..., any_case=True)`), since the workbook's Hive reads `ops.Table1`;
  and a source answered in another database gets its import in the logic
  (`_import_the_database_of`: `from references import crm` beside `from references import
  ops`), else the logic named a module it never imported.
- **The Workbook check** is untouched: it runs each final's own Hive, from the workbook, over
  the workbook's Tables matched by the Table's name, whatever the answer names. A test answers
  both sources and converts again with `overwrite=True`: the check still runs on every cell.
- Docstrings: `project.convert`'s workbook paragraph, `write_decisions`' "sources", the
  decisions module's SOURCE kind and SOURCES comment, `workbook_conversion`'s module.

**Tests** (`tests/test_convert_workbooks.py`, 4 new): a workbook whose Tables are Table1
(job_runs' rows with `hours` and an XLOOKUP into Table2), Table2 (jobs') and a query reading
Table2: each source proposed from its name and listed by check, each Table reference written
from the Table's rows; a source the database has (job_runs) a Decision too, "proposed"
accepted; the two answered in two databases, `ops.job_runs` and `crm.jobs` (a query standing
crm's tables in for ops'), the logic and in_dev.hql repointed, `from references import crm`
added, and the rows right on the Example database, the query's table too; the Workbook check
whatever the answer, converting again. The range test's report line follows the new words.

**The docs, stop by stop** (the beginner reader's report on ticket 15):

1. A Table's name: how-to 33's When you'd use it, step 3 and step 6 (four Decisions now),
   step 7 answers `"sources"` (each "proposed", and how Table1 or another database is
   answered); the README's step 2 and step 7; the overview's new tripping point; EXCEL_FLOW's
   step 5 and decisions node; CHANGES.md's What's new (the coordinator's line). Its "a proposed
   name ... in `RENAME`" was untrue since ticket 07's review: now "its `"name"` Decision".
2. Any workbook converts as it is, the Formula workbook optional: how-to 33's When you'd use
   it and step 3; the README's step 1, now "Take your workbook as it is"; EXCEL_FLOW's step 1
   and node (the overview's step follows).
3. The slicer back: how-to 33's step 9, in Excel's words (load the rows into a sheet, Insert >
   PivotTable, Insert > Slicer on team), and a preview filtered on team, run.
4. Step 2's "repeats": said before it, expected, what it means, and that the next line shows
   the Key holds.
5. `conn`: step 1 says it is the connection, the Example database's here, your team's in your
   notebook's `connect(...)` line, linking Start a Project.
6. admin/removed/: step 8 says the rename keeps the old name's files there, named by the time,
   nothing lost, nothing reads them.
7. TODO lines that wait on nothing: step 8 says they are no Decision and need no answer.
8. The compare: `partitions=[]` dropped, the table having no Partitions, so every row is read;
   what compare.md says at work, "Passed: every row: it has no Partitions."; the Done line says
   "at work" and "here". The README's "seeded" dropped from EXCEL_FLOW's node and step 5: a
   workbook's table never reads itself.
9. Copilot files: how-to 33's step 11 and the README's step 3 give one short list in 00's Index
   order (15, 11, 12; 20 with a PivotTable; 24 with a slicer, Filter or Top 10; 23 with a
   total), then this workbook's set, and 21 with 03, 05, 06 and 22 with 06, 17.
10. The checklist line: step 6 says its parts in two sentences before printing it.

**Ticket 15's reviews.** Standards: `tools/example_project.py`'s mark-stripping loop is one
function, `_delete_conversion_marks`; `job_hours_workbook` says why it puts sys.path back
(formula_workbook puts the repo first, ahead of the Project's own Toolbox); `MADE_AT` is
`TIMES_PART`; how-to 33's report trimming says it is the page's own, the notebook showing the
whole report (steps 4, 5 and 6). Spec: the overview's Copilot tripping point names 21 with 03,
05 and 06 and 22 with 06 and 17. The Example project answers `"sources"` as the how-to does.

**Regenerated here, after the rebase** (each is the tools' output, so the lead's one
regeneration after ticket 18 merges writes them again): the README's charts
(`tools/workflow_graph.py`), `docs/main/workflows.html`, `docs/main/how_to.html`, the
intermediate Example project (`references/mart__job_hours.py`'s SOURCES, the removed copy's,
written.json) and `docs/main/example_projects.html`. `tests/snapshot/known.txt`: dev's plus the
hashes these runs made it didn't hold; the hashes the old outputs made are left for the lead.

**Left.** A Copilot `.hql` standing for a final gets no SOURCES: it names its tables itself.
The Table reference written for a proposed name the warehouse hasn't (`ops.table1`) stays in
references/ after the answer, as a range's did; remove it with the remove notebook if unwanted.
The code-review skill and the beginner reader haven't run on this ticket (the lead's).


# Toolbox 8.9: a Formula workbook converted in code, PivotTables, and the Workbook check

Label: wayfinder:map

The user (2026-11-19), with 8.8 shipped: "This is the next version upgrade. I want to plan out a
couple things and see if they are worth pursuing for non-technical user usability. Users can be
expected to have fundamental Excel skills and a penchant for pivot tables. The excel conversion
text instructions have bloated to the point I wanted to avoid by not making code conversions an
explicit feature, but I think it's time to make the code. I want to be able to convert an
arbitrary excel file that can have some combination of pivot tables, power query, and excel
functions." Copilot should "'add on' to pivot tables and anticipate changes to converted sql to
make it scalable": "an applied filter should be directly translated, but it should be a copilot
hint that the filter or sliced views could be aggregated in to batched inserts on a table or
different tables." Grilled the same day in five rounds; each answer below is the user's, or "as
you said" to the recommendation.

## Notes

### What is there today (8.8 at 63050726)

- **The Excel path is Copilot alone** (7.2's map: "A Copilot file, no Toolbox code"). Files 15
  (the steps, the map, the reply), 11 (each formula's Hive) and 12 (Power Query, whole-column
  totals and Total Rows) are loaded together, about 25,000 characters, each near the 9,000
  limit. Their rules have IDs (F1 to F10, I1 to I6, V1, V2, M1 to M5, X1 in 11; Q1 to Q7, G1 to
  G5, T1 to T4, S1 to S3, M1, M2, X1 in 12; P1 to P11, R1 to R3 in 15).
- **PivotTables are left alone**: file 11's X1 names them as presentation, and
  `copilot/workbook_text.py` only counts them ("A PivotTable").
- **`copilot/workbook_text.py`** reads an `.xlsx` with the standard library alone (zipfile,
  ElementTree, base64 and struct for the DataMashup, graphlib for the Order) and writes its
  Tables, formulas, Power Queries, defined names and the Order. It "needs nothing but Python".
- **`project.convert(name, hive=None, *, file=None, files=None, query=None, database=...)`**
  reads Hive only; the convert Workflow's notebook calls it on a batch.
- **Dev's Excel tools:** `tools/formula_workbook.py` builds a workbook with openpyxl (dev
  only); `tools/excel_queries.py` saves Power Queries as Excel saves them;
  `tools/workbook_fixtures.py` writes `tests/fixtures/workbook_text/`, three workbooks whose
  saved Power Queries the offline policy allows by name (`QUERY_FIXTURES`, the user's OK
  2026-11-01). `tools/excel_eval.py` and `tools/excel_eval_tasks.py` are the Excel evaluation.
- **sqlglot's executor** already runs dev's Example database (`example_database/executor.py`).
  In the Toolbox only `writing.py`, `engine.py` and `converting.py` may import sqlglot
  (`tools/toolbox_registry.py`'s `LIBRARY_FILES`).
- **The offline policy** refuses a committed workbook's Power Query, data connections, query
  tables and links out (`tools/offline_policy.py`), not a pivot over a Table or range. A Data
  Model pivot saves a connection, so a fixture of one needs an `ALLOWED` entry: the user's OK.

### The decision (ADR 0016)

- **Code, beside the Copilot files.** It reverses 7.2's "not often enough to make code for it".
  ADR 0016 records why, with the user's words.
- **Two paths, equal** (the user: "My non-technical users will likely use copilot, I'll use the
  code"; "Both paths, equal"). Files 11, 12 and 15 stay. Neither path is the other's
  reference: each is tested on its own, on the same tasks and by the same Workbook check, and
  each Copilot rule ID is tied to a test of the code giving the same Hive.

### What the code reads (rounds 1 to 3)

- **Any mix** of a Table's formulas, Power Query and PivotTables: the user, "the dependency
  graph fixes all of it so the format of the intermediate transforms doesn't matter for
  users". Roles are read from what reads what, as file 15's P1 to P11 and R1 to R3 say.
- **Data stays in Tables**: file 11's X1 refusal of a formula outside a Table holds on both
  paths (round 2, Q3).
- **One reader**, standard library only, moves into the Toolbox's folder and learns pivots;
  `workbook_text.py` loads it by its path, so it still needs nothing but Python, and the
  registry records that exception (round 3, Q6).
- **A pivot's source** (round 2, Q2): a Table, a query's output, or a plain range, read as the
  Table it would be, convert; a Data Model pivot whose values are plain sums converts from the
  query feeding it; a DAX measure and an OLAP source are refused and named.

### Formulas and Power Query in code

- **The same rules the Copilot files hold**, by their IDs: what converts, what converts with a
  mark, what is refused and named (NULL in its place). The code writes each final's Hive as
  sqlglot trees, through Hive text kept in the Conversion folder, then converts it as any
  batch's Hive is (round 1, Q1; ADR 0014's Unchecked pieces hold).

### PivotTables into Hive (rounds 1 to 4)

- **Row and Column fields** are the GROUP BY; a Column field is written as rows, never a
  column per value, so a new value flows in, marked "Column field <name>: written as rows"
  (round 1, Q3). The wide shape is a Copilot add-on (file 21).
- **Values**: each its aggregate (Sum, Count, Average, Max, Min, StdDev, Var; Distinct Count as
  `COUNT(DISTINCT)`); Show Values As (% of grand, row or column total, running total,
  difference from, rank) a Window; a calculated field a Column over the sums; date grouping
  (months, quarters, years) and number grouping (bins) an expression in the GROUP BY (round 3,
  Q2).
- **A calculated item** becomes a column beside the real rows (the user: "you can derive the
  calculated items and add a column to a table, regardless of whether or not it's strictly
  normalized. this preserves the aggregates and allows user expected outcomes from their
  tables"). `Coastal = East + West` on Region is a column `coastal`, `SUM(CASE WHEN region IN
  ('East', 'West') THEN sales END)` over the row's other keys, repeated on each of their rows; a
  ratio item is the ratio of the conditional sums, never a sum of row ratios (round 4, Q1).
- **Totals: what the pivot shows converts** (the user: "convert what is present in the table.
  The user should be responsible for correct presentation"). Each total level the pivot shows,
  a grand total or a field's subtotals, is a final of its own, `<pivot> (grand total)`,
  `<pivot> (by <field>)`, as file 12's T2 makes a Total Row one; never a Subtotal row in the
  pivot's own final (round 2, Q1).
- **GETPIVOTDATA** in a Table's formula makes the pivot a step: a CTE, read by a LEFT JOIN on
  the fields it names, as file 11's F8 lookups are (round 3, Q3).
- **Refused and named**: "Show items with no data", a DAX measure, an OLAP source. Charts stay
  left alone.
- **A pivot's name**: its own, in snake case; Excel's default, such as `PivotTable3`, is a
  Decision proposing `<sheet name>_pivot` (round 2, Q4).

### Pivot filters (rounds 1, 3 and 4; CONTEXT.md)

- **Every kind converts as the workbook was last saved**: a Report filter, items hidden on a
  Row or Column field, a slicer's selection (on each pivot it is connected to), a Timeline's
  dates, a value filter such as Top 10 (a rank Window). Each is the condition it is, its values
  written in.
- **Each is a Decision** of the table it ends up in (round 1, Q6), keeping the filter by
  default, its other proposals keeping every slice (round 3, Q4; round 4, Q2):
  - **fold into the grain**: the WHERE dropped, the column in the GROUP BY;
  - **one batch per value**: the value a Run value, the table partitioned on the column;
  - **a table per value**, named `<pivot>_<value>`, offered too, "emphasize how many different
    tables it would create. a filter with 100 conditions would make 100 tables, but the higher
    layer filter may have only 3, which is manageable." Each layer's count, and their
    combination's, from the values the pivot cache holds, as "at least".
- **The Copilot path reaches the same Decision**: file 20 has Copilot write
  `-- Pivot filter: <kind> <field>` above each such condition, and convert reads it (round 2,
  Q6). File 21 explains the trade-offs and what no Decision does, such as two pivots differing
  only in their filter made one table.

### The Workbook check (round 1, Q9; rounds 2 and 3; CONTEXT.md)

- **Offline, on the workbook's own Tables, never the warehouse**: the user, "check the sql
  against the 'databases' inside the excel file. the check works 'offline'. the actual sql will
  likely conflict with the old data inside an excel file."
- Each final's Hive runs on sqlglot's executor over the workbook's typed rows standing in for
  each `<database>.<table>`; its rows are compared with the values Excel last stored, a Table's
  cells, a Total Row's, a pivot's.
- **A match** (round 3, Q5): numbers within a relative 1e-9, on stored values, not as shown; a
  blank matches NULL only where file 11's M1 marks it. A difference is listed in the convert
  notebook, one line a cell ("Region East, Mar: Excel 1,204, Hive 1,198"), and blocks nothing.
- **It checks Copilot's Hive too**, when the workbook is in the batch beside the `.hql` files
  (round 2, Q7).

### Copilot (rounds 1 to 3)

- **Files 11, 12 and 15 stay** (the user: "keep them"); file 11's X1 stops naming PivotTables
  as left alone.
- **File 20, PivotTables into Hive**: the pivot rules, with IDs, and the `-- Pivot filter:` mark.
- **File 21, growing a converted pivot**: add-ons written as Toolbox code in the Table notebook
  (Show Values As, calculated fields, date grouping, the wide shape, totals as a rollup), loaded
  with 03, 05 and 06; and Pivot filters at scale, each layer's table count. The workbook is a
  one-time way in: an add-on is never a change to the pivot and a reconvert (round 1, Q8).
- **`workbook_text.py` shows each pivot** as `PivotTable "name"`: its source, Row, Column and
  Value fields with each summary and Show Values As, calculated fields and items, Pivot filters
  with slicers, the totals shown, its cells and values, and its place in the Order (round 3, Q7).
- **00_start_here.txt** says when to load 20 and 21.

### Testing (round 2, Q8; round 3, Q9)

- **Pivot workbooks** are written by a dev tool, on `tools/formula_workbook.py`, with each
  pivot's cache, definition, slicers and stored cells. Its stored values are worked out by the
  tool from each task's reference Hive, so they test the reader and the conversion, never
  Excel's own arithmetic.
- **A handful the user builds in Excel**, kept in `.eval-local/` for a manual round, test that
  the reader reads what Excel itself saves. Committing any as fixtures, or a Data Model fixture,
  is an `ALLOWED` entry: ask the user.
- **Queries in test workbooks** go on a Power Query sheet ("Query <name>:" with the M below),
  which the reader already reads, except the fixtures `QUERY_FIXTURES` already allows.
- **The bar**, as 7.2's: about 40 pivot tasks, 20 held out, each case alone and mixed with
  formulas and M; 95% on held-out for Haiku and Sonnet on the Copilot path; at most two tuning
  rounds, then a design spec. The code path is scored by the same scorer on the same tasks,
  and every miss is a bug.
- The held-out tasks are written before file 20, as 7.2 wrote them before file 11.

### The docs (round 4, Q3)

- An Intermediate how-to, "Convert an Excel workbook", on the Example database, its workbook
  from the dev tool: a Table with formulas, a query, and a pivot with a slicer reading them.
- The intermediate Example project gains that batch; the Example projects page shows it.
- The README's Excel steps and the Workflows overview show both ways into convert.
- CHANGES.md's `## 8.9`. The beginner reader runs on all of it.

### The version (round 1; round 4, Q5)

8.9, the user's: "this is an upgrade to 8, so the next version number." Its Upgrade step has
nothing to change in a Project and touches nothing under `scheduled_runs/<name>/`. It freezes the
Example projects at 8.8 in `tests/upgrade_from/8.8/`. Only the last task ticket changes
`version.txt`.

### Hive that stays small (ticket 17, the user's, 2026-11-19)

- The user: "add a ticket that sweeps the documentation to make sure the sql produced is memory
  efficient. I just wasted an hour of time 'debugging' an inefficient statement that has no
  logical errors in it, just was written to have bloated ctes."
- No doc or Copilot file says what a CTE costs in Hive today. Ticket 17 writes the rules once,
  checked against Hive's documentation, sweeps `docs/`, the README, `worked_examples/`, the
  Example projects and Copilot files 00 to 21, and adds a repo test that reads every SQL block
  with sqlglot for a CTE read twice, a `SELECT *` in a CTE, a column nothing reads and an ORDER
  BY with no LIMIT.
- It bears on 8.9's own Hive: file 15 and tickets 04 to 06 write each step as a CTE in each
  final reading it, so a step read twice in one final is worked out twice. It lands before
  files 20 and 21 (11, 12), the docs (15) and the rounds (14), so they are written and scored
  to it.

### Words

- **Pivot filter** and **Workbook check** (new), **Formula workbook**, **Conversion** and **Excel
  path** (widened): CONTEXT.md, 2026-11-19. _Avoid_: slicer filter, page filter, applied filter,
  sliced view; offline check, sample test.
- **ADR 0016**: a Formula workbook converts in code, beside the Copilot files.

## Tickets

- [01 The workbook reader in the Toolbox's folder](issues/01-the-workbook-reader.md)
- [02 Pivot workbooks for tests](issues/02-pivot-workbooks.md)
- [03 The reader reads PivotTables](issues/03-the-reader-reads-pivots.md)
- [04 Formulas and roles into Hive, in code](issues/04-formulas-in-code.md)
- [05 Power Query and totals into Hive, in code](issues/05-power-query-in-code.md)
- [06 PivotTables into Hive, in code](issues/06-pivots-in-code.md)
- [07 The convert Workflow reads a workbook](issues/07-convert-reads-a-workbook.md)
- [08 The Pivot filter Decision](issues/08-the-pivot-filter-decision.md)
- [09 The Workbook check](issues/09-the-workbook-check.md)
- [10 The pivot tasks and their baseline](issues/10-pivot-tasks.md)
- [11 Copilot file 20: PivotTables into Hive](issues/11-copilot-file-20.md)
- [12 Copilot file 21: growing a converted pivot](issues/12-copilot-file-21.md)
- [13 The two paths tied, rule by rule](issues/13-the-two-paths-tied.md)
- [14 The rounds: file 20 tuned, held-out scored, the code path scored](issues/14-the-rounds.md)
- [15 The docs](issues/15-the-docs.md)
- [16 8.9: the Upgrade step and the raise](issues/16-eight-point-nine.md)
- [17 Hive that stays small: the docs and Copilot files swept for bloated CTEs](issues/17-memory-efficient-hive.md)

One at a time, by number, the user's habit. 01 and 02 can run side by side; once 01 is done,
04 can; once 03 and 04 are, 05, 06 and 10 can. The real dependencies are in each ticket's `Blocked by:`.

## Records this changes

- **`sqlglot_composer/`:** a new reader file, standard library only (01, 03); a new file writing
  a workbook's Hive (04 to 06); a new file for the Workbook check, importing sqlglot (09);
  `converting.py`, `decisions.py`, `project.py`, `workflows.py`, `project_templates.py` (07 to
  09); `public.py` (07, 09); `upgrades.py` and `version.txt` (16).
- **`copilot/`:** `workbook_text.py` (01, 03); `20_*.txt` and `21_*.txt` and their sources in
  `tools/copilot_sources/` (11, 12); `00_start_here.txt` and file 11's X1 (11); the
  all-in-one file (11, 12).
- **`tools/`:** `toolbox_registry.py` (01, 04, 09); `formula_workbook.py` and a pivot writer
  (02); `excel_eval.py` and `excel_eval_tasks.py` (10, 14); `workbook_fixtures.py` (02, 03);
  `example_project.py`, `workflows_page.py` (15); `offline_policy.py` only with the user's OK
  (02).
- **Tests:** new tests for each ticket; the rule-ID ties (13); `tests/test_upgrades.py` and
  `tests/upgrade_from/8.8/` (16).
- **Docs:** a how-to, the README, the Workflows overview (15); CHANGES.md's `## 8.9` (16);
  `docs/copilot-eval.md`'s Excel section (10, 14).
- **CONTEXT.md:** the five words (already, 2026-11-19). **ADR 0016** (already, 2026-11-19).
- **CLAUDE.md:** this map.

## Decisions so far

- [01 The workbook reader](issues/01-the-workbook-reader.md): `sqlglot_composer/workbook_reader.py`,
  standard library only, `read_workbook` giving a `Workbook` (sheets, defined names, queries, the
  Order of `Piece`s); `workbook_text.py` puts the folder first on `sys.path` only while it imports
  the reader, as `spec_from_file_location` is dynamic code the offline policy refuses in
  `copilot/`; the base64 audit entry moved with it (the user's OK, 2026-11-19); the script's
  refusal names the path it looked in. Merged 2026-11-19 (bf90f613).
- [02 Pivot workbooks](issues/02-pivot-workbooks.md): `tools/pivot_tables.py` (`Pivot`, `Value`,
  `Top`, `Slicer`, `Timeline`; `work_out`, `with_pivots`) on `formula_workbook.saved`; stored
  values from the tool's own Hive on the Example database; fixtures 04 to 10 in
  `tests/fixtures/workbook_text/`; a Data Model pivot (Distinct Count) only in memory; refused:
  two values across a Column field, label, date and "greater than" value filters. **Open for the
  user:** six fixtures opened in Excel by hand, as the ticket lists. Merged 2026-11-19
  (9ee84ae3).
- [04 Formulas in code](issues/04-formulas-in-code.md): `workbook_formula_reader.py` (the
  parser, standard library only), `workbook_formulas.py` (file 11's rules by ID, `table_query`,
  `FUNCTIONS`, `Note`) and `workbook_hive.py` (`piece_roles`, `workbook_hive`, `hive_texts`,
  `map_text`); no public name; all 45 formula-only Excel tasks pass. M1 and I1 follow file 11;
  P11 and I1's last limits left for ticket 13. The seam for 05 and 06 is in its Answer.
  Merged 2026-11-19 (c6a9bf0d).
- [03 The reader reads PivotTables](issues/03-the-reader-reads-pivots.md): `Sheet.pivot_tables`
  a list of `PivotTable` (source, Row, Column, Value and Report filter fields, filters, slicers,
  totals shown, cells with their items and stored values); `Workbook.slicers`; the Order's
  `PIVOT_TABLE` and `RANGE` pieces, GETPIVOTDATA in a Table's formula reading a pivot; a Table
  named alone (`VLOOKUP(k, jobs, ...)`) now in the Order; `workbook_text.py` writes each
  `PivotTable "name"`. Merged 2026-11-19 (d7ad237a), with ticket 04 counting the list.
- [06 PivotTables in code](issues/06-pivots-in-code.md): `workbook_pivot_hive.py`; rule IDs PR1
  to PR5, PV1 to PV8, PC1 to PC3, PL1, PL2, PF1 to PF5, PG1, PG2, PS1 to PS4, PN1, PN2, PX1 to
  PX7, each a test and stated in the Answer for file 20; each total level shown its own final;
  every pivot fixture's finals give its stored cells; each Pivot filter's condition carries
  `/* Pivot filter: <kind> <field> */`; `pivot_table_names` for ticket 07 and
  `pivot_filters` (`ConvertedPivotFilter`, `field_values`) for ticket 08. Var and Varp written
  over STDDEV, as sqlglot writes VAR_SAMP as Hive's population VARIANCE (a fix of its own,
  proposed as a session). Merged 2026-11-19 (21d285ac).

## Not yet specified

- The new files' names in `sqlglot_composer/`, and the public name a user calls, if any, beyond
  `project.convert(files=[...])` taking an `.xlsx` (04, 07, 09).
- How `workbook_text.py` loads the reader by its path while the registry still holds every
  Toolbox file's imports (01).

## Out of scope

- A formula outside a Table, or one that reads by position (file 11's X1, round 2, Q3).
- A DAX measure, an OLAP source, "Show items with no data".
- Charts, conditional formatting and any other presentation.
- A Column field written wide by the conversion (a file 21 add-on).
- Checking against the warehouse's rows (the Workbook check is offline).
- Converting a workbook again after its tables are edited: the workbook is a one-time way in.
- Copilot files 11, 12 and 15 retired (the user keeps them).

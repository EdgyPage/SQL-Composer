You are standing in for Microsoft Copilot in a web chat. Use no tools: answer from what is written here and what you already know.

The user pasted this as their first message:

<<<
# Copilot files for sqlglot Composer 8.2: start here

**Read this file to choose the one Copilot file your task needs, then follow the steps below
in order.**

sqlglot Composer 8.2 writes Hive, the SQL of the user's warehouse, from Python. You build a Statement from Clause functions, such as
SELECT, FROM and WHERE, and the Toolbox writes its Hive and refuses one that would give a
wrong number or read too much. These files teach Microsoft Copilot to write that Python, so
you can ask it in plain words.

## Terms

- **Copilot file**: one of the files in this folder; each teaches Copilot one objective.
- **Statement**: one query, built in Python with `statement(...)`, that becomes one string of
  Hive.
- **Project**: your folder at work holding the Toolbox and your own code.
- **Table reference**: the file in your Project's references/ folder that describes one
  table: its columns and their types, its partitions and its Key.
- **Saved table**: a table in the warehouse that your own Statements write.
- **Refusal**: the Toolbox's message when it won't write a Statement's Hive.
- **Workflow**: the steps to one end goal, such as converting Hive, each a cell of the
  Workflow's notebook in admin/workflows/.

## Steps

1. **Choose the file.** Goal: the file that teaches Copilot your task. Action: find your
   task under Which file. Done when you have one file, or for an Excel workbook three, as
   the Decision rules say. Then step 2.
2. **Open a chat.** Goal: a chat holding nothing from another task. Action: open a new chat
   in Copilot. Done when the chat is empty. Then step 3.
3. **Load the file.** Goal: Copilot reads the file first. Action: paste the file as your
   first message, and send it. If a paste is cut short, attach the file instead. Done when
   Copilot has the file. Then step 4.
4. **Ask.** Goal: Copilot knows your tables. Action: say which tables to read: paste each
   one's Table reference, its file in your Project's references/ folder, or say its import
   line and columns, such as: `from references.ops__job_runs import job_runs` gives
   ops.job_runs: run_id bigint, job_id bigint, status string, dt string; partitioned by dt;
   Key run_id. Done when Copilot answers with code. Then step 5.
5. **Run it.** Goal: the code works in your notebook. Action: run what Copilot gives. Done
   when it runs. If the Toolbox refuses it, step 6.
6. **Fix a refusal.** Goal: code the Toolbox takes. Action: start a new chat with file 09,
   paste the code and the whole message, and ask for the fix. Done when Copilot answers
   with the fixed code. Then step 5.

## Decision rules

- If the Toolbox refused your code, load file 09.
- If your task is to convert an Excel workbook, attach files 15, 11 and 12 (or paste
  each as a message of its own), then attach the workbook and ask Copilot to convert
  it: a chat holds one file at a time, but for this one task.
- If you want a query of Hive someone else wrote as Toolbox code, load file 07. If you want
  their Hive made into Saved tables in your Project, end to end, load file 13.
- Otherwise, load the one file whose line under Which file names your task.
- If you want something else after a task, start a new chat with that task's file.

## Which file

- `01_imports_and_project.txt`: start a Project, import the Toolbox, your Table
  references and warehouse.py's query and execute, and run a Statement.
- `02_table_references.txt`: describe a table: add its Table reference, or write one by
  hand for a Saved table, with its columns, partitions and Key; check its Key.
- `03_build_a_statement.txt`: read rows: pick columns, filter, count, add up, group, sort,
  and build in steps with Derived tables.
- `04_joins.txt`: combine tables with JOIN, LEFT_JOIN and the others.
- `05_windows_and_subtotals.txt`: a rank or row number in each group, the latest row or top N
  of each group, the row before, running totals; subtotals; stacking Statements.
- `06_save_a_table.txt`: write a Saved table: its Table notebook's logic cell, with
  create(), rows(), preview() and write().
- `07_convert_hive.txt`: turn Hive someone else wrote into Toolbox code.
- `08_check_and_compare.txt`: compare a Statement with the Hive it replaces, check a Key, see
  what is left to do in the Project, follow lineage.
- `09_fix_a_refusal.txt`: fix code the Toolbox refused.
- `10_hand_written_hive_and_functions.txt`: labels from a lookup or a chain of if/else,
  Hive functions the Toolbox doesn't wrap, Hive written by hand, and upkeep of a table.
- `11_excel_formula_workbooks.txt`: each formula of a Formula workbook, an Excel workbook
  laid out as `formula_workbook.xlsx` shows, as Hive; loaded with files 15 and 12.
- `12_excel_power_query.txt`: the same workbook's Power Query, whole-column totals and Total
  Rows as Hive; loaded with files 15 and 11.
- `13_workflows.txt`: converting Hive and promoting it to prod, a whole job step by step,
  from its Workflow notebook in admin/workflows/.
- `14_workflows_new_tables_and_upkeep.txt`: a new Saved table, from a query or by hand,
  Table references, an upgrade, a change to a Saved table, each a whole job step by step.
- `15_excel_workbook_steps.txt`: turn a Formula workbook into Hive, step by step: which
  Tables and queries become which queries, and the reply; loaded with files 11 and 12.

## Fitting Copilot

- Copilot takes at most 8,000 characters at once, spaces and line breaks included, and each
  file fits.
- Edit a copy if you like, then count it from the download's top folder:
  `python copilot/count_characters.py my_copy.txt` says how many characters it holds and
  whether it fits.

## Self-check

- The chat is new, and its first message is the file your task's line names (for an Excel
  workbook, files 15, 11 and 12).
- Your question names each table to read, by its Table reference or its import line and
  columns.
- For a refusal, the new chat holds file 09, your code and the whole message.

>>>

Then asked:

Convert this workbook. Copilot files 15, 11 and 12 are attached, and the workbook is attached as text (daily_runs_formula.txt, from workbook_text.py). Please give the map, a Hive query for each final Table, and what to do next.

You replied: load 15_excel_workbook_steps.txt, 11_excel_formula_workbooks.txt and 12_excel_power_query.txt.

The user pasted 15_excel_workbook_steps.txt:

<<<
# Copilot file 15: an Excel workbook into Hive, step by step (sqlglot Composer 8.2)

**Follow the steps below in order, as written. Add no step, skip none, and reply in the shape
the Output section gives.**

Objective: turn the calculations of an Excel workbook the user attaches, or the text
`workbook_text.py` writes of it, into one Hive query per final, for the user's convert
Workflow to check and make Toolbox code of.
Load this file when the user attaches a workbook and asks for its calculations as Hive, with
file 11 (each formula's Hive) and file 12 (Power Query, whole-column totals and Total Rows).

## Terms

- **Table**: an Excel Table; the workbook shows each as `Excel Table "name"`, its headers and
  rows, and any Total Row.
- **Typed column**: a column whose cells hold values; a **formula column** holds formulas.
- **Query**: a Power Query; the workbook lists each after its sheets as `Power Query "name"`,
  its M below it. A query and the Table it loads are two things, even with one name. A
  query's name inside another query's M, as in `Table.Sort(owner_load, ...)`, is that query.
- **Sample**: a Table's typed rows are a sample of a database table of the Table's name,
  which holds more rows: read the table, never the sample.
- **Source**: a database table a final reads, `<database>.<table>`; a Table's typed columns
  are one, of the Table's name. **Step**: a Table or query a final reads, as a CTE. **Final**:
  a Table that gets a query of its own. The Decision rules give each piece its role.
- **Mark**: a formula converted where Excel and Hive can differ, named in the map (file 11).
- **Parameters**, **Keys**: the workbook's two settings Tables, read by step 4.

## Steps

1. **Read.** Goal: see all of the workbook. Action: list each `Excel Table` with its typed
   and formula columns and Total Row, each defined name, and each `Power Query` listed after
   the sheets, with what each reads: its line under `Order, each piece after every piece it
   reads:`, or else each Table and query its M or formulas name, and its loading query.
   Done when every `Excel Table` and `Power Query` is on your list with what it reads. Then
   step 2.
2. **Decide each role.** Goal: know what each piece becomes. Action: give each Table and each
   query its role by the Decision rules, one rule per piece, a query apart from its Table.
   Done when each listed piece has a role. Then step 3.
3. **Write the map.** Goal: the user sees each piece's role. Action: write the Output's map
   from steps 1 and 2. Done when the map names each piece on your list. Then step 4.
4. **Write each final's reads.** Goal: each final's query reads what its Table reads. Action:
   for each final, start its query: each source read as `<database>.<table>`, each step it
   reads as a CTE in it (`WITH name AS (...)`), each CTE after every CTE it reads. **A
   Table's typed columns are always read from `<database>.<table>`, never typed in**; only a
   summary's typed groups are typed in.
   Done when each final has its FROM and CTEs. Then step 5.
5. **Write each final's columns.** Goal: each column gives the workbook's values. Action:
   write the columns in the Table's order, each formula by file 11, each query step and
   total by file 12, each calculated one named with AS; read a Parameters value in as its
   value; match a value typed over a formula on its Keys row's columns. Done when each
   final's block is whole. Then step 6.
6. **Name what changed.** Goal: the user sees each change. Action: list each mark, each
   refusal (NULL in its place, with why), each thing left alone, and each `<...>` to fill
   in, by files 11 and 12. Done when each is in the map. Then step 7.
7. **Check.** Goal: a reply with nothing to fix. Action: go through the Self-check; fix any
   answer it finds wrong. Done when each check holds; then reply.

## Decision rules

- If a Table has only typed columns and no query loads it, it is a source, never a final.
- If a Table has a formula column and no query loads it: if another Table's formula or a
  query reads it, it is a step; if nothing else reads it, it is a final. Its own formula
  columns reading its own row don't count.
- If a Table's only typed columns are the ones its SUMIFS or COUNTIFS match on, it is a
  summary: its final query is a GROUP BY of the Table it reads, its typed rows kept.
- If a query's M names another query, the named query is a step: a CTE in each final that
  reads it, `WITH owner_load AS (...)`, never a read of `<database>.owner_load`.
- If a query loads a Table: if another Table's formula reads that Table, the Table is a step;
  if not, the Table is a final, its rows the query's.
- If a query loads nothing and nothing reads it, leave it out, and name it.
- If a Table has a Total Row, its Total Row is a final of its own, `<Table> (Total Row)`,
  with a column for each Total Row cell that holds a total, and no other column.
- Parameters and Keys are never a source, step or final.
- If pieces read each other in a loop, refuse each final in it, no block; name the loop.

## Output

Reply with these parts, in this order, and nothing else:

1. **Map**: Sources, Steps and Finals, each with its columns; then each value typed over a
   formula, each mark, each refusal, what was left alone, and each `<...>` to fill in.
2. **Hive**: a heading and one ```sql block per final, Total Rows included, nothing between.
3. **Next**: "Take out what you don't want, fill in each `<...>`, save each query as a .hql
   file named for its final, and run the convert Workflow on them as one batch (file 13). It
   writes and checks the Toolbox code."

## Examples

Table jobs (job_id, job_name), typed. Table job_runs (run_id, job_id, duration_mins) adds
job_name `=XLOOKUP([@job_id],jobs[job_id],jobs[job_name])`. Map: Sources jobs, job_runs (its typed
columns). Finals job_runs (run_id, job_id, duration_mins, job_name). jobs is a source only.

```sql
SELECT r.run_id, r.job_id, r.duration_mins, j.job_name
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

Query ok_runs keeps job_runs' SUCCESS rows and loads Table ok_runs; query ok_by_job reads query
ok_runs and loads Table ok_by_job. Map: Sources job_runs. Steps query ok_runs. Finals Table ok_runs and Table
ok_by_job: no formula reads either Table. Each final has its own block:

```sql
SELECT run_id, job_id, duration_mins FROM <database>.job_runs WHERE status = 'SUCCESS'
```

```sql
WITH ok_runs AS (
  SELECT run_id, job_id, duration_mins FROM <database>.job_runs WHERE status = 'SUCCESS'
)
SELECT job_id, COUNT(*) AS runs FROM ok_runs GROUP BY job_id
```

Table by_job (job_id typed; runs `=COUNTIFS(job_runs[job_id],[@job_id])`) with a Total Row
summing runs. Map: Sources job_runs. Finals by_job, a summary, and by_job (Total Row),
file 12's second example. by_job's typed job_ids, its groups, are typed in:

```sql
SELECT j.job_id, COALESCE(c.runs, 0) AS runs
FROM (SELECT 1 AS job_id UNION ALL SELECT 2) j
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) c
  ON j.job_id = c.job_id
```

## Self-check

- Each `Excel Table` and `Power Query` the workbook lists has a role in the map.
- Each final, Total Rows included, has its own ```sql block; no block is a step alone.
- Each final's columns are its Table's, in order; a refused one is `NULL AS` its header.
- Each source and each Table's typed columns are read from `<database>.<table>`; the only
  rows typed in are a summary's groups.
- Each Total Row's block has a column only for each cell that holds a total.
- Each step a final reads is a CTE inside that final's block, after each CTE it reads.
- Each value typed over a formula is in a CASE, matched on its Keys row's columns.
- Each mark, refusal, thing left alone and `<...>` is named in the map.

>>>

The user pasted 11_excel_formula_workbooks.txt:

<<<
# Copilot file 11: each Excel formula's Hive (sqlglot Composer 8.2)

**Use this file as reference while you follow file 15's steps: it says what each formula of
an attached workbook becomes in Hive.**

Objective: write each formula of an Excel workbook as the Hive that gives the same values.
Load this file when the user attaches a workbook and asks for its calculations as Hive, with
file 15 (the steps, the map and the reply) and file 12 (Power Query and totals).

## Terms

- **Formula column**: a Table column whose cells hold a formula, such as `=[@duration_mins]/60`.
- `[@units]`, `[@[Unit Price]]` and `sales[[#This Row],[units]]` name a column of the same
  row; `sales[units]` the whole column. `_xlfn.` is only Excel's prefix: read past it.
- **Mark**: a formula converted where Excel and Hive can differ, named in the map.
- **Refused**: a formula with no Hive here: `NULL AS` its header, named in the map with why.

## Names in the Hive

- Write the database as `<database>`.
- Keep a Table name or header that is a plain name (letters, digits, `_`) as it is.
- Write any other in snake case in brackets: header `Unit Price` is `<unit_price>`, Table
  `Sales Data` is `<database>.<sales_data>`, each a `<...>` for the user to fill in.

## Formulas

- `+ - * /` as they are; `^` POWER; `&` CONCAT(a, b); TRUE, FALSE as they are.
- AND(a, b, c): `a AND b AND c`; OR(a, b): `(a OR b)`, bracketed, as AND joins before OR;
  NOT(x): `NOT x`. Hive has no AND() or OR() function: IF(AND(a, b), 1, 0) is
  IF(a AND b, 1, 0).
- IF as it is. IFS(c1, v1, c2, v2): `CASE WHEN c1 THEN v1 WHEN c2 THEN v2 END`.
  SWITCH(x, "a", 1, 0): `CASE x WHEN 'a' THEN 1 ELSE 0 END`.
- IFERROR(a / b, 0): COALESCE(a / b, 0), as a divide by 0 is NULL; IFNA(x, v) and
  XLOOKUP's fourth argument, v: COALESCE(x, v). ISBLANK(x): x IS NULL.
- ROUND, ABS, POWER, SQRT as they are; MOD(a, b): PMOD(a, b); INT: FLOOR; MIN(a, b) and
  MAX(a, b) of one row's cells: LEAST and GREATEST.
- LEFT(x, n): SUBSTR(x, 1, n); RIGHT(x, n): SUBSTR(x, -n); MID(x, s, n): SUBSTR(x, s, n);
  LEN: LENGTH; FIND(a, x): INSTR(x, a); SEARCH(a, x): INSTR(LOWER(x), LOWER(a));
  ISNUMBER(FIND(..)): INSTR(..) > 0; SUBSTITUTE: REPLACE; PROPER: INITCAP; CONCATENATE:
  CONCAT; TEXTJOIN(",", TRUE, a, b): CONCAT_WS(',', a, b); VALUE(x): CAST(x AS DOUBLE);
  UPPER, LOWER, TRIM as they are.
- YEAR, MONTH, DAY as they are; DATE(2026,9,1): '2026-09-01'; TODAY(): CURRENT_DATE;
  d + n, d - n: DATE_ADD(d, n), DATE_SUB(d, n); DATEDIF(a, b, "d"):
  DATEDIFF(b, a), "m": FLOOR(MONTHS_BETWEEN(b, a)), "y": FLOOR(MONTHS_BETWEEN(b, a) / 12);
  EOMONTH(d, 0): LAST_DAY(d); EDATE(d, n): ADD_MONTHS(d, n), marked: a month's end stays
  one; WEEKDAY(d): DAYOFWEEK(d); TEXT(d, "yyyy-mm"): DATE_FORMAT(d, 'yyyy-MM').
- The first of d's month, DATE(YEAR(d), MONTH(d), 1) or EOMONTH(d, -1)+1:
  `CAST(TRUNC(d, 'MM') AS STRING)`. The Monday of d's week, d-WEEKDAY(d,2)+1:
  `CAST(NEXT_DAY(DATE_ADD(d, 7 * -1), 'MO') AS STRING)`.
- XLOOKUP(k, t[a], t[b]), VLOOKUP(k, t, n, FALSE), INDEX(t[b], MATCH(k, t[a], 0)):
  `LEFT JOIN t ON k = t.a`, then t.b. XLOOKUP("rate", Parameters[name], Parameters[value]):
  its value, typed in.
- SUMIFS(t[v], t[a], [@a], t[s], "x") over its own Table: `SUM(CASE WHEN s = 'x' THEN v
  END) OVER (PARTITION BY a)`. Over another Table: LEFT JOIN `(SELECT a, SUM(v) AS total
  FROM t WHERE s = 'x' GROUP BY a)`. Either way COALESCE(.., 0), as Excel gives 0 where
  nothing matches. COUNTIFS: COUNT(*), MAXIFS: MAX, MINIFS: MIN, each with COALESCE too;
  AVERAGEIFS: AVG, left NULL. SUMIF and AVERAGEIF(t[a], [@a], t[v]), COUNTIF(t[a], [@a]):
  the -IFS form, one match.
- RANK.EQ(x, t[x]) or RANK: `RANK() OVER (ORDER BY x DESC)`; with 1 as a third argument, ASC.

## Conditions in an -IF(S) form

- "x": `s = 'x'`; ">10", ">=", "<", "<=": that comparison; "<>x": `(s <> 'x' OR s IS NULL)`,
  as Excel counts a blank there; "<>" alone: `s IS NOT NULL`; ">="&[@d]: against this row's d.
- Every condition of one -IFS form holds at once: join them with AND, two on one column too
  (">10" and "<=30": `v > 10 AND v <= 30`). If two -IFS forms are added that differ in one
  value only, then that value is an OR: write one, with `s IN ('x', 'y')`.
- SUMPRODUCT over conditions: `*` between them is AND; `+` is OR where both can't hold at
  once, such as two values of one column, or written `((..)+(..)>0)`.
  SUMPRODUCT((t[s]="x")*(t[v]>5)*t[v]): `SUM(CASE WHEN s = 'x' AND v > 5 THEN v ELSE 0
  END)`; with no column to add, as `(..)*1`: `COUNT(CASE WHEN .. THEN 1 END)`. If it reads
  its own Table, then add OVER (), as each row shows the same total.
- A wildcard, "*ail*" or "f*": `LOWER(s) LIKE '%ail%'`, `'f%'`, as Excel ignores case.
- `t[d], "<="&[@d]` over its own Table is a running total, ties included as Excel's: `SUM(v)
  OVER (PARTITION BY a ORDER BY d RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`;
  COUNTIFS the same with COUNT(*). COUNTIFS(t[a], [@a], t[v], ">"&[@v])+1: `RANK() OVER
  (PARTITION BY a ORDER BY v DESC)`; with "<", ASC.

## A value typed over a formula

- Write it as a CASE on its row: `CASE WHEN run_id = 103 THEN 9 ELSE duration_mins / 60 END`,
  matching the row on the columns its Keys row names.
- If no Keys row names that Table, match every typed column of the row, and say there is no
  Keys row.

## Marks: convert, and name

- A blank cell: Excel reads it as 0 or "", Hive as NULL. Where the sample has a blank in a
  column a formula reads, write COALESCE(x, 0) or COALESCE(x, ''), and name the mark
  "blank". Inside an -IF(S) form or ISBLANK, write the column as it is: they skip a blank,
  as SUM, AVG, MIN and MAX skip NULL.
- VLOOKUP or MATCH with TRUE or 1 is approximate: write it as the exact match, and name it.
- A date held as text, such as 20260911: `CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2),
  '-', SUBSTR(dt, 7, 2))`, and name it.
- A defined name for a cell outside a Table: write its value, and say to move it into
  Parameters.

## Refused: NULL in its place, and named

INDIRECT, OFFSET, RAND, RANDBETWEEN; a reference to a cell outside a Table that isn't a
defined name, named by its address, such as C2; a LAMBDA, or a defined name holding a formula;
a formula reading its own column (circular); ROW(), the row before, and anything else that
hangs on the order of a sheet's rows; MEDIAN; FILTER, UNIQUE, SORT and other spilled arrays;
NETWORKDAYS; any formula files 11 and 12 don't list.

Left alone, and named: charts, PivotTables, and cells outside a Table.

## Example

Table job_runs (run_id, job_id, duration_mins) adds hours `=[@duration_mins]/60`, typed over
as 9 where run_id is 103; Keys holds job_runs, run_id. Map: Sources job_runs. Finals job_runs
(run_id, job_id, duration_mins, hours). Typed over: hours where run_id is 103.

```sql
SELECT run_id, job_id, duration_mins,
  CASE WHEN run_id = 103 THEN 9 ELSE duration_mins / 60 END AS hours
FROM <database>.job_runs
```

## Self-check

- Each formula column is in its final's SELECT, by this file, or `NULL AS` its header.
- Each value typed over a formula is a CASE matched on its Keys row's columns.
- Each COALESCE this file asks for is there, and each mark is named.
- No AND(, OR( or NOT( is left in the Hive: each is written `a AND b`, `(a OR b)`, `NOT x`.

>>>

The user pasted 12_excel_power_query.txt:

<<<
# Copilot file 12: Power Query, whole-column totals and Total Rows into Hive (sqlglot Composer 8.2)

**Use this file as reference while you follow file 15's steps: it says what each Power Query
step, whole-column total and Total Row of an attached workbook becomes in Hive.**

Objective: write each Power Query, each whole-column total and each Total Row of an Excel
workbook as the Hive that gives the same rows.
Load this file when the user attaches a workbook and asks for its calculations as Hive, with
file 15 (the steps, the map and the reply) and file 11 (each formula's Hive).

## Terms

- **M**: Power Query's language. A query is a `let` of named steps, each reading the one
  before; `in` names the step it gives. Read the steps in order.
- **Total Row**: the row Excel adds inside a Table's range, under its last row, each total a
  SUBTOTAL(...) over a column: the workbook shows it as the Table's `Total Row`. It is the
  Total Row, never a row of data.
- A query step no section here lists is refused: NULL for each column it makes, or the query
  left out, named with why.

## Reading a table and its rows

- `Excel.CurrentWorkbook(){[Name="t"]}[Content]` reads Table t, as `<database>.t`. Another
  query's name, as in `Table.Sort(q, ...)`, reads query q: a CTE, `WITH q AS (...)`, written
  after each CTE q reads, each read by the next: a query, then the Table it loads, then a
  formula column reading that Table. `#date(2026, 9, 1)`: '2026-09-01'.
- Table.SelectRows: WHERE; after a Table.Group, HAVING, repeating the aggregate. M's `<>`
  keeps a null, as Hive's doesn't: `(status <> 'TEST' OR status IS NULL)`. `[c] = null`:
  `c IS NULL`; `[c] <> null`: `c IS NOT NULL`.
- Text.Contains([c], "x"), Text.StartsWith, Text.EndsWith: `c LIKE '%x%'`, `'x%'`, `'%x'`,
  case kept, as M keeps it. `not`: NOT.
- List.Contains({1, 3}, [c]): `c IN (1, 3)`. List.Contains(u[k], [k]), a row whose k is in
  another table: `LEFT SEMI JOIN u ON u.k = t.k`; with `not`, the LeftAnti join below.
- Table.SelectColumns, RemoveColumns, RenameColumns: the SELECT list; TransformColumnTypes:
  nothing.
- Table.AddColumn: an expression AS its name, `if c then a else b` as IF(c, a, b).
  Table.TransformColumns(t, {{"c", Text.Upper}}): UPPER(c) AS c. Table.ReplaceValue(t, null,
  0, Replacer.ReplaceValue, {"c"}): COALESCE(c, 0) AS c.
- M's functions as their twins in file 11: Text.Upper, Text.Lower, Text.Trim, Text.Length;
  Text.Start(x, n): SUBSTR(x, 1, n); Text.End(x, n): SUBSTR(x, -n); Text.Middle(x, s, n):
  SUBSTR(x, s + 1, n), as M counts from 0; Text.Replace: REPLACE; Text.Proper: INITCAP;
  Text.Combine({a, b}, ","): CONCAT_WS(',', a, b); Number.Round: BROUND, as M rounds a half
  to even; Number.RoundDown, RoundUp: FLOOR, CEIL; Number.Abs: ABS; Number.Mod: PMOD;
  Date.Year, Date.Month, Date.Day; Date.AddDays: DATE_ADD; Date.AddMonths: ADD_MONTHS;
  Date.AddYears(d, n): ADD_MONTHS(d, 12 * n); Date.EndOfMonth: LAST_DAY;
  Date.StartOfMonth: `CAST(TRUNC(d, 'MM') AS STRING)`.

## Grouping, joining, stacking

- Table.Group: GROUP BY, Table.RowCount(_) as COUNT(*), List.Sum, List.Max, List.Min and
  List.Average as SUM, MAX, MIN and AVG, List.StandardDeviation as STDDEV_SAMP.
  List.Count(List.Distinct([c])): COUNT(DISTINCT c), which leaves out NULL where M counts it
  as a value: name it where c has a blank in the sample.
- NestedJoin then ExpandTableColumn, by JoinKind: LeftOuter: LEFT JOIN; Inner: JOIN;
  RightOuter: LEFT JOIN, the two tables swapped; FullOuter: FULL OUTER JOIN; LeftAnti: `LEFT
  JOIN u ON t.k = u.k WHERE u.k IS NULL`, t's columns only; RightAnti: the same, swapped.
  ExpandTableColumn's fourth argument, new names: AS.
- A NestedJoin on every column, its new column removed, in Table.Distinct: Inner is
  `INTERSECT`, LeftAnti is `EXCEPT`.
- Table.AddColumn(t, "u", each u), then expanded: `CROSS JOIN u`.
- Table.Combine: UNION ALL; inside Table.Distinct, UNION. Table.Distinct alone: SELECT
  DISTINCT.
- Table.Unpivot(t, {"a", "b"}, "measure", "amount") or UnpivotOtherColumns: one SELECT per
  column unpivoted, stacked with UNION ALL, `'a' AS measure, a AS amount`, each with `WHERE
  a IS NOT NULL`, as M drops a null there.

## A whole column, and the Total Row

- SUM(t[v]), AVERAGE, COUNT, COUNTA, MIN, MAX in a formula column: `SUM(v) OVER ()` and so on,
  COUNTA as COUNT(v); STDEV.S: STDDEV_SAMP; VAR.S: VAR_SAMP; SUMPRODUCT(t[a], t[b]):
  `SUM(a * b) OVER ()`.
- A Total Row is a final of its own, `<Table> (Total Row)`: one row, a column for each cell
  that holds a total, in the Table's order, and no column for a cell that is empty or a label
  such as "Total", reading the Table's final query as a CTE. SUBTOTAL(109, ...) is a SUM,
  101 AVG, 102 or 103 COUNT, 104 MAX, 105 MIN.
- If the user says no one needs a Total Row's total kept as a table, write no block for it,
  and name it in the map as left out.
- Write the Table's own final query without its Total Row, so it holds only its rows: a Saved
  table holds no Subtotal row.

## Sorting

- Table.Sort then FirstN: ORDER BY ... LIMIT, Order.Descending as DESC. FirstN alone: LIMIT.
- Table.AddIndexColumn(t, "n", 1, 1) after a Table.Sort: `ROW_NUMBER() OVER (ORDER BY ...)
  AS n`; inside a Table.Group's `each`, PARTITION BY its keys.
- A Table.Sort with no FirstN or index after it: write no ORDER BY, as a Hive table holds no
  order, and name the order as dropped.

## Marks: convert, and name

- M reading Sql.Database or a source outside the workbook: read the table it names, and name
  it, for the user to check.
- Table.Pivot: a `SUM(CASE WHEN severity = 'high' THEN 1 END) AS high` column per value in
  the sample, THEN 1 to count and THEN v to add up v, NULL where none, as M leaves it; name
  the pivot's columns as now fixed.

## Refused, and named

Web.Contents or any web source (leave that query out); Table.AddIndexColumn with no Sort
before it; Table.FillDown and FillUp; Table.Distinct with a column list; List.Median.

## Examples

Table job_runs (run_id, job_id, status, duration_mins); query busy_jobs loads Table busy_jobs:

    let
        Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Ok = Table.SelectRows(Source, each [status] <> null
            and Text.StartsWith([status], "SUCC")),
        Grouped = Table.Group(Ok, {"job_id"}, {{"runs", each Table.RowCount(_), Int64.Type}}),
        Busy = Table.SelectRows(Grouped, each [runs] > 1)
    in
        Busy

Map: Sources job_runs. Finals busy_jobs (job_id, runs).

```sql
SELECT job_id, COUNT(*) AS runs
FROM <database>.job_runs
WHERE status IS NOT NULL AND status LIKE 'SUCC%'
GROUP BY job_id
HAVING COUNT(*) > 1
```

Table by_job (job_id typed; runs `=COUNTIFS(job_runs[job_id],[@job_id])`) has a Total Row
summing runs. As a summary, its typed job_ids, 1 and 2, are typed in (file 15). Its Total
Row's block reads by_job's final query as a CTE:

```sql
WITH by_job AS (
  SELECT j.job_id, COALESCE(c.runs, 0) AS runs
  FROM (SELECT 1 AS job_id UNION ALL SELECT 2) j
  LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) c
    ON j.job_id = c.job_id
)
SELECT SUM(runs) AS runs FROM by_job
```

## Self-check

- Each query's steps are read in order, each in its final's query or named as refused.
- Each ORDER BY has a LIMIT after it.
- Each Total Row is its own final, and its Table's final holds only the Table's rows.

>>>

The user attached daily_runs_formula.txt:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
  D1: Parameters: the fixed values your formulas use, one row per value. Put its name under name and the value under value, such as tax_rate and 0.2 (a plain number, not 20%), then read it by name in a formula: XLOOKUP("tax_rate", Parameters[name], Parameters[value]). Leave the Table empty if no formula uses a fixed value. See step 6 on the Steps sheet.
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
  D1: Keys: only for a Table where a value was typed over a formula. Add one row for that Table, however many values were typed over in it: the Table's name under table, and under key_columns the typed column or columns that tell its rows apart, separated by commas, such as job_runs with run_id, or sales with region, month. Copilot uses them to find the row a typed value belongs to. If no column tells the rows apart, leave the Table out. A Table with no value typed over a formula needs no row here. See step 10 on the Steps sheet.
Sheet "job_runs"
  Excel Table "job_runs", A2:F11
    Headers: run_id | job_id | status | duration_mins | avg_retry_secs | dt
    Row 2: 95 | 1 | SUCCESS | 12 | 2 | 2026-09-23
    Row 3: 96 | 2 | SUCCESS | 18 | 0 | 2026-09-23
    Row 4: 97 | 3 | FAILED | 30 | 8 | 2026-09-23
    Row 5: 98 | 2 |  | 15 |  | 2026-09-23
    Row 6: 99 | 1 | TEST | 5 | 0 | 2026-09-23
    Row 7: 101 | 1 | SUCCESS | 10 | 1 | 2026-09-24
    Row 8: 102 | 2 | FAILED | 20 | 6 | 2026-09-24
    Row 9: 103 | 3 | SUCCESS | 30 | 0 | 2026-09-24
    Row 10: 104 | 1 | SUCCESS | 40 | 3 | 2026-09-24
  A1: Copied from ops.job_runs in our warehouse.
Sheet "Clean"
  Excel Table "CleanRuns", A1:F8, loaded by Power Query "CleanRuns"
    Headers: run_id | job_id | status | duration_mins | avg_retry_secs | dt
    Row 2: 95 | 1 | SUCCESS | 12 | 2 | 2026-09-23
    Row 3: 96 | 2 | SUCCESS | 18 | 0 | 2026-09-23
    Row 4: 97 | 3 | FAILED | 30 | 8 | 2026-09-23
    Row 5: 101 | 1 | SUCCESS | 10 | 1 | 2026-09-24
    Row 6: 102 | 2 | FAILED | 20 | 6 | 2026-09-24
    Row 7: 103 | 3 | SUCCESS | 30 | 0 | 2026-09-24
    Row 8: 104 | 1 | SUCCESS | 40 | 3 | 2026-09-24
  H1: Loaded by the Power Query "CleanRuns" from job_runs: runs with no status, and test runs, left out.
Sheet "Power Query"
  A1: This workbook's Power Query, which the tool that made this file can't add to it, so the Table CleanRuns on the Clean sheet holds the rows the query gives, typed in. To see the workbook as it should be, add the query in Excel: Data > Get Data > From Other Sources > Blank Query, Home > Advanced Editor, paste its M below, and name it CleanRuns. Then delete the typed-in Table on Clean, and Home > Close & Load To > Table, at A1 of Clean.
Sheet "Daily"
  Excel Table "daily", A1:C4
    Headers: dt | runs | total_duration_mins
    Row 2: 2026-09-23 | =COUNTIFS(CleanRuns[dt],[@dt]) | =SUMIFS(CleanRuns[duration_mins],CleanRuns[dt],[@dt])
    Row 3: 2026-09-24 | =COUNTIFS(CleanRuns[dt],[@dt]) | =SUMIFS(CleanRuns[duration_mins],CleanRuns[dt],[@dt])
    Total Row: Total | =SUBTOTAL(109,daily[runs]) | =SUBTOTAL(109,daily[total_duration_mins])
  E1: One row per day of the clean runs, and a Total Row.
Power Query "CleanRuns" (loads into Excel Table "CleanRuns"):
    let
        Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Typed = Table.TransformColumnTypes(Source, {{"run_id", Int64.Type}, {"job_id", Int64.Type},
            {"status", type text}, {"duration_mins", Int64.Type}, {"dt", type text}}),
        Kept = Table.SelectRows(Typed, each [status] <> null and [status] <> "TEST")
    in
        Kept
Order, each piece after every piece it reads:
  1. Excel Table "Parameters"
  2. Excel Table "Keys"
  3. Excel Table "job_runs"
  4. Power Query "CleanRuns", reads Excel Table "job_runs"
  5. Excel Table "CleanRuns", loaded by Power Query "CleanRuns"
  6. Excel Table "daily", its formulas read Excel Table "CleanRuns"
Each final's query reads the steps it needs as CTEs in this order, each CTE after every CTE it reads.
>>>

Answer the user's question as you would in that chat, with any code in a ```python block and any SQL in a ```sql block.
Write your reply under one heading, `## Q1`.

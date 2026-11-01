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

Convert this workbook.

You replied: load 15_excel_workbook_steps.txt, 11_excel_formula_workbooks.txt and 12_excel_power_query.txt.

The user pasted 15_excel_workbook_steps.txt:

<<<
# Copilot file 15: an Excel workbook into Hive, step by step (sqlglot Composer 8.2)

**Follow the steps below in order, as written. Add no step, skip none, and reply in the shape
the Output section gives.**

Objective: turn the calculations of an Excel workbook the user attaches into one Hive query
per final, for the user's convert Workflow to check and make Toolbox code of.
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
   the sheets. Done when every `Excel Table` and `Power Query` in the workbook is on your list.
   Then step 2.
2. **Decide each role.** Goal: know what each piece becomes. Action: give each Table and each
   query its role by the Decision rules, one rule per piece, a query apart from its Table.
   Done when each listed piece has a role. Then step 3.
3. **Write the map.** Goal: the user sees each piece's role. Action: write the Output's map
   from steps 1 and 2. Done when the map names each piece on your list. Then step 4.
4. **Write each final's reads.** Goal: each final's query reads what its Table reads. Action:
   for each final, start its query: each source read as `<database>.<table>`, each step it
   reads as a CTE in it (`WITH name AS (...)`). **A Table's typed columns are always read
   from `<database>.<table>`, never typed in**; only a summary's typed groups are typed in.
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
summing runs. Map: Sources job_runs. Finals by_job, a summary, and by_job (Total Row). As a
summary, by_job's typed job_ids, its groups, are typed in; job_runs is read:

```sql
SELECT j.job_id, COALESCE(c.runs, 0) AS runs
FROM (SELECT 1 AS job_id UNION ALL SELECT 2) j
LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM <database>.job_runs GROUP BY job_id) c
  ON j.job_id = c.job_id
```

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

- Each `Excel Table` and `Power Query` the workbook lists has a role in the map.
- Each final, Total Rows included, has its own ```sql block; no block is a step alone.
- Each final's columns are its Table's, in order; a refused one is `NULL AS` its header.
- Each source and each Table's typed columns are read from `<database>.<table>`; the only
  rows typed in are a summary's groups.
- Each Total Row's block has a column only for each cell that holds a total.
- Each step a final reads is a CTE inside that final's block.
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
  query's name, as in `Table.Sort(q, ...)`, reads query q: a CTE, `WITH q AS (...)`. `#date(2026, 9, 1)`:
  '2026-09-01'.
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
  such as "Total", reading the Table's final query as a CTE. SUBTOTAL(109,
  ...) is a SUM, 101 AVG, 102 or 103 COUNT, 104 MAX, 105 MIN.
- Write the Table's own final query without its Total Row, so it holds only its rows: a Saved
  table holds no Subtotal row.

## Order

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

## Example

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

## Self-check

- Each query's steps are read in order, each in its final's query or named as refused.
- Each ORDER BY has a LIMIT after it.
- Each Total Row is its own final, and its Table's final holds only the Table's rows.

>>>

The user attached team_report_formula.xlsx:

<<<
Sheet "Steps"
  A1: Formula workbook: how to fill it in
  A2: Copilot reads this workbook and writes Hive, the SQL your team's database runs, without anyone explaining what the workbook is for. Make a copy of this file for each piece of work, then do steps 1 to 12 below in order. Each step says its goal, what to do, and when it is done; go to the next step only then.
  A3: Words used here:
  A4: Table: an Excel Table, made with Ctrl+T, with a name and one header row. Copilot converts only what is inside a Table.
  A5: Raw data: the records the work starts from, as values, with no formula in them.
  A6: Calculation: a value worked out from others, by a formula or by a Power Query step.
  A7: Typed column: a column whose cells hold values someone typed, not formulas, such as run_id. Not the same as a typed-over value.
  A8: Typed-over value: a value someone typed into one row of a column that holds a formula, in place of the formula.
  A9: Copilot files: the numbered text files in the copilot folder this workbook came from. Loaded in a Copilot chat, they tell Copilot how to convert your workbook.
  A10: The Parameters and Keys sheets:
  A11: Parameters holds the fixed values your formulas use, such as a tax rate: one row each, its name under name and its value under value (step 6). Keys is only for a Table where a value was typed over a formula: it names the columns that tell that Table's rows apart, so Copilot can find the row the typed value belongs to (step 10). Both start empty: leave a sheet empty when no step asks you to fill it in.
  A12: Your data:
  A13: 1. Paste one table of raw data. Goal: a sample of the data the work starts from, as plain values. Action: paste a sample of one table of raw data on a sheet of its own, as values only (Home > Paste > Paste Values): one header row, one row per record, no blank rows, no merged cells. Paste only the columns that hold data; you rebuild the columns that hold formulas in step 4. Done when the sheet holds the header row and the sample's rows, and nothing else. Then step 2.
  A14: 2. Make it a named Table. Goal: a Table Copilot can read by name. Action: click inside the sample, press Ctrl+T and tick "My table has headers". Then set its name in Table Design > Table Name (on older Excel, Design under Table Tools), by the first of the three rules below that fits. Copilot keeps the names you give, and marks any it can't match to a database table for you to fill in. Done when the Table has its name. Then step 3.
  A15: If the data was already in a Table: keep that Table's name.
  A16: If you know the database table it comes from: use the part of its name after the dot, such as job_runs for ops.job_runs. Then right-click the row number of the header row, choose Insert to add a row above it, and type there where it came from, such as "Copied from ops.job_runs".
  A17: Otherwise: give it any name, with no spaces.
  A18: 3. Repeat for each table of raw data. Goal: all the raw data in Tables. Action: do steps 1 and 2 for every other table of raw data the work starts from. Done when each one is a named Table on a sheet of its own. Then step 4.
  A19: Your calculations:
  A20: 4. Add each calculation on a row as a column. Goal: each calculation written once, by column name. Action: add a column to a Table for each calculation, and write its formula once, in the first row. Click a cell in the same row rather than typing its address, and Excel writes it by column name, such as =[@units]*[@price]. Excel fills the formula down the column. If you see it written as =sales[[#This Row],[units]]*sales[[#This Row],[price]], it is the same formula. Done when each calculation on a Table's own row has its column. Then step 5.
  A21: 5. Add each calculation that reads another Table, each summary and each total. Goal: every other calculation in a Table, by name. Action: write a calculation that reads another Table, such as an XLOOKUP or a SUMIFS, the same way, naming the other Table: =XLOOKUP([@product_id], products[product_id], products[name]). Rebuild a summary of totals, such as a block of SUMIFS cells or a PivotTable, as a Table of its own: a column for what it groups by, one row per group, and a column for each figure: SUMIFS for a total, COUNTIFS for a count, AVERAGEIFS for an average, MAXIFS for the largest, MINIFS for the smallest. To total any Table, raw or summary, turn on its Total Row (Table Design > Total Row) and pick each column's total from the list in its last row: Copilot reads a total typed as a row of its own as one more row of data. Done when each summary is a Table of its own and each total is in a Total Row. Then step 6.
  A22: 6. Move each fixed value into Parameters. Goal: every fixed value in one place, read by name. Action: add each fixed value a formula uses to the Parameters Table, one row per value, whether it was typed in a cell such as $B$3 or inside a formula such as *0.2, and change the formula to read it by name: =XLOOKUP("tax_rate", Parameters[name], Parameters[value]). Write a value as a plain number or text: 0.2, not 20%. Done when each formula reads its fixed values from Parameters. Then step 7.
  A23: 7. Use Power Query for a calculation, if you use Power Query. If you don't, go to step 8. Goal: a calculation done by Power Query in place of a formula. Action: Data > From Table/Range, make the changes in the Power Query Editor, then Close & Load to a new Table. Copilot reads its steps, and the new Table converts like any other. Done when each query you made is loaded to a Table. Then step 8.
  A24: 8. Write running totals with SUMIFS. Goal: formulas Copilot can read as SQL. Action: write a running total as =SUMIFS(t[v], t[d], "<="&[@d]), which Copilot can read. A formula that reads the row above, or a cell outside a Table, can't be read as SQL: Copilot names it and leaves its column empty for you to finish. Done when each running total is written with SUMIFS. Then step 9.
  A25: Before you hand it over:
  A26: 9. Take out what you don't want converted. Goal: only what you want converted left in a Table. Action: delete anything you don't want converted: a Table, or a column. Keep each typed-over value you want kept: step 10 is for those. Whatever is left in a Table converts. Done when each Table holds only what you want converted. Then step 10.
  A27: 10. Put back each typed-over value and name its Table in Keys. If no value was typed over a formula, go to step 11: a Table with no value typed over a formula needs no row in Keys. Goal: each typed-over value converted as it is, for its row. Action: find each in the original workbook (Ctrl+` shows formulas, so a typed value stands out) and type it over the formula in the same row here, making sure your sample holds that row. Then add one row to the Keys Table for that Table, however many values were typed over in it: the Table's name under table, and under key_columns the typed column or columns that tell its rows apart, separated by commas. For example, job_runs with run_id; or sales with region, month. If no column tells the rows apart, leave the Table out of Keys: Copilot then matches the row on all its typed columns. Done when each typed-over value is in its row here, and each Table that holds one has its row in Keys or has no column that tells its rows apart. Then step 11.
  A28: 11. Keep each calculation you want converted inside a Table. Goal: nothing you want converted left outside a Table. Action: move into a Table any calculation still outside one. Copilot leaves charts and anything outside a Table alone, and names them; titles and notes can stay. Done when every calculation you want converted is inside a Table. Then step 12.
  A29: 12. Hand it to Copilot. Goal: the Hive for your workbook. Action: go through the checks below, then save the workbook, attach it in a Copilot chat with Copilot files 15, 11 and 12 loaded, and ask Copilot to convert it. Done when Copilot replies with the Hive for your workbook.
  A30: Check before you attach it:
  A31: Each table of raw data is a named Table on a sheet of its own, with one header row.
  A32: Each calculation is a formula column in a Table, a Power Query loaded to a Table, a summary Table or a Total Row.
  A33: Each fixed value a formula uses is a row in Parameters, written as a plain number or text.
  A34: Each Table that holds a typed-over value has its row in Keys, or has no column that tells its rows apart.
  A35: Nothing you don't want converted is left in a Table.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2: None | None
  D1: Parameters: the fixed values your formulas use, one row per value. Put its name under name and the value under value, such as tax_rate and 0.2 (a plain number, not 20%), then read it by name in a formula: XLOOKUP("tax_rate", Parameters[name], Parameters[value]). Leave the Table empty if no formula uses a fixed value. See step 6 on the Steps sheet.
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2: None | None
  D1: Keys: only for a Table where a value was typed over a formula. Add one row for that Table, however many values were typed over in it: the Table's name under table, and under key_columns the typed column or columns that tell its rows apart, separated by commas, such as job_runs with run_id, or sales with region, month. Copilot uses them to find the row a typed value belongs to. If no column tells the rows apart, leave the Table out. A Table with no value typed over a formula needs no row here. See step 10 on the Steps sheet.
Sheet "Jobs"
  Excel Table "jobs", A2:D6
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
  A1: Copied from ops.jobs in our warehouse.
Sheet "Runs"
  Excel Table "job_runs", A2:G11
    Headers: run_id | job_id | status | duration_mins | avg_retry_secs | dt | team
    Row 2: 95 | 1 | SUCCESS | 12 | 2 | 2026-09-23 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])
    Row 3: 96 | 2 | SUCCESS | 18 | 0 | 2026-09-23 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])
    Row 4: 97 | 3 | FAILED | 30 | 8 | 2026-09-23 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])
    Row 5: 98 | 2 | None | 15 | None | 2026-09-23 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])
    Row 6: 99 | 1 | TEST | 5 | 0 | 2026-09-23 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])
    Row 7: 101 | 1 | SUCCESS | 10 | 1 | 2026-09-24 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])
    Row 8: 102 | 2 | FAILED | 20 | 6 | 2026-09-24 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])
    Row 9: 103 | 3 | SUCCESS | 30 | 0 | 2026-09-24 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])
    Row 10: 104 | 1 | SUCCESS | 40 | 3 | 2026-09-24 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])
  A1: Copied from ops.job_runs in our warehouse; team looked up from Jobs.
Sheet "Teams"
  Excel Table "teams", A2:C5
    Headers: team | runs | total_duration_mins
    Row 2: data | =COUNTIFS(job_runs[team],teams[[#This Row],[team]]) | =SUMIFS(job_runs[duration_mins],job_runs[team],teams[[#This Row],[team]])
    Row 3: finance | =COUNTIFS(job_runs[team],teams[[#This Row],[team]]) | =SUMIFS(job_runs[duration_mins],job_runs[team],teams[[#This Row],[team]])
    Row 4: web | =COUNTIFS(job_runs[team],teams[[#This Row],[team]]) | =SUMIFS(job_runs[duration_mins],job_runs[team],teams[[#This Row],[team]])
  A1: One row per team: its runs, and their minutes added up.
>>>

Answer the user's question as you would in that chat, with any code in a ```python block and any SQL in a ```sql block.
Write your reply under one heading, `## Q1`.

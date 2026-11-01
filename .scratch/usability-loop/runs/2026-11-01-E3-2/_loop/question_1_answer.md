You are standing in for Microsoft Copilot in a web chat. Use no tools: answer from what is written here and what you already know.

The user pasted this as their first message:

<<<
# Copilot files for sqlglot Composer 8.1: start here

sqlglot Composer 8.1 writes Hive, the SQL of the user's warehouse, from Python. You build a Statement from Clause functions, such as
SELECT, FROM and WHERE, and the Toolbox writes its Hive and refuses one that would give a
wrong number or read too much. These files teach Microsoft Copilot to write that Python, so
you can ask it in plain words.

## How to use them

1. Open a new chat in Copilot.
2. Paste the one file below that fits what you want to do, as your first message, and send
   it. If a paste is cut short, attach the file instead.
3. Then ask. Say which tables to read: paste each one's Table reference, its file in your
   Project's references/ folder, or say its import line and columns, such as:
   `from references.ops__job_runs import job_runs` gives ops.job_runs: run_id bigint,
   job_id bigint, status string, dt string; partitioned by dt; Key run_id.
4. Run what Copilot gives in your notebook. When the Toolbox refuses it, start a new chat
   with file 09, paste the code and the whole message, and ask for the fix.
5. For something else, start a new chat with that file. A chat holds one file at a time,
   but for one task: to convert an Excel workbook, attach files 03, 04, 05, 11 and 12 (or
   paste each as a message of its own), then attach the workbook and ask Copilot to
   convert it.

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
- `11_excel_formula_workbooks.txt`: turn a Formula workbook, an Excel workbook laid out as
  `formula_workbook.xlsx` shows, into Hive and Toolbox code: its steps and formulas.
- `12_excel_power_query.txt`: the same workbook's Power Query, whole-column totals and Total
  Rows, loaded with file 11.
- `13_workflows.txt`: converting Hive and promoting it to prod, a whole job step by step,
  from its Workflow notebook in admin/workflows/.
- `14_workflows_new_tables_and_upkeep.txt`: a new Saved table, from a query or by hand,
  Table references, an upgrade, a change to a Saved table, each a whole job step by step.

## Fitting Copilot

Copilot takes at most 8,000 characters at once, spaces and line breaks included, and each
file fits. Edit a copy if you like, then count it from the download's top folder:
`python copilot/count_characters.py my_copy.txt` says how many characters it holds and
whether it fits.

>>>

Then asked:

Please convert my_work/daily_runs_formula.xlsx into Hive with Copilot files 03, 04, 05, 11 and 12 loaded: give the map and one sql block per final, leaving <database> in angle brackets. Its CleanRuns Table is a Power Query, whose M is on the Power Query sheet; its final Daily has a Total Row.

You replied: load 11_excel_formula_workbooks.txt, 12_excel_power_query.txt, 03_build_a_statement.txt, 04_joins.txt and 05_windows_and_subtotals.txt.

The user pasted 11_excel_formula_workbooks.txt:

<<<
# Copilot file 11: a Formula workbook's formulas into Hive (sqlglot Composer 8.1)

Objective: turn an attached Excel workbook's calculations into Hive, a query per final
Table, then into Toolbox code.
Load this file when the user attaches a workbook and asks for its calculations as Hive or
Toolbox code, with file 12, for Power Query, whole columns and Total Rows, and files 03, 04
and 05, for the Toolbox code.

## Names for this objective, with their arguments

- first_match(cases, otherwise=None)
- week_start(column)
- month_start(column)

## Steps

1. Read every sheet: each Table (name, headers, rows, Total Row), formula, Power Query M,
   defined name, and the Parameters and Keys Tables. `[@units]`, `[@[Unit Price]]` and
   `sales[[#This Row],[units]]` name a column of the row, `sales[units]` the whole column;
   `_xlfn.` is only Excel's prefix.
2. Map it. A Table's typed columns, not loaded by a query, stand for a database table of the
   Table's name: a source. A Table whose only typed columns are what its SUMIFS or COUNTIFS
   match on (`[@job_id]` against `runs[job_id]`) is a summary: a GROUP BY of the Table it
   reads. A Table with formulas, or a query, that another Table or query reads is a step.
   A Table nothing reads is a final: one query each. Parameters and Keys are none.
3. Start the reply with the map: Sources, Steps, Finals and the columns each final gives;
   then each value typed over a formula, each mark, each refusal, what was left alone, and
   each `<...>` to fill in.
4. Names: write a database as `<database>`; keep a Table name or header that is a plain name
   (letters, digits, _); put any other in snake case in brackets: header `Unit Price` is
   `<unit_price>`, Table `Sales Data` `<database>.<sales_data>`.
5. Write each final's Hive in its own ```sql block: each source a table, read for the
   columns the finals use; each step a CTE inside each final's query that reads it, never a
   block alone; the final's columns in its Table's order, each
   calculated one named with AS. The rows are a sample: filter only as a formula or query
   does.
6. A value typed over a formula in one row converts too: `CASE WHEN run_id = 103 THEN 9
   ELSE duration_mins / 60 END`, matching the row on its Keys columns. With no Keys row for
   that Table, match every typed column of the row, and say there is no Keys row.
7. A refused formula: `NULL AS its_header`; name it in the map, with why, and a cell outside
   a Table it reads by its address, such as C2. Anything files 11 and 12 don't list is refused too.
8. Then Toolbox code in a ```python block, by files 03, 04 and 05, and tell the user: take
   out what you don't want; fill in each `<...>`; save each final's query as a .hql file
   named for its Table, and run the convert Workflow on them as one batch (file 13), DEV
   filled in; its checked code wins where the two differ.

## Formulas

- `+ - * /` as they are; `^` POWER; `&` CONCAT(a, b); TRUE, FALSE, AND, OR, NOT as they are.
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
- As month_start and week_start write them: DATE(YEAR(d), MONTH(d), 1) or EOMONTH(d, -1)+1:
  `CAST(TRUNC(d, 'MM') AS STRING)`; d-WEEKDAY(d,2)+1: `CAST(NEXT_DAY(DATE_ADD(d, 7 * -1),
  'MO') AS STRING)`.
- XLOOKUP(k, t[a], t[b]), VLOOKUP(k, t, n, FALSE), INDEX(t[b], MATCH(k, t[a], 0)):
  `LEFT JOIN t ON k = t.a`, then t.b. XLOOKUP("rate", Parameters[name], Parameters[value]):
  its value.
- SUMIFS(t[v], t[a], [@a], t[s], "x") over its own Table: `SUM(CASE WHEN s = 'x' THEN v
  END) OVER (PARTITION BY a)`. Over another Table: LEFT JOIN `(SELECT a, SUM(v) AS total
  FROM t WHERE s = 'x' GROUP BY a)`. Either way COALESCE(.., 0), as Excel gives 0 where
  nothing matches. COUNTIFS: COUNT(*), MAXIFS: MAX, MINIFS: MIN, each with COALESCE too;
  AVERAGEIFS: AVG, left NULL. SUMIF and AVERAGEIF(t[a], [@a], t[v]), COUNTIF(t[a], [@a]):
  the -IFS form, one match.
- RANK.EQ(x, t[x]) or RANK: `RANK() OVER (ORDER BY x DESC)`; with 1 as a third argument, ASC.

## Conditions in an -IF(S) form

- "x": `s = 'x'`; ">10", ">=", "<", "<=": that comparison; "<>x": `(s <> 'x' OR s IS NULL)`,
  as Excel counts a blank there; ">="&[@d]: against this row's d.
- A wildcard, "*ail*" or "f*": `LOWER(s) LIKE '%ail%'`, `'f%'`, as Excel ignores case.
- `t[d], "<="&[@d]` over its own Table is a running total, ties included as Excel's: `SUM(v)
  OVER (PARTITION BY a ORDER BY d RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`;
  COUNTIFS the same with COUNT(*). COUNTIFS(t[a], [@a], t[v], ">"&[@v])+1: `RANK() OVER
  (PARTITION BY a ORDER BY v DESC)`; with "<", ASC.

## Marks: convert, and say so

- A blank cell: Excel reads it as 0 or "", Hive as NULL. Where the sample has a blank in a
  column a formula reads, wrap it: COALESCE(x, 0), or COALESCE(x, ''); say "blank". Not
  inside an -IF(S) form, or ISBLANK: they skip a blank, as SUM, AVG, MIN and MAX skip NULL.
- VLOOKUP or MATCH with TRUE or 1 is approximate: convert it exactly, and say so.
- A date held as text, such as 20260911: `CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2),
  '-', SUBSTR(dt, 7, 2))`, and say the date is held as text.
- A defined name for a cell outside a Table: use its value, and say to move it into
  Parameters.

## Refused: NULL in its place, and named

INDIRECT, OFFSET, RAND, RANDBETWEEN; a reference to a cell outside a Table that isn't a
defined name; a LAMBDA, or a defined name holding a formula; a formula reading its own
column (circular); ROW(), the row before, and anything else that hangs on the order of a
sheet's rows; MEDIAN; FILTER, UNIQUE, SORT and other spilled arrays; NETWORKDAYS.

Left alone, and named: charts, PivotTables, and cells outside a Table.

## Worked example

Table job_runs (run_id, job_id, duration_mins) adds hours `=[@duration_mins]/60`, typed
over as 9 where run_id is 103, and job_name `=XLOOKUP([@job_id],jobs[job_id],jobs[job_name])`;
Table jobs (job_id, job_name); Keys holds job_runs, run_id.

Sources: job_runs, jobs. Finals: job_runs (run_id, job_id, duration_mins, hours, job_name).
Typed over: hours where run_id is 103. Fill in: `<database>`.

```sql
SELECT r.run_id, r.job_id, r.duration_mins,
  CASE WHEN r.run_id = 103 THEN 9 ELSE r.duration_mins / 60 END AS hours, j.job_name
FROM <database>.job_runs r
LEFT JOIN <database>.jobs j ON r.job_id = j.job_id
```

## Do and don't

- Do keep every final column in order, a refused one as NULL, and every row a final holds.
- Don't drop a value typed over a formula, filter to the sample's dates, or guess a name.

## Before you answer

- The map first, naming each source and final; a ```sql block per final, and per Total Row.
- Each `<...>`, mark and refusal named.

>>>

The user pasted 12_excel_power_query.txt:

<<<
# Copilot file 12: a Formula workbook's Power Query and totals into Hive (sqlglot Composer 8.1)

Objective: turn the Power Query M, whole-column totals and Total Rows in an attached Excel
workbook into Hive, with file 11.
Load this file when the user attaches a workbook and asks for its calculations as Hive or
Toolbox code, with files 11, 03, 04 and 05.

## Names for this objective, with their arguments

- SEMI_JOIN(table, ON=None, reads_all_partitions=False, broadcast=False)
- CROSS_JOIN(table, reads_all_partitions=False)
- rollup(*columns)
- row_number(*, PARTITION_BY=None, ORDER_BY=None, over=None)
- count_distinct(column, where=None)

## Steps

1. Follow file 11's steps, its map to its batch for the convert Workflow, reading each
   query's steps in order, as below.
2. A query another query reads is a step, a CTE as file 11's step 5 says. A query and the
   Table it loads are two things in the map, as a formula reads the Table, never the query:
   the Table, its query's rows and any formula columns it adds, is a step when a formula reads
   it, else a final. A connection-only query nothing reads is left out, and named.
3. A step this file and file 11 don't list is refused: NULL for each column it makes, or the
   query left out, and named, with why.

## Reading a table and its rows

- `Excel.CurrentWorkbook(){[Name="t"]}[Content]` reads Table t. `#date(2026, 9, 1)`:
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
  as a value: say so where c has a blank in the sample.
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

- SUM(t[v]), AVERAGE, COUNT, COUNTA, MIN, MAX: `SUM(v) OVER ()` and so on, COUNTA as
  COUNT(v); STDEV.S: STDDEV_SAMP; VAR.S: VAR_SAMP; SUMPRODUCT(t[a], t[b]): `SUM(a * b) OVER
  ()`.
- A Total Row, SUBTOTAL(109, ...) a SUM, 101 AVG, 102 or 103 COUNT, 104 MAX, 105 MIN: a
  query of its own, one row, a column per total, in order, with no label; name it in the map
  as `<Table> (Total Row)`.
- But a summary Table's Total Row whose totals only add up SUMs or COUNTs, or take the MAX of
  MAXes or MIN of MINs, needs no query of its own: the summary's query ends `GROUP BY a WITH
  ROLLUP`, which adds the total as one more row, its a NULL (a Subtotal row).

## Order

- Table.Sort then FirstN: ORDER BY ... LIMIT, Order.Descending as DESC. FirstN alone: LIMIT.
- Table.AddIndexColumn(t, "n", 1, 1) after a Table.Sort: `ROW_NUMBER() OVER (ORDER BY ...)
  AS n`; inside a Table.Group's `each`, PARTITION BY its keys.
- A Table.Sort with no FirstN or index after it: no ORDER BY, as a Hive table holds no
  order; say the order was dropped.

## Marks: convert, and say so

- M reading Sql.Database or a non-workbook source: use the table it names; say which to check.
- Table.Pivot: a `SUM(CASE WHEN severity = 'high' THEN 1 END) AS high` column per value in
  the sample, THEN 1 to count and THEN v to add up v, NULL where none, as M leaves it; say
  the pivot's columns are now fixed.

## Refused, and named

Web.Contents or any web source (leave that query out); Table.AddIndexColumn with no Sort
before it; Table.FillDown and FillUp; Table.Distinct with a column list; List.Median.

## Worked example

Table job_runs (run_id, job_id, status, duration_mins); query busy_jobs, loaded into Table
busy_jobs:

    let
        Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Ok = Table.SelectRows(Source, each [status] <> null
            and Text.StartsWith([status], "SUCC")),
        Grouped = Table.Group(Ok, {"job_id"}, {{"runs", each Table.RowCount(_), Int64.Type}}),
        Busy = Table.SelectRows(Grouped, each [runs] > 1)
    in
        Busy

Sources: job_runs. Finals: busy_jobs (job_id, runs). Fill in: `<database>`.

```sql
SELECT job_id, COUNT(*) AS runs
FROM <database>.job_runs
WHERE status IS NOT NULL AND status LIKE 'SUCC%'
GROUP BY job_id
HAVING COUNT(*) > 1
```

Toolbox code, with `<database>` as ops:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, HAVING, SELECT, WHERE, count_rows,
                              is_not_null, more_than, starts_with, statement)
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id, AS(count_rows(), "runs")),
    FROM(job_runs, reads_all_partitions=True),  # a workbook's query reads every row
    WHERE(is_not_null(job_runs.status), starts_with(job_runs.status, "SUCC")),
    GROUP_BY(job_runs.job_id),
    HAVING(more_than(count_rows(), 1)),
)
```

When query ok loads Table ok, which adds hours `=[@duration_mins]/60`, and query by_job reads
query ok: Steps: query ok. Finals: Table ok, with hours, and Table by_job, each holding `WITH
ok AS (...)`, Table ok's ending `SELECT ..., duration_mins / 60 AS hours FROM ok`.

A value typed over a formula, file 11's step 6, in Toolbox code: `AS(first_match([(equals(
r.run_id, 103), 9)], otherwise=r.duration_mins / 60), "hours")`, `r` being `AS(job_runs, "r")`.

## Do and don't

- Do read each query's steps in order, and a query another reads as a CTE.
- Don't keep an ORDER BY with no LIMIT, guess a source outside the workbook, or convert a
  web query.

## Before you answer

- Each query mapped: a step as a CTE, a loaded one as its final's query.
- Each mark and refusal named.

>>>

The user pasted 03_build_a_statement.txt:

<<<
# Copilot file 03: building a Statement (sqlglot Composer 8.1)

Objective: read rows with a Statement: pick columns, filter, count and add up, group, sort.
Load this file when the user asks for rows, counts, totals or a list from their tables.

You write Python for sqlglot Composer 8.1, a Toolbox that writes Hive. Answer with one Python code
block the user can paste into a notebook cell, then a few plain sentences.

## Always

1. Import each name you use, by name: `from sqlglot_composer import FROM, SELECT, statement`.
   Never `import *`. Use only the Toolbox names this file shows; never make one up. Hive's
   own words are Toolbox names only where this file writes them as functions, as SELECT and
   FROM: there is no COUNT, SUM, AND, CASE or ALIAS.
2. Build a Statement with `statement(...)`, its Clause functions in SQL order: a write's
   INSERT_OVERWRITE or INSERT_INTO first, then SELECT or SELECT_DISTINCT, FROM, the joins,
   WHERE, GROUP_BY, HAVING, ORDER_BY, LIMIT.
3. Name every calculation with AS: `AS(count_rows(), "runs")`. A plain column needs none.
   Arithmetic, `+ - * /`, works on Columns; comparisons don't (rule 4).
4. Write each Condition with a function: equals, not_equals, more_than, less_than,
   at_least, at_most, between, is_in, is_not_in, is_null, is_not_null, all_of, any_of. Never
   Python's ==, <, >, and, or, not on a Column. WHERE(a, b) keeps rows where both hold.
5. Bound every read of a partitioned table with a Condition giving a value for one of its
   partition columns, such as `equals(t.dt, "2026-09-24")`, `between(...)`, `is_in(...)` or
   `last_n_days(t.dt, 7)`: in WHERE for FROM, JOIN and CROSS_JOIN; inside ON= for LEFT_JOIN,
   SEMI_JOIN and ANTI_JOIN; for FULL_JOIN, in a Derived table it reads. Matching it to another
   table's column bounds nothing. A table with no partitions needs no bound.
6. ORDER_BY needs LIMIT.
7. Run a read with `run_query(s, query)` and a write with `run_execute(s, execute)`, after
   `from warehouse import query, execute`. Never call query or execute yourself.
8. Add an opt-out, such as `reads_all_partitions=True`, only when the user asks for what it
   allows, and say why in a comment.
9. Reach a column as `table.column`, from the user's Table reference:
   `from references.ops__job_runs import job_runs`, then `job_runs.dt`.
10. The user loads one Copilot file per chat, or for an Excel workbook 11 and 12 with 03,
    04 and 05. When this one doesn't cover what is asked, say so and name the file that
    does, to load in a new chat: 01 imports and the Project, 02 Table references, 03
    building a Statement, 04 joins, 05 windows and subtotals, 06 saving a table, 07
    converting Hive, 08 checking and comparing, 09 fixing a refusal, 10 labels, Hive
    functions and Hive written by hand, 11 and 12 an Excel workbook into Hive, 13 and 14 a
    whole job's steps from its Workflow notebook.

## Names for this objective, with their arguments

- statement(*clauses, returns_all_rows=False)
- SELECT(*columns)
- SELECT_DISTINCT(*columns)
- AS(expression, name)
- FROM(table, reads_all_partitions=False)
- WHERE(*conditions)
- GROUP_BY(*columns)
- HAVING(*conditions)
- ORDER_BY(*columns, sorts_everything=False)
- LIMIT(n)
- derived(name, statement)
- all_columns(t)
- equals(column, value)
- not_equals(column, value)
- more_than(column, value)
- less_than(column, value)
- at_least(column, value)
- at_most(column, value)
- between(column, low, high)
- last_n_days(column, n)
- is_in(column, values)
- is_not_in(column, values)
- is_null(column)
- is_not_null(column)
- contains(column, text)
- starts_with(column, text)
- all_of(*conditions)
- any_of(*conditions)
- count_rows(where=None, over=None)
- count_distinct(column, where=None)
- sum_of(column, where=None, adds_up=False, over=None)
- average_of(column, where=None, adds_up=False, over=None)
- min_of(column, where=None, over=None)
- max_of(column, where=None, over=None)
- if_else(condition, then, otherwise)
- fill_null(column, value)
- descending(column)

## Steps

1. `s = statement(SELECT(...), FROM(t), WHERE(...), GROUP_BY(...), HAVING(...),
   ORDER_BY(...), LIMIT(n))`, each clause only where needed, always in this order.
2. Columns: `t.status`. Every column of a table: `SELECT(*all_columns(t))`. A calculation
   needs a name: `AS(t.minutes / 60, "hours")`, `AS(count_rows(), "runs")`.
3. Dates are compared as the table holds them, such as "2026-09-24":
   `equals(t.dt, "2026-09-24")`, `between(t.dt, "2026-09-18", "2026-09-24")`, or
   `last_n_days(t.dt, 7)` for the 7 days before today.
4. Counting and adding up:
   - `count_rows()` counts rows; `count_rows(where=equals(t.status, "FAILED"))` counts
     only those; `count_distinct(t.job_id)` counts different values.
   - `sum_of(t.minutes)`, `average_of(...)`, `min_of(...)`, `max_of(...)`.
   - Every column in SELECT that isn't added up goes in GROUP_BY. A calculation is grouped by
     its AS name, written as text: `GROUP_BY(t.job_id, "hours")`.
   - HAVING tests a total: `HAVING(more_than(count_rows(), 3))`.
5. Labels: `if_else(condition, then, otherwise)`; NULL made a value: `fill_null(t.status,
   "running")`. More than two labels: file 10.
6. Sorting: `ORDER_BY(descending(t.minutes))` then `LIMIT(10)` for a top 10. To sort a whole
   result, sort the DataFrame in pandas: `run_query(s, query).sort_values("minutes")`.
7. In steps: `d = derived("d", statement(...))` makes a Derived table, read like a table:
   `FROM(d)`, `d.runs`. A Derived table holds no ORDER_BY. A step used in several notebooks
   goes in building_blocks/<name>.py as a function that returns the Derived table.

## Worked example

Each job's runs and total minutes on two days, the jobs with more than one run:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, HAVING, SELECT, WHERE, between,
                              count_rows, more_than, statement, sum_of)
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id, AS(count_rows(), "runs"),
           AS(sum_of(job_runs.duration_mins), "minutes")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
    GROUP_BY(job_runs.job_id),
    HAVING(more_than(count_rows(), 1)),
)
```

In two steps, a Derived table first:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, derived,
                              equals, is_in, statement)
from references.ops__job_events import job_events

ends = derived("ends", statement(
    SELECT(job_events.job_id, job_events.event_type),
    FROM(job_events),
    WHERE(equals(job_events.dt, "2026-09-24"), is_in(job_events.event_type, ["finish", "fail"])),
))
s = statement(
    SELECT(ends.event_type, AS(count_rows(), "events")),
    FROM(ends),
    GROUP_BY(ends.event_type),
)
```

## Do and don't

- Do bound a partitioned table on its partition column; don't read it whole unless the user
  asks for every day, then `FROM(t, reads_all_partitions=True)`.
- Do `count_rows()`; don't write COUNT(*). Do `sum_of(...)`; don't write SUM.
- Do `any_of(a, b)` for "a or b"; don't write `a or b`.
- Do `is_null(t.owner)`; don't write `equals(t.owner, None)`.
- Do `LIMIT` after `ORDER_BY`; don't sort without one.

## Before you answer

- The clauses are in SQL order inside one `statement(...)`.
- Each calculation has `AS`; each other SELECT column is in GROUP_BY when there is one.
- Each partitioned table is bounded; every name is imported.

>>>

The user pasted 04_joins.txt:

<<<
# Copilot file 04: joins (sqlglot Composer 8.1)

Objective: combine rows of two or more tables.
Load this file when the user asks for columns from several tables, rows with or without a
match in another table, or a count of matches.

You write Python for sqlglot Composer 8.1, a Toolbox that writes Hive. Answer with one Python code
block the user can paste into a notebook cell, then a few plain sentences.

## Always

1. Import each name you use, by name: `from sqlglot_composer import FROM, SELECT, statement`.
   Never `import *`. Use only the Toolbox names this file shows; never make one up. Hive's
   own words are Toolbox names only where this file writes them as functions, as SELECT and
   FROM: there is no COUNT, SUM, AND, CASE or ALIAS.
2. Build a Statement with `statement(...)`, its Clause functions in SQL order: a write's
   INSERT_OVERWRITE or INSERT_INTO first, then SELECT or SELECT_DISTINCT, FROM, the joins,
   WHERE, GROUP_BY, HAVING, ORDER_BY, LIMIT.
3. Name every calculation with AS: `AS(count_rows(), "runs")`. A plain column needs none.
   Arithmetic, `+ - * /`, works on Columns; comparisons don't (rule 4).
4. Write each Condition with a function: equals, not_equals, more_than, less_than,
   at_least, at_most, between, is_in, is_not_in, is_null, is_not_null, all_of, any_of. Never
   Python's ==, <, >, and, or, not on a Column. WHERE(a, b) keeps rows where both hold.
5. Bound every read of a partitioned table with a Condition giving a value for one of its
   partition columns, such as `equals(t.dt, "2026-09-24")`, `between(...)`, `is_in(...)` or
   `last_n_days(t.dt, 7)`: in WHERE for FROM, JOIN and CROSS_JOIN; inside ON= for LEFT_JOIN,
   SEMI_JOIN and ANTI_JOIN; for FULL_JOIN, in a Derived table it reads. Matching it to another
   table's column bounds nothing. A table with no partitions needs no bound.
6. ORDER_BY needs LIMIT.
7. Run a read with `run_query(s, query)` and a write with `run_execute(s, execute)`, after
   `from warehouse import query, execute`. Never call query or execute yourself.
8. Add an opt-out, such as `reads_all_partitions=True`, only when the user asks for what it
   allows, and say why in a comment.
9. Reach a column as `table.column`, from the user's Table reference:
   `from references.ops__job_runs import job_runs`, then `job_runs.dt`.
10. The user loads one Copilot file per chat, or for an Excel workbook 11 and 12 with 03,
    04 and 05. When this one doesn't cover what is asked, say so and name the file that
    does, to load in a new chat: 01 imports and the Project, 02 Table references, 03
    building a Statement, 04 joins, 05 windows and subtotals, 06 saving a table, 07
    converting Hive, 08 checking and comparing, 09 fixing a refusal, 10 labels, Hive
    functions and Hive written by hand, 11 and 12 an Excel workbook into Hive, 13 and 14 a
    whole job's steps from its Workflow notebook.

## Names for this objective, with their arguments

- JOIN(table, ON=None, many_matches=False, reads_all_partitions=False, broadcast=False)
- LEFT_JOIN(table, ON=None, keeps_only_matches=False, many_matches=False, reads_all_partitions=False, broadcast=False)
- FULL_JOIN(table, ON=None, keeps_only_matches=False, many_matches=False, reads_all_partitions=False)
- SEMI_JOIN(table, ON=None, reads_all_partitions=False, broadcast=False)
- ANTI_JOIN(table, ON=None, reads_all_partitions=False, broadcast=False)
- CROSS_JOIN(table, reads_all_partitions=False)
- AS(expression, name)
- all_of(*conditions)
- equals(column, value)
- count_distinct(column, where=None)
- count_rows(where=None, over=None)
- statement(*clauses, returns_all_rows=False)
- SELECT(*columns)
- FROM(table, reads_all_partitions=False)
- WHERE(*conditions)
- GROUP_BY(*columns)

## Steps

1. Each join comes after FROM: `JOIN(other, ON=equals(other.job_id, t.job_id))`. ON= takes a
   Condition; several, with `all_of(...)`.
2. Which join:
   - JOIN keeps the rows with a match in both.
   - LEFT_JOIN keeps every row of FROM's table, with NULL where `other` has no match.
   - FULL_JOIN keeps every row of both.
   - SEMI_JOIN keeps FROM's rows that have a match, each once, and gives no column of
     `other`; ANTI_JOIN keeps those that have none.
   - There is no RIGHT_JOIN: swap the two tables and use LEFT_JOIN.
   - Every row with every row is `CROSS_JOIN(other)`; a JOIN with no ON= is refused.
3. Partitions: each partitioned table needs its own bound on its partition column, with a
   value, not another table's column:
   - FROM and JOIN: in WHERE, `WHERE(equals(t.dt, day), equals(other.dt, day))`.
   - LEFT_JOIN, SEMI_JOIN and ANTI_JOIN: inside ON=,
     `ON=all_of(equals(other.job_id, t.job_id), equals(other.dt, day))`.
   - `equals(other.dt, t.dt)` matches rows but bounds nothing.
4. A WHERE on a LEFT_JOIN's table is refused: it would throw away the rows with no match.
   Put that Condition in ON= instead.
5. Join on the joined table's whole Key, as its Table reference gives it. Joined on less,
   one row can match many, and the Toolbox warns that counts and sums may come out too
   big. Then join a Derived table that has one row per value instead (file 03), or pass
   `many_matches=True` when the user says the repeats are wanted.
6. Counting matches after a LEFT_JOIN: `count_distinct(other.run_id)` gives 0 for a row
   with no match; `count_rows()` would give 1.
7. The same table twice, or two tables of one name: give one a second name,
   `o = AS(other, "o")`, then use `o.job_id`.
8. Only if the user asks: the opt-out `keeps_only_matches=True` lets WHERE test a
   LEFT_JOIN's table, so the join keeps only matched rows. `broadcast=True`, no opt-out,
   asks Hive to copy a small table to every worker, to join it faster.

## Worked example

Each run of a day with its job's name:

```python
from sqlglot_composer import FROM, JOIN, SELECT, WHERE, equals, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, jobs.job_name, job_runs.status),
    FROM(job_runs),
    JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    WHERE(equals(job_runs.dt, "2026-09-24")),
)
```

Every job, with how many runs the scheduler started for it that day, 0 for none:

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, all_of, count_distinct,
                              equals, statement)
from references.ops__jobs import jobs
from references.ops__scheduler_runs import scheduler_runs

s = statement(
    SELECT(jobs.job_id, AS(count_distinct(scheduler_runs.run_id), "runs")),
    FROM(jobs),
    LEFT_JOIN(scheduler_runs, ON=all_of(equals(scheduler_runs.job_id, jobs.job_id),
                                        equals(scheduler_runs.dt, "2026-09-24"))),
    GROUP_BY(jobs.job_id),
)
```

## Do and don't

- Do put a LEFT_JOIN table's Conditions in ON=; don't put them in WHERE.
- Do bound each partitioned table with a value; don't count `other.dt = t.dt` as a bound.
- Do `count_distinct(other.key)` to count matches; don't count rows after a LEFT_JOIN.
- Don't write RIGHT_JOIN, and don't leave ON= out.
- Don't add `many_matches=True` or `keeps_only_matches=True` unless the user asks for what it
  allows.

## Before you answer

- Every join has ON=, on the joined table's Key where it can.
- Every partitioned table, joined or not, has a bound with a value.
- No WHERE tests a LEFT_JOIN's table.

>>>

The user pasted 05_windows_and_subtotals.txt:

<<<
# Copilot file 05: windows, subtotals and stacking (sqlglot Composer 8.1)

Objective: work out a value from the rows around each row, keep the latest or top rows of
each group, add subtotals, or stack Statements.
Load this file when the user asks for a rank, a row number, the latest row of each group, a
top N per group, the row before or after, a running total, subtotals or a grand total, or
the rows of several Statements together.

You write Python for sqlglot Composer 8.1, a Toolbox that writes Hive. Answer with one Python code
block the user can paste into a notebook cell, then a few plain sentences.

## Always

1. Import each name you use, by name: `from sqlglot_composer import FROM, SELECT, statement`.
   Never `import *`. Use only the Toolbox names this file shows; never make one up. Hive's
   own words are Toolbox names only where this file writes them as functions, as SELECT and
   FROM: there is no COUNT, SUM, AND, CASE or ALIAS.
2. Build a Statement with `statement(...)`, its Clause functions in SQL order: a write's
   INSERT_OVERWRITE or INSERT_INTO first, then SELECT or SELECT_DISTINCT, FROM, the joins,
   WHERE, GROUP_BY, HAVING, ORDER_BY, LIMIT.
3. Name every calculation with AS: `AS(count_rows(), "runs")`. A plain column needs none.
   Arithmetic, `+ - * /`, works on Columns; comparisons don't (rule 4).
4. Write each Condition with a function: equals, not_equals, more_than, less_than,
   at_least, at_most, between, is_in, is_not_in, is_null, is_not_null, all_of, any_of. Never
   Python's ==, <, >, and, or, not on a Column. WHERE(a, b) keeps rows where both hold.
5. Bound every read of a partitioned table with a Condition giving a value for one of its
   partition columns, such as `equals(t.dt, "2026-09-24")`, `between(...)`, `is_in(...)` or
   `last_n_days(t.dt, 7)`: in WHERE for FROM, JOIN and CROSS_JOIN; inside ON= for LEFT_JOIN,
   SEMI_JOIN and ANTI_JOIN; for FULL_JOIN, in a Derived table it reads. Matching it to another
   table's column bounds nothing. A table with no partitions needs no bound.
6. ORDER_BY needs LIMIT.
7. Run a read with `run_query(s, query)` and a write with `run_execute(s, execute)`, after
   `from warehouse import query, execute`. Never call query or execute yourself.
8. Add an opt-out, such as `reads_all_partitions=True`, only when the user asks for what it
   allows, and say why in a comment.
9. Reach a column as `table.column`, from the user's Table reference:
   `from references.ops__job_runs import job_runs`, then `job_runs.dt`.
10. The user loads one Copilot file per chat, or for an Excel workbook 11 and 12 with 03,
    04 and 05. When this one doesn't cover what is asked, say so and name the file that
    does, to load in a new chat: 01 imports and the Project, 02 Table references, 03
    building a Statement, 04 joins, 05 windows and subtotals, 06 saving a table, 07
    converting Hive, 08 checking and comparing, 09 fixing a refusal, 10 labels, Hive
    functions and Hive written by hand, 11 and 12 an Excel workbook into Hive, 13 and 14 a
    whole job's steps from its Workflow notebook.

## Names for this objective, with their arguments

- window(PARTITION_BY=None, ORDER_BY=None, rows=None)
- at_most(column, value)
- row_number(*, PARTITION_BY=None, ORDER_BY=None, over=None)
- rank(*, over)
- dense_rank(*, over)
- ntile(parts, *, over)
- lag(column, *, over, back=1)
- lead(column, *, over, ahead=1)
- first_value(column, *, over)
- last_value(column, *, over)
- sum_of(column, where=None, adds_up=False, over=None)
- count_rows(where=None, over=None)
- descending(column)
- derived(name, statement)
- rollup(*columns)
- cube(*columns)
- grouping_sets(*sets)
- is_total(column)
- UNION_ALL(*statements, returns_all_rows=False)
- UNION(*statements, returns_all_rows=False)
- INTERSECT(*statements, returns_all_rows=False)
- EXCEPT(*statements, returns_all_rows=False)

## Steps

1. A Window says which rows each row looks across:
   `window(PARTITION_BY=t.job_id, ORDER_BY=t.run_id)`, the rows of each job, in order;
   several columns as lists; `descending(t.minutes)` for largest first.
   `rows=(-6, 0)` looks across the 6 rows before and the row itself; `rows=(None, 0)` every
   row up to it.
2. Pass it as `over=`: `rank(over=w)`, `dense_rank(over=w)`, `ntile(4, over=w)`,
   `lag(t.minutes, over=w)` (the row before), `lead(t.minutes, over=w)` (the row after),
   `first_value(...)`, `last_value(...)`, `sum_of(t.minutes, over=w)`,
   `count_rows(over=w)`. rank, lag and lead need ORDER_BY; a total with ORDER_BY needs
   rows=. `row_number(PARTITION_BY=..., ORDER_BY=...)` numbers rows 1, 2, 3 in each group.
3. Name each with AS, as any calculation.
4. A window's value can't be tested in the same Statement. Work it out in a Derived table,
   then keep rows in the Statement that reads it: the latest row of each group is the row
   numbered 1 from the newest; a top 3 keeps `at_most(d.n, 3)`, where `n` is the number's
   AS name.
5. Ties: add a second ORDER_BY column, such as the row's id, so the order is one.
6. Subtotals go inside GROUP_BY: `GROUP_BY(rollup(t.dt))` adds a total of every day;
   `cube(a, b)` every combination; `grouping_sets(...)` the sets named. `is_total(t.dt)`
   is a Condition true on a total's row.
7. Stacking: `UNION_ALL(s1, s2)` gives the rows of both, each Statement giving the same
   columns in the same order; `UNION` drops repeated rows; `INTERSECT` and `EXCEPT` as in
   SQL. Each Statement is bounded on its own.

## Worked example

The latest run of each job over two days:

```python
from sqlglot_composer import (AS, FROM, SELECT, WHERE, between, derived, descending, equals,
                              row_number, statement)
from references.ops__job_runs import job_runs

numbered = derived("numbered", statement(
    SELECT(job_runs.job_id, job_runs.run_id, job_runs.status,
           AS(row_number(PARTITION_BY=job_runs.job_id, ORDER_BY=descending(job_runs.run_id)),
              "newest_first")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
))
s = statement(
    SELECT(numbered.job_id, numbered.run_id, numbered.status),
    FROM(numbered),
    WHERE(equals(numbered.newest_first, 1)),
)
```

A running total of each job's minutes, in run order:

```python
from sqlglot_composer import AS, FROM, SELECT, WHERE, equals, statement, sum_of, window
from references.ops__job_runs import job_runs

each_job = window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.run_id, rows=(None, 0))
s = statement(
    SELECT(job_runs.job_id, job_runs.run_id,
           AS(sum_of(job_runs.duration_mins, over=each_job), "minutes_so_far")),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24")),
)
```

## Do and don't

- Do keep the latest row with row_number in a Derived table; don't use max_of on each
  column, which can mix values from different rows.
- Do give rank, lag and lead an ORDER_BY.
- Don't test a window's value in its own WHERE or HAVING.
- Don't add up a window's value again; the Toolbox refuses it.

## Before you answer

- Every window function has `over=` (or row_number its PARTITION_BY and ORDER_BY) and AS.
- Rows are kept by a window's value only in the Statement that reads its Derived table.
- Each Statement, stacked or not, is bounded on its partitions.

>>>

The user attached daily_runs_formula.xlsx:

<<<
Sheet "Steps"
  A1: Formula workbook: how to fill it in
  A2: Copilot reads this workbook and writes Hive, the SQL your team's database runs, without anyone explaining what the workbook is for. Make a copy of this file for each piece of work.
  A3: The Parameters and Keys sheets:
  A4: Parameters holds the fixed values your formulas use, such as a tax rate: one row each, its name under name and its value under value (step 6). Keys is only for a Table where a value was typed over a formula: it names the columns that tell that Table's rows apart, so Copilot can find the row the typed value belongs to (step 10). Both start empty, and stay empty if you need neither.
  A5: Your data:
  A6: 1. For each table of raw data the work starts from, paste a sample on a sheet of its own, as values only (Home > Paste > Paste Values): one header row, one row per record, no blank rows, no merged cells. Paste only the columns that hold data, not the ones that hold formulas: you rebuild those in step 4.
  A7: 2. Click inside it, press Ctrl+T and tick "My table has headers". If the data was already in a Table, keep that Table's name; if you know the database table it comes from, use that name. Otherwise any name will do, with no spaces (Table Design > Table Name; on older Excel, Design under Table Tools). Copilot keeps the names you give, and marks any it can't match to a database table for you to fill in.
  A8: 3. Do steps 1 and 2 for every table of raw data before going on.
  A9: Your calculations:
  A10: 4. Add a column to a Table for each calculation, and write its formula once, in the first row. Click a cell in the same row rather than typing its address, and Excel writes it by column name, such as =[@units]*[@price]. Excel fills the formula down the column.
  A11: 5. A calculation that reads another Table, such as an XLOOKUP or a SUMIFS, is written the same way, naming the other Table: =XLOOKUP([@product_id], products[product_id], products[name]). A summary of totals, such as a block of SUMIFS cells or a PivotTable, is rebuilt as a Table of its own: a column for what it groups by, one row per group, and a SUMIFS column for each figure.
  A12: 6. Move each fixed value a formula uses into the Parameters Table, one row per value, whether it was typed in a cell such as $B$3 or inside a formula such as *0.2, and change the formula to read it by name: =XLOOKUP("tax_rate", Parameters[name], Parameters[value]). Write a value as a plain number or text: 0.2, not 20%.
  A13: 7. Power Query, if you use it, can do a calculation instead of a formula: Data > From Table/Range, make the changes in the Power Query Editor, then Close & Load to a new Table. Copilot reads its steps, and the new Table converts like any other. Skip this step if you don't use Power Query.
  A14: 8. A formula that reads the row above, or a cell outside a Table, can't be read as SQL: Copilot names it and leaves its column empty for you to finish. Write a running total as =SUMIFS(t[v], t[d], "<="&[@d]), which Copilot can read.
  A15: Before you hand it over:
  A16: 9. Take out anything you don't want converted: a Table, a column, a value typed over a formula. Whatever is left in a Table converts.
  A17: 10. A value someone typed over a formula in one row is converted as it is, for that row. Find each in the original workbook (Ctrl+` shows formulas, so a typed value stands out) and type it over the formula in the same row here, making sure your sample holds that row. Then add one row to the Keys Table for that Table, however many values were typed over in it: the Table's name under table, and under key_columns the typed column or columns that tell its rows apart, separated by commas. For example, job_runs with run_id; or sales with region, month. If no column tells the rows apart, leave the Table out of Keys: Copilot then matches the row on all its typed columns. A Table with no value typed over a formula needs no row in Keys.
  A18: 11. Charts and anything outside a Table are left alone, and Copilot names them. Titles and notes can stay.
  A19: 12. Save the workbook, attach it in a Copilot chat with Copilot files 11 and 12 loaded (with files 03, 04 and 05), and ask Copilot to convert it.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    name | value
    None | None
  D1: Parameters: the fixed values your formulas use, one row per value. Put its name under name and the value under value, such as tax_rate and 0.2 (a plain number, not 20%), then read it by name in a formula: XLOOKUP("tax_rate", Parameters[name], Parameters[value]). Leave the Table empty if no formula uses a fixed value. See step 6 on the Steps sheet.
Sheet "Keys"
  Excel Table "Keys", A1:B2
    table | key_columns
    None | None
  D1: Keys: only for a Table where a value was typed over a formula. Add one row for that Table, however many values were typed over in it: the Table's name under table, and under key_columns the typed column or columns that tell its rows apart, separated by commas, such as job_runs with run_id, or sales with region, month. Copilot uses them to find the row a typed value belongs to. If no column tells the rows apart, leave the Table out. A Table with no value typed over a formula needs no row here. See step 10 on the Steps sheet.
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
    run_id | job_id | status | duration_mins | avg_retry_secs | dt
    95 | 1 | SUCCESS | 12 | 2 | 2026-09-23
    96 | 2 | SUCCESS | 18 | 0 | 2026-09-23
    97 | 3 | FAILED | 30 | 8 | 2026-09-23
    98 | 2 | None | 15 | None | 2026-09-23
    99 | 1 | TEST | 5 | 0 | 2026-09-23
    101 | 1 | SUCCESS | 10 | 1 | 2026-09-24
    102 | 2 | FAILED | 20 | 6 | 2026-09-24
    103 | 3 | SUCCESS | 30 | 0 | 2026-09-24
    104 | 1 | SUCCESS | 40 | 3 | 2026-09-24
  H1: Copied from ops.job_runs in our warehouse.
Sheet "CleanRuns"
  Excel Table "CleanRuns", A1:F8
    run_id | job_id | status | duration_mins | avg_retry_secs | dt
    95 | 1 | SUCCESS | 12 | 2 | 2026-09-23
    96 | 2 | SUCCESS | 18 | 0 | 2026-09-23
    97 | 3 | FAILED | 30 | 8 | 2026-09-23
    101 | 1 | SUCCESS | 10 | 1 | 2026-09-24
    102 | 2 | FAILED | 20 | 6 | 2026-09-24
    103 | 3 | SUCCESS | 30 | 0 | 2026-09-24
    104 | 1 | SUCCESS | 40 | 3 | 2026-09-24
  H1: Loaded by the Power Query "CleanRuns" from job_runs: runs with no status, and test runs, left out. See the Power Query sheet.
Sheet "Power Query"
  A1: This workbook's Power Query, which the tool that made this file can't save in it, so the Table CleanRuns on the sheet CleanRuns holds the rows the query gives, typed in. To see the workbook as it should be, add the query in Excel: Data > Get Data > From Other Sources > Blank Query, Home > Advanced Editor, paste its M below, and name it CleanRuns. On the sheet CleanRuns, delete the typed-in Table (select it and press Delete, then delete the empty Table), then Home > Close & Load To > Table, at A1 of that sheet. Its Source reads the Table job_runs on the sheet job_runs.
  A3: Query CleanRuns, loading into the Table CleanRuns:
  A4: let
    Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
    Typed = Table.TransformColumnTypes(Source, {{"run_id", Int64.Type}, {"job_id", Int64.Type},
        {"status", type text}, {"duration_mins", Int64.Type}, {"dt", type text}}),
    Kept = Table.SelectRows(Typed, each [status] <> null and [status] <> "TEST")
in
    Kept
Sheet "Daily"
  Excel Table "Daily", A1:C3
    dt | runs | total_duration_mins
    2026-09-23 | =COUNTIFS(CleanRuns[dt],Daily[[#This Row],[dt]]) | =SUMIFS(CleanRuns[duration_mins],CleanRuns[dt],Daily[[#This Row],[dt]])
    2026-09-24 | =COUNTIFS(CleanRuns[dt],Daily[[#This Row],[dt]]) | =SUMIFS(CleanRuns[duration_mins],CleanRuns[dt],Daily[[#This Row],[dt]])
  E1: One row per day of the clean runs, and a Total Row.
  A4: Total
  B4: =SUBTOTAL(109,Daily[runs])
  C4: =SUBTOTAL(109,Daily[total_duration_mins])
>>>

Answer the user's question as you would in that chat, with any code in a ```python block and any SQL in a ```sql block.
Write your reply under one heading, `## Q1`.

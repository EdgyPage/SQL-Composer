You are standing in for Microsoft Copilot in a web chat. Use no tools: answer from what is written here and what you already know.

Before asking anything, the user loaded these files:

<<<
# Copilot file 11: a Formula workbook's formulas into Hive (sqlglot Composer 7.2)

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
   `<unit_price>`, Table `Sales Data` `<database>.<sales_data>`. Never guess one.
5. Write each final's Hive in its own ```sql block: each source a table, read for the
   columns the finals use; each step a CTE inside each final's query that reads it, never a
   block alone; the final's columns in its Table's order, each
   calculated one named with AS. The rows are a sample: filter only as a formula or query
   does.
6. A value typed over a formula in one row converts too: `CASE WHEN run_id = 103 THEN 9
   ELSE duration_mins / 60 END`, matching the row on its Keys columns. With no Keys row for
   that Table, match every typed column of the row, and say there is no Keys row. A Table
   with no value typed over a formula needs none.
7. A refused formula: `NULL AS its_header`; name it in the map, with why, and a cell outside
   a Table it reads by its address, such as C2. Anything files 11 and 12 don't list is refused too.
8. Then Toolbox code in a ```python block, by files 03, 04 and 05, and tell the user: take
   out of the workbook what you don't want converted; fill in each `<...>`; run
   `project.convert` on the Hive; its checked code wins where the two differ.

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


# Copilot file 12: a Formula workbook's Power Query and totals into Hive (sqlglot Composer 7.2)

Objective: turn the Power Query M, whole-column totals and Total Rows in an attached Excel
workbook into Hive, with file 11.
Load this file when the user attaches a workbook and asks for its calculations as Hive or
Toolbox code, with file 11, which holds the steps, the map and the formulas, and files 03,
04 and 05.

## Names for this objective, with their arguments

- SEMI_JOIN(table, ON=None, reads_all_partitions=False, broadcast=False)
- CROSS_JOIN(table, reads_all_partitions=False)
- rollup(*columns)
- row_number(*, PARTITION_BY=None, ORDER_BY=None, over=None)
- count_distinct(column, where=None)

## Steps

1. Follow file 11's steps, reading each query's steps in order, as below.
2. A query another query reads is a step, a CTE as file 11's step 5 says. A query and the
   Table it loads are two things, as a formula reads the Table, never the query: the Table,
   its query's rows and any formula columns it adds, is a step when a formula reads it, else
   a final. A connection-only query nothing reads is left out, and named.
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
query ok: Steps: query ok. Finals: Table ok, with hours, and by_job, each a query holding `WITH
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


# Copilot file 03: building a Statement (sqlglot Composer 7.2)

Objective: read rows with a Statement: pick columns, filter, count and add up, group, sort.
Load this file when the user asks for rows, counts, totals or a list from their tables.

You write Python for sqlglot Composer 7.2, a Toolbox that writes Hive. Answer with one Python code
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
    functions and Hive written by hand, 11 and 12 an Excel workbook into Hive.

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


# Copilot file 04: joins (sqlglot Composer 7.2)

Objective: combine rows of two or more tables.
Load this file when the user asks for columns from several tables, rows with or without a
match in another table, or a count of matches.

You write Python for sqlglot Composer 7.2, a Toolbox that writes Hive. Answer with one Python code
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
    functions and Hive written by hand, 11 and 12 an Excel workbook into Hive.

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


# Copilot file 05: windows, subtotals and stacking (sqlglot Composer 7.2)

Objective: work out a value from the rows around each row, keep the latest or top rows of
each group, add subtotals, or stack Statements.
Load this file when the user asks for a rank, a row number, the latest row of each group, a
top N per group, the row before or after, a running total, subtotals or a grand total, or
the rows of several Statements together.

You write Python for sqlglot Composer 7.2, a Toolbox that writes Hive. Answer with one Python code
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
    functions and Hive written by hand, 11 and 12 an Excel workbook into Hive.

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

Each task below is a separate request the user sends next. Answer each as you would in that chat: reply with its `## X..` heading, then your answer, with SQL in ```sql blocks and any Python in ```python blocks.

## X41

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x41.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_runs"
  Excel Table "job_runs", A1:G10
    Headers: run_id | job_id | status | duration_mins | longest_first | shortest_ok | job_total
    Row 2: 95 | 1 | SUCCESS | 12 | =RANK.EQ([@duration_mins],job_runs[duration_mins]) | =MINIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[status],"SUCCESS") | =SUMIF(job_runs[job_id],[@job_id],job_runs[duration_mins])
    Row 3: 96 | 2 | SUCCESS | 18 | =RANK.EQ([@duration_mins],job_runs[duration_mins]) | =MINIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[status],"SUCCESS") | =SUMIF(job_runs[job_id],[@job_id],job_runs[duration_mins])
    Row 4: 97 | 3 | FAILED | 30 | =RANK.EQ([@duration_mins],job_runs[duration_mins]) | =MINIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[status],"SUCCESS") | =SUMIF(job_runs[job_id],[@job_id],job_runs[duration_mins])
    Row 5: 98 | 2 |  | 15 | =RANK.EQ([@duration_mins],job_runs[duration_mins]) | =MINIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[status],"SUCCESS") | =SUMIF(job_runs[job_id],[@job_id],job_runs[duration_mins])
    Row 6: 99 | 1 | TEST | 5 | =RANK.EQ([@duration_mins],job_runs[duration_mins]) | =MINIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[status],"SUCCESS") | =SUMIF(job_runs[job_id],[@job_id],job_runs[duration_mins])
    Row 7: 101 | 1 | SUCCESS | 10 | =RANK.EQ([@duration_mins],job_runs[duration_mins]) | =MINIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[status],"SUCCESS") | =SUMIF(job_runs[job_id],[@job_id],job_runs[duration_mins])
    Row 8: 102 | 2 | FAILED | 20 | =RANK.EQ([@duration_mins],job_runs[duration_mins]) | =MINIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[status],"SUCCESS") | =SUMIF(job_runs[job_id],[@job_id],job_runs[duration_mins])
    Row 9: 103 | 3 | SUCCESS | 30 | =RANK.EQ([@duration_mins],job_runs[duration_mins]) | =MINIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[status],"SUCCESS") | =SUMIF(job_runs[job_id],[@job_id],job_runs[duration_mins])
    Row 10: 104 | 1 | SUCCESS | 40 | =RANK.EQ([@duration_mins],job_runs[duration_mins]) | =MINIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[status],"SUCCESS") | =SUMIF(job_runs[job_id],[@job_id],job_runs[duration_mins])
>>>

## X42

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x42.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "jobs"
  Excel Table "jobs", A1:E5
    Headers: job_id | job_name | runs | avg_mins | id_order
    Row 2: 1 | nightly_load | =COUNTIF(job_runs[job_id],jobs[[#This Row],[job_id]]) | =IFERROR(AVERAGEIF(job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[duration_mins]),0) | =_xlfn.RANK.EQ(jobs[[#This Row],[job_id]],jobs[job_id],1)
    Row 3: 2 | invoice_sync | =COUNTIF(job_runs[job_id],jobs[[#This Row],[job_id]]) | =IFERROR(AVERAGEIF(job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[duration_mins]),0) | =_xlfn.RANK.EQ(jobs[[#This Row],[job_id]],jobs[job_id],1)
    Row 4: 3 | report_build | =COUNTIF(job_runs[job_id],jobs[[#This Row],[job_id]]) | =IFERROR(AVERAGEIF(job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[duration_mins]),0) | =_xlfn.RANK.EQ(jobs[[#This Row],[job_id]],jobs[job_id],1)
    Row 5: 4 | cache_warm | =COUNTIF(job_runs[job_id],jobs[[#This Row],[job_id]]) | =IFERROR(AVERAGEIF(job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[duration_mins]),0) | =_xlfn.RANK.EQ(jobs[[#This Row],[job_id]],jobs[job_id],1)
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
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
>>>

## X43

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x43.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
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
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
Sheet "busy_teams"
  Excel Table "busy_teams", A1:D2, loaded by Power Query "busy_teams"
    Headers: team | runs | shortest | avg_mins
    Row 2: finance | 5 | 15 | 22.6
Sheet "statuses"
  Excel Table "statuses", A1:B8, loaded by Power Query "statuses"
    Headers: job_id | status
    Row 2: 1 | SUCCESS
    Row 3: 1 | TEST
    Row 4: 2 | 
    Row 5: 2 | FAILED
    Row 6: 2 | SUCCESS
    Row 7: 3 | FAILED
    Row 8: 3 | SUCCESS
Power Query "busy_teams" (loads into Excel Table "busy_teams"):
    let
        Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Jobs = Excel.CurrentWorkbook(){[Name="jobs"]}[Content],
        Joined = Table.NestedJoin(Source, {"job_id"}, Jobs, {"job_id"}, "j", JoinKind.Inner),
        Expanded = Table.ExpandTableColumn(Joined, "j", {"team"}),
        Grouped = Table.Group(Expanded, {"team"}, {
            {"runs", each Table.RowCount(_), Int64.Type},
            {"shortest", each List.Min([duration_mins]), type number},
            {"avg_mins", each List.Average([duration_mins]), type number}}),
        Busy = Table.SelectRows(Grouped, each [runs] > 4)
    in
        Busy
Power Query "statuses" (loads into Excel Table "statuses"):
    let
        Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Kept = Table.SelectColumns(Source, {"job_id", "status"}),
        Unique = Table.Distinct(Kept)
    in
        Unique
>>>

## X44

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x44.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
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
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
Sheet "scheduler_runs"
  Excel Table "scheduler_runs", A1:C10
    Headers: run_id | job_id | dt
    Row 2: 95 | 1 | 2026-09-23
    Row 3: 96 | 2 | 2026-09-23
    Row 4: 97 | 3 | 2026-09-23
    Row 5: 98 | 2 | 2026-09-23
    Row 6: 100 | 3 | 2026-09-23
    Row 7: 101 | 1 | 2026-09-24
    Row 8: 102 | 2 | 2026-09-24
    Row 9: 103 | 3 | 2026-09-24
    Row 10: 104 | 1 | 2026-09-24
Sheet "jobs_with_runs"
  Excel Table "jobs_with_runs", A1:B11, loaded by Power Query "jobs_with_runs"
    Headers: run_id | job_name
    Row 2:  | cache_warm
    Row 3: 96 | invoice_sync
    Row 4: 98 | invoice_sync
    Row 5: 102 | invoice_sync
    Row 6: 95 | nightly_load
    Row 7: 99 | nightly_load
    Row 8: 101 | nightly_load
    Row 9: 104 | nightly_load
    Row 10: 97 | report_build
    Row 11: 103 | report_build
Sheet "never_scheduled"
  Excel Table "never_scheduled", A1:C2, loaded by Power Query "never_scheduled"
    Headers: job_id | job_name | team
    Row 2: 4 | cache_warm | web
Power Query "jobs_with_runs" (loads into Excel Table "jobs_with_runs"):
    let
        Runs = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Jobs = Excel.CurrentWorkbook(){[Name="jobs"]}[Content],
        Joined = Table.NestedJoin(Runs, {"job_id"}, Jobs, {"job_id"}, "j", JoinKind.RightOuter),
        Expanded = Table.ExpandTableColumn(Joined, "j", {"job_name"}),
        Kept = Table.SelectColumns(Expanded, {"run_id", "job_name"})
    in
        Kept
Power Query "never_scheduled" (loads into Excel Table "never_scheduled"):
    let
        Jobs = Excel.CurrentWorkbook(){[Name="jobs"]}[Content],
        Scheduled = Excel.CurrentWorkbook(){[Name="scheduler_runs"]}[Content],
        Unscheduled = Table.NestedJoin(Jobs, {"job_id"}, Scheduled, {"job_id"}, "s",
            JoinKind.LeftAnti),
        Kept = Table.SelectColumns(Unscheduled, {"job_id", "job_name", "team"})
    in
        Kept
>>>

## X45

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x45.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
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
Sheet "scheduler_runs"
  Excel Table "scheduler_runs", A1:C10
    Headers: run_id | job_id | dt
    Row 2: 95 | 1 | 2026-09-23
    Row 3: 96 | 2 | 2026-09-23
    Row 4: 97 | 3 | 2026-09-23
    Row 5: 98 | 2 | 2026-09-23
    Row 6: 100 | 3 | 2026-09-23
    Row 7: 101 | 1 | 2026-09-24
    Row 8: 102 | 2 | 2026-09-24
    Row 9: 103 | 3 | 2026-09-24
    Row 10: 104 | 1 | 2026-09-24
Sheet "run_days"
  Excel Table "run_days", A1:B11, loaded by Power Query "run_days"
    Headers: run_id | dt
    Row 2: 95 | 2026-09-23
    Row 3: 96 | 2026-09-23
    Row 4: 97 | 2026-09-23
    Row 5: 98 | 2026-09-23
    Row 6: 99 | 2026-09-23
    Row 7: 100 | 2026-09-23
    Row 8: 101 | 2026-09-24
    Row 9: 102 | 2026-09-24
    Row 10: 103 | 2026-09-24
    Row 11: 104 | 2026-09-24
Sheet "matched"
  Excel Table "matched", A1:D11, loaded by Power Query "matched"
    Headers: run_id | job_id | dt | status
    Row 2:  |  |  | TEST
    Row 3: 95 | 1 | 2026-09-23 | SUCCESS
    Row 4: 96 | 2 | 2026-09-23 | SUCCESS
    Row 5: 97 | 3 | 2026-09-23 | FAILED
    Row 6: 98 | 2 | 2026-09-23 | 
    Row 7: 100 | 3 | 2026-09-23 | 
    Row 8: 101 | 1 | 2026-09-24 | SUCCESS
    Row 9: 102 | 2 | 2026-09-24 | FAILED
    Row 10: 103 | 3 | 2026-09-24 | SUCCESS
    Row 11: 104 | 1 | 2026-09-24 | SUCCESS
Power Query "run_days" (loads into Excel Table "run_days"):
    let
        Runs = Table.SelectColumns(Excel.CurrentWorkbook(){[Name="job_runs"]}[Content], {"run_id", "dt"}),
        Scheduled = Table.SelectColumns(Excel.CurrentWorkbook(){[Name="scheduler_runs"]}[Content], {"run_id", "dt"}),
        Unique = Table.Distinct(Table.Combine({Runs, Scheduled}))
    in
        Unique
Power Query "matched" (loads into Excel Table "matched"):
    let
        Scheduled = Excel.CurrentWorkbook(){[Name="scheduler_runs"]}[Content],
        Runs = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Joined = Table.NestedJoin(Scheduled, {"run_id"}, Runs, {"run_id"}, "r", JoinKind.FullOuter),
        Expanded = Table.ExpandTableColumn(Joined, "r", {"status"})
    in
        Expanded
>>>

## X51

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x51.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_runs"
  Excel Table "job_runs", A1:I10
    Headers: run_id | job_id | status | duration_mins | dt | long_in_job | not_ok | failed_in_job | running_mins
    Row 2: 95 | 1 | SUCCESS | 12 | 2026-09-23 | =COUNTIFS(job_runs[job_id],[@job_id],job_runs[duration_mins],">15") | =COUNTIFS(job_runs[status],"<>SUCCESS") | =COUNTIFS(job_runs[job_id],[@job_id],job_runs[status],"*ail*") | =SUMIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[dt],"<="&[@dt])
    Row 3: 96 | 2 | SUCCESS | 18 | 2026-09-23 | =COUNTIFS(job_runs[job_id],[@job_id],job_runs[duration_mins],">15") | =COUNTIFS(job_runs[status],"<>SUCCESS") | =COUNTIFS(job_runs[job_id],[@job_id],job_runs[status],"*ail*") | =SUMIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[dt],"<="&[@dt])
    Row 4: 97 | 3 | FAILED | 30 | 2026-09-23 | =COUNTIFS(job_runs[job_id],[@job_id],job_runs[duration_mins],">15") | =COUNTIFS(job_runs[status],"<>SUCCESS") | =COUNTIFS(job_runs[job_id],[@job_id],job_runs[status],"*ail*") | =SUMIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[dt],"<="&[@dt])
    Row 5: 98 | 2 |  | 15 | 2026-09-23 | =COUNTIFS(job_runs[job_id],[@job_id],job_runs[duration_mins],">15") | =COUNTIFS(job_runs[status],"<>SUCCESS") | =COUNTIFS(job_runs[job_id],[@job_id],job_runs[status],"*ail*") | =SUMIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[dt],"<="&[@dt])
    Row 6: 99 | 1 | TEST | 5 | 2026-09-23 | =COUNTIFS(job_runs[job_id],[@job_id],job_runs[duration_mins],">15") | =COUNTIFS(job_runs[status],"<>SUCCESS") | =COUNTIFS(job_runs[job_id],[@job_id],job_runs[status],"*ail*") | =SUMIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[dt],"<="&[@dt])
    Row 7: 101 | 1 | SUCCESS | 10 | 2026-09-24 | =COUNTIFS(job_runs[job_id],[@job_id],job_runs[duration_mins],">15") | =COUNTIFS(job_runs[status],"<>SUCCESS") | =COUNTIFS(job_runs[job_id],[@job_id],job_runs[status],"*ail*") | =SUMIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[dt],"<="&[@dt])
    Row 8: 102 | 2 | FAILED | 20 | 2026-09-24 | =COUNTIFS(job_runs[job_id],[@job_id],job_runs[duration_mins],">15") | =COUNTIFS(job_runs[status],"<>SUCCESS") | =COUNTIFS(job_runs[job_id],[@job_id],job_runs[status],"*ail*") | =SUMIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[dt],"<="&[@dt])
    Row 9: 103 | 3 | SUCCESS | 30 | 2026-09-24 | =COUNTIFS(job_runs[job_id],[@job_id],job_runs[duration_mins],">15") | =COUNTIFS(job_runs[status],"<>SUCCESS") | =COUNTIFS(job_runs[job_id],[@job_id],job_runs[status],"*ail*") | =SUMIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[dt],"<="&[@dt])
    Row 10: 104 | 1 | SUCCESS | 40 | 2026-09-24 | =COUNTIFS(job_runs[job_id],[@job_id],job_runs[duration_mins],">15") | =COUNTIFS(job_runs[status],"<>SUCCESS") | =COUNTIFS(job_runs[job_id],[@job_id],job_runs[status],"*ail*") | =SUMIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[dt],"<="&[@dt])
>>>

## X52

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x52.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_runs"
  Excel Table "job_runs", A1:F11
    Headers: run_id | job_id | duration_mins | share | vs_avg | rank_in_job
    Row 2: 95 | 1 | 12 | =job_runs[[#This Row],[duration_mins]]/SUM(job_runs[duration_mins]) | =job_runs[[#This Row],[duration_mins]]-AVERAGE(job_runs[duration_mins]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]],job_runs[duration_mins],">"&job_runs[[#This Row],[duration_mins]])+1
    Row 3: 96 | 2 | 18 | =job_runs[[#This Row],[duration_mins]]/SUM(job_runs[duration_mins]) | =job_runs[[#This Row],[duration_mins]]-AVERAGE(job_runs[duration_mins]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]],job_runs[duration_mins],">"&job_runs[[#This Row],[duration_mins]])+1
    Row 4: 97 | 3 | 30 | =job_runs[[#This Row],[duration_mins]]/SUM(job_runs[duration_mins]) | =job_runs[[#This Row],[duration_mins]]-AVERAGE(job_runs[duration_mins]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]],job_runs[duration_mins],">"&job_runs[[#This Row],[duration_mins]])+1
    Row 5: 98 | 2 | 15 | =job_runs[[#This Row],[duration_mins]]/SUM(job_runs[duration_mins]) | =job_runs[[#This Row],[duration_mins]]-AVERAGE(job_runs[duration_mins]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]],job_runs[duration_mins],">"&job_runs[[#This Row],[duration_mins]])+1
    Row 6: 99 | 1 | 5 | =job_runs[[#This Row],[duration_mins]]/SUM(job_runs[duration_mins]) | =job_runs[[#This Row],[duration_mins]]-AVERAGE(job_runs[duration_mins]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]],job_runs[duration_mins],">"&job_runs[[#This Row],[duration_mins]])+1
    Row 7: 101 | 1 | 10 | =job_runs[[#This Row],[duration_mins]]/SUM(job_runs[duration_mins]) | =job_runs[[#This Row],[duration_mins]]-AVERAGE(job_runs[duration_mins]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]],job_runs[duration_mins],">"&job_runs[[#This Row],[duration_mins]])+1
    Row 8: 102 | 2 | 20 | =job_runs[[#This Row],[duration_mins]]/SUM(job_runs[duration_mins]) | =job_runs[[#This Row],[duration_mins]]-AVERAGE(job_runs[duration_mins]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]],job_runs[duration_mins],">"&job_runs[[#This Row],[duration_mins]])+1
    Row 9: 103 | 3 | 30 | =job_runs[[#This Row],[duration_mins]]/SUM(job_runs[duration_mins]) | =job_runs[[#This Row],[duration_mins]]-AVERAGE(job_runs[duration_mins]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]],job_runs[duration_mins],">"&job_runs[[#This Row],[duration_mins]])+1
    Row 10: 104 | 1 | 40 | =job_runs[[#This Row],[duration_mins]]/SUM(job_runs[duration_mins]) | =job_runs[[#This Row],[duration_mins]]-AVERAGE(job_runs[duration_mins]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]],job_runs[duration_mins],">"&job_runs[[#This Row],[duration_mins]])+1
    Total Row: Total |  | =SUBTOTAL(109,job_runs[duration_mins]) | =SUBTOTAL(109,job_runs[share]) |  | 
>>>

## X53

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x53.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
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
Sheet "by_job"
  Excel Table "by_job", A1:D5
    Headers: job_id | total_mins | runs | longest
    Row 2: 1 | =SUMIFS(job_runs[duration_mins],job_runs[job_id],by_job[[#This Row],[job_id]]) | =COUNTIFS(job_runs[job_id],by_job[[#This Row],[job_id]]) | =_xlfn.MAXIFS(job_runs[duration_mins],job_runs[job_id],by_job[[#This Row],[job_id]])
    Row 3: 2 | =SUMIFS(job_runs[duration_mins],job_runs[job_id],by_job[[#This Row],[job_id]]) | =COUNTIFS(job_runs[job_id],by_job[[#This Row],[job_id]]) | =_xlfn.MAXIFS(job_runs[duration_mins],job_runs[job_id],by_job[[#This Row],[job_id]])
    Row 4: 3 | =SUMIFS(job_runs[duration_mins],job_runs[job_id],by_job[[#This Row],[job_id]]) | =COUNTIFS(job_runs[job_id],by_job[[#This Row],[job_id]]) | =_xlfn.MAXIFS(job_runs[duration_mins],job_runs[job_id],by_job[[#This Row],[job_id]])
    Total Row: Total | =SUBTOTAL(109,by_job[total_mins]) | =SUBTOTAL(109,by_job[runs]) | =SUBTOTAL(104,by_job[longest])
>>>

## X54

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x54.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_runs"
  Excel Table "job_runs", A1:I10
    Headers: run_id | dt | month_end | a_month_on | due | week_of | month_of | weekday | label
    Row 2: 95 | 2026-09-23 | =EOMONTH([@dt],0) | =EDATE([@dt],1) | =[@dt]+7 | =[@dt]-WEEKDAY([@dt],2)+1 | =DATE(YEAR([@dt]),MONTH([@dt]),1) | =WEEKDAY([@dt]) | =TEXT([@dt],"yyyy-mm")
    Row 3: 96 | 2026-09-23 | =EOMONTH([@dt],0) | =EDATE([@dt],1) | =[@dt]+7 | =[@dt]-WEEKDAY([@dt],2)+1 | =DATE(YEAR([@dt]),MONTH([@dt]),1) | =WEEKDAY([@dt]) | =TEXT([@dt],"yyyy-mm")
    Row 4: 97 | 2026-09-23 | =EOMONTH([@dt],0) | =EDATE([@dt],1) | =[@dt]+7 | =[@dt]-WEEKDAY([@dt],2)+1 | =DATE(YEAR([@dt]),MONTH([@dt]),1) | =WEEKDAY([@dt]) | =TEXT([@dt],"yyyy-mm")
    Row 5: 98 | 2026-09-23 | =EOMONTH([@dt],0) | =EDATE([@dt],1) | =[@dt]+7 | =[@dt]-WEEKDAY([@dt],2)+1 | =DATE(YEAR([@dt]),MONTH([@dt]),1) | =WEEKDAY([@dt]) | =TEXT([@dt],"yyyy-mm")
    Row 6: 99 | 2026-09-23 | =EOMONTH([@dt],0) | =EDATE([@dt],1) | =[@dt]+7 | =[@dt]-WEEKDAY([@dt],2)+1 | =DATE(YEAR([@dt]),MONTH([@dt]),1) | =WEEKDAY([@dt]) | =TEXT([@dt],"yyyy-mm")
    Row 7: 101 | 2026-09-24 | =EOMONTH([@dt],0) | =EDATE([@dt],1) | =[@dt]+7 | =[@dt]-WEEKDAY([@dt],2)+1 | =DATE(YEAR([@dt]),MONTH([@dt]),1) | =WEEKDAY([@dt]) | =TEXT([@dt],"yyyy-mm")
    Row 8: 102 | 2026-09-24 | =EOMONTH([@dt],0) | =EDATE([@dt],1) | =[@dt]+7 | =[@dt]-WEEKDAY([@dt],2)+1 | =DATE(YEAR([@dt]),MONTH([@dt]),1) | =WEEKDAY([@dt]) | =TEXT([@dt],"yyyy-mm")
    Row 9: 103 | 2026-09-24 | =EOMONTH([@dt],0) | =EDATE([@dt],1) | =[@dt]+7 | =[@dt]-WEEKDAY([@dt],2)+1 | =DATE(YEAR([@dt]),MONTH([@dt]),1) | =WEEKDAY([@dt]) | =TEXT([@dt],"yyyy-mm")
    Row 10: 104 | 2026-09-24 | =EOMONTH([@dt],0) | =EDATE([@dt],1) | =[@dt]+7 | =[@dt]-WEEKDAY([@dt],2)+1 | =DATE(YEAR([@dt]),MONTH([@dt]),1) | =WEEKDAY([@dt]) | =TEXT([@dt],"yyyy-mm")
>>>

## X55

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x55.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "jobs"
  Excel Table "jobs", A1:I5
    Headers: job_id | job_name | team | region | title | tag | code | has_sync | tens
    Row 2: 1 | nightly_load | data | LON | =PROPER(SUBSTITUTE(jobs[[#This Row],[job_name]],"_"," ")) | =_xlfn.TEXTJOIN("/",TRUE,jobs[[#This Row],[team]],jobs[[#This Row],[region]]) | =CONCATENATE(jobs[[#This Row],[region]],"-",jobs[[#This Row],[job_id]]) | =ISNUMBER(SEARCH("SYNC",jobs[[#This Row],[job_name]])) | =VALUE(jobs[[#This Row],[job_id]]&"0")
    Row 3: 2 | invoice_sync | finance | PAR | =PROPER(SUBSTITUTE(jobs[[#This Row],[job_name]],"_"," ")) | =_xlfn.TEXTJOIN("/",TRUE,jobs[[#This Row],[team]],jobs[[#This Row],[region]]) | =CONCATENATE(jobs[[#This Row],[region]],"-",jobs[[#This Row],[job_id]]) | =ISNUMBER(SEARCH("SYNC",jobs[[#This Row],[job_name]])) | =VALUE(jobs[[#This Row],[job_id]]&"0")
    Row 4: 3 | report_build | finance | NYC | =PROPER(SUBSTITUTE(jobs[[#This Row],[job_name]],"_"," ")) | =_xlfn.TEXTJOIN("/",TRUE,jobs[[#This Row],[team]],jobs[[#This Row],[region]]) | =CONCATENATE(jobs[[#This Row],[region]],"-",jobs[[#This Row],[job_id]]) | =ISNUMBER(SEARCH("SYNC",jobs[[#This Row],[job_name]])) | =VALUE(jobs[[#This Row],[job_id]]&"0")
    Row 5: 4 | cache_warm | web | LON | =PROPER(SUBSTITUTE(jobs[[#This Row],[job_name]],"_"," ")) | =_xlfn.TEXTJOIN("/",TRUE,jobs[[#This Row],[team]],jobs[[#This Row],[region]]) | =CONCATENATE(jobs[[#This Row],[region]],"-",jobs[[#This Row],[job_id]]) | =ISNUMBER(SEARCH("SYNC",jobs[[#This Row],[job_name]])) | =VALUE(jobs[[#This Row],[job_id]]&"0")
>>>

## X56

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x56.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_runs"
  Excel Table "job_runs", A1:K10
    Headers: run_id | job_id | status | duration_mins | avg_retry_secs | no_status | weeks | at_least_20 | spread | weighted | scheduled_on
    Row 2: 95 | 1 | SUCCESS | 12 | 2 | =ISBLANK(job_runs[[#This Row],[status]]) | =INT(job_runs[[#This Row],[duration_mins]]/7) | =MAX(job_runs[[#This Row],[duration_mins]],20) | =_xlfn.STDEV.S(job_runs[duration_mins]) | =SUMPRODUCT(job_runs[duration_mins],job_runs[avg_retry_secs]) | =_xlfn.XLOOKUP(job_runs[[#This Row],[run_id]],scheduler_runs[run_id],scheduler_runs[dt],"unscheduled")
    Row 3: 96 | 2 | SUCCESS | 18 | 0 | =ISBLANK(job_runs[[#This Row],[status]]) | =INT(job_runs[[#This Row],[duration_mins]]/7) | =MAX(job_runs[[#This Row],[duration_mins]],20) | =_xlfn.STDEV.S(job_runs[duration_mins]) | =SUMPRODUCT(job_runs[duration_mins],job_runs[avg_retry_secs]) | =_xlfn.XLOOKUP(job_runs[[#This Row],[run_id]],scheduler_runs[run_id],scheduler_runs[dt],"unscheduled")
    Row 4: 97 | 3 | FAILED | 30 | 8 | =ISBLANK(job_runs[[#This Row],[status]]) | =INT(job_runs[[#This Row],[duration_mins]]/7) | =MAX(job_runs[[#This Row],[duration_mins]],20) | =_xlfn.STDEV.S(job_runs[duration_mins]) | =SUMPRODUCT(job_runs[duration_mins],job_runs[avg_retry_secs]) | =_xlfn.XLOOKUP(job_runs[[#This Row],[run_id]],scheduler_runs[run_id],scheduler_runs[dt],"unscheduled")
    Row 5: 98 | 2 |  | 15 |  | =ISBLANK(job_runs[[#This Row],[status]]) | =INT(job_runs[[#This Row],[duration_mins]]/7) | =MAX(job_runs[[#This Row],[duration_mins]],20) | =_xlfn.STDEV.S(job_runs[duration_mins]) | =SUMPRODUCT(job_runs[duration_mins],job_runs[avg_retry_secs]) | =_xlfn.XLOOKUP(job_runs[[#This Row],[run_id]],scheduler_runs[run_id],scheduler_runs[dt],"unscheduled")
    Row 6: 99 | 1 | TEST | 5 | 0 | =ISBLANK(job_runs[[#This Row],[status]]) | =INT(job_runs[[#This Row],[duration_mins]]/7) | =MAX(job_runs[[#This Row],[duration_mins]],20) | =_xlfn.STDEV.S(job_runs[duration_mins]) | =SUMPRODUCT(job_runs[duration_mins],job_runs[avg_retry_secs]) | =_xlfn.XLOOKUP(job_runs[[#This Row],[run_id]],scheduler_runs[run_id],scheduler_runs[dt],"unscheduled")
    Row 7: 101 | 1 | SUCCESS | 10 | 1 | =ISBLANK(job_runs[[#This Row],[status]]) | =INT(job_runs[[#This Row],[duration_mins]]/7) | =MAX(job_runs[[#This Row],[duration_mins]],20) | =_xlfn.STDEV.S(job_runs[duration_mins]) | =SUMPRODUCT(job_runs[duration_mins],job_runs[avg_retry_secs]) | =_xlfn.XLOOKUP(job_runs[[#This Row],[run_id]],scheduler_runs[run_id],scheduler_runs[dt],"unscheduled")
    Row 8: 102 | 2 | FAILED | 20 | 6 | =ISBLANK(job_runs[[#This Row],[status]]) | =INT(job_runs[[#This Row],[duration_mins]]/7) | =MAX(job_runs[[#This Row],[duration_mins]],20) | =_xlfn.STDEV.S(job_runs[duration_mins]) | =SUMPRODUCT(job_runs[duration_mins],job_runs[avg_retry_secs]) | =_xlfn.XLOOKUP(job_runs[[#This Row],[run_id]],scheduler_runs[run_id],scheduler_runs[dt],"unscheduled")
    Row 9: 103 | 3 | SUCCESS | 30 | 0 | =ISBLANK(job_runs[[#This Row],[status]]) | =INT(job_runs[[#This Row],[duration_mins]]/7) | =MAX(job_runs[[#This Row],[duration_mins]],20) | =_xlfn.STDEV.S(job_runs[duration_mins]) | =SUMPRODUCT(job_runs[duration_mins],job_runs[avg_retry_secs]) | =_xlfn.XLOOKUP(job_runs[[#This Row],[run_id]],scheduler_runs[run_id],scheduler_runs[dt],"unscheduled")
    Row 10: 104 | 1 | SUCCESS | 40 | 3 | =ISBLANK(job_runs[[#This Row],[status]]) | =INT(job_runs[[#This Row],[duration_mins]]/7) | =MAX(job_runs[[#This Row],[duration_mins]],20) | =_xlfn.STDEV.S(job_runs[duration_mins]) | =SUMPRODUCT(job_runs[duration_mins],job_runs[avg_retry_secs]) | =_xlfn.XLOOKUP(job_runs[[#This Row],[run_id]],scheduler_runs[run_id],scheduler_runs[dt],"unscheduled")
Sheet "scheduler_runs"
  Excel Table "scheduler_runs", A1:C10
    Headers: run_id | job_id | dt
    Row 2: 95 | 1 | 2026-09-23
    Row 3: 96 | 2 | 2026-09-23
    Row 4: 97 | 3 | 2026-09-23
    Row 5: 98 | 2 | 2026-09-23
    Row 6: 100 | 3 | 2026-09-23
    Row 7: 101 | 1 | 2026-09-24
    Row 8: 102 | 2 | 2026-09-24
    Row 9: 103 | 3 | 2026-09-24
    Row 10: 104 | 1 | 2026-09-24
>>>

## X57

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x57.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
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
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
Sheet "picked"
  Excel Table "picked", A1:E6, loaded by Power Query "picked"
    Headers: run_id | job_id | status | avg_retry_secs | status_lc
    Row 2: 95 | 1 | SUCCESS | 2 | success
    Row 3: 96 | 2 | SUCCESS | 0 | success
    Row 4: 98 | 2 |  | 0 | 
    Row 5: 101 | 1 | SUCCESS | 1 | success
    Row 6: 104 | 1 | SUCCESS | 3 | success
Sheet "ran_jobs"
  Excel Table "ran_jobs", A1:D2, loaded by Power Query "ran_jobs"
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
Power Query "picked" (loads into Excel Table "picked"):
    let
        Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Picked = Table.SelectRows(Source, each List.Contains({1, 2}, [job_id])
            and ([status] = null or Text.StartsWith([status], "S"))),
        Filled = Table.ReplaceValue(Picked, null, 0, Replacer.ReplaceValue, {"avg_retry_secs"}),
        Lower = Table.AddColumn(Filled, "status_lc", each Text.Lower([status]), type text),
        Kept = Table.SelectColumns(Lower, {"run_id", "job_id", "status", "avg_retry_secs",
            "status_lc"})
    in
        Kept
Power Query "ran_jobs" (loads into Excel Table "ran_jobs"):
    let
        Jobs = Excel.CurrentWorkbook(){[Name="jobs"]}[Content],
        Runs = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Ran = Table.SelectRows(Jobs, each List.Contains(Runs[job_id], [job_id])
            and Text.Contains([job_name], "a"))
    in
        Ran
>>>

## X58

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x58.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
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
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
Sheet "scheduler_runs"
  Excel Table "scheduler_runs", A1:C10
    Headers: run_id | job_id | dt
    Row 2: 95 | 1 | 2026-09-23
    Row 3: 96 | 2 | 2026-09-23
    Row 4: 97 | 3 | 2026-09-23
    Row 5: 98 | 2 | 2026-09-23
    Row 6: 100 | 3 | 2026-09-23
    Row 7: 101 | 1 | 2026-09-24
    Row 8: 102 | 2 | 2026-09-24
    Row 9: 103 | 3 | 2026-09-24
    Row 10: 104 | 1 | 2026-09-24
Sheet "region_budgets"
  Excel Table "region_budgets", A1:C5
    Headers: job_id | budget_cents | region
    Row 2: 1 | 150 | eu
    Row 3: 2 | 200 | eu
    Row 4: 3 | 350 | us
    Row 5: 4 | 50 | eu
Sheet "job_regions"
  Excel Table "job_regions", A1:B9, loaded by Power Query "job_regions"
    Headers: job_id | region
    Row 2: 1 | eu
    Row 3: 1 | us
    Row 4: 2 | eu
    Row 5: 2 | us
    Row 6: 3 | eu
    Row 7: 3 | us
    Row 8: 4 | eu
    Row 9: 4 | us
Sheet "numbered"
  Excel Table "numbered", A1:D10, loaded by Power Query "numbered"
    Headers: run_id | dt | duration_mins | n
    Row 2: 104 | 2026-09-24 | 40 | 1
    Row 3: 97 | 2026-09-23 | 30 | 2
    Row 4: 103 | 2026-09-24 | 30 | 3
    Row 5: 102 | 2026-09-24 | 20 | 4
    Row 6: 96 | 2026-09-23 | 18 | 5
    Row 7: 98 | 2026-09-23 | 15 | 6
    Row 8: 95 | 2026-09-23 | 12 | 7
    Row 9: 101 | 2026-09-24 | 10 | 8
    Row 10: 99 | 2026-09-23 | 5 | 9
Sheet "days_per_job"
  Excel Table "days_per_job", A1:B4, loaded by Power Query "days_per_job"
    Headers: job_id | days
    Row 2: 1 | 2
    Row 3: 2 | 2
    Row 4: 3 | 2
Sheet "unrun"
  Excel Table "unrun", A1:B2, loaded by Power Query "unrun"
    Headers: run_id | job_id
    Row 2: 100 | 3
Sheet "measures"
  Excel Table "measures", A1:C18, loaded by Power Query "measures"
    Headers: run_id | measure | amount
    Row 2: 95 | duration_mins | 12
    Row 3: 95 | avg_retry_secs | 2
    Row 4: 96 | duration_mins | 18
    Row 5: 96 | avg_retry_secs | 0
    Row 6: 97 | duration_mins | 30
    Row 7: 97 | avg_retry_secs | 8
    Row 8: 98 | duration_mins | 15
    Row 9: 99 | duration_mins | 5
    Row 10: 99 | avg_retry_secs | 0
    Row 11: 101 | duration_mins | 10
    Row 12: 101 | avg_retry_secs | 1
    Row 13: 102 | duration_mins | 20
    Row 14: 102 | avg_retry_secs | 6
    Row 15: 103 | duration_mins | 30
    Row 16: 103 | avg_retry_secs | 0
    Row 17: 104 | duration_mins | 40
    Row 18: 104 | avg_retry_secs | 3
Power Query "job_regions" (loads into Excel Table "job_regions"):
    let
        Jobs = Table.SelectColumns(Excel.CurrentWorkbook(){[Name="jobs"]}[Content], {"job_id"}),
        Regions = Table.Distinct(Table.SelectColumns(Excel.CurrentWorkbook(){[Name="region_budgets"]}[Content], {"region"})),
        Paired = Table.AddColumn(Jobs, "r", each Regions),
        Expanded = Table.ExpandTableColumn(Paired, "r", {"region"})
    in
        Expanded
Power Query "numbered" (loads into Excel Table "numbered"):
    let
        Source = Table.SelectColumns(Excel.CurrentWorkbook(){[Name="job_runs"]}[Content], {"run_id", "dt", "duration_mins"}),
        Sorted = Table.Sort(Source, {{"duration_mins", Order.Descending}, {"run_id",
            Order.Ascending}}),
        Numbered = Table.AddIndexColumn(Sorted, "n", 1, 1)
    in
        Numbered
Power Query "days_per_job" (loads into Excel Table "days_per_job"):
    let
        Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Grouped = Table.Group(Source, {"job_id"}, {{"days", each List.Count(List.Distinct([dt])),
            Int64.Type}}),
        Sorted = Table.Sort(Grouped, {{"days", Order.Descending}})
    in
        Sorted
Power Query "unrun" (loads into Excel Table "unrun"):
    let
        Scheduled = Table.SelectColumns(Excel.CurrentWorkbook(){[Name="scheduler_runs"]}[Content], {"run_id", "job_id"}),
        Runs = Table.SelectColumns(Excel.CurrentWorkbook(){[Name="job_runs"]}[Content], {"run_id", "job_id"}),
        Missing = Table.NestedJoin(Scheduled, {"run_id", "job_id"}, Runs, {"run_id", "job_id"},
            "r", JoinKind.LeftAnti),
        Unique = Table.Distinct(Table.RemoveColumns(Missing, {"r"}))
    in
        Unique
Power Query "measures" (loads into Excel Table "measures"):
    let
        Source = Table.SelectColumns(Excel.CurrentWorkbook(){[Name="job_runs"]}[Content], {"run_id", "duration_mins",
            "avg_retry_secs"}),
        Long = Table.UnpivotOtherColumns(Source, {"run_id"}, "measure", "amount")
    in
        Long
>>>

## X67

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x67.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_runs"
  Excel Table "job_runs", A1:G10
    Headers: run_id | job_id | duration_mins | dt | team | alerts | running_mins
    Row 2: 95 | 1 | 12 | 2026-09-23 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =COUNTIF(run_alerts[run_id],job_runs[[#This Row],[run_id]]) | =SUMIFS(job_runs[duration_mins],job_runs[job_id],job_runs[[#This Row],[job_id]],job_runs[dt],"<="&job_runs[[#This Row],[dt]])
    Row 3: 96 | 2 | 18 | 2026-09-23 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =COUNTIF(run_alerts[run_id],job_runs[[#This Row],[run_id]]) | =SUMIFS(job_runs[duration_mins],job_runs[job_id],job_runs[[#This Row],[job_id]],job_runs[dt],"<="&job_runs[[#This Row],[dt]])
    Row 4: 97 | 3 | 30 | 2026-09-23 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =COUNTIF(run_alerts[run_id],job_runs[[#This Row],[run_id]]) | =SUMIFS(job_runs[duration_mins],job_runs[job_id],job_runs[[#This Row],[job_id]],job_runs[dt],"<="&job_runs[[#This Row],[dt]])
    Row 5: 98 | 2 | 15 | 2026-09-23 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =COUNTIF(run_alerts[run_id],job_runs[[#This Row],[run_id]]) | =SUMIFS(job_runs[duration_mins],job_runs[job_id],job_runs[[#This Row],[job_id]],job_runs[dt],"<="&job_runs[[#This Row],[dt]])
    Row 6: 99 | 1 | 5 | 2026-09-23 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =COUNTIF(run_alerts[run_id],job_runs[[#This Row],[run_id]]) | =SUMIFS(job_runs[duration_mins],job_runs[job_id],job_runs[[#This Row],[job_id]],job_runs[dt],"<="&job_runs[[#This Row],[dt]])
    Row 7: 101 | 1 | 10 | 2026-09-24 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =COUNTIF(run_alerts[run_id],job_runs[[#This Row],[run_id]]) | =SUMIFS(job_runs[duration_mins],job_runs[job_id],job_runs[[#This Row],[job_id]],job_runs[dt],"<="&job_runs[[#This Row],[dt]])
    Row 8: 102 | 2 | 20 | 2026-09-24 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =COUNTIF(run_alerts[run_id],job_runs[[#This Row],[run_id]]) | =SUMIFS(job_runs[duration_mins],job_runs[job_id],job_runs[[#This Row],[job_id]],job_runs[dt],"<="&job_runs[[#This Row],[dt]])
    Row 9: 103 | 3 | 30 | 2026-09-24 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =COUNTIF(run_alerts[run_id],job_runs[[#This Row],[run_id]]) | =SUMIFS(job_runs[duration_mins],job_runs[job_id],job_runs[[#This Row],[job_id]],job_runs[dt],"<="&job_runs[[#This Row],[dt]])
    Row 10: 104 | 1 | 40 | 2026-09-24 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =COUNTIF(run_alerts[run_id],job_runs[[#This Row],[run_id]]) | =SUMIFS(job_runs[duration_mins],job_runs[job_id],job_runs[[#This Row],[job_id]],job_runs[dt],"<="&job_runs[[#This Row],[dt]])
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
Sheet "run_alerts"
  Excel Table "run_alerts", A1:D10
    Headers: alert_id | run_id | severity | dt
    Row 2: 1 | 97 | high | 2026-09-23
    Row 3: 2 | 97 | low | 2026-09-23
    Row 4: 3 | 101 | low | 2026-09-24
    Row 5: 4 | 101 | low | 2026-09-24
    Row 6: 5 | 101 | high | 2026-09-24
    Row 7: 6 | 102 | high | 2026-09-24
    Row 8: 7 | 103 | low | 2026-09-24
    Row 9: 8 | 103 | low | 2026-09-24
    Row 10: 9 | 104 | low | 2026-09-24
Sheet "by_team"
  Excel Table "by_team", A1:C4
    Headers: team | total_mins | alerted_runs
    Row 2: data | =SUMIFS(job_runs[duration_mins],job_runs[team],by_team[[#This Row],[team]]) | =COUNTIFS(job_runs[team],by_team[[#This Row],[team]],job_runs[alerts],">0")
    Row 3: finance | =SUMIFS(job_runs[duration_mins],job_runs[team],by_team[[#This Row],[team]]) | =COUNTIFS(job_runs[team],by_team[[#This Row],[team]],job_runs[alerts],">0")
    Total Row: Total | =SUBTOTAL(109,by_team[total_mins]) | =SUBTOTAL(109,by_team[alerted_runs])
Sheet "noisy_runs"
  Excel Table "noisy_runs", A1:D4, loaded by Power Query "noisy_runs"
    Headers: run_id | team | alerts | running_mins
    Row 2: 97 | finance | 2 | 30
    Row 3: 101 | data | 3 | 67
    Row 4: 103 | finance | 2 | 60
Power Query "noisy_runs" (loads into Excel Table "noisy_runs"):
    let
        Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Noisy = Table.SelectRows(Source, each [alerts] >= 2),
        Kept = Table.SelectColumns(Noisy, {"run_id", "team", "alerts", "running_mins"})
    in
        Kept
>>>

## X68

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x68.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
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
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
Sheet "region_budgets"
  Excel Table "region_budgets", A1:C5
    Headers: job_id | budget_cents | region
    Row 2: 1 | 150 | eu
    Row 3: 2 | 200 | eu
    Row 4: 3 | 350 | us
    Row 5: 4 | 50 | eu
Sheet "by_region"
  Excel Table "by_region", A1:D4, loaded by Power Query "by_region"
    Headers: region | total_mins | runs | share
    Row 2: eu | 120 | 7 | =by_region[[#This Row],[total_mins]]/SUM(by_region[total_mins])
    Row 3: us | 60 | 2 | =by_region[[#This Row],[total_mins]]/SUM(by_region[total_mins])
    Total Row: Total | =SUBTOTAL(109,by_region[total_mins]) |  | 
Sheet "top_runs"
  Excel Table "top_runs", A1:C3, loaded by Power Query "top_runs"
    Headers: run_id | job_name | region
    Row 2: 104 | nightly_load | eu
    Row 3: 97 | report_build | us
Power Query "base" (connection only):
    let
        Runs = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Jobs = Excel.CurrentWorkbook(){[Name="jobs"]}[Content],
        Budgets = Excel.CurrentWorkbook(){[Name="region_budgets"]}[Content],
        Named = Table.ExpandTableColumn(Table.NestedJoin(Runs, {"job_id"}, Jobs, {"job_id"},
            "j", JoinKind.Inner), "j", {"job_name"}),
        Placed = Table.ExpandTableColumn(Table.NestedJoin(Named, {"job_id"}, Budgets,
            {"job_id"}, "b", JoinKind.LeftOuter), "b", {"region"})
    in
        Placed
Power Query "by_region" (loads into Excel Table "by_region"):
    let
        Grouped = Table.Group(base, {"region"}, {
            {"total_mins", each List.Sum([duration_mins]), type number},
            {"runs", each Table.RowCount(_), Int64.Type}}),
        Kept = Table.SelectRows(Grouped, each [runs] >= 2)
    in
        Kept
Power Query "top_runs" (loads into Excel Table "top_runs"):
    let
        Sorted = Table.Sort(base, {{"duration_mins", Order.Descending}, {"run_id",
            Order.Ascending}}),
        Top = Table.FirstN(Sorted, 2),
        Kept = Table.SelectColumns(Top, {"run_id", "job_name", "region"})
    in
        Kept
>>>

## X71

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x71.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
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
Sheet "ok_runs"
  Excel Table "ok_runs", A1:D6, loaded by Power Query "ok_runs"
    Headers: run_id | job_id | duration_mins | hours
    Row 2: 95 | 1 | 12 | =ok_runs[[#This Row],[duration_mins]]/60
    Row 3: 96 | 2 | 18 | =ok_runs[[#This Row],[duration_mins]]/60
    Row 4: 101 | 1 | 10 | =ok_runs[[#This Row],[duration_mins]]/60
    Row 5: 103 | 3 | 30 | =ok_runs[[#This Row],[duration_mins]]/60
    Row 6: 104 | 1 | 40 | =ok_runs[[#This Row],[duration_mins]]/60
Sheet "ok_by_job"
  Excel Table "ok_by_job", A1:B4, loaded by Power Query "ok_by_job"
    Headers: job_id | total_mins
    Row 2: 1 | 62
    Row 3: 2 | 18
    Row 4: 3 | 30
Power Query "ok_runs" (loads into Excel Table "ok_runs"):
    let
        Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Ok = Table.SelectRows(Source, each [status] = "SUCCESS"),
        Kept = Table.SelectColumns(Ok, {"run_id", "job_id", "duration_mins"})
    in
        Kept
Power Query "ok_by_job" (loads into Excel Table "ok_by_job"):
    let
        Grouped = Table.Group(ok_runs, {"job_id"}, {
            {"total_mins", each List.Sum([duration_mins]), type number}})
    in
        Grouped
>>>

## X72

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x72.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "jobs"
  Excel Table "jobs", A1:E5
    Headers: job_id | job_name | team | runs | total
    Row 2: 1 | nightly_load | data | =COUNTIF(job_runs[job_id],jobs[[#This Row],[job_id]]) | =SUMIF(job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[duration_mins])
    Row 3: 2 | invoice_sync | finance | =COUNTIF(job_runs[job_id],jobs[[#This Row],[job_id]]) | =SUMIF(job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[duration_mins])
    Row 4: 3 | report_build | finance | =COUNTIF(job_runs[job_id],jobs[[#This Row],[job_id]]) | =SUMIF(job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[duration_mins])
    Row 5: 4 | cache_warm | web | =COUNTIF(job_runs[job_id],jobs[[#This Row],[job_id]]) | =SUMIF(job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[duration_mins])
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
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
Sheet "by_team"
  Excel Table "by_team", A1:B4
    Headers: team | team_total
    Row 2: data | =SUMIFS(jobs[total],jobs[team],by_team[[#This Row],[team]])
    Row 3: finance | =SUMIFS(jobs[total],jobs[team],by_team[[#This Row],[team]])
    Row 4: web | =SUMIFS(jobs[total],jobs[team],by_team[[#This Row],[team]])
Sheet "busy_jobs"
  Excel Table "busy_jobs", A1:C3, loaded by Power Query "busy_jobs"
    Headers: job_id | job_name | runs
    Row 2: 1 | nightly_load | 4
    Row 3: 2 | invoice_sync | 3
Power Query "busy_jobs" (loads into Excel Table "busy_jobs"):
    let
        Source = Excel.CurrentWorkbook(){[Name="jobs"]}[Content],
        Busy = Table.SelectRows(Source, each [runs] >= 3),
        Kept = Table.SelectColumns(Busy, {"job_id", "job_name", "runs"})
    in
        Kept
>>>

## X75

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x75.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
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
Sheet "long_runs"
  Excel Table "long_runs", A1:D7, loaded by Power Query "long_runs"
    Headers: run_id | dt | duration_mins | over
    Row 2: 96 | 2026-09-23 | 18 | =long_runs[[#This Row],[duration_mins]]-15
    Row 3: 97 | 2026-09-23 | 30 | =long_runs[[#This Row],[duration_mins]]-15
    Row 4: 98 | 2026-09-23 | 15 | =long_runs[[#This Row],[duration_mins]]-15
    Row 5: 102 | 2026-09-24 | 20 | =long_runs[[#This Row],[duration_mins]]-15
    Row 6: 103 | 2026-09-24 | 30 | =long_runs[[#This Row],[duration_mins]]-15
    Row 7: 104 | 2026-09-24 | 40 | =long_runs[[#This Row],[duration_mins]]-15
Sheet "long_per_day"
  Excel Table "long_per_day", A1:B3, loaded by Power Query "long_per_day"
    Headers: dt | runs
    Row 2: 2026-09-23 | 3
    Row 3: 2026-09-24 | 3
Power Query "long_runs" (loads into Excel Table "long_runs"):
    let
        Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Long = Table.SelectRows(Source, each [duration_mins] >= 15),
        Kept = Table.SelectColumns(Long, {"run_id", "dt", "duration_mins"})
    in
        Kept
Power Query "long_per_day" (loads into Excel Table "long_per_day"):
    let
        Grouped = Table.Group(long_runs, {"dt"}, {{"runs", each Table.RowCount(_), Int64.Type}})
    in
        Grouped
>>>

## X76

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x76.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
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
Sheet "finance_jobs"
  Excel Table "finance_jobs", A1:C3, loaded by Power Query "finance_jobs"
    Headers: job_id | job_name | label
    Row 2: 2 | invoice_sync | =UPPER(finance_jobs[[#This Row],[job_name]])
    Row 3: 3 | report_build | =UPPER(finance_jobs[[#This Row],[job_name]])
Sheet "finance_runs"
  Excel Table "finance_runs", A1:C6, loaded by Power Query "finance_runs"
    Headers: run_id | job_name | duration_mins
    Row 2: 96 | invoice_sync | 18
    Row 3: 97 | report_build | 30
    Row 4: 98 | invoice_sync | 15
    Row 5: 102 | invoice_sync | 20
    Row 6: 103 | report_build | 30
Power Query "finance_jobs" (loads into Excel Table "finance_jobs"):
    let
        Source = Excel.CurrentWorkbook(){[Name="jobs"]}[Content],
        Finance = Table.SelectRows(Source, each [team] = "finance"),
        Kept = Table.SelectColumns(Finance, {"job_id", "job_name"})
    in
        Kept
Power Query "finance_runs" (loads into Excel Table "finance_runs"):
    let
        Runs = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Joined = Table.NestedJoin(Runs, {"job_id"}, finance_jobs, {"job_id"}, "f",
            JoinKind.Inner),
        Expanded = Table.ExpandTableColumn(Joined, "f", {"job_name"}),
        Kept = Table.SelectColumns(Expanded, {"run_id", "job_name", "duration_mins"})
    in
        Kept
>>>

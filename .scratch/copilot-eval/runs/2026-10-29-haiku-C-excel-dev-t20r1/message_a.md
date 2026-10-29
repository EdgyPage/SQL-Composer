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
   reads. A query, or a Table another Table or query reads, is a step. A Table nothing reads
   is a final: one query each. Parameters and Keys are neither.
3. Start the reply with the map: Sources, Steps, Finals and the columns each final gives;
   then each value typed over a formula, each mark, each refusal, what was left alone, and
   each `<...>` to fill in.
4. Names: write a database as `<database>`; keep a Table name or header that is a plain name
   (letters, digits, _); put any other in snake case in brackets: header `Unit Price` is
   `<unit_price>`, Table `Sales Data` `<database>.<sales_data>`. Never guess one.
5. Write each final's Hive in its own ```sql block: each source a table, read for the
   columns the finals use, each step a CTE, `WITH step AS (...)`, the final's columns in its
   Table's order, each calculated one named with AS. The rows are a sample: filter only as a
   formula or query does.
6. A value typed over a formula in one row converts too: `CASE WHEN run_id = 97 THEN 100
   ELSE duration_mins / 60 END`, matching the row on its Keys columns. With no Keys row for
   that Table, match every typed column of the row, and say there is no Keys row. A Table
   with no value typed over a formula needs none.
7. A refused formula: `NULL AS its_header`; name it in the map, with why, and for a cell
   outside a Table say outside and the cell, such as C2. Anything files 11 and 12 don't list
   is refused too.
8. Then Toolbox code in a ```python block, by files 03, 04 and 05, and tell the user: take
   out of the workbook what you don't want converted; fill in each `<...>`; run
   `project.convert` on the Hive; its checked code wins where the two differ.

## Formulas

- `+ - * /` as they are; `^` POWER; `&` CONCAT(a, b); TRUE, FALSE, AND, OR, NOT as they are.
- IF as it is. IFS(c1, v1, c2, v2): `CASE WHEN c1 THEN v1 WHEN c2 THEN v2 END`.
  SWITCH(x, "a", 1, 0): `CASE x WHEN 'a' THEN 1 ELSE 0 END`.
- IFERROR(a / b, 0): COALESCE(a / b, 0), as Hive gives NULL for a divide by 0; IFNA(x, v)
  and XLOOKUP's fourth argument, v: COALESCE(x, v). ISBLANK(x): x IS NULL.
- ROUND, ABS, POWER, SQRT as they are; MOD(a, b): PMOD(a, b); INT: FLOOR; MIN(a, b) and
  MAX(a, b) of one row's cells: LEAST and GREATEST.
- LEFT(x, n): SUBSTR(x, 1, n); RIGHT(x, n): SUBSTR(x, -n); MID(x, s, n): SUBSTR(x, s, n);
  LEN: LENGTH; FIND(a, x): INSTR(x, a); SEARCH(a, x): INSTR(LOWER(x), LOWER(a)), as it
  ignores case; ISNUMBER(FIND(..)): INSTR(..) > 0; SUBSTITUTE: REPLACE; PROPER: INITCAP;
  CONCATENATE: CONCAT; TEXTJOIN(",", TRUE, a, b): CONCAT_WS(',', a, b); VALUE(x): CAST(x AS
  DOUBLE); UPPER, LOWER, TRIM as they are.
- YEAR, MONTH, DAY as they are; DATE(2026,9,1): '2026-09-01'; TODAY(): CURRENT_DATE; NOW():
  CURRENT_TIMESTAMP; d + n, d - n: DATE_ADD(d, n), DATE_SUB(d, n); DATEDIF(a, b, "d"):
  DATEDIFF(b, a), "m": FLOOR(MONTHS_BETWEEN(b, a)), "y": the same / 12; EOMONTH(d, 0):
  LAST_DAY(d); EDATE(d, n): ADD_MONTHS(d, n); WEEKDAY(d): DAYOFWEEK(d); TEXT(d, "yyyy-mm"):
  DATE_FORMAT(d, 'yyyy-MM'), Excel's month mm as MM.
- As month_start and week_start write them: DATE(YEAR(d), MONTH(d), 1) or EOMONTH(d, -1)+1:
  `CAST(TRUNC(d, 'MM') AS STRING)`; d-WEEKDAY(d,2)+1: `CAST(NEXT_DAY(DATE_ADD(d, 7 * -1),
  'MO') AS STRING)`.
- XLOOKUP(k, t[a], t[b]), VLOOKUP(k, t, n, FALSE), INDEX(t[b], MATCH(k, t[a], 0)):
  `LEFT JOIN t ON k = t.a`, then t.b. XLOOKUP("rate", Parameters[name], Parameters[value]):
  the value, 0.5.
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

- CROSS_JOIN(table, reads_all_partitions=False)
- SEMI_JOIN(table, ON=None, reads_all_partitions=False, broadcast=False)
- ANTI_JOIN(table, ON=None, reads_all_partitions=False, broadcast=False)
- row_number(*, PARTITION_BY=None, ORDER_BY=None, over=None)
- count_distinct(column, where=None)

## Steps

1. Follow file 11's steps, reading each query's steps in order, as below.
2. A query another query or a Table's formula reads is a step: a CTE, `WITH q AS (...)`. A
   query loaded into a Table nothing reads gives that final's rows. A connection-only query
   nothing reads is left out, and named.
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
  SUBSTR(x, s + 1, n), as M counts from 0; Number.Round, Number.Abs; Number.Mod: PMOD;
  Date.Year, Date.Month, Date.Day; Date.AddDays: DATE_ADD; Date.AddMonths: ADD_MONTHS;
  Date.EndOfMonth: LAST_DAY; Date.StartOfMonth: `CAST(TRUNC(d, 'MM') AS STRING)`.

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
- A Total Row, SUBTOTAL(109, ...) a SUM, 101 AVG, 102 or 103 COUNT, 104 MAX, 105 MIN: a final
  of its own, `<Table> (total row)`, one row: a column per total, in order, no label. On a
  summary whose totals each SUM a SUM or a COUNT, MAX a MAX or MIN a MIN: none of its own,
  but `GROUP BY a WITH ROLLUP` in the summary's query, the total row's a NULL.

## Order

- Table.Sort then FirstN: ORDER BY ... LIMIT, Order.Descending as DESC. FirstN alone: LIMIT.
- Table.AddIndexColumn(t, "n", 1, 1) after a Table.Sort: `ROW_NUMBER() OVER (ORDER BY ...)
  AS n`; inside a Table.Group's `each`, PARTITION BY its keys.
- A Table.Sort with no FirstN or index after it: no ORDER BY, as a Hive table holds no
  order; say the order was dropped.

## Marks: convert, and say so

- M reading Sql.Database or a non-workbook source: use the table it names; say which to check.
- Table.Pivot: a `SUM(CASE WHEN severity = 'high' THEN 1 END) AS high` column per value in
  the sample, NULL where none, as M leaves it; say the pivot's columns are now fixed.

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
    FROM(job_runs, reads_all_partitions=True),  # the query reads every row
    WHERE(is_not_null(job_runs.status), starts_with(job_runs.status, "SUCC")),
    GROUP_BY(job_runs.job_id),
    HAVING(more_than(count_rows(), 1)),
)
```

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

## X01

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x01.xlsx, as you read it:

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
  Excel Table "job_runs", A1:E10
    Headers: run_id | job_id | duration_mins | dt | duration_hours
    Row 2: 95 | 1 | 12 | 2026-09-23 | =[@duration_mins]/60
    Row 3: 96 | 2 | 18 | 2026-09-23 | =[@duration_mins]/60
    Row 4: 97 | 3 | 30 | 2026-09-23 | =[@duration_mins]/60
    Row 5: 98 | 2 | 15 | 2026-09-23 | =[@duration_mins]/60
    Row 6: 99 | 1 | 5 | 2026-09-23 | =[@duration_mins]/60
    Row 7: 101 | 1 | 10 | 2026-09-24 | =[@duration_mins]/60
    Row 8: 102 | 2 | 20 | 2026-09-24 | =[@duration_mins]/60
    Row 9: 103 | 3 | 30 | 2026-09-24 | =[@duration_mins]/60
    Row 10: 104 | 1 | 40 | 2026-09-24 | =[@duration_mins]/60
>>>

## X02

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x02.xlsx, as you read it:

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
    Headers: run_id | job_id | status | duration_mins | slow_job1 | flag
    Row 2: 95 | 1 | SUCCESS | 12 | =AND(job_runs[[#This Row],[duration_mins]]>10,job_runs[[#This Row],[job_id]]=1) | =IF(OR(job_runs[[#This Row],[duration_mins]]>25,job_runs[[#This Row],[job_id]]=3),"check","ok")
    Row 3: 96 | 2 | SUCCESS | 18 | =AND(job_runs[[#This Row],[duration_mins]]>10,job_runs[[#This Row],[job_id]]=1) | =IF(OR(job_runs[[#This Row],[duration_mins]]>25,job_runs[[#This Row],[job_id]]=3),"check","ok")
    Row 4: 97 | 3 | FAILED | 30 | =AND(job_runs[[#This Row],[duration_mins]]>10,job_runs[[#This Row],[job_id]]=1) | =IF(OR(job_runs[[#This Row],[duration_mins]]>25,job_runs[[#This Row],[job_id]]=3),"check","ok")
    Row 5: 98 | 2 |  | 15 | =AND(job_runs[[#This Row],[duration_mins]]>10,job_runs[[#This Row],[job_id]]=1) | =IF(OR(job_runs[[#This Row],[duration_mins]]>25,job_runs[[#This Row],[job_id]]=3),"check","ok")
    Row 6: 99 | 1 | TEST | 5 | =AND(job_runs[[#This Row],[duration_mins]]>10,job_runs[[#This Row],[job_id]]=1) | =IF(OR(job_runs[[#This Row],[duration_mins]]>25,job_runs[[#This Row],[job_id]]=3),"check","ok")
    Row 7: 101 | 1 | SUCCESS | 10 | =AND(job_runs[[#This Row],[duration_mins]]>10,job_runs[[#This Row],[job_id]]=1) | =IF(OR(job_runs[[#This Row],[duration_mins]]>25,job_runs[[#This Row],[job_id]]=3),"check","ok")
    Row 8: 102 | 2 | FAILED | 20 | =AND(job_runs[[#This Row],[duration_mins]]>10,job_runs[[#This Row],[job_id]]=1) | =IF(OR(job_runs[[#This Row],[duration_mins]]>25,job_runs[[#This Row],[job_id]]=3),"check","ok")
    Row 9: 103 | 3 | SUCCESS | 30 | =AND(job_runs[[#This Row],[duration_mins]]>10,job_runs[[#This Row],[job_id]]=1) | =IF(OR(job_runs[[#This Row],[duration_mins]]>25,job_runs[[#This Row],[job_id]]=3),"check","ok")
    Row 10: 104 | 1 | SUCCESS | 40 | =AND(job_runs[[#This Row],[duration_mins]]>10,job_runs[[#This Row],[job_id]]=1) | =IF(OR(job_runs[[#This Row],[duration_mins]]>25,job_runs[[#This Row],[job_id]]=3),"check","ok")
>>>

## X03

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x03.xlsx, as you read it:

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
    Headers: run_id | job_id | status | duration_mins | avg_retry_secs | dt | score | mins_per_retry | total_secs
    Row 2: 95 | 1 | SUCCESS | 12 | 2 | 2026-09-23 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS",1,"FAILED",-1,0) | =IFERROR(job_runs[[#This Row],[duration_mins]]/job_runs[[#This Row],[avg_retry_secs]],0) | =job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]]
    Row 3: 96 | 2 | SUCCESS | 18 | 0 | 2026-09-23 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS",1,"FAILED",-1,0) | =IFERROR(job_runs[[#This Row],[duration_mins]]/job_runs[[#This Row],[avg_retry_secs]],0) | =job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]]
    Row 4: 97 | 3 | FAILED | 30 | 8 | 2026-09-23 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS",1,"FAILED",-1,0) | =IFERROR(job_runs[[#This Row],[duration_mins]]/job_runs[[#This Row],[avg_retry_secs]],0) | =job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]]
    Row 5: 98 | 2 |  | 15 |  | 2026-09-23 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS",1,"FAILED",-1,0) | =IFERROR(job_runs[[#This Row],[duration_mins]]/job_runs[[#This Row],[avg_retry_secs]],0) | =job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]]
    Row 6: 99 | 1 | TEST | 5 | 0 | 2026-09-23 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS",1,"FAILED",-1,0) | =IFERROR(job_runs[[#This Row],[duration_mins]]/job_runs[[#This Row],[avg_retry_secs]],0) | =job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]]
    Row 7: 101 | 1 | SUCCESS | 10 | 1 | 2026-09-24 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS",1,"FAILED",-1,0) | =IFERROR(job_runs[[#This Row],[duration_mins]]/job_runs[[#This Row],[avg_retry_secs]],0) | =job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]]
    Row 8: 102 | 2 | FAILED | 20 | 6 | 2026-09-24 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS",1,"FAILED",-1,0) | =IFERROR(job_runs[[#This Row],[duration_mins]]/job_runs[[#This Row],[avg_retry_secs]],0) | =job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]]
    Row 9: 103 | 3 | SUCCESS | 30 | 0 | 2026-09-24 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS",1,"FAILED",-1,0) | =IFERROR(job_runs[[#This Row],[duration_mins]]/job_runs[[#This Row],[avg_retry_secs]],0) | =job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]]
    Row 10: 104 | 1 | SUCCESS | 40 | 3 | 2026-09-24 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS",1,"FAILED",-1,0) | =IFERROR(job_runs[[#This Row],[duration_mins]]/job_runs[[#This Row],[avg_retry_secs]],0) | =job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]]
>>>

## X04

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x04.xlsx, as you read it:

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
  Excel Table "jobs", A1:H5
    Headers: job_id | job_name | team | region | code | name_length | third | odd
    Row 2: 1 | nightly_load | data | LON | =UPPER(LEFT(jobs[[#This Row],[job_name]],3))&"-"&jobs[[#This Row],[region]] | =LEN(jobs[[#This Row],[job_name]]) | =ROUND(jobs[[#This Row],[job_id]]/3,2) | =MOD(jobs[[#This Row],[job_id]],2)
    Row 3: 2 | invoice_sync | finance | PAR | =UPPER(LEFT(jobs[[#This Row],[job_name]],3))&"-"&jobs[[#This Row],[region]] | =LEN(jobs[[#This Row],[job_name]]) | =ROUND(jobs[[#This Row],[job_id]]/3,2) | =MOD(jobs[[#This Row],[job_id]],2)
    Row 4: 3 | report_build | finance | NYC | =UPPER(LEFT(jobs[[#This Row],[job_name]],3))&"-"&jobs[[#This Row],[region]] | =LEN(jobs[[#This Row],[job_name]]) | =ROUND(jobs[[#This Row],[job_id]]/3,2) | =MOD(jobs[[#This Row],[job_id]],2)
    Row 5: 4 | cache_warm | web | LON | =UPPER(LEFT(jobs[[#This Row],[job_name]],3))&"-"&jobs[[#This Row],[region]] | =LEN(jobs[[#This Row],[job_name]]) | =ROUND(jobs[[#This Row],[job_id]]/3,2) | =MOD(jobs[[#This Row],[job_id]],2)
>>>

## X05

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x05.xlsx, as you read it:

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
  Excel Table "job_runs", A1:D10
    Headers: run_id | dt | month | days_since
    Row 2: 95 | 2026-09-23 | =MONTH(job_runs[[#This Row],[dt]]) | =DATEDIF(DATE(2026,9,1),job_runs[[#This Row],[dt]],"d")
    Row 3: 96 | 2026-09-23 | =MONTH(job_runs[[#This Row],[dt]]) | =DATEDIF(DATE(2026,9,1),job_runs[[#This Row],[dt]],"d")
    Row 4: 97 | 2026-09-23 | =MONTH(job_runs[[#This Row],[dt]]) | =DATEDIF(DATE(2026,9,1),job_runs[[#This Row],[dt]],"d")
    Row 5: 98 | 2026-09-23 | =MONTH(job_runs[[#This Row],[dt]]) | =DATEDIF(DATE(2026,9,1),job_runs[[#This Row],[dt]],"d")
    Row 6: 99 | 2026-09-23 | =MONTH(job_runs[[#This Row],[dt]]) | =DATEDIF(DATE(2026,9,1),job_runs[[#This Row],[dt]],"d")
    Row 7: 101 | 2026-09-24 | =MONTH(job_runs[[#This Row],[dt]]) | =DATEDIF(DATE(2026,9,1),job_runs[[#This Row],[dt]],"d")
    Row 8: 102 | 2026-09-24 | =MONTH(job_runs[[#This Row],[dt]]) | =DATEDIF(DATE(2026,9,1),job_runs[[#This Row],[dt]],"d")
    Row 9: 103 | 2026-09-24 | =MONTH(job_runs[[#This Row],[dt]]) | =DATEDIF(DATE(2026,9,1),job_runs[[#This Row],[dt]],"d")
    Row 10: 104 | 2026-09-24 | =MONTH(job_runs[[#This Row],[dt]]) | =DATEDIF(DATE(2026,9,1),job_runs[[#This Row],[dt]],"d")
Sheet "region_costs"
  Excel Table "region_costs", A1:E29
    Headers: job_id | cost_cents | region | dt | day
    Row 2: 1 | 120 | eu | 20260911 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 3: 2 | 180 | eu | 20260911 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 4: 3 | 300 | us | 20260911 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 5: 1 | 110 | eu | 20260912 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 6: 1 | 130 | eu | 20260913 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 7: 1 | 120 | eu | 20260914 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 8: 2 | 200 | eu | 20260914 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 9: 3 | 410 | us | 20260914 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 10: 1 | 100 | eu | 20260915 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 11: 2 | 170 | eu | 20260915 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 12: 1 | 250 | eu | 20260916 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 13: 2 | 190 | eu | 20260916 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 14: 1 | 120 | eu | 20260917 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 15: 2 | 160 | eu | 20260917 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 16: 1 | 140 | eu | 20260918 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 17: 2 | 220 | eu | 20260918 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 18: 3 | 120 | us | 20260918 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 19: 1 | 110 | eu | 20260919 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 20: 1 | 120 | eu | 20260920 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 21: 1 | 130 | eu | 20260921 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 22: 2 | 210 | eu | 20260921 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 23: 3 | 330 | us | 20260921 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 24: 1 | 100 | eu | 20260922 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 25: 2 | 180 | eu | 20260922 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 26: 1 | 120 | eu | 20260923 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 27: 2 | 180 | eu | 20260923 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 28: 1 | 100 | eu | 20260924 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 29: 2 |  | eu | 20260924 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
>>>

## X06

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x06.xlsx, as you read it:

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
  Excel Table "job_runs", A1:E10
    Headers: run_id | job_id | duration_mins | job_name | runs_of_job
    Row 2: 95 | 1 | 12 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]])
    Row 3: 96 | 2 | 18 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]])
    Row 4: 97 | 3 | 30 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]])
    Row 5: 98 | 2 | 15 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]])
    Row 6: 99 | 1 | 5 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]])
    Row 7: 101 | 1 | 10 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]])
    Row 8: 102 | 2 | 20 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]])
    Row 9: 103 | 3 | 30 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]])
    Row 10: 104 | 1 | 40 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]])
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
>>>

## X07

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x07.xlsx, as you read it:

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
  Excel Table "job_runs", A1:E10
    Headers: run_id | job_id | status | team | region
    Row 2: 95 | 1 | SUCCESS | =VLOOKUP([@job_id],jobs,3,FALSE) | =INDEX(jobs[region],MATCH([@job_id],jobs[job_id],0))
    Row 3: 96 | 2 | SUCCESS | =VLOOKUP([@job_id],jobs,3,FALSE) | =INDEX(jobs[region],MATCH([@job_id],jobs[job_id],0))
    Row 4: 97 | 3 | FAILED | =VLOOKUP([@job_id],jobs,3,FALSE) | =INDEX(jobs[region],MATCH([@job_id],jobs[job_id],0))
    Row 5: 98 | 2 |  | =VLOOKUP([@job_id],jobs,3,FALSE) | =INDEX(jobs[region],MATCH([@job_id],jobs[job_id],0))
    Row 6: 99 | 1 | TEST | =VLOOKUP([@job_id],jobs,3,FALSE) | =INDEX(jobs[region],MATCH([@job_id],jobs[job_id],0))
    Row 7: 101 | 1 | SUCCESS | =VLOOKUP([@job_id],jobs,3,FALSE) | =INDEX(jobs[region],MATCH([@job_id],jobs[job_id],0))
    Row 8: 102 | 2 | FAILED | =VLOOKUP([@job_id],jobs,3,FALSE) | =INDEX(jobs[region],MATCH([@job_id],jobs[job_id],0))
    Row 9: 103 | 3 | SUCCESS | =VLOOKUP([@job_id],jobs,3,FALSE) | =INDEX(jobs[region],MATCH([@job_id],jobs[job_id],0))
    Row 10: 104 | 1 | SUCCESS | =VLOOKUP([@job_id],jobs,3,FALSE) | =INDEX(jobs[region],MATCH([@job_id],jobs[job_id],0))
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
>>>

## X08

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x08.xlsx, as you read it:

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
  Excel Table "by_job", A1:D4
    Headers: job_id | total_mins | avg_retry | longest
    Row 2: 1 | =SUMIFS(job_runs[duration_mins],job_runs[job_id],by_job[[#This Row],[job_id]]) | =AVERAGEIFS(job_runs[avg_retry_secs],job_runs[job_id],by_job[[#This Row],[job_id]]) | =_xlfn.MAXIFS(job_runs[duration_mins],job_runs[job_id],by_job[[#This Row],[job_id]])
    Row 3: 2 | =SUMIFS(job_runs[duration_mins],job_runs[job_id],by_job[[#This Row],[job_id]]) | =AVERAGEIFS(job_runs[avg_retry_secs],job_runs[job_id],by_job[[#This Row],[job_id]]) | =_xlfn.MAXIFS(job_runs[duration_mins],job_runs[job_id],by_job[[#This Row],[job_id]])
    Row 4: 3 | =SUMIFS(job_runs[duration_mins],job_runs[job_id],by_job[[#This Row],[job_id]]) | =AVERAGEIFS(job_runs[avg_retry_secs],job_runs[job_id],by_job[[#This Row],[job_id]]) | =_xlfn.MAXIFS(job_runs[duration_mins],job_runs[job_id],by_job[[#This Row],[job_id]])
>>>

## X09

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x09.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2: rate | 0.5
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2: job_runs | run_id
Sheet "job_runs"
  Excel Table "job_runs", A1:G10
    Headers: run_id | job_id | duration_mins | avg_retry_secs | team | team_mins | cost
    Row 2: 95 | 1 | 12 | 2 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =SUMIFS(job_runs[duration_mins],job_runs[team],job_runs[[#This Row],[team]]) | =(job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]])*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 3: 96 | 2 | 18 | 0 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =SUMIFS(job_runs[duration_mins],job_runs[team],job_runs[[#This Row],[team]]) | =(job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]])*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 4: 97 | 3 | 30 | 8 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =SUMIFS(job_runs[duration_mins],job_runs[team],job_runs[[#This Row],[team]]) | 100
    Row 5: 98 | 2 | 15 |  | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =SUMIFS(job_runs[duration_mins],job_runs[team],job_runs[[#This Row],[team]]) | =(job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]])*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 6: 99 | 1 | 5 | 0 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =SUMIFS(job_runs[duration_mins],job_runs[team],job_runs[[#This Row],[team]]) | =(job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]])*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 7: 101 | 1 | 10 | 1 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =SUMIFS(job_runs[duration_mins],job_runs[team],job_runs[[#This Row],[team]]) | =(job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]])*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 8: 102 | 2 | 20 | 6 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =SUMIFS(job_runs[duration_mins],job_runs[team],job_runs[[#This Row],[team]]) | =(job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]])*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 9: 103 | 3 | 30 | 0 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =SUMIFS(job_runs[duration_mins],job_runs[team],job_runs[[#This Row],[team]]) | =(job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]])*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 10: 104 | 1 | 40 | 3 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =SUMIFS(job_runs[duration_mins],job_runs[team],job_runs[[#This Row],[team]]) | =(job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]])*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
>>>

## X10

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x10.xlsx, as you read it:

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
    Headers: run_id | job_id | duration_mins | dt | hours | sample
    Row 2: 95 | 1 | 12 | 2026-09-23 | =job_runs[[#This Row],[duration_mins]]/60 | =RAND()
    Row 3: 96 | 2 | 18 | 2026-09-23 | =job_runs[[#This Row],[duration_mins]]/60 | =RAND()
    Row 4: 97 | 3 | 30 | 2026-09-23 | =job_runs[[#This Row],[duration_mins]]/60 | =RAND()
    Row 5: 98 | 2 | 15 | 2026-09-23 | =job_runs[[#This Row],[duration_mins]]/60 | =RAND()
    Row 6: 99 | 1 | 5 | 2026-09-23 | =job_runs[[#This Row],[duration_mins]]/60 | =RAND()
    Row 7: 101 | 1 | 10 | 2026-09-24 | =job_runs[[#This Row],[duration_mins]]/60 | =RAND()
    Row 8: 102 | 2 | 20 | 2026-09-24 | =job_runs[[#This Row],[duration_mins]]/60 | =RAND()
    Row 9: 103 | 3 | 30 | 2026-09-24 | 9 | =RAND()
    Row 10: 104 | 1 | 40 | 2026-09-24 | =job_runs[[#This Row],[duration_mins]]/60 | =RAND()
>>>

## X11

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x11.xlsx, as you read it:

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
  Excel Table "job_runs", A1:D10
    Headers: run_id | duration_mins | pick | scaled
    Row 2: 95 | 12 | =INDIRECT("B"&ROW()) | =job_runs[[#This Row],[duration_mins]]*Summary!$C$2
    Row 3: 96 | 18 | =INDIRECT("B"&ROW()) | =job_runs[[#This Row],[duration_mins]]*Summary!$C$2
    Row 4: 97 | 30 | =INDIRECT("B"&ROW()) | =job_runs[[#This Row],[duration_mins]]*Summary!$C$2
    Row 5: 98 | 15 | =INDIRECT("B"&ROW()) | =job_runs[[#This Row],[duration_mins]]*Summary!$C$2
    Row 6: 99 | 5 | =INDIRECT("B"&ROW()) | =job_runs[[#This Row],[duration_mins]]*Summary!$C$2
    Row 7: 101 | 10 | =INDIRECT("B"&ROW()) | =job_runs[[#This Row],[duration_mins]]*Summary!$C$2
    Row 8: 102 | 20 | =INDIRECT("B"&ROW()) | =job_runs[[#This Row],[duration_mins]]*Summary!$C$2
    Row 9: 103 | 30 | =INDIRECT("B"&ROW()) | =job_runs[[#This Row],[duration_mins]]*Summary!$C$2
    Row 10: 104 | 40 | =INDIRECT("B"&ROW()) | =job_runs[[#This Row],[duration_mins]]*Summary!$C$2
Sheet "Summary"
  C2: 3
  A bar chart
>>>

## X12

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x12.xlsx, as you read it:

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
  Excel Table "job_runs", A1:E10
    Headers: run_id | duration_mins | running | loop | with_tax
    Row 2: 95 | 12 | =SUM(OFFSET(job_runs[[#Headers],[duration_mins]],1,0,ROW()-1,1)) | =job_runs[[#This Row],[loop]]+1 | =job_runs[[#This Row],[duration_mins]]*tax_rate
    Row 3: 96 | 18 | =SUM(OFFSET(job_runs[[#Headers],[duration_mins]],1,0,ROW()-1,1)) | =job_runs[[#This Row],[loop]]+1 | =job_runs[[#This Row],[duration_mins]]*tax_rate
    Row 4: 97 | 30 | =SUM(OFFSET(job_runs[[#Headers],[duration_mins]],1,0,ROW()-1,1)) | =job_runs[[#This Row],[loop]]+1 | =job_runs[[#This Row],[duration_mins]]*tax_rate
    Row 5: 98 | 15 | =SUM(OFFSET(job_runs[[#Headers],[duration_mins]],1,0,ROW()-1,1)) | =job_runs[[#This Row],[loop]]+1 | =job_runs[[#This Row],[duration_mins]]*tax_rate
    Row 6: 99 | 5 | =SUM(OFFSET(job_runs[[#Headers],[duration_mins]],1,0,ROW()-1,1)) | =job_runs[[#This Row],[loop]]+1 | =job_runs[[#This Row],[duration_mins]]*tax_rate
    Row 7: 101 | 10 | =SUM(OFFSET(job_runs[[#Headers],[duration_mins]],1,0,ROW()-1,1)) | =job_runs[[#This Row],[loop]]+1 | =job_runs[[#This Row],[duration_mins]]*tax_rate
    Row 8: 102 | 20 | =SUM(OFFSET(job_runs[[#Headers],[duration_mins]],1,0,ROW()-1,1)) | =job_runs[[#This Row],[loop]]+1 | =job_runs[[#This Row],[duration_mins]]*tax_rate
    Row 9: 103 | 30 | =SUM(OFFSET(job_runs[[#Headers],[duration_mins]],1,0,ROW()-1,1)) | =job_runs[[#This Row],[loop]]+1 | =job_runs[[#This Row],[duration_mins]]*tax_rate
    Row 10: 104 | 40 | =SUM(OFFSET(job_runs[[#Headers],[duration_mins]],1,0,ROW()-1,1)) | =job_runs[[#This Row],[loop]]+1 | =job_runs[[#This Row],[duration_mins]]*tax_rate
Sheet "Summary"
  B3: 0.2
Defined name tax_rate: Summary!$B$3
>>>

## X13

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x13.xlsx, as you read it:

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
  Excel Table "job_runs", A1:D10
    Headers: run_id | job_id | name | doubled
    Row 2: 95 | 1 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE) | =DOUBLE(job_runs[[#This Row],[job_id]])
    Row 3: 96 | 2 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE) | =DOUBLE(job_runs[[#This Row],[job_id]])
    Row 4: 97 | 3 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE) | =DOUBLE(job_runs[[#This Row],[job_id]])
    Row 5: 98 | 2 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE) | =DOUBLE(job_runs[[#This Row],[job_id]])
    Row 6: 99 | 1 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE) | =DOUBLE(job_runs[[#This Row],[job_id]])
    Row 7: 101 | 1 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE) | =DOUBLE(job_runs[[#This Row],[job_id]])
    Row 8: 102 | 2 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE) | =DOUBLE(job_runs[[#This Row],[job_id]])
    Row 9: 103 | 3 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE) | =DOUBLE(job_runs[[#This Row],[job_id]])
    Row 10: 104 | 1 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE) | =DOUBLE(job_runs[[#This Row],[job_id]])
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
Defined name DOUBLE: _xlfn.LAMBDA(x,x*2)
>>>

## X14

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x14.xlsx, as you read it:

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
    Headers: run_id | job_id | status | duration_mins | avg_retry_secs | dt | hours
    Row 2: 95 | 1 | SUCCESS | 12 | 2 | 2026-09-23 | =job_runs[[#This Row],[duration_mins]]/60
    Row 3: 96 | 2 | SUCCESS | 18 | 0 | 2026-09-23 | =job_runs[[#This Row],[duration_mins]]/60
    Row 4: 97 | 3 | FAILED | 30 | 8 | 2026-09-23 | =job_runs[[#This Row],[duration_mins]]/60
    Row 5: 98 | 2 |  | 15 |  | 2026-09-23 | =job_runs[[#This Row],[duration_mins]]/60
    Row 6: 99 | 1 | TEST | 5 | 0 | 2026-09-23 | =job_runs[[#This Row],[duration_mins]]/60
    Row 7: 101 | 1 | SUCCESS | 10 | 1 | 2026-09-24 | =job_runs[[#This Row],[duration_mins]]/60
    Row 8: 102 | 2 | FAILED | 20 | 6 | 2026-09-24 | =job_runs[[#This Row],[duration_mins]]/60
    Row 9: 103 | 3 | SUCCESS | 30 | 0 | 2026-09-24 | =job_runs[[#This Row],[duration_mins]]/60
    Row 10: 104 | 1 | SUCCESS | 40 | 3 | 2026-09-24 | =job_runs[[#This Row],[duration_mins]]/60
Sheet "by_job"
  Excel Table "by_job", A1:B4
    Headers: job_id | total_hours
    Row 2: 1 | =SUMIFS(job_runs[hours],job_runs[job_id],by_job[[#This Row],[job_id]])
    Row 3: 2 | =SUMIFS(job_runs[hours],job_runs[job_id],by_job[[#This Row],[job_id]])
    Row 4: 3 | =SUMIFS(job_runs[hours],job_runs[job_id],by_job[[#This Row],[job_id]])
Also in the workbook: a PivotTable on sheet "Pivot", from Table job_runs: rows job_id, values Sum of duration_mins
>>>

## X15

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x15.xlsx, as you read it:

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
Sheet "tblRuns"
  Excel Table "tblRuns", A1:D10
    Headers: Run ID | Job ID | Duration (mins) | Hours
    Row 2: 95 | 1 | 12 | =[@[Duration (mins)]]/60
    Row 3: 96 | 2 | 18 | =[@[Duration (mins)]]/60
    Row 4: 97 | 3 | 30 | =[@[Duration (mins)]]/60
    Row 5: 98 | 2 | 15 | =[@[Duration (mins)]]/60
    Row 6: 99 | 1 | 5 | =[@[Duration (mins)]]/60
    Row 7: 101 | 1 | 10 | =[@[Duration (mins)]]/60
    Row 8: 102 | 2 | 20 | =[@[Duration (mins)]]/60
    Row 9: 103 | 3 | 30 | =[@[Duration (mins)]]/60
    Row 10: 104 | 1 | 40 | =[@[Duration (mins)]]/60
>>>

## X16

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x16.xlsx, as you read it:

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
  Excel Table "long_runs", A1:D6, loaded by Power Query "long_runs"
    Headers: run_id | job_id | minutes | hours
    Row 2: 96 | 2 | 18 | 0.3
    Row 3: 97 | 3 | 30 | 0.5
    Row 4: 102 | 2 | 20 | 0.3333333333333333
    Row 5: 103 | 3 | 30 | 0.5
    Row 6: 104 | 1 | 40 | 0.6666666666666666
Power Query "long_runs" (loads into Excel Table "long_runs"):
    let
        Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Kept = Table.SelectColumns(Source, {"run_id", "job_id", "duration_mins"}),
        Long = Table.SelectRows(Kept, each [duration_mins] > 15),
        Hours = Table.AddColumn(Long, "hours", each [duration_mins] / 60, type number),
        Renamed = Table.RenameColumns(Hours, {{"duration_mins", "minutes"}})
    in
        Renamed
>>>

## X17

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x17.xlsx, as you read it:

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
Sheet "ok_by_job"
  Excel Table "ok_by_job", A1:C4, loaded by Power Query "ok_by_job"
    Headers: job_id | runs | total_mins
    Row 2: 1 | 3 | 62
    Row 3: 2 | 1 | 18
    Row 4: 3 | 1 | 30
Power Query "ok_runs" (connection only):
    let
        Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Succeeded = Table.SelectRows(Source, each [status] = "SUCCESS")
    in
        Succeeded
Power Query "ok_by_job" (loads into Excel Table "ok_by_job"):
    let
        Source = ok_runs,
        Grouped = Table.Group(Source, {"job_id"}, {
            {"runs", each Table.RowCount(_), Int64.Type},
            {"total_mins", each List.Sum([duration_mins]), type number}})
    in
        Grouped
>>>

## X18

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x18.xlsx, as you read it:

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
Sheet "top_runs"
  Excel Table "top_runs", A1:C4, loaded by Power Query "top_runs"
    Headers: run_id | job_name | duration_mins
    Row 2: 104 | nightly_load | 40
    Row 3: 97 | report_build | 30
    Row 4: 103 | report_build | 30
Power Query "top_runs" (loads into Excel Table "top_runs"):
    let
        Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Jobs = Excel.CurrentWorkbook(){[Name="jobs"]}[Content],
        Joined = Table.NestedJoin(Source, {"job_id"}, Jobs, {"job_id"}, "job", JoinKind.LeftOuter),
        Expanded = Table.ExpandTableColumn(Joined, "job", {"job_name"}),
        Sorted = Table.Sort(Expanded, {{"duration_mins", Order.Descending}}),
        Top = Table.FirstN(Sorted, 3),
        Kept = Table.SelectColumns(Top, {"run_id", "job_name", "duration_mins"})
    in
        Kept
>>>

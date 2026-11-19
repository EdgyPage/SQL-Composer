# Power Query and totals into Hive, in code

Type: task
Status: resolved
Blocked by: 03, 04
Size: XL

## Question

The code path's second half for M and totals: file 12's rules, written by the Toolbox.

## Done when

- **M read** as file 12's Terms say: a `let` of named steps, each reading the one before, `in`
  naming the one it gives; another query's name a CTE (Q1). Only what file 12's rules list is
  read; any other step is refused, its columns NULL or the query left out, named with why.
- **Each rule of file 12 by its ID**, Q1 to Q7, G1 to G5, T1 to T4, S1 to S3, M1, M2, X1.
- **Total Rows** each a final of their own (T2), reading the Table's final as a CTE.
- Tests: one per rule ID; file 12's Worked patterns each as a test; the three
  `tests/fixtures/workbook_text/` workbooks' saved queries converted.

## Answer

**Built.** Four new files in the Toolbox's folder (split so after the review), all in the
registry's `PYTHON_FILES`, the three that name sqlglot's trees in `LIBRARY_FILES` too (and in
`docs/agents/standards.md`'s list); no public name.

- `sqlglot_composer/workbook_m_reader.py` (standard library alone): `read_m(m)` reads a
  query's M into a small tree (`MValue`, `MName`, `MField`, `MItem`, `MCall`, `MList`,
  `MRecord`, `MEach`, `MIf`, `MOperation`, `MNot`, `MNegative`, `MLet`, `MType`) by M's grammar
  and M's operator order, through `m_tokens` and `MReader`. A column in brackets with a space
  (`[Unit Price]`) is one piece. A function of the query's own (`(x) => ..`), `try`, `error`,
  `meta`, `as`, `is` and a range `{a..b}` are refused (`Refused`, X1).
- `sqlglot_composer/workbook_power_query.py`, file 12's M rules by ID (Q1 to Q7, G1 to G5,
  S1 to S3, M1, M2, X1):
  - `power_query_hive(name, book)` gives a query's SELECT and its Notes, or raises `Refused`
    (the query left out). Each step is written into the SELECT the step before built
    (`Rows`: FROM, joins, WHERE, GROUP BY, HAVING, a pending sort, LIMIT, DISTINCT, columns of
    tables a NestedJoin or a Group made, each column's sample), and that SELECT is read in
    brackets only where the rows need it (`ready_rows`, `facets_of`), as a filter after a
    FirstN. `TABLE_STEPS` maps each Table function file 12 lists to its writer; steps are read
    from `in`, each once (`named_rows`). Another query is read by its CTE's name, its columns
    and sample from its own M (`query_read`).
  - `web_source(m)`: X1's web sources.
- `sqlglot_composer/workbook_totals.py`, file 12's T1 to T4:
  - `WHOLE_COLUMN_FUNCTIONS` (T1), added in `_functions()`: SUM, AVERAGE, COUNT, COUNTA, MIN,
    MAX, STDEV.S, VAR.S of one whole column, and SUMPRODUCT of whole columns alone; anything
    else falls to file 11's writer in `FUNCTIONS`.
  - `total_row_finals(workbook, queries, book, left_out)` (T2 to T4), and `TOTAL_ROW`, moved
    here from `workbook_hive.py`, which imports it.
- `sqlglot_composer/lean_hive.py`, which knows nothing of M or workbooks: `lean_ctes(query,
  whole)`, `passed_through(query)`, `columns_read_after(query, cte)` and `with_ctes(query,
  ctes)`, ticket 17's rules (below), for tickets 06 and 17 to use on any query's tree.
- `sqlglot_composer/workbook_hive.py`, at the seam: `_power_query_tree` calls
  `power_query_hive` (a refusal is a REFUSED Note, `left out: <why>`; a left-out P8 query
  reaching the web is named REFUSED X1 too); `workbook_hive` calls `total_row_finals` with
  every Table's query (steps' too, so a step Table's Total Row reads its step as a CTE), in
  place of ticket 04's `_total_row_finals`; `_functions()` adds T1's. Outside the seam: **ticket 04's workaround is gone**: sources are
  read in the Order, as ticket 03's reader sees a bare Table name, and X07 and X13 still pass;
  `workbook_hive(.., total_rows_left_out=())` is T3's say-so; each final goes through
  `lean_ctes`; `map_text` names each Total Row final, with its columns, among the Finals (file
  15's W3). `workbook_formulas.py`: two refusal texts that said T1 "isn't written yet" now say
  what isn't listed; `EXCEL_AGGREGATES`, the one table of Excel's aggregates that `IFS_FORMS`,
  T1 and T2 read; `check_argument_count`, which `call_arguments` and the M steps both call.

**Tested** in `tests/test_workbook_power_query.py`, 125 tests: one or more per rule ID, each
named for it (Q1 to Q7 with 26 of Q7's twins, G1 to G5 with all six JoinKinds, T1 to T4, S1 to
S3, M1, M2, X1 with nine refusals), the M reader, file 12's W1 and W2, the three fixtures (01
and 02 converted, 03 refused by the reader's LoopError), and **every Excel evaluation task with
a Power Query, a whole-column total or a Total Row, 39 of them (dev and held out)**, read from
`formula_workbook.saved` and scored by `excel_eval.score`: all 39 pass, and ticket 04's 45
formula tasks still do. Three of ticket 04's tests changed with the behaviour: P9 and file 15's
W2 now convert, and P2's step CTE is lean. `tests/snapshot/known.txt`: 159 hashes added, 5
removed that only ticket 04's tests made and no test makes now; `tests/workers.py` groups the
new stand-in Hive fixture.

**Read differently from file 12, or beyond it, and why (for ticket 13):**

- **Q2:** `<>` between two columns is refused: M keeps a row where one is null and the other
  isn't, and drops it where both are. File 12 writes only a column against a constant. Either
  the file says so, or both paths write `(a <> b OR (a IS NULL) <> (b IS NULL))`.
- **Q3:** a third argument (a Comparer) is refused, not listed; `%` and `_` in the text are
  escaped in the LIKE.
- **Q4:** `List.Contains(u[k], [k])` is a join only as one of a SelectRows' conditions joined
  by `and`, or `not` of one; anywhere else refused (Q4).
- **Q6:** Table.TransformColumns takes a function's name or an `each` (`each _ * 10`).
- **Q7:** Text.Middle and Date.AddYears are written as the file writes them, `SUBSTR(x, s + 1,
  n)` and `ADD_MONTHS(d, 12 * n)`, with two numbers the M gives worked out
  (`SUBSTR(status, 2, 2)`, `ADD_MONTHS(dt, 24)`), after the review.
- **G2:** RightOuter is the file's LEFT JOIN with the tables swapped (X44's reference writes
  RIGHT JOIN; the rows agree). Aliases come from the NestedJoin's new column name for M's
  second table, as the person named it.
- **G3:** INTERSECT and EXCEPT only inside a Table.Distinct, as the file says; a NestedJoin on
  every column without one is G2's join.
- **G4:** Table.Combine lines the tables' columns up by name, NULL where one has none, as M
  does; the file doesn't say.
- **G5:** the measure and amount columns come after the kept ones; the file doesn't say.
- **S1, S3:** a sort stays pending through filters and column steps, and is dropped (S3) at a
  Group, a join, a Combine, a Pivot or an Unpivot, or the query's end.
- **S2:** an index starting or counting other than 1, 1 is `(ROW_NUMBER() OVER (..) - 1) *
  step + start`, and M's default start is 0: the file lists only 1, 1.
- **M1:** Sql.Database, and Oracle's, PostgreSQL's and MySQL's `.Database`, read the Item
  named as `<database>.<item>`: the person's database, not the M's database argument. A native
  query (`[Query=..]`) is refused. Its columns are what the steps name, else the Table it
  loads.
- **M2:** the pivot's values are the sample's, in the order they first appear, a blank left
  out; List.Count is `SUM(CASE .. THEN 1 END)`, List.Max, Min and Average their aggregate.
- **X1:** a column a refused step makes is NULL (AddIndexColumn with no sort, FillDown's and
  FillUp's columns, List.Median, an M function not listed); a step that changes the rows
  (Web.Contents, Distinct with a column list, a Table function not listed) leaves the query
  out, and its Table is named P7.
- **T1:** another Table's whole column, `COUNT(jobs[job_id])`, is a CROSS JOIN of its total, as
  file 11's I3 writes SUMPRODUCT over another Table; T1 lists only its own Table's form. COUNT
  is COUNT(v), as the file says, though Excel's COUNT counts numbers only.
- **T2:** a Total Row of a Table of typed columns alone, a source, reads its database table
  directly (`SELECT SUM(v) AS v FROM <database>.t`): it has no final query to read as a CTE,
  which T2 assumes. Only SUBTOTAL's 101 to 105 and 109 are listed; any other total is NULL,
  named T2; a label or an empty cell has no column.
- **T3:** the person's say-so is `total_rows_left_out`; ticket 07 or 08 gives it its Decision.
- **sqlglot, for both paths:** sqlglot's Hive writer turns `VAR_SAMP` into `VARIANCE`, which
  in Hive is the population variance, and `VAR_POP` into `VARIANCE_POP`, which Hive lacks. The
  code writes `VAR_SAMP` as it is (`workbook_totals.whole_table_total`). The lead confirmed it
  reaches the shipped Toolbox's writer too (`writing.sql_text`), and it goes to a fix of its
  own; until then any Hive read and written again by sqlglot meets it.

**For ticket 13: each place the code reads file 12 or 15 differently, and the line the file
would need** to say the same (or the code changes to the file's):

| Rule | What the code does | The line the file would need |
|---|---|---|
| 12's Q2 | `<>` between two columns is refused | Q2, after `(status <> 'TEST' OR status IS NULL)`: "Between two columns, `[a] <> [b]`, refused: M keeps a row where one is null, which no plain Hive comparison does." |
| 12's T1 | another Table's whole column, `SUM(u[v])`, is a CROSS JOIN of its total | T1, at its end: "Of another Table's column, `CROSS JOIN (SELECT SUM(v) AS total FROM u) c`, then `c.total`." |
| 12's T1 | COUNT(t[v]) is COUNT(v), counting every value where Excel's COUNT counts numbers only | T1: "COUNT counts numbers only: where v holds text, mark it." Or the code refuses COUNT of a column of text. |
| 12's T2 | a Total Row of a Table of typed columns alone, a source, reads its database table, `SELECT SUM(v) AS v FROM <database>.t` | T2, after "reading the Table's final query as a CTE": "A Table of typed columns alone has none: read `<database>.<table>` itself." |
| 12's S2 | an index from start s counting by k, other than 1, 1, is `(ROW_NUMBER() OVER (..) - 1) * k + s`; M's own default start is 0 | S2, at its end: "Starting at s, counting by k: `(ROW_NUMBER() OVER (..) - 1) * k + s`; AddIndexColumn(t, "n") alone starts at 0." |
| 12's G4 | Table.Combine lines the tables' columns up by name, NULL where one has none | G4, after UNION ALL: "each SELECT's columns in the first table's order by name, `NULL AS c` where a table has no c." |
| 12's G5 | the measure and amount columns come after the kept ones | G5, after `'a' AS measure, a AS amount`: "after the columns kept, in their order." |
| 12's M1 | the Item read is `<database>.<item>`, the person's database, never the M's database argument; a native query (`[Query=..]`) refused | M1: "read the Item it names as `<database>.<item>`; a query of its own, `[Query="..."]`, is refused (X1)." |
| 12's M2 | the values are the sample's in the order they first appear, a blank left out; List.Count is `SUM(CASE .. THEN 1 END)`, List.Max, Min and Average their aggregate of v | M2, after "a column per value in the sample": "in the order they first appear, a blank none"; and "List.Max, List.Min, List.Average: MAX, MIN, AVG of `CASE .. THEN v END`." |
| 12's Q7 | two numbers the M gives are worked out: `SUBSTR(status, 2, 2)` | Q7, after Text.Middle's: "with s a number, s + 1 worked out: Text.Middle(x, 1, 2) is SUBSTR(x, 2, 2)." |
| 15's W2 | the step CTE carries only the columns the final reads: `ok_runs AS (SELECT job_id FROM ..)` | W2's second block: `WITH ok_runs AS (SELECT job_id FROM <database>.job_runs WHERE status = 'SUCCESS')`, and a line "a CTE carries only the columns read after it" (ticket 17's rule). |

Kept as file 12 writes it, though ticket 17's rule would say otherwise: W2's and T2's Total Row
reads the Table's final whole as a CTE, every column carried.

**For ticket 17 (Hive that stays small), as asked mid-ticket:**

- Done in code: a filter stays in the SELECT that reads its source; steps that rename, reorder
  or add a column are one SELECT; a step is read in brackets only where the rows need it.
  `lean_ctes` leaves out of each CTE every column nothing after it reads, by name, last CTE
  first (a DISTINCT or UNION CTE kept whole), on every final, formula ones too.
  `passed_through` folds a final that only reads its last CTE whole, as a Table a query loads,
  into that CTE's query (file 15's W2 shape).
- Kept, as file 12 asks: **W2 and T2** read the Table's final whole as a CTE, so a Total Row's
  CTE carries every column of the Table, read or not (X52's carries `rank_in_job`).
- Differs from the files' text, the rows the same: file 15's W2 shows the step CTE `ok_runs`
  with `run_id` and `duration_mins`, which `ok_by_job` doesn't read; the code leaves them out.
- Left: the M code never reads a CTE twice in one final, but ticket 04's formula code can,
  where two joins of one Table's formulas read the same step (a lookup and an -IFS total into
  one step Table); and file 15 has each step "a CTE in each final reading it", so two finals
  each work a shared step out.

## Review

The code review (2026-11-19), its Standards and Spec findings, each answered (rebased onto
dev's 16afc196 first):

1. **Docstrings; `unchanged`'s name:** `copied`, `copied_columns` are gone (finding 2);
   `other_column` is `other_table_column`, with a docstring; `unchanged` is
   `types_buffer_or_headers`, for the three steps it serves.
2. **One way per job:** the five `exp.Identifier(this=.., quoted=False)` are `identifier`
   (idempotent on a name `hive_name` already wrote), and `lean_hive.with_ctes` sets a WITH
   from its CTEs as they are, so none is built by hand; `workbook_hive.py`'s three are
   `identifier` too. `step_arguments` calls `workbook_formulas.check_argument_count`, which
   `call_arguments` calls too, the file's wording passed in ("file 12"). `copied_rows` and its
   hand copies are `copy.deepcopy`, the one way a step copies rows.
3. **Middle Man:** `workbook_hive._total_row_finals` is gone; `workbook_hive` calls
   `total_row_finals` itself.
4. **Divergent Change:** `workbook_power_query.py` holds the M rules alone; T1 to T4 are
   `workbook_totals.py`; `lean_ctes`, `passed_through`, `columns_read_after` and the new
   `with_ctes` are `lean_hive.py`, which imports sqlglot alone, so tickets 06 and 17 can use
   them without the Power Query file. Registry and standards.md's list updated.
5. **The aggregate tables:** `workbook_formulas.EXCEL_AGGREGATES` is the one table of Excel's
   aggregates as Hive's; `IFS_FORMS` reads it, T1 is its keys, and T2's `SUBTOTALS` maps each
   number to an Excel aggregate it names.
6. **Tests:** Q5's Table.TransformColumnTypes, Table.Buffer and Table.PromoteHeaders each alone
   give the rows as they are; X1's Table.FillUp is refused, NULL in its column.
7. **Q7's constants:** `folded_numbers` works out a sum or product of two numbers the M gives:
   `SUBSTR(status, 2, 2)`, `ADD_MONTHS(dt, 24)`; with a column, `job_id + 1`, kept. Tests for
   both.
8. **For ticket 13:** the table in the Answer lists each place, with the line file 12 or 15
   would need.
9. **VAR_SAMP:** kept as written; the Answer notes the lead's finding and its own fix.

Tests rerun: `test_workbook_power_query.py` (125), `test_workbook_hive.py`,
`test_workbook_reader.py`, `test_excel_eval.py` and the repo checks named in the ticket's
brief: 838 passed; ruff clean.

# Formulas and roles into Hive, in code

Type: task
Status: resolved
Blocked by: 01
Size: XL

## Question

The code path's first half: each piece's role (file 15's P1 to P11, R1 to R3) and each formula's
Hive (file 11's rules), written by the Toolbox (ADR 0016).

## Done when

- **Roles** from the reader's Order: source, step, final, summary final, settings
  (Parameters, Keys), left out, refused in a loop; a query and the Table it loads are two
  pieces.
- **Each final's Hive** as sqlglot trees: sources as `<database>.<table>`, steps as CTEs in
  order, columns in the Table's order, a Parameters value written in, a typed-over value a
  CASE on its Keys row (V1, V2), a summary's groups written in (R1).
- **Each rule of file 11 by its ID**, F1 to F10, I1 to I6, V1, V2, M1 to M5, X1: converted,
  converted with its mark, or refused as `NULL AS` its header and named. A header that isn't a
  plain name is written as file 11's N2 says.
- What it gives back: each final's Hive, and a list of what was written in, marked, refused and
  left alone, in file 15's map's words.
- **No new public name yet**: ticket 07 gives the user's call.
- Tests: one per rule ID, its formula giving the Hive the rule gives; file 15's and file 11's
  Worked patterns each as a test.

## Answer

**Built.** Two new files in the Toolbox's folder, both in the registry's `PYTHON_FILES` and
`LIBRARY_FILES` (they name sqlglot's trees), no public name (nothing in `public.py` or
`__init__`):

- `sqlglot_composer/workbook_formulas.py`: each formula written as file 11's rule with its ID.
  `read_formula(text)` reads a formula, held (`t[[#This Row],[x]]`, `_xlfn.`) or typed
  (`[@x]`, `[@[A b]]`), into a small tree (`Constant`, `ThisRow`, `WholeColumn`, `WholeTable`,
  `TablePart`, `CellAddress`, `Name`, `Call`, `Operation`, `Negative`, `Percent`, `Omitted`,
  `AnyOf`), Excel's operators in Excel's order. `table_query(table, base, book)` writes one
  Table's SELECT: typed columns from `base`, each formula column by its rule or `NULL AS` its
  header, and the joins its formulas need (`Lookup`, F8; `Totals`, F9 and I3), one per key,
  joins and totals nothing reads dropped. `FUNCTIONS` maps each function name file 11 lists to
  the function writing it; `Refused(rule, why)` is a refusal; `Note(kind, rule, where, text)`
  is one line of the map, `kind` one of `WRITTEN_IN`, `TYPED_OVER`, `MARK`, `REFUSED`,
  `LEFT_ALONE`, `TO_FILL_IN` (file 15's Output's words), `rule` its ID, so ticket 13 can tie
  each to its test.
- `sqlglot_composer/workbook_hive.py`: roles and each final. `piece_roles(workbook)` gives
  each Piece its role from the reader's Order (`SOURCE`, `STEP`, `FINAL`, `SUMMARY_FINAL`,
  `SETTINGS`, `LOADS` for a query loading a Table nothing else reads, `LEFT_OUT`).
  `workbook_hive(workbook, database="<database>")` gives a `WorkbookHive`: `roles`, `finals`
  (each final's sqlglot tree by its name in the workbook, steps as CTEs in the Order) and
  `notes`. `hive_texts(hive)` writes each final's Hive (through `writing.sql_text`);
  `map_text(hive, workbook)` writes file 15's Map. `is_summary(table)` is P4.

**Tested** in `tests/test_workbook_hive.py`, 106 tests: one or more per rule ID, each named for
it (N1, N2, F1 to F10, I1 to I6, V1, V2, M1 to M5, X1 with 15 refusals and the left-alone
names; P1 to P11, R1, R3), compared as sqlglot writes both; file 15's W1, W2 (roles), W3 and
file 11's W1; and **every formula-only task of the Excel evaluation**, 45 of them (dev and
held out), read from the workbook file `formula_workbook.saved` gives and scored by
`excel_eval.score` itself, rows on the stand-in Hive, map, tables read and names: all 45 pass.
The only change to a task is leaving out the PivotTable a note in the text names, which the
file doesn't hold. 86 hashes join `tests/snapshot/known.txt` for the Hive these tests write.
`tests/workers.py` groups the new stand-in Hive fixture.

**The seam for tickets 05 and 06.** Each adds a file of its own (to `PYTHON_FILES` and
`LIBRARY_FILES`) and touches `workbook_hive.py` only in the function for its kind of piece,
plus one line in `_functions()`:

- **05 (Power Query, totals):** replace the body of `_power_query_tree(piece, role, book)` to
  give a query's SELECT (the Table a query loads is then built over it: `book.reads[Piece(
  POWER_QUERY, name)]` holds its CTE's name for a `STEP`, the tree itself for `LOADS`;
  `_cte_name` gives `<name>_query` where a Table of its name is a step too). Replace the body
  of `_total_row_finals(workbook, finals, book)` to return `{"<Table> (Total Row)": tree}`,
  reading `finals[table]` as a CTE (`TOTAL_ROW` is the suffix). Add T1's functions in
  `_functions()` (`{**FUNCTIONS, **its_functions}`): SUM, AVERAGE, COUNT, COUNTA, STDEV.S,
  VAR.S are new names; MIN, MAX and SUMPRODUCT are mine for file 11's forms and refuse a whole
  column with rule "T1", so 05's should write the T1 form and else call
  `workbook_formulas.FUNCTIONS[name](call, place)`.
- **06 (PivotTables):** add a branch for 03's pivot kind in `_piece_tree(piece, role, book)`
  (any other kind is refused there today), its total levels as finals beside
  `_total_row_finals`, and drop the PivotTable line from `_left_alone` (X1 still names them).
  `piece_roles` already gives an unknown kind `STEP` if another piece reads it, else `FINAL`.
  GETPIVOTDATA goes in `_functions()`; its LEFT JOIN on the pivot's CTE needs a join record of
  its own beside `Lookup` and `Totals` in `workbook_formulas._join_hive`, the one place 06
  touches that file.
- **A function's writer** is `Callable[[Call, Place], exp.Expression]`; it raises
  `Refused(rule, why)` and adds marks to `place.marks`, notes to `place.query.notes`. What it
  can call: `hive_of`, `this_row`, `looked_up`, `totals_read`, `written` (a rule's Hive as
  text with p0, p1 placeholders), `hive_call`, `binary`, `all_of`, `constant_hive`,
  `identifier`, `hive_name`.

**Read differently from the files, and why:**

- **P11:** the reader refuses the whole workbook with its LoopError (ticket 01), so no final
  converts, where file 15 refuses only the finals in the loop. The test holds the reader's
  refusal.
- **I1, `">="&[@d]` against this row:** converted only as I5's running total over its own
  Table (`"<="` ascending, `">="` descending); any other comparison with this row, and any over
  another Table, is refused, as no GROUP BY join holds it.
- **M1:** COALESCE where Excel's blank changes the result: an arithmetic operand but a divisor
  (Excel's #DIV/0! and Hive's NULL agree there), `&` and CONCAT (`''`), and a comparison with a
  constant (`0` or `''`); elsewhere the column is as it is.
- **F9:** COALESCE(.., 0) on a window's SUM, MAX and MIN, as the file says (never COUNT, which
  is never NULL), but none on I5's running totals, as I5 writes them. Some evaluation
  references leave it off a MINIFS (X41); the rows agree on the Example database.
- **R1, W3:** a summary's groups are written in as W3 writes them, `SELECT 1 AS job_id UNION
  ALL SELECT 2`, and its -IFS are F9's joins over another Table, so its final is W3's shape
  rather than a GROUP BY of the Table it reads.
- **F8:** a lookup into its own Table, or into Keys, is refused (not a form file 11 lists).
- **F5:** SEARCH with a text writes the text in lower case, `INSTR(LOWER(x), 'load')`, where
  the file writes `LOWER(a)`; the same Hive.
- **Aliases:** the first letter of a table name's last word, as file 15's W1 writes `job_runs
  r`; none where a final joins nothing, as file 11's W1.
- **A formula column whose rows hold different formulas** is refused; a blank cell in one is
  read as a value typed over it, NULL.

**Left for later:** R2 and P9's Total Row final (05: today each is named as refused, T2), every
Power Query (05: named as refused, Q1, and the Tables it loads, P7), T1's whole-column totals
(05: refused, T1), PivotTables (06: left alone, named). **One reader gap, for ticket 03:** the
Order doesn't see a Table named bare, as `VLOOKUP(k, jobs, 3, FALSE)` names jobs
(`TABLE_REFERENCE` wants `jobs[`). `workbook_hive` reads every source before any Table, so a
source read that way converts (X07, X13); a step read only that way would be given the wrong
role and order. The code-review skill hasn't run on this ticket.

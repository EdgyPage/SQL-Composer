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

**Built.** Three new files in the Toolbox's folder, all in the registry's `PYTHON_FILES`, the
two that name sqlglot's trees in `LIBRARY_FILES` too, and no public name (nothing in
`public.py` or `__init__`):

- `sqlglot_composer/workbook_formula_reader.py` (standard library alone): `read_formula(text)`
  reads a formula, held (`t[[#This Row],[x]]`, `_xlfn.`) or typed (`[@x]`, `[@[A b]]`), into a
  small tree (`Constant`, `ThisRow`, `WholeColumn`, `WholeTable`, `TablePart`, `CellAddress`,
  `Name`, `Call`, `Operation`, `Negative`, `Percent`, `Omitted`, `AnyOf`), Excel's operators
  in Excel's order, through `formula_tokens` and `FormulaReader`; `parts_of` walks a tree;
  `Refused(rule, why)` is a refusal, an internal signal turned into a Note.
- `sqlglot_composer/workbook_formulas.py`: each formula written as file 11's rule with its ID.
  `table_query(table, base, book)` writes one Table's SELECT: typed columns from `base`, each
  formula column by its rule or `NULL AS` its header, and the joins its formulas need
  (`Lookup`, F8; `Totals`, F9 and I3; `RowTotals`, I1's comparison with this row), one per
  key, joins and totals nothing reads dropped. `FUNCTIONS` maps each function name file 11
  lists to the function writing it; `Note(kind, rule, where, text)` is one line of the map,
  `kind` one of `WRITTEN_IN`, `TYPED_OVER`, `MARK`, `REFUSED`, `LEFT_ALONE`, `TO_FILL_IN`
  (file 15's Output's words), `rule` its ID, so ticket 13 can tie each to its test.
- `sqlglot_composer/workbook_hive.py`: roles and each final. `piece_roles(workbook)` gives
  each Piece its role from the reader's Order (`SOURCE`, `STEP`, `FINAL`, `SUMMARY_FINAL`,
  `SETTINGS`, `LOADS` for a query loading a Table nothing else reads, `LEFT_OUT`).
  `workbook_hive(workbook, database="<database>")` gives a `WorkbookHive`: `roles`, `finals`
  (each final's sqlglot tree by its name in the workbook, steps as CTEs in the Order) and
  `notes`. `hive_texts(hive)` writes each final's Hive (through `writing.sql_text`);
  `map_text(hive, workbook)` writes file 15's Map. `is_summary(table)` is P4.

**Tested** in `tests/test_workbook_hive.py`, 111 tests: one or more per rule ID, each named for
it (N1, N2, F1 to F10, I1 to I6, V1, V2, M1 to M5, X1 with 15 refusals and the left-alone
names; P1 to P11, R1, R3), compared as sqlglot writes both; file 15's W1, W2 (roles), W3 and
file 11's W1; and **every formula-only task of the Excel evaluation**, 45 of them (dev and
held out), read from the workbook file `formula_workbook.saved` gives and scored by
`excel_eval.score` itself, rows on the stand-in Hive, map, tables read and names: all 45 pass.
The only change to a task is leaving out the PivotTable a note in the text names, which the
file doesn't hold. `tests/snapshot/known.txt` knows the Hive these tests write (88 hashes after
the review). `tests/workers.py` groups the new stand-in Hive fixture.

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
  can call: `hive_of`, `row_cell_hive` (a column of the row as a formula reads it, M1's
  COALESCE in), `this_row` (the same with no COALESCE), `lookup_hive`, `totals_read`,
  `rule_hive` (a rule's Hive as text with p0, p1 placeholders), `hive_call`, `binary`,
  `operand_hive`, `all_of`, `constant_hive`, `identifier`, `hive_name`, `call_arguments`,
  `argument_given`, `window_order`, `free_alias`. A formula's parts and `read_formula` come
  from `workbook_formula_reader.py`.

**Read differently from the files, and why:**

- **P11 (for ticket 13):** file 15's P11 and the reader disagree. File 15 refuses only the
  finals in a loop and converts the rest; the reader (ticket 01) refuses the whole workbook
  with its LoopError, naming each link, so no final converts, and the code is as it is (the
  test holds the reader's refusal). To agree, either file 15's P11 says the workbook is
  refused as a whole, naming each link, as the reader does; or the reader gives back the
  Order of every piece outside the loop with the loop's pieces beside it, and
  `workbook_hive` refuses only each final reading a piece in it.
- **I1, `">="&[@d]` against this row:** over its own Table, I5's running total where it is
  one (`"<="` ascending, `">="` descending, one such criteria on the same column); any other
  comparison with this row, over its own Table or another, is a LEFT JOIN of a total worked
  out for each row: `(SELECT k.id, SUM(u.v) AS total FROM <this Table> k JOIN t u ON u.d >=
  k.d .. GROUP BY k.id)`, joined back on the Table's Keys row, or else every typed column
  (marked V2), COALESCE(.., 0) but for AVERAGEIFS. Checked on the Example database's
  job_runs against an independent count. **Still refused, for ticket 13** (file 11's I1
  says "against this row's d" with no limit, so either it names these or the code learns
  them): a comparison with a value of this row that isn't one of its typed columns (a formula
  column, a lookup's result, an expression); over its own Table, a comparison reading one of
  its own formula columns; and a Table whose rows repeat on their key columns, where a total
  can't be matched back to one row. A row whose key column is blank matches nothing, so its
  total is 0 where Excel gives it one.
- **M1:** as file 11 says: COALESCE wherever a formula reads a typed column of its row with a
  blank in the workbook, a bare `=[@x]`, a function's argument and a divisor included
  (`x / COALESCE(y, 0)` gives NULL as `x / NULL` does), but inside an -IF(S) form or ISBLANK.
  `COALESCE(x, 0)` where the column's other cells are numbers, `COALESCE(x, '')` else.
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
role and order. 

## Review

The code review (2026-11-19), its Standards and Spec findings, each answered:

1. **M1 everywhere:** fixed, as the Answer's M1 says; the M1 test adds a bare `=[@status]`,
   `UPPER([@status])` and a divisor.
2. **I1 beyond the running total:** fixed: `_compared_ifs`, `RowTotals`, `row_keys`, three
   tests of it (own Table, another Table, what still refuses, rows repeating on their keys).
   What still can't convert is listed for ticket 13 in the Answer.
3. **P11:** the code is as it was; the Answer says, for ticket 13, how file 15's P11 and the
   reader disagree and what each would need to agree.
4. **The parser split out:** `workbook_formula_reader.py`, standard library alone, in
   `PYTHON_FILES` (not `LIBRARY_FILES`: it imports no sqlglot). Its `arguments` method is
   `read_arguments`.
5. **Names:** `written` is `rule_hive`, `given` `argument_given`, `ordered` `window_order`,
   `arguments` `call_arguments`, `bracketed` `operand_hive`, `looked_up` `lookup_hive`,
   `_wildcard` `_wildcard_condition`, `_shown` `value_text`, `_matched`
   `_key_match_condition`, `_branch` `_if_value_hive`, `_approximate` `_mark_approximate`,
   `_differs` `_is_differing_argument`, `_exclusive` `_is_exclusive`; `new_alias` is
   `free_alias`, which only gives one, and each caller adds it to `taken`. The seam list in
   the Answer has the new names.
6. **One way per job:** `value_text` alone writes an integral float as an integer (it was
   `_shown` and `_written_number`); the IN list is `exp.In` itself, so no placeholders are
   built by hand.
7. **`_cte_name`:** plain `if` statements.
8. **`SAME_IN_HIVE`:** each entry a `HiveTwin(name, fewest, most)`.
9. **`Refused`:** a comment says it is never shown to the user, so not `refusals.refuse`, and
   is turned into a Note. **`_functions()`:** its docstring says it copies so a file adding
   its writers never changes `FUNCTIONS`, which holds file 11's alone.
10. **`_cell_of`:** gone: `key_columns` gives Columns, so each key's cell is read from its own
    column.
11. **Spec: R2 and P9's Total Row final, and P7's Tables a query loads:** deferred to ticket
    05, as the Answer's "Left for later" says: each is named as refused today (T2, Q1, P7),
    and `_total_row_finals` and `_power_query_tree` are where 05's Hive goes.

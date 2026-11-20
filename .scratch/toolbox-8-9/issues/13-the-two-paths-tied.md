# The two paths tied, rule by rule

Type: task
Status: resolved
Blocked by: 05, 06, 11
Size: M

## Question

How the code and the Copilot files are kept saying the same thing, neither the other's
reference (round 2, Q5; ADR 0016: "Both paths, equal").

## Done when

- **Every rule ID** in files 11, 12, 15 and 20 has a test of the code giving the Hive the rule
  gives, and every such test names its rule ID.
- **A repo test** fails when a Copilot file holds a rule ID with no test, or a test names an ID
  no Copilot file holds.
- `docs/agents/standards.md` says a rule changes in both places in one commit.

## Comments

- From ticket 04's review (2026-11-19), two places the code and the Copilot files disagree,
  for this ticket to settle, as `04-formulas-in-code.md`'s Answer says in full:
  - **P11**: file 15 refuses only the finals in a loop; the reader refuses the whole workbook.
    Either file 15 says the workbook is refused, or the reader gives the Order outside the loop
    and `workbook_hive` refuses only the finals reading a piece in it.
  - **I1** `">="&[@d]`: still refused in code, though file 11 sets no limit: a comparison with
    a value of the row that isn't a typed column; over its own Table, one reading its own
    formula column; a Table whose rows repeat on their keys. A blank key column gives 0 where
    Excel gives a total. Either file 11 names these, or the code learns them.

## Answer

Built 2026-11-19 on dev's e276a610. Every rule ID of files 11, 12, 15 and 20 has a test of the
code naming it, a repo test holds the tie both ways, and each disagreement tickets 04, 05, 06,
11 and 17 listed is settled, as is PV8's grand total, which ticket 09's Workbook check found.

### The repo test

`tests/repo/test_rules_tied_to_tests.py`, on a reader added to `tools/copilot_files.py`:

- **`copilot_files.rule_ids(text)`** reads a Copilot file's rule IDs: each `- **ID** ` line
  under a heading starting `## Rules`, and each row of a Patterns table that gives a role
  (file 15's P1 to P13). A Patterns table whose last column is headed `Rules` (files 11, 12,
  20) only points at rules, so its P1 to P8 aren't rule IDs. `worked_pattern_ids(text)` reads
  each `### W1: ...` heading.
- **The Excel files** are `excel_eval.EXCEL_FILES` and `PIVOT_FILE` (15, 11, 12, 20), read
  from `copilot/`. **The tests of the code** are `tests/**/test_*workbook*.py`, read with ast.
- **A test names an ID** by its name's start: `test_f9_...`, a range `test_p5_to_p8_...` or
  `test_t1_to_t2_...`, or `test_file_12_m1_...`. The `file_NN_` form is needed for an ID two
  Excel files hold (11's and 12's M1, M2 and X1), and for a Worked pattern.
- **It fails** on a rule ID no test names, on a test naming an ID no Excel file holds (a rule,
  or for a `file_NN_` name a Worked pattern too), and on a bare ID two files hold, naming the
  `file_NN_` form to use. Two more tests hold the reader and the name parsing.

### The tests added or renamed

- **Renamed, as M1, M2 and X1 are in both 11 and 12:** `test_workbook_hive.py`'s `test_m1_`,
  `test_m2_` and the three `test_x1_` are `test_file_11_...`; `test_workbook_power_query.py`'s
  `test_m1_`, `test_m2_` and three `test_x1_` are `test_file_12_...`.
- **New, for the IDs with no test** (file 15's):
  - `test_r2_a_total_rows_final_has_a_column_for_each_cell_holding_a_total_no_other`;
  - `test_file_15_p12_a_pivot_a_tables_getpivotdata_reads_is_a_step` and
    `test_file_15_p13_any_other_pivot_is_a_final_and_each_total_level_shown`, in
    `tests/sqlglot_checks/test_sqlglot_workbook_pivot_hive.py`;
  - `test_h1_each_step_is_read_once_in_a_final_forms_grouped_alike_one_join`,
    `test_h1_a_lookup_and_a_total_on_one_step_read_it_once_each` (the shape ticket 17 kept),
    `test_h2_a_cte_selects_only_the_columns_read_after_it_never_a_star` (in
    `test_workbook_hive.py`); `test_h3_each_where_is_in_the_select_reading_its_source_before_any_join`,
    `test_h4_columns_renamed_or_added_in_the_select_reading_a_step_never_a_copying_cte`,
    `test_h5_no_order_by_without_a_limit_in_a_cte_and_no_distinct_after_a_join` (in
    `test_workbook_power_query.py`).
- **New, for a settlement:** `test_ps1_never_its_cells_typed_in_never_a_cte_named_for_the_table_it_reads`
  (ticket 11's PS1 "never"s, over every pivot fixture and built workbook);
  `test_q2_not_equal_between_two_columns_keeps_a_row_where_one_is_null` (in place of the
  refusal's test); `test_t1_to_t2_count_of_a_column_of_text_is_refused_as_excels_counts_numbers_only`;
  `test_i1_a_joined_comparison_refuses_a_blank_key`;
  `test_file_12_m2_a_pivot_by_max_min_or_average_is_refused`; P11's test, renamed
  `test_p11_pieces_reading_each_other_in_a_loop_refuse_the_workbook_each_link_named`, also
  reads each link named; PV8's test reads the grand total.
- **Ticket 06's row test** (`cell_value`) read only the first row a level's final gave for a
  cell, so a grand total of a row per source row passed. It now gives the count where several
  rows match (but a calculated item's cell, which PC1 repeats on each real item's row), which
  no stored value matches.

### Each disagreement, and how it was settled

| Where | Settled | How |
|---|---|---|
| 15's P11 (04) | the file follows the code | P11: "the workbook refused, each link named", as the reader refuses it; option one of ticket 04's two, as `workbook_conversion.py` (ticket 09's) and `workbook_text.py` catch the reader's LoopError whole |
| 11's I1 limits (04) | the file names them, the code adds one | I1: "against this row's typed d (and a typed t[d] over its own Table); refused where rows repeat or hold a blank on their Keys (V1, V2)". A blank key, which gave 0 where Excel gives a total, is now refused in `row_keys` |
| 12's Q2, `<>` between two columns (05) | the code learns it, the file says it | `(a <> b OR (a IS NULL) <> (b IS NULL))`: kept where one side alone is null, as M's null <> null is false |
| 12's T1, another Table's column (05) | the file follows the code | T1: "Another Table's column: CROSS JOIN its total" |
| 12's T1, COUNT of text (05) | both refuse | COUNT, or a Total Row's SUBTOTAL(102), of a typed column holding text is refused (`check_counts_numbers`, T1 and T2), as Excel's counts numbers alone; T1 says so |
| 12's T2, a source's Total Row (05) | no change | the code reads `<database>.t` itself, with no final query to read as a CTE; the same rows as a CTE of it (the lead's call) |
| 12's S2, start and step (05) | the file follows the code | S2: "From s by k: `(ROW_NUMBER() OVER (..) - 1) * k + s`; none given, 0" (the lead's call: M's default start is 0) |
| 12's G4, Combine by name (05) | the file follows the code | G4: "columns matched by name, NULL where missing" |
| 12's G5, column order (05) | the file follows the code | G5: "after the kept columns" |
| 12's M1, a native query (05) | the file follows the code | X1 lists "a native `[Query=..]`"; the Item as `<database>.<item>` is M1's "the table it names" with N1's `<database>` |
| 12's M2, List.Max, Min, Average (05) | the code follows the file | refused (M2), as M2 lists counting and adding up alone (the lead's call: rare); the values' order and a blank left out are M2's "per value in the sample" |
| 12's Q7, numbers worked out (05) | no change | `SUBSTR(x, 2, 2)` and `SUBSTR(x, 1 + 1, 2)` give the same rows (the lead's call) |
| 15's W2, the step's columns (05) | done by ticket 17 | `ok_runs` selects `job_id` alone |
| 15's H1, a lookup and a total on one step (17) | the file follows the code | H1: "...share one join (file 11's F9); a lookup needs its own" |
| 20's PS1 "never"s (11) | a test of the code | the code never types a pivot's cells in nor reads a table of a CTE's own name unqualified |
| 20's PV8, a grand total (09, mid-ticket) | the code is fixed, the file says it | a level grouping by nothing whose values are all NULL is `SELECT NULL AS v`, no FROM, one row, where it gave a row per source row (fixture 10's `PivotTable2 (grand total)`); PV8: "grouping by nothing: no FROM" |

Ticket 04's other readings (M1, F9, R1 and W3, F8, F5, aliases, a formula column of different
formulas) and ticket 05's (Q3, Q4, Q6, G2, G3, S1 and S3, X1) already say what the files say,
or fall under a refusal the files list ("any formula files 11 and 12 don't list", "a step no
rule here lists is refused"), so none changes.

### Each Copilot file change, for ticket 14's round

Lengths with Windows line breaks, as written: 11 8,991; 12 9,000; 15 8,998; 20 8,999. No
split: file 12's room came from its Terms and Worked patterns, as the lead asked, then its
Load line.

| File | Change |
|---|---|
| 11 | I1's limits (above); to fit, the bold first line ("find each formula in Patterns"), the Load line ("file 12 (Power Query)") and the Formula column term ("a column of formulas") |
| 12 | Q2's two columns; T1's other Table and COUNT of text; S2's start and step; G4 by name; G5's column order; X1's native query. To fit: the M and Total Row terms and the unlisted-step term shortened; W1's heading, its M's indentation and `Int64.Type`, its SQL on three lines; W2's intro; the Load line ("file 11 (formulas)") |
| 15 | P11 the workbook refused; H1's lookup; W2's Map line shortened |
| 20 | PV8's grouping by nothing; to fit, the bold first line, the "Decision in convert" term and W1's Finals line |

### Also

- `docs/agents/standards.md`, a section "A Formula workbook's two paths say the same": a rule
  changes in the code and its Copilot file in one commit, with its test named for its ID.
- `tests/snapshot/known.txt`: 14 hashes added, the Hive the new tests make. None taken out:
  the old grand total's text (`SELECT NULL AS .. FROM ..`) and the Q2 refusal's are no longer
  made, which a whole-suite run with `SNAPSHOT_WRITE=1` drops.
- **Found beyond the lists, the code settled, file 12 waiting for ticket 14:** M's `[a] = [b]`
  between two columns keeps a row where both are null (M's null = null is true), where Hive's
  `a = b` drops it. The code writes `(a = b OR (a IS NULL AND b IS NULL))` (`equality_hive`,
  `test_q2_equal_between_two_columns_keeps_a_row_where_both_are_null`). File 12, at 9,000, has
  no room: **for ticket 14**, Q2 needs "`=` between two columns: `(a = b OR (a IS NULL AND b IS
  NULL))`." Until then the two paths differ on it: the Copilot path writes `a = b`.
- Tests run: the workbook tests, `tests/test_pivot_tables.py`, `tests/sqlglot_checks`,
  `tests/test_copilot_files.py`, `tests/test_excel_eval.py`, `tests/test_eval_sources.py`,
  `test_eval_rounds.py`, `test_eval_ladder.py` and all of `tests/repo/`: 4,645 passed and 119
  passed, ruff clean. Not run: the whole suite, and the code-review skill.

# Hive with a literal list converts without guessed types

Type: task
Status: resolved
Blocked by: 04
Size: S

## Question

Found by round one (E2-3): Copilot's Hive for a workbook whose team list was typed in became an
Unchecked statement with guessed types, where a Saved table's columns were wanted.

## Done when

- The shape is reproduced in a test, and either converts to a Saved table with typed columns or
  is refused saying what to write in its place.

## Answer

The shape converts as it did, kept whole: a Statement needs a FROM, which a typed-in list has
none of. Its Table reference no longer guesses: `converting.typed_selected_columns` has
sqlglot's `qualify` and `annotate_types` work out each column's type from the Project's Table
references (`project._reference_types`), and only a type it can't tell, or one with a
precision, such as a decimal, stays a guessed-type Decision.
`tests/test_run_workflow.py::test_a_query_kept_whole_as_hive_has_its_columns_typed` holds E2-3's
shape; `tests/test_batches.py`'s kept-whole test now has run_id typed and y, from explode,
guessed.

## Review

- Spec: the shape is a Saved table, its logic an Unchecked statement as before, its Table
  reference typed: the "converts to a Saved table with typed columns" branch. A type with a
  precision, a decimal's, stays guessed, held by the test; Hive's VARCHAR(n) sqlglot reads as
  string. A KeyError or ValueError from sqlglot's qualify leaves the types untold, as a
  SqlglotError does.
- Standards: the guard comes before the query is read, and the docstring says plainly when a
  column is "".

# Run values

Type: task
Status: open
Blocked by: 03
Size: L

## Question

A tag's answer is fixed Hive text; the user wants the latest date at each run, worked out in
Python and written into plain Hive (map, "Run values").

## Done when

- **Answered in the decisions cell with a function**: the cell imports it from the Project,
  such as `from building_blocks.run_values import period_end`, and answers
  `{"tags": {"PERIOD_END": period_end}}`. `project.write_decisions` writes the import and
  `TAGS = {"PERIOD_END": period_end}` into the Table reference, and writes it again on a new
  answer, function or text. A function not importable from the Project (defined in the
  notebook, say) is refused, naming where to put it.
- **Called each time `write()` is built**, with no arguments: `script_tag` calls it and
  writes what it gives: a `datetime.date` as `'2026-10-31'`; an `int` or `float` as is; a
  `str` as Hive text, held to what 8.3 holds an answer to. Anything else is refused, naming
  the function and what it gave.
- **A failing function**: a dry run (`run_tables()` with no `execute`, `show_hive`) writes
  `<PERIOD_END>` where the value goes and says what the function raised; anything that sends
  refuses before sending.
- **The Guards** count a Run value as a value (03).
- **The compare** fills each tag of the original's Hive with the value the same run gave the
  table, called once for both.
- A quoted tag's Run value is spliced into its string, as a text answer is.
- 01's journey answers `PERIOD_END` with a function of the Project's and passes past create
  and write.

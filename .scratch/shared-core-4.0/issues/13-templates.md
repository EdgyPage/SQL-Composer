# Templates

Type: task
Status: open
Blocked by: 11, 12
Size: M

## Question

`templates/starter/` (notebook_start, table_reference, building_block, report_statement,
saved_table, daily_pipeline, check_my_tables) and `templates/intermediate/` (incremental_load,
as_of_snapshot, weekly_rollup, building_block_library, quality_checks, settings_driven), with
`<UPPER_SNAKE>` placeholders listed in each docstring's "Fill in:" block.

## Done when

- tests/test_templates.py: placeholders match the list; filled from Example database values, each parses and runs; the beginner reader has run.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).

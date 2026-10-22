# The Example database, the Templates and the Example projects

Type: task
Status: open
Blocked by: 03
Size: L

## Question

With days gone (03), the Example database still has a table partitioned by `dt` everywhere but
`ops.jobs`, and the Table notebook Templates are each built around a day (`daily_table`,
`incremental_load`, `weekly_rollup`, `as_of_lookup`). The user (2026-10-21) chose a mixed Example
database, so the examples show the variety they have at work, and fewer Templates, each one
earning its keep ("if templates are too much work to maintain, as this introduces yet another
onboarding pitfall, an example chart of which files I am responsible for creating helps").

## Done when

- The Example database holds three kinds of table:
  - tables with no partitions;
  - tables partitioned by something that isn't a date, such as `region`;
  - tables partitioned by a date.

  Some of them have no Key. Each Guard, Warning and Load limit is still shown catching a wrong
  number on it.
- Two Table notebook Templates are left, with no day placeholder in either:
  - `saved_table`, which defines `create`, `rows`, `preview` and `write`;
  - `quality_checks`.

  The `saved_table_reference` Template stays, with no `dt` and no `key=[..., "dt"]`. The
  `building_block` Template stays, taking no day arguments. `daily_table`, `incremental_load`,
  `weekly_rollup` and `as_of_lookup` are gone, and `new_table`'s default is `saved_table`.
- Every Template's first lines list its placeholders, as the README says they do. Today the
  `saved_table_reference` and `building_block` Templates don't.
- Both Example projects are rebuilt with `tools/example_project.py` on the new Example database
  and Templates. Their Building blocks no longer say "per job day". Their READMEs say only what
  is true of how each file was made: a file copied by the generator isn't said to come from a
  Project action.
- The Worked examples, the gallery and the how-tos run on the new Example database, changed only
  as far as they need. 07 reworks the how-tos.
- CHANGES.md's "To update from 6.x" says which Templates are gone, and that a Project's own
  copies in `admin/templates/` stay until the user deletes them.
- CLAUDE.md's Definition of done, the beginner reader included.

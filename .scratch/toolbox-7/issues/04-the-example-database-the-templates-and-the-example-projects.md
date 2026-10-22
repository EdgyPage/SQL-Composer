# The Example database, the Templates and the Example projects

Type: task
Status: resolved
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

## Answer

Built 2026-10-21 in a worktree (e4630d6), merged into dev as d19fb72.

- The Example database has nine tables: the seven, with their rows unchanged, and
  `ops.region_budgets` (partitioned by region alone, Key [job_id, region]) and `ops.team_notes`
  (no partitions, no Key). Its docstring describes the three kinds.
- Table notebook Templates: `saved_table` (new_table's default; `READS = <READS>`, a condition
  picking the rows write() reads; `<PARTITION_COLUMN>`) and `quality_checks`; plus
  `saved_table_reference` (`partitioned_by=[]`, `key=None`) and `building_block` (takes `reads`,
  a condition). daily_table, incremental_load, weekly_rollup and as_of_lookup are gone. Each
  Template lists its placeholders first; none says "Date partition".
- Both Example projects rebuilt; the intermediate one has six Saved tables, among them
  `mart.budget_overruns` (partitioned by region, one write per region) and `mart.job_notes` (no
  partitions, no Key). READMEs say how each file was made.

## Reviews

- Spec (2026-10-21): a Guard, Warning and Load limit on the new tables only in tests (ticket 07
  shows them); only one table has no Key (enough to show the kind); the README's intermediate
  description (ticket 07 rewrites it).
- Standards (2026-10-21): no breach; quality_checks' text written out in full instead of
  .replace() on shared strings, and long lines wrapped (review batch).
- Beginner reader (2026-10-21), costliest stops, sent to ticket 07 and 06: filling a notebook
  and its Table reference in step, with no filled-in pair to compare with; the Starter
  notebooks use DAY where the Template uses READS, so none is the Template filled in plainly;
  Building blocks copied by hand (ticket 06's new_block); what to give `<LOCATION>`.
- Drift: d19fb72 opened D236 (fixed in the review batch).


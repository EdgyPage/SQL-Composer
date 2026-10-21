# run_tables refuses what write_day gives

Type: task
Status: claimed
Blocked by: -
Size: S

## Question

Found while hinting ticket 02: `project.run_tables` passes what each table's `write_day(day)`
gives straight to `lineage.in_order`, unchecked. A `write_day` that gives Session settings,
or anything but Statements and Unchecked statements, stops with Python's AttributeError, not a
four-part message. Confirm it, then refuse it as the Toolbox refuses a wrong value elsewhere.

## Done when

- A `write_day` giving something `run_tables` can't send is refused with the four-part message,
  naming the table and what it gave; a test holds it.
- The pytest run passes, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).

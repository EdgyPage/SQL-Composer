# Add `INSERT_INTO` and `drop_table`

Type: task
Status: claimed
Blocked by: -

## Question

The user asked, in the review of 2026-09-26, for Worked examples of inserting into a table and of
dropping a table if it exists, and chose to add both as public names rather than only explain them.
This reverses two earlier decisions:

- "How do pieces combine across Levels?" (ticket 10): "**Replace, never append.** There is no
  `INSERT_INTO`, so re-running a day replaces it instead of doubling it."
- "Does the Toolbox check a Table reference against the warehouse?" (ticket 16): `create_table`'s
  docstring tells the user to "drop the table on the server first", with no Toolbox name for it.

Build the two names, taking the 61 public names to 63:

- **`INSERT_INTO(t)`**, a clause function in `clauses.py` beside `INSERT_OVERWRITE`. It adds the
  Statement's rows to one day of a Saved table and keeps the rows already there. Every rule of
  `INSERT_OVERWRITE` holds: it goes first, the table needs a Date partition, one day per write
  (loop over `by_day`), columns lined up by name. There is no Guard against re-running a day:
  like `CROSS_JOIN`, the name is the opt-out, and the docstring says plainly that sending the
  same day twice doubles it. A Statement has at most one write.
- **`drop_table(t)`**, beside `create_table` in `tables.py`. It returns the Statement
  `DROP TABLE IF EXISTS db.table` for a real table's Table reference, to send with `run`. It has no
  keyword: `IF EXISTS` is always on, since Hive by default ignores a drop of a missing table
  anyway (`hive.exec.drop.ignorenonexistent`), and the name says what it does. The docstring says
  it deletes every day of the table, and that the usual reason is changing a Saved table's
  columns: drop, create again, write the days again.

Done when the definition of done in `CLAUDE.md` holds, with a Worked example that creates a Saved
table, overwrites a day, adds to a day, backfills with `by_day`, and drops and creates the table
again, each step saying why.

## Comments

**Build decisions (2026-09-26).**

- sqlglot builds a `DROP` tree differently at the two ends of the supported range (`this=` below
  30, `tables=[...]` from 30), so `drop_table` sets whichever the installed sqlglot has, and the
  import self-check refuses a sqlglot whose `DROP TABLE` drops its table name.
- The refusals that named `INSERT_OVERWRITE(t)` now name whichever write the Statement has.

**The user's decision on the version (2026-09-26).** 2.0 was already exported with 61 names,
so the user raised `TOOLBOX_VERSION` to "2.1" (drift item D12), and `CHANGES.md` has a 2.1
section for the two names.

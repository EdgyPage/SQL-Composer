# Add `INSERT_INTO` and `drop_table`

Type: task
Status: resolved
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

## Answer

`INSERT_INTO(t)` and `drop_table(t)` ship as the 62nd and 63rd public names, and the user
raised `TOOLBOX_VERSION` to "2.1". `INSERT_INTO` follows every rule of `INSERT_OVERWRITE` and keeps
the day's rows; `drop_table` always writes `DROP TABLE IF EXISTS`. The Example gallery opens with
six Worked examples of common jobs, led by `saved_table.py`: create, create if missing,
overwrite a day, add a second table's rows to it, backfill, and drop and rebuild, each step
saying why. The code review and the beginner reader are answered below; pytest passes at both
ends of the sqlglot range, and no drift item is open.

## Comments

**Build decisions (2026-09-26).**

- sqlglot builds a `DROP` tree differently at the two ends of the supported range (`this=` below
  30, `tables=[...]` from 30), so `drop_table` sets whichever the installed sqlglot has, and the
  import self-check refuses a sqlglot whose `DROP TABLE` drops its table name.
- The refusals that named `INSERT_OVERWRITE(t)` now name whichever write the Statement has.

**The user's decision on the version (2026-09-26).** 2.0 was already exported with 61 names,
so the user raised `TOOLBOX_VERSION` to "2.1" (drift item D12), and `CHANGES.md` has a 2.1
section for the two names.

**Also done under this ticket, at the user's request of 2026-09-26.** The user asked for the
example library to be built out with common SQL jobs, each saying why, and for the internals
to read plainly to an intermediate Python user. So beside the Saved-table example
(`saved_table.py`), five more Worked examples of common jobs landed: `jobs_that_never_ran`,
`labels_and_counts`, `groups_and_top_n`, `lists_and_text` and `step_by_step`. The gallery now
shows a script without `careless()`/`fixed()` as its steps in turn, common jobs first.
Behaviour-neutral readability refactors landed in 63ebaaa.

**Code review (2026-09-26), `d5bcd93...HEAD`.**

- *Standards:* no hard violations. Fixed:
  - Overwrite versus append is decided by a bool, `s._replaces_day`, not by reading the
    message text.
  - `_write` is renamed `_write_clause`; a Clause's `items` and `trees` become `group_columns`
    and `sort_keys`; `_partition_of` becomes `_spans_key`, and its long lines are
    wrapped.
  - `_day_unknown` returns its error, and the caller raises it.
  - `hive_table` takes a plain `partition=` argument.
  - The gallery's entry lists are tidied.
  - The glossary's Worked example allows a Saved table made from the Example tables.
- *Standards, kept as they are:*
  - `__init__`'s DROP check repeats `drop_table`'s branch on purpose, so it tests what
    `drop_table` builds.
  - `for day in backfill()` keeps the Toolbox's own `by_day` wording.
  - A Clause still has one set of fields for every clause kind. That reads better than a
    class per clause, under "No abstraction to study first".
- *Spec:* nothing implemented wrongly; every edge case tried held.
  - Fixed: `drop_table("mart.x")`, given a name as text, now says so instead of calling it a
    Derived table.
  - Scope beyond the ticket's one example is recorded above.
  - `export_lineage` refuses a `drop_table` Statement as it refuses `create_table`'s, which is
    fine.

**Beginner reader (2026-09-26):** [reports/23-beginner-reader.md](../reports/23-beginner-reader.md).
Answered, since each is a bug against the scripts or a wording fix with one plain answer:

- A1: `saved_table.backfill()` wrote only the failed runs, wiping step 3's rows. It now sends
  each day's step 2 then step 3, and says what backfilling is for. `by_day` can't split
  `alerted_runs`, whose DISTINCT would have to keep `dt`, which a write can't select.
- A2: `INSERT_INTO`'s example adds a second table's rows (runs with a high alert) and says to
  send `INSERT_OVERWRITE` first; its first line warns that sending it twice adds twice.
- A3: `drop_table` is for a Saved table you made, and says it would drop a source table too.
  `create_table` offers `check_table_reference` first, and says the drop deletes every day.
- A4: a clause twice now names it: "has INSERT_OVERWRITE and INSERT_INTO, but a Statement has
  only one INSERT clause".
- A5, B7, B8, B10, B11, B16, B17, B18 and B25: "two jobs"; "Build a Saved table"; why `dt` isn't
  selected; why WHERE may test a total from a step; the create_table negatives unstacked; the
  no-Date-partition fix says a Saved table is filled from a table with days; "one day's
  Partition" gone; `run_query` explained; the TEST run left out of the outcome counts.

Left for the user to decide: B5 (what to advise about HIVE-18702 needs the work cluster's Hive
version and engine, still in the map's "Not yet specified"); B9, B12, B13, B19 to B24, B26 to
B30, each a one-line wording choice in older docstrings or the gallery header.

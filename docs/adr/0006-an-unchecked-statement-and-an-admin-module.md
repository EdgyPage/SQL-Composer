# An Unchecked statement for what isn't written yet, and an admin module for changes to tables

Status: accepted

The Toolbox had no way to send Hive it didn't write: `hive_function` covers one function, and the
first design ruled out raw SQL so that every Statement passes the Guards, the Load limits and
Lineage. On 2026-10-15 the user asked not to need a new version for one statement they need now,
and asked for the commands that change their own tables (drops, ALTERs) to be written for them
rather than by hand.

So 5.0 adds two things, each kept apart from the everyday Statements:

- **`unchecked_hive("...")`, the Unchecked statement**, runs Hive text the user writes, the way a
  Statement is run, though it isn't one. No Guard or Load limit looks inside it, and Lineage draws
  it as one opaque step with a warning badge. It is allowed, not encouraged: each one marks something the
  Toolbox should learn to write. Text that starts `DROP`, `ALTER` or `TRUNCATE` warns, naming the
  admin function that writes it, checked.
- **The admin module** (`from sqlglot_composer import admin`, not in the star import) writes the
  changes to a Saved table's definition or data: dropping the table or its old days, adding
  columns, setting properties, moving it to a folder of its own. Each is an ordinary Statement,
  which `show_hive` prints after what it changes and what can't be undone. Each refuses a table
  that isn't one of the user's Saved tables. `drop_table` moves here from the ordinary names.
- **The Admin log** keeps a text record of every Admin statement and Unchecked statement run:
  when, which table, the Hive, the script and its commit, and whether it worked. Its Unchecked
  statements are the list of what to add next.

This reverses the first design's "no raw SQL" for the one, loudly marked, case.

## Considered options

- **No escape hatch**: every need waits for a Toolbox feature and a release. Rejected by the user.
- **Admin statements that run only with a confirmation**, such as `run(..., confirm="<table>")`,
  or that only hand back text to run by hand. Rejected: using the Toolbox at work is already a
  privilege, so friction on friction adds clutter; keeping the commands in their own module,
  logged, is the separation.
- **Leave drops and ALTERs to the Unchecked statement.** Rejected: they are common enough to write
  checked, with their warnings, and the hatch should hold only real unknowns.

## Consequences

- A pipeline can now carry Hive the Toolbox didn't build, as an Unchecked statement, so the dry
  run, Lineage and the Admin log all say so where it appears.
- The ordinary names lose `drop_table`; 5.0's CHANGES says to import it from `admin`.
- The Admin log is a file the Toolbox writes beside the user's notebook, like Lineage pages.

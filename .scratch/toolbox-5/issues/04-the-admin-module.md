# The admin module

Type: task
Status: open
Blocked by: 02, 03
Size: M

## Question

Map family 4 and ADR 0006. `from sqlglot_composer import admin` (not in the star import):
`drop_table` (moved from the ordinary names), `drop_days(t, before=)`, `add_columns(t, send=)`,
`set_properties(t, ...)`, `move_to_own_folder(t, send=)`. Each an ordinary Statement, its
description (what it changes, what can't be undone) printed by show_hive before its Hive, refused on a table that isn't one
of the user's Saved tables, logged in the Admin log when run. A how-to, "Move a Saved table to its
own folder".

## Done when

- Each admin Statement's Hive in the golden corpora; the refusals; the log entry; the how-to's
  move run on the Example database where it can.
- Both runs pass, the code-review skill has run with this ticket as its spec, its drift items are
  closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's Definition of done).

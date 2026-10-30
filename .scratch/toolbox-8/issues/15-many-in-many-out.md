# Multi-inserts, many writes to one table, and a table that reads itself

Type: task
Status: open
Blocked by: 14
Size: M

## Question

The user (2026-10-30): "Perhaps something that exports to multiple tables too." And an
incremental script's table reads itself, which in dev starts empty.

## Done when

- A multi-insert (`FROM src INSERT OVERWRITE TABLE a … INSERT OVERWRITE TABLE b …`) gives one
  Saved table per target, each reading the shared FROM. Today's refusal of several INSERTs goes.
- Several statements writing one table give one Saved table whose logic stacks the pieces in
  script order (a Stack, UNION ALL), each piece's filter kept.
- A table whose statement reads itself gets a seed step in the convert Workflow, a permission: a
  call that copies the original's rows into the dev copy once, logged in `sent.csv`; `write()`
  then runs as written. The checklist says why.
- Each case has a test on the Example database, and a how-to example in ticket 19.

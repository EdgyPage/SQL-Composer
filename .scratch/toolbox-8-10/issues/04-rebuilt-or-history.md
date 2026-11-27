# Rebuilt or History: each table's kind, a Decision proposed from its write

Type: task
Status: open
Blocked by: -
Size: M
Spec: [specs/04-rebuilt-or-history.md](../specs/04-rebuilt-or-history.md)

## Question

Nothing asks whether a table is rebuilt whole by each write or keeps its past rows (round 1,
Q7 and Q9; round 2, Q6; CONTEXT.md's Rebuilt table and History table). The kind decides whether
a table has a Seed (ticket 05).

## Done when

- **Each table convert and `new_table` write has a kind**, Rebuilt or History, in its Table
  reference, answered in the Workflow's decisions cell as 8.5's Decisions are, never by a hand
  edit; answering again changes it.
- **Proposed from the write**, and accepted as 8.5's proposals are:
  - DROP, then CREATE and INSERT: Rebuilt;
  - `INSERT OVERWRITE TABLE` with no PARTITION: Rebuilt;
  - `INSERT OVERWRITE ... PARTITION (dt = <value>)`: History;
  - `INSERT INTO`, an append: History;
  - a dynamic `PARTITION (dt)` overwrite: no proposal, so the Decision waits on the user.
  A Conversion's table whose write reads itself, which has a `seed()` today, is History.
- A Rebuilt table never asks about a Seed; a History table always does (ticket 05).
- An answer may be given once under `all_tables`, a table's own overriding it.
- **Tests**: each write above gives its proposal; the dynamic overwrite leaves the Decision
  open and the step waits on it; an answer under `all_tables` and one of a table's own.
- The beginner reader runs, since the decisions cell changes.

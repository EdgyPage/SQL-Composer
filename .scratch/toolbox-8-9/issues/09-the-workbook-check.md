# The Workbook check

Type: task
Status: open
Blocked by: 07
Size: L

## Question

The check of a Formula workbook's Hive against the workbook's own numbers, offline (round 1,
Q9; round 2, Q7; round 3, Q5; CONTEXT.md's Workbook check).

## Done when

- **A new Toolbox file**, in the registry's `LIBRARY_FILES`, runs each final's Hive on sqlglot's
  executor, each `<database>.<table>` standing in for the workbook's typed rows of that Table,
  and compares its rows with the values Excel last stored: a Table's cells, a Total Row's, a
  pivot's.
- **A match**: numbers within a relative 1e-9 on stored values; a blank matches NULL only where
  file 11's M1 marks it; rows matched on the final's Key or its GROUP BY, in any order.
- **A difference** is one line a cell in the convert notebook ("Region East, Mar: Excel 1,204,
  Hive 1,198"), and blocks nothing. A piece the executor can't run is named, with why.
- **It never reads the warehouse** and never calls `query`.
- **The Copilot path**: a batch of `.hql` files with the workbook beside them checks each `.hql`
  whose name is a final's.
- Tests: a match and a difference for each kind of final; an `.hql` from Copilot checked; the
  offline trap holds.

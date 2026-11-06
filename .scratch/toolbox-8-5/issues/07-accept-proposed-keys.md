# A batch's proposed Keys accepted at once

Type: task
Status: open
Blocked by: 02
Size: S

## Question

Each table's proposed Key is confirmed one by one (map, Q5).

## Done when

- `"all_tables": {"key": "proposed"}` accepts each table's proposed Key, written as if typed;
  a table's own `"key"` wins; a table with no proposal stays open, named in the report.
- A guessed column type is never accepted so: `"all_tables"` refuses `"types"`, saying each is
  the table's own.
- `project.check()`'s printed DECISIONS offers it when two tables or more have a proposed Key.

## Answer

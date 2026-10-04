# Join Guards read the condition tree

Type: task
Status: claimed
Blocked by: 06

## Question

Two join Guards fire on correct Statements, which teaches users to opt out by reflex
(candidate 7 of [report.html](../report.html)):

1. **The LEFT_JOIN Guard refuses `any_of(is_null(joined.col), ...)`**, the usual way to keep
   unmatched rows or matched rows that pass a test. The Guard knows only whether a condition
   *is* an is_null (`Condition._tests_for_null`), so an any_of with one inside is refused, and
   its fix, moving the condition into ON=, changes the answer.
2. **ON= built from an all_of Building block gets a false RepeatedRowsWarning.** `flatten`
   stops at an AND in brackets, so `ON=all_of(key_block, ...)` hides the key equality inside
   `key_block`, and the join is said not to use the key.

## Decisions (made under the user's goal to implement every candidate worth it, 2026-10-03)

- **A condition knows which joined tables' unmatched rows it keeps**: is_null of a table's
  column keeps that table's; any_of keeps a table when any of its parts does; all_of keeps it
  when every part that mentions it does. The LEFT_JOIN Guard refuses a WHERE condition on the
  joined table only when the condition doesn't keep that table's unmatched rows.
- **The key check reads through brackets around an AND**: AND is associative, so
  `(a AND b) AND c` is a, b, c; an OR inside an AND stays whole. `trees.Node.flatten` itself
  is left as it is, since a test holds it to sqlglot's own flatten, which keeps the brackets.

## Done when

- Both have tests through the public names, run in both Editions.
- Both runs pass; goldens and galleries regenerated if their text changed.
- The code-review skill has run with this ticket as its spec, and the drift items are closed.

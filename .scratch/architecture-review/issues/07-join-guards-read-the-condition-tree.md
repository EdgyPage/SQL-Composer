# Join Guards read the condition tree

Type: task
Status: resolved
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

## Answer

Built in `33b3bc5`, reworked after the review in the commit after it.

- A Condition knows which tables' rows with no match it keeps (`_keeps_unmatched`): is_null of
  a table's column; any_of when any part keeps it; all_of when every part mentioning the table
  keeps it (`_kept_by_all`). The LEFT_JOIN Guard asks it.
- The repeated-rows check reads an AND in brackets inside an AND the same way (`_and_parts`);
  `trees.Node.flatten` keeps its brackets, as a test holds it to sqlglot's.
- `tests/test_join_guards.py` pins both in both Editions, nested cases included.

**Beginner reader** ([report](../reports/07-beginner-reader.md)): 4 stops; 3 changed, 1
answered.

**Code review (2026-10-03), `33b3bc5`.**
- *Standards:* no hard violations. Fixed: LEFT_JOIN's docstring, which said every WHERE on the
  joined table is refused; the alias named once; all_of's rule as a small function. Kept:
  is_null reading its column's tree, as the rest of the file does.
- *Spec:* no wrong behaviour found in many probes; nested cases added as tests. One
  conservative refusal is left as the Decision says: with two LEFT_JOINs, is_null of the second
  table doesn't count as keeping the first's rows with no match.

| Items | Opened by | Closed by |
|---|---|---|
| (none) | `33b3bc5` was clean | |

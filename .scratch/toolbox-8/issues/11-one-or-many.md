# One or many: every Project action takes a list

Type: task
Status: open
Blocked by: 10
Size: M

## Question

The user (2026-10-30): "let's generalize patterns to assume multiple inputs across the board to
scale for this stuff."

## Done when

- Every Project action that takes a thing (a table name, a Building block, a file, a Conversion
  name, a Table reference) takes a str or a list of them, the same way, and gives one report for
  the batch. A call with one str works as today.
- A batch that stops on one item names it, says why, and keeps the items done before it, which
  its report lists; the refusal says how to run the rest.
- Each public signature and docstring says it; CHANGES.md's `## 8.0` begins with it.
- CONTEXT.md's Project action entry says "one or many".
- The graph's counts don't rise.

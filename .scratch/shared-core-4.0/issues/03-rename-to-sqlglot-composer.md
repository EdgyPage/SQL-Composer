# Rename to sqlglot composer

Type: task
Status: open
Blocked by: 02
Size: L

## Question

Rename `sql_composer` to `sqlglot_composer` and "SQL Composer" to "sqlglot Composer"
everywhere: tools, tests (imports, the golden corpus file name), worked_examples, the drift
hook, the CI job's id and name, the README template, CONTEXT.md, CLAUDE.md, standards.md, the
beginner reader's brief.

## Done when

- The goldens and galleries differ only by names; the beginner reader has run.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).

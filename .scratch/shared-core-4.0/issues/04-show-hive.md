# Show hive

Type: task
Status: open
Blocked by: 03
Size: S

## Question

A new public name, `show_hive(*statements)`, in running.py: prints the Hive each Statement
sends, each ending in `;`, several headed `-- 1 of 3: <variable name>`, ready to paste into
Hue, Beeline, DBeaver or spark-sql, and returns the same text. Takes Statements or a list such
as by_day gives; refuses what to_hive refuses. Docstring example, cheat-sheet line, CHANGES.

## Done when

- Tests in both Editions: one Statement, a by_day list, the text is to_hive's plus `;`, printed equals returned; the beginner reader has run.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).

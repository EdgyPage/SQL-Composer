# Show hive

Type: task
Status: resolved
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

## Answer

Built in the commit that resolves this ticket.

- `show_hive(*statements)` (composer_core/running.py) prints each Statement's Hive, exactly
  what to_hive gives and run sends, with a `;` added, and returns the same text. Several
  Statements, or a list such as by_day gives, are each headed `-- 1 of 2: failed_runs`: the
  variable a Statement is in, or `days[0]` for one in a named list, or just the number.
- It returns a `HiveText`, a str that a notebook doesn't show a second time, since show_hive has
  printed it.
- `name_in(frame, value)` finds a variable's name by identity, for show_hive and export_lineage
  alike (lineage's `statement_names` now uses it).
- The public names are 64; the cheat sheet's line comes from the docstring. The CHANGES line goes
  into ticket 15's 4.0 section (the map's note lists it).

**Code review (2026-10-05).** Spec: fixed Statements in a list losing their own names, a list
inside a list now refused plainly, the CHANGES line noted for ticket 15. Standards: one name
lookup for both features (no lazy import), the same frame lookup as export_lineage, a
two-Statement example in the docstring, "Spark's" wording gone.

**Beginner reader (2026-10-05).** Fixed: the heading names explained (the variable it is in),
why to write `text = show_hive(...)`, the `;` explained without Spark, Beeline dropped.


# Unchecked expressions and the Unchecked derived table

Type: task
Status: open
Blocked by: 01
Size: M

## Question

A Conversion keeps the 80% that converts (ADR 0014): what the Clause functions can't write stays
Hive text at the smallest size, one expression or one CTE, inside an otherwise checked
Statement. The user said yes (2026-10-26) to three names beside `unchecked_hive`, so a search
for `unchecked_` finds every piece the Toolbox still has to learn.

## Done when

- `unchecked_column(text)` gives back a Column and `unchecked_condition(text)` a Condition, each
  written into the Statement as the text given. The Toolbox parses the text to read the columns
  it names, and refuses text it can't parse as one Hive expression, or that names a table the
  Statement doesn't read. A Column whose text is an aggregate needs `AS` and `GROUP_BY`, as
  `hive_function`'s do.
- `unchecked_derived(name, text, columns=[...])` gives back a `Table` read as any Derived table
  is: its columns are the ones declared, and a read of one that isn't declared is refused as for
  any Table. Its text is one SELECT, kept as written.
- Lineage traces an Unchecked expression to the columns its text names, with the same warning
  badge as an Unchecked statement's step, and draws an Unchecked derived table as one opaque box
  over the tables its text reads.
- The Guards, Warnings and Load limits check the rest of the Statement as now. Where one can't
  look inside an Unchecked piece (a partition filter written only in an `unchecked_condition`,
  say), it says so in its message rather than passing silently or refusing.
- The Admin log notes each Statement sent with an Unchecked piece in it, as it notes an Unchecked
  statement.
- Each name is public, typed, with a Worked example opening its docstring, and in the gallery.
- CLAUDE.md's Definition of done, the beginner reader included.

## Glossary

New, under "Writing a Statement":

> **Unchecked expression**:
> Hive text the user, or a Conversion, writes in place of one Column or Condition that no Toolbox
> function writes yet, inside an otherwise checked Statement. The Toolbox reads which columns it
> names, so Lineage traces it, but no Guard looks inside it. In Python, `unchecked_column(...)`
> and `unchecked_condition(...)` give one back.
> _Avoid_: raw expression, SQL snippet, passthrough

> **Unchecked derived table**:
> A Derived table whose Statement is Hive text kept as written, with its output columns
> declared, for a piece no Clause function writes yet. It is read like any Derived table and
> shown as one opaque box in Lineage. In Python, `unchecked_derived(...)` gives back a `Table`.
> _Avoid_: raw CTE, unchecked view

**Unchecked statement**'s last sentence gains: "Its smaller kin, the Unchecked expression and
the Unchecked derived table, sit inside a Statement."

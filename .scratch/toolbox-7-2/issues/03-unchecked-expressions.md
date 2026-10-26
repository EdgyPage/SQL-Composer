# Unchecked expressions and the Unchecked derived table

Type: task
Status: resolved
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

## Answer

Built 2026-10-26 in a worktree (branch `worktree-agent-ae89c3879a8b9d2d7`, cut from dev at
ffd8bde), side by side with ticket 04; the main session merges it into dev and runs the reviews.

- **`unchecked_column(text, /, **columns)` and `unchecked_condition(text, /, **columns)`** give
  back a Column and a Condition. Each column the text reads is a `{name}` placeholder, bound by
  keyword to the real Column, the way str.format reads them, a literal brace doubled (the main
  session's design, made after this ticket was written): `unchecked_condition("{status} RLIKE
  '^FAIL'", status=job_runs.status)`. `text` is positional-only, so any placeholder name works,
  `text` and `name` included. The tree holds a new Node kind, `Unchecked` (its text, the
  placeholders' names, the bound Columns' Nodes as its children, and whether it adds rows up or
  looks through a window), so `walk()`, Lineage and the Guards see the real columns, and a table
  renamed with AS writes right. writing.py fills each placeholder with its Column's Hive (a
  calculation in round brackets) and reads the text with sqlglot.
- **"Names a table the Statement doesn't read"** now falls out of the placeholders: the bound
  Columns are real, so statement(...) refuses one of a table it doesn't read, as for any column.
  Text that names a column itself is refused, the call written out with its placeholder:
  `unchecked_column("upper({team})", team=jobs.team)`.
- **Refused**, each in four parts from `refuse(...)`: text that isn't a string or is empty; braces
  str.format can't read; a placeholder with no name, a conversion or a format spec; a
  placeholder with no Column passed, a Column passed that no placeholder names, or a value that
  isn't a Column; text that, filled in, doesn't read as Hive (sqlglot's reason, without its
  character count, which counts the stand-ins); more than one expression; a name given with AS
  inside the text; a sub-query or any table read of its own (pointing to unchecked_derived);
  a placeholder inside quotes. Not checked: that an `unchecked_condition`'s text is a condition,
  which Hive refuses loudly.
- **Written as sqlglot reads the text**, not byte for byte: to_hive reads every Statement's
  Hive back to check it, so the text goes through sqlglot like the rest (capitals, a default
  argument dropped, a `--` comment as `/* */`), as hive_function's calls do. The docstrings say
  so. The same goes for the Unchecked derived table's SELECT, laid out as the Toolbox lays out
  its Hive.
- **An aggregate** in the text (sqlglot's own aggregate functions, or a name on hive_function's
  list, outside OVER) is marked on the Node, so `is_aggregate`/`has_aggregate` treat it as
  hive_function's: it needs AS (as every calculation) and GROUP_BY, and is refused in WHERE. A
  window (OVER) is marked too, so `has_window` refuses it in WHERE as a Window. An Unchecked
  column adds up unless a Column bound to it doesn't, as hive_function's.
- **`unchecked_derived(name, text, columns={...})`**: `columns` is a dict of name and Hive type
  (or None), as Table's is, rather than the ticket's list, so values compared with its columns
  are checked as any Table's. Its text must read as one SELECT (or a UNION, INTERSECT or EXCEPT);
  where sqlglot can tell the names of the columns it gives (no `*`), they must be the ones
  declared, in any case. The Table's `_statement` holds an `UncheckedSelect` (tables.py: the
  text and the tables it reads, read by sqlglot, leaving out its own WITH names), and each of the
  `_statement` sites handles it: `derived_tables` doesn't look inside it, `statements_within`
  and the subtotals check skip it, `_with` writes it as a CTE through a new `UncheckedSelect`
  Node, the repr is `unchecked_derived('steps', columns: ...)`, and FROM, AS, INSERT_OVERWRITE's
  and python_step's refusals treat it as the Derived table it is.
- **Keys**: it has none, its `_keys.lost` saying its Hive is written by hand. A JOIN on it warns
  as on any Derived table without a Key, giving that reason. A write reading it is still refused
  by the Key Guard unless `unproven_key=True`, the message giving the reason: that Guard's job
  is to refuse any write whose Key it can't prove, so it isn't loosened here.
- **Where a Guard or Load limit can't look inside**, it warns (a new, not public,
  `UncheckedWarning`), each silenced by the opt-out it already has: a partitioned table whose
  partition columns are filtered only inside an Unchecked expression (opt-out
  `reads_all_partitions=True`; one that names no partition column is refused as ever); a WHERE
  that reads a LEFT_JOIN's or a FULL_JOIN's table only inside one (opt-out
  `keeps_only_matches=True`); and a FROM or JOIN reading an Unchecked derived table whose text
  reads tables, at statement(...), naming them (opt-out `reads_all_partitions=True` on that
  read). Their messages are built in refusals.py.
- **The Admin log**: run_query and run_execute (so project.run_tables too) add an entry for a
  Statement holding one, headed `Statement with an Unchecked expression`, `... an Unchecked
  derived table` or both, its Call line each piece's call (`unchecked_derived("steps", ...)`
  for a derived table). to_hive and show_hive log nothing. The log's header is unchanged: the
  Example projects and the frozen 7.1 ones for ticket 02 hold it.
- **Lineage**: an output or Derived table column worked out by an Unchecked expression traces to
  the columns it binds, its box named after the Unchecked statement's badge (`⚠ team_region`)
  and drawn marked unchecked; a condition box gets the badge only, since the page's script
  compares a condition's kind exactly. An Unchecked derived table is one box, `⚠ Unchecked
  derived table`, in its own group (drawn as a Derived table, marked unchecked), with an arrow
  in from a whole-table box for each table its text reads and out to a box for each declared
  column. The Keys list says it has none and why; a section's opening lists the Unchecked pieces
  its Statement holds; and the tables its text reads count as read when ordering Statements.
- **The Example database** refuses a LATERAL VIEW plainly ("its executor has no LATERAL VIEW"):
  sqlglot's executor failed on one with a message holding an object's id, which would change
  the gallery on every run.
- Public names 105 (`tests/repo/test_toolbox_checks.py`, "Toolbox 7.2, ticket 03"); each
  docstring opens with a Worked example on the Example database (unchecked_column's runs; the
  other two show their Hive, which the executor can't run); the gallery is regenerated; the
  how-to page and the Example projects come out unchanged. CHANGES `## 7.2` "Also new"; CONTEXT:
  the two entries (the Unchecked expression's with a phrase on placeholders), the Unchecked
  statement's added sentence, and the Admin log's entry now naming Statements that hold one.
- The golden Hive corpus (`tools/hive_corpus.py`, which now skips an Unchecked derived table's
  parts) gains the three docstrings' cases, nothing else changing; the Clean branch README's
  count of names is 105.
- Tests: `tests/test_unchecked_expressions.py`, and each new Warning's `_warns` and `_opt_out`
  in `tests/test_refusals.py`.

Left for the main session: the code review, the beginner reader and the drift review, after the
merge.

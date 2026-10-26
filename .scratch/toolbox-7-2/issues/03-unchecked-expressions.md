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

## Reviews

Merged into dev as 1078a08; the code review's fixes in b158071 (with ticket 08's). The
beginner reader's report, [reports/03-08-beginner-reader.md](../reports/03-08-beginner-reader.md),
and drift items D268 to D270 were fixed in a worktree, finding by finding:

- Beginner reader, 03:
  - 1 (two phrasings of "no ... function writes it yet"): fixed, unchecked_hive's first line
    says "no Toolbox function", as the other three do.
  - 2 (placeholders named `name`): fixed. Each refusal's fix shows a call of its own kind
    that runs on the Example database (`unchecked_column("upper({team})", team=jobs.team)`, a
    LIKE condition for unchecked_condition, `SELECT DISTINCT team FROM ops.jobs` for
    unchecked_derived), and the docstrings write `{minutes}`, `{job_name}`, never `{name}`; a
    test holds that no fix names `{name}` or `name=`.
  - 3 (examples that can't run here): fixed, unchecked_condition's docstring says the Example
    database has no RLIKE and gives a LIKE that runs; unchecked_derived's says it has no
    LATERAL VIEW. Answered: the failed run's Admin log entry is right, as it logs every run of
    a Statement holding Hive written by hand, failed ones too.
  - 4 (unchecked_derived's example unexplained): fixed, a paragraph says what explode, split
    and LATERAL VIEW do there. Answered: the example is kept, as the corpus and gallery hold it,
    and LATERAL VIEW is the piece no Clause function writes.
  - 5 (three placeholder styles): answered, by design: unchecked_hive takes a whole statement,
    where an f-string of Table references is its way; the Unchecked expressions bind columns so
    Lineage traces them; unchecked_derived's text names its own tables, which the Toolbox
    reads. Its braces are now refused (item 6), and its docstring says it takes none.
  - 6 (braces sqlglot can't write, a raw error at to_hive; costliest 2): fixed. Each text is
    written once at the call through `writing.sql_text` (`_unwritable`), and what sqlglot reads
    but can't write is refused in four parts, saying a brace is doubled and only the two
    Unchecked expressions take placeholders.
  - 7 (ILIKE rewritten): fixed in unchecked_column's docstring, which names it.
  - 8 (sqlglot's class name in a refusal): fixed, "Required keyword ... <class ...>" is said in
    plain words, and a test holds no `<class` in a refusal.
  - 9 (`unchecked_column("upper({})", jobs.team)`): answered: Python's own TypeError names the
    one positional argument; catching more would put `*args` in help()'s signature.
  - 10 (a condition that isn't one; unchecked_column in WHERE): fixed, WHERE (any place taking
    conditions) given an unchecked_column refuses with the same call written as
    unchecked_condition. Answered: whether a text is a condition stays unchecked, as Hive
    refuses one loudly; the docstring now says so.
  - 11 and 12 (the Warnings' opt-outs; `{x} IS NULL`): fixed. Each opt-out says what it means
    there ("reads_all_partitions=True), which here says you have checked the Unchecked
    expression bounds them"; keeps_only_matches=True "says you have checked the Unchecked
    expression: that WHERE may keep it, whether or not it keeps the rows with no match", which
    is true of a condition that keeps the NULL rows too), and the LEFT_JOIN fix names the
    table, not `{x}`.
  - 13 (a Warning for a text reading no partitioned table): fixed. A read of an Unchecked
    derived table warns only for the tables its text reads that are partitioned, by their
    Table references (`tables.partitioned_by_name`, over the Table references in use, the
    Example database's included), or that the Toolbox has none for; the message says which.
  - 14 (joining one that already groups; costliest 3): fixed. `unchecked_derived(...,
    key=[...])`, as Table takes it, gives it a Key taken on trust: a JOIN on it is checked as on
    a Derived table with a Key, a write reading it isn't refused when its key holds, the Keys
    in Lineage name it, and a JOIN on one without a key says key= may name it. The docstring
    and CONTEXT.md's entry say so.
  - 15: fixed with D269.
  - 16 (repr gives no sign it's unchecked): answered, a Column's repr is its Hive, as for
    every Column; Lineage and the Admin log mark it.
  - 17 (CHANGES' LATERAL VIEW): fixed, it says what LATERAL VIEW does, and names key=.
- Drift: D268 fixed, the fix for a column named itself is built from sqlglot's reading
  (`writing.with_placeholders`): every column named itself becomes a placeholder, named by its
  plain name (numbered if taken, never a Python keyword), text in quotes left alone, the
  columns already passed kept, and `<table>` where the text gives no table; tests follow each
  fix and check it isn't refused. D269 fixed in set_admin_log's docstring and the Admin log's
  HEADER, the Example projects regenerated (only their admin_log.md heading changed; the frozen
  7.1 projects are untouched). D270 closed by 1a0ef3d: ticket 07's Conversion entry landed in
  CONTEXT.md before these fixes were rebased onto dev, so "or a Conversion" in the Unchecked
  expression's entry names a glossary word and stays.

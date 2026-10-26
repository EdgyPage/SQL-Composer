# Checking a Conversion

Type: task
Status: open
Blocked by: 07
Size: M

## Question

The user (2026-10-26): "give me the tools to check the conversions because it'll likely be the
case that something 80% convertable exists". Two checks, grilled the same day: the Hive,
compared at every Conversion (ticket 06's round trip), and the rows, through the user's `query`,
when they ask, and again after every edit they make to the converted notebook.

## Done when

- `compare_with_original(statement, original, query=query, where=...)` sends one query through
  `query` that counts the rows each gives and the rows found in one and not the other, matched
  on every column, and gives back a Verdict-like report: the counts, and a few differing rows of
  each side to look at. It reads only through `query`, never `execute`.
- A partitioned table read without `where=` is refused as any unbounded read is, unless
  `reads_all_partitions=True`; the report says which partitions it compared.
- A Statement holding Unchecked pieces is compared as any other; the report names them, since a
  difference there can't be traced further by the Toolbox.
- `compare_hive(statement, original)` gives back whether the two match once normalised by
  sqlglot, and where they first differ: the check ticket 06 runs, for the user to run again
  after editing the notebook.
- The converted notebook has a cell for each, after the logic, and `finish_conversion` keeps
  them in the Table notebook until the user removes them.
- Names are public, typed, with a Worked example on the Example database opening each
  docstring.
- CLAUDE.md's Definition of done, the beginner reader included.

## Answer (the functions)

Built 2026-10-26 in a worktree, beside tickets 03 and 04, before 07: the two functions, not
the notebook cells, which 07's converted notebook will hold. The main session settled, before
the build, `partition={...}` in place of `where=`, one query through `query`, the original's
columns matched by name and in order, and that only `writing.py` reads Hive with sqlglot.

**Where they live: a new file, `sqlglot_composer/comparisons.py`**, listed in
`tools/toolbox_registry.py`. Neither fits an existing file: `tables.py`, home of `check_key`
and `Verdict`, is about one table and is 1,800 lines already; 07's Conversion can import them
from here. The sqlglot work is in `writing.py`: `normalised_query`, `query_columns` and
`rows_compared`. `running.py` gains `hive_without_automatic_limit(s)`.

**Both give back a `Verdict`**, the type `check_key` gives, with `ok` and a readable repr, so
no new public type: its docstring now names the two. The numbers are in its lines, not fields.

**`compare_hive(statement, original)`**: "the same" is decided and written in its docstring.
Both are read by sqlglot's Hive and written out pretty; these don't count: spacing, case
(names are lower-cased, as Hive reads them; functions sqlglot doesn't know upper-cased),
backticks (a name is quoted only where Hive needs it), comments, a trailing `;`, a bracket
that changes nothing (round a column, value, call or bracket; round a whole condition, output
or argument; an AND in an AND, an OR in an OR; never round or in an operator, nor one written
as a function, like `DIV`), INNER and OUTER, `AS` giving a column its own name, and the short
names of tables: each table, and a WITH table, is called by its own name where nothing beside
it already is, and a query reading one table alone drops the table from its columns (but in
ORDER BY, where the name may stand for an output named otherwise). No `qualify` or `simplify`:
anything else counts, even where the rows match (`NOT a = b` against `a <> b`), which
`compare_with_original` is for. Where they differ it shows the first differing line of each,
by line number, stripped of its indent, or "(nothing: it ends after line N)".

**`compare_with_original(statement, original, *, query, partition=None,
reads_all_partitions=False)`**: one query, built as text by `writing.rows_compared` with both
queries read by sqlglot and written back in. The brief's FULL OUTER JOIN on `<=>` doesn't run
on the Example database (its executor has no `<=>`), so the two sides are stacked with UNION
ALL, each row marked 1/0 per side, and grouped on every column, which matches NULL with NULL
and counts repeats without any join: Hive's usual way to diff two tables. One more CTE each
gives the four totals and up to 5 differing rows per side (`LIMIT` in a CTE, no window, since
the Example database refuses those), joined onto the totals by a constant so the totals come
back even when nothing differs. The answer is read by place, not by column name, as some Hive
clients prefix names with their table.
- Hive takes no WITH inside another, so each side's WITH tables are moved up into the one
  WITH, renamed `statement_<name>` and `original_<name>`, each read keeping the name it was
  called by, so `day_runs.run_id` still reads it.
- The Statement's Hive is to_hive's without the automatic LIMIT `set_load_limits(rows=...)`
  adds when sending (and so for `compare_hive` too): that LIMIT would make every comparison
  differ.
- A write (the Statement or the original's `INSERT ... SELECT`) is compared by its SELECT, as
  the map recommended for the scan; SET lines or a second statement are refused, "holds 2
  statements, where one query goes".
- The columns: both sides' names come from their Hive, read by sqlglot, Hive's own names for
  what has none (`_c1`) and `*` as `*`; compared case-blind. A mismatch refuses, naming both
  lists, before anything is sent.
- `partition=`: a dict of output columns to one value each, written by `literal()`, kept with
  `=` on both sides inside the comparison, after each side's query (Hive pushes it down to the
  table). Refusals copy `compute_statistics`' shape: not a dict, empty, an unknown name (listing
  the columns), None or a column as a value. Left out while any table the Statement reads,
  through its Derived tables and Stacks too, is partitioned, it refuses as `check_key`'s
  `where=` does (ValueError, the opt-out named in the fix), unless `reads_all_partitions=True`.
  The report says "where dt = '...'", ", in every Partition", or nothing for a Statement that
  reads no partitioned table. The original's own tables aren't checked: the Toolbox doesn't
  know them.
- Not done: "the report names Unchecked pieces". Unchecked expressions and derived tables are
  ticket 03's, built beside this; the main session or 07 adds the line once both are merged.

**A fix to the Example database, found on the way** (`engine.py`): sqlglot's executor names
each step of a UNION, INTERSECT or EXCEPT after the table it reads and keeps one step per
name, so a Stack of two reads of one table (`job_runs` on two days) gave one side's rows twice,
silently. Where a query stacks, `run_query` now writes it out as the executor does and renames
each repeated table name (`job_runs_2`) with its columns, scope by scope. The comparison
depended on it; `tests/test_stacking.py` holds it, and CHANGES.md says so.

**Left for whoever runs it at work**: Hive must accept both sides in one UNION ALL, so a column
of one type on one side and another on the other may be refused by an old Hive; a column of
arrays or maps can't be grouped by Hive at all. The suite could only run on sqlglot 30.23.0
here: CI's 25.24.2 run is the first on the bottom of the range (`compare_hive` doesn't need the
executor; `compare_with_original`'s Worked example skips there as `run_query`'s do).

Hive sqlglot reads but can't write back as Hive is refused, not written loosely: `sql_text`
stays the one writer, always strict (a test holds it), for what is only shown too.

Tests: `tests/test_comparisons.py`; the gallery and how-to page regenerated; CHANGES.md's 7.2
"Also new" has a line for each; the README template counts 104 names.

## Reviews

Built beside 03 and merged into dev as 7aba998; the code review's fixes in b158071 (the
Unchecked pieces named, the comparison sent through `send_logged`, a partition= on no partition
column refused). The beginner reader's report,
[reports/03-08-beginner-reader.md](../reports/03-08-beginner-reader.md), drift items D266 and
D267, and one more asked for by the main session were fixed in a worktree, finding by finding:

- Beginner reader, 08:
  - 1 ("the Hive it was converted from"): fixed, each docstring and message says "the original
    Hive it replaces", which reads without knowing a Conversion, and holds too for Hive
    rewritten by hand.
  - 2 (short names unclear): fixed, compare_hive's docstring gives `r in FROM ops.job_runs r`
    and says plainly what each is written as.
  - 3 (" = :"): fixed, "a <> b written as NOT a = b".
  - 4 ("line 6 of each"): fixed. The Verdict says "lines 1 to 5 match, and line 6 differs",
    shows up to two matching lines before it, "line 4, in both: ...", then the line of each;
    the docstring says the lines are counted as both are written out for comparing, not as
    to_hive writes them.
  - 5 (the first differing line can mislead; conditions in another order): fixed, the lines
    before it show where it is (a test holds the extra column case), and the docstring says
    two conditions in the other order count.
  - 6 ("..", INNER and OUTER): fixed, sqlglot's reason loses its full stop, its `<Token ...>`
    names and its "Line 1, Col: 17" (said "at line 1, column 17"); "LEFT OUTER JOIN is LEFT
    JOIN" is said.
  - 7 (reads_all_partitions=True on FROM, then partition=): fixed, a sentence in the Worked
    example says why.
  - 8 (a Statement that filters its own partition; costliest 1): fixed. partition= may name a
    partition column of a table the Statement reads that it doesn't give: every read of that
    table, in the Statement and in the original alike, becomes a read of that Partition alone
    (`(SELECT * FROM ops.job_runs WHERE dt = '...') AS job_runs`, `writing._reads_bounded`), so
    the original needs no dt among its columns. The Verdict says "reading ops.job_runs where
    dt = '...'". The refusal without partition= names a partition column, never another
    (`_example`), and says which table it partitions; "in every Partition" is said only where
    no read of the Statement is bounded by its own conditions, else "each in the Partitions its
    own conditions pick". A write into one static Partition is compared the same way (tested),
    as is a Conversion whose notebook passes the original's PARTITION(...) column.
  - 9 (where=): fixed, refused pointing to partition= with an example.
  - 10 (a Verdict whose ok is False is truthy): fixed, `bool(verdict)` is its ok, for
    check_key and check_table_reference too; nothing in the Toolbox, its tools or tests relied
    on a Verdict being always true (grepped). Verdict's docstring and CHANGES say so.
  - 11 (None in one table, NaN in another): answered, that is pandas showing each answer as
    the warehouse gives it; the comparison matched NULL with NULL already.
  - 12 (the Unchecked line): fixed, a full sentence: where the rows match, "The rows match, so
    it gives what the original gives here."; where they differ, "Check that Hive first: the
    Toolbox can't trace a difference inside it." The docstring says so (D267), and the Admin
    log entry's heading now ends ", compared with the original by compare_with_original".
  - 13 (the comparison query can't be previewed): answered, not done here: a preview needs a
    public way to show it, a new name for the tracker; the Example database's refusal names
    what its executor lacks.
  - 14 (a positional query): answered, query= is keyword-only as in check_key, so the call
    always names it.
- Drift: D266 fixed, the docstring says partition= must name a partition column of a
  partitioned table the Statement reads, or reads_all_partitions=True. D267 fixed, its
  paragraph names the Admin log entry and the last line.
- The main session (2026-10-26): SET lines in the original, and before an INSERT, are passed
  over by compare_hive and compare_with_original (`writing._read_query`), since inherited Hive
  often starts with them and ticket 07's notebook compares the Hive exactly as given; a second
  query, or an INSERT and a SELECT, is still refused ("holds 2 statements besides its SET
  lines"). Both docstrings say so; tested for each.

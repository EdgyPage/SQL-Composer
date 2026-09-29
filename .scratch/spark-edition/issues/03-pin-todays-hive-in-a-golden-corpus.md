# Pin today's Hive, reprs and lineage in a golden corpus

Type: task
Status: resolved
Blocked by: 01

## Question

Tickets 10-13 move SQL Composer's leaves off sqlglot trees and must keep every string it writes
byte-identical. Today nothing pins all of it: doctests normalise whitespace, the gallery check runs
only at the pin, and DESCRIBE/SHOW PARTITIONS text and lineage order are barely asserted. Pin it
first.

- `tools/hive_corpus.py` renders a corpus, reusing `tools/example_gallery.py`'s collectors (the
  docstring examples, the Statement scripts and the example setting at `:111-124`).
- `tests/hive_corpus_cases.py` adds the edge cases: 80/81-character line-width pairs for IN,
  AND/OR in WHERE/HAVING/ON, CASE, function arguments and windows; nested brackets; CTE chains
  one to three deep; INSERT OVERWRITE and INSERT INTO with and without CTEs; every create_table
  type form; DROP; DESCRIBE and SHOW PARTITIONS, including a reserved name such as `ops.order`;
  reserved, digit-first and spaced column names; compact date_format partitions; last_n_days on a
  timestamp column; `any_of` with three branches; arithmetic brackets; and a seeded generator of
  about 200 Statements built only through public names.
- For each case, under a stable id, write to `tests/hive_corpus/sql_composer.txt`: `to_hive`,
  the repr of every output and condition, `readable`, the DESCRIBE/SHOW PARTITIONS text from a
  recording send, and the lineage Markdown twin without its "Made by" line.
- `tests/test_hive_corpus.py` asserts the committed file equals a fresh render (read with
  `read_text`, so a CRLF checkout passes), and skips below the sqlglot pin with its reason.
- Add BEL, FF, VT, BS, NUL and SUB to `tests/escaping_cases.py`, pinned to today's text.

No Toolbox file changes.

## Done when

The golden is committed, rendered from today's code (the code `main` holds as 955dafd). The
Definition of done in `CLAUDE.md` holds; pytest passes at sqlglot 30.19.0, and at 25.24.2 with
the golden skipped and its reason shown.

## Answer

The golden corpus is in place: `tools/hive_corpus.py` writes `tests/hive_corpus/sql_composer.txt`,
377 cases under stable ids, each pinning what a user sees through four public seams, and
`tests/test_hive_corpus.py` fails at the sqlglot pin while the committed file differs from what
the Toolbox writes. A test change of one word (backticking `status`) changes 3,500 of its lines.
`tests/escaping_cases.py` pins six more control characters. No Toolbox file changed; pytest
passes at sqlglot 30.19.0 (1,095 tests) and at 25.24.2 (1,037, with the golden skipped and its
reason shown). The code review is answered below, and neither commit touched a watched path, so
no drift review was due.

## Comments

**The seams (the user's choice, 2026-09-29).** The golden pins four public seams per case:
`to_hive`, the repr of every output and condition, the commands the warehouse helpers send
through a recording send, and `export_lineage`'s Markdown without its dated line. The internal
`tables.readable` is not pinned directly; its text shows in the lineage Markdown's formulas.

**Build decisions.**

- `tools/hive_corpus.py` reuses `tools/example_gallery.py`'s docstring and Worked-example
  collectors, `example_setting` (today 2026-09-25, a temporary folder) and `run_step`. The
  cases are 25 docstring examples, 39 Worked-example functions (careless with its opt-out too),
  106 edge cases, 200 generated Statements and 7 tables' warehouse commands: 377 in all, about
  1.1 MB, rendered in about 8.5 s.
- The edge cases and the generator live in `tests/hive_corpus_cases.py` and build only through
  public names. Each generated case has a seed of its own, so adding one never shifts another.
  The line-width pairs were measured once on sqlglot 30.19.0 and are written in as numbers, so
  the cases never adjust themselves to the printer.
- A Toolbox refusal is written in full; it is told apart by its four-part message. Any other
  error from `to_hive` or `export_lineage` is written by its type alone and marked "not a Toolbox
  refusal"; an error while building a case fails the run.
- The tool reads a Statement's private parts only to find what to repr; everything written comes
  through public names. If tickets 12-13 rename those parts, the tool fails loudly.
- The test skips, and the tool refuses to write, unless sqlglot is exactly the pin, read from
  `requirements-dev.txt`.
- `tests/escaping_cases.py` gains BEL, FF, VT, backspace, NUL and SUB, pinned to today's text.

**Findings for later tickets.**

- **The golden holds only at the pin.** On sqlglot 25.24.2, inside the supported range, five
  cases differ: `ROW_NUMBER() OVER (...)` is written on one line; a `struct<a:int,b:string>`
  column is written `STRUCT<a INT, b STRING>`, without the colon Hive needs; `date_format` gains
  `CAST(... AS TIMESTAMP)`; and `datediff` gains `TO_DATE(...)`. Ticket 06 of v2 found the
  output identical across the range; these shapes weren't in its probe. For tickets 04, 12 and 25.
- **`create_table` lets a bad type through to a crash.** `bigint unsigned` passes the type check
  but `to_hive` then stops with sqlglot's raw `ParseError`, not a four-part message; `json`,
  `uuid` and `interval` pass and are written as types Hive doesn't have. For ticket 25's strict
  types.
- **sqlglot changes a `hive_function` pattern's meaning.** `hive_function("date_format", dt,
  "YYYY-MM")` is written with `'yyyy-MM'`; in Hive, `YYYY` is the week-based year. For ticket 25
  and the declared `hive_function` difference.
- **Control characters.** sqlglot writes BEL, FF, VT and backspace as `\a`, `\f`, `\v`, `\b`, and
  lets NUL and SUB into the text raw; it reads all six back itself. For ticket 09.
- **`DESCRIBE` and `SHOW PARTITIONS` don't backtick a reserved table name.** For `ops.order` the
  warehouse helpers send `DESCRIBE ops.order` and `SHOW PARTITIONS ops.order`, while
  `create_table` and `drop_table` write ``ops.`order` ``. Hive very likely refuses the bare word,
  so `write_table_reference`, `check_table_reference` and `check_key` would fail on such a
  table. For ticket 09 (as a 2.1 fix) or ticket 25's backticks.

**Code review (2026-09-29), `45552c5...76ca4cb`.**

- *Standards:*
  - Fixed: "edition", which the glossary doesn't have yet, is gone from the test and the
    escaping cases; "chain" (on Clause function's _Avoid_ list) and `level` no longer name a
    Derived table's depth (the ids are now `edge:derived:depth_1..3`); the helpers and markers
    have names that say what they are (`_opted_out`, `_building`, `CASE_MARK`, `PART_MARK`,
    `REFUSAL_TYPES`, `refusal_or_raise`); the golden labels each warehouse helper by its public
    name; the ON lines are labelled by the read's position, not by the Toolbox's private call
    text; the unused `blocks_by_id` is gone; the tool refuses to write off the pin, as
    `tools/example_gallery.py` does, puts the repo on `sys.path` itself, and the test reads the
    pin and the golden's path from it.
  - Answered, not changed: "case" is test vocabulary here, as in `STRING_CASES`, not a name for
    a Statement or Worked example. The tool reads a Statement's private parts because the
    ticket allows no Toolbox change; only what they hold is written, through repr. The repeated
    `SELECT job_id, count_rows() ... GROUP_BY job_id` shape stays, as standards.md prefers
    plain repetition. `_listed`'s one-or-a-list check stays, as by_day returns a list.
- *Spec:*
  - Fixed: OR width pairs for HAVING (43/44) and ON (8/9); create_table cases for `real`,
    `double precision`, an untyped column, a table with no Date partition, and each edge
    table, backticked names included; every create_table case names its table `mart.typed`, so
    adding a type changes no other case; the recording send lists its newest day in the table's
    date_format, so the compact table's `check_key` pins the SELECT it sends instead of a
    refusal only the fake warehouse caused; the missed finding above.
  - Answered, not changed: the extra cases (hive_function, reads, careless opt-outs, the
    select-list width pair) are kept; each is an edge case in the ticket's sense, and two of
    them surfaced the findings above.

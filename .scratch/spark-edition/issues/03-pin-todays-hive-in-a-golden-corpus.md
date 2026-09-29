# Pin today's Hive, reprs and lineage in a golden corpus

Type: task
Status: open
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

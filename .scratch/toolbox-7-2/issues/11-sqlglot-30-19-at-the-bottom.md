# sqlglot 30.19.0 at the bottom of the range

Type: task
Status: in progress
Blocked by: 10
Size: M

## Question

The user (2026-10-26): "We can drop testing against the lower versions of sqlglot", then:
"Raise the supported sqlglot floor to 30.19.0: drop CI's 25.24.2 job, remove the code that only
older sqlglot needed, and update requirements, README and CHANGES. Do it as a 7.2 ticket with
the usual reviews."

The range was 25.24.2 up to (not including) 31, with the Example database needing 30.19.0.
30.19.0 is where the Example database already starts, so from 7.2 the whole Toolbox does.

## Done when

- `engine.py`'s range starts at 30.19.0: the import refuses an older sqlglot, saying so, and
  `_EXECUTOR_NEEDS`, the Example database's own floor, is gone, with what checked it.
- Each piece that only an older sqlglot needed is gone, each checked first on 30.19.0 and
  30.23.0 (a scratch venv at 30.19.0, as CI runs only the pin):
  - finding a piece's line by its words, and `hive_tokens`, as 30.19.0 notes every word's place;
  - ROLLUP (a, b) held beside GROUP BY's columns;
  - the comma before GROUPING SETS, DATE_SUB's brackets, the struct-colon refusal;
  - `from`/`with` beside `from_`/`with_`, and DROP's `this` beside `tables`;
  - the `needs_example_database` marker and the skip it gave, since the Example database now
    runs wherever the Toolbox imports.
- What 30.19.0 still needs stays, saying so: the multi-INSERT fallback, as 30.19.0 can't read
  FROM ... INSERT ... INSERT.
- CI runs one job, at the pin; `requirements-dev.txt`, the README template, the offline audit,
  CLAUDE.md and CHANGES.md's 7.2 say 30.19.0 up to (not including) 31.
- The suite passes on 30.23.0 and, once, on 30.19.0.
- CLAUDE.md's Definition of done, the beginner reader included (the import's refusal and the
  README change).

## Answer

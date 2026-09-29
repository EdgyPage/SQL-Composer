# Split the Example database into a shared send and `sql_composer/engine.py`

Type: task
Status: resolved
Blocked by: 03, 08

## Question

The Example database's data and its DESCRIBE/SHOW PARTITIONS answers are neutral; only running a
SELECT needs sqlglot. Separate the two, with every message byte-identical.

New `sql_composer/engine.py`, declaring TOOLBOX_VERSION, with no `>>>` examples:

- `check_library()` takes over `sql_composer/__init__.py:164-234` word for word. Its constants
  become `_LIBRARY_LOWEST`, `_LIBRARY_BELOW` and `_LIBRARY_NEWEST_TESTED`, and the pin and CI
  tests read them there.
- `run_query(text, tables) -> (columns, rows)` takes over the executor code
  (`sql_composer/example_database.py:157-241` and `:270-282`), importing sqlglot only inside
  functions.

`__init__.py` calls `engine.check_library()` right after `_check_files()`. `tests/conftest.py`'s
`example_database_cannot_run()` asks the Edition's `engine.py` instead of importing sqlglot
itself (ticket 07's review), so ticket 16 can block sqlglot in the Spark run.
`example_database.py` stops importing sqlglot and gains three shared text rules:

- a query is answered only when its first word is SELECT or WITH and no line starts with INSERT,
  CREATE, DROP, ALTER, TRUNCATE or LOAD; anything else "can't be written to";
- a query sorts itself when it has an ORDER BY outside every `OVER (...)`;
- when it doesn't, the rows are sorted by every column, None first, so both Editions show the
  same rows in the same order.

Update `tests/test_example_database.py:107-108`, regenerate `examples.html`, and add a CHANGES 2.1
line about the fixed row order.

## Done when

The Definition of done in `CLAUDE.md` holds; pytest is green at both ends; every import-stop
message and doctest output is unchanged; a test proves `_sorts_itself(to_hive(s)) ==
bool(s._order_by)` over the corpus; `WITH ... INSERT` text is refused as "can't be written to";
the golden is byte-identical; and the gallery's diff is row order only, reviewed.

## Answer

`sql_composer/engine.py` holds what SQL Composer runs on:

- `check_installed()`, which `__init__.py` calls right after `_check_files()`. It is the old sqlglot
  check, moved word for word, with its constants now `_LOWEST`, `_BELOW` and `_NEWEST_TESTED`.
- `run_query(text, tables) -> (columns, rows)`, the executor code. It imports sqlglot only inside
  its functions.
- `example_database_cannot_run()`, which `tests/conftest.py` now asks instead of importing sqlglot
  itself.

Every stop message and doctest output is unchanged.

`example_database.py` no longer imports sqlglot. It gains three shared text rules:

- **Only a query is answered.** Its command, the first word or the first after WITH's Derived
  tables, must be SELECT, and no second command may follow a `;`. Anything else is refused as
  "can't be written to".
- **A query sorts itself** only with an ORDER BY outside every bracket.
- **Otherwise the rows are sorted** by every column, None first.

A test proves `_sorts_itself(to_hive(s)) == bool(s._order_by)` over more than 150 corpus Statements.
The golden is byte-identical. The gallery's diff was reviewed as row order in six tables plus the
docstring's new sentence. CHANGES has a 2.1 line for the fixed row order.

## Comments

**Code review (2026-09-29), `4dbc93f` and `8499a79`.**

- *Standards:*
  - **Fixed:**
    - No name says "library", which the glossary keeps out of the Toolbox. The check is
      `check_installed()`, its constants are `_LOWEST`, `_BELOW` and `_NEWEST_TESTED`, and the
      behaviour check is `_sqlglot_behaviour` again.
    - The `__init__.py` comment says what `engine.py` checks.
    - The executor's version test reuses `_numbers`, and its messages write 30.19.0 from
      `_EXECUTOR_NEEDS`.
    - The sorting test's name says "every bracket".
  - **Answered, not changed:**
    - `run_query` still receives the Example database's `(table, rows)` pairs and reads `_columns`
      for its schema. The Spark engine (ticket 19) needs the same pairs to build its views, and
      `ops` is the one database both engines serve. Ticket 19 revisits this if its shape differs.
    - `run_query` keeps the name the ticket gave it. It is private to the Edition, beside a public
      `run` and a user's `send`.
- *Spec:*
  - **Fixed:** the query rule is stricter than the ticket's "no line starts with INSERT...". The
    review found four gaps in that rule:
    - a one-line `WITH x AS (...) INSERT INTO ...` was answered with an empty DataFrame;
    - `SELECT 1; DROP TABLE ...` reached the executor;
    - a query after a `-- comment` line was refused;
    - a double-quoted string could hide or fake an ORDER BY.

    `_outside_brackets` now blanks comments, every quoted text (single, double, backticks) and
    everything inside brackets. `_is_query` asks that the command be SELECT. A test covers each
    case.

    The drift review of `a9d9730` found two more gaps (D25, D26), both fixed:
    - an alias written without AS right after a bracket, as in `COUNT(*) load`, was taken for a
      command;
    - a `--` comment after code on the same line was left in.
  - **For ticket 14:** the shared `example_database.py` docstring still names sqlglot's executor and
    30.19.0, which `editions.swap()` refuses. The neutral wording belongs with the other claims.

**Beginner reader (2026-09-29):**
[reports/10-beginner-reader.md](../reports/10-beginner-reader.md). Its three costliest stops were
answered:

- The write refusal's fix sent a plain string to `to_hive`, which refuses text. It now says
  `to_hive(drop_table(t))`, and that `to_hive` takes what `create_table`, `drop_table` or
  `statement(...)` builds.
- "Sorted by every column" now says the first column comes first, then the second, with None
  first.
- The docstring and CHANGES now say that at work rows come back in no fixed order, and to sort in
  pandas when the order matters. This also answers stop 5, where a bare ORDER_BY is refused
  without a LIMIT.

Both texts now say "Statement" and drop "every run" (stops 4 and 6). Stop 7, sqlglot named in the
docstring, is ticket 14's.

# Split the Example database into a shared send and `sql_composer/engine.py`

Type: task
Status: claimed
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

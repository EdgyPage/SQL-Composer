# Put every sqlglot-only step behind `sql_composer/writing.py`

Type: task
Status: resolved
Blocked by: 10

## Question

Before the leaves change, gather every call that only sqlglot can make into one file whose
interface both Editions will share (a repo test holds the same names and parameters in both, from
ticket 15):

- `hive_text(node, pretty=False)`, and `sql_text` for sqlglot trees (today `tables.hive_text`,
  the only `.sql()` call, `sql_composer/tables.py:72-74`);
- `read_back(text)`, sqlglot's parse-back. `running.py` keeps the comparison and the one
  product-neutral refusal from `sql_composer/running.py:225-233`, so the message isn't copied into
  two hand-written files;
- `read_back_function(name, args, call)`: returns the aggregate flag, or raises the "don't fit"
  TypeError moved word for word from `sql_composer/calculations.py:362-370`;
- `hive_type(text)`, from `sql_composer/tables.py:1098-1108`;
- `describe_text(name)` and `show_partitions_text(name)`, from `tables.py:707` and `:729-731`.

`_set_part` and the DROP `tables`/`this` switch (sqlglot 30 renamed both) move in too. The Example
database and `engine.py` use `sql_text`. `writing.py` declares TOOLBOX_VERSION and has no `>>>`
examples.

Tests: the single-writer rule in `tests/sqlglot_edition/test_sqlglot_escaping_toolbox.py`
(`test_sql_text_is_written_in_exactly_one_function`) becomes `("writing.py", "sql_text")`;
`tests/test_statements.py::test_to_hive_stops_on_hive_that_doesnt_read_back_the_same` is
replaced by a test that patches `writing.read_back`.

## Done when

The Definition of done in `CLAUDE.md` holds; no shared module names the hive dialect, `ErrorLevel`
or `parse_one`; the golden and `examples.html` are byte-identical; pytest is green at both ends.

## Answer

`sql_composer/writing.py` holds every step only sqlglot can take (`9d5f627`):

- `sql_text`, the one `.sql()` call, and `hive_text` for a Statement's parts;
- `read_back`, the parse-back to_hive's self-check compares (running.py keeps the comparison and
  its refusal);
- `read_back_function` for hive_function, with the "don't fit" TypeError word for word;
- `hive_type`, `describe_text` and `show_partitions_text`;
- `set_part` and `drop`, sqlglot 30's renames;
- `hive_call`, which the date calls needed so that no shared file names the dialect.

A test holds that no shared file passes `dialect=` or `read=`, names `parse_one` or `ErrorLevel`,
or holds the string "hive". The golden and `examples.html` are byte-identical, and pytest is green
at both ends.

## Comments

**Code review (2026-09-29), `9d5f627`.**

- *Spec:*
  - **Fixed:**
    - The dialect test also catches "hive" passed positionally.
    - engine.py's behaviour check now writes through `sql_text`, which raises where `.sql()` only
      warned. A sqlglot that can't write a checked piece now counts as behaving differently, and
      gets the four-part stop instead of a raw exception.
  - **Answered, not changed:**
    - `hive_call` wasn't on the ticket's list. Ticket 12 replaces the date calls with `Call`
      nodes, and writing.py's replay then builds them, so `hive_call` goes before ticket 15 fixes
      the interface.
    - `read_back_function` returns the read-back tree, not the aggregate flag, since a Column
      still holds sqlglot's tree until ticket 12. With `HiveFunction(name, args, aggregate)` it
      returns the flag, and its parameter becomes `args`, as the ticket names it.
- *Standards:*
  - **Answered, not changed:**
    - `hive_text` only passes through to `sql_text` for now. Ticket 12 makes it turn the
      Toolbox's own tree into sqlglot's first.
    - `drop` builds a tree and drops nothing, and `set_part` and `drop` join the shared
      interface for now. Ticket 13 builds DROP and every Statement part as the Toolbox's own
      nodes, and both go.
    - `describe_text` and `show_partitions_text` import `hive_table` from tables.py inside the
      function. Ticket 12 moves the naming rule into trees.py, which writing.py imports, and the
      back-reach goes.
    - running.py calls `writing.read_back` through the module, so a test can stand in for it in
      either Edition. The other files import names.
    - `read_back_function`'s docstring says it gives "why its arguments don't fit". Ticket 12
      rewrites it with the new return value, and it will name the TypeError.

**Beginner reader (2026-09-29):**
[reports/11-beginner-reader.md](../reports/11-beginner-reader.md). Answered:

- `tables.py` names `literal(...)` as the one place a Python value enters a Statement, with no
  "them".
- `writing.py` says it writes a Statement as Hive with the sqlglot package, explains "sqlglot
  tree", and says each Edition writes Hive its own way behind the same function names. That no
  longer claims the other Edition's file uses sqlglot.
- `read_back_function` says it raises TypeError, and `read_back` says to_hive compares the two
  texts. "Hive's own functions" is now "Hive's built-in functions", and "sqlglot 30" is now
  "sqlglot version 30".

Stops 3 (`hive_text` beside `sql_text`) and 8 (`drop` beside `drop_table`) go with tickets 12 and
13, which change `hive_text` and remove `drop`.

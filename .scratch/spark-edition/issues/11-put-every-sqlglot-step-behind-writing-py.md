# Put every sqlglot-only step behind `sql_composer/writing.py`

Type: task
Status: open
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

Tests: `tests/test_escaping_toolbox.py`'s single-writer rule becomes
`("writing.py", "sql_text")`; `tests/test_statements.py:480-484` is replaced by a test that
patches `writing.read_back`.

## Done when

The Definition of done in `CLAUDE.md` holds; no shared module names the hive dialect, `ErrorLevel`
or `parse_one`; the golden and `examples.html` are byte-identical; pytest is green at both ends.

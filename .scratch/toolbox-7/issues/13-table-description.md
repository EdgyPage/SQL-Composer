# A Table description: reading DESCRIBE once, and printing it for stand-ins

Type: task
Status: claimed
Blocked by: 11
Size: M

## Question

From the architecture review of 2026-10-22 (candidate 4); the user: "Do candidates 3 and 4 and 5
on the architecture task". Toolbox 7.1, which isn't exported yet.

`sqlglot_composer/tables.py` reads what DESCRIBE and DESCRIBE FORMATTED print (`_ask`,
`Described`, `_describe`, `_read_detail`, `_cell`, `_stored_as`, `_listed_names`, and
`_buckets_problems`, which parses "num buckets" itself), but hands callers a bag keyed by
Hive's own lower-case labels. So "is it managed?" is worked out twice (`tables.py` and
`admin.py`, `details.get("table type") or details.get("type")`), and `admin.py` imports the
private `_describe` and `Described`. The reverse, "a Table reference as DESCRIBE prints it", is
written by hand at least six times: `example_database._describe`, `tools/hive_corpus.py`
`describe_frame`, `tests/hive_corpus_cases.py` `warehouse` (with FORMATTED),
`tests/test_saved_table_storage.py` `formatted` (Hive and one-line dialects),
`tests/test_tables.py` `answering` and its frames, `tests/test_warehouse_answers.py`
`answering`; and `tools/how_to_page.py`, `tests/test_admin_module.py` and
`tools/hive_corpus.Recording` rebuild DESCRIBE too.

## Done when

- One private module of the Toolbox (listed in `tools/toolbox_registry.py`) reads DESCRIBE and
  DESCRIBE FORMATTED, in each dialect the Toolbox reads today, into a description that
  answers in the Toolbox's words: its columns and types, partition columns, location, whether
  it is managed, file format, buckets and properties. No caller reads a Hive label.
  check_table_reference, check_key's and write_table_reference's reads, add_columns and
  move_to_own_folder / check_the_copy use it; admin imports no private name from tables.
- The same module prints a Table reference as DESCRIBE or DESCRIBE FORMATTED would, in each
  dialect, so that reading what it prints gives the description back: a round-trip test per
  dialect.
- A stand-in warehouse built from any Table references, answering DESCRIBE, DESCRIBE FORMATTED
  and SHOW PARTITIONS from them, and keeping what it is sent: the Example database's
  answers to DESCRIBE come from it, and the test fakes and tools listed above become one-line
  setups of it, unless a fake needs a malformed answer on purpose (then it says so).
- What a user sees doesn't change: the same verdicts, refusals and Example database answers.
- No public name added.

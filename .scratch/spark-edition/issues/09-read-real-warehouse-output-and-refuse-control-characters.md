# Read real warehouse output, and refuse BEL, FF and VT in a value (2.1 fixes)

Type: task
Status: claimed
Blocked by: 03

## Question

Four bugs affect the sqlglot edition today, and both Editions once the files are shared. They are
2.1 fixes: each gets a CHANGES line under 2.1, and `main` may be re-exported as 2.1 with them.

- `_newest_partition_value` (`sql_composer/tables.py:727-738`) reads partition values as the
  warehouse lists them, which escapes them (`dt=2026%2F09%2F24`). Unescape each value, so
  write_table_reference detects `%Y/%m/%d`.
- The same function takes `__HIVE_DEFAULT_PARTITION__` (the NULL day) for the newest day. Skip
  it, so check_key doesn't read the NULL day.
- `_describe` (`sql_composer/tables.py:705-724`) opens the partition section on
  `# Partition Information` but never closes it, and Spark 4.0 can print more sections after it.
  Close the section at any other `#` header, so a column with a DEFAULT isn't taken for a
  partition column.
- sqlglot writes BEL, FF and VT inside a string as `\a`, `\f` and `\v`, which Hive and Spark
  read as the letters a, f and v, so the value changes silently (verified on 30.19.0). The user
  chose to refuse such a value: a new Guard in `refusals.py`, fired from `tables.literal`, with
  its refuses and opt-out tests (or "No opt-out" in its docstring), a four-part message, and the
  cases pinned by ticket 3 moved to "refused".

Test the parsing with stand-in sends shaped like Hive's output and like Spark's (the design panel
checked Spark's DescribeTableCommand and ShowPartitionsCommand in 3.5.3 and 4.0.1).

## Done when

The Definition of done in `CLAUDE.md` holds (the beginner reader reads the new refusal), pytest is
green at both ends, and the golden changes only in the refused cases.

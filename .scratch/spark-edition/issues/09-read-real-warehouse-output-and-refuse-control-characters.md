# Read real warehouse output, and refuse BEL, FF and VT in a value (2.1 fixes)

Type: task
Status: resolved
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

## Answer

Four 2.1 fixes, each with its own CHANGES line (`e828629`, `f20da09`, `719aa88`, `951f03b`):

- **Escaped days.** SHOW PARTITIONS values are unescaped, so `2026%2F09%2F24` is read as
  2026/09/24 and `write_table_reference` finds `%Y/%m/%d`.
- **Rows with no day.** `__HIVE_DEFAULT_PARTITION__` is never taken for the newest day.
- **DESCRIBE.** DESCRIBE is read section by section: only a partition section names partition
  columns, so Spark's "# Column Default Values" isn't taken for more of them. Spark's "#
  Partitioning" row, as in a Delta or Iceberg table, is read as the column it names.
- **Control characters.** A value holding a bell, a form feed or a vertical tab is refused by a
  new Guard with no opt-out. It fires in `literal()`, so every way a string value enters a
  Statement is covered. A `date_format` holding one gets its own message.

  The message says what the character is (what `\a`, `\f` or `\v` gives in a Python string),
  which letter Hive and Spark would read instead, and, as its fix, to put r before a Windows
  path's quotes or double the backslash. Any other unprinted character in a `date_format`, such
  as a tab, keeps the general message.

The golden changed in one case only: DESCRIBE and SHOW PARTITIONS of `ops.order` now backtick the
name. That goes beyond "only the refused cases", since the golden holds no refused case. It was
ticket 03's finding, sent here as a 2.1 fix, and `create_table` and `drop_table` already
backticked such a name.

## Comments

**Code review (2026-09-29), `e828629`.** Every finding was fixed in `f20da09`:

- *Standards:*
  - The CHANGES lines use Partition only for a slice of a table, and say "rows with no day", not
    "NULL day".
  - The Guard's fix is code to paste, and its reason names the letter.
  - `literal()` finds the character and the Guard only says why, like the other Guards.
  - DESCRIBE's header rows are named constants.
- *Spec:*
  - A `date_format` holding a control character is refused. The review found it got past the
    Guard.
  - The tests stand in for Hive's DESCRIBE as well as Spark's, include a multi-column listing with
    `%3D`, `%25` and `%5C`, and cover every way a string value enters a Statement.
  - Each fix has its own CHANGES line.
  - The stale comment in `tests/escaping_cases.py` is gone.

**Beginner reader (2026-09-29):**
[reports/09-beginner-reader.md](../reports/09-beginner-reader.md). Its three costliest stops were
answered in `719aa88`:

- The old fix (take the character out) would quietly change a Windows path. The fix is now r
  before the quotes, or a doubled backslash.
- CHANGES now says what 2.0 got wrong and what to redo: put back a Date partition 2.0 said to
  remove, and run `check_key` again.
- The CHANGES line on Spark's DESCRIBE says what the reader would have seen.

The drift review of `719aa88` then found the date_format message firing for a tab and two lost
notes (D22-D24), fixed in `951f03b`.

The docstring stops C1-C4 predate the ticket. C1 and C2 were answered by saying what each helper
reads from SHOW PARTITIONS. C3 and C4 are left as they were.

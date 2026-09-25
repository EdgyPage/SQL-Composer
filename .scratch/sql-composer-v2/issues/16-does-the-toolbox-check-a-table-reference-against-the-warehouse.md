# Does the Toolbox check a Table reference against the warehouse?

Type: grilling
Status: resolved
Blocked by: 11

## Question

A Table reference is generated once from `DESCRIBE` and then edited by hand, and it is never
regenerated. So a table that gains, loses, renames or retypes a column later goes unnoticed until a
query fails on the server, or until it silently doesn't fail. Saved tables make this worse:
`create_table` uses `IF NOT EXISTS`, so an existing table with different columns is left alone, and
`INSERT_OVERWRITE` lines columns up against the Table reference, not the real table.

For a tool with a life of about seven months, decide:

- whether a check is worth having at all, or a docstring warning is enough;
- if it is, what it compares (names, types, order, partition columns), whether it runs only when
  called (`check_table_reference(t, send=...)`) or at some other moment, and what it does with a
  difference: report it, or refuse;
- whether a Saved table gets a stricter check before its first write.

## Answer

**An on-demand check that reports, and a strict `create_table`.** Of the ways the warehouse can
move under a Table reference, three are silent, which is why a check earns its place:

| warehouse change | what happens |
| --- | --- |
| column dropped or renamed | loud: Hive's `Invalid column reference` |
| column added | harmless: the Table reference just doesn't offer it |
| column retyped | **silent**: the Guards check values against the old type, Hive casts quietly |
| Date partition changes format | **silent**: the both-ends date bound matches no days, or the wrong ones |
| Saved table with a different column count | loud: Hive's `column number/types are different` |
| Saved table with the same count, different order or names | **silent**: `INSERT OVERWRITE` fills by position |

**`check_table_reference(t, send=...)`**, beside `check_key` in `tables.py`:

- **runs only when called.** Nothing runs it automatically, not even before a write: an extra
  metadata call on every `run` (and every day of a `by_day` backfill) would make "is my table
  still the same?" happen without being asked.
- **sends `DESCRIBE` and `SHOW PARTITIONS`** through the user's own `send`, the same metadata reads
  `write_table_reference` makes, and reuses its parsing.
- **reports and never refuses.** It returns a verdict that prints readably, like `check_key`'s:
  "`ops.job_runs` matches its Table reference", or a list of **problems** and **notes**, each with
  the exact line to change in the Table reference file. It never raises and never edits the file,
  which stays the user's and is never regenerated.
- **says "differs from its Table reference", never "drift"**, a word `dev` already uses for its
  drift reviewer.

What it compares:

- **Problems:** a Table reference column the table lacks; a type that differs, compared after
  normalising case and spaces (`DECIMAL(10, 2)` equals `decimal(10,2)`), skipping columns typed
  `None`; a Date partition that is no longer a partition column, or whose newest value from
  `SHOW PARTITIONS` no longer parses with `date_format`.
- **Notes:** a column the table has but the Table reference lacks ("add it if you want it");
  partition columns added or gone; column order, worded "matters only if a Statement writes to
  this table", since the Toolbox can't tell a Saved table's Table reference from any other.
- **Not compared:** comments, `key` (that's `check_key`), `does_not_add_up` (Hive knows nothing
  of it).

**`create_table(t)` is strict by default.** It emits a plain `CREATE TABLE`, which Hive refuses
when the table exists, so editing a Saved table's Table reference and re-running `create_table` no
longer looks as if it updated the table. `create_table(t, may_exist=True)` restores
`IF NOT EXISTS`. The Toolbox only builds the string and never sees the server's reply, so the
docstring explains Hive's `AlreadyExistsException` and what to do: drop the table on the server
first, or check it with `check_table_reference`.

**No stricter check before a Saved table's first write.** The strict `create_table` means a first
write follows a table made exactly as its Table reference says, or a loud failure. The docstrings of
`INSERT_OVERWRITE` and `create_table` say: after editing a Saved table's Table reference, run
`check_table_reference`.

Handed on:

- **"Build the Toolbox core"** builds `check_table_reference` (a 61st public name) and the strict
  `create_table`, and has `example_database.send` answer `DESCRIBE` and `SHOW PARTITIONS` from its
  own Table references and rows, so `write_table_reference`, `check_key` and
  `check_table_reference` can be doctested and practised in the sandbox.
- **"How do pieces combine across Levels - CTE, subquery, or saved table?"** Its `create_table`
  changes from `IF NOT EXISTS` to strict (see the note there).

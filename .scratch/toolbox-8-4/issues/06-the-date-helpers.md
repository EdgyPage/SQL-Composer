# today, latest_partition and hive_date

Type: task
Status: open
Blocked by: 05
Size: M

## Question

The user wants helpers for writing a Run value's function: "a date lookup function converted
to usable hive formatted text. a helper function inside the toolbox would be nice for that.
utc for default time zone, give options to adjust." (map, Q13).

## Done when

- `today(utc_offset_hours=0)` gives today's date in UTC, or at the offset given; public, in
  `public.py`'s `__all__`. `last_n_days` follows it, now UTC. No library is added.
- `latest_partition(column, query)` sends `SHOW PARTITIONS <table>` through the user's `query`
  and gives the newest value of that partition column: a date when it reads as one, else the
  value as text or a number. A column that isn't a partition column is refused before
  anything is sent; a table with no Partitions is refused naming it.
- `hive_date(day)` gives `'2026-10-31'` for a date, refusing anything else.
- Each has a docstring example run as a test, `latest_partition` on the Example database.
- `tools/toolbox_registry.py` and the offline policy hold: nothing reaches past `query`.

## Answer
Built 2026-11-05.

- **`today(utc_offset_hours=0)`**, now public, in `conditions.py`: the date in UTC, or that
  many hours from it, refusing an offset that isn't a number between -24 and 24.
  `last_n_days` follows it, so it counts from UTC's today. No library added, so no zone names
  (map, Q13). The tests' fixed day takes the offset too.
- **`latest_partition(column, query)`**, in `script_tags.py`: sends `SHOW PARTITIONS
  <table>` through `describe.send_describe` (renamed from `_send_describe`, which
  `describe` already used for DESCRIBE), reads the column's value from each listed
  Partition, its `%XX` escapes undone, and gives the newest: a date when every value reads as
  one, a number when every value is digits, else the last as text. A column that isn't a
  partition column is refused before anything is sent; a table with none listed is refused.
- **`hive_date(day)`**: `'2026-10-31'`, a datetime with its time, refusing anything that
  isn't a date.
- Each has a docstring example run as a test; `latest_partition`'s on the Example database.
  Nothing reaches past `query`.
- **Tests**, `tests/test_run_values.py`: today's offsets and refusals, `latest_partition` on
  the Example database and on stand-in listings by a team, a batch number and an escaped
  region, its refusals, and `hive_date`.

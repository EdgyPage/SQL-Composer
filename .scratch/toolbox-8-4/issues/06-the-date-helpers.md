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

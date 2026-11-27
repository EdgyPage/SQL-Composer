# The Seed widened: a History table usable from its first day

Type: task
Status: open
Blocked by: 04
Size: L
Spec: [specs/05-the-seed-widened.md](../specs/05-the-seed-widened.md)

## Question

Today only a Conversion's table whose write reads itself gets a Seed. Every History table needs
one, limited to the past days that matter (round 1, Q8; round 2, Q2 to Q5; round 3, Q4 to Q8;
round 4, Q1; CONTEXT.md's Seed). The user: "I want to be able to have a historical table that
is usable from day one by loading in relevant data from a subset of all available partitions."

## Done when

- **Every History table has a Seed**; a Rebuilt table has none.
- **Its limit, `"seed": {"months": N}`**, in the decisions cell for a table or under
  `all_tables`, proposed as 1. N calendar months back from the newest Partition the source
  holds, both ends included; values keep their written form (`2026-11-27`, `20261127`) in the
  WHERE. The value, range and list forms stay for anything else.
- **The date partition is found from its values**: a partition column, from DESCRIBE's
  "# Partition Information", whose every value SHOW PARTITIONS lists reads as a date. None, or
  two, and nothing is proposed: the Seed's Decision stays open in the value, range and list
  forms. With `dt` and `hour`, the months limit `dt`, and every `hour` is loaded.
- **With an Original, the Seed copies from it** (`seed_copy`), whether or not the write reads
  itself.
- **With none** (`new_table`, or a query alone), it runs the write once for each past day,
  oldest first, as of that day: the day goes wherever the write reads today (`current_date`,
  or a Run value for today), so a write that targets yesterday runs as of the day after. Only
  the run's today changes, never the logic. Each run writes the one Partition folder a
  scheduled write writes.
- **A History table with no Partitions** (an append) is copied whole from its Original; with
  none, the months count back from today and the write runs as of each day.
- **A failed day doesn't stop it**: the Seed goes on, and its report lists each day not loaded
  with the warehouse's error, and each that wrote no rows as "no rows", its empty Partition
  kept.
- **It runs on its own**, first, in whichever step writes the table (convert's write step,
  `new_table`'s, promote's), whenever a History table holds no Partitions yet (no rows, for
  one with none). No cell sends it by hand, and a rerun never loads twice.
- **In prod** it copies from the Original; a History table with none copies from its dev
  table, within the same limit.
- **Tests**, on the Example database: a months limit from a newest Partition; `yyyy-MM-dd` and
  `yyyyMMdd` values; no date partition, so no proposal; `dt` with `hour`; a copy for a table
  that doesn't read itself; a write run as of each day with `date_sub(current_date, 1)`; a
  failed day and an empty one in the report; a rerun that loads nothing; prod from dev.
- The beginner reader runs, since the Seed's report and decisions change.

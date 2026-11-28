# Spec: The Seed widened, a History table usable from its first day

Status: ready-for-agent
Ticket: [05](../issues/05-the-seed-widened.md)

## Problem Statement

A History table's new copy, in dev or prod, holds only the days its own writes have added
since it was made, so for weeks it is too short for anything that reads it. Today the Toolbox
loads past rows, the Seed, only for a converted table whose write reads its own table. A daily
load that reads only source tables starts with one Partition, and its compare still passes, so
nothing tells the user the history is missing. A table made with `new_table` has no Original
to copy from at all. The user: "I want to be able to have a historical table that is usable
from day one by loading in relevant data from a subset of all available partitions", limited
by "the last month, two months, or four months, or some other single param a user could fill
in".

## Solution

Every History table has a Seed, which runs on its own before the table's first write and loads
its past days, limited by one number: `"seed": {"months": N}`, proposed as 1. A table with an
Original copies those days from it. A table without one runs its own write as of each past
day, so the folders it leaves are the ones its scheduled writes add to. A day that fails or
has no rows doesn't stop the Seed; its report lists each. In prod, a table without an Original
copies the days the user checked in dev.

## User Stories

1. As a user with a History table, I want its past days loaded before its first write, so that
   it's usable from its first day.
2. As a user, I want to say how far back with one number, `"seed": {"months": N}`, so that I
   don't write dates by hand.
3. As a user, I want the number proposed as 1, so that I usually accept it.
4. As a user, I want to give the number once under `all_tables`, so that a whole Batch takes
   one line.
5. As a user, I want the months counted back from the newest Partition the source holds, not
   today, so that a source that hasn't loaded today still gives me a full month.
6. As a user, I want calendar months with both ends included, so that "2 months" from
   2026-11-27 means 2026-09-27 to 2026-11-27.
7. As a user whose dates are written `20261127`, I want them kept that way in what is sent, so
   that the warehouse matches its own values.
8. As a user, I want the date partition found from its values, whatever it's called, so that
   my oddly named columns still work.
9. As a user whose table is partitioned by `dt` and `hour`, I want the months to limit `dt` and
   every `hour` loaded, so that whole days come in.
10. As a user whose table has no date partition, I want the Seed's Decision left open in the
    value, range and list forms, so that I say what to load.
11. As a user, I want the value, range and list forms kept, so that anything 8.4 allowed still
    works.
12. As a converter whose History table has an Original, I want its past days copied from it,
    even when the write doesn't read itself, so that a daily load has its history.
13. As a user whose History table has no Original, I want its write run once for each past day,
    oldest first, so that each day reads what its sources held.
14. As a user whose write computes its date in Hive, such as `date_sub(current_date, 1)`, I want
    each run done as of the right day, so that the day it writes is the day I asked for.
15. As a user, I want only the run's "today" changed, never my logic, so that the Seed writes
    exactly what my scheduled write would have.
16. As a user, I want each Seed run to write the same Partition folder my scheduled write
    writes, so that the table's files look the same whichever wrote them.
17. As a user whose source lacks some days, I want the Seed to carry on, so that I get every
    day that can be loaded.
18. As a user, I want the Seed's report to list each day not loaded with the warehouse's error,
    so that I know what's missing and why.
19. As a user, I want a day that wrote no rows listed as "no rows", its empty Partition kept, so
    that I tell "nothing there" from "failed".
20. As a user, I want the Seed to run on its own in the step that writes the table, so that I
    never send it by hand.
21. As a user, I want it to run only while the table holds no Partitions, so that running the
    step again never loads twice.
22. As a user with an unpartitioned History table, an append, I want it copied whole from its
    Original, or with none, the months counted back from today and its write run as of each
    day, so that it has history too.
23. As a user promoting a History table with an Original, I want prod's Seed copied from the
    Original, so that prod matches what dev was built from.
24. As a user promoting a History table with no Original, I want prod's Seed copied from my dev
    table, within the same limit, so that prod gets exactly the rows I checked.
25. As a user in a dry run, I want to see each Statement the Seed would send, so that I can
    read it first.
26. As a user running the Workflow through `project.run_workflow`, I want the same Seed, so that
    the runner and the notebooks agree.
27. As a user whose table was seeded before 8.10, I want its `seed()` and SEED kept, so that
    nothing I answered is lost.

## Implementation Decisions

- **The kind gates the Seed** (ticket 04): every History table has a Seed Decision; a Rebuilt
  table has none.
- **The months form** is a new limit beside the value, range and list forms, answered as
  `"seed": {"months": N}` under a table or `all_tables`, proposed as 1. When the Seed is
  built it becomes a range on the date partition, from N calendar months before the newest
  Partition the source holds up to that Partition, both ends included, each value written in
  the form SHOW PARTITIONS lists.
- **The date partition**: a partition column, as DESCRIBE's Partition Information lists it,
  whose every value SHOW PARTITIONS gives reads as a date (`yyyy-MM-dd` or `yyyyMMdd`), both
  read through the user's `query`. None, or more than one, and the months form isn't proposed.
  Other partition columns are loaded whole.
- **The source**, for counting back: the Original when there is one; with none, the newest
  Partition of the table the write reads its date from, and for an unpartitioned History table
  with no Original, today.
- **A Seed with an Original** copies, as today's seed copy does, now for every History table
  with one.
- **A Seed with none runs the write as of each day**, oldest first: the day is put wherever the
  write reads today, the Hive's current date or a Run value for today, so a write targeting
  yesterday runs as of the day after. Each run is the table's own write, unchanged but for its
  today, writing one Partition.
- **The Seed's report**, printed when it runs, lists each day loaded, each not loaded with the
  warehouse's error, and each that wrote no rows as "no rows"; it never stops on a day.
- **It runs on its own**, first, in the step that writes the table: convert's write step,
  `new_table`'s, and promote's, while the table holds no Partitions (no rows, for an
  unpartitioned one). The convert notebook's separate seed cell goes; the Workflows' notebooks
  are written again.
- **In prod**, a Seed copies from the Original; with none, from the dev table, within the same
  limit.
- Glossary: CONTEXT.md's Seed already holds the wider meaning.

## Testing Decisions

- A good test runs the Workflow and reads the History table's Partitions and rows back from the
  warehouse, and the Seed's report from what was printed.
- The seam is the Workflow journey, on its stand-in warehouse; no new warehouse ability is
  needed, since every Statement a Seed sends holds plain dates:
  - convert a one-Partition daily load that doesn't read itself; accept History and one
    month; the table holds the month's days from its Original;
  - `new_table` with a write targeting `date_sub(current_date, 1)`; its write run as of each
    day; each Partition holds that day's rows;
  - a source table missing some days and empty on one: the report lists each, and the Seed
    goes on;
  - the step run again sends no Seed;
  - promote a History table with no Original: prod's Partitions are dev's.
  Once through the notebooks, once through `project.run_workflow`.
- Smaller tests on the Example database: the months form's range from a newest Partition;
  `yyyy-MM-dd` and `yyyyMMdd`; no date partition, so no proposal; `dt` with `hour`; an
  unpartitioned History table.
- Prior art: the journeys' "promote a seeded table limiting its prod seed" test, and the seed
  limit tests of 8.4.

## Out of Scope

- Seeding a Rebuilt table.
- Seeding from a time-versioned snapshot of a source.
- Rewriting a write into one Statement over the whole range.
- A Warning for missing days (ticket 06).

## Further Notes

- The map's "Aggregate or historical" note and Settled rounds 1 to 4 hold every choice.
- The Seed's report and Decisions change, so the beginner reader runs.

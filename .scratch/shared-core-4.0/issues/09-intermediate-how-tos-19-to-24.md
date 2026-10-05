# Intermediate how tos 19 to 24

Type: task
Status: open
Blocked by: 08
Size: L

## Question

How-tos 19-24: a day written another way and a second partition; as-of lookups from a daily
snapshot; week and month rollups; incremental loads and late data; a layered pipeline; a
library of Building blocks.

## Done when

- Each runs as a doctest in both Editions; the beginner reader has run.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).

## Comments

- From ticket 05 (2026-10-05): `write_table_reference("ops.region_costs", ...)` writes
  `date_partition=None` with a TODO, since its first partition, region, holds no day (as
  architecture-review ticket 01 decided). Once dt is named, `check_table_reference` gives the
  `date_format="%Y%m%d",` line. How-to 19 should walk through exactly that, or this ticket may
  decide write_table_reference finds dt itself (a behaviour change: ask the user). The beginner
  reader also stopped at, in composer_core/tables.py: the "newest region ... isn't a day the
  Toolbox can bound; name it" TODO; the note "a Statement may bound too"; the verdict "matches"
  when no Date partition is named; and write_table_reference's docstring not saying what
  happens to a table partitioned first by something other than days.


# check_project warns while a History table lacks its Seed's days

Type: task
Status: resolved
Blocked by: 05
Size: S
Spec: [specs/06-check-project-warns-of-missing-days.md](../specs/06-check-project-warns-of-missing-days.md)

## Question

A Seed that couldn't load every day goes on (ticket 05); what it left out must stay visible
(round 2, Q5; round 3, Q6).

## Done when

- **`check_project` gives a Warning**, never a refusal, for each History table that lacks
  Partitions its Seed's limit named, or holds them empty: "mart.job_day_facts lacks 3 of the
  31 days its Seed loads: 2026-10-04, ...".
- A Rebuilt table, and a History table holding every day, give none.
- **Tests**: a History table missing days, one with an empty day, and one whole.
- The beginner reader runs, since a new Warning is a message a beginner reads.

## Answer

Built 2026-11-27.

- **`project.check(query=...)`**, a new keyword, None by default: without it check() reads
  nothing of the warehouse and says what it said before, so every Workflow's decision-step
  `project.check()` cell and its DECISIONS are unchanged. With it, `seeding.missing_days_lines`
  gives, after what blocks something and before the Lineage state, one Warning per History
  table short of its Seed's days: "Warning: mart_dev.x lacks 2 of the 14 days its Seed loads:
  2026-09-13 and 2026-09-20. That stops nothing, but what reads it finds no rows for those
  days until each is written." A day held with no rows is shown "2026-09-15 (no rows)"; past
  five the rest are counted ("... and 15 more").
- **Which tables**: each Table folder whose Table reference is answered History, partitioned,
  its SEED answered, and written at least once (admin/sent.csv): a table never written is
  passed over, since its Seed runs at its first write, and so is one holding no Partition yet.
- **Which days**, counted as the Seed counts them, from the same source
  (`seeding.source_to_copy`): for a Seed copied, each day its source (the Original, or in prod
  the dev copy's Original or the dev copy) holds that its SEED keeps, the months form counted
  back from the source's newest Partition, a value, range or list as seed_copy's WHERE keeps
  it (`_is_kept_by`); for one run as of each day, each day `_days_to_run` gives, every day of
  the range. Missing is a day of those with no row in a GROUP BY read of the table. A day its
  Original never held isn't one its copy could load, so it isn't named. A Seed whose days
  can't be told (no one column of dates, a write reading no today, a SEED or logic that stops)
  gives nothing.
- **A table whose Partitions your query can't read** is named once, under the Warnings: "Not
  checked for the days its Seed loads: X, as your query couldn't read its Partitions. Your
  query said: No connection: call connect(...) first."
- **admin/check_project.ipynb** now has a connect cell after the path (`from warehouse import
  connect, query` and CONNECT_LINES) and `project.check(query=query)`; its text cell says what
  the Warning is. The Example projects and `docs/main/example_projects.html` are written again.
- **Tests**: `tests/journeys/test_workflow_journeys.py`, after the Seed journeys: a converted
  daily table seeded from its Original, whole (no Warning), then two days dropped; an empty day
  (SHOW PARTITIONS listing a Partition with no rows); the value, range and list forms; a
  Rebuilt table; a query that can't read; and the new_table journey whose Seed ran as of each
  day, check_project run cell by cell naming 20 of 32 days, quiet once they are written.
  `tests/snapshot/known.txt` gained the 10 texts these make.
- **Also fixed, from ticket 05**: `seed_tables` added to `project.__all__` and to the decided
  names in `tests/repo/test_toolbox_checks.py` (two how-to quoting tests failed without it);
  the four breaks `tests/repo/test_standard.py` found: a dense comprehension each in
  `seeding.date_partitions` and `converting.day_on_column`, now loops, and two private names
  another file has too, seeding's `_first_line` (upgrades.py's) now `_error_first_line`, and
  converting's `_day_of` (workbook_pivot_hive.py's) now `_day_given_by`.
- **For ticket 08**: no Upgrade writes check_project.ipynb again (REWRITTEN_IN_8_0's note), so
  an upgraded Project keeps `project.check()` and gets no Warning; `to_8_10` may mark it.
  `admin/check_project.ipynb` is in `AWAITING_ITS_STEP` until it decides.
- **For ticket 07**: how-tos 08 and 34, and the README template's check step, could name the
  Warning; ticket 05's note that a Seed copied from the Original makes the compare of a seeded
  Partition pass whatever the write does still waits on a line there.
- **Texts a beginner sees, changed**: the missing-days Warning and the not-checked line;
  check()'s docstring and its new `query=`; check_project.ipynb's text cell and its cells;
  seeding.py's module docstring. The beginner reader hasn't run: this implementer spawns no
  agent.

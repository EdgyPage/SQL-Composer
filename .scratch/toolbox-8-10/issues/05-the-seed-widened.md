# The Seed widened: a History table usable from its first day

Type: task
Status: resolved
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

## Answer

Built 2026-11-27.

- **The Seed Decision**: `SEED = {...}` in the Table reference, now a Decision kind,
  `decisions.SEED_LIMIT`, answered as `"seed"` under a table or `all_tables`. convert and
  new_table write it beside KIND (`decisions.seed_block`) for every table not proposed Rebuilt:
  `SEED = {"months": 1}  # proposed: dt holds dates in mart.x`, made and marked `# proposed`
  as a Key from a query is, so it blocks nothing; with no column of dates found (none, two, or
  the Partitions unreadable), `SEED = {}  # TODO: nothing proposed: <why>`, open, offered once
  under all_tables when several tables share it. A Rebuilt table has none: answering "rebuilt"
  takes the block out, and an open SEED never waits on a table proposed or answered Rebuilt.
  A table with no Partitions proposes `{}` (its Original copied whole) or, with no Original,
  `{"months": 1}` counted back from today. write_decisions takes `{"months": N}`, refusing an N
  that isn't a whole number from 1.
- **The column of dates** (`seeding.date_source`): the one partition column whose every SHOW
  PARTITIONS value reads as `yyyy-MM-dd` or `yyyyMMdd`, read through your query; the other
  partition columns, such as `hour`, are loaded whole. The months form becomes a range,
  calendar months, both ends included, values kept as written (`seeding.months_before`,
  `written_like`).
- **project.seed_tables(tables, query=, execute=)**, a new public name, this ticket's, in
  `sqlglot_composer/seeding.py`: only a History table holding no Partition (no row, for one with
  none) is seeded, so a rerun loads nothing. With an Original it sends `seed_copy`; in prod it
  copies the dev copy's Original, or the dev copy where there is none, within the dev copy's
  SEED (promote now keeps dev's SEED line). With none it runs the write as of each day, oldest
  first: the logic is loaded again under `conditions.run_as_of(day)`, so `today()`, a Run value
  from it and `last_n_days` give that day, and CURRENT_DATE in the Hive is written as that day
  (`seeding.with_today`); the day the write targets is read back from its Hive
  (`converting.day_on_column`), so a write targeting yesterday runs as of the day after. A day
  that fails is reported with the warehouse's first line, and the rest go on; one GROUP BY read
  afterwards lists each day with no rows. Sends are logged as "Seed" in the Admin log and as
  `seed` in admin/sent.csv (`workflows.SEED_SENT`), never counted as a write. With no execute
  it is a dry run. A table seeded before 8.10 keeps its `seed()`, sent as it was.
- **The Workflows**: convert's and promote's seed steps are gone (6 steps each); their write
  step's cell is `print(project.seed_tables(..., query=query, execute=execute))` then
  `project.run_tables(...)`, and new_table's step 7 the same after its creates. new_table's
  step 3 is `project.reference_from_logic(TABLES, query=query)` (a new `query=`), which proposes
  SEED from the first table preview() reads with a column of dates. convert no longer writes
  `seed()` into a Table notebook (`converting.with_seed` is gone); `batch_tables(...,
  seeded=True)` and `promoted_tables(..., seeded=True)` stay for batches from before 8.10.
- **Tests**: `tests/test_seed_widened.py` (months from a newest Partition; `yyyyMMdd`; no column
  of dates, open, answered with a list; dt with hour; an append copied whole; a Rebuilt table
  with no SEED; months refused and under all_tables; the as-of text). Journeys in
  `tests/journeys/test_workflow_journeys.py`: a one-Partition daily load seeded from its
  Original cell by cell (its write step run again sends no Seed) and through the runner (a dry
  run sends nothing); new_table with `date_sub(current_date, 1)`, a source missing a day and a
  day the warehouse refuses, the report listing each, a rerun sending no Seed, then promote
  copying dev's Partitions into prod; the same through the runner with a Run value from
  `today()`. Updated: test_seed_limits, test_batches, test_decisions_for_every_table,
  test_promotion, test_prod_building_blocks, test_hivevars, test_run_values,
  test_compare_step, test_run_workflow, and the journeys' step numbers.
- **Choices the spec left open**: a write that reads no today (no CURRENT_DATE, no Run value
  that changes with the day) isn't run as of each day: the report says its first write loads
  what it reads. "The table the write reads its date from" is the first table it reads with a
  column of dates. In a dry run a table that can't be read holds nothing; in a real run that
  read's error stops its Seed. SEED is open when the Original's Partitions can't be read, as
  on the Example database, so those tests and how-to 09 answer it.
- **Left**: a Seed copied from the Original makes the compare of a seeded Partition pass
  whatever the write does (the tag-answered-wrong journey now limits its Seed to show the
  failure): worth a line in ticket 06 or 07. KNOWN_ACTIONS for the two new_table-from-a-query
  journeys rose by one each, to 14 and 15: ticket 04, merged with 02, types the kind. The
  beginner reader hasn't run: this implementer spawns no agent.
- **For ticket 07 (docs)**: how-to 09 got only what its doctest needed (steps 11 and 12
  reworded, the seed under all_tables); Copilot files 13, 14, 16 were written again from their
  sources, but 17's source and the Copilot evaluation's tasks (T41, T42, T48, T49,
  `FAILS_COMPARED`) still name the old seed step's cells, which still run, since `seeded=True`
  now gives []. docs/workflows.md, the pages, how-to 29 and the Example projects are written
  again.
- **For ticket 08 (the Upgrade)**: every Project's convert, promote and new_table notebooks
  change (the seed cells gone, the write cells, new_table's step 3 `query=query`), so `to_8_10`
  must write them again; `test_the_example_projects_of_each_version_since_8_3_upgrade_straight_into_this_ones`
  fails until it does.
- **Texts a beginner sees, changed**: the SEED comment block and line in a Table reference;
  check()'s seed question and the DECISIONS "seed" line it prints; write_decisions' seed report
  lines and refusals; the checklist's Seed note; the write steps' Goal and Action in all three
  Workflows, the decision step's "run steps 3, 5 and 6 again", PARTITIONS' "step 6"; the
  Seed's report; the docstrings of `seed_tables` and `reference_from_logic`; how-to 09.

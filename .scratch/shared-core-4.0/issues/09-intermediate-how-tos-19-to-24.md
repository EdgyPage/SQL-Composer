# Intermediate how tos 19 to 24

Type: task
Status: resolved
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

## Answer

Built in 3f9bee6 (with 7f247e8, write_table_reference's docstring), fixed up after its code
review and first beginner read in b57e0b5, and after its confirming beginner read in the commit
that resolves this ticket.

- **The how-tos.** `worked_examples/how_to/19_a_day_written_another_way.py` to
  `24_share_building_blocks_between_statements.py`, `For: Intermediate`, each one fresh notebook
  on the Example database, each Common mistake run live, every new Statement's Hive shown with
  `show_hive`:
  - 19 A day written another way, and a second partition: `ops.region_costs`, split by region
    and then by a dt written like `20260911`; DESCRIBE and SHOW PARTITIONS, then
    `write_table_reference`, which looks for the Date partition in the first partition column
    only, so it writes `date_partition=None` and a TODO; the TODO filled in as
    `date_partition="dt",` and `date_format="%Y%m%d",`, checked with `check_table_reference`;
    the days bounded, then the region too. Mistakes: keeping `date_partition=None` (no message
    stops you), naming dt without its date_format (`check_table_reference` gives the line),
    writing the day the usual way.
  - 20 Look things up as of a day: `ops.job_owners`, a daily snapshot ("snapshot" defined here
    as plain English); each run joined on the job and the day, the snapshot bounded in its own
    right; each team's runs as owned at the time; each job's newest row with `row_number` in a
    Derived table. Mistakes: joining on the job alone (the repeated-rows Warning), taking the
    team from today's table (silent, the total still 28), leaving the snapshot's days unbounded
    (the Load limit's refusal).
  - 21 Week and month rollups: each job's runs per `week_start` and `month_start`, the different
    jobs per week, the Hive's DATE_ADD and NEXT_DAY worked through; Check it worked counts runs
    per day on the Example database and adds them into weeks in pandas. Mistakes: adding up each
    day's count of different jobs, leaving the week out of GROUP_BY, weeks the days only partly
    cover.
  - 22 Incremental loads and late data: `mart.job_day` rewritten over the last three days with
    `last_n_days` and `by_day`, a preview first, why INSERT_OVERWRITE makes sending a day again
    safe, how many days to choose; the late row is an event of its own day that reaches the
    warehouse after that day's run. Mistakes: the window as one write, dt left out of GROUP_BY,
    INSERT_INTO for the window.
  - 23 A pipeline of Saved tables: `mart.job_day` from the events, `mart.team_day` from it and
    `ops.job_owners`, the weekly rollup `weekly_rollup(first_day, last_day)` read over
    2026-09-21 to 2026-09-27, the day's writes in order (writer before reader), one Lineage for
    the chain. Mistakes: a Saved table's Table reference changed but not its write
    (`drop_table`, create, write again, since `may_exist=True` changes nothing), saving the
    weekly rollup (the live refusal that `INSERT_OVERWRITE(team_week)` covers 7 days), a step
    that rewrites the table it reads (`export_lineage` refuses the loop).
  - 24 Share Building blocks between Statements: blocks that take the days, one that reads other
    blocks handed to it as arguments (an anti-join), a Statement built from them, a semi-join as
    a block, one name per block whatever the days, and the blocks in one file at Level 1.
    Mistakes: building one block twice in a Statement, the day in a block's name, bounding the
    LEFT_JOIN's table in WHERE (the bound in `ON=` shown live).
- **sqlglot Composer's page.** sqlglot's executor can't run `row_number`, `week_start` or
  `month_start`, so 20 and 21 give pandas stand-ins (`newest_owner_in_pandas()`,
  `starts_per_week_in_pandas()` and the like), each sqlglot-only block saying a pasted run stops
  with a RuntimeError and the result was worked out in pandas; the Spark run's doctests hold
  each stand-in's result to what Spark gives.
- **Ticket 12's question** (how-to 24's "blocks built from other blocks" against the Levels
  rule): blocks that read each other go in one file; a Building block file never imports
  another; a block from another file is taken as an argument, the Statement at Level 2 importing
  both files. 24's "Put the blocks in a file" says so.
- **This ticket's comment, write_table_reference on `ops.region_costs`.** Not changed in
  behaviour (that would be the user's call): how-to 19 walks through the TODO, and 7f247e8 has
  write_table_reference's docstring say it looks in the first partition column only and that
  `check_table_reference` gives the date_format line once dt is named. The TODO's own words
  ("newest region") are ticket 16's item 11.
- **Deviations from the Question.** How-to 23 is "A pipeline of Saved tables"
  (`#a_pipeline_of_saved_tables`), not "a layered pipeline", and 24 is "Share Building blocks
  between Statements" (`#share_building_blocks_between_statements`), not "a library of Building
  blocks": the glossary avoids "layer" (it says Level) and "library". And 23's weekly rollup is
  read, not saved: a write fills one day of its Saved table, so a week can't be one write; the
  rollup is a Statement over `mart.team_day`'s saved days, and saving it is one of 23's Common
  mistakes, refused live.
- **The page tool (ticket 06's).** A step's globals hold `__name__`, as a notebook's do
  (3f9bee6; ticket 08 needed the same); after the review, `tools/how_to_page.py` refuses text
  outside an Edition block that would name one Edition twice on a page, folds a written file
  longer than 120 lines in `<details>`, and names a file the same as one shown earlier instead
  of showing it again (b57e0b5), each with a test in `tests/test_how_tos.py`.

**Code review (2026-10-05).** Fixed in b57e0b5, with the first beginner read's stops. Spec: the
renames above; drift D129 (27's Goal, in ticket 10), D135 and D136 ("layer" gone from 23; the
weekly rollup read, not saved, over 2026-09-21..27), D137 (23's changed Table reference: drop,
create, write again) and D138 (22's late row). Standards: 23's weekly-rollup save made a live
mistake, and the Lineage file's pinned commit 1a2b3c4 explained; the silent mistakes in 19, 20
and 22 say "No message stops you"; 20's and 21's sqlglot-only blocks say a pasted run stops with
a RuntimeError; 21's Check it worked runs on the Example database; 22's `last_n_days` and the
real-today line; 24's `many_matches=True`, the ON= bound live and the Levels. Kept, answered:
"snapshot" stays plain English, defined once in 20; 21's GROUP_BY refusal suggesting dt for a
week is ticket 16's item 8, and 19's example day '20260925' in a refusal its item 6.

**Beginner reader (2026-10-05).** Two reads. The first's stops in 19-24 (Derived table and
`WITH`, NULL shown as None, `7 * -1`, the day in 19's message being an example, how blocks share
files) were fixed in b57e0b5. The confirming read, on b57e0b5, found every earlier stop clear
and six new ones here, fixed in the commit that resolves this ticket: 22 said "today" where its
window is the days before today (now "the days before yesterday as well as yesterday", and "the
run just after midnight", "a run writing only its newest day"); 23's "the one day its FROM table
reads" (now "so Saved tables hold days, not weeks"); 20's bound "in WHERE" (now "in WHERE (or in
ON=)", as its last mistake shows); 19's "newest region" (now the last region SHOW PARTITIONS
lists, the TODO's word kept in brackets); 21's NEXT_DAY worked for Thursday 2026-09-24 and
Monday 2026-09-14; and 20's jobs named with their ids, "nightly_load (job 1)", as 22 and 25 do.

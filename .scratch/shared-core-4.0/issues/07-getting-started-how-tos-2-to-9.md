# Getting started how tos 2 to 9

Type: task
Status: resolved
Blocked by: 06
Size: L

## Question

How-tos 2-9 of the approved plan: import a table's column names programmatically; describe a
table by hand; a first Statement and its Hive to paste; filter rows; count per group; join
safely; reusable Derived tables (WITH ... AS in the Hive); latest per key with row_number.

## Done when

- Each runs as a doctest in both Editions; the beginner reader has run.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).

## Answer

Built in eeaddd0, then fixed after its code review and beginner reads in d85e7a8 and the
commit that resolves this ticket.

- **The how-tos.** `worked_examples/how_to/02_import_column_names.py` to
  `09_latest_row_per_key.py`, each one fresh notebook on the Example database, each Common
  mistake run live, and each step that runs a new Statement showing its Hive first, with
  `show_hive`:
  - 2 Import a table's column names: DESCRIBE, `write_table_reference` for one table and in a
    loop, the TODOs filled in, `check_table_reference`, `check_key`, `first_look`,
    `all_columns`, and a SELECT from a list of names with `getattr`.
  - 3 Describe a table by hand: one sentence for what a row is, each argument of `Table`, the
    file to keep, a Statement on it, `date_format=` and a `datetime.date`, and `create_table`'s
    Hive to check.
  - 4 Build a first Statement and paste its Hive: a clause at a time, `to_hive`, `AS`,
    `show_hive` of one and of two Statements, a .sql file, `run`.
  - 5 Filter rows: the days, `equals`, the comparisons, `is_in` (from another result too),
    `contains`, `any_of` and `all_of`, `is_null`, and NULL's traps.
  - 6 Count and add up per group: `count_rows`, `sum_of`, `min_of`, `max_of`, `where=`,
    `count_distinct`, two columns, `HAVING`, the top N.
  - 7 Join tables safely: the keys, a safe JOIN, the repeated-rows Warning and a total too big,
    adding up first with `derived`, `LEFT_JOIN` and `fill_null`, the rows with no match.
  - 8 Reusable Derived tables: `derived`, a Building block taking the days, checked alone,
    a block reading another (handed in as an argument), the same block in two Statements, its
    file.
  - 9 The latest row per key: why `max_of` isn't the latest row, `row_number` in a Derived
    table, number 1, the top N per group; on sqlglot Composer, pandas stand-ins answer the
    `row_number` Statements, and its page shows the stop a notebook gives once.
- **Cross-links.** "Next" lists and in-prose links among how-tos 1-18 where they help, and
  from them to 19-30: 1→2, 4; 2→3, 18, 19; 3→10, 19; 4→5, 11, 12; 7→8, 16; 8→2, 13, 24; 9→20, 28;
  10→3, 4, 7; 11→6, 22; 12→22, 23; 13→8, 29; 14→23, 29; 15→7; 16→5, 7, 8; 17→25, 26;
  18→2, 19. The links to how-to 23 use its slug on this branch, `#a_layered_pipeline`; ticket
  09's fix-up renames it "A pipeline of Saved tables", so the slug is updated after merging.

**Code review (2026-10-05).** Three reviews of eeaddd0 (standards, spec, and a reading of the
page). Must fix, each done: how-to 4's long_runs.sql held both Statements, as `text` was
reassigned by `show_hive(runs_that_day, long_runs)` (the file is now written before, and Check
it worked is exact, `== to_hive(long_runs) + ";"`); ten steps ran a new Statement without
showing its Hive (2's every_column, 5's failed, 6's all_runs, days_per_job and per_job_day,
7's runs_with_alerts, careless_total and every_job, 8's two block checks, 9's careless, and
9's newest_ids too: each now has `text = show_hive(...)`); 8's `busy_report` used the avoided
word "report" (now `busy_with_names`); 8's "the same stop comes when one Statement reads one
block twice" was false, a different ValueError (deleted); 7's 210 didn't add up (now: runs 97
and 103 twice, 101 three times, the four runs with no alert not at all, 180 + 30 + 30 + 20 -
50); 3's Opt-out is "for the rare call where a total really is what you mean". 2's "already
there" stays prose, not run live: the FileExistsError names an absolute path, which the page
refuses to show (ticket 16, item 10, changes the message, and the step can then run). Drift
items from the merge, each fixed: D132, 8's busy_jobs called runs_per_job itself while each
block lives in its own Level 1 file (it now takes the Derived table as an argument, as how-to
24 does, and says why); D133, 7 said `is_null` was the one condition on a LEFT_JOIN's table
that belongs in WHERE (an `any_of` holding one is allowed too); D134, 3's "the one argument you
can't leave out" (now: unlike `key=`, `does_not_add_up=` and `date_format=`, it has no
default). The badge test in tests/test_how_tos.py built its expected title with the code under
test, `example_gallery.inline`; it now uses `html.escape`.

**Beginner reader (2026-10-05).** The first read of eeaddd0, as a Python-first SQL beginner,
stopped costliest at how-to 9 on sqlglot Composer's page: its steps stop with a RuntimeError in
a real notebook (no window functions), while the page showed pandas results. A sqlglot-only
block now runs that stop once, live, says "here and in the steps below", and says the results
are what Hive gives at work, worked out in pandas. Then: 2's `first_look` reads your real
yesterday, empty on the Example database in a notebook (said); 7's "Add up before you join"
brought in `derived`, WITH, `LEFT_JOIN` and `fill_null` at once (split into "Add up first, with
derived", pointing to how-to 8, and "Keep every run with LEFT_JOIN", saying the alerts' days now
sit inside alerts_per_run); 6's HAVING repeats the calculation while ORDER_BY sorts by name
(SQL works HAVING out before SELECT names anything, ORDER_BY after); 8's import line
`from table_references.job_runs import job_runs` against 2's `from job_runs import job_runs`
(one paragraph). Also fixed: DESCRIBE's empty row; Saved table defined at first use (2, 3);
"counts of different values" everywhere; 2's Check it worked asks for its three files by name;
3's "step after next", its key (job, region, day), `date_partition=`'s default, and create_table's
PARTITIONED BY and STORED AS ORC; NULL shown as NULL on the page, None or NaN in pandas;
"bound" (5 reworded, 7 says what the message's "bounds" means); checks comparing rows in row
order (5 sorts, 6 and 9 compare dicts, and say why); COUNT(CASE WHEN ...) explained (6);
GuardRefused (2) and LoadRefused (6) told apart; 7's `many_matches=True` in two mistakes; 7's
"On the page" line; 9's stand-in argument `newest=` (now `largest_first=`); "small executor"
(9's prose); 4's "Python's own object", "Statement" for SQL text in Hue (now "query"), and
`last_n_days` leaving today out; 6's "counting functions" (now "calculation functions"); 8's
Goal split in three; 8's per_team needing no days of its own; Lineage defined at first use
(8); 2's "Once you've filled in a file's TODOs"; 1's Next line that read as a place.
A confirming read of the fixed how-tos was started on d85e7a8; its report is still to come,
and this ticket stays open until any costly stop it finds is fixed or answered here.

**Confirming beginner read (2026-10-05), after d85e7a8.** The earlier fixes held. Fixed in the
commit after the merge: how-to 9's check of `newest` now says that on sqlglot Composer's Example
database the run stops and `newest` is the pandas result; DESCRIBE's blank row is "the fifth",
its name empty and its other cells NULL; how-to 8's busy_jobs sentence and its file rule, which
now agrees with how-to 24 (a few blocks may share a file; a block file never imports another);
the first_look result said to be "as if today were 2026-09-25"; why fill_null wraps sum_of; "as
the message's Usual fix says"; ORDER_BY sorts smallest first on its own; first_runs' Hive
described. Left: "distinct counts" against "counts of different values" (the generated TODO and
the GuardRefused message say "distinct counts"; ticket 16 may align them).


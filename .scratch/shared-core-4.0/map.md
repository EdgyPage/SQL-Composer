# Toolbox 4.0: one shared core, the sqlglot Composer rename, how-tos, example projects and templates

Label: wayfinder:map

## Destination

A user can learn and start the Toolbox without writing their own files first: a polished
how-to page at two levels, two generated example projects laid out as work should be, and a
templates library to copy and fill in. The two Editions share one folder of code, so nothing is
generated twice and nothing can drift, and the Hive that runs can be printed ready to paste
anywhere.

## Notes

- **Where it comes from.** On 2026-10-05 the user, reading the code, found "no way or example
  to interact with the code without making my own files and knowing", and asked for a gallery
  of how-tos for building tables and lineages; "a generated set of files in an example folder
  showing what a correct file structure looks like with example 1 and example 2 and example 3
  which is some sort of combination or interation between examples one and two"; to show off
  "how to contruct tables, how to create stable CTEs, how to create lineages, how to import
  tabe coumn names programatically, and any more things you can think of"; and "a small
  templates library of expected structures or paradigms" so users can "plug and play their
  specifics".
- **The reorganisation (the user, 2026-10-05).** "rename the effectively sqlglot version to
  match the schema of spark_composer ie sqlglot_composer. Second, try to share as many
  resources betweent he two versions as possible to prevent version drift and simplyfy
  testing. I am ok with copyting and pasting two folders eg composer_code and spark_version
  instead of just one."
- **The user's answers (2026-10-05):**
  - Users' import line names the Edition folder: `from spark_composer import *` or
    `from sqlglot_composer import *`; the Edition folder loads the shared folder beside it.
  - The shared folder is `composer_core/`.
  - The sqlglot Edition's product name is "sqlglot Composer".
  - It ships as **Toolbox version 4.0**. Raise TOOLBOX_VERSION only in ticket 15.
  - "really develop the example how tos ... inside code blocks or in very nice html like
    examples.html", and "be sure there's a method to return the executed string as a printed
    statement ready for copy and paste to other programs".
  - "Add an intermediate set of how tos and project. You can build out the example data
    tables to support it as needed."
- **The approved plan** is the design: one `composer_core/edition.py` the Edition plugs its
  `writing` and `engine` into (one Edition per Python), a thin Edition `__init__`, tests that
  import from `sqlglot_composer` with the Spark run aliasing only that package, `show_hive`,
  a `how_to.html` page per Edition with Getting started (1-18) and Intermediate (19-30)
  how-tos, three new Example database tables, `example_projects/{starter,intermediate}/`,
  `templates/{starter,intermediate}/`, and a `main` that ships all of them, generated once per
  Edition.
- **Order.** Seam, then split, then rename: renamed first, the soon-deleted swap() would refuse
  the product name "sqlglot Composer". Through tickets 01-02 the goldens and both galleries
  stay byte-identical.
- **Every ticket follows CLAUDE.md's Definition of done**: both runs pass, the code-review
  skill has run with the ticket as its spec, no drift item is left open, and the beginner
  reader has run when anything a beginner sees changes.
- **The version.** Drift version items from tickets 01-14 are answered "folds into 4.0, the
  user's choice (2026-10-05)" and stay open until ticket 15, as the Spark effort did for 3.0.
  Nothing is exported before ticket 15.
- **Ticket 15's CHANGES 4.0 section** says, besides the update steps: you copy two folders;
  importing both Editions in one Python now stops (before 4.0 the two could sit side by side);
  tracebacks name `composer_core.refusals.GuardRefused` (drift review of 2269d4e); SQL Composer
  is sqlglot Composer, so delete `sql_composer`, copy in `sqlglot_composer` and
  `composer_core`, and change `from sql_composer import` and `sql_composer.VERSION` (drift
  review of 403c8fe, D121).
- Ticket 15's CHANGES 4.0 section also gains `show_hive`, the new public name (ticket 04),
  and the Example database's three new tables, `job_events`, `job_owners` and
  `region_costs`, with its unknown-table refusal now naming all six (ticket 05, D123).
- Ticket 15's CHANGES 4.0 section also gains a fixed bug (ticket 11): **export_lineage no
  longer lists a LEFT JOIN's table's conditions under "Rows that count" for the columns that
  don't come from it.** A LEFT_JOIN keeps every row before it, so what decided the joined
  table's rows (its own WHERE, or the WHERE and JOIN of the Statement that wrote it) decides
  only the columns read from it; before 4.0 those conditions were listed under every column,
  as if they had dropped rows. With many_matches=True they are still listed, since each row
  can then count several times.
- **Ticket 15 reruns `python tools/example_project.py` after raising TOOLBOX_VERSION** (and
  again for each Example project ticket 12 adds): an Example project's lineage footers name the
  Toolbox version, which the generator takes from TOOLBOX_VERSION rather than pinning, so the
  staleness test in tests/test_example_projects.py fails until it is rerun (ticket 11).
- Ticket 15's CHANGES 4.0 section also says each Edition's folder now holds `how_to.html`, the
  how-to page, beside `examples.html`, and that the import now stops when it is missing, as it
  does for `examples.html` (ticket 06, D127).
- Ticket 15's CHANGES 4.0 section also gains ticket 16's two new refusals and clearer messages
  (items 5-13):
  - **Comparing two tables' days written different ways is refused**, a new Guard with no
    opt-out: `equals(region_costs.dt, job_events.dt)`, where one Date partition writes its days
    like 20260925 and the other like 2026-09-25, built without a word and matched no rows. Any
    comparison of the two is refused, in `ON=` or `WHERE`, and so is one through a Derived
    table's column that passes a Date partition on unchanged. The message names both
    date_formats.
  - **run refuses a send that gives back something other than a pandas DataFrame** for a
    read, such as the plain list of rows a query API gives, or None from a send with no return,
    and says to end the send with `return pd.DataFrame(rows)`. Before, the list came back from
    run as it was. A write's send may still give back anything.
  - **run, to_hive and show_hive refuse in their own name** what isn't a Statement; for a
    Derived table the fix wraps it in `statement(SELECT(all_columns(d)), FROM(d))`, and for a
    list it loops over its Statements.
  - **Clearer fixes:** a day written the wrong way is shown as the Table reference writes it,
    your own day where it can be read, and a day written another table's way also offers that
    table's date_format; a calculation's name in a comparison, as in
    `HAVING(at_least("runs", 3))`, says to write the calculation itself; a missing GROUP_BY
    for a calculation such as `week_start(dt)` names the calculation and offers its name,
    `GROUP_BY("week")`, not the column inside it; the repeated-rows Warning on a table keyed
    by its Date partition says to match the day too, with `all_of`; write_table_reference
    names the file it won't overwrite, not its whole path, and its TODO for a table first
    partitioned by something else says "its last region value" and "name it in
    date_partition=", not "its newest region" and "name it".
- **Ticket 15 reruns `python tools/example_project.py` after raising TOOLBOX_VERSION**, and
  `python tools/example_project.py --project intermediate` (ticket 12): an Example project's
  lineage footers name the Toolbox version, which the generator takes from TOOLBOX_VERSION
  rather than pinning, so the staleness test in tests/test_example_projects.py fails until it
  is rerun (ticket 11).
- Ticket 15's CHANGES 4.0 section also says the how-to page holds 30 how-tos, Getting started
  (1-18) and Intermediate (19-30), the second group covering a table whose days are written
  like 20260911 or that is split first by something other than days, as-of lookups, week and
  month rollups, late data, a pipeline of Saved tables, shared Building blocks, data-quality
  checks, settings, hive_function, finishing in pandas, reviewing a change with Lineage and
  testing your own Statements; that write_table_reference's docstring now says it looks for the
  Date partition in the first partition column only, writing `date_partition=None` and a TODO
  otherwise (ticket 09, 7f247e8); and that the README's "Where the two Editions' Hive differs"
  now says what ANSI mode is (tickets 09 and 10).
- Ticket 15's CHANGES 4.0 section also gains the Templates (ticket 13): `templates/`, a
  starter set and an intermediate set of scripts to copy into a project and fill in, each
  placeholder listed in its docstring, and a README giving the order to use them in.
- Ticket 15's CHANGES 4.0 section also gains ticket 16's four fixed bugs (items 1-4):
  - **A Warning always shows**: a RepeatedRowsWarning from a scope with no `__name__`, as some
    notebook tools and `exec` give, was dropped unseen, and under `python -c` it stopped with
    "'__main__' is not a built-in module".
  - **export_lineage lists a LEFT_JOIN's own ON= only under the columns read from its table**
    (and under every column of its Statement when another of its conditions that can drop rows
    reads that table, as an anti-join's WHERE(is_null(...)) does, or with many_matches=True;
    and under what a second LEFT_JOIN matching on its columns brings), in the Statement
    that joins and in every Statement downstream of the Saved table it writes; before 4.0 it was
    listed under every column, as if it dropped rows. And a write's bound on a joined table's
    Date partition that its JOIN's ON= sets equal to the day written is listed only in the
    write's own section, as the day written is.
  - **A join that compares a column with itself stops**: JOIN or LEFT_JOIN whose ON= sets a
    column of the joined table equal to the same column of a table of the same name, as when
    one Statement reads one Building block twice, stops with a ValueError saying to give the
    second a name of its own; before 4.0 it warned that the join "matches on nothing".
  - **sqlglot Composer's Example database refuses a query it would answer wrong**: one that
    adds up rows after a join where sqlglot's executor would read a joined table's column in
    place of a same-named column of a table before it (NULL after a LEFT_JOIN), with "The
    Example database can't run this Hive"; Spark Composer's runs it.

- Ticket 15's CHANGES 4.0 section also says what the download now holds (ticket 14):
  `example_projects/` and `templates/`, each with a folder per Edition, every file stamped
  "copy it, then edit your copy", for reading and copying from, which the Toolbox doesn't need;
  and the README's new sections, Update from 3.x, How-tos, Example projects and Templates.
  The beginner reader's costliest stop on ticket 14's preview was the README's "This is
  version 3.2" beside "Update from 3.x" and "Before 4.0", with no 4.0 in CHANGES.md: ticket 15's
  version raise and CHANGES 4.0 answer it, so check the previewed README reads true after.
- Ticket 15's export now needs both sqlglot and pyspark installed in the Python that runs it
  (it already did, to import each Edition) and runs each Example project's dry run; no Java.

## Records this changes

- ADR 0002's generated-copies paragraph: superseded by ADR 0003 (ticket 02).
- "Copy one, the whole folder": now copy `composer_core/` and one Edition folder.
- The `main` allowlist: adds `composer_core/`, `example_projects/<edition>/` and
  `templates/<edition>/` (ticket 14).
- CONTEXT.md: Edition, Toolbox and Clean branch amended; the new word Composer core; "CTE"
  stays avoided ("Derived table (WITH ... AS in the Hive)"); the new word Example project, and
  Level saying where a script such as run_pipeline.py sits, above the Levels (ticket 11, D124).

## Decisions so far

- [The Edition seam](issues/01-the-edition-seam.md): every shared file reaches the Edition's
  writing and engine through edition.py, which one Edition plugs into per Python; lineage's
  time, commit and version can be pinned; the goldens and galleries are unchanged.
- [The split into composer_core](issues/02-the-split-into-composer-core.md): one core folder,
  two thin Editions that check both folders, plug in and re-export; one Edition per Python;
  the export ships composer_core; ADR 0003.
- [The rename to sqlglot Composer](issues/03-rename-to-sqlglot-composer.md): sqlglot_composer
  and "sqlglot Composer" everywhere but the records; the project is "the Toolbox"; named_for
  refuses the old name.
- [show_hive](issues/04-show-hive.md): prints the Hive that runs with a `;`, each Statement
  headed by its variable's name, and returns it; 64 public names.
- [Example database tables for the intermediate level](issues/05-example-database-tables-for-the-intermediate-level.md):
  ops.job_events, ops.job_owners and ops.region_costs, 14 days each, the last partitioned by
  region then a dt written 20260911; the first three tables and every golden unchanged;
  sqlglot's executor can't run week_start, month_start or row_number on them.
- [The starter example project](issues/11-the-starter-example-project.md):
  `example_projects/starter/`, three examples with the steps create, preview(day),
  write_day(day) and backfill(first_day, last_day), and run_pipeline.py above the Levels;
  `tools/example_project.py --project` regenerates its Table references and lineage, the
  time and commit pinned, the version not; the glossary gains Example project; export_lineage
  no longer lists a LEFT JOIN's table's conditions under the other columns' rows that count.
- [The how-to page](issues/06-the-how-to-page.md): `tools/how_to_page.py` writes `how_to.html`
  per Edition from `worked_examples/how_to/NN_slug.py` docstrings (`For: Getting started` or
  `Intermediate`, six fixed headings), every step run live with lineage pinned; Edition-only
  blocks may hold steps; a how-to's `NAME_in_pandas()` stands in where sqlglot Composer's
  Example database can't run a Statement; the filter script is shared with examples.html; how-to
  1, Start a notebook; the page links to no README anchor.
- [The intermediate example project](issues/12-the-intermediate-example-project.md):
  `example_projects/intermediate/` with settings.py at Level 0; example 1 saves each job's cost
  per day with its days rewritten like 2026-09-24 (days written differently can't be joined),
  example 2 each job's day with its team as of that day, example 3 each team's days, added into
  weeks when read (a write fills one day); one step, `write_days(first_day, last_day)`, for the
  last 3 days or a backfill; settings-driven quality checks; a lineage review whose "before"
  file the generator writes with the edit undone. How-to 24's "blocks built from other blocks"
  breaks the Levels rule: ticket 09 decides.
- [Getting started how-tos 2 to 9](issues/07-getting-started-how-tos-2-to-9.md): import a
  table's column names, describe a table by hand, a first Statement and its Hive to paste,
  filter rows, count per group, join safely, Derived tables as Building blocks (a block reading
  another takes it as an argument), the latest row per key; every new Statement's Hive shown;
  sqlglot Composer's page shows the row_number stop once and labels its pandas results;
  Next and in-prose links among how-tos 1-18 and to 19-30.
- [Getting started how-tos 10 to 18](issues/08-getting-started-how-tos-10-to-18.md): save a
  table, backfill, a daily pipeline, Lineage of one Statement and of a pipeline, Load limits,
  Guards, Warnings and opt-outs, Statements in a loop, keeping a Table reference true; each
  mistake run live; the page now shows a step's Warning (a notebook scope's `__name__`).
- [Intermediate how-tos 19 to 24](issues/09-intermediate-how-tos-19-to-24.md): a day written
  like 20260911 behind a region partition, as-of lookups from a daily snapshot, week and month
  rollups, incremental loads and late data; 23 is "A pipeline of Saved tables" and 24 "Share
  Building blocks between Statements" (the glossary avoids "layer" and "library"); the weekly
  rollup is read, not saved (a write fills one day); blocks that read each other share a file,
  a block from another file is taken as an argument; write_table_reference's TODO left as it is.
- [Intermediate how-tos 25 to 30](issues/10-intermediate-how-tos-25-to-30.md): data-quality
  checks, Table references and Statements from settings, hive_function and the three places the
  Editions' Hive differs (only 27 shows them), lag, rank and a rolling sum in pandas, reviewing a
  change by comparing Lineage files, testing a Statement against a pandas oracle; no new Toolbox
  code; the page tool refuses text naming one Edition twice on a page and folds long files.
- [The Templates](issues/13-templates.md): `templates/starter/` (notebook_start,
  keep_table_references_true, building_block, saved_table_reference, saved_table,
  daily_pipeline, per_group_statement) and `templates/intermediate/` (incremental_load and
  incremental_pipeline, which fit the starter pieces, weekly_rollup, as_of_lookup,
  building_blocks, quality_statements, settings_driven on settings.py's text pattern), with
  `<UPPER_SNAKE>` placeholders under "Fill in:" and a README giving their order; names avoid
  "report", "check" and "library"; notebook_start and keep_table_references_true work from an
  empty folder; the tests fill both sets in as one; the glossary's Template is rewritten.
- [Toolbox follow-ups the how-tos found](issues/16-toolbox-follow-ups-from-the-how-tos.md):
  warn_at_callers_line always shows its Warning; a LEFT_JOIN's ON= counts only for the columns
  read from its table (unless a condition that drops rows reads it), and a joined Date bound tied
  to the day written is listed with the write; sqlglot Composer's Example database refuses the
  joins its executor would answer wrong; an ON= comparing a column with itself is refused;
  clearer messages; two new refusals the user chose: days written two ways compared (a Guard,
  no opt-out) and a read's send that gives back no DataFrame.
- [The export ships it all](issues/14-the-export-ships-it-all.md): main holds
  `example_projects/<edition>/` and `templates/<edition>/`, dev's copies named for each Edition
  with named_for, their paths one folder deeper and line 1 stamped "copy it, then edit your
  copy"; the export also checks an Edition alone stops asking for composer_core, both Editions
  in one Python stop, and each run_pipeline.py's dry run runs (no Java); the README gains Update
  from 3.x, How-tos, Example projects and Templates, with generated HOW-TOS and TEMPLATES
  lists; how_to_page's check_links isn't widened, since no how-to links there.

## Not yet specified

- Nothing open.

## Out of scope

- Rewriting a user's 3.x files: the README's Update section tells them what to change.
- Window functions beyond row_number: how-to 28 finishes them in pandas.
- A how-to video or notebook files (.ipynb): the how-tos are text and HTML.

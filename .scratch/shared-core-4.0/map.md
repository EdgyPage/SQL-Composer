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

## Records this changes

- ADR 0002's generated-copies paragraph: superseded by ADR 0003 (ticket 02).
- "Copy one, the whole folder": now copy `composer_core/` and one Edition folder.
- The `main` allowlist: adds `composer_core/`, `example_projects/<edition>/` and
  `templates/<edition>/` (ticket 14).
- CONTEXT.md: Edition, Toolbox and Clean branch amended; the new word Composer core; "CTE"
  stays avoided ("Derived table (WITH ... AS in the Hive)").

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
- [Example database tables for the intermediate level](issues/05-example-database-tables-for-the-intermediate-level.md):
  ops.job_events, ops.job_owners and ops.region_costs, 14 days each, the last partitioned by
  region then a dt written 20260911; the first three tables and every golden unchanged;
  sqlglot's executor can't run week_start, month_start or row_number on them.

## Not yet specified

- Whether a how-to page links to a fixed anchor in the README (ticket 06).

## Out of scope

- Rewriting a user's 3.x files: the README's Update section tells them what to change.
- Window functions beyond row_number: how-to 28 finishes them in pandas.
- A how-to video or notebook files (.ipynb): the how-tos are text and HTML.

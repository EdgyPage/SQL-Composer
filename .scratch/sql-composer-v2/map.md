# SQL Composer v2

Label: wayfinder:map

## Destination

v2 of the Toolbox built and in use: a small, beginner-readable set of Python functions that
compose Hive SQL strings, with typo-proof columns through Table references, an offline lineage
HTML export, and load-safe defaults for multi-million-row tables. It is developed on `dev` with
tests and maintainer agents, and exported to a clean `main` that pastes over an existing directory
at work without touching the user's own scripts.

## Notes

- **Execution override: ON.** The user chose a built v2 over a spec. Once a component's governing
  decisions close, its build graduates from fog into a `task` ticket on this map.
- **The governing test is beginner readability.** The user is a Python-first SQL beginner. Judge
  every decision by whether they could read and follow it on first contact. Some safety
  complication may stay, but no abstraction that has to be studied before it can be used.
- **v1 is a superseded first draft.** Its code and its Metric / Dimension / Grain / Tag / Case
  model are out; do not build on either. Salvage knowledge only: the escaping test matrix
  (now `tests/escaping_cases.py`), the sqlglot ground truth, and
  `docs/adr/0001-sqlglot-over-sqlalchemy.md`, which still stands. `CONTEXT.md` was rewritten for
  v2 during charting.
- **Branches.** All work lands on `dev`. `main` is the Clean branch: generated from `dev` by an
  export script that copies an allowlist (the Toolbox plus a short README), never edited by hand.
  A check fails if `main` holds anything outside the allowlist, or if the Toolbox imports anything
  beyond stdlib, pandas, numpy and sqlglot. `python tools/export_clean.py` writes it; its first
  run replaced v1, which stays in `main`'s history.
- **Install at work.** The user pastes files over an existing directory, overwriting on a name
  clash. Their own scripts sit beside the Toolbox and import it laterally, never from inside it. A
  Toolbox update must never touch them.
- **Levels.** Level 0 Table references, Level 1 Building blocks, Level 2 Statements. Any script
  another script imports is a `.py` file; notebooks exist only at the top, to compose, preview and
  submit. Imports only point downward. All Levels live outside the Toolbox.
- **Load safety is a default, not an option.** Assume multi-million-row partitioned tables and
  limited compute on both the notebook and the server. Data does come back into pandas. A naive
  `select *` must not pull a whole table; find where this matters and get ahead of it by default.
- **Allowed at work:** Python stdlib, pandas, numpy, sqlglot. Output is a Hive SQL string for an
  API that accepts only strings.
- **Everything is generated.** Every output and artifact the Toolbox produces (SQL, lineage
  HTML, Markdown reports) is built from the Statement by code, never written or edited by hand.
- **Skills.** Grilling tickets call `grilling` and `domain-modeling`; prototype tickets call
  `prototype`; research tickets call `research`. `CONTEXT.md` is the glossary.

## Decisions so far

<!-- one line per closed ticket: [ticket name](issues/NN-slug.md): one-line gist -->

- [How can one offline HTML file render an explorable graph?](issues/04-how-can-one-offline-html-file-render-a-graph.md):
  draw it ourselves as inline SVG with a Python-computed layered layout and about 20 lines of JS
  (6 KB, no dependency); sqlglot's per-column trees must be merged on `db.table.column` and given
  the filter and join-key edges it omits.
- [Can sqlglot's own executor run an example database?](issues/14-can-sqlglots-executor-run-an-example-database.md):
  yes for joins, grouping, CTEs and three of four demonstrations; but `COUNT(DISTINCT)` is
  silently wrong before 30.19.0, there are no window functions, and date buckets should be stored
  as plain columns.
- [Which Hive query shapes choke a cluster, and what does strict mode already refuse?](issues/03-which-hive-query-shapes-choke-a-cluster.md):
  strict mode is off by default and overridable, and a plain `SELECT *` streams the whole table
  through HiveServer2, so the Toolbox enforces six defaults of its own, each with a named opt-out.
- [How does a composed Statement read?](issues/01-how-does-a-composed-statement-read.md):
  clause functions in SQL order (`statement(SELECT(...), FROM(runs), WHERE(equals(...)))`, then
  `to_hive(...)`), with columns as Table reference attributes and conditions as named functions,
  not operators; every calculation is named and sub-query columns stay checked.
- [What does the work environment actually have?](issues/02-what-does-the-work-environment-have.md):
  no probing at work, to prevent data leakage; JupyterLab 4 on a Linux VM with generous but
  unknown limits, so the Toolbox checks its own library versions on import and every lineage
  export gets a script-free Markdown twin.
- [Which sqlglot APIs can the Toolbox use at work?](issues/06-which-sqlglot-apis-can-the-toolbox-use-at-work.md):
  support sqlglot 25.24.2 up to (not including) 31 and pin `dev` to 30.19.0; on import, refuse an out-of-range
  version plus three behaviour checks; the example database needs 30.19.0 and falls back to
  labelled pandas numbers.
- [How does the Toolbox survive being pasted over an existing directory?](issues/05-how-does-the-toolbox-survive-an-overwrite-install.md):
  a flat package folder `sql_composer/`, imported only from its top level and replaced whole on
  update, which stops on import if it finds extra or missing files or mixed versions; a hand-raised
  feature number plus an export stamp, with the README at `.github/README.md`.
- [Which guardrails on how a Statement is written earn their place?](issues/08-which-guardrails-on-writing-a-statement-earn-their-place.md):
  every Guard refuses at the offending call, with a four-part message and an opt-out keyword on
  that call; ten Guards stay, including repeated rows off the key and unsafe re-grouping, and there
  is no raw-SQL entry point.
- [How much may a Statement touch and return by default?](issues/09-how-much-may-a-statement-touch-and-return.md):
  a date partition bounded at both ends, no `ORDER BY` without `LIMIT`, and no `OFFSET` or `*`
  (`all_columns(t)` instead); an automatic `LIMIT` and a date cap are seams that ship off; the
  API is reached only through `run(s, send=...)`, and `by_day(s)` chunks reads and backfills.
- [How do pieces combine across Levels - CTE, subquery, or saved table?](issues/10-how-do-pieces-combine-across-levels.md):
  a Derived table always becomes a CTE the Toolbox writes, even when kept in a Building block; a
  Saved table is written explicitly by an `INSERT_OVERWRITE(t)` Statement one day at a time,
  created from its typed Table reference, and lineage joins Statements across it.
- [What goes in a Table reference, and is it written or generated?](issues/11-what-goes-in-a-table-reference.md):
  one `Table(...)` call with typed columns, a required `date_partition`, and an optional `key` and
  `does_not_add_up`, followed by filters about that table alone; `write_table_reference` writes it
  once from `DESCRIBE` and never overwrites it, and a Saved table's is written by hand.
- [What's in the Toolbox?](issues/12-whats-in-the-toolbox.md): 59 names in eight flat modules,
  each with a doctest-ready example and a generated cheat sheet; SQL-echoing lower-case aggregates
  (`sum_of`), named comparisons, arithmetic by operators, `AS` for a second copy of a table, no
  pattern functions, and `set_load_limits` defaulting to no limit.
- [What does `dev` enforce, and which maintainer agents does it carry?](issues/13-what-does-dev-enforce.md):
  `pytest` holds every mechanical check and CI runs it on Python 3.11 against both ends of the
  sqlglot range; a drift reviewer runs after each commit and its findings become the next commits,
  which the export refuses to skip; two agents, a code reviewer and an advisory beginner reader;
  and a generated, searchable Example gallery ships in `sql_composer/`.
- [What does the Example database demonstrate, and where does it run?](issues/15-what-does-the-example-database-demonstrate.md):
  three made-up tables (`jobs`, `job_runs`, `run_alerts`) shipped inside the Toolbox as
  `example_database`, a sandbox with its own `send`; seven demonstrations, each shown in the
  gallery and checked by a test; and a join off the key now warns and runs rather than refusing.
- [Does the Toolbox check a Table reference against the warehouse?](issues/16-does-the-toolbox-check-a-table-reference-against-the-warehouse.md):
  an on-demand `check_table_reference(t, send=...)` that reports problems and notes, each with the
  line to change, and never refuses; `create_table` becomes strict, with `may_exist=True` for
  `IF NOT EXISTS`; nothing runs automatically before a write.
- [What does exploring a Statement's lineage look like?](issues/07-what-does-exploring-a-statements-lineage-look-like.md):
  one graph with every step on screen, controls to expand, collapse or hide each table and CTE,
  and a Grouped flowchart view; `export_lineage(*statements, to=None)` writes it and a Markdown
  twin under a generated name in `lineage/`, joining Statements across Saved tables.
- [Retire v1 from `dev` and carry over the salvage](issues/17-retire-v1-from-dev-and-carry-over-the-salvage.md):
  v1 is gone; the escaping matrix lives on as `tests/escaping_cases.py`; the dev files, CI, the
  three hooks, the drift list, the standards, the beginner reader and the new `CLAUDE.md` are in
  place, and the suite passes.
- [Build the Toolbox core](issues/18-build-the-toolbox-core.md): `sql_composer/` ships 60 of
  the 61 names in eight flat modules, every one with a doctest on the Example database; 609
  tests pass; `TOOLBOX_VERSION = "2.0"` and the 59th name being `TOOLBOX_VERSION` are
  confirmed by the user, and `ORDER_BY` inside a Derived table stays a Guard.
- [Build the Clean-branch export](issues/19-build-the-clean-branch-export.md):
  `python tools/export_clean.py` builds the stamped Toolbox and a README with a generated cheat
  sheet from the `dev` commit, checks and imports it, and commits it to `main` locally, refusing
  while a drift item is open; the first export replaced v1, and pushing is the user's step.
- [Build the Example database's demonstrations](issues/21-build-the-example-databases-demonstrations.md):
  seven Statement scripts in `worked_examples/statements/`, each with `careless()` and `fixed()`
  and a test checking both numbers against pandas; `week_start` and `row_number` give labelled
  pandas results, and `tests/test_levels.py` holds the Levels over `worked_examples/`.
- [Build `lineage.py`](issues/22-build-lineage-py.md): `export_lineage` ships as the 61st
  name. It writes an inline-SVG page with Graph and Grouped flowchart views and a Mermaid
  Markdown twin to a generated name in `lineage/`, and joins Statements across Saved tables.
  Boxes show the Toolbox call each calculation was written with; `TOOLBOX_VERSION` stays
  "2.0", as the user confirmed.
- [Build the Example gallery](issues/20-build-the-example-gallery.md): `tools/example_gallery.py`
  writes `sql_composer/examples.html`, one script-optional page with all 68 Worked examples,
  each with its Python, Hive, result (or a labelled pandas result) and the Toolbox names it
  uses, careless and fixed side by side; a test fails when the committed page is stale.
- [Add `INSERT_INTO` and `drop_table`](issues/23-add-insert-into-and-drop-table.md): at the
  user's request, a day of a Saved table can now be added to as well as replaced, and a table
  dropped, reversing ticket 10's "replace, never append"; the first write of a day stays
  `INSERT_OVERWRITE`. 63 names, `TOOLBOX_VERSION` "2.1", and six Worked examples of common jobs.

## Not yet specified

- **`UNION_ALL`.** Stacking two Statements is left out until a real Statement needs it. From Hive
  3.1, an ACID table refuses `INSERT OVERWRITE` combined with `UNION ALL`, so it's more than a
  one-line clause.
- **The real limits at work.** The API's row cap and timeout, and how big a DataFrame the notebook
  takes comfortably. The user measures these at work, then the automatic `LIMIT` and the
  dates-per-query cap (both unset) may get values. Also the Hive version, the engine (Tez or MR),
  and whether managed tables are ACID, which decide how a Saved table's write behaves.
- **Lineage for SQL the Toolbox didn't build.** sqlglot can parse a pasted query cheaply; whether
  that is worth supporting.
- **A worked walkthrough** from Table reference to submitted Statement, for the user.

## Out of scope

- **The v1 semantic model** (Metric, Dimension, Grain, Tag, Case as concepts to learn): ruled out
  in charting by the beginner-readability test. Its *guarantees* are not out: the user asked for
  them back as lightweight functions shown working on an example database (see the guardrails
  and example-database tickets). The model does not return.
- **Dialects other than Hive.**
- **Life beyond roughly seven months.** The data migration ends the need, so scalability past
  that is not a goal.

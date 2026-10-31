# Toolbox 8.0: a standard, a refactor to it, and Workflows

Label: wayfinder:map

The user (2026-10-30), with 7.2 exported and pushed, asked for two things, grilled the same day:

- **A coding standard** "that makes code easier to review. Looking over the code base, there seem
  to be a lot of bespoke functions. I do not want to impose standards that harm the utility or
  functionality of the library, but I want documented style patterns that make the code easier
  to maintain and read." Then, while grilling: "I want less code to review that I actually
  understand, so I think more simple is the way to go instead of less and complex."
- **Automation for anticipated workflows.** "I have to convert multiple sql statements full of
  CTEs with create statements to databases I don't have permissions to. While engaging with the
  program, I was told to create manual files and whatnot. I quickly lost track of the steps I
  needed to perform and what I needed to do. Why do I have to create manual files when the
  answer of what to do was already given back to me as code? If we know the code, then
  implement it." And: "Most importantly, I want to be able to import long collections of sql
  statements that exports references and renames tables. This scales from 1 to n statements.
  Perhaps something that exports to multiple tables too."

The user ordered it: "guidelines, refactor, workflow rework". Three phases, in that order.

## Notes

### The version

- **Phases 1 and 2 raise no version**: nothing a user sees changes (public names, Hive,
  refusal messages). **Phase 3 is 8.0**, the user's number (2026-10-30), raised by its last
  ticket with its Upgrade step, as every raise does.
- **The glossary lands with the ticket that makes it true**, as 7.0 and 7.2 did. The words were
  grilled on 2026-10-30 and are below, under "Words"; each ticket names the ones it lands.

### Phase 1: the standard (ticket 01)

- **Simple over short**, the headline: write the version a reader follows in one pass, even when
  it takes more lines. Share a function only when the same job recurs and its name says the
  whole job; otherwise repeat the plain code. Where "less code" and "simple" pull apart, simple
  wins.
- **Two audiences.** Code a user copies (Worked examples, how-tos, Templates, Example projects)
  keeps "no abstraction to study first" and its allowance for repetition. The Toolbox's insides
  and `tools/` follow the job table instead.
- **The job table** in `docs/agents/standards.md`: each recurring job and its one function. From
  the survey (2026-10-30): a list in prose (five ways today, `refusals.in_words` the most used),
  a plural (26 inline, though `project._counted` exists), a quoted Python value (four ways),
  splitting `db.table` (seven ways), raising a refusal (five ways, and some errors skip the
  four-part message), dropping duplicates (two `_once`), and `git_hash` and two more copied
  between `checks.py` and `tools/export_clean.py`. Only jobs that are truly the same.
- **Names.** A function that only returns a value is named for what it returns
  (`refusal_text`); one that acts (writes, sends, refuses) starts with a verb. Every private
  name is unique across the Toolbox (four `_listed` today, each a different job). A prefix
  means one thing everywhere: `read_` reads a file, `check_` returns nothing and refuses on a
  failure, `is_`/`has_` return a bool. Public names keep theirs (phase 2 changes none).
- **No clever one-liners.** No nested or chained conditional expression; no
  `next(gen, default)` (a plain loop, or a named function); a comprehension has one `for`, at
  most one `if`, and no comprehension inside it; no walrus; `or`/`and` give bools, but
  `x or default` where `x` may be None or empty; a lambda only as a `key=`.
- **Each rule is held in one place.** ruff (pinned 0.15.17, already run by
  `tests/repo/test_toolbox_checks.py`, C901 at 10): add E501 at the 96 already set, SIM, C4,
  RET, and PLR0911, PLR0912 and PLR0915 at their defaults. A new repo test reads the tree for
  what ruff can't: a body of at most 50 lines, docstring left out; the one-liner rules; private
  names unique. `standards.md` holds only what neither can judge, such as whether a name says
  what it returns.
- **The new test starts with a list of what breaks it today**, written by the ticket, which
  may only shrink: a new break fails, and phase 2 empties the list.

### Phase 2: the refactor (tickets 02 to 09)

- **All of the Toolbox and `tools/`**, the user's choice: "I anticipate less lines of code under
  new standards that keep the review size small". Tests change only to follow a moved private
  name, so they stay an independent check.
- **No public name changes**, and nothing a user sees: proved by the suite and by a snapshot,
  taken first (02), of every Hive string and refusal message the Worked examples, how-tos,
  Example projects and eval references give, which each refactor commit must match.
- **One ticket per group of modules**, each a reviewable change, each emptying its part of
  ticket 01's list.

### Phase 3: Workflows (tickets 10 to 20)

#### The graph first (ticket 10)

- **One source.** Each Workflow's steps are plain data in the Toolbox: a step declares its start
  materials, its end artifacts, its kind, a function saying whether it is done, read from the
  Project's files, and the call that does it. No classes.
- **Three kinds of manual edge.** A **decision** needs the user's judgement (a `# CONVERSION:`
  risk, a partition to compare on): it can't go, so it is defaulted and gathered in one place.
  A **permission** is a Warehouse send the user calls on purpose (`run_execute`, `create()`,
  `write()`, `run_tables`, a seed): kept by design. **Fiddling** is typing what the code already
  knows, copying or pasting a file, uncommenting a call, or filling a placeholder a CREATE
  already answers: the target is zero.
- **`tools/workflow_graph.py`**, dev only, builds the graph from the declarations, adds the
  manual steps today's docs and refusals ask for, and reports every manual edge and every gap
  (an artifact a step needs that nothing makes). It writes `docs/workflows.md`, a Mermaid
  diagram per Workflow (text in markdown: GitHub and VS Code draw it, nothing loads), a test
  keeping it equal to what the tool writes. Ticket 10 maps today's Workflows as they are, the
  baseline fiddling count; each later ticket drives its count down, and a test fails while an
  intended Workflow has a fiddling edge.

#### The intended Workflows, by start materials and end artifacts

| Workflow | Start materials | End artifacts |
|---|---|---|
| convert | Hive scripts, the Dev Database's name, read access to their sources | per table they create, a dev Table folder: written in dev, compared with its original, every decision ticked |
| promote | dev Table folders whose decisions are ticked and compares passed, the Prod Database's name | generated prod Table folders, written in prod |
| new_table | a table name and what it should hold | a dev Table folder whose logic loads, written in dev, and its Table reference |
| references | table names the user's `query` can DESCRIBE | filled Table references, the Reference sheet, the Database modules |
| upgrade | a Project at an older version, the new Toolbox copied in | the Project at the new version, every `# UPGRADE` box ticked |
| change_a_saved_table | a Saved table and the change wanted | the change sent, logged, and its check passed |

"A good start" (the user): convert is the one that matters most.

#### The Project's layout (ticket 12)

- **Workflow-agnostic things stay in `admin/`**: the check (`check_project`, which also holds
  `do_next()`), `run_tables`, `refresh_reference_sheet`, `check_references`, one `remove`
  notebook for every `remove_*`, the Registry, the Admin log, `removed/`, and two new files:
  - **`admin/databases.py`**, `DEV = "..."` and `PROD = "..."`, written by `start()` with `<...>`
    to fill in, read by every Workflow so no call passes them; the check names it until filled;
  - **`admin/sent.csv`**, one row per Warehouse send (time, call, table, Workflow instance),
    appended by `run_tables` and the notebooks' `create()` and `write()`. A Warehouse step is
    done when its row is there: a filter over one small file, never a Warehouse call. The Admin
    log stays the human record.
- **Each Workflow in `admin/workflows/<name>/`**: `convert/` (taking in today's
  `conversions/`), `promote/`, `new_table/` (with `new_block`), `references/`, `upgrade/` (with
  `upgrade_<v>.md`), and `change_a_saved_table/`. Each holds its notebook, generated from its
  step list (one cell per step, its call written out, and a `do_next()` cell), and its named
  instances, one subfolder each (`convert/weekly/`); `upgrade` has none. The how-to of each
  Workflow is generated from the same list, so the two can't drift (the user: "do both and
  align documentation to code").
- **What belongs to one table travels with it**, in `tables/<t>/conversion/`: the statement it
  came from, its checklist items, its compare result. An instance folder is only the batch's
  index: the scripts as given, their order, the tables that came from them.
- **`project.check()` names each instance's next step**, and **`project.do_next()`** runs it when
  it changes only files; it stops before any Warehouse send, which the report names as a call
  ready to run. The status lives in `check()`, the call the user already runs: no new
  `status()`.
- **One or many, everywhere** (ticket 11): every Project action that takes a thing takes a str or
  a list of them, the same way, with one report for the batch; a batch that stops on one item
  names it and keeps those done. The user: "generalize patterns to assume multiple inputs
  across the board".

#### Convert (tickets 13 to 16)

- **n scripts in.** `project.convert("weekly", files=[...])` splits each script into its
  statements and orders every statement of the batch by what reads what.
- **Names.** Each table a script creates becomes a Saved table in the Dev Database named
  `<table>_<its database>` (`ops_reports.weekly_events` becomes `<dev>.weekly_events_ops_reports`),
  and every later statement that reads it reads that Saved table, never the original. The user:
  "Other jobs run on the original tables so I can't assume data integrity by swapping creates
  with references to the original tables." Tables a script only reads are read in place.
- **Collisions.** The same table created twice in a batch is more writes to one table, noted on
  the checklist. Two different tables with the same dev name refuse before anything is written,
  naming both, with `rename={...}` on the call as the way out.
- **What each statement becomes** (the user: "assume all"):

  | In the script | Becomes |
  |---|---|
  | `CREATE TABLE … AS SELECT` | a dev Saved table, its columns from the query |
  | `CREATE TABLE (cols) PARTITIONED BY …`, then `INSERT` | one dev Saved table: the CREATE gives columns, types and Partitions, the INSERT the logic |
  | `INSERT OVERWRITE/INTO` a table the batch didn't create | a dev Saved table named by the rule, its columns from DESCRIBE of the original |
  | `CREATE TEMPORARY TABLE` | a dev Saved table like any other, marked temporary on the checklist |
  | `CREATE VIEW` | a dev Saved table, marked "was a view" |
  | `DROP TABLE IF EXISTS` | nothing (the Saved table's `create()` covers it), noted on the checklist |
  | `TRUNCATE`, then `INSERT INTO` | an INSERT_OVERWRITE |
  | `SET` | the Session settings of the tables after it |
  | `ALTER TABLE … ADD PARTITION`, `MSCK REPAIR` | nothing (`write()` manages Partitions), listed |
  | anything else | an Unchecked statement, its names swapped |

- **Many out, many in.** A multi-insert (`FROM src INSERT OVERWRITE TABLE a … INSERT OVERWRITE
  TABLE b …`) gives one Saved table per target. Several statements writing one table give one
  Saved table whose logic stacks the pieces in script order.
- **A table that reads itself** (an incremental `INSERT INTO t … WHERE dt > (SELECT MAX(dt) FROM
  t)`) gets a seed step, a permission: copy the original's rows into the dev copy once, then run
  as written, so the compare means something.
- **References out.** Table references for the sources, from DESCRIBE, as today, and one for each
  dev table it creates, from the CREATE's columns, types and Partitions (a CTAS's from its
  query): no `<COLUMN_TYPE>`, the Key unset unless the script makes it plain.
- **Table folders directly.** The names are known, so the Conversion writes
  `tables/<dev>__<table>/` itself; `finish_conversion` retires.
- **Nothing blocks.** A statement it can't convert becomes an Unchecked statement in its own
  notebook, names swapped, listed; the batch goes on. Each decision gets the default that keeps
  the original's rows, gathered on one checklist; what a CREATE answers is filled in, never a
  placeholder.
- **Running it again.** `convert(...)` rewrites a file the user hasn't touched, keeps one they
  edited and writes the fresh one beside it, listed on the checklist; `convert(..., overwrite=
  True)` replaces everything, archiving first. Edits are told apart by the hash each file had
  when written. No interactive asking: the user ruled out a menu ("wrapping this in a just makes
  the scalability worse").
- **The steps**: (1) `convert(...)`, a file step; (2) the checklist, the user's, done when every
  box is ticked, blocking nothing in dev; (3) `run_tables(<its tables>, execute=execute)`, a
  permission; (4) a compare per table with its original on the latest partition both have, found
  through `query`, the user's as an override, a permission; (5) done: the instance moves to
  `admin/workflows/convert/finished/<name>/` and the check stops listing it.

#### Promote (ticket 17)

- **`project.promote(tables)`**, a Project action: a generated prod copy of each dev Table folder,
  and every notebook among them that reads another names its prod copy. Dev stays the source:
  re-promoting replaces the prod copy, archiving the old; a prod folder is never edited by hand,
  and the check reports one that is. The `_<their db>` suffix stays unless the call renames.
- **It refuses** a table whose checklist has a box unticked, whose compare hasn't passed, or that
  reads a dev table not promoted with it, naming each.
- The user (2026-10-30): "I have two dbs that I own, a dev and a prod, so I can default to dev
  and make the purposful decision to carry over the prod name in to the code."

### Words

Each lands in CONTEXT.md with the ticket named.

- **Dev Database** (12): the Database the user owns for tables still being built and checked,
  where a Conversion puts every table it creates. **Prod Database**: the one the user owns for
  tables other people rely on; a table reaches it only by the user's choice. _Avoid_: sandbox,
  scratch database, staging, home database.
- **Workflow** (10): an ordered list of steps that takes a Project to one end goal. Each step
  knows whether it is done, read from the Project's files, and which call does it. Checking the
  Project names the first step not done in each Workflow; a step that changes only files can be
  run for the user, one that touches the Warehouse never is. _Avoid_: wizard, menu, pipeline,
  recipe, playbook.
- **Conversion** (13, 14): reads one or more scripts of Hive, and writes a Table folder per table
  they create, in the Dev Database, named `<table>_<its database>`, with Table references for
  what they read. **Conversion folder** becomes the batch's index in `admin/workflows/convert/`.
  _Avoid_ as now.
- **Promotion** (17): a Project action that copies one or more Saved tables' code from the Dev
  Database to the Prod Database. _Avoid_: deploy, release, convert to prod, publish.
- **Project action** (11, 12): the list in its entry, and "one or many".

## Tickets

Phase 1, the standard:

- [01 The standard, the ruff rules, and the test with its shrinking list](issues/01-the-standard.md)

Phase 2, the refactor, no version raise:

- [02 The snapshot of every Hive string and refusal message](issues/02-the-snapshot.md)
- [03 The job table's functions](issues/03-the-job-tables-functions.md)
- [04 Refactor: refusals, conditions, calculations, kinds, keys, describe](issues/04-refactor-checks-and-columns.md)
- [05 Refactor: clauses, windows, joins, stacking](issues/05-refactor-clauses.md)
- [06 Refactor: writing, engine, trees, converting](issues/06-refactor-writing-and-reading.md)
- [07 Refactor: tables, admin, upkeep, unchecked, python_steps](issues/07-refactor-tables-and-admin.md)
- [08 Refactor: project, project_files, notebooks, upgrades, checks, project_templates](issues/08-refactor-project.md)
- [09 Refactor: lineage, comparisons, running, example_database, public, `__init__`, and tools/](issues/09-refactor-the-rest.md)

Phase 3, Workflows, 8.0:

- [10 The Workflow graph, docs/workflows.md, and today's baseline](issues/10-the-workflow-graph.md)
- [11 One or many: every Project action takes a list](issues/11-one-or-many.md)
- [12 The admin layout: databases.py, sent.csv, admin/workflows/, check() and do_next()](issues/12-the-admin-layout.md)
- [13 A Conversion reads n scripts: statements, order, names, references](issues/13-n-scripts.md)
- [14 A Conversion writes Table folders, a checklist, and runs again safely](issues/14-table-folders-and-the-checklist.md)
- [15 Multi-inserts, many writes to one table, and a table that reads itself](issues/15-many-in-many-out.md)
- [16 The compare step](issues/16-the-compare-step.md)
- [17 Promotion](issues/17-promotion.md)
- [18 The other four Workflows with no fiddling](issues/18-the-other-four-workflows.md)
- [19 The docs and the Copilot files](issues/19-the-docs.md)
- [20 8.0: the Upgrade step and the raise](issues/20-eight-point-oh.md)

One at a time, by number, the user's habit. The real dependencies are in each ticket's
`Blocked by:`.

## Records this changes

- `docs/agents/standards.md`, `pyproject.toml`'s ruff rules, a new repo test (01).
- CONTEXT.md, ticket by ticket, as "Words" says.
- CLAUDE.md: this map (with the map); the admin layout (12); 8.0 (20).
- `docs/workflows.md` (10), the README, the how-tos, the Worked examples, the Example projects,
  and Copilot file 07 (19); CHANGES.md's `## 8.0` (11 onward).

## Decisions so far

- [01 The standard, the ruff rules, and the test with its shrinking list](issues/01-the-standard.md):
  Simple over short, the job table (`shared.*`), names and plain expressions in standards.md;
  ruff adds E501, SIM, C4, RET and three PLR limits; the tree test and ruff count against
  `tests/repo/known_breaks.py`, by file and rule, which only shrinks; long lines wait for phase 2.
- [02 The snapshot of every Hive string and refusal message](issues/02-the-snapshot.md): recorded
  while the suite runs, at the four places the Toolbox makes text; `tests/snapshot/known.txt`
  holds 4,653 hashes after its review, and `SNAPSHOT_WRITE=1` writes it only from a whole, passing
  run.
- [03 The job table's functions](issues/03-the-job-tables-functions.md): `sqlglot_composer/shared.py`
  (`in_words`, `counted`, `singular_or_plural`, `python_literal`, `split_table_name`); every
  caller moved onto it; `tools/lower_known_breaks.py` lowers the list after a fix.
- [10 The Workflow graph, docs/workflows.md, and today's baseline](issues/10-the-workflow-graph.md):
  `sqlglot_composer/workflows.py` lists each Workflow's steps by kind; `tools/workflow_graph.py`
  draws `docs/workflows.md`; baseline fiddling 17 (convert 11); done-checks land with ticket 12.

## Not yet specified

- Which partition a compare uses when the original has none in common with the dev copy (16).
- How an Unchecked statement's names are swapped when its Hive can't be parsed at all (13).

## Out of scope

- Renaming a public name in phases 1 and 2; refactoring tests beyond a moved private name.
- An interactive menu, `input()` prompts, or a command line.
- `do_next()` sending anything to the Warehouse.
- A Project-wide dev/prod switch: Promotion writes the prod name into the code, by the user's
  choice.
- Reading the Warehouse to learn whether a step is done.

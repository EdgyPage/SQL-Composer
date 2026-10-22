# Toolbox 7.0: query and execute, no days, Databases, and docs with one flow

Label: wayfinder:map

The user (2026-10-21) tried the Clean branch and came back with notes, grilled the same day. They
want strong seams that don't need the code read: a `send` whose contract they had to dig out,
and a column they couldn't find how to select, are the two places it failed them. They asked
for:

- the warehouse reached through two calls, as their work's API has: `execute`, which gives back
  no DataFrame, and `query`, which does;
- Lineage that shows where a change made in Python lives, without modelling what it does;
- a column of a Table reference reached as database, table and column, whose text drops into a
  hand-written SELECT;
- the day assumption gone from everywhere ("distracting and annoying and incorrect"): different
  tables have different partitions, not every table has a Key, and they create a table with a
  `SET` and a `CREATE ... LOCATION` path they work out themselves;
- most of all, the how-tos, the Example projects and the Templates reworked: they were told to
  make files from prose alone, and the guide was "internally inconsistent with no flow to it".

They first asked for Python 3.13, then: "pin the venv to 3.12". Nothing changes there: `.venv`
is 3.12.10 and `requirements.txt` already pins every package for 3.12.

## Notes

### The version

- **7.0, a major version**, the user's choice ("v7"). Ticket 01 raises it. CHANGES.md's
  `## 7.0` has a "To update from 6.x" part that grows with each ticket: `send.py`, every
  `date_partition=`, every `write_day` and every `send=` change in the user's own files. No
  export until the whole of 7.0 is done; ticket 08 is the first cut if 7.0 runs long.
- **The glossary lands with the ticket that makes it true**, not ahead of the code: each ticket
  says which CONTEXT.md entries it rewrites, in the words grilled on 2026-10-21. A glossary ahead
  of the code would open a drift item on every commit until 7.0 is done. The ADRs, 0011 and
  0012, record decisions, so they land in 01.

### Toolbox 7.1: tickets 09 to 11

- **09 to 11 are Toolbox 7.1**, the user's call (2026-10-22): "Make sure this is version 7.1".
  7.0 is dev as d3c0a93 left it, and stays as CHANGES.md's `## 7.0` says; 09 raises the version
  to 7.1 and writes CHANGES.md's `## 7.1`, with "To update from 7.0".

### The warehouse calls (ADR 0012)

- **`send` is removed, not deprecated.** The user: "deprecate Send in favor of Execute and Query
  so I don't get confused". The Project's `send.py` becomes `warehouse.py`, holding two
  functions only: `query(hive: str) -> pd.DataFrame` and `execute(hive: str) -> None`.
- **No wrapper object.** The user asked what a `Warehouse` holding both was worth over the two
  functions; one argument saved isn't worth a type to learn. Each Toolbox function takes, as
  keyword arguments, only the calls it uses, so its signature says what it needs:
  `check_key(t, query=query)`, `run(s, query=query, execute=execute)`.
- **The user picks the call** (2026-10-22, reversing 02's routing; ticket 09):
  `run_query(s, query)` and `run_execute(s, execute)` replace `run`. Each refuses the plain
  mix-up, saying which to call, and never sends to the other call. `unchecked_hive(text)` takes
  no `returns_rows=`. The user: "Decision logic inside the wrapper is too complex for this
  project." 
- **`send=` anywhere is the Toolbox's refusal**, naming `query=` and `execute=`, not Python's
  TypeError; `project.check()` reports a `send.py` with no `warehouse.py`.

### No days (ADR 0011)

- **A table's partitions are its own**, of any kind, or none (the user: "different tables have
  different partitions"). `date_partition=` and `date_format=` go; `partitioned_by=[...]` stands
  alone.
- **The Load limit on reads**: a read of a partitioned table that filters none of its partition columns
  is refused; `reads_all_partitions=True` opts out. An unpartitioned table is never limited.
  "At both ends" and `set_load_limits(dates=...)` go.
- **Writes**: dynamic partitions by default, `PARTITION(region, load_id)` from the rows' own
  values, replacing only the partitions the rows hold, with the settings that needs added as
  `show_hive` adds them now; static with `partition={"region": "EU"}`. Each notebook's `write()`
  picks `INSERT_OVERWRITE` or `INSERT_INTO`; a Table reference holds no write mode. The day
  Guards and `by_day` go.
- **The Key is optional** (the user: "not every table has keys"). No Key: a write isn't checked
  and needs no `unproven_key=True`; a join onto the table keeps its repeated-rows Warning, with
  `many_matches=True`; `add_references` still writes `key=None  # TODO`, which may stay.
- **`run_tables()` takes no day.** A notebook's logic defines `write()`, which takes nothing; a
  value it needs is a constant in its notebook's first cell.
- **`location=` is used exactly as written.** The user builds paths "on my own in a throwaway
  easy to configure config file". The Toolbox adds no folder, needs no absolute path (so
  `${hivevar:root}/mart.db/team_day` is fine, its `SET` sent with `hive_settings`), and keeps
  one check: two Saved tables can't name one folder.
- **Kept**: external tables only, ORC unless the reference says Parquet, no TRUNCATE or MERGE.
- **Changed**: `repair_partitions` and `compute_statistics(t, partition={...})` work on any
  partitioned table; `admin.drop_partitions(t, where=...)` replaces `admin.drop_days`.
- **`check_key` reads what `where=` picks** (the user, 2026-10-21, asked when 03 was
  planned): `check_key(t, query=..., where=...)`. On a partitioned table, leaving `where=`
  out is refused as any unbounded read is, unless `reads_all_partitions=True`; an
  unpartitioned table is checked whole.
- **Lineage draws nothing extra for a write into partitions** (the user, 2026-10-21):
  partition columns are traced as any copied or calculated column is, and a static
  `partition={...}` is one line on the write's box, such as "writes region = EU".
- **Day helpers stay as plain helpers**: `last_n_days`, `between`, `week_start` and
  `month_start` on any date column, compared as written.

### Databases and the text of a table

- **`from references import ops`, then `ops.jobs.job_id`**: a Database is one object whose
  attributes are its tables, in a `references/__init__.py` the Project actions keep current, never
  written by hand. Each Table reference stays its own file, as 6.0 settled; Aliases stay beside
  their table.
- **JupyterLab 4 is where the user writes**, so tab completion is the kernel's, through
  `__dir__`, at each step; nothing is written for an editor that doesn't run the code.
- **Text, never three parts**: Hive refuses `ops.jobs.job_id` in a SELECT. A column's text stays
  `jobs.job_id`; a table's becomes `ops.jobs AS jobs`, so `f"SELECT {ops.jobs.job_id} FROM
  {ops.jobs}"` is Hive that runs. The f-string is the one way: an Unchecked statement stays one
  opaque step over whole tables in Lineage.

### Python steps

- **Declare-only.** The user: "not an important feature ... if this is severely out of scope,
  push back". The Toolbox moves no data; the user saves the DataFrame with their own API and
  declares `python_step(add_margin, reads=[...], writes=table)`. Lineage shows one opaque box
  naming the function's file, name and line, read from the function itself.

### The docs

- **A file map in the README**: every file of a Project, who makes it (which Project action),
  and what the user fills in. After 06, the user makes by hand only the Project folder and the
  copied Toolbox folder.
- **The chain of types, early**: Table, Column, Condition, Clause, Statement, the Hive `str`, the
  DataFrame, each with the call that makes the next, in README step 3 and atop the how-tos; each
  how-to labels the type of each value it makes (the user: "modelling the expected type flow
  inside the howto is a helpful idea").
- **One story**: README step N is Getting started how-to N, each going on from the Starter
  Example project as the step before left it. Intermediate how-tos stay a menu, each starting
  from the Intermediate Example project. Every how-to works inside a Project.
- **About 25 how-tos from 40**, one way to do each job: the repeats found on 2026-10-21 merge
  (1 and 4; 10 to 13; 13 and 26; 14 to 16; 2 and 3, the hand-written reference made
  Intermediate), and the day how-tos (12, 13, 22 to 25) become one, "Rewrite some partitions".
- **An edit is shown as the file after it**, under a heading naming the file; the test applies
  it out of sight. No `Path.write_text` on the page.
- **Links by name, never by number**, so a renumbering breaks nothing.
- **Every public docstring opens with an example call**, and a refusal of a wrong argument names
  the arguments that function takes.

## Tickets

- [01 Version 7.0 and the ADRs](issues/01-version-7-0-and-the-adrs.md)
- [02 query and execute replace send](issues/02-query-and-execute-replace-send.md)
- [03 Tables have no days](issues/03-tables-have-no-days.md)
- [04 The Example database, the Templates and the Example projects](issues/04-the-example-database-the-templates-and-the-example-projects.md)
- [04 The Example database, the Templates and the Example projects](issues/04-the-example-database-the-templates-and-the-example-projects.md):
  nine tables of three kinds; Templates saved_table and quality_checks (READS, PARTITION_COLUMN);
  Example projects rebuilt; the Starter notebooks to follow the Template plainly (ticket 07).
- [05 Databases and the text of a table](issues/05-databases-and-the-text-of-a-table.md)
- [06 new_block and check_references](issues/06-new-block-and-check-references.md)
- [07 The docs rework](issues/07-the-docs-rework.md)
- [06 new_block and check_references](issues/06-new-block-and-check-references.md): new_block and
  remove_block; register adopts a hand-made block; start() run again adds what a Project lacks;
  check_references.ipynb reads the Reference sheet.
- [07 The docs rework](issues/07-the-docs-rework.md): 26 how-tos, README step N is Getting started
  how-to N through the Starter project; the file map and the chain of types; file blocks; every
  public docstring opens with an example.
- [08 Python steps](issues/08-python-steps.md)
- [09 You pick query or execute](issues/09-you-pick-query-or-execute.md): run_query and
  run_execute replace run; returns_rows= goes; admin.check_the_copy.
- [10 One answer to a Statement's kind](issues/10-one-answer-to-a-statements-kind.md): the
  architecture review's candidate 1, built with 09.
- [11 One notebook reader](issues/11-one-notebook-reader.md): the architecture review's
  candidate 2; load's refusal of a broken notebook.

The order is the user's (2026-10-21): one at a time, each blocked by the one before, since 02 to
06 share `project.py`, `running.py`, `tables.py` and the Templates, and 07 writes about the shape
the others leave. 03 and 04 are the largest: `date_partition` alone is named 169 times in 14
Toolbox files and 198 times in 23 test files.

## Records this changes

- CONTEXT.md, ticket by ticket: Warehouse, Level and How-to (02); Table reference, Key, Saved
  table, Admin statement, Partition, Statistics and Template, and Date partition removed (03);
  Database (05); Python step (08); the Toolbox version's example 7.0 (01). Each ticket holds the
  words.
- `docs/adr/0011-tables-have-no-days.md` and `docs/adr/0012-query-and-execute.md` (01), drafted
  with this map; ADRs 0004, 0005 and 0007 name them in their Status lines.
- `docs/clean-branch-readme.md`, the how-tos, the gallery and both Example projects (07, and
  wherever an earlier ticket breaks one).

## Decisions so far

- [01 Version 7.0 and the ADRs](issues/01-version-7-0-and-the-adrs.md): 7.0 everywhere the
  current version is named; ADRs 0011 and 0012 in, 0004, 0005 and 0007 pointing to them;
  CHANGES `## 7.0` waits for the later tickets.
- [02 query and execute replace send](issues/02-query-and-execute-replace-send.md): warehouse.py
  holds query and execute; run picks one per step (the move's count step reads through query);
  returns_rows= has no default; `send=` is refused by `**removed`; both calls raise on failure.

- [03 Tables have no days](issues/03-tables-have-no-days.md): partitioned_by= for any table; a
  read filters one partition column; writes dynamic or partition={...}; Key optional;
  run_tables() and write(); location= as written; every write needs a Saved table.
- [05 Databases and the text of a table](issues/05-databases-and-the-text-of-a-table.md): one
  generated module per Database, references/<db>.py (not one __init__.py), so a broken reference
  breaks only its Database; str(table) is `ops.jobs AS jobs`.
- [08 Python steps](issues/08-python-steps.md): python_step(fn, reads=, writes=) declares a
  pandas change; Lineage names its file, function and line; run_tables passes over it; how-to 41.

## Not yet specified

- Nothing.

## Out of scope

- Python 3.13: the user chose to stay on 3.12.
- The Toolbox moving pandas data into the warehouse: Python steps are declared only.
- The Toolbox choosing between query and execute (09 took it out).
- A `Warehouse` wrapper, and a `send` kept beside `query` and `execute`.
- Three-part column names in Hive text, and building any Saved table's path.
- A second form of Unchecked statement that takes Columns, and column-level Lineage through one.
- Completion for editors that don't run the code (Pylance, PyCharm).
- Managed tables, TRUNCATE and MERGE (ADR 0007 stands there).

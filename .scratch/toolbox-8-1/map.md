# Toolbox 8.1: Decisions in place of hand edits, and a runner for each Workflow

Label: wayfinder:map

The user (2026-10-31), with 8.0 built on dev and CI passing, before exporting it: "I want to
examine the workflows in detail. I want to minimize all manual fiddling. Let's look for
opportunities to set up paramters with placeholder code and variables or iron out the the
workflows to enabled programatic workflows. The workflow graps should provide a clue on wwhat
the intended paths are supposed to be." Grilled the same day, 20 questions, every one settled.
Then: "does this flow match the core functions of handing of sql code to become a maintained
referenced table, converting and referencing many to many tables as a long sql statement?",
which added staging tables (Q18) and a referenced end (Q19). The user named the version 8.1.

8.0 isn't exported yet: "do not push to main at the end, I have another round of changes
planned". Whether 8.0 is exported before 8.1 starts, or 8.1 ships with it, is the user's call.

## Notes

### Where 8.0 left the Workflows (2026-10-31)

Six Workflows, 24 steps (`sqlglot_composer/workflows.py`, drawn in `docs/workflows.md`). Each
decision step today means opening a generated file and editing it:

| Workflow | Step done by hand | What the user does |
|---|---|---|
| convert | 2. Tick each checklist box | per table: each `# CONVERSION:` mark, each type written "string" as a guess, `location=`, the Key, sending the SET lines; then edit `checklist.md` to tick each box |
| promote | 2. Fill in each prod `location=` | edit each prod Table reference |
| new_table | 2. Fill in the Table reference | each column and type, `partitioned_by`, the Key, `location` |
| new_table | 3. Write the logic | eight kinds of `<...>` in the Template's notebook |
| references | 2. Fill in TODO lines | the Key, `does_not_add_up`, a line saying what one row is |
| change_a_saved_table | 1. Write the Admin statement | `where=...` in a code cell |
| upgrade | 2. Each UPGRADE mark | needs the user: stays as it is |

new_table's preview and change_a_saved_table's `show_hive` have `done=None`, so `do_next()`
always stops at them. `do_next()` never sends anything.

### Tests that run the Workflows (ticket 01, first)

The user, while the map was written (2026-10-31): "be sure to add tests that actually test the
workflows". 8.0's tests check one step at a time (`tests/test_workflow_steps.py`, the done
functions, each Project action); nothing runs a Workflow from its start materials to its end
goal as the user does. So, before anything changes:

- **A journey per Workflow**, `tests/test_workflow_journeys.py`: each starts a Project, fills
  in the Workflow notebook's names cell as a user types it, and runs the notebook's code cells
  top to bottom, the notebook the Project ships, not a copy of its calls, with `query` and
  `execute` the Example database's. Each ends by asserting its end goal, read from the
  Warehouse and the files: convert, each dev table written and compared, the Batch finished;
  promote, each prod table written and in the Reference sheet; new_table, the dev table
  written; references, each Table reference and the Reference sheet; change_a_saved_table,
  the change sent and logged; upgrade, no mark left.
- **The user's own case as a journey**: a long script, CTEs, CREATE statements, a staging table,
  a FROM with several INSERTs, into Databases the user can't write to, through convert, promote
  and referenced: the journey the map's second question asked about.
- **Every hand edit counted.** A journey may edit only its notebook's names cell, and, from 02,
  its decisions cell. Each other edit it needs today, a file opened and changed or a box
  ticked, is a named step in the journey, listed in a known-fiddling list in the test file,
  which only shrinks, as `tests/repo/known_breaks.py` does: a new hand edit fails, and each
  ticket that removes one removes it from the list. At 8.1 the list holds only upgrade's marks.
- **One source of steps.** The user, the same day: "be sure the documentation on the copilot
  files including listed steps is cohesive and correct". A repo test holds each Workflow's
  steps the same everywhere they are listed: `workflows.py`, its notebook, `docs/workflows.md`,
  the README, how-to 29 and Copilot file 13, all generated from the first; and each step's call
  a hand-written Copilot file or how-to quotes a call of today's steps. It runs on 8.0's docs
  first (01), and 12 reads every Copilot file again as one story once 8.1 changes the steps.
- **Through the runner too** (07): each journey is run a second way, as one
  `project.run_workflow(...)` call, and once with `dry_run=True`, which must send nothing.

### Decisions (Q1, Q2, Q9, Q10, Q11, Q12)

- **A Decision**, the new word (see Words): one thing about one table that only the user
  decides, which the table's files show made or not. Every box any Workflow asks for is one of
  seven kinds, each a question the files answer:

  | Kind | Made when | Where |
  |---|---|---|
  | placeholder | no `<...>` left | new_table's Table reference and logic |
  | location | `location=` isn't None or `<...>` | convert, promote, new_table |
  | Key | `key=` is set, or None by the user's choice | convert, new_table, references |
  | guessed type | each column the Toolbox could only guess has the user's type | convert, new_table |
  | mark | no `# UPGRADE` line left | upgrade |
  | keep or fold | the user chose, for a table only its own Batch reads (Q18) | convert |
  | TODO | no `TODO:` line left | listed only: blocks nothing (Q12) |

  So the work is kinds by tables, never kinds by Workflows: each decision step waits on its
  kinds, for its instance's tables, through one shared done-check.
- **The decisions cell** (Q1, Q10): each Workflow notebook gets one beside its names cell,
  one dict per table, written pre-filled with the Toolbox's proposals, `"<...>"` where it has
  none: `DECISIONS = {"mart_dev.team_fails_mart": {"key": ["team", "dt"], "location": "<...>",
  "types": {"fails": "int"}}}`. A file step writes each answer into the table's files. The
  user's answer, not an edit of a generated file, is how a Decision is made.
- **The cell wins over what the Toolbox wrote; a file the user changed by hand is kept and
  reported** (Q11), as a Batch run again keeps one today (its `fresh/` copies).
- **`checklist.md` stays, generated and read-only** (Q9): each Decision of the table, made or
  open, written again each time the Decisions are read. It is never ticked by hand.
- **TODO lines block nothing** (Q12): a line saying what one row is, or `does_not_add_up`, is
  documentation; check() lists them.

### Location stays the user's (Q3)

"keep this manual for now. the fixed structiure is going to be user/dir/db/table, I think
assuming the table dir should be the table name should remain a human decision." So nothing
proposes a location: it is a Decision with no proposal, answered in the decisions cell. No
location pattern in `admin/databases.py`.

### The Key, proposed (Q4)

- The Toolbox already works a Key out of a Statement (`keys.py`, ADR 0005): the GROUP_BY
  columns it returns; none with rollup, cube, grouping_sets, or a UNION_ALL; a column WHERE
  holds to one value, or one another Key column decides, left out; a nested grouping decided by
  the outer one; a row_number(...) a second Key. Its Key is the proposal, the first when there
  are two, the other named beside it; None when it finds none.
- `check_key` confirms the Key against the dev copy, after its write and before the compare:
  a Key the rows break fails the step, naming the rows.

### What stops blocking (Q5, Q6, Q13)

- **`# CONVERSION:` marks block nothing** (Q5): each opt-out a Conversion added keeps the
  original's rows, and the compare step proves them. The marks stay in the logic, listed in
  `batch.md` and the checklist view, for the user to change only if they want to.
- **The original's SET lines are sent by the write step** (Q6): `run_tables` sends a table's
  Session settings before its write, so no box asks for it.
- **A step that only prints blocks nothing** (Q13): new_table's preview, and
  change_a_saved_table's `show_hive`. The runner prints each on the way; check() lists them as
  "read this". change_a_saved_table's check that its Check first line names stays a step.

### The runner (Q7, Q16)

- `project.run_workflow(workflow, *, query, execute, dry_run=False)` runs one Workflow's steps
  in order, from its names and decisions cells, its calls to the Warehouse included: the user
  chose to send by passing `execute`. It stops at an open Decision, or at a failure, naming the
  instance, the step and what to do; run again, the done-checks skip what is done, so it resumes
  where it stopped.
- `dry_run=True` sends nothing: it prints each step and the Hive each call would send.
- One instance or many (Q16), as 8.0's Project actions take one name or many: a names cell's
  NAME or TABLES may be a list, each run in turn.
- `do_next()` stays as it is: file steps only, never sending.

### new_table, from the logic and from a query (Q8, Q14, Q17)

- **The Table reference comes from the logic** (Q8): the steps swap, logic first, then a file
  step writes the Table reference from it: its columns from the SELECT, their types from the
  Table references it reads (a type it can't tell a guessed-type Decision), `partitioned_by`,
  the Key (Q4) and `location` (a Decision).
- **New table from a query** (Q14): the names cell takes the query as Hive, in a .hql file or as
  text, and the converter builds its logic in Toolbox code: "convert a query that doesn't exist
  yet". No `<...>` to fill in. The Template's notebook stays for a table started by hand.
- **Made in dev, promoted** (Q17): such a table is made in the Dev Database, `<DEV>.<table>`,
  and promoted like a Conversion's, so every new Saved table takes the same path: dev, checked,
  promoted. A new table from a query is a Batch of one.

### Staging tables (Q18)

- A table a long script writes and only its own Batch reads, such as a CREATE TEMPORARY, or a
  scratch CREATE ... AS read later and DROPped at the end, is a keep-or-fold Decision. Folded,
  it becomes a Derived table in each table that reads it: never created, written, compared or
  promoted. Kept, it is a Saved table, as today.
- The proposal is fold for a TEMPORARY table or one the Batch DROPs, keep otherwise.
  `converting._create_note` notes "was a temporary table" today, and nothing more.
- Not yet specified: a staging table written by several statements (stacked), or with
  Partitions its reader filters, may not fold into one Derived table; settled while building
  (10), keeping it a Saved table where it can't.

### Referenced and maintained (Q19, Q20)

- **Promote's last step refreshes the Reference sheet and the Database modules** for the prod
  tables (Q19), a file step: the end goal, a table others reference, is reached in the Workflow.
- **The daily run stays `admin/run_tables.ipynb`** (Q20), outside the Workflows: a schedule is
  the user's platform's job.

### The version

- 8.1, the user's number (2026-10-31), raised by the last ticket (13) with its Upgrade step,
  as every raise does: a Project's Workflow notebooks gain their decisions cells, and an
  8.0 `checklist.md` with boxes ticked by hand carries its answers into the cell.
- **The glossary lands with the ticket that makes it true**, as 8.0's did. The word grilled on
  2026-10-31 is under Words.

### Words

- **Decision** (lands with 02):

  > **Decision**:
  > One thing about one table that only the user decides, which the table's files show made or
  > not: its Key, its location, a column type the Toolbox could only guess, a `<...>` left to
  > fill in, or, for a table only its own Batch reads, whether it is kept as a Saved table or
  > folded into each table that reads it as a Derived table. The user answers each in a
  > Workflow's notebook, beside its names cell, where the Toolbox shows its proposal when it has
  > one, and a Workflow's step that waits on Decisions is done once each is made. A Decision is
  > never ticked by hand: the files say whether it is made.
  > _Avoid_: box, checklist item, TODO

- **Workflow** gains "decisions cell" beside its names cell (02), and its fiddling count falls
  as the tickets land.

## Tickets

- [01 End-to-end tests of each Workflow, and the hand edits each needs today](issues/01-workflow-journeys.md)
- [02 Decisions: the kinds, the decisions cell, and one done-check](issues/02-decisions.md)
- [03 Writing Decisions into the files, and the checklist view](issues/03-writing-decisions.md)
- [04 The Key, proposed from the logic and checked in dev](issues/04-the-key-proposed.md)
- [05 What stops blocking: CONVERSION marks, TODO lines, steps that only print](issues/05-what-stops-blocking.md)
- [06 The write step sends the SET lines](issues/06-set-lines-sent.md)
- [07 The runner: run_workflow, one or many, dry_run](issues/07-the-runner.md)
- [08 new_table: the Table reference from the logic](issues/08-reference-from-the-logic.md)
- [09 new_table from a query, made in dev and promoted](issues/09-new-table-from-a-query.md)
- [10 Staging tables: keep or fold](issues/10-keep-or-fold.md)
- [11 Promote ends referenced: the Reference sheet and the Database modules](issues/11-promote-ends-referenced.md)
- [12 The docs and the Copilot files](issues/12-the-docs.md)
- [13 8.1: the Upgrade step and the raise](issues/13-eight-point-one.md)

One at a time, by number, the user's habit. The real dependencies are in each ticket's
`Blocked by:`.

## Records this changes

- `tests/test_workflow_journeys.py` and its known-fiddling list (01), shrinking with each
  ticket after it.
- CONTEXT.md: Decision, and Workflow's decisions cell (02).
- CLAUDE.md: this map (with the map); 8.1 (13).
- `docs/workflows.md`, the README, the how-tos, the Example projects and the Copilot files,
  file 13 most (12); CHANGES.md's `## 8.1` (02 onward).

## Decisions so far

(none yet)

## Not yet specified

- How a file shows a guessed type made: a mark on its line in the Table reference, read by the
  done-check, or the answer in the cell alone (02).
- How the cell tells `key=None` chosen from a Key not yet decided: None against `"<...>"` (02).
- Staging tables that can't fold into one Derived table (10).

## Out of scope

- A location pattern in `admin/databases.py`, or any proposed location (Q3).
- The Admin statement as names-cell inputs: it stays a code cell, `help(admin)` listing the
  choices (Q15).
- A seventh Workflow for the daily run, or scheduling (Q20).
- `do_next()` sending anything to the Warehouse: the runner sends, `do_next()` doesn't.
- An interactive menu, `input()` prompts, or a command line, as in 8.0.

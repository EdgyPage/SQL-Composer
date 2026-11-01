# Toolbox 8.2: the Workflows tested by people with no context, and the SQL in plain sight

Label: wayfinder:map

The user (2026-11-01), with 8.1 exported to main and pushed: "I want to increase usability of
the workflows. we need to create an iteration loop to go through workflows including the excel
to sql conversion steps. I'm thinking spawning fresh dumb subagents and testing if they can
actually complete the tasks and whther or not the workflow instructions are correct. The agents
get access to write code, fill out placeholders, etc, and read documentation." And: "I want to
be able to simply import and create tables from sql statements that create multiple tables and
use many ctes. I want to be able to hand off an excel document template to a non-technical user
and have them be able to convert their custom table views to correct sql and then add that sql
to to the tables." Grilled the same day, 13 questions, every one settled. The user named the
version 8.2.

## Notes

### How SQL becomes tables today (Q1, the user's first question)

The convert Workflow, `project.convert`, takes Hive as written, one query or long scripts with
CTEs, CREATE statements, staging tables and a FROM with several INSERTs (the long-script
journey, `tests/journeys/test_workflow_journeys.py`). Each table a script writes becomes a Table
folder in the Dev Database: a notebook whose logic cell builds the query from Toolbox Python,
`create()`, `write()` and `preview()` writing its Hive; a Table reference; and the original kept
as text in `conversion/statement.hql` and `in_dev.hql`, for comparing. `run_tables` sends the
CREATE and INSERT through the user's `execute`, so the tables land in Hive; `export_lineage`
writes each table's Lineage. The SQL is not stored as the table's definition: the Python is the
source of truth.

The user, Q1: "I want to be able to inspect the sql the python constructs at a glance. I trust
the toolbox to create the sql at runtime, but I want to be able to check my work." Q5: "a
function that creates the file I can include at runtime works." So (Q10): **`export_hive()`**,
a cell beside the lineage cell in each Table notebook, writes `<db>__<table>.hql` beside it:
`create()`, any `seed()`, the table's Session settings, then `write()`, in the order
`run_tables` sends them, under a header saying it is generated and edited in the notebook.
`export_hive(statement)` writes one Statement's Hive. The saved_table Template and convert's
notebooks gain the cell; so do the Example projects' Table notebooks, a hand change listed in
`GAINED_BY_HAND`.

### The Excel path (Q2, Q3, Q6, Q7)

A non-technical user's "custom table view" is a Formula workbook's final Table, one no other
Table reads, which becomes a new Saved table (CONTEXT.md, Formula workbook; "custom table view"
is a word to avoid). The user, Q3: "fill out excel template, which may or may not include
multiple tables using different data sources ie a workbook with multiple Tables on multiple
worksheets, and then conert via copilot. I do not want to maintain a conversion module in the
Toolbox. I want to see if a user can read and understand instructions from a blank template.
You'll have to create some blank templates and fill them in using only instructions from
documentation to ensure nothing is missing or overlooked. I am giving these guides to
non-technical users."

The blank template is `copilot/formula_workbook.xlsx`, its Steps sheet the guide; the Hive
comes from Copilot files 11 and 12, never a Toolbox module. Q6: the same person adds the SQL to
the tables, through new_table's QUERIES ("assume yes for now. In reality, I would likely have
the non-technical user fill out the form and I'd handle the conversions"): one agent fills the
template, and a fresh agent, with no memory of it, converts and adds the tables. Q7: the
workbook's own values are the truth: each final Table's Saved table holds the rows that Table
shows, as `tools/excel_eval.py` already checks Copilot's Hive, now checked on the table in the
warehouse; each scenario has an answer key, written before any run.

### The loop (Q4, Q8, Q9, Q11, Q12)

- **Agents:** fresh, small models (Haiku) for every role, the Copilot stand-in too (Q4: "Make
  sure the models used to assist in handing off instructions are also dumb"). Roles: a
  zero-context technical user for a Workflow scenario; for an Excel scenario, a zero-context
  non-technical user who moves a presentation workbook into a copy of the blank template by its
  Steps sheet, then a fresh agent who converts it through Copilot and adds the tables.
- **What they read (Q9):** only what main ships, the Clean tree built into a temporary folder by
  the export's own builder each round: README, how-tos, Copilot files, the blank workbook, the
  Example projects. No dev tests, tools or `.scratch/`. The user: "I want to assume 0 context
  with non-technical users. They have access to documentation they likely won't read all the
  way through so they will search for help from documentation fed to copilot."
- **Asking for help (Q11):** an agent stuck ends its turn with a question; the loop starts a
  fresh Copilot stand-in loaded as a real user loads it (file 00, then the file it names),
  relays the answer, and resumes the agent. At most five questions a run; a run that needs more
  is stuck. Questions are counted beside passes: each is a gap in the docs.
- **Scoring:** each scenario's end goal, read from the warehouse that keeps each write
  (`tools/workflow_warehouse.py`) and the Project's files, against its answer key.
- **Rounds (Q8):** scenarios split dev and held out before any run; each dev scenario runs
  three times a round with fresh agents; fixes come from dev failures only, to what a user
  reads (README, how-tos, the Steps sheet, notebook text, refusals, Copilot files), and the
  user: "You have latitude to fix bugs while testing", so a Toolbox bug found is fixed too.
  Stop once every dev scenario passes three of three in two rounds running; held-out scenarios
  run once per version.
- **Scenarios (Q12):**

| Split | Workflow scenarios (a zero-context technical user) | Excel scenarios (non-technical, then a fresh agent converts) |
|---|---|---|
| dev | convert one script with CTEs; new table from its Template; new table from a query; references; change a Saved table | E1 one sheet of raw data with formulas; E2 two data sources on two sheets, joined; E3 a Power Query step and a Total Row |
| held out | convert a long script with staging, then promote; upgrade a Project left by 8.0 | E4 several final Tables across sheets, with Parameters and Keys |

  Each Excel scenario starts from a presentation workbook made for it, the user's own view.
  E3's Power Query can't be made with openpyxl, so its M code is written for the scenario and
  kept in the workbook file, where the agents and Copilot read it (the user: "Generate the code
  of power query and throw it in conversion process. Assume the model can access it from the
  file.").

### What a user reads is an exact process (the user, while 02 was built)

"keep in mind you are writing insructions in copilot instructions and the howtos and examples.
So these are machine readable and human readable. llms need support for processes and exact
step orders to prevent hallucinations." So every fix the rounds make (05) is written as
numbered steps, in the order they are done, naming each file, cell and call exactly. And: "you
have permission to edit and add documentation files within reason."

### Running a notebook (02)

The agents can't press Run, so `tools/notebook_runner.py`, copied into each run as
`run_notebook.py`, runs a notebook's code cells in turn as Run All does. Its `exec` is an
`ALLOWED` site of `tools/offline_policy.py`, the user's OK given 2026-11-01 ("A cell runner").
The warehouse a run's agents write to keeps its tables in a JSON file between processes
(`tools/workflow_warehouse.py`'s SavedWarehouse), since each notebook and script runs in a
process of its own.

## Tickets

- [01 export_hive: each table's SQL in a file beside its notebook](issues/01-export-hive.md)
- [02 The loop's harness: agents, relay, workspace, scoring](issues/02-the-loop-harness.md)
- [03 The scenarios and their answer keys](issues/03-scenarios-and-keys.md)
- [04 Round one: main's docs as they ship](issues/04-round-one.md)
- [05 Tuning rounds: fix what dev runs find](issues/05-tuning-rounds.md)
- [06 The held-out round](issues/06-held-out-round.md)
- [07 8.2: the docs, the Upgrade step and the raise](issues/07-eight-point-two.md)
- [08 A calculation's type, from what it reads](issues/08-calculation-types.md), found by 03
- [09 The Example database runs subtotals, and a group's column beside an
  aggregate](issues/09-example-database-subtotals.md), found by 03
- [10 A count written as a SUM converts to count_rows](issues/10-a-count-written-as-a-sum.md),
  found by 04
- [11 A conversion's files name the right notebook and
  database](issues/11-a-conversions-files-name-the-right-place.md), found by 04
- [12 project.check() names a Key still to answer](issues/12-check-names-an-open-key.md), found
  by 04
- [13 Hive with a literal list converts without guessed
  types](issues/13-copilots-hive-with-a-literal-list.md), found by 04
- [14 RENAME in the convert notebook's names cell](issues/14-rename-in-the-convert-notebook.md), found
  by 04
- [15 A CTE of rows typed in keeps its Key](issues/15-rows-typed-in-keep-their-key.md), found by
  05's round two
- [16 A subquery of rows typed in converts as a CTE of them does](issues/16-a-subquery-of-rows-typed-in.md),
  found by 06
- [17 Each SQL mapping a Conversion makes, tested](issues/17-each-sql-mapping-tested.md), for
  the goal's tests
- [18 Every doc to Microsoft's instruction rules, then every Workflow tested
  again](issues/18-docs-to-microsofts-instruction-rules.md), the user's ask
- [19 What ticket 18's round found, fixed, then everything tested
  again](issues/19-the-ticket-18-rounds-findings.md), the user's ask

One at a time, by number. 01 to 03 are built before any round, so round one measures the docs
as main ships them. A Toolbox bug a round finds gets a ticket of its own, numbered on.

## Records this changes

- `sqlglot_composer/`: `export_hive` (01), and what the rounds find (05).
- The Templates, convert's notebooks, the Example projects (01); the Steps sheet, the README,
  the how-tos and the Copilot files (05).
- CONTEXT.md: Formula workbook's final Table (already, 2026-11-01).
- CLAUDE.md: this map (with the map); 8.2 (07). CHANGES.md's `## 8.2` (01 onward).

## Decisions so far

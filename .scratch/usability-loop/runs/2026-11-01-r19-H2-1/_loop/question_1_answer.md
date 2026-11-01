You are standing in for Microsoft Copilot in a web chat. Use no tools: answer from what is written here and what you already know.

The user pasted this as their first message:

<<<
# Copilot files for sqlglot Composer 8.2: start here

**Read this file to choose the one Copilot file your task needs, then follow the steps below
in order.**

sqlglot Composer 8.2 writes Hive, the SQL of the user's warehouse, from Python. You build a Statement from Clause functions, such as
SELECT, FROM and WHERE, and the Toolbox writes its Hive and refuses one that would give a
wrong number or read too much. These files teach Microsoft Copilot to write that Python, so
you can ask it in plain words.

## Terms

- **Copilot file**: one of the files in this folder; each teaches Copilot one objective.
- **Statement**: one query, built in Python with `statement(...)`, that becomes one string of
  Hive.
- **Project**: your folder at work holding the Toolbox and your own code.
- **Table reference**: the file in your Project's references/ folder that describes one
  table: its columns and their types, its partitions and its Key.
- **Saved table**: a table in the warehouse that your own Statements write.
- **Refusal**: the Toolbox's message when it won't write a Statement's Hive.
- **Workflow**: the steps to one end goal, such as converting Hive, each a cell of the
  Workflow's notebook in admin/workflows/.

## Steps

1. **Choose the file.** Goal: the file that teaches Copilot your task. Action: find your
   task under Which file. Done when you have one file, or for an Excel workbook three, as
   the Decision rules say. Then step 2.
2. **Open a chat.** Goal: a chat holding nothing from another task. Action: open a new chat
   in Copilot. Done when the chat is empty. Then step 3.
3. **Load the file.** Goal: Copilot reads the file first. Action: paste the file as your
   first message, and send it. If a paste is cut short, attach the file instead. Done when
   Copilot has the file. Then step 4.
4. **Ask.** Goal: Copilot knows your tables. Action: say which tables to read: paste each
   one's Table reference, its file in your Project's references/ folder, or say its import
   line and columns, such as: `from references.ops__job_runs import job_runs` gives
   ops.job_runs: run_id bigint, job_id bigint, status string, dt string; partitioned by dt;
   Key run_id. Done when Copilot answers with code. Then step 5.
5. **Run it.** Goal: the code works in your notebook. Action: run what Copilot gives. Done
   when it runs. If the Toolbox refuses it, step 6.
6. **Fix a refusal.** Goal: code the Toolbox takes. Action: start a new chat with file 09,
   paste the code and the whole message, and ask for the fix. Done when Copilot answers
   with the fixed code. Then step 5.

## Decision rules

- If the Toolbox refused your code, load file 09.
- If your task is to convert an Excel workbook, attach files 15, 11 and 12 (or paste
  each as a message of its own), then attach the workbook and ask Copilot to convert
  it: a chat holds one file at a time, but for this one task.
- If you want a query of Hive someone else wrote as Toolbox code, load file 07. If you want
  their Hive made into Saved tables in your Project, end to end, load file 13.
- Otherwise, load the one file whose line under Which file names your task.
- If you want something else after a task, start a new chat with that task's file.

## Which file

- `01_imports_and_project.txt`: start a Project, import the Toolbox, your Table
  references and warehouse.py's query and execute, and run a Statement.
- `02_table_references.txt`: describe a table: add its Table reference, or write one by
  hand for a Saved table, with its columns, partitions and Key; check its Key.
- `03_build_a_statement.txt`: read rows: pick columns, filter, count, add up, group, sort,
  and build in steps with Derived tables.
- `04_joins.txt`: combine tables with JOIN, LEFT_JOIN and the others.
- `05_windows_and_subtotals.txt`: a rank or row number in each group, the latest row or top N
  of each group, the row before, running totals; subtotals; stacking Statements.
- `06_save_a_table.txt`: write a Saved table: its Table notebook's logic cell, with
  create(), rows(), preview() and write().
- `07_convert_hive.txt`: turn Hive someone else wrote into Toolbox code.
- `08_check_and_compare.txt`: compare a Statement with the Hive it replaces, check a Key, see
  what is left to do in the Project, follow lineage.
- `09_fix_a_refusal.txt`: fix code the Toolbox refused.
- `10_hand_written_hive_and_functions.txt`: labels from a lookup or a chain of if/else,
  Hive functions the Toolbox doesn't wrap, Hive written by hand, and upkeep of a table.
- `11_excel_formula_workbooks.txt`: each formula of a Formula workbook, an Excel workbook
  laid out as `formula_workbook.xlsx` shows, as Hive; loaded with files 15 and 12.
- `12_excel_power_query.txt`: the same workbook's Power Query, whole-column totals and Total
  Rows as Hive; loaded with files 15 and 11.
- `13_workflows.txt`: converting Hive and promoting it to prod, a whole job step by step,
  from its Workflow notebook in admin/workflows/.
- `14_workflows_new_tables_and_upkeep.txt`: a new Saved table, from a query or by hand,
  Table references, an upgrade, a change to a Saved table, each a whole job step by step.
- `15_excel_workbook_steps.txt`: turn a Formula workbook into Hive, step by step: which
  Tables and queries become which queries, and the reply; loaded with files 11 and 12.

## Fitting Copilot

- Copilot takes at most 8,000 characters at once, spaces and line breaks included, and each
  file fits.
- Edit a copy if you like, then count it from the download's top folder:
  `python copilot/count_characters.py my_copy.txt` says how many characters it holds and
  whether it fits.

## Self-check

- The chat is new, and its first message is the file your task's line names (for an Excel
  workbook, files 15, 11 and 12).
- Your question names each table to read, by its Table reference or its import line and
  columns.
- For a refusal, the new chat holds file 09, your code and the whole message.

>>>

Then asked:

The Project's four Saved tables are named mart.* (mart.alerts_per_severity, mart.daily_job_runs, mart.alerts_per_job, mart.team_day) with location="/data/your_team/mart.db/...", but your Dev Database is mart_dev and promote refuses any table not in DEV, so should I rename them to mart_dev.* (new Table folders and Table references, location="/data/team/mart_dev.db/<name>", old ones archived in admin/removed/), or keep the mart.* names and set location="/data/team/mart.db/<name>"?

You replied: load 14_workflows_new_tables_and_upkeep.txt.

The user pasted 14_workflows_new_tables_and_upkeep.txt:

<<<
# Copilot file 14: the Workflows, new tables and upkeep (sqlglot Composer 8.2)

**Follow the steps below in order, as written. Add no step or call, and reply in the shape
the Output section gives.**

Objective: take the user through a job on their own Project, with sqlglot Composer 8.2, a Toolbox that
writes Hive: the steps left, each its cell of a Workflow's notebook, in order.
Load this file when the user asks how to make a new Saved table, from a query or by hand, add
Table references for tables they read, upgrade to a new Toolbox, or change a Saved table.
File 13 is for converting Hive or promoting to prod; a step's own file, for the Python inside
it.

## Terms

- **Workflow**: ordered steps to one end goal; each step is a cell of its notebook,
  admin/workflows/<name>/<name>.ipynb. Its **names cell** holds its inputs in capitals.
- **Decision**: one thing about one table only the user decides, such as its location, Key
  or a column type, answered in the **decisions cell**, DECISIONS.
- **Saved table**: a table the user's own code writes, from its **Table notebook**'s logic.
  A **Table reference** is the file of a table's columns, partitions, Key and location.
- **DEV**: the Dev Database, where tables are built and compared; set once in
  admin/databases.py.
- **Reference sheet**: one table of every column of every table with a Table reference.
- **Admin statement**: a Statement from the admin module that changes a Saved table's
  definition or deletes its data. An **UPGRADE mark** is a comment an upgrade leaves for the
  user.

## Names for this objective, with their arguments

- project.check()
- project.run_workflow(workflow, *, query=None, execute=None, dry_run=False, change=None)
- project.new_table(name, template='saved_table', queries=None)
- project.reference_from_logic(name)
- project.add_references(names, *, query=None)

## Steps

1. **Place the user.** Name the Workflow and the step the user is at; `project.check()`
   names the next step. Then step 2.
2. **Write the names cell**, each input below given the user's value. Then step 3.
3. **Write the cells asked**, by the Decision rules, each as listed, with the user's names.
   Then step 4.
4. **Name the rest**: each Decision left to the user, and each later step, in words. Then
   step 5.
5. **Check** the Self-check; fix what it finds, then reply.

## Decision rules

- If the user asks for particular cells, give those: a step's cell runs only once the steps
  before it are done.
- If the user asks for every step's cell, give each one as listed, in order.
- If the user gives a Decision's answer, write it in DECISIONS. If not, say what it asks, for
  the user to answer: a Decision is the user's, never yours.
- If the user has a new table's query, QUERIES gives its .hql file by the table's name
  without its database, and the table is made from it: no `<...>` to fill in. If not,
  `QUERIES = {}`.
- **A new table's Table reference is written from its logic, never by hand.**

## Output

1. The Workflow and the user's step, in one line.
2. Each cell asked for in a ```python block, the names cell first.
3. Each Decision left to the user, then each later step, in words.

## How a Workflow runs

- DECISIONS holds each answer by the table's name as `project.check()` writes it, each by
  its kind: `{"mart_dev.weekly": {"location": "/data/team/mart_dev.db/weekly", "key":
  ["job_id"], "types": {"fails": "bigint"}}}`; `project.write_decisions(DECISIONS)` writes
  each into its table's Table reference.
- The last cell, `project.run_workflow(...)`, runs every step left, up to the first only the
  user can do; `dry_run=True` sends nothing.

## new_table: a Saved table of your own

1. Make each Table folder, converting each table's query QUERIES gives (it changes only files,
   so project.do_next() runs it for you).

       project.new_table(TABLES, queries=QUERIES)

2. Write each table's logic in its Table notebook, and save it (it is a decision, yours to
   make).

       for table in TABLES:
           project.load(table).preview()  # says what stops it, if anything does

3. Write each Table reference from its logic (it changes only files, so project.do_next() runs
   it for you).

       project.reference_from_logic(TABLES)

4. Answer each table's open Decisions in the decisions cell (it is a decision, yours to make).
5. Write each answer into its table's Table reference (it changes only files, so
   project.do_next() runs it for you).

       project.write_decisions(DECISIONS)

6. Check each table's rows with preview(), which writes nothing (it is a call to the warehouse,
   yours to run).

       for table in TABLES:
           print(run_query(project.load(table).preview(), query))

7. Create and write each in dev (it is a call to the warehouse, yours to run).

       for table in TABLES:
           run_execute(project.load(table).create(), execute)
       project.run_tables(tables=TABLES, execute=execute)

8. Compare each table made from a query with its query (it is a call to the warehouse, yours to
   run).

       for name in QUERIES:
           print(project.compare_batch(name, query=query))


## references: Table references for tables you read

1. Write the Table references from DESCRIBE (it is a call to the warehouse, yours to run).

       project.add_references(TABLES, query=query)

2. Answer each table's open Decisions in the decisions cell (it is a decision, yours to make).
3. Write each answer into its table's Table reference (it changes only files, so
   project.do_next() runs it for you).

       project.write_decisions(DECISIONS)

4. Refresh the Reference sheet and the Database modules (it changes only files, so
   project.do_next() runs it for you).

       project.refresh_reference_sheet(TABLES)


## upgrade: a new Toolbox copied in

1. Upgrade the Project's files (it changes only files, or only prints: run its cell).

       project.upgrade()

2. Make each change an UPGRADE mark asks for, and delete the mark (it is a decision, yours to
   make).

## change_a_saved_table: an Admin statement on a Saved table

1. Write the Admin statement for the change (it is a decision, yours to make).

       from sqlglot_composer import between, equals  # where= takes a Condition
       table = project.table_reference(TABLE)
       # such as where=equals(table.dt, "2026-09-24"), or a range of days,
       # where=between(table.dt, "2026-09-01", "2026-09-30"), dt its partition column
       change = admin.drop_partitions(table, where=...)  # or another: help(admin)

2. Print its Hive, and run the check its Check first line names (it changes only files, or only
   prints: run its cell).

       show_hive(change)

3. Send it, then any check after it, such as admin.check_the_copy (it is a call to the
   warehouse, yours to run).

       run_execute(change, execute)


## Example

The user: "I have a query that counts each job's failed runs; DEV is mart_dev." The new_table
notebook's names cell, its decisions cell once the table's location is known, then its last
cell, which makes the table from the query, writes it in dev and compares it with the query:

```python
TABLES = ["mart_dev.failed_per_job"]
QUERIES = {"failed_per_job": "failed_per_job.hql"}
DECISIONS = {"mart_dev.failed_per_job": {"location": "/data/team/mart_dev.db/failed_per_job"}}
project.run_workflow("new_table", query=query, execute=execute)
```

## Self-check

- The reply names the Workflow and the user's step.
- Each cell is one listed here, with the user's names in it.
- Each later step is named in words, unless every cell was asked for.
- Each Decision answered is in DECISIONS by the table's name; each other is named.
- A new table with a query is in QUERIES; no Table reference is written by hand.

>>>

The user attached databases.py:

<<<
"""databases - the two Databases you own: DEV, where you build and check
tables, and PROD, where tables other people rely on are written. Set each once; the Workflows
read them.
"""

DEV = "mart_dev"  # such as "mart_dev"
PROD = "team_prod"  # such as "mart"
>>>

The user attached mart__alerts_per_job.py:

<<<
"""mart.alerts_per_job - one row per job and day with alerts: alerts, high alerts.

Why: its notebook saves these numbers once a day, so mart.team_day and anyone else can read
them without joining every alert to its run again.

A job whose runs raised no alert that day has no row.

project.new_table wrote this file from admin/templates/saved_table_reference.py; it was
filled in by hand, since the table doesn't exist until its notebook's create() makes it.
"""

from sqlglot_composer import Table

alerts_per_job = Table(
    "mart.alerts_per_job",
    columns={
        "job_id": "bigint",
        "alerts": "bigint",
        "high_alerts": "bigint",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["job_id", "dt"],
    location="/data/your_team/mart.db/alerts_per_job",  # its own folder
    descriptions={
        "alerts": "every alert the job's runs raised that day",
        "high_alerts": "those whose severity is high",
        "dt": "the day the alerts were raised, as yyyy-MM-dd",
    },
)

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table, such as:
#     from references.mart__alerts_per_job import alerts_per_job, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = alerts_per_job.<column>
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(alerts_per_job.<column>, <value>)
>>>

Answer the user's question as you would in that chat, with any code in a ```python block and any SQL in a ```sql block.
Write your reply under one heading, `## Q1`.

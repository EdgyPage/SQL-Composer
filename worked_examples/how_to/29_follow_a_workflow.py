"""Follow a Workflow

For: Intermediate

## Goal

Do a whole job from its Workflow notebook, step by step, with nothing typed twice. A Workflow is
an ordered list of steps that takes a Project, your folder of scripts at work, from what you
bring to one end goal, such as converting scripts or promoting tables. Each Workflow has a
notebook in admin/workflows/, a folder for each, and each Workflow below is drawn and listed
from the steps its notebook runs. A Decision is one thing about one table that only you decide,
such as its location or its Key, the columns whose values name exactly one row.

## When you'd use it

- If you start one of the jobs below, follow its Workflow's notebook, as the steps below do.
- If you don't know which step of a Workflow comes next, run `project.check()`: it names the
  next step of each Workflow you have started.
- If you want every step left run for you, run the notebook's last cell,
  `project.run_workflow(...)`, in place of the steps' cells: it runs every step left, the calls
  to the warehouse too, up to the first only you can do: a Decision, or a check of what a step
  printed.
- If you haven't sent anything yet, run `project.run_workflow(...)` with `dry_run=True` first:
  it sends nothing through your execute and says the Hive each step would send. It runs for real
  convert and the references Workflow's first step, which read DESCRIBE, and each step that
  changes only files up to the first that would send; after that it names each such step, "would
  run: ...", and runs none.
- If you want only the steps that change files run, run `project.do_next()`.
- If you have no Project yet, do [Start a Project](#start_a_project) first.

## Steps

### 1. Start a Project

Goal: a Project whose admin/workflows/ folder holds a notebook for each Workflow, each waiting
for its names cell:

>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/ and warehouse.py.
Next: set conn, your connection, in warehouse.py.

Done when `project.start()` says it started a Project. Then step 2.

### 2. Choose the Workflow for your job

Goal: the one Workflow whose end goal is yours. Each Workflow is described after these steps,
with its chart, its names cell and its steps.

- If you want a Workflow that turns Hive someone else wrote, one query or a batch of scripts,
  into your own code, choose convert: admin/workflows/convert/convert.ipynb.
- If you want a Workflow that carries Saved tables from your Dev Database to your Prod Database,
  choose promote: admin/workflows/promote/promote.ipynb.
- If you want a Workflow that makes a Table folder for each new Saved table, choose new_table:
  admin/workflows/new_table/new_table.ipynb.
- If you want a Workflow that writes a Table reference for each table your Project reads, from
  its DESCRIBE, choose references: admin/workflows/references/references.ipynb.
- If you want a Workflow that carries the Project's files to the Toolbox you copied in, once you
  have restarted the kernel, choose upgrade: admin/workflows/upgrade/upgrade.ipynb.
- If you want a Workflow that changes a Saved table in the warehouse with one of the admin
  module's Admin statements, each logged in admin/admin_log.md, choose change_a_saved_table:
  admin/workflows/change_a_saved_table/change_a_saved_table.ipynb.

In each chart, a plain box is a step that changes only files, or only prints; a box with double
edges a call to the warehouse, yours to run; a diamond a decision, yours to make; and a box with
round corners something a step needs or makes.

Done when you know the notebook to open. Then step 3.

### 3. Open its notebook

Goal: the notebook whose cells run your job's steps. Each Workflow notebook starts by finding
the Project, then imports what its steps call:

    from sqlglot_composer import (
        admin,
        hive_settings,
        project,
        run_execute,
        run_query,
        show_hive,
    )
    from warehouse import query, execute

Done when its first cells run without an error. Then step 4.

### 4. Fill in its names cell, and save it

Goal: the start materials the Workflow works on, named once. Write each name its names cell asks
for, as its Workflow's section below shows, and save the notebook.

Done when each name the cell asks for is filled in and saved. Then step 5.

### 5. Run its steps in order

Goal: the Workflow's end goal reached. Run each step's cell in turn, as its Workflow's section
below lists them, or its last cell in their place. At a step that is a decision, yours to make,
make it: write your answer to each open Decision in the decisions cell, beside the names cell,
and save it, or read what the step before printed. Then run the next step.

Done when `project.check()` says every step of the Workflow is done. Then check it worked,
below.

The Workflows, for steps 2 to 5:

### The convert Workflow

Turns Hive someone else wrote, one query or a batch of scripts, into your own code: each table
the scripts write becomes a Saved table in your Dev Database, with its Table folder, and what
only you can decide of it, a Decision, answered in the decisions cell.

Its chart, drawn from the steps of its notebook, admin/workflows/convert/convert.ipynb:

```mermaid
flowchart TD
    s0[["1. Convert the scripts: each table they write a Saved table in dev"]]:::warehouse_call
    s1{"2. Answer each table's open Decisions in the decisions cell"}:::your_decision
    s2["3. Write each answer into its table's Table reference"]:::files_only
    s3[["4. Create each table in dev"]]:::warehouse_call
    s4[["5. Seed each table that reads itself, once, from its original"]]:::warehouse_call
    s5[["6. Write each table in dev"]]:::warehouse_call
    s6[["7. Compare each table with its original"]]:::warehouse_call
    t0("Hive scripts"):::thing
    t1("your Dev Database's name"):::thing
    t2("read access to the sources"):::thing
    t3("a dev Table folder per table the scripts write"):::thing
    t4("a Table reference per table, each Script tag in its TAGS"):::thing
    t5("each answer in the decisions cell"):::thing
    t6("each answer written in"):::thing
    t7("each made in dev"):::thing
    t8("each seeded"):::thing
    t9("each written in dev"):::thing
    t10("each compared with its original"):::thing
    t0 --> s0
    t1 --> s0
    t2 --> s0
    s0 --> t3
    s0 --> t4
    t4 --> s1
    s1 --> t5
    t5 --> s2
    s2 --> t6
    t6 --> s3
    s3 --> t7
    t7 --> s4
    s4 --> t8
    t8 --> s5
    s5 --> t9
    t9 --> s6
    s6 --> t10
    classDef files_only fill:#e3f2e1,stroke:#4a8a3f
    classDef warehouse_call fill:#e1ecf7,stroke:#3f6a9a
    classDef your_decision fill:#fbf1d6,stroke:#a8842a
    classDef thing fill:#ffffff,stroke:#888888
```

Its names cell, which you fill in and save first:

    # the batch's name, plain lowercase, such as "weekly" (or, for the last cell alone,
    # a list of batches converted already)
    NAME = ''
    # the scripts' files, from this folder, such as ["daily.hql"], or [] to read HIVE
    FILES = []
    # the Hive as text, such as \"\"\"SELECT ...\"\"\", or None to read FILES
    HIVE = None
    # the database of a table the Hive names without one
    DATABASE = 'default'
    # a name of your own for a table's copy in dev, by the table's full name, such as
    # {"mart.team_fails": "team_fails"} for mart_dev.team_fails: left out, a copy is
    # <table>_<its database>, such as mart_dev.team_fails_mart
    RENAME = {}
    # each staging table convert names, kept or folded, such as {"ops_reports.failed":
    # "keep"}: left out, a temporary or DROPped one is folded, any other kept
    STAGING = {}

Its decisions cell, beside it, where you answer each open Decision:

    DECISIONS = {}  # your answer to each open Decision, by the table's name as
    # project.check() writes it, such as
    # {"mart_dev.weekly_ops": {"location": "/data/team/mart_dev.db/weekly",
    #                          "key": ["job_id"], "types": {"fails": "bigint"},
    #                          "tags": {"PERIOD_END": "'2026-10-31'"}}}
    # "key": None says no columns name one row. project.check() names each one open, and
    # prints a whole DECISIONS to paste over this line: fill in each <FILL IN>. A Key the
    # Toolbox proposed, marked # proposed in its Table reference, is kept unless you
    # answer "key" here.

Its steps, in order:

1. Convert the scripts: each table they write a Saved table in dev (it is a call to the
   warehouse, yours to run).

    project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                    rename=RENAME, staging=STAGING)

2. Answer each table's open Decisions in the decisions cell (it is a decision, yours to make).
3. Write each answer into its table's Table reference (it changes only files, so
   project.do_next() runs it for you).

    project.write_decisions(DECISIONS)

4. Create each table in dev (it is a call to the warehouse, yours to run).

    for table in project.batch_tables(NAME):
        run_execute(project.load(table).create(), execute)

5. Seed each table that reads itself, once, from its original (it is a call to the warehouse,
   yours to run).

    to_seed = project.batch_tables(NAME, seeded=True)
    if not to_seed:
        print("Seeded nothing: no table of the batch reads itself.")
    else:
        run_execute(hive_settings("dynamic_partitions"), execute)
        for table in to_seed:
            run_execute(project.load(table).seed(), execute)

6. Write each table in dev (it is a call to the warehouse, yours to run).

    project.run_tables(tables=project.batch_tables(NAME), execute=execute)

7. Compare each table with its original (it is a call to the warehouse, yours to run).

    project.compare_batch(NAME, query=query)


Its last cell runs every step left, in place of their cells:

    # Every step left, in place of their cells, up to the first only you can do.
    # Add dry_run=True to see the Hive it would send, sending nothing through your
    # execute: help(project.run_workflow) says the steps it still runs:
    project.run_workflow("convert", query=query, execute=execute)

### The promote Workflow

Carries Saved tables from your Dev Database to your Prod Database.

Its chart, drawn from the steps of its notebook, admin/workflows/promote/promote.ipynb:

```mermaid
flowchart TD
    s0["1. Promote each table: a prod copy of its folder and Table reference"]:::files_only
    s1{"2. Answer each prod table's open Decisions in the decisions cell"}:::your_decision
    s2["3. Write each answer into its prod table's Table reference"]:::files_only
    s3[["4. Create each table in prod"]]:::warehouse_call
    s4[["5. Seed each prod table that reads itself, once, from its original"]]:::warehouse_call
    s5[["6. Write each table in prod"]]:::warehouse_call
    s6["7. Refresh the Reference sheet and the Database modules"]:::files_only
    t0("dev Table folders, each Decision made and compared"):::thing
    t1("your Prod Database's name"):::thing
    t2("prod Table folders"):::thing
    t3("prod Table references"):::thing
    t4("each answer in the decisions cell"):::thing
    t5("each with its location="):::thing
    t6("each made in prod"):::thing
    t7("each seeded in prod"):::thing
    t8("each written in prod"):::thing
    t9("each in the Reference sheet"):::thing
    t0 --> s0
    t1 --> s0
    s0 --> t2
    s0 --> t3
    t3 --> s1
    s1 --> t4
    t4 --> s2
    s2 --> t5
    t5 --> s3
    s3 --> t6
    t6 --> s4
    s4 --> t7
    t7 --> s5
    s5 --> t8
    t8 --> s6
    s6 --> t9
    classDef files_only fill:#e3f2e1,stroke:#4a8a3f
    classDef warehouse_call fill:#e1ecf7,stroke:#3f6a9a
    classDef your_decision fill:#fbf1d6,stroke:#a8842a
    classDef thing fill:#ffffff,stroke:#888888
```

Its names cell, which you fill in and save first:

    # the dev tables, by their names in your Dev Database, such as
    # ["mart_dev.daily_job_runs"]
    TABLES = []

Its decisions cell, beside it, where you answer each open Decision:

    DECISIONS = {}  # your answer to each open Decision, by the table's name as
    # project.check() writes it, such as
    # {"mart_dev.weekly_ops": {"location": "/data/team/mart_dev.db/weekly",
    #                          "key": ["job_id"], "types": {"fails": "bigint"},
    #                          "tags": {"PERIOD_END": "'2026-10-31'"}}}
    # "key": None says no columns name one row. project.check() names each one open, and
    # prints a whole DECISIONS to paste over this line: fill in each <FILL IN>. A Key the
    # Toolbox proposed, marked # proposed in its Table reference, is kept unless you
    # answer "key" here.

Its steps, in order:

1. Promote each table: a prod copy of its folder and Table reference (it changes only files, so
   project.do_next() runs it for you).

    project.promote(TABLES)

2. Answer each prod table's open Decisions in the decisions cell (it is a decision, yours to
   make).
3. Write each answer into its prod table's Table reference (it changes only files, so
   project.do_next() runs it for you).

    project.write_decisions(DECISIONS)

4. Create each table in prod (it is a call to the warehouse, yours to run).

    for table in project.promoted_tables(TABLES):
        run_execute(project.load(table).create(), execute)

5. Seed each prod table that reads itself, once, from its original (it is a call to the
   warehouse, yours to run).

    to_seed = project.promoted_tables(TABLES, seeded=True)
    if not to_seed:
        print("Seeded nothing: no prod copy reads itself.")
    else:
        run_execute(hive_settings("dynamic_partitions"), execute)
        for table in to_seed:
            run_execute(project.load(table).seed(), execute)

6. Write each table in prod (it is a call to the warehouse, yours to run).

    project.run_tables(tables=project.promoted_tables(TABLES), execute=execute)

7. Refresh the Reference sheet and the Database modules (it changes only files, so
   project.do_next() runs it for you).

    project.refresh_reference_sheet(project.promoted_tables(TABLES))


Its last cell runs every step left, in place of their cells:

    # Every step left, in place of their cells, up to the first only you can do.
    # Add dry_run=True to see the Hive it would send, sending nothing through your
    # execute: help(project.run_workflow) says the steps it still runs:
    project.run_workflow("promote", query=query, execute=execute)

### The new_table Workflow

Makes a Table folder for each new Saved table: from its query, when QUERIES gives one, its logic
written for you; else from a Template, its logic for you to write. A Building block, a piece
several notebooks share, is made with project.new_block(...).

Its chart, drawn from the steps of its notebook, admin/workflows/new_table/new_table.ipynb:

```mermaid
flowchart TD
    s0["1. Make each Table folder, converting each table's query QUERIES gives"]:::files_only
    s1{"2. Write each table's logic in its Table notebook, and save it"}:::your_decision
    s2["3. Write each Table reference from its logic"]:::files_only
    s3{"4. Answer each table's open Decisions in the decisions cell"}:::your_decision
    s4["5. Write each answer into its table's Table reference"]:::files_only
    s5[["6. Check each table's rows with preview(), which writes nothing"]]:::warehouse_call
    s6[["7. Create and write each in dev"]]:::warehouse_call
    s7[["8. Compare each table made from a query with its query"]]:::warehouse_call
    t0("the tables' names"):::thing
    t1("a Table folder"):::thing
    t2("what each table should hold"):::thing
    t3("its logic"):::thing
    t4("its Table reference"):::thing
    t5("each answer in the decisions cell"):::thing
    t6("a dev Table folder whose logic loads"):::thing
    t7("its rows, checked"):::thing
    t8("written in dev"):::thing
    t9("each from a query compared with it"):::thing
    t0 --> s0
    s0 --> t1
    t1 --> s1
    t2 --> s1
    s1 --> t3
    t3 --> s2
    s2 --> t4
    t4 --> s3
    s3 --> t5
    t5 --> s4
    s4 --> t6
    t6 --> s5
    s5 --> t7
    t7 --> s6
    t4 --> s6
    s6 --> t8
    t8 --> s7
    s7 --> t9
    classDef files_only fill:#e3f2e1,stroke:#4a8a3f
    classDef warehouse_call fill:#e1ecf7,stroke:#3f6a9a
    classDef your_decision fill:#fbf1d6,stroke:#a8842a
    classDef thing fill:#ffffff,stroke:#888888
```

Its names cell, which you fill in and save first:

    # the new tables, by their names in the warehouse, such as
    # ["mart_dev.daily_job_runs"]
    TABLES = []
    # each table's query, by its name without its database, as Hive text or a .hql file
    # in admin/workflows/new_table/, such as {"daily_job_runs": "daily_job_runs.hql"}
    # for mart_dev.daily_job_runs: it is made in your Dev Database, its logic written
    # from its query
    QUERIES = {}

Its decisions cell, beside it, where you answer each open Decision:

    DECISIONS = {}  # your answer to each open Decision, by the table's name as
    # project.check() writes it, such as
    # {"mart_dev.weekly_ops": {"location": "/data/team/mart_dev.db/weekly",
    #                          "key": ["job_id"], "types": {"fails": "bigint"},
    #                          "tags": {"PERIOD_END": "'2026-10-31'"}}}
    # "key": None says no columns name one row. project.check() names each one open, and
    # prints a whole DECISIONS to paste over this line: fill in each <FILL IN>. A Key the
    # Toolbox proposed, marked # proposed in its Table reference, is kept unless you
    # answer "key" here.

Its steps, in order:

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


Its last cell runs every step left, in place of their cells:

    # Every step left, in place of their cells, up to the first only you can do.
    # Add dry_run=True to see the Hive it would send, sending nothing through your
    # execute: help(project.run_workflow) says the steps it still runs:
    project.run_workflow("new_table", query=query, execute=execute)

### The references Workflow

Writes a Table reference for each table your Project reads, from its DESCRIBE.

Its chart, drawn from the steps of its notebook, admin/workflows/references/references.ipynb:

```mermaid
flowchart TD
    s0[["1. Write the Table references from DESCRIBE"]]:::warehouse_call
    s1{"2. Answer each table's open Decisions in the decisions cell"}:::your_decision
    s2["3. Write each answer into its table's Table reference"]:::files_only
    s3["4. Refresh the Reference sheet and the Database modules"]:::files_only
    t0("table names your query can DESCRIBE"):::thing
    t1("Table references with TODO lines"):::thing
    t2("each answer in the decisions cell"):::thing
    t3("filled-in Table references"):::thing
    t4("the Reference sheet"):::thing
    t5("the Database modules"):::thing
    t0 --> s0
    s0 --> t1
    t1 --> s1
    s1 --> t2
    t2 --> s2
    s2 --> t3
    t3 --> s3
    s3 --> t4
    s3 --> t5
    classDef files_only fill:#e3f2e1,stroke:#4a8a3f
    classDef warehouse_call fill:#e1ecf7,stroke:#3f6a9a
    classDef your_decision fill:#fbf1d6,stroke:#a8842a
    classDef thing fill:#ffffff,stroke:#888888
```

Its names cell, which you fill in and save first:

    # the tables, by their names in the warehouse, such as ["mart.daily_job_runs"]
    TABLES = []

Its decisions cell, beside it, where you answer each open Decision:

    DECISIONS = {}  # your answer to each open Decision, by the table's name as
    # project.check() writes it, such as
    # {"mart_dev.weekly_ops": {"location": "/data/team/mart_dev.db/weekly",
    #                          "key": ["job_id"], "types": {"fails": "bigint"},
    #                          "tags": {"PERIOD_END": "'2026-10-31'"}}}
    # "key": None says no columns name one row. project.check() names each one open, and
    # prints a whole DECISIONS to paste over this line: fill in each <FILL IN>. A Key the
    # Toolbox proposed, marked # proposed in its Table reference, is kept unless you
    # answer "key" here.

Its steps, in order:

1. Write the Table references from DESCRIBE (it is a call to the warehouse, yours to run).

    project.add_references(TABLES, query=query)

2. Answer each table's open Decisions in the decisions cell (it is a decision, yours to make).
3. Write each answer into its table's Table reference (it changes only files, so
   project.do_next() runs it for you).

    project.write_decisions(DECISIONS)

4. Refresh the Reference sheet and the Database modules (it changes only files, so
   project.do_next() runs it for you).

    project.refresh_reference_sheet(TABLES)


Its last cell runs every step left, in place of their cells:

    # Every step left, in place of their cells, up to the first only you can do.
    # Add dry_run=True to see the Hive it would send, sending nothing through your
    # execute: help(project.run_workflow) says the steps it still runs:
    project.run_workflow("references", query=query, execute=execute)

### The upgrade Workflow

Carries the Project's files to the Toolbox you copied in, once you have restarted the kernel.

Its chart, drawn from the steps of its notebook, admin/workflows/upgrade/upgrade.ipynb:

```mermaid
flowchart TD
    s0["1. Upgrade the Project's files"]:::files_only
    s1{"2. Make each change an UPGRADE mark asks for, and delete the mark"}:::your_decision
    t0("a Project at an older version"):::thing
    t1("the new Toolbox copied in"):::thing
    t2("the Project at the new version"):::thing
    t3("UPGRADE marks"):::thing
    t4("every UPGRADE mark dealt with"):::thing
    t0 --> s0
    t1 --> s0
    s0 --> t2
    s0 --> t3
    t3 --> s1
    s1 --> t4
    classDef files_only fill:#e3f2e1,stroke:#4a8a3f
    classDef your_decision fill:#fbf1d6,stroke:#a8842a
    classDef thing fill:#ffffff,stroke:#888888
```

Its steps, in order:

1. Upgrade the Project's files (it changes only files, or only prints: run its cell).

    project.upgrade()

2. Make each change an UPGRADE mark asks for, and delete the mark (it is a decision, yours to
   make).

Its last cell runs every step left, in place of their cells:

    # Every step left, in place of their cells, up to the first only you can do.
    # Add dry_run=True to see the Hive it would send, sending nothing through your
    # execute: help(project.run_workflow) says the steps it still runs:
    project.run_workflow("upgrade")

### The change_a_saved_table Workflow

Changes a Saved table in the warehouse with one of the admin module's Admin statements, each
logged in admin/admin_log.md.

Its chart, drawn from the steps of its notebook,
admin/workflows/change_a_saved_table/change_a_saved_table.ipynb:

```mermaid
flowchart TD
    s0{"1. Write the Admin statement for the change"}:::your_decision
    s1[["2. Print its Hive, and run the check its Check first line names"]]:::warehouse_call
    s2[["3. Send it, then any check after it, such as admin.check_the_copy"]]:::warehouse_call
    t0("a Saved table"):::thing
    t1("the change wanted"):::thing
    t2("an Admin statement"):::thing
    t3("its Hive, read and checked"):::thing
    t4("the change sent"):::thing
    t5("the change logged"):::thing
    t0 --> s0
    t1 --> s0
    s0 --> t2
    t2 --> s1
    s1 --> t3
    t3 --> s2
    s2 --> t4
    s2 --> t5
    classDef warehouse_call fill:#e1ecf7,stroke:#3f6a9a
    classDef your_decision fill:#fbf1d6,stroke:#a8842a
    classDef thing fill:#ffffff,stroke:#888888
```

Its names cell, which you fill in and save first:

    # the Saved table to change, such as "mart.daily_job_runs"
    TABLE = ''

Its steps, in order:

1. Write the Admin statement for the change (it is a decision, yours to make).

    from sqlglot_composer import between, equals  # where= takes a Condition
    table = project.table_reference(TABLE)
    # such as where=equals(table.dt, "2026-09-24"), or a range of days,
    # where=between(table.dt, "2026-09-01", "2026-09-30"), dt its partition column
    change = admin.drop_partitions(table, where=...)  # or another: help(admin)

2. Print its Hive, and run the check its Check first line names (it is a call to the warehouse,
   yours to run).

    show_hive(change)
    print(query("SHOW PARTITIONS " + TABLE))

3. Send it, then any check after it, such as admin.check_the_copy (it is a call to the
   warehouse, yours to run).

    run_execute(change, execute)


Its last cell runs every step left, in place of their cells:

    # Every step left, in place of their cells, up to the first only you can do.
    # Add dry_run=True to see the Hive it would send, sending nothing through your
    # execute: help(project.run_workflow) says the steps it still runs:
    project.run_workflow("change_a_saved_table", query=query, execute=execute, change=change)

## Check it worked

Before you go on, check that:

- `project.check()` names the next step of each Workflow you have started, or says that every
  step is done;
- `project.check()` names no open Decision for the tables of the Workflow you ran.

## Common mistakes

### A step named again after you ran it

`project.check()` names a step no file tells of, such as change_a_saved_table's "Print its
Hive", until a later step is done, and says so: once you have run it, go on to the next step. A
step that only reads, such as new_table's preview, is never named on its own: check() names it
beside the step after it.

## Next

- Walk the convert Workflow through a batch of scripts: [Convert someone else's
  Hive](#convert_someone_elses_hive).
"""

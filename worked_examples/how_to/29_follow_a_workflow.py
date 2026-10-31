"""Follow a Workflow

For: Intermediate

## Goal

Do a whole job from its Workflow notebook, step by step, with nothing typed
twice: each Workflow below is drawn and listed from the steps its notebook
runs, in admin/workflows/, a folder for each.

## When you'd use it

Each time you start one of the jobs below. `project.check()` names the next
step of each Workflow you have started, and `project.do_next()` runs the steps
it can for you, up to the first that is yours.

It needs [Start a Project](#start_a_project).

## Steps

### Start a Project

Every Project has the Workflow notebooks, each waiting for its names cell:

>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/ and warehouse.py.
Next: set conn, your connection, in warehouse.py.

Each Workflow notebook starts by finding the Project, then imports what its steps call:

    from sqlglot_composer import (
        admin,
        hive_settings,
        project,
        run_execute,
        run_query,
        show_hive,
    )
    from warehouse import query, execute

### The convert Workflow

Turns Hive someone else wrote, one query or a batch of scripts, into your own code: each table
the scripts write becomes a Saved table in your Dev Database, with its Table folder and a
checklist.

Its chart, drawn from the steps of its notebook, admin/workflows/convert/convert.ipynb:

```mermaid
flowchart TD
    s0[["1. Convert the scripts: each table they write a Saved table in dev"]]
    class s0 permission
    t0 --> s0
    t1 --> s0
    t2 --> s0
    s0 --> t3
    s0 --> t4
    s1{"2. Tick each box of each table's checklist"}
    class s1 decision
    t4 --> s1
    s1 --> t5
    s2[["3. Create each table in dev"]]
    class s2 permission
    t5 --> s2
    s2 --> t6
    s3[["4. Seed each table that reads itself, once, from its original"]]
    class s3 permission
    t6 --> s3
    s3 --> t7
    s4[["5. Write each table in dev"]]
    class s4 permission
    t7 --> s4
    s4 --> t8
    s5[["6. Compare each table with its original"]]
    class s5 permission
    t8 --> s5
    s5 --> t9
    t0("Hive scripts")
    class t0 thing
    t1("your Dev Database's name")
    class t1 thing
    t2("read access to the sources")
    class t2 thing
    t3("a dev Table folder per table the scripts write")
    class t3 thing
    t4("a checklist per table")
    class t4 thing
    t5("each decision made")
    class t5 thing
    t6("each made in dev")
    class t6 thing
    t7("each seeded")
    class t7 thing
    t8("each written in dev")
    class t8 thing
    t9("each compared with its original")
    class t9 thing
    classDef file fill:#e3f2e1,stroke:#4a8a3f
    classDef permission fill:#e1ecf7,stroke:#3f6a9a
    classDef decision fill:#fbf1d6,stroke:#a8842a
    classDef fiddling fill:#f8d7d5,stroke:#b03a30
    classDef thing fill:#ffffff,stroke:#888888
```

Its names cell, which you fill in and save first:

    # the batch's name, plain lowercase, such as "weekly"
    NAME = ''
    # the scripts' files, from this folder, such as ["daily.hql"], or [] to read HIVE
    FILES = []
    # the Hive as text, such as \"\"\"SELECT ...\"\"\", or None to read FILES
    HIVE = None
    # the database of a table the Hive names without one
    DATABASE = 'default'

Its steps:

- 1. Convert the scripts: each table they write a Saved table in dev (a call to the warehouse,
  yours to run).

    project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE)

- 2. Tick each box of each table's checklist (a decision, yours to make).
- 3. Create each table in dev (a call to the warehouse, yours to run).

    for table in project.batch_tables(NAME):
        run_execute(project.load(table).create(), execute)

- 4. Seed each table that reads itself, once, from its original (a call to the warehouse, yours
  to run).

    run_execute(hive_settings("dynamic_partitions"), execute)
    for table in project.batch_tables(NAME, seeded=True):
        run_execute(project.load(table).seed(), execute)

- 5. Write each table in dev (a call to the warehouse, yours to run).

    project.run_tables(tables=project.batch_tables(NAME), execute=execute)

- 6. Compare each table with its original (a call to the warehouse, yours to run).

    project.compare_batch(NAME, query=query)


### The promote Workflow

Carries Saved tables from your Dev Database to your Prod Database.

Its chart, drawn from the steps of its notebook, admin/workflows/promote/promote.ipynb:

```mermaid
flowchart TD
    s0["1. Promote each table: a prod copy of its Table folder and Table reference"]
    class s0 file
    t0 --> s0
    t1 --> s0
    s0 --> t2
    s0 --> t3
    s1{"2. Fill in each prod Table reference's location="}
    class s1 decision
    t3 --> s1
    s1 --> t4
    s2[["3. Create each table in prod"]]
    class s2 permission
    t4 --> s2
    s2 --> t5
    s3[["4. Seed each prod table that reads itself, once, from its original"]]
    class s3 permission
    t5 --> s3
    s3 --> t6
    s4[["5. Write each table in prod"]]
    class s4 permission
    t6 --> s4
    s4 --> t7
    t0("dev Table folders, each box ticked and compared")
    class t0 thing
    t1("your Prod Database's name")
    class t1 thing
    t2("prod Table folders")
    class t2 thing
    t3("prod Table references")
    class t3 thing
    t4("each with its location=")
    class t4 thing
    t5("each made in prod")
    class t5 thing
    t6("each seeded in prod")
    class t6 thing
    t7("each written in prod")
    class t7 thing
    classDef file fill:#e3f2e1,stroke:#4a8a3f
    classDef permission fill:#e1ecf7,stroke:#3f6a9a
    classDef decision fill:#fbf1d6,stroke:#a8842a
    classDef fiddling fill:#f8d7d5,stroke:#b03a30
    classDef thing fill:#ffffff,stroke:#888888
```

Its names cell, which you fill in and save first:

    # the dev tables, by their names in your Dev Database, such as
    # ["mart_dev.daily_job_runs"]
    TABLES = []

Its steps:

- 1. Promote each table: a prod copy of its Table folder and Table reference (a file step, which
  do_next() runs for you).

    project.promote(TABLES)

- 2. Fill in each prod Table reference's location= (a decision, yours to make).
- 3. Create each table in prod (a call to the warehouse, yours to run).

    for table in project.promoted_tables(TABLES):
        run_execute(project.load(table).create(), execute)

- 4. Seed each prod table that reads itself, once, from its original (a call to the warehouse,
  yours to run).

    run_execute(hive_settings("dynamic_partitions"), execute)
    for table in project.promoted_tables(TABLES, seeded=True):
        run_execute(project.load(table).seed(), execute)

- 5. Write each table in prod (a call to the warehouse, yours to run).

    project.run_tables(tables=project.promoted_tables(TABLES), execute=execute)


### The new_table Workflow

Makes a Table folder for each new Saved table, for you to fill in and write. A Building block, a
piece several notebooks share, is made with project.new_block(...).

Its chart, drawn from the steps of its notebook, admin/workflows/new_table/new_table.ipynb:

```mermaid
flowchart TD
    s0["1. Make each Table folder"]
    class s0 file
    t0 --> s0
    s0 --> t1
    s0 --> t2
    s1{"2. Fill in each Table reference, in references/, and save it"}
    class s1 decision
    t2 --> s1
    s1 --> t3
    s2{"3. Write each table's logic in its Table notebook, and save it"}
    class s2 decision
    t1 --> s2
    t4 --> s2
    s2 --> t5
    s3[["4. Check each table's rows with preview(), which writes nothing"]]
    class s3 permission
    t5 --> s3
    s3 --> t6
    s4[["5. Create and write each in dev"]]
    class s4 permission
    t6 --> s4
    t3 --> s4
    s4 --> t7
    t0("the tables' names")
    class t0 thing
    t1("a Table folder")
    class t1 thing
    t2("its Table reference to fill in")
    class t2 thing
    t3("its Table reference")
    class t3 thing
    t4("what each table should hold")
    class t4 thing
    t5("a dev Table folder whose logic loads")
    class t5 thing
    t6("its rows, checked")
    class t6 thing
    t7("written in dev")
    class t7 thing
    classDef file fill:#e3f2e1,stroke:#4a8a3f
    classDef permission fill:#e1ecf7,stroke:#3f6a9a
    classDef decision fill:#fbf1d6,stroke:#a8842a
    classDef fiddling fill:#f8d7d5,stroke:#b03a30
    classDef thing fill:#ffffff,stroke:#888888
```

Its names cell, which you fill in and save first:

    # the tables, by their names in the warehouse, such as ["mart.daily_job_runs"]
    TABLES = []

Its steps:

- 1. Make each Table folder (a file step, which do_next() runs for you).

    project.new_table(TABLES)

- 2. Fill in each Table reference, in references/, and save it (a decision, yours to make).
- 3. Write each table's logic in its Table notebook, and save it (a decision, yours to make).

    for table in TABLES:
        project.load(table).write()  # says what stops it, if anything does

- 4. Check each table's rows with preview(), which writes nothing (a call to the warehouse,
  yours to run).

    for table in TABLES:
        print(run_query(project.load(table).preview(), query))

- 5. Create and write each in dev (a call to the warehouse, yours to run).

    for table in TABLES:
        run_execute(project.load(table).create(), execute)
    project.run_tables(tables=TABLES, execute=execute)


### The references Workflow

Writes a Table reference for each table your Project reads, from its DESCRIBE.

Its chart, drawn from the steps of its notebook, admin/workflows/references/references.ipynb:

```mermaid
flowchart TD
    s0[["1. Write the Table references from DESCRIBE"]]
    class s0 permission
    t0 --> s0
    s0 --> t1
    s1{"2. Fill in each TODO line and Alias"}
    class s1 decision
    t1 --> s1
    s1 --> t2
    s2["3. Refresh the Reference sheet and the Database modules"]
    class s2 file
    t2 --> s2
    s2 --> t3
    s2 --> t4
    t0("table names your query can DESCRIBE")
    class t0 thing
    t1("Table references with TODO lines")
    class t1 thing
    t2("filled-in Table references")
    class t2 thing
    t3("the Reference sheet")
    class t3 thing
    t4("the Database modules")
    class t4 thing
    classDef file fill:#e3f2e1,stroke:#4a8a3f
    classDef permission fill:#e1ecf7,stroke:#3f6a9a
    classDef decision fill:#fbf1d6,stroke:#a8842a
    classDef fiddling fill:#f8d7d5,stroke:#b03a30
    classDef thing fill:#ffffff,stroke:#888888
```

Its names cell, which you fill in and save first:

    # the tables, by their names in the warehouse, such as ["mart.daily_job_runs"]
    TABLES = []

Its steps:

- 1. Write the Table references from DESCRIBE (a call to the warehouse, yours to run).

    project.add_references(TABLES, query=query)

- 2. Fill in each TODO line and Alias (a decision, yours to make).
- 3. Refresh the Reference sheet and the Database modules (a file step, which do_next() runs for
  you).

    project.refresh_reference_sheet(TABLES)


### The upgrade Workflow

Carries the Project's files to the Toolbox you copied in, once you have restarted the kernel.

Its chart, drawn from the steps of its notebook, admin/workflows/upgrade/upgrade.ipynb:

```mermaid
flowchart TD
    s0["1. Upgrade the Project's files"]
    class s0 file
    t0 --> s0
    t1 --> s0
    s0 --> t2
    s0 --> t3
    s1{"2. Make each change an #35; UPGRADE mark asks for, and tick its box"}
    class s1 decision
    t3 --> s1
    s1 --> t4
    t0("a Project at an older version")
    class t0 thing
    t1("the new Toolbox copied in")
    class t1 thing
    t2("the Project at the new version")
    class t2 thing
    t3("#35; UPGRADE marks")
    class t3 thing
    t4("every #35; UPGRADE box ticked")
    class t4 thing
    classDef file fill:#e3f2e1,stroke:#4a8a3f
    classDef permission fill:#e1ecf7,stroke:#3f6a9a
    classDef decision fill:#fbf1d6,stroke:#a8842a
    classDef fiddling fill:#f8d7d5,stroke:#b03a30
    classDef thing fill:#ffffff,stroke:#888888
```

Its steps:

- 1. Upgrade the Project's files (a file step, which do_next() runs for you).

    project.upgrade()

- 2. Make each change an # UPGRADE mark asks for, and tick its box (a decision, yours to make).

### The change_a_saved_table Workflow

Changes a Saved table in the warehouse with one of the admin module's Admin statements, each
logged in admin/admin_log.md.

Its chart, drawn from the steps of its notebook,
admin/workflows/change_a_saved_table/change_a_saved_table.ipynb:

```mermaid
flowchart TD
    s0{"1. Write the Admin statement for the change"}
    class s0 decision
    t0 --> s0
    t1 --> s0
    s0 --> t2
    s1["2. Print its Hive, and run the check its Check first line names"]
    class s1 file
    t2 --> s1
    s1 --> t3
    s2[["3. Send it, then any check after it, such as admin.check_the_copy"]]
    class s2 permission
    t3 --> s2
    s2 --> t4
    s2 --> t5
    t0("a Saved table")
    class t0 thing
    t1("the change wanted")
    class t1 thing
    t2("an Admin statement")
    class t2 thing
    t3("its Hive, read and checked")
    class t3 thing
    t4("the change sent")
    class t4 thing
    t5("the change logged")
    class t5 thing
    classDef file fill:#e3f2e1,stroke:#4a8a3f
    classDef permission fill:#e1ecf7,stroke:#3f6a9a
    classDef decision fill:#fbf1d6,stroke:#a8842a
    classDef fiddling fill:#f8d7d5,stroke:#b03a30
    classDef thing fill:#ffffff,stroke:#888888
```

Its names cell, which you fill in and save first:

    # the Saved table to change, such as "mart.daily_job_runs"
    TABLE = ''

Its steps:

- 1. Write the Admin statement for the change (a decision, yours to make).

    table = project.table_reference(TABLE)
    change = admin.drop_partitions(table, where=...)  # or another: help(admin)

- 2. Print its Hive, and run the check its Check first line names (a file step, which do_next()
  runs for you).

    show_hive(change)

- 3. Send it, then any check after it, such as admin.check_the_copy (a call to the warehouse,
  yours to run).

    run_execute(change, execute)


## Check it worked

`project.check()` says each Workflow's next step, or that every step is done.

## Common mistakes

### A step named again after you ran it

A step no file tells of, such as a preview, is named until a later step is
done, and says so: once you have run it, go on.

## Next

[Convert someone else's Hive](#convert_someone_elses_hive) walks the convert
Workflow through a batch of scripts.
"""

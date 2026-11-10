"""Save a table

For: Getting started

## Goal

Keep a Statement's rows in a Saved table: a real table in the warehouse that your Project
writes, and that other Statements then read like any other table. A Statement is one query; a
Project is your folder of scripts at work, in the Toolbox's fixed layout. `project.new_table`
makes the table's Table folder, the folder that holds everything about one Saved table, with a
Table notebook in it, the notebook whose cells create and write the table, made from the
saved_table Template, the empty shape of such a notebook. It also makes the table's Table
reference, the file that describes the table's columns. You fill in both, try the notebook's
steps, and from then on `project.run_tables` writes the table with the Project's other Saved
tables.

## When you'd use it

- If a result is slow to work out, save it in a Saved table: working it out once is cheaper
  than working it out again every time someone asks.
- If many notebooks and dashboards read a result, save it in a Saved table, so each reads the
  rows already worked out.
- If you need each Partition's rows kept as they were when they were written, save them in a
  Saved table. A Partition is a slice of a table: the rows that share one value of each column
  the table is partitioned by, such as one day.
- If you only need the rows once, run the Statement with `run_query` instead, as
  [Build and run a first statement](#build_and_run_a_first_statement) shows.

The Example database, the small made-up tables this page runs on, can be read but not written
to. So on this page each write shows its Hive, ready to paste, and a write that is sent goes to
warehouse.py's execute, which here calls `example_database.execute`: it prints the write's
first line and changes nothing. At work, the same calls send it to your warehouse, through your
own execute.

## Steps

### 1. Set up the Project the last how-to left

Goal: a Project with the Table references the Saved table reads.

[Share Building blocks](#share_building_blocks) left the Project with its Table references
filled in and one Building block. The Saved table this how-to makes reads one table,
`ops.run_alerts`, so the calls below make the Project again with three Table references alone,
as `project.add_references` writes them:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/, scheduled_runs/ and warehouse.py.
Next: at the top of each notebook, fill in connect(...) with your connection.
>>> from warehouse import connect, query, execute
>>> connect(example_database)
>>> project.add_references(["ops.jobs", "ops.job_runs", "ops.run_alerts"], query=query)
Wrote references/ops__jobs.py, references/ops__job_runs.py and references/ops__run_alerts.py:
    fill in their TODO lines.
...
Wrote references/ops.py: from references import ops gives ops.job_runs, ops.jobs and
    ops.run_alerts.
Restart the kernel of a notebook that imported references, to see a table added since.

Done when `project.add_references` says it wrote the three Table references. Then step 2.

### 2. Make its Table folder

Goal: the table's Table folder, Table notebook and Table reference, each waiting to be filled
in.

The table is mart.alerts_per_severity: how many alerts of each severity, low or high, the runs
raised each day. `project.new_table` takes its name, its database first. A Workflow is an
ordered list of steps that takes a Project to one end goal; the new_table Workflow's notebook,
admin/workflows/new_table/new_table.ipynb, runs this call on the names in its names cell.
Calling it from any notebook of the Project does the same:

>>> project.new_table("mart.alerts_per_severity")
Made tables/mart__alerts_per_severity/: mart__alerts_per_severity.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__alerts_per_severity.py: project.reference_from_logic writes it.

It made four things, and listed two of them, the Table folder and the Table reference, in the
registry, the Project's list of everything a Project action made:

- tables/mart__alerts_per_severity/, the table's Table folder, named after the database and
  the table joined by two underscores;
- mart__alerts_per_severity.ipynb in it, the Table notebook, from the saved_table Template: a
  Saved table worked out from a table it reads, a count per group of the rows it reads;
- lineage/ beside it, empty until the notebook exports the table's Lineage;
- references/mart__alerts_per_severity.py, its Table reference. A Saved table doesn't exist
  until its notebook creates it, so nothing can be asked of it: this one stands in until
  `project.reference_from_logic` writes it from the logic you write.

Both hold `<...>` placeholders. Type over each in the notebook, brackets and all; the Table
reference's are written for you, once the logic is. Until you do, the notebook isn't Python
yet, and `project.load`, which runs a notebook's logic from anywhere in the Project, says which
line stops it:

>>> project.load("mart.alerts_per_severity")
Traceback (most recent call last):
...
ValueError:
  What happened:  project.load("mart.alerts_per_severity"): the logic cell of
                  tables/mart__alerts_per_severity/mart__alerts_per_severity.ipynb isn't Python
                  yet, at its line 9: from references.<SOURCE_NAME> import <SOURCE_TABLE>
...

Done when tables/mart__alerts_per_severity/ and references/mart__alerts_per_severity.py are
there. Then step 3.

### 3. Fill in its notebook

Goal: a Table notebook that says what the table reads and how it counts it.

Open the notebook in Jupyter. This is it as `project.new_table` wrote it, from the saved_table
Template, the table's database and name filled in, `<...>` everywhere else:

The file `tables/mart__alerts_per_severity/mart__alerts_per_severity.ipynb`, as project.new_table wrote it:

    # %% [markdown]
    # # mart.alerts_per_severity
    #
    # Fill in every `<...>` in the code cells below, brackets and all: the notebook won't run with
    # one left. They are:
    #   - `<SOURCE_NAME>` and `<SOURCE_TABLE>`: the table it reads, by its file in references/ and
    #     its name there, such as `ops__job_runs` and `job_runs`;
    #   - `<READS>`: which of its rows write() reads, as a condition on it, such as
    #     `equals(job_runs.dt, "2026-09-24")` or `equals(region_costs.region, "eu")`. On a
    #     partitioned table, it must filter one of its partition columns. A table that isn't
    #     partitioned can be read whole: delete the line `READS = <READS>` and each line
    #     `WHERE(READS),` instead;
    #   - `<GROUP_COLUMN>`: the column each row is for, such as `job_id`;
    #   - `<COUNT_NAME>`: the name of the count it saves, in quotes, such as `"runs"`;
    #   - `<PARTITION_COLUMN>`: the column of the table it reads that fills this table's partition
    #     column, such as `dt` or `region`. If this table isn't partitioned, delete the two lines
    #     of rows() naming `<PARTITION_COLUMN>`, and write `PARTITIONED_BY = []`, instead.
    #
    # ## Terms
    #
    # - **Logic**: the code cell that starts `# logic`, cell 2. It only imports and defines, so
    #   `project.load("mart.alerts_per_severity")` can run it from anywhere else, for lineage across your
    #   tables and for `admin/run_tables.ipynb`, which sends its `write()`.
    # - **Table reference**: `references/mart__alerts_per_severity.py`, the script describing this table: its
    #   columns and their types, its Partitions and its Key.
    # - **Partition**: the rows of a table that share one value of each column it is partitioned
    #   by.
    # - **Key**: the columns whose values name exactly one row of the table.
    # - **Decision**: one thing about this table that only you decide, such as its location; its
    #   Table reference says whether it is made.
    #
    # ## Steps
    #
    # 1. **Fill in each `<...>`.** Goal: logic that runs. Action: type over each one listed above,
    #    in the code cells. Done when no code cell holds a `<...>`; then step 2.
    # 2. **Save the notebook.** Goal: the logic its Table reference is written from. Action: save
    #    it. Done when it is saved; then step 3.
    # 3. **Write its Table reference.** Goal: a Table reference written from the logic. Action:
    #    run `project.reference_from_logic("mart.alerts_per_severity")`, a new_table Workflow step, which
    #    writes `references/mart__alerts_per_severity.py` from the logic, for you to answer.
    #    It lists the columns write() saves, in the order its SELECT gives them: here
    #    <GROUP_COLUMN>, typed as the table read types it, then <COUNT_NAME>, a count, "bigint",
    #    and last its partition column, if it has one, as PARTITIONED_BY names it. Its Key,
    #    proposed from the logic, is the column each row is for, and the partition column if it
    #    has one, such as key=["job_id", "region"].
    #    Done when `references/mart__alerts_per_severity.py` lists those columns; then step 4.
    # 4. **Answer its Decisions.** Goal: each Decision made. Action: answer each open Decision its
    #    Table reference leaves, such as its location, in the new_table Workflow's decisions
    #    cell. Done when its Table reference leaves no Decision open; then step 5.
    # 5. **Say what one row is.** Goal: a reader knows what the table holds. Action: write one
    #    line saying what one row of mart.alerts_per_severity is, in place of the TODO line below. Done when
    #    no TODO line is left in this cell; then step 6.
    # 6. **Run the cells.** Goal: the logic tried, its lineage and Hive written, and its rows in
    #    the Reference sheet. Action: run the code cells top to bottom, once its Table reference
    #    is written from the logic. Done when each runs with no error, and cell 3 shows the rows
    #    `preview()` gives.
    #
    # ## This table
    #
    # TODO: say in one line what one row of mart.alerts_per_severity is.
    #
    # A Saved table worked out from a table it reads: a count per group of the rows READS picks.
    # It is partitioned as PARTITIONED_BY says, or not at all.
    #
    # Made by `project.new_table("mart.alerts_per_severity")` from
    # `admin/templates/saved_table.py`, which filled in the database, the table and its file's name,
    # mart__alerts_per_severity.
    #
    # ## The code cells
    #
    # - 1: the Project, your connection, connected with `connect(...)`, and your query.
    # - 2: the logic, which starts `# logic`.
    # - 3: try it.
    # - 4: its lineage.
    # - 5: its Hive, in mart__alerts_per_severity.hql.
    # - 6: its rows in the Reference sheet.
    #
    # ## Self-check
    #
    # - No code cell holds a `<...>`.
    # - `references/mart__alerts_per_severity.py` lists the columns `write()` saves, and leaves no Decision open.
    # - One line above says what one row is, and no TODO line is left.
    # - Each code cell runs top to bottom with no error.


    # %%
    # 1. The Project and your query
    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

    from sqlglot_composer import export_hive, export_lineage, project, run_query, show_hive
    from warehouse import connect, query

    # Your connection to the warehouse. Each notebook runs on its own, so each connects here, at
    # its top, before it calls query or execute: write yours in the line below and delete its #,
    # such as connect(your_library.connect(...)). A connection kept in a file outside the Project,
    # such as team_connection.py, is imported by these lines, written in that line's place:
    #     sys.path.append("C:/work/connections")  # the folder team_connection.py is in
    #     from team_connection import conn
    #     connect(conn)
    # connect(your_connection)

    # %%
    # logic
    # 2. The logic: imports, the rows it reads, and functions only
    from sqlglot_composer import (
        AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Clause, Statement, count_rows,
        create_table, equals, statement,
    )
    from references.mart__alerts_per_severity import alerts_per_severity  # this table's own Table reference
    # each table it reads, such as: from references.ops__job_runs import job_runs
    from references.<SOURCE_NAME> import <SOURCE_TABLE>

    # The rows write() reads: change it to write others. A condition that calls something other
    # than equals, such as between or is_in, needs it added to the import above.
    READS = <READS>

    # This table's partition columns, in the order its SELECT gives them, last: [] for none.
    PARTITIONED_BY = ["<PARTITION_COLUMN>"]


    def create() -> Statement:
        \"\"\"Step 1: create mart.alerts_per_severity from its Table reference, if it isn't there yet.\"\"\"
        return create_table(alerts_per_severity, may_exist=True)


    def rows() -> list[Clause]:
        \"\"\"The clauses preview and write share, so the two can never disagree: a count per group
        of the rows READS picks.

        A partitioned table's partition columns come last in SELECT, in its Table reference's
        order, named as it names them: INSERT_OVERWRITE fills each Partition from the rows' own
        values, and replaces only the Partitions they fill. They stay in GROUP_BY too, so each
        Partition's rows stay apart.
        \"\"\"
        return [
            SELECT(
                <SOURCE_TABLE>.<GROUP_COLUMN>,  # what each row is for
                AS(count_rows(), <COUNT_NAME>),
                <SOURCE_TABLE>.<PARTITION_COLUMN>,  # this table's partition column, last
            ),
            FROM(<SOURCE_TABLE>),
            WHERE(READS),
            GROUP_BY(
                <SOURCE_TABLE>.<GROUP_COLUMN>,
                <SOURCE_TABLE>.<PARTITION_COLUMN>,  # kept, so each Partition's rows stay apart
            ),
        ]


    def preview() -> Statement:
        \"\"\"Step 2: the rows write() would save, as a SELECT to run and check first.\"\"\"
        return statement(*rows())


    def write() -> Statement:
        \"\"\"Step 3: save the rows, replacing the Partitions they fill, or the whole table if it
        isn't partitioned: sent twice, it leaves the same rows, not twice as many.\"\"\"
        return statement(INSERT_OVERWRITE(alerts_per_severity), *rows())

    # %%
    # 3. Try it: the Hive of each step, then the rows
    show_hive([create(), write()])
    run_query(preview(), query)

    # %%
    # 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
    export_lineage(write())

    # %%
    # 5. Its Hive: mart__alerts_per_severity.hql beside this notebook, from the logic as last saved
    export_hive()

    # %%
    # 6. The Reference sheet: this table's rows, from references/mart__alerts_per_severity.py
    project.refresh_reference_sheet("mart.alerts_per_severity")

Its text cell starts with a list of what each `<...>` is for. Type over each one in the code
cells. Then, in the text cell, put one line saying what a row is in place of the TODO line.
Once every step the text cell lists is done, you may cut it down to that line and what the
table is, as here. Here is the whole notebook, filled in, as it is in the Starter Example
project, a Project made for the Example database to read and copy from:

The file `tables/mart__alerts_per_severity/mart__alerts_per_severity.ipynb`, after you fill it in:

    # %% [markdown]
    # # mart.alerts_per_severity
    #
    # One row per severity and day: how many alerts of that severity the runs raised that day.
    #
    # A Saved table worked out from a table it reads: a count per group of the rows READS picks.
    # It is partitioned as PARTITIONED_BY says, or not at all.
    #
    # Made by `project.new_table("mart.alerts_per_severity")` from
    # `admin/templates/saved_table.py`, which filled in the database, the table and its file's name,
    # mart__alerts_per_severity. Run the cells top to bottom once both are filled in.
    #
    # The code cells: 1 the Project and your query, connected by `connect(...)`; 2 the logic,
    # which starts `# logic`; 3 try it; 4 its lineage; 5 its Hive, in mart__alerts_per_severity.hql;
    # 6 its rows in the Reference sheet.
    # The logic only imports and defines, so `project.load("mart.alerts_per_severity")` can run it
    # from anywhere else, for lineage across your tables and for `admin/run_tables.ipynb`, which
    # sends its `write()`.

    # %%
    # 1. The Project and your query
    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

    from sqlglot_composer import export_hive, export_lineage, project, run_query, show_hive
    from warehouse import connect, query

    # Your connection to the warehouse. Each notebook runs on its own, so each connects here, at
    # its top, before it calls query or execute: write yours in the line below and delete its #,
    # such as connect(your_library.connect(...)). A connection kept in a file outside the Project,
    # such as team_connection.py, is imported by these lines, written in that line's place:
    #     sys.path.append("C:/work/connections")  # the folder team_connection.py is in
    #     from team_connection import conn
    #     connect(conn)
    # connect(your_connection)

    # %%
    # logic
    # 2. The logic: imports, the rows it reads, and functions only
    from sqlglot_composer import (
        AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Clause, Statement, count_rows,
        create_table, equals, statement,
    )
    from references.mart__alerts_per_severity import alerts_per_severity  # this table's own Table reference
    # each table it reads, such as: from references.ops__job_runs import job_runs
    from references.ops__run_alerts import run_alerts

    # The rows write() reads: change it to write others. A condition that calls something other
    # than equals, such as between or is_in, needs it added to the import above.
    READS = equals(run_alerts.dt, "2026-09-24")

    # This table's partition columns, in the order its SELECT gives them, last: [] for none.
    PARTITIONED_BY = ["dt"]


    def create() -> Statement:
        \"\"\"Step 1: create mart.alerts_per_severity from its Table reference, if it isn't there yet.\"\"\"
        return create_table(alerts_per_severity, may_exist=True)


    def rows() -> list[Clause]:
        \"\"\"The clauses preview and write share, so the two can never disagree: a count per group
        of the rows READS picks.

        A partitioned table's partition columns come last in SELECT, in its Table reference's
        order, named as it names them: INSERT_OVERWRITE fills each Partition from the rows' own
        values, and replaces only the Partitions they fill. They stay in GROUP_BY too, so each
        Partition's rows stay apart.
        \"\"\"
        return [
            SELECT(
                run_alerts.severity,  # what each row is for
                AS(count_rows(), "alerts"),
                run_alerts.dt,  # this table's partition column, last
            ),
            FROM(run_alerts),
            WHERE(READS),
            GROUP_BY(
                run_alerts.severity,
                run_alerts.dt,  # kept, so each Partition's rows stay apart
            ),
        ]


    def preview() -> Statement:
        \"\"\"Step 2: the rows write() would save, as a SELECT to run and check first.\"\"\"
        return statement(*rows())


    def write() -> Statement:
        \"\"\"Step 3: save the rows, replacing the Partitions they fill, or the whole table if it
        isn't partitioned: sent twice, it leaves the same rows, not twice as many.\"\"\"
        return statement(INSERT_OVERWRITE(alerts_per_severity), *rows())

    # %%
    # 3. Try it: the Hive of each step, then the rows
    show_hive([create(), write()])
    run_query(preview(), query)

    # %%
    # 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
    export_lineage(write())

    # %%
    # 5. Its Hive: mart__alerts_per_severity.hql beside this notebook, from the logic as last saved
    export_hive()

    # %%
    # 6. The Reference sheet: this table's rows, from references/mart__alerts_per_severity.py
    project.refresh_reference_sheet("mart.alerts_per_severity")

Each `<...>` became:

- `<SOURCE_NAME>` and `<SOURCE_TABLE>`: ops__run_alerts and `run_alerts`, the table it reads,
  by its file in references/ and its name there;
- `<READS>`: `equals(run_alerts.dt, "2026-09-24")`, the rows write() reads: one day of
  `ops.run_alerts`, which is partitioned by dt, so a read must filter dt;
- `<GROUP_COLUMN>`: severity, the column each row is for, so
  `<SOURCE_TABLE>.<GROUP_COLUMN>` became `run_alerts.severity`;
- `<COUNT_NAME>`: `"alerts"`, the name of the count, in quotes, since it is a value, where a
  name Python reads, such as `run_alerts`, goes in bare;
- `<PARTITION_COLUMN>`: dt, the column of `ops.run_alerts` that fills this table's own
  partition column, so `<SOURCE_TABLE>.<PARTITION_COLUMN>` became `run_alerts.dt`.

The notebook has six code cells, run top to bottom:

1. the path lines and imports, as in [Start a Project](#start_a_project), and your query;
2. the logic, whose first line is `# logic`: imports, READS, and four functions, each giving a
   Statement and running nothing: create, rows, preview and write. `rows()` holds the clauses
   preview and write share, so the rows you check are the rows you save;
3. try it: each step's Hive, then the rows;
4. its Lineage, the record of which table columns feed each of its columns, as
   [Follow lineage](#follow_lineage) shows;
5. its Hive, in mart__alerts_per_severity.hql beside the notebook, as step 9 shows;
6. its rows in the Reference sheet, the one table listing every column of every table the
   Project has a Table reference for, as [Keep the Project in order](#keep_the_project_in_order)
   shows.

Done when no `<...>` is left in the notebook's code cells. Then step 4.

### 4. Fill in its Table reference, beside it

Goal: a Table reference that describes the table the notebook's write() fills.

references/mart__alerts_per_severity.py describes the table the notebook's write() fills.
This is it as `project.new_table` wrote it, from the saved_table_reference Template, to stand
in until the logic is written: then `project.reference_from_logic("mart.alerts_per_severity")`,
the new_table Workflow's step, writes it from the logic, its columns, partition columns and Key,
leaving its location= for you to answer. The Starter Example project's file was written by
hand instead, so it is the Starter's own, and this how-to shows that way:

The file `references/mart__alerts_per_severity.py`, as project.new_table wrote it:

    \"\"\"mart.alerts_per_severity - TODO: say in one line what one row is.

    project.reference_from_logic("mart.alerts_per_severity") writes this file again from the table's logic,
    filling in what is left. They are:
        <COLUMNS>: the columns write() saves and their types, from its logic's preview().

    Why: TODO: who reads this table, and why it is saved rather than worked out each time.

    project.new_table wrote this file from admin/templates/saved_table_reference.py, to stand in
    until the table's logic is written: then project.reference_from_logic writes it again, its
    columns and types from preview(), its partition columns from PARTITIONED_BY, and the Key its
    query makes. A Saved table doesn't exist until its notebook's create() makes it from this
    file, so nothing can be asked of it: its logic says what it holds.
    \"\"\"

    from sqlglot_composer import Table

    alerts_per_severity = Table(
        "mart.alerts_per_severity",
        columns={"<COLUMNS>": "string"},  # project.reference_from_logic writes them, from the logic
        location=None,  # TODO: its own folder, such as "/data/your_team/mart.db/alerts_per_severity"
    )

    # --- Aliases ------------------------------------------------------------------------------
    # Your own names for this table's columns and conditions, written by hand below.
    # Import one beside the table: from references.mart__alerts_per_severity import alerts_per_severity, <alias>
    #
    # A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
    # get back, still call the column by its own name. To rename an output, use AS(...).
    #     <alias> = alerts_per_severity.<column>
    # A condition Alias names a condition on this table alone, for WHERE or
    # count_rows(where=...). Add what it calls, such as equals, to the import at the top.
    #     <alias> = equals(alerts_per_severity.<column>, <value>)

It has no `does_not_add_up=`, which the Table references `project.add_references` writes have:
the Template's table saves counts, which add up, so it is left out and taken as empty. Add
`does_not_add_up=[...]` yourself if your table saves an average, a ratio or a distinct count.
reference_from_logic writes each column, its partition columns and Key; by hand, write those,
location= and the TODO lines, as here, the file as it is in the Starter Example project:

The file `references/mart__alerts_per_severity.py`, after you fill it in:

    \"\"\"mart.alerts_per_severity - one row per severity and day: the alerts raised.

    Why: its notebook saves the day's count of low and high alerts, so a dashboard of alerts
    reads two rows a day rather than every alert.

    project.new_table wrote this file from admin/templates/saved_table_reference.py, and it was
    then written by hand, which keeps it yours: project.reference_from_logic would have written it
    from the table's logic. Its notebook's text cell says which columns it lists, and its Key.
    \"\"\"

    from sqlglot_composer import Table

    alerts_per_severity = Table(
        "mart.alerts_per_severity",
        columns={
            "severity": "string",
            "alerts": "bigint",
            "dt": "string",
        },
        partitioned_by=["dt"],
        key=["severity", "dt"],
        location="/data/your_team/mart.db/alerts_per_severity",  # its own folder
        descriptions={
            "severity": "low / high, as ops.run_alerts holds it",
            "alerts": "the alerts of that severity raised that day",
            "dt": "the day the alerts were raised, as yyyy-MM-dd",
        },
    )

    # --- Aliases ------------------------------------------------------------------------------
    # Your own names for this table's columns and conditions, written by hand below.
    # Import one beside the table: from references.mart__alerts_per_severity import alerts_per_severity, <alias>
    #
    # A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
    # get back, still call the column by its own name. To rename an output, use AS(...).
    #     <alias> = alerts_per_severity.<column>
    # A condition Alias names a condition on this table alone, for WHERE or
    # count_rows(where=...). Add what it calls, such as equals, to the import at the top.
    #     <alias> = equals(alerts_per_severity.<column>, <value>)

- `columns={...}` lists each column write() saves, in the order its SELECT gives them, each
  with its Hive type as DESCRIBE prints it: `"severity"` is a `"string"`, as in
  `ops.run_alerts`, the count `"alerts"` is a `"bigint"`, and the partition column `"dt"`
  comes last.
- `partitioned_by=["dt"]` makes the table kept a Partition at a time, here a day: a write
  replaces the Partitions it fills, and every Statement that reads the table must filter dt.
- `key=["severity", "dt"]` is its Key, the columns whose values name one row of the table:
  each row is one severity on one day, so a severity alone repeats, once a day. The warehouse
  never checks a Key, so the Toolbox does: a write whose rows could share one is refused as it
  is built. Here GROUP_BY makes one row per severity and dt.
- `location=` is the table's own folder in the warehouse, where its files go: a Decision, one
  thing about the table that only you decide, written in quotes and used exactly as written.
  Ask whoever looks after your warehouse where your team may write, such as
  `"/data/your_team/mart.db/alerts_per_severity"`. Give each Saved table a folder of its own,
  never one inside another's: the Toolbox refuses two that share one.
- `descriptions={...}` says what each column holds, for the Reference sheet.

Done when the Table reference holds no `<...>` and no TODO line. Then step 5.

### 5. Add it to its Database module

Goal: references/mart.py, the module that gives the Database mart's tables. A Database is a
named group of tables, the first part of a table's name, `mart` in `mart.alerts_per_severity`;
its Database module is the one file in references/ that gives each of its tables.

A Saved table joins its Database module, references/mart.py, once its Table reference has no
`<...>` left: the next Project action that writes the Database modules adds it, for example
`project.refresh_reference_sheet`, which cell 6 runs, for its own table. Run here, it writes
mart.py:

>>> project.refresh_reference_sheet("mart.alerts_per_severity")
Wrote references/reference_sheet.csv: 3 rows, 1 table.
Wrote references/mart.py: from references import mart gives mart.alerts_per_severity.
Restart the kernel of a notebook that imported references, to see a table added since.

Done when it says it wrote references/mart.py. Then step 6.

### 6. Import it from references

Goal: the Saved table as a Table other Statements read. `from references import mart` gives
the table, as `ops` gives yours:

>>> from references import mart
>>> mart.alerts_per_severity  # -> Table
Table('mart.alerts_per_severity', columns: severity, alerts, dt)

Done when `mart.alerts_per_severity` shows its three columns. Then step 7.

### 7. Load its logic

Goal: the notebook's functions, by name. In Jupyter, run the notebook's cells top to bottom.
Here, `project.load` runs its logic cell and gives back its functions by name, as any notebook
of the Project can: an object with one attribute per function of the logic cell, such as
`logic.write`:

>>> logic = project.load("mart.alerts_per_severity")  # -> the notebook's functions
>>> logic
The logic of mart.alerts_per_severity: create, rows, preview, write.

Done when `logic` names create, rows, preview and write. Then step 8.

### 8. Try its steps

Goal: the Hive that creates and writes the table, and the rows the write would save. Cell 3
prints the Hive of the steps that create the table and write the rows READS picks, then runs
the preview, the rows the write would save:

>>> text = show_hive([logic.create(), logic.write()])  # -> str
-- 1 of 2
CREATE EXTERNAL TABLE IF NOT EXISTS mart.alerts_per_severity (
  severity STRING,
  alerts BIGINT,
  PRIMARY KEY (severity, dt) DISABLE NOVALIDATE
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC
LOCATION '/data/your_team/mart.db/alerts_per_severity';
<BLANKLINE>
-- 2 of 2
-- The Session setting "dynamic_partitions": this write fills dt from its rows.
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
INSERT OVERWRITE TABLE mart.alerts_per_severity PARTITION(dt)
SELECT
  run_alerts.severity,
  COUNT(*) AS alerts,
  run_alerts.dt
FROM ops.run_alerts AS run_alerts
WHERE
  run_alerts.dt = '2026-09-24'
GROUP BY
  run_alerts.severity,
  run_alerts.dt;
>>> run_query(logic.preview(), query)  # -> DataFrame
  severity  alerts          dt
0     high       2  2026-09-24
1      low       5  2026-09-24

- `logic.create()` gives CREATE EXTERNAL TABLE IF NOT EXISTS, from the Table reference: EXTERNAL
  and LOCATION make it a table whose files are yours, in its own folder, and IF NOT EXISTS,
  `may_exist=True` in the notebook, skips a table that is there already and never changes it,
  so the cell can run every day. `PRIMARY KEY ... DISABLE NOVALIDATE` writes the Key for
  whoever reads the table's description: Hive keeps it and never checks it.
- `logic.write()` gives INSERT OVERWRITE: it replaces whatever the Partitions it fills held,
  and no other, so sending it twice leaves the same rows, not twice as many.

At work, `project.run_tables`, in steps 11 and 12, sends each table's write() and never its
create(), so create each table once, before its first `project.run_tables`. From any notebook
of the Project, with `logic` from `project.load` as here, that is
`run_execute(logic.create(), execute)`; in the table's own notebook, add a cell after cell 3
that runs its create() the same way, and import execute beside query in cell 1. The Example
database can be read but not written, so this page creates nothing.

Done when the preview gives one row per severity for 2026-09-24. Then step 9.

### 9. Keep its Hive beside it

Goal: the table's Hive in a file beside its notebook, to read and to commit. Cell 3 already
prints each step's Hive, but only as the notebook's output, which is gone once the cell runs
again. Cell 5, `export_hive()`, keeps that Hive in a file beside the notebook,
mart__alerts_per_severity.hql, for two things cell 3 can't do: a file to read at a glance,
without opening the notebook or running anything, and a file to commit with the notebook, so
each commit shows the Hive the table sent then. It holds create(), then write(), each as
show_hive shows it, in the order they are sent, under lines saying the file is generated. The
Python stays the table's definition, so edit the logic and leave the file as written. To change
it:

1. edit cell 2, the logic, of mart__alerts_per_severity.ipynb;
2. save the notebook (Ctrl+S in Jupyter): `export_hive()` reads the notebook as last saved,
   so a change you haven't saved isn't in the file;
3. run cell 5, `export_hive()`, which writes mart__alerts_per_severity.hql again, over the one
   before: the same text when the logic is the same.

The file is to read and to commit, not to run: `project.run_tables`, in steps 11 and 12, sends
the writes. Jupyter runs a notebook in its own folder, so the calls below move there first, as
opening the notebook would, then back:

>>> import os
>>> from pathlib import Path
>>> os.chdir("tables/mart__alerts_per_severity")
>>> export_hive()
Wrote mart__alerts_per_severity.hql beside its notebook, the Hive of 2 steps, in the order
they are sent: create() and write().
>>> print(Path("mart__alerts_per_severity.hql").read_text())
-- The Hive of mart.alerts_per_severity, generated by export_hive() from the logic cell
-- of mart__alerts_per_severity.ipynb, beside this file. Edit the logic there, not this
-- file: each export_hive() writes it again, from the notebook as last saved. It holds 2
-- steps, in the order they are sent: create() and write().
<BLANKLINE>
-- 1 of 2: create()
CREATE EXTERNAL TABLE IF NOT EXISTS mart.alerts_per_severity (
  severity STRING,
  alerts BIGINT,
  PRIMARY KEY (severity, dt) DISABLE NOVALIDATE
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC
LOCATION '/data/your_team/mart.db/alerts_per_severity';
<BLANKLINE>
-- 2 of 2: write()
-- The Session setting "dynamic_partitions": this write fills dt from its rows.
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
INSERT OVERWRITE TABLE mart.alerts_per_severity PARTITION(dt)
SELECT
  run_alerts.severity,
  COUNT(*) AS alerts,
  run_alerts.dt
FROM ops.run_alerts AS run_alerts
WHERE
  run_alerts.dt = '2026-09-24'
GROUP BY
  run_alerts.severity,
  run_alerts.dt;
<BLANKLINE>
>>> os.chdir("../..")

Given a Statement instead, `export_hive` writes that Statement's Hive alone, as show_hive shows
it, in a file named for the Statement's variable, in the folder of the notebook or script that
calls it. Put each Statement in a variable of its own, such as daily and weekly, and pass each
in a call of its own: export_hive(daily), then export_hive(weekly), writes daily.hql and
weekly.hql. Pass each in its own call, never in a loop, whose one variable would name every
file the same, each over the one before.

Done when mart__alerts_per_severity.hql holds create(), then write(). Then step 10.

### 10. Choose how a write fills its Partitions

Goal: know which of the two ways a write fills Partitions you want.

The Template's write selects the partition column, `run_alerts.dt`, and its Hive says
PARTITION(dt) with no value: each row goes to the Partition its own dt names, so a write
whose READS picks several days fills each of them. The Toolbox puts the partition columns last
in SELECT, where Hive looks for them, wherever you list them. Filling Partitions from the rows
needs Hive's dynamic partitioning switched on first: show_hive prints the two SET lines that do
it, the Session setting `"dynamic_partitions"`, a named set of Hive SET lines sent before a
Statement, ahead of the write, and `project.run_tables` sends them first.

A write can name its Partition instead, with `partition={...}`. Its SELECT then leaves the
partition column out, and its Hive names the day, with no SET lines:

>>> from references import ops
>>> alerts_per_severity = mart.alerts_per_severity  # -> Table
>>> run_alerts = ops.run_alerts  # -> Table
>>> one_day = statement(  # -> Statement
...     INSERT_OVERWRITE(alerts_per_severity, partition={"dt": "2026-09-24"}),
...     SELECT(run_alerts.severity, AS(count_rows(), "alerts")),
...     FROM(run_alerts),
...     WHERE(equals(run_alerts.dt, "2026-09-24")),
...     GROUP_BY(run_alerts.severity),
... )
>>> text = show_hive(one_day)  # -> str
INSERT OVERWRITE TABLE mart.alerts_per_severity PARTITION(dt = '2026-09-24')
SELECT
  run_alerts.severity,
  COUNT(*) AS alerts
FROM ops.run_alerts AS run_alerts
WHERE
  run_alerts.dt = '2026-09-24'
GROUP BY
  run_alerts.severity;

`partition=` says where the rows go, and WHERE which rows are read, and nothing checks that the
two agree: keep them the same day. The Template's way needs no such care, since each row
carries its own day; [Rewrite some partitions](#rewrite_some_partitions) shows when to name
them.

- If each row carries its own Partition's value, select the partition column, as the Template
  does, and leave `partition=` out.
- If you write one Partition you name, give `partition={...}` and leave the partition column
  out of SELECT.

Done when the Hive of `one_day` names its Partition, PARTITION(dt = '2026-09-24'). Then
step 11.

### 11. Print the writes of the Project's tables

Goal: read each write before anything is sent. `project.run_tables` loads every Table
notebook's logic and sends each table's write(), each table before any table that reads it.
With no execute, it prints each write's Hive in that order and sends nothing, a dry run to read
first:

>>> project.run_tables()
-- 1 of 1: mart.alerts_per_severity
-- The Session setting "dynamic_partitions": this write fills dt from its rows.
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
INSERT OVERWRITE TABLE mart.alerts_per_severity PARTITION(dt)
SELECT
  run_alerts.severity,
  COUNT(*) AS alerts,
  run_alerts.dt
FROM ops.run_alerts AS run_alerts
WHERE
  run_alerts.dt = '2026-09-24'
GROUP BY
  run_alerts.severity,
  run_alerts.dt;
Printed 1 write in order, and sent nothing. Pass execute= to run them.

Done when it says `Printed 1 write in order, and sent nothing.` Then step 12.

### 12. Write it with the Project's other tables

Goal: each Saved table written, in order. With your query and execute, from warehouse.py,
`project.run_tables` sends the writes. This page gave connect(...) the Example database as its
connection, in step 1, so here its execute prints the first line of each thing sent. It takes query= as well as execute=, since a write() may give an Admin statement, one
that changes a Saved table's definition or deletes its data, or an Unchecked statement, Hive
written by hand, and one that reads rows goes to your query. A write fills dt from its rows, so
the Session setting `"dynamic_partitions"` goes first:

>>> project.run_tables(execute=execute)
execute: SET hive.exec.dynamic.partition=true
execute: SET hive.exec.dynamic.partition.mode=nonstrict
execute: INSERT OVERWRITE TABLE mart.alerts_per_severity PARTITION(dt)
1 of 1: mart.alerts_per_severity  worked
Wrote 1 table, in order.

At work, you run the admin notebook admin/run_tables.ipynb, or your team's scheduler does.
Each write() writes the rows its notebook's READS picks: change READS to write others.

Done when it says `Wrote 1 table, in order.` Then check it worked, below.

## Check it worked

The Table folder holds its notebook, its Hive and lineage/, and the registry lists the folder
and its Table reference beside the ones before:

>>> from pathlib import Path
>>> sorted(path.name for path in Path("tables/mart__alerts_per_severity").iterdir())
['lineage', 'mart__alerts_per_severity.hql', 'mart__alerts_per_severity.ipynb']
>>> project.check()
Every Table folder, Table reference, Building block and Scheduled run is registered, and each
    one registered is there.
...

Below its first line, it lists each line add_references proposed that you haven't kept or
changed yet, which blocks nothing.

The preview gave a row per severity, and its counts add up to the day's alerts:

>>> rows = run_query(logic.preview(), query)  # -> DataFrame
>>> int(rows["alerts"].sum())
7

Before you go on, check that:

- tables/mart__alerts_per_severity/ holds lineage, mart__alerts_per_severity.hql and
  mart__alerts_per_severity.ipynb;
- `project.check()` says every Table folder and Table reference is registered;
- the preview's alerts add up to 7, the day's alerts;
- `project.run_tables(execute=execute)` ends with `Wrote 1 table, in order.`

## Common mistakes

### Selecting the partition column a write names

With `partition={"dt": ...}`, the day comes from `partition=`, so a write that also selects
`run_alerts.dt` is refused as you build it:

>>> statement(
...     INSERT_OVERWRITE(alerts_per_severity, partition={"dt": "2026-09-24"}),
...     SELECT(run_alerts.severity, AS(count_rows(), "alerts"), run_alerts.dt),
...     FROM(run_alerts),
...     WHERE(equals(run_alerts.dt, "2026-09-24")),
...     GROUP_BY(run_alerts.severity, run_alerts.dt),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(alerts_per_severity): it also selects dt.
...

Pick one of the two ways: select only `run_alerts.severity` and the count with `partition=`,
or leave `partition=` out and let the rows fill it, as the Template does.

### Leaving the partition column out of GROUP_BY

Each row of the result is one group, so a column in SELECT must be in GROUP_BY. The Template
keeps the partition column in both: dropped from GROUP_BY, the write is refused by a Guard, a
check that refuses a Statement that would give a wrong result:

>>> statement(
...     INSERT_OVERWRITE(alerts_per_severity),
...     SELECT(run_alerts.severity, AS(count_rows(), "alerts"), run_alerts.dt),
...     FROM(run_alerts),
...     WHERE(equals(run_alerts.dt, "2026-09-24")),
...     GROUP_BY(run_alerts.severity),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  SELECT has run_alerts.dt, which GROUP_BY leaves out.
...

Keep the partition column in GROUP_BY as well as in SELECT: `GROUP_BY(run_alerts.severity,
run_alerts.dt)`, as the Template's rows() does.

### Making a Table folder that is already there

`project.new_table` leaves a Table folder that is there as it is: it holds your notebook and its
Lineage. Run again for the same table, it stops:

>>> project.new_table("mart.alerts_per_severity")
Traceback (most recent call last):
...
FileExistsError:
  What happened:  project.new_table("mart.alerts_per_severity"):
                  tables/mart__alerts_per_severity/ is already there, so nothing was made.
...

Open the notebook that is there instead. To start a table again, archive its folder first, as
[Keep the Project in order](#keep_the_project_in_order) shows.

## Next

- Follow a Saved table's columns back to the tables it reads, and write a table that reads
  another: [Follow lineage](#follow_lineage).
- See it beside every other table's columns, and keep the Project tidy:
  [Keep the Project in order](#keep_the_project_in_order).
- Rewrite some of its Partitions, such as last week's: [Rewrite some
  partitions](#rewrite_some_partitions).
- How a Saved table is stored, and its Key: [Choose how a Saved table is
  stored](#choose_how_a_saved_table_is_stored) and [Keys](#keys).
- The gallery's [`create_table`](examples.html#create_table) and
  [`INSERT_OVERWRITE`](examples.html#INSERT_OVERWRITE) entries.
"""  # noqa: E501 - the files it writes, shown byte for byte as the Project writes them

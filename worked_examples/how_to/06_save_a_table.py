"""Save a table

For: Getting started

## Goal

Keep a Statement's rows in a Saved table: a real table in the warehouse that your Project
writes, and that other Statements then read like any other table. `project.new_table` makes
its Table folder, holding a Table notebook made from the saved_table Template, and its Table
reference. You fill in both, try the notebook's steps, and from then on `project.run_tables`
writes it with the Project's other Saved tables.

## When you'd use it

When a result is slow to work out, or many notebooks and dashboards read it: it is cheaper to
work it out once and save it than to work it out again every time someone asks. A Saved table
also keeps each Partition's rows as they were when they were written.

The Example database can be read but not written to, so on this page each write shows its
Hive, ready to paste, and a write that is sent goes to warehouse.py's execute, which here calls
`example_database.execute`: it prints the write's first line and changes nothing. At work, the
same calls send it to your warehouse, through your own execute.

## Steps

### Where the last how-to left the Project

[Share Building blocks](#share_building_blocks) left the Project with its Table references
filled in and one Building block. The Saved table this how-to makes reads one table,
`ops.run_alerts`, so the steps below make the Project again with three Table references alone,
as `project.add_references` writes them:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/ and warehouse.py.
Next: write your two functions, query and execute, in warehouse.py.
>>> from warehouse import query, execute
>>> project.add_references(["ops.jobs", "ops.job_runs", "ops.run_alerts"], query=query)
Wrote references/ops__jobs.py, references/ops__job_runs.py and references/ops__run_alerts.py: fill in their TODO lines.
Wrote references/ops.py: from references import ops gives ops.job_runs, ops.jobs and ops.run_alerts.
Restart the kernel of a notebook that imported references, to see a table added since.

### Make its Table folder

The table is mart.alerts_per_severity: how many alerts of each severity, low or high, the runs
raised each day. `project.new_table` takes its name, its database first. The admin notebook
admin/new_table.ipynb holds this call, ready to fill in; calling it from any notebook of the
Project does the same:

>>> project.new_table("mart.alerts_per_severity")
Made tables/mart__alerts_per_severity/: mart__alerts_per_severity.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__alerts_per_severity.py: fill in its <...> and TODO lines.

It made four things, and listed two of them, the Table folder and the Table reference, in the
registry:

- tables/mart__alerts_per_severity/, the table's Table folder, named after the database and
  the table joined by two underscores;
- mart__alerts_per_severity.ipynb in it, the Table notebook, from the saved_table Template: a
  Saved table worked out from a table it reads, a count per group of the rows it reads;
- lineage/ beside it, empty until the notebook exports the table's Lineage;
- references/mart__alerts_per_severity.py, its Table reference. A Saved table doesn't exist
  until its notebook creates it, so nothing can be asked of it: you fill its Table reference
  in by hand.

Both hold `<...>` placeholders, each to type over, brackets and all. Until you do, the notebook
isn't Python yet, and `project.load`, which runs a notebook's logic from anywhere in the
Project, says which line stops it:

>>> project.load("mart.alerts_per_severity")
Traceback (most recent call last):
...
ValueError:
  What happened:  project.load("mart.alerts_per_severity"): the logic cell of tables/mart__alerts_per_severity/mart__alerts_per_severity.ipynb isn't Python yet, at its line 9: from references.<SOURCE_NAME> import <SOURCE_TABLE>
...

### Fill in its notebook

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
    #     naming `<PARTITION_COLUMN>` instead.
    #
    # Then fill in this table's Table reference, `references/mart__alerts_per_severity.py`: its `<...>` and TODO
    # lines.
    # It lists the columns write() saves, in the order its SELECT gives them: here
    # <GROUP_COLUMN>, typed as the table read types it, then <COUNT_NAME>, a count, "bigint", and
    # last its partition column, if it has one, also named in partitioned_by=[...]. Its Key is
    # the column each row is for, and the partition column if it has one, such as
    # key=["job_id", "region"].
    #
    # TODO: say in one line what one row of mart.alerts_per_severity is.
    #
    # A Saved table worked out from a table it reads: a count per group of the rows READS picks.
    # It is partitioned however its Table reference says, or not at all.
    #
    # Made by `project.new_table("mart.alerts_per_severity")` from
    # `admin/templates/saved_table.py`, which filled in the database, the table and its file's name,
    # mart__alerts_per_severity. Run the cells top to bottom once both are filled in.
    #
    # The code cells: 1 the Project and your query; 2 the logic, which starts `# logic`; 3 try it;
    # 4 its lineage; 5 its rows in the Reference sheet. The logic only imports and defines, so
    # `project.load("mart.alerts_per_severity")` can run it from anywhere else, for lineage across your
    # tables and for `admin/run_tables.ipynb`, which sends its `write()`.

    # %%
    # 1. The Project and your query
    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

    from sqlglot_composer import export_lineage, project, run, show_hive
    from warehouse import query

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
    run(preview(), query=query)

    # %%
    # 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
    export_lineage(write())

    # %%
    # 5. The Reference sheet: this table's rows, from references/mart__alerts_per_severity.py
    project.refresh_reference_sheet("mart.alerts_per_severity")

Its text cell starts with a list of what each `<...>` is for. Type over each one in the code
cells. Then, in the text cell, put one line saying what a row is in place of that list, the
lines about the Table reference below it and the TODO line. Here is the whole notebook, filled
in, as it is in the Starter Example project:

The file `tables/mart__alerts_per_severity/mart__alerts_per_severity.ipynb`, after you fill it in:

    # %% [markdown]
    # # mart.alerts_per_severity
    #
    # One row per severity and day: how many alerts of that severity the runs raised that day.
    #
    # A Saved table worked out from a table it reads: a count per group of the rows READS picks.
    # It is partitioned however its Table reference says, or not at all.
    #
    # Made by `project.new_table("mart.alerts_per_severity")` from
    # `admin/templates/saved_table.py`, which filled in the database, the table and its file's name,
    # mart__alerts_per_severity. Run the cells top to bottom once both are filled in.
    #
    # The code cells: 1 the Project and your query; 2 the logic, which starts `# logic`; 3 try it;
    # 4 its lineage; 5 its rows in the Reference sheet. The logic only imports and defines, so
    # `project.load("mart.alerts_per_severity")` can run it from anywhere else, for lineage across your
    # tables and for `admin/run_tables.ipynb`, which sends its `write()`.

    # %%
    # 1. The Project and your query
    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

    from sqlglot_composer import export_lineage, project, run, show_hive
    from warehouse import query

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
    run(preview(), query=query)

    # %%
    # 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
    export_lineage(write())

    # %%
    # 5. The Reference sheet: this table's rows, from references/mart__alerts_per_severity.py
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

The notebook has five code cells, run top to bottom:

1. the path lines and imports, as in [Start a Project](#start_a_project), and your query;
2. the logic, whose first line is `# logic`: imports, READS, and four functions, each giving a
   Statement and running nothing: create, rows, preview and write. `rows()` holds the clauses
   preview and write share, so the rows you check are the rows you save;
3. try it: each step's Hive, then the rows;
4. its Lineage, as [Follow lineage](#follow_lineage) shows;
5. its rows in the Reference sheet, as [Keep the Project in order](#keep_the_project_in_order)
   shows.

### Fill in its Table reference, beside it

Open references/mart__alerts_per_severity.py in your editor and fill it in beside the
notebook: it describes the table the notebook's write() fills. This is it as
`project.new_table` wrote it, from the saved_table_reference Template:

The file `references/mart__alerts_per_severity.py`, as project.new_table wrote it:

    \"\"\"mart.alerts_per_severity - TODO: say in one line what one row is.

    Fill in every <...> below, brackets and all: Python stops at one left in. They are:
        <COLUMN> and <COLUMN_TYPE>: a column write() saves and its Hive type, each in quotes,
            such as "job_id" and "bigint". Copy the line for each column, in the order write()
            saves them, its partition columns last.
        <LOCATION>: the table's own folder, in quotes, such as "/data/your_team/mart.db/alerts_per_severity".
    Then partitioned_by= and key=, and the TODO lines.

    Why: TODO: who reads this table, and why it is saved rather than worked out each time.

    project.new_table wrote this file from admin/templates/saved_table_reference.py. A Saved
    table's Table reference is filled in by hand, since the table doesn't exist until its
    notebook's create() makes it from this file. Its notebook's text cell says which columns it
    lists, and its Key.
    \"\"\"

    from sqlglot_composer import Table

    alerts_per_severity = Table(
        "mart.alerts_per_severity",
        columns={
            <COLUMN>: <COLUMN_TYPE>,  # a line per column write() saves, its partition columns last
        },
        partitioned_by=[],  # its partition columns, in order, such as ["region"]: [] for none
        key=None,  # the columns whose values name one row, such as ["job_id"]: None if none do
        location=<LOCATION>,  # its own folder, in quotes
        descriptions={},  # optional: {"column": "what it holds"}, for the Reference sheet
    )

    # --- Aliases ------------------------------------------------------------------------------
    # Your own names for this table's columns and conditions, written by hand below.
    # Import one beside the table: from references.mart__alerts_per_severity import alerts_per_severity, <alias>
    #
    # A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame run
    # gives back, still call the column by its own name. To rename an output, use AS(...).
    #     <alias> = alerts_per_severity.<column>
    # A condition Alias names a condition on this table alone, for WHERE or
    # count_rows(where=...). Add what it calls, such as equals, to the import at the top.
    #     <alias> = equals(alerts_per_severity.<column>, <value>)

It has no `does_not_add_up=`, which the Table references `project.add_references` writes have:
the Template's table saves counts, which add up, so it is left out and taken as empty. Add
`does_not_add_up=[...]` yourself if your table saves an average, a ratio or a distinct count.
Type over each `<...>`, and fill in the TODO lines, as here, the file as it is in the Starter
Example project:

The file `references/mart__alerts_per_severity.py`, after you fill it in:

    \"\"\"mart.alerts_per_severity - one row per severity and day: the alerts raised.

    Why: its notebook saves the day's count of low and high alerts, so a dashboard of alerts
    reads two rows a day rather than every alert.

    project.new_table wrote this file from admin/templates/saved_table_reference.py. A Saved
    table's Table reference is filled in by hand, since the table doesn't exist until its
    notebook's create() makes it from this file. Its notebook's text cell says which columns it
    lists, and its Key.
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
    # A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame run
    # gives back, still call the column by its own name. To rename an output, use AS(...).
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
- `location=` is what `<LOCATION>` became: the table's own folder in the warehouse, where its
  files go, in quotes and used exactly as written. Ask whoever looks after your warehouse where
  your team may write, such as `"/data/your_team/mart.db/alerts_per_severity"`. No two Saved
  tables may share a folder, or have one inside the other: the Toolbox refuses two that do.
- `descriptions={...}` says what each column holds, for the Reference sheet.

### Reach it from references

A Saved table joins its Database module, references/mart.py, once its Table reference has no
`<...>` left: the next Project action that writes the Database modules adds it, for example
`project.refresh_reference_sheet`, which cell 5 runs, for its own table. Run here, it writes
mart.py:

>>> project.refresh_reference_sheet("mart.alerts_per_severity")
Wrote references/reference_sheet.csv: 3 rows, 1 table.
Wrote references/mart.py: from references import mart gives mart.alerts_per_severity.
Restart the kernel of a notebook that imported references, to see a table added since.

Then `from references import mart` gives the table, as `ops` gives yours:

>>> from references import mart
>>> mart.alerts_per_severity  # -> Table
Table('mart.alerts_per_severity', columns: severity, alerts, dt)

### Try its steps

In Jupyter, run the notebook's cells top to bottom. Here, `project.load` runs its logic cell
and gives back its functions by name, as any notebook of the Project can: an object with one
attribute per function of the logic cell, such as `logic.write`:

>>> logic = project.load("mart.alerts_per_severity")  # -> the notebook's functions
>>> logic
The logic of mart.alerts_per_severity: create, rows, preview, write.

Cell 3 prints the Hive of the steps that create the table and write the rows READS picks, then
runs the preview, the rows the write would save:

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
>>> run(logic.preview(), query=query)  # -> DataFrame
  severity  alerts          dt
0     high       2  2026-09-24
1      low       5  2026-09-24

- `logic.create()` gives CREATE EXTERNAL TABLE IF NOT EXISTS, from the Table reference: EXTERNAL and
  LOCATION make it a table whose files are yours, in its own folder, and IF NOT EXISTS,
  `may_exist=True` in the notebook, skips a table that is there already and never changes it,
  so the cell can run every day. `PRIMARY KEY ... DISABLE NOVALIDATE` writes the Key for
  whoever reads the table's description: Hive keeps it and never checks it.
- `logic.write()` gives INSERT OVERWRITE: it replaces whatever the Partitions it fills held,
  and no other, so sending it twice leaves the same rows, not twice as many.

At work, `project.run_tables`, below, sends each table's write() and never its create(), so
create each table once, before its first `project.run_tables`. From any notebook of the
Project, with `logic` from `project.load` as here, that is
`run(logic.create(), execute=execute)`; in the table's own notebook, add a cell after cell 3
that runs its create() the same way, and import execute beside query in cell 1. The Example
database can be read but not written, so this page creates nothing.

### How a write fills its Partitions

The Template's write selects the partition column, `run_alerts.dt`, and its Hive says
PARTITION(dt) with no value: each row goes to the Partition its own dt names, so a write
whose READS picks several days fills each of them. The Toolbox puts the partition columns last
in SELECT, where Hive looks for them, wherever you list them. Filling Partitions from the rows
needs Hive's dynamic partitioning switched on first: show_hive prints the two SET lines that do
it, the Session setting `"dynamic_partitions"`, ahead of the write, and `project.run_tables`
sends them first.

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

### Write it with the Project's other tables

`project.run_tables` loads every Table notebook's logic and sends each table's write(), each
table before any table that reads it. With no execute, it prints each write's Hive in that
order and sends nothing, a dry run to read first:

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

With your query and execute, from warehouse.py, it sends them. The Project's warehouse.py
holds the Example database's two calls until you write your own, so here its execute prints
the first line of each thing sent. It takes query= as well as execute=, since a write() may
give an Admin statement or an Unchecked statement, and one that reads rows goes to your query.
A write fills dt from its rows, so the Session setting `"dynamic_partitions"` goes first:

>>> project.run_tables(query=query, execute=execute)
execute: SET hive.exec.dynamic.partition=true
execute: SET hive.exec.dynamic.partition.mode=nonstrict
execute: INSERT OVERWRITE TABLE mart.alerts_per_severity PARTITION(dt)
1 of 1: mart.alerts_per_severity  worked
Wrote 1 table, in order.

At work, you run the admin notebook admin/run_tables.ipynb, or your team's scheduler does.
Each write() writes the rows its notebook's READS picks: change READS to write others.

## Check it worked

The Table folder holds its notebook and lineage/, and the registry lists the folder and its
Table reference beside the ones before:

>>> from pathlib import Path
>>> sorted(path.name for path in Path("tables/mart__alerts_per_severity").iterdir())
['lineage', 'mart__alerts_per_severity.ipynb']
>>> project.check()
Every Table folder, Table reference and Building block is registered, and each one registered is there.

The preview gave a row per severity, and its counts add up to the day's alerts:

>>> rows = run(logic.preview(), query=query)  # -> DataFrame
>>> int(rows["alerts"].sum())
7

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

Leave `run_alerts.dt` out of SELECT, or leave `partition=` out and let the rows fill it, as the
Template does.

### Leaving the partition column out of GROUP_BY

Each row of the result is one group, so a column in SELECT must be in GROUP_BY. The Template
keeps the partition column in both: dropped from GROUP_BY, the write is refused:

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

### Making a Table folder that is already there

`project.new_table` never writes over a Table folder: it holds your notebook and its Lineage.
Run again for the same table, it stops:

>>> project.new_table("mart.alerts_per_severity")
Traceback (most recent call last):
...
FileExistsError:
  What happened:  project.new_table("mart.alerts_per_severity"): tables/mart__alerts_per_severity/ is already there, so nothing was made.
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
"""

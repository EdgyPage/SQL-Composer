"""Hand-written Hive with your Table references

For: Intermediate

## Goal

Send Hive you write by hand, for what no Clause function writes, with your Table references'
names dropped into it by an f-string: `unchecked_hive(f"SELECT {ops.jobs.job_id} FROM
{ops.jobs}")`. A Table reference is the file that describes one table, its columns, its
Partitions and its Key; a Clause function, such as `SELECT` or `WHERE`, writes one part of a
Statement, a query the Toolbox checks. Hive written by hand is an Unchecked statement: each name
in it is spelt as its Table reference spells it, `run_query` sends the text as you wrote it,
and Lineage, the record of which columns feed each result, shows it as one step over the tables
it reads.

## When you'd use it

- If you have Hive already, such as a colleague's query, and need it run today, send it as an
  Unchecked statement, then rewrite it in Clause functions when you have time.
- If you need a command the Toolbox doesn't write, such as SHOW PARTITIONS, write it by hand.
- If you need a shape of query the Toolbox doesn't write, such as a subquery inside WHERE,
  write it by hand.
- If the Clause functions write what you need, use them: no Guard, Warning or Load limit looks
  inside hand-written Hive.
- If you have no Project or Table references yet, do [Start a Project](#start_a_project),
  [Add your tables' references](#add_your_tables_references) and
  [Build and run a first statement](#build_and_run_a_first_statement) first;
  [Follow lineage](#follow_lineage) shows the Lineage it is drawn in.

## Steps

### 1. Start from the Intermediate Example project

Goal: a Project, your folder of scripts at work, to write the Hive in. Work in a copy of the
Intermediate Example project, at its top: copy `example_projects/intermediate/` from the
download to a folder of your own, copy the `sqlglot_composer` folder into it, as a Project holds
it, and open a notebook there. This page makes the same copy in its first step, from the
download the Toolbox came in, into the folder it runs in, which Python's path holds already, as
Jupyter's does for a notebook's own folder:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "intermediate", ".", dirs_exist_ok=True)

Done when the folder you work in holds the Project's admin/, references/ and tables/ folders.
Then step 2.

### 2. Add the Table reference of ops.jobs

Goal: both tables the Hive reads, readable from Python. The Project has the Table reference of
ops.job_events already. Add the one of ops.jobs, as
[Add your tables' references](#add_your_tables_references) shows. Its TODO lines can wait: no
Key is read in Hive you write by hand.

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> from warehouse import query, execute
>>> project.add_references(["ops.jobs"], query=query)
Wrote references/ops__jobs.py: fill in its TODO lines.
...
Wrote references/ops.py: from references import ops gives ops.job_events, ops.job_owners,
    ops.jobs, ops.region_budgets, ops.region_costs and ops.team_notes.
Restart the kernel of a notebook that imported references, to see a table added since.
>>> from references import ops

`query` and `execute` come from the Project's warehouse.py, which in the Example project
calls the Example database; yours calls your warehouse.

Done when `from references import ops` runs without an error. Then step 3.

### 3. Read a table's text and a column's text

Goal: know what an f-string drops in. A Table reference turned into text, as an f-string turns
it, is its name as FROM writes it, with the name Hive calls it by after AS. A column's is that
name, a dot, and the column:

>>> str(ops.jobs)  # -> str
'ops.jobs AS jobs'
>>> str(ops.jobs.job_id)  # -> str
'jobs.job_id'

A column is `jobs.job_id`, not `ops.jobs.job_id`, though you reach it in Python as
`ops.jobs.job_id`: Hive names a column by its table's name after AS, and refuses a name of
three parts in a SELECT. So the table's text goes after FROM or JOIN, where the AS belongs,
and the column's anywhere a column goes.

Done when the table's text ends with `AS jobs` and the column's is `jobs.job_id`. Then step 4.

### 4. Write the Hive in an f-string

Goal: the hand-written Hive, its names spelt by your Table references. Here is Hive handed to
you: the jobs that had an event on 2026-09-24, found with a subquery inside WHERE, a shape the
Toolbox writes as a `SEMI_JOIN` instead. Put f before the string, and each name in `{...}`:

>>> jobs, job_events = ops.jobs, ops.job_events  # -> Table, Table
>>> busy_jobs = unchecked_hive(  # -> UncheckedStatement
...     f"SELECT {jobs.job_id}, {jobs.job_name} FROM {jobs} "
...     f"WHERE {jobs.job_id} IN (SELECT {job_events.job_id} FROM {job_events} "
...     f"WHERE {job_events.dt} = '2026-09-24')")
>>> text = show_hive(busy_jobs)  # -> str
-- Unchecked statement, written by hand: no Guard, Warning or Load limit looked inside
SELECT jobs.job_id, jobs.job_name FROM ops.jobs AS jobs WHERE jobs.job_id IN (SELECT
    job_events.job_id FROM ops.job_events AS job_events WHERE job_events.dt = '2026-09-24');
>>> run_query(busy_jobs, query)  # -> DataFrame
   job_id      job_name
0       1  nightly_load
1       2  invoice_sync

The text is sent as you wrote it: the Toolbox checks none of it. What the f-string gives you
is the spelling: a column renamed in its Table reference is renamed here too, and a name
mistyped, such as `jobs.job_idd`, stops at once with a message naming the table's columns,
rather than reaching the warehouse.

Done when the run gives jobs 1 and 2. Then step 5.

### 5. Send it with the call that suits it

Goal: each piece of Hive sent through the right one of your two calls. You choose the call by
the function you call: `run_query` sends the text through your query, which gives back a
DataFrame, as for a SELECT, SHOW or DESCRIBE; `run_execute` sends it through your execute,
which gives back nothing, as for a CREATE or ALTER. A view, which the Toolbox doesn't write, is
created through your execute; the Example database's prints the first line it is given, and
changes nothing:

>>> finance_jobs = unchecked_hive(  # -> UncheckedStatement
...     f"CREATE VIEW IF NOT EXISTS mart.finance_jobs AS "
...     f"SELECT {jobs.job_id}, {jobs.job_name} FROM {jobs} WHERE {jobs.team} = 'finance'")
>>> run_execute(finance_jobs, execute)
execute: CREATE VIEW IF NOT EXISTS mart.finance_jobs AS SELECT jobs.job_id, jobs.job_name FROM
    ops.jobs AS jobs WHERE jobs.team = 'finance'

Each run of an Unchecked statement adds an entry to the Admin log, admin/admin_log.md, the
Toolbox's record of what you ran: its entries are the list of what the Toolbox should learn to
write next.

Done when your execute is given the CREATE VIEW. Then step 6.

### 6. Write a table's name alone yourself

Goal: Hive for a command that takes a bare table name. DESCRIBE and SHOW PARTITIONS take a
table's name with no AS after it, so write the name yourself, as the warehouse knows it:

>>> days = run_query(unchecked_hive("SHOW PARTITIONS ops.job_events"), query)  # -> DataFrame
>>> days.tail(2)
        partition
12  dt=2026-09-23
13  dt=2026-09-24

Done when the last two Partitions shown are dt=2026-09-23 and dt=2026-09-24. Then step 7.

### 7. Draw its Lineage: one step over whole tables

Goal: see how Lineage shows hand-written Hive. `export_lineage` draws an Unchecked statement as
one step it can't see inside, reading each table its text names, whole: no column is followed
through it.

>>> html_file, markdown_file = export_lineage(
...     busy_jobs, to="lineage/busy_jobs.html")  # -> tuple[Path, Path]
>>> print(markdown_file.read_text(encoding="utf-8").split("## busy_jobs")[1].split("###")[0])
<BLANKLINE>
<BLANKLINE>
⚠ An Unchecked statement: Hive written by hand, which no Guard, Warning or Load limit looked
    inside, so its columns can't be followed through it. It reads ops.job_events and ops.jobs.
<BLANKLINE>
<BLANKLINE>

A Statement built with Clause functions, such as the same question with `SEMI_JOIN`, is drawn
column by column: rewrite the Hive that way once you have time, and its Lineage says where
each column comes from.

Done when the Lineage names ops.job_events and ops.jobs as read. Then check it worked, below.

## Check it worked

The Hive holds each table's text after FROM, and the run gave the two jobs with an event on
2026-09-24:

>>> "FROM ops.jobs AS jobs WHERE" in to_hive(busy_jobs)
True
>>> list(run_query(busy_jobs, query)["job_name"])
['nightly_load', 'invoice_sync']

Before you go on, check that:

- the Hive of `busy_jobs` holds `FROM ops.jobs AS jobs`;
- the run gives nightly_load and invoice_sync;
- admin/admin_log.md holds an entry for each Unchecked statement you ran.

## Common mistakes

### Writing a column with its Database

Write a column's name out as you reach it in Python, and the Hive has three parts in it:

    unchecked_hive(f"SELECT ops.jobs.job_id FROM {jobs}")

Hive refuses it, saying it can't find the table or column `ops`: after `FROM ops.jobs AS
jobs` the table is called `jobs`. The Example database's own small executor runs it anyway, so
try it at work. Drop the column's text in with `{jobs.job_id}`.

### A table's text after DESCRIBE

An f-string gives a table's text with its AS, which only FROM and JOIN take:

>>> to_hive(unchecked_hive(f"DESCRIBE {jobs}"))
'DESCRIBE ops.jobs AS jobs'

Hive refuses that. Write the name alone, `"DESCRIBE ops.jobs"`, as the steps do for SHOW
PARTITIONS.

### Sending a read with run_execute

The Toolbox doesn't read your text to choose a call: it sends it through the one you called.
A read sent with `run_execute` goes to your execute, which gives back nothing, so its rows are
lost:

>>> run_execute(unchecked_hive("SHOW PARTITIONS ops.job_events"), execute)
execute: SHOW PARTITIONS ops.job_events

Send Hive that gives back rows with `run_query`, as the steps do.

### Expecting a Load limit

No Load limit, the check that refuses a read too big for the cluster, looks inside the text, so
a read of a partitioned table that filters none of its days is sent as written, and reads every
day: here all 14 days of ops.job_events.

>>> every_day = unchecked_hive(
...     f"SELECT COUNT(*) AS events FROM {job_events}")  # -> UncheckedStatement
>>> run_query(every_day, query)
   events
0      57

At work that can be the whole of a big table. Filter its partition column yourself, as
`busy_jobs` does with `{job_events.dt} = '2026-09-24'`.

## Next

- [Semi-, anti- and full joins](#semi_anti_and_full_joins): the subquery above, written as a
  `SEMI_JOIN`, which the Toolbox checks and draws column by column.
- [Call other Hive functions](#call_other_hive_functions): a Hive function inside a Statement,
  rather than the whole Statement by hand.
- [Follow lineage](#follow_lineage): Lineage of Statements and Saved tables.
- The gallery's [`unchecked_hive`](examples.html#unchecked_hive) entry.
"""

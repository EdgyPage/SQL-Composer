# The Toolbox: sqlglot Composer

A toolbox for writing Hive SQL in Python. Queries are composed from Python functions and a small
stack of the user's own scripts, emitted as a single Hive SQL string - sent to a query API that
accepts only strings - and traced back to the table columns they read.

## Language

### What ships to work

**Toolbox**:
The set of Python functions that compose Hive SQL - the only thing copied to work, as one
folder, sqlglot Composer's. Before 6.0 it came in two Editions, and was copied as two
folders, a shared core and an Edition's own.
_Avoid_: library, package, framework, SQL module, Edition, Composer core

**Toolbox version**:
The feature number of the Toolbox (`7.2`), raised only when a big feature lands, and written in
one place: the Toolbox folder's `version.txt`, which also lists each of its files, so the import
can tell one that differs from the download. Two copies of the same Toolbox version are told
apart by when they were exported.
_Avoid_: release, build, hash

**Clean branch**:
The branch holding only the Toolbox, a copy of the Example projects and the Templates, and their
README, change notes, license and requirements.txt, generated from the Dev branch and never
edited by hand.
_Avoid_: release branch, prod branch, copy branch

**Dev branch**:
The branch where all work happens: the Toolbox plus its tests, agents and tracker.
_Avoid_: develop, internal branch, testing branch

**Warehouse**:
Where Statements run at work: the tables, and the Hive that runs a Statement's Hive on them.
Each Toolbox user has one; the Example database stands in for it. The Toolbox reaches it only
through the user's two calls: `query`, which gives back rows as a DataFrame, and `execute`, which
gives back nothing, as the user's own API does. The user chooses which call sends each
Statement; the Toolbox never chooses for them.
_Avoid_: backend, engine, server, platform, send

### The user's own scripts

**Project**:
The user's folder at work holding the Toolbox and their own scripts in one fixed layout: an
admin folder, a flat folder of Table references, Building blocks, and a Table folder for each
Saved table they build.
_Avoid_: workspace, repo, codebase

**Table folder**:
The folder in a Project that holds everything about one Saved table the user builds: the
notebook whose Statements create and write it, and its past Lineage. Only a Project action
creates or removes one.
_Avoid_: table directory, table project, model folder

**Table notebook**:
The notebook in a Table folder whose cells create, preview and write its Saved table, made from
a Template when the Table folder is made. Its logic cell, the one whose first line is
`# logic`, holds the table's logic alone, its imports and its functions, so other notebooks
can load and use that logic without running the rest.
_Avoid_: table script, pipeline notebook, job

**Registry**:
The Project's list of every Table folder, Table reference and Building block a Project action
made, and when each was removed. What is in the Project but not in the Registry was made by hand; what is in
the Registry but not in the Project was moved or deleted by hand.
_Avoid_: manifest, inventory, index

**Project action**:
A one-time change to a Project's files - starting a Project, creating or removing a Table
folder or a Building block, adding Table references - run from the admin folder and recorded
in the Admin log. Where an Admin statement changes the warehouse, a Project action changes only
files. The user makes only the Project's folder and the copy of the Toolbox in it; a Project
action makes every other file, for the user to fill in.
_Avoid_: admin statement, migration, setup step

**Reference sheet**:
One table listing every column of every table the Project has a Table reference for, with its
type, its aliases and what it holds, to read and search outside Python.
_Avoid_: data dictionary, catalog, master sheet

**Alias**:
A name the user gives by hand, in a Table reference, to one of its table's columns or to a
condition on that table alone, so Statements can say it shorter or plainer.
_Avoid_: nickname, shortcut, synonym

**Level**:
One of three tiers of the user's own scripts. A script imports only from lower Levels and
from the Toolbox, never from a higher or equal Level. In a Project, the Table references and
the warehouse calls are Level 0, as is each Database module, the one Level 0 script that
imports Level 0 scripts (its Database's Table references), the Building blocks Level 1, and
each Table notebook's logic Level 2. What runs the Statements of many Table notebooks in order
sits above the three Levels, so it may read all of them.
_Avoid_: layer, tier, stage

**Table reference**:
A Level 0 script describing one table: its columns and their types, its Partitions and its Key,
where it has them, and the filters that concern that table alone.
_Avoid_: table config, schema file, declaration, model, standard query

**Database**:
A named group of tables in the warehouse, the first part of a table's name (`ops` in
`ops.jobs`). In a Project, each Database the Table references name is one Python object whose
attributes are its tables, so a column is reached as `ops.jobs.job_id`: its Database module,
`references/ops.py`, which the Project actions and refresh_reference_sheet write, never by
hand, and `from references import ops` imports.
_Avoid_: schema, namespace

**Key**:
The columns whose values name exactly one row of a table: the table's primary key, declared on
its Table reference. Not every table has one, and nothing is checked against a Key a table
doesn't have. The warehouse never checks it; the Toolbox does, before writing a Saved table
that has one and when joining, and Lineage shows where an output keeps or loses it. A Derived
table's Key is worked out from how its Statement makes its rows. `check_key(...)` and
`check_table_reference(...)` give back a `Verdict`, the name a type hint uses; its `ok` says
whether the check found nothing wrong.
_Avoid_: unique key, id, partition key

**Building block**:
A Level 1 piece of the user's own code reused across notebooks: most often a piece of a
Statement - a filter, a join or a sub-query - and sometimes what a Statement needs beside it,
such as the function a Python step names or a named set of Session settings. In a Project, each
is a file of its own in the building_blocks folder, named as it is, which a Project action makes
from a Template.
_Avoid_: fragment, component, snippet, helper

**Statement**:
A Level 2 query, assembled from Table references and Building blocks, or written by the Toolbox
for one of the user's Saved tables, that becomes one Hive SQL string. A Session setting's `SET`
lines and an Unchecked statement aren't Statements, but are run, shown and listed in a pipeline
the same way. In Python it is a `Statement`, what `statement(...)` gives back, and the name a
type hint uses (`-> Statement`).
_Avoid_: report, case, output script

### Writing a Statement

**Clause function**:
A Toolbox function named after one SQL clause - `SELECT`, `FROM`, `WHERE`, `GROUP_BY` - and
written in SQL order. A Statement is made of them, given in that order. Each gives back a
`Clause`, the name a type hint uses.
_Avoid_: builder, chain, method

**Column**:
One column of a table, as a Table reference's attribute (`job_runs.status`), or a calculation
made from columns, as `job_runs.duration_mins / 60` and `sum_of(...)` give back. `Column` is the
name a type hint uses. `AS(...)` gives back a `Named`: a column with the name it gets in the
result. `descending(...)` gives back an `Ordering`: a column to sort by from largest to smallest.
_Avoid_: field

**Condition**:
A test on rows, for `WHERE`, `HAVING` or `ON=`, as `equals(...)` and the other condition
functions give back, and `all_of(...)` and `any_of(...)` combine. `Condition` is the name a type
hint uses.
_Avoid_: predicate, criterion

**Guard**:
A check the Toolbox runs while a Statement is composed, which refuses a Statement that would
silently give a wrong result, unless the call that made the mistake carries the Guard's opt-out.
Guards protect the answer. Load limits protect the cluster, and are not Guards.
_Avoid_: guardrail, check, validation, rule

**Warning**:
A check the Toolbox runs while a Statement is composed, which lets the Statement through but says
at the offending call why a number may come out wrong, unless that call carries the Warning's
opt-out. Used where the risky Statement is often the one the user meant, such as a join off the
joined table's key.
_Avoid_: soft guard, lint, notice, advisory

**Derived table**:
A Statement given a name so another Statement can read from it, with its output columns checked
like a Table reference's. It lives only inside the Statement that reads it, and is never stored.
In Python, `derived(...)` gives back a `Table`, read like any other, so a Building block that
gives one back says `-> Table`.
_Avoid_: view, temp table, CTE (the CTE is how it lands in the string, not what it is)

**Window**:
The rows a calculation looks across for each row of a Statement: the rows of that row's group,
in an order, and sometimes only those near it, such as the six before it. A calculation over a
Window gives each row a value of its own and keeps every row, as a running total, a rank or the
value of the row before does. Its groups are SQL's PARTITION BY, which has nothing to do with a
Partition. In Python, `window(...)` gives back a `Window`, the name a type hint uses.
_Avoid_: frame, OVER clause (OVER is how it lands in the string), analytic function

**Stack**:
A Statement made of other whole Statements, whose rows it puts together one Statement after
another, their columns matched by name: every row of each (`UNION_ALL`), each different row
once (`UNION`), only the rows found in all of them (`INTERSECT`), or the first one's rows found
in none of the others (`EXCEPT`).
_Avoid_: union (the Hive word for one kind), set operation, combined query, append

**Subtotal row**:
A row a Statement's grouping adds to its groups' rows, totalling the rows of several groups,
such as one per team over all its jobs, or the grand total, one over every row. The columns it
totals over are empty in it, as a real row's may be too, so the Toolbox can say which rows are
subtotal rows. In Python, `rollup(...)`, `cube(...)` and `grouping_sets(...)` give back
`Subtotals`, which go in GROUP_BY to ask for these rows: the name a type hint uses.
_Avoid_: total row, rollup row, summary row

**Saved table**:
A real table in the warehouse that a Statement writes into, which other Statements then read through
its own Table reference, like any other table. It is what Hive calls an external table: its
files are in a folder of its own, which its Table reference names along with how it is
stored; the user's own Statements are the only ones
that write it. Hive's other kind, a managed table, keeps its files where the warehouse chooses:
create_table made those before 5.0, and admin.move_to_own_folder moves one to a folder of its
own.
_Avoid_: materialized view, cache, temp table, output table

**Unchecked statement**:
Hive text the user writes by hand and runs through the Toolbox, as a Statement is run, when no
Clause function covers it yet. No Guard, Warning or Load limit looks inside it; text that drops,
alters or truncates a table only gets a note naming the admin function that does the job, where
one does. Lineage
shows it as one opaque step. Each one marks something the Toolbox should learn to write. In
Python, `unchecked_hive(...)` gives back an `UncheckedStatement`, the name a type hint uses.
_Avoid_: raw SQL, passthrough, custom query

**Python step**:
A change the user makes to data in Python, outside any Statement, and saves to a table
themselves, declared to the Toolbox with the columns it read and the table it wrote. Lineage
shows it as one opaque step naming the function that made the change and where it lives; the
Toolbox never moves its data. In Python, `python_step(...)` gives back a `PythonStep`, the name a
type hint uses.
_Avoid_: transform, pandas step, UDF

**Admin statement**:
A Statement from the Toolbox's admin module that changes a Saved table's definition or deletes its
data, such as dropping a table or some of its Partitions, adding columns, setting its properties or moving
it to a folder of its own. It runs like any Statement, shows what it will change and what can't
be undone before its Hive, and is refused for any table that isn't one of the user's Saved
tables. The admin module is imported by name, apart from the everyday names.
_Avoid_: one-time action, migration, maintenance

**Admin log**:
The text record the Toolbox keeps of every Admin statement, Unchecked statement and Project
action the user has run: when, on which table, the Hive sent or the files changed, from which
script, and whether it worked. Newest last;
the Toolbox only ever adds to it.
_Avoid_: audit trail, history

### Reading and loading

**Lineage**:
The record of which table columns feed each output column of a Statement.
_Avoid_: provenance, trace, data flow

**Partition**:
A slice of a table: the rows that share one value of each column the table is partitioned by.
Each table has its own partition columns, of any kind - a date, a region, a load - or none, and
a Statement should constrain them rather than read the table whole.
_Avoid_: shard, segment, Date partition

**Bucket**:
One of a fixed number of files a table's rows are spread into by hashing some of its columns,
which makes joins and lookups on those columns cheaper. Unlike a Partition, a Statement never
bounds it.
_Avoid_: shard, chunk, cluster

**Statistics**:
What the warehouse has counted about a table's Partitions and their columns - how many rows and
bytes, how many different values - from which it picks how to join the table. Counting them
changes no row, and they can be counted again at any time.
_Avoid_: stats, metadata, metrics

**Plan**:
How Hive will run a Statement - which tables it reads, with which filters, and how it joins
them - shown without running it.
_Avoid_: query plan, execution plan, explain output

**Map join**:
A join in which the warehouse copies a small table whole to every worker, so the big table's
rows are matched where they are, without first being sorted and sent across the cluster. Hive
chooses one by itself from the tables' sizes and statistics; `broadcast=True` asks for one.
_Avoid_: replicated join, small-table join

**Session setting**:
A Hive `SET` the user sends before a Statement, which holds for the rest of the session. A named
set of them can be kept and sent again in one step. In Python, `hive_settings(...)` gives back
`SessionSettings`, the name a type hint uses.
_Avoid_: config, option, parameter

**Load limit**:
A check that refuses a Statement that would read or return more than the cluster or the notebook
can take, unless the call that reads or returns too much carries the limit's opt-out.
_Avoid_: guard, quota, throttle, safety check

### Learning the Toolbox

**Example database**:
A small set of made-up tables, with their Table references, on which Worked examples run and each
Guard and Warning is shown catching a wrong number. It ships inside the Toolbox, so Statements
can be practised on it at work without touching the warehouse.
_Avoid_: fixture, sample data, demo database, test tables

**Worked example**:
A Statement written for the Example database's tables, or for a Saved table made from them, shown
with the Python that builds it and the Hive it emits. It sits either in a Toolbox function's docstring or on its own.
_Avoid_: case, sample, recipe, demo

**Example project**:
A Project made for the Example database's tables, as the user makes their own - its Table
references, Building blocks and a Table notebook per Saved table, filled in - to read and copy
from. Where a Worked example shows one Statement and its Hive, an Example project shows the files
around many; a Template is the empty shape to fill in.
_Avoid_: sample project, demo, template, starter kit

**Template**:
The shape of one of the user's own scripts, with its specifics left out - the tables, columns,
values and names - each marked as a placeholder, to copy into a project and fill in; a Template
with a placeholder left in doesn't run. Where an Example project shows scripts filled in for the
Example database, a Template is the empty shape of such a script, or of one a project keeps
beside them, such as a Table notebook. The Toolbox ships its Templates inside it, and a
Project keeps its own copies in its admin folder, to edit and add to.
_Avoid_: skeleton, boilerplate, stub, scaffold, example

**Example gallery**:
The searchable page holding every Worked example, generated from them, which ships in the
Toolbox.
_Avoid_: cookbook, docs site, examples page

**README**:
The page the Clean branch opens on: a tutorial of numbered steps, from installing the Toolbox
to a project of the user's own, each pointing to the How-tos that walk through it. A How-to is never called a
tutorial; what changed in each version is in the change notes, never in the README.
_Avoid_: manual, guide, docs

**How-to**:
A walkthrough of one job from start to finish, as one notebook: its goal, when you'd use it, its
steps, how to check it worked, the mistakes people make first, and what to read next. Its steps
run on the Example database; what works only at work, such as your own query and execute, is
shown and not run. There are Getting started how-tos and Intermediate how-tos, on a page the
Toolbox ships beside its Example gallery.
_Avoid_: tutorial, guide, lesson, recipe

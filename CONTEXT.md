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
The branch holding only the Toolbox (its Templates inside it), the pages in its docs folder
(the How-tos, the Example gallery, the Workflows overview and the Example projects page), the
Copilot files, and their README, change notes, license and requirements.txt, generated from the
Dev branch and never edited by hand.
_Avoid_: release branch, prod branch, copy branch

**Dev branch**:
The branch where all work happens: the Toolbox plus its tests, agents and tracker.
_Avoid_: develop, internal branch, testing branch

**Warehouse**:
Where Statements run at work: the tables, and the Hive that runs a Statement's Hive on them.
Each Toolbox user has one; the Example database stands in for it. The Toolbox reaches it only
through the user's two calls: `query`, which gives back rows as a DataFrame, and `execute`, which
gives back nothing. Both pass the Hive to the user's connection, which each notebook gives
the Project's warehouse.py with `connect(...)` before either is called, so each notebook, a
Scheduled run among them, picks the account it runs as. The user chooses which call sends each
Statement; the Toolbox never chooses for them.
_Avoid_: backend, engine, server, platform, send

**Dev Database**:
The database in the Warehouse where the user may create and write tables of their own: each
Saved table is built, written and compared there first.
_Avoid_: sandbox, scratch schema, my db

**Prod Database**:
The database others read the user's finished Saved tables from. A table reaches it only once
promoted from the Dev Database.
_Avoid_: live, production schema

**Database settings**:
What differs between the Dev Database and the Prod Database, kept as one set of values for
each, under the same names in both: the database's name, the folder its tables' files go
under, the account its connection runs as, and any value of the user's own. Carrying a table
or a Building block from dev to prod swaps one Database's settings for the other's, name by
name, so a value missing from one of them is refused.
_Avoid_: config, environment, profile, Session settings (a Hive SET)

**Promotion**:
The user's choice to carry one or more Saved tables from the Dev Database to the Prod
Database: a prod copy of each table's code and of each Building block it uses, each prod copy
reading the prod copies of the others promoted with it and the Prod Database's settings. The
dev table stays the source: a change is made in dev and promoted again, never in the prod
copy, so dev's Building blocks may change freely while prod's change only when promoted. A
table is promoted only once each of its Decisions is made, and with each dev table it reads.
A Conversion's table whose compare failed, or that wasn't compared, is promoted all the same,
named as such first, since the choice is the user's (Toolbox 8.10).
_Avoid_: deploy, release, convert to prod, publish

### The user's own scripts

**Project**:
The user's folder at work holding the Toolbox and their own scripts in one fixed layout: an
admin folder, which holds a folder per Workflow, a flat folder of Table references, Building
blocks, a Table folder for each Saved table they build, and a folder for each Scheduled run.
It records, in its admin folder, the Toolbox version that last wrote it.
_Avoid_: workspace, repo, codebase

**Scheduled run**:
A notebook in a Project that an outside scheduler runs top to bottom: it takes the values the
scheduler passes in, builds the Statements it names from the Table notebooks' logic and its own,
with the writes of each Project table they read, in Lineage order, and only then sends them,
giving back what each read returns. It runs what it names, in whichever Database that is; two
Scheduled runs may write the same table, and keeping them from stepping over each other is the
user's design. Within its own cell a Guard Hive runs past as written only warns.
_Avoid_: job, DAG, pipeline, schedule

**Parameter**:
A value an outside scheduler passes into a Scheduled run, one of the names in its parameters
cell, read by that name's type hint and checked before anything is built, so the run refuses a
value it can't read rather than run with it. A parameter may stand in for a Run value for that
run only, by the Run value's name; it is neither a Run value, a Script tag nor a Session
setting.
_Avoid_: argument, variable, input, setting

**Table folder**:
The folder in a Project that holds everything about one Saved table the user builds: the
notebook whose Statements create and write it, its past Lineage, and the Hive the notebook's
logic sends, which the notebook's `export_hive()` writes beside it to read, never to edit. Only
a Project action creates or removes one.
_Avoid_: table directory, table project, model folder

**Table notebook**:
The notebook in a Table folder whose cells create, preview and write its Saved table, made from
a Template when the Table folder is made. Its logic cell, the one whose first line is
`# logic`, holds the table's logic alone, its imports and its functions, so other notebooks
can load and use that logic without running the rest.
_Avoid_: table script, pipeline notebook, job

**Registry**:
The Project's list of every Table folder, Table reference, Building block, Scheduled run and
Conversion folder a Project action made, and when each was removed. What is in the Project but not in the Registry was made by hand; what is in
the Registry but not in the Project was moved or deleted by hand.
_Avoid_: manifest, inventory, index

**Project action**:
A one-time change to a Project's files - starting a Project, creating or removing a Table
folder, a Building block or a Scheduled run, adding Table references, upgrading the Project, converting Hive,
comparing a Conversion's tables, promoting tables and archiving a Conversion folder - run from
the admin folder or a Workflow's notebook, and recorded in the Admin log. One that takes a name
takes a list of names too, each done in turn. Where an Admin statement changes the warehouse, a
Project action changes only files. The user makes only the Project's folder and the copy of the
Toolbox in it; a Project action makes every other file, for the user to fill in.
_Avoid_: admin statement, migration, setup step

**Workflow**:
An ordered list of steps that takes a Project from its start materials, what the user brings,
to one end goal, such as converting scripts or promoting tables. The user names its inputs,
the start materials it works on, such as the tables, once, in its notebook's names cell, and
answers each Decision a step waits on in its decisions cell.
Each step touches only files
(or only prints), makes a call to the Warehouse the user makes on purpose, asks a decision only
the user can make, or is fiddling: a step done by hand though the code already knows the
answer, which the Toolbox works to remove.
_Avoid_: wizard, menu, pipeline, recipe, playbook

**Decision**:
One thing about one table that only the user decides, which the table's files show made or
not: its location, its Key, a column type the Toolbox could only guess, the value a Script
tag stands for, the Partitions its Seed copies, the name proposed for a table made from a
Formula workbook, the database table proposed for cells a PivotTable reads, each Pivot
filter kept or its every slice kept instead, or a `<...>` left to fill in. The user answers
each in a Workflow's decisions cell, and a step writes each answer into the table's Table
reference. An answer may be given once for every table of a batch, and a table's own answer
overrides it; an answer may also be a Run value's function, called each time the table is
written. A `<...>` is filled in by hand. A new Saved table's
`<COLUMNS>` is the one a step writes, from its logic. A Workflow's step that waits on Decisions
is done once each is made. A Decision is never ticked by hand: the files say whether it is made.
_Avoid_: box, checklist item, TODO

**Upgrade**:
A Project action that carries a Project's files from the Toolbox version that last wrote them
to the one copied in, one version at a time. It makes the changes that need no judgement,
archiving each file first, and marks every one it leaves for the user with an
`# UPGRADE` comment at the line and a box on a checklist. It never changes the warehouse. Every
Toolbox version ships the step from the one before.
_Avoid_: migration, port, conversion, update script

**Conversion**:
A Project action that reads Hive someone else wrote, one query or one or more scripts, or a
Formula workbook, and writes the user's own code for it. Each table the scripts write becomes a Saved table in the
user's Dev Database, named <table>_<its database>, and what reads it after its write reads
that copy; a Staging table may instead be folded into the tables that read it. One query
alone becomes a Saved table named for the batch, and in a batch of several scripts, each
script that holds one query alone a Saved table named for its file. Each final of a Formula
workbook is a query alone, a Saved table named for its Table or its PivotTable.
Each gets its Table folder, whose notebook's Statement gives the same rows, its Table
reference, and a checklist of what only the user can decide. What no Toolbox function writes yet is left as Unchecked
pieces, and each risk the original took is marked `# CONVERSION:` for the user to decide.
_Avoid_: migration, port, translation, import, upgrade

**Original**:
The table a converted script writes, in the warehouse already, which its Saved table copies:
a Saved table that reads itself is seeded once with the original's rows, and is compared with
it. A prod copy's original is its dev copy's original, not the dev copy.
_Avoid_: source table, old table

**Batch**:
One or more scripts of Hive converted together by one Conversion, with every statement in
them ordered by what reads what; a Formula workbook in it gives a script for each of its
finals. Where each script is, and the list of what each statement became, are kept in the
convert Workflow's folder, under the batch's name: a script read from a file, or a workbook,
is read where it is, never copied, and only Hive given as text, or a workbook's finals' Hive,
is kept there.
_Avoid_: job, bundle, script set

**Conversion folder**:
A batch's index, in the convert Workflow's folder: where each script is (Hive given as text,
and each workbook final's Hive, kept in its scripts/), their order, what each statement became and the tables that came from
them. What belongs to one table, the statements it came from, the scan and its checklist, is
in that table's own Table folder.
_Avoid_: staging folder, draft, scratch folder

**Script tag**:
A `<PARM="NAME"/>` in Hive someone else wrote, NAME being whatever variable name that program
used, such as `<PARM="PERIOD_END"/>`, which it filled in before Hive read it. It stands for something in one table's
statements only: the same tag may stand for a different value in another table. A Conversion
reads past each, where a value goes, and leaves it as a Decision of the table it ends up in;
the Hive text the user answers stands in its place, and answering again changes it.
_Avoid_: parameter (a Scheduled run's), PARM, variable, placeholder

**Run value**:
The value a Python function gives each time a Statement is built, any function, the
user's own or a library's, filled in where a value goes, where a Script tag stood or where a
seed's limit goes, such as the latest Partition the warehouse holds. The Toolbox writes it
into the Hive as plain text, so the Hive it sends, and the Hive a dry run shows, hold the
value itself, and the Statement's lineage traces each one standing as a value: the
function, what it was given, the value it gave, and each table the Toolbox read for it while it
ran.
_Avoid_: parameter (a Scheduled run's), variable, runtime param, Hive variable

**Hivevar**:
A `${hivevar:NAME}` in the Hive, which the warehouse fills in each time the Hive runs, from
a value given at that moment. It's how a Script tag's place is left for whatever runs the
Hive to fill in, where a Run value's is filled in as the Statement is built: the Script tag
stays as it is, and a Hivevar is one answer it can be given,
`hivevar("PERIOD_END", default=...)`, standing in quotes where its value does. When the
Toolbox runs the Hive, it sends the value as `SET hivevar:NAME=value` before each write
holding it: the default, Hive text or a Run value's function, unless a Scheduled run gives
another by its NAME. An export writes the default into a `.hivevars` file beside the `.hql`
instead, since Hive lets a SET in a script beat a value given on the command line: a
scheduler passes it when it runs one Statement's `.hql`, or a Table notebook's write() steps,
never its create() or seed(); a Scheduled run's is only to read, as the run sends its own.
_Avoid_: placeholder, runtime param

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
table's Key is worked out from how its Statement makes its rows, and so a Conversion
proposes a Saved table's Key, the one its query makes, which the user may change and its
compare checks on the dev copy. `check_key(...)` and
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
In a Scheduled run's own cell, one Hive runs past as written warns instead, as a Warning does.
Guards protect the answer.
Load limits protect the cluster, and are not Guards.
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

**Staging table**:
A table a long script writes with a CREATE TABLE ... AS SELECT only so a statement after it can
read it, as a temporary table, or one the script DROPs later. A Conversion
folds one, its query a Derived table in each table that reads it, or keeps it a Saved table of
its own, as the user chooses: folded is proposed for a temporary or DROPped one.
_Avoid_: temp table, scratch table, intermediate table

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
`Subtotals`, which go in GROUP_BY to ask for these rows: the name a type hint uses. It is not
Excel's **Total Row**, which a Saved table never holds.
_Avoid_: total row (for this row; Excel's own is the Total Row), rollup row, summary row

**Total Row**:
Excel's row of totals under a Table, turned on in Table Design and filled in from a list in
each column's last cell. A Formula workbook totals a Table with it, never with a row of data
typed in; Copilot writes it as a query of its own, one row, never as a Subtotal row in the
Table's query, since a Saved table refuses one.
_Avoid_: totals row, summary row

**Pivot filter**:
What a PivotTable leaves out, as the workbook was last saved: its Report filter, the items
hidden on a Row or Column field, a slicer's selection, a Timeline's dates, or a value filter
such as Top 10. It is converted as the condition it is, its values written in. Keeping it is a
Decision of the table it ends up in, whose other answers keep every slice instead: the filtered
column becomes part of what one row is, each value is written as its own batch, or each value
gets a table of its own, as many tables as the filter has values. A value filter, such as Top
10, keeps items by their rank among the rest, which changes as the rows do, so it has no fixed
value to write a batch or a table for: it is kept, or folded to keep every item. A table per
value needs the values the PivotTable's cache held, so for a script's Hive alone, which holds
no cache, that answer waits until the script is converted beside its workbook.
_Avoid_: slicer filter, page filter, applied filter, sliced view

**Saved table**:
A real table in the warehouse that a Statement writes into, which other Statements then read through
its own Table reference, like any other table. It is what Hive calls an external table: its
files are in a folder of its own, which its Table reference names along with how it is
stored; the user's own Statements are the only ones
that write it. Hive's other kind, a managed table, keeps its files where the warehouse chooses:
create_table made those before 5.0, and admin.move_to_own_folder moves one to a folder of its
own.
_Avoid_: materialized view, cache, temp table, output table

**Rebuilt table**:
A Saved table each write replaces whole, so its first write leaves it complete and it needs
no Seed. Which kind a table is, Rebuilt or History, is one of its Decisions. What its query
computes doesn't decide it: a summary rebuilt every run is a Rebuilt table.
_Avoid_: aggregate table, full refresh

**History table**:
A Saved table each write adds rows to, or replaces some of, such as one Partition for the
run's date, keeping the rest: what reads it expects its past rows to be there. A new copy
holds only what its writes have added since, so it needs a Seed to be usable from its first
day. A daily summary that keeps every day's Partition is a History table.
_Avoid_: historical table, incremental table, aggregate table

**Seed**:
The one-time load of a History table's past rows, in dev or in prod, before its first write,
so the table is usable from that first day: copied from its Original when a Conversion made
it, and otherwise written by its own write for each past Partition. It runs once; a write
runs every time. Its limit, one of the table's Decisions, picks which of the past Partitions
it loads, so years of rows the table doesn't need are left behind. In Python, `seed()` in its
Table notebook.
_Avoid_: backfill, preload, bootstrap, initial load

**Unchecked statement**:
Hive text the user writes by hand and runs through the Toolbox, as a Statement is run, when no
Clause function covers it yet. No Guard, Warning or Load limit looks inside it; text that drops,
alters or truncates a table only gets a note naming the admin function that does the job, where
one does. Lineage
shows it as one opaque step. Each one marks something the Toolbox should learn to write. In
Python, `unchecked_hive(...)` gives back an `UncheckedStatement`, the name a type hint uses.
Its smaller kin, the Unchecked expression and the Unchecked derived table, sit inside a
Statement.
_Avoid_: raw SQL, passthrough, custom query

**Unchecked expression**:
Hive text the user, or a Conversion, writes in place of one Column or Condition that no Toolbox
function writes yet, inside an otherwise checked Statement. The Toolbox reads which columns it
names, each written as a `{name}` placeholder and passed as the Column itself, so Lineage
traces it, but no Guard looks inside it. A Hive variable in it, such as `${hivevar:day}`, is
Hive, kept as written, never a placeholder. In Python, `unchecked_column(...)` and
`unchecked_condition(...)` give one back.
_Avoid_: raw expression, SQL snippet, passthrough

**Unchecked derived table**:
A Derived table whose Statement is Hive text kept as written, with its output columns
declared, for a piece no Clause function writes yet. It is read like any Derived table and
shown as one opaque box in Lineage. It has no Key the Toolbox can see unless its `key=[...]`
names one, which the Toolbox takes on trust. In Python, `unchecked_derived(...)` gives back a
`Table`.
_Avoid_: raw CTE, unchecked view

**Python step**:
A change the user makes to data in Python, outside any Statement, and saves to a table
themselves, declared to the Toolbox with the columns it read and the table it wrote. Lineage
shows it as one opaque step naming the function that made the change and where it lives.
Elsewhere the Toolbox never moves its data, but a Scheduled run writes the table of one given
the SELECT its function takes: its rows pulled through `query`, saved through `execute`. In
Python, `python_step(...)` gives back a `PythonStep`, the name a type hint uses.
_Avoid_: transform, pandas step, UDF

**Admin statement**:
A Statement from the Toolbox's admin module that changes a Saved table's definition or deletes its
data, such as dropping a table or some of its Partitions, adding columns, setting its properties or moving
it to a folder of its own. It runs like any Statement, shows what it will change and what can't
be undone before its Hive, and is refused for any table that isn't one of the user's Saved
tables. The admin module is imported by name, apart from the everyday names.
_Avoid_: one-time action, migration, maintenance

**Admin log**:
The text record the Toolbox keeps of every Admin statement, Unchecked statement, Statement
holding an Unchecked expression or Unchecked derived table, and Project action the user has
run: when, on which table, the Hive sent or the files changed, from which script, and whether it
worked. Newest last;
the Toolbox only ever adds to it.
_Avoid_: audit trail, history

### Reading and loading

**Lineage**:
The record of which table columns feed each output column of a Statement. It is a
Statement's, column by column: the drawing of a whole Project's tables is its **Project
lineage**.
_Avoid_: provenance, trace, data flow

**Project lineage**:
The drawing of every Saved table of a Project, the tables each one's write reads, and the
Scheduled runs that write it, a table more than one run writes marked and a loop among them
drawn red: table by table, with no columns. Written by hand, by
`project.export_project_lineage()` into `admin/lineage/`, never by a Scheduled run (2026-11-09).
_Avoid_: dependency graph, DAG, data map

**Effective logic**:
What a column of a Saved table or of a Scheduled run's SELECT really holds: its own logic and
the rows that count for it, with each Saved table's column it reads replaced by that column's
Effective logic, all the way down to the tables the Project doesn't write. Its own Statement
may stay the same while its Effective logic changes, when something it reads changes. A Run
value counts as its function and what it was given, never the value it gave, and an Unchecked
statement, Unchecked derived table or Python step counts as a whole (2026-11-17).
_Avoid_: full lineage, resolved logic, deep lineage

**Lineage state**:
The Project's record of each column's own logic and Effective logic, each Table reference's
columns and types among them, to which a row is added each time one changes, saying when, at
which commit and from which call. Recorded by the Project actions that change a table or
Table reference, a Table notebook's Hive export, an Upgrade, or by hand, never by a Scheduled
run, and never reaching the warehouse. It is a record, not a drawing: neither a Statement's
Lineage nor the Project lineage (2026-11-17).
_Avoid_: snapshot, lineage table, lineage history

**Lineage difference**:
What changed in the Lineage state between two points, by table and column: each Own change and
Inherited change, with the chain from each inherited one down to the change it comes from,
and when each changed table was next written. A change only the Toolbox's new way of writing
Hive made, recorded by an Upgrade, is shown apart, never as an Own change (2026-11-17).
_Avoid_: diff, diff file, changelog

**Own change**:
A change to a column's own logic, or the rows that count for it, in its own Statement, or to a
Table reference's column: added, removed or retyped. A change to a Building block the
Statement uses is an Own change of each column it changes, named as coming from that block.
_Avoid_: direct change

**Inherited change**:
A change to a column's Effective logic while its own logic stayed the same, because a column
it reads, at some table up the chain, had an Own change.
_Avoid_: induced change, indirect change, side effect

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
_Avoid_: config, option, parameter (a Scheduled run's)

**Load limit**:
A check that refuses a Statement that would read or return more than the cluster or the notebook
can take, unless the call that reads or returns too much carries the limit's opt-out.
_Avoid_: guard, quota, throttle, safety check

### Learning the Toolbox

**Example database**:
A small set of made-up tables, with their Table references and a query and execute over them, on
which Worked examples run and each Guard and Warning is shown catching a wrong number. It is the
Dev branch's alone, beside the Toolbox and never in it (Toolbox 8.7): the Toolbox holds nothing
runnable for examples, so on the Clean branch the Example database is read as pages, each
example showing what it gave, never run. A docstring's example names its tables, `query` and
`execute` alone, in the place of the user's own.
_Avoid_: fixture, sample data, demo database, test tables

**Worked example**:
A Statement written for the Example database's tables, or for a Saved table made from them, shown
with the Python that builds it and the Hive it emits. It sits either in a Toolbox function's docstring or on its own.
_Avoid_: case, sample, recipe, demo

**Example project**:
A Project made for the Example database's tables, as the user makes their own - its Table
references, Building blocks and a Table notebook per Saved table, filled in - to read and copy
from. Where a Worked example shows one Statement and its Hive, an Example project shows the files
around many; a Template is the empty shape to fill in. Its notebooks connect to the Example
database, so it runs on the Dev branch alone, and the Clean branch reads it as pages (Toolbox
8.7).
_Avoid_: sample project, demo, template, starter kit

**Template**:
The shape of one of the user's own scripts, with its specifics left out - the tables, columns,
values and names - each marked as a placeholder, to copy into a project and fill in; a Template
with a placeholder left in doesn't run. Where an Example project shows scripts filled in for the
Example database, a Template is the empty shape of such a script, or of one a project keeps
beside them, such as a Table notebook. The Toolbox ships its Templates inside it, and a
Project keeps its own copies in its admin folder, to edit and add to.
_Avoid_: skeleton, boilerplate, stub, scaffold, example

**Copilot files**:
Plain-text files a user loads into Microsoft Copilot before asking it for Toolbox code: one for
each objective, such as building a Statement or converting Hive, each small enough for Copilot
to take whole, and one that says which to load. They teach Copilot the Toolbox's names and
how a Statement is built, so it writes code the user would otherwise write by hand.
_Avoid_: prompt pack, system prompt, cheat sheet

**Metric request**:
Text a user writes, with Copilot's questions (Copilot file 19), that says exactly what each
new column of a metric should hold, built on the user's Column definitions, in a section per
column, each column asked for on its own: its name and one plain sentence, its formula in plain
maths, each quantity in it by its table and column, one row per what, the days counted, what is
left out, the edge cases, how to check it in words, and the questions still open, each Gap
among them with its fix. It is not SQL and works out no numbers: it is given to a chatbot that
knows the databases, which defines the columns from it.
_Avoid_: spec, prompt, requirements doc

**Column definitions**:
The list of a user's tables' columns and what each holds, pasted from their data dictionary,
which a Metric request is built on. Often messy: some vague, some blank, a unit unstated.
_Avoid_: schema, data dictionary (the definitions are what the user pastes from it)

**Gap**:
What a Metric request's metric needs that no Column definition gives, such as a time of day no
table keeps, or a column whose definition is too vague to decide. The request names it under
"Missing data:" with a "Fix:", what to ask or add, and never puts another quantity in its place
unasked.
_Avoid_: missing field, unknown

**False premise**:
What a user says as fact about their data that their own Column definitions or Sample rows
refute, such as "a NULL status is a crash" where the definitions say NULL means still running.
Copilot names what refutes it, pushing back while it asks or in the request, and the request
builds on what the data holds. If the user keeps their reading, the request builds on that.
_Avoid_: wrong assumption, user error

**Quantity**:
A number a Metric request's formula uses, such as "failed runs", said so exactly that a chatbot
can't read it two ways: which rows count, by which column's values, and what is left out.
_Avoid_: measure, field, variable

**Grain**:
What one row of a new column's result is, and which rows there are, as a Metric request says
it: "one row per job with a finished run", "one row per team per day".
_Avoid_: level, granularity, key (a Key is a table's)

**Sample rows**:
Rows a user pastes into a Copilot chat, from a table or a spreadsheet, which show Copilot the
columns and values there are; a Metric request names some of them in how to check it, and
works out nothing on them.
_Avoid_: sample data, test data, dataset

**Formula workbook**:
An Excel workbook laid out so its formulas can be read as SQL: a sample of raw data in Excel
Tables, each calculation in a Table's formulas, a Power Query step or a PivotTable, in any mix,
and fixed values in a Table of their own. What reads what decides each piece's part, so which
of them a calculation uses doesn't matter. A Table's typed columns stand for the database table it samples; which Tables
are final is read from what reads what, never declared; and the Tables keep whatever names they
have. A person moves a presentation workbook's
data and formulas into one, so Copilot can turn it into Hive without anyone explaining the
workbook. A final Table, one no other Table reads, is a table the person wants to keep: its
Hive becomes a new Saved table.
_Avoid_: state table, Excel template, mapping sheet, custom table view

**Example gallery**:
The searchable page holding every Worked example, generated from them, which ships in the
download's docs folder.
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
shown and not run. There are Getting started how-tos and Intermediate how-tos, on a page in the
download's docs folder beside the Example gallery.
_Avoid_: tutorial, guide, lesson, recipe

**Workflows overview**:
The page in the download's docs folder that shows every Workflow, and the Excel path, as one
drawing: which leads into which, each one's steps in a few words, and the places people trip.
Each Workflow's full walkthrough is its How-to.
_Avoid_: workflow map, flowchart, dashboard

**Example projects page**:
The page in the download's docs folder that shows each Example project as it ran on the Dev
branch: its folders, each notebook's cells with what they printed, and its lineage pages.
_Avoid_: project gallery, sample projects page

**Excel path**:
The way from a Formula workbook to Saved tables: a person fills in the workbook, Copilot
turns it into Hive or the convert Workflow reads the workbook itself, and the convert Workflow
makes the result the Toolbox's own.
_Avoid_: Excel workflow, spreadsheet import

**Workbook check**:
A Conversion's check of a Formula workbook's Hive, whoever wrote it: each final's rows worked out
from the workbook's own Tables, on this computer, and compared with the values Excel last stored.
It never reads the warehouse, whose rows have moved on from the workbook's. A difference is
listed, cell by cell, and stops nothing.
_Avoid_: offline check, sample test, workbook test

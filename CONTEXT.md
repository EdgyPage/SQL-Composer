# The Toolbox: sqlglot Composer and Spark Composer

A toolbox for writing Hive SQL in Python. Queries are composed from Python functions and a small
stack of the user's own scripts, emitted as a single Hive SQL string - sent to a query API that
accepts only strings, or run on Spark - and traced back to the table columns they read.

## Language

### What ships to work

**Toolbox**:
The set of Python functions that compose Hive SQL - the only thing copied to work. It comes in two
Editions, and is copied as the Composer core and one Edition.
_Avoid_: library, package, framework, SQL module

**Edition**:
One of the two forms the Toolbox comes in, with the same functions and almost the same Hive:
sqlglot Composer, which needs sqlglot at work, and Spark Composer, which needs pyspark and runs
its Hive on Spark. A notebook uses one.
_Avoid_: flavour, variant, port, fork, backend, dialect

**Composer core**:
The part of the Toolbox both Editions share, written once: every function a user calls. An Edition
adds what is its own, how it writes its Hive and runs its Example database.
_Avoid_: base, common, shared library, framework

**Toolbox version**:
The feature number of the Toolbox (`4.0`), raised only when a big feature lands, and shared by both
Editions. Two copies of the same Toolbox version are told apart by when they were exported.
_Avoid_: release, build, hash

**Clean branch**:
The branch holding only the Toolbox's Composer core, its Editions, each Edition's copy of the
Example projects and the Templates, and their README, generated from the Dev branch and never
edited by hand.
_Avoid_: release branch, prod branch, copy branch

**Dev branch**:
The branch where all work happens: the Toolbox plus its tests, agents and tracker.
_Avoid_: develop, internal branch, testing branch

**Warehouse**:
Where Statements run at work: the tables, and the Hive or Spark that runs a Statement's Hive on
them. Each Toolbox user has one; the Example database stands in for it.
_Avoid_: backend, engine, server, platform

### The user's own scripts

**Level**:
One of three tiers of the user's own scripts. A script imports only from lower Levels and from the
Toolbox, never from a higher or equal Level. A script that runs Statements in order, such as an
Example project's run_pipeline.py, sits above the three Levels, so it may import from all of them.
A settings.py beside them, which holds what Statements read about each table and imports none of
the user's scripts, is Level 0, like the Table references.
_Avoid_: layer, tier, stage

**Table reference**:
A Level 0 script describing one table: its columns and their types, its Date partition and key,
and the filters that concern that table alone.
_Avoid_: table config, schema file, declaration, model, standard query

**Building block**:
A Level 1 piece of a Statement - a filter, a join or a sub-query - reused across Statements.
_Avoid_: fragment, component, snippet, helper

**Statement**:
A Level 2 query, assembled from Table references and Building blocks, that becomes one Hive SQL
string.
_Avoid_: report, case, output script

### Writing a Statement

**Clause function**:
A Toolbox function named after one SQL clause - `SELECT`, `FROM`, `WHERE`, `GROUP_BY` - and
written in SQL order. A Statement is a list of them.
_Avoid_: builder, chain, method

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
_Avoid_: view, temp table, CTE (the CTE is how it lands in the string, not what it is)

**Saved table**:
A real table in the warehouse that a Statement writes into, which other Statements then read through
its own Table reference, like any other table.
_Avoid_: materialized view, cache, temp table, output table

### Reading and loading

**Lineage**:
The record of which table columns feed each output column of a Statement.
_Avoid_: provenance, trace, data flow

**Partition**:
A slice of a table that a Statement should constrain rather than read whole.
_Avoid_: shard, bucket, segment

**Date partition**:
The one date column a table is partitioned by, which every Statement reading the table must bound
at both ends.
_Avoid_: dt, partition key, date column

**Load limit**:
A check that refuses a Statement that would read or return more than the cluster or the notebook
can take, unless the call that reads or returns too much carries the limit's opt-out.
_Avoid_: guard, quota, throttle, safety check

### Learning the Toolbox

**Example database**:
A small set of made-up tables, with their Table references, on which Worked examples run and each
Guard and Warning is shown catching a wrong number. It ships inside each Edition, so Statements
can be practised on it at work without touching the warehouse.
_Avoid_: fixture, sample data, demo database, test tables

**Worked example**:
A Statement written for the Example database's tables, or for a Saved table made from them, shown
with the Python that builds it and the Hive it emits. It sits either in a Toolbox function's docstring or on its own.
_Avoid_: case, sample, recipe, demo

**Example project**:
A folder of the user's own scripts laid out as a project at work should be - Table references,
Building blocks, Statements and a script that runs them in order - written for the Example
database's tables, to read and copy from. Where a Worked example shows one Statement and its
Hive, an Example project shows the files around many; a Template is the empty shape to fill in.
_Avoid_: sample project, demo, template, starter kit

**Template**:
The shape of one of the user's own scripts, with its specifics left out - the tables, columns,
days and names - each marked as a placeholder, to copy into a project and fill in; a Template
with a placeholder left in doesn't run. Where an Example project shows scripts filled in for the
Example database, a Template is the empty shape of such a script, or of one a project keeps
beside them, such as a notebook's first cells. Each Edition ships a starter set and an
intermediate set, beside its Example projects.
_Avoid_: skeleton, boilerplate, stub, scaffold, example

**Example gallery**:
The searchable page holding every Worked example, generated from them; each Edition ships its
own.
_Avoid_: cookbook, docs site, examples page

**How-to**:
A walkthrough of one job from start to finish, as one notebook: its goal, when you'd use it, its
steps, how to check it worked, the mistakes people make first, and what to read next. Its steps
run on the Example database; what works only at work, such as your own send, is shown and not
run. There are Getting started how-tos and Intermediate how-tos, on a page each Edition ships
beside its Example gallery.
_Avoid_: tutorial, guide, lesson, recipe

# SQL Composer

A toolbox for writing Hive SQL in Python. Queries are composed from Python functions and a small
stack of the user's own scripts, emitted as a single string for a query API that accepts only
strings, and traced back to the table columns they read.

## Language

### What ships to work

**Toolbox**:
The set of Python functions that compose Hive SQL - the only thing copied to work.
_Avoid_: library, package, framework, SQL module

**Toolbox version**:
The feature number of the Toolbox (`3.1`), raised only when a big feature lands. Two copies of the
same Toolbox version are told apart by when they were exported.
_Avoid_: release, build, hash

**Clean branch**:
The branch holding only the Toolbox, generated from the Dev branch and never edited by hand.
_Avoid_: release branch, prod branch, copy branch

**Dev branch**:
The branch where all work happens: the Toolbox plus its tests, agents and tracker.
_Avoid_: develop, internal branch, testing branch

### The user's own scripts

**Level**:
One of three tiers of the user's own scripts. A script imports only from lower Levels and from the
Toolbox, never from a higher or equal Level.
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

**Derived table**:
A Statement given a name so another Statement can read from it, with its output columns checked
like a Table reference's. It lives only inside the Statement that reads it, and is never stored.
_Avoid_: view, temp table, CTE (the CTE is how it lands in the string, not what it is)

**Saved table**:
A real table that a Statement writes into on the server, which other Statements then read through
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

# SQL Composer

A toolbox for writing Hive SQL in Python. Queries are composed from Python functions and a small
stack of the user's own scripts, emitted as a single string for a query API that accepts only
strings, and traced back to the table columns they read.

## Language

### What ships to work

**Toolbox**:
The set of Python functions that compose Hive SQL - the only thing copied to work.
_Avoid_: library, package, framework, SQL module

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
A Level 0 script describing one table: its columns, and the standard queries against it.
_Avoid_: table config, schema file, declaration, model

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

**Derived table**:
A Statement given a name so another Statement can read from it, with its output columns checked
like a Table reference's.
_Avoid_: view, temp table, CTE (a CTE is only one way it can land in the string)

### Reading and loading

**Lineage**:
The record of which table columns feed each output column of a Statement.
_Avoid_: provenance, trace, data flow

**Partition**:
A slice of a table that a Statement should constrain rather than read whole.
_Avoid_: shard, bucket, segment

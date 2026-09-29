# What is the PySpark edition, and how does it sit beside SQL Composer?

Type: grilling
Status: resolved
Blocked by: -

## Question

The user asked (2026-09-29) for a slight restructure that splits the codebase into two versions,
one built on sqlglot and one on PySpark, with the whole of today's functionality in the PySpark
one: Toolbox, tests, Worked examples, lineage, docs and the admin decisions (versioning, export to
`main`). The user hasn't settled which one work will use, so both are to be built out. The tests
both pass should be shared as far as possible, for the most coverage and the least drift.

Decide what "the PySpark version" writes, what it is called, where it ships, how it is versioned
and tested, and how the code splits so that almost everything is shared.

## Answer

**A second Edition, `spark_composer` ("Spark Composer"), with the same 63 public names and no
sqlglot, which prints its own Hive text for `spark.sql()`.** The split follows the one place
sqlglot really sits: the leaves of a Statement.

The user's answers, 2026-09-29:

- **Output:** Spark SQL text, printed by the Toolbox itself (no sqlglot), run with `spark.sql()`.
  Not a DataFrame plan.
- **Name:** a different package, `spark_composer`, so both folders can sit side by side at work.
- **Clean branch:** one `main` holding both folders and one README.
- **Target:** Spark with Hive support, reading the same partitioned Hive tables.
- **Public names:** identical in both Editions, `to_hive` and `hive_function` included.
- **Version:** lockstep, one TOOLBOX_VERSION, raised to 3.0 when the PySpark edition ships.
- **Java:** the user installs JDK 17 on their machine.
- **pyspark:** `>=3.5.0,<4.1`, pin 4.0.4, CI at the bottom and the pin.
- **3.0 Hive changes, all approved:** `CAST(... AS STRING)` around week_start and month_start;
  backticks for Spark's reserved words; strict create_table types; refuse BEL, FF and VT in a
  value, shipped early as a 2.1 fix.
- **hive_function:** one shared argument and aggregate list in both Editions; calls compared and
  shown as written.
- **At work:** pyspark runs in the notebook kernel. Whether tables are ACID: not known yet.

The plan built on these answers (the architecture and tickets 02-26) is on the map. The user
approved it on 2026-09-29.

## Comments

**How the answer was reached (2026-09-29).** A read-only map of the repo (eight explorers and a
critic) found that a Statement, Clause and Table are plain Python and sqlglot sits only in
`Column._tree`, `Condition._tree`, the ORDER BY keys, `_ddl`, the writer, the Example database's
executor and the import self-check. Guards, Load limits, Spans, `by_day`, refusals, the lineage
graph and pages, and the self-check's file, version and stamp logic are already backend-neutral.
A design panel (five lenses and an integrating critic) then stress-tested the architecture. Its
refinements are in the tickets: a golden corpus before any refactor, replaying today's sqlglot
calls so SQL Composer stays byte-identical, sqlglot's tree shapes kept so lineage order doesn't
move, a helper process for the Spark Example database, and a shared-text sort so both Example
databases return identical rows.

**Rejected options.** A DataFrame-API edition (the user chose text); keeping sqlglot in the
PySpark edition with `dialect="spark"` (the user wants no sqlglot there); the same package name
for both (the user wants both side by side); a second clean branch (the user chose one `main`);
an in-process local Spark for the Example database (it would share the user's session).

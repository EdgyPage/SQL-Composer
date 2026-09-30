# A second Edition writes the same Hive without sqlglot, and runs it on Spark

Status: accepted

The user hasn't settled which engine work will use, so the Toolbox is built twice, as two Editions
with the same 63 public names: SQL Composer (`sql_composer`) writes its Hive with sqlglot, as ADR
0001 decided, and Spark Composer (`spark_composer`) writes the same Hive with a printer of its own
and runs it with `spark.sql()` on Spark with Hive support, for a work environment that has pyspark
and not sqlglot. To share almost everything, a Statement is held in a small tree the Toolbox owns
(`trees.py`), instead of in sqlglot's: its SELECT, write, CREATE or DROP, down to its columns,
conditions, calculations and sort keys. SQL Composer's `writing.py` rebuilds each Node with the
sqlglot calls it always made, so its trees, and its Hive, are what they were; Spark Composer's
prints the Nodes itself. Two files are written by hand in each folder: the one that turns the tree
into text, and the one that checks the library and runs the Example database; each Edition also
generates its own Example gallery. Every other file of `spark_composer` is generated from
`sql_composer`'s, and a test fails if a copy is stale.

This supersedes ADR 0001's rejection of "a hand-rolled AST and Hive renderer" in two ways: the
Toolbox now owns its tree in both Editions, and Spark Composer hand-writes its Hive. ADR 0001's
reason still stands, because escaping and precedence are where hand-written query builders go
wrong. It is met by keeping sqlglot as the printer's oracle. On `dev`, both Editions write a
golden corpus of about 380 cases, the escaping matrix and every Worked example, and a test lets
the two differ only where a declared row says why. SQL Composer still writes every string through
sqlglot.

## Considered options

- **A DataFrame-API Edition.** The user chose Hive text: it reads the same in both Editions, and
  every Guard and Load limit already reasons about the Statement, not about DataFrames.
- **Keeping sqlglot in Spark Composer** with `dialect="spark"`. This is the cheapest option,
  but the user wants an Edition that needs no sqlglot at work.
- **Vendoring sqlglot inside Spark Composer's folder.** It would still need no install, but the
  user would paste a copy of the very library the Edition exists to do without, far larger than
  the Toolbox, with no way to update it but the next export.
- **One folder that detects its library.** One folder would hold the writing code for both
  libraries, and the import self-check could no longer say which library a copy needs. This was
  rejected for two folders with the same file names.
- **Spark for the Example database in the user's own Python.** PySpark allows one SparkContext per
  process, so the Example database would either run on the user's real session or pin their
  session to its own. It runs in a helper process instead.
- **Storing trees in sqlglot's printed form.** This was rejected so that SQL Composer rebuilds
  exactly the sqlglot trees it builds today, and its Hive stays byte-identical on every sqlglot in
  its range.

## Consequences

- The Spark printer copies one sqlglot version's layout, so raising the sqlglot pin can force
  printer work; a test makes that visible.
- A calculation's Node keeps the shape of the sqlglot tree SQL Composer built for it, part for
  part, because the lineage orders a calculation's columns by a breadth-first walk. A test holds
  every tree in the golden corpus to its sqlglot tree.
- hive_function is kept as written, so a call sqlglot writes in another function's form, such as
  nvl as COALESCE, no longer equals that function's calculation.
- Both Editions share one Toolbox version and ship together on one Clean branch.
- The places their Hive differs are declared in one table on `dev`, each with its reason: division
  (Spark 4 refuses to divide by zero under ANSI), `hive_function` spelled as given, and a float
  written as a DOUBLE literal (Spark reads `0.5` as a DECIMAL).

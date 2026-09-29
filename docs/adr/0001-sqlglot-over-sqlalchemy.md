# Use sqlglot, not SQLAlchemy, to build and render SQL

Status: accepted; superseded in part by ADR 0002, which gives the Toolbox a tree of its own and
its second Edition, Spark Composer, a Hive printer of its own, rather than a Spark dialect string.
SQL Composer still writes its Hive with sqlglot.

The composer builds Hive SQL as an expression tree and renders it to a string that is handed to an
external query API. SQLAlchemy is the obvious choice for SQL in Python and it is the wrong one here:
it ships no Hive dialect, it delegates literal escaping to a DBAPI driver that does not exist in a
compile-only design, and it exposes no column-level lineage. sqlglot has Hive as a first-class
dialect, escapes Hive string literals correctly, and ships a lineage module.

## Considered options

**SQLAlchemy Core with a hand-written Hive dialect.** Its included dialects are PostgreSQL, MySQL,
SQLite, Oracle and SQL Server; Hive exists only as a third-party dialect via PyHive. Reaching Hive
means subclassing `DefaultDialect`, `IdentifierPreparer` and `SQLCompiler` for backtick quoting and
LIMIT rendering. Worse, the escaping argument that would justify the dependency does not apply:
SQLAlchemy delegates escaping to the DBAPI, `literal_binds` is documented as supporting only basic
types, and the docs warn against using it with untrusted input. We would be writing a dialect to get
a renderer we could not trust with values.

**A hand-rolled AST and Hive renderer.** No dependency, exact output, and lineage falls out of the
same nodes. Rejected because correct literal escaping and operator precedence are precisely where
hand-written query builders rot, and Hive is the base dialect of the Spark family - so sqlglot makes
a later move to Spark or Databricks a dialect string rather than a rewrite.

## Consequences

sqlglot is deliberately not semver: minor releases carry backwards-incompatible changes. The version
must be pinned exactly.

Its escaping is correct for Hive but is not a documented contract - no injection or untrusted-input
guidance exists in its docs, and the behaviour is only visible in source and dialect tests. The test
suite therefore carries an escaping matrix of its own, so that an upgrade changing this fails here
rather than in production.

Escaping applies only to string-literal nodes. Values injected as vars, unquoted identifiers, or by
parsing an interpolated string bypass it entirely. Values enter the tree as converted literals,
never as text.

sqlglot is a transpiler, not a validator: unsupported constructs are best-effort translated with a
warning by default. Generation runs with unsupported constructs raising instead, column resolution
is validated explicitly, and sqlglot's logger is escalated - none of these are on by default.

# Build Statements and DDL as Toolbox trees, so no shared file imports sqlglot

Type: task
Status: open
Blocked by: 12

## Question

Finish the move: `running.to_hive` still builds `exp.Select`, `exp.Insert` and `exp.With`, and
`create_table`/`drop_table` still put an `exp.Create`/`exp.Drop` on `Statement._ddl`
(`sql_composer/tables.py:1062-1065`, `:1093-1095`).

- Select, Insert, With, CTE, Partition, Create and Drop become Nodes; `writing.hive_statement`
  turns a whole Statement tree into text.
- A column's type is still checked on the `create_table` call, through `writing.hive_type`.
- Empty ticket 6's sqlglot exception: only `sql_composer/writing.py` and `sql_composer/engine.py`
  may import sqlglot, held by an AST test.
- Fix the comments that call these sqlglot trees (`sql_composer/clauses.py:68`, `:117`, `:119`).
- Finish the tree section of ADR 0002.

## Done when

The Definition of done in `CLAUDE.md` holds; the import-tier test holds; the golden and
`examples.html` are byte-identical; pytest is green at both ends.

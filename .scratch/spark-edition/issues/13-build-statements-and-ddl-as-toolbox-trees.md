# Build Statements and DDL as Toolbox trees, so no shared file imports sqlglot

Type: task
Status: resolved
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

## Answer

to_hive builds a whole Statement as Nodes (`02dae64`):

- `Select`, whose parts are its clauses. `group_by` and `order_by` are lists, and `limit` is a
  number.
- `Table`, which holds the database and the name apart, a `PARTITION(...)` and an alias.
- `Join`, whose `how` is "JOIN", "LEFT JOIN" or "CROSS JOIN".
- `CTE`, and `Insert`, `Create` with `ColumnDef`, and `Drop`, each naming its table in `target`.

WITH is not a Node of its own. It is the `derived_tables` part of a Select or an Insert, a list of
CTEs, since the Hive puts it at the top of either.

`writing.hive_statement` writes a whole Statement. SQL Composer's `writing.py` replays each Node
with the sqlglot calls it always made, so the golden, `examples.html` and every doctest are
byte-identical at both ends. `create_table` still checks each type when it is called, through
`writing.hive_type`. Only `writing.py` and `engine.py` import sqlglot:

- ticket 6's exception list is gone;
- `test_no_shared_file_may_import_either_library` and the AST import test hold the rule.

The comments that called these sqlglot trees are fixed, and ADR 0002's tree section says the whole
Statement is a Node.

## Comments

**Code review (2026-09-29), `02dae64`.** The Spec axis found every Hive byte-identical against the
parent at both ends, the golden's 378 cases included.

- *Standards:*
  - **Fixed:**
    - `hive_text` has no `pretty` flag, which nothing passed any more. `hive_statement` writes a
      whole Statement laid out.
    - JOIN's two flags that excluded each other are one `how`.
    - `Insert`, `Create` and `Drop` name their table in `target`, so `Node.table` stays a
      column's table name.
    - A `Table` holds `db` and `name` apart, so no printer splits a dotted name.
    - `order_by` is a list like `group_by`.
    - WITH's part is `derived_tables`, after the glossary.
    - The KINDS comment says a walk goes through the parts that hold Nodes.
  - **Answered, not changed:** the `CTE` kind keeps the name the glossary allows for how a
    Derived table lands in the Hive.
- *Spec:*
  - **Answered:** there is no `With` Node, as the Answer says. The ADR's float row belongs to
    ticket 04's default, recorded in the map's Notes. The ADR's "kept as written" and
    `Node.name`'s docstring were fixed as D27 and D28.
  - **Beginner reader:** not run. No text a user sees changed: the one docstring that did,
    `trees.py`'s, was read with ticket 12.

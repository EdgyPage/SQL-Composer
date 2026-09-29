# Hold Columns, Conditions and sort keys in the Toolbox's own tree

Type: task
Status: open
Blocked by: 11

## Question

Replace the sqlglot trees in `Column._tree`, `Condition._tree` and the ORDER BY keys with
`trees.Node`, keeping SQL Composer's output byte-identical on every sqlglot version in range.

`sql_composer/trees.py` (shared):

- `Node(kind, **parts)`, with meta, `set`, `copy`, structural `==`, a breadth-first `walk` and
  `find_all` over parts in their written order, `flatten`, and `.name`/`.table` on columns. It has
  no `__len__` or `__bool__`, and `__hash__ = None`, as sqlglot's trees don't hash either.
- A closed set of KINDS, with sqlglot's shapes, because lineage orders its boxes and arrows by a
  breadth-first walk (`sql_composer/lineage.py:153`, `:174`): binary, left-deep AND/OR with
  sqlglot's `_combine` bracket rule; `Paren` from `tables._bracketed`; `Case` holding `If`;
  `Count(Distinct)`; `Not(In)`; `Not(Is Null)`; `Window(RowNumber, partition_by,
  Order[Ordered])`; `Alias`; `Var`.
- `HiveFunction(name, args as written, aggregate)`: calls are compared and walked as written (the
  user's decision), so `hive_function("nvl", ...)` no longer equals `fill_null(...)`. This gets a
  CHANGES line.
- `Call` for the five Toolbox date calls (date_sub, next_day, trunc, unix_timestamp,
  from_unixtime).
- `HIVE_AGGREGATES` and the shared hive_function argument-count table move here.

`sql_composer/writing.py` gains `to_sqlglot(node)`, which **replays** today's exact sqlglot calls
(`Literal.string/number`, `to_identifier`, `exp.column`, `exp.alias_`, `exp.func(...,
dialect="hive")` for the date calls, and the hive_function read-back cached by text), never a
generic constructor, so the sqlglot trees themselves stay identical. `tables.readable` stays
shared: it copies the tree top-down, replaces each noted node with a `Var` holding its call, and
calls `hive_text`.

Tests: `tests/sqlglot_edition/test_trees_match_sqlglot.py` checks, over every corpus tree, the
column order against `to_sqlglot(node).find_all(exp.Column)`, pairwise `==`, `has_aggregate`
against the old function, the flatten of ON, and window partition names.
`tests/test_trees.py` tests `Node` on hand-built nodes. The f-string AST rule extends to `Node(...)`
and `trees.*` calls.

## Done when

The Definition of done in `CLAUDE.md` holds; the golden, `examples.html` and every doctest are
byte-identical; the parity tests pass; pytest is green at both ends; the ticket lists every
semantic difference from 2.1.

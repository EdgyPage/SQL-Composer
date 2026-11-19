"""Hive that stays small: a query's CTEs kept to what its rows need (Toolbox 8.9, ticket 05,
for ticket 17's rules).

Hive works a CTE out each time it is read, so a final's query should carry in each CTE only the
columns something after it reads, and read no CTE that only passes rows on. `lean_ctes` does
both to any query's tree, whatever wrote it: a Formula workbook's Table, Power Query, Total Row
or pivot (`workbook_hive.py`, `workbook_totals.py`). It changes no row: a column is left out
only where nothing of its name is read after its CTE, and a CTE whose rows its columns decide,
a DISTINCT or a UNION, is kept whole.
"""

from __future__ import annotations

from sqlglot import exp

# What a SELECT may hold beyond its columns and its FROM, each of which changes its rows.
ROW_PARTS = ("joins", "where", "group", "having", "order", "limit", "distinct")


def lean_ctes(query: exp.Query, whole: tuple[str, ...] = ()) -> exp.Query:
    """A query with each CTE's columns that nothing after it reads left out, last CTE first,
    and a CTE that only passes its rows on to the query folded into it (`passed_through`); a
    DISTINCT or UNION CTE kept whole, and so is each CTE `whole` names."""
    lean = passed_through(query.copy())
    held = lean.args.get("with_")
    if held is None:
        return lean
    ctes = list(held.expressions)
    for number in reversed(range(len(ctes))):
        cte = ctes[number]
        body = cte.this
        if cte.alias in whole or not isinstance(body, exp.Select) or body.args.get("distinct"):
            continue
        read = columns_read_after(lean, cte)
        kept = [each for each in body.expressions if each.alias_or_name in read]
        if kept and len(kept) < len(body.expressions):
            body.set("expressions", kept)
    return lean


def passed_through(query: exp.Query) -> exp.Query:
    """A query that only reads its last CTE's every column, as it is, as a Table a query loads
    does (file 15's W2): that CTE's own query, after the CTEs before it."""
    held = query.args.get("with_")
    if held is None or not isinstance(query, exp.Select):
        return query
    last = held.expressions[-1]
    source = query.args.get("from_")
    if source is None or not isinstance(source.this, exp.Table) or (
            source.this.name != last.alias) or source.this.alias or any(
            query.args.get(part) for part in ROW_PARTS):
        return query
    if [each.sql() for each in query.expressions] != last.this.named_selects:
        return query
    return with_ctes(last.this, list(held.expressions[:-1]))


def with_ctes(query: exp.Query, ctes: list[exp.CTE]) -> exp.Query:
    """A copy of `query` after `ctes`, each as it is, in their order; `query` alone where there
    are none."""
    written = query.copy()
    if ctes:
        written.set("with_", exp.With(expressions=[cte.copy() for cte in ctes]))
    return written


def columns_read_after(query: exp.Query, cte: exp.CTE) -> set[str]:
    """Every column's name the query reads outside `cte` and the CTEs before it: a name read
    from any table, so a column is left out only where nothing of that name is read."""
    before = True
    read: set[str] = set()
    held = query.args["with_"]
    for each in held.expressions:
        if not before:
            read |= {column.name for column in each.this.find_all(exp.Column)}
        if each is cte:
            before = False
    body = query.copy()
    body.set("with_", None)
    return read | {column.name for column in body.find_all(exp.Column)}

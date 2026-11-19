"""Pivot filters, as a Conversion keeps them for their Decision (Toolbox 8.9, ticket 07).

A Pivot filter's condition carries the mark Copilot file 20 has Copilot write above it,
`-- Pivot filter: <kind> <field>`, and that the code path writes after it, `/* Pivot filter:
<kind> <field> */`. `pivot_filters_in` reads either into the record the workbook's Pivot
filters give, `workbook_pivot_hive.ConvertedPivotFilter`, so both paths reach one Decision
(ticket 08). A batch keeps each table's records in its written.json (`pivot_filter_record`),
and `pivot_filters_of_batch` reads them back.
"""

from __future__ import annotations

import ast
import datetime
import re
from dataclasses import asdict, replace
from pathlib import Path

import sqlglot
from sqlglot import exp

from .converting import python_of_literal
from .script_tags import readable_tags
from .workbook_formulas import snake_case
from .workbook_pivot_hive import (
    FILTER_RULES,
    HIDDEN_ITEMS,
    TIMELINE,
    TOP_FILTER,
    ConvertedPivotFilter,
)
from .workflows import batch_record
from .writing import read_hive, sql_text

# Where a batch's written.json keeps each table's Pivot filters.
PIVOT_FILTERS = "pivot_filters"
_FILTER_KINDS = "|".join(map(re.escape, FILTER_RULES))
PIVOT_FILTER_MARK = re.compile(rf"\s*Pivot filter: (?P<kind>{_FILTER_KINDS}) (?P<field>.+?)\s*")
# The same mark in Hive's text, a -- comment to its line's end or a /* */ comment.
PIVOT_FILTER_MARK_IN_TEXT = re.compile(
    rf"(?:--[ \t]*|/\*\s*)Pivot filter: (?P<kind>{_FILTER_KINDS}) (?P<field>[^\n]*?)"
    r"\s*(?:\*/|$)", re.MULTILINE)
# Excel's caption of a value, by the aggregate a value filter's RANK orders by: Sum of x.
_CAPTION_WORDS = {exp.Sum: "Sum", exp.Count: "Count", exp.Avg: "Average", exp.Max: "Max",
                  exp.Min: "Min"}


def pivot_filters_in(text: str, final: str) -> list[ConvertedPivotFilter]:
    """Each Pivot filter Hive marks, `final` the table it is in, once each: its kind and field
    from its mark, and its values from the condition the mark is on. Hive alone holds no
    pivot cache, so `field_values` is empty; and the value a value filter ranks by is named as
    Excel names it by default, such as "Sum of duration_mins". Hive sqlglot can't read marks
    none."""
    try:
        trees = read_hive(readable_tags(text))
    except sqlglot.errors.ParseError:
        return []
    found, conjuncts = [], []
    for tree in trees:
        for select in tree.find_all(exp.Select):
            where = select.args.get("where")
            if where is not None:
                found += _pivot_filters_in_where(where, final)
                conjuncts += _conjuncts(where.this)
    # sqlglot drops a comment above some conditions, such as one starting NOT: such a mark,
    # in the text and in no comment of the tree, is read by its field and kind alone.
    read = [(each.kind, each.field) for each in found]
    for mark in PIVOT_FILTER_MARK_IN_TEXT.finditer(text):
        if (mark["kind"], mark["field"]) in read:
            read.remove((mark["kind"], mark["field"]))
            continue
        marked = _condition_of_kind(conjuncts, mark["kind"], mark["field"])
        found.append(_pivot_filter_of(final, mark["kind"], mark["field"], marked))
    return list(dict.fromkeys(found))


def _pivot_filters_in_where(where: exp.Where, final: str) -> list[ConvertedPivotFilter]:
    """Each Pivot filter marked in one WHERE, but in a subquery of it, which has its own, in
    the order of the conditions they are on. A mark right after WHERE may be the WHERE's own
    comment, as sqlglot reads it."""
    conjuncts = _conjuncts(where.this)
    found = []
    for node in _nodes_outside_subqueries(where):
        for comment in node.comments or []:
            mark = PIVOT_FILTER_MARK.fullmatch(comment)
            if mark is None:
                continue
            kind, name = mark["kind"], mark["field"]
            marked = _marked_condition(node, conjuncts, kind, name)
            place = len(conjuncts)
            if marked is not None:
                place = [id(each) for each in conjuncts].index(id(marked))
            found.append((place, _pivot_filter_of(final, kind, name, marked)))
    return [pivot_filter for _, pivot_filter in sorted(found, key=lambda each: each[0])]


def _conjuncts(condition: exp.Expression) -> list[exp.Expression]:
    """The conditions a WHERE joins with AND, each as written, its brackets kept."""
    bare = condition.unnest()
    if isinstance(bare, exp.And):
        return _conjuncts(bare.left) + _conjuncts(bare.right)
    return [condition]


def _nodes_outside_subqueries(condition: exp.Expression) -> list[exp.Expression]:
    """Each node of a condition, in the order it is written, but those inside a subquery."""
    found, waiting = [], [condition]
    while waiting:
        node = waiting.pop()
        found.append(node)
        if not isinstance(node, (exp.Subquery, exp.Query)):
            waiting += reversed(list(node.iter_expressions()))
    return found


def _marked_condition(node: exp.Expression, conjuncts: list[exp.Expression], kind: str,
                      name: str) -> exp.Expression | None:
    """The condition a mark is on: the one holding the node the mark is on, where it reads the
    field; else the first that reads the field and is of the mark's kind, among those the node
    holds, as a mark above an AND may be, or else in the whole WHERE; None where none is."""
    for each in conjuncts:
        if _is_inside(node, each) and _reads_field(each, name):
            return each
    held = [each for each in conjuncts if _is_inside(each, node)]
    return _condition_of_kind(held, kind, name) or _condition_of_kind(conjuncts, kind, name)


def _condition_of_kind(conjuncts: list[exp.Expression], kind: str,
                       name: str) -> exp.Expression | None:
    """The first condition that reads a pivot field's column and is written as a Pivot filter
    of `kind` is; None where none is."""
    for each in conjuncts:
        if _reads_field(each, name) and _is_of_kind(each.unnest(), kind):
            return each
    return None


def _is_inside(node: exp.Expression, outer: exp.Expression) -> bool:
    """Whether `node` is `outer` or inside it."""
    found: exp.Expression | None = node
    while found is not None:
        if found is outer:
            return True
        found = found.parent
    return False


def _reads_field(condition: exp.Expression, name: str) -> bool:
    """Whether a condition reads a pivot field's column, by its name or in snake case."""
    names = {name.lower(), snake_case(name)}
    return any(column.name.lower() in names for column in condition.find_all(exp.Column))


def _is_of_kind(condition: exp.Expression, kind: str) -> bool:
    """Whether a condition is written as a Pivot filter of `kind` is: a Timeline's a BETWEEN,
    a value filter's an IN of a subquery, the hidden items' a <> or a NOT, and a Report
    filter's or a slicer's none of these."""
    if kind == TIMELINE:
        return isinstance(condition, exp.Between)
    if kind == TOP_FILTER:
        return isinstance(condition, exp.In) and condition.args.get("query") is not None
    drops = any(isinstance(node, (exp.NEQ, exp.Not)) for node in condition.walk())
    return drops == (kind == HIDDEN_ITEMS)


def _pivot_filter_of(final: str, kind: str, name: str,
                     condition: exp.Expression | None) -> ConvertedPivotFilter:
    """The record of one marked Pivot filter, its values read from its condition; none where
    no condition was found for its mark."""
    if condition is None:
        return ConvertedPivotFilter(final, kind, name, (), ())
    bare = condition.unnest()
    if kind == TIMELINE:
        days = [_literal_value(bare.args["low"]), _literal_value(bare.args["high"])]
        return ConvertedPivotFilter(final, kind, name, tuple(
            datetime.datetime.fromisoformat(str(day)) for day in days), ())
    if kind == TOP_FILTER:
        return _value_filter_of(final, name, bare)
    return ConvertedPivotFilter(final, kind, name, tuple(_condition_values(bare, kind)), ())


def _condition_values(condition: exp.Expression, kind: str) -> list[object]:
    """The items a Report filter's or a slicer's condition keeps, or the items a hidden items'
    drops, in the order written, a blank as None: `f = x`, `f IN (..)` and `f IS NULL` kept;
    `f <> x`, `NOT f IN (..)` and `NOT f IS NULL` dropped, a blank kept beside them, `f IS
    NULL OR`, no item."""
    values: list[object] = []
    for node in condition.walk(bfs=False):
        if kind == HIDDEN_ITEMS:
            values += _dropped_values(node)
        elif isinstance(node, exp.EQ):
            values.append(_literal_value(node.expression))
        elif isinstance(node, exp.In) and not isinstance(node.parent, exp.Not):
            values += [_literal_value(each) for each in node.expressions]
        elif isinstance(node, exp.Is):
            values.append(None)
    return values


def _dropped_values(node: exp.Expression) -> list[object]:
    """The items one part of a hidden items' condition drops: a <>'s value, a NOT IN's values,
    and a NOT IS NULL's blank, None."""
    if isinstance(node, exp.NEQ):
        return [_literal_value(node.expression)]
    if not isinstance(node, exp.Not):
        return []
    inner = node.this.unnest()
    if isinstance(inner, exp.In):
        return [_literal_value(each) for each in inner.expressions]
    if isinstance(inner, exp.Is):
        return [None]
    return []


def _value_filter_of(final: str, name: str, condition: exp.Expression) -> ConvertedPivotFilter:
    """A value filter's record: how many items it keeps, from its subquery's `<= n`; the value
    it ranks by, as Excel's default caption names it; and whether it keeps the bottom ones, an
    ascending RANK."""
    kept = [node for node in condition.find_all(exp.LTE)
            if isinstance(node.expression, exp.Literal)]
    count: tuple[object, ...] = ()
    if kept:
        count = (_literal_value(kept[0].expression),)
    ranked_by, bottom = "", False
    for window in condition.find_all(exp.Window):
        order = window.args.get("order")
        if order is None:
            continue
        first = order.expressions[0]
        ranked_by = _caption_of(first.this)
        bottom = not first.args.get("desc")
    return ConvertedPivotFilter(final, TOP_FILTER, name, count, (), ranked_by, bottom)


def _caption_of(value: exp.Expression) -> str:
    """The caption Excel gives a value by default, by its aggregate, such as "Sum of
    duration_mins"; any other as its Hive."""
    word = _CAPTION_WORDS.get(type(value))
    if word is not None and isinstance(value.this, exp.Column):
        return f"{word} of {value.this.name}"
    return sql_text(value)


def _literal_value(node: exp.Expression) -> object:
    """A Hive literal as the value it is, as `converting.python_of_literal` writes it as
    Python: a text, a number, True or False; None for NULL, or anything else."""
    python = python_of_literal(node)
    if python is None:
        return None
    return ast.literal_eval(python)


def with_field_values_of(marked: list[ConvertedPivotFilter],
                         given: list[ConvertedPivotFilter]) -> list[ConvertedPivotFilter]:
    """Each Pivot filter Hive marks, `marked`, with every value its field takes, taken from
    the workbook's Pivot filter of the same field, `given`, the filters of the final the Hive
    is Copilot's for; as it was where the workbook has none."""
    by_field = {each.field.lower(): each.field_values for each in given}
    return [replace(each, field_values=by_field.get(each.field.lower(), each.field_values))
            for each in marked]


# --- The record a batch keeps ---------------------------------------------------------------

# How a batch's written.json keeps a Pivot filter's date and time, and its date.
TIME_KEPT = "time"
DAY_KEPT = "day"


def pivot_filter_record(written: ConvertedPivotFilter) -> dict[str, object]:
    """A Pivot filter as a batch's written.json keeps it: each field of its record, each of
    its values as `json_value` writes it, as JSON holds no date."""
    record = asdict(written)
    for name in ("values", "field_values"):
        record[name] = [json_value(value) for value in record[name]]
    return record


def pivot_filter_of_record(record: dict[str, object]) -> ConvertedPivotFilter:
    """A Pivot filter read back from a batch's written.json, as `pivot_filter_record` kept it,
    each date and time as it was."""
    values = tuple(value_of_json(value) for value in record["values"])
    field_values = tuple(value_of_json(value) for value in record["field_values"])
    return ConvertedPivotFilter(str(record["final"]), str(record["kind"]),
                                str(record["field"]), values, field_values,
                                str(record["ranked_by"]), bool(record["bottom"]))


def json_value(value: object) -> object:
    """A value as JSON holds it: a date and time as {"time": its ISO text}, a date as {"day":
    its ISO text}, any other as it is."""
    if isinstance(value, datetime.datetime):
        return {TIME_KEPT: value.isoformat()}
    if isinstance(value, datetime.date):
        return {DAY_KEPT: value.isoformat()}
    return value


def value_of_json(value: object) -> object:
    """A value `json_value` wrote, as it was."""
    if isinstance(value, dict) and TIME_KEPT in value:
        return datetime.datetime.fromisoformat(value[TIME_KEPT])
    if isinstance(value, dict) and DAY_KEPT in value:
        return datetime.date.fromisoformat(value[DAY_KEPT])
    return value


def pivot_filters_of_batch(root: Path, name: str) -> dict[str, list[ConvertedPivotFilter]]:
    """Each Pivot filter of each table the batch `name` made, by the table, as its
    written.json keeps them, for the table's Decision (ticket 08): none for a batch that kept
    none, or that isn't there."""
    kept = batch_record(root, name).get(PIVOT_FILTERS, {})
    found = {}
    for table, filters in kept.items():
        found[table] = [pivot_filter_of_record(each) for each in filters]
    return found

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
from .decisions import PivotFilterAnswer
from .script_tags import readable_tags, tags_as_written
from .shared import counted, in_words
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
    the order of the conditions they are on."""
    return [_pivot_filter_of(final, kind, name, marked)
            for kind, name, marked in _marks_in_where(where)]


def _marks_in_where(where: exp.Where) -> list[tuple[str, str, exp.Expression | None]]:
    """Each Pivot filter mark in one WHERE, but in a subquery of it, as its kind, its field
    and the condition it is on, None where none is found, in the order of the conditions. A
    mark right after WHERE may be the WHERE's own comment, as sqlglot reads it."""
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
            found.append((place, (kind, name, marked)))
    return [mark for _, mark in sorted(found, key=lambda each: each[0])]


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




# --- Each Pivot filter's Decision, in words (ticket 08) -------------------------------------

# How a blank is shown, as Excel shows one, and named in a list and in a table per value's
# name.
BLANK_SHOWN = "(blank)"
BLANK_NAME = "blank"
# How each Pivot filter's note in its table's checklist starts.
NOTE_START = "Pivot filter "
# How many of a field's values a Decision names before it counts the rest.
VALUES_NAMED = 6


def pivot_filter_keys(filters: list[ConvertedPivotFilter]) -> dict[str, ConvertedPivotFilter]:
    """Each Pivot filter of one table by the name its Decision has in PIVOT_FILTERS: its
    field, or its kind and field where another of the table's filters has the field too."""
    fields = [each.field for each in filters]
    keyed = {}
    for each in filters:
        key = each.field
        if fields.count(each.field) > 1:
            key = f"{each.kind} {each.field}"
        keyed[key] = each
    return keyed


def pivot_filter_in_words(written: ConvertedPivotFilter) -> str:
    """What a Pivot filter keeps, in words: "the slicer on status keeps FAILED and SUCCESS";
    its kind and field alone where its values weren't read."""
    shown = [value_shown(value) for value in written.values]
    if not shown:
        return f"the {written.kind} on {written.field}"
    if written.kind == HIDDEN_ITEMS:
        return f"the items hidden on {written.field} leave out {in_words(shown)}"
    if written.kind == TIMELINE:
        return f"the Timeline on {written.field} keeps {shown[0]} to {shown[-1]}"
    if written.kind == TOP_FILTER:
        end = "bottom" if written.bottom else "top"
        return (f"the value filter on {written.field} keeps the {end} {shown[0]} "
                f"{written.field} by {written.ranked_by}")
    return f"the {written.kind} on {written.field} keeps {in_words(shown)}"


def value_shown(value: object) -> str:
    """A value as a Pivot filter's Decision shows it: a day as 2026-09-24, a blank as Excel
    shows one, (blank)."""
    if value is None:
        return BLANK_SHOWN
    if isinstance(value, datetime.datetime) and value.time() == datetime.time():
        return value.date().isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    return str(value)


def values_listed(written: ConvertedPivotFilter) -> str:
    """The values a Pivot filter's field takes, as the PivotTable's cache held them, in words:
    "FAILED, SUCCESS, TEST and blank"; the first few and how many more, where there are
    many."""
    shown = [BLANK_NAME if value is None else value_shown(value)
             for value in written.field_values]
    if len(shown) <= VALUES_NAMED:
        return in_words(shown)
    rest = len(shown) - VALUES_NAMED + 1
    return f"{', '.join(shown[:VALUES_NAMED - 1])} and {rest} more"


def layer_counts(keyed: dict[str, ConvertedPivotFilter]) -> list[tuple[list[str], int]]:
    """How many tables a table per value makes, layer by layer, a layer being each field the
    table is filtered on, and every layer together where there are two or more: each as the
    names of its Pivot filters and the count, 0 for a layer whose values aren't known. A
    value filter is no layer: it has no table per value."""
    layered = [key for key, each in keyed.items() if each.kind != TOP_FILTER]
    layers = [([key], len(keyed[key].field_values)) for key in layered]
    if len(layers) > 1:
        together = 1
        for _, count in layers:
            together *= count
        layers.append((layered, together))
    return layers


def layers_in_words(keyed: dict[str, ConvertedPivotFilter]) -> str:
    """layer_counts in words, each layer's values named: "status: at least 4 tables (FAILED,
    SUCCESS, TEST and blank); dt: at least 2 tables (2026-09-23 and 2026-09-24); status and
    dt together: at least 8 tables"."""
    said = []
    for names, count in layer_counts(keyed):
        tables = counted(count, "table")
        if len(names) > 1:
            said.append(f"{in_words(names)} together: at least {tables}")
        else:
            said.append(f"{names[0]}: at least {tables} ({values_listed(keyed[names[0]])})")
    return "; ".join(said)


def pivot_filter_line_text(key: str, keyed: dict[str, ConvertedPivotFilter]) -> str:
    """What a Pivot filter's line in PIVOT_FILTERS says of it: what it keeps, then how many
    tables each answer makes, a table per value's from the values the PivotTable's cache
    held, which it names; a value filter's two answers alone."""
    written = keyed[key]
    words = pivot_filter_in_words(written)
    column = column_name(written.field)
    if written.kind == TOP_FILTER:
        kept = value_shown(written.values[0]) if written.values else "items"
        return (f'{words}. "{PivotFilterAnswer.KEEP}": 1 table, those {kept}; '
                f'"{PivotFilterAnswer.FOLD}": 1 table, every {column}. A value filter has only '
                "these two answers, as it keeps items by their rank, which changes as the rows "
                "do")
    tables = (f"a table per {column}, how many not known, as a script's Hive holds no "
              "PivotTable cache")
    if written.field_values:
        tables = (f"at least {counted(len(written.field_values), 'table')}, one per {column} "
                  f"the PivotTable's cache held ({values_listed(written)})")
    return (f'{words}. "{PivotFilterAnswer.KEEP}": 1 table, that selection; '
            f'"{PivotFilterAnswer.FOLD}": 1 table, every {column}; '
            f'"{PivotFilterAnswer.BATCH}": 1 table, a Partition per {column}; '
            f'"{PivotFilterAnswer.TABLES}": {tables}')


def pivot_filter_note(table: str, key: str, keyed: dict[str, ConvertedPivotFilter],
                      text: str) -> str:
    """The note of one Pivot filter's Decision in its table's checklist, `text` the Hive the
    table was converted from: what the table shows; each answer, in Excel's words first, and
    how many tables it makes, a table per value's layer by layer; and which to pick."""
    written = keyed[key]
    keys, values = shown_by(text, written)
    shows = f"{in_words(values) or 'its rows'} by {in_words(keys)}"
    if not keys:
        shows = f"{in_words(values) or 'its rows'} over every row"
    opening = (f"{NOTE_START}{key}, a Decision. What {table} shows: {shows}, only where "
               f"{pivot_filter_in_words(written)}, as the workbook was last saved. Its "
               f'answers, each given as "pivot_filters": {{"{key}": ...}}: '
               f'"{PivotFilterAnswer.KEEP}", proposed: 1 table, that selection alone. ')
    column = column_name(written.field)
    if written.kind == TOP_FILTER:
        return opening + (f'"{PivotFilterAnswer.FOLD}": 1 table, every {column}, the value '
                          f"filter dropped. A value filter has only these two answers: it "
                          f"{VALUE_FILTER_REASON}.")
    return opening + _every_value_said(table, key, keyed, keys) + (
        f' Which to pick: to tab through each {column} in a presentation, as with a slicer, '
        f'"{PivotFilterAnswer.FOLD}" keeps every {column} in one table to slice later; '
        f'"{PivotFilterAnswer.BATCH}" when each {column} is written on its own schedule; '
        f'"{PivotFilterAnswer.TABLES}" only for a handful; "{PivotFilterAnswer.KEEP}" when one '
        "selection is all anyone needs. A handful of tables, such as 3, is manageable; a "
        f'hundred is a reason to "{PivotFilterAnswer.FOLD}" or "{PivotFilterAnswer.BATCH}" '
        "instead.")


# Why a value filter has no "batch" or "tables" answer, as its note and its refusal say.
VALUE_FILTER_REASON = ("keeps items by their rank among the rest, which changes as the rows "
                       "do, so it has no fixed value to write a batch or a table for")


def _every_value_said(table: str, key: str, keyed: dict[str, ConvertedPivotFilter],
                      keys: list[str]) -> str:
    """What a Pivot filter's note says of the three answers that keep every value: "fold",
    "batch" and "tables", each in Excel's words or plain ones first, and how many tables or
    Partitions each makes."""
    written = keyed[key]
    column = column_name(written.field)
    grain = in_words([*keys, column])
    if column in keys:
        grain = in_words(keys)
    partitions = "a Partition per value"
    if written.field_values:
        partitions = f"at least {counted(len(written.field_values), 'Partition')}"
    return (f'"{PivotFilterAnswer.FOLD}": like dragging {written.field} from Filters to Rows '
            f"in the PivotTable: 1 table, every {column}, {column} a column of {table} and "
            f"part of what one row is, a row for each {grain}. "
            f'"{PivotFilterAnswer.BATCH}": 1 table written one {column} at a time, each run '
            f"writing its own {column}'s rows: {table} is partitioned on {column}, a Partition "
            f"per {column} ({partitions}), and the {column} each run writes is the Script tag "
            f'{tag_name(written.field)}, answered under "tags" with the Run value proposed '
            f'there. "{PivotFilterAnswer.TABLES}": like Excel\'s Show Report Filter Pages: a '
            f"table per {column}, named {table}_<value>, such as "
            f"{table}_{_value_names(written)[0]}: {_tables_said(written, keyed)}")


def _tables_said(written: ConvertedPivotFilter, keyed: dict[str, ConvertedPivotFilter]) -> str:
    """What a Pivot filter's note says of how many tables a table per value makes: each layer
    and every layer together, from the values the PivotTable's cache held, which it names, a
    layer and "at least" each said; or why that isn't known."""
    if not written.field_values:
        return (f"how many isn't known, as its Hive came from a script, which holds no "
                f"PivotTable cache of the values {written.field} takes, so "
                f'"{PivotFilterAnswer.TABLES}" waits until you convert the script beside its '
                "workbook.")
    return (f"{layers_in_words(keyed)}. A layer is each field the table is filtered on, and "
            '"at least" as these are the values the PivotTable\'s cache held when the '
            "workbook was saved: the warehouse may hold more.")


def column_name(field: str) -> str:
    """The column a PivotTable's field is in the Hive: its name in snake case."""
    return snake_case(field)


def tag_name(field: str) -> str:
    """The Script tag one batch per value of a field writes where its value goes: STATUS for
    status."""
    return column_name(field).upper()


def batch_default(written: ConvertedPivotFilter) -> object:
    """The value a batch's Script tag is proposed with, where the warehouse fills it in each
    run: the first value the filter keeps, or else the first the field takes, never a
    blank."""
    kept = [value for value in written.values if value is not None]
    if written.kind == HIDDEN_ITEMS:
        kept = []
    kept += [value for value in written.field_values
             if value is not None and value not in written.values]
    return kept[0] if kept else ""


def _value_names(written: ConvertedPivotFilter) -> list[str]:
    """The name each value a Pivot filter's field takes gives its table per value, in snake
    case, a blank's "blank", and a _2 where two would share one."""
    names: list[str] = []
    for value in written.field_values or written.values or ("value",):
        name = BLANK_NAME
        if value is not None:
            name = snake_case(value_shown(value)) or BLANK_NAME
        while name in names:
            name = f"{name}_2"
        names.append(name)
    return names


def answers_in_words(keyed: dict[str, ConvertedPivotFilter], answers: dict[str, str],
                     held: dict[str, object]) -> str:
    """Each Pivot filter's answer in words, as write_decisions' report says it, `held` giving
    the value a table per value holds."""
    said = []
    for key, written in keyed.items():
        answer = answers.get(key, PivotFilterAnswer.KEEP)
        column = column_name(written.field)
        if answer == PivotFilterAnswer.FOLD:
            said.append(f"every {column}, {column} part of what one row is")
        elif answer == PivotFilterAnswer.BATCH:
            said.append(f"one batch per {column}, the {column} each run writes the Script tag "
                        f"{tag_name(written.field)}, proposed in its Table reference's TAGS")
        elif answer == PivotFilterAnswer.TABLES:
            said.append(f"{column} {value_shown(held.get(key))} alone, a table per {column}")
        else:
            said.append(f"{pivot_filter_in_words(written)}, kept")
    return "; ".join(said)


def table_slices(table: str, keyed: dict[str, ConvertedPivotFilter],
                 answers: dict[str, str]) -> dict[str, dict[str, object]]:
    """Each table a Pivot filter's answers make of `table`, by its full name, and the value
    each Pivot filter answered "tables" holds it to, by the filter's name in PIVOT_FILTERS:
    the table alone where none is, else one per value, `<table>_<value>`, and one per value of
    each layer together where two or more are."""
    slices: dict[str, dict[str, object]] = {table: {}}
    for key, written in keyed.items():
        if answers.get(key) != PivotFilterAnswer.TABLES:
            continue
        grown = {}
        for name, held in slices.items():
            for value, value_name in zip(written.field_values, _value_names(written),
                                         strict=True):
                grown[f"{name}_{value_name}"] = {**held, key: value}
        slices = grown
    return slices


# --- The Hive each answer gives (ticket 08) ------------------------------------------------


def shown_by(text: str, written: ConvertedPivotFilter) -> tuple[list[str], list[str]]:
    """What the query holding a Pivot filter's condition shows: the names of its keys, each
    output that is no aggregate, and of its values, each output that is one; none where
    sqlglot can't read the Hive or the condition isn't found."""
    for tree in _hive_trees(text):
        found = _condition_in(tree, written)
        if found is None:
            continue
        keys, values = [], []
        for each in found[0].expressions:
            if each.find(exp.AggFunc, exp.Window) is None:
                keys.append(each.alias_or_name)
            else:
                values.append(each.alias_or_name)
        return keys, values
    return [], []


def answer_problem(text: str, written: ConvertedPivotFilter,
                   answer: PivotFilterAnswer) -> str | None:
    """Why a Pivot filter can't take `answer` in the Hive its table was converted from,
    `text`, or None when it can: a value filter has no value to batch or to make a table of;
    a table per value needs the values the field takes; and folding a field into what one row
    is, or batching it, whose compare reads every batch's rows, where the filter sits in a
    step other parts of the query read, would change their rows too."""
    if answer == PivotFilterAnswer.KEEP:
        return None
    if written.kind == TOP_FILTER and answer in (PivotFilterAnswer.BATCH,
                                                 PivotFilterAnswer.TABLES):
        return (f'a value filter {VALUE_FILTER_REASON}: answer "{PivotFilterAnswer.KEEP}" or '
                f'"{PivotFilterAnswer.FOLD}"')
    if answer == PivotFilterAnswer.TABLES and not written.field_values:
        return (f"how many values {written.field} takes isn't known: its Hive came from a "
                "script, which holds no PivotTable cache of them; convert the script beside "
                f'its workbook, or answer "{PivotFilterAnswer.FOLD}" or '
                f'"{PivotFilterAnswer.BATCH}"')
    for tree in _hive_trees(text):
        found = _condition_in(tree, written)
        if found is None:
            continue
        select, condition = found
        column = _field_column(condition, written.field)
        # A value filter folded keeps every item of the step's own grain: nothing is added.
        if (answer in (PivotFilterAnswer.FOLD, PivotFilterAnswer.BATCH)
                and written.kind != TOP_FILTER and select is not _outer(tree)):
            return (f"this filter sits in a step, a CTE that other parts of the query read "
                    f"too, so making {column.name} part of what one row is there would change "
                    f'their rows as well: answer "{PivotFilterAnswer.KEEP}" or '
                    f'"{PivotFilterAnswer.TABLES}", or move the filter out of the step in the '
                    "Hive and convert it again")
        return None
    return (f"its condition, marked /* Pivot filter: {written.kind} {written.field} */, isn't "
            "in the Hive it was converted from: convert it again")


def hive_answered(text: str,
                  answered: list[tuple[ConvertedPivotFilter, PivotFilterAnswer, object]],
                  pretty: bool = False, every_batch: bool = False) -> str:
    """Hive with each Pivot filter's condition rewritten as its answer says, `answered`
    giving each filter, its answer and, for "tables", the one value its table holds: "fold"
    drops the condition and adds its column to the outputs and the GROUP BY; "batch" holds the
    column to a Script tag, `<PARM="STATUS"/>`, and writes the Partition of that value, or,
    with `every_batch`, gives every batch's rows together, as "fold" does but its column last,
    as a Partition's is, for the compare step to read; "tables" holds it to its value; "keep"
    leaves it. Each statement written as Hive, laid out over lines when `pretty`; the text as
    it is where every answer keeps."""
    if all(answer == PivotFilterAnswer.KEEP for _, answer, _ in answered):
        return text
    trees = _hive_trees(text)
    for written, answer, value in answered:
        for tree in trees:
            found = _condition_in(tree, written)
            if answer != PivotFilterAnswer.KEEP and found is not None:
                _answer_in(tree, *found, written, answer, value, every_batch)
                break
    return tags_as_written(";\n".join(sql_text(tree, pretty=pretty) for tree in trees))


def _hive_trees(text: str) -> list[exp.Expression]:
    """Hive read by sqlglot, each bare Script tag in backticks first; none where it can't."""
    try:
        return read_hive(readable_tags(text))
    except sqlglot.errors.ParseError:
        return []


def _condition_in(tree: exp.Expression, written: ConvertedPivotFilter
                  ) -> tuple[exp.Select, exp.Expression] | None:
    """The query holding a Pivot filter's condition in one statement, and the condition, by
    its mark; else, as a mark sqlglot drops is read, by its field and kind; None where none
    is."""
    selects = list(tree.find_all(exp.Select))
    for select in selects:
        where = select.args.get("where")
        if where is None:
            continue
        for kind, name, marked in _marks_in_where(where):
            if (kind, name) == (written.kind, written.field) and marked is not None:
                return select, marked
    for select in selects:
        where = select.args.get("where")
        if where is None:
            continue
        marked = _condition_of_kind(_conjuncts(where.this), written.kind, written.field)
        if marked is not None:
            return select, marked
    return None


def _outer(tree: exp.Expression) -> exp.Expression:
    """A statement's own query: an INSERT's SELECT, or the query itself."""
    if isinstance(tree, exp.Insert):
        return tree.expression
    return tree


def _field_column(condition: exp.Expression, name: str) -> exp.Column:
    """The column a Pivot filter's condition reads its field by, its comments left off; the
    field in snake case where the condition reads none by its name."""
    names = {name.lower(), snake_case(name)}
    for column in condition.find_all(exp.Column):
        if column.name.lower() in names:
            return _copy_without_comments(column)
    return exp.column(snake_case(name))


def _copy_without_comments(node: exp.Expression) -> exp.Expression:
    """A copy of a node, with no comment on it or inside it, as a mark on it."""
    copied = node.copy()
    for each in copied.walk():
        each.comments = None
    return copied


def _is_aggregated(select: exp.Select) -> bool:
    """Whether a query gives one row per group: it has a GROUP BY, or an output aggregates."""
    return select.args.get("group") is not None or any(
        each.find(exp.AggFunc) is not None for each in select.expressions)


def _group_names(select: exp.Select) -> list[str]:
    """The name of each column a query's GROUP BY names alone, in lower case."""
    group = select.args.get("group")
    keys = list(group.expressions) if group is not None else []
    return [each.name.lower() for each in keys if isinstance(each, exp.Column)]


def _answer_in(tree: exp.Expression, select: exp.Select, condition: exp.Expression,
               written: ConvertedPivotFilter, answer: PivotFilterAnswer, value: object,
               every_batch: bool) -> None:
    """Rewrite one Pivot filter's condition, in the query `select` of the statement `tree`,
    as `answer` says, as hive_answered does, `every_batch` too; a mark the WHERE itself held
    is taken off."""
    column = _field_column(condition, written.field)
    where = select.args["where"]
    mark = f" Pivot filter: {written.kind} {written.field} "
    where.comments = [each for each in where.comments or [] if each.strip() != mark.strip()]
    batch = answer == PivotFilterAnswer.BATCH
    if answer == PivotFilterAnswer.FOLD or (batch and every_batch):
        _drop_condition(select, condition)
        _add_to_grain(select, column, last=batch)
        return
    if batch:
        place = _tag_place(written)
        rewritten = exp.EQ(this=column.copy(), expression=place)
        _add_static_partition(tree, column.name, place.copy())
    else:
        rewritten = _equals(column, value)
    # On the value, so Hive shows the mark after the condition, as the conversion wrote it.
    rewritten.expression.add_comments([mark])
    condition.replace(rewritten)


def _drop_condition(select: exp.Select, condition: exp.Expression) -> None:
    """Take one condition out of a query's WHERE, and the WHERE where it was its only one."""
    where = select.args["where"]
    rest = [each for each in _conjuncts(where.this) if each is not condition]
    if rest:
        where.set("this", exp.and_(*rest))
    else:
        select.set("where", None)


def _add_to_grain(select: exp.Select, column: exp.Column, last: bool) -> None:
    """Add a column to what one row of a query is: to its outputs, before its first
    aggregate, or `last`, as a Partition's column is; and to its GROUP BY where it
    aggregates; each where it isn't already."""
    name = column.name.lower()
    projections = list(select.expressions)
    if name not in [each.alias_or_name.lower() for each in projections]:
        at = len(projections)
        for number, each in enumerate(projections):
            if not last and each.find(exp.AggFunc, exp.Window) is not None:
                at = number
                break
        select.set("expressions", [*projections[:at], column.copy(), *projections[at:]])
    if _is_aggregated(select) and name not in _group_names(select):
        group = select.args.get("group")
        keys = list(group.expressions) if group is not None else []
        select.set("group", exp.Group(expressions=[*keys, column.copy()]))


def _tag_place(written: ConvertedPivotFilter) -> exp.Expression:
    """Where one batch per value's Script tag stands: inside quotes for a field of text or
    days, bare, in backticks for sqlglot, for one of numbers."""
    tag = f'<PARM="{tag_name(written.field)}"/>'
    numbers = [value for value in (*written.values, *written.field_values)
               if isinstance(value, (int, float)) and not isinstance(value, bool)]
    if numbers:
        return exp.Column(this=exp.Identifier(this=tag, quoted=True))
    return exp.Literal.string(tag)


def _equals(column: exp.Column, value: object) -> exp.Expression:
    """A condition holding a column to one value: IS NULL for a blank, a number bare, any
    other value as text."""
    if value is None:
        return exp.Is(this=column.copy(), expression=exp.Null())
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return exp.EQ(this=column.copy(), expression=exp.Literal.number(value))
    return exp.EQ(this=column.copy(), expression=exp.Literal.string(value_shown(value)))


def _add_static_partition(tree: exp.Expression, name: str, place: exp.Expression) -> None:
    """Make an INSERT write the Partition of one value of a column, PARTITION (status =
    ...), beside any it writes already; a query alone, with no INSERT, is left."""
    if not isinstance(tree, exp.Insert) or not isinstance(tree.this, exp.Table):
        return
    partition = tree.this.args.get("partition")
    given = list(partition.expressions) if partition is not None else []
    equals = exp.EQ(this=exp.column(name), expression=place)
    tree.this.set("partition", exp.Partition(expressions=[*given, equals]))

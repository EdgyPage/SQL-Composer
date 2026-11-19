"""Save PivotTables into a workbook the way Excel saves them, for dev's tests and evaluations.

openpyxl writes no PivotTable, so a workbook built with it holds none. This adds them to the
saved file, as Excel saves them (ECMA-376 Part 1, 18.10; [MS-XLSX] for slicers and Timelines):

- for each source a pivot cache: its definition (`xl/pivotCache/pivotCacheDefinition<n>.xml`),
  naming the source, a Table or a plain range, and each field with its items, its date or
  number groups and its calculated items; and its records, a row for each source row;
- for each pivot its definition (`xl/pivotTables/pivotTable<n>.xml`): its Row, Column and Value
  fields, its row and column items, its Report filters, hidden items, value filter and Timeline
  filter, its totals, and its place; its cells, which `work_out` gives, are on its sheet;
- for each slicer and Timeline its cache (`xl/slicerCaches/`, `xl/timelineCaches/`), naming
  each pivot it filters and what it has selected, the slicer or Timeline itself, on its sheet
  (`xl/slicers/`, `xl/timelines/`), and a drawing placing it there;
- every content type and relationship these need, and the defined name Excel gives each
  slicer and Timeline.

The stored values, each value cell of a pivot, are worked out by Hive run on the Example
database's rows, never typed by hand: `work_out` writes the Hive of each total level the pivot
shows (its items, each subtotal, the grand totals), runs it with the Example database's own
executor, and places each row it gives. So they test the reader and the conversion, never
Excel's own arithmetic: where the two may differ, the Hive's answer is stored, such as a blank
where Excel shows an error (a StdDev of one value is #DIV/0! in Excel), or a tie in a rank,
ranked as Hive's RANK ranks it.

A pivot is laid out in compact form, as Excel lays out a new one: its Row fields in one column,
each item's subtotal on the item's own row, a Column field's subtotals after its items, its
Report filters above it, at A3 when it has one or none. What this doesn't write, and refuses
with a ValueError saying so: more than one value with a Column field (several values stand side
by side only with none), a pivot with no Row field, a value filter on any but the outermost Row
or Column field, a calculated item in a pivot whose values aren't all Sums shown as themselves,
a calculated formula of more than names, numbers, + - * / and parentheses, and a Data Model
pivot with more than Row fields and values.

Distinct Count is a summary only a Data Model pivot has, and a Data Model pivot reads its rows
through a connection to the workbook's Data Model, so `data_model=True` writes one: an OLAP
cache over the connection ThisWorkbookDataModel, with no records, its source Table added to the
model by a worksheet connection. Its model, a database Excel itself writes in
`xl/model/item.data`, isn't written, so Excel can't open it: it tests the reader alone. Its
connections are what the offline policy refuses in a committed workbook, so none is committed
without the user's OK to an `ALLOWED` entry.

Whether Excel opens a written workbook without a repair is checked by hand, by the user, on the
workbooks ticket 02 of `.scratch/toolbox-8-9/map.md` names: dev has no Excel.
"""

from __future__ import annotations

import datetime
import io
import re
import zipfile
from collections.abc import Callable
from dataclasses import dataclass, field
from xml.sax.saxutils import escape, quoteattr

from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import column_index_from_string, coordinate_from_string

from excel_queries import (HEAD, PACKAGE_RELATIONSHIPS, RELATIONSHIP_TYPES, SPREADSHEET,
                           relationship, with_relationships)

X14 = "http://schemas.microsoft.com/office/spreadsheetml/2009/9/main"
X15 = "http://schemas.microsoft.com/office/spreadsheetml/2010/11/main"
MARKUP = "http://schemas.openxmlformats.org/markup-compatibility/2006"
SHEET_DRAWING = "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"
DRAWING = "http://schemas.openxmlformats.org/drawingml/2006/main"
SPREADSHEET_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml."
TYPES = {
    "pivotCacheDefinition": SPREADSHEET_TYPE + "pivotCacheDefinition+xml",
    "pivotCacheRecords": SPREADSHEET_TYPE + "pivotCacheRecords+xml",
    "pivotTable": SPREADSHEET_TYPE + "pivotTable+xml",
    "connections": SPREADSHEET_TYPE + "connections+xml",
    "drawing": "application/vnd.openxmlformats-officedocument.drawing+xml",
    "slicer": "application/vnd.ms-excel.slicer+xml",
    "slicerCache": "application/vnd.ms-excel.slicerCache+xml",
    "timeline": "application/vnd.ms-excel.timeline+xml",
    "timelineCache": "application/vnd.ms-excel.timelineCache+xml",
}
# Each relationship's type that isn't under RELATIONSHIP_TYPES.
OFFICE_RELATIONSHIPS = {
    "slicer": "http://schemas.microsoft.com/office/2007/relationships/slicer",
    "slicerCache": "http://schemas.microsoft.com/office/2007/relationships/slicerCache",
    "timeline": "http://schemas.microsoft.com/office/2011/relationships/timeline",
    "timelineCache": "http://schemas.microsoft.com/office/2011/relationships/timelineCache",
}
# Each extension, by the URI [MS-XLSX] gives it.
EXTENSIONS = {
    "pivotCacheDefinition": "{725AE2AE-9491-48be-B2B4-4EB974FC3084}",
    "pivotTableDefinition": "{962EF5D1-5CA2-4c93-8EF4-DBF5C05439D2}",
    "dataField": "{E15A36E0-9728-4e99-A89B-3F7291B0FE68}",
    "pivotFilter": "{0605FD5F-26C8-4aeb-8148-2DB25E43C511}",
    "slicerCaches": "{BBE1A952-AA13-448e-AADC-164F8A28A991}",
    "slicerList": "{A8765BA9-456A-4dab-B4F3-ACF838C121DE}",
    "timelineCacheRefs": "{D0CA8CA8-9F24-4464-BF8E-62219DCF47F9}",
    "timelineRefs": "{7E03D99C-DC04-49d9-9315-930204A7B6E9}",
    "dataModel": "{FCE2AD5D-F65C-4FA6-A056-5C36A1767C68}",
    "connection": "{DE250136-89BD-433C-8126-D09CA5730AF9}",
}
# Each summary a value may have, by the word Excel's file holds, and its caption's first words.
SUMMARIES = {"sum": "Sum", "count": "Count", "average": "Average", "max": "Max", "min": "Min",
             "stdDev": "StdDev", "var": "Var", "distinctCount": "Distinct Count"}
# Each Show Values As a value may have; rank is Excel 2010's, saved in an extension.
SHOWN_AS = ("", "percentOfTotal", "percentOfRow", "percentOfCol", "runTotal", "difference",
            "rank")
PERCENTS = ("percentOfTotal", "percentOfRow", "percentOfCol")
# The date levels a date field may be grouped by, coarsest first.
DATE_LEVELS = ("years", "quarters", "months")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
BLANK = "(blank)"
# Excel counts days from this one, so 2026-09-23 is day 46288.
DAY_ZERO = datetime.datetime(1899, 12, 30)
# When the caches were last refreshed, written the same in every build.
REFRESHED = "46290.5"
FORMULA_TOKEN = re.compile(r"\s*('[^']*'|[A-Za-z_]\w*|\d+(?:\.\d+)?|[-+*/()])")
NAME_TOKEN = re.compile(r"'[^']*'|[A-Za-z_]\w*")
# How many columns and rows a slicer or Timeline's drawing takes, beside its pivot.
SLICER_WIDTH, SLICER_HEIGHT = 3, 10
# What every pivot's definition says as a new one Excel 2019 or later saves: compact form,
# Excel's own formats, values captioned "Values".
COMMON_PIVOT_ATTRIBUTES = (
    'applyNumberFormats="0" applyBorderFormats="0" applyFontFormats="0" '
    'applyPatternFormats="0" applyAlignmentFormats="0" applyWidthHeightFormats="1" '
    'dataCaption="Values" updatedVersion="8" minRefreshableVersion="3" useAutoFormatting="1" '
    'itemPrintTitles="1" createdVersion="8" indent="0" outline="1" outlineData="1" '
    'multipleFieldFilters="0"')
# A Data Model pivot's hierarchy, one for each of its cache's.
PIVOT_HIERARCHY = '<pivotHierarchy dragToData="1"/>'
STYLE = ('<pivotTableStyleInfo name="PivotStyleLight16" showRowHeaders="1" showColHeaders="1" '
         'showRowStripes="0" showColStripes="0" showLastColumn="1"/>')


# --- What a pivot is ------------------------------------------------------------------------


@dataclass(frozen=True)
class Value:
    """One value of a pivot: the `summary` of the source field `field`, by Excel's word for
    it (`sum`, `count`, `average`, `max`, `min`, `stdDev`, `var`, or `distinctCount`, which
    only a Data Model pivot has), shown as itself or as `shown_as` says: `percentOfTotal`,
    `percentOfRow`, `percentOfCol`, `runTotal` in `base_field`, `difference` from the item
    `base_item` of `base_field`, or `rank`, largest first, in `base_field`. `name` is its
    caption; left out, it is Excel's, such as "Sum of duration_mins"."""

    field: str
    summary: str = "sum"
    shown_as: str = ""
    base_field: str = ""
    base_item: object = None
    name: str = ""


@dataclass(frozen=True)
class Top:
    """A value filter, as Excel's Top 10 keeps items: the `count` items of `field` whose
    value (the pivot's `value`th) is largest, or smallest when `bottom`."""

    field: str
    count: int
    value: int = 0
    bottom: bool = False


@dataclass(frozen=True)
class Pivot:
    """One PivotTable over the Table or plain range `source`, on `sheet`, named `name`, its
    top left at `at`, or else at A3, or below its Report filters.

    `rows` and `columns` are its Row and Column fields, outermost first; `values` its values.
    `report_filters` gives each Report filter's selected items, all of them when empty;
    `hidden` the items hidden on a Row or Column field; `top` a value filter. Its cache, which
    pivots on one source with the same of these share, holds `calculated_fields` (each name
    and formula, such as "duration_mins/60"), `calculated_items` (each field, item name and
    formula, such as ("team", "data_web", "data+web")), `dates`, each date field grouped by
    the levels named (`months`, `quarters`, `years`), and `bins`, each number field grouped
    from a start to an end in bins as wide as the third number. A grouped date field keeps its
    name for its finest level, and each coarser level is a field of its own, "Quarters" or
    "Years", as Excel names them. A grouped field's item is named by its label: "Sep", "10-19".

    `subtotals_off` names each field whose subtotals are off. `grand_total_row` is the Grand
    Total row at the bottom, `grand_total_column` the one at the right (in Excel's file,
    colGrandTotals and rowGrandTotals). `source_rows` is Hive giving every column of a source
    that holds formulas, each formula's column worked out. `data_model` writes a Data Model
    pivot, the only kind with Distinct Count."""

    source: str
    rows: tuple[str, ...]
    values: tuple[Value, ...]
    name: str = "PivotTable1"
    sheet: str = "Pivot"
    at: str = ""
    columns: tuple[str, ...] = ()
    report_filters: dict[str, tuple[object, ...]] = field(default_factory=dict)
    hidden: dict[str, tuple[object, ...]] = field(default_factory=dict)
    top: Top | None = None
    calculated_fields: dict[str, str] = field(default_factory=dict)
    calculated_items: tuple[tuple[str, str, str], ...] = ()
    dates: dict[str, tuple[str, ...]] = field(default_factory=dict)
    bins: dict[str, tuple[float, float, float]] = field(default_factory=dict)
    subtotals_off: tuple[str, ...] = ()
    grand_total_row: bool = True
    grand_total_column: bool = True
    source_rows: str = ""
    data_model: bool = False


@dataclass(frozen=True)
class Slicer:
    """A slicer on `field`, filtering each pivot `pivots` names, all on one cache, to the
    items `selected`, on the first of those pivots' sheet."""

    field: str
    pivots: tuple[str, ...]
    selected: tuple[object, ...]


@dataclass(frozen=True)
class Timeline:
    """A Timeline on the date field `field`, filtering each pivot `pivots` names, all on one
    cache, to the days from `start` to `end`, each yyyy-MM-dd, on the first of those pivots'
    sheet."""

    field: str
    pivots: tuple[str, ...]
    start: str
    end: str


@dataclass(frozen=True)
class Source:
    """What a pivot reads: the Table `name`, or, when `ref` gives its place, the plain range
    there on the sheet `name`; its `columns`, and the `rows` that `hive`, run on the Example
    database, gives. Each column `dates` names holds yyyy-MM-dd text, which the workbook holds
    as dates."""

    name: str
    columns: tuple[str, ...]
    rows: tuple[tuple[object, ...], ...]
    hive: str
    dates: tuple[str, ...] = ()
    ref: str = ""


# --- A pivot cache --------------------------------------------------------------------------


@dataclass(frozen=True)
class Group:
    """How a cache field groups the date or number field at `base`: by `level` (`months`,
    `quarters`, `years` or `bins`) into the items `labels`, the first and last for values
    before and after its range, which `bounds` gives (a bin's width third); `parent` is the
    field of its next coarser level."""

    level: str
    base: int
    labels: tuple[str, ...]
    bounds: tuple[object, ...]
    parent: int | None = None


@dataclass
class CacheField:
    """One field of a pivot cache: a source column, at `column` in each row; a coarser date
    level of one (`group`, with no column); or a calculated field (`formula`). `shared`
    holds its items in the order they first appear, when it `is_shared`, as a field on an
    axis, filtered or sliced is, then its calculated items."""

    name: str
    column: int | None = None
    formula: str = ""
    group: Group | None = None
    is_shared: bool = False
    shared: list[object] = field(default_factory=list)
    calculated_items: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class Cache:
    """One pivot cache, number `id` in the workbook, over `source`, shared by `pivots`."""

    id: int
    source: Source
    fields: list[CacheField]
    pivots: list[Pivot]
    data_model: bool = False


@dataclass(frozen=True)
class Item:
    """One item of a field, in the order a pivot shows them: `x` its place among the cache's
    shared items or its group's labels, `key` what the Hive gives for it, `label` what its
    cell shows."""

    x: int
    key: object
    label: object


@dataclass(frozen=True)
class Line:
    """One row or column of a pivot's body: an `item`, `path` the places of its items, one
    per field, outermost first; the `subtotal` of the item its path ends at; the `grand`
    total; or, with no Column field, the column of the pivot's `value`th value."""

    kind: str
    path: tuple[int, ...] = ()
    value: int = 0


@dataclass
class WorkedPivot:
    """A pivot worked out: its cache, its body's `rows` and `columns`, the row and column of
    its body's top left cell (`corner`), each cell it fills on its sheet with its stored
    value, and the Hive the values were worked out by."""

    pivot: Pivot
    cache: Cache
    rows: list[Line]
    columns: list[Line]
    corner: tuple[int, int]
    cells: dict[str, object]
    hive: list[str]


@dataclass
class Worked:
    """Every pivot of a workbook worked out, their caches, and the slicers and Timelines on
    them."""

    caches: list[Cache]
    pivots: list[WorkedPivot]
    slicers: tuple[Slicer | Timeline, ...]


def _plain_value(value: object) -> object:
    """A value from the Example database as a cell holds it: a plain number or text, or None
    for a blank cell."""
    if value is None or value != value:  # None, or a missing number
        return None
    return value.item() if hasattr(value, "item") else value


def caption(value: Value) -> str:
    """A value's caption: its name, or Excel's, such as "Sum of duration_mins"."""
    return value.name or f"{SUMMARIES[value.summary]} of {value.field}"


def _day(text: str) -> datetime.datetime:
    return datetime.datetime.strptime(text, "%Y-%m-%d")


def _number(value: float) -> str:
    """A number as Excel's file writes it: a whole number with no `.0`."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _sort_key(value: object) -> tuple[bool, bool, object]:
    """Where an item sorts: Excel's A to Z, numbers before text, a blank last."""
    if value is None:
        return (True, False, 0)
    if isinstance(value, str):
        return (False, True, value.lower())
    return (False, False, value)


def _date_labels(level: str, first: datetime.datetime, end: datetime.datetime
                 ) -> tuple[str, ...]:
    """A date level's items, as Excel labels them: before the range, each month, quarter or
    year, then after it."""
    before = f"<{first.month}/{first.day}/{first.year}"
    after = f">{end.month}/{end.day}/{end.year}"
    if level == "months":
        middle = MONTHS
    elif level == "quarters":
        middle = ("Qtr1", "Qtr2", "Qtr3", "Qtr4")
    else:
        middle = tuple(str(year) for year in range(first.year, end.year + 1))
    return (before, *middle, after)


def _bin_labels(start: float, end: float, size: float, whole: bool) -> tuple[str, ...]:
    """Bins' items, as Excel labels them: below the start, each bin, above the end."""
    labels = [f"<{_number(start)}"]
    low = start
    while low <= end:
        high = low + size - 1 if whole else low + size
        labels.append(f"{_number(low)}-{_number(high)}")
        low += size
    return (*labels, f">{_number(end)}")


def _date_fields(source: Source, pivot: Pivot, fields: list[CacheField]) -> None:
    """Group each date field `pivot.dates` names: the field itself by its finest level, and a
    new field for each coarser level, Quarters or Years, after the source's."""
    for name, levels in pivot.dates.items():
        column = source.columns.index(name)
        days = [_day(row[column]) for row in source.rows if row[column] is not None]
        first, end = min(days), max(days) + datetime.timedelta(days=1)
        ordered = [level for level in DATE_LEVELS if level in levels]
        places = {ordered[-1]: column}
        for level in reversed(ordered[:-1]):
            places[level] = len(fields)
            fields.append(CacheField(level.capitalize()))
        for number, level in enumerate(ordered):
            parent = places[ordered[number - 1]] if number else None
            fields[places[level]].group = Group(level, column, _date_labels(level, first, end),
                                                (first, end), parent)


def _bin_fields(source: Source, pivot: Pivot, fields: list[CacheField]) -> None:
    """Group each number field `pivot.bins` names into its bins."""
    for name, (start, end, size) in pivot.bins.items():
        column = source.columns.index(name)
        whole = all(isinstance(row[column], int) for row in source.rows
                    if row[column] is not None)
        fields[column].group = Group("bins", column, _bin_labels(start, end, size, whole),
                                     (start, end, size))


def _shared_fields(pivots: list[Pivot], slicers: tuple[Slicer | Timeline, ...]) -> set[str]:
    """The fields whose items a cache shares: each on an axis, filtered, hidden or sliced."""
    names = {pivot.name for pivot in pivots}
    shared = {slicer.field for slicer in slicers
              if isinstance(slicer, Slicer) and set(slicer.pivots) & names}
    for pivot in pivots:
        shared |= {*pivot.rows, *pivot.columns, *pivot.report_filters, *pivot.hidden}
    return shared


def _new_cache(number: int, source: Source, pivots: list[Pivot],
               slicers: tuple[Slicer | Timeline, ...]) -> Cache:
    """The cache `pivots` share over `source`: a field for each source column, then each
    coarser date level and each calculated field; each shared field's items, and its
    calculated items."""
    pivot = pivots[0]
    fields = [CacheField(name, column) for column, name in enumerate(source.columns)]
    _date_fields(source, pivot, fields)
    _bin_fields(source, pivot, fields)
    fields += [CacheField(name, formula=formula)
               for name, formula in pivot.calculated_fields.items()]
    shared = _shared_fields(pivots, slicers)
    for cache_field in fields:
        if cache_field.column is None or cache_field.group or cache_field.name not in shared:
            continue
        cache_field.is_shared = True
        column = [row[cache_field.column] for row in source.rows]
        cache_field.shared = list(dict.fromkeys(column))
    for name, item, formula in pivot.calculated_items:
        named = _field(fields, name)
        named.calculated_items.append((item, formula))
        named.shared.append(item)
    return Cache(number, source, fields, pivots, pivot.data_model)


def _field(fields: list[CacheField], name: str) -> CacheField:
    for cache_field in fields:
        if cache_field.name == name:
            return cache_field
    raise ValueError(f"A pivot names a field {name!r} its source doesn't have.")


def _place(cache: Cache, name: str) -> int:
    return cache.fields.index(_field(cache.fields, name))


def items(cache: Cache, place: int) -> list[Item]:
    """The items of the cache's field at `place`, in the order a pivot shows them: a grouped
    field's labels in order; else its shared items A to Z, a blank last, then its calculated
    items."""
    cache_field = cache.fields[place]
    if cache_field.group:
        return [Item(number, number, label)
                for number, label in enumerate(cache_field.group.labels)]
    calculated = [item for item, _ in cache_field.calculated_items]
    real = [value for value in cache_field.shared if value not in calculated]
    found = []
    for value in sorted(real, key=_sort_key):
        label = BLANK if value is None else value
        found.append(Item(cache_field.shared.index(value), value, label))
    return found + [Item(cache_field.shared.index(item), item, item) for item in calculated]


def _cache_key(pivot: Pivot) -> str:
    """What pivots must agree on to share a cache: their source and what their cache holds."""
    return repr((pivot.source, pivot.source_rows, sorted(pivot.dates.items()),
                 sorted(pivot.bins.items()), sorted(pivot.calculated_fields.items()),
                 pivot.calculated_items, pivot.data_model))


# --- The Hive each stored value is worked out by --------------------------------------------


def _literal(value: object) -> str:
    if isinstance(value, str):
        return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"
    return _number(value)


def _key_sql(cache: Cache, place: int) -> str:
    """Hive giving a field's key in a source row: its column's value, or, for a grouped
    field, its group's place among the labels."""
    cache_field = cache.fields[place]
    group = cache_field.group
    if not group:
        return cache_field.name
    base = cache.source.columns[group.base]
    if group.level == "months":
        branches = [f"WHEN SUBSTR({base}, 6, 2) = '{month:02d}' THEN {month}"
                    for month in range(1, 13)]
    elif group.level == "quarters":
        branches = [f"WHEN SUBSTR({base}, 6, 2) <= '{quarter * 3:02d}' THEN {quarter}"
                    for quarter in range(1, 5)]
    elif group.level == "years":
        branches = [f"WHEN SUBSTR({base}, 1, 4) = '{label}' THEN {number}"
                    for number, label in enumerate(group.labels[1:-1], 1)]
    else:
        branches = _bin_branches(base, group)
    return "CASE " + " ".join(branches) + " END"


def _bin_branches(base: str, group: Group) -> list[str]:
    """The CASE branches giving a number's bin: 0 below the start, the last above the end."""
    start, end, size = group.bounds
    last = len(group.labels) - 1
    branches = [f"WHEN {base} < {_number(start)} THEN 0"]
    for number in range(1, last - 1):
        branches.append(f"WHEN {base} < {_number(start + number * size)} THEN {number}")
    return [*branches, f"WHEN {base} <= {_number(end)} THEN {last - 1}",
            f"WHEN {base} > {_number(end)} THEN {last}"]


def _key_of(cache: Cache, place: int, given: object) -> object:
    """The key of an item as a description names it: a grouped field's by its label."""
    group = cache.fields[place].group
    if group:
        return group.labels.index(given)
    return given


def _kept(key: str, keys: list[object]) -> str:
    """Hive keeping the rows whose `key` is one of `keys`, a blank among them as IS NULL."""
    values = [_literal(value) for value in keys if value is not None]
    parts = []
    if values:
        parts.append(f"{key} IN ({', '.join(values)})")
    if None in keys:
        parts.append(f"{key} IS NULL")
    if not parts:
        return "1 = 0"
    return "(" + " OR ".join(parts) + ")"


def _dropped(key: str, keys: list[object]) -> str:
    """Hive dropping the rows whose `key` is one of `keys`, a blank among them as IS NULL."""
    values = [_literal(value) for value in keys if value is not None]
    if None in keys and values:
        return f"({key} IS NOT NULL AND {key} NOT IN ({', '.join(values)}))"
    if None in keys:
        return f"{key} IS NOT NULL"
    return f"({key} IS NULL OR {key} NOT IN ({', '.join(values)}))"


def _keys(cache: Cache, place: int, given: tuple[object, ...]) -> list[object]:
    return [_key_of(cache, place, item) for item in given]


def _conditions(worked: Worked, cache: Cache, pivot: Pivot) -> list[str]:
    """The WHERE of every Hive a pivot is worked out by: its Report filters, its hidden items,
    and each slicer's selection and Timeline's days on it."""
    found = []
    for name, selected in pivot.report_filters.items():
        place = _place(cache, name)
        if selected:
            found.append(_kept(_key_sql(cache, place), _keys(cache, place, selected)))
    for name, hidden in pivot.hidden.items():
        place = _place(cache, name)
        found.append(_dropped(_key_sql(cache, place), _keys(cache, place, hidden)))
    for slicer in worked.slicers:
        if pivot.name not in slicer.pivots:
            continue
        if isinstance(slicer, Timeline):
            found.append(f"{slicer.field} BETWEEN '{slicer.start}' AND '{slicer.end}'")
            continue
        place = _place(cache, slicer.field)
        found.append(_kept(_key_sql(cache, place), _keys(cache, place, slicer.selected)))
    return found


def _hive(cache: Cache, steps: list[str], select: str) -> str:
    """Hive reading the source's rows as `source`, then each step, then `select`."""
    return "WITH " + ", ".join([f"source AS ({cache.source.hive})", *steps]) + " " + select


def _formula_sql(formula: str, written: Callable[[str], str]) -> str:
    """A calculated field's or item's formula as Hive, each name in it as `written` writes
    it: only names, numbers, + - * / and parentheses."""
    tokens = [token.strip() for token in FORMULA_TOKEN.findall(formula)]
    if "".join(tokens) != re.sub(r"\s+", "", formula):
        raise ValueError("The pivot tool writes a calculated formula of names, numbers, "
                         f"+ - * / and parentheses only, not {formula!r}.")
    return " ".join(written(token.strip("'")) if NAME_TOKEN.fullmatch(token) else token
                    for token in tokens)


def _aggregate(cache: Cache, value: Value) -> str:
    """Hive giving one value's summary over a group's source rows; a calculated field's
    formula over the Sums of the fields it names, as Excel works one out."""
    formula = _field(cache.fields, value.field).formula
    if formula:
        return _formula_sql(formula, _sum_of)
    name = value.field
    variance = (f"CASE WHEN COUNT({name}) > 1 THEN (SUM({name} * {name}) - SUM({name}) * "
                f"SUM({name}) / COUNT({name})) / (COUNT({name}) - 1) END")
    sql = {"sum": f"SUM({name})", "count": f"COUNT({name})", "average": f"AVG({name})",
           "max": f"MAX({name})", "min": f"MIN({name})", "var": variance,
           "stdDev": f"POWER({variance}, 0.5)", "distinctCount": f"COUNT(DISTINCT {name})"}
    return sql[value.summary]


def _sum_of(name: str) -> str:
    return f"SUM({name})"


def _calculated_sql(cache: Cache, place: int, formula: str, value: Value) -> str:
    """Hive giving a calculated item's value of `value` over a group's source rows: its
    formula over each item's Sum, an item with no rows counting 0, as in Excel."""
    key = _key_sql(cache, place)

    def item_sum(item: str) -> str:
        return f"COALESCE(SUM(CASE WHEN {key} = {_literal(item)} THEN {value.field} END), 0)"

    return _formula_sql(formula, item_sum)


def _grouped_sql(cache: Cache, keys: list[int], aggregate: str, where: list[str]) -> str:
    """Hive grouping the source rows `where` keeps by the fields at `keys`, giving them as
    k0, k1 and so on, then v, the `aggregate`."""
    selected = [f"{_key_sql(cache, place)} AS k{number}" for number, place in enumerate(keys)]
    sql = f"SELECT {', '.join([*selected, f'{aggregate} AS v'])} FROM source"
    if where:
        sql += " WHERE " + " AND ".join(where)
    if keys:
        sql += " GROUP BY " + ", ".join(_key_sql(cache, place) for place in keys)
    return sql


def _position_sql(cache: Cache, place: int, key: str) -> str:
    """Hive giving the place a pivot shows a key's item at, the order a running total runs."""
    if cache.fields[place].group:
        return key
    branches = []
    for number, item in enumerate(items(cache, place)):
        if item.key is None:
            branches.append(f"WHEN {key} IS NULL THEN {number}")
        else:
            branches.append(f"WHEN {key} = {_literal(item.key)} THEN {number}")
    return "CASE " + " ".join(branches) + " END"


def _shown_sql(cache: Cache, value: Value, keys: list[int], across: int) -> str:
    """Hive giving the value as Show Values As shows it, over the grouped rows, whose first
    `across` keys are Row fields; NULL where its base field isn't among the keys."""
    names = [f"k{number}" for number in range(len(keys))]
    totalled = {"percentOfTotal": [], "percentOfRow": names[:across],
                "percentOfCol": names[across:]}
    if value.shown_as in totalled:
        return f"v / SUM(v) OVER ({_partition(totalled[value.shown_as])})"
    base = _place(cache, value.base_field)
    if base not in keys:
        return "NULL"
    key = names[keys.index(base)]
    others = _partition([name for name in names if name != key])
    if value.shown_as == "runTotal":
        order = _position_sql(cache, base, key)
        return (f"SUM(v) OVER ({others} ORDER BY {order} ROWS BETWEEN UNBOUNDED PRECEDING "
                "AND CURRENT ROW)")
    if value.shown_as == "rank":
        return f"RANK() OVER ({others} ORDER BY v DESC)"
    item = _literal(_key_of(cache, base, value.base_item))
    return (f"CASE WHEN {key} = {item} THEN NULL ELSE v - MAX(CASE WHEN {key} = {item} "
            f"THEN v END) OVER ({others}) END")


def _partition(names: list[str]) -> str:
    if not names:
        return ""
    return "PARTITION BY " + ", ".join(names)


def example_database_rows(hive: str) -> list[tuple[object, ...]]:
    """The rows `hive` gives on the Example database, each value as a cell holds it."""
    # Only a filled-in workbook reads the Example database: the empty Formula workbook, which
    # copilot_files.py builds, needs nothing of the Toolbox's.
    import example_database

    found = []
    for row in example_database.query(hive).itertuples(index=False):
        found.append(tuple(_plain_value(value) for value in row))
    return found


def _top_condition(cache: Cache, pivot: Pivot, where: list[str], ran: list[str]) -> str:
    """Hive keeping the items a value filter keeps, which Hive of their own works out."""
    top = pivot.top
    place = _place(cache, top.field)
    order = "ASC" if top.bottom else "DESC"
    grouped = _grouped_sql(cache, [place], _aggregate(cache, pivot.values[top.value]), where)
    hive = _hive(cache, [f"grouped AS ({grouped})",
                         f"ranked AS (SELECT k0, RANK() OVER (ORDER BY v {order}) AS place "
                         "FROM grouped)"],
                 f"SELECT k0 FROM ranked WHERE place <= {top.count}")
    ran.append(hive)
    return _kept(_key_sql(cache, place), [row[0] for row in example_database_rows(hive)])


@dataclass(frozen=True)
class _LevelHive:
    """The Hive of one total level's values: `hive`, giving each key of `keys` but the field
    at `item_place` when it gives a calculated item's rows, whose key is `item`."""

    hive: str
    keys: list[int]
    item_place: int | None = None
    item: str = ""


def _level_hive(cache: Cache, pivot: Pivot, keys: list[int], across: int, number: int,
                where: list[str]) -> list[_LevelHive]:
    """The Hive of one total level's values of the `number`th value, `keys` the fields it
    groups by: the value's own rows, then each calculated item's among the keys; a level
    without the calculated item's field adds the item up in its total, as Excel does."""
    value = pivot.values[number]
    aggregate = _aggregate(cache, value)
    found = []
    for place, cache_field in enumerate(cache.fields):
        for item, formula in cache_field.calculated_items:
            sql = _calculated_sql(cache, place, formula, value)
            if place not in keys:
                aggregate += f" + {sql}"
                continue
            others = [key for key in keys if key != place]
            found.append(_LevelHive(_hive(cache, [], _grouped_sql(cache, others, sql, where)),
                                    others, place, item))
    grouped = _grouped_sql(cache, keys, aggregate, where)
    if not value.shown_as:
        return [_LevelHive(_hive(cache, [], grouped), keys), *found]
    names = "".join(f"k{key}, " for key in range(len(keys)))
    shown = _shown_sql(cache, value, keys, across)
    return [_LevelHive(_hive(cache, [f"grouped AS ({grouped})"],
                             f"SELECT {names}{shown} AS v FROM grouped"), keys), *found]


def _level_values(cache: Cache, pivot: Pivot, level: tuple[int, int, int], where: list[str],
                  ran: list[str]) -> dict[tuple[tuple[int, ...], tuple[int, ...]], object]:
    """One total level's values, `level` how many Row and Column fields it groups by and
    which value, each by its row's and its column's paths of item places."""
    rows = [_place(cache, name) for name in pivot.rows[:level[0]]]
    columns = [_place(cache, name) for name in pivot.columns[:level[1]]]
    keys = rows + columns
    found = {}
    for level_hive in _level_hive(cache, pivot, keys, len(rows), level[2], where):
        ran.append(level_hive.hive)
        for row in example_database_rows(level_hive.hive):
            given = dict(zip(level_hive.keys, row[:-1], strict=True))
            if level_hive.item_place is not None:
                given[level_hive.item_place] = level_hive.item
            places = [_position(cache, key, given[key]) for key in keys]
            found[(tuple(places[:len(rows)]), tuple(places[len(rows):]))] = row[-1]
    return found


def _position(cache: Cache, place: int, key: object) -> int:
    """The place a pivot shows the item of a key at, among its field's items."""
    for number, item in enumerate(items(cache, place)):
        if item.key == key:
            return number
    raise ValueError(f"The Hive gave {key!r}, no item of {cache.fields[place].name}.")


# --- Laying out a pivot ---------------------------------------------------------------------


def _prefixes(paths: set[tuple[int, ...]]) -> list[tuple[int, ...]]:
    """Every path and each path leading to it, each before the paths it leads to."""
    found = set()
    for path in paths:
        found |= {path[:length] for length in range(1, len(path) + 1)}
    return sorted(found)


def _row_lines(pivot: Pivot, paths: set[tuple[int, ...]]) -> list[Line]:
    """A pivot's rows, in compact form: each item after its parent, then the Grand Total."""
    lines = [Line("item", path) for path in _prefixes(paths)]
    if pivot.grand_total_row:
        lines.append(Line("grand"))
    return lines


def _column_lines(pivot: Pivot, paths: set[tuple[int, ...]]) -> list[Line]:
    """A pivot's columns: each value's, with no Column field; else each item, each field's
    subtotals after its items, then the Grand Total."""
    if not pivot.columns:
        return [Line("item", (), number) for number in range(len(pivot.values))]
    lines = _columns_under(pivot, _prefixes(paths), ())
    if pivot.grand_total_column:
        lines.append(Line("grand"))
    return lines


def _columns_under(pivot: Pivot, prefixes: list[tuple[int, ...]], parent: tuple[int, ...]
                   ) -> list[Line]:
    lines = []
    for path in prefixes:
        if len(path) != len(parent) + 1 or path[:-1] != parent:
            continue
        if len(path) == len(pivot.columns):
            lines.append(Line("item", path))
            continue
        lines += _columns_under(pivot, prefixes, path)
        if pivot.columns[len(path) - 1] not in pivot.subtotals_off:
            lines.append(Line("subtotal", path))
    return lines


def repeats(lines: list[Line]) -> list[int]:
    """How many of each line's first items are the line before's, which Excel's file leaves
    out of the line (its `r`): never all of them."""
    found = []
    before: tuple[int, ...] = ()
    for line in lines:
        same = 0
        while same < min(len(line.path), len(before)) and line.path[same] == before[same]:
            same += 1
        found.append(min(same, max(len(line.path) - 1, 0)))
        before = line.path
    return found


def _shows_values(pivot: Pivot, line: Line, fields: tuple[str, ...]) -> bool:
    """Whether a row or column shows values: all but an outer item's own row or column
    when its field's subtotals are off."""
    if line.kind != "item" or len(line.path) in (0, len(fields)):
        return True
    return fields[len(line.path) - 1] not in pivot.subtotals_off


def work_out(pivots: tuple[Pivot, ...], slicers: tuple[Slicer | Timeline, ...],
             sources: dict[str, Source]) -> Worked:
    """Every pivot worked out over its source's rows, each source `sources` gives by name:
    their caches, one shared by the pivots that agree on what it holds, and each pivot's
    lines and cells, its values worked out by Hive on the Example database."""
    worked = Worked([], [], slicers)
    by_key: dict[str, Cache] = {}
    for pivot in pivots:
        _check(pivot)
        key = _cache_key(pivot)
        if key not in by_key:
            sharing = [other for other in pivots if _cache_key(other) == key]
            by_key[key] = _new_cache(len(by_key) + 1, sources[pivot.source], sharing, slicers)
            worked.caches.append(by_key[key])
    for slicer in slicers:
        caches = {_cache_key(pivot) for pivot in pivots if pivot.name in slicer.pivots}
        if len(caches) != 1:
            raise ValueError(f"A slicer or Timeline on {slicer.field} filters pivots of one "
                             "cache only: give them one source and the same cache.")
    for pivot in pivots:
        worked.pivots.append(_worked_pivot(worked, by_key[_cache_key(pivot)], pivot))
    return worked


def _check(pivot: Pivot) -> None:
    """Refuse what the tool doesn't write, saying what."""
    summaries = {value.summary for value in pivot.values}
    refused = [
        (not pivot.rows, "a pivot with no Row field"),
        (len(pivot.values) > 1 and bool(pivot.columns),
         "more than one value with a Column field"),
        (pivot.top is not None and pivot.top.field not in (*pivot.rows[:1], *pivot.columns[:1]),
         "a value filter on any but the outermost Row or Column field"),
        (bool(pivot.calculated_items) and (summaries != {"sum"} or any(
            value.shown_as for value in pivot.values)),
         "a calculated item in a pivot whose values aren't all Sums shown as themselves"),
        ("distinctCount" in summaries and not pivot.data_model,
         "Distinct Count but in a Data Model pivot"),
        (pivot.data_model and bool(pivot.columns or pivot.report_filters or pivot.hidden
                                   or pivot.top or pivot.calculated_fields
                                   or pivot.calculated_items or pivot.dates or pivot.bins),
         "a Data Model pivot with more than Row fields and values"),
        (not summaries <= set(SUMMARIES) or any(value.shown_as not in SHOWN_AS
                                                 for value in pivot.values),
         "a summary or a Show Values As Excel doesn't have"),
    ]
    for is_refused, what in refused:
        if is_refused:
            raise ValueError(f"The pivot tool doesn't write {what} ({pivot.name}).")


def _worked_pivot(worked: Worked, cache: Cache, pivot: Pivot) -> WorkedPivot:
    """One pivot's lines and cells, each value worked out by Hive."""
    ran: list[str] = []
    where = _conditions(worked, cache, pivot)
    if pivot.top:
        where.append(_top_condition(cache, pivot, where, ran))
    deepest = _level_values(cache, pivot, (len(pivot.rows), len(pivot.columns), 0), where,
                            ran)
    rows = _row_lines(pivot, {row for row, _ in deepest})
    columns = _column_lines(pivot, {column for _, column in deepest})
    values = {}
    for row in rows:
        for column in columns:
            level = (len(row.path), len(column.path), column.value)
            if level not in values:
                values[level] = _level_values(cache, pivot, level, where, ran)
    corner = _corner(pivot)
    cells = _filter_cells(cache, pivot, corner)
    cells.update(_body_cells(cache, pivot, rows, columns, corner, values))
    return WorkedPivot(pivot, cache, rows, columns, corner, cells, ran)


def _corner(pivot: Pivot) -> tuple[int, int]:
    """The row and column of a pivot body's top left cell: `at`, else A3, or lower to leave
    each Report filter its row above, and a blank row."""
    if pivot.at:
        column, row = coordinate_from_string(pivot.at)
        return row, column_index_from_string(column)
    return max(3, len(pivot.report_filters) + 2), 1


def _at(row: int, column: int) -> str:
    return f"{get_column_letter(column)}{row}"


def _label(cache: Cache, name: str, number: int) -> object:
    """What an item's cell shows: its label, an item of a date column as a date."""
    place = _place(cache, name)
    label = items(cache, place)[number].label
    cache_field = cache.fields[place]
    if cache_field.group or label == BLANK or cache_field.column is None:
        return label
    if cache.source.columns[cache_field.column] in cache.source.dates:
        return _day(label)
    return label


def _filter_cells(cache: Cache, pivot: Pivot, corner: tuple[int, int]) -> dict[str, object]:
    """Each Report filter's two cells, above the pivot: its field, and what it shows."""
    top, left = corner
    cells = {}
    first = top - len(pivot.report_filters) - 1
    for number, (name, selected) in enumerate(pivot.report_filters.items()):
        cells[_at(first + number, left)] = name
        if len(selected) == 1:
            place = _place(cache, name)
            item = _position(cache, place, _key_of(cache, place, selected[0]))
            cells[_at(first + number, left + 1)] = _label(cache, name, item)
        elif selected:
            cells[_at(first + number, left + 1)] = "(Multiple Items)"
        else:
            cells[_at(first + number, left + 1)] = "(All)"
    return cells


def _body_cells(cache: Cache, pivot: Pivot, rows: list[Line], columns: list[Line],
                corner: tuple[int, int], values: dict) -> dict[str, object]:
    """Each cell of a pivot's body: its headers, each row's and column's label, and each
    stored value."""
    top, left = corner
    first_row = top + len(pivot.columns) + 1
    cells = {_at(top + len(pivot.columns), left): "Row Labels"}
    if pivot.columns:
        cells[_at(top, left)] = caption(pivot.values[0])
        cells[_at(top, left + 1)] = "Column Labels"
    for number, (column, repeat) in enumerate(zip(columns, repeats(columns), strict=True)):
        cells.update(_column_header(cache, pivot, column, repeat, (top, left + 1 + number)))
    for number, row in enumerate(rows):
        cells[_at(first_row + number, left)] = _row_label(cache, pivot, row)
        for place, column in enumerate(columns):
            stored = _stored(pivot, values, row, column)
            if stored is not None:
                cells[_at(first_row + number, left + 1 + place)] = stored
    return cells


def _stored(pivot: Pivot, values: dict, row: Line, column: Line) -> object:
    if not (_shows_values(pivot, row, pivot.rows)
            and _shows_values(pivot, column, pivot.columns)):
        return None
    level = (len(row.path), len(column.path), column.value)
    return values[level].get((row.path, column.path))


def _row_label(cache: Cache, pivot: Pivot, row: Line) -> object:
    if row.kind == "grand":
        return "Grand Total"
    return _label(cache, pivot.rows[len(row.path) - 1], row.path[-1])


def _column_header(cache: Cache, pivot: Pivot, column: Line, repeat: int,
                   place: tuple[int, int]) -> dict[str, object]:
    """A column's header cells: a value's caption, the Grand Total's, a subtotal's, or the
    label of each item its column is the first under."""
    top, at = place
    if not pivot.columns:
        return {_at(top, at): caption(pivot.values[column.value])}
    if column.kind == "grand":
        return {_at(top + 1, at): "Grand Total"}
    level = len(column.path) - 1
    if column.kind == "subtotal":
        label = _label(cache, pivot.columns[level], column.path[-1])
        return {_at(top + 1 + level, at): f"{label} Total"}
    return {_at(top + 1 + depth, at): _label(cache, pivot.columns[depth], column.path[depth])
            for depth in range(repeat, len(column.path))}


# --- The cache's parts ----------------------------------------------------------------------


def _is_day(cache: Cache, cache_field: CacheField) -> bool:
    return (cache_field.column is not None
            and cache.source.columns[cache_field.column] in cache.source.dates)


def _item_xml(value: object, is_day: bool) -> str:
    """One shared item or record value, as the cache writes it."""
    if value is None:
        return "<m/>"
    if is_day:
        return f'<d v="{value}T00:00:00"/>'
    if isinstance(value, str):
        return f"<s v={quoteattr(value)}/>"
    return f'<n v="{_number(value)}"/>'


def _shared_items_xml(cache: Cache, cache_field: CacheField) -> str:
    """A source field's sharedItems: what kinds of value it holds, and its items if shared."""
    values = [row[cache_field.column] for row in cache.source.rows]
    present = [value for value in values if value is not None]
    blank = ['containsBlank="1"'] if None in values else []
    if _is_day(cache, cache_field):
        flags = ['containsSemiMixedTypes="0"', 'containsNonDate="0"', 'containsDate="1"',
                 'containsString="0"', *blank, f'minDate="{min(present)}T00:00:00"',
                 f'maxDate="{max(present)}T00:00:00"']
    elif all(isinstance(value, str) for value in present):
        flags = blank
    else:
        flags = [*([] if blank else ['containsSemiMixedTypes="0"']), 'containsString="0"',
                 *blank, 'containsNumber="1"']
        if all(isinstance(value, int) for value in present):
            flags.append('containsInteger="1"')
        flags += [f'minValue="{_number(min(present))}"', f'maxValue="{_number(max(present))}"']
    if not cache_field.is_shared:
        return f"<sharedItems {' '.join(flags)}/>" if flags else "<sharedItems/>"
    shown = "".join(_item_xml(value, _is_day(cache, cache_field))
                    for value in cache_field.shared)
    flags.append(f'count="{len(cache_field.shared)}"')
    return f"<sharedItems {' '.join(flags)}>{shown}</sharedItems>"


def _field_group_xml(cache_field: CacheField) -> str:
    """How a field is grouped: its parent level, the field it groups, its range, and its
    items' labels."""
    group = cache_field.group
    if group is None:
        return ""
    parent = f' par="{group.parent}"' if group.parent is not None else ""
    if group.level == "bins":
        start, end, size = group.bounds
        bounds = (f'autoStart="0" autoEnd="0" startNum="{_number(start)}" '
                  f'endNum="{_number(end)}" groupInterval="{_number(size)}"')
    else:
        first, end = group.bounds
        bounds = (f'groupBy="{group.level}" startDate="{first.isoformat()}" '
                  f'endDate="{end.isoformat()}"')
    labels = "".join(f"<s v={quoteattr(label)}/>" for label in group.labels)
    return (f'<fieldGroup{parent} base="{group.base}"><rangePr {bounds}/>'
            f'<groupItems count="{len(group.labels)}">{labels}</groupItems></fieldGroup>')


def _cache_field_xml(cache: Cache, place: int) -> str:
    cache_field = cache.fields[place]
    name = quoteattr(cache_field.name)
    if cache_field.formula:
        return (f"<cacheField name={name} numFmtId=\"0\" formula="
                f"{quoteattr(cache_field.formula)} databaseField=\"0\"/>")
    group = _field_group_xml(cache_field)
    if cache_field.column is None:
        return f'<cacheField name={name} numFmtId="0" databaseField="0">{group}</cacheField>'
    number_format = "14" if _is_day(cache, cache_field) else "0"
    return (f'<cacheField name={name} numFmtId="{number_format}">'
            f"{_shared_items_xml(cache, cache_field)}{group}</cacheField>")


def _calculated_items_xml(cache: Cache) -> str:
    """The cache's calculated items, each its formula and the item it is."""
    found = []
    for place, cache_field in enumerate(cache.fields):
        for item, formula in cache_field.calculated_items:
            shared = cache_field.shared.index(item)
            found.append(
                f"<calculatedItem formula={quoteattr(formula)}><pivotArea cacheIndex=\"1\" "
                'outline="0" fieldPosition="0"><references count="1">'
                f'<reference field="{place}" count="1"><x v="{shared}"/>'
                "</reference></references></pivotArea></calculatedItem>")
    if not found:
        return ""
    return f'<calculatedItems count="{len(found)}">{"".join(found)}</calculatedItems>'


def cache_definition_xml(cache: Cache) -> str:
    """A pivot cache's definition part, over a Table or a plain range."""
    source = cache.source
    if source.ref:
        where = f"<worksheetSource ref=\"{source.ref}\" sheet={quoteattr(source.name)}/>"
    else:
        where = f"<worksheetSource name={quoteattr(source.name)}/>"
    fields = "".join(_cache_field_xml(cache, place) for place in range(len(cache.fields)))
    return (f'{HEAD}<pivotCacheDefinition xmlns="{SPREADSHEET}" xmlns:r="{RELATIONSHIP_TYPES}"'
            f' r:id="rId1" refreshedDate="{REFRESHED}" createdVersion="8" refreshedVersion="8"'
            f' minRefreshableVersion="3" recordCount="{len(source.rows)}">'
            f'<cacheSource type="worksheet">{where}</cacheSource>'
            f'<cacheFields count="{len(cache.fields)}">{fields}</cacheFields>'
            f"{_calculated_items_xml(cache)}"
            f'<extLst><ext uri="{EXTENSIONS["pivotCacheDefinition"]}" xmlns:x14="{X14}">'
            f'<x14:pivotCacheDefinition pivotCacheId="{cache.id}"/></ext></extLst>'
            "</pivotCacheDefinition>")


def records_xml(cache: Cache) -> str:
    """A pivot cache's records part: each source row, a shared field's value by its place
    among the shared items, any other as itself."""
    rows = []
    for row in cache.source.rows:
        values = []
        for cache_field in cache.fields:
            if cache_field.column is None:
                continue
            value = row[cache_field.column]
            if cache_field.is_shared:
                values.append(f'<x v="{cache_field.shared.index(value)}"/>')
            else:
                values.append(_item_xml(value, _is_day(cache, cache_field)))
        rows.append("<r>" + "".join(values) + "</r>")
    return (f'{HEAD}<pivotCacheRecords xmlns="{SPREADSHEET}" xmlns:r="{RELATIONSHIP_TYPES}" '
            f'count="{len(rows)}">{"".join(rows)}</pivotCacheRecords>')


# --- The pivot table's part -----------------------------------------------------------------


def _hidden_keys(worked: Worked, pivot: Pivot, cache: Cache, name: str) -> list[object]:
    """The keys of the items a pivot hides on a field: hidden, left out of a Report filter
    of several items, or not selected on a slicer."""
    place = _place(cache, name)
    keys = _keys(cache, place, pivot.hidden.get(name, ()))
    selections = [selected for field_name, selected in pivot.report_filters.items()
                  if field_name == name and len(selected) > 1]
    selections += [slicer.selected for slicer in worked.slicers if isinstance(slicer, Slicer)
                   and slicer.field == name and pivot.name in slicer.pivots]
    for selected in selections:
        kept = _keys(cache, place, selected)
        keys += [item.key for item in items(cache, place) if item.key not in kept]
    return keys


def _pivot_field_xml(worked: Worked, pivot: Pivot, cache: Cache, place: int) -> str:
    """One field as a pivot holds it: on which axis, whether it is a value, whether its
    subtotals show, and, for a field on an axis, filtered or sliced, its items."""
    cache_field = cache.fields[place]
    name = cache_field.name
    axes = {**dict.fromkeys(pivot.report_filters, "axisPage"),
            **dict.fromkeys(pivot.columns, "axisCol"), **dict.fromkeys(pivot.rows, "axisRow")}
    attributes = [f'axis="{axes[name]}"'] if name in axes else []
    if name in {value.field for value in pivot.values}:
        attributes.append('dataField="1"')
    if len(pivot.report_filters.get(name, ())) > 1:
        attributes.append('multipleItemSelectionAllowed="1"')
    if cache_field.formula:
        attributes += ['dragToRow="0"', 'dragToCol="0"', 'dragToPage="0"']
    attributes.append('showAll="0"')
    subtotals = not (cache_field.formula or name in pivot.subtotals_off)
    if not subtotals:
        attributes.append('defaultSubtotal="0"')
    hidden = _hidden_keys(worked, pivot, cache, name)
    if name not in axes and not hidden:
        return f"<pivotField {' '.join(attributes)}/>"
    shown = ""
    for item in items(cache, place):
        mark = ' h="1"' if item.key in hidden else ""
        shown += f'<item x="{item.x}"{mark}/>'
    count = len(items(cache, place)) + subtotals
    total = '<item t="default"/>' if subtotals else ""
    return (f"<pivotField {' '.join(attributes)}><items count=\"{count}\">{shown}{total}"
            "</items></pivotField>")


def _line_xml(line: Line, repeat: int) -> str:
    """One row or column item of a pivot's file: its kind, how many items it repeats, which
    value, and each of its own items' places."""
    attributes = ""
    if line.kind in ("grand", "subtotal"):
        attributes += f' t="{"grand" if line.kind == "grand" else "default"}"'
    if repeat:
        attributes += f' r="{repeat}"'
    if line.value:
        attributes += f' i="{line.value}"'
    places = line.path[repeat:] or (0,)
    xs = "".join("<x/>" if place == 0 else f'<x v="{place}"/>' for place in places)
    return f"<i{attributes}>{xs}</i>"


def _lines_xml(lines: list[Line]) -> str:
    return "".join(_line_xml(line, repeat)
                   for line, repeat in zip(lines, repeats(lines), strict=True))


def _rows_xml(wp: WorkedPivot, fields: list[int]) -> str:
    """A pivot's Row fields, by their places among its fields, and its rows."""
    rows = "".join(f'<field x="{place}"/>' for place in fields)
    return (f'<rowFields count="{len(fields)}">{rows}</rowFields>'
            f'<rowItems count="{len(wp.rows)}">{_lines_xml(wp.rows)}</rowItems>')


def _columns_xml(wp: WorkedPivot) -> str:
    """A pivot's Column fields and columns: its values' own, the field -2, when it has more
    than one; one column and no field when it has one value and no Column field."""
    pivot, cache = wp.pivot, wp.cache
    xml = ""
    if len(pivot.values) > 1:
        xml = '<colFields count="1"><field x="-2"/></colFields>'
        columns = "".join(_line_xml(Line("item", (column.value,), column.value), 0)
                          for column in wp.columns)
    elif pivot.columns:
        names = "".join(f'<field x="{_place(cache, name)}"/>' for name in pivot.columns)
        xml = f'<colFields count="{len(pivot.columns)}">{names}</colFields>'
        columns = _lines_xml(wp.columns)
    else:
        columns = "<i/>"
    return xml + f'<colItems count="{len(wp.columns)}">{columns}</colItems>'


def _page_fields_xml(pivot: Pivot, cache: Cache) -> str:
    if not pivot.report_filters:
        return ""
    found = []
    for name, selected in pivot.report_filters.items():
        place = _place(cache, name)
        item = ""
        if len(selected) == 1:
            item = f' item="{_position(cache, place, _key_of(cache, place, selected[0]))}"'
        found.append(f'<pageField fld="{place}"{item} hier="-1"/>')
    return f'<pageFields count="{len(found)}">{"".join(found)}</pageFields>'


def _data_field_xml(pivot: Pivot, cache: Cache, value: Value) -> str:
    """One value as a pivot's file holds it: its caption, field, summary and Show Values As."""
    attributes = [f"name={quoteattr(caption(value))}", f'fld="{_place(cache, value.field)}"']
    if value.summary not in ("sum", "distinctCount"):
        attributes.append(f'subtotal="{value.summary}"')
    if value.shown_as and value.shown_as != "rank":
        attributes.append(f'showDataAs="{value.shown_as}"')
    base_field = _place(cache, value.base_field) if value.base_field else 0
    base_item = 0
    if value.shown_as == "difference":
        base_item = _position(cache, base_field, _key_of(cache, base_field, value.base_item))
    attributes += [f'baseField="{base_field}"', f'baseItem="{base_item}"']
    if value.shown_as in PERCENTS:
        attributes.append('numFmtId="10"')
    if value.shown_as != "rank":
        return f"<dataField {' '.join(attributes)}/>"
    return (f"<dataField {' '.join(attributes)}><extLst><ext uri=\"{EXTENSIONS['dataField']}\""
            f' xmlns:x14="{X14}"><x14:dataField pivotShowAs="rankDescending"/></ext></extLst>'
            "</dataField>")


def timeline_name(timeline: Timeline) -> str:
    """The name of a Timeline's cache, and its defined name, as Excel names them."""
    return "NativeTimeline_" + re.sub(r"\W", "_", timeline.field)


def slicer_name(slicer: Slicer) -> str:
    """The name of a slicer's cache, and its defined name, as Excel names them."""
    return "Slicer_" + re.sub(r"\W", "_", slicer.field)


def _serial(day: str) -> int:
    return (_day(day) - DAY_ZERO).days


def _filters_xml(worked: Worked, pivot: Pivot, cache: Cache) -> str:
    """A pivot's value filter and each Timeline's filter on it."""
    found = []
    if pivot.top:
        top = '' if not pivot.top.bottom else ' top="0"'
        found.append(f'<filter fld="{_place(cache, pivot.top.field)}" type="count" '
                     f'evalOrder="-1" id="{len(found) + 1}" iMeasureFld="{pivot.top.value}">'
                     '<autoFilter ref="A1"><filterColumn colId="0">'
                     f'<top10{top} val="{pivot.top.count}" filterVal="{pivot.top.count}"/>'
                     "</filterColumn></autoFilter></filter>")
    for timeline in _timelines_on(worked, pivot):
        found.append(
            f'<filter fld="{_place(cache, timeline.field)}" type="dateBetween" evalOrder="-1" '
            f'id="{len(found) + 1}" name="{timeline_name(timeline)}"><autoFilter ref="A1">'
            '<filterColumn colId="0"><customFilters and="1"><customFilter '
            f'operator="greaterThanOrEqual" val="{_serial(timeline.start)}"/><customFilter '
            f'operator="lessThanOrEqual" val="{_serial(timeline.end)}"/></customFilters>'
            f'</filterColumn></autoFilter><extLst><ext uri="{EXTENSIONS["pivotFilter"]}" '
            f'xmlns:x15="{X15}"><x15:pivotFilter useWholeDay="1"/></ext></extLst></filter>')
    if not found:
        return ""
    return f'<filters count="{len(found)}">{"".join(found)}</filters>'


def _timelines_on(worked: Worked, pivot: Pivot) -> list[Timeline]:
    return [slicer for slicer in worked.slicers
            if isinstance(slicer, Timeline) and pivot.name in slicer.pivots]


def location_xml(wp: WorkedPivot) -> str:
    """Where a pivot's body sits, and where its headers, values and Report filters are."""
    pivot = wp.pivot
    top, left = wp.corner
    bottom = top + len(pivot.columns) + len(wp.rows)
    header = "0" if len(pivot.values) > 1 else "1"
    pages = ""
    if pivot.report_filters:
        pages = f' rowPageCount="{len(pivot.report_filters)}" colPageCount="1"'
    return (f'<location ref="{_at(top, left)}:{_at(bottom, left + len(wp.columns))}" '
            f'firstHeaderRow="{header}" firstDataRow="{1 + len(pivot.columns)}" '
            f'firstDataCol="1"{pages}/>')


def pivot_table_xml(worked: Worked, wp: WorkedPivot) -> str:
    """A pivot table's definition part."""
    pivot, cache = wp.pivot, wp.cache
    totals = ""
    if not pivot.grand_total_column:
        totals += ' rowGrandTotals="0"'
    if not pivot.grand_total_row:
        totals += ' colGrandTotals="0"'
    fields = "".join(_pivot_field_xml(worked, pivot, cache, place)
                     for place in range(len(cache.fields)))
    rows = [_place(cache, name) for name in pivot.rows]
    values = "".join(_data_field_xml(pivot, cache, value) for value in pivot.values)
    return (f'{HEAD}<pivotTableDefinition xmlns="{SPREADSHEET}" name={quoteattr(pivot.name)} '
            f'cacheId="{cache.id}" {COMMON_PIVOT_ATTRIBUTES}{totals}>{location_xml(wp)}'
            f'<pivotFields count="{len(cache.fields)}">{fields}</pivotFields>'
            f"{_rows_xml(wp, rows)}{_columns_xml(wp)}{_page_fields_xml(pivot, cache)}"
            f'<dataFields count="{len(pivot.values)}">{values}</dataFields>{STYLE}'
            f'{_filters_xml(worked, pivot, cache)}'
            f'<extLst><ext uri="{EXTENSIONS["pivotTableDefinition"]}" xmlns:x14="{X14}">'
            '<x14:pivotTableDefinition hideValuesRow="1" '
            'xmlns:xm="http://schemas.microsoft.com/office/excel/2006/main"/></ext></extLst>'
            "</pivotTableDefinition>")


# --- Slicers and Timelines ------------------------------------------------------------------


def _first_pivot(worked: Worked, slicer: Slicer | Timeline) -> WorkedPivot:
    """The first pivot a slicer or Timeline filters, whose sheet it is on."""
    for wp in worked.pivots:
        if wp.pivot.name in slicer.pivots:
            return wp
    raise ValueError(f"A slicer or Timeline on {slicer.field} names no pivot of the workbook.")


def _pivots_xml(worked: Worked, slicer: Slicer | Timeline, tabs: dict[str, int]) -> str:
    """The pivots a slicer or Timeline filters, each by its sheet's tab id and its name."""
    found = "".join(f'<pivotTable tabId="{tabs[wp.pivot.sheet]}" '
                    f"name={quoteattr(wp.pivot.name)}/>"
                    for wp in worked.pivots if wp.pivot.name in slicer.pivots)
    return f"<pivotTables>{found}</pivotTables>"


def slicer_cache_xml(worked: Worked, slicer: Slicer, tabs: dict[str, int]) -> str:
    """A slicer's cache part: the pivots it filters, and each item, its selected ones marked."""
    cache = _first_pivot(worked, slicer).cache
    place = _place(cache, slicer.field)
    selected = _keys(cache, place, slicer.selected)
    shown = []
    for item in items(cache, place):
        mark = ' s="1"' if item.key in selected else ""
        shown.append(f'<i x="{item.x}"{mark}/>')
    return (f'{HEAD}<slicerCacheDefinition xmlns="{X14}" xmlns:mc="{MARKUP}" mc:Ignorable="x" '
            f'xmlns:x="{SPREADSHEET}" name="{slicer_name(slicer)}" '
            f"sourceName={quoteattr(slicer.field)}>{_pivots_xml(worked, slicer, tabs)}"
            f'<data><tabular pivotCacheId="{cache.id}"><items count="{len(shown)}">'
            f"{''.join(shown)}</items></tabular></data></slicerCacheDefinition>")


def timeline_cache_xml(worked: Worked, timeline: Timeline, tabs: dict[str, int]) -> str:
    """A Timeline's cache part: the pivots it filters, the filter it is on the first, the days
    it has selected, and the whole years its field's dates span."""
    owner = _first_pivot(worked, timeline)
    cache = owner.cache
    column = cache.source.columns.index(timeline.field)
    days = [_day(row[column]) for row in cache.source.rows if row[column] is not None]
    first = datetime.datetime(min(days).year, 1, 1)
    end = datetime.datetime(max(days).year + 1, 1, 1)
    filter_id = _timelines_on(worked, owner.pivot).index(timeline) + 1 + bool(owner.pivot.top)
    return (f'{HEAD}<timelineCacheDefinition xmlns="{X15}" xmlns:mc="{MARKUP}" '
            f'mc:Ignorable="x" xmlns:x="{SPREADSHEET}" name="{timeline_name(timeline)}" '
            f"sourceName={quoteattr(timeline.field)}>{_pivots_xml(worked, timeline, tabs)}"
            '<state minimalRefreshVersion="6" lastRefreshVersion="6" '
            f'pivotCacheId="{cache.id}" filterType="dateBetween" filterId="{filter_id}" '
            f"filterPivotName={quoteattr(owner.pivot.name)} "
            f'filterTabId="{tabs[owner.pivot.sheet]}"><selection '
            f'startDate="{timeline.start}T00:00:00" endDate="{timeline.end}T00:00:00"/>'
            f'<bounds startDate="{first.isoformat()}" endDate="{end.isoformat()}"/></state>'
            "</timelineCacheDefinition>")


def slicers_xml(slicers: list[Slicer]) -> str:
    """The slicers on one sheet."""
    found = "".join(f"<slicer name={quoteattr(slicer.field)} cache=\"{slicer_name(slicer)}\" "
                    f'caption={quoteattr(slicer.field)} rowHeight="241300"/>'
                    for slicer in slicers)
    return (f'{HEAD}<slicers xmlns="{X14}" xmlns:mc="{MARKUP}" mc:Ignorable="x" '
            f'xmlns:x="{SPREADSHEET}">{found}</slicers>')


def timelines_xml(timelines: list[Timeline]) -> str:
    """The Timelines on one sheet, each showing months."""
    found = "".join(
        f"<timeline name={quoteattr(timeline.field)} cache=\"{timeline_name(timeline)}\" "
        f'caption={quoteattr(timeline.field)} level="2" selectionLevel="2" '
        f'scrollPosition="{timeline.start}T00:00:00"/>' for timeline in timelines)
    return (f'{HEAD}<timelines xmlns="{X15}" xmlns:mc="{MARKUP}" mc:Ignorable="x" '
            f'xmlns:x="{SPREADSHEET}">{found}</timelines>')


def _anchor_xml(number: int, slicer: Slicer | Timeline, place: tuple[int, int]) -> str:
    """One slicer's or Timeline's place in its sheet's drawing, from the column and row
    `place` (counted from 0), drawn as Excel 2010 draws a slicer and Excel 2013 a Timeline."""
    column, row = place
    if isinstance(slicer, Slicer):
        needs = "a14"
        namespace = "http://schemas.microsoft.com/office/drawing/2010/slicer"
        required = 'xmlns:a14="http://schemas.microsoft.com/office/drawing/2010/main"'
        shape = f"<sle:slicer xmlns:sle=\"{namespace}\" name={quoteattr(slicer.field)}/>"
    else:
        needs = "tsle"
        namespace = "http://schemas.microsoft.com/office/drawing/2012/timeslicer"
        required = f'xmlns:tsle="{namespace}"'
        shape = f"<tsle:timeslicer name={quoteattr(slicer.field)}/>"
    return (f'<xdr:twoCellAnchor editAs="oneCell"><xdr:from><xdr:col>{column}</xdr:col>'
            f"<xdr:colOff>0</xdr:colOff><xdr:row>{row}</xdr:row><xdr:rowOff>0</xdr:rowOff>"
            f"</xdr:from><xdr:to><xdr:col>{column + SLICER_WIDTH}</xdr:col><xdr:colOff>0"
            f"</xdr:colOff><xdr:row>{row + SLICER_HEIGHT}</xdr:row><xdr:rowOff>0</xdr:rowOff>"
            f'</xdr:to><mc:AlternateContent xmlns:mc="{MARKUP}"><mc:Choice {required} '
            f'Requires="{needs}"><xdr:graphicFrame macro=""><xdr:nvGraphicFramePr>'
            f"<xdr:cNvPr id=\"{number + 1}\" name={quoteattr(slicer.field)}/>"
            "<xdr:cNvGraphicFramePr/></xdr:nvGraphicFramePr><xdr:xfrm><a:off x=\"0\" y=\"0\"/>"
            f'<a:ext cx="0" cy="0"/></xdr:xfrm><a:graphic><a:graphicData uri="{namespace}">'
            f"{shape}</a:graphicData></a:graphic></xdr:graphicFrame></mc:Choice>"
            "</mc:AlternateContent><xdr:clientData/></xdr:twoCellAnchor>")


def drawing_xml(worked: Worked, sheet: str) -> str:
    """The drawing placing each slicer and Timeline on `sheet`, to the right of its pivots,
    one under the other."""
    right = max(wp.corner[1] + len(wp.columns) for wp in worked.pivots
                if wp.pivot.sheet == sheet)
    on_sheet = [slicer for slicer in worked.slicers
                if _first_pivot(worked, slicer).pivot.sheet == sheet]
    anchors = "".join(_anchor_xml(number, slicer, (right + 1, number * (SLICER_HEIGHT + 1)))
                      for number, slicer in enumerate(on_sheet))
    return (f'{HEAD}<xdr:wsDr xmlns:xdr="{SHEET_DRAWING}" xmlns:a="{DRAWING}">{anchors}'
            "</xdr:wsDr>")


# --- A Data Model pivot ---------------------------------------------------------------------


def _model_name(cache: Cache, name: str) -> str:
    """A source column's hierarchy, as the Data Model names it: [Table].[column]."""
    return f"[{cache.source.name}].[{name}]"


def _model_fields(cache: Cache) -> list[tuple[str, int | None, int]]:
    """A Data Model cache's fields: each Row field, with its source column's place, then each
    value, a measure, with none; each with its hierarchy's place."""
    pivot = cache.pivots[0]
    found = [(name, _place(cache, name), _place(cache, name)) for name in pivot.rows]
    found += [(caption(value), None, len(cache.source.columns) + number)
              for number, value in enumerate(pivot.values)]
    return found


def data_model_cache_xml(cache: Cache) -> str:
    """A Data Model pivot's cache part: an OLAP cache over the connection
    ThisWorkbookDataModel, a field for each Row field and value, and no records."""
    fields = []
    for name, place, hierarchy in _model_fields(cache):
        if place is None:
            fields.append(f'<cacheField name="[Measures].[{escape(name)}]" '
                          f'caption={quoteattr(name)} numFmtId="0" hierarchy="{hierarchy}" '
                          'level="32767"/>')
            continue
        unique = escape(_model_name(cache, name))
        shared = "".join(f'<s v="{unique}.&amp;[{escape(str(item.label))}]" '
                         f"c={quoteattr(str(item.label))}/>" for item in items(cache, place))
        fields.append(f'<cacheField name="{unique}.[{escape(name)}]" caption={quoteattr(name)} '
                      f'numFmtId="0" hierarchy="{hierarchy}" level="1"><sharedItems '
                      f'count="{len(items(cache, place))}">{shared}</sharedItems></cacheField>')
    table = escape(cache.source.name)
    return (f'{HEAD}<pivotCacheDefinition xmlns="{SPREADSHEET}" xmlns:r="{RELATIONSHIP_TYPES}" '
            f'saveData="0" refreshedDate="{REFRESHED}" createdVersion="8" refreshedVersion="8" '
            'minRefreshableVersion="3" recordCount="0" supportSubquery="1" '
            'supportAdvancedDrill="1"><cacheSource type="external" connectionId="1"/>'
            f'<cacheFields count="{len(fields)}">{"".join(fields)}</cacheFields>'
            f'{_hierarchies_xml(cache)}<kpis count="0"/><dimensions count="2">'
            '<dimension measure="1" name="Measures" uniqueName="[Measures]" '
            'caption="Measures"/>'
            f'<dimension name="{table}" uniqueName="[{table}]" caption="{table}"/></dimensions>'
            f'<measureGroups count="1"><measureGroup name="{table}" caption="{table}"/>'
            '</measureGroups><maps count="1"><map measureGroup="0" dimension="1"/></maps>'
            f'<extLst><ext uri="{EXTENSIONS["pivotCacheDefinition"]}" xmlns:x14="{X14}">'
            f'<x14:pivotCacheDefinition slicerData="0" pivotCacheId="{cache.id}" '
            'supportSubqueryNonVisual="1" supportSubqueryCalcMem="1" supportAddCalcMems="1"/>'
            "</ext></extLst></pivotCacheDefinition>")


def _hierarchies_xml(cache: Cache) -> str:
    """A Data Model cache's hierarchies: one for each source column, then each measure, each
    naming the cache fields that use it."""
    used = {hierarchy: number for number, (_, _, hierarchy) in enumerate(_model_fields(cache))}
    found = []
    table = escape(cache.source.name)
    for place, name in enumerate(cache.source.columns):
        unique = escape(_model_name(cache, name))
        usage = ""
        if place in used:
            usage = (f'<fieldsUsage count="2"><fieldUsage x="-1"/>'
                     f'<fieldUsage x="{used[place]}"/></fieldsUsage>')
        found.append(f'<cacheHierarchy uniqueName="{unique}" caption={quoteattr(name)} '
                     f'attribute="1" defaultMemberUniqueName="{unique}.[All]" '
                     f'allUniqueName="{unique}.[All]" dimensionUniqueName="[{table}]" '
                     f'displayFolder="" count="0" unbalanced="0">{usage}</cacheHierarchy>')
    for number, value in enumerate(cache.pivots[0].values):
        name = escape(caption(value))
        found.append(f'<cacheHierarchy uniqueName="[Measures].[{name}]" caption="{name}" '
                     f'measure="1" displayFolder="" measureGroup="{table}" count="0" '
                     'oneField="1" hidden="1"><fieldsUsage count="1"><fieldUsage '
                     f'x="{used[len(cache.source.columns) + number]}"/></fieldsUsage>'
                     "</cacheHierarchy>")
    return f'<cacheHierarchies count="{len(found)}">{"".join(found)}</cacheHierarchies>'


def data_model_pivot_xml(wp: WorkedPivot) -> str:
    """A Data Model pivot's definition part: its fields as its OLAP cache numbers them, and a
    pivot hierarchy for each of the cache's hierarchies."""
    pivot, cache = wp.pivot, wp.cache
    fields = []
    for _, place, _ in _model_fields(cache):
        if place is None:
            fields.append('<pivotField dataField="1" showAll="0"/>')
            continue
        count = len(items(cache, place))
        shown = "".join(f'<item x="{number}"/>' for number in range(count))
        fields.append('<pivotField axis="axisRow" allDrilled="1" showAll="0" dataSourceSort="1"'
                      f' defaultAttributeDrillState="1"><items count="{count}">{shown}</items>'
                      "</pivotField>")
    values = "".join(f"<dataField name={quoteattr(caption(value))} "
                     f'fld="{len(pivot.rows) + number}" baseField="0" baseItem="0"/>'
                     for number, value in enumerate(pivot.values))
    count = len(cache.source.columns) + len(pivot.values)
    usage = "".join(f'<rowHierarchyUsage hierarchyUsage="{_place(cache, name)}"/>'
                    for name in pivot.rows)
    return (f'{HEAD}<pivotTableDefinition xmlns="{SPREADSHEET}" name={quoteattr(pivot.name)} '
            f'cacheId="{cache.id}" {COMMON_PIVOT_ATTRIBUTES}>{location_xml(wp)}'
            f'<pivotFields count="{len(fields)}">{"".join(fields)}</pivotFields>'
            f"{_rows_xml(wp, list(range(len(pivot.rows))))}{_columns_xml(wp)}"
            f'<dataFields count="{len(pivot.values)}">{values}</dataFields>'
            f'<pivotHierarchies count="{count}">{PIVOT_HIERARCHY * count}'
            f"</pivotHierarchies>{STYLE}"
            f'<rowHierarchiesUsage count="{len(pivot.rows)}">{usage}</rowHierarchiesUsage>'
            "</pivotTableDefinition>")


def _model_tables(caches: list[Cache]) -> list[str]:
    return list(dict.fromkeys(cache.source.name for cache in caches))


def connections_xml(caches: list[Cache]) -> str:
    """The workbook's connections: ThisWorkbookDataModel, then one adding each Data Model
    pivot's Table to the model."""
    model = ('<connection id="1" keepAlive="1" name="ThisWorkbookDataModel" '
             'description="Data Model" type="5" refreshedVersion="8" minRefreshableVersion="5" '
             'background="1"><dbPr connection="Data Model Connection" command="Model" '
             'commandType="1"/><olapPr sendLocale="1" rowDrillCount="1000"/><extLst>'
             f'<ext uri="{EXTENSIONS["connection"]}" xmlns:x15="{X15}"><x15:connection id="" '
             'model="1"/></ext></extLst></connection>')
    added = "".join(
        f'<connection id="{number}" name="WorksheetConnection_{escape(table)}" type="102" '
        'refreshedVersion="8" minRefreshableVersion="5"><extLst>'
        f'<ext uri="{EXTENSIONS["connection"]}" xmlns:x15="{X15}"><x15:connection '
        f'id="{escape(table)}"><x15:rangePr sourceName="{escape(table)}"/></x15:connection>'
        "</ext></extLst></connection>" for number, table in enumerate(_model_tables(caches), 2))
    return f'{HEAD}<connections xmlns="{SPREADSHEET}">{model}{added}</connections>'


def data_model_xml(caches: list[Cache]) -> str:
    """The workbook's extension naming each Table its Data Model holds."""
    found = "".join(f'<x15:modelTable id="{escape(table)}" name="{escape(table)}" '
                    f'connection="WorksheetConnection_{escape(table)}"/>'
                    for table in _model_tables(caches))
    return (f'<ext uri="{EXTENSIONS["dataModel"]}" xmlns:x15="{X15}"><x15:dataModel>'
            f"<x15:modelTables>{found}</x15:modelTables></x15:dataModel></ext>")


# --- Into the saved workbook ----------------------------------------------------------------


@dataclass
class _Package:
    """A workbook's parts as text while pivots are added to it: each new part's content
    type, each relationship and extension the workbook and each sheet gain, each sheet's
    drawing, and each defined name."""

    text: dict[str, str]
    types: list[tuple[str, str]] = field(default_factory=list)
    workbook_links: list[str] = field(default_factory=list)
    workbook_extensions: list[str] = field(default_factory=list)
    sheet_links: dict[str, list[str]] = field(default_factory=dict)
    sheet_extensions: dict[str, list[str]] = field(default_factory=dict)
    drawings: dict[str, str] = field(default_factory=dict)
    names: list[str] = field(default_factory=list)

    def add(self, path: str, xml: str, kind: str) -> None:
        """Add the part `path`, of the content type `TYPES[kind]`."""
        self.text[path] = xml
        self.types.append(("/" + path, TYPES[kind]))


def _link(rid: str, kind: str, target: str) -> str:
    """A relationship, its type an Office one or one under RELATIONSHIP_TYPES."""
    if kind in OFFICE_RELATIONSHIPS:
        return (f'<Relationship Id="{rid}" Type="{OFFICE_RELATIONSHIPS[kind]}" '
                f'Target="{target}"/>')
    return relationship(rid, kind, target)


def _relationships_of(links: list[str]) -> str:
    """A relationships part holding `links`."""
    return (f'{HEAD}<Relationships xmlns="{PACKAGE_RELATIONSHIPS}">{"".join(links)}'
            "</Relationships>")


def _sheets(text: dict[str, str]) -> dict[str, tuple[str, int]]:
    """Each sheet's part and tab id, by its name."""
    targets = {}
    for found in re.finditer(r"<Relationship ([^>]*)/>", text["xl/_rels/workbook.xml.rels"]):
        attributes = dict(re.findall(r'(\w+)="([^"]*)"', found.group(1)))
        target = attributes["Target"]
        if target.startswith("/"):
            targets[attributes["Id"]] = target[1:]
        else:
            targets[attributes["Id"]] = "xl/" + target
    sheets = {}
    for found in re.finditer(r"<sheet ([^>]*)/>", text["xl/workbook.xml"]):
        attributes = dict(re.findall(r'([\w:]+)="([^"]*)"', found.group(1)))
        name = attributes["name"].replace("&lt;", "<").replace("&gt;", ">")
        sheets[name.replace("&amp;", "&")] = (targets[attributes["r:id"]],
                                              int(attributes["sheetId"]))
    return sheets


def _add_caches(package: _Package, worked: Worked) -> None:
    """Each cache's definition and records, and, for a Data Model pivot, the connections and
    the Data Model's Tables."""
    for cache in worked.caches:
        path = f"xl/pivotCache/pivotCacheDefinition{cache.id}.xml"
        if cache.data_model:
            package.add(path, data_model_cache_xml(cache), "pivotCacheDefinition")
        else:
            package.add(path, cache_definition_xml(cache), "pivotCacheDefinition")
            package.add(f"xl/pivotCache/pivotCacheRecords{cache.id}.xml", records_xml(cache),
                        "pivotCacheRecords")
            package.text[f"xl/pivotCache/_rels/pivotCacheDefinition{cache.id}.xml.rels"] = (
                _relationships_of([_link("rId1", "pivotCacheRecords",
                                         f"pivotCacheRecords{cache.id}.xml")]))
        package.workbook_links.append(_link(f"rIdPivotCache{cache.id}", "pivotCacheDefinition",
                                            f"pivotCache/pivotCacheDefinition{cache.id}.xml"))
    modelled = [cache for cache in worked.caches if cache.data_model]
    if modelled:
        package.add("xl/connections.xml", connections_xml(modelled), "connections")
        package.workbook_links.append(_link("rIdConnections", "connections", "connections.xml"))
        package.workbook_extensions.append(data_model_xml(modelled))


def _add_pivot_tables(package: _Package, worked: Worked, sheets: dict[str, tuple[str, int]]
                      ) -> None:
    """Each pivot's definition, and its sheet's link to it."""
    for number, wp in enumerate(worked.pivots, 1):
        path = f"xl/pivotTables/pivotTable{number}.xml"
        if wp.cache.data_model:
            package.add(path, data_model_pivot_xml(wp), "pivotTable")
        else:
            package.add(path, pivot_table_xml(worked, wp), "pivotTable")
        package.text[f"xl/pivotTables/_rels/pivotTable{number}.xml.rels"] = _relationships_of(
            [_link("rId1", "pivotCacheDefinition",
                   f"../pivotCache/pivotCacheDefinition{wp.cache.id}.xml")])
        package.sheet_links.setdefault(sheets[wp.pivot.sheet][0], []).append(
            _link(f"rIdPivotTable{number}", "pivotTable",
                  f"../pivotTables/pivotTable{number}.xml"))


def _add_slicer_caches(package: _Package, worked: Worked, tabs: dict[str, int]) -> None:
    """Each slicer's and Timeline's cache and defined name, and the workbook's lists of
    them."""
    listed = {"slicerCache": [], "timelineCache": []}
    for number, slicer in enumerate(worked.slicers, 1):
        if isinstance(slicer, Slicer):
            kind, xml, name = ("slicerCache", slicer_cache_xml(worked, slicer, tabs),
                               slicer_name(slicer))
        else:
            kind, xml, name = ("timelineCache", timeline_cache_xml(worked, slicer, tabs),
                               timeline_name(slicer))
        package.names.append(f'<definedName name="{name}">#N/A</definedName>')
        package.add(f"xl/{kind}s/{kind}{number}.xml", xml, kind)
        package.workbook_links.append(_link(f"rId{kind}{number}", kind,
                                            f"{kind}s/{kind}{number}.xml"))
        listed[kind].append(f"rId{kind}{number}")
    if listed["slicerCache"]:
        package.workbook_extensions.append(
            f'<ext uri="{EXTENSIONS["slicerCaches"]}" xmlns:x14="{X14}"><x14:slicerCaches>'
            + "".join(f'<x14:slicerCache r:id="{rid}"/>' for rid in listed["slicerCache"])
            + "</x14:slicerCaches></ext>")
    if listed["timelineCache"]:
        package.workbook_extensions.append(
            f'<ext uri="{EXTENSIONS["timelineCacheRefs"]}" xmlns:x15="{X15}">'
            "<x15:timelineCacheRefs>"
            + "".join(f'<x15:timelineCacheRef r:id="{rid}"/>'
                      for rid in listed["timelineCache"])
            + "</x15:timelineCacheRefs></ext>")


def _add_sheet_slicers(package: _Package, worked: Worked, sheet: tuple[str, str],
                       number: int) -> None:
    """One sheet's slicers part, Timelines part and drawing, and its links to them; `sheet`
    is its name and its part."""
    name, part = sheet
    on_sheet = [slicer for slicer in worked.slicers
                if _first_pivot(worked, slicer).pivot.sheet == name]
    links = package.sheet_links.setdefault(part, [])
    extensions = package.sheet_extensions.setdefault(part, [])
    slicers = [slicer for slicer in on_sheet if isinstance(slicer, Slicer)]
    timelines = [slicer for slicer in on_sheet if isinstance(slicer, Timeline)]
    if slicers:
        package.add(f"xl/slicers/slicer{number}.xml", slicers_xml(slicers), "slicer")
        links.append(_link("rIdSlicers", "slicer", f"../slicers/slicer{number}.xml"))
        extensions.append(f'<ext uri="{EXTENSIONS["slicerList"]}" xmlns:x14="{X14}">'
                          '<x14:slicerList><x14:slicer r:id="rIdSlicers"/></x14:slicerList>'
                          "</ext>")
    if timelines:
        package.add(f"xl/timelines/timeline{number}.xml", timelines_xml(timelines), "timeline")
        links.append(_link("rIdTimelines", "timeline", f"../timelines/timeline{number}.xml"))
        extensions.append(f'<ext uri="{EXTENSIONS["timelineRefs"]}" xmlns:x15="{X15}">'
                          '<x15:timelineRefs><x15:timelineRef r:id="rIdTimelines"/>'
                          "</x15:timelineRefs></ext>")
    package.add(f"xl/drawings/drawingPivot{number}.xml", drawing_xml(worked, name), "drawing")
    links.append(_link("rIdSlicerDrawing", "drawing", f"../drawings/drawingPivot{number}.xml"))
    package.drawings[part] = "rIdSlicerDrawing"


def _with_r(xml: str, root: str) -> str:
    """A part's XML, its root declaring the relationships namespace as `r`."""
    start = xml.index(f"<{root}")
    end = xml.index(">", start)
    if "xmlns:r=" in xml[start:end]:
        return xml
    return xml[:start] + f'<{root} xmlns:r="{RELATIONSHIP_TYPES}"' + xml[start + len(root) + 1:]


def _finish_sheets(package: _Package) -> None:
    """Each sheet's new relationships, then its drawing and extensions where Excel's schema
    puts them: the drawing before its Tables, the extensions last."""
    text = package.text
    for part, links in package.sheet_links.items():
        folder, file = part.rsplit("/", 1)
        rels = f"{folder}/_rels/{file}.rels"
        text[rels] = with_relationships(text.get(rels, _relationships_of([])), links)
    for part in {*package.drawings, *package.sheet_extensions}:
        xml = _with_r(text[part], "worksheet")
        if part in package.drawings:
            drawing = f'<drawing r:id="{package.drawings[part]}"/>'
            before = "<tableParts" if "<tableParts" in xml else "</worksheet>"
            xml = xml.replace(before, drawing + before, 1)
        extensions = "".join(package.sheet_extensions.get(part, []))
        if extensions:
            xml = xml.replace("</worksheet>", f"<extLst>{extensions}</extLst></worksheet>")
        text[part] = xml


def _finish_workbook(package: _Package, worked: Worked) -> None:
    """The workbook's defined names, pivot caches, extensions, relationships and content
    types."""
    text = package.text
    xml = _with_r(text["xl/workbook.xml"], "workbook")
    names = "".join(package.names)
    if names and "</definedNames>" in xml:
        xml = xml.replace("</definedNames>", names + "</definedNames>")
    elif names:
        xml = xml.replace("<calcPr", f"<definedNames>{names}</definedNames><calcPr")
    caches = "".join(f'<pivotCache cacheId="{cache.id}" r:id="rIdPivotCache{cache.id}"/>'
                     for cache in worked.caches)
    added = f"<pivotCaches>{caches}</pivotCaches>"
    if package.workbook_extensions:
        added += f"<extLst>{''.join(package.workbook_extensions)}</extLst>"
    text["xl/workbook.xml"] = xml.replace("</workbook>", added + "</workbook>")
    text["xl/_rels/workbook.xml.rels"] = with_relationships(text["xl/_rels/workbook.xml.rels"],
                                                            package.workbook_links)
    text["[Content_Types].xml"] = text["[Content_Types].xml"].replace(
        "</Types>", "".join(f'<Override PartName="{name}" ContentType="{kind}"/>'
                            for name, kind in package.types) + "</Types>")


def with_pivots(saved: bytes, worked: Worked) -> bytes:
    """The workbook `saved`, with every pivot `worked` holds saved in it as Excel saves one:
    its cache, its definition, and the slicers and Timelines on it. The pivots' cells are on
    their sheets already, written with the workbook."""
    if not worked.pivots:
        return saved
    with zipfile.ZipFile(io.BytesIO(saved)) as workbook:
        parts = {name: workbook.read(name) for name in workbook.namelist()}
    package = _Package({name: data.decode("utf-8") for name, data in parts.items()
                        if name.endswith((".xml", ".rels"))})
    sheets = _sheets(package.text)
    _add_caches(package, worked)
    _add_pivot_tables(package, worked, sheets)
    _add_slicer_caches(package, worked, {name: tab for name, (_, tab) in sheets.items()})
    on_sheets = list(dict.fromkeys(_first_pivot(worked, slicer).pivot.sheet
                                   for slicer in worked.slicers))
    for number, name in enumerate(on_sheets, 1):
        _add_sheet_slicers(package, worked, (name, sheets[name][0]), number)
    _finish_sheets(package)
    _finish_workbook(package, worked)
    written = io.BytesIO()
    with zipfile.ZipFile(written, "w", zipfile.ZIP_DEFLATED) as workbook:
        for name in [*parts, *(name for name in package.text if name not in parts)]:
            if name in package.text:
                workbook.writestr(name, package.text[name].encode("utf-8"))
            else:
                workbook.writestr(name, parts[name])
    return written.getvalue()

"""The workbook reader: an Excel workbook (.xlsx) read as Excel saves it, given back as data
(Toolbox 8.9, ticket 01; ADR 0016).

`read_workbook` gives each sheet's Excel Tables, each column typed or a formula column, with
its Total Row's cell; the sheet's other cells; its PivotTables; the workbook's defined names;
each Power Query's M; each slicer and Timeline; and the Order, each piece after every piece it
reads. The M comes from the queries the workbook holds, its DataMashup part. A workbook that
holds none, such as one whose Excel couldn't add a query, gives them from its Power Query
sheet: a cell "Query <its name>:" with the M in the cell below it. A loop, such as a query
reading a Table whose formulas read that query's own Table, has no Order, and is refused with a
LoopError naming each link of it.

A PivotTable (ticket 03) is read as Excel saves one (ECMA-376 Part 1, 18.10; [MS-XLSX] for
Excel 2010's and 2013's extensions), in any layout, compact, outline or tabular: its name and
sheet; its source, a Table, a range read as the Table it would be, the Data Model or an OLAP
cube; its Row, Column, Value and Report filter fields, each value's summary and Show Values
As; its calculated fields and items with their formulas; each field's date, number or
hand-made grouping, its hidden items and its subtotals; its value, label and date filters; the
totals it shows; each slicer and Timeline connected to it, with what it has selected; and each
value cell, with the row and column items it stands for and the value Excel last stored there.
The cells a pivot fills are its own, not its sheet's other cells. In the Order a pivot reads
its source, and a Table whose formula reads it with GETPIVOTDATA reads the pivot.

It is the one reader of a workbook. `copilot/workbook_text.py`, which writes a workbook as text
for a Copilot chat, loads this file alone, by its folder's path, never through the Toolbox's
`__init__`, which checks sqlglot; so this file imports the standard library alone, and nothing
of its own folder, and the script still needs nothing but Python (`tools/toolbox_registry.py`'s
`WORKBOOK_READER`). It reads only the workbook it is given, and runs nothing the workbook holds.
"""

from __future__ import annotations

import base64
import datetime
import graphlib
import io
import posixpath
import re
import struct
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree

# The kinds of piece the Order puts in order, in Excel's words: a range is one a PivotTable
# reads that isn't in a Table.
EXCEL_TABLE = "Excel Table"
POWER_QUERY = "Power Query"
PIVOT_TABLE = "PivotTable"
RANGE = "Range"
# The kinds of a PivotTable's source beside a Table and a range, in Excel's words.
DATA_MODEL = "Data Model"
OLAP = "OLAP cube"
DATA_CONNECTION = "data connection"
OTHER_WORKBOOK = "another workbook"
CONSOLIDATION = "multiple consolidation ranges"
# The field a pivot's Row or Column fields name for its values, when it has more than one.
VALUES = "Values"
# A value that is a measure of the Data Model written in DAX, not a summary of one column.
DAX_MEASURE = "DAX measure"
# What a pivot's row or column of totals is: a field's subtotal, or the Grand Total.
TOTAL = "Total"
GRAND_TOTAL = "Grand Total"
# The kinds of a pivot's filter, beside its Report filters, hidden items and slicers.
VALUE_FILTER = "Value Filter"
LABEL_FILTER = "Label Filter"
DATE_FILTER = "Date Filter"
# A base item that is the item before or after, not a named one, by its number in the file.
BASE_ITEMS = {1048828: "(previous)", 1048829: "(next)"}
# Each summary, by the word Excel's file holds and the word Excel shows.
SUMMARIES = {"sum": "Sum", "count": "Count", "average": "Average", "max": "Max", "min": "Min",
             "product": "Product", "countNums": "Count Numbers", "stdDev": "StdDev",
             "stdDevp": "StdDevp", "var": "Var", "varp": "Varp"}
# A Data Model value Excel made by summing, counting or the like one column: "Sum of sales".
IMPLICIT_MEASURE = re.compile(
    r"(Sum|Count|Average|Max|Min|Distinct Count|StdDev|StdDevp|Var|Varp) of (.+)")
# Each Show Values As, by the word Excel's file holds and the words Excel shows.
SHOWN_AS = {"normal": "", "difference": "Difference From", "percent": "% Of",
            "percentDiff": "% Difference From", "runTotal": "Running Total In",
            "percentOfRow": "% of Row Total", "percentOfCol": "% of Column Total",
            "percentOfTotal": "% of Grand Total", "index": "Index",
            "percentOfParent": "% of Parent Total",
            "percentOfParentRow": "% of Parent Row Total",
            "percentOfParentCol": "% of Parent Column Total",
            "percentOfRunningTotal": "% Running Total In",
            "rankAscending": "Rank Smallest to Largest",
            "rankDescending": "Rank Largest to Smallest"}
# The Show Values As that read a base field, and those that read a base item of it too.
WITH_BASE_FIELD = {"difference", "percent", "percentDiff", "runTotal", "percentOfParent",
                   "percentOfRunningTotal", "rankAscending", "rankDescending"}
WITH_BASE_ITEM = {"difference", "percent", "percentDiff"}
# A field's subtotals, by the attribute Excel's file holds and the word Excel shows.
SUBTOTALS = {"sumSubtotal": "Sum", "countASubtotal": "Count", "avgSubtotal": "Average",
             "maxSubtotal": "Max", "minSubtotal": "Min", "productSubtotal": "Product",
             "countSubtotal": "Count Numbers", "stdDevSubtotal": "StdDev",
             "stdDevPSubtotal": "StdDevp", "varSubtotal": "Var", "varPSubtotal": "Varp"}
# A field's subtotals when it shows Excel's own: the Automatic ones.
AUTOMATIC = "Automatic"
# A row or column of a custom subtotal, by the type Excel's file gives it.
SUBTOTAL_LINES = {"sum": "Sum", "countA": "Count", "avg": "Average", "max": "Max",
                  "min": "Min", "product": "Product", "count": "Count Numbers",
                  "stdDev": "StdDev", "stdDevP": "StdDevp", "var": "Var", "varP": "Varp"}
# A label or value filter's test, by the end of the type Excel's file holds.
FILTER_TESTS = {"Equal": "equals", "NotEqual": "does not equal",
                "BeginsWith": "begins with", "NotBeginsWith": "does not begin with",
                "EndsWith": "ends with", "NotEndsWith": "does not end with",
                "Contains": "contains", "NotContains": "does not contain",
                "GreaterThan": "is greater than",
                "GreaterThanOrEqual": "is greater than or equal to",
                "LessThan": "is less than", "LessThanOrEqual": "is less than or equal to",
                "Between": "is between", "NotBetween": "is not between"}
# A date filter's test, by the type Excel's file holds; Q1 to Q4 and M1 to M12 are the
# quarters' and months' own.
DATE_TESTS = {"dateEqual": "Equals", "dateNotEqual": "Does Not Equal",
              "dateOlderThan": "Before", "dateOlderThanOrEqual": "Before or Equal To",
              "dateNewerThan": "After", "dateNewerThanOrEqual": "After or Equal To",
              "dateBetween": "Between", "dateNotBetween": "Not Between",
              "tomorrow": "Tomorrow", "today": "Today", "yesterday": "Yesterday",
              "nextWeek": "Next Week", "thisWeek": "This Week", "lastWeek": "Last Week",
              "nextMonth": "Next Month", "thisMonth": "This Month", "lastMonth": "Last Month",
              "nextQuarter": "Next Quarter", "thisQuarter": "This Quarter",
              "lastQuarter": "Last Quarter", "nextYear": "Next Year", "thisYear": "This Year",
              "lastYear": "Last Year", "yearToDate": "Year to Date"}
MONTH_NAMES = ("January", "February", "March", "April", "May", "June", "July", "August",
               "September", "October", "November", "December")
# A Top 10 filter's unit, by the type Excel's file holds.
TOP_UNITS = {"count": "Items", "percent": "Percent", "sum": "Sum"}
# A GETPIVOTDATA's pivot, by its second argument: a cell, on a sheet or the formula's own.
GETPIVOTDATA = re.compile(
    r"GETPIVOTDATA\(\s*(?:\"(?:[^\"]|\"\")*\"|[^,()]+)\s*,\s*"
    r"(?:('(?:[^']|'')+'|[^'!,()\s]+)!)?\$?([A-Z]{1,3})\$?(\d+)")
# A name a formula uses alone, with no [ after it, such as jobs in VLOOKUP(x,jobs,2,0): not
# a function's, a sheet's or a cell's, once its strings and brackets are taken out.
BARE_NAME = re.compile(r"(?<![\w.!$])([A-Za-z_\\][\w.]*)(?![\w.(!\[])")
# An OLAP member's caption, the end of its unique name: [job_runs].[status].&[SUCCESS].
MEMBER = re.compile(r"&\[((?:[^\]]|\]\])*)\]$")
# The two kinds of a Table's column: values typed in, or a formula in at least one row.
TYPED = "typed"
FORMULA = "formula"
# Excel's own number formats that show a date, by their ids.
DATE_FORMATS = {*range(14, 23), *range(45, 48)}
# A query's label on a Power Query sheet, with its M in the cell below.
QUERY_LABEL = re.compile(r"Query (.+):")
# A query reading the workbook's Table or name `x`: Excel.CurrentWorkbook(){[Name="x"]}.
READS_THE_WORKBOOK = re.compile(
    r'Excel\.CurrentWorkbook\(\)\s*\{\s*\[\s*Name\s*=\s*"((?:[^"]|"")+)"\s*\]\s*\}')
# A structured reference to Table `x`, such as x[dt] or x[[#This Row],[dt]].
TABLE_REFERENCE = re.compile(r"(?<![\w.\]!])([A-Za-z_\\][\w.]*)\[")
# The start of each query a section document's M shares: `shared name =`.
SHARED = re.compile(r'shared\s+(#"(?:[^"]|"")*"|[A-Za-z_][\w.]*)\s*=')


@dataclass
class Column:
    """One column of an Excel Table: its header, its kind, TYPED or FORMULA, each row's cell
    below the header, and its Total Row's cell.

    A cell holds a formula as "=" and the formula as the workbook saves it, such as
    `=SUMIFS(t[a],t[b],t[[#This Row],[b]])`, else its value; an empty cell is None, and so is
    `total` in a Table with no Total Row. A formula column holds a formula in at least one row,
    with any value typed over one in another; a typed column holds values alone."""

    header: str
    kind: str
    cells: list[str | int | float | bool | datetime.datetime | None]
    total: str | int | float | bool | datetime.datetime | None = None


@dataclass
class Table:
    """One Excel Table: its name, its range, its columns, whether its last row is a Total
    Row, and the query that loads it, if any."""

    name: str
    ref: str
    columns: list[Column]
    has_total_row: bool = False
    loaded_by: str = ""


@dataclass
class PivotSource:
    """What a PivotTable reads: its `kind`, EXCEL_TABLE, RANGE, DATA_MODEL, OLAP,
    DATA_CONNECTION, OTHER_WORKBOOK or CONSOLIDATION; its `name`, the Table's, the range's
    (its defined name, else its sheet and place, such as Runs!A1:F10) or the connection's; for
    a Table or a range, the `table` it is or would be; for the Data Model, the `model_tables`
    the pivot reads; and the `pieces` of the workbook it reads: the Table, the range, or each
    Table or query that loads a Data Model table it reads."""

    kind: str
    name: str
    table: Table | None = None
    model_tables: list[str] = field(default_factory=list)
    pieces: list[Piece] = field(default_factory=list)


@dataclass
class Grouping:
    """How a pivot's field groups the field `field`: `by` Excel's word, "Seconds", "Minutes",
    "Hours", "Days", "Months", "Quarters" or "Years" for dates, "Number" for bins `interval`
    wide (Days are `interval` days too), or "Items" for groups made by hand, each group's name
    and the items it holds in `groups`; from `start` to `end`, as Excel's Grouping dialog says
    them, Starting at and Ending at."""

    by: str
    field: str
    start: int | float | datetime.datetime | None = None
    end: int | float | datetime.datetime | None = None
    interval: int | float | None = None
    groups: dict[str, list[object]] = field(default_factory=dict)


@dataclass
class PivotField:
    """One field of a pivot: its name; its `items`, in the order the pivot shows them, a blank
    as None, a grouped field's by their labels, such as "Sep" or "10-19"; the items `hidden` on
    it, unticked, but for a Report filter's or a slicer's own; a calculated field's `formula`,
    as the workbook saves it, such as "duration_mins/60"; each calculated item's formula, by
    the item, such as {"done": "SUCCESS+FAILED"}; its `grouping`; its `subtotals`, [AUTOMATIC],
    the functions chosen, such as ["Sum", "Count"], or none; and whether it shows items with
    no data."""

    name: str
    items: list[object] = field(default_factory=list)
    hidden: list[object] = field(default_factory=list)
    formula: str = ""
    calculated_items: dict[str, str] = field(default_factory=dict)
    grouping: Grouping | None = None
    subtotals: list[str] = field(default_factory=list)
    shows_items_with_no_data: bool = False


@dataclass
class PivotValue:
    """One value of a pivot, in the Values area: its `caption`, such as "Sum of
    duration_mins"; the `field` it summarizes; its `summary`, Excel's word, such as "Sum" or
    "Distinct Count", or DAX_MEASURE; its Show Values As, Excel's words, such as "% of Column
    Total", or "" for none; and the base field and base item that reads, if any."""

    caption: str
    field: str
    summary: str
    shown_as: str = ""
    base_field: str = ""
    base_item: object = None


@dataclass
class ReportFilter:
    """One Report filter of a pivot, in its Filters area: its field and the items it shows,
    one, several, or none for (All)."""

    field: str
    selected: list[object] = field(default_factory=list)


@dataclass
class PivotFilter:
    """A value, label or date filter on a pivot's Row or Column field: its `kind`,
    VALUE_FILTER, LABEL_FILTER or DATE_FILTER; its `test`, Excel's words, such as "Top",
    "Bottom", "begins with" or "Between"; its `values`; for a value filter, the value it reads,
    `by`; and a Top 10's `unit`, "Items", "Percent" or "Sum"."""

    field: str
    kind: str
    test: str
    values: list[object] = field(default_factory=list)
    by: str = ""
    unit: str = ""


@dataclass
class Slicer:
    """A slicer: its `name`, the one its defined name has, such as Slicer_status; its
    `field`; its `caption` and `sheet`; each pivot it is connected to; and the items it has
    selected, none when nothing is saved."""

    name: str
    field: str
    caption: str = ""
    sheet: str = ""
    pivots: list[str] = field(default_factory=list)
    selected: list[object] = field(default_factory=list)


@dataclass
class Timeline:
    """A Timeline: its `name`, such as NativeTimeline_dt; its date `field`; its `caption` and
    `sheet`; each pivot it is connected to; and the first and last day it has selected, None
    when it shows every date."""

    name: str
    field: str
    caption: str = ""
    sheet: str = ""
    pivots: list[str] = field(default_factory=list)
    start: datetime.datetime | None = None
    end: datetime.datetime | None = None


@dataclass
class PivotLine:
    """The row or column a pivot's cell is on: each field and item it stands for, outermost
    first, and its `total`: "" for an item's, TOTAL or a custom subtotal's function, such as
    "Sum", for a field's subtotal, or GRAND_TOTAL. A row of an outer item alone, as compact
    form shows its subtotal on it, names that item alone."""

    items: list[tuple[str, object]] = field(default_factory=list)
    total: str = ""


@dataclass
class PivotCell:
    """One value cell of a pivot: where it is, by row and column; the caption of the value it
    shows; its `row` and `column`; and the value Excel last stored there, None if blank."""

    at: tuple[int, int]
    value: str
    row: PivotLine
    column: PivotLine
    stored: str | int | float | bool | datetime.datetime | None


@dataclass
class PivotTable:
    """One PivotTable: its name, sheet and place (`ref`, its body without its Report
    filters); its source; its Row and Column fields, outermost first, VALUES among them when
    its values stand side by side; its values; its Report filters; each field of its cache, by
    name; its value, label and date filters; each slicer and Timeline connected to it; which
    Grand Totals it shows, the row at its bottom and the column at its right, and the fields
    whose subtotals it shows; its layout, Excel's "Compact Form", "Outline Form" or "Tabular
    Form"; and each value cell."""

    name: str
    sheet: str
    ref: str
    source: PivotSource
    rows: list[str] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    values: list[PivotValue] = field(default_factory=list)
    report_filters: list[ReportFilter] = field(default_factory=list)
    fields: dict[str, PivotField] = field(default_factory=dict)
    filters: list[PivotFilter] = field(default_factory=list)
    slicers: list[Slicer | Timeline] = field(default_factory=list)
    grand_total_row: bool = False
    grand_total_column: bool = False
    subtotals: list[str] = field(default_factory=list)
    layout: str = "Compact Form"
    cells: list[PivotCell] = field(default_factory=list)


@dataclass
class Sheet:
    """One sheet: its Tables, its other cells by their row and column, such as (1, 4) for D1,
    the kind of each chart, such as "bar", and its PivotTables."""

    title: str
    tables: list[Table] = field(default_factory=list)
    cells: dict[tuple[int, int], str | int | float | bool | datetime.datetime] = field(
        default_factory=dict)
    charts: list[str] = field(default_factory=list)
    pivot_tables: list[PivotTable] = field(default_factory=list)


@dataclass
class Query:
    """One Power Query: its name, its M, and the Table it loads, if any."""

    name: str
    m: str
    loads: str = ""


@dataclass(frozen=True)
class Piece:
    """One piece of the Order: its kind, EXCEL_TABLE or POWER_QUERY, and its name."""

    kind: str
    name: str


@dataclass
class Workbook:
    """What a workbook holds: its sheets, its defined names with what each stands for (but a
    slicer's or a Timeline's own), its Power Queries, the Order, each piece after every piece
    it reads, as the workbook lists them where that leaves a choice, with the pieces each
    reads, and its slicers and Timelines."""

    sheets: list[Sheet]
    defined_names: dict[str, str]
    queries: list[Query]
    order: dict[Piece, list[Piece]]
    slicers: list[Slicer | Timeline] = field(default_factory=list)

    @property
    def pivot_tables(self) -> list[PivotTable]:
        """Each PivotTable of the workbook, sheet by sheet."""
        found = []
        for sheet in self.sheets:
            found += sheet.pivot_tables
        return found


class LoopError(ValueError):
    """The workbook's pieces read each other in a loop, so no order puts each after what it
    reads."""


def read_workbook(source: Path | bytes) -> Workbook:
    """What a workbook holds, read from its file or its bytes. A query from a Power Query
    sheet loads the Table of its name, if there is one. A loop is refused with a LoopError."""
    data = source if isinstance(source, bytes) else Path(source).read_bytes()
    with zipfile.ZipFile(io.BytesIO(data)) as parts:
        connections = _connections(parts)
        book = _xml(parts, "xl/workbook.xml")
        linked = _relationships(parts, "xl/workbook.xml")
        sheets, tabs = _worksheets(parts, book, linked, connections)
        names = {name.get("name", ""): name.text or "" for name in _all(book, "definedName")
                 if name.get("localSheetId") is None}
        in_the_mashup = _mashup_queries(parts)
        held_sheets = [sheet for sheet, _ in sheets]
        pivot_book = _PivotBook(parts, {sheet.title: sheet for sheet in held_sheets},
                                {table.name: table for table in _every_table(held_sheets)},
                                names, connections, _model_pieces(book, connections))
        slicers = _add_pivot_tables(pivot_book, sheets, linked, tabs)
    sheets = held_sheets
    queries = [Query(name, m) for name, m in in_the_mashup or _take_sheet_queries(sheets)]
    tables = {table.name: table for table in _every_table(sheets)}
    for query in queries:
        if not in_the_mashup and query.name in tables:
            tables[query.name].loaded_by = query.name
        for table in tables.values():
            if table.loaded_by == query.name:
                query.loads = table.name
    for slicer in slicers:
        names.pop(slicer.name, None)
    return Workbook(sheets, names, queries, _in_order(_pieces_read(sheets, queries)), slicers)


def coordinate(row: int, column: int) -> str:
    """Where a cell is, from its row and column, such as C2 for (2, 3)."""
    letters = ""
    while column:
        column, left = divmod(column - 1, 26)
        letters = chr(65 + left) + letters
    return f"{letters}{row}"


def piece_name(piece: Piece) -> str:
    """A piece as Excel names it, such as `Excel Table "job_runs"`."""
    return f'{piece.kind} "{piece.name}"'


def shifted_formula(formula: str, rows: int, columns: int) -> str:
    """A shared formula as the cell `rows` down and `columns` across from its first holds it:
    each reference not held with `$` moved as far."""
    def move(found: re.Match[str]) -> str:
        fixed_column, letters, fixed_row, digits = found.groups()
        row, column = _where(letters + digits)
        moved = coordinate(row if fixed_row else row + rows,
                           column if fixed_column else column + columns)
        moved_letters, moved_digits = re.fullmatch(r"([A-Z]+)(\d+)", moved).groups()
        return f"{fixed_column}{moved_letters}{fixed_row}{moved_digits}"
    return re.sub(r'(?<![\w"\[])(\$?)([A-Z]{1,3})(\$?)(\d+)(?![\w(])', move, formula)


def section_queries(m: str) -> list[tuple[str, str]]:
    """Each query a section document's M shares, as its name and its expression, in order:
    `shared name = let ... in ...;`, each read to its `;` past strings and comments."""
    found = []
    start = SHARED.search(m)
    while start is not None:
        name = start.group(1)
        if name.startswith("#"):
            name = name[2:-1].replace('""', '"')
        end = _statement_end(m, start.end())
        found.append((name, m[start.end():end].strip()))
        start = SHARED.search(m, end + 1)
    return found


# --- Reading the workbook's parts -----------------------------------------------------------
# Each part's XML is read by its elements' own names, whatever namespace they are in.


def _xml(parts: zipfile.ZipFile, name: str) -> ElementTree.Element:
    return ElementTree.fromstring(parts.read(name))


def _all(element: ElementTree.Element, name: str) -> Iterator[ElementTree.Element]:
    """Each element named `name` under `element`, at any depth."""
    return element.iterfind(f".//{{*}}{name}")


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _relationship_id(element: ElementTree.Element) -> str:
    """The relationship an element names, its `r:id`."""
    for key, value in element.attrib.items():
        if key.endswith("}id"):
            return value
    return ""


def _relationships(parts: zipfile.ZipFile, part: str) -> dict[str, tuple[str, str]]:
    """Each relationship of `part`, by its id: its type's last word and the part it names."""
    folder, file = posixpath.split(part)
    rels = posixpath.join(folder, "_rels", file + ".rels")
    if rels not in parts.namelist():
        return {}
    found = {}
    for rel in _all(_xml(parts, rels), "Relationship"):
        target = rel.get("Target", "")
        if rel.get("TargetMode") == "External":
            continue
        path = target[1:] if target.startswith("/") else posixpath.normpath(
            posixpath.join(folder, target))
        found[rel.get("Id", "")] = (rel.get("Type", "").rsplit("/", 1)[-1], path)
    return found


def _texts(element: ElementTree.Element) -> str:
    """The text of a string item, its runs joined, leaving out how to say it (phonetic runs)."""
    phonetic: set[int] = set()
    for run in _all(element, "rPh"):
        phonetic |= {id(text) for text in _all(run, "t")}
    own = [element] if _local(element.tag) == "t" else []
    return "".join(t.text or "" for t in [*own, *_all(element, "t")] if id(t) not in phonetic)


def _shared_strings(parts: zipfile.ZipFile) -> list[str]:
    name = "xl/sharedStrings.xml"
    if name not in parts.namelist():
        return []
    return [_texts(item) for item in _all(_xml(parts, name), "si")]


def _date_styles(parts: zipfile.ZipFile) -> set[int]:
    """The index of each cell style that shows its number as a date."""
    name = "xl/styles.xml"
    if name not in parts.namelist():
        return set()
    styles = _xml(parts, name)
    dated = set(DATE_FORMATS)
    for number_format in _all(styles, "numFmt"):
        code = re.sub(r'"[^"]*"|\[[^\]]*\]|\\.', "", number_format.get("formatCode", ""))
        if re.search(r"[dy]", code, re.IGNORECASE):
            dated.add(int(number_format.get("numFmtId", "0")))
    cell_styles = styles.find("{*}cellXfs")
    if cell_styles is None:
        return set()
    return {index for index, style in enumerate(cell_styles.iterfind("{*}xf"))
            if int(style.get("numFmtId", "0")) in dated}


def _where(at: str) -> tuple[int, int]:
    """A cell's row and column, from where it is, such as (2, 3) for C2."""
    letters, digits = re.fullmatch(r"([A-Z]+)(\d+)", at).groups()
    column = 0
    for letter in letters:
        column = column * 26 + ord(letter) - 64
    return int(digits), column


def _number(text: str) -> int | float:
    return float(text) if re.search(r"[.eE]", text) else int(text)


def _value(cell: ElementTree.Element, strings: list[str], dated: set[int]
           ) -> str | int | float | bool | datetime.datetime | None:
    """A cell's value, as its type says: None for a cell that holds nothing."""
    kind = cell.get("t", "n")
    if kind == "inlineStr":
        inline = cell.find("{*}is")
        return _texts(inline) if inline is not None else ""
    value = cell.find("{*}v")
    if value is None or value.text is None:
        return None
    return _typed(kind, value.text, strings, int(cell.get("s", "0")) in dated)


def _typed(kind: str, text: str, strings: list[str], dated: bool
           ) -> str | int | float | bool | datetime.datetime:
    """A cell's saved text as the value its type, `t`, says: a shared string, a TRUE or FALSE,
    a formula's text or an error, a date, or a number."""
    if kind == "s":
        return strings[int(text)]
    if kind == "b":
        return text == "1"
    if kind in ("str", "e"):
        return text
    if dated:
        return datetime.datetime(1899, 12, 30) + datetime.timedelta(days=float(text))
    return _number(text)


def _cells(parts: zipfile.ZipFile, part: str, strings: list[str], dated: set[int]
           ) -> dict[tuple[int, int], str | int | float | bool | datetime.datetime]:
    """Each cell of a sheet that holds something, by where it is: a formula as "=" and its
    text, else its value. A shared formula's later cells are worked out from its first."""
    cells: dict[tuple[int, int], str | int | float | bool | datetime.datetime] = {}
    shared: dict[str, tuple[str, tuple[int, int]]] = {}
    for cell in _all(_xml(parts, part), "c"):
        where = _where(cell.get("r", "A1"))
        formula = cell.find("{*}f")
        text = ""
        if formula is not None and formula.text:
            text = formula.text
        if formula is not None and formula.get("t") == "shared":
            index = formula.get("si", "")
            if text:
                shared[index] = (text, where)
            elif index in shared:
                first, (row, column) = shared[index]
                text = shifted_formula(first, where[0] - row, where[1] - column)
        value = "=" + text if text else _value(cell, strings, dated)
        if value is not None:
            cells[where] = value
    return cells


def _range(ref: str) -> tuple[tuple[int, int], tuple[int, int]]:
    first, _, last = ref.replace("$", "").partition(":")
    return _where(first), _where(last or first)


def _is_formula(value: str | int | float | bool | datetime.datetime | None) -> bool:
    return isinstance(value, str) and value.startswith("=")


def _column(cells: dict[tuple[int, int], str | int | float | bool | datetime.datetime],
            column: int, rows: range, total_row: int | None) -> Column:
    """One column of a Table: its header, from the cell above `rows`, its cells in `rows`, and
    its cell on `total_row`, if the Table has a Total Row."""
    header = cells.get((rows.start - 1, column))
    below = [cells.get((row, column)) for row in rows]
    kind = TYPED
    if any(_is_formula(value) for value in below):
        kind = FORMULA
    total = None
    if total_row is not None:
        total = cells.get((total_row, column))
    return Column("" if header is None else str(header), kind, below, total)


def _table(parts: zipfile.ZipFile, part: str,
           cells: dict[tuple[int, int], str | int | float | bool | datetime.datetime],
           loads: dict[str, str]) -> Table:
    """The Table `part` holds, its columns read from its sheet's `cells`, and the query that
    loads it, through its query table's connection."""
    held = _xml(parts, part)
    name = held.get("displayName") or held.get("name", "")
    ref = held.get("ref", "")
    (top, left), (bottom, right) = _range(ref)
    has_total_row = int(held.get("totalsRowCount", "0")) > 0
    total_row = None
    rows = range(top + 1, bottom + 1)
    if has_total_row:
        total_row, rows = bottom, range(top + 1, bottom)
    columns = [_column(cells, column, rows, total_row) for column in range(left, right + 1)]
    loaded_by = ""
    for kind, query_table in _relationships(parts, part).values():
        if kind == "queryTable":
            loaded_by = loads.get(_xml(parts, query_table).get("connectionId", ""), "")
    return Table(name, ref, columns, has_total_row, loaded_by)


def _charts(parts: zipfile.ZipFile, drawing: str) -> list[str]:
    """The kind of each chart a drawing holds, such as "bar", in the drawing's order."""
    linked = _relationships(parts, drawing)
    kinds = []
    for chart in _all(_xml(parts, drawing), "chart"):
        kind, path = linked.get(_relationship_id(chart), ("", ""))
        if kind != "chart":
            continue
        plot = _xml(parts, path).find("{*}chart/{*}plotArea")
        drawn = []
        if plot is not None:
            drawn = [_local(child.tag) for child in plot if _local(child.tag).endswith("Chart")]
        kinds.append(drawn[0].removesuffix("Chart").replace("3D", " 3D") if drawn else "")
    return kinds


def _worksheets(parts: zipfile.ZipFile, book: ElementTree.Element,
                linked: dict[str, tuple[str, str]], connections: dict[str, _Connection]
                ) -> tuple[list[tuple[Sheet, str]], dict[str, str]]:
    """Each worksheet, in the workbook's order, with its part, and each one's title by its
    sheet id, which a slicer names its pivot's sheet by."""
    strings = _shared_strings(parts)
    dated = _date_styles(parts)
    loads = {number: connection.query for number, connection in connections.items()}
    sheets = []
    tabs = {}
    for held in _all(book, "sheet"):
        kind, part = linked.get(_relationship_id(held), ("", ""))
        if kind == "worksheet":
            sheets.append((_sheet(parts, held.get("name", ""), part, strings, dated, loads),
                           part))
            tabs[held.get("sheetId", "")] = held.get("name", "")
    return sheets, tabs


def _sheet(parts: zipfile.ZipFile, title: str, part: str, strings: list[str],
           dated: set[int], loads: dict[str, str]) -> Sheet:
    """One sheet: its Tables in the order it lists them, then its other cells and charts; its
    PivotTables are read after every sheet."""
    cells = _cells(parts, part, strings, dated)
    sheet = Sheet(title)
    linked = _relationships(parts, part)
    for table_part in _all(_xml(parts, part), "tablePart"):
        kind, path = linked.get(_relationship_id(table_part), ("", ""))
        if kind == "table":
            sheet.tables.append(_table(parts, path, cells, loads))
    in_a_table = set()
    for table in sheet.tables:
        (top, left), (bottom, right) = _range(table.ref)
        for row in range(top, bottom + 1):
            in_a_table |= {(row, column) for column in range(left, right + 1)}
    sheet.cells = {where: value for where, value in sorted(cells.items())
                   if where not in in_a_table}
    for kind, path in linked.values():
        if kind == "drawing":
            sheet.charts += _charts(parts, path)
    return sheet


def _every_table(sheets: list[Sheet]) -> list[Table]:
    """Each Table of the workbook, sheet by sheet."""
    tables = []
    for sheet in sheets:
        tables += sheet.tables
    return tables


# --- PivotTables ----------------------------------------------------------------------------
# A pivot's cache, its pivot cache definition, holds each field and its items; the pivot's own
# part holds where each field is, and its rows and columns as places among those items; its
# sheet holds the values Excel last stored in its cells.


@dataclass
class _PivotBook:
    """What reading a workbook's pivots needs of it: its parts, its sheets and Tables by name,
    its defined names, its connections by id, and the piece that loads each Data Model table,
    by the table's name."""

    parts: zipfile.ZipFile
    sheets: dict[str, Sheet]
    tables: dict[str, Table]
    names: dict[str, str]
    connections: dict[str, _Connection]
    model: dict[str, Piece]


@dataclass
class _PivotCache:
    """A pivot cache as its pivots read it: its definition, each field's name (an OLAP
    field's caption), each field's items as its pivots number them (a grouped field's labels),
    each calculated field's formula, each field's grouping, each field's calculated items, and
    each Data Model measure's summary and field, by the measure's place."""

    held: ElementTree.Element
    names: list[str]
    items: list[list[object]]
    formulas: list[str]
    groupings: list[Grouping | None]
    calculated_items: dict[str, dict[str, str]]
    measures: dict[int, tuple[str, str]]


def _model_pieces(book: ElementTree.Element, connections: dict[str, _Connection]
                  ) -> dict[str, Piece]:
    """The piece that loads each of the Data Model's tables, by the table's name: the Table
    its connection adds, or the query it loads."""
    by_name = {connection.name: connection for connection in connections.values()}
    found = {}
    for model_table in _all(book, "modelTable"):
        connection = by_name.get(model_table.get("connection", ""))
        if connection is not None and connection.table:
            found[model_table.get("name", "")] = Piece(EXCEL_TABLE, connection.table)
        elif connection is not None and connection.query:
            found[model_table.get("name", "")] = Piece(POWER_QUERY, connection.query)
    return found


def _add_pivot_tables(book: _PivotBook, sheets: list[tuple[Sheet, str]],
                      linked: dict[str, tuple[str, str]], tabs: dict[str, str]
                      ) -> list[Slicer | Timeline]:
    """Add each sheet's PivotTables to it, taking the cells each fills off its other cells,
    and give back the workbook's slicers and Timelines, each added to the pivots it is
    connected to."""
    slicer_caches = [(kind, _xml(book.parts, path)) for kind, path in linked.values()
                     if kind in ("slicerCache", "timelineCache")]
    timelines = {held.get("name", "") for kind, held in slicer_caches
                 if kind == "timelineCache"}
    caches: dict[str, _PivotCache] = {}
    pivots: dict[str, PivotTable] = {}
    for sheet, part in sheets:
        for kind, path in _relationships(book.parts, part).values():
            if kind != "pivotTable":
                continue
            cache = _pivot_cache(book, path)
            pivot = _pivot_table(book, sheet, path, cache, timelines)
            caches[f"{sheet.title}!{pivot.name}"] = cache
            pivots[f"{sheet.title}!{pivot.name}"] = pivot
            sheet.pivot_tables.append(pivot)
            top, left, bottom, right = _pivot_bounds(pivot)
            for row in range(top, bottom + 1):
                for column in range(left, right + 1):
                    sheet.cells.pop((row, column), None)
    shown = _slicers_shown(book.parts, sheets)
    slicers = []
    for kind, held in slicer_caches:
        connected = [f"{tabs.get(each.get('tabId', ''), '')}!{each.get('name', '')}"
                     for each in held.iterfind("{*}pivotTables/{*}pivotTable")]
        if kind == "slicerCache":
            slicer = _slicer(held, [caches[name] for name in connected if name in caches])
        else:
            slicer = _timeline(held)
        slicer.caption, slicer.sheet = shown.get(slicer.name, ("", ""))
        for name in connected:
            if name in pivots:
                _connect(slicer, pivots[name])
        slicers.append(slicer)
    return slicers


def _pivot_bounds(pivot: PivotTable) -> tuple[int, int, int, int]:
    """The first and last row and column of the cells a pivot fills: its body, and its Report
    filters above it, each a row of two cells, with a blank row under them."""
    (top, left), (bottom, right) = _range(pivot.ref or "A1")
    if pivot.report_filters:
        top -= len(pivot.report_filters) + 1
        right = max(right, left + 1)
    return top, left, bottom, right


def _connect(slicer: Slicer | Timeline, pivot: PivotTable) -> None:
    """Connect a slicer or Timeline to a pivot: the items a slicer leaves out are its own,
    not hidden on the pivot's field."""
    slicer.pivots.append(pivot.name)
    pivot.slicers.append(slicer)
    if isinstance(slicer, Slicer) and slicer.field in pivot.fields:
        pivot.fields[slicer.field].hidden = []


def _item_value(item: ElementTree.Element) -> object:
    """A shared item or a group's label as its value: text, a number, a date, a TRUE or
    FALSE, an error's text, or None for a blank; an OLAP member by its caption."""
    kind = _local(item.tag)
    text = item.get("c") or item.get("v", "")
    if kind == "m":
        return None
    if kind == "n" and item.get("c") is None:
        return _number(text)
    if kind == "d":
        return datetime.datetime.fromisoformat(text)
    if kind == "b":
        return text in ("1", "true")
    return text


def _pivot_cache(book: _PivotBook, pivot_part: str) -> _PivotCache:
    """The cache a pivot's part names."""
    path = ""
    for kind, linked_path in _relationships(book.parts, pivot_part).values():
        if kind == "pivotCacheDefinition":
            path = linked_path
    held = _xml(book.parts, path)
    held_fields = list(held.iterfind("{*}cacheFields/{*}cacheField"))
    names = [held_field.get("caption") or held_field.get("name", "")
             for held_field in held_fields]
    items = []
    for held_field in held_fields:
        listed = held_field.find("{*}fieldGroup/{*}groupItems")
        if listed is None:
            listed = held_field.find("{*}sharedItems")
        items.append([] if listed is None else [_item_value(item) for item in listed])
    groupings = [_grouping(names, items, place, held_field)
                 for place, held_field in enumerate(held_fields)]
    return _PivotCache(held, names, items,
                       [held_field.get("formula", "") for held_field in held_fields],
                       groupings, _calculated_items(held, names, items),
                       _olap_measures(held, held_fields))


def _date_or_none(text: str | None) -> datetime.datetime | None:
    return None if text is None else datetime.datetime.fromisoformat(text)


def _number_or_none(text: str | None) -> int | float | None:
    return None if text is None else _number(text)


def _grouping(names: list[str], items: list[list[object]], place: int,
              held_field: ElementTree.Element) -> Grouping | None:
    """How a cache field groups its base field, if it does: by a range of dates or numbers,
    or into groups made by hand."""
    group = held_field.find("{*}fieldGroup")
    if group is None:
        return None
    base = int(group.get("base", str(place)))
    grouped = names[base] if base < len(names) else ""
    ranged = group.find("{*}rangePr")
    if ranged is not None and ranged.get("groupBy", "range") == "range":
        return Grouping("Number", grouped, _number_or_none(ranged.get("startNum")),
                        _number_or_none(ranged.get("endNum")),
                        _number(ranged.get("groupInterval", "1")))
    if ranged is not None:
        level = ranged.get("groupBy", "")
        interval = None
        if level == "days":
            interval = _number(ranged.get("groupInterval", "1"))
        return Grouping(level.capitalize(), grouped, _date_or_none(ranged.get("startDate")),
                        _date_or_none(ranged.get("endDate")), interval)
    discrete = group.find("{*}discretePr")
    if discrete is None:
        return None
    grouping = Grouping("Items", grouped)
    labels = items[place]
    for number, held in enumerate(discrete.iterfind("{*}x")):
        label = _value_at(labels, int(held.get("v", "0")))
        grouping.groups.setdefault(str(label), []).append(_value_at(items[base], number))
    return grouping


def _value_at(values: list[object], place: int) -> object:
    """The value at `place`, or None when the workbook names a place that isn't there."""
    if 0 <= place < len(values):
        return values[place]
    return None


def _field_name(names: list[str], place: int) -> str:
    """The name of a cache's field at `place`, or "" when the workbook names a place that
    isn't there."""
    if 0 <= place < len(names):
        return names[place]
    return ""


def _calculated_items(held: ElementTree.Element, names: list[str], items: list[list[object]]
                      ) -> dict[str, dict[str, str]]:
    """Each calculated item's formula, by its field's name and its own."""
    found: dict[str, dict[str, str]] = {}
    for calculated in held.iterfind("{*}calculatedItems/{*}calculatedItem"):
        reference = calculated.find("{*}pivotArea/{*}references/{*}reference")
        if reference is None or int(reference.get("field", "0")) >= len(names):
            continue
        place = int(reference.get("field", "0"))
        held_item = reference.find("{*}x")
        number = 0 if held_item is None else int(held_item.get("v", "0"))
        item = _value_at(items[place], number)
        found.setdefault(names[place], {})[str(item)] = calculated.get("formula", "")
    return found


def _olap_measures(held: ElementTree.Element, held_fields: list[ElementTree.Element]
                   ) -> dict[int, tuple[str, str]]:
    """Each Data Model or OLAP measure's summary and field, by its place among the cache's
    fields: one Excel made, such as "Distinct Count of job_id", by its words; any other a
    DAX_MEASURE, by its name."""
    hierarchies = list(held.iterfind("{*}cacheHierarchies/{*}cacheHierarchy"))
    found = {}
    for place, held_field in enumerate(held_fields):
        if not held_field.get("name", "").startswith("[Measures]."):
            continue
        caption = held_field.get("caption") or held_field.get("name", "")
        hierarchy = _value_at(hierarchies, int(held_field.get("hierarchy", "-1")))
        made_by_excel = hierarchy is not None and (
            hierarchy.get("hidden") == "1"
            or hierarchy.find(".//{*}cacheHierarchy[@aggregatedColumn]") is not None)
        implicit = IMPLICIT_MEASURE.fullmatch(caption)
        found[place] = (DAX_MEASURE, caption)
        if implicit and made_by_excel:
            found[place] = (implicit.group(1), implicit.group(2))
    return found


def _pivot_table(book: _PivotBook, sheet: Sheet, part: str, cache: _PivotCache,
                 timelines: set[str]) -> PivotTable:
    """One PivotTable, from its part on `sheet` and its cache, its stored values from the
    sheet's cells; a filter named as a Timeline is the Timeline's own."""
    held = _xml(book.parts, part)
    held_fields = list(held.iterfind("{*}pivotFields/{*}pivotField"))
    fields = {}
    indexed = []
    for place, name in enumerate(cache.names):
        held_field = _value_at(held_fields, place)
        if held_field is None:
            held_field = ElementTree.Element("pivotField")
        fields[name], items = _pivot_field(cache, place, held_field)
        indexed.append(items)
    values = [_pivot_value(cache, held_value, indexed)
              for held_value in held.iterfind("{*}dataFields/{*}dataField")]
    report_filters = _report_filters(held, cache.names, indexed, fields)
    for report_filter in report_filters:
        if report_filter.field in fields:
            fields[report_filter.field].hidden = []
    location = held.find("{*}location")
    pivot = PivotTable(
        held.get("name", ""), sheet.title, "" if location is None else location.get("ref", ""),
        _pivot_source(book, cache, sheet.title), _axis_fields(held, "rowFields", cache.names),
        _axis_fields(held, "colFields", cache.names), values, report_filters, fields,
        _pivot_filters(held, cache.names, values, timelines), layout=_layout(held))
    rows = [name for name in pivot.rows if name != VALUES]
    columns = [name for name in pivot.columns if name != VALUES]
    pivot.grand_total_row = held.get("colGrandTotals") != "0" and bool(rows)
    pivot.grand_total_column = held.get("rowGrandTotals") != "0" and bool(columns)
    pivot.subtotals = [name for name in rows[:-1] + columns[:-1] if fields[name].subtotals]
    row_lines = _pivot_lines(held.find("{*}rowItems"), _axis_places(held, "rowFields"),
                             cache.names, indexed)
    column_lines = _pivot_lines(held.find("{*}colItems"), _axis_places(held, "colFields"),
                                cache.names, indexed)
    if location is not None:
        pivot.cells = _pivot_cells(location, row_lines, column_lines, values, sheet.cells)
    return pivot


def _pivot_field(cache: _PivotCache, place: int, held_field: ElementTree.Element
                 ) -> tuple[PivotField, list[object]]:
    """One field as a pivot holds it, and the value of each of its items by its place, as
    the pivot's rows and columns name them."""
    name = cache.names[place]
    pivot_field = PivotField(name, formula=cache.formulas[place],
                             calculated_items=cache.calculated_items.get(name, {}),
                             grouping=cache.groupings[place], subtotals=_subtotals(held_field),
                             shows_items_with_no_data=held_field.get("showAll") != "0")
    indexed = []
    for item in held_field.iterfind("{*}items/{*}item"):
        value = _value_at(cache.items[place], int(item.get("x", "-1")))
        indexed.append(value)
        if item.get("t", "data") != "data" or item.get("m") == "1":
            continue
        pivot_field.items.append(value)
        if item.get("h") == "1":
            pivot_field.hidden.append(value)
    return pivot_field, indexed


def _subtotals(held_field: ElementTree.Element) -> list[str]:
    """A field's subtotals: the functions chosen, Excel's own (AUTOMATIC), or none."""
    chosen = [word for attribute, word in SUBTOTALS.items() if held_field.get(attribute) == "1"]
    if chosen:
        return chosen
    if held_field.get("defaultSubtotal") == "0":
        return []
    return [AUTOMATIC]


def _axis_places(held: ElementTree.Element, axis: str) -> list[int]:
    """The place of each of a pivot's Row or Column fields, -2 for its values."""
    return [int(each.get("x", "0")) for each in held.iterfind(f"{{*}}{axis}/{{*}}field")]


def _axis_fields(held: ElementTree.Element, axis: str, names: list[str]) -> list[str]:
    """The name of each of a pivot's Row or Column fields, outermost first."""
    found = []
    for place in _axis_places(held, axis):
        found.append(VALUES if place < 0 else _field_name(names, place))
    return found


def _layout(held: ElementTree.Element) -> str:
    """A pivot's Report Layout, in Excel's words."""
    if held.get("compact") != "0":
        return "Compact Form"
    if held.get("outline") == "1":
        return "Outline Form"
    return "Tabular Form"


def _pivot_source(book: _PivotBook, cache: _PivotCache, sheet: str) -> PivotSource:
    """What a pivot's cache reads."""
    source = cache.held.find("{*}cacheSource")
    kind = "worksheet" if source is None else source.get("type", "worksheet")
    if kind == "worksheet":
        held = None if source is None else source.find("{*}worksheetSource")
        return _worksheet_source(book, held, sheet)
    if kind == "external":
        return _external_source(book, cache, source.get("connectionId", ""))
    if kind == "consolidation":
        return PivotSource(CONSOLIDATION, "")
    return PivotSource(kind, "")


def _worksheet_source(book: _PivotBook, held: ElementTree.Element | None, sheet: str
                      ) -> PivotSource:
    """A source on a sheet: a Table, a range named by a defined name or by its place, read as
    the Table it would be, or a range in another workbook."""
    if held is None:
        return PivotSource(RANGE, "")
    name = held.get("name", "").split("[")[0]
    if _relationship_id(held):
        return PivotSource(OTHER_WORKBOOK, name or held.get("ref", ""))
    if name in book.tables:
        return PivotSource(EXCEL_TABLE, name, book.tables[name],
                           pieces=[Piece(EXCEL_TABLE, name)])
    on, ref = held.get("sheet", sheet), held.get("ref", "")
    if name in book.names:
        on, _, ref = book.names[name].rpartition("!")
        on = on.removeprefix("'").removesuffix("'").replace("''", "'")
    ref = ref.replace("$", "")
    name = name or f"{on}!{ref}"
    table = None
    if on in book.sheets and ref:
        (top, left), (bottom, right) = _range(ref)
        cells = book.sheets[on].cells
        table = Table(name, ref, [_column(cells, column, range(top + 1, bottom + 1), None)
                                  for column in range(left, right + 1)])
    return PivotSource(RANGE, name, table, pieces=[Piece(RANGE, name)])


def _external_source(book: _PivotBook, cache: _PivotCache, number: str) -> PivotSource:
    """A source through a connection: the Data Model, an OLAP cube, or other data."""
    connection = book.connections.get(number, _Connection(""))
    if connection.is_model:
        hierarchies = list(cache.held.iterfind("{*}cacheHierarchies/{*}cacheHierarchy"))
        tables = []
        for held_field in cache.held.iterfind("{*}cacheFields/{*}cacheField"):
            hierarchy = _value_at(hierarchies, int(held_field.get("hierarchy", "-1")))
            if hierarchy is not None:
                tables.append(hierarchy.get("measureGroup")
                              or hierarchy.get("dimensionUniqueName", "").strip("[]"))
        tables = list(dict.fromkeys(table for table in tables if table))
        pieces = [book.model[table] for table in tables if table in book.model]
        return PivotSource(DATA_MODEL, connection.name, model_tables=tables, pieces=pieces)
    if connection.is_olap or cache.held.find("{*}cacheHierarchies") is not None:
        return PivotSource(OLAP, connection.name)
    return PivotSource(DATA_CONNECTION, connection.name)


def _pivot_value(cache: _PivotCache, held: ElementTree.Element, indexed: list[list[object]]
                 ) -> PivotValue:
    """One value of a pivot, from its data field: its summary, Show Values As and base."""
    place = int(held.get("fld", "0"))
    caption = held.get("name", "")
    summary = SUMMARIES.get(held.get("subtotal", "sum"), held.get("subtotal", ""))
    summarized = _field_name(cache.names, place)
    if place in cache.measures:
        summary, summarized = cache.measures[place]
    shown = held.get("showDataAs", "normal")
    extended = held.find(".//{*}extLst//{*}dataField[@pivotShowAs]")
    if extended is not None:
        shown = extended.get("pivotShowAs", shown)
    value = PivotValue(caption, summarized, summary, SHOWN_AS.get(shown, shown))
    base = int(held.get("baseField", "0"))
    if shown in WITH_BASE_FIELD:
        value.base_field = _field_name(cache.names, base)
    if shown in WITH_BASE_ITEM:
        number = int(held.get("baseItem", "0"))
        value.base_item = BASE_ITEMS.get(number)
        if value.base_item is None and base < len(indexed):
            value.base_item = _value_at(indexed[base], number)
    return value


def _member(name: str, caption: str | None) -> object:
    """An OLAP member, by its caption, or the end of its unique name."""
    found = MEMBER.search(name)
    if caption is not None or found is None:
        return caption
    return found.group(1).replace("]]", "]")


def _report_filters(held: ElementTree.Element, names: list[str], indexed: list[list[object]],
                    fields: dict[str, PivotField]) -> list[ReportFilter]:
    """Each Report filter, and the items it shows: its one item, the items it doesn't hide
    when it shows several, or none for (All)."""
    found = []
    for page in held.iterfind("{*}pageFields/{*}pageField"):
        place = int(page.get("fld", "0"))
        name = _field_name(names, place)
        report_filter = ReportFilter(name)
        if page.get("item") is not None and place < len(indexed):
            report_filter.selected = [_value_at(indexed[place], int(page.get("item", "0")))]
        elif MEMBER.search(page.get("name", "")):
            report_filter.selected = [_member(page.get("name", ""), page.get("cap"))]
        elif name in fields and fields[name].hidden:
            report_filter.selected = [item for item in fields[name].items
                                      if item not in fields[name].hidden]
        found.append(report_filter)
    return found


def _pivot_filters(held: ElementTree.Element, names: list[str], values: list[PivotValue],
                   timelines: set[str]) -> list[PivotFilter]:
    """Each value, label and date filter on a pivot, but a Timeline's own."""
    found = []
    for held_filter in held.iterfind("{*}filters/{*}filter"):
        if held_filter.get("name") in timelines:
            continue
        name = _field_name(names, int(held_filter.get("fld", "0")))
        measure = _value_at(values, int(held_filter.get("iMeasureFld", "0")))
        by = "" if measure is None else measure.caption
        found.append(_pivot_filter(held_filter, name, by))
    return found


def _pivot_filter(held: ElementTree.Element, name: str, by: str) -> PivotFilter:
    """One filter on the field `name`, `by` the value a value filter reads."""
    kind = held.get("type", "")
    if kind in TOP_UNITS:
        top = held.find(".//{*}top10")
        test = "Top"
        count: int | float = 10
        if top is not None:
            test = "Bottom" if top.get("top") == "0" else "Top"
            count = _number(top.get("val", "10"))
        return PivotFilter(name, VALUE_FILTER, test, [count], by, TOP_UNITS[kind])
    given = [held.get(key) for key in ("stringValue1", "stringValue2")
             if held.get(key) is not None]
    if not given:
        given = [custom.get("val", "") for custom in held.iterfind(".//{*}customFilter")]
    values = [_filter_value(text) for text in given]
    if kind.startswith("value"):
        return PivotFilter(name, VALUE_FILTER, FILTER_TESTS.get(kind[5:], kind), values, by)
    if kind.startswith("caption"):
        return PivotFilter(name, LABEL_FILTER, FILTER_TESTS.get(kind[7:], kind), values)
    return PivotFilter(name, DATE_FILTER, _date_test(kind), values)


def _filter_value(text: str) -> int | float | str:
    """A filter's value as the workbook saves it: a number, or text."""
    if re.fullmatch(r"-?\d+(\.\d+)?([eE][-+]?\d+)?", text):
        return _number(text)
    return text


def _date_test(kind: str) -> str:
    """A date filter's test in Excel's words, such as "Before" or "Quarter 1" or "March"."""
    quarter = re.fullmatch(r"Q([1-4])", kind)
    month = re.fullmatch(r"M(1[0-2]|[1-9])", kind)
    if quarter:
        return f"Quarter {quarter.group(1)}"
    if month:
        return MONTH_NAMES[int(month.group(1)) - 1]
    return DATE_TESTS.get(kind, kind)


def _line_total(kind: str) -> str:
    """What a row or column of a pivot's body is, by its type: an item's (""), a subtotal's
    (TOTAL, or a custom subtotal's function), or the GRAND_TOTAL."""
    if kind == "data":
        return ""
    if kind == "default":
        return TOTAL
    if kind == "grand":
        return GRAND_TOTAL
    return SUBTOTAL_LINES.get(kind, kind)


def _pivot_lines(held: ElementTree.Element | None, places: list[int], names: list[str],
                 indexed: list[list[object]]) -> list[tuple[PivotLine | None, int]]:
    """Each row or column of a pivot's body, in order: its line, None for a blank line, and
    the place of the value it shows. Each names its items by their places among its fields'
    items, after the first `r` items of the line before, which it repeats."""
    found: list[tuple[PivotLine | None, int]] = []
    path: list[int] = []
    for line in [] if held is None else held.iterfind("{*}i"):
        kind = line.get("t", "data")
        value = int(line.get("i", "0"))
        if kind in ("grand", "blank"):
            found.append((None if kind == "blank" else PivotLine([], GRAND_TOTAL), value))
            continue
        path = path[:int(line.get("r", "0"))] + [int(each.get("v", "0"))
                                                  for each in line.iterfind("{*}x")]
        items = []
        for position, number in enumerate(path):
            place = _value_at(places, position)
            if place is None or place < 0:
                continue
            items.append((_field_name(names, place), _value_at(indexed[place], number)))
        found.append((PivotLine(items, _line_total(kind)), value))
    return found


def _pivot_cells(location: ElementTree.Element, rows: list[tuple[PivotLine | None, int]],
                 columns: list[tuple[PivotLine | None, int]], values: list[PivotValue],
                 cells: dict[tuple[int, int], str | int | float | bool | datetime.datetime]
                 ) -> list[PivotCell]:
    """Each value cell of a pivot's body, row by row, with the value its sheet stores there:
    the body's values start `firstDataRow` rows and `firstDataCol` columns into its place."""
    (top, left), _ = _range(location.get("ref", "A1"))
    first_row = top + int(location.get("firstDataRow", "1"))
    first_column = left + int(location.get("firstDataCol", "1"))
    found = []
    for row_number, (row, row_value) in enumerate(rows):
        for column_number, (column, column_value) in enumerate(columns):
            value = _value_at(values, max(row_value, column_value))
            if row is None or column is None or value is None:
                continue
            at = (first_row + row_number, first_column + column_number)
            found.append(PivotCell(at, value.caption, row, column, cells.get(at)))
    return found


def _slicers_shown(parts: zipfile.ZipFile, sheets: list[tuple[Sheet, str]]
                   ) -> dict[str, tuple[str, str]]:
    """The caption of each slicer and Timeline the sheets show, and the sheet it is on, by
    its cache's name."""
    found = {}
    for sheet, part in sheets:
        for kind, path in _relationships(parts, part).values():
            if kind not in ("slicer", "timeline"):
                continue
            for shown in _xml(parts, path).iterfind(f"{{*}}{kind}"):
                found[shown.get("cache", "")] = (shown.get("caption", ""), sheet.title)
    return found


def _olap_name(source: str) -> str:
    """A field by its name: an OLAP one, such as [job_runs].[status], by its last part."""
    found = re.search(r"\[((?:[^\]]|\]\])*)\]$", source)
    if found is None:
        return source
    return found.group(1).replace("]]", "]")


def _slicer(held: ElementTree.Element, caches: list[_PivotCache]) -> Slicer:
    """A slicer, from its cache: its field and the items it has selected, as its first
    pivot's cache names them, or, over the Data Model, by their captions."""
    slicer = Slicer(held.get("name", ""), _olap_name(held.get("sourceName", "")))
    tabular = held.find("{*}data/{*}tabular")
    if tabular is not None and caches and slicer.field in caches[0].names:
        items = caches[0].items[caches[0].names.index(slicer.field)]
        slicer.selected = [_value_at(items, int(item.get("x", "-1")))
                           for item in tabular.iterfind("{*}items/{*}i")
                           if item.get("s") == "1"]
    captions = {item.get("n", ""): item.get("c") for item in _all(held, "i")}
    for selection in _all(held, "selection"):
        name = selection.get("n", "")
        if not name.endswith(".[All]"):
            slicer.selected.append(_member(name, captions.get(name)))
    return slicer


def _timeline(held: ElementTree.Element) -> Timeline:
    """A Timeline, from its cache: its field and the days it has selected."""
    timeline = Timeline(held.get("name", ""), _olap_name(held.get("sourceName", "")))
    selection = held.find("{*}state/{*}selection")
    if selection is not None:
        timeline.start = _date_or_none(selection.get("startDate"))
        timeline.end = _date_or_none(selection.get("endDate"))
    return timeline


# --- The Power Queries ----------------------------------------------------------------------


def _quoted_end(m: str, at: int) -> int:
    """Where the string starting with the `"` at `at` ends: its closing `"`, past each `""`."""
    at += 1
    while at < len(m) and not (m[at] == '"' and not m.startswith('""', at)):
        at += 2 if m.startswith('""', at) else 1
    return at


def _statement_end(m: str, at: int) -> int:
    """Where the statement starting at `at` ends: its `;`, outside any string or comment."""
    while at < len(m):
        if m.startswith("//", at):
            at = m.find("\n", at)
            at = len(m) if at < 0 else at
        elif m.startswith("/*", at):
            at = m.find("*/", at + 2)
            at = len(m) if at < 0 else at + 1
        elif m[at] == '"':
            at = _quoted_end(m, at)
        elif m[at] == ";":
            return at
        at += 1
    return len(m)


def _mashup_queries(parts: zipfile.ZipFile) -> list[tuple[str, str]]:
    """Each query the workbook's DataMashup part holds, as Excel saves it ([MS-QDEFF]): base64
    of a version, then the length of a zip and the zip, whose Formulas/Section1.m holds every
    query's M."""
    for name in parts.namelist():
        if not re.fullmatch(r"customXml/item\d+\.xml", name):
            continue
        held = _xml(parts, name)
        if _local(held.tag) != "DataMashup":
            continue
        mashup = base64.b64decode("".join((held.text or "").split()))
        length = struct.unpack_from("<I", mashup, 4)[0]
        with zipfile.ZipFile(io.BytesIO(mashup[8:8 + length])) as package:
            return section_queries(package.read("Formulas/Section1.m").decode("utf-8-sig"))
    return []


@dataclass
class _Connection:
    """One of the workbook's connections: its name; the Power Query it reads, if any; the
    Table it adds to the Data Model, if any; whether it is the Data Model's own
    (ThisWorkbookDataModel), and whether it reads an OLAP cube."""

    name: str
    query: str = ""
    table: str = ""
    is_model: bool = False
    is_olap: bool = False


def _connections(parts: zipfile.ZipFile) -> dict[str, _Connection]:
    """Each of the workbook's connections, by its id."""
    name = "xl/connections.xml"
    if name not in parts.namelist():
        return {}
    found = {}
    for connection in _xml(parts, name).iterfind("{*}connection"):
        database = connection.find("{*}dbPr")
        text = database.get("connection", "") if database is not None else ""
        command = database.get("command", "") if database is not None else ""
        location = re.search(r'Location=(?:"((?:[^"]|"")*)"|([^;]*))', text)
        query = ""
        if location:
            query = location.group(1) if location.group(1) is not None else location.group(2)
        added = connection.find(".//{*}rangePr")
        found[connection.get("id", "")] = _Connection(
            connection.get("name", ""), query.replace('""', '"'),
            added.get("sourceName", "") if added is not None else "",
            connection.get("name") == "ThisWorkbookDataModel" or command == "Model",
            connection.find("{*}olapPr") is not None)
    return found


def _take_sheet_queries(sheets: list[Sheet]) -> list[tuple[str, str]]:
    """Take each query a Power Query sheet holds off its sheet, and give them back: a cell
    "Query <its name>:" with its M in the cell below it."""
    found = []
    for sheet in sheets:
        for (row, column), value in list(sheet.cells.items()):
            label = QUERY_LABEL.fullmatch(value) if isinstance(value, str) else None
            m = sheet.cells.get((row + 1, column))
            if label and isinstance(m, str):
                found.append((label.group(1), m))
                del sheet.cells[(row, column)], sheet.cells[(row + 1, column)]
    return found


# --- What reads what, and in what order -----------------------------------------------------


def _m_names(m: str) -> list[str]:
    """Each name a query's M uses outside its strings and comments, quoted (#"...") or not."""
    names, kept, at = [], [], 0
    while at < len(m):
        if m.startswith('#"', at):
            end = _quoted_end(m, at + 1)
            names.append(m[at + 2:end].replace('""', '"'))
            kept.append(" ")
            at = end + 1
        elif m[at] == '"':
            at = _quoted_end(m, at) + 1
            kept.append(" ")
        elif m.startswith("//", at):
            end = m.find("\n", at)
            at = len(m) if end < 0 else end
        elif m.startswith("/*", at):
            end = m.find("*/", at + 2)
            at = len(m) if end < 0 else end + 2
        else:
            kept.append(m[at])
            at += 1
    return re.findall(r"(?<![\w.#])[A-Za-z_][\w.]*", "".join(kept)) + names


def _formulas_text(table: Table) -> str:
    """Every formula a Table holds, its Total Row's among them, joined by spaces."""
    formulas = []
    for column in table.columns:
        formulas += [value for value in [*column.cells, column.total] if _is_formula(value)]
    return " ".join(formulas)


def _bare_names(formulas: str) -> list[str]:
    """Each name formulas use alone, with no [ after it, such as jobs in
    VLOOKUP([@job_id],jobs,2,FALSE): outside strings, a quoted sheet's name and every
    bracket, so neither a column's name nor a Table's own [ is one."""
    plain = re.sub(r"'(?:[^']|'')*'!", "", re.sub(r'"(?:[^"]|"")*"', '""', formulas))
    shorter = re.sub(r"\[[^\[\]]*\]", "", plain)
    while shorter != plain:
        plain, shorter = shorter, re.sub(r"\[[^\[\]]*\]", "", shorter)
    return BARE_NAME.findall(plain)


def _pivot_pieces(pivots: list[PivotTable]) -> list[Piece]:
    """Each pivot's piece: by its name, or by its sheet and name where another pivot has it."""
    names = [pivot.name for pivot in pivots]
    return [Piece(PIVOT_TABLE, pivot.name if names.count(pivot.name) == 1
                  else f"{pivot.sheet}!{pivot.name}") for pivot in pivots]


def _pivots_read(formulas: str, sheet: str, pivots: list[PivotTable], pieces: list[Piece]
                 ) -> list[Piece]:
    """The pivot each GETPIVOTDATA in formulas on `sheet` reads, by a cell of the pivot."""
    found = []
    for quoted, letters, digits in GETPIVOTDATA.findall(formulas):
        on = quoted.removeprefix("'").removesuffix("'").replace("''", "'") or sheet
        row, column = _where(letters + digits)
        for pivot, piece in zip(pivots, pieces, strict=True):
            top, left, bottom, right = _pivot_bounds(pivot)
            if pivot.sheet == on and top <= row <= bottom and left <= column <= right:
                found.append(piece)
    return found


def _table_reads(table: Table, sheet: str, tables: dict[str, str], query_names: set[str],
                 pivots: tuple[list[PivotTable], list[Piece]]) -> list[Piece]:
    """The pieces a Table reads: the query that loads it, each Table its formulas name, as
    `x[...]` or alone, and each pivot they read with GETPIVOTDATA."""
    pieces = []
    if table.loaded_by in query_names:
        pieces.append(Piece(POWER_QUERY, table.loaded_by))
    formulas = _formulas_text(table)
    for name in TABLE_REFERENCE.findall(formulas) + _bare_names(formulas):
        other = tables.get(name.lower())
        if other and other != table.name:
            pieces.append(Piece(EXCEL_TABLE, other))
    pieces += _pivots_read(formulas, sheet, *pivots)
    return list(dict.fromkeys(pieces))


def _query_reads(query: Query, tables: dict[str, str], query_names: set[str]) -> list[Piece]:
    """The pieces a query reads: each Table it names as Excel.CurrentWorkbook(){[Name=...]},
    and each other query its M names."""
    pieces = []
    for name in READS_THE_WORKBOOK.findall(query.m):
        other = tables.get(name.replace('""', '"').lower())
        if other:
            pieces.append(Piece(EXCEL_TABLE, other))
    pieces += [Piece(POWER_QUERY, name) for name in _m_names(query.m)
               if name in query_names and name != query.name]
    return list(dict.fromkeys(pieces))


def _pieces_read(sheets: list[Sheet], queries: list[Query]) -> dict[Piece, list[Piece]]:
    """Each Table, query, range a pivot reads and pivot, in the workbook's order, and each
    piece it reads."""
    tables = {table.name.lower(): table.name for table in _every_table(sheets)}
    query_names = {query.name for query in queries}
    pivots = []
    for sheet in sheets:
        pivots += sheet.pivot_tables
    pivot_pieces = _pivot_pieces(pivots)
    reads: dict[Piece, list[Piece]] = {}
    for sheet in sheets:
        for table in sheet.tables:
            reads[Piece(EXCEL_TABLE, table.name)] = _table_reads(
                table, sheet.title, tables, query_names, (pivots, pivot_pieces))
    for query in queries:
        reads[Piece(POWER_QUERY, query.name)] = _query_reads(query, tables, query_names)
    for pivot in pivots:
        for piece in pivot.source.pieces:
            if piece.kind == RANGE:
                reads.setdefault(piece, [])
    for pivot, piece in zip(pivots, pivot_pieces, strict=True):
        reads[piece] = [read for read in pivot.source.pieces if read in reads]
    return reads


def _link(reader: Piece, read: Piece) -> str:
    """One link of a loop in Excel's words: a query reads a Table or a query, it loads its
    Table, or a Table's formulas read another Table."""
    if reader.kind == EXCEL_TABLE and read.kind == POWER_QUERY:
        return f"{piece_name(read)} loads {piece_name(reader)}"
    if reader.kind == EXCEL_TABLE:
        return f"{piece_name(reader)}'s formulas read {piece_name(read)}"
    return f"{piece_name(reader)} reads {piece_name(read)}"


def _in_order(reads: dict[Piece, list[Piece]]) -> dict[Piece, list[Piece]]:
    """Each piece after every piece it reads, as `reads` lists them where that leaves a choice,
    with what each reads; a loop is refused, naming its pieces."""
    place = {piece: number for number, piece in enumerate(reads)}
    sorter = graphlib.TopologicalSorter(reads)
    try:
        sorter.prepare()
    except graphlib.CycleError as error:
        # graphlib gives the loop with each piece before the piece that reads it.
        loop = error.args[1]
        links = "; ".join(_link(reader, piece) for piece, reader in zip(loop, loop[1:]))
        raise LoopError(
            f"Its pieces read each other in a loop: {links}.\n"
            "Why: each piece must come after every piece it reads, and in a loop none can, so "
            "no Hive gives the same rows.\n"
            "Usual fix: in Excel, break one of these links, such as a query reading the raw "
            "data's Table in place of a Table in the loop; save the workbook, and run this "
            "again.") from None
    ordered = []
    while sorter.is_active():
        ready = sorted(sorter.get_ready(), key=place.__getitem__)
        ordered += ready
        sorter.done(*ready)
    return {piece: reads[piece] for piece in ordered}

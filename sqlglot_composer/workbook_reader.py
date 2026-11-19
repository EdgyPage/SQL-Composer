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
# The last part of an OLAP name, each ]] in it a ]: status in [job_runs].[status], or a
# member's caption, SUCCESS in [job_runs].[status].&[SUCCESS].
MEMBER = re.compile(r"\[((?:[^\]]|\]\])*)\]$")
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
        pivots = []
        for sheet in self.sheets:
            pivots += sheet.pivot_tables
        return pivots


class LoopError(ValueError):
    """The workbook's pieces read each other in a loop, so no order puts each after what it
    reads: `what` names each link, `why` says why it is refused and `fix` the usual fix, and
    its message is the three, as copilot/workbook_text.py shows it."""

    def __init__(self, what: str, why: str, fix: str) -> None:
        super().__init__(f"{what}\nWhy: {why}\nUsual fix: {fix}")
        self.what = what
        self.why = why
        self.fix = fix


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
        sheets_read = [sheet for sheet, _ in sheets]
        pivot_book = _PivotBook(parts, {sheet.title: sheet for sheet in sheets_read},
                                {table.name: table for table in _every_table(sheets_read)},
                                names, connections, _model_pieces(book, connections))
        slicer_caches = _slicer_caches(parts, linked)
        pivots = _read_pivot_tables(pivot_book, sheets, slicer_caches)
        slicers = _slicers(slicer_caches, pivots, tabs, _slicers_shown(parts, sheets))
    _add_pivot_tables(pivots)
    _connect_slicers(slicers, pivots)
    sheets = sheets_read
    queries = [Query(name, m) for name, m in in_the_mashup or _take_sheet_queries(sheets)]
    tables = {table.name: table for table in _every_table(sheets)}
    for query in queries:
        if not in_the_mashup and query.name in tables:
            tables[query.name].loaded_by = query.name
        for table in tables.values():
            if table.loaded_by == query.name:
                query.loads = table.name
    for slicer, _ in slicers:
        names.pop(slicer.name, None)
    return Workbook(sheets, names, queries, _in_order(_pieces_read(sheets, queries)),
                    [slicer for slicer, _ in slicers])


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
    for sheet_element in _all(book, "sheet"):
        kind, part = linked.get(_relationship_id(sheet_element), ("", ""))
        title = sheet_element.get("name", "")
        if kind == "worksheet":
            sheets.append((_sheet(parts, title, part, strings, dated, loads), part))
            tabs[sheet_element.get("sheetId", "")] = title
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
class _CacheField:
    """One field of a pivot cache: its name (an OLAP field's caption); its items as its
    pivots number them (a grouped field's labels); a calculated field's formula; how it groups
    a field; its calculated items' formulas, by the item; and, for a Data Model or OLAP
    measure, its summary and the field it summarizes."""

    name: str
    items: list[object]
    formula: str = ""
    grouping: Grouping | None = None
    calculated_items: dict[str, str] = field(default_factory=dict)
    measure: tuple[str, str] | None = None


@dataclass
class _PivotCache:
    """A pivot cache as its pivots read it: its definition, and each of its fields."""

    cache_definition: ElementTree.Element
    fields: list[_CacheField]

    @property
    def names(self) -> list[str]:
        """Each field's name, in the cache's order."""
        return [cache_field.name for cache_field in self.fields]


@dataclass
class _ReadPivot:
    """A PivotTable as read, the sheet it is on, and its cache, which its slicers read their
    items from."""

    sheet: Sheet
    pivot: PivotTable
    cache: _PivotCache


def _model_pieces(book: ElementTree.Element, connections: dict[str, _Connection]
                  ) -> dict[str, Piece]:
    """The piece that loads each of the Data Model's tables, by the table's name: the Table
    its connection adds, or the query it loads."""
    by_name = {connection.name: connection for connection in connections.values()}
    pieces = {}
    for model_table in _all(book, "modelTable"):
        connection = by_name.get(model_table.get("connection", ""))
        if connection is not None and connection.table:
            pieces[model_table.get("name", "")] = Piece(EXCEL_TABLE, connection.table)
        elif connection is not None and connection.query:
            pieces[model_table.get("name", "")] = Piece(POWER_QUERY, connection.query)
    return pieces


def _pivot_key(sheet: str, name: str) -> str:
    """A pivot by its sheet and name, such as Pivot!PivotTable1: a pivot's name is its own on
    its sheet only."""
    return f"{sheet}!{name}"


def _unquoted_sheet(name: str) -> str:
    """A sheet's name as a formula or a defined name quotes it, 'My sheet', unquoted."""
    return name.removeprefix("'").removesuffix("'").replace("''", "'")


def _olap_last_part(name: str) -> str:
    """The last part of an OLAP name: status in [job_runs].[status], SUCCESS in the member
    [job_runs].[status].&[SUCCESS]; a name with no brackets as it is."""
    last_part = MEMBER.search(name)
    if last_part is None:
        return name
    return last_part.group(1).replace("]]", "]")


def _slicer_caches(parts: zipfile.ZipFile, linked: dict[str, tuple[str, str]]
                   ) -> list[tuple[str, ElementTree.Element]]:
    """Each slicer's and Timeline's cache, as its kind, slicerCache or timelineCache, and its
    definition."""
    return [(kind, _xml(parts, path)) for kind, path in linked.values()
            if kind in ("slicerCache", "timelineCache")]


def _read_pivot_tables(book: _PivotBook, sheets: list[tuple[Sheet, str]],
                       slicer_caches: list[tuple[str, ElementTree.Element]]
                       ) -> dict[str, _ReadPivot]:
    """Each sheet's PivotTables, by their sheet and name, as `_pivot_key` gives it, each with
    its sheet and its cache."""
    timelines = {definition.get("name", "") for kind, definition in slicer_caches
                 if kind == "timelineCache"}
    pivots = {}
    for sheet, part in sheets:
        for kind, path in _relationships(book.parts, part).values():
            if kind == "pivotTable":
                cache = _pivot_cache(book, path)
                pivot = _pivot_table(book, sheet, path, cache, timelines)
                pivots[_pivot_key(sheet.title, pivot.name)] = _ReadPivot(sheet, pivot, cache)
    return pivots


def _add_pivot_tables(pivots: dict[str, _ReadPivot]) -> None:
    """Add each pivot to its sheet, taking the cells it fills off the sheet's other cells."""
    for read in pivots.values():
        read.sheet.pivot_tables.append(read.pivot)
        top, left, bottom, right = _pivot_bounds(read.pivot)
        for row in range(top, bottom + 1):
            for column in range(left, right + 1):
                read.sheet.cells.pop((row, column), None)


def _slicers(slicer_caches: list[tuple[str, ElementTree.Element]],
             pivots: dict[str, _ReadPivot], tabs: dict[str, str],
             shown: dict[str, tuple[str, str]]) -> list[tuple[Slicer | Timeline, list[str]]]:
    """Each slicer and Timeline, with its caption and sheet, and the pivots it is connected
    to, by their keys: a sheet by its id, as a slicer's cache names it, and a name."""
    slicers = []
    for kind, definition in slicer_caches:
        keys = []
        for connected in definition.iterfind("{*}pivotTables/{*}pivotTable"):
            keys.append(_pivot_key(tabs.get(connected.get("tabId", ""), ""),
                                   connected.get("name", "")))
        if kind == "slicerCache":
            caches = [pivots[key].cache for key in keys if key in pivots]
            slicer = _slicer(definition, caches)
        else:
            slicer = _timeline(definition)
        slicer.caption, slicer.sheet = shown.get(slicer.name, ("", ""))
        slicers.append((slicer, [key for key in keys if key in pivots]))
    return slicers


def _connect_slicers(slicers: list[tuple[Slicer | Timeline, list[str]]],
                     pivots: dict[str, _ReadPivot]) -> None:
    """Connect each slicer and Timeline to the pivots it names, each to the other."""
    for slicer, keys in slicers:
        for key in keys:
            pivot = pivots[key].pivot
            slicer.pivots.append(pivot.name)
            pivot.slicers.append(slicer)
            if isinstance(slicer, Slicer):
                _clear_hidden(pivot.fields, slicer.field)


def _clear_hidden(fields: dict[str, PivotField], name: str) -> None:
    """Clear the items hidden on the field `name`: those a Report filter or a slicer on it
    leaves out are the filter's own, not hidden on the field, though Excel marks them so."""
    if name in fields:
        fields[name].hidden = []


def _pivot_bounds(pivot: PivotTable) -> tuple[int, int, int, int]:
    """The first and last row and column of the cells a pivot fills: its body, and its Report
    filters above it, each a row of two cells, with a blank row under them."""
    (top, left), (bottom, right) = _range(pivot.ref or "A1")
    if pivot.report_filters:
        top -= len(pivot.report_filters) + 1
        right = max(right, left + 1)
    return top, left, bottom, right


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
    """The cache a pivot's part names: each field with its items, and then, as they read
    other fields, each field's grouping, calculated items and measure."""
    path = ""
    for kind, linked_path in _relationships(book.parts, pivot_part).values():
        if kind == "pivotCacheDefinition":
            path = linked_path
    cache_definition = _xml(book.parts, path)
    cache_fields = list(cache_definition.iterfind("{*}cacheFields/{*}cacheField"))
    fields = []
    for cache_field in cache_fields:
        listed = cache_field.find("{*}fieldGroup/{*}groupItems")
        if listed is None:
            listed = cache_field.find("{*}sharedItems")
        items = []
        if listed is not None:
            items = [_item_value(item) for item in listed]
        fields.append(_CacheField(cache_field.get("caption") or cache_field.get("name", ""),
                                  items, cache_field.get("formula", "")))
    for place, cache_field in enumerate(cache_fields):
        fields[place].grouping = _grouping(fields, place, cache_field)
    _add_calculated_items(cache_definition, fields)
    _add_measures(cache_definition, cache_fields, fields)
    return _PivotCache(cache_definition, fields)


def _date_or_none(text: str | None) -> datetime.datetime | None:
    if text is None:
        return None
    return datetime.datetime.fromisoformat(text)


def _number_or_none(text: str | None) -> int | float | None:
    if text is None:
        return None
    return _number(text)


def _grouping(fields: list[_CacheField], place: int, cache_field: ElementTree.Element
              ) -> Grouping | None:
    """How a cache field groups its base field, if it does: by a range of dates or numbers,
    or into groups made by hand."""
    field_group = cache_field.find("{*}fieldGroup")
    if field_group is None:
        return None
    base = _value_at(fields, int(field_group.get("base", str(place))))
    grouped = "" if base is None else base.name
    range_group = field_group.find("{*}rangePr")
    if range_group is not None and range_group.get("groupBy", "range") == "range":
        return Grouping("Number", grouped, _number_or_none(range_group.get("startNum")),
                        _number_or_none(range_group.get("endNum")),
                        _number(range_group.get("groupInterval", "1")))
    if range_group is not None:
        level = range_group.get("groupBy", "")
        interval = None
        if level == "days":
            interval = _number(range_group.get("groupInterval", "1"))
        return Grouping(level.capitalize(), grouped,
                        _date_or_none(range_group.get("startDate")),
                        _date_or_none(range_group.get("endDate")), interval)
    discrete = field_group.find("{*}discretePr")
    if discrete is None or base is None:
        return None
    grouping = Grouping("Items", grouped)
    for number, group_of_item in enumerate(discrete.iterfind("{*}x")):
        label = _value_at(fields[place].items, int(group_of_item.get("v", "0")))
        grouping.groups.setdefault(str(label), []).append(_value_at(base.items, number))
    return grouping


def _value_at(values: list[object], place: int) -> object:
    """The value at `place`, or None when the workbook names a place that isn't there."""
    if 0 <= place < len(values):
        return values[place]
    return None


def _add_calculated_items(cache_definition: ElementTree.Element, fields: list[_CacheField]
                          ) -> None:
    """Add each calculated item's formula to its field, by the item."""
    for calculated in cache_definition.iterfind("{*}calculatedItems/{*}calculatedItem"):
        reference = calculated.find("{*}pivotArea/{*}references/{*}reference")
        if reference is None:
            continue
        cache_field = _value_at(fields, int(reference.get("field", "0")))
        item_place = reference.find("{*}x")
        if cache_field is None or item_place is None:
            continue
        item = _value_at(cache_field.items, int(item_place.get("v", "0")))
        cache_field.calculated_items[str(item)] = calculated.get("formula", "")


def _add_measures(cache_definition: ElementTree.Element,
                  cache_fields: list[ElementTree.Element], fields: list[_CacheField]) -> None:
    """Add each Data Model or OLAP measure's summary and field to its cache field: one Excel
    made, such as "Distinct Count of job_id", by its words; any other a DAX_MEASURE, by its
    name."""
    hierarchies = list(cache_definition.iterfind("{*}cacheHierarchies/{*}cacheHierarchy"))
    for place, cache_field in enumerate(cache_fields):
        if not cache_field.get("name", "").startswith("[Measures]."):
            continue
        caption = cache_field.get("caption") or cache_field.get("name", "")
        hierarchy = _value_at(hierarchies, int(cache_field.get("hierarchy", "-1")))
        made_by_excel = hierarchy is not None and (
            hierarchy.get("hidden") == "1"
            or hierarchy.find(".//{*}cacheHierarchy[@aggregatedColumn]") is not None)
        implicit = IMPLICIT_MEASURE.fullmatch(caption)
        fields[place].measure = (DAX_MEASURE, caption)
        if implicit and made_by_excel:
            fields[place].measure = (implicit.group(1), implicit.group(2))


def _pivot_table(book: _PivotBook, sheet: Sheet, part: str, cache: _PivotCache,
                 timelines: set[str]) -> PivotTable:
    """One PivotTable, from its part on `sheet` and its cache, its stored values from the
    sheet's cells; a filter named as a Timeline is the Timeline's own."""
    pivot_table_definition = _xml(book.parts, part)
    fields, items_by_place = _pivot_fields(pivot_table_definition, cache)
    values = [_pivot_value(cache, data_field, items_by_place) for data_field
              in pivot_table_definition.iterfind("{*}dataFields/{*}dataField")]
    report_filters = _report_filters(pivot_table_definition, cache.names, items_by_place,
                                     fields)
    for report_filter in report_filters:
        _clear_hidden(fields, report_filter.field)
    location = pivot_table_definition.find("{*}location")
    ref = ""
    if location is not None:
        ref = location.get("ref", "")
    pivot = PivotTable(
        name=pivot_table_definition.get("name", ""), sheet=sheet.title, ref=ref,
        source=_pivot_source(book, cache, sheet.title),
        rows=_axis_fields(pivot_table_definition, "rowFields", cache.names),
        columns=_axis_fields(pivot_table_definition, "colFields", cache.names),
        values=values, report_filters=report_filters, fields=fields,
        filters=_pivot_filters(pivot_table_definition, cache.names, values, timelines),
        layout=_layout(pivot_table_definition))
    _add_totals(pivot, pivot_table_definition)
    row_lines = _pivot_lines(pivot_table_definition.find("{*}rowItems"),
                             _axis_places(pivot_table_definition, "rowFields"), cache.names,
                             items_by_place)
    column_lines = _pivot_lines(pivot_table_definition.find("{*}colItems"),
                                _axis_places(pivot_table_definition, "colFields"),
                                cache.names, items_by_place)
    if location is not None:
        pivot.cells = _pivot_cells(location, row_lines, column_lines, values, sheet.cells)
    return pivot


def _pivot_fields(pivot_table_definition: ElementTree.Element, cache: _PivotCache
                  ) -> tuple[dict[str, PivotField], list[list[object]]]:
    """Each field of a pivot's cache as the pivot holds it, by name, and each field's items
    by their places, as the pivot's rows and columns name them."""
    pivot_field_elements = list(
        pivot_table_definition.iterfind("{*}pivotFields/{*}pivotField"))
    fields = {}
    items_by_place = []
    for place, cache_field in enumerate(cache.fields):
        pivot_field_element = _value_at(pivot_field_elements, place)
        if pivot_field_element is None:
            pivot_field_element = ElementTree.Element("pivotField")
        fields[cache_field.name], items = _pivot_field(cache_field, pivot_field_element)
        items_by_place.append(items)
    return fields, items_by_place


def _add_totals(pivot: PivotTable, pivot_table_definition: ElementTree.Element) -> None:
    """Add to a pivot the totals it shows: its Grand Total row, with a Row field, its Grand
    Total column, with a Column field, and each outer field's subtotals."""
    rows = [name for name in pivot.rows if name != VALUES]
    columns = [name for name in pivot.columns if name != VALUES]
    pivot.grand_total_row = (pivot_table_definition.get("colGrandTotals") != "0"
                             and bool(rows))
    pivot.grand_total_column = (pivot_table_definition.get("rowGrandTotals") != "0"
                                and bool(columns))
    pivot.subtotals = [name for name in rows[:-1] + columns[:-1]
                       if pivot.fields[name].subtotals]


def _pivot_field(cache_field: _CacheField, pivot_field_element: ElementTree.Element
                 ) -> tuple[PivotField, list[object]]:
    """One field as a pivot holds it, and the value of each of its items by its place, as
    the pivot's rows and columns name them."""
    pivot_field = PivotField(
        cache_field.name, formula=cache_field.formula,
        calculated_items=cache_field.calculated_items, grouping=cache_field.grouping,
        subtotals=_subtotals(pivot_field_element),
        shows_items_with_no_data=pivot_field_element.get("showAll") != "0")
    items_by_place = []
    for item in pivot_field_element.iterfind("{*}items/{*}item"):
        value = _value_at(cache_field.items, int(item.get("x", "-1")))
        items_by_place.append(value)
        if item.get("t", "data") != "data" or item.get("m") == "1":
            continue
        pivot_field.items.append(value)
        if item.get("h") == "1":
            pivot_field.hidden.append(value)
    return pivot_field, items_by_place


def _subtotals(pivot_field_element: ElementTree.Element) -> list[str]:
    """A field's subtotals: the functions chosen, Excel's own (AUTOMATIC), or none."""
    chosen = [word for attribute, word in SUBTOTALS.items()
              if pivot_field_element.get(attribute) == "1"]
    if chosen:
        return chosen
    if pivot_field_element.get("defaultSubtotal") == "0":
        return []
    return [AUTOMATIC]


def _axis_places(pivot_table_definition: ElementTree.Element, axis: str) -> list[int]:
    """The place of each of a pivot's Row or Column fields, -2 for its values."""
    return [int(axis_field.get("x", "0"))
            for axis_field in pivot_table_definition.iterfind(f"{{*}}{axis}/{{*}}field")]


def _axis_fields(pivot_table_definition: ElementTree.Element, axis: str, names: list[str]
                 ) -> list[str]:
    """The name of each of a pivot's Row or Column fields, outermost first."""
    axis_fields = []
    for place in _axis_places(pivot_table_definition, axis):
        if place < 0:
            axis_fields.append(VALUES)
        else:
            axis_fields.append(_value_at(names, place) or "")
    return axis_fields


def _layout(pivot_table_definition: ElementTree.Element) -> str:
    """A pivot's Report Layout, in Excel's words."""
    if pivot_table_definition.get("compact") != "0":
        return "Compact Form"
    if pivot_table_definition.get("outline") == "1":
        return "Outline Form"
    return "Tabular Form"


def _pivot_source(book: _PivotBook, cache: _PivotCache, sheet: str) -> PivotSource:
    """What a pivot's cache reads."""
    cache_source = cache.cache_definition.find("{*}cacheSource")
    if cache_source is None:
        return _worksheet_source(book, None, sheet)
    kind = cache_source.get("type", "worksheet")
    if kind == "worksheet":
        return _worksheet_source(book, cache_source.find("{*}worksheetSource"), sheet)
    if kind == "external":
        return _external_source(book, cache, cache_source.get("connectionId", ""))
    if kind == "consolidation":
        return PivotSource(CONSOLIDATION, "")
    return PivotSource(kind, "")


def _worksheet_source(book: _PivotBook, worksheet_source: ElementTree.Element | None,
                      sheet: str) -> PivotSource:
    """A source on a sheet: a Table, a range named by a defined name or by its place, read as
    the Table it would be, or a range in another workbook."""
    if worksheet_source is None:
        return PivotSource(RANGE, "")
    name = worksheet_source.get("name", "").split("[")[0]
    if _relationship_id(worksheet_source):
        return PivotSource(OTHER_WORKBOOK, name or worksheet_source.get("ref", ""))
    if name in book.tables:
        return PivotSource(EXCEL_TABLE, name, book.tables[name],
                           pieces=[Piece(EXCEL_TABLE, name)])
    on, ref = worksheet_source.get("sheet", sheet), worksheet_source.get("ref", "")
    if name in book.names:
        quoted, _, ref = book.names[name].rpartition("!")
        on = _unquoted_sheet(quoted)
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
    cache_definition = cache.cache_definition
    if connection.is_model:
        hierarchies = list(cache_definition.iterfind("{*}cacheHierarchies/{*}cacheHierarchy"))
        tables = []
        for cache_field in cache_definition.iterfind("{*}cacheFields/{*}cacheField"):
            hierarchy = _value_at(hierarchies, int(cache_field.get("hierarchy", "-1")))
            if hierarchy is not None:
                tables.append(hierarchy.get("measureGroup")
                              or hierarchy.get("dimensionUniqueName", "").strip("[]"))
        tables = list(dict.fromkeys(table for table in tables if table))
        pieces = [book.model[table] for table in tables if table in book.model]
        return PivotSource(DATA_MODEL, connection.name, model_tables=tables, pieces=pieces)
    if connection.is_olap or cache_definition.find("{*}cacheHierarchies") is not None:
        return PivotSource(OLAP, connection.name)
    return PivotSource(DATA_CONNECTION, connection.name)


def _pivot_value(cache: _PivotCache, data_field: ElementTree.Element,
                 items_by_place: list[list[object]]) -> PivotValue:
    """One value of a pivot, from its data field: its summary, Show Values As and base."""
    cache_field = _value_at(cache.fields, int(data_field.get("fld", "0")))
    summary = SUMMARIES.get(data_field.get("subtotal", "sum"), data_field.get("subtotal", ""))
    summarized = ""
    if cache_field is not None:
        summarized = cache_field.name
    if cache_field is not None and cache_field.measure is not None:
        summary, summarized = cache_field.measure
    shown = data_field.get("showDataAs", "normal")
    extended = data_field.find(".//{*}extLst//{*}dataField[@pivotShowAs]")
    if extended is not None:
        shown = extended.get("pivotShowAs", shown)
    value = PivotValue(data_field.get("name", ""), summarized, summary,
                       SHOWN_AS.get(shown, shown))
    base = int(data_field.get("baseField", "0"))
    if shown in WITH_BASE_FIELD:
        value.base_field = _value_at(cache.names, base) or ""
    if shown in WITH_BASE_ITEM:
        number = int(data_field.get("baseItem", "0"))
        value.base_item = BASE_ITEMS.get(number)
        if value.base_item is None and base < len(items_by_place):
            value.base_item = _value_at(items_by_place[base], number)
    return value


def _report_filters(pivot_table_definition: ElementTree.Element, names: list[str],
                    items_by_place: list[list[object]], fields: dict[str, PivotField]
                    ) -> list[ReportFilter]:
    """Each Report filter, and the items it shows: its one item, the items it doesn't hide
    when it shows several, or none for (All); over an OLAP cube, its member, by its caption."""
    report_filters = []
    for page_field in pivot_table_definition.iterfind("{*}pageFields/{*}pageField"):
        place = int(page_field.get("fld", "0"))
        name = _value_at(names, place) or ""
        member = page_field.get("name", "")
        report_filter = ReportFilter(name)
        if page_field.get("item") is not None and place < len(items_by_place):
            item = _value_at(items_by_place[place], int(page_field.get("item", "0")))
            report_filter.selected = [item]
        elif "&[" in member:
            report_filter.selected = [page_field.get("cap") or _olap_last_part(member)]
        elif name in fields and fields[name].hidden:
            report_filter.selected = [item for item in fields[name].items
                                      if item not in fields[name].hidden]
        report_filters.append(report_filter)
    return report_filters


def _pivot_filters(pivot_table_definition: ElementTree.Element, names: list[str],
                   values: list[PivotValue], timelines: set[str]) -> list[PivotFilter]:
    """Each value, label and date filter on a pivot, but a Timeline's own."""
    pivot_filters = []
    for pivot_filter in pivot_table_definition.iterfind("{*}filters/{*}filter"):
        if pivot_filter.get("name") in timelines:
            continue
        name = _value_at(names, int(pivot_filter.get("fld", "0"))) or ""
        measure = _value_at(values, int(pivot_filter.get("iMeasureFld", "0")))
        by = ""
        if measure is not None:
            by = measure.caption
        pivot_filters.append(_pivot_filter(pivot_filter, name, by))
    return pivot_filters


def _pivot_filter(pivot_filter: ElementTree.Element, name: str, by: str) -> PivotFilter:
    """One filter on the field `name`, `by` the value a value filter reads."""
    kind = pivot_filter.get("type", "")
    if kind in TOP_UNITS:
        top = pivot_filter.find(".//{*}top10")
        test = "Top"
        count: int | float = 10
        if top is not None:
            test = "Bottom" if top.get("top") == "0" else "Top"
            count = _number(top.get("val", "10"))
        return PivotFilter(name, VALUE_FILTER, test, [count], by, TOP_UNITS[kind])
    given = [pivot_filter.get(key) for key in ("stringValue1", "stringValue2")
             if pivot_filter.get(key) is not None]
    if not given:
        given = [custom.get("val", "")
                 for custom in pivot_filter.iterfind(".//{*}customFilter")]
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


def _pivot_lines(items_element: ElementTree.Element | None, places: list[int],
                 names: list[str], items_by_place: list[list[object]]
                 ) -> list[tuple[PivotLine | None, int]]:
    """Each row or column of a pivot's body, from its rowItems or colItems, in order: its
    line, None for a blank line, and the place of the value it shows. Each names its items by
    their places among its fields' items, after the first `r` items of the line before, which
    it repeats."""
    lines: list[tuple[PivotLine | None, int]] = []
    if items_element is None:
        return lines
    path: list[int] = []
    for line in items_element.iterfind("{*}i"):
        kind = line.get("t", "data")
        value = int(line.get("i", "0"))
        if kind == "blank":
            lines.append((None, value))
            continue
        if kind == "grand":
            lines.append((PivotLine([], GRAND_TOTAL), value))
            continue
        path = path[:int(line.get("r", "0"))] + [int(item_place.get("v", "0"))
                                                  for item_place in line.iterfind("{*}x")]
        items = []
        for position, number in enumerate(path):
            place = _value_at(places, position)
            if place is None or place < 0:
                continue
            items.append((_value_at(names, place) or "",
                          _value_at(items_by_place[place], number)))
        lines.append((PivotLine(items, _line_total(kind)), value))
    return lines


def _pivot_cells(location: ElementTree.Element, rows: list[tuple[PivotLine | None, int]],
                 columns: list[tuple[PivotLine | None, int]], values: list[PivotValue],
                 cells: dict[tuple[int, int], str | int | float | bool | datetime.datetime]
                 ) -> list[PivotCell]:
    """Each value cell of a pivot's body, row by row, with the value its sheet stores there:
    the body's values start `firstDataRow` rows and `firstDataCol` columns into its place."""
    (top, left), _ = _range(location.get("ref", "A1"))
    first_row = top + int(location.get("firstDataRow", "1"))
    first_column = left + int(location.get("firstDataCol", "1"))
    pivot_cells = []
    for row_number, (row, row_value) in enumerate(rows):
        for column_number, (column, column_value) in enumerate(columns):
            value = _value_at(values, max(row_value, column_value))
            if row is None or column is None or value is None:
                continue
            at = (first_row + row_number, first_column + column_number)
            pivot_cells.append(PivotCell(at, value.caption, row, column, cells.get(at)))
    return pivot_cells


def _slicers_shown(parts: zipfile.ZipFile, sheets: list[tuple[Sheet, str]]
                   ) -> dict[str, tuple[str, str]]:
    """The caption of each slicer and Timeline the sheets show, and the sheet it is on, by
    its cache's name."""
    captions_and_sheets = {}
    for sheet, part in sheets:
        for kind, path in _relationships(parts, part).values():
            if kind not in ("slicer", "timeline"):
                continue
            for shown in _xml(parts, path).iterfind(f"{{*}}{kind}"):
                captions_and_sheets[shown.get("cache", "")] = (shown.get("caption", ""),
                                                               sheet.title)
    return captions_and_sheets


def _slicer(slicer_cache: ElementTree.Element, caches: list[_PivotCache]) -> Slicer:
    """A slicer, from its cache: its field and the items it has selected, as its first
    pivot's cache names them, or, over the Data Model, by their captions."""
    slicer = Slicer(slicer_cache.get("name", ""),
                    _olap_last_part(slicer_cache.get("sourceName", "")))
    tabular = slicer_cache.find("{*}data/{*}tabular")
    if tabular is not None and caches and slicer.field in caches[0].names:
        items = caches[0].fields[caches[0].names.index(slicer.field)].items
        slicer.selected = [_value_at(items, int(item.get("x", "-1")))
                           for item in tabular.iterfind("{*}items/{*}i")
                           if item.get("s") == "1"]
    captions = {item.get("n", ""): item.get("c") for item in _all(slicer_cache, "i")}
    for selection in _all(slicer_cache, "selection"):
        member = selection.get("n", "")
        if not member.endswith(".[All]"):
            slicer.selected.append(captions.get(member) or _olap_last_part(member))
    return slicer


def _timeline(timeline_cache: ElementTree.Element) -> Timeline:
    """A Timeline, from its cache: its field and the days it has selected."""
    timeline = Timeline(timeline_cache.get("name", ""),
                        _olap_last_part(timeline_cache.get("sourceName", "")))
    selection = timeline_cache.find("{*}state/{*}selection")
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
    connections = {}
    for connection in _xml(parts, name).iterfind("{*}connection"):
        database = connection.find("{*}dbPr")
        text = database.get("connection", "") if database is not None else ""
        command = database.get("command", "") if database is not None else ""
        location = re.search(r'Location=(?:"((?:[^"]|"")*)"|([^;]*))', text)
        query = ""
        if location:
            query = location.group(1) if location.group(1) is not None else location.group(2)
        range_added = connection.find(".//{*}rangePr")
        table = ""
        if range_added is not None:
            table = range_added.get("sourceName", "")
        connections[connection.get("id", "")] = _Connection(
            name=connection.get("name", ""), query=query.replace('""', '"'), table=table,
            is_model=connection.get("name") == "ThisWorkbookDataModel" or command == "Model",
            is_olap=connection.find("{*}olapPr") is not None)
    return connections


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
    pieces = []
    for pivot in pivots:
        if names.count(pivot.name) == 1:
            pieces.append(Piece(PIVOT_TABLE, pivot.name))
        else:
            pieces.append(Piece(PIVOT_TABLE, _pivot_key(pivot.sheet, pivot.name)))
    return pieces


def _pivots_read(formulas: str, sheet: str, pivots: list[PivotTable], pieces: list[Piece]
                 ) -> list[Piece]:
    """The pivot each GETPIVOTDATA in formulas on `sheet` reads, by a cell of the pivot."""
    read = []
    for quoted, letters, digits in GETPIVOTDATA.findall(formulas):
        on = _unquoted_sheet(quoted) or sheet
        row, column = _where(letters + digits)
        for pivot, piece in zip(pivots, pieces, strict=True):
            top, left, bottom, right = _pivot_bounds(pivot)
            if pivot.sheet == on and top <= row <= bottom and left <= column <= right:
                read.append(piece)
    return read


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
            f"Its pieces read each other in a loop: {links}.",
            "each piece must come after every piece it reads, and in a loop none can, so no "
            "Hive gives the same rows.",
            "in Excel, break one of these links, such as a query reading the raw data's Table "
            "in place of a Table in the loop; save the workbook, and run this again.") from None
    ordered = []
    while sorter.is_active():
        ready = sorted(sorter.get_ready(), key=place.__getitem__)
        ordered += ready
        sorter.done(*ready)
    return {piece: reads[piece] for piece in ordered}

"""The workbook reader: an Excel workbook (.xlsx) read as Excel saves it, given back as data
(Toolbox 8.9, ticket 01; ADR 0016).

`read_workbook` gives each sheet's Excel Tables, each column typed or a formula column, with
its Total Row's cell; the sheet's other cells; the workbook's defined names; each Power Query's
M; and the Order, each piece after every piece it reads. The M comes from the queries the
workbook holds, its DataMashup part. A workbook that holds none, such as one whose Excel
couldn't add a query, gives them from its Power Query sheet: a cell "Query <its name>:" with the
M in the cell below it. A loop, such as a query reading a Table whose formulas read that
query's own Table, has no Order, and is refused with a LoopError naming each link of it.

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

# The two kinds of piece the Order puts in order, in Excel's words.
EXCEL_TABLE = "Excel Table"
POWER_QUERY = "Power Query"
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
class Sheet:
    """One sheet: its Tables, its other cells by their row and column, such as (1, 4) for D1,
    the kind of each chart, such as "bar", and how many PivotTables it holds."""

    title: str
    tables: list[Table] = field(default_factory=list)
    cells: dict[tuple[int, int], str | int | float | bool | datetime.datetime] = field(
        default_factory=dict)
    charts: list[str] = field(default_factory=list)
    pivot_tables: int = 0


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
    """What a workbook holds: its sheets, its defined names with what each stands for, its
    Power Queries, and the Order, each piece after every piece it reads, as the workbook lists
    them where that leaves a choice, with the pieces each reads."""

    sheets: list[Sheet]
    defined_names: dict[str, str]
    queries: list[Query]
    order: dict[Piece, list[Piece]]


class LoopError(ValueError):
    """The workbook's pieces read each other in a loop, so no order puts each after what it
    reads."""


def read_workbook(source: Path | bytes) -> Workbook:
    """What a workbook holds, read from its file or its bytes. A query from a Power Query
    sheet loads the Table of its name, if there is one. A loop is refused with a LoopError."""
    data = source if isinstance(source, bytes) else Path(source).read_bytes()
    with zipfile.ZipFile(io.BytesIO(data)) as parts:
        strings = _shared_strings(parts)
        dated = _date_styles(parts)
        loads = _connections(parts)
        book = _xml(parts, "xl/workbook.xml")
        linked = _relationships(parts, "xl/workbook.xml")
        sheets = []
        for held in _all(book, "sheet"):
            kind, part = linked.get(_relationship_id(held), ("", ""))
            if kind == "worksheet":
                sheets.append(_sheet(parts, held.get("name", ""), part, strings, dated, loads))
        names = {name.get("name", ""): name.text or "" for name in _all(book, "definedName")
                 if name.get("localSheetId") is None}
        in_the_mashup = _mashup_queries(parts)
    queries = [Query(name, m) for name, m in in_the_mashup or _take_sheet_queries(sheets)]
    tables = {table.name: table for table in _every_table(sheets)}
    for query in queries:
        if not in_the_mashup and query.name in tables:
            tables[query.name].loaded_by = query.name
        for table in tables.values():
            if table.loaded_by == query.name:
                query.loads = table.name
    return Workbook(sheets, names, queries, _in_order(_pieces_read(sheets, queries)))


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


def _sheet(parts: zipfile.ZipFile, title: str, part: str, strings: list[str],
           dated: set[int], loads: dict[str, str]) -> Sheet:
    """One sheet: its Tables in the order it lists them, then its other cells, charts and
    PivotTables."""
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
        elif kind == "pivotTable":
            sheet.pivot_tables += 1
    return sheet


def _every_table(sheets: list[Sheet]) -> list[Table]:
    """Each Table of the workbook, sheet by sheet."""
    tables = []
    for sheet in sheets:
        tables += sheet.tables
    return tables


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


def _connections(parts: zipfile.ZipFile) -> dict[str, str]:
    """The query each of the workbook's connections reads, by the connection's id."""
    name = "xl/connections.xml"
    if name not in parts.namelist():
        return {}
    found = {}
    for connection in _all(_xml(parts, name), "connection"):
        database = connection.find("{*}dbPr")
        text = database.get("connection", "") if database is not None else ""
        location = re.search(r'Location=(?:"((?:[^"]|"")*)"|([^;]*))', text)
        if location:
            query = location.group(1) if location.group(1) is not None else location.group(2)
            found[connection.get("id", "")] = query.replace('""', '"')
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


def _pieces_read(sheets: list[Sheet], queries: list[Query]) -> dict[Piece, list[Piece]]:
    """Each Table and query, in the workbook's order, and each piece it reads."""
    tables = {table.name.lower(): table.name for table in _every_table(sheets)}
    query_names = {query.name for query in queries}
    reads: dict[Piece, list[Piece]] = {}
    for table in _every_table(sheets):
        pieces = []
        if table.loaded_by in query_names:
            pieces.append(Piece(POWER_QUERY, table.loaded_by))
        for name in TABLE_REFERENCE.findall(_formulas_text(table)):
            other = tables.get(name.lower())
            if other and other != table.name:
                pieces.append(Piece(EXCEL_TABLE, other))
        reads[Piece(EXCEL_TABLE, table.name)] = list(dict.fromkeys(pieces))
    for query in queries:
        pieces = []
        for name in READS_THE_WORKBOOK.findall(query.m):
            other = tables.get(name.replace('""', '"').lower())
            if other:
                pieces.append(Piece(EXCEL_TABLE, other))
        pieces += [Piece(POWER_QUERY, name) for name in _m_names(query.m)
                   if name in query_names and name != query.name]
        reads[Piece(POWER_QUERY, query.name)] = list(dict.fromkeys(pieces))
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

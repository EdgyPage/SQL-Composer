# sqlglot Composer 8.6 - copy it, then edit your copy
"""Write an Excel workbook as text for a Copilot chat: its Tables, formulas and Power Queries,
and the order in which each piece reads the others.

    python copilot/workbook_text.py "my work/costs.xlsx"     writes costs.txt beside it

Run it in a terminal in the download's top folder, with your workbook's path in quotes.

Attach the .txt in place of the workbook, with Copilot files 15, 11 and 12, and ask Copilot to
convert it. The text shows each sheet's Excel Tables row by row, with formulas as you type
them, then the sheet's other cells, each Power Query with its M, and each defined name. The M
comes from the queries the workbook holds. A workbook that holds none, such as one whose
Excel couldn't add a query, gives them from its Power Query sheet: a cell "Query <its name>:"
with the M in the cell below it.

The text ends with each piece in order, each after every piece it reads, each line saying how
in Excel's words:
- a query reads each Table it names as `Excel.CurrentWorkbook(){[Name="..."]}` and each other
  query its M names;
- a Table is loaded by the query that loads it, and its formulas read each Table they name,
  such as `job_runs[dt]`.
A last line says how the Order is used: each final's query reads the steps it needs as CTEs in
that order.

A loop, such as a query reading a Table whose formulas read that query's own Table, has no
such order. The script names each link of it, writes nothing, and exits with 1.

It needs nothing but Python, reads only the workbook you name, and writes only the .txt beside
it. It runs nothing the workbook holds.
"""

import base64
import datetime
import graphlib
import io
import posixpath
import re
import struct
import sys
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree

# The title the Formula workbook's Steps sheet starts with, which the text shows in one line.
STEPS_TITLE = "Formula workbook: how to fill it in"
# Excel's own number formats that show a date, by their ids.
DATE_FORMATS = {*range(14, 23), *range(45, 48)}
# A query's label on a Power Query sheet, with its M in the cell below.
QUERY_LABEL = re.compile(r"Query (.+):")
# A query reading the workbook's Table or name `x`: Excel.CurrentWorkbook(){[Name="x"]}.
READS_THE_WORKBOOK = re.compile(
    r'Excel\.CurrentWorkbook\(\)\s*\{\s*\[\s*Name\s*=\s*"((?:[^"]|"")+)"\s*\]\s*\}')
# A structured reference to Table `x`, such as x[dt] or x[[#This Row],[dt]].
TABLE_REFERENCE = re.compile(r"(?<![\w.\]!])([A-Za-z_\\][\w.]*)\[")
# A formula's reference to the row it is on, as a workbook's file holds it.
HELD_THIS_ROW = re.compile(r"[\w.]+\[\[#This Row\],(\[[^\]]+\])\]")
# The start of each query a section document's M shares: `shared name =`.
SHARED = re.compile(r'shared\s+(#"(?:[^"]|"")*"|[A-Za-z_][\w.]*)\s*=')


@dataclass
class Table:
    """One Excel Table: its name, its range, its rows of cells, and the query that loads it."""

    name: str
    ref: str
    rows: list[list[object]]
    totals_row: bool = False
    loaded_by: str = ""


@dataclass
class Sheet:
    """One sheet: its Tables, its other cells by where they are, and the kind of each chart."""

    title: str
    tables: list[Table] = field(default_factory=list)
    cells: dict[tuple[int, int], object] = field(default_factory=dict)
    charts: list[str] = field(default_factory=list)
    pivot_tables: int = 0


@dataclass
class Query:
    """One Power Query: its name, its M, and the Table it loads, if any."""

    name: str
    m: str
    loads: str = ""


@dataclass
class Workbook:
    """What a workbook holds that its text shows."""

    sheets: list[Sheet]
    defined_names: list[tuple[str, str]]
    queries: list[Query]


class LoopError(ValueError):
    """The workbook's pieces read each other in a loop, so no order puts each after what it
    reads."""


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
    phonetic = {id(t) for run in _all(element, "rPh") for t in _all(run, "t")}
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


def _where(coordinate: str) -> tuple[int, int]:
    """A cell's row and column, from where it is, such as (2, 3) for C2."""
    letters, digits = re.fullmatch(r"([A-Z]+)(\d+)", coordinate).groups()
    column = 0
    for letter in letters:
        column = column * 26 + ord(letter) - 64
    return int(digits), column


def _coordinate(row: int, column: int) -> str:
    """Where a cell is, from its row and column, such as C2 for (2, 3)."""
    letters = ""
    while column:
        column, left = divmod(column - 1, 26)
        letters = chr(65 + left) + letters
    return f"{letters}{row}"


def _shifted(formula: str, rows: int, columns: int) -> str:
    """A shared formula as the cell `rows` down and `columns` across from its first holds it:
    each reference not held with `$` moved as far."""
    def move(found: re.Match[str]) -> str:
        fixed_column, letters, fixed_row, digits = found.groups()
        row, column = _where(letters + digits)
        moved = _coordinate(row if fixed_row else row + rows,
                            column if fixed_column else column + columns)
        moved_letters, moved_digits = re.fullmatch(r"([A-Z]+)(\d+)", moved).groups()
        return f"{fixed_column}{moved_letters}{fixed_row}{moved_digits}"
    return re.sub(r'(?<![\w"\[])(\$?)([A-Z]{1,3})(\$?)(\d+)(?![\w(])', move, formula)


def _number(text: str) -> int | float:
    return float(text) if re.search(r"[.eE]", text) else int(text)


def _value(cell: ElementTree.Element, strings: list[str], dated: set[int]) -> object:
    """A cell's value, as its type says: None for a cell that holds nothing."""
    kind = cell.get("t", "n")
    if kind == "inlineStr":
        inline = cell.find("{*}is")
        return _texts(inline) if inline is not None else ""
    value = cell.find("{*}v")
    if value is None or value.text is None:
        return None
    return _typed(kind, value.text, strings, int(cell.get("s", "0")) in dated)


def _typed(kind: str, text: str, strings: list[str], dated: bool) -> object:
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
           ) -> dict[tuple[int, int], object]:
    """Each cell of a sheet that holds something, by where it is: a formula as "=" and its
    text, else its value. A shared formula's later cells are worked out from its first."""
    cells: dict[tuple[int, int], object] = {}
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
                text = _shifted(first, where[0] - row, where[1] - column)
        value = "=" + text if text else _value(cell, strings, dated)
        if value is not None:
            cells[where] = value
    return cells


def _range(ref: str) -> tuple[tuple[int, int], tuple[int, int]]:
    first, _, last = ref.replace("$", "").partition(":")
    return _where(first), _where(last or first)


def _table(parts: zipfile.ZipFile, part: str, cells: dict[tuple[int, int], object],
           loads: dict[str, str]) -> Table:
    """The Table `part` holds, its rows read from its sheet's `cells`, and the query that
    loads it, through its query table's connection."""
    held = _xml(parts, part)
    name = held.get("displayName") or held.get("name", "")
    ref = held.get("ref", "")
    (top, left), (bottom, right) = _range(ref)
    rows = [[cells.get((row, column)) for column in range(left, right + 1)]
            for row in range(top, bottom + 1)]
    loaded_by = ""
    for kind, query_table in _relationships(parts, part).values():
        if kind == "queryTable":
            loaded_by = loads.get(_xml(parts, query_table).get("connectionId", ""), "")
    return Table(name, ref, rows, int(held.get("totalsRowCount", "0")) > 0, loaded_by)


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
        in_a_table |= {(row, column) for row in range(top, bottom + 1)
                       for column in range(left, right + 1)}
    sheet.cells = {where: value for where, value in sorted(cells.items())
                   if where not in in_a_table}
    for kind, path in linked.values():
        if kind == "drawing":
            sheet.charts += _charts(parts, path)
        elif kind == "pivotTable":
            sheet.pivot_tables += 1
    return sheet


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


def take_sheet_queries(sheets: list[Sheet]) -> list[tuple[str, str]]:
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


def read_workbook(source: Path | bytes) -> Workbook:
    """What a workbook holds that its text shows, read from its file or its bytes. A query
    from a Power Query sheet loads the Table of its name, if there is one."""
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
        names = [(name.get("name", ""), name.text or "") for name in _all(book, "definedName")
                 if name.get("localSheetId") is None]
        in_the_mashup = _mashup_queries(parts)
    queries = [Query(name, m) for name, m in in_the_mashup or take_sheet_queries(sheets)]
    tables = {table.name: table for sheet in sheets for table in sheet.tables}
    for query in queries:
        if not in_the_mashup and query.name in tables:
            tables[query.name].loaded_by = query.name
        for table in tables.values():
            if table.loaded_by == query.name:
                query.loads = table.name
    return Workbook(sheets, names, queries)


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


def _add(pieces: list[tuple[str, str]], piece: tuple[str, str]) -> None:
    """Add `piece` to `pieces`, unless it is there."""
    if piece not in pieces:
        pieces.append(piece)


def pieces_read(workbook: Workbook) -> dict[tuple[str, str], list[tuple[str, str]]]:
    """Each Table and query, in the workbook's order, and each piece it reads."""
    tables = {table.name.lower(): table.name for sheet in workbook.sheets
              for table in sheet.tables}
    queries = {query.name for query in workbook.queries}
    read: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for sheet in workbook.sheets:
        for table in sheet.tables:
            pieces = [("Power Query", table.loaded_by)] if table.loaded_by in queries else []
            formulas = " ".join(value for row in table.rows for value in row
                                if isinstance(value, str) and value.startswith("="))
            for name in TABLE_REFERENCE.findall(formulas):
                other = tables.get(name.lower())
                if other and other != table.name:
                    _add(pieces, ("Excel Table", other))
            read[("Excel Table", table.name)] = pieces
    for query in workbook.queries:
        pieces = []
        for name in READS_THE_WORKBOOK.findall(query.m):
            other = tables.get(name.replace('""', '"').lower())
            if other:
                _add(pieces, ("Excel Table", other))
        for name in _m_names(query.m):
            if name in queries and name != query.name:
                _add(pieces, ("Power Query", name))
        read[("Power Query", query.name)] = pieces
    return read


def piece_name(piece: tuple[str, str]) -> str:
    """A piece as the text names it, such as `Excel Table "job_runs"`."""
    return f'{piece[0]} "{piece[1]}"'


def _link(reader: tuple[str, str], read: tuple[str, str]) -> str:
    """One link of a loop in Excel's words: a query reads a Table or a query, it loads its
    Table, or a Table's formulas read another Table."""
    if reader[0] == "Excel Table" and read[0] == "Power Query":
        return f"{piece_name(read)} loads {piece_name(reader)}"
    if reader[0] == "Excel Table":
        return f"{piece_name(reader)}'s formulas read {piece_name(read)}"
    return f"{piece_name(reader)} reads {piece_name(read)}"


def in_order(workbook: Workbook) -> list[tuple[tuple[str, str], list[tuple[str, str]]]]:
    """Each Table and query after every piece it reads, as the workbook lists them where that
    leaves a choice, with what each reads; a loop is refused, naming its pieces."""
    read = pieces_read(workbook)
    place = {piece: number for number, piece in enumerate(read)}
    sorter = graphlib.TopologicalSorter(read)
    try:
        sorter.prepare()
    except graphlib.CycleError as error:
        # graphlib gives the loop with each piece before the piece that reads it.
        loop = error.args[1]
        links = "; ".join(_link(reader, read) for read, reader in zip(loop, loop[1:]))
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
    return [(piece, read[piece]) for piece in ordered]


# --- The text -------------------------------------------------------------------------------


def as_typed(formula: str) -> str:
    """A formula as a person types it, and Excel's formula bar shows it: no `_xlfn.` or other
    prefix Excel saves before a newer function, and `[@units]` for the row it is on."""
    def this_row(found: re.Match[str]) -> str:
        column = found.group(1)[1:-1]
        return f"[@{column}]" if re.fullmatch(r"\w+", column) else f"[@[{column}]]"
    return HELD_THIS_ROW.sub(this_row, re.sub(r"_xl(?:fn|ws|pm)\.", "", formula))


def cell_text(value: object, typed: bool) -> str:
    """A cell's value as text: a formula as typed, or as saved when `typed` is False, and a
    whole number with no `.0`."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).upper()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, str) and value.startswith("=") and typed:
        return as_typed(value)
    return str(value)


def _row_label(table: Table, number: int, count: int) -> str:
    """How the text names row `number` of a Table of `count` rows."""
    if number == 1:
        return "Headers"
    if table.totals_row and number == count:
        return "Total Row"
    return f"Row {number}"


def _sheet_lines(sheet: Sheet, typed: bool) -> list[str]:
    """One sheet as text: its Tables row by row, then its other cells, charts and
    PivotTables."""
    if sheet.title == "Steps" and sheet.cells.get((1, 1)) == STEPS_TITLE:
        return ['Sheet "Steps": the empty Formula workbook\'s steps, as it ships.']
    lines = [f'Sheet "{sheet.title}"']
    for table in sheet.tables:
        by = f', loaded by Power Query "{table.loaded_by}"' if table.loaded_by else ""
        lines.append(f'  Excel Table "{table.name}", {table.ref}{by}')
        for number, row in enumerate(table.rows, 1):
            cells = " | ".join(cell_text(value, typed) for value in row)
            lines.append(f"    {_row_label(table, number, len(table.rows))}: {cells}")
    for (row, column), value in sheet.cells.items():
        lines.append(f"  {_coordinate(row, column)}: {cell_text(value, typed)}")
    lines += [f"  A {kind} chart" if kind else "  A chart" for kind in sheet.charts]
    return lines + ["  A PivotTable"] * sheet.pivot_tables


def as_text(workbook: Workbook, typed: bool = True) -> str:
    """The workbook as text: each sheet, each Power Query and its M, each defined name, then
    each piece in order."""
    lines = [line for sheet in workbook.sheets for line in _sheet_lines(sheet, typed)]
    for query in workbook.queries:
        to = f'loads into Excel Table "{query.loads}"' if query.loads else "connection only"
        lines.append(f'Power Query "{query.name}" ({to}):')
        lines += [f"    {line}" for line in query.m.strip().splitlines()]
    for name, text in workbook.defined_names:
        lines.append(f"Defined name {name}: {cell_text('=' + text, typed)[1:]}")
    lines.append("Order, each piece after every piece it reads:")
    for number, (piece, pieces) in enumerate(in_order(workbook), 1):
        lines.append(f"  {number}. {_order_line(piece, pieces)}")
    lines.append("Each final's query reads the steps it needs as CTEs in this order, each CTE "
                 "after every CTE it reads.")
    return "\n".join(lines) + "\n"


def _order_line(piece: tuple[str, str], pieces: list[tuple[str, str]]) -> str:
    """A piece's line in the Order, in Excel's words: the query that loads a Table, the Tables
    a Table's formulas read, and what a query reads."""
    loaded_by = [other for other in pieces
                 if piece[0] == "Excel Table" and other[0] == "Power Query"]
    read = [other for other in pieces if other not in loaded_by]
    line = piece_name(piece)
    if loaded_by:
        line += ", loaded by " + ", ".join(piece_name(other) for other in loaded_by)
    if read:
        verb = "its formulas read" if piece[0] == "Excel Table" else "reads"
        line += f", {verb} " + ", ".join(piece_name(other) for other in read)
    return line


def workbook_text(source: Path | bytes, typed: bool = True) -> str:
    """A workbook's text, from its file or its bytes."""
    return as_text(read_workbook(source), typed)


def main(arguments: list[str]) -> int:
    """Write each workbook named as a .txt beside it: 0 once each is written, 1 when one
    can't be, 2 with none named."""
    if not arguments:
        print("Run it as: python workbook_text.py your_workbook.xlsx")
        return 2
    failed = 0
    for name in arguments:
        path = Path(name)
        try:
            text = workbook_text(path)
        except LoopError as error:
            print(f"{path}: nothing was written. {error}", file=sys.stderr)
            failed = 1
            continue
        except (OSError, zipfile.BadZipFile, KeyError, ElementTree.ParseError):
            print(f"{path} can't be read as an Excel workbook (.xlsx).\n"
                  "Why: the script reads a workbook as Excel saves it, a zip of its parts.\n"
                  "Usual fix: name a workbook that is there, saved by Excel as .xlsx, not .xls "
                  "or .csv.", file=sys.stderr)
            failed = 1
            continue
        written = path.with_suffix(".txt")
        written.write_text(text, encoding="utf-8")
        print(f"Wrote {written}: attach it in place of {path.name}.")
    return failed


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

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

It reads the workbook with the Toolbox's own reader, sqlglot_composer/workbook_reader.py:
keep the sqlglot_composer folder beside the copilot folder that holds this script, as the
download holds them. It needs nothing installed but Python, reads only the workbook you name,
and writes only the .txt beside it. It runs nothing the workbook holds.
"""

import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

# The reader is loaded alone, from the Toolbox's folder beside this one, and never through the
# Toolbox's own import, which needs sqlglot; the folder is on the path only while it loads.
TOOLBOX = str(Path(__file__).resolve().parent.parent / "sqlglot_composer")
sys.path.insert(0, TOOLBOX)
try:
    import workbook_reader
    from workbook_reader import LoopError, Piece, Sheet, Table, Workbook
except ModuleNotFoundError:
    sys.exit("workbook_text.py can't find the workbook reader, "
             "sqlglot_composer/workbook_reader.py.\n"
             "Why: it reads your workbook with the Toolbox's reader, which it looks for in "
             f"{TOOLBOX}.\n"
             "Usual fix: put the download's sqlglot_composer folder there, beside the copilot "
             "folder that holds this script; nothing needs installing.")
finally:
    sys.path.remove(TOOLBOX)

# The title the Formula workbook's Steps sheet starts with, which the text shows in one line.
STEPS_TITLE = "Formula workbook: how to fill it in"
# A formula's reference to the row it is on, as a workbook's file holds it.
HELD_THIS_ROW = re.compile(r"[\w.]+\[\[#This Row\],(\[[^\]]+\])\]")


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


def _table_rows(table: Table) -> list[list[object]]:
    """A Table's rows as its sheet shows them: its headers, each row below them, and its Total
    Row, if it has one."""
    rows: list[list[object]] = [[column.header for column in table.columns]]
    for number in range(len(table.columns[0].cells)):
        rows.append([column.cells[number] for column in table.columns])
    if table.has_total_row:
        rows.append([column.total for column in table.columns])
    return rows


def _row_label(table: Table, number: int, count: int) -> str:
    """How the text names row `number` of a Table of `count` rows."""
    if number == 1:
        return "Headers"
    if table.has_total_row and number == count:
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
        rows = _table_rows(table)
        for number, row in enumerate(rows, 1):
            cells = " | ".join(cell_text(value, typed) for value in row)
            lines.append(f"    {_row_label(table, number, len(rows))}: {cells}")
    for (row, column), value in sheet.cells.items():
        lines.append(f"  {workbook_reader.coordinate(row, column)}: {cell_text(value, typed)}")
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
    for name, text in workbook.defined_names.items():
        lines.append(f"Defined name {name}: {cell_text('=' + text, typed)[1:]}")
    lines.append("Order, each piece after every piece it reads:")
    for number, (piece, pieces) in enumerate(workbook.order.items(), 1):
        lines.append(f"  {number}. {_order_line(piece, pieces)}")
    lines.append("Each final's query reads the steps it needs as CTEs in this order, each CTE "
                 "after every CTE it reads.")
    return "\n".join(lines) + "\n"


def _order_line(piece: Piece, pieces: list[Piece]) -> str:
    """A piece's line in the Order, in Excel's words: the query that loads a Table, the Tables
    a Table's formulas read, and what a query reads."""
    is_a_table = piece.kind == workbook_reader.EXCEL_TABLE
    loaded_by = [other for other in pieces
                 if is_a_table and other.kind == workbook_reader.POWER_QUERY]
    read = [other for other in pieces if other not in loaded_by]
    line = workbook_reader.piece_name(piece)
    if loaded_by:
        line += ", loaded by " + ", ".join(workbook_reader.piece_name(other)
                                           for other in loaded_by)
    if read:
        verb = "its formulas read" if is_a_table else "reads"
        line += f", {verb} " + ", ".join(workbook_reader.piece_name(other) for other in read)
    return line


def workbook_text(source: Path | bytes, typed: bool = True) -> str:
    """A workbook's text, from its file or its bytes."""
    return as_text(workbook_reader.read_workbook(source), typed)


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

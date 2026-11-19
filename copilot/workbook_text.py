"""Write an Excel workbook as text for a Copilot chat: its Tables, formulas, PivotTables and
Power Queries, and the order in which each piece reads the others.

    python copilot/workbook_text.py "my work/costs.xlsx"     writes costs.txt beside it

Run it in a terminal in the download's top folder, with your workbook's path in quotes.

Attach the .txt in place of the workbook, with Copilot files 15, 11 and 12, and ask Copilot to
convert it. The text shows each sheet's Excel Tables row by row, with formulas as you type
them, then the sheet's other cells and its PivotTables, each Power Query with its M, and each
defined name. Each PivotTable is shown as `PivotTable "name"`, with what it reads (its
Source), its Rows, Columns, Values and Filters as the PivotTable Fields pane shows them, each
Value's Summarize Values By and Show Values As, its calculated fields and items, its grouped
fields, its hidden items, its value filters, each slicer and Timeline connected to it with what
it has selected, the totals it shows, and each of its cells. For each cell, the text gives the
number Excel last stored in it, and a percentage as Excel shows it where the Value is shown as
a %; then which Value it is, and the row and column items it stands for. The M comes from the
queries the workbook holds. A workbook that holds none, such as one whose
Excel couldn't add a query, gives them from its Power Query sheet: a cell "Query <its name>:"
with the M in the cell below it.

The text ends with each piece in order, each after every piece it reads, each line saying how
in Excel's words:
- a query reads each Table it names as `Excel.CurrentWorkbook(){[Name="..."]}` and each other
  query its M names;
- a Table is loaded by the query that loads it, and its formulas read each Table they name,
  such as `job_runs[dt]`, or `jobs` alone in `VLOOKUP([@job_id],jobs,2,FALSE)`, and each
  PivotTable they read with GETPIVOTDATA;
- a PivotTable reads its Source: a Table, a range, or each Table or query loading the Data
  Model's tables it reads.
A last line says how the Order is used: each final's query reads the steps it needs as CTEs in
that order.

A loop, such as a query reading a Table whose formulas read that query's own Table, has no
such order. The script names each link of it, writes nothing, and exits with 1.

It reads the workbook with the Toolbox's own reader, sqlglot_composer/workbook_reader.py:
keep the sqlglot_composer folder beside the copilot folder that holds this script, as the
download holds them. It needs nothing installed but Python, reads only the workbook you name,
and writes only the .txt beside it. It runs nothing the workbook holds.
"""

import datetime
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
    from workbook_reader import (LoopError, Piece, PivotCell, PivotField, PivotFilter,
                                 PivotLine, PivotSource, PivotTable, PivotValue, Sheet, Slicer,
                                 Table, Timeline, Workbook)
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
    for pivot in sheet.pivot_tables:
        lines += _pivot_table_lines(pivot, typed)
    return lines


def _item_text(item: object, typed: bool) -> str:
    """An item of a pivot's field as text: a blank as Excel shows it, (blank)."""
    if item is None:
        return "(blank)"
    return cell_text(item, typed)


def _items_text(items: list[object], typed: bool) -> str:
    """Items of a pivot's field as text, one after the other, such as "FAILED, SUCCESS"."""
    return ", ".join(_item_text(item, typed) for item in items)


def _source_text(source: PivotSource) -> str:
    """What a pivot reads, in Excel's words."""
    if source.kind == workbook_reader.EXCEL_TABLE:
        by = ""
        if source.table is not None and source.table.loaded_by:
            by = f', loaded by Power Query "{source.table.loaded_by}"'
        return f'Excel Table "{source.name}"{by}'
    if source.kind == workbook_reader.RANGE and source.table is not None:
        headers = " | ".join(column.header for column in source.table.columns)
        return f"the range {source.name}, read as the Table it would be: {headers}"
    if source.kind == workbook_reader.DATA_MODEL:
        line = f"the Data Model, its tables {', '.join(source.model_tables)}"
        if source.pieces:
            loaded = ", ".join(workbook_reader.piece_name(piece) for piece in source.pieces)
            line += f", loaded from {loaded}"
        return line
    if source.kind == workbook_reader.OLAP:
        return f'an OLAP cube, through the connection "{source.name}"'
    return f'{source.kind} "{source.name}"'


def _value_text(value: PivotValue, typed: bool) -> str:
    """A pivot's value as its Value Field Settings say it: Summarize Values By, then Show
    Values As, with its base field and item."""
    if value.summary == workbook_reader.DAX_MEASURE:
        line = f'Value "{value.caption}": the DAX measure {value.field}'
    else:
        line = f'Value "{value.caption}": {value.summary} of {value.field}'
    if value.shown_as:
        line += f", Show Values As {value.shown_as}"
    if value.base_field:
        line += f", Base field {value.base_field}"
    if value.base_field and value.base_item is not None:
        line += f", Base item {_item_text(value.base_item, typed)}"
    return line


def _grouping_text(pivot_field: PivotField, typed: bool) -> str:
    """How a pivot's field groups another, as Excel's Grouping dialog says it."""
    grouping = pivot_field.grouping
    line = f'Field "{pivot_field.name}" groups {grouping.field}'
    if grouping.by == "Items":
        groups = "; ".join(f'"{name}" = {_items_text(items, typed)}'
                           for name, items in grouping.groups.items())
        return f"{line} by hand: {groups}"
    if grouping.by == "Number":
        line += f" By {cell_text(grouping.interval, typed)}"
    else:
        line += f" By {grouping.by}"
    if grouping.by == "Days" and grouping.interval is not None:
        line += f", Number of days {cell_text(grouping.interval, typed)}"
    if grouping.start is not None:
        line += f", Starting at {_day_text(grouping.start, typed)}"
    if grouping.end is not None:
        line += f", Ending at {_day_text(grouping.end, typed)}"
    return line


def _day_text(value: object, typed: bool) -> str:
    """A date with no time of day as its day alone, 2026-09-24, as Excel shows it; any other
    value as its cell would show it."""
    if isinstance(value, datetime.datetime) and value.time() == datetime.time():
        return value.date().isoformat()
    return cell_text(value, typed)


def _field_lines(pivot: PivotTable, typed: bool) -> list[str]:
    """What a pivot's fields hold beyond where they are: calculated fields and items, each
    grouping of a field it shows, items hidden, and items shown with no data."""
    shown = {*pivot.rows, *pivot.columns, *(each.field for each in pivot.report_filters)}
    lines = []
    for pivot_field in pivot.fields.values():
        if pivot_field.formula:
            lines.append(f'Calculated Field "{pivot_field.name}" = {pivot_field.formula}')
        for item, formula in pivot_field.calculated_items.items():
            lines.append(f'Calculated Item "{item}" on {pivot_field.name} = {formula}')
        if pivot_field.grouping is not None and pivot_field.name in shown:
            lines.append(_grouping_text(pivot_field, typed))
        if pivot_field.hidden:
            lines.append(f"Items hidden on {pivot_field.name}: "
                         f"{_items_text(pivot_field.hidden, typed)}")
        if pivot_field.shows_items_with_no_data and pivot_field.name in shown:
            lines.append(f"Show items with no data: on, for {pivot_field.name}")
    return lines


def _filter_text(pivot_filter: PivotFilter, typed: bool) -> str:
    """A value, label or date filter, as its dialog says it."""
    values = " and ".join(_item_text(value, typed) for value in pivot_filter.values)
    line = f"{pivot_filter.kind} on {pivot_filter.field}: "
    if pivot_filter.unit:
        return line + f"{pivot_filter.test} {values} {pivot_filter.unit} by {pivot_filter.by}"
    if pivot_filter.by:
        line += f"{pivot_filter.by} "
    return line + f"{pivot_filter.test} {values}".rstrip()


def _slicer_text(slicer: Slicer | Timeline, typed: bool) -> str:
    """A slicer or Timeline: where it is, its field, what it has selected, and the pivots it
    is connected to."""
    if isinstance(slicer, Timeline):
        kind, selected = "Timeline", _timeline_selection(slicer, typed)
    else:
        kind, selected = "Slicer", _items_text(slicer.selected, typed) or "(All)"
    line = f'{kind} "{slicer.caption or slicer.name}"'
    if slicer.sheet:
        line += f' on sheet "{slicer.sheet}"'
    return (f"{line}, field {slicer.field}: selected {selected}; connected to "
            f"{', '.join(slicer.pivots)}")


def _timeline_selection(timeline: Timeline, typed: bool) -> str:
    """The days a Timeline has selected: one day, from one to another, or every date."""
    if timeline.start is None:
        return "every date"
    if timeline.start == timeline.end:
        return _day_text(timeline.start, typed)
    return f"{_day_text(timeline.start, typed)} to {_day_text(timeline.end, typed)}"


def _totals_text(pivot: PivotTable) -> str:
    """The totals a pivot shows: its Grand Total row and column, and each field's
    subtotals."""
    shown = []
    if pivot.grand_total_row:
        shown.append("Grand Total row")
    if pivot.grand_total_column:
        shown.append("Grand Total column")
    for name in pivot.subtotals:
        functions = pivot.fields[name].subtotals
        chosen = ""
        if functions != [workbook_reader.AUTOMATIC]:
            chosen = f" ({', '.join(functions)})"
        shown.append(f"subtotals of {name}{chosen}")
    return f"Totals shown: {', '.join(shown) or 'none'}"


def _line_text(area: str, line: PivotLine, typed: bool) -> str:
    """The row or column a cell is on, such as "Rows job_id 1", "Columns dt 2026-09-23
    Total" or "Rows Grand Total"."""
    if line.total == workbook_reader.GRAND_TOTAL:
        return f"{area} Grand Total"
    items = ", ".join(f"{name} {_item_text(item, typed)}" for name, item in line.items)
    return " ".join(part for part in (area, items, line.total) if part)


def _cell_line(pivot: PivotTable, cell: PivotCell, typed: bool) -> str:
    """One value cell: what Excel stored in it, and as a percentage where its Value is shown
    as a %, then its Value and the items it stands for."""
    parts = [cell.value]
    shown_as = [value.shown_as for value in pivot.values if value.caption == cell.value]
    is_a_number = isinstance(cell.stored, int | float) and not isinstance(cell.stored, bool)
    if is_a_number and shown_as and shown_as[0].startswith("%"):
        parts.insert(0, f"{cell.stored * 100:.2f}%")
    if any(name != workbook_reader.VALUES for name in pivot.rows):
        parts.append(_line_text("Rows", cell.row, typed))
    if any(name != workbook_reader.VALUES for name in pivot.columns):
        parts.append(_line_text("Columns", cell.column, typed))
    stored = "empty" if cell.stored is None else cell_text(cell.stored, typed)
    return (f"      {workbook_reader.coordinate(*cell.at)}: {stored} "
            f"({'; '.join(parts)})")


def _pivot_table_lines(pivot: PivotTable, typed: bool) -> list[str]:
    """One PivotTable as text: its Source, its fields as the PivotTable Fields pane holds
    them, its Pivot filters, its totals and its cells."""
    lines = [f"Source: {_source_text(pivot.source)}"]
    for area, names in (("Rows", pivot.rows), ("Columns", pivot.columns)):
        if names:
            lines.append(f"{area}: {', '.join(names)}")
    lines += [_value_text(value, typed) for value in pivot.values]
    for report_filter in pivot.report_filters:
        selected = _items_text(report_filter.selected, typed)
        if len(report_filter.selected) > 1:
            selected = f"(Multiple Items) {selected}"
        lines.append(f"Filter {report_filter.field}: {selected or '(All)'}")
    lines += _field_lines(pivot, typed)
    lines += [_filter_text(pivot_filter, typed) for pivot_filter in pivot.filters]
    lines += [_slicer_text(slicer, typed) for slicer in pivot.slicers]
    lines.append(_totals_text(pivot))
    lines.append("Cells: each value cell, what Excel last stored in it, then the Value "
                 "it shows and the Rows and Columns items it stands for:")
    return ([f'  PivotTable "{pivot.name}", {pivot.ref}']
            + [f"    {line}" for line in lines]
            + [_cell_line(pivot, cell, typed) for cell in pivot.cells])


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

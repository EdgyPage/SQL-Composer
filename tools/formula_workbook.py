"""Build the empty Formula workbook, `copilot/formula_workbook.xlsx`.

Run it on `dev` after changing the steps below; `python tools/copilot_files.py` runs it too:

    python tools/formula_workbook.py

A test fails while the committed workbook differs from what this builds, compared by its
sheets, Tables and cells: a zip's times change with every build, so its bytes would too.

A Formula workbook is laid out so Copilot can read its formulas as SQL: a sample of raw data in
Excel Tables, each calculation in a Table's formulas or a Power Query step, and fixed values in
a Table of their own. A person copies this empty one and moves a presentation workbook's data
and formulas into the copy. It holds the steps and the two Tables whose headers are fixed,
Parameters and Keys, empty: no data Table, no formula and no row, since a filled-in example is
something to half-edit and forget.

It is the one file main ships that main can't rebuild: openpyxl, which writes it, is pinned in
requirements-dev.txt only, and the export copies the file as dev holds it.

The Copilot evaluation's Excel tasks (`tools/excel_eval_tasks.py`) describe filled-in Formula
workbooks, `FormulaWorkbook`: `build` makes one, a copy of the empty one with each Table's sample
rows read from the Example database, and `as_text` writes what Copilot reads in it, read back
from the saved file, for a proxy model, which can't be given a file. openpyxl writes no Power
Query and no PivotTable, so a workbook's queries are given as their M, and anything else it
can't write as a note, both in the text alone.
"""

from __future__ import annotations

import io
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import openpyxl
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT)]
EMPTY = ROOT / "copilot" / "formula_workbook.xlsx"

# The steps sheet, one paragraph a row. A heading is a line that ends with a colon.
STEPS = (
    "Formula workbook: how to fill it in",
    "Copilot reads this workbook and writes Hive, the SQL your team's database runs, without "
    "anyone explaining what the workbook is for. Make a copy of this file for each piece of "
    "work.",
    "Your data:",
    "1. For each table of raw data the work starts from, paste a sample on a sheet of its own, "
    "as values only (Home > Paste > Paste Values): one header row, one row per record, no blank "
    "rows, no merged cells. Paste only the columns that hold data, not the ones that hold "
    "formulas: you rebuild those in step 4.",
    "2. Click inside it, press Ctrl+T and tick \"My table has headers\". If the data was already "
    "in a Table, keep that Table's name; if you know the database table it comes from, use "
    "that name. Otherwise any name will do, with no spaces (Table Design > Table Name; on older "
    "Excel, Design under Table Tools). Copilot keeps the names you give, and marks any it "
    "can't match to a database table for you to fill in.",
    "3. Do steps 1 and 2 for every table of raw data before going on.",
    "Your calculations:",
    "4. Add a column to a Table for each calculation, and write its formula once, in the first "
    "row. Click a cell in the same row rather than typing its address, and Excel writes it by "
    "column name, such as =[@units]*[@price]. Excel fills the formula down the column.",
    "5. A calculation that reads another Table, such as an XLOOKUP or a SUMIFS, is written the "
    "same way, naming the other Table: =XLOOKUP([@product_id], products[product_id], "
    "products[name]). A summary of totals, such as a block of SUMIFS cells or a PivotTable, is "
    "rebuilt as a Table of its own: a column for what it groups by, one row per group, and a "
    "SUMIFS column for each figure.",
    "6. Move each fixed value a formula uses into the Parameters Table, one row a value, whether "
    "it was typed in a cell such as $B$3 or inside a formula such as *0.2, and read it by name: "
    "=XLOOKUP(\"tax_rate\", Parameters[name], Parameters[value]).",
    "7. Power Query, if you use it, can do a calculation instead of a formula: Data > From "
    "Table/Range, make the changes in the Power Query Editor, then Close & Load to a new Table. "
    "Copilot reads its steps, and the new Table converts like any other. Skip this step if you "
    "don't use Power Query.",
    "8. A formula that reads the row above, such as a running total, or a cell outside a Table, "
    "can't be read as SQL: Copilot names it and leaves its column empty for you to finish.",
    "Before you hand it over:",
    "9. Take out anything you don't want converted: a Table, a column, a value typed over a "
    "formula. Whatever is left in a Table converts.",
    "10. A value someone typed over a formula in one row is converted as it is, for that row. "
    "Find each in the original workbook (Ctrl+` shows formulas, so a typed value stands out) "
    "and type it over the formula in the same row here. Then add a row to the Keys Table: the "
    "Table's name under table, and under key_columns the column or columns that tell its "
    "rows apart, separated by commas: job_runs and run_id, or sales and region, month. A "
    "Table with no value typed over a formula needs no row in Keys.",
    "11. Charts and anything outside a Table are left alone, and Copilot names them. Titles "
    "and notes can stay.",
    "12. Save the workbook, attach it in a Copilot chat with Copilot file 11 loaded (with files "
    "03, 04 and 05), and ask Copilot to convert it.",
)
# The Tables whose headers are fixed, each on a sheet of its own name.
TABLES = {"Parameters": ("name", "value"), "Keys": ("table", "key_columns")}
# What a person sees in a workbook, sheet by sheet: its cells' values by place, and each of
# its Tables' places.
Contents = dict[str, dict[str, dict[str, object]]]


def empty_workbook() -> openpyxl.Workbook:
    """The empty Formula workbook, as this builds it."""
    workbook = openpyxl.Workbook()
    steps = workbook.active
    steps.title = "Steps"
    steps.column_dimensions["A"].width = 100
    for row, paragraph in enumerate(STEPS, 1):
        cell = steps.cell(row=row, column=1, value=paragraph)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        if row == 1 or paragraph.endswith(":"):
            cell.font = Font(bold=True, size=14 if row == 1 else 11)
    for name, headers in TABLES.items():
        sheet = workbook.create_sheet(name)
        for column, header in enumerate(headers, 1):
            sheet.cell(row=1, column=column, value=header)
            sheet.column_dimensions[get_column_letter(column)].width = 24
        # Excel needs a row under the headers, left empty here.
        table = Table(displayName=name, ref=f"A1:{get_column_letter(len(headers))}2")
        table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
        sheet.add_table(table)
    return workbook


def contents(workbook: openpyxl.Workbook) -> Contents:
    """What a person sees in a workbook: each sheet's cells by place, and each Table's place."""
    return {sheet.title: {"cells": {cell.coordinate: cell.value for row in sheet.iter_rows()
                                    for cell in row if cell.value is not None},
                          "tables": {name: sheet.tables[name].ref for name in sheet.tables}}
            for sheet in workbook.worksheets}


# --- A filled-in Formula workbook, for the Copilot evaluation --------------------------------


@dataclass(frozen=True)
class ExcelTable:
    """One Excel Table of a filled-in Formula workbook, on a sheet of its own name.

    Its columns are `headers`, in order: each one `formulas` names is calculated, by that
    formula as a person types it (`=[@duration_mins]/60`), and the rest are typed, their rows
    the rows `rows`, Hive, gives on the Example database, column by column. `typed_over` holds
    each value typed over a formula, by the row's first typed value and the column's header.
    `loaded_by` names the Power Query that loads the Table, if one does."""

    name: str
    headers: tuple[str, ...]
    rows: str = ""
    formulas: dict[str, str] = field(default_factory=dict)
    typed_over: dict[tuple[object, str], object] = field(default_factory=dict)
    loaded_by: str = ""


@dataclass(frozen=True)
class FormulaWorkbook:
    """A filled-in Formula workbook: its Tables; its Parameters and Keys rows; its Power
    Queries, each (name, M); its defined names, each (name, what it refers to); cells outside
    any Table, each (sheet, cell, value); whether a sheet holds a chart; notes on what openpyxl
    can't write, such as a PivotTable; and whether its text shows each formula as a person types
    it (`[@units]`) or as the file holds it (`sales[[#This Row],[units]]`)."""

    tables: tuple[ExcelTable, ...]
    parameters: tuple[tuple[str, object], ...] = ()
    keys: tuple[tuple[str, str], ...] = ()
    queries: tuple[tuple[str, str], ...] = ()
    defined_names: tuple[tuple[str, str], ...] = ()
    cells: tuple[tuple[str, str, object], ...] = ()
    chart: bool = False
    notes: tuple[str, ...] = ()
    as_typed: bool = False


# Excel's newer functions, which its file holds with the _xlfn. prefix Excel adds.
NEWER = re.compile(r"(?<![\w.])(XLOOKUP|XMATCH|SWITCH|IFS|MAXIFS|MINIFS|CONCAT|TEXTJOIN|LET|"
                   r"LAMBDA|RANDARRAY)\(")
THIS_ROW = re.compile(r"\[@(\[[^\]]+\]|[^\[\]]+)\]")
HELD_THIS_ROW = re.compile(r"\w+\[\[#This Row\],(\[[^\]]+\])\]")


def as_held(formula: str, table: str) -> str:
    """A formula as a workbook's file holds it: `[@units]` in Table sales written out as
    `sales[[#This Row],[units]]`, and each newer function with its `_xlfn.` prefix."""
    def this_row(found: re.Match[str]) -> str:
        column = found.group(1)
        return f"{table}[[#This Row],{column if column.startswith('[') else f'[{column}]'}]"
    return NEWER.sub(r"_xlfn.\1(", THIS_ROW.sub(this_row, formula))


def as_typed(formula: str) -> str:
    """A formula as a person types it, and Excel's formula bar shows it: the reverse of
    `as_held`."""
    def this_row(found: re.Match[str]) -> str:
        column = found.group(1)[1:-1]
        return f"[@{column}]" if re.fullmatch(r"\w+", column) else f"[@[{column}]]"
    return HELD_THIS_ROW.sub(this_row, formula.replace("_xlfn.", ""))


def _cell_value(value: object) -> object:
    """A value from the Example database as a cell holds it: a plain number or text, or None
    for a blank cell."""
    if value is None or value != value:  # None, or a missing number
        return None
    return value.item() if hasattr(value, "item") else value


def build(described: FormulaWorkbook) -> openpyxl.Workbook:
    """The filled-in Formula workbook `described` describes: a copy of the empty one."""
    workbook = empty_workbook()
    for title, rows in (("Parameters", described.parameters), ("Keys", described.keys)):
        sheet = workbook[title]
        for number, row in enumerate(rows, 2):
            for column, value in enumerate(row, 1):
                sheet.cell(row=number, column=column, value=value)
        sheet.tables[title].ref = f"A1:B{max(len(rows), 1) + 1}"
    for described_table in described.tables:
        _add_table(workbook, described_table)
    for name, refers_to in described.defined_names:
        workbook.defined_names[name] = DefinedName(name, attr_text=as_held(refers_to, ""))
    for title, coordinate, value in described.cells:
        sheet = workbook[title] if title in workbook.sheetnames else workbook.create_sheet(title)
        sheet[coordinate] = as_held(value, "") if isinstance(value, str) else value
    if described.chart:
        _add_chart(workbook, workbook[described.tables[0].name])
    return workbook


def _add_table(workbook: openpyxl.Workbook, described: ExcelTable) -> None:
    """One Excel Table on a sheet of its own: its headers, then a row for each of its sample
    rows, each calculated column holding its formula, or the value typed over it."""
    # Only a filled-in workbook reads the Example database: the empty one, which
    # copilot_files.py builds, needs nothing of the Toolbox's.
    from sqlglot_composer import example_database

    sheet = workbook.create_sheet(described.name)
    typed = [header for header in described.headers if header not in described.formulas]
    rows = (example_database.query(described.rows).itertuples(index=False)
            if described.rows else [])
    for column, header in enumerate(described.headers, 1):
        sheet.cell(row=1, column=column, value=header)
    count = 0
    for count, row in enumerate(rows, 1):
        values = dict(zip(typed, (_cell_value(value) for value in row), strict=True))
        first = values[typed[0]] if typed else count
        for column, header in enumerate(described.headers, 1):
            if header in values:
                value = values[header]
            else:
                value = described.typed_over.get(
                    (first, header), as_held(described.formulas[header], described.name))
            sheet.cell(row=count + 1, column=column, value=value)
    last = get_column_letter(len(described.headers))
    sheet.add_table(Table(displayName=described.name, ref=f"A1:{last}{max(count, 1) + 1}"))


def _add_chart(workbook: openpyxl.Workbook, sheet: openpyxl.worksheet.worksheet.Worksheet
               ) -> None:
    """A bar chart of `sheet`'s first column, on the Summary sheet."""
    chart = BarChart()
    chart.add_data(Reference(sheet, min_col=1, min_row=1, max_row=sheet.max_row),
                   titles_from_data=True)
    summary = (workbook["Summary"] if "Summary" in workbook.sheetnames
               else workbook.create_sheet("Summary"))
    summary.add_chart(chart, "F2")


def _shown(value: object, typed: bool) -> str:
    """A cell's value as text: a formula as held or typed, a whole number with no `.0`."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).upper()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, str) and value.startswith("=") and typed:
        return as_typed(value)
    return str(value)


def as_text(described: FormulaWorkbook) -> str:
    """What Copilot reads in the filled-in Formula workbook `described`, read back from the file
    `build` saves: each sheet's Tables, row by row, and its other cells and charts, then the
    Power Queries, the defined names, and the notes."""
    saved = io.BytesIO()
    build(described).save(saved)
    workbook = openpyxl.load_workbook(io.BytesIO(saved.getvalue()))
    loaded = {table.name: table.loaded_by for table in described.tables if table.loaded_by}
    lines = []
    for sheet in workbook.worksheets:
        if sheet.title == "Steps":
            lines.append('Sheet "Steps": the empty Formula workbook\'s steps, as it ships.')
            continue
        lines.append(f'Sheet "{sheet.title}"')
        in_a_table = set()
        for table in sheet.tables.values():
            name = table.displayName
            by = f', loaded by Power Query "{loaded[name]}"' if name in loaded else ""
            lines.append(f'  Excel Table "{name}", {table.ref}{by}')
            for number, row in enumerate(sheet[table.ref], 1):
                in_a_table |= {cell.coordinate for cell in row}
                shown = " | ".join(_shown(cell.value, described.as_typed) for cell in row)
                lines.append(f"    {'Headers' if number == 1 else f'Row {number}'}: {shown}")
        for row in sheet.iter_rows():
            for cell in row:
                if cell.coordinate not in in_a_table and cell.value is not None:
                    lines.append(f"  {cell.coordinate}: "
                                 f"{_shown(cell.value, described.as_typed)}")
        lines += ["  A bar chart" for _ in sheet._charts]
    loads = {by: table for table, by in loaded.items()}
    for name, m in described.queries:
        to = f'loads into Excel Table "{loads[name]}"' if name in loads else "connection only"
        lines.append(f'Power Query "{name}" ({to}):')
        lines += [f"    {line}" for line in m.strip().splitlines()]
    for name, defined in workbook.defined_names.items():
        lines.append(f"Defined name {name}: "
                     f"{_shown('=' + defined.attr_text, described.as_typed)[1:]}")
    lines += [f"Also in the workbook: {note}" for note in described.notes]
    return "\n".join(lines) + "\n"


def main() -> int:
    """Write the empty Formula workbook into copilot/, unless it already holds what this
    builds: a new build differs in its bytes, its zip's times, though nothing in it does."""
    built = empty_workbook()
    if EMPTY.exists() and contents(openpyxl.load_workbook(EMPTY)) == contents(built):
        print(f"{EMPTY.relative_to(ROOT).as_posix()} is up to date.")
        return 0
    built.save(EMPTY)
    print(f"Wrote {EMPTY.relative_to(ROOT).as_posix()}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

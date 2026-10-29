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
"""

from __future__ import annotations

import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parent.parent
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
    "Table's name, and the column or columns that tell its rows apart, separated by commas, "
    "such as job_runs | run_id, or sales | region, month. A Table with no value typed over a "
    "formula needs no row in Keys.",
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


def main() -> int:
    """Write the empty Formula workbook into copilot/."""
    empty_workbook().save(EMPTY)
    print(f"Wrote {EMPTY.relative_to(ROOT).as_posix()}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

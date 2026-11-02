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
something to half-edit and forget. Filled-in examples are files of their own, in
`copilot/examples/`, which `tools/formula_workbook_examples.py` builds.

It and the examples beside it are the files main ships but can't rebuild: openpyxl, which
writes them, is pinned in requirements-dev.txt only, and the export copies them as dev holds
them.

The Copilot evaluation's Excel tasks (`tools/excel_eval_tasks.py`) describe filled-in Formula
workbooks, `FormulaWorkbook`: `build` makes one, a copy of the empty one with each Table's
sample rows read from the Example database, and `as_text` writes what Copilot reads in it, read
back from the saved file, for a proxy model, which can't be given a file. openpyxl writes no
Power Query and no PivotTable, so a workbook's queries are given as their M, and anything else
it can't write as a note, both in the text alone.
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
from openpyxl.worksheet.filters import AutoFilter
from openpyxl.worksheet.table import Table, TableColumn, TableFormula, TableStyleInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT)]
sys.path[:0] = [str(ROOT / "copilot"), str(ROOT / "tools")]

import excel_queries  # noqa: E402
import workbook_text  # noqa: E402

EMPTY = ROOT / "copilot" / "formula_workbook.xlsx"

# The steps sheet, one paragraph a row. A heading is a line that ends with a colon.
STEPS = (
    "Formula workbook: how to fill it in",
    "Copilot reads this workbook and writes Hive, the SQL your team's database runs, without "
    "anyone explaining what the workbook is for. Make a copy of this file for each piece of "
    "work, then do steps 1 to 12 below in order. Each step says its goal, what to do, and when "
    "it is done; go to the next step only then.",
    "Words used here:",
    "Table: an Excel Table, made with Ctrl+T, with a name and one header row. Copilot converts "
    "only what is inside a Table.",
    "Raw data: the records the work starts from, as values, with no formula in them.",
    "Calculation: a value worked out from others, by a formula or by a Power Query step.",
    "Typed column: a column whose cells hold values someone typed, not formulas, such as "
    "run_id. Not the same as a typed-over value.",
    "Typed-over value: a value someone typed into one row of a column that holds a formula, in "
    "place of the formula.",
    "Copilot files: the numbered text files in the copilot folder this workbook came from. "
    "Loaded in a Copilot chat, they tell Copilot how to convert your workbook.",
    "M: a Power Query's text, which its Advanced Editor shows (step 7).",
    "The Parameters and Keys sheets:",
    "Parameters holds the fixed values your formulas use, such as a tax rate: one row each, "
    "its name under name and its value under value (step 6). Keys is only for a Table where a "
    "value was typed over a formula: it names the columns that tell that Table's rows apart, "
    "so Copilot can find the row the typed value belongs to (step 10). Both start empty: leave "
    "a sheet empty when no step asks you to fill it in.",
    "Your data:",
    "1. Paste one table of raw data. Goal: a sample of the data the work starts from, as plain "
    "values. Action: paste a sample of one table of raw data on a sheet of its own, as values "
    "only (Home > Paste > Paste Values): one header row, one row per record, no blank rows, no "
    "merged cells. Paste only the columns that hold data; you rebuild the columns that hold "
    "formulas in step 4. Done when the sheet holds the header row and the sample's rows, and "
    "nothing else. Then step 2.",
    "2. Make it a named Table. Goal: a Table Copilot can read by name. Action: click inside "
    "the sample, press Ctrl+T and tick \"My table has headers\". Then set its name in Table "
    "Design > Table Name (on older Excel, Design under Table Tools), by the first of the three "
    "rules below that fits. Copilot keeps the names you give, and marks any it can't match to "
    "a database table for you to fill in. Done when the Table has its name. Then step 3.",
    "If the data was already in a Table: keep that Table's name.",
    "If you know the database table it comes from: use the part of its name after the dot, "
    "such as job_runs for ops.job_runs. Then right-click the row number of the header row, "
    "choose Insert to add a row above it, and type there where it came from, such as "
    "\"Copied from ops.job_runs\".",
    "Otherwise: give it any name, with no spaces.",
    "3. Repeat for each table of raw data. Goal: all the raw data in Tables. Action: do steps "
    "1 and 2 for every other table of raw data the work starts from. Done when each one is a "
    "named Table on a sheet of its own. Then step 4.",
    "Your calculations:",
    "4. Add each calculation on a row as a column. Goal: each calculation written once, by "
    "column name. Action: add a column to a Table for each calculation, and write its formula "
    "once, in the first row. Click a cell in the same row rather than typing its address, and "
    "Excel writes it by column name, such as =[@units]*[@price]. Excel fills the formula down "
    "the column. If you see it written as =sales[[#This Row],[units]]*sales[[#This "
    "Row],[price]], it is the same formula. Done when each calculation on a Table's own row "
    "has its column. Then step 5.",
    "5. Add each calculation that reads another Table, each summary and each total. Goal: "
    "every other calculation in a Table, by name. Action: write a calculation that reads "
    "another Table, such as an XLOOKUP or a SUMIFS, the same way, naming the other Table: "
    "=XLOOKUP([@product_id], products[product_id], products[name]). Rebuild a summary of "
    "totals, such as a block of SUMIFS cells or a PivotTable, as a Table of its own: a column "
    "for what it groups by, one row per group, and a column for each figure: SUMIFS for a "
    "total, COUNTIFS for a count, AVERAGEIFS for an average, MAXIFS for the largest, MINIFS "
    "for the smallest. To total any Table, raw or summary, turn on its Total Row (Table "
    "Design > Total Row) and pick each column's total from the list in its last row: Copilot "
    "reads a total typed as a row of its own as one more row of data. Done when each summary "
    "is a Table of its own and each total is in a Total Row. Then step 6.",
    "6. Move each fixed value into Parameters. Goal: every fixed value in one place, read by "
    "name. Action: add each fixed value a formula uses to the Parameters Table, one row per "
    "value, whether it was typed in a cell such as $B$3 or inside a formula such as *0.2, and "
    "change the formula to read it by name: =XLOOKUP(\"tax_rate\", Parameters[name], "
    "Parameters[value]). Write a value as a plain number or text: 0.2, not 20%. Done when each "
    "formula reads its fixed values from Parameters. Then step 7.",
    "7. Use Power Query for a calculation, if you use Power Query. If you don't, go to step 8. "
    "Goal: a calculation done by Power Query in place of a formula, reading your Tables. "
    "Action: copy each query's M from your original workbook: Data > Queries & Connections, "
    "right-click the query, Edit, then Home > Advanced Editor. Here, add it: Data > Get Data "
    "> From Other Sources > Blank Query, Home > Advanced Editor, paste the M, and change the "
    "line that reads its source to read your Table by name, such as Source = "
    "Excel.CurrentWorkbook(){[Name=\"job_runs\"]}[Content]. Name the query for the Table it "
    "makes, then Home > Close & Load To > Table. Example 03, examples/03_power_query.xlsx in "
    "the copilot folder this workbook came from, shows two. Copilot reads the query's steps, "
    "and the Table it loads converts like any other. If your Excel can't add a query: on a "
    "sheet named Power Query, type Query <its name>: in a cell and paste its M in the cell "
    "below, then type the rows it gives into a Table of its name. Done when each query is "
    "loaded to a Table of its name, or its M is on the Power Query sheet and its rows are "
    "typed into a Table of its name. Then step 8.",
    "8. Write running totals with SUMIFS. Goal: formulas Copilot can read as SQL. Action: "
    "write a running total as =SUMIFS(t[v], t[d], \"<=\"&[@d]), which Copilot can read. A "
    "formula that reads the row above, or a cell outside a Table, can't be read as SQL: "
    "Copilot names it and leaves its column empty for you to finish. Done when each running "
    "total is written with SUMIFS. Then step 9.",
    "Before you hand it over:",
    "9. Take out what you don't want converted. Goal: only what you want converted left in a "
    "Table. Action: delete anything you don't want converted: a Table, or a column. Keep each "
    "typed-over value you want kept: step 10 is for those. Whatever is left in a Table "
    "converts. Done when each Table holds only what you want converted. Then step 10.",
    "10. Put back each typed-over value and name its Table in Keys. If no value was typed over "
    "a formula, go to step 11: a Table with no value typed over a formula needs no row in "
    "Keys. Goal: each typed-over value converted as it is, for its row. Action: find each in "
    "the original workbook (Ctrl+` shows formulas, so a typed value stands out) and type it "
    "over the formula in the same row here, making sure your sample holds that row. Then add "
    "one row to the Keys Table for that Table, however many values were typed over in it: the "
    "Table's name under table, and under key_columns the typed column or columns that tell its "
    "rows apart, separated by commas. For example, job_runs with run_id; or sales with region, "
    "month. If no column tells the rows apart, leave the Table out of Keys: Copilot then "
    "matches the row on all its typed columns. Done when each typed-over value is in its row "
    "here, and each Table that holds one has its row in Keys or has no column that tells its "
    "rows apart. Then step 11.",
    "11. Keep each calculation you want converted inside a Table. Goal: nothing you want "
    "converted left outside a Table. Action: move into a Table any calculation still outside "
    "one. Copilot leaves charts and anything outside a Table alone, and names them; titles "
    "and notes can stay. Done when every calculation you want converted is inside a Table. "
    "Then step 12.",
    "12. Hand it on. Goal: the Hive for your workbook. Action: go through the checks below, "
    "then save the workbook. If someone else converts it for you, such as your data team, "
    "send it to them: the rest of this step is theirs. Else attach it in a Copilot chat with "
    "Copilot files 15, 11 and 12 loaded, and ask Copilot to convert it. If you can run "
    "Python, first run workbook_text.py, in the copilot folder, on this workbook: it writes "
    "a .txt of the same name beside it, which you attach in place of the workbook. The "
    "README's section on handing over an Excel workbook says how. Done when Copilot replies "
    "with the Hive for your workbook, or the workbook is sent.",
    "Check before you hand it on:",
    "Each table of raw data is a named Table on a sheet of its own, with one header row.",
    "Each calculation is a formula column in a Table, a Power Query loaded to a Table, a "
    "summary Table or a Total Row.",
    "Each fixed value a formula uses is a row in Parameters, written as a plain number or "
    "text.",
    "Each Table that holds a typed-over value has its row in Keys, or has no column that tells "
    "its rows apart.",
    "Nothing you don't want converted is left in a Table.",
)
# The Tables whose headers are fixed, each on a sheet of its own name.
TABLES = {"Parameters": ("name", "value"), "Keys": ("table", "key_columns")}
# What each of those Tables is for, beside it on its sheet, for someone who opens the sheet
# before reading the steps.
NOTES = {
    "Parameters": "Parameters: the fixed values your formulas use, one row per value. Put its "
                  "name under name and the value under value, such as tax_rate and 0.2 (a "
                  "plain number, not 20%), then read it by name in a formula: "
                  "XLOOKUP(\"tax_rate\", Parameters[name], Parameters[value]). Leave the Table "
                  "empty if no formula uses a fixed value. See step 6 on the Steps sheet.",
    "Keys": "Keys: only for a Table where a value was typed over a formula. Add one row for "
            "that Table, however many values were typed over in it: the Table's name under "
            "table, and under key_columns the typed column or columns that tell its rows "
            "apart, separated by commas, such as job_runs with run_id, or sales with region, "
            "month. Copilot uses them to find the row a typed value belongs to. If no column "
            "tells the rows apart, leave the Table out. A Table with no value typed over a "
            "formula needs no row here. See step 10 on the Steps sheet.",
}
# What a person sees in a workbook, sheet by sheet: its cells' values by place, and each of
# its Tables' places, as `declared` gives them.
Contents = dict[str, dict[str, dict[str, object]]]
# Each function a Total Row offers, by the SUBTOTAL code its cell holds: 109 adds up the column.
SUBTOTAL_CODES = {"average": 101, "countNums": 102, "count": 103, "max": 104, "min": 105,
                  "stdDev": 107, "sum": 109, "var": 110}


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
        table = new_table(name, headers, 1)
        table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
        sheet.add_table(table)
        # A column apart from the Table, so a row added to it never reaches the note.
        note = sheet.cell(row=1, column=len(headers) + 2, value=NOTES[name])
        note.alignment = Alignment(wrap_text=True, vertical="top")
        sheet.column_dimensions[note.column_letter].width = 60
    return workbook


def new_table(name: str, headers: tuple[str, ...], rows: int,
              totals: dict[str, str] | None = None) -> Table:
    """Table `name`, its `headers` over `rows` rows, then a Total Row if `totals` gives one, by
    header, declared as Excel declares one: Excel opens a Table whose Total Row its columns
    don't declare, or whose filter reaches into it, as a file to repair, and drops the Table."""
    last = get_column_letter(len(headers))
    table = Table(displayName=name, ref=f"A1:{last}{rows + 1 + bool(totals)}",
                  autoFilter=AutoFilter(ref=f"A1:{last}{rows + 1}"),
                  tableColumns=[TableColumn(id=number, name=header)
                                for number, header in enumerate(headers, 1)])
    if totals:
        table.totalsRowCount = 1
        for column in table.tableColumns:
            value = totals.get(column.name)
            if value is None:
                continue
            if not value.startswith("="):
                column.totalsRowLabel = value
                continue
            column.totalsRowFunction = _total_row_function(value, name, column.name)
            if column.totalsRowFunction == "custom":
                column.totalsRowFormula = TableFormula(attr_text=value[1:])
    return table


def _total_row_function(formula: str, table: str, column: str) -> str:
    """The function a Total Row cell's formula is, by its name in `SUBTOTAL_CODES`, or "custom"
    for a formula that is none of them."""
    for function, code in SUBTOTAL_CODES.items():
        if formula == f"=SUBTOTAL({code},{table}[{column}])":
            return function
    return "custom"


def declared(table: Table) -> tuple[object, ...]:
    """A Table as its file declares it: its place, its filter's, and each column's name and
    Total Row label, function or formula."""
    return (table.ref, table.autoFilter.ref if table.autoFilter else None,
            tuple((column.name, column.totalsRowLabel, column.totalsRowFunction,
                   column.totalsRowFormula.attr_text if column.totalsRowFormula else None)
                  for column in table.tableColumns))


def contents(workbook: openpyxl.Workbook) -> Contents:
    """What a person sees in a workbook: each sheet's cells by place, and each Table as its file
    declares it."""
    by_sheet: Contents = {}
    for sheet in workbook.worksheets:
        cells = {}
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is not None:
                    cells[cell.coordinate] = cell.value
        tables = {name: declared(sheet.tables[name]) for name in sheet.tables}
        by_sheet[sheet.title] = {"cells": cells, "tables": tables}
    return by_sheet


# --- A filled-in Formula workbook, for the Copilot evaluation --------------------------------


@dataclass(frozen=True)
class ExcelTable:
    """One Excel Table of a filled-in Formula workbook, on a sheet of its own name.

    Its columns are `headers`, in order: each one `formulas` names is calculated, by that
    formula as a person types it (`=[@duration_mins]/60`), and the rest are typed, their rows
    the rows `rows`, Hive, gives on the Example database, column by column. `typed_over` holds
    each value typed over a formula, by the row's first typed value and the column's header.
    `loaded_by` names the Power Query that loads the Table, if one does. `totals` is its Total
    Row, if it has one: each cell's value or formula, as the file holds it, by header."""

    name: str
    headers: tuple[str, ...]
    rows: str = ""
    formulas: dict[str, str] = field(default_factory=dict)
    typed_over: dict[tuple[object, str], object] = field(default_factory=dict)
    loaded_by: str = ""
    totals: dict[str, str] = field(default_factory=dict)


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
NEWER = re.compile(r"(?<![\w.])(XLOOKUP|XMATCH|SWITCH|IFS|MAXIFS|MINIFS|RANK\.EQ|STDEV\.S|"
                   r"VAR\.S|CONCAT|TEXTJOIN|LET|LAMBDA|RANDARRAY)\(")
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
        if title not in workbook.sheetnames:
            workbook.create_sheet(title)
        sheet = workbook[title]
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
    count = max(count, 1)
    if described.totals:
        total_row = count + 2  # under the headers and the rows
        for column, header in enumerate(described.headers, 1):
            sheet.cell(row=total_row, column=column, value=described.totals.get(header))
    sheet.add_table(new_table(described.name, described.headers, count, described.totals))


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


def row_label(table: Table, number: int, count: int) -> str:
    """How the text names row `number` of a Table of `count` rows: its headers, a row of
    values, or its Total Row."""
    if number == 1:
        return "Headers"
    if table.totalsRowCount and number == count:
        return "Total Row"
    return f"Row {number}"


def built(described: FormulaWorkbook) -> bytes:
    """The file `build` saves of the filled-in Formula workbook `described`, which holds no
    Power Query: openpyxl writes none."""
    held = io.BytesIO()
    build(described).save(held)
    return held.getvalue()


def saved(described: FormulaWorkbook) -> bytes:
    """The filled-in Formula workbook `described`, saved as Excel saves it: the file `built`
    gives, then its Power Queries saved in it, each loading the Table it loads."""
    if not described.queries:
        return built(described)
    loads = {table.loaded_by: table.name for table in described.tables if table.loaded_by}
    return excel_queries.with_queries(built(described), list(described.queries), loads)


def as_text(described: FormulaWorkbook) -> str:
    """What Copilot reads in the filled-in Formula workbook `described`: the text
    `copilot/workbook_text.py` writes of the file `saved` gives, formulas as the workbook's
    `as_typed` says, then the notes."""
    text = workbook_text.workbook_text(saved(described), typed=described.as_typed)
    return text + "".join(f"Also in the workbook: {note}\n" for note in described.notes)


def openpyxl_text(described: FormulaWorkbook) -> str:
    """The same workbook's text, as openpyxl reads the file `build` saves, its queries and
    their Tables from `described`, with no order: the view the script's tests hold it to."""
    workbook = openpyxl.load_workbook(io.BytesIO(built(described)))
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
            rows = sheet[table.ref]
            for number, row in enumerate(rows, 1):
                in_a_table |= {cell.coordinate for cell in row}
                shown = " | ".join(_shown(cell.value, described.as_typed) for cell in row)
                lines.append(f"    {row_label(table, number, len(rows))}: {shown}")
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

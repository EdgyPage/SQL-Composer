"""Fill in the Formula workbook copy for the Daily sheet, as its Steps sheet says.

Reads the team's from_your_team/daily_runs.xlsx (values and formulas), and writes
my_work/daily_runs_formula.xlsx, which is the copy of main/copilot/formula_workbook.xlsx.
"""
import openpyxl
from openpyxl.worksheet.table import Table, TableColumn, TableStyleInfo, AutoFilter
from openpyxl.styles import Alignment

RUN = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-E3-3"
SOURCE = f"{RUN}/from_your_team/daily_runs.xlsx"
TARGET = f"{RUN}/my_work/daily_runs_formula.xlsx"

src = openpyxl.load_workbook(SOURCE)
wb = openpyxl.load_workbook(TARGET)


def style(table_name, ref, auto_ref):
    t = Table(displayName=table_name, ref=ref)
    t.autoFilter = AutoFilter(ref=auto_ref)
    t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    return t


# 1 and 2. The raw data, values only, as a Table named for the database table it copies.
raw = src["Raw"]
ws = wb.create_sheet("job_runs")
for row in raw.iter_rows(min_row=1, max_row=10, min_col=1, max_col=6):
    for c in row:
        ws.cell(row=c.row, column=c.column, value=c.value)
ws["H1"] = raw["H1"].value  # the team's note, outside the Table
ws.add_table(style("job_runs", "A1:F10", "A1:F10"))

# 7. The Power Query "CleanRuns": its rows are typed in here, as the example workbooks do,
# because openpyxl can't save a query. Its M is kept on the Power Query sheet.
clean = src["Clean"]
ws = wb.create_sheet("CleanRuns")
for row in clean.iter_rows(min_row=1, max_row=8, min_col=1, max_col=6):
    for c in row:
        ws.cell(row=c.row, column=c.column, value=c.value)
ws["H1"] = ('Loaded by the Power Query "CleanRuns" from job_runs: runs with no status, '
            'and test runs, left out.')
ws.add_table(style("CleanRuns", "A1:F8", "A1:F8"))

# 3 to 5. The Daily sheet rebuilt as a Table of its own: what it groups by (dt, typed),
# one row per group, a COUNTIFS and a SUMIFS column, and the Total Row.
ws = wb.create_sheet("daily")
ws["A1"], ws["B1"], ws["C1"] = "dt", "runs", "total_duration_mins"
for r, day in ((2, "2026-09-23"), (3, "2026-09-24")):
    assert src["Daily"][f"A{r}"].value == day
    ws[f"A{r}"] = day
    ws[f"B{r}"] = "=COUNTIFS(CleanRuns[dt],daily[[#This Row],[dt]])"
    ws[f"C{r}"] = "=SUMIFS(CleanRuns[duration_mins],CleanRuns[dt],daily[[#This Row],[dt]])"
ws["A4"] = "Total"
ws["B4"] = "=SUBTOTAL(109,daily[runs])"
ws["C4"] = "=SUBTOTAL(109,daily[total_duration_mins])"
ws["E1"] = "One row per day of the clean runs, and a Total Row."
daily = style("daily", "A1:C4", "A1:C3")
daily.totalsRowCount = 1
daily.tableColumns = [
    TableColumn(id=1, name="dt", totalsRowLabel="Total"),
    TableColumn(id=2, name="runs", totalsRowFunction="sum"),
    TableColumn(id=3, name="total_duration_mins", totalsRowFunction="sum"),
]
ws.add_table(daily)

# 7. The Power Query's steps, as text, for Copilot to read.
M = (
    "let\n"
    '    Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],\n'
    '    Typed = Table.TransformColumnTypes(Source, {{"run_id", Int64.Type}, {"job_id", Int64.Type},\n'
    '        {"status", type text}, {"duration_mins", Int64.Type}, {"dt", type text}}),\n'
    '    Kept = Table.SelectRows(Typed, each [status] <> null and [status] <> "TEST")\n'
    "in\n"
    "    Kept"
)
ws = wb.create_sheet("Power Query")
ws["A1"] = ("This workbook's Power Query, which the tool that made this file can't save in it, so "
            "the Table CleanRuns holds the rows the query gives, typed in. The query is the team's "
            'Power Query "CleanRuns", which read the sheet Raw; it now reads the Table job_runs, '
            "the same rows. To see the workbook as it should be, add the query in Excel: Data > Get "
            "Data > From Other Sources > Blank Query, Home > Advanced Editor, paste its M below, and "
            'name it CleanRuns. On the sheet CleanRuns, delete the typed-in Table (select it and '
            'press Delete, then delete the empty Table), then Home > Close & Load To > Table, at A1 of that sheet.')
ws["A1"].alignment = Alignment(wrap_text=True, vertical="top")
ws["A3"] = "Query CleanRuns:"
ws["A4"] = M
ws["A4"].alignment = Alignment(wrap_text=True, vertical="top")
ws.column_dimensions["A"].width = 110

# Put the sheets in order: the Steps sheet first, then the Parameters and Keys tables, then the data.
order = ["Steps", "Parameters", "Keys", "job_runs", "CleanRuns", "daily", "Power Query"]
wb._sheets = [wb[name] for name in order]
wb.active = 0

wb.save(TARGET)
print("saved", TARGET, wb.sheetnames)

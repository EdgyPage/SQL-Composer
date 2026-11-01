"""Fill in a copy of copilot/formula_workbook.xlsx with the team's daily_runs.xlsx.

Follows the Steps sheet: raw data as a named Table (job_runs), the team's Power Query
CleanRuns (its M kept on a Power Query sheet, its rows typed in as the example shows),
and the Daily summary rebuilt as a Table (daily) with a Total Row.
"""
import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo, TableColumn
from openpyxl.worksheet.filters import AutoFilter

BASE = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r19-E3-2"
TEMPLATE = BASE + "/main/copilot/formula_workbook.xlsx"
SOURCE = BASE + "/from_your_team/daily_runs.xlsx"
OUT = BASE + "/my_work/daily_runs_formula.xlsx"

STYLE = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)

src = openpyxl.load_workbook(SOURCE)
wb = openpyxl.load_workbook(TEMPLATE)

# ---- Step 1 to 2: the raw data, values only, as a named Table ----------------
raw_src = src["Raw"]
raw_rows = [list(r) for r in raw_src.iter_rows(min_row=1, max_row=raw_src.max_row,
                                               min_col=1, max_col=6, values_only=True)]
header = raw_rows[0]
data = [r for r in raw_rows[1:] if any(v is not None for v in r)]
assert header == ["run_id", "job_id", "status", "duration_mins", "avg_retry_secs", "dt"], header

raw = wb.create_sheet("job_runs")
# Step 2, second rule: the database table is ops.job_runs, so a row above the header
# says where it came from.
raw["A1"] = "Copied from ops.job_runs"
for c, name in enumerate(header, start=1):
    raw.cell(row=2, column=c, value=name)
for r, row in enumerate(data, start=3):
    for c, v in enumerate(row, start=1):
        raw.cell(row=r, column=c, value=v)
last_raw_row = 2 + len(data)
t_raw = Table(displayName="job_runs", ref=f"A2:F{last_raw_row}")
t_raw.tableStyleInfo = STYLE
raw.add_table(t_raw)

# ---- Step 7: the team's Power Query CleanRuns --------------------------------
# The M is kept as text on a Power Query sheet, its Raw read now as the Table job_runs.
pq_src = src["Power Query CleanRuns"]
m_lines = [r[0] for r in pq_src.iter_rows(min_row=2, max_row=pq_src.max_row, values_only=True)]
m_text = "\n".join(m_lines).replace('Excel.CurrentWorkbook(){[Name="Raw"]}',
                                     'Excel.CurrentWorkbook(){[Name="job_runs"]}')
assert 'Name="job_runs"' in m_text

# The rows the query gives, worked out from the raw rows by the query's own rule:
# status is not null and not TEST.
kept = [r for r in data if r[2] is not None and r[2] != "TEST"]
clean_src = src["Clean"]
clean_expected = [list(r) for r in clean_src.iter_rows(min_row=2, max_row=clean_src.max_row,
                                                       min_col=1, max_col=6, values_only=True)]
assert kept == clean_expected, "query rows do not match the team's Clean sheet"

clean = wb.create_sheet("CleanRuns")
for c, name in enumerate(header, start=1):
    clean.cell(row=1, column=c, value=name)
for r, row in enumerate(kept, start=2):
    for c, v in enumerate(row, start=1):
        clean.cell(row=r, column=c, value=v)
t_clean = Table(displayName="CleanRuns", ref=f"A1:F{1 + len(kept)}")
t_clean.tableStyleInfo = STYLE
clean.add_table(t_clean)

pq = wb.create_sheet("Power Query")
pq["A1"] = ("The Power Query CleanRuns, as the team wrote it, reading the Table job_runs now. "
            "The Table CleanRuns on its sheet holds the rows this query gives, typed in.")
pq["A3"] = "Query CleanRuns (loads the Table CleanRuns):"
pq["A4"] = m_text

# ---- Step 5: the Daily summary, rebuilt as a Table with a Total Row ----------
daily_src = src["Daily"]
days = [daily_src["A2"].value, daily_src["A3"].value]
assert days == ["2026-09-23", "2026-09-24"], days

daily = wb.create_sheet("Daily")
daily["A1"] = "dt"
daily["B1"] = "runs"
daily["C1"] = "total_duration_mins"
for i, d in enumerate(days, start=2):
    daily.cell(row=i, column=1, value=d)
    daily.cell(row=i, column=2,
               value="=COUNTIFS(CleanRuns[dt],daily[[#This Row],[dt]])")
    daily.cell(row=i, column=3,
               value="=SUMIFS(CleanRuns[duration_mins],CleanRuns[dt],daily[[#This Row],[dt]])")
total_row = 2 + len(days)  # row 4
daily.cell(row=total_row, column=1, value="Total")
daily.cell(row=total_row, column=2, value="=SUBTOTAL(109,daily[runs])")
daily.cell(row=total_row, column=3, value="=SUBTOTAL(109,daily[total_duration_mins])")
daily["E1"] = "One row per day of the clean runs, and a Total Row."

t_daily = Table(displayName="daily", ref=f"A1:C{total_row}", totalsRowCount=1)
t_daily.tableStyleInfo = STYLE
# Excel keeps the filter on the rows above the Total Row only.
t_daily.autoFilter = AutoFilter(ref=f"A1:C{total_row - 1}")
t_daily.tableColumns = [
    TableColumn(id=1, name="dt", totalsRowLabel="Total"),
    TableColumn(id=2, name="runs", totalsRowFunction="sum"),
    TableColumn(id=3, name="total_duration_mins", totalsRowFunction="sum"),
]
daily.add_table(t_daily)

# The Parameters and Keys sheets stay as the template has them: no fixed values in any
# formula, and no value typed over a formula.

wb.save(OUT)
print("saved", OUT)
print("sheets:", wb.sheetnames)

"""Fill in a copy of the Formula workbook for daily_runs.xlsx, as its Steps sheet says."""
import shutil
from pathlib import Path

import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo

WORK = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-E3-1")
TEMPLATE = WORK / "main" / "copilot" / "formula_workbook.xlsx"
TEAM = WORK / "from_your_team" / "daily_runs.xlsx"
OUT = WORK / "my_work" / "daily_runs_formula.xlsx"

STYLE = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)

# Step 0: make the copy of the empty Formula workbook.
shutil.copyfile(TEMPLATE, OUT)
wb = openpyxl.load_workbook(OUT)
team = openpyxl.load_workbook(TEAM)

# Steps 1 to 3: the raw data, as values only, one header row, its data columns only.
# Raw is a copy of ops.job_runs, so its Table takes that database table's name.
src = team["Raw"]
raw = wb.create_sheet("Raw")
for r in range(1, 11):
    for c in range(1, 7):
        raw.cell(row=r, column=c, value=src.cell(row=r, column=c).value)
raw["H1"] = src["H1"].value  # a note, outside the Table: notes can stay (step 11)
raw_table = Table(displayName="job_runs", ref="A1:F10")
raw_table.tableStyleInfo = STYLE
raw.add_table(raw_table)

# Step 7: the Power Query that loads Clean from Raw. Its Table, CleanRuns, is kept
# with the rows the query gives. The query now reads the Table job_runs.
src_clean = team["Clean"]
clean = wb.create_sheet("Clean")
for r in range(1, 9):
    for c in range(1, 7):
        clean.cell(row=r, column=c, value=src_clean.cell(row=r, column=c).value)
clean["H1"] = src_clean["H1"].value
clean_table = Table(displayName="CleanRuns", ref="A1:F8")
clean_table.tableStyleInfo = STYLE
clean.add_table(clean_table)

src_pq = team["Power Query CleanRuns"]
pq = wb.create_sheet("Power Query CleanRuns")
for r in range(1, 9):
    text = src_pq.cell(row=r, column=1).value
    if text is not None and 'Name="Raw"' in text:
        text = text.replace('Name="Raw"', 'Name="job_runs"')
    pq.cell(row=r, column=1, value=text)

# Step 5: the Daily sheet rebuilt as a Table of its own: a column for what it groups
# by (dt), one row per group, a COUNTIFS and a SUMIFS column, written by column name
# (step 4) rather than by cell address, and the Total Row kept as the sheet has it.
daily = wb.create_sheet("Daily")
daily["A1"] = "dt"
daily["B1"] = "runs"
daily["C1"] = "total_duration_mins"
daily["A2"] = "2026-09-23"
daily["A3"] = "2026-09-24"
daily["A4"] = "Total"
for r in (2, 3):
    daily[f"B{r}"] = "=COUNTIFS(CleanRuns[dt],daily_runs[[#This Row],[dt]])"
    daily[f"C{r}"] = "=SUMIFS(CleanRuns[duration_mins],CleanRuns[dt],daily_runs[[#This Row],[dt]])"
daily["B4"] = "=SUBTOTAL(109,daily_runs[runs])"
daily["C4"] = "=SUBTOTAL(109,daily_runs[total_duration_mins])"
daily["E1"] = src_daily_note = team["Daily"]["E1"].value
daily_table = Table(displayName="daily_runs", ref="A1:C4")
daily_table.tableStyleInfo = STYLE
daily.add_table(daily_table)

# Parameters and Keys stay empty: no formula reads a fixed value, and no value
# was typed over a formula.

wb.save(OUT)
print("saved", OUT)
print("sheets", wb.sheetnames)

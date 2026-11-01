"""Fill in a copy of the Formula workbook for the team's run_report.xlsx, as its Steps sheet says.

Steps followed:
  1-2  the Runs sheet's data, as values, on a sheet of its own; a row inserted above its header
       with "Copied from ops.job_runs"; the Table named job_runs (the part after the dot).
  4-5  the Report sheet's summary rebuilt as a Table of its own, run_report: a job_id column
       (typed groups), and a column for each figure with COUNTIFS / AVERAGEIFS over job_runs.
  6, 8, 10  nothing to add: no fixed value in a formula (FAILED is a criterion, kept inline, as
       in examples/02_summary_and_total_row.xlsx), no running total, no typed-over formula.
  7    no Power Query.
"""
import shutil
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.worksheet.table import Table, TableFormula, TableStyleInfo

WORK = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r20-E1-3")
TEMPLATE = WORK / "main" / "copilot" / "formula_workbook.xlsx"
SOURCE = WORK / "from_your_team" / "run_report.xlsx"
TARGET = WORK / "my_work" / "run_report_formula.xlsx"

STYLE = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)


def add_table(ws, name, ref, formulas=None):
    """Add an Excel Table; formulas maps a column name to its formula (the file's own spelling)."""
    table = Table(displayName=name, ref=ref)
    table.tableStyleInfo = STYLE
    ws.add_table(table)
    if formulas:
        # openpyxl names columns from the header cells only when it writes the file, so set
        # the names here too, to attach each calculated column's formula to the right one.
        table._initialise_columns()
        header_cells = ws[ref][0]
        for column, cell in zip(table.tableColumns, header_cells):
            column.name = str(cell.value)
            if column.name in formulas:
                column.calculatedColumnFormula = TableFormula(attr_text=formulas[column.name])
    return table


def main():
    if TARGET.exists():
        raise SystemExit(f"{TARGET} exists; remove it first")
    shutil.copy(TEMPLATE, TARGET)

    wb = load_workbook(TARGET)
    src = load_workbook(SOURCE)
    runs = src["Runs"]
    report = src["Report"]

    # Step 1-2: the raw data, values only, with a row inserted above its header.
    ws = wb.create_sheet("job_runs")
    ws["A1"] = "Copied from ops.job_runs"
    ws["A1"].font = Font(italic=True)
    data_rows = [
        [cell.value for cell in row[:6]]  # A:F hold the data; G is empty, H1 is a note
        for row in runs.iter_rows(min_row=1, max_row=runs.max_row)
    ]
    headers = data_rows[0]
    assert headers == ["run_id", "job_id", "status", "duration_mins", "avg_retry_secs", "dt"], headers
    for r, values in enumerate(data_rows, start=2):
        for c, value in enumerate(values, start=1):
            ws.cell(row=r, column=c, value=value)
    last_row = 1 + len(data_rows)
    for c, width in enumerate([10, 8, 10, 14, 15, 12], start=1):
        ws.column_dimensions[chr(ord("A") + c - 1)].width = width
    add_table(ws, "job_runs", f"A2:F{last_row}")

    # Step 4-5: the Report's summary, rebuilt as a Table of its own.
    rs = wb.create_sheet("run_report")
    rs_headers = [cell.value for cell in report[1][:4]]
    assert rs_headers == ["job_id", "runs", "failed_runs", "avg_duration_mins"], rs_headers
    for c, header in enumerate(rs_headers, start=1):
        rs.cell(row=1, column=c, value=header)
    groups = [report.cell(row=r, column=1).value for r in range(2, report.max_row + 1)
              if report.cell(row=r, column=1).value is not None]
    assert groups == [1, 2, 3], groups
    formulas = {
        "runs": "COUNTIFS(job_runs[job_id],run_report[[#This Row],[job_id]])",
        "failed_runs": ('COUNTIFS(job_runs[job_id],run_report[[#This Row],[job_id]],'
                        'job_runs[status],"FAILED")'),
        "avg_duration_mins": ("AVERAGEIFS(job_runs[duration_mins],"
                              "job_runs[job_id],run_report[[#This Row],[job_id]])"),
    }
    for r, group in enumerate(groups, start=2):
        rs.cell(row=r, column=1, value=group)
        for c, header in enumerate(rs_headers[1:], start=2):
            rs.cell(row=r, column=c, value="=" + formulas[header])
    # The team's note stays beside the Table, as the Steps sheet allows for notes.
    rs["F1"] = report["F1"].value
    for c, width in enumerate([10, 10, 14, 19], start=1):
        rs.column_dimensions[chr(ord("A") + c - 1)].width = width
    add_table(rs, "run_report", f"A1:D{1 + len(groups)}",
              formulas={h: formulas[h] for h in formulas})

    wb.calculation.fullCalcOnLoad = True
    wb.save(TARGET)
    print("saved", TARGET)


if __name__ == "__main__":
    main()

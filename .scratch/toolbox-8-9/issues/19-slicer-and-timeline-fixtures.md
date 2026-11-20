# The slicer and Timeline fixtures open in Excel

Type: task
Status: resolved
Blocked by: 02
Size: M

## Question

The user (2026-11-19), opening ticket 02's fixtures in Excel: `05_pivot_slicer_two_pivots.xlsx`
and `08_pivot_timeline_filters.xlsx` "are currupt". Ticket 02's Answer named 08, 05 and 10 as the
likeliest to need a repair: their slicer, Timeline and extension parts were written from
[MS-XLSX] without an Excel-saved file to compare against. The user will give Excel's repair log
for both and a small workbook saved in Excel with a pivot, a slicer and a Timeline, kept local in
`.eval-local/` (never committed).

## Done when

- `tools/pivot_tables.py` writes each part Excel's repair log names as Excel itself writes it,
  compared part by part with the user's Excel-saved sample.
- Fixtures 05 and 08 (and 10, which the user hasn't reported, checked against the sample too)
  regenerated; the reader's and the conversion's tests still pass on them.
- The user opens 05, 08 and 10 in Excel with no repair prompt: the ticket names what to look at.
- The sample is never committed; any committed fixture Excel saved, with its parts the offline
  policy reads, waits for the user's OK to an `ALLOWED` entry.

## Answer

Done 2026-11-20 (the user: "just do what you're waiting on me to do"), with Excel 16 on this
computer driven from PowerShell and VBScript (COM), so no repair log or sample was needed
from the user. With its alerts off Excel refuses a corrupt workbook rather than repair it, so
each fault was found by opening copies of the fixture, each with one thing changed, and
compared with a workbook Excel built and saved itself (a Table, a pivot, a slicer and a
Timeline: `.eval-local/excel-repair/sample_slicer_timeline.xlsx`, never committed). Excel's
parts matched the fixtures' in shape; two faults were elsewhere.

- **Two lists of defined names (05 and 08).** openpyxl writes an empty `<definedNames />`;
  `_finish_workbook` looked only for `</definedNames>`, so `Slicer_status` (05) and
  `NativeTimeline_dt` (08) went into a second list before `<calcPr>`, and Excel refuses a
  workbook with two. They now go into the one list.
- **A shared number field of whole values without `containsInteger` (08).** Its Report
  filter is on `avg_retry_secs`, whole numbers held as floats, and a blank. The flag was set
  only for Python ints; Excel sets it by value (its own saved sample of the same field says
  `containsInteger="1"`) and refuses the field without it. It is now set by value.

Fixtures 04 to 10 regenerated, and each opens in Excel, read-only, with no repair: 05 with
its two pivots and its slicer, 08 with its pivot and its Timeline, 10 with its three pivots.
Tests (`tests/test_pivot_tables.py`): one list of names for a slicer and for a Timeline, and
`containsInteger` for a shared number field of whole values with a blank.

**CI's two failures on 0d8957d6, the same tools.** `test_workbook_text`'s fixture 06 and
`test_example_projects`' `job_hours.xlsx` were built on Windows, where openpyxl writes a
sheet through a temporary text file, so a cell's `\n` (fixture 06's M on its Power Query
sheet) came out `\r\n`; CI builds on Linux, `\n`. `formula_workbook._as_excel_saves` now
saves each workbook's parts with `\n`, as Excel does
(`test_a_line_break_in_a_cell_is_saved_as_excel_saves_it_on_any_computer`); fixture 06 and
the intermediate Project's `job_hours.xlsx` were written again, and both tests pass with
`CI` set.

**Left.** Fixtures 01 to 03, the Power Query ones, are refused by Excel too, though no one had
reported them; the empty Formula workbook and the three Copilot examples open. Taking out
their query parts (the DataMashup, the connection, the query table) doesn't make 01 open, so
its fault is elsewhere: a ticket of its own.

**Against the Done-when lines.** The comparison was with a sample Excel built and saved on
this computer, not one the user saved, and no repair log was read (Excel with its alerts off
refuses rather than repairs); the faults came from bisecting instead, and only those two
parts are recorded. Fixtures 04, 06, 07 and 09 were written again too, by
`_as_excel_saves`, their content the same but each sheet's line breaks. The sample stays in
`.eval-local/excel-repair/`, git-ignored.

**For the user to look at, opening 05, 08 and 10 in Excel by hand** (COM opened them
read-only with alerts off, which may not show a prompt a double-click would): no "We found a
problem with some content" prompt; on 05's Pivot sheet, the status slicer with SUCCESS and
FAILED selected, both pivots filtered to them; on 08's Pivot sheet, the dt Timeline on
2026-09-24 and the avg_retry_secs Report filter; on 10's, its three pivots.

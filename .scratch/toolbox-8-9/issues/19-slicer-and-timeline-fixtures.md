# The slicer and Timeline fixtures open in Excel

Type: task
Status: open
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

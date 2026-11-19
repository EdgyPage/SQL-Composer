# Beginner reader, 2026-11-19: ticket 03's pivot text

Read: `copilot/workbook_text.py`'s docstring and the text it writes of a workbook with
PivotTables (`05_pivot_slicer_two_pivots.txt`, `08_pivot_timeline_filters.txt`), as a person
with Excel and pivot skills, not Python. Every cell checked by hand against the rows, the
slicer's selection, the hidden item and the Timeline's day: each describes its pivot right.
Advisory; the user decides what changes.

## Stops

1. **The docstring's sentence on cells** used "value" for both a cell's number and the Value
   field, in one sentence of a dozen parts.
2. **A Timeline's dates** were written with midnight times, the same day twice, where Excel
   shows a day; fixture 05 wrote its dates without a time.
3. **A % of Column Total cell** showed 0.625, where Excel shows 62.50%.
4. **A slicer connected to two pivots** is written under each: briefly read as two slicers,
   settled by "connected to PivotTable1, runs_by_day".
5. **The Order's last line**, "Each final's query reads the steps it needs as CTEs": "final"
   and "CTE" mean nothing to an Excel user. It predates ticket 03.

Plain as Excel says them: `Rows:`, `Columns:`, `Filter avg_retry_secs: (All)`, `Items hidden on
status: TEST`, `Totals shown: ...`, `Value "Sum of duration_mins": Sum of duration_mins`.

## Fixed, 2026-11-19 (96038be9)

- Stop 1: the sentence split in two, "Value" capitalised for the field.
- Stop 2: a date with no time of day written as its day, once when the first and last day
  are the same; date grouping's start and end too.
- Stop 3: Excel's percentage beside the stored number, `C5: 0.625 (62.50%; ...)`.

## Left, for the user

- Stop 4: the slicer is written under each pivot it filters, as the pivot's own filter.
- Stop 5: the line is for Copilot, which reads "final" and "CTE" in files 15, 11 and 12.

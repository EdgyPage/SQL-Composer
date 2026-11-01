# Beginner reader: how-to 15 and CHANGES 8.2 (ticket 09), 2026-11-01

Read: the diff to `worked_examples/how_to/15_rollups_and_subtotals.py` and the three new
`## 8.2` bullets in `CHANGES.md`.

## Stops

1. **`team_totals`' output, its `None` column.** The text had just said pandas shows NULL as
   NaN; the output shows `job_id` as `None`, and nothing said why (the column is NULL in every
   row, so pandas has no number type for it). **Stuck.**
2. **"A column of whole numbers with a NaN in it shows its numbers as 1.0, 2.0 ...".** Clear
   after one reread, but the line ran to 155 characters, unwrapped, and the next sentence
   ("report_build, job 3, counts for finance...") was stuck onto the pandas aside. **Reread.**
3. **"and the tables on this page as NULL".** The outputs show NaN or None, beside three ways
   of showing an empty value. **Reread.**
4. **"Pasted into your own notebook..." (lines 88-93).** Truthful: only the week and month
   calls stop. "The results here were worked out in pandas" could be read as covering the
   subtotals too. **Moment.**
5. **CHANGES, the Example database bullet.** A line break after "And a"; "as a value typed over
   a formula converts" hard to read. **Reread.**
6. **CHANGES, the types bullet.** "Decision" sent the reader to CONTEXT.md. **Moment.**

## What was changed

- 1 and 2: a paragraph of its own after the first output: pandas keeps NaN only among
  fractions, so whole numbers with a NaN show as 1.0, 2.0; a column NULL in every row shows
  None, as the next steps' job_id. report_build's sentence back with the subtotal paragraph.
- 3: "and the tables on this page as NULL" taken out.
- 4: "The week and month results were worked out in pandas".
- 5: the bullet rewrapped, and "which a Formula workbook's value typed over a formula converts
  to".
- 6: left: Decision is the glossary's word, which CHANGES uses throughout 8.1.

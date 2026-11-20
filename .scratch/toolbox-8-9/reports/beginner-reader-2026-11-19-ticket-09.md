# Beginner reader, 2026-11-19: ticket 09 (the Workbook check)

Run by the lead on Opus, reading as a person with Excel and pivot skills, over what ticket 09
first built (86c15012): convert's report and batch.md section for the Workbook check, and
`project.convert`'s docstring. It edited nothing. 6 stops. The reader's words are summarized
here, as the lead relayed them.

## Stops, and what changed for each

1. **`ABOUT`, the check's first sentence, had no verb** ("The Workbook check of runs.xlsx: each
   final's Hive run ..."). It said "final" without explaining it, and never said what a
   difference means or whose job it is. Now it reads "The Workbook check of runs.xlsx ran the
   Hive of each table the workbook gave, on this computer, over the workbook's own Tables, and
   compared its rows with the values the workbook shows, as last saved. A difference means the
   Hive doesn't give what the workbook's formula, query or PivotTable gave on the same rows:
   look at each one, though none stops anything." The sentence about the old sample follows,
   unchanged. batch.md's section starts "It ran ...".
2. **A table's name at the start of a line read as an ordinary word** ("pivot, from
   PivotTable1:"). Now the Saved table is named in full and the workbook's piece as the other
   texts name it: `mart_dev.pivot, from PivotTable "PivotTable1":`, `mart_dev.job_runs_report,
   from Excel Table "job_runs":`, `... from the Total Row of Excel Table "job_runs":`, and
   `... from PivotTable "PivotTable1" (grand total):`. A Copilot script reads `pivot.hql,
   Copilot's Hive of PivotTable "PivotTable1":`.
3. **"Grand Total: Hive gives the row, the PivotTable shows none (5 times)"** didn't say which
   side was wrong or what to do. Now: "Grand Total: the Hive gives 9 rows where the PivotTable
   shows one: fix the Hive, in the `# logic` cell of its table's notebook". A row the pivot
   doesn't show at all reads "...: the Hive gives a row the PivotTable doesn't show: fix the
   Hive, ...", or "N rows". A Table's extra row reads "the Hive gives this row, and the
   workbook's Table doesn't hold it: fix the Hive, ...", and a missing row reads "the
   workbook's Table holds this row, and the Hive doesn't give it".
4. **"the small executor the check runs on hasn't got"** was jargon, and "compare it by hand"
   didn't say how. Now: "not checked: the check can't run FLOOR on this computer. To compare it
   by hand, run its table's preview() on your warehouse and look for the same rows in the
   workbook, though the warehouse's rows may have moved on." The other reasons follow the same
   pattern: "the check couldn't read its Hive: ...", and "the check couldn't run its Hive on
   this computer: ...".
5. **`NEXT` used "logic cell" and "a rule's mark" without explaining them.** Now: "For each
   difference, compare the table's Hive, in the `# logic` cell of its notebook, with the
   workbook's formula, query or PivotTable; the rule its checklist names may explain it.
   Convert again after a change to check again."
6. **"the values Excel last stored", and the docstring's "one line a cell".** Now "the values
   the workbook shows, as last saved". The docstring says: "The report and batch.md list each
   cell where the two differ, each on a line of its own; a difference stops nothing, but is
   yours to look at." The note about unsaved formula results now reads "as the file holds no
   value saved for them: a file saved by a tool, not by Excel, holds none".

The lead's call 3 added one more line a person sees: each cell where the workbook shows an
Excel error and the Hive gives NULL, listed apart under its final, "job_id 1, dt 2026-09-23:
the workbook shows #REF!, and the Hive gives NULL". The final's own line counts these cells
separately: "5 of 6 cells match the workbook; below, 0 differences and 1 cell where the
workbook shows an Excel error and the Hive gives NULL, neither a match nor a difference:".

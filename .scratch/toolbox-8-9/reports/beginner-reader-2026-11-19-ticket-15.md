# Beginner reader, 2026-11-19: ticket 15's how-to 33, the README and the overview

Read: how-to 33, "Convert an Excel workbook", in full; the README template's Excel section and
the lines naming the Copilot files; the Workflows overview's Excel box, hand-off and tripping
points. As a person with Excel skills and a liking for pivot tables, converting their own
workbook for the first time. Advisory; the user decides what changes.

## Stops

1. "a Table, job_events, of ops.job_events' rows pasted in" and DATABASE `"ops"`: nothing says
   convert matches a Table to a warehouse table by its name. Tables are called Table1 or
   SalesData: rename them? From two databases? **Stuck.** (The user's answer: ticket 20.)
2. The README's Excel step 1, "copy `copilot/formula_workbook.xlsx` and follow its Steps sheet",
   against the how-to's "Save it as it is": rebuild in the template or not? **Stuck.**
3. "to tab through each team in a presentation ... "fold" ... to slice later": how is the slicer
   got back from a Saved table? Only "a WHERE on team" is offered. **Reread.**
4. Step 2's "repeats" message and its table of copies look like an error until the next line
   says the Key holds. **Reread.**
5. `connect(conn)`: where `conn` comes from is never said. **A moment.**
6. "The files of mart.teams_pivot go to admin/removed/" reads as a deletion until the rename is
   shown. **A moment.**
7. "TODO lines ... which wait on nothing": must they be filled in? **A moment.**
8. The example ends "failed, couldn't compare"; "Done when the compare says it passed, at work"
   is never seen; `partitions=[]` is never explained; the README says "created, seeded and
   written", the how-to never seeds. **Reread.**
9. Seven Copilot file numbers to work out (15, 11, 12, 23, 20, 24; 21 with 03, 05, 06; 22 with
   06, 17). **Reread.**
10. The checklist line of about 250 words in one paragraph. **Reread.**

Clear: the tripping points and the overview's hand-off; the Excel box links the how-to. For a
workbook like the example, mostly gets the person to a Saved table; for their own, stops 1 and 2
decide whether convert reads it at all.

## Fixed

Ticket 20 (with stop 1, the user's Decision); its Answer has each in full.

1. Each source a converted table reads is a SOURCES Decision, proposed from its name (Table1 as
   ops.table1); how-to 33 (When you'd use it, steps 3, 6, 7), the README's steps 2 and 7, the
   overview and CHANGES.md say a Table's name needn't match the warehouse.
2. "Take your workbook as it is": any workbook converts as it is, the Formula workbook an
   optional template (how-to 33's step 3, the README's step 1, EXCEL_FLOW).
3. Step 9 gets the slicer back in Excel's words (Insert > PivotTable, Insert > Slicer on the
   Saved table's rows) and filters the preview on team.
4. Step 2 says before it that "repeats" is expected and what it means.
5. Step 1 says where `conn` comes from.
6. Step 8 says admin/removed/ keeps the old name's files: nothing lost.
7. Step 8 says the TODO lines need no answer.
8. Step 10 drops `partitions=[]`, says what compare.md says at work; "seeded" is gone from the
   README's Excel chart and steps.
9. Step 11 and the README's step 3 give one short list in 00's Index order.
10. Step 6 says the checklist line's parts before printing it.

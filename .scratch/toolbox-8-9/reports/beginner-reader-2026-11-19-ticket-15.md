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

Ticket 20 (with stop 1, the user's Decision); see its Answer for each stop.

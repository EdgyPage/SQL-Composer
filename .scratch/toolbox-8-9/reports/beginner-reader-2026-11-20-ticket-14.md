# Beginner reader, 2026-11-20: ticket 14's rewordings of files 15, 20 and 22, and the page

Read: Copilot file 15's P6, R3 and H2, file 20's PS2 and file 22's F4, as a person with Excel
skills converting a workbook whose PivotTable is built on a Power Query's Table, and answering a
Report filter's Decision so a scheduler runs one status at a time; the Example projects page's
line on an archived notebook. Advisory; the user decides what changes.

## Stops

1. File 15's P6, "a query loading a Table a PivotTable or another Table's formula reads": the
   clause has to be split to see a PivotTable is one of two readers. **Reread.**
2. File 15's R3 and P2 counted a PivotTable as a reader of a query's Table but not of a formula
   Table: is a formula Table a pivot reads a step or a final? **Stuck.**
3. File 15's H2, "never `*`: a short CTE is quicker to check": is `*` wrong or only untidy?
   **A moment.**
4. File 20's PS2, "that query's Hive as a CTE": what is the CTE called, when PS1 says "never a
   CTE named for the table it reads" and a query and its Table can share a name? **Reread,
   close to Stuck.**
5. File 22's F4, "a second decisions cell": the convert notebook's check() prints a DECISIONS
   "to paste over the decisions cell's". A second cell, or the same one? Does check() paste, or
   do I? Is write_decisions run twice? **Stuck.**
6. F4's "accept it": as `"proposed"`, as a Key is, or by keeping the pasted line? **Reread.**
7. F4's "the first value kept": the first of which values? **A moment.**
8. The page's "An archived copy, kept in admin/removed/ when its table was renamed": renamed to
   what? **Reread.**
9. Under that line, the archived notebook's own Steps still say "Run the cells". **A moment.**

## Fixed

Ticket 14's Answer, "The reviews", has each in full.

- 1 and 2: P2 names a PivotTable among a formula Table's readers, and R3 says "any other piece
  reads it (a Table, query or PivotTable)" in both its clauses, as the code's `piece_roles`
  does.
- 4: PS2 says "a CTE named for the query".
- 5 and 6: F4 says check() prints a DECISIONS with the tag's proposal, to paste over the cell's
  DECISIONS, keep the proposal to accept it, and run the cell again.

Not changed: 3 (file 15 is at 8,839 of 9,000 characters), 7, 8 and 9.

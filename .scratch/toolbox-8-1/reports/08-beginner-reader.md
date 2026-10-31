# Beginner reader: ticket 08, a new table's Table reference from its logic

Run 2026-10-31 on the uncommitted ticket 08 diff; saved here by the session, in short, each
stop followed by what was done.

1. **How-to 6 still teaches writing the reference by hand** (its lines 67-69, 342, 394-397),
   against the new story. *Partly done:* it now says the reference stands in until
   reference_from_logic writes it, and that the page writes it by hand instead, as the
   Starter did. *Left for ticket 12*, which reads every how-to again as one story.
2. **The how-to's and the Starter's filled notebooks have no PARTITIONED_BY.** Not changed:
   a Project's own Table notebooks are the user's, which an upgrade never rewrites, so the
   Starter's stay as written; reference_from_logic refuses a logic cell with no
   PARTITIONED_BY, saying to add one. Ticket 12.
3. **"partitioned however its Table reference says".** *Done:* "as PARTITIONED_BY says".
4. **"once both are filled in".** *Done:* "once its Table reference is written from the logic".
5. **new_table's report said "fill in its <...> and TODO lines".** *Done:* "project.
   reference_from_logic writes it", in the report and each page that shows it.
6. **"proposed by project.convert"** in a file convert never made. *Done:* "proposed from its
   query".
7. **The written file drops "Why: TODO" and adds does_not_add_up=; its location example ends
   in this_table.** Not changed: it is the file a Conversion writes, the same everywhere.
8. **Step 4 has no cell; the DECISIONS cell is far up; the file's location=None TODO looks
   like something to edit.** Not changed: ticket 12.
9. **"It is a decision" under writing the logic.** Not changed: the step's kind; ticket 12.
10. **When a type is a guess.** Not changed: reference_from_logic's docstring says, where
    nothing tells; the Decision names it.

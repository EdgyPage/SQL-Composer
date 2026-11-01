# Beginner reader: ticket 20

The reader (opus, 2026-11-01) read ticket 20's diff as a Python-first beginner who knows little
SQL. It read the Excel files as a non-technical Excel user. It rendered the upgrade and
new_table notebooks' cells and ran `write_decisions` and `do_next()` in a scratch folder. Each stop
below is followed by what changed.

1. **Formula workbook step 7 (stuck).** "Paste the query's M" never said where the M comes
   from, how to make it read a Table, where example 03 is, or to name the query. The fallback's
   "no Excel at hand" made no sense to someone in Excel. Its Done when left out the typed rows.
   *Changed:* step 7 now:
   - copies the M from the original workbook (Queries & Connections, Edit, Advanced Editor);
   - shows the `Excel.CurrentWorkbook(){[Name="job_runs"]}[Content]` source line;
   - names the query for its Table, and gives example 03's path;
   - lays out the fallback (`Query <its name>:` with the M below it, and the rows typed into a
     Table of its name), which its Done when checks.
   - "M" is in "Words used here".
2. **README Excel step 3 against step 5 and the check (stuck).** Leaving out a Total Row's
   query went against "each final has its file". *Changed:*
   - The note moves to step 5: "leave out each final no one needs kept as a table, such as a
     Total Row".
   - A Total Row's file is named `by_job_total.hql`.
   - Step 5's Done when and the check now read "each final you keep".
   - Step 3 defines a final as "the Tables your work ends with".
3. **README Update step 6 repeated step 5 (nearly stuck).** The 8.0 Upgrade already marks
   `admin/databases.py`. *Changed:* step 6 is gone. Step 5's rules say what the mark on
   `admin/databases.py` asks for, using the file's own placeholders, `<DEV_DATABASE>` and
   `<PROD_DATABASE>`, and that naming them renames nothing.
4. **Update step 5 had no "then step 6".** *Changed:* step 6 is gone, so step 5 is the last
   step again.
5. **write_decisions' TODO lines against "open while it holds a TODO:".** *Changed:* its
   docstring and decisions.py's say that a TODO: on any other line, such as the docstring's
   first line or `does_not_add_up=`, is no Decision. The message is unchanged.
6. **Step 12, "turns it into tables" and "attach".** *Changed:* step 12 is "Hand it on",
   "If someone else converts it for you, such as your data team". Its checklist heading is
   "Check before you hand it on:".
7. **do_next()'s "named".** *Changed:* it reads "each Workflow you started is done, or you have
   started none", in the docstring's word.
8. **new_table step 1's order.** *Changed:* the action opens with what to do first: "if
   `QUERIES` gives a query, first give each table it reads a Table reference, with the
   references Workflow. Then run the cell below." It then names the batch for its table.
9. **The upgrade about text: undefined DEV/PROD, no step asking for it.** *Changed:* the note
   leaves `about`, which also fixes how-to 29's spliced bullet. It moves into step 2's action,
   tied to the mark that asks for the names.
10. **File 12's Total Row line: "it" and the split SUBTOTAL.** *Changed:* the SUBTOTAL line
    stays whole. A bullet of its own says: "If the user says no one needs a Total Row's total
    kept as a table, write no block for it, and name it in the map as left out."
11. **Step 7's Done when against the fallback.** *Changed:* folded into 1.

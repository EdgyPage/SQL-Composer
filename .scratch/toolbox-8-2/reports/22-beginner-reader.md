# Beginner reader: tickets 21 and 22, the workbook as text

The reader (opus, 2026-11-01) read the script, README step 2, the Steps sheet's step 12, and
Copilot files 15 and 12. It read as a Python-first beginner, and the Excel parts as a
non-technical Excel user. It also ran the script on example 03 and on the loop fixture. Each
stop is listed with what changed.

1. **Step 12: "attach the text workbook_text.py ... writes of it" (stuck).** It read as
   attaching the .py file. *Changed:* "first run workbook_text.py, in the copilot folder, on
   this workbook: it writes a .txt of the same name beside it, which you attach in place of
   the workbook. The README's section on handing over an Excel workbook says how."
2. **README step 2: the .txt and the .xlsx read as equal choices (stuck).** It gave no reason,
   no path in quotes, and left a working `%run` path unsaid. A user without Python lost the
   M, and the loop led nowhere. *Changed:*
   - a Goal: "Copilot may not see a Power Query's M inside an attached workbook; the workbook
     written as text shows it";
   - two if-branches;
   - the full command in one code span, with the path in quotes, from a terminal in the
     download's top folder; `%run` is dropped;
   - for no Python, "keep each query's M on its Power Query sheet too";
   - a loop: "it writes nothing: break the link it names in Excel, save, and run it again";
   - the section's opening line: three Copilot files and the workbook.
3. **The loop refusal's "reads ... reads ... reads" chain.** Two pieces were named "back", and
   the fix named no piece. *Changed:* each link is named in Excel's words: `Power Query "back"
   reads Excel Table "looped"; Power Query "back" loads Excel Table "back"; Excel Table
   "looped"'s formulas read Excel Table "back"`. The fix: "break one of these links, such as a
   query reading the raw data's Table in place of a Table in the loop". The script says
   "nothing was written".
4. **File 15 step 1's cut-short heading.** *Changed:* it quotes the whole heading, "Order,
   each piece after every piece it reads:".
5. **File 12's "in the order each reads the next" (backwards).** *Changed:* "each read by the
   next".
6. **File 15's third example: two finals, one block.** *Changed:* "by_job (Total Row), file
   12's second example".
7. **"Order" meant sorting in file 12.** *Changed:* file 12's "## Order" is "## Sorting".
8. **File 12's new example's typed 1 and 2.** *Changed:* "As a summary, its typed job_ids, 1
   and 2, are typed in (file 15)". The heading is "## Examples".
9. **File 15's loop rule, "in it".** *Changed:* "refuse each final in it, no block; name the
   loop". The map's refusals hold it.
10. **Example 03's text carries its Hive sheet.** *Left:* the sheet's own A2 says to delete it
    before trying the workbook on Copilot. The README's examples line names the Hive sheet as
    the answer.
11. **The docstring: "when Excel couldn't save the query".** *Changed:* "A workbook that holds
    none, such as one whose Excel couldn't add a query, gives them from its Power Query
    sheet". The usage line runs from the top folder, as the README does.
12. **Smaller points.**
    - *Left:* Parameters and Keys show in the Order; they are Tables, and file 15's rule keeps
      them out of the map.
    - *Left:* a missing file gets the "can't be read" message; its fix line says to name a
      workbook that is there.

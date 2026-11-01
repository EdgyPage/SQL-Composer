# Beginner reader: ticket 18, the docs rewritten to the instruction rules

Run 2026-11-01 on the uncommitted rewrite. It read the README template (opening, Terms, steps 1
to 3, the Excel section), the Steps sheet, Copilot file 15, the starter's convert notebook and
how-to 03, as a Python-first user new to SQL, and found 47 stops.

## Its three costliest stops, and what was done

1. The README's Excel chart and its step 2 named Copilot files 03, 04, 05, 11 and 12, the rest
   15, 11 and 12. Fixed: the chart and steps are written by `tools/workflow_graph.py`, whose
   EXCEL_FLOW now names 15, 11 and 12.
2. The Excel path's convert run: the README said each table passes "its compare" while the
   convert notebook compares each "with its original", and an Excel query writes no table; the
   batch-naming rule was circular, and "reads itself" undefined. Fixed: the notebook's Terms
   define Original for a query alone (the rows it gives), "reads itself" and "staging table";
   the README's Excel step 5 is two steps, saving and converting, saying what the compare
   checks for a query alone, and the section closes with a check.
3. Typed-over values and "typed column": the Steps sheet's step 9 said to delete typed-over
   values and step 10 to put them back; "typed column" was undefined there; file 15's first
   example listed job_runs as a source and a final against its own rule. Fixed: step 9 deletes
   only Tables and columns, keeping the typed-over values step 10 is for; the sheet defines a
   typed column; file 15 defines source, step, final and mark plainly, and its example says
   which part of job_runs is a source.

## Also fixed

- File 15's and file 00's steps each now have a goal, an action and a done-when; file 15's
  step 4 is two steps, the reads and the columns (stops 29, 30).
- The convert notebook's Decision term says "answered yet" in place of "made" (stop 37).

## Left for a follow-up (none blocks a run)

The README's two levels both called "step" (1); terms used before Terms define them, Admin
log and names cell (2, 3); the Python and package-version notes (4, 5); the shape `conn` must
have, an object with `.query` and `.execute` (6); the "Every file of a Project" reference in
the middle of step 1 (7); `check_key` shown without a call (10); ON undefined (11); item 3.4's
three actions and a done-when that doesn't fit `to_hive`'s docstring (12); the Steps sheet's
steps 2, 4, 5 and 10 each holding more than one action, kept so the step numbers others cite
stay put (21 to 24); AVERAGEIFS and the others in file 15's summary rule (32); how-to 03's
import lines (45, 46); the convert notebook's Self-check sitting in its first cell (36) and its
names cell comments (40 to 43).

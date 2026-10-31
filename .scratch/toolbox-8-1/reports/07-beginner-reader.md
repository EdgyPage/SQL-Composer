# Beginner reader: ticket 07, project.run_workflow

Run 2026-10-31 on the uncommitted ticket 07 diff. The reader had no write tool, so the session
saved its report here, in short; each stop is followed by what was done.

## Would I know...

- **When to use run_workflow rather than each cell?** Not really: every place offered it as an
  "Or", and it didn't stop at the checks its steps ask for.
- **What a dry run does?** Only from the docstring, after running it: it converts a batch and
  writes answers in for real; CHANGES and how-to 29 said only "sends nothing".
- **What to do after a stop?** For a refusal, yes; for a Decision, by inference; for the
  warehouse's error or a failed compare, "Mend it" pointed nowhere.

## Stops, and what was done

1. **"up to the first that needs you"** read like do_next's "yours". *Done:* "up to the first
   only you can do", and the docstring lists each kind of stop.
2. **The example skipped step 2 silently.** *Done:* a step done already is reported, "done
   already, skipped".
3. **It reads the saved notebook, not the running one.** *Done:* the docstring says so first.
4. **"its files"**. *Done:* "the Project's files".
5. **Three kinds of stop in one sentence; "a step done by hand"** matched no stop it showed.
   *Done:* a list of four stops, each with what to do.
6. **It ran every unfinished batch, not only those named; "each NAME's list names".** *Done:*
   it runs only the batches the names cell names (the Spec review found it too), said plainly;
   NAME's comment says a list is for run_workflow, of batches converted already.
7. **A dry run converts and writes answers in, and shows no Hive while a Decision is open.**
   *Done:* the docstring, CHANGES and how-to 29 say what it runs for real and where it stops.
8. **`change: object`.** *Done:* `Statement | None` (the Standards review too).
9. **No example of a stop.** Not changed: test_run_workflow and the journeys hold each stop.
10. **"Mend it" pointed nowhere; `...`; single quotes.** *Done:* each stop says what to mend,
    and every stop ends "Then save the notebook, and run its last cell again".
11. **A refusal's columns no longer lined up.** *Done:* its own indentation is kept.
12. **On the Example database convert's compare can't pass.** Not changed: the Example
    database keeps no write, as compare_batch's docstring says.
13. **A Decision stop had no run-again line.** *Done:* the same last line as every stop.
14. **The warehouse's own lines print above the report.** Not changed: the report is what it
    gives back once it stops.
15. **Step 5 showed in a dry run but not a run.** *Done:* each step is reported either way,
    skipped when done.
16. **The notebook's opening said the last cell is do_next().** *Done:* it says each step's
    cell, or in their place the last cell, run_workflow; do_next() is the cell before.
17. **"yours to run" a cell above a cell that runs it.** *Done:* the opening says the last
    cell runs the steps in place of their cells.
18. **"# Or run every step left"**: or what? *Done:* "# Every step left, in place of their
    cells, up to the first only you can do".
19. **change_a_saved_table's runner sent the change without stopping at step 2's check, and
    never showed its Check first line.** *Done:* a step no file tells of that only prints is a
    check, so a run stops after it: the change's Hive is shown as show_hive shows it, Check
    first line with it, and step 3's own cell sends it. The runner never sends the change, so a
    second change to the same table can't be passed over. new_table's preview, which only
    reads, the map's Q13 says waits on nothing: the runner prints it and goes on, as the
    docstring now says.
20. **Why upgrade has the cell.** Not changed: it runs the upgrade, then stops at the marks.
21. **How-to 29's head.** *Done:* rewritten, saying which to use.
22. **"Its last cell runs..." then "# Or ..."**. *Done:* "in place of their cells".
23. **CHANGES' commas.** *Done:* rewritten.
24. **CHANGES' dry run.** *Done:* says what it runs for real.
25. **"each batch"; why two.** *Done:* "the batch its names cell names"; do_next() "still runs
    only the steps that change files".

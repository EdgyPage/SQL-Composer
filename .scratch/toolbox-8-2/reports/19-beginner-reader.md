# Beginner reader on ticket 19 (uncommitted diff against b935588c)

Saved from the reader's hand-back; it may write no file itself.

## The three costliest stops

1. **Stuck: check_references contradicts itself.** Its text cell (ADMIN_NOTEBOOKS
   "check_references" in project.py) still says a partitioned table's Key isn't checked
   there, while its code cell now checks it, and the README says it does; its last cell's
   comment still leaves a partitioned Key to you.
2. **Stuck, then a reread: the refusal for Hive sqlglot can't read.** It names hive.hql for
   Hive passed as text; its "line 1" (where the statement starts) and sqlglot's "Line 2"
   (where it broke) disagree; sqlglot's "Required keyword: 'this' missing for And" means
   nothing to a beginner; "as Excel has" reads as "like Excel, Hive has none".
3. **Reread: compare.md with several results, and when you are done.** "Done when each
   table's compare.md says it passed" doesn't say every result must pass; an extra compare
   after the batch has moved to finished/ can fail, leaving a finished batch promote refuses;
   compare_batch's docstring still shows a compare.md with no `## ` heading and says nothing
   of results kept side by side.

## Every other stop, in reading order

- Connecting: where the sys.path lines go (in warehouse.py, in place of
  `conn = example_database`); "the Project's own folders" when warehouse.py imports
  sqlglot_composer, a folder in the Project; how-to 01's comment cut mid-sentence.
- Checking a file: `equals` used before section 3 explains it, with no import shown, and no
  reason given for checking one Partition; "of the 2 SHOW PARTITIONS lists" misparses;
  "latest" Partition assumes dates; SHOW PARTITIONS gives dt=2026-09-24 where equals wants
  the value.
- Convert step 5: "NAME being the names cell's" is elliptical, and the print(...) wrap is
  unexplained; "both tables" and an unpartitioned table in the same batch are unsaid.
- Copilot file 11: brackets on OR only, unexplained (AND binds tighter); NOT( not in the
  self-check; "two -IFS forms are added" wants a worked pair; `+` in SUMPRODUCT counts a row
  where both hold twice, where OR counts it once; ELSE 0 here against COALESCE above;
  "as `(..)*1`"; "reads its own Table".

# Beginner reader: Toolbox 7.2 ticket 13, the Copilot files

Read 2026-10-27 on 221376a: copilot/00 to 10, each read as the user pasting it and as the text
Copilot follows; count_characters.py run with no argument, a file, and a missing file; the
README's "Have Copilot write it", CONTEXT.md's Copilot files, CHANGES.md's 7.2 bullet. Worked
examples of 05, 06 and 08 run on the Example database, and two refusals 09 quotes triggered:
all ran, the wording matching. Saved by the session (the reader writes no file).

## Stops, condensed

1. 00: Hive is never said to be SQL. (a moment)
2. 00: how much of a table's description to type, every chat; could the reference file be
   pasted? (a reread)
3. "8,000 characters before a chat": a message's limit? (a moment)
4. Where count_characters.py runs from; a missing file gives a traceback and exit 0; "with
   Windows line breaks" unexplained in its output. (a reread)
5. "SQL's words are not Toolbox names" beside SELECT, FROM and WHERE. (a reread)
6. One file per chat, yet "names this file or another Copilot file lists", rule 10's "file
   10", `at_most` in 05 and `Clause`, `Statement` in 06 from no list. (stuck)
7. Where a partition bound goes: rule 5 names FROM, JOIN and LEFT_JOIN and one partition
   column; 04 adds SEMI and ANTI, nothing for FULL or CROSS; 07 says "as the Hive bounded it";
   08 bounds one of two partition columns. (a reread, in four places)
8. ORDER_BY needs LIMIT, with sorts_everything and pandas sorting met later. (a moment)
9 to 31. Smaller: returns_all_rows and query=None unexplained; SET line; Database module;
   send=; Table's storage arguments; "last" in columns; "trust"; Verdict and Project action;
   adds_up; `/` allowed while `==` isn't; a GROUP_BY name as text; last_n_days and today;
   keeps_only_matches and broadcast (stuck); FULL and CROSS bounds; a warning against a
   refusal; AS on a table; which example tables are partitioned; row_number against rank;
   rows= "keeps"; a total needing rows=; `d.n`; grouping_sets' shape; INTERSECT and EXCEPT;
   WITH from derived.
32. 06 against the Table notebook project.new_table writes: READS and rows() there, DAY and
    rows(day) here; the notebook sending its own write, where run_tables does. (stuck)
33. 06's send order skips hive_settings("dynamic_partitions"), which its own write needs.
    (stuck)
34 to 45. Smaller: partition= beside "partition last"; two files in one answer; run_tables'
    order; HIVE undefined and the CONVERSION mark in 07; "as the Hive bounded it" against
    rule 5; hive_settings' name twice; constants for a list in 07 only; CTE; 08's date format;
    compare_hive against compare_with_original; LoadRefused for sorting; 09's "before" not
    shown; "key" in mapped against Key; compute_statistics' columns=.
46 to 48. Where copilot/ is; CHANGES' counter with no folder; "cheat sheet" avoided beside
    the README's Cheat sheet. (a moment)

## The three costliest

Stops 32 and 33 (file 06 against the real notebook and its send order), stop 6 (one file per
chat against "another Copilot file"), stop 7 (the partition bound across four files).

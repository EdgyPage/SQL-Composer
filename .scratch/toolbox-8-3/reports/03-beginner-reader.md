# Beginner reader: ticket 03, the tag Decision (2026-11-04)

Run on the newest Opus on step 2's text, check() and the checklist, write_decisions' reports,
the TAGS block, the scan line and script_tag's docstring, in scratch Projects answering tags
right, again, and in each wrong form. 21 stops; what was done with each:

| # | The stop | Done |
|---|---|---|
| 1 | the decisions cell's example has no "tags" | it shows `"tags": {"PERIOD_END": "'2026-10-31'"}` |
| 2 | "the program" is never introduced | step 2 says "the program that ran the scripts, such as a scheduler, replaced with a value before Hive read it" |
| 3 | "a bare tag with its quotes and all" reads backwards | "A tag standing alone, as in `dt <= <PARM=.../>`, is answered with the value's own quotes" and the quoted case beside it |
| 4 | check() and the checklist don't say bare or quoted | the question names it and how to answer: `tags: PERIOD_END, bare at weekly.hql, line 10: answer ... with its quotes, such as "'2026-10-31'"` |
| 5 | `team_2` reads as a column | `SKIP_TEAM` |
| 6 | why only steps 3, 6 and 7 | "the table is made already, so 4 and 5 stay done" |
| 7 | TAGS' comment: "Until then", may I edit it? | says to answer under "tags" and that step 3 writes over what is there |
| 8 | "line 6: its value" | "bare, at weekly.hql, line 10. Answer it with its quotes, ..." |
| 10 | the scan line names no notebook | names admin/workflows/convert/convert.ipynb, step 3 and step 4 |
| 11 | an answer given again looks like a first | "tags: PERIOD_END is '2026-09-24' now, in place of '2026-09-23': run steps 6 and 7 again." |
| 12 | "not Hive text"; an unquoted date became 1994 | "a Python int: give the Hive as Python text ... (a date typed with no quotes is a subtraction to Python)" |
| 13 | a "tags" that isn't a dict is ignored | named: "give a dict of each tag's answer by its NAME" |
| 14 | a bare date with no quotes is accepted, then "a bug in the Toolbox"; a quoted answer quoted again is accepted | both named and left unwritten, the tag still open, with the answer to give |
| 15 | the hivevar example has no quotes | `'${hivevar:period_end}'`, "in quotes when it holds a date" |
| 16 | a hivevar no SET line sets: written or not? | "written, but no SET line ... sets it, so the write would send it as it is: answer again with the value itself" |
| 17 | where is session_settings()? the answer's quotes dropped | "the SET hivevar line its Table notebook's HIVE_SETTINGS keeps"; the answer shown as given |
| 18 | "its next step" | "step 3, project.write_decisions" |

Left: 9, the scan's lines of statement.hql beside the script's (a scan's own numbering, older
than 8.3, Q6); 19, the TODO lines repeated by each write_decisions (older than 8.3); 20, the
Table reference pointing back to the checklist (7's rewording covers it); 21, sqlglot's own
warning on a SET hivevar line (sqlglot's logger, Q6).

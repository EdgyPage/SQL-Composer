# Beginner reader: ticket 07, the docs (2026-11-04)

Run on the newest Opus on how-to 09, the README's section 9, how-to 29's convert steps and
Copilot files 07 and 13, with scratch conversions. 17 stops; what was done with each:

| # | The stop | Done |
|---|---|---|
| 1 | "the script never says the day itself", yet it types the day five times | "Its author tagged only that one day; the others are typed in, and the converted code keeps them as they are" |
| 2 | a nightly tag answered with one fixed day | a Common mistake, "Answering a nightly tag with one day": answer "'${hivevar:run_day}'" with a SET hivevar line kept in the script; the README and Copilot 13 say the same |
| 3 | three step numberings: "run steps 6 and 7 again", "its step 3 writes it here", "step 3 and check() print" | the messages name what the step does: "write it and compare it again", "project.write_decisions writes it here"; the README says "the convert step" |
| 4 | told to paste a block never shown | step 6 prints the block's RUN_DAY line |
| 5 | "its place reads the day from TAGS" is hard to picture | step 4 shows WHERE(equals(a.dt, script_tag(TAGS["RUN_DAY"]))) and TAGS saying <PARM="RUN_DAY"/> |
| 6 | "a bare tag's with the day's own quotes" | "A bare tag's answer is the day with its own quotes, "'2026-09-24'"" |
| 7 | "by its NAME, saying where it stands" | "named RUN_DAY, as the tag is. project.check() says where it stands and how to answer it" |
| 8 | "as a compare would show" the day | the scheduler's job says the day; a compare shows rows that differ |
| 9 | a guessed type "to answer too" though the block holds "string" | "a guessed type, "string" in the block: keep it, or give its type" |
| 11 | "by table" | "once for each table it ends up in, since it may stand for a different value in each" |
| 12 | no example of a quoted tag | `'<PARM="STATUS"/>'`, answered `{"tags": {"STATUS": "failed"}}` |
| 13 | "run the steps that write the answers in, write each table and compare each again" | "then run step 5's steps again: write the answers in, write each table, and compare each" |
| 14 | why compare another Partition | "once your dev table holds it" |
| 16 | Copilot 07's "TAGS["NAME"] in its string"; where TAGS comes from | `'<PARM="NAME"/>'`, `TAGS["NAME"]`; "TAGS is in its Table reference" |
| 17 | the subtraction's result | "2026 - 9 - 24" |

Left: 10, one example date everywhere (the hints' 2026-10-31 is a day no example holds, on
purpose, so it is never mistaken for one); 15, the decisions cell's comment names only
project.check() (D415: it is shared by every Workflow, and only check() prints the block in
each); script_tag in Copilot 07's names list (its signature would put the file over 8,000
characters; the bullet names it).

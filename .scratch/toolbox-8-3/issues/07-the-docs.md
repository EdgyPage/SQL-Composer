# The docs and the Copilot files

Type: task
Status: resolved
Blocked by: 02, 03, 04, 05, 06
Size: M

## Question

Everything a user reads about converting tells of Script tags, the printed `DECISIONS` and
`PARTITION`, as exact numbered steps (8.2's map, "What a user reads is an exact process").

## Done when

- How-to 09 (convert someone else's Hive) shows a script with a Script tag, step 1's printed
  `DECISIONS`, the tag answered, and a wrong date answered again. How-to 29, the README and
  `docs/workflows.md` say the same where they tell of the convert step.
- Copilot file 07 (convert Hive) and file 13 (Workflows) tell of tags and the printed
  `DECISIONS`; `tools/merge_copilot_files.py` writes the all-in-one again.
- The one-source-of-steps test passes.
- The beginner reader runs on what changed; its report is linked here.
- Asked of the user here: whether the usability loop gains a convert scenario with Script tags
  (map, "Not yet specified").

## Answer
Built 2026-11-04.

- **How-to 09**: the nightly script holds a Script tag, `WHERE a.dt = <PARM="RUN_DAY"/>`, which
  step 2 says the scheduler fills in; step 4 says it is read past and its place reads TAGS;
  step 5 shows check() naming it, bare at daily.hql, line 9; step 6 says step 3 and check()
  print a DECISIONS to paste, and answers the tag, with the wrong day on purpose; step 7
  writes it, then answers it again with the right day, write_decisions saying "tags: RUN_DAY
  is '2026-09-24' now, in place of '2026-09-23'". Common mistakes gain "Answering a bare
  Script tag without its quotes", and "Leaving a Decision open" says to paste what check()
  prints.
- **How-to 29 and docs/workflows.md** are drawn from the Workflows by
  `tools/workflow_graph.py`, so they say what step 2's and step 7's texts say (03, 05, 06):
  written again. **The README** (`docs/clean-branch-readme.md`, section 9) says what a Script
  tag is, that step 3 and check() print a DECISIONS to paste, how a bare and a quoted tag are
  answered and changed, and PARTITION in place of the call in a new cell.
- **Copilot files**: 07 maps `<PARM="NAME"/>` to `script_tag(TAGS["NAME"])` bare and
  `TAGS["NAME"]` in its string when quoted, its value the user's; 13 gives "tags" in
  DECISIONS, the printed DECISIONS and `<FILL IN>`, how a tag is answered, "never guess its
  value: ask", and PARTITION. 07 stays under 8,000 characters (7,823), a few bullets
  shortened for it; `tools/merge_copilot_files.py` wrote the all-in-one again.
- **The usability loop** (asked of the user, 2026-11-04: yes): scenario W6, "convert a script
  holding Script tags", dev split, gives `from_your_team/daily_fails.hql` with a bare
  RUN_DAY and a quoted SKIP_TEAM, the job saying what the scheduler put in each; the
  warehouse ran `daily_fails_ran.hql`, each filled in; its key is the warehouse's rows, the
  compare passed and the Table reference holding '2026-09-24'. `reference_w6` reaches it
  through the decisions cell, and `tests/journeys/test_usability_scenarios.py` holds it to
  the key.
- **D417** (CHANGES.md, PARTITION) is fixed in this commit.
- **Code review** (review-spec, with standards, on sonnet): every bullet met but the beginner
  reader, run since. Fixed: four workbooks rebuilt a byte apart left as committed; Copilot
  07's SET line names run_execute again; how-to 09's Goal rewrapped; `reference_w6` has its
  docstring. Answered: how-to 29 and docs/workflows.md say the new steps already, drawn by
  tools/workflow_graph.py since 03, 05 and 06.
- **Beginner reader**: [its report](../reports/07-beginner-reader.md); fixed, the costliest
  first: a nightly tag answered with one day, now a Common mistake with the hivevar answer;
  the messages name what a step does, not its number, which differs from page to page; the
  how-to prints the block's tag line and shows the converted WHERE and TAGS.

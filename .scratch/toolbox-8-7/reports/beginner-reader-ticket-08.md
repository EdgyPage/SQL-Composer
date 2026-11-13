# Beginner reader: ticket 08, the schedule Workflow

Run 2026-11-13, on Opus, over the uncommitted changes of ticket 08 against 89798750: the new
schedule notebook (starter and intermediate), admin/scheduled_runs.ipynb's text, the README
template's "The Workflows", "Scheduled runs" and "Every file of a Project", how-tos 01, 29 and
31, Copilot file 18 and the intermediate Example project's README. Advisory only; what was done
with each stop is in the ticket's Answer.

I found 10 places where a beginner would stop in ticket 08's changes; three of them cost the
most (listed at the end). I edited no files. Each stop gives the file, the words, and what
would have kept me going.

## Stops

1. `example_projects/starter/admin/workflows/schedule/schedule.ipynb`, the Terms list:
   "**Template**: the empty shape of a Table notebook, in admin/templates/". Step 1 then makes a
   *Scheduled run* from `scheduled_run.py`. Five more terms (Table notebook, Table folder, Saved
   table, Statement, Hive) never come up in this Workflow, but "Scheduled run" is not among the
   terms. **Stuck for a while:** I thought I was in the wrong Workflow. Fix: define Template as
   "the empty shape of a notebook", add "Scheduled run", and drop the terms this Workflow
   doesn't use.
2. The same notebook, the run_workflow cell: "Add dry_run=True to see the Hive it would send".
   This Workflow sends no Hive, and the step "changes only files". The import and connect cell
   also connects to the warehouse for a step that never reaches it. **Reread.** Fix: leave out
   the dry_run line here, or add "(this Workflow sends none)".
3. The same notebook: one step can be run three ways (its own cell, `project.do_next()`,
   `project.run_workflow("schedule")`), with three Decision rules. For a one-step Workflow I
   couldn't tell which one to pick. **Reread.**
4. `example_projects/intermediate/admin/workflows/schedule/schedule.ipynb`:
   `NAME = 'weekly_team'` is filled in, but step 1 "refuses a name already taken", and
   `weekly_team` already exists. Running the cell there gets refused. **A moment.** Fix: a line
   saying this notebook is a record of how weekly_team was made, so its step is already done.
5. `docs/clean-branch-readme.md`, the "Every file of a Project" line: "runs
   `project.new_scheduled_run(NAME)`, `NAME` `"<name>"`". Two code spans side by side with no
   verb between them. **Reread.** Fix: "with `NAME = "<name>"`".
6. The README's `### schedule` section, and Copilot file 18, both say "Its names cell is
   `NAME = "weekly"`", but the notebook ships `NAME = ''`. **A moment.** Fix: "such as
   `NAME = "weekly"`".
7. The README's rules bullet: "If the Workflow is upgrade, change_a_saved_table or schedule, run
   each step's cell in turn, making each decision where its step says". schedule has one step
   and no decision. **A moment.** The Workflow definition near the top (line 42: "run 'Run up
   to your Decisions', answer in the decisions cell…") doesn't fit schedule either.
8. `worked_examples/how_to/31_schedule_a_run.py`, step 3: "The `TABLES = ["mart.team_days"]`
   cell of admin/scheduled_runs.ipynb runs step 2's `project.describe_logic` the same way."
   While both calls sat in one notebook, this belonged here. Now it points back to step 2 from
   inside step 3, and to a different notebook. The README also runs these steps in the other
   order (make first, then describe), so now I go back and forth between two notebooks.
   **Reread.** Fix: move the sentence into step 2.
9. The same file: "name the run in its names cell, … save it, and run its cells down to…". I
   couldn't tell at once whether "it" meant the cell or the notebook. **A moment.** Fix: "save
   the notebook".
10. `copilot/18_scheduled_runs.txt`: the new "## schedule" section, with its numbered "1.",
    comes after "## Output". The file opens with "Follow the steps below in order… reply as
    Output says", and its Objective is filling in a notebook that is already made. A step to
    *make* one, placed after Output, reads like an extra instruction to Copilot. **Reread.**
    Fix: put it before Objective as background, with no number on it.

The README's "Scheduled runs" step 1 and its by-hand list, the scheduled_runs.ipynb first text
cell, `01_start_a_project.py`'s line, the 29 schedule section, and the intermediate README's
weekly_team row all read cleanly.

## The three that cost the most

1. Stop 1: the Template term describes a Table notebook, and Scheduled run is not defined
   (`schedule.ipynb` Terms).
2. Stop 8: `31_schedule_a_run.py` step 3 points back to step 2 in another notebook, and the
   step order differs from the README's.
3. Stop 2: the dry_run "Hive it would send" comment and the warehouse connect, in a Workflow
   that only writes files.

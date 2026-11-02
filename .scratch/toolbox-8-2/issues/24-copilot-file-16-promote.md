# Copilot file 16: the promote Workflow on its own, and file 13's wording given back

Type: task
Status: open
Blocked by: 23
Size: S

## Question

Ticket 23 left Copilot file 13 at 2 characters to spare. Its wording was trimmed to fit, and
the beginner reader stopped on the trims (`.scratch/toolbox-8-2/reports/23-beginner-reader.md`,
stop 12). The user (2026-11-01) said Copilot files may be added where it's appropriate.

File 13 holds two Workflows: convert, and promote. Promote's steps take 1,533 of its
characters, and no Copilot evaluation task tests them.

## Done when

- **File 16, `16_workflows_promote.txt`.** It holds the promote Workflow, standing alone as
  every Copilot file does: Objective, Terms, Names, Steps, Decision rules, Output, How a
  Workflow runs, its steps, an Example and a Self-check.
- **File 13.** It holds convert alone. Its Objective sends promote to file 16, and its wording
  trimmed in ticket 23 is given back where it fits.
- **File 00.** Its list names file 16, and its Decision rules route promoting to it. Each file
  that names file 13 for promote names 16.
- **The evaluation.** Objective 16 has three tasks, two dev and one held out, each a promote
  Workflow task run after a convert batch whose compare passed. Each reference passes, and a
  wrong answer fails.
- The docs that list the Copilot files list 16: the README, `docs/copilot-eval.md`,
  `CHANGES.md`. Every Copilot file stays at 8,000 characters or fewer.
- Tested with tickets 23's round.

## Review

The spec review (review-spec, sonnet) and the beginner reader (opus) each had findings fixed
or answered:

- **Fixed, from the spec review:**
  - File 16's location rule follows `_prod_location`. promote fills a location from an
    earlier promote, or from a dev location named for the Dev Database. Otherwise the
    location is a Decision left open, which `project.check()` names.
  - File 16 gives `rename=` for a prod copy named otherwise.
  - `docs/copilot-eval.md` says 42 tasks.
  - The tasks' objective 13 heading says convert, and DAILY_FAILS_MADE's comment sits above
    it again.
- **Fixed, from the beginner reader:**
  - Files 13 and 16 say where `query` and `execute` come from.
  - File 13's NAME says which cell takes a list of batches, `project.run_workflow(...)`. Its
    rules write `DECISIONS = {}` when none is open.
  - File 16 names file 14 for new_table, and its example says the location is left for promote.
  - File 00's line for file 07 sends a whole job of Hive into tables to file 13.
- **Answered, left as is:**
  - Each file's first line, "Add no step or call", means no call beyond its steps' cells.
    Those cells use the Toolbox's names, which the notebook's first cell imports.
  - File 13's Terms keep DEV and PROD, as its steps use DEV and its routing names PROD.
  - T39's cells became FAILS_COMPARED, so the promote tasks run the same convert first.

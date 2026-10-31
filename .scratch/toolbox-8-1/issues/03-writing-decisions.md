# Writing Decisions into the files, and the checklist view

Type: task
Status: resolved
Blocked by: 02
Size: M

## Question

A Decision answered in the decisions cell reaches the files by a file step, never by the
user editing a generated file (map, "Decisions": Q1, Q9, Q11).

## Done when

- A file step writes each answered Decision into the table's files: `key=`, `location=`, a
  guessed type, in its Table reference; keep or fold, from 10. It runs in each Workflow with
  Decisions, before the step that waits on them, and `do_next()` runs it.
- The cell wins over what the Toolbox wrote. A file the user changed by hand is kept, and the
  step reports it, with a fresh copy beside it as a Batch run again does (`fresh/`).
- `tables/<t>/conversion/checklist.md` is generated and read-only: each Decision of the table,
  made or open, written again each time the Decisions are read. Nothing ticks a box by hand; a
  box the user ticks is written over, and check() says so once.
- Its journeys show it (`tests/test_workflow_journeys.py`, ticket 01): no journey opens a Table
  reference to fill in a Key, a location or a type, or ticks a box: those entries leave the
  known-fiddling list.

## Answer

Built 2026-10-31, with 02.

- `project.write_decisions(DECISIONS)`, a new Project action and a file step after each
  decision step (convert's 3, promote's 3, references' 3; `do_next()` runs it): each answer is
  written into the open line it answers. A line made already, as yours is once you change it,
  is kept, and a different answer named; so is an answer for a table with no Table
  reference, or one that answers no Decision; a cell not by table is refused.
- `conversion/checklist.md` is a view written again by convert and by write_decisions: the
  table's open Decisions, read from its Table reference, then notes that block nothing (each
  `# CONVERSION:` mark, a seed, a piece kept as Hive, a logic cell refused). No box anywhere:
  promote refuses a table with a Decision open, in place of a box unticked.
- The journeys answer in the decisions cell: convert's and references' hand edits left the
  known-fiddling list, 4 left (new_table's two `<...>`, the Admin statement, the Upgrade's
  marks). A table the scripts only create has its Decisions too.
- Docs: how-to 9 answers Decisions with write_decisions; the README, how-to 1, how-to 29 (its
  decisions cell shown), Copilot files 07 and 13, the Example projects and their notebooks.
- Tests: `tests/test_decisions.py`; the batch, promotion, compare and conversion tests moved
  from boxes to Decisions.

### After the review (2026-10-31)

- Standards: `answered_text` (an `Answered`: the text, each answer written, each left
  unwritten) and `Decision.question()`, named for what they give; `still_open`, `answers`;
  `workflows.decisions_waited_on` in place of project's `_open_decisions_of`, so the promote
  special case lives with the Workflows; one placeholder pattern; `_guessed` once; the
  answers' names from `ANSWERS`; "Wrote N answers" counts answers, not lines; the private
  `_about` renamed `_subject_of` (lineage has one).
- Spec: a `location=None,` with its TODO taken off is still open; a type answered for a column
  not guessed is named; convert waits only on what the cell answers (a `<...>` is filled in by
  hand: new_table's); check() says where to answer; stale words fixed (CONTEXT.md's
  Promotion, batch.md's docstring). Left: the cell isn't pre-filled with proposals (02's
  Answer); the Key's proposal is 04's; new_table's own decisions cell comes with 08.
- Beginner reader: [03-beginner-reader.md](../reports/03-beginner-reader.md).

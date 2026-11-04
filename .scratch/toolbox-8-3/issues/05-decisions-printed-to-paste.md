# Decisions printed to paste

Type: task
Status: resolved
Blocked by: 03
Size: M

## Question

Answering step 2 today means running `project.check()` in a cell of the user's own, or opening
each table's `conversion/checklist.md`, then typing a dict from lines (map, Q22).

## Done when

- Step 1's output (`project.convert`, and new_table's step converting a query) and
  `project.check()` print the instance's open Decisions as one whole `DECISIONS = {...}`,
  ready to paste into the decisions cell: each table by its dev name, each value still to give
  `"<FILL IN>"`, a proposal where the Toolbox has one, and each tag's script and line in a
  comment beside it.
- A `"<FILL IN>"` pasted and left is no answer: step 2 isn't done, and step 3 writes nothing
  for it.
- It holds in every Workflow with a decisions cell: convert, promote, new_table and references.
- The Toolbox still never writes into the notebook (8.1's 02): it prints.
- Each journey answers its decisions by pasting what was printed and filling it in.

## Answer
Built 2026-11-04.

- **The block** (`decisions.to_paste`): a whole `DECISIONS = {...}`, each table by its dev name,
  each Decision the cell answers: `"location"` and `"key"` as `"<FILL IN>"`, a guessed type's
  proposal `"string"`, each tag `"<FILL IN>"`; a comment beside each says what to write, a
  tag's saying bare or inside quotes, its script and line, and how its answer is written
  (`decisions.tag_hint`, which `tag_question` shares). A placeholder, filled in by hand, isn't
  in it. It is plain Python literals and comments, so it pastes as it is.
- **Where it prints**: step 1's report, `project.convert`'s, after its "Next:" line, and so
  new_table's step converting a query, which goes through the same batch report; and
  `project.check()`, under each next step that waits on Decisions, in every Workflow with a
  decisions cell: convert, promote, new_table and references (`_next_step_line`, through
  `_to_paste`). The Toolbox prints it and never writes into the notebook.
- **`"<FILL IN>"` is no answer** (`decisions.FILL_IN`): `is_answered` says no, so step 2 isn't
  done; `answered_text` writes nothing for it and names it, "location: still <FILL IN>: write
  its answer there"; a tag's `tag_answer_problem` says the same.
- **Journeys**: `Journey.paste_decisions` reads the block check() printed for the Workflow's
  next step, fills in each `<FILL IN>` and types it, asserting none is left; the convert
  journeys, the tag journey and references answer so. The runner journeys type their answers
  before step 1 runs, when nothing is printed yet, as a user running the whole Workflow at
  once does.
- **Code review** (review-standards, review-spec, on sonnet). Fixed: the block prints with
  no indent, so its lines paste into the cell as they are (an indented first line is an
  IndentationError in a plain Python cell); the decisions cell's name is one constant,
  `decisions.DECISIONS_NAME`, which `workflows.DECISIONS` takes; "still <FILL IN>" is one
  helper, `still_to_fill_in`; `paste_lines` and `_paste_text` for names that say what they
  return; `_types_lines` and `_tags_lines` in place of one function split on a kind; the
  decisions cell's own comment says check() and step 1 print a DECISIONS to paste;
  `project.convert`'s docstring example shows the block; the FILL IN test covers "key"; the
  hivevar journey pastes; new_table's report is tested to print the block, its query's tag at
  hive.hql, the name its Conversion folder keeps a query given as text under. Answered:
  promote's block is keyed by each prod copy's name, as promote's decision step asks, which
  is the name check() writes there; the runner journeys and the answer-again ones type, as
  the user does in those cases; `paste_lines` is a function of decisions.py, no public name.

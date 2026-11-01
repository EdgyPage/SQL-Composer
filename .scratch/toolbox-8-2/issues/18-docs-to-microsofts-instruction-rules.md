# Every doc to Microsoft's instruction rules, then every Workflow tested again

Type: task
Status: resolved
Blocked by: 17
Size: L

## Question

The user (2026-11-01): "Create a new ticket that updates all documentation to the rules of the
copilot instructions from Microsoft. Redo all tests for all workflows after rewriting the
documentation." The rules, from Microsoft Learn's "Write effective instructions for
declarative agents", are written down in `docs/agents/instruction-rules.md`.

Found first, on the Excel path, the user asking for better results there: the Excel held-out
round scored 85% of 39 with one proxy answering every workbook in one reply, reading its
message in pieces; given five workbooks a proxy, as a person gives one to a fresh chat, the
dev split scores 97% (X43 missed both of its Power Queries, listed after the sheets). Files 11
and 12 word the step-or-final decision twice, differently, and close with a self-check of two
wishes.

## Done when

- `docs/agents/instruction-rules.md` holds the rules, and `docs/agents/standards.md` points to
  it for docs.
- Each document a person or Copilot follows is rewritten to the rules, its facts unchanged:
  - each Copilot file, 00 to 14, and any file the rewrite adds (Excel's workflow, its decision
    rules, output contract, examples and self-check, in a file of its own if 11 and 12 can't
    hold them under 8,000 characters), with `00_start_here.txt` and each doc naming the files
    the Excel path loads;
  - the README template, `docs/clean-branch-readme.md`, and `docs/workflows.md`;
  - each how-to's prose in `worked_examples/how_to/`;
  - the Formula workbook's Steps sheet;
  - the text cells of each Workflow notebook and Table notebook the Toolbox writes.
- `tools/excel_eval.py proxy` takes a few tasks at a time (`--tasks`), and the Excel and Copilot
  evaluations' rounds give each proxy a few tasks, as `docs/copilot-eval.md` says.
- Every test runs again on the rewritten docs:
  - the full pytest;
  - the Copilot evaluation, arm C, every objective: dev until it holds, then held-out once;
  - the Excel evaluation, arm C: dev until it holds, then held-out once;
  - the usability loop, from main as the rewrite leaves it: each dev scenario (W1 to W5, E1
    to E3) three times and each held-out one (H1, H2, E4) once, fresh agents;
  - each score recorded beside the last, in `.scratch/copilot-eval/results.md` and
    `.scratch/usability-loop/results.md`.
- The beginner reader reads the rewritten README template and Copilot files; its report is
  linked here.

## Answer

Six agents, each in a worktree, rewrote a set of documents to the rules; their sources were
taken onto dev and every output regenerated: Copilot files 01 to 05, 06 to 10, 00, 13, 14 and
`_always.txt`; the README template and `docs/workflows.md`'s wording in `tools/workflow_graph.py`;
the 29 how-tos' prose (`tools/how_to_page.py` now shows numbered lists and bold); the Steps
sheet, the Workflow notebooks' text cells (`Step.goal`, `action`, `done_when`, a Terms list
picked from what each cell says), the Table notebook Templates and a converted table's text
cell. Files 11, 12 and the new 15 were written here. `tests/test_copilot_files.py` holds every
Copilot file to the shape (Terms, a closing Self-check); `tests/test_how_tos.py` each how-to's
steps; `tests/test_workflow_steps.py` each Workflow step's goal, action and done-when.

Two choices the ticket didn't name, for the user to keep or undo:
- The Excel path loads files 15, 11 and 12 and Copilot answers with Hive alone; it wrote
  Toolbox code too, by files 03, 04 and 05, which the convert Workflow writes from the Hive,
  checked. The Hive is what a person saves and converts.
- `project.convert` keeps Hive passed as text from its first line to its last, ending on one
  line break: Hive pasted after `HIVE = """` and a line break shifted every line number in
  batch.md by one (found by the evaluation's T32 and T37; tested by
  `test_hive_pasted_any_way_is_kept_from_its_first_line_to_its_last`).

The evaluations, each proxy given a few tasks as a person asks one per chat (`excel_eval.py
proxy --tasks`; the others one objective each), are in `.scratch/copilot-eval/results.md`:
- Copilot files 01 to 14: dev 96%, then 100% once shared rule 1 again let a name in the
  user's own code through; held-out 100% of 13, a clean score.
- The Excel path: dev rounds 97%, 97%, 100%, 100% and the last on the final files (round 5);
  held-out 82% once, its failures then written into files 15 and 12, so the 97% after is a
  second look, marked so. The Excel scorer gained `reads`: an answer typing in a Table's
  sample rows, where it should read the table, fails.

The usability loop, from main as bf383aa left it (`.scratch/usability-loop/results.md`, "The
ticket 18 round"): every dev scenario 3/3 (W1 to W5 with no question, E1 to E3 with the one
conversion each asks Copilot for), and each held-out one 1/1 (H1 and H2 with none, E4 with
one). E3-2 asked a second time only because the loop showed an attached Table's Total Row as a
typed row; the loop now names it as the Excel evaluation does, tested. What the round found,
none failing a run, is listed there for after 8.2: chiefly file 11 on Excel's AND() and OR(),
`--cells` needing the imports and names cells, and `check_key` on a partitioned table.

## Review

- Standards: no hard finding. `said` and `read` renamed for what they hold; a test holds each
  Workflow step's three texts. Left: the term definitions written in four modules
  (`NOTEBOOK_TERMS`, the Template's, a converted table's, how-to 29's), a judgement call.
- Spec: the README's Excel chart still named 03, 04 and 05, written by
  `tools/workflow_graph.py`: fixed there. Files 15 and 00 now give every step a goal, an
  action and a done-when; file 13's steps stay short, its 17 characters spare leaving no room.
  The second held-out look is labelled in its row.
- Beginner reader: `.scratch/toolbox-8-2/reports/18-beginner-reader.md`; its three costliest
  stops are fixed, the smaller ones listed there as follow-ups.

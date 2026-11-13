# Memo for the Copilot and Excel evaluations

Type: task
Status: open
Blocked by: -
Size: M

## Question

Each round of `tools/copilot_eval.py` and `tools/excel_eval.py` asks every task again (Q11b).
How does a round ask only the tasks whose text changed?

## Done when

- Each task's reply and score is kept under a key made of:
  - the task's id and text;
  - the arm;
  - the model;
  - the hash of the text that arm loads, such as the one objective file for arm C, or file 00
    and the file it names for arm R.
- The store is in `.scratch/copilot-eval/memo/`, plain files, one per key, so a round's
  replies stay readable and can be scored again.
- A `plan` command names, for a split, arm and model, the tasks to ask and why: no reply kept,
  the text changed, or `--fresh`. The rest are taken from the memo.
- `prompts` and `proxy` write only the tasks `plan` names. `score` scores the kept replies
  with the new ones, and its results row says how many came from the memo.
- Held-out tasks are still scored once per files version; the memo never scores a held-out
  task against a files version it wasn't asked on.
- `docs/copilot-eval.md` says how, for the Copilot files and the Excel tasks.
- Ticket 11's three-proxy evaluation uses the same store.

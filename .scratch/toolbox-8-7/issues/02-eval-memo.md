# Memo for the Copilot and Excel evaluations

Type: task
Status: resolved
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

## Answer

### The memo (built 2026-11-13)

- **The store.** `tools/eval_memo.py` keeps each reply in `.scratch/copilot-eval/memo/`, one
  plain file per key, named `<task>-<arm>-<model>-<hash of the key>.md`. Each file holds its key's
  parts, the date asked, the score line, then `## Reply` and the reply as it came.
- **The key.** It is the task's id and a hash of its text (the prompt `prompts` prints), the
  arm, the model, and a hash of the text the arm loads:
  - nothing in A0;
  - the README's opening in A1;
  - the objective's file in C;
  - for the Excel tasks' C, files 15, 11 and 12;
  - in R, file 00 and the first file the reply names.

  A held-out task in an arm that loads a Copilot file (C, R, and Excel's C) also carries the
  files version: one SHA-256 of every file in `copilot/`, by path and bytes, line endings
  read as `\n`.
- **The tools.** Each tool gives its own `memo_key(task_id, reply, arm, model, files)`, and
  `eval_memo` does the rest:
  - it adds the commands' arguments (`add_round_commands`);
  - it plans and prints a round (`round_plan`, `print_round`);
  - it gathers the replies to score and keeps them (`round_replies`, `keep_round`, `memo_line`).
- **The commands.**
  - `plan` prints the files version, then one line per task: `ask:` and why, or `from the
    memo` and its file.
  - `prompts`, `template` and `proxy` write only the tasks to ask, or print `Nothing to ask`.
  - `score` scores the answers file's replies with the round's kept ones, writes each back with
    its new score, prints `N of M replies from the memo`, and adds a `from memo` column to
    both tables in `results.md`.
- **Ticket 11** can use the store as it is: give `hashed_key` its task's id and text, the arm,
  the model and the loaded text, and call `task_plan`, `write_kept` and `read_kept`. It needn't
  go through the CLI glue.

**Decided:**

- **Why a task is asked.** The plan gives a fourth reason beside the ticket's three: "the text
  arm X loads changed". It says which part of the key moved.
- **`--fresh` and held-out tasks.** `--fresh` asks every dev task again, but never a held-out
  task already asked on the same key. A held-out task is "scored once per files version", and
  `--fresh` would break that.
- **Which held-out tasks carry the files version.** It is in the key only for arms that load a
  Copilot file. In A0 and A1 a held-out task is asked once, until its text or the arm's text
  changes: those arms load no Copilot file, so a files change can't move their replies.
- **Which files version a new reply is kept under.** It is the one the answers file's header
  names, as `memo_files:`, not the one `score` sees. `template` writes the line, `plan` prints
  the value for a proxy round's header, and `score` refuses a held-out reply whose header
  lacks it. A held-out reply asked on one version and scored after `copilot/` changed is kept
  under the version it was asked on. The round's kept held-out replies are taken by that
  version too. The header's `files:` stays the git tree hash for `results.md`.
- **Arm and model come from the header.** `score` refuses an answers file whose header lacks
  either, since the memo keys on both. `plan`, `prompts`, `template` and `proxy` need
  `--model`, and `prompts` and `template` need `--arm`, because the tasks to ask depend on
  both.
- **`template` writes only the tasks to ask.** Otherwise an empty block left from the template
  would be scored as a new reply and replace a kept one. `template(split)` became
  `template(tasks, memo_files)`.
- **`score` with no `--split`, `--objective` or `--tasks`** scores the file's replies alone,
  as before, and still keeps them.
- **The memo is committed.** It lives under `.scratch/` with the runs, so a round's replies stay
  readable and can be scored again on another computer. A key's file is overwritten when the
  same key is asked again. Earlier keys stay, which is how `plan` can say what changed.
- **Arm R** falls back to file 00 alone when its reply names no file, or a file `copilot/`
  doesn't have.

## Code review

Run with this ticket as the spec and 89798750 as the fixed point. Its sub-agents ran as
`review-standards` and `review-spec`, on Sonnet.

**Standards**

- **Hard: one way per job.** `round_plan`, `tasks_to_ask`, `_score_answers`, the parser wiring
  and `main`'s tail were the same in `copilot_eval.py` and `excel_eval.py`. **Fixed:** they
  moved into `eval_memo`: `add_round_commands`, `round_plan`, `print_round`, `round_replies`
  (now one `RoundReplies`), `keep_round` and `memo_line`. Each tool keeps:
  - its `memo_key`;
  - an `asked_text` for its own prompt, template and proxy formats;
  - a `_score_answers` of about a dozen lines that calls its own scorer, report and results
    row.
- **`memo_key` named three ways.** **Fixed:** `eval_memo`'s is now `hashed_key`, and the two
  tools' `memo_key` share one signature.
- **Names.**
  - **Fixed:** `Key.task_text` and `loaded_text` hold hashes, so they are now
    `task_text_hash` and `loaded_text_hash`, in the file too.
  - **Fixed:** `planned()` is now `task_plan()`.
  - **Fixed:** `arm_and_model` both returned a value and refused. It is now
    `check_answers_header`, which refuses and returns nothing.
  - **Answered:** `given` is what both tools already call their parsed arguments.
- **Data clumps of `(arm, model, files)` and `(key_of, folder)`.** **Answered:** one
  `functools.partial` carries the first, and `RoundReplies` now carries the second. A wider
  record would be machinery to study first.
- **`Planned.reason == ""` alongside `kept`.** **Answered:** `task_plan` sets both, and every
  reader checks `kept`. `reason` is only the text to print.
- **`results_row`'s `from_memo=0` default.** **Answered:** the existing results-row test calls
  it without the count.
- **`plan_text` reaching through `kept.key.file_name()`.** **Answered:** this is a minor
  judgement call, and the chain is short.

**Spec**

- **Held-out replies keyed on the files at score time, not at ask time.** **Fixed:** see
  `memo_files:` under Decided. A test scores a held-out reply asked on "aaa" and finds it kept
  under "aaa". Another holds that a kept held-out reply isn't taken for a round on another
  version.
- **A0 and A1 held-out tasks are asked once, undocumented.** **Fixed:** `docs/copilot-eval.md`
  says so.
- **CLI changes beyond the spec** (`--arm`, `--model`, `--tasks` on every Excel command,
  `template(tasks)`). **Answered:**
  - "`prompts` and `proxy` write only the tasks `plan` names" needs the arm and the model.
  - `template` follows for the reason under Decided.
  - Excel's `--tasks` is what its rounds already used.
- **`score` keeps replies without `--split`.** **Answered:** a reply scored is a reply asked.
  Keeping it is what saves the next round from asking it again.
- **The extra plan reason, and `--fresh` held back on held-out tasks.** **Answered:** both
  are under Decided.
- **Arm R with no file named.** **Answered:** it falls back to file 00, as under Decided.
- **A header value with a newline could break parsing.** **Answered:** a score line's newlines
  are written as spaces. The key's parts are ids, arm and model names, and hex hashes.
- **The two `results.md` tables are ragged before the new column.** **Answered:** the table
  notes say the earlier rows have no count.
- **Ticket 11 doesn't use the store yet.** **Answered:** it is ticket 11's to do, and the
  Answer says how.

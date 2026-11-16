# File 19 holds false premises, and 8.7 is exported again

Type: task
Status: open
Blocked by: 12
Size: M

## Question

The user (2026-11-15): "add fixing file 19 to the tickets if applicable. We'll have to revert
8.7 on main and make a new 8.7, but it's a small fix."

This ticket runs only if ticket 12's baseline finds a miss: a dev premise task (M24, M25, M26)
failing on arm C. If all three pass, it closes as not needed, with the round named. The
held-out tasks, M27 and M28, never decide whether it runs or what the fix says.

## The fix

- **Fix from the dev failures only.** Each change to `tools/copilot_sources/19_metric_request.txt`
  names the dev task and the failed element it answers, as 8.7's tuning did.
- **The likely shape:** a rule beside D2 and A3. When the user states what a column or table
  holds, check it against the definitions and any pasted rows. If they disagree, say what each
  says, quoting the definition or the row, and ask which holds, with "Recommended: the
  definition". If the user keeps their reading, the request says it as they did, and part 9
  records the conflict. Also a line for "When the user says, do", such as "has one row per",
  "means", "is the day".
- **The room is tight.** File 19 is 8,722 characters against the 9,000 limit, 124 to spare.
  The fix makes room by tightening wording elsewhere in the file. Only if that can't be done
  without losing a rule does the file split, as the Copilot files' rule says, and splitting is
  asked of the user first.
- **Regenerate** with `.venv/Scripts/python tools/copilot_files.py` and
  `tools/merge_copilot_files.py`; `count_characters.py` passes.

## Measuring it

File 19 is part of every Metric task's loaded text, so a change to it re-asks every task:
- **Dev:** all 15 dev tasks on arm C, Haiku. The fix passes when M24 to M26 pass and no dev task
  that passed on 8.7's file 19 now fails. Further rounds fix only from dev failures.
- **Held out:** all 13 held-out tasks, once, on the final version of the file. Each is scored
  and recorded, including M27 and M28's first score on a fixed file. A held-out failure is
  recorded, not tuned on.
- **Cost:** `plan` prints the estimate first. From the 8.7 rounds, about 45k tokens a
  conversation, a dev round is about 700k and the held-out round about 600k.

## Shipping it as 8.7 again

- **No version raise.** The user chose to ship the fix as 8.7, as 7.2 was once exported again.
  `sqlglot_composer/version.txt` stays 8.7; there is no Upgrade step and no freeze under
  `tests/upgrade_from/`. The Toolbox's folder doesn't change, and only `copilot/` and its
  sources do.
- **CHANGES.md** gets a line under 8.7 saying file 19 now checks what the user says a column
  holds against the definitions, and when 8.7 was exported again. A user who copied file 19
  from the first 8.7 export knows to copy it again.
- **Before the push**, the definition of done: pytest, the code-review skill with this ticket as
  its spec, and the beginner reader over the changed file 19, since a beginner pastes it. Then
  the drift review over the commits the push sends, which touch `copilot/`. CI passes on the
  pushed dev commit.
- **The export:** `.venv/Scripts/python tools/export_clean.py`, from that dev commit. Each
  export builds main whole and commits it on top of what main holds. So the new 8.7 replaces
  the first one in a new commit, and main's history keeps both. There is no revert commit and
  no force-push: main moves forward, as it did from 8.6 to 8.7.
- **The push of main** is the user's step, run when they say.

## Done when

- **The fix (only if ticket 12 found a dev miss):**
  - file 19's source, `copilot/` and the all-in-one file are regenerated, each within the
    limit;
  - the dev round passes as above and the held-out round is scored once, both recorded in
    `metric/results.md` and the ledger;
  - `CHANGES.md` has its 8.7 line, and no drift item is left open.
- **The export and push:** dev is pushed with CI passing, main is exported again at 8.7, and
  main is pushed when the user says.
- **Or, if ticket 12 found no dev miss:** this ticket is resolved as not needed, naming the
  round.

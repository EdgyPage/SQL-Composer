# The tag Decision: answered, written in, answered again

Type: task
Status: open
Blocked by: 02
Size: L

## Question

Make a Script tag's value a Decision, a fifth kind beside location, Key, guessed type and
placeholder (map, "Script tags are Decisions", Q17 to Q21).

## Done when

- `decisions.py` names the kind. A table with tags has a `tags={...}` line in its Table
  reference, open while any tag in it is unanswered; its logic reads it.
- The decisions cell answers it under `"tags"`, by the table's dev name:
  `{"mart_dev.daily_close_mart": {"tags": {"PERIOD_END": "'2026-10-31'"}}}`. The answer is Hive
  text, put exactly where the tag's characters were.
- `project.write_decisions` (convert's step 3, and new_table's) writes it in. Answering again
  writes the new value over the old, as a Key marked `# proposed` is; no file is edited by hand.
- Step 2 waits on it, and step 4 (create) doesn't run while one is open. `project.check()` and
  each table's `conversion/checklist.md` name each open tag, its script and its line.
- An answer of `${hivevar:...}` works end to end. Settled here and recorded below: where its
  value is sent from (map, "Not yet specified"), with no step done by hand if it can be helped.
- 01's journey passes, its tags answered in the decisions cell alone; `KNOWN_FIDDLING` loses
  what this removes. A further journey answers a date wrong, sees the compare fail, answers
  again and passes.
- The Workflow graph and `docs/workflows.md` show convert's step 2 waiting on tags.

## Answer

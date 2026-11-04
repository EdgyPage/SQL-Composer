# Step 3 names an answer that matches nothing

Type: task
Status: resolved
Blocked by: 03
Size: S

## Question

The user, Q15: "flag mistakes". An answer in the decisions cell that matches nothing would sit
there unused while the real Decision stays open (map, "The convert notebook without cells of
your own").

## Done when

- `project.write_decisions` refuses, writing nothing, when any answer matches no Decision of
  the instance's tables: a table not in it, a kind not in the cell's words (`"tag"` for
  `"tags"`), a tag the table doesn't hold (`PERIOD_ED`), a column with no guessed type. The
  refusal names each, and the nearest name where there is one.
- A Decision made already that an answer may change, a Key marked `# proposed` or a tag's
  value, is a match.
- It holds in every Workflow with a decisions cell, a refusal through `refusals.py` as the
  others are.

## Answer
Built 2026-11-04.

- **The refusal**: `project.write_decisions` checks every answer first
  (`_refuse_answers_matching_nothing`) and refuses, writing nothing, naming each answer that
  matches no Decision of the Project's tables, with the nearest name (difflib): a table with no
  Table reference, a kind the cell doesn't take (`"tag"` for `"tags"`, `"keys"` for `"key"`), a
  column the table doesn't have, a tag its TAGS doesn't hold (`PERIOD_ED`). Every such answer
  is named at once, as "2 answers of the decisions cell match no Decision:", then one per
  line. Through `refusals.py`, as the others are.
- **A match**: a tag answered before, a Key marked `# proposed`, any column the table has.
  A column the table has whose type wasn't guessed stays a note, kept unwritten, not a
  refusal: step 3 runs again with the same DECISIONS after a tag is answered again (03), and
  a type written by an earlier run is no longer marked guessed, so refusing it would refuse
  every second run. A location or Key made already stays a note too, as before.
- **Every Workflow**: convert, promote, new_table and references all write their decisions
  cell through `write_decisions`, so the refusal holds in each.
- **Moved**: `decisions.answered_text` no longer names an unknown kind or a tag the table
  doesn't hold, since the refusal does; `decisions.tag_names` gives a reference's tags for it.
- Tests: `tests/test_decisions.py`, a table, a kind, "tag" for "tags", a column and a tag
  refused with the right answer beside it unwritten too; two at once; a tag answered before is
  a match.
- **Code review** (review-standards, review-spec, on sonnet). Fixed in a second commit: a
  table's columns are looked up by its Table reference's file name, the same key that finds
  the reference, so a reference found is never read as having no columns; the nearest table
  is named from every reference's file; `types_by_stem`, `reference_text` and
  `_unmatched_answers` for names that said less; the refusal names the table in place of
  "it". Answered: the spec's "the instance's tables" is met as the Project's tables, since
  write_decisions takes the decisions cell alone and every Workflow calls it so; an answer
  for a real table of the Project outside the batch has a Decision to answer there, and is
  written, which the map's "a table that isn't in the batch" narrows to "a table not in the
  Project"; the spec's "a column with no guessed type" is met as "a column the table doesn't
  have", for the reason above, a column it has staying a note.

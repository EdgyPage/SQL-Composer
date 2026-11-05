# Step 3 clears the needless many_matches

Type: task
Status: open
Blocked by: 01
Size: M

## Question

Step 1 adds `many_matches=True` and a `# CONVERSION:` mark to each join on a table whose Key
isn't answered yet, and nothing takes them out once step 3 writes the Keys (map, Q10, Q17).

## Done when

- `project.write_decisions`, once it writes a Key, builds each converted table of the batch
  again and takes out each `many_matches=True`, with its mark and its checklist note, whose
  Repeated-rows warning no longer fires. Its output names each one taken out.
- One still firing stays, as does every other opt-out and mark.
- A join on a table with no Key still warns and never stops.
- Only marks the Conversion wrote are taken out: a `many_matches=True` the user wrote, with no
  mark, stays.
- 01's journey answers the Key and sees the mark go.

## Answer
Built 2026-11-05.

- **`project.write_decisions`**, once an answer writes a Key into any Table reference, calls
  `_take_out_needless_many_matches(root)`: each Table folder whose logic cell holds a
  `# CONVERSION: many_matches=True` mark has its logic built again, through `preview()` (its
  `write()` refuses before `location=` is answered), and each marked `many_matches=True` is
  taken out, with its mark, when building without it shows no more Repeated-rows Warnings than
  with it. The cell is written back in place (`notebooks.write_cell_text`).
- **Its notes go too**: the opt-out's note in `conversion/checklist.md`, written again with
  `_checklist_text`, and its line under the table in each `batch.md`, its batch's or a
  finished one's (`_batch_md_mark_line`, now the one place that line is written). A note
  stays while another mark of the same name is left.
- **The report** says, for each one taken out, `<table>: took JOIN(t, many_matches=True) out
  of tables/<stem>/<stem>.ipynb, with its # CONVERSION: mark and its checklist note: with the
  Keys written, the join no longer repeats rows.`
- **What stays**: one whose Warning still fires (a Key the ON= doesn't cover, or `None`),
  every other opt-out and mark, a `many_matches=True` with no mark above its call's line (the
  user's), and any table whose logic doesn't build. A join on a table with no Key still only
  warns.
- **`converting.marked_opt_outs(logic, keyword)`**, beside `with_opt_out`: each marked opt-out
  as `with_opt_out` named it, and the logic with it and its mark taken out, for both forms
  `with_opt_out` writes (`, many_matches=True`, and a line of its own before a closing
  bracket).
- **Tests**: `tests/test_batches.py` (taken out, with the report, checklist and batch.md; one
  still firing stays; `"key": None` stays; the user's own stays; a `reads_all_partitions` mark
  stays) and `tests/test_converting.py` (`marked_opt_outs` undoes `with_opt_out` in both forms;
  no mark, no opt-out). 01's journey asserts the mark goes once `mart_dev.job_teams_mart`'s Key
  is answered; it stays xfail for tickets 05 to 09.

## Review

Code review, with 04 and 11:

- **Fixed:** the loop's index is `next_to_try` and the count `warning_count`, from
  `_repeated_rows_warning_count`; the place an opt-out's note names, `OPT_OUT_NOTE_PLACE`, is
  written once, for `_checklist_notes` and `_take_out_notes` both.
- **Answered:** it builds every Table folder holding a mark, not only the batch's: a Key
  written for one table can make a join in another needless, as a source table's Key answered
  in the references Workflow does. Each mark is tried in turn with the others still in place,
  and one still needed is kept, so the order changes nothing a Warning would say. 01's journey
  holds the mark's going once the journey passes, with 09.

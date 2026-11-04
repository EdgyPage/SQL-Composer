# Beginner reader: ticket 05, DECISIONS printed to paste (2026-11-04)

Run on the newest Opus in a scratch Project: convert, check(), the block pasted and partly
filled in, write_decisions. 16 stops; what was done with each:

| # | The stop | Done |
|---|---|---|
| 1 | where the block goes; does a later, smaller block lose answers? | "Paste this over the DECISIONS = ... line of <notebook>, <batch>'s decisions cell, or over a DECISIONS you pasted before (each answer step 3 wrote already is kept)" |
| 2 | "FILL IN" with its brackets taken off is taken as an answer; "run steps 6 and 7 again" when they never ran | any answer holding "fill in", in any case, is no answer (`is_left_to_fill_in`); "if the table is written already, run steps 6 and 7 again" |
| 3 | a proposed Key is left out without a word; "A Key marked # proposed is made" | the cell says "A Key the Toolbox proposed, marked # proposed in its Table reference, is kept unless you answer "key" here." |
| 4 | "write its answer there" | "write its answer in the decisions cell in its place, then run step 3 again" |
| 6 | the block sits outside its Workflow's entry | it names the notebook and batch, between blank lines |
| 7 | location has no example | `# its folder, such as "/data/your_team/mart_dev.db/closing"` |
| 8 | the tag hint's "with its quotes" | "the value with its own quotes, such as ..." / "the value with no quotes, such as "failed""; write_decisions' docstring the same |
| 9 | 200-character comment lines | the hints shortened |
| 10 | "<FILL IN>" is text where a list goes | `# a list, such as ["job_id", "dt"], or None when no columns name one row` |
| 11 | convert's docstring block wraps | its lines fit, shortened with ... |
| 12 | step 2's Action never mentions the block | it does |
| 13 | write_decisions' docstring never says <FILL IN> | it does |
| 14 | a guessed type pre-filled "string" | "then fill in each <FILL IN> and check each guessed type" |

Left: 5, check() lists the questions above the block (kept: a placeholder, filled in by hand,
is in the list and not the block, and the list reads without the block); 15, a traceback from
convert for a column the table lacks, and 16, do_next()'s output with no heading, both older
than 8.3 (Q6).

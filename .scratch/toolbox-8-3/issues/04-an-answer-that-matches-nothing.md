# Step 3 names an answer that matches nothing

Type: task
Status: open
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

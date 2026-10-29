# File 12 shows a query and the Table it loads, read apart, by example

Type: task
Status: claimed
Blocked by: 21
Size: S

## Question

Ticket 21 fixed one held-out cause but not the other: with two wordings of the rule, Haiku
still took a loaded Table for a step when another query reads the query that loads it, and
the two share a name (X70, X73). Sonnet never did. The misses file suggests an example rather
than another rule. The user (2026-10-29): "Try the example".

## Done when

- Four new tasks for that case, written and committed before file 12 changes: X75 and X76 dev,
  X77 and X78 held out, each a query and the Table it loads sharing a name, the Table adding a
  formula column, another query reading the query.
- File 12 gains a short example of the case, within 8,000 characters.
- At most two dev rounds, Haiku, arm C; then held-out once, Haiku and Sonnet, arm C, on the
  whole split, against ticket 18's thresholds, and on X70, X73, X77 and X78 for this case.
- `.venv/Scripts/python -m pytest`, the code review, the beginner reader and the drift review;
  then the user's call on pushing dev, CI and the export.

## Answer

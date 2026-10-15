# Joins

Type: task
Status: open
Blocked by: 01
Size: M

## Question

Map family 5. `SEMI_JOIN` (LEFT SEMI JOIN; only the reading side's columns selectable),
`ANTI_JOIN` (LEFT JOIN ... WHERE key IS NULL), `FULL_JOIN`, `JOIN(..., broadcast=True)` (MAPJOIN
hint); `RIGHT_JOIN` refused, its fix the swapped LEFT_JOIN. Keys carried through each (ticket 01).

## Done when

- Each join's Hive and rows in both Editions; the Example database gains a table for FULL_JOIN
  to reconcile if it needs one; a how-to on semi-, anti- and full joins.
- Both runs pass, the code-review skill has run with this ticket as its spec, its drift items are
  closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's Definition of done).

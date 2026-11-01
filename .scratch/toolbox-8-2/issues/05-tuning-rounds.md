# Tuning rounds: fix what dev runs find

Type: task
Status: open
Blocked by: 04
Size: L

## Question

What a zero-context user needs that the docs, the Steps sheet, the notebooks and the refusals
don't give, found by the dev scenarios (map, "The loop": Q8).

## Done when

- Each round: fixes from dev failures only, to what a user reads (the README, the how-tos, the
  Steps sheet, notebook text, refusal messages, Copilot files), each a commit naming the runs
  that showed it; a Toolbox bug a run finds fixed too, test first, or a ticket of its own if it
  is large.
- Then every dev scenario runs three times again, and the round is recorded.
- Done once every dev scenario passes three of three in two rounds running, and the questions
  asked fall to what the scenario's job can't say.
- The beginner reader reads what changed most, and its report is linked here.

## Found since round one's note

- E3-1: the non-technical user typed the Daily table's Total as a data row, its SUBTOTAL
  formulas reading their own column, not the Table's Total Row (Table Design > Total Row): the
  Steps sheet should say how to turn the Total Row on. The converter fixed a copy by hand.
- E3-1: the relay missed its question; the converter waited and ended stuck (the loop's fault,
  rerun after relaying).

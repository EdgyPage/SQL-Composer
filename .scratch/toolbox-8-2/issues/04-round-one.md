# Round one: main's docs as they ship

Type: task
Status: open
Blocked by: 01, 02, 03
Size: M

## Question

How far a zero-context user gets today, before anything is fixed (map, "The loop": Q13).

## Done when

- Every dev scenario runs three times and every held-out scenario once, each with fresh agents,
  on the Clean tree as it builds with 01 in, and each run is recorded.
- `.scratch/usability-loop/results.md` has round one's rows and a note: each scenario's passes,
  questions asked, and where each failed run stopped, quoted from its log.
- Each failure is sorted: a doc gap (what a user reads didn't say it), a Toolbox bug, or the
  scenario's own fault; nothing is fixed in this ticket.

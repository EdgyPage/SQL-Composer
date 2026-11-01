# Round one: main's docs as they ship

Type: task
Status: resolved
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

## Answer

Round one ran 2026-11-01 on the Clean tree built from 01df34c: every dev scenario three times,
every held-out once, 27 runs, each recorded in `.scratch/usability-loop/results.md` with round
one's note. 24 passed. W1 (0/3) and H1 (0/1) failed on the scenario's own naming: each agent did
the whole job and named its copy as the original, where the key holds only the Toolbox's
default name. E3-1 passed once the relay, late, passed on its question. The note sorts every
finding into the scenario's fault, the loop's, a Toolbox bug or a doc gap; ticket 05 fixes them.

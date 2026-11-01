# The held-out round

Type: task
Status: resolved
Blocked by: 05
Size: S

## Question

Whether the fixes help a user with a job the loop wasn't tuned on (map, "The loop": Q8).

## Done when

- Each held-out scenario runs once on the docs as tuning left them, with fresh agents, and is
  recorded whatever it scores; nothing is changed after it for that version.
- Its score is set beside round one's in `.scratch/usability-loop/results.md`, with a note.

## Answer

The held-out round (2026-11-01, main from bcb2239f, the docs as rounds one to three left them)
ran H1, H2 and E4 once each, fresh agents: all three passed, 3 of 3, where round one passed 2
of 3 (H1 named its copies by hand). H1 named them through RENAME with no question; E4 asked
Copilot once, for the conversion. Its note, beside round one's scores, is the last section of
`.scratch/usability-loop/results.md`. It found one Toolbox gap, a FROM subquery of rows typed
in kept whole as Unchecked Hive, ticket 16; nothing in the docs is changed after it for 8.2.

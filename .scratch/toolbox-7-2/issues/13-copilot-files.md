# The Copilot files, one per objective, each at most 8,000 characters

Type: task
Status: open
Blocked by: 12
Size: L

## Question

Ticket 12's request: objective-based files Copilot loads one at a time, every file at most
8,000 characters, and "a helper script to count the characters".

## Done when

- `copilot/` holds `00_start_here.txt` and the ten objective files `01` to `10`, each at most
  8,000 characters, each standing alone: Objective, the shared Rules, the Names for the
  objective (generated, with signatures), Steps, worked examples, Do/Don't, Self-check.
- `copilot/count_characters.py` counts them, standard library only, and exits 1 over the limit.
- `tools/copilot_files.py` renders them from `tools/copilot_sources/`, refusing any file over the
  limit; `tests/test_copilot_files.py` holds committed equals generated, the limit, every code
  block running on the Example database, public names only, no glossary word to avoid, no URL.
- `copilot/` ships on main; the README, CHANGES.md's 7.2, CONTEXT.md, CLAUDE.md and the drift
  list say so.
- CLAUDE.md's Definition of done, the beginner reader included.

## Answer

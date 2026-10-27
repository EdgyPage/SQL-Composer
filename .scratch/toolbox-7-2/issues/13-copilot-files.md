# The Copilot files, one per objective, each at most 8,000 characters

Type: task
Status: resolved
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

Built 2026-10-27, after ticket 12's baseline. `tools/copilot_files.py` renders
`tools/copilot_sources/` into `copilot/`: each objective file has the same parts (Objective,
Load this file when, the shared Always block from `_always.txt`, the Names for this objective
with each signature from `inspect.signature`, Steps, a Worked example, Do and don't, Before you
answer), and refuses one over 8,000 characters as `copilot/count_characters.py` counts it:
every character, spaces and line breaks included, and the larger of the count as saved and
with Windows line breaks.

The counts, files adcab40d:


Settled while building:

- The headings avoid the glossary's words: the shared block is "Always", not rules, and the
  self-check "Before you answer". The avoid-word test reads a curated list of the words that
  can only mean the wrong thing (raw SQL, guardrail, snippet, CTE as a name...), as "check",
  "import" and "case" are also everyday words.
- A file's names heading says "with their arguments", not "use no others": the files rightly
  use names other files list, as `equals` in file 07.
- A code block that calls a Project action (project.start, convert...) is read, not run, by
  the tests; every other block runs in the stand-in Project on the Example database, and a
  logic cell's functions that take nothing are called.
- Two examples mirrored held-out tasks (file 08's `check_key` of `job_owners` over 2026-09-20
  to 24, as T24; file 10's failed/slow/ok chain, as T30), which would leak their answers: both
  were replaced with other tables and conditions before any held-out run. Dev tasks may
  resemble the examples; the held-out split is the measure.

First measure, arm C on the dev split, Haiku, files 353cbeeb (before the two examples were
replaced): 100% passed, against 30% for A1 and 20% for A0 (`.scratch/copilot-eval/results.md`).
Ticket 14 scores the held-out split.

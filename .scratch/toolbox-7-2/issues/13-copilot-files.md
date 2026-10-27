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

The counts, after the reviews' fixes:

    00_start_here.txt: 2,773 characters (2,819 with Windows line breaks), limit 8,000: 5,181 to spare
    01_imports_and_project.txt: 6,563 characters (6,694 with Windows line breaks), limit 8,000: 1,306 to spare
    02_table_references.txt: 7,195 characters (7,327 with Windows line breaks), limit 8,000: 673 to spare
    03_build_a_statement.txt: 7,311 characters (7,467 with Windows line breaks), limit 8,000: 533 to spare
    04_joins.txt: 7,229 characters (7,369 with Windows line breaks), limit 8,000: 631 to spare
    05_windows_and_subtotals.txt: 7,128 characters (7,272 with Windows line breaks), limit 8,000: 728 to spare
    06_save_a_table.txt: 7,381 characters (7,524 with Windows line breaks), limit 8,000: 476 to spare
    07_convert_hive.txt: 7,458 characters (7,598 with Windows line breaks), limit 8,000: 402 to spare
    08_check_and_compare.txt: 6,225 characters (6,347 with Windows line breaks), limit 8,000: 1,653 to spare
    09_fix_a_refusal.txt: 6,846 characters (6,974 with Windows line breaks), limit 8,000: 1,026 to spare
    10_hand_written_hive_and_functions.txt: 6,937 characters (7,071 with Windows line breaks), limit 8,000: 929 to spare

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

## Reviews

- Beginner reader: [reports/13-beginner-reader.md](../reports/13-beginner-reader.md). Fixed:
  - 32, 33 (file 06 against the real notebook): 06 now teaches the saved_table Template's
    shape, READS and rows() with no argument, says run_tables sends the writes with their
    Session settings first, and sends the dynamic_partitions setting before a write sent by
    hand. Its second example, a Table reference, went to make room (file 02 has it).
  - 6 (one file per chat): Always now says to use the names this file shows, and rule 10
    names every other file by number, for the user to load in a new chat; 05 lists at_most,
    06 says what Clause and Statement are.
  - 7 (the partition bound): Always rule 5 says it whole: a value for one of its partition
    columns, in WHERE for FROM, JOIN and CROSS_JOIN, in ON= for LEFT, SEMI and ANTI, in a
    Derived table for FULL; 07 says to bound a table the Hive read whole, or ask.
  - 1, 2, 3, 4 (00 and the counter): Hive is said to be SQL; a Table reference may be pasted
    whole; "at once" in place of "before a chat", everywhere; the counter is run from the
    download's top, and a missing file is said and fails.
  - 5, 18, 19, 21, 27, 29, 36, 39, 44, 46, 47: Always rule 1 and 3, GROUP_BY's text name,
    keeps_only_matches and broadcast in 04, rows= "looks across", d.n, HIVE and the mark in
    07, CTE named, "None among the dict's keys", where copilot/ is, the counter's folder.
  - Answered: the rest are a word met before its file explains it, or an argument no
    objective needs (returns_all_rows, Table's storage arguments, compute_statistics'
    columns=); each is in the Names list, and the files may not grow past 8,000 characters
    to explain every argument.
- Code review of 221376a (2026-10-27):
  - Standards: fixed, the shipped counter's `from __future__` import (code a user copies has
    none), its one-liners and names, two functions in place of a tuple; copilot_files'
    `named`, its parenthesised test and REPLACED_ARGUMENTS, main's docstring; the tests'
    docstrings on AVOIDED and HIVE_WORDS; Always rule 5's joins; CLAUDE.md's wrap. Answered:
    the Always block is repeated by design, each file standing alone; the tests use the
    scorer's private helpers, as one test tool of another.
  - Spec: fixed, the counts; the reviews here; held-out leaks: file 10's lookup was T21's
    (team: data, web), now a region's city; file 09 quoted T27's refusal on its own table and
    day, now another table. Answered: file 02's Table reference teaches what T06 asks, as the
    file must, with another table and columns; file 05's lag and 10's first_match are the
    functions' own uses.
- Drift: D289 (CONTEXT.md's Clean branch), D290 (the export's docstrings), D291 (copilot/
  held to the strictest offline level, as user-copied code) fixed in the commit after
  221376a.

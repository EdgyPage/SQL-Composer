# Copilot file 20: PivotTables into Hive

Type: task
Status: resolved
Blocked by: 06, 10, 17
Size: L

## Question

The Copilot path's pivot rules, with the same IDs as ticket 06's (round 2, Q5: "make pivot
instructions too").

## Done when

- **`tools/copilot_sources/20_*.txt`**, written to `copilot/` by `tools/copilot_files.py`, at
  most 9,000 characters, in files 11 and 12's shape: Patterns, Terms, Rules by ID, Worked
  patterns, Self-check.
- It holds every rule in the map's Notes "PivotTables into Hive" and "Pivot filters", and has
  Copilot write `-- Pivot filter: <kind> <field>` above each such condition.
- **File 15** gives a pivot its role (a step when GETPIVOTDATA reads it, else a final), and
  **file 11's X1** no longer names PivotTables as left alone; each stays within 9,000.
- **`00_start_here.txt`** loads 20 with 15, 11 and 12 for a workbook with a pivot.
- The all-in-one file is merged again.

## Answer

Built 2026-11-19 on dev's c8c5ffbe, rebased for the review onto 669700fe (ticket 07 merged):
`tools/copilot_sources/20_excel_pivot_tables.txt`, written to `copilot/20_excel_pivot_tables.txt`,
8,997 characters with Windows line breaks (3 to spare), in files 11 and 12's shape: Patterns P1
to P8, Terms, Rules by ID, a Worked pattern, Self-check C1 to C3. This Answer is as the review
left it (below). No evaluation round ran: ticket 14 tunes it.

**What it holds, by ticket 06's IDs** (every one; a test holds each by its `- **ID** ` line):
source and name PS1 to PS4, PN1, PN2; rows PR1 to PR5; values PV1 to PV8; calculated items PC1
to PC3; totals PL1, PL2; Pivot filters PF1 to PF5 and, under them, **the mark**: on the line
above each condition, at every level, `-- Pivot filter: <kind> <field>` (in a CASE, before its
WHEN), its kind in CONTEXT.md's words, each named in the map's Marks too; GETPIVOTDATA PG1,
PG2; refused PX1 to PX7. The marks the rules ask the map for are ticket 10's words: "Column
field <name>: written as rows" (PR2), "default name" and the name proposed (PN2), "added into
the total" (PC3), NULL where Excel shows a blank (PV8).

**Ticket 07's two changes** (from the coordinator, mid-ticket): PN2 proposes the sheet's name
in snake case plus `_pivot`, or the sheet's name alone where it ends in pivot (`pivot`); PS3
reads a plain range as its sheet in snake case (`<database>.runs`), with no `<...>`, the table
it samples a Decision in convert. The scorer maps `runs` to X97's `job_runs` by the task's
`names`, so such a reply still runs.

**Shortened to fit, and how.** Each rule keeps its ID and its Hive's shape, in a line or two,
with letters for names (`f`, `x`, `b`, `i`, `n`): PR4's bins end in `..`; PF5 is the IN over a
RANK in a subquery, with "Its second read stays" so Copilot doesn't fold it against file 15's
H1; PV1's Var and Varp a STDDEV squared, "never VARIANCE"; PX1 to PX7 each "NULL" or "no
final", their reasons left in ticket 06. Hive functions are written plain, not in backticks,
as files 11 and 12 write them: a backticked call that parses as Python must be a Toolbox name
(`test_every_function_named_in_backticks_is_the_toolboxs_or_the_users`).

**The Worked pattern, for what the baseline missed most:** W1, a Column field, a slicer and
both Grand Totals: its four finals, each its own block (the pivot's own, `(by job_id)`, `(by
dt)`, `(grand total)`), each reading `<database>.job_runs`, each with the slicer's condition
under its mark, and the map's marks for rows, the default name and the slicer. Each block is
lean, runs on the Example database, and the four new sets of rows are in
`tests/snapshot/known.txt`. It is no dev task's workbook. GETPIVOTDATA's shape is PG1's words
alone, as file 11 has one Worked pattern (the review, finding 1).

**Beyond ticket 06's text, for ticket 13:** PS1's "never its cells typed in, never a CTE named
for the table it reads" is the Copilot path's own, from ticket 10's baseline misses (rows typed
in, Sonnet's "circular reference"); the code path never writes either, so ticket 13 has no test
of the code to tie it to, only the scorer's `reads` check.

**The rules checked on the dev tasks.** Replies written by hand from the rules alone, in file
15's Output, for 17 of the 20 dev pivot tasks (X86 to X88, X90 to X100, X102 to X104), scored
with `excel_eval.scored` in a throwaway test (not the CLI, so nothing reached the memo or the
ledger): every one passes. X102 needed one line of file 15 (below).

**The other files** (lengths with Windows line breaks):

- **15** (8,977): Patterns P12, a PivotTable a Table's GETPIVOTDATA reads: step, a CTE; P13,
  any other: final, and each total level shown; Final is "a Table or PivotTable"; step 5
  writes each pivot by file 20; C1 names `PivotTable`; R1's summary is a Table whose only typed
  columns are what its SUMIFS, COUNTIFS, AVERAGEIFS, MAXIFS, MINIFS **or GETPIVOTDATA** match
  on. GETPIVOTDATA is there for X102: team_report's one typed column, team, is only what its
  GETPIVOTDATA matches, the same shape as a COUNTIFS summary, and its reference gives exactly
  the teams it lists, so its teams are written in as a summary's groups; read from
  `<database>.team_report` they name a table the warehouse doesn't have. The Load line and the
  header name file 20. To fit: the Objective's end, step 2's wording, W1's map columns, W2's "A
  block each:" and Next's last sentence ("It writes and checks the Toolbox code") went; H1 to
  H5 are untouched.
- **11** (8,928): X1's "Left alone" no longer names PivotTables; the Load line names file 20.
- **12** (8,854): the Load line names file 20.
- **00** (8,984): Index P18, a workbook with a PivotTable: 15, 11, 12, 20; R6 ("A workbook is
  the one task with several files in a chat"), step 1 and C1 say 20 too; Which file lists
  `20_excel_pivot_tables.txt`. To fit: 12's and 15's lines and 18's "top to bottom" shortened.

**Beyond the files.** `tools/excel_eval.py` names the Excel files once: `EXCEL_FILES` ("15",
"11", "12"), loaded by every Excel task in arm C, and `PIVOT_FILE` ("20"), loaded too by a task
whose workbook has a PivotTable, as `files_of(task)` gives them, as file 00's Index says. So file 20
is in no memo key of the 84 formula and query tasks (their keys still change, with files 15, 11
and 12's text);
`proxy_groups` gives a proxy only tasks loading the same files. `docs/copilot-eval.md` says
so; `tests/test_eval_rounds.py`'s Index check expects 20 beside 15, 11 and 12. Left for ticket 15
(the docs): the README, `tools/workflow_graph.py`, `tools/workflows_page.py`,
`copilot/workbook_text.py`'s docstring, the Formula workbook's Steps sheet and
`tools/formula_workbook_examples.py` still say "files 15, 11 and 12".

Tests: `tests/test_copilot_files.py` (new tests hold every rule ID, the mark, and 00's row
against the evaluation's files), `test_excel_eval.py` (a new test of arm C's files and
groups), `test_eval_sources.py`, `test_eval_rounds.py`, `test_eval_ladder.py`,
`tests/repo/test_lean_hive.py`, `test_toolbox_checks.py`, `test_standard.py`,
`test_local_paths.py`, `test_code_audit.py`, `test_offline_policy.py`, `test_pointers.py`.
Not run: the whole suite.

## Review

The coordinator's review of cb492113 (2026-11-19), rebased first onto dev's 669700fe; each
finding answered in `fix(8.9): ticket 11's review: ...`.

1. **W1's fourth block.** Written: W1 now gives all four finals it lists, each a block. To make
   room, W2 (a slicer and hidden items) and W3 (GETPIVOTDATA) went, the slicer and its mark
   moved into W1's four blocks, so the mark is shown at every level; PG1's words give
   GETPIVOTDATA's shape, as file 11 gets by with one Worked pattern.
2. **Ticket 06's words, both paths equal.** PG1: the step pivot's CTE carries only the Values
   read and no Calculated Item; one LEFT JOIN of it a final where one join serves (file 15's
   H1); an item it lacks, Excel's #REF!, NULL and marked (C3 names PG1's mark). PG2: the total
   level read is a step too. PR3: Days "of one day" (else PX6). PF4: "on the date column
   itself". PV3: a quoted 'Unit Price' reads too. PS1: a source with no Hive is refused. PS1's
   two "never"s stay, noted above as beyond ticket 06 for ticket 13.
3. **Cuts restored.** File 15's R1 lists SUMIFS, COUNTIFS, AVERAGEIFS, MAXIFS and MINIFS again,
   GETPIVOTDATA beside them, with why in the Answer; file 15's Table term keeps "headers"; file
   00's R6 reads "A workbook is the one task with several files in a chat", which can't read as
   contradicting four attached files.
4. **If/then lines and terms.** PN2 (the sheet ends in pivot, or else), PV8 (the level groups
   by the base field, or else), PF2 (a blank kept, a blank hidden) and PC1 (several Values)
   have a branch a line. Terms defines Calculated Field and Item, Show Values As and its base
   field, slicer, Timeline, and "a Decision in convert"; "Row field" and "Column field", Excel's
   own words, went for room.
5. **`EXCEL_FILES`.** Arm C loads file 20 only for a task whose workbook has a pivot
   (`files_of`), so file 20 is in none of the other 84 tasks' memo keys (files 15, 11 and 12's
   edits still change theirs, as ticket 17's did); `proxy_groups` keeps a
   proxy's tasks to one set of files; `docs/copilot-eval.md` says so. A test holds both.
6. **The list named once.** `tools/excel_eval.py`'s docstrings and comments say "the Excel
   files", named by `EXCEL_FILES`, `PIVOT_FILE` and `files_of`; `docs/copilot-eval.md` names
   them once, at its Excel section's top, and says "the Excel files" after;
   `tests/test_copilot_files.py` builds its `EXCEL_FILES` from the evaluation's. The test is
   three: `test_file_20_holds_every_pivot_rule`, `test_file_20_has_copilot_mark_each_pivot_filter`
   and `test_start_here_loads_the_excel_files_the_evaluation_loads`.

Lengths after the review, with Windows line breaks: 00 8,984; 11 8,928; 12 8,854; 15 8,977; 20
8,997. `tests/snapshot/known.txt`: the four new sets of rows of W1's blocks in; of the five the
first build added, the two no test makes now out, the three dev's tests also make kept.

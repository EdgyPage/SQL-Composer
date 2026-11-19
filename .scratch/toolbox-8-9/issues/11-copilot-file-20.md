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

Built 2026-11-19 on dev's c8c5ffbe: `tools/copilot_sources/20_excel_pivot_tables.txt`, written
to `copilot/20_excel_pivot_tables.txt`, 8,987 characters with Windows line breaks (13 to
spare), in files 11 and 12's shape: Patterns P1 to P8, Terms, Rules by ID, Worked patterns,
Self-check C1 to C4. No evaluation round ran: ticket 14 tunes it.

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

**Worked patterns, for what the baseline missed most:** W1 a Column field with both Grand
Totals, its four finals (the pivot's own, `(by job_id)` and `(grand total)` shown, `(by dt)`
said), the table read from `<database>.job_runs`, and the map's marks for rows and the default
name; W2 a slicer and hidden items, each condition under its mark; W3 GETPIVOTDATA, the pivot a
CTE of the Value read, LEFT JOINed. Each block is lean (one read per CTE, only the columns read
after), runs on the Example database, and their five sets of rows are added to
`tests/snapshot/known.txt`. None is a dev task's workbook.

**The rules checked on the dev tasks.** Replies written by hand from the rules alone, in file
15's Output, for 17 of the 20 dev pivot tasks (X86 to X88, X90 to X100, X102 to X104), scored
with `excel_eval.scored` in a throwaway test (not the CLI, so nothing reached the memo or the
ledger): every one passes. X102 needed one line of file 15 (below).

**The other files** (lengths with Windows line breaks):

- **15** (8,993): Patterns P12, a PivotTable a Table's GETPIVOTDATA reads: step, a CTE; P13,
  any other: final, and each total level shown; Final is "a Table or PivotTable"; step 5
  writes each pivot by file 20; C1 names `PivotTable`; R1's summary is a Table matched by -IFS
  forms or GETPIVOTDATA (X102's team_report, whose typed teams are written in); the Load line
  and the header name file 20. To fit: the Objective's end, Table's term, R1's list of -IFS
  names, step 2's wording, W2's "A block each:" and Next's last sentence ("It writes and checks
  the Toolbox code") went; H1 to H5 are untouched.
- **11** (8,928): X1's "Left alone" no longer names PivotTables; the Load line names file 20.
- **12** (8,854): the Load line names file 20.
- **00** (8,992): Index P18, a workbook with a PivotTable: 15, 11, 12, 20; R6, step 1 and C1
  say 20 too; Which file lists `20_excel_pivot_tables.txt`. To fit: 12's and 15's lines and
  18's "top to bottom" shortened.

**Beyond the files.** `tools/excel_eval.py`'s `EXCEL_FILES` is ("15", "11", "12", "20"), as
ticket 10 left for this ticket, so arm C loads file 20 for every Excel task (every arm C memo
key changes; ticket 14's rounds ask again), and `docs/copilot-eval.md` says so;
`tests/test_eval_rounds.py`'s Index check expects 20 beside 15, 11 and 12. Left for ticket 15
(the docs): the README, `tools/workflow_graph.py`, `tools/workflows_page.py`,
`copilot/workbook_text.py`'s docstring, the Formula workbook's Steps sheet and
`tools/formula_workbook_examples.py` still say "files 15, 11 and 12".

Tests: `tests/test_copilot_files.py` (a new test holds every rule ID, the mark and 00's row),
`test_excel_eval.py`, `test_eval_sources.py`, `test_eval_rounds.py`,
`tests/repo/test_lean_hive.py`, `test_toolbox_checks.py`, `test_standard.py`,
`test_local_paths.py`, `test_code_audit.py`, `test_offline_policy.py`, `test_pointers.py`: 1207
passed. Not run: the whole suite. The code-review skill hasn't run on this ticket.

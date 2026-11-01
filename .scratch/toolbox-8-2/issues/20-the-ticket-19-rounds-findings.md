# What ticket 19's usability round found, fixed, then everything tested again

Type: task
Status: resolved
Blocked by: 19
Size: M

## Question

The user (2026-11-01), of the gaps ticket 19's round found: "Go ahead with ticket 20". None
failed a run; each cost a run a question, a guess or a reread (`.scratch/usability-loop/results.md`,
"The ticket 19 round").

## Done when

- **Tables named before an Upgrade's Databases.** The README's Update section and the upgrade
  Workflow's text say that setting DEV and PROD renames nothing: a Saved table named before
  keeps its name and folder, and new tables, conversions and promotions use the names set.
- **A Power Query without Excel at hand, and who asks Copilot.** The Steps sheet's step 7 adds
  a query the way example 03 shows (Blank Query, Advanced Editor), and says what to do when it
  can't be added: keep its M on a Power Query sheet and type its rows into the Table it loads.
  Step 12 says the step may be someone else's, such as the data team's.
- **Running a Workflow's cells.** The usability loop's runner lists a notebook's code cells,
  by number and first line (`--list`), and the loop's message names it, and says how to change
  a cell without Jupyter.
- **new_table from a query.** Its first step says that a query is converted as convert does,
  in a batch of its own that moves to finished/ once compared, and that each table the query
  reads needs its Table reference first.
- **TODO lines left.** write_decisions counts a Table reference's docstring TODO line too.
- **A Total Row's final.** File 12 and the README's Excel path say a Total Row's query may be
  left out when no one needs its total kept as a table.
- **project.do_next() with nothing left.** It says each Workflow named is done, or none is
  named, in place of "No Workflow is started".
- Everything tested again: the full pytest; the Copilot and Excel evaluations, arm C, dev then
  held-out once; the usability loop, each dev scenario three times and each held-out one once.

## Answer

- **Tables named before an Upgrade's Databases.** The README's Update step 5 has a rule for
  the mark the 8.0 Upgrade leaves in `admin/databases.py`: fill in DEV and PROD, and naming them
  renames nothing. The upgrade Workflow's step 2 says the same, beside that mark.
- **Power Query without Excel, and who asks Copilot.** The Steps sheet's step 7 copies a
  query's M, adds it as a Blank Query reading a Table by name, names it, and points to example
  03. If the query can't be added, its M goes under `Query <name>:` on a Power Query sheet, its
  rows typed into a Table of its name. "M" is in "Words used here". Step 12 is "Hand it on":
  someone else, such as the data team, may convert it.
- **Running a Workflow's cells.** `run_notebook.py --list` prints each code cell's number and
  first line, and the loop's message names it and says how to change a cell's JSON.
- **new_table from a query.** Its step 1 opens with what to do first, a Table reference for
  each table the query reads. Then it says the query is converted in a batch of its own, named
  for its table, which moves to `finished/` once compared.
- **TODO lines.** write_decisions counts a docstring's TODO line. Its docstring and
  decisions.py's say a TODO on any other line is no Decision.
- **A Total Row's final.** README step 5 leaves out a final no one needs, such as a Total
  Row, and names a Total Row's file `by_job_total.hql`. File 12: if the user says no one needs
  it, write no block and name it in the map.
- **do_next() with nothing left.** "each Workflow you started is done, or you have started
  none".

Everything was tested again, from main as 7847124 left it (`.scratch/copilot-eval/results.md`,
`.scratch/usability-loop/results.md`, "The ticket 20 round"):

| Check | Dev | Held out |
|---|---|---|
| Copilot evaluation | 100% of 26 | 100% of 13 |
| Excel evaluation | 100% of 42 | 100% of 42 |
| Usability loop | every scenario 3/3 | each scenario 1/1 |

In the usability loop, each Excel run asked one question, the convert step 12 names, and
phase 1 asked none. E3's runs used step 7's fallback, and the Total Rows were left out as asked.
What the round found, none failing a run, is ticket 21.

## Review

The code review (review-standards and review-spec, sonnet), each finding fixed or answered:

- The upgrade Workflow's `about` held the DEV/PROD note, which broke how-to 29's spliced
  bullet: the note moved into step 2's action, beside the mark that asks for the names.
- new_table step 1's action did two things, its precondition last: it now opens with "if
  `QUERIES` gives a query, first give each table it reads a Table reference".
- File 12's Total Row note split `SUBTOTAL(109,` mid-call and had no if/then: it is a bullet
  of its own, "If the user says no one needs a Total Row's total kept as a table, write no
  block for it, and name it in the map as left out."
- `copilot/` didn't hold the file 12 change: regenerated with copilot_files and
  merge_copilot_files.
- A reference with only a docstring TODO counts exactly 1: tested.
- `todo_lines` builds two named lists with `splitlines()`; `list_cells` uses `splitlines()`.
- Answered, left as is: the runner's usage text repeats its docstring's, as a command's
  usage does; the loop's message is long, but each line is one an agent of the round needed.
- do_next's message names neither case: it now reads "each Workflow you started is done, or
  you have started none".

The beginner reader's report, each stop and what changed:
`.scratch/toolbox-8-2/reports/20-beginner-reader.md`.

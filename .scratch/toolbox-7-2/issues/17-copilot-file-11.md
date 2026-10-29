# Copilot file 11: a Formula workbook into Hive, and a Toolbox draft

Type: task
Status: open
Blocked by: 16
Size: M

## Question

The user (2026-10-28) chose a Copilot file over Toolbox code: "it's more viable to create
skeleton instructions on HOW to convert xcel files and formulas in to sql for a cheap Copilot to
figure out, similar to our instruction files, than to maintain the codebase directly". The
8,000-character limit stays, as a standard for a file a person can read; Copilot may be assumed
to have every `copilot/` file.

The user's tests in their own Copilot, the same day: an attached workbook gives Copilot each
formula, in the long form `sales[[#This Row],[units]]*sales[[#This Row],[price]]`, the Table's
name, and the Power Query M inside it. So the person attaches the Formula workbook as it is.

## Done when

- `copilot/11_excel_formula_workbooks.txt`, from `tools/copilot_sources/`, at most 8,000
  characters, with the parts every Copilot file has. It tells Copilot to:
  1. read the formulas (both reference forms), the Tables and the Power Query M;
  2. read the direction from what reads what, never from names: a **source** is a Table nothing
     loads that reads no other Table, holding the sample of raw data; a **step** is a query
     (connection-only ones included) or a Table another reads; a **final** Table is one nothing
     reads;
  3. answer with the map first: sources, steps and finals, the columns each uses, each
     typed-over cell, each mark, what was ignored, and each `<...>` to fill in;
  4. write Hive, one query per final Table: each source a table, each step a CTE, the columns
     no final Table uses left out; a name it can't know as `<database>.<sales_data>`, and a
     header that isn't a valid name in snake_case inside `<...>`; a header that is valid passes
     through;
  5. write a typed-over cell as a `CASE` on the row's Key from `Keys`, or, with no `Keys`, on
     all the row's inputs, marked; a column with no typed-over cell needs no Key;
  6. follow the three lists, for formulas and for M: what converts, what converts with a mark,
     what is refused and named, never guessed;
  7. then write a Toolbox draft, saying that `convert` on the Hive writes the checked code and
     wins where the two differ.
  It tells the person to fill in each `<...>` before running `convert`, and to take out of the
  workbook anything they don't want converted.
- `00_start_here.txt` lists file 11 and says Excel work is the one load of several files: `11`
  with `03`, `04` and `05`.
- `tests/test_copilot_files.py` holds file 11 as it holds the others; its Hive and draft
  examples run on the Example database.
- `docs/clean-branch-readme.md` and CHANGES.md's 7.2 name file 11 and the template.
- CLAUDE.md's Definition of done, the beginner reader included.

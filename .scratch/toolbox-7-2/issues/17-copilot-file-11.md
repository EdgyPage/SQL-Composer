# Copilot file 11: a Formula workbook into Hive, and a Toolbox draft

Type: task
Status: resolved
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

## Answer

Built 2026-10-29. `copilot/11_excel_formula_workbooks.txt`, from
`tools/copilot_sources/11_excel_formula_workbooks.txt`, 7,634 characters (7,780 with Windows
line breaks): Objective, the Names for its Toolbox code, eight Steps, the Formulas, Marks,
Refused, Left alone and Power Query M lists, a Worked example with its Hive and its Toolbox
code, Do and don't, and Before you answer. It holds no Always block: it is loaded with files
03, 04 and 05, which do, and `tests/test_copilot_files.py` holds the other parts. The shared
rule 10 and `00_start_here.txt` say an Excel workbook is the one load of four files, and list
file 11. A new test runs each Copilot file's ```sql block on the Example database, once its
`<database>` is ops.

Settled while building:

- **"Toolbox code", not "draft"**: the glossary keeps "draft" from the Conversion folder.
- **A source is a Table's typed columns**, and a summary Table a GROUP BY, as ticket 16
  settled; the glossary's Formula workbook says so.
- **A refused formula is `NULL AS its_header`**, and anything the file doesn't list is
  refused too.
- **The words the scorer looks for are the file's**: "blank", "approximate", "held as text",
  "Parameters", the source M names, "pivot", "no Keys row", "outside" and the cell.

Reviews, on ef2ee57:

- **Spec** (review-spec): fixed IFS (`CASE WHEN c1 THEN v1 ...`, not `CASE x WHEN`), the pivot
  keeping NULL as M does, M's `<>` keeping a null, List.Max, List.Min, List.Average and
  Order.Descending, `[@[Unit Price]]`, the columns each final gives in the map, a source read
  for the columns the finals use, no Keys row needed without a typed-over value, the words for
  no Keys row and for a cell outside a Table, a catch-all for what isn't listed, telling the
  user to take out what they don't want converted, and a test running the Hive example. Kept:
  MOD as PMOD (they differ only for a negative divisor) and a lookup's LEFT JOIN, which fans
  out on a repeated key where Excel takes the first; both are rare in a sample.
- **Standards** (review-standards): no hard violation; "draft" became "Toolbox code". Kept
  "CTE", which the glossary allows for how a Derived table lands in the string, and the
  Excel-capitalised "Table", which the Formula workbook entry uses.
- **Beginner reader** (beginner-reader, opus), advisory. Its costliest three, each fixed in
  the README template: the four-file load as numbered steps, attaching 03, 04, 05 and 11;
  where the names for each `<...>` come from (the Project's `references/`, or whoever owns
  the data); and `project.convert("name", HIVE, query=query)` in `admin/convert.ipynb`, whose
  code wins over Copilot's. Also taken: checking the map, and the Keys step naming which cell
  holds what. Not taken: explaining partitions inside file 11, which file 03 does.
- **Drift**: D298 and D299 (rule 10 and the generator's docstring), fixed in fc512e9.

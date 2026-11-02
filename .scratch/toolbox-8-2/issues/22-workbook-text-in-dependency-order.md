# A workbook as text, in dependency order, with nothing but Python

Type: task
Status: resolved
Blocked by: none
Size: M

## Question

The user (2026-11-01): "Make it a ticket. Add it as ticket 22. Proceed with 21 and 22 in
whatever order is easiest. Construct some files under dev with the template, feel free to edit
the template, and keep main clean of external libraries."

A Formula workbook reaches Copilot as an attached .xlsx. What Copilot reads from it is
untested: the evaluations and the usability loop give their stand-in a text view of the
workbook (`workbook_text` in `tools/usability_loop.py`). Real Copilot can't see a query's M at
all, which is why the Steps sheet's step 7 keeps the M on a Power Query sheet. One run of a
script with nothing but Python can write that view itself, real queries' M included, in the
order each piece reads the others, and that text is what Copilot gets.

## Done when

- **The script.** `copilot/workbook_text.py` ships on main, beside `count_characters.py`, and
  uses nothing but Python's standard library: no openpyxl.
  - `python workbook_text.py costs.xlsx`, or `%run workbook_text.py costs.xlsx` in a notebook,
    writes `costs.txt` beside the workbook.
  - It writes each sheet's Excel Tables row by row, formulas as typed, then the other cells, the
    defined names, and each Power Query and its M. This is the view the evaluations already
    give their stand-in.
  - The M comes from the `DataMashup` part Excel saves (`Formulas/Section1.m`, [MS-QDEFF]). A
    workbook without one, such as a copy of the template, gives it from its Power Query sheet
    instead: `Query <name>:` with the M below it.
  - Each Table and query says what it reads and what it loads:
    - a query's `Excel.CurrentWorkbook(){[Name=...]}` Tables and the queries its M names;
    - the Table a query loads, from `xl/connections.xml` and the Table's query table, or, from a
      Power Query sheet, the Table of the query's name;
    - the Tables a formula's structured references name.
  - Its Order section lists the pieces so each comes after what it reads (`graphlib`).
  - A loop is refused, naming its pieces.
- **Fixtures on dev.** Workbooks built from the template, with real queries saved the way Excel
  saves them: a `DataMashup` part, connections and query tables. They cover:
  - a chain of a query, the Table it loads and a formula reading that Table;
  - a query reading a query;
  - a loop.
  They are built by a dev tool with openpyxl, which only dev installs.
- **One view, tested.**
  - The script's view of every Excel evaluation task's workbook equals the openpyxl view the
    harness gives today. Then the harness uses the script, so the evaluations measure the text
    Copilot gets.
  - Its view of each fixture is checked line by line.
- **The docs.** The README's Excel path and the Steps sheet's step 12 say that whoever converts
  the workbook may run the script and attach the text in place of the workbook. Copilot file 15
  reads the text's Order section (ticket 21).
- **The checks.**
  - `tools/code_audit.py` flags the script's `base64`, which decodes the `DataMashup`.
  - `tools/offline_policy.py` flags a workbook's connections, query tables and `DataMashup`.
  - Each site needs the user's OK before it is added to AUDITED or ALLOWED.
- Everything tested again, with ticket 21.

## The user's OKs (2026-11-01)

- An AUDITED entry for `copilot/workbook_text.py`'s `base64`, which decodes the `DataMashup` part
  and only reads it as text: "Yes, allow it".
- The fixture workbooks are committed files, under `tests/fixtures/`, so the user can open them
  in Excel: "Committed files". They need ALLOWED entries for their connections, query tables
  and `DataMashup`, and AUDITED entries for their base64.

## Answer

- **The script.** `copilot/workbook_text.py` ships on main and uses only Python's standard
  library.
  - `python copilot/workbook_text.py "my work/costs.xlsx"`, run from the download's top folder,
    writes `costs.txt` beside the workbook. The beginner reader found the `%run` form
    confusing, so the docs dropped it.
  - It reads the M from `customXml/item1.xml`'s `DataMashup`, and what each query loads from the
    connections and query tables.
  - A workbook with no queries gives its M from its Power Query sheet.
  - Its Order lists each piece after every piece it reads, in Excel's words.
  - A loop writes nothing and names each link.
- **Fixtures.**
  - `tools/workbook_fixtures.py` builds three: a chain, a query reading a query, and a loop. It
    uses the template and `tools/excel_queries.py`, which saves the queries as Excel does.
  - Each fixture is committed under `tests/fixtures/workbook_text/` with its text.
- **One view.**
  - `tools/formula_workbook.as_text` is the script's text. The old openpyxl view is the test
    oracle, and the two are equal for every Excel evaluation task.
  - The evaluations and the loop give their stand-in that text.
- **The docs.**
  - README step 2 has a branch for running the script and one for not running it.
  - The Steps sheet's step 12 says to run the script and attach the .txt.
  - File 15 reads the Order (ticket 21).
- **The checks.** The script's and the builder's base64, and the fixtures' DataMashup,
  connections and query tables, are in AUDITED and ALLOWED, with the user's OKs above.

Everything was tested again, from main as 2109ed37 left it (`.scratch/copilot-eval/results.md`,
`.scratch/usability-loop/results.md`, "The tickets 21 and 22 round"):

| Check | Dev | Held out |
|---|---|---|
| Copilot evaluation | 88% of 26; 06 and 13 run again, 100% of 6 | 100% of 13 |
| Excel evaluation | 100% of 42 | 98% of 42 |
| Usability loop | every scenario 3/3 | each scenario 1/1 |

X71 and X78, with their new chain (21chain-dev, 21chain-held), were scored after the round: both
passed. The dependency order put the step's CTE before the formula Table reading it.

- **The Copilot dev misses.**
  - T16 and T17 wrote a static-partition INSERT. That is valid Hive, but the scorer wants the
    reference's form.
  - T37 put the Hive in its `query` variable.
  - Files 06 and 13 didn't change, and their rerun passed every task.
- **The Excel held-out miss.** X69 gave the date-held-as-text conversion to a dt passed
  through unchanged.
- **The usability loop.**
  - Each Excel phase 2 ran `workbook_text.py` and attached its text. Each asked one question,
    the convert itself.
  - Each chain came back with its steps first.
  - Two route proxies named file 15 alone, because the loop's route message asked for one
    file. It now asks for any file file 00 says goes with it.

## Review

The code review (review-standards and review-spec, sonnet), each finding fixed or answered:

- **Fixed, in the script:**
  - the walrus, the `next()` defaults, the `Piece` alias and `from __future__` are gone;
  - `take_sheet_queries` says it changes the sheets it is given;
  - `piece_name` and `cell_text` replace `shown` and `_shown`, and `pieces_read` and
    `in_order` say what they give;
  - two mixed conditionals are unpicked;
  - `_add` adds a piece once, where three places each checked and appended.
- **Fixed elsewhere:** the test hints its task. In `tools/formula_workbook.py`, `built` is the
  one place a workbook is built and saved.
- **The template and examples are stale until the regeneration.** It rebuilds them.
- **Ticket 21's order, in more places.** File 12 says the CTE order where it names a CTE: a
  query, then the Table it loads, then a formula column reading that Table. File 11 names no
  CTE. File 15's loop rule now refuses the loop's finals, and its steps 1 and 4 are rewrapped.
- **Ticket 21's three-link chain task.** X70 already holds one: query staffed, then query
  owner_load and the Table it loads, then query busiest_owner and its Table. None was added.
- **Answered, left as is:**
  - The usability loop's view of an attached .xlsx stays its own. It stands for attaching the
    workbook itself, a path the README keeps for whoever can't run Python. A run that writes
    the text attaches the .txt, which the loop passes on as it is.
  - The three fixtures' names sit in `workbook_fixtures.FIXTURES`, ALLOWED and AUDITED: each
    entry is a site reviewed one by one, as the policy asks, not a pattern.
  - `_statement_end` and `_m_names` each scan past strings and comments: one gives where a
    statement ends, the other the names outside them.
  - `strings`, `dated` and `loads` travel together through three private helpers of one
    reader.
  - `excel_queries` takes queries as `(name, M)`, as `FormulaWorkbook.queries` holds them.
  - The file 12 Total Row example moved from file 15 to make room for the order; file 12 is
    loaded with 15 in every Excel chat.
- **The user's OK** for each ALLOWED and AUDITED entry is recorded above, under "The user's
  OKs".

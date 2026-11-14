# The docs on main

Type: task
Status: resolved
Blocked by: 06, 07, 12
Size: L

## Question

With the Example database on dev only (ticket 12), how does a user learn from main? The user's
words: "include a schema and data preview of the database relevant to the example in the howto"
(Q28, Q30, Q32).

## Done when

- **The docs pages move.** `how_to.html` and `examples.html` leave the Toolbox's folder for
  main's `docs/`, with `workflows.html` (ticket 07). The README links each.
- **Each how-to shows the tables its example uses:** each table's columns and types, and its
  first few rows, beside the code and its output. The tables shown are those the example reads.
- **An "Example projects" page in `docs/`** replaces main's `example_projects/`. For each
  Project, it shows:
  - its folders;
  - its notebooks' cells and outputs, from dev's runs;
  - its lineage, linked.
- **The README's tutorial sections** walk through the user's own Project and warehouse. Each
  step shows its code and what it gives, from dev's run. It says once that the examples'
  tables, such as `job_runs`, are an Example warehouse's, shown in the how-tos.
- **`tools/export_clean.py`:**
  - `COPIED` loses `example_projects`;
  - `docs/` ships;
  - the offline check reads the pages.

  Its tests follow.
- CLAUDE.md's description of main, and `docs/usability-loop.md` and the scenarios' phase
  messages, name the new paths.
- The beginner reader reads the README and a how-to, and its report is linked here.

## Answer

Built 2026-11-13, on dev at a586359d.

- **The pages leave the Toolbox's folder.** `how_to.html`, `examples.html` and `workflows.html`
  moved with git to `docs/main/`, where dev writes main's `docs/`; the new Example projects page
  joins them. `tools/toolbox_registry.py` names `DOCS` (main's `docs`), `DOCS_ON_DEV`
  (`docs/main`), the four `PAGES`, and `lineage_pages`, each Example project's lineage page by
  the path main ships it at. `FILES` no longer lists the pages, and `checks.py` loses `_PAGES`:
  the import self-check's missing-file stop says what a missing .py does, as the folder holds
  no page. Relative links between the pages hold, as they sit side by side as before; the
  export test follows every link from the README, page to page, and holds that each lands
  and that every file of main's `docs/` is reached.
- **Each how-to shows the tables it reads.** Under its title, `tools/how_to_page.py` writes a
  block of the Example database's tables the how-to reads, each a fold naming the table, its
  columns' count, its Partitions and its rows' count; opened, its columns and types (and
  descriptions) from DESCRIBE, and its first five rows. "Reads" is every Example database table
  named in the Hive the steps send to query or execute, or in a Statement they build: 27 of the
  31 how-tos read one or more; 01, 28, 29 and 30 say they read none. Tests: each how-to has the
  block under its title; a how-to with a result on the Example database shows a table; each
  table shown has each column and type and its first row; a made-up how-to shows exactly the
  tables its Hive reads, sent or only built.
- **The how-tos no longer import the Example database or copy main's `example_projects/`.**
  The page and the doctest give the steps two names main doesn't hold: `conn`, the Example
  database's connection, so a step reads `connect(conn)` as a notebook of yours does; and
  `example_project("intermediate")` (or `"starter"`), which copies dev's Example project into
  the folder the page runs in, in place of the 22 how-tos' `shutil.copytree(download /
  "example_projects" / ...)`. Each step 1 says it is a line of this page alone, not a Toolbox
  name, and the page's header says so too. How-to 31's notebook imports `conn` from
  `team_connection`, which the page gives as the Example database. The gallery shows a Worked
  example script's top as a Project's logic cell holds it: `from references.ops__jobs import
  jobs` in place of `import example_database` and `jobs = example_database.jobs`.
- **The Example projects page**, `tools/example_projects_page.py`, writes
  `docs/main/example_projects.html` with the page module. For each Project: its README down to
  "Running it" (which is about running the folder); every file as a tree, each linked to its
  place; each notebook's cells, each code cell with what it printed, its Warnings, its value (a
  DataFrame as a table) or the message it stopped with, run top to bottom as Run All does in a
  fresh copy of the Project, in this Python, with today, the time, commit and version pinned as
  `tools/example_project.py` pins them, so a lineage a cell writes is named as the committed
  one; each other file folded; each lineage page linked at
  `example_projects/<project>/<path>.html`, beside it in main's `docs/`. A setup cell's
  `import example_database` / `connect(example_database)` is shown as `connect(conn)` with a
  comment. 40 notebooks run in about 8 seconds; the page is about 590 KB.
- **The README's tutorial is read, not run.** "How to read this page" says the steps show their
  code and what they gave on the Example database, and once that the examples' tables, such as
  `ops.job_runs` (`job_runs` in a docstring's example), are that Example warehouse's, which the
  download doesn't hold, each how-to showing the tables it reads. Step 2 writes `connect(conn)`;
  step 1.5's connection is `conn = my_api.connect()` then `connect(conn)`; every page link is
  `../docs/...`; "Example projects" points at the page. `tests/test_readme.py` gives the doctests
  `conn`, and holds that the template names no `example_database`.
- **The export.** `COPIED` is `("copilot",)`; `build_docs` writes each page unstamped into main's
  `docs/` and the Example projects' 12 lineage pages into `docs/example_projects/`, refusing a
  page `PAGES` doesn't list or a missing one; `check_offline` reads `docs/`; the dry runs of the
  Example projects go, with main's Example projects; `check_no_example_database` refuses a
  Python import of it in any file, or a page or text line that shows one, but for `CHANGES.md`.
  The allowlist takes `docs/<page>` and `docs/example_projects/**/lineage/*.html`. Tests follow.
- **Main's tree, from `--preview`:** `.github/`, `CHANGES.md`, `LICENSE`, `copilot/`, `docs/`
  (the four pages and `example_projects/`, 16 files), `requirements.txt`, `sqlglot_composer/`.
- **The usability loop.** `HOW_TO_PAGE` is `docs/how_to.html`; the `toolbox` part hashes the
  Toolbox folder and main's `docs/` pages whole, the how-tos on the how-to page by how-to as
  before. The phase message names `main/docs/`. `docs/usability-loop.md` says both.
- **CLAUDE.md**'s first paragraph names main's `docs/` and that main holds no Example project
  or Example database. `docs/agents/standards.md`, `html_page.py`'s docstring and the drift
  reviewer's brief name the pages' new place.
- **Drift item D513** (how-tos 02 and 04 said the Example database's tables "ship inside the
  Toolbox"): both now say they are made-up tables the Toolbox's makers keep, shown under the
  how-to's title. No other "ship(s) inside the Toolbox" about it is left in the how-tos, the
  README template or the Copilot sources (the README's one left is about the Templates, which
  do).
- **Outside the ticket, kept small.** `tests/generated_memo.py` hashes `example_database/` among
  the shared inputs and memoizes the new page; the Example database's "can't run this Hive"
  refusal names `all_columns(ops.jobs)`, not `example_database.jobs`, as the Example projects
  page shows it; prose paragraphs the how-to edits pushed past 96 characters are re-wrapped.

**Regen chain:** `python tools/example_projects_page.py` must run after `tools/example_project.py`
(both projects) and after `how_to_page.py` and `example_gallery.py`, since it reads the Example
projects' files.

**Decided:** dev writes main's `docs/` into `docs/main/`, not `docs/`, since dev's `docs/` holds
dev's own files (ADRs, the agents' standards, audits) that never ship.

**Decided:** the lineage pages ship from dev's `example_projects/` at export, not copied into
`docs/main/`: one copy on dev, so a regenerated Example project can't leave a stale twin.

**Decided:** the pages ship unstamped, as they did in the Toolbox's folder; each names its
version in its title.

**Decided:** "the tables its example reads" are those named in the Hive the steps send or build,
read from the Hive, not from the how-to's prose, so the block can't drift from the steps.

**Decided:** the how-tos' steps keep running on dev, given `conn` and `example_project`, rather
than becoming text only, so every result they show is still checked by the doctest.

**Decided:** the Example projects page runs every notebook as it is committed, Workflow
notebooks included: run with its names cell empty, a Workflow's notebook stops at its first
step needing a name, and the page says so, pointing at the how-tos that run each with names.

**Decided:** the export's check reads Python by its import statements, so `upgrades.py`'s older
steps, whose strings write `from sqlglot_composer import example_database` into an old Project,
pass: they are history the Upgrade chain replays, and ticket 14's 8.7 step rewrites what they
leave.

**Beginner reader:** [report](../reports/beginner-reader-ticket-13.md), on main's README and
how-tos 2 and 11, as `--preview` built them. Taken: the Example projects' "Running it" no longer
shows (item 1); `example_project(...)` is said to be a line of the page alone, not a Toolbox
name, in each step 1 and the page's header (item 2); the README names `ops.job_runs` as the
Example warehouse's, not your warehouse's, says the how-tos' steps are read then repeated, links
the references notebook on the Example projects page, and makes `conn` (items 5 to 7); the
lineage file names a Table notebook's cell prints now match the linked page's, and the how-to
page's header names its three 14-day tables (item 8). Left for the user: `ends_a_run`'s Alias
line not shown in how-to 11 (item 3, before this ticket: the Example projects page now shows the
file); a preview of five rows that can't check a how-to's numbers (item 4: the ticket asks for
"its first few rows"; more rows, or the rows the steps read, is the user's call); the long file
list after `example_project(...)` and the 85 files it names; how-to 2's NaN against NULL and its
long step 4 (before this ticket).

## Code review

Run 2026-11-13 with the `code-review` skill against a586359d, `review-standards` and
`review-spec` on Sonnet.

**Standards:** no hard breach.

- Fixed: `built_hive`'s conditional `for` uses `shared.items_of` ("One way per job").
- Fixed: the Example projects page's cell results are a `Ran` NamedTuple, not dicts by string
  key; `cell_value` is `value_or_error`, `today` is `pinned_today` with a docstring;
  `chr(10)` is gone; `shown_as_yours` names its two replacements as constants.
- Fixed: `example_database_imports`' one condition is `imported_by`, a helper per statement
  kind; the suite's dense-comprehension rule found three more in the new tool and one in
  `tables_read`, each now a loop.
- Fixed: the tests take `PROJECTS` and `project_files` from the tool; `usability_loop.DOCS` is
  `export_clean.DOCS`, from the registry.
- Answered: the how-to page's new `.tables` CSS writes its colours as the rest of its own
  `STYLE` does: the standard says how_to.html isn't under the page module yet.
- Answered: `in_a_project`'s `ops__` prefix: every Example database table is in `ops`, and its
  query refuses any other.
- Answered: the Example projects page's small Markdown reader: how_to_page's prose reader reads
  a how-to's docstring layout, not a README's pipe tables and headings; neither is shared.

**Spec:** every "Done when" bullet built.

- Fixed: the ticket, its Answer and the beginner reader's report link (they were the last
  step).
- Fixed: `docs/example_projects.html` showed the Example database's refusal naming
  `all_columns(example_database.jobs)`; it names `ops.jobs`, and the page test holds that it
  names no `example_database`.
- Answered: `upgrades.py`'s strings: see the last **Decided**; ticket 14's.
- Answered: `checks._PAGES`, `generated_memo.py`, `conftest.py`, `standards.md` and the drift
  reviewer's brief follow from the pages' move; `check_offline` reads `docs/`, held by the
  test of a page loading a script from the internet, for both a page and a lineage page.
- Checked: the phase message names `main/docs/`; the scenario files name no old path.

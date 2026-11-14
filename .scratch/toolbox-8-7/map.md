# Toolbox 8.7: faster dev loops, lineage pages, Hivevars, Metric requests, a leaner library

Label: wayfinder:map

The user (2026-11-13), with 8.6 exported to main: "all seven ideas that are parked for the next
version. And a development only optimization to speed up development time and reduce token
spend: I want to take a look at the user testing pipelines and memoize to reduce processing
times wherever possible." Later the same day: "make sure the lineage traces from scheduled runs
match the changes of the other lineage traces. And let's debloat the main library by taking out
the examples from the code, but keep the examples documentation. I do not want runable python
code for examples and demos inside the main library." Grilled the same day, Q1 to Q32, every
question settled; the user named it 8.7 (Q1: "no one uses this yet but me").

## Notes

### What is there today (8.6 at d1757e59)

- **The usability loop** memoizes per scenario (8.6's ticket 11), but its `inputs_hash` holds
  one hash of main's whole tree. Any change to main, a how-to's typo included, runs all 14
  scenarios again, three Haiku runs for each dev scenario.
- **The Copilot and Excel evaluations** keep no memo: each round asks every task again.
- **The pytest suite** runs on one core of the user's 24. Its slowest 40 tests take about 8½
  minutes:
  - `test_code_audit::test_the_repo_reads_clean`, 183 s;
  - the how-to page's "committed is generated", 51 s;
  - `test_export_clean`, 10 to 17 s each, about 3 minutes in all.
- **Lineage pages.** There are two page builders: `lineage.py`, for `export_lineage` and
  `export_run_lineage`, and `project_lineage.py`, for `export_project_lineage`.
  - All three exports write an HTML and a Markdown page, each with its own inline CSS and
    script.
  - The pastel fills are written out in the CSS, the legend and the Mermaid alike.
  - Clicking a box lights up its path. A box's full Hive is in a report below the drawing, and
    a long step's text runs past its box.
- **The Example database** is inside the Toolbox:
  - `example_database.py`, and the part of `engine.py` that runs its queries;
  - the public name `example_database`;
  - 15 Toolbox files that mention it, and docstring `>>>` examples that import it;
  - main's `example_projects/`, which connect with `connect(example_database)`;
  - the README tutorial, which runs on it;
  - all 31 how-tos, which import it.

  `how_to.html` (1.3 MB) and `examples.html` (450 KB) are half the Toolbox folder's 3.7 MB.
- **A Script tag** can already be answered with Hivevar text, `"'${hivevar:period_end}'"`. It
  has no default, and the Toolbox sends no value for it.
- **SORT_ARRAY.** On sqlglot 30.23.0, 16 shapes of the user's
  `CONCAT_WS(' | ', SORT_ARRAY(COLLECT_SET(x)))` convert to one argument. The `True` the user
  saw comes only from a source that already said `SORT_ARRAY(..., TRUE)`, Spark's form, which
  sqlglot keeps.

### Dev only: memoize the testing pipelines (Q2, Q11, Q24)

These come first, so that every later round costs less. None of them ships.

- **The usability loop.** Each scenario is keyed on what its agent reads, not on main's whole
  tree:
  - the README, hashed section by section, the sections its path uses;
  - the how-tos and Copilot files its path uses;
  - the Toolbox folder, whole, since code changes behaviour;
  - the files its phase messages name.
- **The Copilot and Excel evaluations.** Each task's answer and score are kept, keyed by task,
  arm, model and the hash of the text that arm loads. A round asks only the tasks whose text
  changed.
- **The pytest suite.** The user's words: "dev has looser restrictions. be sure when you're
  using multiple cores to release memory when the tasks are done. you may want to look in to
  making a test dependency tree to keep all relevant tests on certain cores."
  - **The code audit** keeps each file's result by its content hash, plus the hash of the
    audit's own code and its `AUDITED` list, in a git-ignored folder.
  - **The export tests** share one Clean tree per session among those that only read it.
  - **Generated pages** are regenerated only when an input's hash changed.
  - **pytest-xdist** spreads the tests across cores, with tests that share a costly fixture
    grouped onto one worker, and each worker's memory freed when its group is done.
  - CI still runs every "committed equals generated" check whole: a local shortcut never
    passes what CI would fail.

### Lineage pages (Q3 to Q5, Q14, Q15, and the user's addition)

- **The HTML page is the full view.** The user's words: "there must be nothing markdown can do
  that html can't. md can be for minimum viable tracing, with interactive elements and
  whatever added in html."
  - Markdown keeps each table or step, what it reads and writes, and its Hive in full.
  - A test holds that each line of the Markdown is in the HTML page too.
- **The side panel** (Q4). Clicking a box opens a panel beside the drawing; the click still
  lights the path. The panel shows:
  1. the step's full Hive, wrapped, with a Copy button;
  2. the tables it reads and writes;
  3. its Run values and the Session settings sent before it;
  4. on the Project page, which Scheduled runs write that table.

  The report below the drawing goes.
- **Bold colours** (Q5), on all three pages: the Okabe–Ito set (eight colours chosen to stay
  distinguishable with colour blindness), each fill's text dark or white, whichever reads
  better. The loops' red is used for nothing else. The user's words: "subject to testing, but
  usable here to start. swapping palettes is easy."
- **One shared page module** (Q15). It holds the colour tokens (defined once), the base CSS,
  and the drawing's and the panel's script. Every page is built from it: the three lineage
  pages and the Workflows overview.
- **An HTML section in `docs/agents/standards.md`.** The user's words: "maintain good code
  conventions for the html pages ... add coding guidelines for the html that we have for
  python". It requires:
  - colours only through named tokens, and no inline `style=`;
  - every page works offline, with text escaped;
  - scripts that run with no build step;
  - the same plain words for the user as the Python uses.

  What a test can hold goes into a test.
- **The Scheduled run's lineage page matches the others.** The user's addition. It's already a
  Statement lineage written to HTML and Markdown. It takes the same module, colours, panel and
  Markdown as the rest, and a test holds that all three pages come from the one module.

### The Workflows overview page (Q10, Q19)

- `workflows.html`, beside the other docs pages (main's `docs/`, ticket 13).
- It's interactive: click a Workflow to see its steps as bullet points and its common tripping
  points. Arrows show the hand-offs, such as a converted table going on to promote.
- It covers every Workflow, the schedule Workflow (ticket 08) and the Excel path.
- It's built from `tools/workflow_graph.py`'s steps, plus a hand-written list of tripping
  points drawn from the usability rounds' findings.
- The user's words: "Don't include all documentation, that's what the search documents for
  Copilot are for. High level to bullet points."
- A test holds that every Workflow is on it, with each step matching its notebook.

### The schedule Workflow (Q9, Q18)

- **A move, not a change.** The user's words: "I want whatever happens in
  project.new_scheduled_run() to happen. Just moving the existing functionality in to its own
  workflow."
- The notebook is `admin/workflows/schedule/schedule.ipynb`, with `NAME` in its names cell.
- `admin/scheduled_runs.ipynb` loses its `NEW_RUNS` cell. Its lineage and Hive cells (`RUNS`,
  `TABLES`) stay.
- Removing a run joins `admin/remove.ipynb`, if it isn't there already.
- `project.new_scheduled_run` stays, for code.

### Hivevar (Q7, Q12, Q13, Q20)

- **Script tags stay exactly as they are.** The user's words: "please don't revisit the script
  behavior since we got so much work in to it converting correctly."
- A tag's Decision gains one more kind of answer:
  `hivevar("PERIOD_END", default="'2026-10-31'")`, where `default=` takes text or a Run value
  function.
  - **In the Hive:** it's written `'${hivevar:PERIOD_END}'` where the tag stood, quoted as the
    tag stood.
  - **When the Toolbox sends it** (`run_execute`, `run_tables`, a Scheduled run): it first
    sends `SET hivevar:PERIOD_END=<value>`, as Session settings are sent. The value is the
    default, unless a Scheduled run overrides it by name:
    `build_run(..., hivevars={"PERIOD_END": ...})`.
  - **When exported** (`export_hive`, `export_run_hive`): no `SET` line goes in the Hive,
    because Hive lets a script's own `SET` beat a value given on the command line. Instead, a
    `<name>.hivevars` file beside it holds each default as `--hivevar PERIOD_END=2026-10-31`,
    one per line, for the scheduler to pass or change. A Run value default is worked out at
    export.

### SORT_ARRAY (Q6, Q23, Q25)

- **`hive_function` stays open.** The user's words: "I don't necessarily want to box in the
  conversions should the underlying sql change capability."
- A Conversion reading `SORT_ARRAY(x, TRUE)` writes the one-argument form, since ascending is
  Hive's default, with a `changed` finding.
- `SORT_ARRAY(x, FALSE)` is kept, with a finding that the user's Hive may refuse it.

### Copilot file 19: Metric request (Q8, Q16, Q17, Q21)

- **The aim.** It takes a user "from non-specific requirements to specific ones WITHOUT
  detailed table knowledge", most of all to define new metrics. What comes out is a Metric
  request, text for the user's chatbot that knows the indexed databases and column
  descriptions, not SQL. The user: "I don't know how hard this will be to successfully
  implement."
- **A Metric request holds:**
  1. the metric's name and one plain sentence;
  2. its formula in plain maths over named quantities;
  3. each quantity exactly, by column name where the user knows one, else in exact words;
  4. one row per what;
  5. the days counted;
  6. what is left out;
  7. the edge cases;
  8. a worked example, on the user's sample rows when they give some;
  9. the questions still open.
- **How Copilot works through it:**
  - Each column has its own section, and Copilot asks "one column or two?", and "are these two
    really one?", before going on. The user: "requirements for columns are muddled together".
  - It asks one question at a time, each with a recommended answer, and shows the formula back
    after each change.
  - It probes with questions such as "Does a retried run count once or twice?".
  - It pushes back and offers thoughtful criticism without overruling the user.
- **The file:** `copilot/19_metric_request.txt`, loaded on its own.
- **Its evaluation:**
  - **Stand-in user:** a proxy plays a user with a vague goal and a secret answer key.
  - **Grilling:** a second proxy, loaded with file 19, grills it and writes a Metric request.
  - **Stand-in chatbot:** a third proxy, given the Example database's column descriptions,
    defines the column from the request.
  - **Scoring:** a pass gives the key's numbers. The baseline is the same chatbot given only
    the vague goal.
  - **Tasks:** six, four dev and two held-out, memoized like the others.

### The Example database leaves the library (the user's addition, Q26 to Q32)

- **The library holds nothing runnable for examples or demos.** The user's words: "The users
  should consult the documentation and example htmls besides code directly. If the user has to
  consult code directly, that's a usability failure."
- **What moves to dev only:**
  - `example_database.py`, and the part of `engine.py` that runs its queries (the sqlglot check
    stays);
  - the public name `example_database`;
  - main's `example_projects/`.
- **Docstring `>>>` examples stay** (Q27, Q31). They lose their import lines and use the
  tables by name, and dev's doctest run supplies them. The README says once whose tables they
  are.
- **The docs pages move.** `how_to.html` and `examples.html` go to main's `docs/` (Q28). Each
  how-to shows the columns of the tables its example uses and a few of their rows (Q32).
- **The Example projects become a page.** An "Example projects" page in `docs/` shows each
  Project's folders, notebooks and outputs, built from dev's runs (Q30).
- **The README tutorial is read, not run.** Each step shows its code and what it gives (Q32).
- **The Upgrade** rewrites a Project's `example_database` imports and marks what it can't
  rewrite (Q29). Moving the pages needs no Upgrade step: the user replaces the Toolbox's folder
  whole.

### The version

8.7, named by the user (Q1). Its Upgrade step:
- rewrites or marks `example_database` imports;
- makes `admin/workflows/schedule/`;
- takes `NEW_RUNS` out of `admin/scheduled_runs.ipynb`.

It also freezes the Example projects at 8.6 in `tests/upgrade_from/8.6/`.

### Words

- **Hivevar** (CONTEXT.md, 2026-11-13). _Avoid_: placeholder, runtime param.
- **Metric request** (CONTEXT.md, 2026-11-13). _Avoid_: spec, prompt, requirements doc.
- **Example database** and **Example project** change with ticket 12: dev only, read on main
  as pages.

## Tickets

- [01 The usability loop's memo per scenario](issues/01-usability-memo.md)
- [02 Memo for the Copilot and Excel evaluations](issues/02-eval-memo.md)
- [03 A faster pytest suite](issues/03-faster-suite.md)
- [04 An HTML standard and one page module](issues/04-html-standard.md)
- [05 Bold colours](issues/05-bold-colours.md)
- [06 The side panel and minimal Markdown](issues/06-side-panel.md)
- [07 The Workflows overview page](issues/07-workflows-overview.md)
- [08 The schedule Workflow](issues/08-schedule-workflow.md)
- [09 Hivevar](issues/09-hivevar.md)
- [10 SORT_ARRAY's TRUE](issues/10-sort-array.md)
- [11 Copilot file 19, Metric request](issues/11-metric-request.md)
- [12 The Example database leaves the library](issues/12-example-database-out.md)
- [13 The docs on main](issues/13-docs-on-main.md)
- [14 8.7: the Upgrade step and the raise](issues/14-eight-point-seven.md)
- [15 The usability round](issues/15-the-usability-round.md)
- [16 The Copilot files use the room](issues/16-copilot-files-use-the-room.md), added
  2026-11-13 after the user raised the limit to 9,000
- [17 The Copilot files at 100](issues/17-copilot-files-at-100.md), added 2026-11-13: more
  Metric request tasks, files written to be looked up, every evaluation at 100

01 to 03 come first. Then 04, with 05, 06 and 07 after it. 08 to 12 can run alongside that
chain, and 13 after 12. 14 and 15 come last. The real dependencies are in each ticket's
`Blocked by:`.

## Records this changes

- **`sqlglot_composer/`:**
  - `lineage.py` and `project_lineage.py`, and a new page module (04 to 06);
  - `workflows.py` and `project.py` (08);
  - `script_tags.py`, `run_values.py`, `running.py` and `scheduled_runs.py` (09);
  - `converting.py` (10);
  - `example_database.py`, `engine.py`, `public.py`, `__init__.py` and the docstrings (12);
  - `upgrades.py` and `version.txt` (14).
- **`tools/`:**
  - `usability_loop.py` (01);
  - `copilot_eval.py` and `excel_eval.py` (02, 11);
  - `code_audit.py` and `export_clean.py` (03, 13);
  - `toolbox_registry.py` (04, 12);
  - `workflow_graph.py` (07);
  - `how_to_page.py`, `example_gallery.py` and `example_project.py` (12, 13).
- **Tests:** `tests/conftest.py` and the doctest setup (03, 12); `requirements-dev.txt`, with
  pytest-xdist (03); `.github/workflows/dev.yml` (03).
- **Docs:**
  - `docs/agents/standards.md` (04);
  - the README, the how-tos, the Copilot files (07 to 13);
  - `docs/usability-loop.md` and `docs/copilot-eval.md` (01, 02, 11).
- **CONTEXT.md:** Hivevar and Metric request (already, 2026-11-13); Example database and
  Example project (12).
- **CLAUDE.md:** this map, and what main holds (12, 13). CHANGES.md's `## 8.7`.

## Decisions so far

- **01:** the usability loop hashes main by part (the Toolbox folder, each README section, each
  how-to, each Copilot file) and each scenario's `reads.json` names what its path reads, so
  `plan` memoizes a scenario until something it reads changes, naming what changed.
- **02:** the Copilot and Excel evaluations keep each reply and score in
  `.scratch/copilot-eval/memo/`, keyed by task, arm, model and the hash of the arm's text, and
  a round asks only the tasks whose key changed.
- **03:** the suite runs on pytest-xdist with costly fixtures grouped per worker
  (`tests/workers.py`), the code audit and "committed is generated" tests memoized in
  `.pytest_cache/memo/`, and CI regenerating everything whole.
- **04:** one page module, `sqlglot_composer/html_page.py`, holds the colour tokens, base CSS
  and scripts every page is built from, and `docs/agents/standards.md` gains an HTML section.
- **05:** bold colours from the Okabe–Ito set, each fill with the same dark text, the loops'
  red used for nothing else, on all three lineage pages.
- **06:** clicking a box opens a side panel (full Hive with Copy, reads and writes, Run values
  and Session settings, the Scheduled runs that write it); the report below the drawing goes,
  and each Markdown line is in the HTML too.
- **07:** `workflows.html`, built by `tools/workflows_page.py` from `tools/workflow_graph.py`'s
  steps and a hand-kept list of tripping points, covers every Workflow, schedule and the Excel
  path, and a test holds each step to its notebook.
- **08:** the schedule Workflow, `admin/workflows/schedule/schedule.ipynb` with `NAME`, moves
  `project.new_scheduled_run` into a Workflow of its own; `admin/scheduled_runs.ipynb` loses
  `NEW_RUNS`.
- **09:** a Script tag's Decision may be `hivevar("NAME", default=...)`: the Hive holds
  `'${hivevar:NAME}'`, the Toolbox sends `SET hivevar:` before a write, and `export_hive`
  writes the defaults into a `.hivevars` file beside the `.hql`, never a SET line.
- **10:** a Conversion writes `SORT_ARRAY(x, TRUE)` as `SORT_ARRAY(x)` with a `changed`
  finding, and keeps any other second argument with a `kept` finding.
- **11:** Copilot file 19, the Metric request, grills a vague goal one question at a time into
  nine parts for the user's chatbot, measured by a stand-in user, griller and chatbot.
- **12:** the Example database leaves the library for `example_database/` at the repo's top,
  dev only; docstring examples keep their tables by name, and the public name goes.
- **13:** the how-tos, gallery, Workflows overview and a new Example projects page move to
  main's `docs/` (dev's `docs/main/`), each how-to showing the tables it reads, the README
  tutorial read, not run.
- **14:** 8.7's Upgrade step rewrites or marks `example_database` imports, makes
  `admin/workflows/schedule/` and takes out `NEW_RUNS`, with the Example projects frozen at 8.6.
- **15:** the usability round ran all 15 scenarios, none memoized, every run passing (W8 through
  the schedule Workflow, the new W9 a Hivevar exported); its findings were fixed in the README,
  Copilot file 18, the Workflows overview and the loop's stand-in, or recorded for the next
  version.
- **16:** with the limit raised to 9,000 characters, every Copilot file gained what the
  evaluations and beginner readers showed missing, each now 8,060 to 8,800 characters.

## Not yet specified

## Out of scope

- Changing how Script tags are read or converted (Q12).
- Narrowing `hive_function`'s arguments for `sort_array` (Q25).
- Proposals in the schedule Workflow beyond what `new_scheduled_run` does (Q18).
- The Metric request writing SQL (Q8).
- A runnable Example database on main (Q26).

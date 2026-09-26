# Build the Example gallery

Type: task
Status: claimed
Blocked by: 15, 18, 21

## Question

Build the generator for `sql_composer/examples.html` and its first standalone Worked examples, as
decided in "What does `dev` enforce, and which maintainer agents does it carry?".

- **Sources:** every docstring's `>>>` example, plus one short Statement script per standalone
  Worked example in the Example database's `statements/` folder. Each script's module docstring
  gives a title and one sentence on why you'd write it.
- **Each entry shows:**
  - its title and why;
  - the Python;
  - the Hive it emits;
  - the result table on the Example database, where the executor can run it;
  - the Toolbox names it uses, worked out from the code.
- **The page:** one self-contained HTML file with no dependency. A few lines of script filter
  entries by any word, but everything is plain HTML, so Ctrl+F still works without scripts. It
  follows the lineage research's approach ("How can one offline HTML file render an explorable
  graph?").
- **Kept in step:** the page is committed on `dev`, and a test fails if regenerating it changes
  it. It sits inside `sql_composer/`, so it ships and is on the self-check's file list.

"What does the Example database demonstrate, and where does it run?" decides the tables, the
engine and where the scripts sit. The Example database itself is built in "Build the Toolbox
core", and its demonstrations in "Build the Example database's demonstrations".

Done when the `dev` checks pass and the gallery holds every docstring example plus the first
standalone Worked examples, among them the latest-per-key and top-N-per-group patterns that
`row_number`'s docstring points to.

## Comments

**From "What does the Example database demonstrate, and where does it run?" (2026-09-25).**

- **The standalone Worked examples** are the seven demonstrations from "Build the Example
  database's demonstrations", in `worked_examples/statements/`.
- **A demonstration's entry** puts its `careless()` and `fixed()` Statements side by side. Each
  side shows its Hive and its result, with the Guard's refusal or the Warning's message under the
  careless one. The prototype's `demo.html`, tab A, on `prototype/example-database`, is the rough
  shape.
- **The `row_number` and `week_start` entries** show a pandas result labelled "computed in pandas,
  not by running this Hive".
- **On the sqlglot 25.24.2 CI run,** the regenerate-and-compare test skips with a reason.

**Build decisions (2026-09-25), where the tickets left something open.** Each picks the most
beginner-readable option; the user may overturn any of them.

- **Where the scripts sit:** the ticket says the Example database's `statements/` folder;
  "Build the Example database's demonstrations" put them in `worked_examples/statements/`, so the
  gallery reads every Statement script there, in file-name order. A later script joins the
  gallery by being added to that folder.
- **The generator is `tools/example_gallery.py`,** beside `tools/export_clean.py`: a `dev`-only
  script that never ships, since the export copies only `sql_composer/`.
  `python tools/example_gallery.py` rewrites `sql_composer/examples.html`. It needs sqlglot
  30.19.0, the `dev` pin, since it runs the Example database.
- **The seams under test:** the committed `sql_composer/examples.html`, read as text (what
  ships); `example_gallery.gallery_page()`, which returns the page, compared with the committed
  copy; the export's `build(...)`, which must stamp the page and list it in `_FILES`; and the
  import self-check, which must stop when the page is missing.
- **Order:** the Worked examples on their own come first, since they show what goes wrong; then
  every docstring's example, in the cheat sheet's order (`__all__`). The two constants share
  the Toolbox's own docstring, so they are one entry. `example_database.send`'s docstring has an
  example too, so it gets an entry after `example_database`.
- **A docstring entry** shows the name as its title and its first line (its cheat-sheet line)
  as the why, then the rest of the docstring's prose. The example is shown step by step, like a
  notebook: each step's Python without the `>>>` prompts, so it pastes into a notebook, and under
  it what the docstring shows, labelled "Hive" when it is Hive. The shown output is the
  docstring's own, which the doctests check, so `help(name)` and the gallery agree.
- **Hive and results for a docstring:** each Statement the example hands to `to_hive(...)` is
  run on the Example database, and its result table is shown. Each Statement it hands to
  `run(...)` gets its Hive shown, since the docstring shows only the result. Where the Example
  database can't run a Statement, the entry says so in one line, from its own message. Where
  a Worked example builds the same Hive and has a pandas result, that result is shown instead,
  labelled "computed in pandas, not by running this Hive": that is how `row_number`'s entry
  gets its latest run per job. `week_start`'s example builds no Statement, so its entry shows
  each day of the Example database with its week, computed in pandas by the re-grouping Worked
  example's own `with_week`, with the same label.
- **A Worked example's entry** shows its title, its why, and the rest of its module docstring;
  the top of the script (imports and the days it reads) and every Building block it imports, so
  the Python is complete; then `careless()` and `fixed()` side by side, each with its Python,
  its Hive and its result. Under the careless side is the Guard's refusal or the Warning's
  message. Where the Guard has an opt-out, the careless side also shows the Statement with the
  opt-out pasted, its Hive and its wrong result, which is what Hive would give. Any other
  Statement function in the script (`top_runs_per_job`) is shown below the pair the same way.
- **Result tables** are plain HTML tables with no index column, as Hive returns them, and a
  missing value reads `NULL`, the word the Worked examples use.
- **Toolbox names used** are the public names read from the Python shown (plus the entry's own
  name for a docstring), in the cheat sheet's order. A docstring entry also links to the Worked
  examples that use its name.
- **Today is 2026-09-25 on the page,** as in the doctests, so `last_n_days(job_runs.dt, 2)`
  reads both of the Example database's days. The page says so at the top.
- **The page:** light colours and system fonts like the lineage page; one `<style>`, and one
  short `<script>` that shows a filter box (hidden without scripts) and hides the entries that
  don't hold every word typed. Everything else is plain HTML, so Ctrl+F finds any word.
- **The README template** gains one sentence pointing at `sql_composer/examples.html`, and
  `CHANGES.md` a line under 2.0, since a user who doesn't know the page exists can't open it.

**Code review (2026-09-25), `code-review` over `ec7b7a7..HEAD`,** with this ticket and tickets
13, 15 and 04 (and the Answers of 18, 19, 21 and 22) as the spec and `docs/agents/standards.md`
as the standards. The spec reviewer checked every number on the page against the Example
database's rows and the demonstrations' docstrings, and found none wrong. Fixed in the commit
after this note:

- **Standards:**
  - 106 empty code boxes sat between docstring steps, from the blank text doctest's parser
    returns between examples. They are gone, and a test holds it.
  - A refusal read `GuardRefused:` and a Warning `RepeatedRowsWarning: ` differently. Both now
    read as Python prints them: the kind on its own line, then the four lines.
  - The README sentence set "those examples" apart from the Worked examples, though the
    glossary counts a docstring's example as a Worked example, and it had a comma splice.
  - The step labels "It shows" and "It stops" are now "Python shows" and "Python stops with an
    error"; "the opt-out pasted" is "the opt-out added".
  - `built_by` no longer writes the refusal's kind into a string for `careless_html` to read
    back; `users`, `twins` and a reused `found` are `used_by`, `pandas_results_by_hive` and
    `version`; the test's `entry_html` is `entry_section`, unlike the generator's.
- **Spec:**
  - The `run` and `example_database` entries showed pandas' printout, with its index, under
    "Result on the Example database". The printout is now labelled "Python shows", and every
    Statement handed to `run(...)`, like one handed to `to_hive(...)` or `export_lineage(...)`,
    gets its result as a plain table. So the rule is one: each Statement an example hands to
    the Toolbox shows its Hive (unless the docstring prints it) and its result.
  - A pandas result was headed "Result on the Example database, computed in pandas, ...",
    claiming the Example database in the same breath as saying it didn't run. It is now
    "Result, computed in pandas, not by running this Hive".

Answered, not changed:

- **A name every Worked example on its own uses** (`SELECT`, `AS`, `FROM`, `statement`,
  `example_database`) gets no "Worked examples that use it" links, since a list of all seven
  says nothing. The build decision above is narrowed to that.
- **`week_start`'s pandas table is a special case** in the generator, since its docstring's
  example builds no Statement and ticket 15 asks for its pandas result. It uses the
  re-grouping Worked example's own `with_week`, so the week is worked out in one place.
- **Only `RuntimeError` and `ValueError` read as "the Example database can't run this"**:
  those are what its `send` raises. Anything else stops the generator, which is what should
  happen on `dev` when something unexpected breaks.
- **The page's header adds the two lines to paste before an example, and the filter says how
  many entries it shows.** Both help a first reader, and neither is a new name.
- **Smells left, since standards.md prefers plain repetition to machinery:** `output_label`
  matches the Toolbox's class names as text (the classes aren't public names); the handed
  Statements are told apart by the function's name; `script_entry` returns four things; the
  test lists the Toolbox's modules itself rather than asking the generator, so it checks the
  generator instead of trusting it.

**Also found, not from this ticket:** the import self-check compares export stamps only in
`.py` files, so an `examples.html` (like `CHANGES.md`) pasted from another export isn't caught.
The page changes only with the code, so a stale page means a stale folder, which the `.py`
stamps already catch unless the page alone was copied.

**Drift (2026-09-25).** 83132c9 and 7df509c-before reviews: D10 opened on b147888 (the README
promised every entry's result on the Example database) and closed in 802ea13; D11 opened on
802ea13 (it promised every entry's Hive) and closed in 75c8e2f. No item is open.

**Beginner reader (2026-09-25).** Report:
[reports/20-beginner-reader.md](../reports/20-beginner-reader.md), run over the page, the
README paragraph and the CHANGES.md line. Its advice is for the user. It checked every number,
Hive and label on the page against the Example database's rows and found none wrong, and every
entry present. It found these outright bugs, fixed in the commit after this note:

- **The Worked examples on their own pointed at files a Toolbox user doesn't have.** The page
  said they were "in the Toolbox", labelled each one "worked_examples/statements/...", and its
  paste instructions would fail on `from building_blocks ...`. The page now says the scripts
  are kept where the Toolbox is written, that each entry shows all their Python, and how to
  paste one with its Building block; a test holds that no `worked_examples/` path shows.
- **A pasted example uses your own today,** so `last_n_days` reads other days and, from
  2026-09-26 on, finds no rows in the Example database. The page now says so and gives the
  `between(...)` to write instead; a test checks that it reads the same days.
- **"filters by any word"** in the README and CHANGES.md read as OR; the box keeps the entries
  holding every word, and both now say so.

Its costliest stops, for the user to weigh:

- **Why `count_rows(where=is_not_null(job_runs.run_id))`** in the LEFT_JOIN examples: nothing
  says that `COUNT(*)` would count a job with no runs as 1.
- **The re-grouping Guard's "Usual fix"** fits an average, not a distinct count (also found by
  ticket 21's reader); it is `refusals.py`'s message, so changing it is a Toolbox change.
- **`by_day`'s docstring snippet** overwrites `df` each day, so only the last day survives if
  pasted as is; also a Toolbox docstring.

Also noted, not changed: `run`'s entry shows its result twice (as pandas prints it, then as a
table); names that every Worked example uses get no "Worked examples that use it" line, and
the page doesn't say why; `GROUP_BY`'s entry has no result, while `week_start`'s has a pandas
one.

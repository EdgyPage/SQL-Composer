# The export ships it all

Type: task
Status: resolved
Blocked by: 13
Size: M

## Question

main's layout: composer_core/, sqlglot_composer/, spark_composer/ (each with examples.html and
how_to.html), example_projects/<edition>/{starter,intermediate}/, templates/<edition>/...,
.github/README.md. The allowlist, stamps ("copy it, then edit your copy" for projects and
templates), the fresh-Python imports, each run_pipeline.py run, the both-Editions refusal, and
the README's Install, Update from 3.x, How-tos, Example projects and Templates sections.

`templates/README.md` ships too, beside the two sets, named for each Edition through
`editions.named_for` like the Templates (ticket 13; `test_the_readme_can_be_named_for_either_edition`
holds that it can be).

## Done when

- `python tools/export_clean.py --preview <tmp>` gives exactly that layout; nothing is committed to main.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).

## Answer

Built in d8ccf4f, fixed up after its reviews in the commit that resolves this ticket.

- **main's layout.** `python tools/export_clean.py --preview <folder>` builds `composer_core/`
  (stamped "Composer core <version>, exported ... - generated from dev, do not edit"),
  `sqlglot_composer/` and `spark_composer/` (flat, each with `examples.html` and `how_to.html`),
  `example_projects/<edition>/{starter,intermediate}/...`, `templates/<edition>/README.md` and
  `templates/<edition>/{starter,intermediate}/*.py`, and `.github/README.md`: 153 files, nothing
  else. Nothing is committed, and `--preview` runs while drift items are open.
- **The copies.** Each Edition's copy of `example_projects/` and `templates/` is dev's, named
  for it with `editions.named_for`. The Spark run of
  `test_the_committed_project_is_what_the_generator_writes` holds that this is what
  `tools/example_project.py --edition spark` writes, lineage included, so the export needs no
  generator run and no Java. `with_mains_paths` writes each place a copied file names as main
  has it, one folder deeper: `example_projects/starter/` becomes
  `example_projects/<edition>/starter/`, and an Example project README's `PYTHONPATH=../..` (and
  `set PYTHONPATH=..\..`) gains a `..`. The project READMEs now say the Toolbox's folders "sit
  in the Toolbox's top folder, the one that holds `example_projects` too", true on dev and main.
- **Stamps.** Every copied file's line 1 is "<Edition> <version>, exported ... - copy it, then
  edit your copy", as a `#` or `<!-- -->` comment, on export only: a Template with a
  placeholder left in still doesn't parse, and dev's generator tests are untouched.
- **The allowlist.** The Toolbox folders stay flat; `example_projects/` and `templates/` may
  nest any depth under a shipped Edition's folder, and nowhere else.
- **The checks the export runs**, each with a test that spoils dev and sees the refusal:
  - each Edition imports in a fresh Python with the other library blocked (as before);
  - each Edition copied alone, without `composer_core`, stops with "Copy the composer_core
    folder from the same download beside the ...";
  - importing `sqlglot_composer` then `spark_composer` in one Python stops with "... was
    imported after ...";
  - each `example_projects/<edition>/<level>/run_pipeline.py` runs its dry run with
    `PYTHONPATH=../../..`, the other library blocked, prints show_hive's `-- 1 of `, and leaves
    no file in the tree. A dry run sends nothing, so Spark Composer's runs without Java
    (checked with Java off the PATH);
  - a commit without `example_projects/`, `templates/` or `worked_examples/how_to/` is refused.
- **The README.** Install says the download's `example_projects` and `templates` are for
  reading and copying, and the Toolbox doesn't need them. Update points 3.x users to the new
  "Update from 3.x": delete `sql_composer`, copy in `composer_core` and `sqlglot_composer`,
  change every `sql_composer` to `sqlglot_composer`, Table references `write_table_reference`
  wrote included, restart; Spark Composer users copy in `composer_core` beside the new
  `spark_composer`; both Editions in one Python now stop. New sections: How-tos (the two pages
  and levels, and a `<!-- HOW-TOS -->` list of all 30 by number under their group, read from
  each how-to's docstring), Example projects (the two projects, the dry run in bash, PowerShell
  and the Windows command prompt, and how to start your own) and Templates (what one is, and a
  `<!-- TEMPLATES -->` list as `templates/README.md`'s tables give them, in their order). Its
  paths name main's layout, so `tests/repo/test_pointers.py` no longer checks it against dev,
  and `test_every_path_the_readme_names_is_on_main` checks it against the Clean tree.
- **Not done: widening how_to_page's `check_links`** to `../example_projects/<edition>/...` and
  `../templates/<edition>/...`, which ticket 06's note asked of this ticket. No how-to links
  there (they name the folders in prose), so it would be a check for links nobody writes;
  how_to_page's docstring now says so. Widen it with the first how-to that links.
- CONTEXT.md's Clean branch now holds each Edition's copy of the Example projects and the
  Templates.

**Code review (2026-10-05).** Two reviews found:

- **Spec:** nothing missing; the Spark copies, compared file by file with the generator's
  `--edition spark` output, were identical but for the intended path rewrites. One robustness
  point: the dry runs run inside the Clean tree, so a dry run that wrote a file would ship it
  unstamped. Fixed test first: `check_dry_runs` refuses a file left behind.
- **Standards:** no hard violation (no Edition file, public name or Composer core file
  changed). Judgement calls, changed: `templates_text` read each Template's docstring's first
  line with `chr(34) * 3`; it now takes "What it is" from `templates/README.md`'s tables, the
  order's own source (the beginner reader found those lines plainer too). `fresh_python`'s
  tuple default for a list is now `None`. The test's own `COPIED` says it is written out on
  purpose, so the tests say what main holds on their own. Not changed:
  - `how_tos_text` reads the how-tos' title and `For:` lines again rather than importing
    `tools/how_to_page.py`, since that import loads an Edition into the export's Python; its
    docstring says so.
  - The checks match the refusal texts users see ("Copy the composer_core folder ...", "was
    imported after"), so a reworded message makes the export refuse and show what it got,
    which is the point.
  - The README rendering stays in export_clean, beside the cheat sheet it already wrote.
  - `check_one_edition_per_python` keeps its guard for an `EXPORTED` of one Edition, which
    `editions.EXPORTED` allows and the tests use.

**Beginner reader (2026-10-05).** One read of the previewed README's new and changed sections
found, and these were changed:

- **Update didn't send 3.x users onward**: it now opens by pointing a copy with `sql_composer`,
  or without `composer_core`, to Update from 3.x. "from another version or export" became
  "another download", and "it stops" "the import stops".
- **Update from 3.x**: step 3 says to change every `sql_composer` to `sqlglot_composer`, Table
  references included; the Spark Composer paragraph says to restart the kernel too.
- **How-tos**: "Start here" now follows A first Statement; "as one notebook" became "in steps
  you paste into one notebook, in order"; "daily copies" became a plain list of what the
  Intermediate how-tos cover.
- **Example projects**: "its own two" became "two Example projects of its own"; the
  intermediate bullet's "which" and doubled "day" are reworded; the dry run is said to be one
  because the Example database can't be written; the PYTHONPATH line is given for bash,
  PowerShell and the Windows command prompt (it stopped the reader on Windows); starting your
  own project says to put the two folders beside `run_pipeline.py`, or to write it from the
  Templates. Each `run_pipeline.py`'s docstring now points at its README's "Running it here".
- **Templates**: the docstring is said to say where to copy the Template; the list's lead-in no
  longer stacks two colons; the list's lines come from `templates/README.md`, not the
  docstrings' first lines (stops on "writers first" and "its differences as text").
- **Not changed here: "This is version 3.2" beside "Update from 3.x" and "Before 4.0"**, with
  no 4.0 in `composer_core/CHANGES.md`, the reader's costliest stop. Ticket 15 raises
  TOOLBOX_VERSION to 4.0 and writes CHANGES 4.0 (drift D120/D122); nothing is exported before.

# The how to page

Type: task
Status: resolved
Blocked by: 04, 05
Size: M

## Question

`tools/how_to_page.py` writes `how_to.html` in each Edition folder from
`worked_examples/how_to/NN_slug.py` walkthroughs, reusing the gallery's machinery: two levels
(Getting started, Intermediate), a contents column, a search box, copy buttons on every Python
and Hive block, the full text of each .py and .md file a step writes, links between how-tos.
Fixed headings: Goal, When you'd use it, Steps, Check it worked, Common mistakes, Next. How-to
1, Start a notebook, is its first page.

## Done when

- A staleness test, a parity test between the two pages, tests/test_how_tos.py.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).

## Answer

Built in c9aed80, then fixed after its code review and beginner reads in 7fad841, caaf369
and the commit that resolves this ticket.

- **The tool.** `tools/how_to_page.py` writes `how_to.html` in each Edition's folder
  (`python tools/how_to_page.py`, `--edition spark`), from the how-tos in
  `worked_examples/how_to/NN_slug.py`. It reuses the Example gallery's machinery from
  `tools/example_gallery.py`: `STYLE`, `example_setting`, `run_step`, `code_html`,
  `hive_html`, `table_html`, `message_text`, `names_html` and `names_in`, and now
  `FILTER_SCRIPT` and `PANDAS_LABEL`.
- **The source format.** A how-to is its docstring: the title on line 1, a line
  `For: Getting started` or `For: Intermediate` on line 3, then the six fixed headings (Goal,
  When you'd use it, Steps, Check it worked, Common mistakes, Next), each once, in order, with
  `###` steps or mistakes under them. Prose, "- " lists, `backticks`, links to `#slug` and
  `examples.html#entry`, `>>>` steps written as a doctest, and indented code shown but not run.
  A block between `[sqlglot_composer only]` (or `[spark_composer only]`) and `[end]` shows on
  that Edition's page only, and may hold `>>>` steps, which run for that Edition only. The tool
  refuses, with what to change, a missing or misplaced heading, a `For:` line that names no
  group or doesn't hold the how-to's number (1-18 Getting started, 19-30 Intermediate), a block
  with a heading or another block in it, a stray `[end]`, two how-tos with one number, a step
  that would show the folder it ran in, and a link to anything but a how-to or a gallery entry.
- **The page.** A contents column per group, a badge on every how-to, a filter box that hides a
  how-to and its contents line together, and a Copy button on every block of Python and Hive
  (clipboard, else select the block and say Ctrl+C), all from one short script; plain HTML
  without it. Each step's Python, then what it really gives, run while the page is written:
  the Hive (labelled "Hive, ready to paste" after `show_hive`), a result table, a Warning, the
  message it stops with, and each file it writes (a `.py` or `.md` file in full, an `.html`
  file by name). Today is 2026-09-25 as on the gallery.
- **Pins.** A lineage's time (2026-09-25 09:00), your scripts' commit (`1a2b3c4`) and the
  Toolbox version are pinned, and `JPY_SESSION_NAME` is cleared, so the page is byte-stable.
- **Registration.** `how_to.html` is in `editions.PAGES`, so each Edition folder's file list
  holds it, the export ships it, and the import self-check stops when it is missing.
- **Tests.** `tests/test_how_tos.py` (shared): the committed page is what the tool writes; each
  how-to runs as a doctest in `tmp_path`; title, `For:` line and headings; every name used
  exists; every link lands; groups, contents and badges; the page needs no other file; the
  script (see below); the written-file display; pandas stand-ins; Edition blocks; each refusal.
  `tests/repo/test_how_to_parity.py`: both pages match once named alike, apart from the
  declared differences (below). `tests/test_import_self_check.py`: the missing-page stop.
- **Glossary.** CONTEXT.md gains How-to.
- **The README.** The page links to no README anchor (the map's open question): it needs
  nothing from the README, and the README's How-tos section, ticket 14, links to the page.

**Code review (2026-10-05).** Each finding, and what was done:

1. *"level" clashed with the glossary's Level.* The how-tos' two groups are now "Getting
   started how-tos" and "Intermediate how-tos": the source line is `For: Getting started`, the
   tool has `GROUPS`, a tuple of `Group` named tuples (name, id, numbers, for_what) read by
   field, `HowTo.group`, the refusal says "says `For: Advanced`" and "the Intermediate how-tos
   are 19 to 30", and the page says "No intermediate how-tos yet." CONTEXT.md's How-to entry
   uses no clashing noun. (Closes drift D126 once merged.)
2. *Three tables, now six.* The header and how-to 1 say six made-up tables, how-to 1 names the
   first three and says the other three hold 14 days. Both pages regenerated. (D125.)
3. *The missing-file stop named both pages.* `composer_core/checks.py` now names only what is
   missing and what it holds (`_PAGES`: CHANGES.md, examples.html, how_to.html), after the .py
   reason; tests cover each page alone, both, and a missing .py file naming no page.
4. *The parity test skipped a whole how-to's Hive for any `hive_function(`.* It now allows in
   the Hive only what Spark Composer adds (and the note saying why), and each row that adds
   nothing's own example, replaced as the row writes it (`NVL(job_runs.status, 'none')` for
   `COALESCE(job_runs.status, 'none')`): how-to 27 must show the hive_function row's example,
   or declare more. A test holds that a different call (NVL2) isn't allowed.
5. *The script test skips without node.* Kept, and on CI (`CI` set) a missing node now fails
   the test rather than skipping: `.github/workflows/dev.yml` runs on `ubuntu-latest`, whose
   image comes with node, though the workflow doesn't set it up itself. Added an always-running
   test: every element the script reaches is on the page (the filter `<p>` with its input and
   count, one `data-for` contents line per how-to, in order, ids unique), and the script calls
   each selector. Behaviour itself (hiding, counting, copying) needs a script engine, so it stays
   in the node test; the page's script was also checked in a real browser.
6. *The filter script was written twice.* `FILTER_SCRIPT` in `tools/example_gallery.py` is the
   gallery's script, and the how-to page's is `FILTER_SCRIPT + HOW_TO_SCRIPT` (contents lines
   follow their how-to through an input listener, then the Copy buttons). Regenerated, both
   galleries were byte-identical; a test holds both scripts to the constant.
7. *"Every step runs on the Example database" wasn't true of `send`.* The entry now says its
   steps run on the Example database, and what works only at work, such as your own send, is
   shown and not run. "Lineage" is capitalised in the group's description, as a glossary word.
8. *Why steps_html, handed_html and example_scope aren't reused.* The gallery's shows a
   docstring's written output (`part.want`) and then each Statement handed to to_hive, run or
   export_lineage, through a scope that wraps those functions. A how-to shows what each step
   really gives, live, step by step, in a scope its own import fills, with files written and
   Warnings caught per step. The tool's own `live_steps_html` (renamed from `steps_html`, so the
   two don't share a name) says so in its docstring. *Links to the example project and
   templates* come with tickets 11 and 13: `example_projects/` exists on dev but neither is on
   main's layout yet (ticket 14 adds them to the allowlist), so `check_links` still allows only
   how-tos and gallery entries. Note for ticket 14: widen `check_links` (and
   `test_every_link_on_the_page_lands`) to `../example_projects/<edition>/...` and
   `../templates/<edition>/...` when main ships them.
9. *The stand-in `class SparkDataFrame`.* Kept on Spark Composer's page only, now in a Spark
   block, worded "Your own `spark` isn't in this notebook, so a stand-in plays its DataFrame
   here; like Spark's, it has a `toPandas` method, which is how `run` knows it is Spark's".
10. *A step sqlglot Composer's Example database can't run.* Built: a how-to's file may give,
   after its docstring, a pandas stand-in `NAME_in_pandas()` for the Statement its steps call
   `NAME`. While the how-to runs, on the page and in its doctest, a query the Example database
   refuses with "can't run this Hive", from that Statement, gets the stand-in's DataFrame;
   the page labels it "Result, computed in pandas, not by running this Hive", as the gallery
   does. Spark Composer's runs it, so the doctest output both Editions share holds the stand-in
   to Spark's result, and the parity test allows only that label. A stand-in whose Statement
   no step makes is refused. Tests: with a week_start Statement, the stand-in's result and label
   on sqlglot Composer, Spark's own result on Spark Composer, the "can't run" message without
   the stand-in, and the refusal. Tickets 07-10 use it for row_number, week_start and
   month_start.

The code-review skill wasn't run again on the fix-up; the findings above are each fixed.

**Beginner reader (2026-10-05).** Run twice as a Python-first SQL beginner on the header and
how-to 1. The first read (on c9aed80) stopped at: the header's today paragraph (a step how-to 1
doesn't have, "here"/"its place" pointers); the sqlglot page teaching a Spark mistake to readers
it had just sent away from Spark; the Spark page's "This page has no Spark" and its missing
first-run Note; the header's list of what a step gives; the Goal using "the send" before
introducing it, and a sqlglot send without column names; "its Hive is written for Spark" (both
pages show the same Hive); the unused `jobs`; "bounds it at both ends"; WHERE's conditions all
holding; `AS job_runs`; show_hive's "prints it once"; two labels for one kind of stop; the
opt-out without when it's right; "every file it imports"; Next's write_table_reference line; the
glossary's "Every step runs"; the missing-page stop naming both pages; and finding the page at
all. Each was fixed as proposed: the today paragraph rewritten; each page shows its own users'
send mistake (sqlglot Composer: a send giving rows without column names, shown live, columns 0,
1, 2; Spark Composer: one without `.toPandas()`), which needed steps inside Edition blocks; the
Spark page says the Example database starts its own Spark, needing Java 17 to 21, about 15
seconds the first time; one label, "Python stops with this message"; the Example gallery's
header and the README template's Example gallery section point to the how-tos. A send returning
a plain list (`lambda hive: [(1,), (2,)]`) is not refused today and the page doesn't add a
Toolbox behaviour: proposal for a later ticket, `run` refusing a send result that isn't a pandas
DataFrame (it already refuses Spark's), as `refuse_a_spark_dataframe` does. The confirming read
(on 7fad841) found no costly stop left from the first; its new ones were fixed in caaf369: a
send that typed column names (now passes on a cursor's `cursor.description`), the Opt-out
line hidden behind `...` in the source, show_hive "just once", "newer tables", the import list
without `example_database`, "copy from where", and why the Spark stand-in has `toPandas`. Left:
the header's capital Warning (a glossary word) and the name `LoadRefused` (a public name).

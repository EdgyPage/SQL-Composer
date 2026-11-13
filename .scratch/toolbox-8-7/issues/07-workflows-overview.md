# The Workflows overview page

Type: task
Status: resolved
Blocked by: 04
Size: M

## Question

Each Workflow has its own chart, but nothing shows how they connect (Q10, Q19). What page shows
the whole path?

## Done when

- **`workflows.html`** is built from the page module (ticket 04), and ships beside the other
  docs pages (ticket 13 moves them to main's `docs/`). The README links to it.
- **One drawing.** It shows:
  - every Workflow: references, new_table, convert, promote, change_a_saved_table, upgrade and
    schedule (ticket 08);
  - the Excel path;
  - an arrow for each hand-off, such as a converted table going on to promote.
- **Click a Workflow** to see:
  - its steps as bullet points, from `tools/workflow_graph.py`'s reading of its notebook;
  - its common tripping points, from a hand-written list drawn from the usability rounds'
    findings in `.scratch/usability-loop/results.md`.
- **High level only.** The user's words: "Don't include all documentation, that's what the
  search documents for Copilot are for. High level to bullet points."
- A test holds that every Workflow is on it, and that each step matches its notebook.
- Ticket 15's beginner reader reads it.

## Answer

Built 2026-11-13.

- **`sqlglot_composer/workflows.html`**, beside `how_to.html`, written by
  `tools/workflows_page.py` (`.venv/Scripts/python tools/workflows_page.py`, after
  `workflow_graph.py` in the regen chain). It is the third of `toolbox_registry.PAGES`, so it
  ships and the export lists it; `checks._PAGES` names it for the import self-check's stop
  ("a missing workflows.html leaves you without the Workflows overview"). The README
  template's "The Workflows" links it.
- **One drawing**, an SVG written in Python: a box for each of references, new_table, convert,
  promote, change_a_saved_table, upgrade and schedule, and one for the Excel path; an arrow for
  each of `HAND_OFFS`' seven hand-offs (references to new_table and to convert, the Excel path
  to convert, new_table and convert to promote, promote to schedule and to
  change_a_saved_table), each with its words as a tooltip and in both ends' parts. upgrade
  has no arrow: its part says it runs on its own, whenever a new Toolbox is copied in.
- **Click a box** (or Tab to it and press Enter): the module's `DRAWING_SCRIPT` lights up its
  path, and the page's own script shows its part of the side panel: what it does (the
  Workflow's `about`), its notebook and names cell, Starts from and Ends with (its start
  materials and end artifacts), its steps by name, each tagged with its kind, its common
  tripping points, its hand-offs, each a link to that part, and the how-to that walks through
  it in full. The first part, "Every Workflow", shows until a box is clicked: which Workflow is
  for which job, the four cells, what a step's tag means, six words from CONTEXT.md, and the
  tripping points every Workflow shares. `workflows.html#convert` opens on convert's part.
- **The tripping points** are `TRIPPING_POINTS`, two to six per box, written by hand, each
  said as what to do. Most are the findings of the rounds in
  `.scratch/usability-loop/results.md`: Run All, `connect(...)`, the run that goes to the end
  with nothing open, printing a report in a script, Table references first, a Key's check and
  `where=`, which Workflow takes one query, RENAME's default name, the compare's one Partition,
  a Table notebook's TODO lines, promote's decisions step with nothing to answer, a
  parameter's default, how a parameter reaches the Statements, change_a_saved_table's imports,
  and the Excel path's three Copilot files, its `<database>`, its Total Row and its typed lists.
  Where the rounds found little (upgrade, schedule's Build and Run cells, PROD's
  `location_root`, an Admin statement), they are the README's and the how-tos' own warnings.
  Findings mended since and no longer true (do_next after a finished batch, promote's report
  asking for `location=`) are left out.
- **Tests: `tests/test_workflows_page.py`**: the committed page is what the tool writes; the
  boxes are exactly the seven Workflows and the Excel path; every Workflow workflows.py holds
  is on it; each Example project notebook's step headings are its part's steps, in order, and
  so are workflows.py's; the Excel path's steps are workflow_graph's; each hand-off is an
  arrow and said on both parts; each box has at least two tripping points; each how-to link
  lands; each link inside the page lands on a part; the page starts as `html_page.page`
  writes it, holds `BASE_CSS`, `DRAWING_CSS` and `DRAWING_SCRIPT`, loads nothing from outside,
  has no `style=` and names colours only through the tokens; without its script every part
  shows; every tag is closed; the README links it; it is one of the registry's pages.
  `tests/test_import_self_check.py` gains the stop for a missing workflows.html.
- **Decided: the schedule Workflow stands in until ticket 08 is merged.** workflows.py holds no
  schedule Workflow on this base, so `workflows_page.NOT_YET_IN_WORKFLOWS` holds one, a
  `Workflow` with project.new_scheduled_run's one step. **At the merge with ticket 08:** delete
  the stand-in (and `workflow_of`'s use of it); `test_a_stand_in_is_only_for_a_workflow_
  workflows_py_does_not_hold_yet` fails until it goes, and the notebook test then reads
  schedule's notebook in each Example project. The test expecting schedule's box passes on
  both sides of the merge.
- **Decided: two new kinds in the page module**, `workflow` and `excel`, each a row of `KINDS`
  with two new `COLOURS` tokens, as the module's docstring says a new kind is made. Ticket 05
  (bold colours, in parallel) changes `COLOURS`: at that merge give `workflow`, `workflow-edge`,
  `excel` and `excel-edge` Okabe–Ito values like the rest.
- **Decided: the panel's parts are in the page, all shown without the script.** The script
  adds a class to the body, and the CSS then hides every part but the shown one. Ticket 06's
  `PANEL_CSS`/`PANEL_SCRIPT` (in parallel) are for the lineage pages' step panel; if it lands
  a panel this page can use, folding this page's into it is a follow-up, not a merge need.
- **Decided: steps by name and kind only**, no calls and no Goal/Action/Done when: the user's
  "high level to bullet points". Each part links its how-to for the rest. The Excel path's
  steps are workflow_graph's `EXCEL_FLOW` sentences up to their first colon.
- **Decided: the steps come from workflows.py, the hand-offs and tripping points from the
  tool.** workflow_graph reads workflows.py the same way, and the page imports only its
  `EXCEL_FLOW`: nothing in workflow_graph changes.
- **Decided: the page stays on dev's how-to links (`how_to.html#slug`)**, relative, so they
  hold when ticket 13 moves both pages to main's `docs/` together.
- **Fixed on the way:** `docs/agents/standards.md`'s HTML section named `test_standard.py`
  without its folder, which `tests/repo/test_pointers.py` refuses (ticket 04's line); it now
  names `tests/repo/test_standard.py`.
- **Beginner reader:** [report](../reports/beginner-reader-ticket-07.md). Its three costliest
  stops were fixed (new_table's step 2 waiting with no Decision open, promote's "compare
  passed", the Admin statement unexplained), with the naming example, `dry_run=True`'s place,
  schedule's tripping points cut to three high-level ones, the Copilot files' folder, the
  step tags' meaning and a short "Words" list; the report's end says what was kept and why.

## Code review

Run 2026-11-13 with the `code-review` skill against 37679376, `review-standards` and
`review-spec` on Sonnet.

**Standards:** no hard violation of the HTML standard (tokens, no `style=`, offline, escaped,
built by `html_page.page`, the drawing's script reused).

- Fixed: the tripping points' heading and list, written three times, is one function,
  `tripping_points_html`; `bullets` takes any `Sequence[str]`, so no `list(...)` wrappers.
- Fixed: the script's `box.id.slice('box_'.length)`, three times, is one function,
  `nameOfBox`, as the standard's "One way per job" asks of a script.
- Fixed: `place` is `top_left`, for what it gives.
- Fixed: the step tags' sentence ("calls the warehouse sends to the warehouse, when you run
  it") and the registry docstring's stacked "and".
- Answered: `NOT_YET_IN_WORKFLOWS` is scaffolding for ticket 08, commented and held by a test
  that fails at the merge until it goes (**Decided** above).
- Answered: `FOUR_CELLS` and `WORDS` are short restatements of the README's four cells and
  CONTEXT.md's words, not tested against them: a test would need the two texts to match word
  for word, and the page's are shortened on purpose. A drift there is the drift reviewer's.
- Answered: `"every"` as a key beside the boxes' names is the panel's first part's id too;
  one dict keeps every tripping point in one place.
- Answered: the tool keeps its prose (hand-offs, tripping points) beside its layout, one page's
  worth, as `workflow_graph.py` keeps `EXCEL_FLOW` beside its drawing.

**Spec:** every "Done when" bullet built.

- Answered: the steps come from workflows.py, not workflow_graph's functions, which read the
  same list: **Decided** above. Each is tested against its notebook's step headings.
- Answered: schedule's steps are the stand-in's until ticket 08, so no notebook holds them on
  this base; at the merge the notebook test reads schedule's notebook (**Decided** above).
- Fixed: the Answer overstated where the tripping points come from, and said promote's
  "nothing to answer" was left out where only its "fill in location=" report was: both now
  said as they are.
- Answered: the "Every Workflow" part's four cells, Words and step tags, and each part's
  Starts from and Ends with, are kept short and were what the beginner reader needed; each
  links its how-to for the rest. The Excel part links the README's "Have Copilot write it",
  a heading the template holds.

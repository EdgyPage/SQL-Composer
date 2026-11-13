# The side panel and minimal Markdown

Type: task
Status: resolved
Blocked by: 04
Size: L

## Question

A long step's text runs past its box, and its full Hive sits in a report below the drawing
(Q3, Q4, Q14). What does a click show, and what does Markdown keep?

## Done when

- **The panel.** On all three lineage pages, the Scheduled run's included, clicking a box opens
  a panel beside the drawing, and still lights up its path. The panel shows:
  1. the step's full Hive, wrapped, with a Copy button;
  2. the tables it reads and the tables it writes;
  3. its Run values, and the Session settings sent before it;
  4. on the Project page, the Scheduled runs that write the table.
- A click off every box closes the panel. Escape closes it too.
- It works with the keyboard: Tab reaches each box, and Enter opens its panel.
- The report below the drawing goes.
- **The Markdown page** keeps each table or step, what it reads and writes, and its Hive in
  full. The drawing, the panel, the path lighting, zoom and the colours are HTML only.
- A test holds that each line of a page's Markdown, its Hive included, is in its HTML too, for
  all three exports.
- The panel's script is in the page module (ticket 04), and the pages pass the offline policy.
- The README's lineage paragraphs and the how-tos that show lineage say what a click shows.

## Answer

Built 2026-11-13.

- **The page module's panel pieces** (`sqlglot_composer/html_page.py`): `Piece(kind, lines)`
  and `Part(key, level, heading, pieces)`, a section both files show; `part_markdown` and
  `part_html` write one Part to each, and `inline_html` reads its `` `code` `` and `**bold**`;
  `panel(parts)`, the `<aside id="panel">` after the drawing; `PANEL_CSS` and
  `PANEL_SCRIPT`, whose `addPanelHandlers(drawing)` opens the Parts a box names in its
  `data-parts`, its own entry (`data-entry`) copied to the top, and `copyHive`.
  `DRAWING_SCRIPT` gains one line: it says which box a click chose, as a `boxchosen` event,
  so the panel opens exactly when the path lights up. `mermaid_class_defs` and
  `mermaid_link_style` went, as nothing draws Mermaid now.
- **All three pages have the panel**, the Scheduled run's being a Statement page. A
  Statement page's box opens its Statement's section: its facts list (Reads, Writes, each Run
  value, each Session settings sent before it), its Hive as submitted, wrapped, with a Copy
  button, then its Calculated columns, Copied columns and Keys; a calculated column's entry
  shows first. The Project page's box opens the table's section: what it is, what it reads,
  what reads it, the Scheduled runs that write it (⚠ for two), a loop, its logic failing to
  load, then each Statement that writes it, with its Run values, Session settings and Hive,
  one Statement two senders share shown once, "by its Table folder and the Scheduled run
  weekly". The Project page now runs `DRAWING_SCRIPT` too, so its paths light up and it
  zooms and pans; its drawing is still in the page, drawn with scripts off.
- **Keyboard**: each box has `tabindex="0" role="button"`; Enter (or Space) clicks it;
  Escape, the Close button, a click on the drawing off every box, or a click on the page off
  the drawing, panel and controls closes the panel and clears the path; Escape gives the
  keyboard back to the box.
- **The report below the drawing went**, and the Statement page's Report checkbox with it.
  With scripts off, every section shows under the drawing.
- **The Markdown** is the sections as text: title, what made it and the two files, each
  Statement's (or table's) section, the footer. No Mermaid chart and no colour.
- **Tests**: `tests/test_html_page.py` holds every line of each page's Markdown, its Hive
  included, on its HTML page (`test_every_line_of_each_markdown_is_in_its_html_too`, all
  three exports, the Project's with and without a loop), the panel and no report on each, the
  panel's pieces from the module, each box reachable with Tab and naming Parts that exist,
  the Hive whole beside a Copy button, and the Project panel's runs, Run value and Hive. The
  lineage tests read the drawing from the page's data in place of the Mermaid chart.
- **Browser check**: a regenerated page opened in the desktop app's browser pane: a click on
  a box opened its Statement's section beside the drawing and lit the path; Escape closed it,
  cleared the path and put focus back on the box; Tab then Enter opened the next box's
  panel; Copy copied the Hive (selection fallback on a `file:` page); a click on the drawing
  off every box closed it. Below 800 pixels wide the panel goes under the drawing.
- **Decided: the Markdown keeps each Statement's calculated and copied columns and Keys**,
  not only what it reads and writes and its Hive: they are the text tracing of each column
  the user's "minimum viable tracing" asks for, and the ticket names only the drawing, panel,
  lighting, zoom and colours as HTML only. Copied columns are a list, not a table.
- **Decided: one Part writes both files**, so the line test holds by construction and a
  section can't say one thing in Markdown and another on the page.
- **Decided: the panel's sections are in the page, not built by the script**, so they are
  escaped in Python, show with scripts off, and the line test reads them.
- **Decided: a box no Statement made opens the nearest Statements linked to it**: a table's
  column the Statements reading it or writing it, a Run value those it feeds.
- **Decided: Session settings per Statement**: on `export_lineage`, those passed (sent before
  all); on a Scheduled run, its table's `session_settings()`, as `built.run` sends them;
  "dynamic_partitions" for a write that fills partitions from its rows.
- **Merged with ticket 09 (Hivevar)**: a Statement holding a Hivevar lists its SET hivevar
  lines among what is sent before it ("Hivevars PERIOD_END, sent before it: SET
  hivevar:PERIOD_END=2026-09-24"), as 09's Answer asks; a Hivevar's box is named by the one
  `_run_value_words`.
- **Decided: Hive as the page showed it before**, `to_hive` (an Unchecked statement's text),
  so a run's Hive file stays the one place with `SET` lines and `;`.
- **Decided: the Project's Scheduled runs list sits in a closed `<details>` under the title**,
  as no box opens it.
- **Decided: the two files' shared line names neither file** ("Written as two files side by
  side, named alike: …"), so the Markdown of two exports compares line for line, as how-to 19
  compares before.md and after.md. The Statement page's no-script note still names its `.md`.
- **Decided: the Hive comes before the Calculated columns** in each section, in both files,
  as the panel's first job is the Hive; how-to 19's expected diff moved with it.
- **Decided: the Piece kind for Hive is the string `"sql"`**, as only the Edition files may
  name the Hive dialect (`test_sqlglot_escaping_toolbox`).
- **The beginner reader** ran on the regenerated Scheduled run page, the README's lineage
  paragraphs, how-to 07 and `export_lineage`'s docstring:
  [report](../reports/beginner-reader-ticket-06.md). Taken: "light up its path" is now "light
  up every box that feeds it and every box it feeds"; "a click off every box" is "a click on
  empty space"; the panel opens "on the right", a calculated column "first, then the
  section", a table's column "the section of each Statement that writes or reads it"; Keys'
  "in the chart" is "on its box in the drawing"; Session settings read "Session settings
  map_joins, sent before it: SET …; SET …"; "whole, its long lines wrapped". Left for the
  user: a column shown twice in a chain (stop 1: a Saved table's column as written and as
  read, so before this ticket); the lit path's red being the loop's (stop 3, ticket 05's
  palette, which can give `lit` its own colour); `derived('x', ...)` in Keys and a Key's
  column order (stop 7, before this ticket); the footer's "commit nogit" (stop 12).

## Code review

Run 2026-11-13 with the `code-review` skill against 37679376, `review-standards` and
`review-spec` on Sonnet.

**Standards:** no hard violation. Judgement calls:

- Fixed: `_steps_of`'s three-`for` comprehension (also a "dense comprehension" break
  `test_standard.py` found) is a loop over `_linked_to(graph, keys)`.
- Fixed: `project_lineage._about` shared a private name with `lineage._about`
  (`test_standard.py`'s "private name twice"); now `_page_about`.
- Answered: `part_markdown` and `part_html` run the same cascade on a Piece's kind: one
  writes Markdown, the other HTML, as `kinds_css` and the Mermaid did for `Kind` (ticket 04's
  "Simple over short"); a map of writers per kind would be machinery for five kinds.
- Answered: `Piece.lines` is a list even for a heading, a block or Hive: one shape for every
  kind keeps `Piece` one NamedTuple; each builder passes one string.
- Answered: `settings` travels beside `ordered` as a list per Statement: `write_lineage`'s two
  callers build it in one line each; a Statement-and-settings type would change every
  caller of `in_order` and `build_graph`.
- Answered: `settings_lines` reads `SessionSettings._names` and `._lines`, as
  `lineage_footer` already did.
- Answered: `capitalise` twice (`f"{where[0].upper()}{where[1:]}"`): two places, one line
  each; a helper isn't clearer.

**Spec:** nothing missing.

- The line test checks each line is on the page, not where: answered, the Part writes both
  files, so a line can't move to another section on one side only.
- Scope: Space as well as Enter, a click off the drawing closing the panel, the narrow-screen
  layout, and the Project page's zoom and pan: kept, each a small part of making the panel
  usable by keyboard and on a laptop; the zoom and pan come with the module's drawing
  script, which the Project page needs for its path to light up.
- Scope: the Markdown keeps the column sections: answered above (**Decided**).
- A box no Statement made opens the nearest Statements: answered above (**Decided**); a table
  column read by two Statements opens both sections.
- Session settings per Statement: checked on the regenerated Scheduled run page, whose
  `mart.job_day_costs` write lists "dynamic_partitions"; the Project test's write lists none
  as its tables have no `session_settings()`.

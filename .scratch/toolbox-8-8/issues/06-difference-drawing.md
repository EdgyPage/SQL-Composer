# The difference page's drawing

Type: task
Status: resolved
Blocked by: 05
Size: M

## Question

The HTML page draws where the changes are (Q16), from the shared page module,
`html_page.py`, by the HTML standard in `docs/agents/standards.md`.

## Done when

- **The drawing** shows the Project's tables table by table, as the Project lineage draws them:
  - a table with an Own change in one colour, one with only Inherited changes in another,
    unchanged ones faded, through two new named tokens from the Okabe–Ito set; the loops' red
    is used for nothing else, as 8.7 holds;
  - a legend naming each.
- **Clicking a table** opens the side panel: its changed columns, each Own change's before and
  after with Copy, each Inherited change's chain down to its root, and when it was next
  written. The click lights the chain, as the other pages light a path.
- With `tables=`, only those tables and their chains are drawn.
- A test holds the page is built from the one module, as the other lineage pages are, and that
  it works offline.
- The Project lineage page doesn't change.

## Answer

Built 2026-11-17, from dev's cdd122ce (tickets 01, 02 and 05), beside tickets 03 and 04.

- **Two tokens and three kinds in `html_page.py`:** `own-change` (`#e69f00`, Okabe–Ito's
  orange) and `inherited-change` (`#56b4e9`, its sky blue), the pair told apart best with
  colour blindness, and `unchanged` (`#fff`, a plain box), each a row of KINDS; the loops' red
  is used for nothing else, and each fill reads with the boxes' dark text.
- **The drawing, in `lineage_difference.to_html`:** every table `Difference.kinds` holds, a box
  each, in columns as the Project lineage lays them out, by `project_lineage.table_columns`
  (its `_columns`, made to take any tables and reads, so its own page is the same), and an
  arrow from each table to each table that reads it, from `Difference.reads`. A box says its
  table, what it is (Saved table, a Scheduled run's Statement, read, not written here) and what
  changed of it ("own change: 1 column", "inherited change only: 2 columns", "unchanged"),
  drawn as `own-change`, `inherited-change` or `unchanged`; an unchanged one is faded
  (opacity .45) unless a click lights its path. With tables=, the Difference holds only those
  and their chains, so only they are drawn.
- **The legend** names the three kinds, then what an arrow, a click and Tab do (`LEGEND`).
- **The side panel:** each changed table's section, as ticket 05 writes it, moves into
  `html_page.panel`: its columns, each Own change's logic and rows that count before and
  after with Copy (the panel's own Copy, so the page's own copy script went), each chain down
  to its root, its Effective logic, and when it was next written. A box opens its section
  (data-parts), and the drawing's script lights everything that feeds it and that it feeds.
  An unchanged table opens a line on the page alone, "No column of it changed, since ...",
  with what it reads; the Markdown twin keeps to what changed. The tables not recorded stay in
  the header; the Building blocks changed and each Upgrade's rewrite, folded, under the
  drawing.
- **Tests:** `tests/test_html_page.py`'s `pages` fixture holds the difference page too, written
  from a Lineage state of two recordings of its own, so it keeps every rule the other lineage
  pages keep (the tokens, no inline style, nothing from outside, the one module, every
  Markdown line on the page, a panel, no two kinds of one colour); `page_kinds` reads its
  LEGEND. `tests/test_lineage_difference.py` gains 4: each table drawn by what changed of it,
  each box reached with Tab and opening its section, the arrows, the unchanged table's line on
  the page alone; the panel holding each Own change's logic with Copy and each chain; tables=
  drawing only those and their chains; and one recording still drawing a page.
- The Project lineage page draws as it did: `test_project_lineage.py` passes as it was. Every
  page's token block and kinds' CSS name every token and kind, so each committed page built
  from the module, the Example projects' lineage pages, `docs/main/example_projects.html` and
  `docs/main/workflows.html`, gains the three new ones, regenerated, and nothing else.
- **The standard:** the drawing's private names (`_difference_drawing`, `_changed_box_svg`,
  `_changed_box_lines`) differ from `project_lineage.py`'s, and its comprehensions stay single.

## Comments

**Code review, 2026-11-17**, of tickets 01 to 06 together (3daf6b09..973594c2), its two axes
on Sonnet, recorded in the ledger as round toolbox-8-8-01-06. Fixed in 3d4a9bac:
- Standards: a whole-table read's expansion was written twice (`lineage_state._each_column`,
  `lineage_difference._reads_of`), now `effective_logic.each_column` and `column_key`;
  `CHANGES_AT_THE_COLUMN` repeated `ROOT_CHANGES`, now gone; `_recorded`, a vague name, is
  `_unrecorded_lines` and `_report_once_recorded`, which builds the call the five actions on
  names each built; a table's change words and box kind come from one map each.
- Spec: `building_blocks/prod/` wasn't hashed, so a prod copy's own change named no block;
  it is now, as `prod/<name>`.

Answered, no change:
- `because` names every changed column up the chain, nearest first, not only the farthest:
  each is a column the inherited change comes from, which the difference's chains need.
- "No Lineage state yet" waits for `admin/lineage.ipynb`: ticket 07 writes it.
- Recordings in one second: `_recorded_at` gives every recording, `export_hive()`'s too, its
  own second. A bumped time can be a few seconds after the clock, so a write in those seconds
  reads as before the change: a few seconds' slack, kept.
- An opaque step's readers show `inherited`: their own logic is unchanged, as Q3 and the
  Inherited change's definition say.
- `since=` before the first recording starting from it, and Building block rows in the one CSV,
  are the ticket changes each Answer records.
- The smells left: the `before` and `rows` pair (a `Recording` type), `record` returning
  text that `record_lineage_state` compares, the Middle Men `deciding_boxes` and `_columns`, and
  `difference(call=...)`'s default. Judgement calls, left for a refactor with no version raise.

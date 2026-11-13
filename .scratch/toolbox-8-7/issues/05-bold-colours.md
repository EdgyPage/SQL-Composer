# Bold colours

Type: task
Status: resolved
Blocked by: 04
Size: S

## Question

Pastel fills are hard to tell apart (Q5). Which bold set replaces them?

## Done when

- The tokens use the Okabe–Ito set (eight colours chosen to stay distinguishable with colour
  blindness). Each fill's text is dark or white, whichever has the higher contrast.
- On all three lineage pages, the Scheduled run's included.
- The loops' red is used for no other kind.
- A test holds:
  - each fill's text contrast meets WCAG AA (4.5:1), worked out from the tokens;
  - no two kinds on one page share a colour.
- The ticket's Answer shows each page before and after.
- The user's words: "subject to testing, but usable here to start. swapping palettes is easy."
  A palette change is one edit, to the token table.

## Answer

Built 2026-11-13.

The user's words, during the build: "for the bold colors, you can just pick a color palette
that's saturated and diverse enough. Shouldn't need to get too creative with font colors or
anything like that." So the palette is saturated colours from the Okabe–Ito set (the loop's
red apart, below), every fill
takes the same dark text, and the tests hold only what the user named: each kind its own
colour, the loops' red its own, and the text readable.

- **The palette is an edit to `html_page.COLOURS` alone**, the token table; nothing else in
  the module changed. A box's first line stays `ink` (`#222`), and its other lines' token,
  `box-text`, goes from grey `#666` to black, so both read on every fill.

  | Kind (page) | Before | After | Text contrast (`ink`, `box-text`) |
  | --- | --- | --- | --- |
  | table column (Statement) | `#eef4ff` | sky blue `#56b4e9` | 6.9, 9.1 |
  | Derived table column (Statement) | `#fff8e6` | yellow `#f0e442` | 12.0, 15.9 |
  | output column (Statement) | `#effaf0` | bluish green `#009e73` | 4.65, 6.1 |
  | condition (Statement, dashed) | `#f4f4f4` | grey `#bbb` | 8.3, 10.9 |
  | Unchecked statement (Statement) | `#fff1e0`, edge `#d9822b` | orange `#e69f00`, edge black | 7.1, 9.3 |
  | Python step (Statement) | `#eaf6f6`, edge `#2b8a8a` | reddish purple `#cc79a7`, edge black | 5.2, 6.9 |
  | table with a Table folder (Project) | `#eef4ff` | sky blue `#56b4e9` | 6.9, 9.1 |
  | Saved table, no Table folder (Project) | `#effaf0` | bluish green `#009e73` | 4.65, 6.1 |
  | read, not written here (Project, dashed) | `#f4f4f4` | grey `#bbb` | 8.3, 10.9 |
  | written by more than one run (Project) | `#fff1e0`, edge `#d9822b` | yellow `#f0e442`, edge black | 12.0, 15.9 |
  | in a loop (Project, edge only) | `#d33` | red `#d33`, unchanged | - |
  | the loop note's words | `#a11` | `#a11`, unchanged | 7.5 on white |
  | a lit path (Statement) | `#d33` | black | - |
  | a group's frame (Grouped flowchart) | pale tints | pale tints of the new colours | - |

- **All three pages take it**: `export_lineage`, `export_run_lineage` (the Scheduled run's,
  the same Statement page) and `export_project_lineage`, and the Project Markdown's Mermaid,
  whose classDef lines come from the same tokens.
- **Before and after**, as the pages themselves, each written at 37679376 and at this ticket
  from the pages the tests write and the Example projects, in
  `.scratch/toolbox-8-7/reports/ticket-05/`; open a pair side by side in a browser. They were
  checked as headless Chrome screenshots too, but a PNG can't stay in the repo: the code audit
  reads every file under `.scratch/` as UTF-8 text, and a new `AUDITED` entry needs the
  user's OK.
  - a Statement page with every kind: [before](../reports/ticket-05/before-every_statement_kind.html),
    [after](../reports/ticket-05/after-every_statement_kind.html);
  - a Statement page with an Unchecked statement: [before](../reports/ticket-05/before-export_lineage.html),
    [after](../reports/ticket-05/after-export_lineage.html);
  - a Scheduled run's page: [before](../reports/ticket-05/before-export_run_lineage.html),
    [after](../reports/ticket-05/after-export_run_lineage.html);
  - the Project page, tables two runs write: [before](../reports/ticket-05/before-export_project_lineage.html),
    [after](../reports/ticket-05/after-export_project_lineage.html);
  - the Project page with a loop: [before](../reports/ticket-05/before-export_project_lineage_a_loop.html),
    [after](../reports/ticket-05/after-export_project_lineage_a_loop.html);
  - the Example projects' mart__team_days: [before](../reports/ticket-05/before-example_team_days.html),
    [after](../reports/ticket-05/after-example_team_days.html); and weekly_team's run:
    [before](../reports/ticket-05/before-example_weekly_team.html),
    [after](../reports/ticket-05/after-example_weekly_team.html).
- **Tests, in `tests/test_html_page.py`**, worked out from the tokens with WCAG 2's contrast,
  computed in the test (checked against 21:1 for black on white, 4.48:1 for `#777`):
  - a box's text, `ink` and `box-text`, reads at 4.5:1 or more on every kind's fill, and the
    loop note's words on the page;
  - no two kinds in a page's legend share a colour (a kind's colour is its fill, or its edge
    when it has none), on all three pages;
  - no other token holds the loops' red.
- `docs/agents/standards.md`'s HTML section names the new tests.
- **Beginner reader**: [report](../reports/beginner-reader-ticket-05.md), run twice, on the
  first palette and on this one; what came of each stop is at its end.
- **Decided: one dark text on every fill**, per the user's words, not a dark-or-white pick
  per fill. A first palette did pick per fill (white on Okabe–Ito's blue), and was dropped
  for this; Okabe–Ito's blue, the one colour black can't read on at 4.5:1, isn't used.
- **Decided: the dashed kinds, condition and read only, are grey** `#bbb`, not a hue: they
  were grey before, they carry no value of their own, and it leaves the six hues for the
  kinds that do. It also answers the beginner reader's "an outside table isn't a condition"
  stop, which a shared purple raised.
- **Decided: a kind keeps its colour across pages where it can**: a Table folder's table is a
  table column's sky blue, a Saved table alone an output column's green.
- **Decided: the shared table is yellow, not Unchecked's orange.** A shared table in a loop
  takes the loop's vermillion edge (a later kind wins), and orange would hide it. Found by the
  beginner reader.
- **Decided: a lit path is black, and so are the edges of Unchecked, Python step and shared
  boxes.** Red is the loops' alone. A click dims everything off the path, so a lit box isn't
  mistaken for an edged one.
- **Decided: the loop keeps its red, `#d33`, not Okabe–Ito's vermillion.** Both beginner
  reads found vermillion read as orange, close to Unchecked's, with the loop's boxes the
  hardest thing on the Project page to spot; the page says a loop is "drawn red". The red is
  now the loops' alone, since the lit path that shared it is black.
- **Decided: no test that the fills are Okabe–Ito's**: the user's words make any saturated,
  varied set fine, so swapping palettes stays an edit to the token table the three tests
  check.
- **Decided: the Statement page's Markdown still has no classDef**, as ticket 04 left it.

## Code review

Run 2026-11-13 with the `code-review` skill against 37679376, `review-standards` and
`review-spec` on Sonnet, on the change as amended by the user's words.

**Spec:** nothing missing or wrong against the amended spec.

- The grey dashed kinds and the loop's `#d33` aren't Okabe–Ito: answered above (**Decided**),
  within the user's "saturated and diverse enough".
- Before and after as HTML pages, not screenshots: answered above.
- Not asked for: the black edges, `box-text` to black, the group frames' tints. Kept: the
  edges were coloured before and only their colour changed; `box-text` is what the
  readability test needs; the group frames are pale tints of their kinds' new colours, as
  they were of the old ones.
- The loops'-red test compares token values, and "no two kinds share" a kind's fill (or edge
  when it has none): kept, the colours the legend's swatches show.
- `kind_colour` would raise KeyError on a kind naming no token: `test_each_token_is_a_colour_
  and_each_kind_names_tokens` already fails first, by name.

**Standards:** no hard violation.

- Fixed: the loop's and the lit path's comments said what changed ("as before", "since");
  they now say what is.
- Fixed: the standard's new sentence named "(ticket 05)"; the ticket's number is gone.
- Fixed on the way, found by the suite: ticket 04's HTML section named `test_standard.py`,
  which `tests/repo/test_pointers.py` refuses as a path that doesn't exist; it now names
  `tests/repo/test_standard.py`.
- Answered: the same hex on two rows (`folder` and `table`, the black edges): the token table
  says "Two names may hold the same colour, each for its own job" (ticket 04), so a page's
  kinds can part later with one edit; the comments link them.
- Answered: `box-text` (`#000`) and `ink` (`#222`) are different values, each its own job: a
  box's other lines and its first.
- Answered: `page_kinds` picks the builder by `"project"` in the fixture's key: the keys are
  written in the same file's `pages` fixture, and the three page names already carry the
  builder's ("export_project_lineage"); a map from key to module is machinery for two
  builders.
- Answered: the group frames' tints are untested: the user's words keep the tests to the
  three they name, and a frame's label is `#555` on a near-white tint.

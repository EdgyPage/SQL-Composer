# An HTML standard and one page module

Type: task
Status: resolved
Blocked by: -
Size: L

## Question

Each lineage page builder (`lineage.py`, `project_lineage.py`) carries its own inline CSS and
script, and the colours are written out in the CSS, the legend and the Mermaid (Q15). What one
module do all pages come from, and what standard holds them?

## Done when

- **A new page module in `sqlglot_composer/`** holds:
  - the colour tokens, each defined once, by kind (table, Derived table, output, condition,
    Unchecked, Python step, folder, Saved table, read only, shared, loop);
  - the base CSS, using only the tokens;
  - the legend, made from the tokens;
  - the Mermaid `classDef` lines, made from the tokens;
  - the drawing's script: zoom, pan, and lighting up a path.
- `tools/toolbox_registry.py` names it.
- `export_lineage`, `export_run_lineage` and `export_project_lineage` are built from it, and
  look as they do today: no visible change in this ticket.
- **`docs/agents/standards.md` gains an HTML section:**
  - colours only through named tokens;
  - no inline `style=`;
  - every page works offline, loading nothing from outside the file;
  - text is escaped;
  - scripts run with no build step;
  - one page module, extended rather than copied;
  - the user's words on a page are as plain as the Python's.
- **Tests hold the rules a test can:**
  - no colour outside the token table;
  - no `style=`;
  - every page passes the offline policy;
  - all three pages come from the one module.

## Answer

Built 2026-11-13.

- **The page module is `sqlglot_composer/html_page.py`**, in `toolbox_registry.PYTHON_FILES`,
  imported by `lineage.py` and `project_lineage.py` and by nothing a user calls; it imports
  only the standard library. Its interface, for tickets 05 to 07:
  - `COLOURS: dict[str, str]`, the token table: every colour a page uses, by name, the one
    place a colour is written. The page's CSS names each as `var(--name)` (`tokens_css()`
    writes the `:root{...}` block); the Mermaid lines write the value out.
  - `Kind(fill, edge=None, dashed=False)`, a NamedTuple of token names, and `KINDS: dict[str,
    Kind]`, each kind of box by its CSS class: `table`, `derived`, `output`, `condition`,
    `unchecked`, `python` (a Statement's lineage) and `folder`, `saved`, `read`, `shared`,
    `loop` (the Project's). An edge is drawn 2 wide. `kinds_css()` makes each kind's box
    rule and legend swatch rule from it.
  - `page(title, body, css, script) -> str`: the whole page. Its `<style>` is the tokens,
    `BASE_CSS` and `kinds_css()`, then the page's `css` pieces in order; then `body`; then,
    if `script` has a piece, one `<script>` holding each in order.
  - `BASE_CSS`, the CSS both pages shared: body, header, legend swatch, main, the drawing's
    frame, a plain box, its text, an arrow, `pre`, tables, footer.
  - `DRAWING_CSS` and `DRAWING_SCRIPT`, for a drawing that answers the mouse: zoom, pan, and
    a click lighting up a path. The script holds `indexBy`, `escapeHtml`, `shortened`,
    `neighboursOf`, `collectReachable` and `addMouseHandlers(svg, visible)`, where `visible`
    is `{boxes: [{id, group}], arrows: [[source, target, kind]]}` and the SVG's boxes are
    `<g class="n ...">` with ids and its arrows `<path class="e ...">` with `data-a`/`data-b`
    (or `data-g` for a group).
  - `legend(entries)`: the `<div class="key">`, each entry `(kind, words)`, its swatch the
    kind's class, its words escaped; `None` for words alone.
  - `mermaid_class_defs(kinds)` and `mermaid_link_style(numbers, kind)`: the Markdown's
    colours, from the same tokens.
  - `script_json(data)`: JSON a `<script>` can hold, `lineage._script_safe` moved here.
- **The three exports are built from it.** `lineage.to_html` (export_lineage and
  export_run_lineage) and `project_lineage.to_html` (export_project_lineage) each write their
  body with f-strings and call `html_page.page`; each keeps only its own pieces: `CSS`,
  `LEGEND` (and `CONTROLS` and `SCRIPT`, the Statement page's layout, controls and view
  switching, in `lineage.py`). The `PAGE` templates and their `__NAME__` markers are gone but
  the Statement script's one `__DATA__`, filled in once with `str.replace`.
- **No visible change**, checked three ways: the lineage tests pass as they were; the
  Markdown of all 71 pages the lineage tests write is the same before and after but for the
  time in the footer; and for five of them (two Statement pages, a run's page, the Project
  page with a loop and with a table two runs write) a scratch script resolved every
  `var(--name)` and compared each CSS selector's declarations before and after: each is the
  same, the only new rules are each kind's (unused on the other page) and the swatches', and
  no two rules of equal weight on one element and property changed order. The swatches and
  the SVG's size moved from `style=` to rules of the same values.
- **`docs/agents/standards.md` has an "HTML pages" section** with the seven rules, and names
  the test that holds what a test can.
- **Tests: `tests/test_html_page.py`**, reading the pages the three exports write (the
  Project's twice, with a loop and with a shared table) and the Toolbox's files: no hex or
  `rgb()`/`hsl()` colour in any Toolbox file outside `COLOURS`; each page's only colours in its
  `:root` block, and each `var(--name)` a token; each Markdown's colours tokens'; no `style=`
  on a page, scripts' markup included; `external_references` empty for each page; each page
  starting with `page`'s head and holding `BASE_CSS` and a legend; the drawing pages holding
  `DRAWING_CSS` and `DRAWING_SCRIPT`; the Project's Markdown holding
  `mermaid_class_defs`'s lines; only `html_page.py` writing `<!doctype`, `<style` or
  `:root{`; and a colour changed in `COLOURS` changing the page and the Markdown.
- **Decided: CSS custom properties** (`var(--name)`), not colours written into the CSS from
  Python, so a page's colours are in one block a reader (and a test) can find, and the CSS
  pieces are plain constants.
- **Decided: a kind's CSS and Mermaid are made from `KINDS`, not written per page**, so ticket
  05's palette is an edit to `COLOURS` and its contrast test can read each kind's fill from the
  table. A swatch shows its edge 2 wide only for a kind with no fill (the loop's), as before.
- **Decided: every page gets every kind's CSS**, not only its own: a kind's rule matches only
  its class, the two pages' classes don't overlap, and a page can't forget one. Ticket 05's
  "no two kinds on one page share a colour" reads the kinds from each page's `LEGEND`.
- **Decided: a page's own CSS and script stay in its builder**, as pieces passed to `page`;
  the module holds only what more than one page needs. The Statement page's ~600 lines of
  layout and controls stay in `lineage.py`, since only it uses them. Ticket 06 adds its
  panel's CSS and script to the module as `PANEL_CSS` and `PANEL_SCRIPT`, and ticket 07's
  page calls `page` with its own pieces and the drawing's.
- **Decided: `DRAWING_CSS` goes after the page's own CSS** (`page(..., [CSS, DRAWING_CSS],
  ...)`), so a lit path wins over a page's arrow styles, as it did.
- **Decided: the Project page still runs no script and draws the same with scripts off**;
  its SVG's size is a `.wrap svg{min-width;aspect-ratio}` rule in its CSS. The Statement
  page's script sets its SVG's size through `svg.style`, which the standard allows for a size
  a script works out, never a colour.
- **Decided: the legend's words are escaped plain text**, so `&#9888;` became the character
  ⚠ (`lineage.UNCHECKED`), and `"filters"` is written `&quot;filters&quot;`: the same on
  screen.
- **Decided: the Statement page's Markdown keeps no `classDef`**: adding colours to its
  Mermaid would be a visible change; ticket 05 or 06 can add them with
  `mermaid_class_defs`.
- **Decided: `tools/` pages (`how_to_page.py`, `example_gallery.py`, `workflow_graph.py`'s
  Mermaid) are not under the module yet**: the ticket names the three lineage pages; ticket 07
  builds `workflows.html` from it, and the colour test reads only the Toolbox's folder.

## Code review

Run 2026-11-13 with the `code-review` skill against 89798750, `review-standards` and
`review-spec` on Sonnet.

**Spec:** every "Done when" bullet built; no missing requirement, nothing wrong.

- The Statement page's Markdown has no `classDef`: answered above (**Decided**), a visible
  change otherwise.
- Scope: the module's script holds helpers beyond zoom, pan and lighting (`indexBy`,
  `escapeHtml`, `shortened`, `neighboursOf`, `collectReachable`). Kept: the drawing's
  functions call them, and tickets 06 and 07 draw boxes too.
- The standard's JavaScript naming line goes beyond "no build step": kept, as the user's
  "add coding guidelines for the html that we have for python"; made concrete (below).
- Visible-change risk (CSS order, `.wrap svg`'s values): checked as the Answer says; the
  `.wrap svg` values are the old `style=`'s, resolved and compared per selector.

**Standards:** no hard violation.

- Fixed: `lineage.to_html`'s `e = html.escape` alias, now `html.escape` as in
  `project_lineage.to_html`.
- Fixed: `mermaid_link_style(numbers, ...)` is `arrow_numbers`, its docstring saying how
  Mermaid numbers arrows and that the kind has an edge of its own.
- Fixed: the standard's "held to this file's other rules as far as they fit" now names which
  rules reach a script ("Names", "One way per job") and that the Python limits don't.
- Answered: `Drawing`, public-looking in a file that isn't public, follows the file's
  `TableRow`, `ReportPart` and `NamedStatement`; its `size_css` keeps `to_html` free of the
  drawing's sizes.
- Answered: `kinds_css` and `mermaid_class_defs` read `Kind` with the same three `if`s for two
  syntaxes; "Simple over short" prefers the plain repeat to a shared description.
- Answered: the 20-pixel margin and 0.8 minimum appear in the Statement page's JavaScript and
  the Project page's Python: two languages, as before this ticket; ticket 06 may draw the
  Project page with the script and drop the Python one.
- Answered: `legend`'s `None` kind for words alone is said in its docstring; a type for the
  pair is machinery for two callers.
- Answered: `lineage.py` still holds the Statement page's CSS, controls and script: only it
  uses them (**Decided** above).
- Answered: `page(..., script=[])` for a page with no script is the Project page's, which
  draws the same with scripts off.

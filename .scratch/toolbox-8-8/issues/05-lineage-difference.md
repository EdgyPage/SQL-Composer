# The Lineage difference

Type: task
Status: resolved
Blocked by: 02
Size: L

## Question

"Highlight when and where changes occured" (Q8, Q20, Q22): what the Lineage state says changed
between two points, written for the user to read.

## Done when

- **`project.export_lineage_difference(since=None, tables=None)`**, a Project action in the
  Admin log, writes `admin/lineage/<time>-difference.md` and the HTML page (ticket 06 draws it;
  this ticket's page holds the lists in the shared page module's sections).
  - `since=` takes a time (`"2026-11-20"`, `"2026-11-20 06:00"`) or a commit, or nothing: the
    newest recording against the one before. A time or commit no recording matches is refused,
    naming the nearest.
  - `tables=` takes one name or a list: only those tables and every chain that reaches them.
    A name the Lineage state doesn't hold is refused, naming the nearest.
- **For each changed table**, its columns:
  - with an Own change: before and after, own logic and rows that count, and the Building
    block it came from (`because`);
  - with an Inherited change only: its chain down to each root, such as
    "`mart.team_report.fail_rate` ← `mart.team_failures.fails`, own change 2026-11-20 at
    1a2b3c4", and its Effective logic before and after written out by following `reads`;
  - added, removed, retyped, and opaque ("opaque: the whole step changed: read it").
- **When the data changed** (Q20): each changed table's first write after the change, from
  `admin/sent.csv`, "first written with this logic: 2026-11-21 06:00", or "not written since".
- **Toolbox rewrites** (`toolbox`) are folded under "rewritten by the Toolbox's upgrade to
  <version>", never among the Own changes.
- Tables or runs not recorded, with why, at the top.
- Its report names each file written and counts the Own and Inherited changes.
- Each Markdown line is in the HTML page too, as 8.7 holds for the other lineage pages.

## Answer

Built 2026-11-17, on its own branch beside tickets 03 and 04, from dev's 67420e18.

- **`sqlglot_composer/lineage_difference.py`** (in the registry), a pure core over the rows
  `lineage_state.read_rows` gives:
  - `difference(rows, since=None, tables=None, sent=None, not_built=None, call=...) ->
    Difference`, the dataclass ticket 06's drawing reads: `since` (the comparison in words),
    `start` and `end` (the recordings compared, by recorded_at; `end` None when nothing was
    recorded after `start`), `tables` (each `ChangedTable`: its name, kind, `own` or
    `inherited`, its `ChangedColumn`s and `first_written`), `blocks` (each Building block's
    row, as (name, change, recorded_at)), `toolbox` (each `ToolboxRewrite`), `not_recorded`,
    and `kinds` and `reads`, every table either end holds with the tables it reads, for the
    drawing (with `tables=`, only those shown).
  - A `ChangedColumn` holds its change, when and at which commit, its row before and after,
    its Effective logic before and after written out (`effective_logic_text`, a tree down to
    the tables the Project doesn't write, a column met twice written once), each chain from it
    down to a root (inherited), and its Building blocks (own).
  - The change over several recordings: added or removed between the two ends, else the
    weightiest a row says (opaque, own, retyped), else inherited; added-and-removed again in
    between is left out; an Upgrade's `toolbox` rows are never among them, only in `toolbox`.
  - `first_written`: the first row of `admin/sent.csv` after the table's last change whose
    tables include it; only a Saved table has one.
- **`since=`:** left out, the recording before the newest against the newest; a time
  (`2026-11-20`, `2026-11-20 06:00`, `... 06:00:00`) starts from the last recording at or
  before it; a commit, whole or short, any case, from the last recording made at it.
  **A change to the ticket:** a time before the first recording starts from the first, and the
  page says so ("since 2026-11-20, from the first recording, of ..."), since a day the first
  recording was made on would otherwise be refused. A commit no recording was made at is
  refused, naming the nearest (difflib) or every commit recorded; text that is neither is
  refused; so is a Project with no Lineage state.
- **`tables=`:** one name or a list; each must be a table (or `<run>.<result>`) the state holds,
  else refused with "Did you mean ...?"; the difference keeps those and every table on the
  chains of their inherited changes.
- **The pages:** `to_markdown` and `to_html`, the same Parts (`html_page.part_markdown` and
  `part_html`): the counts line; "Not recorded"; a section per changed table (own first), its
  first-written line, and a sub-section per column (when, commit, Building block, opaque note,
  type, own logic and rows that count before and after, with Copy, chains, Effective logic
  before and after); "Building blocks changed"; each Upgrade's rewrite, folded in a
  `<details>` on the page. Built by `html_page.page` with `PANEL_CSS` and `PANEL_SCRIPT`, whose
  `copyHive` the page's own short script calls for each Copy button. No drawing and no panel
  yet: ticket 06 adds them.
- **`project.export_lineage_difference(since=None, tables=None)`**, in `project.__all__` and
  `PROJECT_NAMES`, a Project action in the Admin log (its Files line names the two files, its
  Tables named line `tables=`): it works out `effective_logic.project_logic(root)` only for
  `not_built`, then writes `admin/lineage/<time>-difference.html` and `.md`. The module
  docstring's layout and lists name it. Its docstring example is in the Example gallery,
  `docs/main/examples.html`, written again.
- **Tests:** `tests/test_lineage_difference.py`, 19: own and inherited, the Effective logic
  written out and a column met twice, a retyped root two tables down with its chain, a
  Building block, added, removed and opaque, an Upgrade's rewrite apart, since= left out, as a
  time or a commit, refused three ways, tables= and its refusal, no state, one recording,
  first written from sent.csv, every Markdown line on the page with no style and nothing
  external, and the export end to end on the Intermediate Example project, its
  `events_per_job` changed, `tables="mart.team_days"`.
- **Fragile:** recordings are told apart by `recorded_at`, to the second. Two recordings in one
  second (a Project action recording twice, or two notebooks' `export_hive()` at once) read as
  one: their rows merge into one recording, which `columns_at` replays in file order, so the
  state stays right, but the difference can't start between them.

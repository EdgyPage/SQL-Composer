# The Lineage difference

Type: task
Status: open
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

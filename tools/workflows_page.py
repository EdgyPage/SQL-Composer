"""Write the Workflows overview, `docs/main/workflows.html`: every Workflow and the Excel
path in one drawing, an arrow for each hand-off, and, for the one you click, its steps and its
common tripping points (Toolbox 8.7, ticket 07).

Run it on `dev` after changing a Workflow's steps, a hand-off or a tripping point:

    python tools/workflows_page.py

A test fails while the committed page differs from what this writes.

The page is high level by the user's words: "Don't include all documentation, that's what the
search documents for Copilot are for. High level to bullet points." So each Workflow shows what
it does, what it starts from and ends with, its steps by name, as its notebook's headings name
them, and a few tripping points; each links its how-to for the rest.

- **Each Workflow's steps** come from `sqlglot_composer/workflows.py`, as
  `tools/workflow_graph.py` draws them and each notebook's step headings name them; the Excel
  path's from workflow_graph's `EXCEL_FLOW`, each its sentence up to its first colon.
- **The hand-offs** (`HAND_OFFS`) and **the tripping points** (`TRIPPING_POINTS`) are written
  here by hand, the tripping points drawn from the usability rounds' findings in
  `.eval-local/usability/results.md`: what tripped a run, said as what to do.
- **The page** is built with the page module, `sqlglot_composer/html_page.py`: its tokens, base
  CSS, legend and drawing script, which lights up a box's path when it is clicked. Its own
  script shows the clicked Workflow's part of the side panel. With scripts off, every part
  shows, one under another.
"""

from __future__ import annotations

import html
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import toolbox_registry  # noqa: E402
from workflow_graph import EXCEL_FLOW  # noqa: E402

from sqlglot_composer import html_page, workflows  # noqa: E402
from sqlglot_composer.workflows import Workflow  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PAGE_PATH = ROOT / toolbox_registry.DOCS_ON_DEV / "workflows.html"
HOW_TOS = ROOT / "worked_examples" / "how_to"

class Box(NamedTuple):
    """One box of the drawing: a Workflow's name, or "excel"; its title and the line under it;
    its column and row, a row's half a step apart; its kind, as html_page.KINDS names it; and
    the how-to that walks through it in full, by its link, or "" for none."""

    name: str
    title: str
    says: str
    column: int
    row: float
    kind: str
    how_to: str


BOXES = (
    Box("references", "references", "Table references from DESCRIBE", 0, 0.6, "workflow",
        "add_your_tables_references"),
    Box("excel", "the Excel path", "a Formula workbook, as Hive", 0, 1.9, "excel", ""),
    Box("new_table", "new_table", "a new Saved table, in dev", 1, 0, "workflow",
        "save_a_table"),
    Box("convert", "convert", "someone else's Hive, into dev", 1, 1.3, "workflow",
        "convert_someone_elses_hive"),
    Box("promote", "promote", "dev tables carried to prod", 2, 0.65, "workflow",
        "follow_a_workflow"),
    Box("schedule", "schedule", "a run for your scheduler", 3, 0, "workflow",
        "schedule_a_run"),
    Box("change_a_saved_table", "change_a_saved_table", "a change sent to one table", 3, 1.3,
        "workflow", "keep_the_project_in_order"),
    Box("upgrade", "upgrade", "after a new Toolbox comes", 3, 2.4, "workflow",
        "upgrade_your_project_to_a_new_toolbox_version"),
)


class HandOff(NamedTuple):
    """An arrow: what one Workflow, or the Excel path, makes that the next starts from."""

    source: str
    target: str
    what: str


HAND_OFFS = (
    HandOff("references", "new_table", "a Table reference for each table its logic reads"),
    HandOff("references", "convert", "a Table reference for each table its scripts read"),
    HandOff("excel", "convert", "the workbook's Hive, saved as .hql files, as one batch"),
    HandOff("new_table", "promote", "tables in dev, each Decision made"),
    HandOff("convert", "promote", "tables in dev, each Decision made and each compared"),
    HandOff("promote", "schedule", "Saved tables, for a run to write on your scheduler's "
            "timetable"),
    HandOff("promote", "change_a_saved_table", "a Saved table in the warehouse, to change "
            "with an Admin statement"),
)

# What tripped people up in the usability rounds, said as what to do: for every Workflow
# ("every"), then for each box. `code` is written in backticks.
TRIPPING_POINTS: dict[str, tuple[str, ...]] = {
    "every": (
        "Run a notebook's cells one at a time, never Run All: a step after a decision would "
        "write before you make it.",
        "Fill in `connect(...)` in each notebook's setup cell, its first code cell: until you "
        "do, `query` and `execute` refuse.",
        "\"Run up to your Decisions\" runs to the end when nothing waits on you, writing and "
        "comparing each table: to see what it would send first, add `dry_run=True` to its "
        "`project.run_workflow(...)` call.",
        "Paste what it prints over the decisions cell, fill in each `\"<FILL IN>\"` and save "
        "the notebook before you run on.",
        "Lost your place? `project.check()` names the next step of each Workflow you have "
        "started.",
        "In a script of your own, not a notebook, print a Project action's report, such as "
        "`print(project.check())`: a script shows nothing on its own.",
        "Changed a table's logic, a Table reference or a Building block by hand? Run the "
        "Table notebook's cell 5, or `project.record_lineage_state()` in "
        "`admin/lineage.ipynb`: until you do, `project.check()` says the Lineage state is "
        "behind.",
    ),
    "references": (
        "Run it before convert or new_table: the tables they read need their Table "
        "references first.",
        "A Key is the columns whose values name exactly one row: check yours with "
        "`check_key` before you answer it, giving a partitioned table `where=`, one "
        "Partition.",
    ),
    "new_table": (
        "The tables its logic reads need their Table references first: run references for "
        "them.",
        "Have a query already? Give it in `QUERIES`, and its logic is written for you, by a "
        "convert batch run for you; else you write the logic in its Table notebook, where "
        "step 2 waits on you.",
        "Step 2 waits on you even with no Decision open: its cell's `preview()` says what "
        "stops a table's logic, if anything does. Mend it, save the Table notebook, and run "
        "\"Run up to your Decisions\" again: it goes on from step 2.",
        "A Table notebook's TODO lines are yours: fill each in, or delete it.",
    ),
    "convert": (
        "The tables its scripts read need their Table references first: run references for "
        "them.",
        "A table's copy in dev is named for the table and its database: `mart.team_fails` "
        "becomes `mart_dev.team_fails_mart`. Give `RENAME` in the names cell for a name of "
        "your own.",
        "One query, not a whole script? convert takes it, or new_table's `QUERIES`, which "
        "runs a convert batch for you.",
        "The compare checks only the latest Partition both tables hold: name others in "
        "`PARTITIONS`.",
        "A Script tag, `<PARM=\"NAME\"/>`, is a Decision: answer it under `\"tags\"`, as Hive "
        "text or a Run value's function.",
        "A table that reads itself is seeded once from its original: a `\"seed\"` answer "
        "limits the Partitions it copies.",
    ),
    "promote": (
        "Fill in `PROD` in `admin/databases.py` first: each prod table's location is placed "
        "under its `location_root`.",
        "It takes finished tables in dev, each Decision made: `TABLES` left `[]` promotes "
        "every one not promoted yet.",
        "Its decisions step may have nothing to answer, each location placed for you: run on.",
    ),
    "schedule": (
        "The run's notebook has a Build cell, which prints the Hive and sends nothing, and a "
        "Run cell, which sends it: read the Build's Hive first.",
        "Give each value the scheduler passes in a type hint and a default: one left empty "
        "whose hint has no `| None` is refused.",
        "A value the scheduler passes in reaches only the Statements the run hands it to: "
        "work out its days in `statements()` and pass them plain, such as "
        "`write_days(str(monday), str(sunday))`, or give a write the build adds its value "
        "with `run_values=` in the Build cell.",
    ),
    "change_a_saved_table": (
        "An Admin statement is a change to a Saved table itself, such as dropping some of "
        "its Partitions: write yours in step 1's cell.",
        "Read the Hive step 2 prints, and what its check shows, such as the table's "
        "Partitions, before step 3 sends it.",
        "A `where=` takes a Condition, such as `equals(table.dt, \"2026-09-24\")`: step 1's "
        "cell imports `equals` and `between`.",
    ),
    "upgrade": (
        "Copy in the new `sqlglot_composer` folder whole, then restart the kernel before step "
        "1: until you do, it still holds the old code.",
        "Each `UPGRADE` mark names a change only you can make: make it, then delete the mark.",
    ),
    "excel": (
        "Give Copilot all three files, 15, 11 and 12, from the `copilot/` folder, with the "
        "workbook.",
        "Check each name Copilot leaves in angle brackets, such as `<database>`, against your "
        "sheet's notes before you fill it in.",
        "A Table's Total Row, its sums under its last row, becomes a query of its own: a "
        "Saved table refuses subtotal rows.",
        "A list typed into the workbook, such as its teams, and each value on its Parameters "
        "sheet are written into the Hive as they are: a team added later, or a changed rate, "
        "doesn't reach the table until you change the Hive.",
    ),
}

# What the Excel path is, as its part of the panel says it.
EXCEL_ABOUT = ("Turns a Formula workbook into Hive through Copilot, then into Saved tables "
               "through the convert Workflow, and on to prod through promote.")

# How a Workflow notebook's four cells run, as the README's "The Workflows" says it, for the
# panel's first part.
FOUR_CELLS = (
    "**Name what it works on**: fill in the names cell, the code cell under the setup cell, "
    "and save the notebook.",
    "**Run up to your Decisions**: run the cell under it; it runs every step up to the first "
    "only you can do, and prints the `DECISIONS` to paste.",
    "**Make the decisions**: paste it over the decisions cell, fill it in, and save.",
    "**Run the rest**: run the cell under the decisions cell; it goes on from where it "
    "stopped.",
)

# The words the parts use most, as CONTEXT.md says them, shortened, for the panel's first
# part.
WORDS = (
    "**Saved table**: a real table in the warehouse that your code writes.",
    "**Table reference**: a file describing one table: its columns, Partitions and Key.",
    "**Decision**: one thing about one table that only you decide, such as its Key.",
    "**Key**: the columns whose values name exactly one row.",
    "**Partition**: a slice of a table, such as one day's rows.",
    "**Dev and Prod Database**: where your tables are built and checked first, and where "
    "others read them once promoted.",
)

# A step's kind, as its tag on the panel says it.
KIND_TAG = {workflows.FILE_STEP: "files only", workflows.PERMISSION: "calls the warehouse",
            workflows.DECISION: "your decision", workflows.FIDDLING: "by hand"}

# The drawing's sizes, in pixels: a box, the gap between two columns, a row's height, and
# where each of a box's two lines of text sits.
BOX_WIDTH, BOX_HEIGHT, COLUMN_GAP, ROW_HEIGHT = 230, 46, 70, 80
TITLE_Y, SAYS_Y = 19, 36
# How long an arrow's head is, and half its width.
HEAD_LENGTH, HEAD_HALF_WIDTH = 9, 5

CSS = """\
header p{margin:0 0 6px;max-width:70em}
.overview{display:grid;grid-template-columns:minmax(0,2fr) minmax(320px,1fr);gap:16px;\
align-items:start}
.overview .wrap{position:sticky;top:8px}
@media (max-width:860px){.overview{grid-template-columns:minmax(0,1fr)}\
 .overview .wrap{position:static}}
.n:focus{outline:none} .n:focus rect{stroke:var(--lit);stroke-width:2}
.e.head{fill:var(--arrow);stroke:none} .e.head.hit{fill:var(--lit)}
.panel section{border:1px solid var(--faint-rule);padding:2px 14px 10px;margin-bottom:12px}
.scripted .panel section:not(.shown){display:none}
.panel h2{font-size:17px;margin:10px 0 6px} .panel h3{font-size:14px;margin:14px 0 4px}
.panel ul,.panel ol{margin:4px 0;padding-left:22px} .panel li{margin:3px 0}
.tag{font-size:11px;color:var(--muted);border:1px solid var(--rule);border-radius:8px;\
padding:0 6px;margin-left:6px;white-space:nowrap}
.tag.yours{color:var(--ink);border-color:var(--box-edge)}
code{font-family:ui-monospace,monospace;font-size:12.5px}"""

SCRIPT = """\
// The overview's own script: clicking a Workflow's box, or a link to one in the panel, shows
// that Workflow's part of the panel in place of the one shown, and lights up its path.

// Show the part of the panel whose id is `name`, and hide the rest.
function showPart(name) {
  document.querySelectorAll('.panel section').forEach(section => {
    section.classList.toggle('shown', section.id === name);
  });
}

// The name of the Workflow, or "excel", whose box is `box`: its id after box_.
function nameOfBox(box) {
  return box.id.slice('box_'.length);
}

// Click the box of the Workflow `name`, as the mouse would, so its path lights up too.
function clickBox(name) {
  const box = document.getElementById('box_' + name);
  if (box) {
    box.dispatchEvent(new MouseEvent('click', {bubbles: true}));
  } else {
    showPart(name);
  }
}

const svg = document.querySelector('.wrap svg');
addMouseHandlers(svg, VISIBLE);
document.body.classList.add('scripted');
svg.addEventListener('click', event => {
  const box = event.target.closest('.n');
  if (box) {
    showPart(nameOfBox(box));
  }
});
// Enter or the space bar on a box chosen with Tab clicks it.
svg.addEventListener('keydown', event => {
  const box = event.target.closest('.n');
  if (box && (event.key === 'Enter' || event.key === ' ')) {
    event.preventDefault();
    clickBox(nameOfBox(box));
  }
});
document.querySelectorAll('.panel a.go').forEach(link => {
  link.addEventListener('click', event => {
    event.preventDefault();
    clickBox(link.getAttribute('href').slice(1));
  });
});
// A link to a part, such as workflows.html#convert, opens on it; any other on the first.
const opened = window.location.hash.slice(1);
if (opened && document.getElementById(opened)) {
  clickBox(opened);
} else {
  showPart('every');
}"""


def workflow_of(name: str) -> Workflow:
    """The Workflow named `name`, as workflows.py holds it."""
    for workflow in workflows.WORKFLOWS:
        if workflow.name == name:
            return workflow
    raise KeyError(f"No Workflow is named {name!r}.")


def excel_steps() -> list[str]:
    """The Excel path's steps, as workflow_graph's EXCEL_FLOW lists them, each its sentence up
    to its first colon."""
    return [said.split(": ")[0] for said, _ in EXCEL_FLOW[1]]


def how_to_title(slug: str) -> str:
    """A how-to's title, the first line of its docstring, by its link."""
    path = next(HOW_TOS.glob(f"[0-9][0-9]_{slug}.py"))
    return path.read_text(encoding="utf-8").split("\n", 1)[0].removeprefix('"""')


def inline(text: str) -> str:
    """Text as the page shows it: escaped, each `code` in backticks as code and each **bold**
    in bold."""
    shown = html.escape(text, quote=False)
    shown = re.sub(r"`([^`]+)`", r"<code>\1</code>", shown)
    return re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", shown)


def bullets(items: Sequence[str], tag: str = "ul") -> str:
    """A list of the page's, each item shown as `inline` shows it."""
    return f"<{tag}>" + "".join(f"<li>{inline(item)}</li>" for item in items) + f"</{tag}>"


def tripping_points_html(name: str) -> str:
    """A part's common tripping points, under their heading: a box's, or every Workflow's."""
    return f"<h3>Common tripping points</h3>{bullets(TRIPPING_POINTS[name])}"


def top_left(box: Box) -> tuple[int, int]:
    """Where a box's top left corner is drawn."""
    return box.column * (BOX_WIDTH + COLUMN_GAP), round(box.row * ROW_HEIGHT)


def drawing() -> str:
    """The SVG: each box, and each hand-off a curve from the middle of one box's right side to
    the middle of the next one's left side, ending in its head."""
    boxes = {box.name: box for box in BOXES}
    parts = []
    for hand_off in HAND_OFFS:
        (x, y), (x2, y2) = top_left(boxes[hand_off.source]), top_left(boxes[hand_off.target])
        start, end = (x + BOX_WIDTH, y + BOX_HEIGHT // 2), (x2, y2 + BOX_HEIGHT // 2)
        middle = (start[0] + end[0]) // 2
        ends = f'data-a="box_{hand_off.source}" data-b="box_{hand_off.target}"'
        title = (f"<title>{html.escape(hand_off.source)} to {html.escape(hand_off.target)}: "
                 f"{html.escape(hand_off.what)}</title>")
        parts.append(f'<path class="e" {ends} d="M{start[0]},{start[1]} C{middle},{start[1]} '
                     f'{middle},{end[1]} {end[0] - HEAD_LENGTH},{end[1]}">{title}</path>')
        parts.append(f'<path class="e head" {ends} d="M{end[0]},{end[1]} '
                     f"l{-HEAD_LENGTH},{-HEAD_HALF_WIDTH} v{2 * HEAD_HALF_WIDTH} z\"/>")
    for box in BOXES:
        x, y = top_left(box)
        parts.append(f'<g class="n {box.kind}" id="box_{box.name}" tabindex="0" '
                     f'role="button" transform="translate({x},{y})">'
                     f'<rect width="{BOX_WIDTH}" height="{BOX_HEIGHT}" rx="4"/>'
                     f'<text x="10" y="{TITLE_Y}" class="l">{html.escape(box.title)}</text>'
                     f'<text x="10" y="{SAYS_Y}">{html.escape(box.says)}</text>'
                     f"<title>{html.escape(box.title)}: click for its steps and tripping "
                     "points</title></g>")
    width, height = drawing_size()
    # A 10-pixel margin all round, as size_css says too.
    return f'<svg viewBox="-10 -10 {width + 20} {height + 20}">{"".join(parts)}</svg>'


def drawing_size() -> tuple[int, int]:
    """How wide and how high the boxes reach, from the drawing's top left corner."""
    return (max(top_left(box)[0] for box in BOXES) + BOX_WIDTH,
            max(top_left(box)[1] for box in BOXES) + BOX_HEIGHT)


def size_css() -> str:
    """The CSS that sizes the drawing: its viewBox's shape, never shrunk below half its full
    width."""
    width, height = drawing_size()
    return f".wrap svg{{min-width:{width // 2}px;aspect-ratio:{width + 20}/{height + 20}}}"


def hand_offs_html(name: str) -> str:
    """A part's hand-offs: where it comes from and where it goes on to, each a link to that
    part."""
    items = [f'From <a class="go" href="#{hand_off.source}">{hand_off.source}</a>: '
             f"{inline(hand_off.what)}." for hand_off in HAND_OFFS if hand_off.target == name]
    items += [f'On to <a class="go" href="#{hand_off.target}">{hand_off.target}</a>: '
              f"{inline(hand_off.what)}." for hand_off in HAND_OFFS if hand_off.source == name]
    if not items:
        return ("<p>None: run it on its own, whenever you copy in a new Toolbox, before "
                "any other Workflow.</p>")
    return "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"


def in_full(box: Box) -> str:
    """The line under a part that links the how-to walking through it in full."""
    if not box.how_to:
        return ("<p>In full: the README's \"Have Copilot write it\", and the Copilot files' "
                "own words.</p>")
    return (f'<p>In full: the how-to <a href="how_to.html#{box.how_to}">'
            f"{html.escape(how_to_title(box.how_to))}</a>.</p>")


def workflow_part(box: Box) -> str:
    """A Workflow's part of the panel: what it does, its notebook and names cell, what it
    starts from and ends with, its steps, its tripping points and its hand-offs."""
    workflow = workflow_of(box.name)
    notebook = f"admin/workflows/{workflow.name}/{workflow.name}.ipynb"
    if workflow.inputs:
        names = [f"<code>{html.escape(given.name)}</code>" for given in workflow.inputs]
        names_said = f"Its names cell: {', '.join(names)}."
    else:
        names_said = "It has no names cell."
    steps = "".join(
        f'<li>{html.escape(step.name)}<span class="tag'
        f'{" yours" if step.kind == workflows.DECISION else ""}">'
        f"{KIND_TAG[step.kind]}</span></li>" for step in workflow.steps)
    return (f'<section id="{box.name}"><h2>{html.escape(box.title)}</h2>'
            f"<p>{inline(workflow.about)}</p>"
            f'<p class="muted">Its notebook: <code>{notebook}</code>. {names_said}</p>'
            f"<h3>Starts from</h3>{bullets(workflow.start_materials)}"
            f"<h3>Ends with</h3>{bullets(workflow.end_artifacts)}"
            f'<h3>Its steps</h3><ol class="steps">{steps}</ol>'
            f"{tripping_points_html(box.name)}"
            f"<h3>Hand-offs</h3>{hand_offs_html(box.name)}{in_full(box)}</section>")


def excel_part(box: Box) -> str:
    """The Excel path's part of the panel: what it does, its steps, its tripping points and its
    hand-offs."""
    return (f'<section id="{box.name}"><h2>{html.escape(box.title)}</h2>'
            f"<p>{inline(EXCEL_ABOUT)}</p>"
            f'<h3>Its steps</h3>{bullets(excel_steps(), "ol")}'
            f"{tripping_points_html(box.name)}"
            f"<h3>Hand-offs</h3>{hand_offs_html(box.name)}{in_full(box)}</section>")


def every_part() -> str:
    """The panel's first part, shown until you click a box: how a Workflow notebook runs,
    which Workflow is for which job, and what trips people up in every one."""
    choices = "".join(
        f'<li><a class="go" href="#{box.name}">{html.escape(box.title)}</a>: '
        f"{html.escape(box.says)}.</li>" for box in BOXES)
    return ('<section id="every"><h2>Every Workflow</h2>'
            "<p>A Workflow is a notebook in <code>admin/workflows/</code> whose steps take you "
            "from what you start with to one end goal. Click a box for its steps.</p>"
            f"<h3>Which one</h3><ul>{choices}</ul>"
            "<h3>How its notebook runs</h3>"
            f"<p>The convert, promote, new_table and references notebooks read top to bottom, "
            f"in four cells:</p>{bullets(FOUR_CELLS, 'ol')}"
            "<p>In upgrade, change_a_saved_table and schedule, run each step's cell in turn."
            "</p>"
            "<p>Each step's tag says what it is: <i>files only</i> changes only files, or only "
            "prints; <i>calls the warehouse</i> sends to the warehouse, when you run it; "
            "<i>your decision</i> waits on you.</p>"
            f"<h3>Words</h3>{bullets(WORDS)}"
            "<h3>Beside the Workflows</h3>"
            "<p>Two notebooks in <code>admin/</code> belong to no one Workflow: "
            "<code>admin/check_project.ipynb</code>, which checks the Project and names the "
            "next step of each Workflow you have started, and "
            "<code>admin/lineage.ipynb</code>, which records the Lineage state and exports "
            "the Lineage difference: what changed a column, and where up its chain.</p>"
            f"{tripping_points_html('every')}"
            f'<p>In full: the how-to <a href="how_to.html#follow_a_workflow">'
            f'{html.escape(how_to_title("follow_a_workflow"))}</a>.</p></section>')


def page_text() -> str:
    """workflows.html, as this writes it."""
    parts = [every_part()]
    for box in BOXES:
        parts.append(excel_part(box) if box.kind == "excel" else workflow_part(box))
    visible = {"boxes": [{"id": f"box_{box.name}", "group": box.kind} for box in BOXES],
               "arrows": [[f"box_{hand_off.source}", f"box_{hand_off.target}", "e"]
                          for hand_off in HAND_OFFS]}
    legend = html_page.legend([
        ("workflow", "a Workflow: a notebook in admin/workflows/"),
        ("excel", "the Excel path: a workbook to Hive, through Copilot"),
        (None, "an arrow: a hand-off, what one makes and the next starts from"),
        (None, "click a box for its steps and tripping points")])
    body = ("<header><h1>The Workflows</h1>"
            "<p>Every job a Project goes through, and how one hands off to the next. High "
            "level only: each part links its how-to for the rest.</p>"
            f"{legend}</header>\n"
            f'<main class="overview"><div class="wrap">{drawing()}</div>\n'
            f'<aside class="panel">\n' + "\n".join(parts) + "\n</aside></main>\n"
            "<footer>Each Workflow's steps are the steps its notebook runs, by the same names."
            "</footer>")
    script = f"const VISIBLE = {html_page.script_json(visible)};\n{SCRIPT}"
    return html_page.page("The Workflows", body, [CSS, size_css(), html_page.DRAWING_CSS],
                          [html_page.DRAWING_SCRIPT, script])


def main() -> int:
    """Write the page, unless it holds what this writes already."""
    text = page_text()
    if not PAGE_PATH.exists() or PAGE_PATH.read_text(encoding="utf-8") != text:
        PAGE_PATH.write_text(text, encoding="utf-8", newline="\n")
        print(f"Wrote {PAGE_PATH.relative_to(ROOT).as_posix()}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

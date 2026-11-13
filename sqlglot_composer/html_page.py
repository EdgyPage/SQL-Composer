"""The one module every HTML page the Toolbox writes is built from (Toolbox 8.7, ticket 04): the
colour tokens, each written once; the base CSS, which names a colour only by its token; the
legend and the Mermaid classDef lines, made from the tokens; and the drawing's script, which
zooms, pans and lights up a path. docs/agents/standards.md's "HTML pages" is the standard each
page keeps.

It isn't brought by `from sqlglot_composer import *`, and isn't for you to call: export_lineage
and project.export_run_lineage build their page with lineage.py, and
project.export_project_lineage with project_lineage.py, each from here. The Workflows overview,
workflows.html, beside this file, is built from here too, by a tool on dev (ticket 07).

A page is `page(title, body, css, script)`: the head, the tokens, the base CSS and each kind's
CSS come from here; `css` and `script` are the page's own pieces after them, its own and those
it takes from here, such as DRAWING_CSS and DRAWING_SCRIPT. A new kind of box is a row of KINDS,
its colours rows of COLOURS; a palette change is an edit to COLOURS alone.
"""

from __future__ import annotations

import html
import json
from typing import NamedTuple

# Every colour a page uses, by its name: the one place a colour is written. The CSS names each
# as var(--name), and the Mermaid charts write it out from here. Two names may hold the same
# colour, each for its own job.
COLOURS: dict[str, str] = {
    # The page
    "ink": "#222",  # text, and a box's first line
    "page": "#fff",  # the page's background, and a menu's
    "muted": "#777",  # quieter text: a note, the footer
    "rule": "#ddd",  # the header's line, and a table's
    "faint-rule": "#eee",  # around the drawing, and under the controls
    "menu-edge": "#ccc",
    "shadow": "#0002",  # under a menu
    "code": "#f7f7f7",  # behind a block of Hive
    # The drawing
    "box": "#fff",  # a box of no kind
    "box-edge": "#888",  # a box's edge, and a legend swatch's
    "box-text": "#000",  # a box's lines after its first, dark enough for every kind's fill
    "arrow": "#aaa",
    "rows-arrow": "#c9c9c9",  # a dotted arrow
    "filters-arrow": "#b5b5b5",
    "filters-label": "#999",
    "lit": "#000",  # a path lit up by a click: black, as red is the loops' alone
    "group": "#fafafa",  # a group's frame, in the Grouped flowchart
    "group-edge": "#c8c8c8",
    "group-label": "#555",
    # A group of a kind's frame: a pale tint of its kind's colour
    "table-group": "#eef7fd",
    "derived-group": "#fefcec",
    "output-group": "#e6f5f1",
    "condition-group": "#fbfbfb",
    # Each kind of box, as KINDS names them: saturated colours from the Okabe–Ito set, chosen
    # to stay distinguishable with colour blindness, a grey for the dashed kinds, and the
    # loops' red, used for nothing else. Every fill takes the same dark text, and no two kinds
    # on one page share a colour.
    "table": "#56b4e9",  # sky blue
    "derived": "#f0e442",  # yellow
    "output": "#009e73",  # bluish green
    "condition": "#bbb",  # grey, dashed: a condition decides rows, it carries no value
    "unchecked": "#e69f00",  # orange
    "unchecked-edge": "#000",  # black, as each edge drawn to be looked at
    "python": "#cc79a7",  # reddish purple
    "python-edge": "#000",
    "folder": "#56b4e9",  # as a table column's
    "saved": "#009e73",  # as an output column's
    "read": "#bbb",  # as a condition's
    # Yellow, not Unchecked's orange: a shared table in a loop takes the loop's red edge,
    # which orange would hide.
    "shared": "#f0e442",
    "shared-edge": "#000",
    "loop": "#d33",  # red: Okabe–Ito's vermillion reads as orange
    "loop-text": "#a11",  # the words of the note at the top of a loop: a darker red
    "workflow": "#56b4e9",  # sky blue: a Workflow on the overview page
    "workflow-edge": "#000",
    "excel": "#009e73",  # bluish green: the Excel path
    "excel-edge": "#000",
}


class Kind(NamedTuple):
    """How a kind of box is drawn: the token of its fill, None for a plain box's; the token of
    its edge, drawn twice as thick, None for a plain box's; and whether its edge is dashed."""

    fill: str | None
    edge: str | None = None
    dashed: bool = False


# Each kind of box, by the class a box of that kind is drawn with. A box may have more than
# one: a later kind's colours win over an earlier one's.
KINDS: dict[str, Kind] = {
    # A Statement's lineage: a column of each
    "table": Kind("table"),
    "derived": Kind("derived"),
    "output": Kind("output"),
    "condition": Kind("condition", dashed=True),
    "unchecked": Kind("unchecked", "unchecked-edge"),
    "python": Kind("python", "python-edge"),
    # The Project's lineage: a table of each
    "folder": Kind("folder"),
    "saved": Kind("saved"),
    "read": Kind("read", dashed=True),
    "shared": Kind("shared", "shared-edge"),
    "loop": Kind(None, "loop"),
    # The Workflows overview: a box for each Workflow, and one for the Excel path
    "workflow": Kind("workflow", "workflow-edge"),
    "excel": Kind("excel", "excel-edge"),
}

# The CSS every page starts with, after its tokens.
BASE_CSS = """\
body{margin:0;font:14px system-ui,sans-serif;color:var(--ink);background:var(--page)}
header{padding:12px 16px;border-bottom:1px solid var(--rule)} h1{font-size:18px;margin:0 0 6px}
.key span{display:inline-block;margin-right:14px}
.sw{display:inline-block;width:12px;height:12px;border:1px solid var(--box-edge);\
vertical-align:-1px;margin-right:4px}
main{padding:8px 16px 40px} .wrap{overflow-x:auto;border:1px solid var(--faint-rule)}
svg{width:100%;height:auto;display:block}
.n rect{fill:var(--box);stroke:var(--box-edge)}
.n text{font-size:11px;fill:var(--box-text);font-family:ui-monospace,monospace}\
 .n text.l{font:600 13px system-ui,sans-serif;fill:var(--ink)}
.e{fill:none;stroke:var(--arrow);stroke-width:1.3}
pre{background:var(--code);padding:8px;overflow:auto} .muted{color:var(--muted)}
table{border-collapse:collapse}\
 td,th{border:1px solid var(--rule);padding:4px 8px;text-align:left}
footer{padding:8px 16px 24px;color:var(--muted);font-size:12px}"""

# The CSS of a drawing DRAWING_SCRIPT makes answer the mouse: a drag pans it, and a click
# lights up a path and dims the rest. It goes after the page's own CSS, so a lit path wins.
DRAWING_CSS = """\
svg{cursor:grab} .n{cursor:pointer}
.dim{opacity:.15} .hit rect{stroke:var(--lit);stroke-width:2}\
 .e.hit{stroke:var(--lit);stroke-width:2;opacity:1}"""


def page(title: str, body: str, css: list[str], script: list[str]) -> str:
    """An HTML page, whole: titled `title`, its CSS the tokens, BASE_CSS and each kind's, then
    the pieces of `css` in order; `body` inside its <body>; then, if `script` has any piece,
    one <script> holding each in order. `body` and each piece are written as given, so any
    text in them is escaped already."""
    head = ('<!doctype html>\n<html><head><meta charset="utf-8">'
            f"<title>{html.escape(title)}</title><style>\n"
            + "\n".join([tokens_css(), BASE_CSS, kinds_css(), *css])
            + "\n</style></head><body>\n")
    if not script:
        return f"{head}{body}\n</body></html>\n"
    return f"{head}{body}\n<script>\n" + "\n".join(script) + "\n</script></body></html>\n"


def tokens_css() -> str:
    """The CSS that defines each colour token, as var(--name) names it."""
    return ":root{" + ";".join(f"--{name}:{value}" for name, value in COLOURS.items()) + "}"


def kinds_css() -> str:
    """The CSS of each kind of box, a line each: its box's rectangle, then its legend swatch,
    which shows the edge twice as thick only for a kind with no fill of its own."""
    lines = []
    for name, kind in KINDS.items():
        box, swatch = [], []
        if kind.fill:
            box.append(f"fill:var(--{kind.fill})")
            swatch.append(f"background:var(--{kind.fill})")
        if kind.edge:
            box += [f"stroke:var(--{kind.edge})", "stroke-width:2"]
            swatch.append(f"border-color:var(--{kind.edge})")
        if kind.edge and not kind.fill:
            swatch.append("border-width:2px")
        if kind.dashed:
            box.append("stroke-dasharray:4 3")
            swatch.append("border-style:dashed")
        lines.append(f".{name} rect{{{';'.join(box)}}} .sw.{name}{{{';'.join(swatch)}}}")
    return "\n".join(lines)


def legend(entries: list[tuple[str | None, str]]) -> str:
    """The legend under a page's title: for each entry, the swatch of its kind, as KINDS names
    it, then its words; an entry whose kind is None is words alone, such as what the arrows
    mean."""
    spans = []
    for kind, words in entries:
        swatch = ""
        if kind is not None:
            swatch = f'<i class="sw {kind}"></i>'
        spans.append(f"<span>{swatch}{html.escape(words)}</span>")
    return '<div class="key">\n' + "\n".join(spans) + "\n</div>"


def mermaid_class_defs(kinds: list[str]) -> list[str]:
    """A Mermaid classDef line for each of `kinds`, as KINDS names them, coloured from the
    tokens as the page colours them: a kind with no edge of its own has a plain box's."""
    lines = []
    for name in kinds:
        kind = KINDS[name]
        parts = []
        if kind.fill:
            parts.append(f"fill:{COLOURS[kind.fill]}")
        parts.append(f"stroke:{COLOURS[kind.edge or 'box-edge']}")
        if kind.edge:
            parts.append("stroke-width:2px")
        if kind.dashed:
            parts.append("stroke-dasharray:4 3")
        lines.append(f"  classDef {name} {','.join(parts)}")
    return lines


def mermaid_link_style(arrow_numbers: list[str], kind: str) -> str:
    """A Mermaid linkStyle line drawing the arrows numbered `arrow_numbers`, each as Mermaid
    counts them from 0 in the order they are written, in the edge of `kind`, as KINDS names
    it, as thick as its box's. `kind` is one with an edge of its own, as the loop's."""
    edge = COLOURS[KINDS[kind].edge]
    return f"  linkStyle {','.join(arrow_numbers)} stroke:{edge},stroke-width:2px"


def script_json(data: object) -> str:
    """`data` as JSON a <script> can hold without ending: each <, > and & written as its
    code."""
    text = json.dumps(data, ensure_ascii=False)
    return text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


# The drawing's script, which a page puts before its own: what any drawing of boxes and arrows
# needs. A box is an SVG <g class="n ..."> with its id; an arrow, a <path class="e ..."> with
# data-a and data-b, the ids of the boxes at its two ends, or data-g, the group at its end.
# This is an ordinary Python string, so a backslash in the script is written twice.
DRAWING_SCRIPT = """\
// The drawing's script, shared by every page that draws boxes and arrows: it makes the
// picture zoom, pan and light up a path. It is plain JavaScript that any browser runs, with
// nothing to install or download.

// An object holding each item under the key that keyFor(item) gives, to look items up by key.
function indexBy(items, keyFor) {
  const index = {};
  items.forEach(item => {
    index[keyFor(item)] = item;
  });
  return index;
}

// Text made safe to put inside the page's markup: & < > and " become their HTML codes.
function escapeHtml(text) {
  const codes = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'};
  return text.replace(/[&<>"]/g, character => codes[character]);
}

// Text cut to at most maxLength characters, ending in an ellipsis when it was cut, so it fits
// in a box.
function shortened(text, maxLength) {
  if (text.length <= maxLength) {
    return text;
  }
  // The ellipsis character. Its backslash is written twice only in the Python file.
  return text.slice(0, maxLength - 1) + '\\u2026';
}

// For each drawn box, the ids of the boxes with an arrow into it (its sources) and the ids of
// the boxes it has an arrow into (its targets).
function neighboursOf(visible) {
  const sources = {};
  const targets = {};
  visible.boxes.forEach(box => {
    sources[box.id] = [];
    targets[box.id] = [];
  });
  visible.arrows.forEach(([source, target]) => {
    sources[target].push(source);
    targets[source].push(target);
  });
  return {sources: sources, targets: targets};
}

// Every box reachable from box `id` by following `next` (sources, or targets) again and
// again. Each is added to the set `found`, which is returned.
function collectReachable(id, next, found) {
  (next[id] || []).forEach(other => {
    if (!found.has(other)) {
      found.add(other);
      collectReachable(other, next, found);
    }
  });
  return found;
}

// Make the picture answer the mouse: the wheel zooms, dragging pans, and clicking a box
// lights up its path (everything that feeds it and everything it feeds) and dims the rest.
// `visible` holds the boxes drawn, each with its id and group, and the arrows between them.
function addMouseHandlers(svg, visible) {
  const neighbours = neighboursOf(visible);
  const boxIdsByGroup = {};
  visible.boxes.forEach(box => {
    if (!boxIdsByGroup[box.group]) {
      boxIdsByGroup[box.group] = [];
    }
    boxIdsByGroup[box.group].push(box.id);
  });

  // The part of the picture in sight, as [left, top, width, height]. Zooming and panning
  // change it.
  let viewBox = svg.getAttribute('viewBox').split(' ').map(Number);
  // Where a drag started, kept from the mouse button going down until just after it comes up.
  let drag = null;

  function showViewBox() {
    svg.setAttribute('viewBox', viewBox.join(' '));
  }

  // Zoom in or out, keeping the point under the mouse where it is.
  function zoom(event) {
    event.preventDefault();  // stop the page itself from scrolling
    const bounds = svg.getBoundingClientRect();
    const factor = event.deltaY > 0 ? 1.15 : 1 / 1.15;
    const pointX = viewBox[0] + (event.clientX - bounds.left) / bounds.width * viewBox[2];
    const pointY = viewBox[1] + (event.clientY - bounds.top) / bounds.height * viewBox[3];
    viewBox = [
      pointX - (pointX - viewBox[0]) * factor,
      pointY - (pointY - viewBox[1]) * factor,
      viewBox[2] * factor,
      viewBox[3] * factor,
    ];
    showViewBox();
  }

  function startDrag(event) {
    drag = {x: event.clientX, y: event.clientY, viewBox: viewBox.slice(), moved: false};
  }

  // Pan the picture with the mouse, while the button is down.
  function moveDrag(event) {
    if (!drag) {
      return;
    }
    const bounds = svg.getBoundingClientRect();
    const moveX = (event.clientX - drag.x) / bounds.width * viewBox[2];
    const moveY = (event.clientY - drag.y) / bounds.height * viewBox[3];
    if (Math.abs(moveX) + Math.abs(moveY) > 1) {
      drag.moved = true;
    }
    viewBox = [drag.viewBox[0] - moveX, drag.viewBox[1] - moveY, viewBox[2], viewBox[3]];
    showViewBox();
  }

  // Forget the drag only after the click that the browser sends when the button comes up,
  // so that click can tell it ended a drag.
  function endDrag() {
    setTimeout(() => {
      drag = null;
    });
  }

  // Light up the clicked box's path and dim everything else. A click off every box clears
  // the lighting; the click that ends a drag does nothing.
  function lightUpPath(event) {
    if (drag && drag.moved) {
      return;
    }
    svg.querySelectorAll('.n,.e').forEach(element => element.classList.remove('dim', 'hit'));
    const clicked = event.target.closest('.n');
    if (!clicked) {
      return;
    }
    const onPath = collectReachable(clicked.id, neighbours.sources, new Set([clicked.id]));
    collectReachable(clicked.id, neighbours.targets, onPath);
    svg.querySelectorAll('.n').forEach(box => {
      box.classList.add(onPath.has(box.id) ? 'hit' : 'dim');
    });
    svg.querySelectorAll('.e').forEach(arrow => {
      // A filters arrow ends at a group (data-g), so it is on the path if any box in the
      // group is.
      const ends = arrow.dataset.g ? boxIdsByGroup[arrow.dataset.g] : [arrow.dataset.b];
      const lit = onPath.has(arrow.dataset.a) && ends.some(id => onPath.has(id));
      arrow.classList.add(lit ? 'hit' : 'dim');
    });
  }

  // passive: false lets zoom() stop the page from scrolling.
  svg.addEventListener('wheel', zoom, {passive: false});
  svg.addEventListener('pointerdown', startDrag);
  svg.addEventListener('pointermove', moveDrag);
  svg.addEventListener('pointerup', endDrag);
  svg.addEventListener('click', lightUpPath);
}
"""

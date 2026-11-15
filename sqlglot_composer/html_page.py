"""The one module every HTML page the Toolbox writes is built from (Toolbox 8.7, ticket 04): the
colour tokens, each written once; the base CSS, which names a colour only by its token; the
legend, made from the tokens; the drawing's script, which zooms, pans and lights up a path; and
the side panel (ticket 06), which a click on a box opens, and whose parts are the sections of
the page's Markdown twin too. docs/agents/standards.md's "HTML pages" is the standard each page
keeps.

It isn't brought by `from sqlglot_composer import *`, and isn't for you to call: export_lineage
and project.export_run_lineage build their page with lineage.py, and
project.export_project_lineage with project_lineage.py, each from here. The Workflows overview
and the Example projects page, in the download's docs folder, are built from here too, by tools
on dev (tickets 07 and 13).

A page is `page(title, body, css, script)`: the head, the tokens, the base CSS and each kind's
CSS come from here; `css` and `script` are the page's own pieces after them, its own and those
it takes from here, such as DRAWING_CSS and DRAWING_SCRIPT. A new kind of box is a row of KINDS,
its colours rows of COLOURS; a palette change is an edit to COLOURS alone. What a box opens is
a Part, written to the page by panel and to the Markdown by part_markdown, so each line of the
Markdown is on the page too.
"""

from __future__ import annotations

import html
import json
import re
from typing import NamedTuple

# Every colour a page uses, by its name: the one place a colour is written. The CSS names each
# as var(--name). Two names may hold the same colour, each for its own job.
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
    // Say which box was chosen, or null for none, so the side panel can show or close.
    svg.dispatchEvent(new CustomEvent('boxchosen', {bubbles: true, detail: clicked}));
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


# --- The side panel (ticket 06) ---------------------------------------------------------------
# A click on a box, or Enter on a box reached with Tab, opens a panel beside the drawing,
# showing the Parts the box names; the page's Markdown twin writes each Part as a section, so
# the two say the same. With scripts off, every Part shows under the drawing.

# The kinds of Piece a Part holds.
HEADING = "heading"  # a heading, a level under its Part's
TEXT = "text"  # paragraphs, a line each
ITEMS = "items"  # a list, an item a line
BLOCK = "block"  # text kept as it is written, such as a tree or an error, its one line
HIVE = "sql"  # Hive, kept as it is written, its one line, with a Copy button on the page


class Piece(NamedTuple):
    """One piece of a Part: its kind, one of HEADING, TEXT, ITEMS, BLOCK and HIVE, and its
    lines. In a heading, a paragraph or an item, `name` in backticks is code, and **name**
    bold, as Markdown writes them."""

    kind: str
    lines: list[str]


class Part(NamedTuple):
    """What the panel shows for a box, and the Markdown's section of it: its id on the page;
    the level of its heading, 2 for ##; its heading; and its pieces, each a Piece or a Part
    of its own, which gives its own level."""

    key: str
    level: int
    heading: str
    pieces: list[Piece | Part]


def part_markdown(part: Part) -> list[str]:
    """A Part as Markdown lines, each piece followed by an empty line."""
    lines = [f"{'#' * part.level} {part.heading}", ""]
    for piece in part.pieces:
        if isinstance(piece, Part):
            lines += part_markdown(piece)
        elif piece.kind == HEADING:
            lines += [f"{'#' * (part.level + 1)} {piece.lines[0]}", ""]
        elif piece.kind == TEXT:
            for line in piece.lines:
                lines += [line, ""]
        elif piece.kind == ITEMS:
            lines += [*[f"- {line}" for line in piece.lines], ""]
        else:
            fence = "sql" if piece.kind == HIVE else "text"
            lines += [f"```{fence}", piece.lines[0], "```", ""]
    return lines


def part_html(part: Part) -> str:
    """A Part as HTML, inside a <div class="part"> with its id."""
    shown = [f'<div class="part" id="{html.escape(part.key)}">'
             f"<h{part.level}>{inline_html(part.heading)}</h{part.level}>"]
    for piece in part.pieces:
        if isinstance(piece, Part):
            shown.append(part_html(piece))
        elif piece.kind == HEADING:
            level = part.level + 1
            shown.append(f"<h{level}>{inline_html(piece.lines[0])}</h{level}>")
        elif piece.kind == TEXT:
            shown += [f"<p>{inline_html(line)}</p>" for line in piece.lines]
        elif piece.kind == ITEMS:
            items = "".join(f"<li>{inline_html(line)}</li>" for line in piece.lines)
            shown.append(f"<ul>{items}</ul>")
        elif piece.kind == BLOCK:
            shown.append(f"<pre>{html.escape(piece.lines[0])}</pre>")
        else:
            shown.append('<div class="hive"><button type="button" class="copy">Copy</button>'
                         f"<pre>{html.escape(piece.lines[0])}</pre></div>")
    return "".join(shown) + "</div>"


def inline_html(text: str) -> str:
    """A line of a Part as HTML: escaped, then each `name` in backticks as <code>name</code>,
    its fence as long as Markdown's, and each **name** as <b>name</b>."""
    shown = re.sub(r"(`+) ?(.+?) ?\1", r"<code>\2</code>", html.escape(text))
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", shown)


def panel(parts: list[Part]) -> str:
    """The side panel, after the drawing: a Close button, the place the clicked box's own
    entry is shown, and each Part. With scripts off, every Part shows and the button doesn't."""
    return ('<aside id="panel" aria-label="What the box you clicked holds">'
            '<button type="button" class="close" hidden>Close</button>'
            '<div id="panel-box"></div>\n'
            + "\n".join(part_html(part) for part in parts) + "\n</aside>")


# The panel's CSS. While a box's panel is open, the drawing and the panel sit side by side,
# the panel kept in sight as the page scrolls; its Hive is wrapped, never cut.
PANEL_CSS = """\
body.panel-open main{display:flex;gap:12px;align-items:flex-start}
body.panel-open .wrap{flex:1 1 0;min-width:0}
#panel{border-top:1px solid var(--rule);margin-top:12px;background:var(--page)}
body.panel-open #panel{flex:0 0 40%;max-width:640px;margin-top:0;position:sticky;top:8px;\
max-height:calc(100vh - 16px);overflow:auto;border:1px solid var(--faint-rule);padding:0 12px}
#panel .close{float:right;margin-top:10px}
#panel pre{white-space:pre-wrap;overflow-wrap:anywhere}
.hive{position:relative} .hive .copy{position:absolute;top:4px;right:4px}
#panel-box:not(:empty){border-bottom:1px solid var(--rule);margin-bottom:8px}
.n:focus{outline:none} .n:focus-visible rect{stroke:var(--ink);stroke-width:3}
@media (max-width:800px){body.panel-open main{display:block}\
 body.panel-open #panel{position:static;max-height:none;max-width:none;margin-top:12px}}"""

# The panel's script, after DRAWING_SCRIPT, whose 'boxchosen' it listens for. A box names the
# Parts it opens, by their ids, in its data-parts, and its own entry, a Part copied to the
# top of the panel, in its data-entry.
PANEL_SCRIPT = """\
// The side panel's script, shared by every page whose boxes open a panel: a click on a box,
// or Enter on a box reached with Tab, shows what the box holds beside the drawing; a click
// off every box, Escape or the Close button closes it. It is plain JavaScript that any
// browser runs, with nothing to install or download.

// Copy the Hive beside a Copy button. Where the browser won't let a page copy, the Hive is
// selected instead, for Ctrl+C.
function copyHive(button) {
  const hive = button.parentElement.querySelector('pre');
  function say(words) {
    button.textContent = words;
    setTimeout(() => {
      button.textContent = 'Copy';
    }, 2000);
  }
  function selectIt() {
    const range = document.createRange();
    range.selectNodeContents(hive);
    getSelection().removeAllRanges();
    getSelection().addRange(range);
    say(document.execCommand('copy') ? 'Copied' : 'Selected: press Ctrl+C');
  }
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(hive.textContent).then(() => say('Copied'), selectIt);
  } else {
    selectIt();
  }
}

// Make the boxes in `drawing` open the panel. The drawing's script says which box was chosen;
// Enter on a box clicks it, as the mouse would, and Escape clicks off every box.
function addPanelHandlers(drawing) {
  const panel = document.getElementById('panel');
  const parts = panel.querySelectorAll(':scope > .part');
  const entryPlace = document.getElementById('panel-box');
  const closeButton = panel.querySelector('.close');
  let openedFrom = null;  // the box whose panel is open

  function closePanel() {
    panel.hidden = true;
    document.body.classList.remove('panel-open');
    entryPlace.innerHTML = '';
  }

  function openPanel(box) {
    const shown = new Set((box.dataset.parts || '').split(' '));
    parts.forEach(part => {
      part.hidden = !shown.has(part.id);
    });
    entryPlace.innerHTML = '';
    const entry = box.dataset.entry ? document.getElementById(box.dataset.entry) : null;
    if (entry) {
      const copy = entry.cloneNode(true);
      copy.removeAttribute('id');
      entryPlace.appendChild(copy);
    }
    panel.hidden = false;
    document.body.classList.add('panel-open');
    panel.scrollTop = 0;
    openedFrom = box;
  }

  // Close the panel and clear the lit path, as a click on the drawing off every box does.
  function closeAll() {
    const svg = drawing.querySelector('svg');
    if (svg) {
      svg.dispatchEvent(new MouseEvent('click'));
    }
    closePanel();
  }

  // Close it all, then give the keyboard back to the box.
  function closeAndReturn() {
    closeAll();
    if (openedFrom && openedFrom.isConnected) {
      openedFrom.focus();
    }
  }

  drawing.addEventListener('boxchosen', event => {
    if (event.detail) {
      openPanel(event.detail);
    } else {
      closePanel();
    }
  });
  drawing.addEventListener('keydown', event => {
    const box = event.target.closest('.n');
    if (box && (event.key === 'Enter' || event.key === ' ')) {
      event.preventDefault();  // a space would scroll the page
      box.dispatchEvent(new MouseEvent('click', {bubbles: true}));
    }
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !panel.hidden) {
      closeAndReturn();
    }
  });
  // A click on the page off the drawing, the panel and the controls closes it too.
  document.addEventListener('click', event => {
    const kept = event.target.closest(
      '#panel, #controls, .wrap, a, button, select, input, summary');
    if (!kept && !panel.hidden) {
      closeAll();
    }
  });
  closeButton.addEventListener('click', closeAndReturn);
  panel.addEventListener('click', event => {
    const button = event.target.closest('.copy');
    if (button) {
      copyHive(button);
    }
  });
  closeButton.hidden = false;
  closePanel();
}
"""

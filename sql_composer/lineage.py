# SQL Composer 2.0, exported 2026-09-25 20:11 - generated from dev, do not edit
"""Lineage: draw where each column comes from, as an HTML page and as Markdown.

export_lineage(s) writes two files. The HTML page draws every step as its own group of boxes,
from the table columns through each Derived table to the Statement's outputs, with controls
to expand, collapse or hide each table. The Markdown twin needs no script: a Mermaid chart,
then a report on each calculated column, and the Hive as submitted. Pass several Statements
and the drawing continues through each Saved table one writes and another reads.
"""

from __future__ import annotations

import datetime
import html
import inspect
import json
import os
import re
from pathlib import Path

from sqlglot import exp

from .clauses import Statement, derived_tables
from .refusals import GuardRefused, four_part_message
from .running import by_day, to_hive
from .tables import hive_text, readable

TOOLBOX_VERSION = "2.0"


# --- What a box shows --------------------------------------------------------------------------
# Each function gives one line of a box, or "" to leave the line out. Every view reads this
# list, so a line added here shows in the HTML, the Mermaid chart and the report alike.


def name_line(box: dict) -> str:
    return box["name"]


def formula_line(box: dict) -> str:
    """A table column's type; for anything else, how it was written."""
    if box["kind"] == "table":
        return box["type"] or ""
    return box["formula"]


BOX_LINES = [name_line, formula_line]


def box_lines(box: dict) -> list[str]:
    return [line for line in (show(box) for show in BOX_LINES) if line]


# --- The graph -------------------------------------------------------------------------------


class Graph:
    """Boxes and arrows. A box is a table column, a Derived table column, an output or a
    condition. An arrow is "value" (the value flows along it), "rows" (it decides which rows
    count) or "day" (a write's date bound decides the day a Saved table is written)."""

    def __init__(self):
        self.boxes = {}
        self.arrows = []

    def add(self, key: str, **facts) -> str:
        self.boxes.setdefault(key, facts)
        return key

    def arrow(self, source: str | None, target: str, kind: str) -> None:
        if source is not None and (source, target, kind) not in self.arrows:
            self.arrows.append((source, target, kind))

    def parents(self, key: str, kind: str | None = None) -> list[str]:
        return [a for a, b, k in self.arrows if b == key and kind in (None, k)]

    def upstream(self, key: str, kind: str | None = None) -> list[str]:
        seen, todo = [], [key]
        while todo:
            for parent in self.parents(todo.pop(), kind):
                if parent not in seen:
                    seen.append(parent)
                    todo.append(parent)
        return seen


def _table_box(graph: Graph, table, column: str) -> str:
    return graph.add(f"table:{table._name}.{column}", kind="table", group=table._name,
                     name=f"{table._name}.{column}", full=f"{table._name}.{column}",
                     type=table._columns.get(column), formula="", calculated=False)


def _resolver(graph: Graph, step: Statement, index: int):
    """A function from a column in `step` to the key of the box it reads."""
    tables = {read.table._alias: read.table for read in step._reads}

    def resolve(column: exp.Column) -> str | None:
        table = tables.get(column.table)
        if table is None:
            return None  # an output name, as in ORDER BY "runs"
        if table._statement is not None:
            return f"derived:{index}:{table._name}.{column.name}"
        return _table_box(graph, table, column.name)

    return resolve


def _conditions_of(step: Statement) -> list[tuple[str, object, exp.Expression, str]]:
    """Each condition that decides which rows `step` keeps: (clause, condition, tree, then).

    `then` is text written after the tree: a LIMIT's count, after its ORDER BY.
    """
    found = [("WHERE", c, c._tree, "") for c in step._where]
    found += [(f"{read._name.replace('_', ' ')} ON", read.on, read.on._tree, "")
              for read in step._reads if read.on is not None]
    found += [("HAVING", c, c._tree, "") for c in step._having]
    if step._limit is not None:
        order = exp.Order(expressions=[o.copy() for o in step._order_by])
        found.append(("LIMIT", None, order, f"LIMIT {step._limit}"))
    return found


def _condition_text(tree: exp.Expression, then: str) -> tuple[str, str]:
    """A condition's Hive and how it was written, with `then` after each."""
    if isinstance(tree, exp.Order) and not tree.expressions:
        return then, then  # a LIMIT with no ORDER BY
    return tuple(" ".join(x for x in (text.strip(), then) if x)
                 for text in (hive_text(tree), readable(tree)))


def _add_step(graph: Graph, step: Statement, place: dict) -> None:
    """The boxes one step makes (a Derived table, or the Statement): outputs, then conditions."""
    resolve = _resolver(graph, step, place["index"])
    made = []
    for column, name in step._outputs:
        tree = column._tree
        sources = [resolve(used) for used in tree.find_all(exp.Column)]
        if place["kind"] == "output":
            key, shown = f"output:{place['index']}:{name}", name
        else:
            key, shown = f"derived:{place['index']}:{place['table']}.{name}", f"{place['group']}.{name}"
        graph.add(key, kind=place["kind"], group=place["group"], name=shown,
                  full=f"{place['group']}.{name}", type=column._type, sql=hive_text(tree),
                  formula=readable(tree), calculated=not isinstance(tree, exp.Column),
                  group_by=[readable(c._tree) for c in step._group_by] if column._aggregate
                  else [], statement=place["index"])
        for source in sources:
            graph.arrow(source, key, "value")
        made.append(key)
    for number, (clause, condition, tree, then) in enumerate(_conditions_of(step)):
        sql, formula = _condition_text(tree, then)
        key = graph.add(f"condition:{place['index']}:{place['group']}:{number}",
                        kind="condition", group=place["group"],
                        name=f"{clause} in {place['group']}",
                        full=f"{clause} in {place['group']}", type=None, sql=sql,
                        formula=formula, calculated=False, statement=place["index"])
        place["conditions"][(id(step), id(condition))] = key
        for used in tree.find_all(exp.Column):
            graph.arrow(resolve(used), key, "rows")
        for target in made:
            graph.arrow(key, target, "rows")


def _date_bounds(s: Statement) -> tuple[Statement, list]:
    """The step that reads a write's real table through FROM, and its date-bound conditions."""
    step = s
    while step._reads[0].table._statement is not None:
        step = step._reads[0].table._statement
    table = step._reads[0].table
    inner = [read.on for read in step._reads if read._name == "JOIN"]
    key = (table._alias, table._date_partition)
    return step, [c for c in step._where + inner if key in c._spans]


def _add_write(graph: Graph, s: Statement, index: int, conditions: dict) -> list[str]:
    """Arrows from a write's outputs into its Saved table, and the "day written" arrow."""
    table, written = s._write, []
    for _, name in s._outputs:
        target = _table_box(graph, table, name)
        graph.arrow(f"output:{index}:{name}", target, "value")
        written.append(target)
    day = _table_box(graph, table, table._date_partition)
    written.append(day)
    step, bounds = _date_bounds(s)
    for condition in bounds:
        graph.arrow(conditions.get((id(step), id(condition))), day, "day")
    return written


def build_graph(ordered: list[tuple[Statement, str]]) -> Graph:
    """Every box and arrow of the Statements, writers first, keeping what reaches an output."""
    graph, ends = Graph(), []
    groups = _derived_group_names(ordered)
    for index, (s, name) in enumerate(ordered):
        conditions = {}
        for table in derived_tables(s):
            _add_step(graph, table._statement, {
                "index": index, "kind": "derived", "table": table._name,
                "group": groups[(index, table._name)], "conditions": conditions})
        _add_step(graph, s, {"index": index, "kind": "output", "table": None, "group": name,
                             "conditions": conditions})
        ends += [f"output:{index}:{output}" for _, output in s._outputs]
        if s._write is not None:
            ends += _add_write(graph, s, index, conditions)
    keep = set(ends)
    for key in ends:
        keep.update(graph.upstream(key))
    graph.boxes = {k: v for k, v in graph.boxes.items() if k in keep}
    graph.arrows = [a for a in graph.arrows if a[0] in keep and a[1] in keep]
    return graph


def _derived_group_names(ordered) -> dict:
    """Each Derived table's group name: its own, plus "in <Statement>" when that name is
    taken by another passed Statement's Derived table, by a Statement or by a table."""
    names, taken = {}, {name for _, name in ordered}
    for index, (s, _) in enumerate(ordered):
        taken |= _tables_read(s)
        for table in derived_tables(s):
            names.setdefault(table._name, []).append(index)
    return {(index, name): name if len(indexes) == 1 and name not in taken
            else f"{name} in {ordered[index][1]}"
            for name, indexes in names.items() for index in indexes}


# --- Putting the Statements in order ----------------------------------------------------------


def _tables_read(s: Statement) -> set[str]:
    steps = [s] + [table._statement for table in derived_tables(s)]
    return {read.table._name for step in steps for read in step._reads
            if read.table._statement is None}


def in_order(named: list[tuple[Statement, str]]) -> list[tuple[Statement, str]]:
    """The Statements with every writer before the Statements that read what it writes."""
    reads = [_tables_read(s) for s, _ in named]
    needs = [{j for j, (w, _) in enumerate(named) if w._write is not None
              and w._write._name in reads[i]} for i in range(len(named))]
    placed = []
    while len(placed) < len(named):
        ready = [i for i in range(len(named)) if i not in placed and needs[i] <= set(placed)
                 and i not in needs[i]]
        if not ready:
            _refuse_loop(named, reads, _in_the_loop(needs, placed))
        placed.append(ready[0])
    return [named[i] for i in placed]


def _in_the_loop(needs: list[set], placed: list[int]) -> list[int]:
    """The Statements left unplaced that are part of a loop, not just waiting on one."""
    stuck = [i for i in range(len(needs)) if i not in placed]
    while True:
        needed = {j for i in stuck for j in needs[i]}
        kept = [i for i in stuck if i in needed]
        if kept == stuck:
            return stuck
        stuck = kept


def _refuse_loop(named, reads, stuck: list[int]) -> None:
    links = []
    for i in stuck:
        s, name = named[i]
        if s._write is None:
            continue
        readers = [named[j][1] for j in stuck if s._write._name in reads[j]]
        verb = "reads" if len(readers) == 1 else "read"
        links.append(f"{name} writes {s._write._name}, which {' and '.join(readers)} {verb}")
    raise ValueError(
        four_part_message(
            what="export_lineage can't draw these Statements, because they go round in a "
            "loop: " + "; ".join(links) + ".",
            why="Each Statement's lineage would lead back into itself, so the drawing would "
            "have no start.",
            fix="Pass only the Statements on one path from the tables to the result, or "
            "export each one on its own.",
            opt_out=None,
        )
    )


# --- The report ------------------------------------------------------------------------------


def _code(text: str) -> str:
    """Markdown inline code, with a fence that survives backticks inside it."""
    fence = "`" * (max((len(run) for run in re.findall(r"`+", text)), default=0) + 1)
    pad = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{pad}{text}{pad}{fence}"


def _how(box: dict) -> str:
    """How the report names a calculation: as written, then the Hive it became."""
    if box["formula"] != box["sql"]:
        return f"{_code(box['formula'])}, which is {_code(box['sql'])}"
    return _code(box["sql"])


def tree_lines(graph: Graph, key: str, prefix: str = "", last: bool = True,
               top: bool = True) -> list[str]:
    """A calculated column's text tree, back to the table columns it reads."""
    box = graph.boxes[key]
    text = box["full"]
    if box.get("calculated"):
        text += f" = {box['formula']}"
    elif box["kind"] == "table" and box["type"]:
        text += f"  ({box['type']})"
    lines = [text if top else prefix + ("└─ " if last else "├─ ") + text]
    parents = graph.parents(key, "value")
    inner = "" if top else prefix + ("   " if last else "│  ")
    for number, parent in enumerate(parents):
        lines += tree_lines(graph, parent, inner, number == len(parents) - 1, False)
    if top and not parents:
        lines.append("└─ (no columns: it counts rows)")
    return lines


def _rows_that_count(graph: Graph, key: str) -> list[tuple[dict, list[str]]]:
    """Each condition upstream of a box, with the table columns it reads.

    A write's date bound decides which day of its Saved table is written, not which of
    those days a later Statement reads, so it counts only in the write's own section.
    """
    found, upstream = [], graph.upstream(key)
    day_bounds = {a for a, _, kind in graph.arrows if kind == "day"}
    for condition in [k for k in graph.boxes if k in upstream]:
        box = graph.boxes[condition]
        if box["kind"] != "condition" or (
                condition in day_bounds and box["statement"] != graph.boxes[key]["statement"]):
            continue
        found.append((box, _tables_read_by(graph, condition)))
    return found


def _tables_read_by(graph: Graph, condition: str) -> list[str]:
    """The table columns a condition reads, through Derived tables but not past a table."""
    found, todo, seen = [], list(graph.parents(condition)), set()
    while todo:
        key = todo.pop()
        if key in seen:
            continue
        seen.add(key)
        if graph.boxes[key]["kind"] == "table":
            found.append(graph.boxes[key]["name"])
        else:
            todo += graph.parents(key, "value")
    return sorted(found)


def _copied_from(graph: Graph, key: str) -> list[str]:
    chain, at = [], key
    while graph.parents(at, "value"):
        at = graph.parents(at, "value")[0]
        box = graph.boxes[at]
        chain.append(box["full"] + (" (calculated)" if box.get("calculated") else ""))
    return chain


def report(graph: Graph, ordered) -> list[dict]:
    """One section per Statement, writers first: its calculated and copied columns, its Hive."""
    sections = []
    for index, (s, name) in enumerate(ordered):
        mine = [k for k, box in graph.boxes.items() if box.get("statement") == index
                and box["kind"] in ("derived", "output")]
        calculated = [
            {"box": graph.boxes[k], "tree": "\n".join(tree_lines(graph, k)),
             "conditions": _rows_that_count(graph, k)}
            for k in mine if graph.boxes[k]["calculated"]
        ]
        copied = [(graph.boxes[k]["name"], _copied_from(graph, k)) for k in mine
                  if graph.boxes[k]["kind"] == "output" and not graph.boxes[k]["calculated"]]
        sql, note = _submitted(s, name)
        sections.append({"name": name, "about": _about(s, index, ordered),
                         "calculated": calculated, "copied": copied, "sql": sql, "note": note})
    return sections


def _about(s: Statement, index: int, ordered) -> str:
    """One sentence on how a Statement joins the others through Saved tables."""
    parts = []
    for table in sorted(_tables_read(s)):
        writers = [name for other, name in ordered[:index]
                   if other._write is not None and other._write._name == table]
        if writers:
            parts.append(f"It reads the Saved table {table}, written by "
                         f"{' and '.join(writers)} above.")
    if s._write is not None:
        parts.append(f"It writes the Saved table {s._write._name}, one day at a time.")
    return " ".join(parts)


def _submitted(s: Statement, name: str) -> tuple[str, str]:
    """The Hive as submitted; for a write over several days, the first day's."""
    try:
        return to_hive(s), ""
    except GuardRefused:
        if s._write is None:
            raise
    days = by_day(s)
    return to_hive(days[0]), (
        f"This write covers {len(days)} days, and a write replaces one day at a time: send "
        f"it with `for day in by_day({name}): run(day, send=...)`. This is the first day's "
        "Hive.")


# --- The Markdown twin -----------------------------------------------------------------------


def _mermaid_text(text: str) -> str:
    """Text for inside a Mermaid label, with the characters Mermaid reads spelled out."""
    for character, code in (("#", "#35;"), ('"', "#quot;"), ("<", "#lt;"), (">", "#gt;"),
                            ("`", "#96;")):
        text = text.replace(character, code)
    return text


def _short(text: str, n: int) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


def group_of(box: dict) -> str:
    """The group a box is drawn in: a condition sits in the filters of the group it filters."""
    return f"filters on {box['group']}" if box["kind"] == "condition" else box["group"]


def mermaid_chart(graph: Graph) -> list[str]:
    ids = {key: f"n{number}" for number, key in enumerate(graph.boxes)}
    groups = {}
    for key, box in graph.boxes.items():
        groups.setdefault(group_of(box), []).append(key)
    group_ids = {group: f"g{number}" for number, group in enumerate(groups)}
    lines = ["```mermaid", "flowchart LR"]
    for group, keys in groups.items():
        lines.append(f'  subgraph {group_ids[group]}["{_mermaid_text(group)}"]')
        for key in keys:
            shown = box_lines(graph.boxes[key])
            text = "<br/>".join([_mermaid_text(shown[0])]
                                + [f"<small>{_mermaid_text(_short(x, 44))}</small>" for x in shown[1:]])
            ends = ('{{"', '"}}') if graph.boxes[key]["kind"] == "condition" else ('["', '"]')
            lines.append(f"    {ids[key]}{ends[0]}{text}{ends[1]}")
        lines.append("  end")
    filters = []
    for source, target, kind in graph.arrows:
        if kind == "day":
            lines.append(f"  {ids[source]} -.->|day written| {ids[target]}")
        elif graph.boxes[source]["kind"] == "condition":
            line = f"  {ids[source]} -.->|filters| {group_ids[graph.boxes[target]['group']]}"
            if line not in filters:
                filters.append(line)
        else:
            lines.append(f"  {ids[source]} {'-->' if kind == 'value' else '-.->'} {ids[target]}")
    return lines + filters + ["```"]


def _section_markdown(section: dict) -> list[str]:
    lines = [f"## {section['name']}", ""]
    if section["about"]:
        lines += [section["about"], ""]
    lines += ["### Calculated columns", "",
              "Every column that is calculated rather than copied, in the order it is "
              "calculated.", ""]
    for entry in section["calculated"]:
        box = entry["box"]
        lines += [f"#### {_code(box['name'])}", "",
                  f"Calculated in **{box['group']}** as {_how(box)}.", "",
                  "```text", entry["tree"], "```", ""]
        if entry["conditions"]:
            lines.append("Rows that count:")
            lines += [f"- {c['name']}: {_how(c)}" + (f" (reads {', '.join(reads)})" if reads
                                                    else "")
                      for c, reads in entry["conditions"]]
            lines.append("")
        if box["group_by"]:
            lines += ["One value for each different "
                      + " and ".join(_code(g) for g in box["group_by"]) + ".", ""]
    if not section["calculated"]:
        lines += ["None: every column is copied.", ""]
    if section["copied"]:
        lines += ["### Copied columns", "", "| Output | Comes from |", "| --- | --- |"]
        lines += [f"| {_code(name)} | {' ← '.join(chain)} |" for name, chain in section["copied"]]
        lines.append("")
    lines += ["### Hive as submitted", ""]
    if section["note"]:
        lines += [section["note"], ""]
    return lines + ["```sql", section["sql"], "```", ""]


def to_markdown(graph: Graph, sections: list[dict], title: str, footer: str) -> str:
    lines = [f"# Lineage: {title}", "",
             "Made by `export_lineage`. The chart is written in Mermaid, which JupyterLab "
             "draws. Arrows run from where a value comes from to where it goes. A solid "
             "arrow carries a value. A dotted arrow carries a column into a condition, or "
             "runs from a condition to the step whose rows it decides (labelled \"filters\")."
             " A dotted arrow labelled \"day written\" runs from a write's date bound to the "
             "day of the Saved table it writes.", "", "## Graph", ""]
    lines += mermaid_chart(graph) + [""]
    for section in sections:
        lines += _section_markdown(section)
    return "\n".join(lines + ["---", "", footer, ""])


# --- The HTML page ---------------------------------------------------------------------------


def _inline_code(text: str) -> str:
    return f"<code>{html.escape(text)}</code>"


def _how_html(box: dict) -> str:
    if box["formula"] != box["sql"]:
        return f"{_inline_code(box['formula'])}, which is {_inline_code(box['sql'])}"
    return _inline_code(box["sql"])


def _entry_html(entry: dict) -> str:
    box, e = entry["box"], html.escape
    parts = [f'<details open><summary>{_inline_code(box["name"])} '
             f'<span class="muted">in {e(box["group"])}</span></summary>'
             f"<p>Calculated as {_how_html(box)}.</p><pre>{e(entry['tree'])}</pre>"]
    if entry["conditions"]:
        items = "".join(
            f"<li>{e(c['name'])}: {_how_html(c)}"
            + (f' <span class="muted">reads {e(", ".join(reads))}</span>' if reads else "")
            + "</li>"
            for c, reads in entry["conditions"])
        parts.append(f"<p>Rows that count:</p><ul>{items}</ul>")
    if box["group_by"]:
        parts.append("<p>One value for each different "
                     + " and ".join(_inline_code(g) for g in box["group_by"]) + ".</p>")
    return "".join(parts) + "</details>"


def report_html(sections: list[dict]) -> str:
    e, parts = html.escape, []
    for section in sections:
        parts.append(f"<h2>{e(section['name'])}</h2>")
        if section["about"]:
            parts.append(f"<p>{e(section['about'])}</p>")
        parts.append("<h3>Calculated columns</h3>")
        parts += [_entry_html(entry) for entry in section["calculated"]]
        if not section["calculated"]:
            parts.append("<p>None: every column is copied.</p>")
        if section["copied"]:
            rows = "".join(f"<tr><td>{_inline_code(name)}</td><td>{e(' ← '.join(chain))}</td></tr>"
                           for name, chain in section["copied"])
            parts.append("<h3>Copied columns</h3><table><tr><th>Output</th><th>Comes from</th>"
                         f"</tr>{rows}</table>")
        parts.append("<h3>Hive as submitted</h3>")
        if section["note"]:
            parts.append(f"<p>{e(section['note'])}</p>")
        parts.append(f"<pre>{e(section['sql'])}</pre>")
    return "\n".join(parts)


def graph_data(graph: Graph) -> dict:
    """What the page's script draws from: the boxes with their lines, the arrows, the groups."""
    ids = {key: f"n{number}" for number, key in enumerate(graph.boxes)}
    boxes = [{"id": ids[key], "kind": box["kind"], "group": box["group"],
              "lines": box_lines(box),
              "title": "\n".join(x for x in (box["full"], box.get("sql") or box["type"]) if x)}
             for key, box in graph.boxes.items()]
    groups = {}
    for box in graph.boxes.values():
        if box["kind"] != "condition":
            groups.setdefault(box["group"], box["kind"])
    return {"boxes": boxes,
            "arrows": [[ids[a], ids[b], kind] for a, b, kind in graph.arrows],
            "groups": [{"name": name, "kind": kind} for name, kind in groups.items()]}


def _script_safe(data: dict) -> str:
    """JSON that can sit inside a <script> without ending it."""
    text = json.dumps(data, ensure_ascii=False)
    return text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def to_html(graph: Graph, sections: list[dict], title: str, markdown_name: str,
            footer: str) -> str:
    filled = {"TITLE": html.escape(title), "MD": html.escape(markdown_name),
              "FOOTER": html.escape(footer), "REPORT": report_html(sections),
              "DATA": _script_safe(graph_data(graph))}
    # One pass, so text that happens to look like a marker is never filled in itself.
    return re.sub(r"__(TITLE|MD|FOOTER|REPORT|DATA)__", lambda found: filled[found[1]], PAGE)


# --- Naming and placing the files ------------------------------------------------------------


def scripts_commit(folder: Path) -> str:
    """The commit checked out in the git repository holding `folder`: your scripts' commit.

    It is read straight from the .git folder, so no git program is needed. Uncommitted edits
    don't show in it. It is "nogit" when the folder isn't in a repository.
    """
    try:
        for place in [folder, *folder.parents]:
            dot = place / ".git"
            if dot.is_dir() or dot.is_file():
                return _checked_out(place, dot)
    except (OSError, IndexError):
        return "nogit"
    return "nogit"


def _checked_out(place: Path, dot: Path) -> str:
    gitdir = dot
    if dot.is_file():  # a worktree or submodule: .git names the real folder
        gitdir = (place / dot.read_text(encoding="utf-8").split(":", 1)[1].strip()).resolve()
    head = (gitdir / "HEAD").read_text(encoding="utf-8").strip()
    if not head.startswith("ref:"):
        return head[:7]  # a detached HEAD is the commit itself
    ref = head[4:].strip()
    common = gitdir
    if (gitdir / "commondir").exists():
        common = (gitdir / (gitdir / "commondir").read_text(encoding="utf-8").strip()).resolve()
    for base in (gitdir, common):
        if (base / ref).is_file():
            return (base / ref).read_text(encoding="utf-8").strip()[:7]
    packed = common / "packed-refs"
    if packed.exists():
        for line in packed.read_text(encoding="utf-8").splitlines():
            if line.endswith(" " + ref):
                return line[:7]
    return "nocommits"


def calling_file(frame) -> Path | None:
    """The script or notebook that called export_lineage, if it can be told."""
    filename = frame.f_code.co_filename
    if filename.startswith("<") or "ipykernel" in filename:
        notebook = os.environ.get("JPY_SESSION_NAME")
        return Path(notebook) if notebook else None
    return Path(filename)


def statement_names(statements, frame) -> list[str]:
    """The caller's variable name for each Statement, found by identity."""
    names = []
    for position, s in enumerate(statements, start=1):
        found = next((name for scope in (frame.f_locals, frame.f_globals)
                      for name, held in scope.items()
                      if held is s and not name.startswith("_")), None)
        names.append(found or ("statement" if len(statements) == 1
                               else f"statement_{position}"))
    return names


def _plain(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", text)


def default_path(caller: Path | None, commit: str, names: list[str],
                 when: datetime.datetime) -> Path:
    """lineage/{time}_{commit}_lineage_{file}_{names}.html, beside the calling file."""
    stem = caller.stem if caller is not None else "notebook"
    name = (f"{when:%Y%m%d-%H%M%S}_{commit}_lineage_{_plain(stem)}_"
            f"{'__'.join(_plain(n) for n in names)}.html")
    return caller_folder(caller) / "lineage" / name


def caller_folder(caller: Path | None) -> Path:
    """The calling file's folder. A notebook's kernel starts in the notebook's own folder."""
    return caller.parent if caller is not None and caller.is_absolute() else Path.cwd()


def _check_statements(statements) -> list:
    if not statements:
        raise TypeError(four_part_message(
            what="export_lineage() was given no Statement.",
            why="It draws where each column of a Statement comes from.",
            fix="Pass one or more Statements, such as export_lineage(weekly).",
            opt_out=None))
    found = []
    for s in statements:
        if not isinstance(s, Statement) or s._ddl is not None:
            raise TypeError(four_part_message(
                what=f"export_lineage was given {s!r}, which isn't a Statement that reads a "
                "table.",
                why="It draws the lineage of Statements made by statement(...).",
                fix="Pass the Statement itself; for a derived(...) table, pass the Statement "
                "that reads it.",
                opt_out=None))
        if not any(s is seen for seen in found):
            found.append(s)
    return found


def _html_path(to) -> Path:
    path = Path(to)
    if path.suffix.lower() != ".html":
        raise ValueError(four_part_message(
            what=f"export_lineage(..., to={str(to)!r}): to= must name an .html file.",
            why="It names the HTML page; the Markdown twin goes beside it, ending in .md.",
            fix='Write it like to="lineage/weekly.html", or leave to= out for a generated name.',
            opt_out=None))
    return path


def export_lineage(*statements, to=None):
    """Write where each column comes from, as an HTML page and a Markdown twin.

    The HTML draws every step: the table columns, each Derived table and the outputs, with
    the conditions (WHERE, JOIN's ON=, HAVING, LIMIT) as dashed boxes. Click a box to light
    up its whole path; controls expand, collapse or hide each table, and switch to a grouped
    flowchart. The Markdown file needs no script: a Mermaid chart, a report on each
    calculated column, and the Hive. Pass several Statements and the drawing follows each
    Saved table from the Statement that writes it to the ones that read it.

    The files go in a lineage/ folder beside your script or notebook, named by the time,
    your scripts' git commit, the file and the Statement's variable, such as
    lineage/20260925-143000_1a2b3c4_lineage_weekly_report_runs_per_team.html. to= names the
    HTML file instead. It returns the two paths, HTML first.

    >>> runs_per_team = statement(
    ...     SELECT(jobs.team, AS(count_rows(), "runs")),
    ...     FROM(job_runs),
    ...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    ...     WHERE(last_n_days(job_runs.dt, 2)),
    ...     GROUP_BY(jobs.team),
    ... )
    >>> html_file, markdown_file = export_lineage(runs_per_team)
    >>> html_file.parent.name, html_file.name
    ('lineage', '..._lineage_notebook_runs_per_team.html')
    >>> markdown_file.name
    '..._lineage_notebook_runs_per_team.md'
    """
    statements = _check_statements(statements)
    frame = inspect.currentframe().f_back
    when = datetime.datetime.now()
    names = statement_names(statements, frame)
    caller = calling_file(frame)
    commit = scripts_commit(caller_folder(caller))
    html_path = _html_path(to) if to is not None else default_path(caller, commit, names, when)
    markdown_path = html_path.with_suffix(".md")
    ordered = in_order(list(zip(statements, names)))
    graph = build_graph(ordered)
    footer = _footer(when, commit)
    title = ", ".join(name for _, name in ordered)
    sections = report(graph, ordered)
    markdown = to_markdown(graph, sections, title, footer)
    page = to_html(graph, sections, title, markdown_path.name, footer)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(page, encoding="utf-8")
    return html_path, markdown_path


def _footer(when: datetime.datetime, commit: str) -> str:
    from . import VERSION

    return (f"Made by export_lineage on {when:%Y-%m-%d %H:%M}, from your scripts at commit "
            f"{commit}, with {VERSION}.")


PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Lineage: __TITLE__</title><style>
body{margin:0;font:14px system-ui,sans-serif;color:#222;background:#fff}
header{padding:12px 16px;border-bottom:1px solid #ddd} h1{font-size:18px;margin:0 0 6px}
.key span{display:inline-block;margin-right:14px}
.sw{display:inline-block;width:12px;height:12px;border:1px solid #888;vertical-align:-1px;margin-right:4px}
#controls{display:none;padding:8px 16px;border-bottom:1px solid #eee;gap:18px;flex-wrap:wrap;align-items:center}
#controls label{white-space:nowrap} #controls details{position:relative}
#groups{position:absolute;z-index:2;background:#fff;border:1px solid #ccc;padding:8px 10px;box-shadow:0 2px 8px #0002;min-width:260px}
#groups div{display:flex;justify-content:space-between;gap:10px;margin:3px 0}
main{padding:8px 16px 40px} .wrap{overflow-x:auto;border:1px solid #eee}
svg{width:100%;height:auto;cursor:grab;display:block}
.n rect{fill:#fff;stroke:#888} .table rect{fill:#eef4ff} .derived rect{fill:#fff8e6} .output rect{fill:#effaf0}
.condition rect{fill:#f4f4f4;stroke-dasharray:4 3} .collapsed rect{stroke-width:2}
.grp rect{fill:#fafafa;stroke:#c8c8c8} .grp.table rect{fill:#f5f8ff} .grp.derived rect{fill:#fffcf3} .grp.output rect{fill:#f6fcf6}
.grp.condition rect{fill:#fbfbfb;stroke-dasharray:5 4} .grp text{font:600 12px system-ui,sans-serif;fill:#555}
.e.filters{stroke:#b5b5b5} .flabel{font-size:10px;fill:#999}
.n text{font-size:11px;fill:#666;font-family:ui-monospace,monospace} .n text.l{font:600 13px system-ui,sans-serif;fill:#222}
.e{fill:none;stroke:#aaa;stroke-width:1.3} .e.rows,.e.day{stroke-dasharray:3 3;stroke:#c9c9c9} .e.day{stroke:#999}
.dim{opacity:.15} .hit rect{stroke:#d33;stroke-width:2} .e.hit{stroke:#d33;stroke-width:2;opacity:1}
.n{cursor:pointer} pre{background:#f7f7f7;padding:8px;overflow:auto} .muted{color:#777}
summary{cursor:pointer} table{border-collapse:collapse} td,th{border:1px solid #ddd;padding:4px 8px;text-align:left}
#report details{margin:0 0 12px} #report summary{font-size:15px} footer{padding:8px 16px 24px;color:#777;font-size:12px}
</style></head><body>
<header><h1>Lineage: __TITLE__</h1><div class="key">
<span><i class="sw" style="background:#eef4ff"></i>table column</span>
<span><i class="sw" style="background:#fff8e6"></i>Derived table column</span>
<span><i class="sw" style="background:#effaf0"></i>output column</span>
<span><i class="sw" style="background:#f4f4f4;border-style:dashed"></i>condition</span>
<span>solid arrow: carries a value · dotted: a column read by a condition, or a condition deciding which rows count ("filters") · "day written": the date bound that decides which day of a Saved table is written · click a box to light up its path · scroll zooms, drag pans</span>
</div></header>
<div id="controls">
  <label>View <select id="view"><option value="graph">Graph</option><option value="flow">Grouped flowchart</option></select></label>
  <label>Tables <select data-kind="table"></select></label>
  <label>Derived tables <select data-kind="derived"></select></label>
  <label>Outputs <select data-kind="output"></select></label>
  <label><input type="checkbox" id="conditions" checked> Conditions</label>
  <label><input type="checkbox" id="showReport" checked> Report</label>
  <details><summary>Each group</summary><div id="groups"></div></details>
</div>
<main>
<noscript><p><b>Scripts are off, so the graph can't be drawn.</b> The report below and
<code>__MD__</code>, written beside this file, show the same lineage.</p></noscript>
<div class="wrap" id="graph"></div>
<section id="report">__REPORT__</section>
</main>
<footer>__FOOTER__</footer>
<script>
const G=__DATA__, W=250, GX=80, GY=14, LINE=15;
const MODES={table:['expanded','collapsed','hidden'],derived:['expanded','collapsed','hidden'],output:['expanded','collapsed']};
const state={view:'graph',group:{},conditions:true,report:true};
G.groups.forEach(g=>state.group[g.name]='expanded');
const q=new URLSearchParams(location.search);
G.groups.forEach(g=>{const v=q.get('g:'+g.name); if(MODES[g.kind].includes(v))state.group[g.name]=v;});
if(q.get('view')==='flow')state.view='flow';
if(q.get('conditions')==='off')state.conditions=false;
if(q.get('report')==='off')state.report=false;
const byId=Object.fromEntries(G.boxes.map(b=>[b.id,b]));
const esc=s=>s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const short=(s,n)=>s.length<=n?s:s.slice(0,n-1)+'\\u2026';
const joined=(k,k2)=>k==='value'&&k2==='value'?'value':(k==='day'||k2==='day')?'day':'rows';

// Which box stands for a box now: itself, its collapsed group, 'skip' (hidden) or null (off).
function rep(b){ if(b.kind==='condition')return state.conditions?b.id:null;
  const m=state.group[b.group]; return m==='expanded'?b.id:m==='collapsed'?'group:'+b.group:'skip'; }
function visibleGraph(){
  const up={}; G.arrows.forEach(([a,b,k])=>(up[b]=up[b]||[]).push([a,k]));
  const ends=(id,k,seen=new Set())=>{ if(seen.has(id))return[]; seen.add(id);  // through hidden boxes
    const r=rep(byId[id]); if(r!=='skip')return [[id,k]];
    return (up[id]||[]).flatMap(([p,k2])=>ends(p,joined(k,k2),seen)); };
  const boxes={}, arrows=new Map();
  G.boxes.forEach(b=>{const r=rep(b); if(!r||r==='skip')return;
    if(r===b.id)boxes[r]={id:r,kind:b.kind,group:b.kind==='condition'?'filters on '+b.group:b.group,
      base:b.group,lines:b.lines,title:b.title};
    else{const n=G.boxes.filter(x=>x.group===b.group&&x.kind!=='condition').length;
      boxes[r]=boxes[r]||{id:r,kind:b.kind+' collapsed',group:b.group,base:b.group,
        lines:[b.group,n+' columns, collapsed'],title:b.group};}});
  G.arrows.forEach(([a,b,k])=>{const rb=rep(byId[b]); if(!rb||rb==='skip')return;
    ends(a,k).forEach(([src,k2])=>{const ra=rep(byId[src]); if(!ra||ra==='skip'||ra===rb)return;
      const key=ra+'>'+rb; if(!arrows.has(key)||k2==='value')arrows.set(key,[ra,rb,k2]);});});
  return {boxes:Object.values(boxes), arrows:[...arrows.values()]};
}

// Layered layout: each box one column right of its furthest source. An output that feeds
// nothing sits in the last column.
function layout(V){
  const preds={},succs={}; V.boxes.forEach(b=>{preds[b.id]=[];succs[b.id]=[];});
  V.arrows.forEach(([a,b])=>{preds[b].push(a);succs[a].push(b);});
  const layer={}, busy=new Set();
  const depth=id=>{if(id in layer)return layer[id]; if(busy.has(id))return 0; busy.add(id);
    const d=1+Math.max(-1,...preds[id].map(depth)); busy.delete(id); return layer[id]=d;};
  V.boxes.forEach(b=>depth(b.id)); const last=Math.max(0,...Object.values(layer));
  V.boxes.forEach(b=>{if(b.kind.startsWith('output')&&!succs[b.id].length)layer[b.id]=last;});
  const cols=[...Array(last+1)].map((_,i)=>V.boxes.filter(b=>layer[b.id]===i).map(b=>b.id));
  for(let s=0;s<8;s++){const order={}; cols.forEach(c=>c.forEach((id,i)=>order[id]=i));
    const fwd=s%2===0, idx=fwd?[...cols.keys()].slice(1):[...cols.keys()].reverse().slice(1);
    idx.forEach(i=>{const near=fwd?preds:succs;
      const centre=id=>near[id].length?near[id].reduce((t,n)=>t+order[n],0)/near[id].length:order[id];
      cols[i].sort((a,b)=>centre(a)-centre(b)); cols[i].forEach((id,j)=>order[id]=j);});}
  const h=Object.fromEntries(V.boxes.map(b=>[b.id,10+LINE*b.lines.length])), pos={};
  cols.forEach((c,ci)=>{let y=0; c.forEach(id=>{pos[id]=[ci*(W+GX),y]; y+=h[id]+GY;});});
  const height=Math.max(0,...cols.map(c=>c.reduce((t,id)=>t+h[id]+GY,0)));
  return {pos,h,width:cols.length*(W+GX)-GX,height};
}

// Grouped flowchart: each table, Derived table, Statement and its filters is a labelled
// container, laid out by how the groups feed each other; a condition points once at the
// group it filters.
const PAD=12, HEAD=26, GGAP=24;
function flowLayout(V){
  const byBox=Object.fromEntries(V.boxes.map(b=>[b.id,b])), h=id=>10+LINE*byBox[id].lines.length;
  const groups={}; V.boxes.forEach(b=>(groups[b.group]=groups[b.group]||{name:b.group,kind:b.kind.split(' ')[0],boxes:[]}).boxes.push(b.id));
  const into={}, out={}, preds={}, succs={}; Object.keys(groups).forEach(g=>{into[g]=new Set();out[g]=new Set();});
  V.boxes.forEach(b=>{preds[b.id]=[];succs[b.id]=[];});
  V.arrows.forEach(([a,b])=>{preds[b].push(a);succs[a].push(b);
    if(byBox[a].group!==byBox[b].group){into[byBox[b].group].add(byBox[a].group);out[byBox[a].group].add(byBox[b].group);}});
  const layer={}, busy=new Set();
  const depth=g=>{if(g in layer)return layer[g]; if(busy.has(g))return 0; busy.add(g);
    const d=1+Math.max(-1,...[...into[g]].map(depth)); busy.delete(g); return layer[g]=d;};
  Object.keys(groups).forEach(depth); const last=Math.max(0,...Object.values(layer));
  Object.values(groups).forEach(g=>{if(g.kind==='output'&&!out[g.name].size)layer[g.name]=last;});
  const mean=(ids,y)=>{const v=ids.map(i=>y[i]).filter(x=>x!==undefined); return v.length?v.reduce((s,x)=>s+x,0)/v.length:1e9;};
  const place=()=>{const y={}, pos={}, boxes=[];
    for(let i=0;i<=last;i++){
      const gs=Object.values(groups).filter(g=>layer[g.name]===i);
      gs.forEach(g=>{g.boxes.sort((a,b)=>mean(preds[a],y)-mean(preds[b],y)); g.key=mean(g.boxes.flatMap(id=>preds[id]),y);});
      gs.sort((a,b)=>a.key-b.key);
      let top=0; const x=i*(W+2*PAD+GX);
      gs.forEach(g=>{let iy=top+HEAD;
        g.boxes.forEach(id=>{pos[id]=[x+PAD,iy]; y[id]=iy+h(id)/2; iy+=h(id)+GY;});
        boxes.push({name:g.name,kind:g.kind,x,y:top,w:W+2*PAD,h:iy-GY+PAD-top}); top=iy-GY+PAD+GGAP;});}
    return {pos,boxes,y};};
  let P=place();  // then order the first column by what it feeds, and place again
  Object.values(groups).filter(g=>layer[g.name]===0).forEach(g=>g.boxes.sort((a,b)=>mean(succs[a],P.y)-mean(succs[b],P.y)));
  P=place();
  const width=(last+1)*(W+2*PAD+GX)-GX, height=Math.max(0,...P.boxes.map(g=>g.y+g.h));
  return {pos:P.pos,groups:P.boxes,h,width,height};
}

const boxSvg=(b,x,y,h)=>`<g class="n ${b.kind}" id="${b.id}" transform="translate(${x},${y})"><rect width="${W}" height="${h}" rx="4"/>`
  +b.lines.map((t,i)=>`<text x="8" y="${17+i*LINE}"${i?'':' class="l"'}>${esc(short(t,i?38:34))}</text>`).join('')
  +`<title>${esc(b.title)}</title></g>`;
const curve=(sx,sy,tx,ty)=>{const mx=(sx+tx)/2; return `M${sx},${sy} C${mx},${sy} ${mx},${ty} ${tx},${ty}`;};
const dayLabel=(sx,sy,tx,ty)=>`<text class="flabel" x="${(sx+tx)/2-28}" y="${(sy+ty)/2-4}">day written</text>`;

function renderGraph(V){
  const L=layout(V), parts=[];
  V.arrows.forEach(([a,b,k])=>{const [x1,y1]=L.pos[a],[x2,y2]=L.pos[b];
    const sx=x1+W, sy=y1+L.h[a]/2, tx=x2, ty=y2+L.h[b]/2;
    parts.push(`<path class="e ${k}" data-a="${a}" data-b="${b}" d="${curve(sx,sy,tx,ty)}"/>`+(k==='day'?dayLabel(sx,sy,tx,ty):''));});
  V.boxes.forEach(b=>{const [x,y]=L.pos[b.id]; parts.push(boxSvg(b,x,y,L.h[b.id]));});
  return {parts,width:L.width,height:L.height};
}

function renderFlow(V){
  const F=flowLayout(V), byBox=Object.fromEntries(V.boxes.map(b=>[b.id,b])), parts=[], seen=new Set();
  F.groups.forEach(g=>parts.push(`<g class="grp ${g.kind}"><rect x="${g.x}" y="${g.y}" width="${g.w}" height="${g.h}" rx="8"/><text x="${g.x+10}" y="${g.y+17}">${esc(g.name)}</text></g>`));
  const box=Object.fromEntries(F.groups.map(g=>[g.name,g]));
  V.arrows.forEach(([a,b,k])=>{const [x1,y1]=F.pos[a], sx=x1+W, sy=y1+F.h(a)/2;
    if(byBox[a].kind==='condition'&&k!=='day'){const g=box[byBox[b].group], key=a+'>'+g.name; if(seen.has(key))return; seen.add(key);
      const ty=g.y+g.h/2;
      parts.push(`<path class="e rows filters" data-a="${a}" data-g="${esc(g.name)}" d="${curve(sx,sy,g.x,ty)}"/>`
        +`<text class="flabel" x="${g.x-44}" y="${ty-4}">filters</text>`); return;}
    const [x2,y2]=F.pos[b], ty=y2+F.h(b)/2;
    parts.push(`<path class="e ${k}" data-a="${a}" data-b="${b}" d="${curve(sx,sy,x2,ty)}"/>`+(k==='day'?dayLabel(sx,sy,x2,ty):''));});
  V.boxes.forEach(b=>{const [x,y]=F.pos[b.id]; parts.push(boxSvg(b,x,y,F.h(b.id)));});
  return {parts,width:F.width,height:F.height};
}

let links=[], members={};
function draw(){
  const V=visibleGraph(), R=state.view==='flow'?renderFlow(V):renderGraph(V);
  document.getElementById('graph').innerHTML=`<svg viewBox="-10 -10 ${R.width+20} ${R.height+20}" style="min-width:${Math.round(R.width*.8)}px;aspect-ratio:${R.width+20}/${R.height+20}">${R.parts.join('')}</svg>`;
  links=V.arrows; members={}; V.boxes.forEach(b=>(members[b.group]=members[b.group]||[]).push(b.id));
  wire(document.querySelector('#graph svg'));
  document.getElementById('report').style.display=state.report?'':'none';
  const p=new URLSearchParams(); if(state.view!=='graph')p.set('view',state.view);
  Object.entries(state.group).forEach(([g,m])=>{if(m!=='expanded')p.set('g:'+g,m);});
  if(!state.conditions)p.set('conditions','off'); if(!state.report)p.set('report','off');
  try{history.replaceState(null,'',p.toString()?'?'+p:location.pathname);}catch(e){}
  syncControls();
}

function wire(svg){
  const up={},down={}; links.forEach(([a,b])=>{(up[b]=up[b]||[]).push(a);(down[a]=down[a]||[]).push(b);});
  const walk=(id,next,seen)=>{(next[id]||[]).forEach(n=>{if(!seen.has(n)){seen.add(n);walk(n,next,seen);}});return seen;};
  let vb=svg.getAttribute('viewBox').split(' ').map(Number), drag=null;
  const set=()=>svg.setAttribute('viewBox',vb.join(' '));
  svg.addEventListener('wheel',ev=>{ev.preventDefault(); const r=svg.getBoundingClientRect(), f=ev.deltaY>0?1.15:1/1.15;
    const px=vb[0]+(ev.clientX-r.left)/r.width*vb[2], py=vb[1]+(ev.clientY-r.top)/r.height*vb[3];
    vb=[px-(px-vb[0])*f,py-(py-vb[1])*f,vb[2]*f,vb[3]*f]; set();},{passive:false});
  svg.addEventListener('pointerdown',ev=>{drag={x:ev.clientX,y:ev.clientY,vb:vb.slice(),moved:false};});
  svg.addEventListener('pointermove',ev=>{if(!drag)return; const r=svg.getBoundingClientRect();
    const dx=(ev.clientX-drag.x)/r.width*vb[2], dy=(ev.clientY-drag.y)/r.height*vb[3];
    if(Math.abs(dx)+Math.abs(dy)>1)drag.moved=true; vb=[drag.vb[0]-dx,drag.vb[1]-dy,vb[2],vb[3]]; set();});
  svg.addEventListener('pointerup',()=>setTimeout(()=>drag=null));
  svg.addEventListener('click',ev=>{if(drag&&drag.moved)return;
    svg.querySelectorAll('.n,.e').forEach(el=>el.classList.remove('dim','hit'));
    const g=ev.target.closest('.n'); if(!g)return;
    const keep=walk(g.id,up,new Set([g.id])); walk(g.id,down,keep);
    svg.querySelectorAll('.n').forEach(n=>n.classList.add(keep.has(n.id)?'hit':'dim'));
    svg.querySelectorAll('.e').forEach(e=>{const to=e.dataset.g?members[e.dataset.g]:[e.dataset.b];
      e.classList.add(keep.has(e.dataset.a)&&to.some(id=>keep.has(id))?'hit':'dim');});});
}

// Controls: one select per kind sets all its groups; "Each group" sets one at a time.
const opts=kind=>MODES[kind].map(m=>`<option value="${m}">${m}</option>`).join('');
document.querySelectorAll('#controls select[data-kind]').forEach(s=>{const kind=s.dataset.kind;
  if(!G.groups.some(g=>g.kind===kind)){s.parentElement.style.display='none';return;}
  s.innerHTML='<option value="mixed" disabled>mixed</option>'+opts(kind);
  s.onchange=()=>{G.groups.filter(g=>g.kind===kind).forEach(g=>state.group[g.name]=s.value); draw();};});
document.getElementById('groups').innerHTML=G.groups.map(g=>`<div><span>${esc(g.name)}</span><select data-group="${esc(g.name)}">${opts(g.kind)}</select></div>`).join('');
document.querySelectorAll('#groups select').forEach(s=>s.onchange=()=>{state.group[s.dataset.group]=s.value; draw();});
document.getElementById('view').onchange=e=>{state.view=e.target.value; draw();};
document.getElementById('conditions').onchange=e=>{state.conditions=e.target.checked; draw();};
document.getElementById('showReport').onchange=e=>{state.report=e.target.checked; draw();};
function syncControls(){
  document.querySelectorAll('#controls select[data-kind]').forEach(s=>{
    const ms=new Set(G.groups.filter(g=>g.kind===s.dataset.kind).map(g=>state.group[g.name]));
    s.value=ms.size===1?[...ms][0]:'mixed';});
  document.querySelectorAll('#groups select').forEach(s=>s.value=state.group[s.dataset.group]);
  document.getElementById('view').value=state.view;
  document.getElementById('conditions').checked=state.conditions;
  document.getElementById('showReport').checked=state.report;
}
document.getElementById('controls').style.display='flex';
draw();
</script></body></html>
"""


__all__ = ["export_lineage"]

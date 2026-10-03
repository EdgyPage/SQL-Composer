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

from . import VERSION
from .clauses import Statement, derived_tables
from .refusals import (
    GuardRefused,
    LoadRefused,
    four_part_message,
    refuse_what_the_other_edition_made,
)
from .running import by_day, steps, to_hive
from .tables import readable
from .trees import Node
from .writing import hive_text

TOOLBOX_VERSION = "3.2"


# --- What a box shows --------------------------------------------------------------------------
# Both views read box_lines, so a line added there shows in the HTML page and the Mermaid chart
# alike.


def name_line(box: dict) -> str:
    return box["name"]


def formula_line(box: dict) -> str:
    """A table column's type; for anything else, how it was written."""
    if box["kind"] == "table":
        return box["type"] or ""
    return box["formula"]


def box_lines(box: dict) -> list[str]:
    """The lines of text a box shows: its name, then its formula line unless that is empty."""
    return [line for line in (name_line(box), formula_line(box)) if line]


# --- The graph -------------------------------------------------------------------------------


class Graph:
    """Boxes and arrows. A box is a table column, a Derived table column, an output or a
    condition. An arrow is "value" (the value flows along it), "rows" (it decides which rows
    count) or "day" (a write's date bound decides the day a Saved table is written)."""

    def __init__(self):
        self.boxes = {}
        self.arrows = []

    def add(self, key: str, **facts) -> str:
        """Add a box and return its key. A box already added keeps its first facts."""
        self.boxes.setdefault(key, facts)
        return key

    def arrow(self, source: str | None, target: str, kind: str) -> None:
        """Add an arrow once. A source of None (a column that names no box) adds nothing."""
        if source is not None and (source, target, kind) not in self.arrows:
            self.arrows.append((source, target, kind))

    def parents(self, key: str, kind: str | None = None) -> list[str]:
        """The boxes with an arrow into `key`: only arrows of `kind`, unless it is None."""
        return [a for a, b, k in self.arrows if b == key and kind in (None, k)]

    def upstream(self, key: str, kind: str | None = None) -> list[str]:
        """Every box with a path of arrows into `key`: only arrows of `kind`, unless it is None."""
        seen, todo = [], [key]
        while todo:
            for parent in self.parents(todo.pop(), kind):
                if parent not in seen:
                    seen.append(parent)
                    todo.append(parent)
        return seen


def _box_key(kind: str, *parts) -> str:
    """The key a box is kept under in the graph: its kind, then the parts that tell it apart,
    joined by ":", such as "output:0:runs"."""
    return ":".join([kind] + [str(part) for part in parts])


def _table_box(graph: Graph, table, column: str) -> str:
    """The key of a table column's box, added the first time the column is read or written."""
    return graph.add(_box_key("table", f"{table._name}.{column}"), kind="table",
                     group=table._name, name=f"{table._name}.{column}",
                     full=f"{table._name}.{column}",
                     type=table._columns.get(column), formula="", calculated=False)


def _resolver(graph: Graph, step: Statement, index: int):
    """A function from a column in `step` to the key of the box it reads."""
    tables = {read.table._alias: read.table for read in step._reads}

    def resolve(column: Node) -> str | None:
        table = tables.get(column.table)
        if table is None:
            return None  # an output name, as in ORDER BY "runs"
        if table._statement is not None:
            return _box_key("derived", index, f"{table._name}.{column.name}")
        return _table_box(graph, table, column.name)

    return resolve


def _conditions_of(step: Statement) -> list[tuple[str, object, Node, str]]:
    """Each condition that decides which rows `step` keeps: (clause, condition, tree, then).

    `then` is text written after the tree: a LIMIT's count, after its ORDER BY.
    """
    found = [("WHERE", c, c._tree, "") for c in step._where]
    found += [(f"{read._name.replace('_', ' ')} ON", read.on, read.on._tree, "")
              for read in step._reads if read.on is not None]
    found += [("HAVING", c, c._tree, "") for c in step._having]
    if step._limit is not None:
        order = Node("Order", expressions=[o.copy() for o in step._order_by])
        found.append(("LIMIT", None, order, f"LIMIT {step._limit}"))
    return found


def _condition_text(tree: Node, then: str) -> tuple[str, str]:
    """A condition's Hive and how it was written, with `then` after each."""
    if tree.kind == "Order" and not tree.parts["expressions"]:
        return then, then  # a LIMIT with no ORDER BY
    return tuple(" ".join(x for x in (text.strip(), then) if x)
                 for text in (hive_text(tree), readable(tree)))


def _add_step(graph: Graph, step: Statement, index: int, kind: str, group: str,
              conditions: dict, table: str | None = None) -> None:
    """The boxes one step makes (a Derived table, or the Statement): outputs, then conditions.

    `index` is the Statement's place in the order, and `kind` is "derived" or "output".
    `group` is the group the output boxes are drawn in; a condition's box goes in "filters on"
    that group. `table` is the Derived table's own name, given only when kind is "derived".
    """
    resolve = _resolver(graph, step, index)
    made = []
    for column, name in step._outputs:
        tree = column._tree
        sources = [resolve(used) for used in tree.find_all("Column")]
        if kind == "output":
            key, shown = _box_key("output", index, name), name
        else:
            key, shown = _box_key("derived", index, f"{table}.{name}"), f"{group}.{name}"
        graph.add(key, kind=kind, group=group, name=shown, full=f"{group}.{name}",
                  type=column._type, sql=hive_text(tree), formula=readable(tree),
                  calculated=tree.kind != "Column",
                  group_by=[readable(c._tree) for c in step._group_by] if column._aggregate
                  else [], statement=index)
        for source in sources:
            graph.arrow(source, key, "value")
        made.append(key)
    for number, (clause, condition, tree, then) in enumerate(_conditions_of(step)):
        sql, formula = _condition_text(tree, then)
        key = graph.add(_box_key("condition", index, group, number), kind="condition",
                        group=group, name=f"{clause} in {group}", full=f"{clause} in {group}",
                        type=None, sql=sql, formula=formula, calculated=False, statement=index)
        # `conditions` is filled in here for the caller, which passes it on to _add_write so
        # a write's date bound can find its condition's box.
        conditions[(id(step), id(condition))] = key
        for used in tree.find_all("Column"):
            graph.arrow(resolve(used), key, "rows")
        for target in made:
            graph.arrow(key, target, "rows")


def _date_bounds(s: Statement) -> tuple[Statement, list]:
    """The step that reads a write's real table through FROM, and its date-bound conditions."""
    step = steps(s)[-1][0]
    table = step._reads[0].table
    inner = [read.on for read in step._reads if read._name == "JOIN"]
    key = (table._alias, table._date_partition)
    return step, [c for c in step._where + inner if key in c._spans]


def _add_write(graph: Graph, s: Statement, index: int, conditions: dict) -> list[str]:
    """Arrows from a write's outputs into its Saved table, and the "day written" arrow."""
    table, written = s._write, []
    for _, name in s._outputs:
        target = _table_box(graph, table, name)
        graph.arrow(_box_key("output", index, name), target, "value")
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
        conditions = {}  # each condition's box key, filled in by _add_step
        for table in derived_tables(s):
            _add_step(graph, table._statement, index=index, kind="derived",
                      group=groups[(index, table._name)], conditions=conditions,
                      table=table._name)
        _add_step(graph, s, index=index, kind="output", group=name, conditions=conditions)
        ends += [_box_key("output", index, output) for _, output in s._outputs]
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
    """The names of the real tables a Statement reads, itself or through its Derived tables."""
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
    """Refuse Statements that go round in a loop, naming each write and who reads it."""
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
    """The full names of the boxes a copied column comes from, nearest first.

    A box that is a calculation has " (calculated)" after its name.
    """
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
        verb = "writes" if s._replaces_day else "adds to"
        parts.append(f"It {verb} the Saved table {s._write._name}, one day at a time.")
    return " ".join(parts)


def _submitted(s: Statement, name: str) -> tuple[str, str]:
    """The Hive as submitted; for a write over several days, the first day's, even when the
    dates cap refuses the whole write."""
    try:
        return to_hive(s), ""
    except (GuardRefused, LoadRefused):
        if s._write is None:
            raise
    days = by_day(s)
    return to_hive(days[0]), (
        f"This write covers {len(days)} days, and a write fills one day at a time: send "
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
    """The Markdown's Mermaid chart, as lines: a subgraph for each group, then the arrows, with
    one "filters" arrow from each condition to each group whose rows it decides."""
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
    """_how for the HTML page: how a calculation was written, then the Hive it became."""
    if box["formula"] != box["sql"]:
        return f"{_inline_code(box['formula'])}, which is {_inline_code(box['sql'])}"
    return _inline_code(box["sql"])


def _entry_html(entry: dict) -> str:
    """One calculated column in the HTML report: its tree, rows that count, GROUP BY."""
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
    """The short commit checked out in the repository at `place`, whose .git is `dot`."""
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
    """Text for a file name: each character but a letter, digit, _ or - becomes _."""
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
    """The Statements passed, each once; anything that isn't a Statement reading a table is
    refused."""
    if not statements:
        raise TypeError(four_part_message(
            what="export_lineage() was given no Statement.",
            why="It draws where each column of a Statement comes from.",
            fix="Pass one or more Statements, such as export_lineage(weekly).",
            opt_out=None))
    found = []
    for s in statements:
        if not isinstance(s, Statement) or s._ddl is not None:
            refuse_what_the_other_edition_made(s, "export_lineage")
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
    """The to= path, refused unless it names an .html file."""
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
    return (f"Made by export_lineage on {when:%Y-%m-%d %H:%M}, from your scripts at commit "
            f"{commit}, with {VERSION}.")


# The HTML page. to_html fills in each __NAME__ marker; the script at the end draws the lineage.
# This is an ordinary Python string, so a backslash in the script is written twice.
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
// This script draws the lineage as an SVG picture, and makes the controls and the mouse work.
// It is plain JavaScript that any browser runs, with nothing to install or download.

// Everything to draw, filled in by Python: the boxes, the arrows between them, and the groups
// the boxes sit in (a table, a Derived table or a Statement's outputs).
const graph = __DATA__;

// Sizes in the drawing, in pixels.
const BOX_WIDTH = 250;
const COLUMN_GAP = 80;  // between two columns of boxes
const BOX_GAP = 14;  // between two boxes in one column
const LINE_HEIGHT = 15;  // one line of text in a box
const GROUP_PADDING = 12;  // around the boxes inside a group, in the Grouped flowchart
const GROUP_HEADING = 26;  // room for a group's name above its boxes
const GROUP_GAP = 24;  // between two groups in one column

// How each kind of group can be shown. Outputs can be collapsed, but not hidden.
const MODES_BY_KIND = {
  table: ['expanded', 'collapsed', 'hidden'],
  derived: ['expanded', 'collapsed', 'hidden'],
  output: ['expanded', 'collapsed'],
};

// What the reader has chosen: the Graph or the Grouped flowchart ('graph' or 'flow'), each
// group's mode, and whether the conditions and the report show.
const state = {view: 'graph', groupMode: {}, conditions: true, report: true};

// An object holding each item under the key that keyFor(item) gives, to look items up by key.
function indexBy(items, keyFor) {
  const index = {};
  items.forEach(item => {
    index[keyFor(item)] = item;
  });
  return index;
}

// Each box, looked up by its id.
const boxById = indexBy(graph.boxes, box => box.id);

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

// Start from the settings saved in the page's address (after the ?), so a link opens the page
// as it was left. Any group the address doesn't mention starts expanded.
function readSettingsFromAddress() {
  graph.groups.forEach(group => {
    state.groupMode[group.name] = 'expanded';
  });
  const settings = new URLSearchParams(location.search);
  graph.groups.forEach(group => {
    const mode = settings.get('g:' + group.name);
    if (MODES_BY_KIND[group.kind].includes(mode)) {
      state.groupMode[group.name] = mode;
    }
  });
  if (settings.get('view') === 'flow') {
    state.view = 'flow';
  }
  if (settings.get('conditions') === 'off') {
    state.conditions = false;
  }
  if (settings.get('report') === 'off') {
    state.report = false;
  }
}

// Save the settings in the page's address, so reloading the page or sharing its link keeps
// them. Only settings that differ from where the page starts are written.
function saveSettingsInAddress() {
  const settings = new URLSearchParams();
  if (state.view !== 'graph') {
    settings.set('view', state.view);
  }
  Object.entries(state.groupMode).forEach(([name, mode]) => {
    if (mode !== 'expanded') {
      settings.set('g:' + name, mode);
    }
  });
  if (!state.conditions) {
    settings.set('conditions', 'off');
  }
  if (!state.report) {
    settings.set('report', 'off');
  }
  try {
    const address = settings.toString() ? '?' + settings.toString() : location.pathname;
    history.replaceState(null, '', address);
  } catch (error) {
    // A browser may refuse to change the address, as for some pages opened from a file. The
    // drawing still works; only the settings aren't kept.
  }
}

// --- Which boxes and arrows to draw -------------------------------------------------------

// The id of the box drawn in a box's place: its own id; its group's id when the group is
// collapsed; 'skip' when the group is hidden; or null for a condition while conditions are off.
function drawnAs(box) {
  if (box.kind === 'condition') {
    return state.conditions ? box.id : null;
  }
  const mode = state.groupMode[box.group];
  if (mode === 'expanded') {
    return box.id;
  }
  if (mode === 'collapsed') {
    return 'group:' + box.group;
  }
  return 'skip';
}

// The kind of the one arrow drawn for two arrows in a row, when the box between them is
// hidden: 'value' if both carry a value, 'day' if either is a "day written" arrow, and
// otherwise 'rows'.
function joinedArrowKind(first, second) {
  if (first === 'value' && second === 'value') {
    return 'value';
  }
  if (first === 'day' || second === 'day') {
    return 'day';
  }
  return 'rows';
}

// The boxes and arrows to draw now, after collapsing, hiding and switching off conditions. A
// collapsed group is drawn as one box, and arrows through a hidden box are joined around it.
function visibleGraph() {
  // For each box, the arrows coming into it, as [source id, arrow kind].
  const arrowsInto = {};
  graph.arrows.forEach(([source, target, kind]) => {
    if (!arrowsInto[target]) {
      arrowsInto[target] = [];
    }
    arrowsInto[target].push([source, kind]);
  });

  // Where an arrow really starts, as a list of [box id, arrow kind]. When the box it starts
  // from is hidden, it goes on back through the arrows into that box, joining their kinds.
  // A condition switched off is returned as it is, and the caller leaves its arrow out.
  // `visited` holds the boxes already passed, so a loop of arrows can't go round forever.
  function drawnStarts(id, kind, visited) {
    if (visited.has(id)) {
      return [];
    }
    visited.add(id);
    if (drawnAs(boxById[id]) !== 'skip') {
      return [[id, kind]];
    }
    let starts = [];
    (arrowsInto[id] || []).forEach(([source, sourceKind]) => {
      starts = starts.concat(drawnStarts(source, joinedArrowKind(kind, sourceKind), visited));
    });
    return starts;
  }

  const drawnBoxes = {};
  graph.boxes.forEach(box => {
    const drawnId = drawnAs(box);
    if (!drawnId || drawnId === 'skip') {
      return;
    }
    if (drawnId === box.id) {
      drawnBoxes[drawnId] = {
        id: drawnId,
        kind: box.kind,
        group: box.kind === 'condition' ? 'filters on ' + box.group : box.group,
        lines: box.lines,
        title: box.title,
      };
    } else if (!drawnBoxes[drawnId]) {
      // The first box met in a collapsed group makes the one box that stands for the group.
      const columnCount = graph.boxes.filter(
        other => other.group === box.group && other.kind !== 'condition').length;
      drawnBoxes[drawnId] = {
        id: drawnId,
        kind: box.kind + ' collapsed',
        group: box.group,
        lines: [box.group, columnCount + ' columns, collapsed'],
        title: box.group,
      };
    }
  });

  // One arrow for each pair of drawn boxes: the first one found, unless a later one carries a
  // value, which takes its place.
  const drawnArrows = new Map();
  graph.arrows.forEach(([source, target, kind]) => {
    const drawnTarget = drawnAs(boxById[target]);
    if (!drawnTarget || drawnTarget === 'skip') {
      return;
    }
    drawnStarts(source, kind, new Set()).forEach(([start, startKind]) => {
      const drawnSource = drawnAs(boxById[start]);
      if (!drawnSource || drawnSource === 'skip' || drawnSource === drawnTarget) {
        return;
      }
      const pair = drawnSource + '>' + drawnTarget;
      if (!drawnArrows.has(pair) || startKind === 'value') {
        drawnArrows.set(pair, [drawnSource, drawnTarget, startKind]);
      }
    });
  });
  return {boxes: Object.values(drawnBoxes), arrows: Array.from(drawnArrows.values())};
}

// --- Where each box goes ------------------------------------------------------------------

// A box's height: room for each of its lines of text, plus 10 pixels of padding.
function boxHeight(box) {
  return 10 + LINE_HEIGHT * box.lines.length;
}

// Each drawn box's height, looked up by its id.
function boxHeights(boxes) {
  const heights = {};
  boxes.forEach(box => {
    heights[box.id] = boxHeight(box);
  });
  return heights;
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

// The column each item goes in, counting from 0: one column right of its furthest source.
// sourcesOf(id) lists an item's sources. When sources go round in a loop, the item met again
// counts as column 0, so the loop ends.
function columnNumbers(ids, sourcesOf) {
  const columnOf = {};
  const working = new Set();  // the items whose column is still being worked out
  function columnFor(id) {
    if (id in columnOf) {
      return columnOf[id];
    }
    if (working.has(id)) {
      return 0;
    }
    working.add(id);
    const column = 1 + Math.max(-1, ...sourcesOf(id).map(source => columnFor(source)));
    working.delete(id);
    columnOf[id] = column;
    return column;
  }
  ids.forEach(id => columnFor(id));
  return columnOf;
}

// Where each box goes in the Graph. Each box sits one column right of its furthest source,
// and an output that feeds nothing sits in the last column. Then the boxes in each column are
// reordered, to sit level with the boxes they are linked to, so fewer arrows cross.
function graphLayout(visible) {
  const neighbours = neighboursOf(visible);
  const boxIds = visible.boxes.map(box => box.id);
  const columnOf = columnNumbers(boxIds, id => neighbours.sources[id]);
  const lastColumn = Math.max(0, ...Object.values(columnOf));
  visible.boxes.forEach(box => {
    if (box.kind.startsWith('output') && !neighbours.targets[box.id].length) {
      columnOf[box.id] = lastColumn;
    }
  });

  // The ids in each column, from top to bottom.
  const columns = [];
  for (let number = 0; number <= lastColumn; number++) {
    columns.push(visible.boxes.filter(box => columnOf[box.id] === number).map(box => box.id));
  }

  // Make 8 sweeps across the columns, right, then left, and so on, reordering each column
  // but the first one a sweep starts from. Sweeping right, each box moves to the average
  // place of its sources; sweeping left, of its targets.
  for (let sweep = 0; sweep < 8; sweep++) {
    const sweepingRight = sweep % 2 === 0;
    const linked = sweepingRight ? neighbours.sources : neighbours.targets;
    const place = {};  // each box's place in its column, 0 at the top
    columns.forEach(ids => {
      ids.forEach((id, number) => {
        place[id] = number;
      });
    });
    // The average place of the boxes linked to a box, or its own place if there are none.
    const averagePlace = id => {
      if (!linked[id].length) {
        return place[id];
      }
      return linked[id].reduce((total, other) => total + place[other], 0) / linked[id].length;
    };
    const reorder = number => {
      columns[number].sort((a, b) => averagePlace(a) - averagePlace(b));
      columns[number].forEach((id, newPlace) => {
        place[id] = newPlace;
      });
    };
    if (sweepingRight) {
      for (let number = 1; number < columns.length; number++) {
        reorder(number);
      }
    } else {
      for (let number = columns.length - 2; number >= 0; number--) {
        reorder(number);
      }
    }
  }

  const heights = boxHeights(visible.boxes);
  const positions = {};  // each box's top-left corner, as [x, y]
  columns.forEach((ids, number) => {
    let y = 0;
    ids.forEach(id => {
      positions[id] = [number * (BOX_WIDTH + COLUMN_GAP), y];
      y += heights[id] + BOX_GAP;
    });
  });
  const columnHeights = columns.map(
    inColumn => inColumn.reduce((total, id) => total + heights[id] + BOX_GAP, 0));
  return {
    positions: positions,
    heights: heights,
    width: columns.length * (BOX_WIDTH + COLUMN_GAP) - COLUMN_GAP,
    height: Math.max(0, ...columnHeights),
  };
}

// Where each group and box goes in the Grouped flowchart. Each table, Derived table, Statement
// and its filters is a labelled group. A group sits one column right of the furthest group
// feeding it, and an output group that feeds nothing sits in the last column.
function flowchartLayout(visible) {
  const visibleBoxById = indexBy(visible.boxes, box => box.id);
  const heights = boxHeights(visible.boxes);
  const neighbours = neighboursOf(visible);

  // Each group, with the ids of its boxes.
  const groups = {};
  visible.boxes.forEach(box => {
    if (!groups[box.group]) {
      groups[box.group] = {name: box.group, kind: box.kind.split(' ')[0], boxes: []};
    }
    groups[box.group].boxes.push(box.id);
  });

  // For each group, the groups with an arrow into it, and the groups it has an arrow into.
  const groupsFeeding = {};
  const groupsFed = {};
  Object.keys(groups).forEach(name => {
    groupsFeeding[name] = new Set();
    groupsFed[name] = new Set();
  });
  visible.arrows.forEach(([source, target]) => {
    const sourceGroup = visibleBoxById[source].group;
    const targetGroup = visibleBoxById[target].group;
    if (sourceGroup !== targetGroup) {
      groupsFeeding[targetGroup].add(sourceGroup);
      groupsFed[sourceGroup].add(targetGroup);
    }
  });

  const columnOf = columnNumbers(Object.keys(groups), name => Array.from(groupsFeeding[name]));
  const lastColumn = Math.max(0, ...Object.values(columnOf));
  Object.values(groups).forEach(group => {
    if (group.kind === 'output' && !groupsFed[group.name].size) {
      columnOf[group.name] = lastColumn;
    }
  });

  // The average y (distance down the page) of the middles of the boxes in `ids` placed so
  // far. When none is placed yet it is far below everything (1e9), so those boxes sort last.
  function averageMiddle(ids, middles) {
    const placed = ids.map(id => middles[id]).filter(middle => middle !== undefined);
    if (!placed.length) {
      return 1e9;
    }
    return placed.reduce((total, middle) => total + middle, 0) / placed.length;
  }

  // Place every group and its boxes, column by column. In each column, a group's boxes are
  // sorted by where their sources sit, and the groups by where all their boxes' sources sit,
  // so each sits level with what feeds it. It returns each box's top-left corner, each
  // group's frame, and the y of each box's middle.
  function placeGroups() {
    const middles = {};
    const positions = {};
    const frames = [];
    for (let number = 0; number <= lastColumn; number++) {
      const inColumn = Object.values(groups).filter(group => columnOf[group.name] === number);
      inColumn.forEach(group => {
        group.boxes.sort((a, b) => averageMiddle(neighbours.sources[a], middles)
          - averageMiddle(neighbours.sources[b], middles));
        let allSources = [];
        group.boxes.forEach(id => {
          allSources = allSources.concat(neighbours.sources[id]);
        });
        group.sortKey = averageMiddle(allSources, middles);
      });
      inColumn.sort((a, b) => a.sortKey - b.sortKey);
      const x = number * (BOX_WIDTH + 2 * GROUP_PADDING + COLUMN_GAP);
      let top = 0;
      inColumn.forEach(group => {
        let y = top + GROUP_HEADING;
        group.boxes.forEach(id => {
          positions[id] = [x + GROUP_PADDING, y];
          middles[id] = y + heights[id] / 2;
          y += heights[id] + BOX_GAP;
        });
        frames.push({
          name: group.name,
          kind: group.kind,
          x: x,
          y: top,
          width: BOX_WIDTH + 2 * GROUP_PADDING,
          height: y - BOX_GAP + GROUP_PADDING - top,
        });
        top = y - BOX_GAP + GROUP_PADDING + GROUP_GAP;
      });
    }
    return {positions: positions, frames: frames, middles: middles};
  }

  let placed = placeGroups();
  // The first column has no sources to sort by, so sort its boxes by the boxes they feed, now
  // those are placed, and place everything again.
  Object.values(groups).filter(group => columnOf[group.name] === 0).forEach(group => {
    group.boxes.sort((a, b) => averageMiddle(neighbours.targets[a], placed.middles)
      - averageMiddle(neighbours.targets[b], placed.middles));
  });
  placed = placeGroups();
  return {
    positions: placed.positions,
    frames: placed.frames,
    heights: heights,
    width: (lastColumn + 1) * (BOX_WIDTH + 2 * GROUP_PADDING + COLUMN_GAP) - COLUMN_GAP,
    height: Math.max(0, ...placed.frames.map(frame => frame.y + frame.height)),
  };
}

// --- The SVG ------------------------------------------------------------------------------

// The SVG for one box: its rectangle, its lines of text (the first in bold), and a tooltip
// with its full name and its Hive or type.
function boxSvg(box, x, y, height) {
  const lines = box.lines.map((line, number) => {
    const bold = number ? '' : ' class="l"';
    // How many characters fit across the box: fewer on the first line, which is bold.
    const text = escapeHtml(shortened(line, number ? 38 : 34));
    // 8 pixels in from the box's left edge; the first line's baseline 17 pixels down.
    return `<text x="8" y="${17 + number * LINE_HEIGHT}"${bold}>${text}</text>`;
  });
  return `<g class="n ${box.kind}" id="${box.id}" transform="translate(${x},${y})">`
    + `<rect width="${BOX_WIDTH}" height="${height}" rx="4"/>`
    + lines.join('')
    + `<title>${escapeHtml(box.title)}</title></g>`;
}

// An SVG path from (startX, startY) to (endX, endY) that bends smoothly, leaving and arriving
// level.
function curve(startX, startY, endX, endY) {
  const middleX = (startX + endX) / 2;
  return `M${startX},${startY} C${middleX},${startY} ${middleX},${endY} ${endX},${endY}`;
}

// The "day written" label, just above the middle of its arrow.
function dayWrittenLabel(startX, startY, endX, endY) {
  // 28 pixels is about half the label's width, so the label is centred on the arrow.
  const x = (startX + endX) / 2 - 28;
  const y = (startY + endY) / 2 - 4;
  return `<text class="flabel" x="${x}" y="${y}">day written</text>`;
}

// The SVG for one arrow between two boxes, and its label if it is a "day written" arrow.
// data-a and data-b hold the ids of the boxes at its two ends, for lighting up a path.
function arrowSvg(source, target, kind, startX, startY, endX, endY) {
  const path = `<path class="e ${kind}" data-a="${source}" data-b="${target}" `
    + `d="${curve(startX, startY, endX, endY)}"/>`;
  return path + (kind === 'day' ? dayWrittenLabel(startX, startY, endX, endY) : '');
}

// The SVG pieces of the Graph, and its size. An arrow leaves the middle of a box's right side
// and arrives at the middle of the next box's left side.
function renderGraph(visible) {
  const layout = graphLayout(visible);
  const parts = [];
  visible.arrows.forEach(([source, target, kind]) => {
    const [sourceX, sourceY] = layout.positions[source];
    const [targetX, targetY] = layout.positions[target];
    const startX = sourceX + BOX_WIDTH;
    const startY = sourceY + layout.heights[source] / 2;
    const endY = targetY + layout.heights[target] / 2;
    parts.push(arrowSvg(source, target, kind, startX, startY, targetX, endY));
  });
  visible.boxes.forEach(box => {
    const [x, y] = layout.positions[box.id];
    parts.push(boxSvg(box, x, y, layout.heights[box.id]));
  });
  return {parts: parts, width: layout.width, height: layout.height};
}

// The SVG pieces of the Grouped flowchart, and its size. A condition's arrow points once at
// the group it filters, not at each box in it.
function renderFlowchart(visible) {
  const layout = flowchartLayout(visible);
  const visibleBoxById = indexBy(visible.boxes, box => box.id);
  const parts = [];
  layout.frames.forEach(frame => {
    parts.push(`<g class="grp ${frame.kind}">`
      + `<rect x="${frame.x}" y="${frame.y}" `
      + `width="${frame.width}" height="${frame.height}" rx="8"/>`
      + `<text x="${frame.x + 10}" y="${frame.y + 17}">${escapeHtml(frame.name)}</text></g>`);
  });
  const frameByName = indexBy(layout.frames, frame => frame.name);
  const filterArrowsDrawn = new Set();  // "condition>group" for each filters arrow drawn
  visible.arrows.forEach(([source, target, kind]) => {
    const [sourceX, sourceY] = layout.positions[source];
    const startX = sourceX + BOX_WIDTH;
    const startY = sourceY + layout.heights[source] / 2;
    if (visibleBoxById[source].kind === 'condition' && kind !== 'day') {
      const frame = frameByName[visibleBoxById[target].group];
      const drawnKey = source + '>' + frame.name;
      if (!filterArrowsDrawn.has(drawnKey)) {
        filterArrowsDrawn.add(drawnKey);
        const endY = frame.y + frame.height / 2;
        // data-g names the group at the arrow's end, for lighting up a path.
        const groupName = escapeHtml(frame.name);
        parts.push(`<path class="e rows filters" data-a="${source}" data-g="${groupName}" `
          + `d="${curve(startX, startY, frame.x, endY)}"/>`
          + `<text class="flabel" x="${frame.x - 44}" y="${endY - 4}">filters</text>`);
      }
    } else {
      const [targetX, targetY] = layout.positions[target];
      const endY = targetY + layout.heights[target] / 2;
      parts.push(arrowSvg(source, target, kind, startX, startY, targetX, endY));
    }
  });
  visible.boxes.forEach(box => {
    const [x, y] = layout.positions[box.id];
    parts.push(boxSvg(box, x, y, layout.heights[box.id]));
  });
  return {parts: parts, width: layout.width, height: layout.height};
}

// --- Drawing, and what the mouse does -----------------------------------------------------

// Draw the page again from `state`: the picture, the report shown or not, the address and
// the controls. Every control calls this after it changes `state`.
function draw() {
  const visible = visibleGraph();
  const drawing = state.view === 'flow' ? renderFlowchart(visible) : renderGraph(visible);
  // A 10-pixel margin all round, and the picture never shrunk below 80% of its full size.
  const viewBox = `-10 -10 ${drawing.width + 20} ${drawing.height + 20}`;
  const size = `min-width:${Math.round(drawing.width * 0.8)}px;`
    + `aspect-ratio:${drawing.width + 20}/${drawing.height + 20}`;
  document.getElementById('graph').innerHTML = `<svg viewBox="${viewBox}" style="${size}">`
    + `${drawing.parts.join('')}</svg>`;
  addMouseHandlers(document.querySelector('#graph svg'), visible);
  document.getElementById('report').style.display = state.report ? '' : 'none';
  saveSettingsInAddress();
  syncControls();
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

// --- The controls -------------------------------------------------------------------------

// The choices of a menu that sets how a group of this kind is shown.
function modeOptions(kind) {
  return MODES_BY_KIND[kind].map(mode => `<option value="${mode}">${mode}</option>`).join('');
}

// Fill in the controls, and say what each does when it changes. The Tables, Derived tables
// and Outputs menus set every group of their kind at once; "Each group" sets one at a time.
function setUpControls() {
  document.querySelectorAll('#controls select[data-kind]').forEach(menu => {
    const kind = menu.dataset.kind;
    if (!graph.groups.some(group => group.kind === kind)) {
      menu.parentElement.style.display = 'none';  // no group of this kind to set
    } else {
      // "mixed" shows when the groups of this kind are set differently; it can't be picked.
      menu.innerHTML = '<option value="mixed" disabled>mixed</option>' + modeOptions(kind);
      menu.onchange = () => {
        graph.groups.filter(group => group.kind === kind).forEach(group => {
          state.groupMode[group.name] = menu.value;
        });
        draw();
      };
    }
  });
  document.getElementById('groups').innerHTML = graph.groups.map(group => {
    const name = escapeHtml(group.name);
    const menu = `<select data-group="${name}">${modeOptions(group.kind)}</select>`;
    return `<div><span>${name}</span>${menu}</div>`;
  }).join('');
  document.querySelectorAll('#groups select').forEach(menu => {
    menu.onchange = () => {
      state.groupMode[menu.dataset.group] = menu.value;
      draw();
    };
  });
  document.getElementById('view').onchange = event => {
    state.view = event.target.value;
    draw();
  };
  document.getElementById('conditions').onchange = event => {
    state.conditions = event.target.checked;
    draw();
  };
  document.getElementById('showReport').onchange = event => {
    state.report = event.target.checked;
    draw();
  };
}

// Make every control show the current settings.
function syncControls() {
  document.querySelectorAll('#controls select[data-kind]').forEach(menu => {
    const ofKind = graph.groups.filter(group => group.kind === menu.dataset.kind);
    const modes = new Set(ofKind.map(group => state.groupMode[group.name]));
    menu.value = modes.size === 1 ? Array.from(modes)[0] : 'mixed';
  });
  document.querySelectorAll('#groups select').forEach(menu => {
    menu.value = state.groupMode[menu.dataset.group];
  });
  document.getElementById('view').value = state.view;
  document.getElementById('conditions').checked = state.conditions;
  document.getElementById('showReport').checked = state.report;
}

// Start: read the settings, set up the controls, show them (they stay hidden when scripts
// are off), and draw.
readSettingsFromAddress();
setUpControls();
document.getElementById('controls').style.display = 'flex';
draw();
</script></body></html>
"""


__all__ = ["export_lineage"]

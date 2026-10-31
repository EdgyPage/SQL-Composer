"""Draw each Workflow (`sqlglot_composer/workflows.py`) as a graph, and count its hand steps.

Run it on `dev` after changing a Workflow's steps:

    python tools/workflow_graph.py

It writes `docs/workflows.md`: for each Workflow, a Mermaid diagram of its start materials, its
steps and what each makes, and how many steps of each kind it has. A fiddling step, a step done
by hand though the code knows the answer, is drawn in red. It stops, writing nothing, with a
list of each gap: a step that needs what neither the start materials nor an earlier step gives,
or an end artifact no step makes. A test holds the page to what this writes, and each
Workflow's fiddling to at most its count when Toolbox 8.0 began.

It also writes the charts a user reads on `main`, each a Mermaid chart, which GitHub and VS
Code draw and an LLM reads as text, beside the same steps as a numbered list: each Workflow's,
the program flow, the Toolbox's own path, and the Excel flow, from a workbook to prod. They go
between `<!-- chart: NAME -->` and `<!-- /chart -->` in the README template,
`docs/clean-branch-readme.md`, and in how-to 29,
`worked_examples/how_to/29_follow_a_workflow.py`, which this writes whole. `steps_listed`
gives a Workflow's numbered list alone, for a page with no room for its chart. A test holds
every copy to what this writes: never edit one by hand.
"""

from __future__ import annotations

import re
import sys
import textwrap
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs" / "workflows.md"
README = ROOT / "docs" / "clean-branch-readme.md"
HOW_TO = ROOT / "worked_examples" / "how_to" / "29_follow_a_workflow.py"
sys.path.insert(0, str(ROOT))

from sqlglot_composer import project, workflows  # noqa: E402
from sqlglot_composer.workflows import KINDS, Workflow  # noqa: E402

# How a step of each kind is drawn: its node's brackets, its class's name, and the class's
# colours.
DRAWN = {
    workflows.FILE_STEP: ("[", "]", "files_only", "fill:#e3f2e1,stroke:#4a8a3f"),
    workflows.PERMISSION: ("[[", "]]", "warehouse_call", "fill:#e1ecf7,stroke:#3f6a9a"),
    workflows.DECISION: ("{", "}", "your_decision", "fill:#fbf1d6,stroke:#a8842a"),
    workflows.FIDDLING: (">", "]", "by_hand", "fill:#f8d7d5,stroke:#b03a30"),
}
# What each shape of a chart is, as a page says it under its charts.
LEGEND = ("In each chart, a plain box is a step that changes only files, or only prints; a "
          "box with double edges a call to the warehouse, yours to run; a diamond a decision, "
          "yours to make; and a box with round corners something a step needs or makes.")
THING_STYLE = "    classDef thing fill:#ffffff,stroke:#888888"
HEADING = """# Workflows

What a Project goes through to reach each end goal, drawn from `sqlglot_composer/workflows.py`
by `tools/workflow_graph.py`: don't edit this page, run the tool. Each box with round corners is
something a step needs or makes; each step is drawn by its kind:

- a **file step** (green), which touches only files, or only prints, never the
  Warehouse: a Project action, or show_hive;
- a **permission** (blue, double-edged), a call to the Warehouse the user makes on purpose;
- a **decision** (yellow, a diamond), which needs the user's judgement;
- **fiddling** (red, a flag), a step done by hand though the code knows the answer.

Toolbox 8.0 takes each Workflow's fiddling to nothing.
"""


# The Toolbox's own path, from a Table reference to the warehouse: a chart and its steps.
PROGRAM_FLOW = ("""flowchart TD
    reference("Table reference: references/db__table.py")
    clauses["Clause functions: SELECT, FROM, WHERE, JOIN_ON and the rest"]
    statement["statement(...): a Statement"]
    guards{"Guards and Load limits check it as it is built"}
    refusal("a refusal: what happened, why, the usual fix, the opt-out")
    hive["to_hive(s) or show_hive(s): its Hive"]
    read[["run_query(s, query): its rows, through warehouse.py"]]
    change[["run_execute(s, execute): a change, through warehouse.py"]]
    conversion["project.convert: someone else's Hive"]
    notebook["a Saved table's notebook: create() and write()"]
    tables[["project.run_tables: each write(), in order"]]
    reference --> clauses --> statement --> guards
    guards -->|"refused"| refusal
    guards --> hive
    hive --> read
    hive --> change
    conversion --> notebook --> statement
    notebook --> tables --> change""",
                [("A Table reference describes a table you read or write",
                  "references/db__table.py"),
                 ("Clause functions build a Statement, in the order SQL writes them",
                  "statement(SELECT(...), FROM(...), WHERE(...))"),
                 ("Guards and Load limits check it as it is built; a refusal says what "
                  "happened, why, the usual fix and the opt-out", ""),
                 ("to_hive or show_hive gives its Hive", "show_hive(s)"),
                 ("run_query sends a read through your query, run_execute a change through "
                  "your execute, both in warehouse.py",
                  "run_query(s, query)\nrun_execute(s, execute)"),
                 ("A Saved table's notebook builds its create() and write() the same way; "
                  "project.convert writes one from someone else's Hive, and "
                  "project.run_tables runs each write() in order",
                  "project.run_tables(execute=execute)")])
# From an Excel workbook to prod: a chart and its steps.
EXCEL_FLOW = ("""flowchart TD
    workbook("a Formula workbook")
    copilot{{"Copilot, given files 03, 04, 05, 11 and 12: the workbook as Hive"}}
    scripts("its Hive, each name in angle brackets filled in, saved as .hql files")
    convert["the convert Workflow: project.convert(NAME, files=FILES), one batch"]
    dev[["each table created, seeded and written in dev"]]
    compare[["project.compare_batch: each against its query"]]
    promote["project.promote: each copied to prod"]
    prod[["each created and written in prod"]]
    workbook --> copilot --> scripts --> convert --> dev --> compare --> promote --> prod""",
              [("Fill in a Formula workbook, laid out as copilot/formula_workbook.xlsx is", ""),
               ("Give Copilot files 03, 04, 05, 11 and 12 with the workbook: it writes the "
                "workbook as Hive, a query for each final Table", ""),
               ("Fill in each name it writes in angle brackets, save each query as a .hql "
                "file named for its final Table, and convert them as one batch in the convert "
                "Workflow, DEV filled in: each becomes a Saved table named for its file, or, "
                "when the batch is one file, for the batch",
                'project.convert("budget", files=["sales.hql", "regions.hql"], query=query)'),
               ("Tick each checklist, then create, seed and write each table in dev, as the "
                "Workflow's steps say", ""),
               ("Compare each with its query, the Hive Copilot wrote",
                'project.compare_batch("budget", query=query)'),
               ("Promote them, and create and write each in prod, through the promote Workflow",
                "project.promote([...])")])


def steps_listed(workflow: Workflow) -> list[str]:
    """A Workflow's steps as a numbered list: each its name, its kind in words, and its call
    on the lines after it, indented."""
    return _listed([(f"{step.name} (it {workflows.step_said(workflow, step)})", step.call)
                    for step in workflow.steps])


def _listed(steps: list[tuple[str, str]]) -> list[str]:
    """Steps as a numbered list, each a sentence and the call, if any, indented under it."""
    lines = []
    for number, (said, call) in enumerate(steps, 1):
        lines += textwrap.wrap(f"{number}. {said}.", width=96, subsequent_indent="   ",
                               break_long_words=False, break_on_hyphens=False)
        if call:
            # A blank line first, so Markdown shows the call as code, its lines kept.
            lines += ["", *[f"       {line}" for line in call.split("\n")], ""]
    return lines


def chart(name: str) -> list[str]:
    """The chart a user reads, by its name: a Workflow's, program_flow or excel: its Mermaid
    text in a fenced block, then the same steps as a numbered list."""
    if name == "program_flow":
        mermaid, steps = PROGRAM_FLOW
        return ["```mermaid", mermaid, "```", "", *_listed(steps)]
    if name == "excel":
        mermaid, steps = EXCEL_FLOW
        return ["```mermaid", mermaid, "```", "", *_listed(steps)]
    workflow = next(each for each in workflows.WORKFLOWS if each.name == name)
    return [*diagram(workflow, with_calls=False), "", *steps_listed(workflow)]


def with_charts(text: str) -> str:
    """A page's text with each chart between its markers written again, as this draws it."""
    pieces, at = [], 0
    for found in re.finditer(r"<!-- chart: (\w+) -->\n(.*?)<!-- /chart -->", text, re.DOTALL):
        pieces += [text[at:found.start(2)], "\n".join(chart(found.group(1))), "\n"]
        at = found.end(2)
    return "".join(pieces) + text[at:]


def how_to_text() -> str:
    """How-to 29, which this writes whole: each Workflow's chart, names cell and steps, as the
    Workflow notebook it starts from runs them."""
    lines = _how_to_head()
    for workflow in workflows.WORKFLOWS:
        lines += _how_to_section(workflow)
    lines += ["## Check it worked", "",
              "`project.check()` says each Workflow's next step, or that every step is done.",
              "", "## Common mistakes", "",
              "### A step named again after you ran it", "",
              "A step no file tells of, such as a preview, is named until a later step is",
              "done, and says so: once you have run it, go on.", "",
              "## Next", "",
              "[Convert someone else's Hive](#convert_someone_elses_hive) walks the convert",
              "Workflow through a batch of scripts."]
    # A docstring holds no three quotes of its own: the page reads each escaped one as one.
    body = "\n".join(lines[1:]).replace('"""', '\\"\\"\\"')
    return f"{lines[0]}\n{body}\n" + '"""\n'


def _how_to_head() -> list[str]:
    """How-to 29's title, group, Goal, When you'd use it, and its first step, which starts a
    Project and shows the imports each Workflow notebook starts with."""
    return ['"""Follow a Workflow', "", "For: Intermediate", "", "## Goal", "",
            "Do a whole job from its Workflow notebook, step by step, with nothing typed",
            "twice: each Workflow below is drawn and listed from the steps its notebook",
            "runs, in admin/workflows/, a folder for each.", "",
            "## When you'd use it", "",
            "Each time you start one of the jobs below. `project.check()` names the next",
            "step of each Workflow you have started, and `project.do_next()` runs the steps",
            "it can for you, up to the first that is yours.", "",
            "It needs [Start a Project](#start_a_project).", "", "## Steps", "",
            "### Start a Project", "",
            "Every Project has the Workflow notebooks, each waiting for its names cell:", "",
            ">>> from sqlglot_composer import project",
            ">>> project.start()",
            "Started a Project in the folder you're working in: admin/, references/, "
            "building_blocks/,",
            "tables/ and warehouse.py.",
            "Next: set conn, your connection, in warehouse.py.", "",
            "Each Workflow notebook starts by finding the Project, then imports what its "
            "steps call:", "",
            *[f"    {line}" for line in _imports_wrapped()], "",
            *textwrap.wrap(LEGEND, width=96), ""]


def _how_to_section(workflow: Workflow) -> list[str]:
    """One Workflow's part of how-to 29: what it does, its chart, its names cell, and its
    steps, each its kind in words and its call."""
    lines = [f"### The {workflow.name} Workflow", "",
             *textwrap.wrap(workflow.about, width=96), "",
             *textwrap.wrap("Its chart, drawn from the steps of its notebook, "
                            f"admin/workflows/{workflow.name}/{workflow.name}.ipynb:",
                            width=96, break_long_words=False, break_on_hyphens=False), "",
             *diagram(workflow, with_calls=False)]
    if workflow.inputs:
        lines += ["", "Its names cell, which you fill in and save first:", ""]
        for given in workflow.inputs:
            lines += textwrap.wrap(given.about, width=88, initial_indent="    # ",
                                   subsequent_indent="    # ", break_long_words=False,
                                   break_on_hyphens=False)
            lines.append(f"    {given.name} = {given.empty!r}")
    lines += ["", "Its steps:", ""]
    for number, step in enumerate(workflow.steps, 1):
        lines += textwrap.wrap(f"- {number}. {step.name} (it "
                               f"{workflows.step_said(workflow, step)}).",
                               width=96, subsequent_indent="  ", break_long_words=False,
                               break_on_hyphens=False)
        if step.call:
            lines += ["", *[f"    {line}" for line in step.call.split("\n")], ""]
    return [*lines, ""]


def _imports_wrapped() -> list[str]:
    """The imports of a Workflow notebook, each wrapped in brackets when it runs long."""
    lines = []
    for line in project.WORKFLOW_PATH_LINES:
        if not line.startswith("from "):
            continue
        if len(line) <= 88:
            lines.append(line)
            continue
        module, names = line.split(" import ", 1)
        lines += [f"{module} import (", *[f"    {name}," for name in names.split(", ")], ")"]
    return lines


def label(text: str) -> str:
    """Text as a Mermaid label holds it: in double quotes, its own quotes and hashes written as
    Mermaid's codes for them."""
    return '"' + text.replace("#", "#35;").replace('"', "#quot;") + '"'


def kind_counts(workflow: Workflow) -> Counter[str]:
    """How many steps of each kind a Workflow has."""
    return Counter(step.kind for step in workflow.steps)


def gaps(workflow: Workflow) -> list[str]:
    """Each step's need that neither the start materials nor an earlier step gives, and each end
    artifact no step makes."""
    available = set(workflow.start_materials)
    gap_lines = []
    for step in workflow.steps:
        for need in step.needs:
            if need not in available:
                gap_lines.append(f"{workflow.name}: {step.name!r} needs {need!r}, which "
                                 "nothing gives")
        available |= set(step.makes)
    for artifact in workflow.end_artifacts:
        if artifact not in available:
            gap_lines.append(f"{workflow.name}: no step makes {artifact!r}")
    return gap_lines


def diagram(workflow: Workflow, with_calls: bool = True) -> list[str]:
    """A Workflow as a Mermaid flowchart's lines: each thing a node, each step a node of its
    kind, named with its call `with_calls`, an arrow from each thing a step needs and to each
    thing it makes."""
    things: dict[str, str] = {}

    def thing_id(text: str) -> str:
        if text not in things:
            things[text] = f"t{len(things)}"
        return things[text]

    nodes, edges = [], []
    for number, step in enumerate(workflow.steps):
        opening, closing, kind_class, _ = DRAWN[step.kind]
        step_id = f"s{number}"
        text = f"{number + 1}. {step.name}"
        if step.call and with_calls:
            text += f": {step.call}"
        nodes.append(f"    {step_id}{opening}{label(text)}{closing}:::{kind_class}")
        edges += [f"    {thing_id(need)} --> {step_id}" for need in step.needs]
        edges += [f"    {step_id} --> {thing_id(made)}" for made in step.makes]
    things_drawn = [f"    {thing}({label(text)}):::thing" for text, thing in things.items()]
    kinds = {step.kind for step in workflow.steps}
    styles = [f"    classDef {DRAWN[kind][2]} {DRAWN[kind][3]}"
              for kind in KINDS if kind in kinds]
    return ["```mermaid", "flowchart TD", *nodes, *things_drawn, *edges, *styles, THING_STYLE,
            "```"]


def section(workflow: Workflow) -> list[str]:
    """One Workflow's part of the page: its counts, its start and end, and its diagram."""
    counted = kind_counts(workflow)
    counts = ", ".join(f"{counted[kind]} {kind}" for kind in KINDS)
    return [f"## {workflow.name}", "",
            f"Steps: {counts}.", "",
            f"Starts from: {', '.join(workflow.start_materials)}.", "",
            f"Ends with: {', '.join(workflow.end_artifacts)}.", "",
            *diagram(workflow), ""]


def page_text() -> str:
    """docs/workflows.md, as this writes it."""
    lines = [HEADING]
    for workflow in workflows.WORKFLOWS:
        lines += section(workflow)
    return "\n".join(lines)


def main() -> int:
    """Write the page, unless it holds what this writes already; stop, writing nothing, on a
    gap."""
    gap_lines = []
    for workflow in workflows.WORKFLOWS:
        gap_lines += gaps(workflow)
        counted = kind_counts(workflow)
        print(f"{workflow.name}: {counted[workflows.FIDDLING]} fiddling of "
              f"{len(workflow.steps)} steps")
    for gap in gap_lines:
        print(f"Gap: {gap}")
    if gap_lines:
        return 1
    readme = README.read_text(encoding="utf-8")
    for path, text in ((PAGE, page_text()), (README, with_charts(readme)),
                       (HOW_TO, how_to_text())):
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8", newline="\n")
            print(f"Wrote {path.relative_to(ROOT).as_posix()}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

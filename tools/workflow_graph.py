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
# What a Workflow notebook's first cell holds under its imports, since Toolbox 8.6.
CONNECT_SAID = ("Under the imports, the same cell has a line connect(...), for your connection "
                "to the warehouse: each notebook runs on its own, so each connects at its top. "
                "Write yours in it, such as connect(your_library.connect(...)), and delete its "
                "#; until you do, query and execute refuse.")
# What each shape of a chart is, as a page says it under its charts.
LEGEND = ("In each chart, a plain box is a step that changes only files, or only prints; a "
          "box with double edges a call to the warehouse, yours to run; a diamond a decision, "
          "yours to make; and a box with round corners something a step needs or makes.")
THING_STYLE = "    classDef thing fill:#ffffff,stroke:#888888"
HEADING = """# Workflows

What a Project goes through to reach each end goal, drawn from `sqlglot_composer/workflows.py`
by `tools/workflow_graph.py`. **To change this page, change `workflows.py` and run the tool,
which writes the page again.**

## Terms

- **Workflow**: an ordered list of steps that takes a Project from its start materials, what
  the user brings, to one end goal.
- **Start materials** ("Starts from"): what the first steps need. **End artifacts** ("Ends
  with"): what the last steps make.
- A box with round corners is something a step needs or makes.
- Each step is drawn by its kind:
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
    copilot{{"Copilot, given files 15, 11 and 12: the workbook as Hive"}}
    scripts("its Hive, each name in angle brackets filled in, saved as .hql files")
    convert["the convert Workflow: project.convert(NAME, files=FILES), one batch"]
    dev[["each table created, seeded and written in dev"]]
    compare[["project.compare_batch: each against its query"]]
    promote["project.promote: each copied to prod"]
    prod[["each created and written in prod"]]
    workbook --> copilot --> scripts --> convert --> dev --> compare --> promote --> prod""",
              [("Fill in a Formula workbook, laid out as copilot/formula_workbook.xlsx is", ""),
               ("Give Copilot files 15, 11 and 12 with the workbook: it writes the workbook as "
                "Hive, a query for each final Table", ""),
               ("Fill in each name it writes in angle brackets, save each query as a .hql "
                "file named for its final Table, and convert them as one batch in the convert "
                "Workflow, DEV filled in: each becomes a Saved table named for its file, or, "
                "when the batch is one file, for the batch",
                'project.convert("budget", files=["sales.hql", "regions.hql"], query=query)'),
               ("Answer each table's Decisions, then create, seed and write each in dev, as "
                "the Workflow's steps say", ""),
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
    """How-to 29, which this writes whole: its numbered steps, then each Workflow's chart,
    names cell and steps, as the Workflow notebook it starts from runs them."""
    lines = [*_how_to_head(), *_how_to_steps()]
    for workflow in workflows.WORKFLOWS:
        lines += _how_to_section(workflow)
    lines += [
        "## Check it worked", "",
        "Before you go on, check that:", "",
        *_wrapped("- `project.check()` names the next step of each Workflow you have started, "
                  "or says that every step is done;", "  "),
        *_wrapped("- `project.check()` names no open Decision for the tables of the Workflow "
                  "you ran.", "  "), "",
        "## Common mistakes", "",
        "### A step named again after you ran it", "",
        *_wrapped("`project.check()` names a step no file tells of, such as "
                  "change_a_saved_table's \"Print its Hive\", until a later step is done, and "
                  "says so: once you have run it, go on to the next step. A step that only "
                  "reads, such as new_table's preview, is never named on its own: check() "
                  "names it beside the step after it."), "",
        "## Next", "",
        *_wrapped("- Walk the convert Workflow through a batch of scripts: "
                  "[Convert someone else's Hive](#convert_someone_elses_hive).", "  ")]
    # A docstring holds no three quotes of its own: the page reads each escaped one as one.
    body = "\n".join(lines[1:]).replace('"""', '\\"\\"\\"')
    return f"{lines[0]}\n{body}\n" + '"""\n'


def _wrapped(text: str, indent: str = "") -> list[str]:
    """A paragraph, or a list item continued at `indent`, wrapped as a how-to's prose is."""
    return textwrap.wrap(text, width=96, subsequent_indent=indent, break_long_words=False,
                         break_on_hyphens=False)


def _how_to_head() -> list[str]:
    """How-to 29's title, group, Goal and When you'd use it."""
    return [
        '"""Follow a Workflow', "", "For: Intermediate", "", "## Goal", "",
        *_wrapped("Do a whole job from its Workflow notebook, step by step, with nothing "
                  "typed twice. A Workflow is an ordered list of steps that takes a Project, "
                  "your folder of scripts at work, from what you bring to one end goal, such "
                  "as converting scripts or promoting tables. Each Workflow has a notebook in "
                  "admin/workflows/, a folder for each, and each Workflow below is drawn and "
                  "listed from the steps its notebook runs. A Decision is one thing about one "
                  "table that only you decide, such as its location or its Key, the columns "
                  "whose values name exactly one row."), "",
        "## When you'd use it", "",
        *_wrapped("- If you start one of the jobs below, follow its Workflow's notebook, as "
                  "the steps below do.", "  "),
        *_wrapped("- If you don't know which step of a Workflow comes next, run "
                  "`project.check()`: it names the next step of each Workflow you have "
                  "started.", "  "),
        *_wrapped("- If you want every step left run for you, run `project.run_workflow(...)` "
                  "in place of the steps' cells: in convert, promote, new_table and "
                  "references, the two cells under the names cell, \"Run up to your "
                  "Decisions\" and then, under the decisions cell, \"Run the rest\": one "
                  "call, run once before you answer and once after; in the "
                  "others, the notebook's last cell. It runs every step left, the calls to "
                  "the warehouse too, up to the first only you can do: a Decision, a check "
                  "of what a step printed, or a refusal to mend. Run after you answer, it "
                  "goes on and can stop again the same way.", "  "),
        *_wrapped("- If you haven't sent anything yet, run `project.run_workflow(...)` with "
                  "`dry_run=True` first: it sends nothing through your execute and says the "
                  "Hive each step would send. It runs for real convert and the references "
                  "Workflow's first step, which read DESCRIBE, and each step that changes "
                  "only files up to the first that would send; after that it names each such "
                  "step, \"would run: ...\", and runs none.", "  "),
        *_wrapped("- If you want only the steps that change files run, run "
                  "`project.do_next()`.", "  "),
        *_wrapped("- If you have no Project yet, do [Start a Project](#start_a_project) "
                  "first.", "  "), ""]


def _workflow_choices() -> list[str]:
    """One "- If ..." line for each Workflow: what it does, and its notebook."""
    lines = []
    for workflow in workflows.WORKFLOWS:
        lines += _wrapped(f"- If you want a Workflow that {_about_first_clause(workflow)}, "
                          f"choose {workflow.name}: "
                          f"admin/workflows/{workflow.name}/{workflow.name}.ipynb.", "  ")
    return lines


def _how_to_steps() -> list[str]:
    """How-to 29's numbered steps, the first of which starts a Project and the third shows the
    imports each Workflow notebook starts with."""
    return [
        "## Steps", "",
        "### 1. Start a Project", "",
        *_wrapped("Goal: a Project whose admin/workflows/ folder holds a notebook for each "
                  "Workflow, each waiting for its names cell:"), "",
        ">>> from sqlglot_composer import project",
        ">>> project.start()",
        "Started a Project in the folder you're working in: admin/, references/, "
        "building_blocks/,",
        "tables/, scheduled_runs/ and warehouse.py.",
        "Next: at the top of each notebook, fill in connect(...) with your connection.", "",
        "Done when `project.start()` says it started a Project. Then step 2.", "",
        "### 2. Choose the Workflow for your job", "",
        *_wrapped("Goal: the one Workflow whose end goal is yours. Each Workflow is described "
                  "after these steps, with its chart, its names cell and its steps."), "",
        *_workflow_choices(), "",
        *textwrap.wrap(LEGEND, width=96), "",
        "Done when you know the notebook to open. Then step 3.", "",
        "### 3. Open its notebook", "",
        *_wrapped("Goal: the notebook whose cells run your job's steps. Each Workflow "
                  "notebook starts by finding the Project, then imports what its steps "
                  "call:"), "",
        *[f"    {line}" for line in _imports_wrapped()], "",
        *_wrapped(CONNECT_SAID), "",
        "Done when its first cells run without an error. Then step 4.", "",
        "### 4. Fill in its names cell, and save it", "",
        *_wrapped("Goal: the start materials the Workflow works on, named once. Write each "
                  "name its names cell asks for, as its Workflow's section below shows, and "
                  "save the notebook."), "",
        "Done when each name the cell asks for is filled in and saved. Then step 5.", "",
        "### 5. Run its steps in order", "",
        *_wrapped("Goal: the Workflow's end goal reached. Run its run cells, as its "
                  "Workflow's section below shows them, or each step's cell in turn in their "
                  "place. At a step that is a decision, yours to make, make it: write your "
                  "answer to each open Decision in the decisions cell and save it, or read "
                  "what the step before printed. Then run on."), "",
        *_wrapped("An answer is what its kind takes, as the decisions cell's comment shows: a "
                  "folder as text, a Key as a list, a Script tag's day as Hive text. A tag may "
                  "be answered by a Run value's function instead, one of your Project's, "
                  "imported at the top of the decisions cell and given by its name, which the "
                  "Toolbox calls each time the table is written. \"all_tables\" answers once "
                  "for every table the notebook names, and "
                  "a table's own answer overwrites it. A table that reads itself is seeded "
                  "once from its original, every Partition unless its \"seed\" answer limits "
                  "them. [Convert someone else's Hive](#convert_someone_elses_hive) shows each "
                  "one."), "",
        *_wrapped("Done when `project.check()` says every step of the Workflow is done. Then "
                  "check it worked, below."), "",
        "The Workflows, for steps 2 to 5:", ""]


def _about_first_clause(workflow: Workflow) -> str:
    """What a Workflow does, up to its first colon, as words that follow "a Workflow that"."""
    first_clause = workflow.about.split(":")[0].rstrip(".")
    return first_clause[0].lower() + first_clause[1:]


def _how_to_section(workflow: Workflow) -> list[str]:
    """One Workflow's part of how-to 29: what it does, its chart, its names cell, and its
    steps, numbered, each its kind in words and its call."""
    lines = [f"### The {workflow.name} Workflow", "",
             *_wrapped(workflow.about), "",
             *_wrapped("Its chart, drawn from the steps of its notebook, "
                       f"admin/workflows/{workflow.name}/{workflow.name}.ipynb:"), "",
             *diagram(workflow, with_calls=False)]
    if workflow.inputs:
        lines += ["", "Its names cell, which you fill in and save first:", ""]
        for given in workflow.inputs:
            lines += textwrap.wrap(given.about, width=88, initial_indent="    # ",
                                   subsequent_indent="    # ", break_long_words=False,
                                   break_on_hyphens=False)
            lines.append(f"    {given.name} = {given.empty!r}")
    if workflows.reads_straight_down(workflow):
        lines += _intended_path_lines(workflow)
    elif any(step.decides for step in workflow.steps):
        lines += ["", "Its decisions cell, beside it, where you answer each open Decision:",
                  "", *[f"    {line}" for line in workflows.DECISIONS_CELL.split("\n")]]
    lines += ["", "Its steps' own cells, in order:", ""]
    for number, step in enumerate(workflow.steps, 1):
        lines += _wrapped(f"{number}. {step.name} (it {workflows.step_said(workflow, step)}).",
                          "   ")
        if step.call:
            lines += ["", *[f"    {line}" for line in step.call.split("\n")], ""]
    if not workflows.reads_straight_down(workflow):
        lines += ["", "Its last cell runs every step left, in place of their cells:", "",
                  *[f"    {line}" for line in workflows.run_cell_text(workflow).split("\n")]]
    return [*lines, ""]


def _intended_path_lines(workflow: Workflow) -> list[str]:
    """A notebook's intended path, under its names cell, as how-to 29 shows it: its run of
    every step up to the Decisions, its decisions cell, and its run of the rest (8.5)."""
    up_to = workflows.run_cell_text(workflow, workflows.RUN_UP_TO_DECISIONS)
    the_rest = workflows.run_cell_text(workflow, workflows.RUN_THE_REST)
    return ["", *_wrapped(f'Under it, "{workflows.RUN_UP_TO_DECISIONS}", which runs every step '
                          "left up to the first only you can do, and prints the DECISIONS to "
                          "paste:"), "",
            *[f"    {line}" for line in up_to.split("\n")], "",
            "Its decisions cell, under that, where you answer each open Decision:", "",
            *[f"    {line}" for line in workflows.DECISIONS_CELL.split("\n")], "",
            *_wrapped(f'And "{workflows.RUN_THE_REST}", the same call as '
                      f'"{workflows.RUN_UP_TO_DECISIONS}", run again once you have answered: '
                      "it goes on from where the first stopped, and it too stops at the first "
                      "step only you can do, so it can stop again, at a refusal, a compare "
                      "that failed or a Decision left open. Mend what it names and run it "
                      "again. Each step's own cell follows, under Step by step:"), "",
            *[f"    {line}" for line in the_rest.split("\n")]]


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

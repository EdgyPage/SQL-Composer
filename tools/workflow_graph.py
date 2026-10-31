"""Draw each Workflow (`sqlglot_composer/workflows.py`) as a graph, and count its hand steps.

Run it on `dev` after changing a Workflow's steps:

    python tools/workflow_graph.py

It writes `docs/workflows.md`: for each Workflow, a Mermaid diagram of its start materials, its
steps and what each makes, and how many steps of each kind it has. A fiddling step, a step done
by hand though the code knows the answer, is drawn in red. It stops with a list of each gap: a
step that needs what neither the start materials nor an earlier step gives, or an end artifact
no step makes. A test holds the page to what this writes, and each Workflow's fiddling to at
most its count when Toolbox 8.0 began.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs" / "workflows.md"
sys.path.insert(0, str(ROOT))

from sqlglot_composer import workflows  # noqa: E402
from sqlglot_composer.workflows import KINDS, Workflow  # noqa: E402

# How a step of each kind is drawn: its node's brackets, and its class.
SHAPES = {workflows.FILE_STEP: ("[", "]"), workflows.PERMISSION: ("[[", "]]"),
          workflows.DECISION: ("{", "}"), workflows.FIDDLING: (">", "]")}
CLASSES = {workflows.FILE_STEP: "file", workflows.PERMISSION: "permission",
           workflows.DECISION: "decision", workflows.FIDDLING: "fiddling"}
STYLES = ("    classDef file fill:#e3f2e1,stroke:#4a8a3f",
          "    classDef permission fill:#e1ecf7,stroke:#3f6a9a",
          "    classDef decision fill:#fbf1d6,stroke:#a8842a",
          "    classDef fiddling fill:#f8d7d5,stroke:#b03a30",
          "    classDef thing fill:#ffffff,stroke:#888888")
HEADING = """# Workflows

What a Project goes through to reach each end goal, drawn from `sqlglot_composer/workflows.py`
by `tools/workflow_graph.py`: don't edit this page, run the tool. Each box with round corners is
something a step needs or makes; each step is drawn by its kind:

- a **file step** (green), a Project action that changes only files;
- a **permission** (blue, double-edged), a call to the Warehouse the user makes on purpose;
- a **decision** (yellow, a diamond), which needs the user's judgement;
- **fiddling** (red, a flag), a step done by hand though the code knows the answer.

Toolbox 8.0 takes each Workflow's fiddling to nothing.
"""


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
    had = set(workflow.start_materials)
    found = []
    for step in workflow.steps:
        for need in step.needs:
            if need not in had:
                found.append(f"{workflow.name}: {step.name!r} needs {need!r}, which nothing "
                             "gives")
        had |= set(step.makes)
    for artifact in workflow.end_artifacts:
        if artifact not in had:
            found.append(f"{workflow.name}: no step makes {artifact!r}")
    return found


def diagram(workflow: Workflow) -> list[str]:
    """A Workflow as a Mermaid flowchart's lines: each thing a node, each step a node of its
    kind, an arrow from each thing a step needs and to each thing it makes."""
    things: dict[str, str] = {}

    def thing_id(text: str) -> str:
        if text not in things:
            things[text] = f"t{len(things)}"
        return things[text]

    lines = ["```mermaid", "flowchart TD"]
    for number, step in enumerate(workflow.steps):
        opening, closing = SHAPES[step.kind]
        step_id = f"s{number}"
        lines.append(f"    {step_id}{opening}{label(f'{number + 1}. {step.name}')}{closing}")
        lines.append(f"    class {step_id} {CLASSES[step.kind]}")
        for need in step.needs:
            lines.append(f"    {thing_id(need)} --> {step_id}")
        for made in step.makes:
            lines.append(f"    {step_id} --> {thing_id(made)}")
    for text, thing in things.items():
        lines.append(f"    {thing}({label(text)})")
        lines.append(f"    class {thing} thing")
    return [*lines, *STYLES, "```"]


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
    """Write the page, unless it holds what this writes already; stop on a gap."""
    found = []
    for workflow in workflows.WORKFLOWS:
        found += gaps(workflow)
        counted = kind_counts(workflow)
        print(f"{workflow.name}: {counted[workflows.FIDDLING]} fiddling of "
              f"{len(workflow.steps)} steps")
    for gap in found:
        print(f"Gap: {gap}")
    text = page_text()
    if not PAGE.exists() or PAGE.read_text(encoding="utf-8") != text:
        PAGE.write_text(text, encoding="utf-8")
        print(f"Wrote {PAGE.relative_to(ROOT).as_posix()}.")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())

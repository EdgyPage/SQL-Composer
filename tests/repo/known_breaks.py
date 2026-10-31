"""Each break of the standard (docs/agents/standards.md) known when Toolbox 8.0's ticket 01
turned its rules on, by file and rule: a ruff code, or a tree rule test_standard.py reads.

The counts may only fall. Toolbox 8.0's phase 2, the refactor, empties the list; a file it
brings to the standard leaves it. Written by hand, never regenerated to let a break in.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

# The rules test_standard.py reads from the code tree; every other key below is a ruff code.
TREE_RULES = frozenset({"long body", "chained conditional", "next with a default",
                        "dense comprehension", "walrus", "lambda", "private name twice"})

KNOWN_BREAKS: dict[str, dict[str, int]] = {
    "sqlglot_composer/__init__.py": {"private name twice": 1},
    "sqlglot_composer/admin.py": {
        "E501": 11, "dense comprehension": 2, "lambda": 1, "private name twice": 3},
    "sqlglot_composer/calculations.py": {
        "E501": 9, "next with a default": 3, "private name twice": 1, "walrus": 2},
    "sqlglot_composer/checks.py": {"E501": 1, "long body": 1, "next with a default": 1},
    "sqlglot_composer/clauses.py": {
        "E501": 5, "dense comprehension": 2, "private name twice": 2},
    "sqlglot_composer/conditions.py": {"lambda": 2},
    "sqlglot_composer/converting.py": {
        "E501": 24, "PLR0911": 1, "chained conditional": 3, "dense comprehension": 3,
        "lambda": 4, "private name twice": 3},
    "sqlglot_composer/describe.py": {"E501": 3},
    "sqlglot_composer/engine.py": {
        "E501": 10, "chained conditional": 2, "dense comprehension": 4,
        "private name twice": 4},
    "sqlglot_composer/joins.py": {"E501": 3, "next with a default": 1},
    "sqlglot_composer/keys.py": {
        "E501": 3, "PLR0911": 1, "dense comprehension": 1, "lambda": 2,
        "next with a default": 1, "private name twice": 1},
    "sqlglot_composer/notebooks.py": {"private name twice": 1},
    "sqlglot_composer/project.py": {
        "E501": 35, "dense comprehension": 3, "lambda": 1, "long body": 5,
        "next with a default": 3, "private name twice": 3},
    "sqlglot_composer/project_templates.py": {"E501": 4},
    "sqlglot_composer/python_steps.py": {"E501": 2, "private name twice": 1},
    "sqlglot_composer/refusals.py": {"E501": 14, "private name twice": 1},
    "sqlglot_composer/stacking.py": {
        "E501": 3, "dense comprehension": 6, "next with a default": 2},
    "sqlglot_composer/tables.py": {
        "E501": 18, "chained conditional": 3, "dense comprehension": 1, "long body": 3,
        "next with a default": 2, "private name twice": 2},
    "sqlglot_composer/trees.py": {
        "E501": 5, "PLR0911": 1, "dense comprehension": 2, "lambda": 1,
        "private name twice": 1},
    "sqlglot_composer/unchecked.py": {
        "E501": 8, "lambda": 1, "next with a default": 2, "private name twice": 2},
    "sqlglot_composer/upgrades.py": {"E501": 7},
    "sqlglot_composer/upkeep.py": {"E501": 5},
    "sqlglot_composer/windows.py": {"E501": 8, "private name twice": 2},
    "sqlglot_composer/writing.py": {
        "E501": 9, "dense comprehension": 2, "lambda": 23, "private name twice": 5},
}



def is_tree_rule(rule: str) -> bool:
    """Whether a rule is one test_standard.py reads from the code tree."""
    return rule in TREE_RULES


def is_ruff_code(rule: str) -> bool:
    """Whether a rule is ruff's, the rules test_toolbox_checks.py runs ruff for."""
    return rule not in TREE_RULES


def counts_of_rules(breaks: Mapping[str, Mapping[str, int]], is_kind: Callable[[str], bool]
                    ) -> dict[str, dict[str, int]]:
    """`breaks`, by file, with only the rules `is_kind` picks."""
    picked: dict[str, dict[str, int]] = {}
    for path, rules in breaks.items():
        for rule, count in rules.items():
            if is_kind(rule):
                picked.setdefault(path, {})[rule] = count
    return picked


def rose_and_fell(found: Mapping[str, Mapping[str, int]], is_kind: Callable[[str], bool]
                  ) -> tuple[list[str], list[str]]:
    """Each count of the rules `is_kind` picks that rose above the list, and each that fell
    below it: one line per file and rule."""
    now_of, known_of = counts_of_rules(found, is_kind), counts_of_rules(KNOWN_BREAKS, is_kind)
    rose, fell = [], []
    for path in sorted(set(now_of) | set(known_of)):
        now, known = now_of.get(path, {}), known_of.get(path, {})
        for rule in sorted(set(now) | set(known)):
            was, is_now = known.get(rule, 0), now.get(rule, 0)
            if is_now > was:
                rose.append(f"{path}: {rule}, {was} known, {is_now} now")
            elif is_now < was:
                fell.append(f"{path}: {rule}, {was} known, {is_now} now")
    return rose, fell

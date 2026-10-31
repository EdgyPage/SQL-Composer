"""Each break of the standard (docs/agents/standards.md) known when Toolbox 8.0's ticket 01
turned its rules on, by file and rule: a ruff code, or a tree rule test_standard.py reads.

The counts could only fall, and Toolbox 8.0's phase 2, the refactor, emptied the list: the
Toolbox, tools/, tests/ and the Worked examples now break no rule a test holds, so any break
fails. An entry is never added to let one in.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

# The rules test_standard.py reads from the code tree; every other key below is a ruff code.
TREE_RULES = frozenset({"long body", "chained conditional", "next with a default",
                        "dense comprehension", "walrus", "lambda", "private name twice"})

KNOWN_BREAKS: dict[str, dict[str, int]] = {

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

"""The standard's rules a test can hold, read from the code tree (docs/agents/standards.md;
Toolbox 8.0, ticket 01). ruff holds the rest, as pyproject.toml selects them, and
test_toolbox_checks.py runs it.

- a function's body is at most 50 lines, its docstring left out;
- no conditional expression holds another;
- no `next(...)` with a default: a plain loop, or a named function;
- a comprehension has one `for`, at most one `if`, and no comprehension inside it;
- no walrus;
- a lambda only as a `key=`;
- a private function or class at a Toolbox file's top has a name no other Toolbox file's
  top uses.

Each break known when the rules were turned on is in known_breaks.py, by file and rule, and the
count there may only fall: a new break fails, and so does a count that fell and wasn't lowered.
"""

from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

import toolbox_registry
from known_breaks import TREE_RULES, is_tree_rule, rose_and_fell

ROOT = Path(__file__).resolve().parents[2]
# What the tree rules read: the Toolbox and its tools.
READ = (toolbox_registry.FOLDER, "tools")
LONGEST_BODY = 50
COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


def body_lines(function: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """How many lines a function's body takes, its docstring left out."""
    body = function.body
    if ast.get_docstring(function) is not None:
        body = body[1:]
    if not body:
        return 0
    return body[-1].end_lineno - body[0].lineno + 1


def has_a_comprehension(node: ast.AST) -> bool:
    """Whether a part of a comprehension, or a part of that, is a comprehension itself."""
    return any(isinstance(part, COMPREHENSIONS) for part in ast.walk(node))


def comprehension_parts(node: ast.AST) -> list[ast.AST]:
    """What a comprehension is made of: its element (a dict's key and value), and its one
    loop's iterable and conditions."""
    parts = [node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]
    for generator in node.generators:
        parts += [generator.iter, *generator.ifs]
    return parts


def is_dense_comprehension(node: ast.AST) -> bool:
    """Whether a comprehension has two `for`s, two `if`s on one, or a comprehension inside."""
    if len(node.generators) > 1:
        return True
    if any(len(generator.ifs) > 1 for generator in node.generators):
        return True
    return any(has_a_comprehension(part) for part in comprehension_parts(node))


def is_chained_conditional(node: ast.AST) -> bool:
    """Whether a conditional expression holds another, in any of its three parts."""
    inner = []
    for part in (node.test, node.body, node.orelse):
        inner += list(ast.walk(part))
    return any(isinstance(part, ast.IfExp) for part in inner)


def is_long_function(node: ast.AST) -> bool:
    """Whether a function's body, its docstring left out, is longer than the standard allows."""
    return body_lines(node) > LONGEST_BODY


def is_next_with_a_default(node: ast.AST) -> bool:
    """Whether a call is `next(...)` given a default."""
    return isinstance(node.func, ast.Name) and node.func.id == "next" and len(node.args) == 2


# Each tree rule but the walrus's and the lambda's, which every one of its nodes breaks: the
# nodes it reads, and the test that finds a break.
CHECKS = (
    ((ast.FunctionDef, ast.AsyncFunctionDef), "long body", is_long_function),
    ((ast.IfExp,), "chained conditional", is_chained_conditional),
    ((ast.Call,), "next with a default", is_next_with_a_default),
    (COMPREHENSIONS, "dense comprehension", is_dense_comprehension),
)


def key_lambdas(tree: ast.AST) -> set[ast.Lambda]:
    """Every lambda given as a `key=`, the one place a lambda may stand."""
    allowed = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "key" and isinstance(node.value,
                                                                            ast.Lambda):
            allowed.add(node.value)
    return allowed


def tree_breaks(tree: ast.AST) -> Counter[str]:
    """Each tree rule a module breaks, and how many times."""
    found: Counter[str] = Counter()
    allowed = key_lambdas(tree)
    for node in ast.walk(tree):
        for kinds, rule, breaks in CHECKS:
            if isinstance(node, kinds) and breaks(node):
                found[rule] += 1
        if isinstance(node, ast.NamedExpr):
            found["walrus"] += 1
        if isinstance(node, ast.Lambda) and node not in allowed:
            found["lambda"] += 1
    return found


DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def private_functions(tree: ast.Module) -> list[str]:
    """The module's own private functions and classes: those at its top whose names start
    with one `_`."""
    names = []
    for node in tree.body:
        if not isinstance(node, DEFINITIONS):
            continue
        if node.name.startswith("_") and not node.name.startswith("__"):
            names.append(node.name)
    return names


def repo_path(path: Path) -> str:
    """A path as known_breaks.py names it: from the repo's top, with forward slashes."""
    return path.relative_to(ROOT).as_posix()


def private_names_twice(trees: dict[Path, ast.Module]) -> Counter[str]:
    """For each Toolbox file, how many of its private names another Toolbox file defines."""
    toolbox = ROOT / toolbox_registry.FOLDER
    files_of: dict[str, list[Path]] = {}
    for path, tree in trees.items():
        if path.parent == toolbox:
            for name in private_functions(tree):
                files_of.setdefault(name, []).append(path)
    twice: Counter[str] = Counter()
    for paths in files_of.values():
        if len(paths) > 1:
            for path in paths:
                twice[repo_path(path)] += 1
    return twice


def every_tree_break() -> dict[str, Counter[str]]:
    """Every break of the tree rules, by file and rule."""
    trees = {}
    for folder in READ:
        for path in sorted((ROOT / folder).rglob("*.py")):
            trees[path] = ast.parse(path.read_text(encoding="utf-8"))
    found: dict[str, Counter[str]] = {}
    for path, tree in trees.items():
        counted = tree_breaks(tree)
        if counted:
            found[repo_path(path)] = counted
    for path, count in private_names_twice(trees).items():
        found.setdefault(path, Counter())["private name twice"] += count
    return found


def test_the_tree_rules_hold_but_for_the_known_breaks_which_only_shrink() -> None:
    rose, fell = rose_and_fell(every_tree_break(), is_tree_rule)
    assert rose == [], ("Breaks of docs/agents/standards.md the list doesn't know:\n"
                        + "\n".join(rose))
    assert fell == [], ("Fixed: lower each in tests/repo/known_breaks.py, so the break can't "
                        "come back:\n" + "\n".join(fell))


def test_each_tree_rule_finds_what_it_is_for() -> None:
    source = ('def long():\n    """A docstring."""\n' + "    x = 1\n" * 51 +
              "a = 1 if b else 2 if c else 3\n"
              "d = next(iter(e), None)\n"
              "f = [g for h in i for g in h]\n"
              "j = {k: [l for l in k] for k in m}\n"
              "if (n := 1):\n    pass\n"
              "o = lambda p: p\n"
              "q = sorted(r, key=lambda s: s)\n")
    assert tree_breaks(ast.parse(source)) == Counter({
        "long body": 1, "chained conditional": 1, "next with a default": 1,
        "dense comprehension": 2, "walrus": 1, "lambda": 1})
    assert set(tree_breaks(ast.parse(source))) <= TREE_RULES

"""What the Toolbox and tools/ define is used: no dead name, no private name reached across files
but the few listed, and every keyword of a public function passed somewhere.

A use is read with ast, never by running anything: a name or attribute in code, a string that
is exactly the name (getattr, mock.patch.object, __all__), a name in a doctest example, in a
docstring or in docs/clean-branch-readme.md, and a name in any other string of several lines,
which is how the Templates and the admin notebooks hold their code. A file's own uses count
only from its code and its exact strings, so a name its own docstring mentions isn't kept
alive by that.
"""

from __future__ import annotations

import ast
import doctest
import inspect
import re
from collections.abc import Callable, Iterator
from pathlib import Path

import sqlglot_composer
from sqlglot_composer import admin, project

ROOT = Path(__file__).resolve().parents[2]
TOOLBOX = ROOT / "sqlglot_composer"
# Folders no use is read from: a virtual environment, the tracker, generated Example projects
# (tools/example_project_sources/ is read instead) and old worktrees.
LEFT_OUT = {".venv", ".scratch", ".claude", "__pycache__", "example_projects", ".git"}
IDENTIFIER = re.compile(r"[A-Za-z_]\w*")
PRIVATE_CONSTANT = re.compile(r"_[A-Z][A-Z0-9_]*")
EXAMPLES = doctest.DocTestParser()

# Names a file defines for something other than code to read: the version check reads
# TOOLBOX_VERSION by its text, and Python reads __all__.
READ_BY_NAME = {"TOOLBOX_VERSION", "__all__"}

# Defined and used nowhere, each to go with ticket 16 of .scratch/toolbox-7/map.md. The test
# fails on a name missing from here, and on a name here that is used again or gone.
KNOWN_DEAD = {
    ("sqlglot_composer/tables.py", "DATE_FORMAT"),
    ("tools/hive_corpus.py", "cases_in"),
}

# Private names one file reaches in another, each for a reason. A new one fails the test;
# so does one listed here that no file reaches any more.
TICKET_16 = "used across Toolbox files: ticket 16 takes its underscore off"
ONE_CLOCK = "patched to pin the time: ticket 16 makes it one clock, patched once"
PRIVATE_SEAMS = {
    # Tests and tools reach these on purpose.
    ("checks", "_PAGES"): "the self-check's pages, which its test names",
    ("engine", "_LOWEST"): "sqlglot's range, which the version test holds the pin inside",
    ("engine", "_BELOW"): "sqlglot's range, which the version test holds the pin inside",
    ("engine", "_NEWEST_TESTED"): "the pin the version test compares",
    ("example_database", "_TABLES"): "the Example database's tables, which tests describe",
    ("example_database", "_is_query"): "tested on its own, as the query refusal's rule",
    ("example_database", "_sorts_itself"): "tested on its own, as the sort rule",
    ("running", "_self_check"): "swapped out by a test to show nothing unchecked is sent",
    ("tables", "_SET_IT"): "a fix text a test checks against the admin module",
    ("unchecked", "_ALTERED_BY"): "fix texts a test checks against the admin module",
    ("writing", "_REPLAY"): "the replay table a sqlglot check reads",
    ("writing", "_writes_struct_colons"): "swapped by a sqlglot check for an old sqlglot",
    ("lineage", "_version"): "pinned by the page tools so pages don't name a dev version",
    ("lineage", "_now"): ONE_CLOCK,
    ("project", "_now"): ONE_CLOCK,
    ("unchecked", "_now"): ONE_CLOCK,
    ("calculations", "_need_column"): TICKET_16,
    ("clauses", "_flatten"): TICKET_16,
    ("clauses", "_matched_columns"): TICKET_16,
    ("clauses", "_resolve_group_by"): TICKET_16,
    ("engine", "_INSTALL_NEWER"): TICKET_16,
    ("running", "_need_statement"): TICKET_16,
    ("running", "_statement_tree"): TICKET_16,
    ("unchecked", "_code"): TICKET_16,
    ("unchecked", "_script_line"): TICKET_16,
    ("unchecked", "_write_entry"): TICKET_16,
}

# Keywords of a public function nothing passes yet: each wants a test (ticket 16).
UNTESTED_KEYWORDS = {
    ("ANTI_JOIN", "reads_all_partitions"),
    ("CROSS_JOIN", "reads_all_partitions"),
    ("SEMI_JOIN", "reads_all_partitions"),
    ("FULL_JOIN", "many_matches"),
    ("INSERT_INTO", "unproven_key"),
    ("UNION", "returns_all_rows"),
    ("INTERSECT", "returns_all_rows"),
    ("EXCEPT", "returns_all_rows"),
    ("average_of", "adds_up"),
    ("min_of", "where"),
}


def _python_files() -> list[Path]:
    """Every .py file a use is read from, but this one, whose lists name what they list."""
    return sorted(path for path in ROOT.rglob("*.py")
                  if not LEFT_OUT & set(path.relative_to(ROOT).parts)
                  and path != Path(__file__).resolve())


def _docstrings(tree: ast.Module) -> set[int]:
    """The ids of the string constants that are docstrings."""
    found = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if (isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            found.add(id(body[0].value))
    return found


def _code_names(tree: ast.AST) -> Iterator[str]:
    """Each name code reads: a name, an attribute, a name imported."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            yield node.id
        elif isinstance(node, ast.Attribute):
            yield node.attr
        elif isinstance(node, ast.ImportFrom):
            yield from (alias.name for alias in node.names)


def _example_trees(text: str) -> Iterator[ast.Module]:
    """Each doctest example in `text` that is Python, parsed."""
    for example in EXAMPLES.get_examples(text):
        try:
            yield ast.parse(example.source)
        except SyntaxError:
            continue


def _strings(tree: ast.Module) -> Iterator[ast.Constant]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node


def _uses(tree: ast.Module) -> tuple[set[str], set[str]]:
    """The names a file uses: from its code and exact strings, and from all of it."""
    docs = _docstrings(tree)
    own = set(_code_names(tree))
    own |= {node.value for node in _strings(tree) if IDENTIFIER.fullmatch(node.value)}
    every = set(own)
    for node in _strings(tree):
        if ">>>" in node.value:
            every |= {name for example in _example_trees(node.value)
                      for name in _code_names(example)}
        elif "\n" in node.value and id(node) not in docs:
            every |= set(IDENTIFIER.findall(node.value))
    return own, every


README = ROOT / "docs" / "clean-branch-readme.md"
TREES = {path: ast.parse(path.read_text(encoding="utf-8")) for path in _python_files()}
OWN, EVERY = {}, {}
for _path, _tree in TREES.items():
    OWN[_path], EVERY[_path] = _uses(_tree)
_readme = README.read_text(encoding="utf-8")
EVERY[README] = ({name for example in _example_trees(_readme) for name in _code_names(example)}
                 | set(IDENTIFIER.findall(" ".join(re.findall(r"`([^`\n]+)`", _readme)))))
# Every doctest example in the repo's files and the README, parsed: calls are read from these
# as from code.
EXAMPLE_TREES = [example for tree in TREES.values() for node in _strings(tree)
                 if ">>>" in node.value for example in _example_trees(node.value)]
EXAMPLE_TREES += list(_example_trees(_readme))


def _definitions(path: Path) -> Iterator[str]:
    """Each module-level function, class and constant `path` defines."""
    for node in TREES[path].body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield node.name
        elif isinstance(node, ast.Assign):
            yield from (target.id for target in node.targets if isinstance(target, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            yield node.target.id


def _dead() -> set[tuple[str, str]]:
    """Each name the Toolbox or tools/ defines that no file uses, as (file, name)."""
    dead = set()
    for path in [*sorted(TOOLBOX.glob("*.py")), *sorted((ROOT / "tools").glob("*.py"))]:
        for name in _definitions(path):
            if name in READ_BY_NAME or (name.startswith("__") and name.endswith("__")):
                continue
            if name not in OWN[path] and not any(
                    name in names for other, names in EVERY.items() if other != path):
                dead.add((path.relative_to(ROOT).as_posix(), name))
    return dead


def test_nothing_is_defined_that_nothing_uses() -> None:
    assert _dead() == KNOWN_DEAD


STEMS = {path.stem for path in TOOLBOX.glob("*.py")}


def _toolbox_module_call(value: ast.AST) -> str | None:
    """The Toolbox file a toolbox_module("tables") call names, or None."""
    if (isinstance(value, ast.Call) and isinstance(value.func, ast.Name)
            and value.func.id == "toolbox_module" and value.args
            and isinstance(value.args[0], ast.Constant) and value.args[0].value in STEMS):
        return value.args[0].value
    return None


def _bound(node: ast.AST) -> Iterator[tuple[str, str]]:
    """Each (name, Toolbox file) one import or assignment binds."""
    if isinstance(node, ast.ImportFrom):
        yield from ((alias.asname or alias.name, alias.name) for alias in node.names
                    if alias.name in STEMS)
    elif isinstance(node, ast.Import):
        for alias in node.names:
            last = alias.name.split(".")[-1]
            if alias.name.startswith("sqlglot_composer.") and last in STEMS:
                yield alias.asname or last, last
    elif isinstance(node, ast.Assign) and len(node.targets) == 1:
        target, value = node.targets[0], node.value
        pairs = (zip(target.elts, value.elts) if isinstance(target, ast.Tuple)
                 and isinstance(value, ast.Tuple) else [(target, value)])
        for name, call in pairs:
            stem = _toolbox_module_call(call)
            if isinstance(name, ast.Name) and stem:
                yield name.id, stem


def _module_aliases(tree: ast.Module) -> dict[str, set[str]]:
    """Each name a file binds to Toolbox files, such as `lineage`, `tables =
    toolbox_module("tables")`, or `module` in `for module in (lineage, project)`, to their
    file names."""
    aliases: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        for name, stem in _bound(node):
            aliases[name] = {stem}
    for node in ast.walk(tree):
        if (isinstance(node, ast.For) and isinstance(node.target, ast.Name)
                and isinstance(node.iter, (ast.Tuple, ast.List))
                and all(isinstance(item, ast.Name) and item.id in aliases
                        for item in node.iter.elts)):
            aliases[node.target.id] = set().union(*(aliases[item.id] for item in node.iter.elts))
    return aliases


PRIVATE = {(path.stem, name) for path in TOOLBOX.glob("*.py") for name in _definitions(path)
           if name.startswith("_") and not name.endswith("__")}
# Each private constant only one Toolbox file defines, with that file.
UNIQUE_CONSTANTS = {name: owner for owner, name in PRIVATE if PRIVATE_CONSTANT.fullmatch(name)
                    and [other for other, same in PRIVATE if same == name] == [owner]}


def _reached(node: ast.AST, aliases: dict[str, set[str]]) -> Iterator[tuple[str, object]]:
    """Each (Toolbox file, name) one node reaches."""
    if isinstance(node, ast.ImportFrom) and node.module:
        yield from ((node.module.split(".")[-1], alias.name) for alias in node.names)
    elif isinstance(node, ast.Attribute):
        if isinstance(node.value, ast.Name) and node.value.id in aliases:
            yield from ((owner, node.attr) for owner in aliases[node.value.id])
        elif node.attr in UNIQUE_CONSTANTS:
            # A private constant, however the file came by its module, such as engine._LOWEST.
            # A private function's name may be an object's attribute too, such as t._name.
            yield UNIQUE_CONSTANTS[node.attr], node.attr
    elif (isinstance(node, ast.Call) and len(node.args) >= 2
          and isinstance(node.args[0], ast.Name) and node.args[0].id in aliases
          and isinstance(node.args[1], ast.Constant)):
        # mock.patch.object(lineage, "_now", ...), monkeypatch.setattr(...)
        yield from ((owner, node.args[1].value) for owner in aliases[node.args[0].id])


def _private_reaches() -> set[tuple[str, str, str]]:
    """Each private name of a Toolbox file another file reaches, as (owner, name, reacher)."""
    reaches = set()
    for path, tree in TREES.items():
        aliases = _module_aliases(tree)
        found = {pair for node in ast.walk(tree) for pair in _reached(node, aliases)}
        reaches |= {(owner, name, path.relative_to(ROOT).as_posix())
                    for owner, name in found & PRIVATE
                    if not (path.parent == TOOLBOX and path.stem == owner)}
    return reaches


def test_a_private_name_is_reached_from_another_file_only_where_listed() -> None:
    reached = {(owner, name) for owner, name, _ in _private_reaches()}
    assert reached - set(PRIVATE_SEAMS) == set(), "reached and not listed"
    assert set(PRIVATE_SEAMS) - reached == set(), "listed and no longer reached"


def _calls() -> dict[str, tuple[set[str], int]]:
    """For each name called anywhere, in code or a doctest example, the keywords its calls pass
    and the most arguments one passes by position."""
    calls: dict[str, tuple[set[str], int]] = {}
    for tree in [*TREES.values(), *EXAMPLE_TREES]:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
            keywords, most = calls.get(name, (set(), 0))
            keywords |= {keyword.arg for keyword in node.keywords if keyword.arg}
            many = any(isinstance(arg, ast.Starred) for arg in node.args)
            calls[name] = keywords, max(most, 10**6 if many else len(node.args))
    return calls


def _public_functions() -> Iterator[tuple[str, Callable[..., object]]]:
    for module, prefix in ((sqlglot_composer, ""), (admin, "admin."), (project, "project.")):
        for name in module.__all__:
            value = getattr(module, name)
            if inspect.isfunction(value) or value is sqlglot_composer.Table:
                yield prefix + name, value


def _untested_keywords() -> set[tuple[str, str]]:
    """Each argument with a default, of a public function, that no call anywhere passes."""
    calls, untested = _calls(), set()
    for shown, function in _public_functions():
        keywords, most = calls.get(shown.split(".")[-1], (set(), 0))
        for index, parameter in enumerate(inspect.signature(function).parameters.values()):
            optional = parameter.default is not inspect.Parameter.empty
            by_position = (parameter.kind is not inspect.Parameter.KEYWORD_ONLY
                           and index < most)
            if optional and parameter.name not in keywords and not by_position:
                untested.add((shown, parameter.name))
    return untested


def test_every_keyword_of_a_public_function_is_passed_somewhere() -> None:
    assert _untested_keywords() == UNTESTED_KEYWORDS

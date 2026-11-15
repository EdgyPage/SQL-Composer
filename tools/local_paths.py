"""The rule that no tracked file holds a local path or a personal detail (evaluation system,
ticket 02).

The user: "Let's make it a rule from now on not to push that stuff." Records of an evaluation
stay on one machine, under the git-ignored `.eval-local/`; what git holds is instructions, and
instructions name no folder of anyone's computer. This is the one reader of that rule. A test
reads every tracked file with it, a commit hook reads the files a commit would hold, and the
export reads the Clean tree, so all three refuse the same things:

- an absolute user path: `C:\\Users\\<name>\\...`, `C:/Users/<name>/...`, `/c/Users/<name>/...`,
  `/Users/<name>/...` or `/home/<name>/...`, unless the name is a placeholder such as `<name>`;
- the user's own folder name, read at run time from where the repo lies (the folder after
  `Users` or `home` in its path), never written in this repo;
- an AppData, Temp or scratchpad path, which is where an agent's work files go;
- an email address, bar the reserved example domains.

A file that names these patterns in order to check for them goes in `NAMES_THE_PATTERNS`. Text
that isn't UTF-8 (a workbook, an image) is not read. It reaches nothing and runs nothing.

    .venv/Scripts/python tools/local_paths.py --tree <folder>
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path

# The files that name the patterns to check for them: this reader, and the tests of this reader
# and of the hook that use it. Each holds made-up paths on purpose.
NAMES_THE_PATTERNS = frozenset({
    "tools/local_paths.py",
    "tests/repo/test_local_paths.py",
    "tests/repo/test_local_paths_hook.py",
    "tests/repo/test_code_audit.py",  # writes a Startup path into a made-up file to find it
    "tests/repo/test_scrub_history.py",  # the history scrub's rules, on a made-up user
})

# A name that stands for a person's, so a path through it names no one.
PLACEHOLDER = re.compile(r"^(<|\$|%|\{|\.\.\.|\*|name$|user$|username$|you$|me$)",
                         re.IGNORECASE)
_USER_PATH = re.compile(
    r"(?:(?<![\w])[A-Za-z]:[\\/]{1,2}Users|(?<![\w/])/[a-z]/Users|(?<![\w/])/Users"
    r"|(?<![\w/])/home)[\\/]{1,2}([^\\/\s\"'`)\]>]+)",
    re.IGNORECASE)
_WORK_FOLDER = re.compile(
    r"AppData[\\/]{1,2}(?:Local|Roaming|LocalLow)\b"
    r"|[\\/]Temp[\\/]claude\b"
    r"|[\\/]scratchpad[\\/]",
    re.IGNORECASE)
_EMAIL = re.compile(r"[\w.+-]+@((?:[\w-]+\.)+[A-Za-z]{2,})\b")
# Domains reserved for examples (RFC 2606), and the one Claude Code's own attribution line uses.
EXAMPLE_DOMAINS = frozenset({"example.com", "example.org", "example.net", "anthropic.com",
                             "users.noreply.github.com"})
# GitHub's own address, as the committer of a commit made on its website: no one's email. The
# history scrub (`tools/scrub_history.py`) leaves it in a commit's name lines.
GITHUB_COMMITTER = "noreply@github.com"
_SHORTEST_NAME = 3


def own_names(here: Path = Path(__file__),
              environ: Mapping[str, str] = os.environ) -> tuple[str, ...]:
    """The name of this computer's user, read at run time from where the repo lies (the folder
    after `Users` or `home` in `here`'s whole path), so no name is held in the repo. Nothing
    when the repo isn't under a user's folder, the name is too short to tell from words, or
    the repo is on a GitHub Actions machine, whose `/home/runner` is the CI account's and no
    person's (`runner` is also a word the docs use)."""
    if environ.get("GITHUB_ACTIONS") == "true":
        return ()
    # A path written for another computer (a Windows path on Linux) is not absolute here,
    # and is read as written: resolving it would put this folder in front of it.
    parts = here.resolve().parts if here.is_absolute() else here.parts
    for position, part in enumerate(parts[:-1]):
        if part.lower() in ("users", "home") and len(parts[position + 1]) >= _SHORTEST_NAME:
            return (parts[position + 1],)
    return ()


def findings_in(text: str, path: str, names: Iterable[str] | None = None) -> list[str]:
    """Each local path or personal detail in `text`, as `path:line kind: the text`, in order.
    `names` is the user's folder names, `own_names()` when not given."""
    if names is None:
        names = own_names()
    name_patterns = {name: re.compile(rf"(?<![\w-]){re.escape(name)}(?![\w-])", re.IGNORECASE)
                     for name in names}
    found: list[str] = []
    for number, line in enumerate(text.splitlines(), 1):
        for match in _USER_PATH.finditer(line):
            if not PLACEHOLDER.match(match.group(1)):
                found.append(f"{path}:{number} user path: {match.group(0)}")
        if _WORK_FOLDER.search(line):
            found.append(f"{path}:{number} work folder: {line.strip()[:80]}")
        for match in _EMAIL.finditer(line):
            if match.group(1).lower() not in EXAMPLE_DOMAINS:
                found.append(f"{path}:{number} email: {match.group(0)}")
        for name, pattern in name_patterns.items():
            if pattern.search(line):
                found.append(f"{path}:{number} user's folder name: {name}")
    return found


def text_of(data: bytes) -> str | None:
    """The text of `data`, or None if it isn't UTF-8 text."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def scan_files(files: Iterable[tuple[str, bytes]], names: Iterable[str] | None = None
               ) -> list[str]:
    """The findings in each `(path, bytes)` that is read: not a file naming the patterns, and
    text. A path is relative to the repo's root, with forward slashes."""
    names = own_names() if names is None else tuple(names)
    found: list[str] = []
    for path, data in files:
        text = None if path in NAMES_THE_PATTERNS else text_of(data)
        if text is not None:
            found += findings_in(text, path, names)
    return found


def scan_tree(folder: Path, names: Iterable[str] | None = None) -> list[str]:
    """The findings in every file under `folder`, such as the Clean tree."""
    paths = sorted(path for path in folder.rglob("*") if path.is_file()
                   and ".git" not in path.relative_to(folder).parts)
    return scan_files(((path.relative_to(folder).as_posix(), path.read_bytes())
                       for path in paths), names)


REFUSAL = ("{count} place(s) hold a local path or a personal detail, which git must not hold "
           "(records stay under .eval-local/, and instructions name no folder of a computer):\n"
           "{lines}Make each path relative or write <user folder>, or move the record under "
           ".eval-local/.")


def refusal(found: list[str], shown: int = 20) -> str:
    """The message for `found`, which is not empty."""
    lines = "".join(f"  {finding}\n" for finding in found[:shown])
    if len(found) > shown:
        lines += f"  ... and {len(found) - shown} more\n"
    return REFUSAL.format(count=len(found), lines=lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--tree", type=Path, required=True, help="the folder to read")
    given = parser.parse_args(argv)
    found = scan_tree(given.tree)
    if found:
        print(refusal(found), file=sys.stderr)
        return 1
    print("No local path or personal detail.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

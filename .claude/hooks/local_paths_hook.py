"""PreToolUse hook: no commit that would hold a local path or a personal detail.

Records of an evaluation stay under the git-ignored `.eval-local/`, and no tracked file names a
folder of someone's computer (evaluation system, ticket 02). When Claude runs a `git commit`,
this reads the files the commit would hold with `tools/local_paths.py`, the one reader of that
rule, and refuses the commit, saying where each one is.

- **The index:** every added, copied or modified file, read as it is on disk.
- **`git commit -a` or `--all`**, or a command that also runs `git add`, which the index doesn't
  show yet: every modified and every untracked, not-ignored file as well.

It runs git through `drift_list.git`, the hooks' one way to git, which gives nothing when git
fails: then the commit goes through, and so does one made any other way (by the user's own
hand), which the test that reads every tracked file catches.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from drift_list import MAKES_A_COMMIT, git
from hook_io import deny, plain_line, read_hook_input

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import local_paths  # noqa: E402

# `git commit` alone: the same words `MAKES_A_COMMIT` reads, with commit the only subcommand.
COMMIT = re.compile(MAKES_A_COMMIT.pattern.replace(
    "(commit|merge|pull|cherry-pick|revert|am|rebase)", "commit"))
# A command that runs `git add` or `git stage`, or `git commit -a` or `--all`.
ADDS_ON_THE_WAY = re.compile(
    r"(?<![\w.])git\b[^;&|\n]*\b(add|stage)\b"
    r"|(?<![\w.])git\b[^;&|\n]*\bcommit\b[^;&|\n]*\s(-[a-zA-Z]*a[a-zA-Z]*|--all)(\s|$)")
SHOWN = 12


def paths(repo: Path, *args: str) -> list[str]:
    """The paths git prints, NUL-separated, for `args` in `repo`."""
    return [name for name in git(repo, *args, "-z").split("\0") if name]


def files_to_read(repo: Path, command: str) -> list[tuple[str, bytes]]:
    """Each file the commit `command` would hold, as `(path, bytes)` read from `repo`."""
    names = paths(repo, "diff", "--cached", "--name-only", "--diff-filter=ACM")
    if ADDS_ON_THE_WAY.search(command):
        names += paths(repo, "ls-files", "--modified", "--others", "--exclude-standard")
    return [(name, (repo / name).read_bytes()) for name in dict.fromkeys(names)
            if (repo / name).is_file()]


def refusal(tool_input: dict[str, object], cwd: str,
            names: tuple[str, ...] | None = None) -> str | None:
    """Why this call is refused, or None to let it through. `names` is the user's folder
    names, `local_paths.own_names()` when not given."""
    command = str(tool_input.get("command", ""))
    if not COMMIT.search(command):
        return None
    found = local_paths.scan_files(files_to_read(Path(cwd), command), names)
    if not found:
        return None
    shown = [plain_line(finding, 160) for finding in found[:SHOWN]]
    more = f" ... and {len(found) - SHOWN} more" if len(found) > SHOWN else ""
    return ("This commit would hold a local path or a personal detail; records stay under "
            ".eval-local/ and git holds none (CLAUDE.md). Make each path relative or write "
            "<user folder>, or move the record under .eval-local/: " + "; ".join(shown) + more)


def main() -> None:
    hook = read_hook_input()
    why = refusal(hook.get("tool_input", {}), hook.get("cwd", "."))
    if why:
        deny(why)


if __name__ == "__main__":
    main()

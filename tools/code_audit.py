"""The code audit: read the repo for what could hide or run harm, beside the offline policy.

`tools/offline_policy.py` asks whether anything could reach the network, start a process or run
code it can't see. This asks what that leaves out, reading every text file of the repo, the
tracker's notes in `.scratch/` among them:

- **hidden text:** a character that shows nothing or shows something else: bidi controls,
  zero-width characters, NUL and the other control characters besides tab and line ends, and a
  Cyrillic or Greek letter inside a word of Latin ones, which looks like the Latin letter;
- **not UTF-8:** a file that doesn't read as UTF-8 text; a workbook (`.xlsx`, `.xlsm`) is a zip,
  so each part inside it is read as a file of its own, at `<workbook>/<part>`;
- **encoded payload:** a long run of base64, hex or `\\x..` escapes, which could hold code to
  decode and run, and, in Python, a decoder: `base64`, `binascii`, `zlib`, `gzip`, `bz2`,
  `lzma`, `codecs.decode`, `bytes.fromhex`;
- **outside the repo**, in Python: a reach for credentials, the home folder or the system:
  `~`, `Path.home`, `expanduser`, a path into `.ssh`, `.aws` and the like, a system path such
  as `/etc/` or `C:\\Windows\\` or a startup folder, an environment variable whose name says
  key, token, secret, password or credential, and `keyring` or `getpass`;
- **hook**, in Python: code set to run at exit or on every event: `atexit.register`,
  `sys.addaudithook`, and `sys` or `threading`'s `settrace` and `setprofile`;
- **config** that runs or fetches code: a Claude Code hook in `.claude/settings*.json` that runs
  anything but a file in `.claude/hooks/`; a GitHub workflow step that uses an action not pinned
  to a commit, downloads with `curl` or `wget`, or pipes into a shell, and a workflow allowed to
  write or with no `permissions:` of its own; a `pyproject.toml` that loads a pytest plugin with
  `-p` or builds a package; and a requirements line that isn't `name==version`;
- **notebook:** a notebook that was run, whose cells keep an output or a count, or whose
  Markdown holds a script.

It only reads text, never imports or runs what it reads, and reaches nothing. It skips the
folders the offline policy skips (`offline_policy.not_read`: the git folder, caches, Python
environments and Claude Code's worktrees, but none inside the Toolbox or user-copied code),
apart from `.scratch/`, which it reads, since a note can hide text too. `AUDITED` lists each
reviewed site, by file, kind and what its finding says, with the reason it is no harm; an entry
that matches nothing is stale.

    python tools/code_audit.py [--root FOLDER]

It prints each finding, then the offline policy's, as `file:line kind: what`, and exits 1 if
there is any. With `--root`, it reads that folder by both readers' rules, with neither's
reviewed sites, to check a sample.
"""

from __future__ import annotations

import ast
import io
import json
import os
import re
import sys
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path

import offline_policy
from offline_policy import Finding

ROOT = offline_policy.ROOT

# --- What it looks for ---------------------------------------------------------------------

# Characters that show nothing, or turn the text around: bidi controls and marks, zero-width
# characters, and a byte-order mark anywhere but a file's start.
HIDDEN = re.compile("[\u200b-\u200f\u202a-\u202e\u2060-\u2064\u2066-\u2069\ufeff"
                    "\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
# A Cyrillic or Greek letter beside a Latin one in one word, which looks like the Latin letter.
LOOK_ALIKE = re.compile("[A-Za-z][\u0370-\u03ff\u0400-\u04ff]"
                        "|[\u0370-\u03ff\u0400-\u04ff][A-Za-z]")
# Long runs that could hold encoded code.
ENCODED = re.compile(r"[A-Za-z0-9+/]{200,}={0,2}|(?:[0-9a-fA-F]{2}){120,}"
                     r"|(?:\\x[0-9a-fA-F]{2}){50,}")
DECODER_MODULES = ("base64", "binascii", "zlib", "gzip", "bz2", "lzma")
DECODER_CALLS = ("codecs.decode", "bytes.fromhex")
# Strings that name a place credentials are kept, or the home folder.
CREDENTIAL_PATH = re.compile(r"(?:^|[\\/~'\"])\.(?:ssh|aws|azure|gnupg|netrc|git-credentials"
                             r"|pypirc|docker|kube)\b|\bid_(?:rsa|ed25519|ecdsa|dsa)\b|^~[\\/]")
SECRET_NAME = re.compile(r"key|token|secret|passw|credential", re.IGNORECASE)
# A system folder, or the folder whose programs Windows runs at sign-in.
SYSTEM_PATH = re.compile(r"^(?:/etc|/usr|/bin|/sbin|/var|/root|/boot|/System|/Library)/"
                         r"|^[A-Za-z]:[\\/](?:Windows|Program Files|ProgramData)\b"
                         r"|Start Menu[\\/]Programs[\\/]Startup", re.IGNORECASE)
# Calls that set code to run at exit or on every event.
HOOK_CALLS = ("atexit.register", "sys.addaudithook", "sys.settrace", "sys.setprofile",
              "threading.settrace", "threading.setprofile")
CREDENTIAL_MODULES = ("keyring", "getpass", "win32cred", "secretstorage")
HOME_CALLS = ("Path.home", "pathlib.Path.home", "os.path.expanduser", "expanduser")
ENVIRONMENT_READS = ("os.environ", "os.getenv", "os.environ.get", "getenv")
HOOK_COMMAND = re.compile(r'^python3?\s+"?\$CLAUDE_PROJECT_DIR[\\/]\.claude[\\/]hooks[\\/]'
                          r'(?P<file>[\w.-]+\.py)"?\s*$')
PINNED_ACTION = re.compile(r"^[\w.-]+/[\w./-]+@[0-9a-f]{40}$")
FETCH = re.compile(r"\b(?:curl|wget|Invoke-WebRequest|iwr|Invoke-Expression|iex)\b"
                   r"|\|\s*(?:sh|bash|pwsh|powershell|python3?)\b")
PINNED = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*(?:\[[\w,]+\])?==[\w.+!-]+$")


@dataclass(frozen=True)
class Audited:
    """One reviewed site the audit would otherwise report: a finding in `file` (from the repo's
    root) of `kind` whose text holds `holds`, and why it is no harm."""

    file: str
    kind: str
    holds: str
    reason: str

    def matches(self, finding: Finding) -> bool:
        return ((self.file, self.kind) == (finding.path, finding.kind)
                and self.holds in finding.code)


CRAFTED_PATH = "a test's crafted path, which the hooks must strip before they show it"
AUDITED = (
    *(Audited("tests/repo/test_hooks.py", "hidden text", character, CRAFTED_PATH)
      for character in ("U+202E", "U+2066", "U+2069", "U+200F")),
    Audited(".scratch/drift.md", "hidden text", "U+0000",
            "a drift note quoting the NUL the Toolbox escapes in a Hive string"),
    Audited("tests/repo/test_code_audit.py", "outside the repo", "names ",
            "the audit's tests' samples, planted in a temporary folder"),
    Audited("tests/offline_trap.py", "hook", "sys.addaudithook",
            "the network trap every test run installs, which refuses a connection off this "
            "computer"),
    Audited("tools/copilot_eval.py", "hook", "sys.addaudithook",
            "the Copilot scorer's guard, which refuses a process, a socket or a file written "
            "outside its temporary folder while a model's answers run; it only blocks "
            "(the user's OK, 2026-10-27)"),
)


# --- Reading the repo ----------------------------------------------------------------------


def audit(root: Path = ROOT, audited: tuple[Audited, ...] = AUDITED) -> list[Finding]:
    """Each finding in the files under `root` that `audited` doesn't cover."""
    uncovered = []
    for finding in everything_found(root):
        if not any(entry.matches(finding) for entry in audited):
            uncovered.append(finding)
    return uncovered


def stale(root: Path = ROOT, audited: tuple[Audited, ...] = AUDITED) -> list[Finding]:
    """Each entry of `audited` that matches nothing under `root`."""
    found = everything_found(root)
    stale_entries = []
    for entry in audited:
        if not any(entry.matches(finding) for finding in found):
            stale_entries.append(Finding(
                entry.file, 0, "stale entry",
                f"AUDITED's {entry.kind} entry holding {entry.holds!r} matches nothing"))
    return stale_entries


def everything_found(root: Path) -> list[Finding]:
    """Each finding in the files under `root`, reviewed or not."""
    found = []
    for file in files_to_read(root):
        found += findings_in_file(root, file)
    return found


def files_to_read(root: Path) -> list[Path]:
    """Every file under `root` the audit reads, in a steady order."""
    found = []
    for folder, subfolders, names in os.walk(root):
        subfolders[:] = sorted(name for name in subfolders
                               if name == ".scratch"
                               or not offline_policy.not_read(Path(folder, name), root))
        found += [Path(folder, name) for name in sorted(names)]
    return found


def findings_in_file(root: Path, file: Path) -> list[Finding]:
    path = file.relative_to(root).as_posix()
    data = file.read_bytes()
    if file.suffix.lower() in offline_policy.WORKBOOK_FILES and zipfile.is_zipfile(file):
        return workbook_findings(root, data, path)
    return findings_in_text(root, data, path, file.suffix)


def workbook_findings(root: Path, data: bytes, path: str) -> list[Finding]:
    """Each finding in a workbook's parts, each read as a file at `<path>/<part>`. The offline
    policy reads the same parts for what Excel would run or fetch."""
    found = []
    with zipfile.ZipFile(io.BytesIO(data)) as workbook:
        for name in workbook.namelist():
            found += findings_in_text(root, workbook.read(name), f"{path}/{name}",
                                      Path(name).suffix)
    return found


def findings_in_text(root: Path, data: bytes, path: str, suffix: str) -> list[Finding]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        return [Finding(path, data.count(b"\n", 0, error.start) + 1, "not UTF-8",
                        f"byte {data[error.start]:#04x} doesn't read as UTF-8")]
    found = hidden_text(text, path) + encoded_runs(text, path)
    if suffix == ".py":
        found += python_findings(text, path)
    if suffix == ".ipynb":
        found += notebook_findings(text, path)
    found += config_findings(root, text, path)
    return found


# --- Each kind -----------------------------------------------------------------------------


def hidden_text(text: str, path: str) -> list[Finding]:
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        for match in HIDDEN.finditer(line.lstrip("\ufeff") if number == 1 else line):
            character = match.group()
            name = unicodedata.name(character, "a control character")
            found.append(Finding(path, number, "hidden text",
                                 f"U+{ord(character):04X} ({name})"))
        for match in LOOK_ALIKE.finditer(line):
            letter = next(c for c in match.group() if not c.isascii())
            found.append(Finding(path, number, "hidden text",
                                 f"U+{ord(letter):04X} ({unicodedata.name(letter, '?')}) "
                                 "inside a Latin word"))
    return found


def encoded_runs(text: str, path: str) -> list[Finding]:
    return [Finding(path, text.count("\n", 0, match.start()) + 1, "encoded payload",
                    f"a run of {len(match.group())} encoded characters: "
                    f"{match.group()[:24]}...")
            for match in ENCODED.finditer(text)]


def python_findings(text: str, path: str) -> list[Finding]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []  # the offline policy reports a file that doesn't parse
    found = []
    for node in ast.walk(tree):
        for kind, what in _node_findings(node):
            found.append(Finding(path, getattr(node, "lineno", 0), kind, what))
    return found


def _node_findings(node: ast.AST) -> list[tuple[str, str]]:
    """Each (kind, what) one node of a Python file's tree is a finding of."""
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return _import_findings(node)
    if isinstance(node, ast.Call):
        return _call_findings(node)
    if isinstance(node, ast.Subscript) and _dotted(node.value) == "os.environ":
        if not _names_a_secret([node.slice]):
            return []
        return [("outside the repo", f"reads the environment's {_literal(node.slice)}")]
    if (isinstance(node, ast.Constant) and isinstance(node.value, str)
            and (CREDENTIAL_PATH.search(node.value) or SYSTEM_PATH.search(node.value))):
        return [("outside the repo", f"names {node.value[:60]!r}")]
    return []


def _import_findings(node: ast.Import | ast.ImportFrom) -> list[tuple[str, str]]:
    """Each (kind, what) an import is a finding of: a decoder, then a reach for credentials."""
    if isinstance(node, ast.Import):
        names = [alias.name for alias in node.names]
    else:
        names = [node.module or ""]
    decoders = [("encoded payload", f"imports {name}") for name in names
                if name.split(".")[0] in DECODER_MODULES]
    credentials = [("outside the repo", f"imports {name}") for name in names
                   if name.split(".")[0] in CREDENTIAL_MODULES]
    return decoders + credentials


def _call_findings(node: ast.Call) -> list[tuple[str, str]]:
    called = _dotted(node.func)
    found = []
    if called in DECODER_CALLS or called.endswith(".fromhex"):
        found.append(("encoded payload", f"calls {called}"))
    if called in HOME_CALLS or called.endswith(".expanduser"):
        found.append(("outside the repo", f"calls {called}"))
    if called in ENVIRONMENT_READS and _names_a_secret(node.args[:1]):
        found.append(("outside the repo", f"reads the environment's {_literal(node.args[0])}"))
    if called in HOOK_CALLS:
        found.append(("hook", f"calls {called}"))
    return found


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_dotted(node.value)}.{node.attr}"
    return ""


def _literal(node: ast.AST) -> str:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else ""


def _names_a_secret(nodes: list[ast.AST]) -> bool:
    return any(SECRET_NAME.search(_literal(node)) for node in nodes)


def notebook_findings(text: str, path: str) -> list[Finding]:
    try:
        cells = json.loads(text).get("cells", [])
    except (ValueError, AttributeError):
        return []  # the offline policy reports a notebook it can't read
    found = []
    for number, cell in enumerate(cells, 1):
        if cell.get("outputs") or cell.get("execution_count") is not None:
            found.append(Finding(path, 0, "notebook",
                                 f"cell {number} was run: clear its output"))
        source = cell.get("source", "")
        source = "".join(source) if isinstance(source, list) else source
        if cell.get("cell_type") == "markdown" and re.search(r"<script\b|javascript:", source,
                                                             re.IGNORECASE):
            found.append(Finding(path, 0, "notebook",
                                 f"cell {number}'s Markdown holds a script"))
    return found


def config_findings(root: Path, text: str, path: str) -> list[Finding]:
    name = path.rsplit("/", 1)[-1]
    if path.startswith(".claude/") and re.fullmatch(r"settings(\.local)?\.json", name):
        return _hook_findings(root, text, path)
    if path.startswith(".github/workflows/") and name.endswith((".yml", ".yaml")):
        return _workflow_findings(text, path)
    if name == "pyproject.toml":
        return _pyproject_findings(text, path)
    if re.fullmatch(r"requirements[\w-]*\.txt", name):
        return _requirements_findings(text, path)
    return []


def _hook_findings(root: Path, text: str, path: str) -> list[Finding]:
    try:
        hooks = json.loads(text).get("hooks", {})
    except (ValueError, AttributeError):
        return [Finding(path, 0, "config", "it isn't JSON, so its hooks can't be read")]
    found = []
    for event, groups in hooks.items():
        for group in groups:
            for hook in group.get("hooks", []):
                command = hook.get("command", "")
                run = HOOK_COMMAND.match(command)
                if not run or not (root / ".claude" / "hooks" / run["file"]).is_file():
                    found.append(Finding(path, 0, "config",
                                         f"{event} hook runs {command[:80]!r}, not a file in "
                                         ".claude/hooks/"))
    return found


def _workflow_findings(text: str, path: str) -> list[Finding]:
    found = []
    if not re.search(r"^permissions:", text, re.MULTILINE):
        found.append(Finding(path, 0, "config", "it has no permissions: of its own, so it gets "
                             "the repository's default, which may write"))
    for number, line in enumerate(text.splitlines(), 1):
        used = re.match(r"\s*(?:-\s*)?uses:\s*([^\s#]+)", line)
        if used and not PINNED_ACTION.match(used.group(1)):
            found.append(Finding(path, number, "config",
                                 f"uses {used.group(1)}, not pinned to a commit"))
        if FETCH.search(line):
            found.append(Finding(path, number, "config", f"fetches or pipes: {line.strip()}"))
        if re.search(r"\bpermissions:\s*write-all|:\s*write\b", line):
            found.append(Finding(path, number, "config", f"may write: {line.strip()}"))
    return found


def _pyproject_findings(text: str, path: str) -> list[Finding]:
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        if line.strip() == "[build-system]":
            found.append(Finding(path, number, "config", "builds a package"))
        if re.search(r"(?:^|[\s\"'\[,])-p\s*[\w.]", line):
            found.append(Finding(path, number, "config", f"loads a plugin: {line.strip()}"))
    return found


def _requirements_findings(text: str, path: str) -> list[Finding]:
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        line = line.split("#", 1)[0].strip()
        if line and not PINNED.match(line):
            found.append(Finding(path, number, "config",
                                 f"{line!r} isn't a pin written name==version"))
    return found


def main(arguments: list[str]) -> int:
    if "--root" in arguments:
        root = Path(arguments[arguments.index("--root") + 1]).resolve()
        found = audit(root, audited=()) + offline_policy.scan(root, allowed=())
    else:
        found = (audit() + stale() + offline_policy.scan(ROOT)
                 + offline_policy.stale_entries(ROOT))
    sys.stdout.reconfigure(errors="replace")
    for finding in found:
        print(finding)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

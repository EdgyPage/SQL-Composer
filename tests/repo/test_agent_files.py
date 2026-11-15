"""Each agent file in `.claude/agents/` loads as an agent type.

Claude Code reads an agent file's header as YAML. An unquoted value holding ": " is not YAML,
so the agent type quietly goes missing from the session: `zero-context-user` and
`metric-proxy` did (2026-11-14), each description holding "loop: a technical user" or
"(Copilot file 19): the stand-in user".
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
AGENTS = sorted((ROOT / ".claude" / "agents").glob("*.md"))
NEEDED = ("name", "description")


def header(path: Path) -> list[str]:
    """The lines between an agent file's two `---` lines."""
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "---", f"{path.name} doesn't start with its header"
    return lines[1:lines.index("---", 1)]


def test_there_are_agent_files() -> None:
    assert AGENTS


@pytest.mark.parametrize("path", AGENTS, ids=[path.stem for path in AGENTS])
def test_an_agent_header_is_plain_yaml_with_its_name_and_description(path: Path) -> None:
    fields = {}
    for line in header(path):
        key, separator, value = line.partition(": ")
        assert separator and key.isidentifier(), f"{path.name}: {line!r} isn't `key: value`"
        quoted = len(value) > 1 and value[0] == value[-1] and value[0] in "\"'"
        assert quoted or ": " not in value, (
            f"{path.name}: {key}'s value holds ': ', which YAML reads as a second key, so the "
            "agent type won't load. Reword it, or quote the whole value.")
        assert quoted or not value.startswith(("'", '"', "[", "{", "&", "*", "!", "|", ">")), (
            f"{path.name}: {key}'s value starts with a character YAML reads as syntax")
        fields[key] = value
    assert all(fields.get(key) for key in NEEDED), f"{path.name} lacks {NEEDED}"
    assert fields["name"] == path.stem

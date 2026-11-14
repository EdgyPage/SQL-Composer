"""Sources: Used and Read lines, failures tied to doc ids (evaluation system, ticket 06).

A proxy ends each reply with `Used: <ids>` naming the patterns, rules and worked patterns of
the loaded file it followed; a zero-context user ends with `Read: <file> <section>, ...`. The
scorers keep each task's result with them in `.eval-local/sources.csv`, and a summary ranks the
ids by the failing replies that cite them.
"""

from __future__ import annotations

from pathlib import Path

import copilot_eval
import eval_runs
import eval_sources
import excel_eval
import metric_eval
import pytest
from copilot_eval_tasks import BY_ID
from eval_sources import SourceRow

COPILOT = Path(__file__).resolve().parent.parent / "copilot"
AGENTS = Path(__file__).resolve().parent.parent / ".claude" / "agents"
FILES = sorted(COPILOT.glob("[0-9][0-9]_*.txt"))

SAMPLE = """\
## Patterns

| ID | The user says | Do | Copy |
|---|---|---|---|
| P1 | "the rows where ..." | SELECT | W1 |
| P12 | "latest row" | file 05 | A10 |

## Rules

- **R1** Each clause only where needed.
- A2. One question per message.
- P4 band: "size = small".

### W1: each job's runs
"""


def test_the_ids_a_file_defines_are_its_table_rows_bullets_and_worked_patterns() -> None:
    assert eval_sources.defined_ids(SAMPLE) == {"P1", "P12", "R1", "A2", "P4", "W1"}


@pytest.mark.parametrize("path", FILES, ids=lambda path: path.name[:2])
def test_every_id_a_copilot_file_defines_can_be_cited(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    number = path.name[:2]
    defined = eval_sources.defined_ids(text)
    assert defined, f"file {number} defines no id a proxy could cite"
    for one in sorted(defined):
        qualified = eval_sources.resolve([f"{number}:{one}"], {number: text})
        assert qualified == ([f"{number}:{one}"], []), one
        assert eval_sources.resolve([one], {number: text}) == ([f"{number}:{one}"], []), one


@pytest.mark.parametrize("path", FILES, ids=lambda path: path.name[:2])
def test_every_id_a_copilot_file_points_a_reader_to_is_one_it_defines(path: Path) -> None:
    """The Copy column of a Patterns row names ids of the same file, so each is citable."""
    text = path.read_text(encoding="utf-8")
    defined = eval_sources.defined_ids(text)
    for row in text.splitlines():
        if row.startswith("| P") and row.endswith("|"):
            copy = row.rstrip("| ").rsplit("|", 1)[1]
            for pointed in eval_sources.ID.findall(copy):
                assert pointed in defined, f"{path.name}: {row[:40]} points to {pointed}"


def test_a_cited_id_the_file_doesnt_define_is_flagged() -> None:
    loaded = {"03": SAMPLE}
    assert eval_sources.resolve(["R1", "Z99", "03:R77"], loaded) == (
        ["03:R1"], ["Z99", "03:R77"])
    # A file the proxy was not given has no ids to cite.
    assert eval_sources.resolve(["04:R1"], loaded) == ([], ["04:R1"])


def test_an_id_two_loaded_files_define_is_named_by_its_file_or_marked_ambiguous() -> None:
    loaded = {"11": SAMPLE, "12": SAMPLE + "\n- **Q1** Only here.\n"}
    assert eval_sources.resolve(["12:R1", "Q1", "w1"], loaded) == (
        ["12:R1", "12:Q1", "*:W1"], [])


@pytest.mark.parametrize("reply, wanted", [
    ("Code.\n\nUsed: P3, R7, W1", ["P3", "R7", "W1"]),
    ("Code.\n**Used:** 03:P3 03:R7.\n", ["03:P3", "03:R7"]),
    ("Used: `p3`; `r7`\n\nUsed: W1", ["P3", "R7", "W1"]),
    ("Used: none", []),
    ("Used:", []),
    ("No line at all, and the word used in a sentence: used P3.", None),
    ("", None),
])
def test_the_used_line_is_read_from_a_reply_or_is_none(
        reply: str, wanted: list[str] | None) -> None:
    assert eval_sources.used_ids(reply) == wanted


def test_the_read_line_gives_each_file_and_section() -> None:
    reply = ("DONE: made it.\nRead: .github/README.md Update, copilot/13_workflows.txt Steps, "
             "how-to convert")
    assert eval_sources.read_items(reply) == [
        ".github/README.md Update", "copilot/13_workflows.txt Steps", "how-to convert"]
    assert eval_sources.read_items("DONE: made it.") is None


def test_a_reply_with_no_used_line_is_no_source_not_a_failure() -> None:
    loaded = {"03": SAMPLE}
    cited = eval_sources.source_row(run_of("T07"), True, "Code only.", loaded)
    assert cited.status == "no source" and cited.result == "pass" and cited.cited == ""
    none = eval_sources.source_row(run_of("T07"), False, "Code.\nUsed: none", loaded)
    assert none.status == "none" and none.result == "fail"
    some = eval_sources.source_row(run_of("T07"), False, "Code.\nUsed: R1, Z9", loaded)
    assert (some.status, some.cited, some.unknown) == ("cited", "03:R1", "Z9")
    assert some.loaded == eval_runs.text_hash(SAMPLE)[:12]


def run_of(task: str, round_name: str = "r1") -> eval_sources.RunOf:
    return eval_sources.RunOf("2026-11-14", round_name, "copilot", task, "C", "haiku", "files1")


def row(task: str, result: str, cited: str, status: str = "cited",
        round_name: str = "r1") -> SourceRow:
    return SourceRow("2026-11-14", round_name, "copilot", task, "C", "haiku", result,
                     "files1", "abc", status, cited, "")


def test_rows_are_kept_in_the_local_folder_and_a_scored_task_replaces_its_row(
        tmp_path: Path) -> None:
    eval_sources.keep_sources([row("T07", "fail", "03:R1"), row("T08", "pass", "03:W1")],
                              tmp_path)
    eval_sources.keep_sources([row("T07", "pass", "03:R1;03:R7")], tmp_path)
    kept = eval_sources.read_sources(tmp_path)
    assert [(one.task, one.result, one.cited) for one in kept] == [
        ("T08", "pass", "03:W1"), ("T07", "pass", "03:R1;03:R7")]
    assert (tmp_path / "sources.csv").is_file()


def test_the_summary_ranks_ids_by_failing_against_passing_and_lists_uncited_failures() -> None:
    rows = [
        row("T01", "fail", "03:R3;03:W1"), row("T02", "fail", "03:R3"),
        row("T03", "fail", "03:R5"), row("T04", "pass", "03:W1"),
        row("T05", "pass", "03:W1;03:R5"), row("T06", "fail", "", "no source"),
        row("T07", "fail", "", "none"), row("T08", "pass", "", "no source"),
        row("T09", "pass", "03:W1", round_name="r2"),
    ]
    found = eval_sources.attribute([one for one in rows if one.round == "r1"])
    ranked = [(one.id, one.failing, one.passing) for one in found.ranked]
    assert ranked == [("03:R3", 2, 0), ("03:R5", 1, 1), ("03:W1", 1, 2)]
    assert found.failing_replies == 4 and found.passing_replies == 2
    assert [(one.task, one.status) for one in found.uncited_failures] == [
        ("T06", "no source"), ("T07", "none")]
    assert found.no_source == {"fail": 1, "pass": 1}
    text = eval_sources.summary_text(rows, round_name="r1")
    assert text.index("03:R3") < text.index("03:R5") < text.index("03:W1")
    assert "T06" in text and "no source" in text and "T09" not in text


def test_the_summary_flags_cited_ids_the_loaded_files_dont_define() -> None:
    flagged = SourceRow("2026-11-14", "r1", "copilot", "T07", "C", "haiku", "fail", "f", "a",
                        "cited", "03:R1", "Z99;03:R77")
    text = eval_sources.summary_text([flagged])
    assert "Z99" in text and "03:R77" in text and "not defined" in text


def test_a_summary_of_nothing_says_so(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert eval_sources.main(["summary", "--local", str(tmp_path)]) == 0
    assert "No sources recorded" in capsys.readouterr().out


def test_the_summary_command_reads_a_round_of_a_pipeline(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    eval_sources.keep_sources([row("T01", "fail", "03:R3"), row("T02", "pass", "03:R3", )],
                              tmp_path)
    assert eval_sources.main(["summary", "--round", "r1", "--pipeline", "copilot",
                              "--local", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "03:R3" in out and "1 failing" in out


# --- The scorers keep each new reply's sources ------------------------------------------------


def fenced(code: str, used: str = "") -> str:
    return f"```python\n{code}```\n{used}\n"


def test_a_copilot_round_keeps_the_new_replies_sources_and_not_the_memos(
        tmp_path: Path) -> None:
    local = ["--local", str(tmp_path)]
    old = fenced(BY_ID["T08"].reference)
    eval_runs.write_kept(eval_runs.Kept(copilot_eval.memo_key("T08", old, "C", "haiku"),
                                        "2026-11-12", "", old), tmp_path / "memo")
    round_of = ["--split", "dev", "--objective", "03", "--model", "haiku"]
    assert copilot_eval.main(["batch", "C", *round_of, "--round", "r1", *local]) == 0
    answers = tmp_path / "copilot" / "runs" / "r1" / "c03" / "answers.md"
    answers.write_text(f"## T07\n\n{fenced(BY_ID['T07'].reference, 'Used: P1, R3, W1, Z9')}",
                       encoding="utf-8")
    assert copilot_eval.main(["collect", "r1", *local]) == 0
    assert copilot_eval.main(["score", "r1", *local]) == 0
    [kept] = eval_sources.read_sources(tmp_path)
    assert (kept.pipeline, kept.round, kept.task, kept.arm) == ("copilot", "r1", "T07", "C")
    assert kept.result == "pass" and kept.status == "cited"
    assert kept.cited == "03:P1;03:R3;03:W1" and kept.unknown == "Z9"
    assert kept.files == copilot_eval.eval_runs.files_version()
    assert kept.loaded == eval_runs.text_hash(copilot_eval.shared_text("C", "03") or "")[:12]


def test_a_copilot_reply_with_no_used_line_is_kept_as_no_source(tmp_path: Path) -> None:
    local = ["--local", str(tmp_path)]
    round_of = ["--split", "dev", "--objective", "03", "--model", "haiku"]
    copilot_eval.main(["batch", "C", *round_of, "--round", "r1", *local])
    answers = tmp_path / "copilot" / "runs" / "r1" / "c03" / "answers.md"
    answers.write_text(f"## T07\n\n{fenced('x = (')}## T08\n\n{fenced('y = (')}",
                       encoding="utf-8")
    copilot_eval.main(["collect", "r1", *local])
    copilot_eval.main(["score", "r1", *local])
    kept = eval_sources.read_sources(tmp_path)
    assert {(one.task, one.result, one.status) for one in kept} == {
        ("T07", "fail", "no source"), ("T08", "fail", "no source")}


def test_arms_that_load_no_copilot_file_keep_no_sources(tmp_path: Path) -> None:
    local = ["--local", str(tmp_path)]
    round_of = ["--split", "dev", "--objective", "03", "--model", "haiku"]
    copilot_eval.main(["batch", "A0", *round_of, "--round", "r1", *local])
    (tmp_path / "copilot" / "runs" / "r1" / "a0-1").joinpath("answers.md").write_text(
        f"## T07\n\n{fenced('x = (', 'Used: P1')}", encoding="utf-8")
    copilot_eval.main(["collect", "r1", *local])
    copilot_eval.main(["score", "r1", *local])
    assert eval_sources.read_sources(tmp_path) == []


def test_an_excel_round_keeps_ids_by_the_file_they_name(tmp_path: Path) -> None:
    local = ["--local", str(tmp_path)]
    round_of = ["--split", "dev", "--tasks", "X01", "--model", "haiku"]
    excel_eval.main(["batch", "C", *round_of, "--round", "x1", *local])
    (tmp_path / "excel" / "runs" / "x1" / "c-1").joinpath("answers.md").write_text(
        "## X01\n\nNo SQL.\nUsed: 11:F4, 15:W1, 12:Q1, 11:Q1\n", encoding="utf-8")
    excel_eval.main(["collect", "x1", *local])
    excel_eval.main(["score", "x1", *local])
    [kept] = eval_sources.read_sources(tmp_path)
    assert (kept.pipeline, kept.task, kept.result) == ("excel", "X01", "fail")
    assert kept.cited == "11:F4;15:W1;12:Q1" and kept.unknown == "11:Q1"


def test_a_metric_round_keeps_the_ids_copilot_used_across_its_turns(tmp_path: Path) -> None:
    local = ["--local", str(tmp_path)]
    metric_eval.main(["start", "C", "--round", "r1", "--split", "dev", "--model", "haiku",
                      "--only", "M01", *local])
    folder = tmp_path / "metric" / "r1" / "M01"
    (folder / "turn-01-copilot.md").write_text("Which column?\nUsed: A1, D1\nasked",
                                               encoding="utf-8")
    (folder / "turn-01-user.md").write_text("This one.", encoding="utf-8")
    (folder / "turn-02-copilot.md").write_text(
        metric_eval.BY_ID["M01"].example + "\nUsed: A2, G1, D1", encoding="utf-8")
    metric_eval.main(["next", str(folder), *local])
    metric_eval.main(["score", "r1", "C", "--split", "dev", "--model", "haiku",
                      "--only", "M01", *local])
    [kept] = eval_sources.read_sources(tmp_path)
    assert (kept.pipeline, kept.task, kept.result) == ("metric", "M01", "pass")
    assert kept.cited == "19:A1;19:D1;19:A2;19:G1"


def test_a_used_line_after_the_metric_request_is_not_part_of_the_request() -> None:
    request = metric_eval.BY_ID["M01"].example
    assert metric_eval.request_in(request + "\nUsed: A1, Q7\n") == (
        metric_eval.request_in(request))


# --- The instructions that ask for the lines -------------------------------------------------


@pytest.mark.parametrize("agent", ["copilot-proxy", "metric-proxy"])
def test_each_proxy_is_told_to_end_its_reply_with_a_used_line(agent: str) -> None:
    text = (AGENTS / f"{agent}.md").read_text(encoding="utf-8")
    assert "Used:" in text


def test_the_zero_context_user_is_told_to_end_with_a_read_line() -> None:
    assert "Read:" in (AGENTS / "zero-context-user.md").read_text(encoding="utf-8")


def test_arm_c_messages_ask_for_a_used_line_and_arm_r_doesnt() -> None:
    tasks = [BY_ID["T07"]]
    assert "Used:" in copilot_eval.proxy_message("C", tasks)
    assert "Used:" not in copilot_eval.proxy_message("R", tasks)
    assert "Used:" in excel_eval.proxy_message("C", excel_eval.tasks_of("dev")[:1])
    assert "Used:" in metric_eval.copilot_message(metric_eval.BY_ID["M01"])

"""The Templates the Toolbox ships, which project.start() copies into admin/templates/.

Toolbox 6.0's ticket 09, and 7.0's ticket 04, which left two Table notebook Templates, with no
day in either. Each is made into a Table folder's notebook by project.new_table, filled in with
the Example database's tables as a user fills it in, and its logic cell loaded: each code cell
parses, write() writes the table into the Partitions its rows fill, or the whole table when it
isn't partitioned, and preview() runs on the Example database. Every Template lists every
placeholder it holds in its first lines, with an example. The Saved table's Table reference and
the Building block Templates, filled in, run.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pandas as pd
import pytest

from sqlglot_composer import example_database, notebooks, project, run_query, set_admin_log, to_hive
from sqlglot_composer.project import TableLogic
from sqlglot_composer.project_templates import (
    BUILDING_BLOCK,
    NOTEBOOK_TEMPLATES,
    SAVED_TABLE_REFERENCE,
    TEMPLATES,
)

ROOT = Path(__file__).resolve().parent.parent

PLACEHOLDER = re.compile(r"<([A-Z][A-Z0-9_]*)>")
# What new_table and new_block fill in themselves; every other placeholder is the user's.
FILLED_BY_PROJECT_ACTIONS = {"DB", "TABLE", "NAME", "BLOCK"}
DAY = "2026-09-24"
# Each Table notebook Template's placeholders, filled in for the Example database, the columns
# its Saved table holds, its partition columns and its Key.
FILLS = {
    "saved_table": ({"<SOURCE_NAME>": "ops__job_runs", "<SOURCE_TABLE>": "job_runs",
                     "<READS>": f'equals(job_runs.dt, "{DAY}")', "<GROUP_COLUMN>": "job_id",
                     "<COUNT_NAME>": '"runs"', "<PARTITION_COLUMN>": "dt"},
                    {"job_id": "bigint", "runs": "bigint", "dt": "string"}, ["dt"],
                    ["job_id", "dt"]),
    "quality_checks": ({"<CHECKED_NAME>": "ops__job_events", "<CHECKED>": "job_events",
                        "<READS>": f'equals(job_events.dt, "{DAY}")',
                        "<PARTITION_COLUMN>": "dt", "<KEY_COLUMN>": "event_id"},
                       {"row_count": "bigint", "dt": "string"}, ["dt"], ["dt"]),
}
# The same Templates filled in for a table partitioned by region alone, ops.region_budgets.
REGION_FILLS = {
    "saved_table": ({"<SOURCE_NAME>": "ops__region_budgets", "<SOURCE_TABLE>": "region_budgets",
                     "<READS>": 'equals(region_budgets.region, "eu")',
                     "<GROUP_COLUMN>": "job_id", "<COUNT_NAME>": '"budgets"',
                     "<PARTITION_COLUMN>": "region"},
                    {"job_id": "bigint", "budgets": "bigint", "region": "string"}, ["region"],
                    ["job_id", "region"]),
    "quality_checks": ({"<CHECKED_NAME>": "ops__region_budgets", "<CHECKED>": "region_budgets",
                        "<READS>": 'equals(region_budgets.region, "eu")',
                        "<PARTITION_COLUMN>": "region", "<KEY_COLUMN>": "job_id"},
                       {"row_count": "bigint", "region": "string"}, ["region"], ["region"]),
}


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A Project with the Table references of the Example database's tables the fills read."""
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    project.add_references(["ops.job_runs", "ops.job_events", "ops.region_budgets",
                            "ops.team_notes"], query=example_database.query)
    return tmp_path


def saved_reference(name: str, columns: dict[str, str], partitioned_by: list[str],
                    key: list[str] | None) -> str:
    """A Saved table's Table reference, as a user fills in the one new_table wrote."""
    table = name.split(".")[1]
    return (f"from sqlglot_composer import Table\n\n{table} = Table(\n    {name!r},\n"
            f"    columns={columns!r},\n    partitioned_by={partitioned_by!r},\n"
            f"    key={key!r},\n    location='/data/your_team/mart.db/{table}',\n)\n")


def filled_notebook(root: Path, template: str, name: str,
                    fill: tuple[dict[str, str], dict[str, str], list[str], list[str] | None],
                    unpartitioned: bool = False) -> list[str]:
    """Make the table from the Template with new_table, fill in its notebook's placeholders as
    `fill` says and write its Table reference: each code cell's text. `unpartitioned` deletes
    the lines that name the partition column, as a table with none does, and READS and WHERE,
    to read the whole of a table that isn't partitioned."""
    fills, columns, partitioned_by, key = fill
    project.new_table(name, template=template)
    stem = name.replace(".", "__")
    (root / "references" / f"{stem}.py").write_text(
        saved_reference(name, columns, partitioned_by, key), encoding="utf-8")
    path = root / "tables" / stem / f"{stem}.ipynb"
    filled = []
    for kind, text in notebooks.read_cells(path):
        if unpartitioned and kind == "code":
            text = "".join(line for line in text.splitlines(keepends=True)
                           if "<PARTITION_COLUMN>" not in line
                           and line.strip() not in ("READS = <READS>", "WHERE(READS),"))
        for placeholder, value in fills.items():
            text = text.replace(placeholder, value)
        filled.append((kind, text))
    notebooks.write_notebook(path, filled)
    return [text for kind, text in filled if kind == "code"]


def listed(text: str) -> set[str]:
    """The placeholders a Template's first lines list: the lines after "They are:", up to the
    first empty one, which come in its first six lines."""
    lines = text.splitlines()
    start = next(index for index, line in enumerate(lines) if line.endswith("They are:"))
    assert start < 6, lines[:start + 1]
    listing = []
    for line in lines[start + 1:]:
        if line.strip() in ("", "#"):
            break
        listing.append(line)
    return set(PLACEHOLDER.findall("\n".join(listing))) - FILLED_BY_PROJECT_ACTIONS


@pytest.mark.parametrize("template", TEMPLATES)
def test_a_templates_first_lines_list_every_placeholder_it_holds(template: str) -> None:
    text = TEMPLATES[template]
    held = set(PLACEHOLDER.findall(text)) - FILLED_BY_PROJECT_ACTIONS
    assert listed(text) == held


@pytest.mark.parametrize("template", NOTEBOOK_TEMPLATES)
def test_the_fills_fill_every_placeholder(template: str) -> None:
    held = set(PLACEHOLDER.findall(NOTEBOOK_TEMPLATES[template])) - FILLED_BY_PROJECT_ACTIONS
    for fills in (FILLS, REGION_FILLS):
        assert {placeholder[1:-1] for placeholder in fills[template][0]} == held


@pytest.mark.parametrize("template", TEMPLATES)
def test_no_template_speaks_of_a_day(template: str) -> None:
    text = TEMPLATES[template]
    assert "<DAY>" not in text and "DAY =" not in text and "first_day" not in text
    assert '"dt"' not in text and "Date partition" not in text and "DATE_PARTITION" not in text


@pytest.mark.parametrize("template", NOTEBOOK_TEMPLATES)
def test_a_filled_notebook_has_five_code_cells_that_parse(started: Path, template: str) -> None:
    code = filled_notebook(started, template, f"mart.made_from_{template}", FILLS[template])
    assert len(code) == 5
    assert code[1].startswith("# logic\n")
    for text in code:
        assert not PLACEHOLDER.search(text), text
        ast.parse(text)


@pytest.mark.parametrize(("template", "fills", "partition"), [
    (template, fills, partition) for template in NOTEBOOK_TEMPLATES
    for fills, partition in ((FILLS, "dt"), (REGION_FILLS, "region"))])
def test_a_filled_notebooks_logic_writes_the_partitions_its_rows_fill(
        started: Path, template: str,
        fills: dict[str, tuple[dict[str, str], dict[str, str], list[str], list[str] | None]],
        partition: str) -> None:
    name = f"mart.{template}_by_{partition}"
    filled_notebook(started, template, name, fills[template])
    logic = project.load(name)
    hive = to_hive(logic.write())
    # The partition comes from the rows, last in the SELECT, into its Partition of the table.
    assert hive.split("\n")[0] == f"INSERT OVERWRITE TABLE {name} PARTITION({partition})"
    assert re.search(rf"\.{partition}\nFROM ", hive), hive
    preview = run_query(logic.preview(), example_database.query)
    assert isinstance(preview, pd.DataFrame) and len(preview) > 0
    assert list(preview.columns)[-1] == partition
    assert set(preview[partition]) == {DAY if partition == "dt" else "eu"}


@pytest.mark.parametrize("template", NOTEBOOK_TEMPLATES)
def test_a_notebook_for_a_table_with_no_partitions_writes_it_whole(
        started: Path, template: str) -> None:
    """Its partition column's lines and READS deleted, a Template writes a table that isn't
    partitioned, read from a table that isn't either, ops.team_notes, whole."""
    fills = {"saved_table": ({"<SOURCE_NAME>": "ops__team_notes", "<SOURCE_TABLE>": "team_notes",
                              "<GROUP_COLUMN>": "team", "<COUNT_NAME>": '"notes"'},
                             {"team": "string", "notes": "bigint"}, [], None),
             "quality_checks": ({"<CHECKED_NAME>": "ops__team_notes",
                                 "<CHECKED>": "team_notes", "<KEY_COLUMN>": "team"},
                                {"row_count": "bigint"}, [], None)}[template]
    name = f"mart.{template}_whole"
    for text in filled_notebook(started, template, name, fills, unpartitioned=True):
        assert not PLACEHOLDER.search(text), text
    logic = project.load(name)
    hive = to_hive(logic.write())
    assert hive.split("\n")[0] == f"INSERT OVERWRITE TABLE {name}"
    assert "WHERE" not in hive
    preview = run_query(logic.preview(), example_database.query)
    expected = ({"data": 2, "finance": 2, "web": 1} if template == "saved_table"
                else {"row_count": 5})
    assert (preview.set_index("team").notes.to_dict() if template == "saved_table"
            else {"row_count": int(preview.row_count.iloc[0])}) == expected


@pytest.mark.parametrize("template", NOTEBOOK_TEMPLATES)
def test_a_templates_functions_take_nothing(template: str) -> None:
    cell = next(cell for cell in NOTEBOOK_TEMPLATES[template].split("# %%\n")
                if cell.startswith("# logic\n"))
    # Each placeholder made a name, so the cell parses before it is filled in.
    logic = ast.parse(PLACEHOLDER.sub(r"_\1", cell))
    defined = {node.name: node for node in logic.body if isinstance(node, ast.FunctionDef)}
    assert {"create", "rows", "preview", "write"} <= set(defined)
    for name, function in defined.items():
        if name != "column_name":
            assert not function.args.args, (template, name)
    assert "write_day" not in defined and "by_day" not in NOTEBOOK_TEMPLATES[template]
    # The rows it reads are a constant in the logic cell, filled in from <READS>.
    assert any(isinstance(node, ast.Assign) and node.targets[0].id == "READS"
               for node in logic.body)


def test_quality_checks_find_no_repeated_keys_on_the_example_database(started: Path) -> None:
    name = "mart.made_from_quality_checks"
    filled_notebook(started, "quality_checks", name, FILLS["quality_checks"])
    logic = project.load(name)
    assert len(run_query(logic.repeated_keys(), example_database.query)) == 0
    nulls = run_query(logic.null_counts(), example_database.query)
    assert list(nulls.columns)[0] == "null_event_id"


def logic_reading(root: Path, name: str, lines: str) -> TableLogic:
    """The logic of a table made from a one-cell Template of `lines`, which reads what a
    Template under test was filled in to make."""
    # load needs a write(), which these readers have no use for.
    (root / "admin" / "templates" / "reader.py").write_text(
        f"# %%\n# logic\n{lines}\n\ndef write() -> None:\n    return None\n",
        encoding="utf-8")
    project.new_table(name, template="reader")
    return project.load(name)


def filled_reference(**more: str) -> str:
    """The Saved table's Table reference Template, filled in for mart.daily_runs."""
    text = SAVED_TABLE_REFERENCE
    for placeholder, value in {"<DB>": "mart", "<TABLE>": "daily_runs",
                               "<NAME>": "mart__daily_runs", "<COLUMN>": '"job_id"',
                               "<COLUMN_TYPE>": '"bigint"',
                               "<LOCATION>": '"/data/your_team/mart.db/daily_runs"',
                               **more}.items():
        text = text.replace(placeholder, value)
    return text


def test_the_saved_table_reference_template_filled_in_is_a_table(started: Path) -> None:
    (started / "references" / "mart__daily_runs.py").write_text(filled_reference(),
                                                                 encoding="utf-8")
    logic = logic_reading(started, "mart.reader", "from references.mart__daily_runs import "
                          "daily_runs\n\n\ndef table():\n    return daily_runs\n")
    table = logic.table()
    assert repr(table) == "Table('mart.daily_runs', columns: job_id)"
    # Neither partitioned nor keyed until you say so.
    assert table._partitioned_by == [] and table._key is None


def test_the_saved_table_reference_template_takes_any_partition_column(started: Path) -> None:
    text = filled_reference().replace(
        '        "job_id": "bigint",', '        "job_id": "bigint",\n        "region": "string",'
    ).replace("partitioned_by=[],", 'partitioned_by=["region"],').replace(
        "key=None,", 'key=["job_id", "region"],')
    (started / "references" / "mart__daily_runs.py").write_text(text, encoding="utf-8")
    logic = logic_reading(started, "mart.reader", "from references.mart__daily_runs import "
                          "daily_runs\n\n\ndef table():\n    return daily_runs\n")
    assert logic.table()._partitioned_by == ["region"]


def test_the_building_block_template_filled_in_is_a_derived_table(started: Path) -> None:
    """new_block makes the file, filling in <BLOCK>; the user fills in the rest."""
    project.new_block("minutes_per_job")
    block = started / "building_blocks" / "minutes_per_job.py"
    text = block.read_text(encoding="utf-8")
    assert text == BUILDING_BLOCK.replace("<BLOCK>", "minutes_per_job")
    for placeholder, value in {"<SOURCE_NAME>": "ops__job_runs", "<SOURCE_TABLE>": "job_runs",
                               "<GROUP_COLUMN>": "job_id", "<NUMBER_COLUMN>": "duration_mins",
                               "<TOTAL_NAME>": '"minutes"'}.items():
        text = text.replace(placeholder, value)
    block.write_text(text, encoding="utf-8")
    logic = logic_reading(started, "mart.reader", "from building_blocks.minutes_per_job "
                          "import minutes_per_job\nfrom references.ops__job_runs import "
                          "job_runs\nfrom sqlglot_composer import equals\n\n\ndef block(day):\n"
                          "    return minutes_per_job(equals(job_runs.dt, day))\n")
    assert repr(logic.block(DAY)) == (
        "derived('minutes_per_job', columns: job_id, row_count, minutes)")


def test_the_readme_names_each_template_the_toolbox_ships() -> None:
    readme = (ROOT / "docs" / "clean-branch-readme.md").read_text(encoding="utf-8")
    section = readme.split("## Templates\n", 1)[1].split("\n## ", 1)[0]
    assert re.findall(r"^- `(\w+)`: ", section, re.MULTILINE) == list(TEMPLATES)

"""The templates in `templates/`: what each asks you to fill in, and that, filled in, it runs.

A template is one of the user's scripts with its specifics left as placeholders written
`<UPPER_SNAKE>`, such as `<TABLE>`, each listed in its docstring's "Fill in:" block. A
placeholder stands where Python code goes, never inside quotes, so a template with any one of
them left in doesn't parse, and can't run half filled in.

Each template is then filled in from FILLS, with the Example database's values, and written
where its "Copy it to:" line says, in a project folder made for the test. The folder also holds
the Example project's Table references, and for the intermediate templates its Building blocks,
which the filled templates import as a user's own. Every Statement a template's functions give
is built; a write is checked only through to_hive, and each SELECT runs on the Example
database. A SELECT sqlglot's executor can't run, with row_number or week_start, runs only in
Spark Composer's run, and is skipped in sqlglot Composer's with the reason. One that reads a
Saved table, which only a warehouse holds, runs with the Saved table stood in for by the rows
the template that writes it previews.
"""

from __future__ import annotations

import ast
import datetime
import importlib
import inspect
import re
import shutil
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

import editions
from conftest import (
    INSERT, ROOT, edition, project_on_the_path, standing_in, toolbox_module, without_the_write,
)
from sqlglot_composer import (
    FROM, SELECT, Table, all_columns, create_table, example_database, run, statement, to_hive,
)

TEMPLATES = ROOT / "templates"
EXAMPLE_PROJECTS = ROOT / "example_projects"
NAMES = {
    "starter": ["building_block.py", "daily_pipeline.py", "keep_table_references_true.py",
                "notebook_start.py", "per_group_statement.py", "saved_table.py",
                "table_reference.py"],
    "intermediate": ["as_of_lookup.py", "building_blocks.py", "incremental_load.py",
                     "quality_statements.py", "settings_driven.py", "weekly_rollup.py"],
}
PLACEHOLDER = re.compile(r"<[A-Z][A-Z0-9_]*>")
LISTED = re.compile(r"^    (<[A-Z][A-Z0-9_]*>): ", re.MULTILINE)
COPY_IT_TO = re.compile(r"^Copy it to: (\S+\.py)", re.MULTILINE)
MIRRORS = re.compile(r"example_projects/[\w/]+\.(?:py|md)")
LEVEL_FOLDERS = ("table_references", "building_blocks", "statements")

# Example database values for each placeholder, as a user would type them: a name as it is, a
# text in quotes.
FILLS = {
    "starter": {
        "<RUN_HIVE>": "example_database.send(hive)",
        "<TABLE>": "job_runs",
        "<DATE_PARTITION>": "dt",
        "<DAY>": '"2026-09-24"',
        "<SAVED_TABLE>": "job_day_minutes",
        "<SAVED_TABLE_NAME>": '"mart.job_day_minutes"',
        "<GROUP_COLUMN>": "job_id",
        "<GROUP_COLUMN_NAME>": '"job_id"',
        "<GROUP_COLUMN_TYPE>": '"bigint"',
        "<NUMBER_COLUMN>": "duration_mins",
        "<TOTAL>": "minutes",
        "<TOTAL_NAME>": '"minutes"',
        "<BLOCK>": "minutes_per_job_day",
        "<BLOCK_NAME>": '"minutes_per_job_day"',
        "<MORE_THAN_ROWS>": "1",
        "<NEW_TABLE_NAME>": '"ops.job_events"',
    },
    "intermediate": {
        "<SAVED_TABLE>": "job_day_costs",
        "<BLOCK>": "costs_per_job_day",
        "<GROUP_COLUMN>": "job_id",
        "<TOTAL>": "cost_cents",
        "<TOTAL_NAME>": '"cost_cents"',
        "<DAYS_REWRITTEN>": "3",
        "<TABLE>": "job_events",
        "<MATCH_COLUMN>": "job_id",
        "<DATE_PARTITION>": "dt",
        "<SNAPSHOT>": "job_owners",
        "<SNAPSHOT_MATCH_COLUMN>": "job_id",
        "<SNAPSHOT_DATE_PARTITION>": "dt",
        "<LOOKED_UP_COLUMN>": "team",
        "<SNAPSHOT_DAYS>": "7",
        "<EXPECTED_TABLE>": "job_owners",
        "<EXPECTED_MATCH_COLUMN>": "job_id",
        "<EXPECTED_DATE_PARTITION>": "dt",
        "<KEY_COLUMN>": "event_id",
        "<FIRST_TABLE>": "region_costs",
        "<FIRST_DATE_PARTITION>": "dt",
        "<ADD_UP_COLUMN>": "cost_cents",
        "<SECOND_TABLE>": "job_events",
        "<SECOND_DATE_PARTITION>": "dt",
    },
}
# The Example project's folders each set's filled templates import from.
FROM_THE_EXAMPLE_PROJECT = {"starter": ("table_references",),
                            "intermediate": ("table_references", "building_blocks")}
# The days each set's Statements are built for: two of the Example database's days for the
# starter's ops.job_runs, the last 3 of its 14 for the intermediate tables.
DAYS = {"starter": ("2026-09-23", "2026-09-24"), "intermediate": ("2026-09-22", "2026-09-24")}
ALL_DAYS = ("2026-09-11", "2026-09-24")  # every day the intermediate tables hold
# A notebook's first cell runs as it is imported, so it is imported in a test of its own.
RUNS_WHEN_IMPORTED = "notebook_start"
# The SELECTs sqlglot Composer's Example database can't run, by set, template and function.
NO_WINDOW_FUNCTIONS = ("sqlglot's executor has no window functions, so it can't run "
                       "row_number: Spark Composer's run checks it")
NO_WEEK_START = ("sqlglot's executor has no NEXT_DAY, so it can't run week_start: Spark "
                 "Composer's run checks it")
NOT_ON_SQLGLOTS_EXECUTOR = {
    ("intermediate", "as_of_lookup", "newest_per_key"): NO_WINDOW_FUNCTIONS,
    ("intermediate", "weekly_rollup", "week_totals"): NO_WEEK_START,
}


def templates() -> list[Path]:
    return sorted(TEMPLATES.glob("*/*.py"))


def template_id(path: Path) -> str:
    return f"{path.parent.name}/{path.name}"


def docstring(text: str) -> str:
    """A template's docstring, read as text: ast can't read one from a file that doesn't
    parse."""
    return text.split('"""')[1]


def code(text: str) -> str:
    """A template without its docstring."""
    return text.split('"""', 2)[2]


def listed(text: str) -> list[str]:
    """The placeholders the docstring's "Fill in:" block lists, in its order."""
    return LISTED.findall(docstring(text).split("\nFill in:\n")[1])


def filled(text: str, fills: dict[str, str], leave: str | None = None) -> str:
    """The template with each placeholder replaced by its fill, but `leave` left in."""
    return PLACEHOLDER.sub(lambda m: m.group(0) if m.group(0) == leave else fills[m.group(0)],
                           text)


def copied_to(text: str) -> str:
    """Where the docstring's "Copy it to:" line puts the template, in the user's project."""
    return COPY_IT_TO.search(docstring(text)).group(1)


def module_name(relative: str) -> str:
    """The module a notebook in the project's folder imports a script by."""
    return relative.removesuffix(".py").replace("/", ".")


# --- The placeholders --------------------------------------------------------------------------


def test_there_are_both_sets_of_templates() -> None:
    found = {name: sorted(path.name for path in (TEMPLATES / name).glob("*.py"))
             for name in NAMES}
    assert found == NAMES
    assert sorted(path.name for path in TEMPLATES.iterdir()) == sorted(NAMES)


@pytest.mark.parametrize("path", templates(), ids=template_id)
def test_each_placeholder_is_listed_once_and_each_listed_one_is_used(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    names = listed(text)
    assert names, f"{template_id(path)} lists no placeholder under Fill in:"
    assert len(names) == len(set(names)), f"listed twice: {names}"
    assert set(PLACEHOLDER.findall(code(text))) == set(names)
    assert set(PLACEHOLDER.findall(docstring(text))) <= set(names)


@pytest.mark.parametrize("path", templates(), ids=template_id)
def test_a_template_with_any_placeholder_left_in_doesnt_parse(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    fills = FILLS[path.parent.name]
    with pytest.raises(SyntaxError):
        ast.parse(text)
    for name in listed(text):
        with pytest.raises(SyntaxError):
            ast.parse(filled(text, fills, leave=name))


@pytest.mark.parametrize("path", templates(), ids=template_id)
def test_filled_in_it_parses(path: Path) -> None:
    ast.parse(filled(path.read_text(encoding="utf-8"), FILLS[path.parent.name]))


def test_every_fill_is_a_placeholder_of_its_set() -> None:
    for name, fills in FILLS.items():
        used = {placeholder for path in (TEMPLATES / name).glob("*.py")
                for placeholder in listed(path.read_text(encoding="utf-8"))}
        assert set(fills) == used, name


@pytest.mark.parametrize("path", templates(), ids=template_id)
def test_each_template_says_where_it_goes_and_which_files_it_mirrors(path: Path) -> None:
    text = docstring(path.read_text(encoding="utf-8"))
    assert COPY_IT_TO.search(text), f"{template_id(path)} has no 'Copy it to:' line"
    mirrored = MIRRORS.findall(" ".join(text.split()))
    assert mirrored, f"{template_id(path)} names no Example project file it mirrors"
    assert [m for m in mirrored if not (ROOT / m).is_file()] == []


@pytest.mark.parametrize("path", templates(), ids=template_id)
def test_each_template_can_be_named_for_either_edition(path: Path) -> None:
    """The export copies each template for each Edition through editions.named_for, which
    refuses text that would still name sqlglot Composer in Spark Composer's copy."""
    text = path.read_text(encoding="utf-8")
    for each in (editions.SQLGLOT_COMPOSER, editions.SPARK_COMPOSER):
        named = editions.named_for(each, text, where=template_id(path))
        assert f"from {each.folder} import" in named


# --- Filled in, in a project folder --------------------------------------------------------------


def filled_project(name: str, folder: Path):
    """The set's templates filled in, each written where it says, beside the Example project's
    folders they import. Yields what each template became, by its name, such as
    "saved_table": the folder, the path it was written to and its module, imported while the
    project is on the path. notebook_start's isn't imported, since it runs as it is imported."""
    for copied in FROM_THE_EXAMPLE_PROJECT[name]:
        shutil.copytree(EXAMPLE_PROJECTS / name / copied, folder / copied,
                        ignore=shutil.ignore_patterns("__pycache__"))
    written = {}
    for path in sorted((TEMPLATES / name).glob("*.py")):
        text = filled(path.read_text(encoding="utf-8"), FILLS[name])
        relative = copied_to(text)
        (folder / relative).parent.mkdir(parents=True, exist_ok=True)
        (folder / relative).write_text(text, encoding="utf-8")
        written[path.stem] = relative
    top_names = tuple({module_name(relative).split(".")[0] for relative in written.values()}
                      | set(LEVEL_FOLDERS))
    with project_on_the_path(folder, top_names):
        yield {stem: SimpleNamespace(
                   folder=folder, relative=relative,
                   module=None if stem == RUNS_WHEN_IMPORTED
                   else importlib.import_module(module_name(relative)))
               for stem, relative in written.items()}


@pytest.fixture(scope="module")
def starter(tmp_path_factory) -> dict:
    yield from filled_project("starter", tmp_path_factory.mktemp("starter"))


@pytest.fixture(scope="module")
def intermediate(tmp_path_factory) -> dict:
    yield from filled_project("intermediate", tmp_path_factory.mktemp("intermediate"))


def statements_in(result) -> list:
    """The Statements a function gives: one, a list or a dict of them, or a Building block's
    Derived table, read whole by a Statement."""
    statement_type = toolbox_module("clauses").Statement
    values = (result.values() if isinstance(result, dict)
              else result if isinstance(result, list) else [result])
    found = []
    for value in values:
        if isinstance(value, statement_type):
            found.append(value)
        elif isinstance(value, Table) and value._statement is not None:
            found.append(statement(SELECT(all_columns(value)), FROM(value)))
    return found


def built_by(module, days: tuple[str, str]) -> dict[str, list]:
    """Each function the module defines whose parameters are days, by name, with the
    Statements it gives for those days."""
    given = {"day": days[-1], "first_day": days[0], "last_day": days[-1]}
    found = {}
    for name, function in vars(module).items():
        if not inspect.isfunction(function) or function.__module__ != module.__name__:
            continue
        parameters = inspect.signature(function).parameters
        if not set(parameters) <= set(given):
            continue
        built = statements_in(function(**{p: given[p] for p in parameters}))
        if built:
            found[name] = built
    return found


def at_a_level(name: str) -> list[str]:
    """The templates of a set that are copied into a Level folder."""
    return [path.stem for path in sorted((TEMPLATES / name).glob("*.py"))
            if copied_to(path.read_text(encoding="utf-8")).split("/")[0] in LEVEL_FOLDERS]


LEVEL_TEMPLATES = [(name, stem) for name in NAMES for stem in at_a_level(name)]


def level_id(case: tuple[str, str]) -> str:
    return "/".join(case)


@pytest.mark.parametrize("case", LEVEL_TEMPLATES, ids=level_id)
def test_each_statement_it_builds_becomes_hive(request, case: tuple[str, str]) -> None:
    name, stem = case
    module = request.getfixturevalue(name)[stem].module
    if stem == "table_reference":
        (saved,) = [value for value in vars(module).values() if isinstance(value, Table)]
        assert to_hive(create_table(saved)).startswith("CREATE TABLE")
        return
    built = built_by(module, DAYS[name])
    assert built, f"{stem} builds no Statement"
    for function, statements in built.items():
        assert all(to_hive(s) for s in statements), f"{stem}.{function}"


def runnable_selects(name: str, stem: str, module) -> dict[str, list]:
    """Each function's SELECTs that either Example database runs: none that reads a Saved
    table, and none that NOT_ON_SQLGLOTS_EXECUTOR names, which a test of their own runs."""
    found = {}
    for function, statements in built_by(module, DAYS[name]).items():
        if (name, stem, function) in NOT_ON_SQLGLOTS_EXECUTOR:
            continue
        selects = [s for s in statements if s._ddl is None and s._write is None
                   and "mart." not in to_hive(s)]
        if selects:
            found[function] = selects
    return found


# What each Level template's SELECTs are, by function, besides those NOT_ON_SQLGLOTS_EXECUTOR
# names: weekly_rollup's only SELECT reads a Saved table, and is run with it stood in for.
RUNNABLE = {
    ("starter", "building_block"): ["minutes_per_job_day"],
    ("starter", "per_group_statement"): ["per_group"],
    ("starter", "saved_table"): ["preview"],
    ("starter", "table_reference"): [],
    ("intermediate", "as_of_lookup"): ["rows_as_of_their_day"],
    ("intermediate", "building_blocks"): ["keys_expected", "keys_seen"],
    ("intermediate", "incremental_load"): ["preview"],
    ("intermediate", "quality_statements"): ["null_counts", "repeated_keys", "rows_per_day"],
    ("intermediate", "settings_driven"): ["every_daily_total"],
    ("intermediate", "weekly_rollup"): [],
}


@pytest.mark.needs_example_database
@pytest.mark.parametrize("case", LEVEL_TEMPLATES, ids=level_id)
def test_each_select_it_builds_runs_on_the_example_database(request, case) -> None:
    name, stem = case
    module = request.getfixturevalue(name)[stem].module
    selects = runnable_selects(name, stem, module)
    assert sorted(selects) == RUNNABLE[case]
    for statements in selects.values():
        for s in statements:
            assert isinstance(run(s, send=example_database.send), pd.DataFrame)


@pytest.mark.needs_example_database
@pytest.mark.parametrize("case", sorted(NOT_ON_SQLGLOTS_EXECUTOR), ids=level_id)
def test_what_sqlglots_executor_cant_run_runs_on_spark(request, case) -> None:
    name, stem, function = case
    if edition() is editions.SQLGLOT_COMPOSER:
        pytest.skip(NOT_ON_SQLGLOTS_EXECUTOR[case])
    project = request.getfixturevalue(name)
    days = ALL_DAYS if stem == "weekly_rollup" else DAYS[name]
    (built,) = built_by(project[stem].module, days)[function]
    hive = to_hive(built)
    if stem == "weekly_rollup":
        hive = standing_in(hive, {"job_day_costs": costs_saved(project, ALL_DAYS)})
    rows = example_database.send(hive)
    assert len(rows) > 0
    if stem == "weekly_rollup":
        assert set(rows.week) == {"2026-09-07", "2026-09-14", "2026-09-21"}
    if stem == "as_of_lookup":
        assert rows.job_id.is_unique


# --- Each template, filled in ------------------------------------------------------------------


@pytest.mark.needs_example_database
def test_notebook_start_runs_its_first_statement(starter: dict, capsys) -> None:
    importlib.import_module(module_name(starter["notebook_start"].relative))
    printed = capsys.readouterr().out
    assert "one" in printed
    assert "WHERE\n  job_runs.dt = '2026-09-24'\nLIMIT 20;" in printed
    assert "run_id" in printed.split("LIMIT 20;")[1]


def days_written(writes: list) -> list[str]:
    return [to_hive(write).split("PARTITION(dt = '")[1][:10] for write in writes]


def test_a_saved_tables_preview_is_the_select_its_write_sends(starter: dict) -> None:
    module = starter["saved_table"].module
    for day in DAYS["starter"]:
        assert without_the_write(to_hive(module.write_day(day))) == to_hive(module.preview(day))
    assert days_written(module.backfill(*DAYS["starter"])) == list(DAYS["starter"])


def test_an_incremental_load_writes_the_last_days_oldest_first(intermediate: dict) -> None:
    module = intermediate["incremental_load"].module
    assert module.first_day_written("2026-09-24") == "2026-09-22"
    writes = module.write_last_days("2026-09-24")
    assert days_written(writes) == ["2026-09-22", "2026-09-23", "2026-09-24"]
    assert [to_hive(w) for w in writes] == [
        to_hive(w) for w in module.write_days("2026-09-22", "2026-09-24")]


@pytest.mark.needs_example_database
def test_each_day_an_incremental_load_writes_saves_what_its_preview_shows(
        intermediate: dict) -> None:
    module = intermediate["incremental_load"].module
    for day, write in zip(["2026-09-22", "2026-09-23", "2026-09-24"],
                          module.write_last_days("2026-09-24"), strict=True):
        saved = example_database.send(without_the_write(to_hive(write)))
        pd.testing.assert_frame_equal(saved, run(module.preview(day), send=example_database.send),
                                      check_dtype=False)


def test_the_daily_pipeline_sends_each_step_in_order(starter: dict, capsys) -> None:
    pipeline = starter["daily_pipeline"].module
    steps = pipeline.steps("2026-09-24")
    hive = [to_hive(s) for s in steps]
    assert hive[0].startswith("CREATE TABLE IF NOT EXISTS mart.job_day_minutes")
    assert f"{INSERT} mart.job_day_minutes PARTITION(dt = '2026-09-24')" in hive[1]
    sent = []
    pipeline.send_all(sent.append, "2026-09-24")
    assert sent == hive
    pipeline.dry_run(pipeline.DAY)
    printed = capsys.readouterr().out
    for position, (variable, text) in enumerate(
            zip(["create_job_day_minutes", "write_job_day_minutes"], hive), start=1):
        assert f"-- {position} of 2: {variable}\n{text};" in printed


def test_the_daily_pipeline_writes_its_lineage_files(starter: dict) -> None:
    project = starter["daily_pipeline"]
    project.module.write_lineage_files("2026-09-24")
    lineage = project.folder / "lineage"
    assert sorted(path.name for path in lineage.iterdir()) == ["pipeline.html", "pipeline.md"]
    assert "mart.job_day_minutes" in (lineage / "pipeline.md").read_text(encoding="utf-8")


@pytest.mark.needs_example_database
def test_keeping_table_references_true_writes_new_ones_and_compares_the_rest(
        starter: dict, capsys) -> None:
    references = starter["keep_table_references_true"]
    folder = references.folder / "table_references"
    (written,) = references.module.write_new_table_references(example_database.send)
    assert written == folder / "job_events.py"
    assert "TODO" in written.read_text(encoding="utf-8")
    assert references.module.write_new_table_references(example_database.send) == []
    assert "ops.job_events: its Table reference is there already" in capsys.readouterr().out
    references.module.compare_with_the_tables(example_database.send)
    printed = capsys.readouterr().out
    assert printed == ("ops.job_runs matches its Table reference.\n"
                       "ops.job_runs: the key (run_id) holds on 2026-09-24.\n")


@pytest.mark.needs_example_database
def test_the_blocks_built_from_blocks_find_each_key_missing(intermediate: dict) -> None:
    blocks = intermediate["building_blocks"].module
    days = DAYS["intermediate"]
    missing = blocks.keys_missing(blocks.keys_expected(*days), blocks.keys_seen(*days))
    rows = run(statement(SELECT(all_columns(missing)), FROM(missing)), send=example_database.send)
    # report_build, on days it didn't run, and cache_warm, as the Example project's
    # quality_checks.jobs_not_run finds
    assert set(rows.job_id) == {3, 4}


@pytest.mark.needs_example_database
def test_the_quality_statements_run_all_together(intermediate: dict) -> None:
    found = intermediate["quality_statements"].module.run_all(example_database.send,
                                                              *DAYS["intermediate"])
    assert list(found) == ["repeated_keys", "null_counts", "rows_per_day"]
    assert len(found["repeated_keys"]) == 0
    assert list(found["rows_per_day"].dt) == ["2026-09-22", "2026-09-23", "2026-09-24"]


def test_the_settings_make_a_statement_per_table(intermediate: dict) -> None:
    hive = [to_hive(s) for s in intermediate["settings_driven"].module.every_daily_total(
        *DAYS["intermediate"])]
    assert len(hive) == 2
    assert "SUM(region_costs.cost_cents) AS total_cost_cents" in hive[0]
    assert "region_costs.dt BETWEEN '20260922' AND '20260924'" in hive[0]
    assert "job_events.dt BETWEEN '2026-09-22' AND '2026-09-24'" in hive[1]


def costs_saved(project: dict, days: tuple[str, str]) -> pd.DataFrame:
    """What the incremental load would save on each of the days, with the day as dt."""
    module = project["incremental_load"].module
    first = datetime.date.fromisoformat(days[0])
    every_day = [(first + datetime.timedelta(days=n)).isoformat()
                 for n in range((datetime.date.fromisoformat(days[1]) - first).days + 1)]
    return pd.concat([run(module.preview(day), send=example_database.send).assign(dt=day)
                      for day in every_day], ignore_index=True)

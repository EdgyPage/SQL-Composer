"""The Templates in `templates/`: what each asks you to fill in, and that, filled in, it runs.

A Template is the shape of one of the user's scripts with its specifics left as placeholders
written `<UPPER_SNAKE>`, such as `<TABLE>`, each listed in its docstring's "Fill in:" block. A
placeholder stands where Python code goes, never inside quotes, so a Template with any one of
them left in doesn't parse, and can't run half filled in. The README beside the two sets names
every Template.

Each set of Templates is then filled in from FILLS, with the Example database's values, and
written where each Template's "Copy it to:" line says, in a project folder made for the test.
The folder also holds Example project Table references, which the filled Templates import as a
user's own. The intermediate set's folder also holds the starter Templates its incremental load
saves, a Building block and a Saved table's Table reference, filled in as the starter set fills
them, so the two sets are filled in as one, as a user would fill them in.

Every Statement a Template's functions give is built; a write is checked only through to_hive,
and each SELECT runs on the Example database, giving rows unless it looks for repeated keys. A
SELECT sqlglot's executor can't run, with row_number or week_start, runs only in Spark
Composer's run, and is skipped in sqlglot Composer's with the reason. One that reads a Saved
table, which only a warehouse holds, runs with the Saved table stood in for by the rows the
Template that writes it previews. notebook_start and keep_table_references_true also run from
an empty folder, as a user's first files.
"""

from __future__ import annotations

import ast
import importlib
import re
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

import editions
from conftest import (
    COPY_IT_TO, INSERT, PLACEHOLDER, ROOT, TEMPLATES, edition, functions_given,
    is_a_select_on_the_example_database, previewed_days, project_on_the_path, standing_in,
    template_id, without_the_write,
)
from sqlglot_composer import (
    FROM, SELECT, all_columns, create_table, example_database, run, statement, to_hive,
)

EXAMPLE_PROJECTS = ROOT / "example_projects"
README = TEMPLATES / "README.md"
NAMES = {
    "starter": ["building_block.py", "daily_pipeline.py", "keep_table_references_true.py",
                "notebook_start.py", "per_group_statement.py", "saved_table.py",
                "saved_table_reference.py"],
    "intermediate": ["as_of_lookup.py", "building_blocks.py", "incremental_load.py",
                     "incremental_pipeline.py", "quality_statements.py", "settings_driven.py",
                     "weekly_rollup.py"],
}
LISTED = re.compile(r"^    (<[A-Z][A-Z0-9_]*>): ", re.MULTILINE)
MIRRORS = re.compile(r"example_projects/[\w/]+\.(?:py|md)")
LEVEL_FOLDERS = ("table_references", "building_blocks", "statements")

# Example database values for each placeholder, as a user would type them: a name as it is, a
# text in quotes.
FILLS = {
    "starter": {
        "<RUN_HIVE>": "example_database.send(hive)",
        "<KNOWN_QUERY>": "\"SELECT * FROM ops.job_runs WHERE dt = '2026-09-24' LIMIT 5\"",
        "<TABLE_NAME>": '"ops.job_runs"',
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
        "<TOTAL_TYPE>": '"bigint"',
        "<BLOCK>": "minutes_per_job_day",
        "<BLOCK_NAME>": '"minutes_per_job_day"',
        "<STATEMENT>": "minutes_per_job",
        "<MORE_THAN_ROWS>": "1",
        "<NEW_TABLE_NAME>": '"ops.job_events"',
    },
    "intermediate": {
        # incremental_load, incremental_pipeline and weekly_rollup save and read the starter
        # Templates' Building block and Saved table, filled in as the starter set fills them
        "<SAVED_TABLE>": "job_day_minutes",
        "<BLOCK>": "minutes_per_job_day",
        "<GROUP_COLUMN>": "job_id",
        "<TOTAL>": "minutes",
        "<TOTAL_NAME>": '"minutes"',
        "<DAY>": '"2026-09-24"',
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
        "<FIRST_TABLE_NAME>": '"ops.region_costs"',
        "<FIRST_DATE_PARTITION>": '"dt"',
        "<FIRST_KEY>": '"job_id", "region", "dt"',
        "<FIRST_ADD_UP>": '"cost_cents"',
        "<SECOND_TABLE>": "job_events",
        "<SECOND_TABLE_NAME>": '"ops.job_events"',
        "<SECOND_DATE_PARTITION>": '"dt"',
        "<SECOND_KEY>": '"event_id"',
    },
}
# The Example projects whose Table references each set's folder holds, which its filled
# Templates import: the intermediate set's Building block reads the starter's ops.job_runs.
TABLE_REFERENCES_FROM = {"starter": ("starter",), "intermediate": ("starter", "intermediate")}
# The starter Templates each set's folder holds besides its own: the intermediate set's
# incremental load saves a copy of building_block.py into a copy of saved_table_reference.py.
BUILT_ON = {"starter": (), "intermediate": ("building_block", "saved_table_reference")}
# The intermediate Templates that fit the starter Templates, filled in as the starter set is.
FIT_THE_STARTER_SET = ("incremental_load", "incremental_pipeline", "weekly_rollup")
# The days each set's Statements are built for: two of the Example database's days for the
# starter's ops.job_runs, the last 3 of its 14 for the intermediate tables.
DAYS = {"starter": ("2026-09-23", "2026-09-24"), "intermediate": ("2026-09-22", "2026-09-24")}
# A notebook's first cells run as they are imported, so they are imported in a test of their own.
RUNS_WHEN_IMPORTED = "notebook_start"
# The SELECTs sqlglot Composer's Example database can't run, by set, Template and function.
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


def template_text(name: str, stem: str) -> str:
    return (TEMPLATES / name / f"{stem}.py").read_text(encoding="utf-8")


def placeholders(text: str) -> set[str]:
    return {found.group(0) for found in PLACEHOLDER.finditer(text)}


def docstring(text: str) -> str:
    """A Template's docstring, read as text: ast can't read one from a file that doesn't
    parse."""
    return text.split('"""')[1]


def code(text: str) -> str:
    """A Template without its docstring."""
    return text.split('"""', 2)[2]


def listed(text: str) -> list[str]:
    """The placeholders the docstring's "Fill in:" block lists, in its order."""
    return LISTED.findall(docstring(text).split("\nFill in:\n")[1])


def filled(text: str, fills: dict[str, str], leave: str | None = None) -> str:
    """The Template with each placeholder replaced by its fill, but `leave` left in."""
    return PLACEHOLDER.sub(lambda m: m.group(0) if m.group(0) == leave else fills[m.group(0)],
                           text)


def copied_to(text: str) -> str:
    """Where the docstring's "Copy it to:" line puts the Template, in the user's project."""
    return COPY_IT_TO.search(docstring(text)).group(1)


def module_name(relative: str) -> str:
    """The module a notebook in the project's folder imports a script by."""
    return relative.removesuffix(".py").replace("/", ".")


def write_filled(text: str, fills: dict[str, str], folder: Path) -> str:
    """Fill the Template in and write it where it says, in `folder`; return where."""
    text = filled(text, fills)
    relative = copied_to(text)
    (folder / relative).parent.mkdir(parents=True, exist_ok=True)
    (folder / relative).write_text(text, encoding="utf-8")
    return relative


def skip_in_sqlglot_composer(reason: str) -> None:
    if edition() is editions.SQLGLOT_COMPOSER:
        pytest.skip(reason)


# --- The placeholders --------------------------------------------------------------------------


def test_there_are_both_sets_of_templates_and_their_readme() -> None:
    found = {name: sorted(path.name for path in (TEMPLATES / name).glob("*.py"))
             for name in NAMES}
    assert found == NAMES
    assert sorted(path.name for path in TEMPLATES.iterdir()) == sorted([*NAMES, README.name])


def test_the_readme_names_every_template() -> None:
    readme = README.read_text(encoding="utf-8")
    assert [template_id(path) for path in templates()
            if f"`{template_id(path)}`" not in readme] == []


@pytest.mark.parametrize("path", templates(), ids=template_id)
def test_each_placeholder_is_listed_once_and_each_listed_one_is_used(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    names = listed(text)
    assert names, f"{template_id(path)} lists no placeholder under Fill in:"
    assert len(names) == len(set(names)), f"listed twice: {names}"
    assert placeholders(code(text)) == set(names)
    assert placeholders(docstring(text)) <= set(names)


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


def test_the_intermediate_templates_that_fit_the_starter_set_are_filled_in_as_it_is() -> None:
    """incremental_load saves the starter Templates' Building block into their Saved table, so
    each placeholder the two sets share is filled in the same."""
    for stem in FIT_THE_STARTER_SET:
        shared = set(listed(template_text("intermediate", stem))) & set(FILLS["starter"])
        assert shared, stem
        assert {p: FILLS["intermediate"][p] for p in shared} == {
            p: FILLS["starter"][p] for p in shared}, stem


@pytest.mark.parametrize("path", templates(), ids=template_id)
def test_each_template_says_where_it_goes_and_which_files_it_mirrors(path: Path) -> None:
    text = docstring(path.read_text(encoding="utf-8"))
    assert COPY_IT_TO.search(text), f"{template_id(path)} has no 'Copy it to:' line"
    mirrored = MIRRORS.findall(" ".join(text.split()))
    assert mirrored, f"{template_id(path)} names no Example project file it mirrors"
    assert [m for m in mirrored if not (ROOT / m).is_file()] == []


@pytest.mark.parametrize("path", templates(), ids=template_id)
def test_each_template_can_be_named_for_either_edition(path: Path) -> None:
    """The export copies each Template for each Edition through editions.named_for, which
    refuses text that would still name sqlglot Composer in Spark Composer's copy."""
    text = path.read_text(encoding="utf-8")
    for each in (editions.SQLGLOT_COMPOSER, editions.SPARK_COMPOSER):
        named = editions.named_for(each, text, where=template_id(path))
        assert f"from {each.folder} import" in named


def test_the_readme_can_be_named_for_either_edition() -> None:
    """The README ships beside the Templates, named for each Edition the same way."""
    text = README.read_text(encoding="utf-8")
    for each in (editions.SQLGLOT_COMPOSER, editions.SPARK_COMPOSER):
        assert f"`{each.folder}`" in editions.named_for(each, text, where="templates/README.md")


# --- Filled in, in a project folder --------------------------------------------------------------


def filled_project(name: str, folder: Path):
    """The set's Templates filled in, each written where it says, beside the Example project
    Table references they import, and the starter Templates the set builds on. Yields what
    each Template became, by its name, such as "saved_table": the folder, the path it was
    written to and its module, imported while the project is on the path. notebook_start's
    isn't imported, since it runs as it is imported."""
    for project in TABLE_REFERENCES_FROM[name]:
        shutil.copytree(EXAMPLE_PROJECTS / project / "table_references",
                        folder / "table_references", dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__"))
    written = {stem: write_filled(template_text("starter", stem), FILLS["starter"], folder)
               for stem in BUILT_ON[name]}
    for path in sorted((TEMPLATES / name).glob("*.py")):
        written[path.stem] = write_filled(path.read_text(encoding="utf-8"), FILLS[name], folder)
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


def built_by(module, name: str) -> dict[str, list]:
    """Each function the module defines whose parameters are days, by name, with the
    Statements it gives for the set's days."""
    first_day, last_day = DAYS[name]
    return functions_given(module, {"day": last_day, "first_day": first_day,
                                    "last_day": last_day})


def at_a_level(name: str) -> list[str]:
    """The Templates of a set that are copied into a Level folder."""
    return [path.stem for path in sorted((TEMPLATES / name).glob("*.py"))
            if copied_to(path.read_text(encoding="utf-8")).split("/")[0] in LEVEL_FOLDERS]


LEVEL_TEMPLATES = [(name, stem) for name in NAMES for stem in at_a_level(name)]
# The Level Templates whose functions build Statements: all but the Table reference.
STATEMENT_TEMPLATES = [case for case in LEVEL_TEMPLATES if case[1] != "saved_table_reference"]


def level_id(case: tuple[str, ...]) -> str:
    return "/".join(case)


@pytest.mark.parametrize("case", STATEMENT_TEMPLATES, ids=level_id)
def test_each_statement_it_builds_becomes_hive(request, case: tuple[str, str]) -> None:
    name, stem = case
    built = built_by(request.getfixturevalue(name)[stem].module, name)
    assert built, f"{stem} builds no Statement"
    for function, statements in built.items():
        assert all(to_hive(s) for s in statements), f"{stem}.{function}"


def test_the_saved_table_reference_makes_a_create_table(starter: dict) -> None:
    saved = starter["saved_table_reference"].module.job_day_minutes
    hive = to_hive(create_table(saved))
    assert hive.startswith("CREATE TABLE mart.job_day_minutes")
    columns, partitioned_by = hive.split("PARTITIONED BY")
    assert "row_count BIGINT" in columns and "dt STRING" in partitioned_by


def runnable_selects(name: str, stem: str, module) -> dict[str, list]:
    """Each function's SELECTs that either Example database runs: none that reads a Saved
    table, and none that NOT_ON_SQLGLOTS_EXECUTOR names, which a test of its own runs."""
    found = {}
    for function, statements in built_by(module, name).items():
        if (name, stem, function) in NOT_ON_SQLGLOTS_EXECUTOR:
            continue
        selects = [s for s in statements if is_a_select_on_the_example_database(s)]
        if selects:
            found[function] = selects
    return found


# What each Level Template's SELECTs are, by function, besides those NOT_ON_SQLGLOTS_EXECUTOR
# names: weekly_rollup's only SELECT reads a Saved table, and is run with it stood in for.
RUNNABLE = {
    ("starter", "building_block"): ["minutes_per_job_day"],
    ("starter", "per_group_statement"): ["minutes_per_job"],
    ("starter", "saved_table"): ["preview"],
    ("starter", "saved_table_reference"): [],
    ("intermediate", "as_of_lookup"): ["newest_per_key_by_newest_day", "rows_as_of_their_day"],
    ("intermediate", "building_blocks"): ["keys_expected", "keys_seen"],
    ("intermediate", "incremental_load"): ["preview"],
    ("intermediate", "quality_statements"): ["null_counts", "repeated_keys", "rows_per_day"],
    ("intermediate", "settings_driven"): ["every_statement"],
    ("intermediate", "weekly_rollup"): [],
}


@pytest.mark.needs_example_database
@pytest.mark.parametrize("case", LEVEL_TEMPLATES, ids=level_id)
def test_each_select_it_builds_runs_on_the_example_database(request, case) -> None:
    """Each gives rows, but a SELECT of repeated keys, which should find none."""
    name, stem = case
    module = request.getfixturevalue(name)[stem].module
    selects = {} if module is None else runnable_selects(name, stem, module)
    assert sorted(selects) == RUNNABLE[case]
    for function, statements in selects.items():
        for s in statements:
            rows = run(s, send=example_database.send)
            if "times_seen" in rows.columns:
                assert rows.empty, f"{stem}.{function} found a repeated key"
            else:
                assert len(rows) > 0, f"{stem}.{function} gave no rows"


@pytest.mark.needs_example_database
def test_newest_per_key_runs_on_spark(intermediate: dict) -> None:
    """It gives the rows newest_per_key_by_newest_day gives, without row_number."""
    skip_in_sqlglot_composer(
        NOT_ON_SQLGLOTS_EXECUTOR[("intermediate", "as_of_lookup", "newest_per_key")])
    module = intermediate["as_of_lookup"].module
    rows = run(module.newest_per_key("2026-09-24"), send=example_database.send)
    assert len(rows) > 0 and rows.job_id.is_unique
    without = run(module.newest_per_key_by_newest_day("2026-09-24"), send=example_database.send)
    pd.testing.assert_frame_equal(rows.sort_values("job_id").reset_index(drop=True),
                                  without.sort_values("job_id").reset_index(drop=True),
                                  check_dtype=False)


@pytest.mark.needs_example_database
def test_the_weekly_rollup_runs_on_spark(intermediate: dict) -> None:
    """mart.job_day_minutes, which only a warehouse holds, is stood in for by what the
    incremental load previews for each of ops.job_runs' two days."""
    skip_in_sqlglot_composer(
        NOT_ON_SQLGLOTS_EXECUTOR[("intermediate", "weekly_rollup", "week_totals")])
    saved = previewed_days(intermediate["incremental_load"].module, DAYS["starter"])
    hive = to_hive(intermediate["weekly_rollup"].module.week_totals("2026-09-21", "2026-09-27"))
    rows = example_database.send(standing_in(hive, {"job_day_minutes": saved}))
    assert set(rows.week) == {"2026-09-21"}
    # nightly_load's minutes: 12 and 5 on 2026-09-23, 10 and 40 on 2026-09-24
    assert rows.set_index("job_id").minutes[1] == 12 + 5 + 10 + 40


# --- Each starter Template, filled in -----------------------------------------------------------


@pytest.mark.needs_example_database
def test_notebook_start_runs_in_an_empty_folder(tmp_path: Path, monkeypatch, capsys) -> None:
    """As a user's first file: its cell 2 writes the Table reference cell 3 imports, and run
    again leaves it as it is."""
    relative = write_filled(template_text("starter", "notebook_start"), FILLS["starter"], tmp_path)
    monkeypatch.chdir(tmp_path)  # a notebook started in the project's folder
    with project_on_the_path(tmp_path, (module_name(relative), "table_references")):
        importlib.import_module(module_name(relative))
        printed = capsys.readouterr().out
        assert re.search(r"^\s+one\n0\s+1$", printed, re.MULTILINE)
        assert "WHERE\n  job_runs.dt = '2026-09-24'\nLIMIT 20;" in printed
        assert "run_id" in printed.split("LIMIT 20;")[1]
        written = (tmp_path / "table_references" / "job_runs.py").read_text(encoding="utf-8")
        assert "TODO" in written
        del sys.modules[module_name(relative)]
        importlib.import_module(module_name(relative))
        assert ("ops.job_runs has its Table reference already: the file is yours to edit."
                in capsys.readouterr().out)
        assert (tmp_path / "table_references" / "job_runs.py").read_text(
            encoding="utf-8") == written


@pytest.mark.needs_example_database
def test_keeping_table_references_true_starts_in_an_empty_folder(tmp_path: Path,
                                                                 capsys) -> None:
    """On first use, as its docstring says: its import line deleted, and no Table reference
    kept."""
    text = filled(template_text("starter", "keep_table_references_true"), FILLS["starter"])
    first_use = re.sub(r"^from table_references\..*\n", "", text, flags=re.MULTILINE)
    first_use = first_use.replace("TABLE_REFERENCES = [job_runs]", "TABLE_REFERENCES = []")
    assert first_use.count("job_runs") == text.count("job_runs") - 3
    (tmp_path / "keep_table_references_true.py").write_text(first_use, encoding="utf-8")
    with project_on_the_path(tmp_path, ("keep_table_references_true", "table_references")):
        references = importlib.import_module("keep_table_references_true")
        assert references.write_new_table_references(example_database.send) == [
            tmp_path / "table_references" / "job_events.py"]
        references.compare_with_the_tables(example_database.send)
    assert capsys.readouterr().out.startswith("TABLE_REFERENCES is empty: move each table")


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


def days_written(writes: list) -> list[str]:
    return [to_hive(write).split("PARTITION(dt = '")[1][:10] for write in writes]


def test_a_saved_tables_preview_is_the_select_its_write_sends(starter: dict) -> None:
    module = starter["saved_table"].module
    for day in DAYS["starter"]:
        assert without_the_write(to_hive(module.write_day(day))) == to_hive(module.preview(day))
    assert days_written(module.backfill(*DAYS["starter"])) == list(DAYS["starter"])


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


@pytest.mark.parametrize("case", [("starter", "daily_pipeline"),
                                  ("intermediate", "incremental_pipeline")], ids=level_id)
def test_the_pipeline_writes_its_lineage_files(request, case: tuple[str, str]) -> None:
    name, stem = case
    project = request.getfixturevalue(name)[stem]
    project.module.write_lineage_files("2026-09-24")
    lineage = project.folder / "lineage"
    assert sorted(path.name for path in lineage.iterdir()) == ["pipeline.html", "pipeline.md"]
    assert "mart.job_day_minutes" in (lineage / "pipeline.md").read_text(encoding="utf-8")


# --- Each intermediate Template, filled in -------------------------------------------------------


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


def test_the_incremental_pipeline_sends_each_step_in_order(intermediate: dict, capsys) -> None:
    """The starter Templates' Building block and Saved table, saved by an incremental load and
    run by its pipeline: each create, then each day's write, oldest first."""
    pipeline = intermediate["incremental_pipeline"].module
    statements = pipeline.in_order(pipeline.steps("2026-09-24"))
    hive = [to_hive(s) for s in statements]
    assert hive[0].startswith("CREATE TABLE IF NOT EXISTS mart.job_day_minutes")
    assert days_written(statements[1:]) == ["2026-09-22", "2026-09-23", "2026-09-24"]
    sent = []
    pipeline.send_all(sent.append, "2026-09-24")
    assert sent == hive
    pipeline.dry_run(pipeline.DAY)
    printed = capsys.readouterr().out
    names = ["create_job_day_minutes", *[f"write_job_day_minutes[{n}]" for n in range(3)]]
    for position, (variable, text) in enumerate(zip(names, hive, strict=True), start=1):
        assert f"-- {position} of 4: {variable}\n{text};" in printed


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
    assert "null_event_id" in found["null_counts"] and "null_dt" not in found["null_counts"]
    assert list(found["rows_per_day"].dt) == ["2026-09-22", "2026-09-23", "2026-09-24"]


def test_the_settings_make_each_statement_for_each_table(intermediate: dict) -> None:
    statements = intermediate["settings_driven"].module.every_statement(*DAYS["intermediate"])
    assert list(statements) == [
        "repeated_keys ops.region_costs", "rows_per_day ops.region_costs",
        "repeated_keys ops.job_events", "rows_per_day ops.job_events"]
    hive = {name: to_hive(s) for name, s in statements.items()}
    assert "SUM(region_costs.cost_cents) AS cost_cents" in hive["rows_per_day ops.region_costs"]
    assert "region_costs.dt BETWEEN '20260922' AND '20260924'" in hive[
        "rows_per_day ops.region_costs"]
    assert "region_costs.region" in hive["repeated_keys ops.region_costs"]
    assert "job_events.dt BETWEEN '2026-09-22' AND '2026-09-24'" in hive[
        "rows_per_day ops.job_events"]


@pytest.mark.needs_example_database
def test_the_settings_statements_run_all_together(intermediate: dict) -> None:
    found = intermediate["settings_driven"].module.run_all(example_database.send,
                                                           *DAYS["intermediate"])
    assert [len(rows) for name, rows in found.items() if name.startswith("repeated_keys")] == [
        0, 0]
    assert list(found["rows_per_day ops.region_costs"].columns) == ["dt", "row_count",
                                                                   "cost_cents"]
    assert list(found["rows_per_day ops.job_events"].dt) == ["2026-09-22", "2026-09-23",
                                                            "2026-09-24"]

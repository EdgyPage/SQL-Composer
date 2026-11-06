"""Database settings: admin/databases.py's DEV and PROD, each a dict. Toolbox 8.5, ticket 09.

"database" is each one's name, "location_root" the folder its tables' files go under, and any
other name the user's own, given in both. One reader reads them, refusing a dict with no
"database", a name in one and not the other, and a value that isn't text. A table with no
location of its own is placed <location_root>/<database>.db/<table>, from its own Database's
settings, and database_settings(name) gives the user's code a Database's settings. A
databases.py still holding the two names as text, as 8.4 wrote it, is read as {"database": ...}.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import forget_the_projects_modules, toolbox_module

from sqlglot_composer import database_settings, example_database, project, set_admin_log

WEEKLY = """\
CREATE TABLE ops_reports.failed_runs AS
SELECT r.run_id, r.job_id, r.dt FROM ops.job_runs r
WHERE r.dt = '2026-09-24' AND r.status = 'FAILED';
CREATE TABLE IF NOT EXISTS ops_reports.fails_per_job (job_id BIGINT, fails BIGINT)
PARTITIONED BY (dt STRING) STORED AS ORC LOCATION '/data/ops_reports/fails_per_job';
INSERT OVERWRITE TABLE ops_reports.fails_per_job PARTITION (dt='2026-09-24')
SELECT f.job_id, COUNT(*) AS fails FROM ops_reports.failed_runs f GROUP BY f.job_id;
"""
FAILED = "mart_dev.failed_runs_ops_reports"
PER_JOB = "mart_dev.fails_per_job_ops_reports"
SETTINGS = '''"""databases - mine."""

DEV = {"database": "mart_dev", "location_root": "/data/team/dev", "run_as": "svc_dev"}
PROD = {"database": "mart", "location_root": "/data/team/prod", "run_as": "svc_prod"}
'''


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A Project started, its databases.py as start() wrote it."""
    monkeypatch.setattr(sys, "path", list(sys.path))
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    yield tmp_path
    forget_the_projects_modules()


def write_settings(root: Path, text: str) -> None:
    (root / "admin" / "databases.py").write_text(text, encoding="utf-8")


def reference(root: Path, table: str) -> str:
    return (root / "references" / f"{table.replace('.', '__')}.py").read_text(encoding="utf-8")


def refusal(call: object) -> str:
    """What a call refused with, its first part's text."""
    with pytest.raises(ValueError) as refused:
        call()
    return str(refused.value)


# --- What start() writes, and what check() asks for ------------------------------------------


def test_start_writes_each_database_as_its_settings_to_fill_in(started: Path) -> None:
    text = (started / "admin" / "databases.py").read_text(encoding="utf-8")
    assert ('DEV = {"database": "<DEV_DATABASE>", "location_root": "<DEV_LOCATION_ROOT>"}'
            in text)
    assert ('PROD = {"database": "<PROD_DATABASE>", "location_root": "<PROD_LOCATION_ROOT>"}'
            in text)


def test_check_names_each_setting_to_fill_in_once_a_workflow_is_started(started: Path) -> None:
    assert "databases.py" not in repr(project.check())
    notebooks = toolbox_module("notebooks")
    path = started / "admin" / "workflows" / "convert" / "convert.ipynb"
    number = next(number for number, (kind, text) in enumerate(notebooks.read_cells(path), 1)
                  if kind == "code" and text.startswith("NAME ="))
    notebooks.write_cell_text(path, number, 'NAME = "weekly"')
    assert ('admin/databases.py: fill in DEV["database"] and DEV["location_root"]'
            in repr(project.check()))
    write_settings(started, SETTINGS.replace('"/data/team/dev"', '"<DEV_LOCATION_ROOT>"'))
    said = repr(project.check())
    assert 'fill in DEV["location_root"]' in said and 'DEV["database"]' not in said


# --- The one reader ---------------------------------------------------------------------------


def test_database_settings_gives_a_databases_settings_by_its_name_or_a_tables(
        started: Path) -> None:
    write_settings(started, SETTINGS)
    assert database_settings("mart_dev") == {
        "database": "mart_dev", "location_root": "/data/team/dev", "run_as": "svc_dev"}
    assert database_settings("mart.daily_runs")["run_as"] == "svc_prod"


def test_database_settings_refuses_a_database_neither_is(started: Path) -> None:
    write_settings(started, SETTINGS)
    said = refusal(lambda: database_settings("ops.job_runs"))
    assert "ops is neither your Dev Database, mart_dev, nor your Prod Database, mart" in said


def test_a_database_with_no_name_is_refused(started: Path) -> None:
    write_settings(started, SETTINGS.replace('"database": "mart_dev", ', ""))
    said = refusal(lambda: database_settings("mart"))
    assert 'admin/databases.py: DEV has no "database"' in said
    assert "Usual fix:" in said


def test_a_name_in_one_and_not_the_other_is_refused_naming_it(started: Path) -> None:
    write_settings(started, SETTINGS.replace(', "run_as": "svc_prod"', ""))
    said = refusal(lambda: database_settings("mart"))
    assert 'admin/databases.py: "run_as" is in DEV but not in PROD' in said


def test_a_value_that_isnt_text_is_refused(started: Path) -> None:
    write_settings(started, SETTINGS.replace('"svc_dev"', "5"))
    said = refusal(lambda: database_settings("mart"))
    assert 'admin/databases.py: DEV["run_as"] is 5, which isn\'t text' in said


def test_the_two_names_as_text_are_read_as_each_databases_name(started: Path) -> None:
    write_settings(started, 'DEV = "mart_dev"\nPROD = "mart"\n')
    assert database_settings("mart_dev") == {"database": "mart_dev"}
    assert database_settings("mart") == {"database": "mart"}


# --- Where a table's files go -----------------------------------------------------------------


def convert_weekly(root: Path) -> None:
    (root / "weekly.hql").write_text(WEEKLY, encoding="utf-8")
    project.convert("weekly", files=["weekly.hql"], query=example_database.query,
                    database="ops")


def test_convert_places_a_table_with_no_location_of_its_own_under_devs_root(
        started: Path) -> None:
    write_settings(started, SETTINGS)
    convert_weekly(started)
    text = reference(started, FAILED)
    assert ('    location="/data/team/dev/mart_dev.db/failed_runs_ops_reports",' in text)
    decisions = toolbox_module("decisions")
    assert not decisions.open_decisions(text, FAILED, (decisions.LOCATION,))
    # A table whose CREATE gives its own keeps it.
    assert '    location="/data/ops_reports/fails_per_job",' in reference(started, PER_JOB)


def test_with_no_root_a_location_stays_a_decision(started: Path) -> None:
    write_settings(started, 'DEV = "mart_dev"\nPROD = "mart"\n')
    convert_weekly(started)
    assert "    location=None,  # TODO:" in reference(started, FAILED)


def test_new_table_places_its_table_under_devs_root(started: Path) -> None:
    write_settings(started, SETTINGS)
    project.new_table("mart_dev.daily_runs")
    assert ('    location="/data/team/dev/mart_dev.db/daily_runs",'
            in reference(started, "mart_dev.daily_runs"))


def test_a_location_root_under_all_tables_is_refused_pointing_to_databases_py(
        started: Path) -> None:
    write_settings(started, SETTINGS)
    convert_weekly(started)
    said = refusal(lambda: project.write_decisions(
        {"all_tables": {"location_root": "/data/team"}}, tables=[FAILED]))
    assert ('all_tables: location_root is a Database setting now: give it as '
            '"location_root" in DEV and PROD, in admin/databases.py') in said

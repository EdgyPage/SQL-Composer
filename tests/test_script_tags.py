"""Script tags: a <PARM="NAME"/> in Hive someone else wrote, NAME any variable name, which the
program that ran it filled in before Hive read it. Toolbox 8.3.

Ticket 01 holds what a Conversion's batch reader does with each shape of tag before 8.3
changes it: a bare tag stops sqlglot, so its whole statement is left an Unchecked statement,
naming no table; a quoted one reads as a string, kept as written.
"""

from __future__ import annotations

import pytest
from conftest import toolbox_module

converting = toolbox_module("converting")

BARE = ("INSERT OVERWRITE TABLE mart.daily_close PARTITION (dt)\n"
        "SELECT r.job_id, COUNT(*) AS runs, r.dt FROM ops.job_runs r\n"
        'WHERE r.dt <= <PARM="PERIOD_END"/> GROUP BY r.job_id, r.dt;')
QUOTED = ("INSERT OVERWRITE TABLE mart.daily_close PARTITION (dt)\n"
          "SELECT r.job_id, COUNT(*) AS runs, r.dt FROM ops.job_runs r\n"
          """WHERE r.dt <= '<PARM="run_month_2"/>' GROUP BY r.job_id, r.dt;""")


# A bare tag, with another name, in a staging table's CREATE ... AS, and the same tag twice.
STAGING = ("CREATE TEMPORARY TABLE long_runs AS\n"
           "SELECT r.job_id, r.dt FROM ops.job_runs r\n"
           'WHERE r.duration_mins >= <PARM="MinMins"/>;')
TWICE = ("INSERT OVERWRITE TABLE mart.daily_close PARTITION (dt)\n"
         "SELECT r.job_id, COUNT(*) AS runs, r.dt FROM ops.job_runs r\n"
         'WHERE r.dt >= <PARM="PERIOD_END"/> AND r.dt <= <PARM="PERIOD_END"/>\n'
         "GROUP BY r.job_id, r.dt;")


def _statement_of(text: str) -> converting.BatchStatement:
    (statement,) = converting.batch_statements([("daily.hql", text)], "ops")
    return statement


@pytest.mark.parametrize("text", [BARE, STAGING, TWICE], ids=["insert", "staging", "twice"])
def test_a_bare_tag_leaves_its_statement_unread_naming_no_table(text: str) -> None:
    statement = _statement_of(text)
    assert statement.kind == converting.OTHER
    assert statement.table is None
    assert statement.reads == []
    assert statement.note.startswith(converting.UNREAD)


def test_a_quoted_tag_reads_as_a_string_kept_as_written() -> None:
    statement = _statement_of(QUOTED)
    assert statement.table == "mart.daily_close"
    assert statement.reads == ["ops.job_runs"]
    assert '<PARM="run_month_2"/>' in statement.tree.sql(dialect="hive")

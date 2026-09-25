"""The test setup every Toolbox test shares.

Today is pinned to 2026-09-25, the day after the Example database's last day, so
`last_n_days(job_runs.dt, 2)` covers both of its days and every emitted date is fixed. The
load limits are switched off again after each test, since `set_load_limits` changes them for
the whole session.
"""

from __future__ import annotations

import datetime
import re

import pytest
import sqlglot

import sql_composer
from sql_composer import conditions

TODAY = datetime.date(2026, 9, 25)

_found = re.match(r"(\d+)\.(\d+)\.(\d+)", sqlglot.__version__)
SQLGLOT = tuple(int(n) for n in _found.groups()) if _found else (0, 0, 0)
EXECUTOR_READY = SQLGLOT >= (30, 19, 0)

needs_executor = pytest.mark.skipif(
    not EXECUTOR_READY,
    reason="the Example database runs queries only on sqlglot 30.19.0 or newer",
)


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(conditions, "today", lambda: TODAY)


@pytest.fixture(autouse=True)
def no_load_limits():
    yield
    sql_composer.set_load_limits()

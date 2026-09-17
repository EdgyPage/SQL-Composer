"""Shared fixtures for the suite, plus the one bit of bootstrap the layout needs.

`sqlcomposer` and `declarations` are not installed into site-packages in the development
environment; they live at the repository root. pytest's `prepend` import mode inserts the
directory holding a test file (here `tests/`) onto `sys.path`, not the root, and there is no
root-level `conftest.py` to make it do otherwise - so an explicit insert is the difference
between the suite running and the suite collecting zero tests with an ImportError.

ADD fixtures here; do not rewrite one that is already present. Several test modules are
written independently against this file.
"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlcomposer.declaration import Registry  # noqa: E402  (needs the path insert above)


@pytest.fixture(scope="session")
def registry() -> Registry:
    """The frozen fixture Registry every Case in the suite is compiled against.

    Session-scoped because `Registry.freeze()` runs every cross-Declaration check and a
    frozen Registry is immutable by construction - there is nothing for one test to leave
    behind for the next. Importing `declarations` inside the fixture rather than at module
    scope keeps the import error, if the fixture package is ever broken, attached to the
    tests that need it instead of to collection of the whole suite.
    """
    from declarations import REGISTRY

    return REGISTRY


@pytest.fixture(scope="session")
def run_date() -> datetime.date:
    """The single run date every deferred Filter in the suite binds to.

    Frozen rather than `date.today()`: `LAST_7_DAYS` holds a `RunDate`, so today's date
    would put a moving value into every emitted statement and make a golden snapshot
    impossible - the snapshot would pass on the day it was written and fail forever after.

    2026-09-17 is a Thursday, and the seven-day window it opens (2026-09-11 to 2026-09-17)
    therefore straddles a Monday. Nothing in the WHERE clause depends on that, but a window
    that sat inside one ISO week would make a day-bucketed and a week-bucketed Case cover
    the same rows, which is a poor shape for a fixture whose whole point is the difference
    between the two.
    """
    return datetime.date(2026, 9, 17)

"""What sqlglot takes each Hive variance, standard deviation and covariance to mean, as the
Toolbox reads Hive: the tripwire for a sqlglot upgrade that renames or remeans one.

Hive's VARIANCE is the population variance, which sqlglot calls VariancePop; sqlglot's own
Variance is the sample one, Hive's VAR_SAMP. tests/test_variance_functions.py checks the names
each is written under.
"""

from __future__ import annotations

import pytest
from conftest import toolbox_module
from sqlglot import exp

writing = toolbox_module("writing")

MEANINGS = {
    "VARIANCE(x)": exp.VariancePop, "VAR_POP(x)": exp.VariancePop, "VAR_SAMP(x)": exp.Variance,
    "STDDEV_POP(x)": exp.StddevPop, "STDDEV_SAMP(x)": exp.StddevSamp,
    "COVAR_POP(x, y)": exp.CovarPop, "COVAR_SAMP(x, y)": exp.CovarSamp,
}


@pytest.mark.parametrize("call", MEANINGS)
def test_each_is_read_with_hive_s_meaning(call: str) -> None:
    [read] = writing.read_hive(f"SELECT {call} AS v FROM t")
    assert type(read.selects[0].this) is MEANINGS[call]

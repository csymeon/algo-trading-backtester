# tests/test_risk.py

import pandas as pd
import pytest
from utils.risk import historical_var, expected_shortfall

def test_var_es():
    returns = pd.Series([0.01, -0.02, 0.03, -0.04, 0.05])
    var = historical_var(returns, level=0.05)
    assert var >= 0
    es = expected_shortfall(returns, level=0.05)
    assert es >= var
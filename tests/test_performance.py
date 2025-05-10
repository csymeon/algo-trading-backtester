# tests/test_performance.py

import pandas as pd
import pytest
from utils.performance import calculate_returns, calculate_sharpe_ratio, calculate_drawdowns

def test_performance_metrics():
    idx = pd.date_range("2020-01-01", periods=5)
    values = pd.Series([100, 110, 105, 115, 120], index=idx)
    returns = calculate_returns(values)
    assert len(returns) == 4
    sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0)
    assert sharpe > 0
    drawdowns, max_dd = calculate_drawdowns(values)
    assert max_dd <= 0
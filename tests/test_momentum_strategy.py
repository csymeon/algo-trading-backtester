# tests/test_momentum_strategy.py

import pandas as pd
import pytest
from strategies.momentum_strategy import MomentumStrategy

def test_momentum_signals():
    dates = pd.date_range("2020-01-01", periods=4)
    priceA = pd.DataFrame({"Close": [1, 2, 3, 4]}, index=dates)
    priceB = pd.DataFrame({"Close": [4, 3, 2, 1]}, index=dates)
    data = {"A": priceA, "B": priceB}
    strat = MomentumStrategy(lookback=1, top_k=1, bottom_k=1)
    signals = strat.generate_signals(data)
    # On the second date, A should be top momentum, B bottom
    assert signals.loc[dates[1], "A"] == 1
    assert signals.loc[dates[1], "B"] == -1
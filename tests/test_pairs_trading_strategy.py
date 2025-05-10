# tests/test_pairs_trading_strategy.py

import pandas as pd
import numpy as np
import pytest
from strategies.pairs_strategy import PairsTradingStrategy

def test_pairs_trading_signals():
    dates = pd.date_range("2020-01-01", periods=10)
    df_x = pd.DataFrame({"Close": np.arange(10) + 1}, index=dates)
    df_y = pd.DataFrame({"Close": np.arange(10) + 1}, index=dates)
    strat = PairsTradingStrategy(
        symbol_x="X", symbol_y="Y",
        lookback=5, z_entry=2.0, z_exit=0.5
    )
    signals = strat.generate_signals({"X": df_x, "Y": df_y})
    # Identical series are never beyond entry threshold
    assert (signals == 0).all().all()
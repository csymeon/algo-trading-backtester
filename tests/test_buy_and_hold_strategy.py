import pandas as pd
import pytest
from strategies.buy_and_hold_strategy import BuyAndHoldStrategy

def test_buy_and_hold_signals():
    idx    = pd.date_range("2021-01-01", periods=4)
    prices = pd.Series([10, 20, 30, 40], index=idx)
    strat  = BuyAndHoldStrategy()
    signals = strat.generate_signals(prices)

    # all signals should be 1
    assert all(signals == 1)
    # length should match prices
    assert len(signals) == len(prices)
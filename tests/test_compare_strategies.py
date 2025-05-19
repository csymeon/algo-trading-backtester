import pandas as pd
import pytest
from strategies.buy_and_hold_strategy import BuyAndHoldStrategy
from strategies.strategy_template import MovingAverageCrossoverStrategy
from utils.benchmark import compare_strategies

def test_compare_two_strategies():
    idx    = pd.date_range("2020-01-01", periods=6)
    prices = pd.Series([1,2,3,2,1,2], index=idx)
    strategies = {
        'buy_hold': BuyAndHoldStrategy(),
        'ma_cross': MovingAverageCrossoverStrategy(short_window=2, long_window=3)
    }

    summary = compare_strategies(prices, strategies, symbol='SYM', initial_capital=100)

    # Should have two rows
    assert set(summary.index) == {'buy_hold', 'ma_cross'}
    # Final value for buy_hold = 100/1*2 = 200
    assert pytest.approx(summary.loc['buy_hold', 'final_value'], rel=1e-6) == 200
    # Metrics columns exist
    assert 'sharpe' in summary.columns
    assert 'max_drawdown' in summary.columns
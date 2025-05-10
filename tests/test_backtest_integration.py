# tests/test_backtest_integration.py

import pandas as pd
import pytest
from engine.execution_handler import ExecutionHandler
from engine.portfolio import Portfolio
from strategies.strategy_template import MovingAverageCrossoverStrategy

def test_integration_simple_backtest():
    dates = pd.date_range("2020-01-01", periods=5)
    close = [1, 2, 3, 2, 1]
    df = pd.DataFrame({"Close": close}, index=dates)

    strat = MovingAverageCrossoverStrategy(short_window=2, long_window=3)
    data_with_signals = strat.generate_signals(df.copy())

    exec_h = ExecutionHandler(commission_per_trade=0, slippage_pct=0)
    port   = Portfolio(initial_capital=100)

    prev_signal = 0
    port_vals   = []

    for date, row in data_with_signals.iterrows():
        sig   = int(row['signal'].item())
        price = float(row['Close'].item())

        if sig == 1 and prev_signal != 1:
            exec_h.execute_order("BUY", "SYM", 1, price, timestamp=date)
            port.buy("SYM", 1, price, commission=exec_h.commission)
        elif sig == -1 and prev_signal != -1:
            exec_h.execute_order("SELL", "SYM", 1, price, timestamp=date)
            port.sell("SYM", 1, price, commission=exec_h.commission)

        prev_signal = sig
        port_vals.append(port.value({"SYM": price}))

    assert len(exec_h.trades) >= 1
    assert isinstance(port_vals[-1], (int, float))
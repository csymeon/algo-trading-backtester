import pandas as pd
from typing import Dict
from engine.execution_handler import ExecutionHandler
from engine.portfolio import Portfolio
from strategies.buy_and_hold_strategy import BuyAndHoldStrategy
from utils.performance import calculate_returns, calculate_sharpe_ratio, calculate_drawdowns

def backtest_strategy(
    prices: pd.Series,
    signals,
    symbol: str,
    initial_capital: float = 100000,
    qty_per_trade: int = 10,
    commission: float = 0.0,
    slippage: float = 0.0
) -> pd.Series:
    """
    Backtest any signal series or DataFrame: trades on signal changes.
    Returns a Series of portfolio values aligned with prices.
    """
    exec_h = ExecutionHandler(commission_per_trade=commission, slippage_pct=slippage)
    port   = Portfolio(initial_capital=initial_capital)

    # Normalize signals to a Series of ints
    if isinstance(signals, pd.DataFrame):
        sigs = signals["signal"].astype(int)
    else:
        sigs = signals.astype(int)

    values = []
    prev = 0

    for date in prices.index:
        price = float(prices.loc[date])
        sig   = sigs.loc[date]

        if sig == 1 and prev != 1:
            exec_h.execute_order("BUY", symbol, qty_per_trade, price, timestamp=date)
            port.buy(symbol, qty_per_trade, price, commission=commission)
        elif sig == -1 and prev != -1:
            exec_h.execute_order("SELL", symbol, qty_per_trade, price, timestamp=date)
            port.sell(symbol, qty_per_trade, price, commission=commission)

        prev = sig
        values.append(port.value({symbol: price}))

    return pd.Series(values, index=prices.index)

def compare_strategies(
    prices: pd.Series,
    strategies: Dict[str, object],
    symbol: str,
    initial_capital: float = 100000
) -> pd.DataFrame:
    """
    Run multiple strategies and collect performance metrics.
    Returns a DataFrame indexed by strategy name with columns:
    'final_value', 'sharpe', 'max_drawdown'
    """
    results = []
    for name, strat in strategies.items():
        # Handle Buy-and-Hold specially
        if isinstance(strat, BuyAndHoldStrategy):
            port_vals = backtest_strategy(prices, strat.generate_signals(prices),
                                         symbol, initial_capital, qty_per_trade=int(initial_capital/prices.iloc[0]))
        else:
            df_signals = strat.generate_signals(prices)
            port_vals  = backtest_strategy(prices, df_signals, symbol, initial_capital)

        returns   = calculate_returns(port_vals)
        sharpe    = calculate_sharpe_ratio(returns)
        _, max_dd = calculate_drawdowns(port_vals)

        results.append({
            'strategy':     name,
            'final_value':  float(port_vals.iloc[-1]),
            'sharpe':       float(sharpe),
            'max_drawdown': float(max_dd),
        })

    return pd.DataFrame(results).set_index('strategy')
# main.py
# Entry point for running the backtest

from engine.data_handler import DataHandler
from strategies.strategy_template import MovingAverageCrossoverStrategy
from engine.portfolio import Portfolio
from engine.execution_handler import ExecutionHandler

import pandas as pd
from utils.performance import (
    calculate_returns,
    calculate_sharpe_ratio,
    calculate_drawdowns,
    plot_equity_curve
)

def main():
    print("Starting Algorithmic Trading Backtester 🚀")

    # Load data
    data_handler = DataHandler(symbol="SPY", start_date="2020-01-01", end_date="2023-01-01")
    data = data_handler.load_data()

    # Initialize strategy
    strategy = MovingAverageCrossoverStrategy(short_window=50, long_window=200)
    data_with_signals = strategy.generate_signals(data)

    # Initialize portfolio and execution handler
    portfolio = Portfolio(initial_capital=100000)
    execution_handler = ExecutionHandler()

    # Track portfolio value over time
    prev_signal = 0
    portfolio_values = []

    for date, row in data_with_signals.iterrows():
        signal = row['signal'].item()
        price  = row['Close'].item()

        # BUY only when we go from non-1 → 1
        if signal == 1 and prev_signal != 1:
            execution_handler.execute_order("BUY", "SPY", 10, price)
            portfolio.buy("SPY", 10, price, commission=execution_handler.commission)

        # SELL only when we go from non-(-1) → -1
        elif signal == -1 and prev_signal != -1:
            execution_handler.execute_order("SELL", "SPY", 10, price)
            portfolio.sell("SPY", 10, price, commission=execution_handler.commission)

        prev_signal = signal

        # track portfolio value each day
        portfolio_values.append((date, portfolio.value({"SPY": price})))

    # Convert to DataFrame
    portfolio_df = pd.DataFrame(portfolio_values, columns=["Date", "Value"])
    portfolio_df.set_index("Date", inplace=True)

    # Performance analysis
    returns = calculate_returns(portfolio_df["Value"])
    sharpe = calculate_sharpe_ratio(returns)
    drawdowns, max_dd = calculate_drawdowns(portfolio_df["Value"])

    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")

    # 1. Convert trade list to DataFrame
    trade_dicts = [t.__dict__ for t in execution_handler.trades]
    trade_df = pd.DataFrame(trade_dicts)
    trade_df.set_index('timestamp', inplace=True)

    # 2. Save to CSV
    trade_df.to_csv('reports/trade_log.csv')

    print("Trade log saved to reports/trade_log.csv")

    # Plot results
    plot_equity_curve(portfolio_df["Value"], drawdowns)

    # Get the last closing price as a Python float
    last_price = data_with_signals["Close"].iloc[-1].item()

    # Compute portfolio value on that last price
    final_value = portfolio.value({"SPY": last_price})

    # Now final_value is a numeric (float) and the formatter will work
    print(f"Final portfolio value: ${final_value:,.2f}")

if __name__ == "__main__":
    main()
# main.py
# Entry point for running the backtest

from engine.data_handler import DataHandler
from strategies.strategy_template import MovingAverageCrossoverStrategy
from engine.portfolio import Portfolio
from engine.execution_handler import ExecutionHandler

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

    # Basic trading loop (placeholder for full event-driven system)
    for date, row in data_with_signals.iterrows():
        signal = row['signal']
        price = row['Close']

        if signal == 1:
            execution_handler.execute_order("BUY", "SPY", 10, price)
            portfolio.buy("SPY", 10, price)

        elif signal == -1:
            execution_handler.execute_order("SELL", "SPY", 10, price)
            portfolio.sell("SPY", 10, price)

    final_value = portfolio.value({"SPY": data_with_signals.iloc[-1]['Close']})
    print(f"Final portfolio value: ${final_value:,.2f}")

if __name__ == "__main__":
    main()
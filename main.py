# main.py

import pandas as pd

# Core components
from engine.multi_data_handler import MultiDataHandler
from engine.execution_handler import ExecutionHandler
from engine.portfolio import Portfolio

# Strategies
from strategies.momentum_strategy import MomentumStrategy
from strategies.pairs_strategy import PairsTradingStrategy

# Performance & risk
from utils.performance import (
    calculate_returns, calculate_sharpe_ratio,
    calculate_drawdowns, plot_equity_curve
)
from utils.risk import historical_var, expected_shortfall

def main():
    # 1) Parameters
    symbols    = ["AAPL","MSFT","GOOG","AMZN"]          # for your momentum example
    start_date = "2020-01-01"
    end_date   = "2023-01-01"
    initial_cap = 100_000

    # 2) Load multi‐asset data
    data_handler = MultiDataHandler(symbols, start_date, end_date)
    price_data   = data_handler.load_data()            # dict of DataFrames

    # 3) Choose & generate signals
    strat = MomentumStrategy(lookback=90, top_k=2, bottom_k=2)
    signals = strat.generate_signals(price_data)
    # signals is a DataFrame indexed by date, columns=symbols, values in {+1,0,-1}

    # 4) Setup backtest engine
    exec_h = ExecutionHandler(commission_per_trade=1.0, slippage_pct=0.0005)
    port   = Portfolio(initial_capital=initial_cap)

    # 5) Run the backtest
    # track daily total portfolio value
    port_values = []

    # Remember previous signal per symbol to trade only on changes
    prev_sigs = {sym: 0 for sym in symbols}

    for date in signals.index:
        today_prices = {sym: price_data[sym].loc[date, "Close"] for sym in symbols}
        today_sigs   = signals.loc[date]

        # loop each asset
        for sym in symbols:
            sig  = int(today_sigs[sym])
            prev = prev_sigs[sym]
            price = today_prices[sym]

            # BUY signal only on crossover up
            if sig == 1 and prev != 1:
                exec_h.execute_order("BUY", sym, 10, price)
                port.buy(sym, 10, price, commission=exec_h.commission)

            # SELL signal only on crossover down
            elif sig == -1 and prev != -1:
                exec_h.execute_order("SELL", sym, 10, price)
                port.sell(sym, 10, price, commission=exec_h.commission)

            prev_sigs[sym] = sig

        # record portfolio value after all trades that day
        total_val = port.value(today_prices)
        port_values.append((date, total_val))

    # 6) Build a DataFrame of values
    df_vals = pd.DataFrame(port_values, columns=["Date","Value"]).set_index("Date")

    # 7) Performance analytics
    returns = calculate_returns(df_vals["Value"])
    sharpe  = calculate_sharpe_ratio(returns)
    drawdn, max_dd = calculate_drawdowns(df_vals["Value"])
    var_hist = historical_var(returns)
    es       = expected_shortfall(returns)

    print(f"Final portfolio value: ${df_vals['Value'].iloc[-1]:,.2f}")
    print(f"Sharpe Ratio:          {sharpe:.2f}")
    print(f"Max Drawdown:         {max_dd:.2%}")
    print(f"Historical VaR (5%):  {var_hist:.2%}")
    print(f"Expected Shortfall:   {es:.2%}")

    # 8) Plot
    plot_equity_curve(df_vals["Value"], drawdn)

    # 9) Export trade log if you have one
    trades = [t.__dict__ for t in exec_h.trades]
    pd.DataFrame(trades).to_csv("reports/trade_log.csv", index=False)

if __name__ == "__main__":
    main()
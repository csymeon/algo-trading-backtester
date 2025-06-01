# utils/backtester.py

import pandas as pd
from engine.execution_handler import ExecutionHandler
from engine.portfolio         import Portfolio

class Backtester:
    def __init__(self,
                 strategy,            # an instance of any Strategy class
                 initial_capital=100000,
                 qty_per_trade=10,
                 commission=0.0,
                 slippage=0.0,
                 stop_loss_pct=None,  # e.g. 0.05 = 5% stop‐loss
                 take_profit_pct=None # e.g. 0.10 = 10% take‐profit
    ):
        self.strategy       = strategy
        self.initial_capital= initial_capital
        self.qty_per_trade  = qty_per_trade
        self.commission     = commission
        self.slippage       = slippage
        self.stop_loss_pct  = stop_loss_pct
        self.take_profit_pct= take_profit_pct

    def run(self, price_series: pd.Series, symbol: str) -> pd.DataFrame:
        """
        1) Calls self.strategy.generate_signals(price_series) → DataFrame with ["Close","signal"].  
        2) Steps through each date, applies buys/sells, enforces stop‐loss/take‐profit if configured.  
        3) Records a snapshot each day (or only on trades, depending on design).  
        Returns a DataFrame with index=date and columns=["cash","positions","total_equity","signal","price"].  
        """
        df_signals = self.strategy.generate_signals(price_series)
        exec_h = ExecutionHandler(commission_per_trade=self.commission,
                                  slippage_pct=self.slippage)
        port   = Portfolio(initial_capital=self.initial_capital)

        prev_signal = 0
        history = []

        for date, row in df_signals.iterrows():
            price  = float(row["Close"])
            signal = int(row["signal"])

            # Check stop‐loss or take‐profit on existing position, before new signal:
            if self.stop_loss_pct and port.positions.get(symbol, 0) > 0:
                entry_price = exec_h.last_trade_price(symbol)  # (assuming ExecutionHandler can expose that)
                drawdown = (price - entry_price) / entry_price
                if drawdown <= -self.stop_loss_pct:
                    exec_h.execute_order("SELL", symbol, self.qty_per_trade, price)
                    port.sell(symbol, self.qty_per_trade, price, commission=self.commission)

            # Standard MA‐crossover style entry/exit:
            if signal == 1 and prev_signal != 1:
                exec_h.execute_order("BUY", symbol, self.qty_per_trade, price)
                port.buy(symbol, self.qty_per_trade, price, commission=self.commission)

            elif signal == -1 and prev_signal != -1:
                exec_h.execute_order("SELL", symbol, self.qty_per_trade, price)
                port.sell(symbol, self.qty_per_trade, price, commission=self.commission)

            prev_signal = signal

            # In any case, snapshot EOD (cash, positions, total):
            total = port.value({symbol: price})
            history.append({
                "timestamp":   date,
                "cash":        port.cash,
                "positions":   port.positions.copy(),
                "total_equity":total,
                "signal":      signal,
                "price":       price
            })

        return pd.DataFrame(history).set_index("timestamp")
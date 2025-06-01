# engine/portfolio.py
import pandas as pd
import datetime
from typing import Dict

class Portfolio:
    def __init__(self, initial_capital: float):
        # 1) Basic state
        self.initial_capital = initial_capital
        self.cash            = initial_capital
        self.positions       = {}      # e.g. {"AAPL": 10, "MSFT": 5}

        # 2) Internal history list. We'll append one tuple per “snapshot call.”
        #    Format per entry: (timestamp, cash, positions_copy, total_value)
        self._history = []

    def buy(self, symbol: str, quantity: int, price: float, commission: float, timestamp=None):
        """
        Buy `quantity` shares of `symbol` at `price`, minus `commission`.
        Updates cash & positions. Optionally takes `timestamp` so we can record immediately.
        """
        cost = quantity * price + commission
        self.cash -= cost
        self.positions[symbol] = self.positions.get(symbol, 0) + quantity

        # If user provided a timestamp, snapshot right away:
        if timestamp is not None:
            self._record(timestamp, {symbol: price})

    def sell(self, symbol: str, quantity: int, price: float, commission: float, timestamp=None):
        """
        Sell `quantity` shares of `symbol` at `price`, minus `commission`.
        Updates cash & positions. Optionally takes `timestamp` so we can record immediately.
        """
        proceeds = quantity * price - commission
        self.cash += proceeds

        new_qty = self.positions.get(symbol, 0) - quantity
        if new_qty <= 0:
            # Either we liquidated entirely or oversold (assume user never oversells).
            self.positions.pop(symbol, None)
        else:
            self.positions[symbol] = new_qty

        if timestamp is not None:
            self._record(timestamp, {symbol: price})

    def value(self, current_prices: dict) -> float:
        """
        Compute total portfolio value = cash + sum(qty_i * current_price_i) for each open position.
        """
        pos_value = 0.0
        for sym, qty in self.positions.items():
            price = current_prices.get(sym)
            if price is None:
                raise KeyError(f"Missing price for symbol '{sym}' when computing portfolio value.")
            pos_value += qty * price
        return self.cash + pos_value

    def _record(self, timestamp, current_prices: dict):
        """
        Internal: append a snapshot of (timestamp, cash, positions_dict, total_value).
        We'll store a shallow copy of positions so that later changes don't mutate old history.
        """
        total = self.value(current_prices)
        # Make a copy of positions so that future modifications don’t retroactively change history.
        positions_copy = self.positions.copy()
        self._history.append((timestamp, self.cash, positions_copy, total))

    def snapshot(self, timestamp, current_prices: dict):
        """
        Public alias for _record: lets outside code explicitly say “take a snapshot now.”
        Exactly equivalent to self._record(...).
        """
        self._record(timestamp, current_prices)

    def history(self) -> pd.DataFrame:
        """
        Return a DataFrame showing historical snapshots. The DataFrame’s index is `timestamp`,
        and columns are:
            • cash           (float)
            • positions      (dict of symbol→quantity)
            • total_equity   (float)
        If no history exists yet, returns an empty DataFrame with those columns.
        """
        if not self._history:
            return pd.DataFrame(columns=["cash", "positions", "total_equity"])

        df = pd.DataFrame(self._history, columns=["timestamp", "cash", "positions", "total_equity"])
        df.set_index("timestamp", inplace=True)
        return df

    def cash_history(self) -> pd.DataFrame:
        """
        If you only care about cash vs total_equity (and not the raw positions dict),
        you can drop the 'positions' column here and see just cash/total:
        """
        df = self.history()[["cash", "total_equity"]]
        return df

    def current_cash(self) -> float:
        """Quick getter for your live cash balance."""
        return self.cash

    def current_positions(self) -> dict:
        """Quick getter for your live positions dict."""
        return self.positions.copy()
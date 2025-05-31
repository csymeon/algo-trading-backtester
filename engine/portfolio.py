# engine/portfolio.py
import pandas as pd
import datetime
from typing import Dict

class Portfolio:
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.positions = {}
        self.cash = initial_capital
        self._history        = []    # list of (timestamp, cash, total_value)


    def buy(self, symbol, quantity, price, commission=0.0):
        self.positions[symbol] = self.positions.get(symbol, 0) + quantity
        self.cash -= quantity * price
        self.cash -= commission  # deduct commission

    def sell(self, symbol, quantity, price, commission=0.0):
        self.positions[symbol] = self.positions.get(symbol, 0) - quantity
        self.cash += quantity * price
        self.cash -= commission  # deduct commission

    def value(self, current_prices: dict) -> float:
        """
        Compute total portfolio value; if record=True, 
        auto‐append a (today, cash, total) row to history.
        """
        pos_value = sum(qty * current_prices[sym] for sym, qty in self.positions.items())
        total = self.cash + pos_value
        return total
    
    def cash_history(self) -> pd.DataFrame:
        """
        Returns a DataFrame indexed by timestamp with columns ['cash','total'].
        """
        df = pd.DataFrame(self._history, columns=['timestamp','cash','total'])
        df.set_index('timestamp', inplace=True)
        return df
    
    def _record(self, timestamp):
        """
        Internal: append (date, cash, total_value)
        """
        total = self.value({s: p for s, p in self.positions.items()}) \
                if self.positions else self.cash
        self._history.append((timestamp, self.cash, total))
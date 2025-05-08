# strategies/momentum_strategy.py

import pandas as pd
import numpy as np

class MomentumStrategy:
    """
    Simple cross-sectional momentum:
    - Rank assets by n-day return
    - Long top_k, short bottom_k
    """
    def __init__(self, lookback: int = 90, top_k: int = 3, bottom_k: int = 3):
        self.lookback = lookback
        self.top_k     = top_k
        self.bottom_k = bottom_k

    def generate_signals(self, multi_data: dict) -> pd.DataFrame:
        """
        multi_data: dict of { symbol: DataFrame } with 'Close' column.
        Returns a DataFrame signals[symbol] = +1/0/−1 per date.
        """
        # build a price panel
        prices = pd.DataFrame({
            sym: df['Close'] for sym, df in multi_data.items()
        })

        # compute returns
        ret = prices.pct_change(self.lookback).shift(1)
        signals = pd.DataFrame(0, index=prices.index, columns=prices.columns)

        # On each date, rank and assign +1, −1
        for date in ret.index:
            today = ret.loc[date].dropna()
            if len(today) < (self.top_k + self.bottom_k):
                continue
            ranked = today.rank(ascending=False)
            longs  = ranked[ranked <= self.top_k].index
            shorts = ranked[ranked > (len(today) - self.bottom_k)].index
            signals.loc[date, longs]  = 1
            signals.loc[date, shorts] = -1

        return signals
# strategies/pairs_trading_strategy.py

import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import coint

class PairsTradingStrategy:
    """
    Finds co-integrated pairs and trades on z-score of the spread.
    """
    def __init__(self, symbol_x: str, symbol_y: str, lookback: int = 252, z_entry: float = 2.0, z_exit: float = 0.5):
        self.x = symbol_x
        self.y = symbol_y
        self.lookback = lookback
        self.z_entry  = z_entry
        self.z_exit   = z_exit

    def fit(self, df_x: pd.Series, df_y: pd.Series):
        # test cointegration and estimate hedge ratio via OLS
        self.ratio = (df_x / df_y).rolling(self.lookback).mean()
        # track z-score of spread
        spread = df_x - self.ratio * df_y
        self.zscore = (spread - spread.rolling(self.lookback).mean()) / spread.rolling(self.lookback).std()

    def generate_signals(self, multi_data: dict) -> pd.DataFrame:
        px = multi_data[self.x]['Close']
        py = multi_data[self.y]['Close']
        self.fit(px, py)

        # signal DataFrame
        sig = pd.DataFrame(0, index=px.index, columns=[self.x, self.y])
        sig.loc[self.zscore >  self.z_entry, [self.x, self.y]] = [-1, 1]
        sig.loc[self.zscore < -self.z_entry, [self.x, self.y]] = [1, -1]
        sig.loc[self.zscore.abs() < self.z_exit, [self.x, self.y]] = [0, 0]
        return sig
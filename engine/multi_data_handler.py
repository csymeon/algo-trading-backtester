# engine/multi_data_handler.py

import yfinance as yf
import pandas as pd

class MultiDataHandler:
    """
    Fetches and organizes OHLC data for multiple symbols.
    Returns a dict of DataFrames or a single DataFrame with MultiIndex.
    """
    def __init__(self, symbols, start_date, end_date):
        self.symbols    = symbols
        self.start_date = start_date
        self.end_date   = end_date

    def load_data(self):
        # group_by='ticker' gives a dict-like structure
        raw = yf.download(
            tickers=self.symbols,
            start=self.start_date,
            end=self.end_date,
            group_by='ticker',
            auto_adjust=True,
            progress=False
        )
        # Convert into a dict: { symbol: DataFrame }
        data = {}
        for sym in self.symbols:
            df = raw[sym].copy()
            df.dropna(inplace=True)
            data[sym] = df
        return data
# strategies/strategy_template.py
import pandas as pd

class MovingAverageCrossoverStrategy:
    def __init__(self, short_window=50, long_window=200):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, data):
        """
        Accepts either a pd.Series (prices) or a pd.DataFrame with 'Close'.
        Returns a DataFrame with at least these columns:
          - 'Close'  : the price series
          - 'signal' : the trading signal (+1, 0, -1)
        """
        # 1) Wrap a Series into a DataFrame
        if isinstance(data, pd.Series):
            df = data.to_frame(name="Close")
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            raise ValueError("Data must be a pandas Series or DataFrame")

        # 2) Compute moving averages
        df["short_ma"] = df["Close"].rolling(self.short_window).mean()
        df["long_ma"]  = df["Close"].rolling(self.long_window).mean()

        # 3) Generate the signal column
        df["signal"] = 0
        df.loc[df["short_ma"] > df["long_ma"], "signal"] = 1
        df.loc[df["short_ma"] < df["long_ma"], "signal"] = -1

        return df
import pandas as pd

class BuyAndHoldStrategy:
    """
    Naïve strategy: go long at the first bar and hold until the end.
    """
    def generate_signals(self, prices: pd.Series) -> pd.Series:
        # Always +1 on every bar
        signals = pd.Series(1, index=prices.index)
        return signals
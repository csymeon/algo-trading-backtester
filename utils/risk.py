# utils/risk.py

import numpy as np
import pandas as pd

def historical_var(returns: pd.Series, level: float = 0.05) -> float:
    """
    Historical VaR: the level-th percentile of losses.
    """
    if returns.empty:
        return 0.0
    # losses are negative returns
    var = -np.percentile(returns, level * 100)
    return var

def parametric_var(returns: pd.Series, level: float = 0.05) -> float:
    """
    Gaussian VaR: μ + σ * z, where z is the normal quantile
    """
    mu, sigma = returns.mean(), returns.std()
    z = np.abs( np.percentile(np.random.randn(1_000_000), level * 100) )
    return -(mu + sigma * z)

def expected_shortfall(returns: pd.Series, level: float = 0.05) -> float:
    """
    Expected Shortfall (CVaR): mean of the worst losses beyond VaR
    """
    if returns.empty:
        return 0.0
    cutoff = np.percentile(returns, level * 100)
    tail   = returns[returns <= cutoff]
    return -tail.mean()
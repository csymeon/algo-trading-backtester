# utils/risk.py

import numpy as np
import pandas as pd

from utils.performance import skewness, kurtosis

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

def var_historic(r, level=5):
    """
    Returns the historic Value at Risk at a specified level
    i.e. returns the number such that "level" percent of the returns
    fall below that number, and the (100-level) percent are above
    """
    if isinstance(r, pd.DataFrame):
        return r.aggregate(var_historic, level=level)
    elif isinstance(r, pd.Series):
        return -np.percentile(r, level)
    else:
        raise TypeError("Expected r to be a Series or DataFrame")


def cvar_historic(r, level=5):
    """
    Computes the Conditional VaR of Series or DataFrame
    """
    if isinstance(r, pd.Series):
        is_beyond = r <= -var_historic(r, level=level)
        return -r[is_beyond].mean()
    elif isinstance(r, pd.DataFrame):
        return r.aggregate(cvar_historic, level=level)
    else:
        raise TypeError("Expected r to be a Series or DataFrame")


from scipy.stats import norm
def var_gaussian(r, level=5, modified=False):
    """
    Returns the Parametric Gauusian VaR of a Series or DataFrame
    If "modified" is True, then the modified VaR is returned,
    using the Cornish-Fisher modification
    """
    # compute the Z score assuming it was Gaussian
    z = norm.ppf(level/100)
    if modified:
        # modify the Z score based on observed skewness and kurtosis
        s = skewness(r)
        k = kurtosis(r)
        z = (z +
                (z**2 - 1)*s/6 +
                (z**3 -3*z)*(k-3)/24 -
                (2*z**3 - 5*z)*(s**2)/36
            )
    return -(r.mean() + z*r.std(ddof=0))

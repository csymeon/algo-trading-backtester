# utils/performance.py

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def calculate_returns(portfolio_values, type='simple'):
    """
    Calculate returns from portfolio values.
    :param portfolio_values: Series or DataFrame of portfolio values over time.
    :param type: 'simple' for simple returns, 'log' for log returns.
    :return: Series or DataFrame of returns.
    """
    if type not in ['simple', 'log']:
        raise NotImplementedError("type must be 'simple' or 'log'.")
    elif type == 'log':
        returns = np.log(portfolio_values / portfolio_values.shift(1)).dropna()
    elif type == 'simple':
        # Simple returns
        returns = portfolio_values.pct_change().dropna()
    return returns

def compound(r):
    """
    returns the result of compounding the set of returns in r
    """
    return np.expm1(np.log1p(r).sum())

                         
def annualize_rets(r, periods_per_year):
    """
    Annualizes a set of returns
    We should infer the periods per year
    but that is currently left as an exercise
    to the reader :-)
    """
    compounded_growth = (1+r).prod()
    n_periods = r.shape[0]
    return compounded_growth**(periods_per_year/n_periods)-1


def annualize_vol(r, periods_per_year):
    """
    Annualizes the vol of a set of returns
    We should infer the periods per year
    but that is currently left as an exercise
    to the reader :-)
    """
    return r.std()*(periods_per_year**0.5)


def calculate_sharpe_ratio(r, riskfree_rate, periods_per_year):
    """
    Computes the annualized sharpe ratio of a set of returns
    """
    # convert the annual riskfree rate to per period
    rf_per_period = (1+riskfree_rate)**(1/periods_per_year)-1
    excess_ret = r - rf_per_period
    ann_ex_ret = annualize_rets(excess_ret, periods_per_year)
    ann_vol = annualize_vol(r, periods_per_year)
    return ann_ex_ret/ann_vol

def calculate_drawdown(return_series: pd.Series):
    """Takes a time series of asset returns.
       returns a DataFrame with columns for
       the wealth index, 
       the previous peaks, and 
       the percentage drawdown
    """
    wealth_index = 1000*(1+return_series).cumprod()
    previous_peaks = wealth_index.cummax()
    drawdowns = (wealth_index - previous_peaks)/previous_peaks
    return pd.DataFrame({"Wealth": wealth_index, 
                         "Previous Peak": previous_peaks, 
                         "Drawdown": drawdowns})

def plot_equity_curve(portfolio_values, drawdowns=None):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(portfolio_values, label="Portfolio Value")
    if drawdowns is not None:
        ax.plot(drawdowns, label="Drawdown", color='red', alpha=0.3)
        ax.secondary_yaxis('right', functions=(lambda x: x, lambda x: str(x*100) + '%'))
    ax.set_title("Portfolio Value Over Time")
    ax.set_ylabel("Value")
    ax.legend()
    plt.grid(True)
    # plt.tight_layout()
    plt.show()
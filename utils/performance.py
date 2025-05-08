# utils/performance.py

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def calculate_returns(portfolio_values):
    returns = portfolio_values.pct_change().dropna()
    return returns

def calculate_sharpe_ratio(returns, risk_free_rate=0.01):
    excess_returns = returns - (risk_free_rate / 252)
    sharpe = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
    return sharpe

def calculate_drawdowns(portfolio_values):
    cumulative = portfolio_values
    peak = cumulative.cummax()
    drawdown = (cumulative - peak) / peak
    max_drawdown = drawdown.min()
    return drawdown, max_drawdown

def plot_equity_curve(portfolio_values, drawdowns=None):
    fig, ax = plt.subplots(figsize=(10, 6))
    portfolio_values.plot(ax=ax, label="Portfolio Value")
    if drawdowns is not None:
        drawdowns.plot(ax=ax, label="Drawdown", secondary_y=True, color='red', alpha=0.3)
    ax.set_title("Portfolio Value Over Time")
    ax.set_ylabel("Value")
    ax.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
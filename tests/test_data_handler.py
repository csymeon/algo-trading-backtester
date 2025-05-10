# tests/test_data_handler.py

import pandas as pd
import pytest
from engine.data_handler import DataHandler

def test_load_data(monkeypatch):
    # Create dummy DataFrame
    df = pd.DataFrame({
        "Open": [1, 2],
        "High": [1, 2],
        "Low": [1, 2],
        "Close": [1, 2],
        "Volume": [100, 200]
    }, index=pd.date_range("2020-01-01", periods=2))
    # Monkey-patch yfinance download
    monkeypatch.setattr("engine.data_handler.yf.download", lambda symbol, start, end: df)
    handler = DataHandler("AAA", "2020-01-01", "2020-01-02")
    data = handler.load_data()
    assert isinstance(data, pd.DataFrame)
    assert list(data["Close"]) == [1, 2]
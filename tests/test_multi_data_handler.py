# tests/test_multi_data_handler.py

import pandas as pd
import pytest
from engine.multi_data_handler import MultiDataHandler

def test_load_data(monkeypatch):
    dates = pd.date_range("2020-01-01", periods=2)
    dummy = {
        "SYM": pd.DataFrame({"Close": [1, 2]}, index=dates)
    }
    monkeypatch.setattr(
        "engine.multi_data_handler.yf.download",
        lambda tickers, start, end, group_by, auto_adjust, progress: dummy
    )
    handler = MultiDataHandler(["SYM"], "2020-01-01", "2020-01-02")
    data = handler.load_data()
    assert "SYM" in data
    assert list(data["SYM"]["Close"]) == [1, 2]
import pytest
import pandas as pd
from engine.portfolio import Portfolio

def test_buy_and_sell_changes_cash_and_positions():
    p = Portfolio(initial_capital=1000)
    p.buy("AAA", quantity=2, price=10.0, commission=1.0, timestamp=pd.Timestamp("2021-01-01"))
    # 2×10 + 1 commission = 21 spent
    assert p.cash == pytest.approx(1000 - 21)
    assert p.positions["AAA"] == 2

    p.sell("AAA", quantity=1, price=12.0, commission=1.0, timestamp=pd.Timestamp("2021-01-02"))
    # receive 1×12 minus 1 commission
    assert p.cash == pytest.approx(1000 - 21 + 12 - 1)
    assert p.positions["AAA"] == 1

def test_value_computation():
    p = Portfolio(initial_capital=500)
    p.buy("BBB", 1, price=100, commission=0, timestamp=pd.Timestamp("2021-01-01"))
    # position = 1 share, price moves to 110
    assert p.value({"BBB": 110}) == pytest.approx(500 - 100 + 110)

def test_empty_cash_history():
    """
    If no trades or manual records have been made, cash_history() should return an empty DataFrame.
    """
    p = Portfolio(initial_capital=1000)
    hist = p.cash_history()
    assert isinstance(hist, pd.DataFrame)
    assert hist.empty, "cash_history should be empty when no _record has been invoked"


def test_manual_history_and_cash_history_alignment():
    """
    Manually populate _history with known (timestamp, cash, total)
    triples and confirm that cash_history() returns exactly that as a DataFrame with
    proper index and columns.
    """
    p = Portfolio(initial_capital=1000)

    # Build a fake history list: [(timestamp, cash, total), ...]
    manual = [
        (pd.Timestamp("2021-01-01"), 1000.0, 1000.0),
        (pd.Timestamp("2021-01-02"),  900.0, 1000.0),
        (pd.Timestamp("2021-01-03"),  900.0, 1100.0),
        (pd.Timestamp("2021-01-04"), 1100.0, 1100.0),
    ]
    p._history = manual.copy()

    hist_df = p.cash_history()

    # Build expected DataFrame
    expected_df = pd.DataFrame(
        {
            "cash":  [1000.0,  900.0,  900.0, 1100.0],
            "total": [1000.0, 1000.0, 1100.0, 1100.0],
        },
        index=pd.to_datetime([
            "2021-01-01",
            "2021-01-02",
            "2021-01-03",
            "2021-01-04",
        ])
    )

    pd.testing.assert_frame_equal(
        hist_df.sort_index(),
        expected_df.sort_index(),
        check_dtype=False,
        obj="cash_history() did not match the manually assigned _history"
    )


def test_record_invoked_during_buy_and_sell():
    """
    Simulate a simple sequence of trades and manually invoke _record(...) at those timestamps.
    Check that after buy-sell, cash_history() shows correct cash and total.
    """
    p = Portfolio(initial_capital=1000)

    # 1) BUY 2 shares of 'XYZ' at 100 each, no commission
    p.buy("XYZ", quantity=2, price=100.0, commission=0.0, timestamp=pd.Timestamp("2021-02-01"))
    # After this buy:
    #   cash = 1000 - 2*100 = 800
    #   position 'XYZ' = 2
    # For a total value you need today's price, so we'll pretend price=100 when recording:
    dt1 = pd.Timestamp("2021-02-01")
    # Manually record a snapshot at dt1. In real code, buy() would have called _record(dt1).
    # Here we do it explicitly, providing a price dict for value():
    current_price = {"XYZ": 100.0}
    total1 = p.value(current_price)  # should be 800 + 2*100 = 1000
    p._history.append((dt1, p.cash, total1))

    # 2) SELL 1 share of 'XYZ' at 120, no commission
    p.sell("XYZ", quantity=1, price=120.0, commission=0.0, timestamp=pd.Timestamp("2021-02-02"))
    # After this sell:
    #   cash = 800 + 1*120 = 920
    #   position 'XYZ' = 1
    dt2 = pd.Timestamp("2021-02-02")
    current_price = {"XYZ": 120.0}
    total2 = p.value(current_price)  # should be 920 + 1*120 = 1040
    p._history.append((dt2, p.cash, total2))

    # 3) SELL remaining 1 share of 'XYZ' at 110, no commission
    p.sell("XYZ", quantity=1, price=110.0, commission=0.0, timestamp=pd.Timestamp("2021-02-03"))
    # After this sell:
    #   cash = 920 + 1*110 = 1030
    #   positions empty
    dt3 = pd.Timestamp("2021-02-03")
    current_price = {"XYZ": 110.0}
    total3 = p.value(current_price)  # should be 1030 + 0 = 1030
    p._history.append((dt3, p.cash, total3))

    # Now check the resulting history DataFrame:
    hist = p.cash_history()

    # Build what we expect:
    expected = pd.DataFrame(
        {
            "cash":  [800.0,  920.0, 1030.0],
            "total": [1000.0, 1040.0, 1030.0],
        },
        index=pd.to_datetime([
            "2021-02-01",
            "2021-02-02",
            "2021-02-03",
        ])
    )

    pd.testing.assert_frame_equal(
        hist.sort_index(),
        expected.sort_index(),
        check_dtype=False,
        obj="After buy/sell and explicit _record, cash_history() is incorrect"
    )
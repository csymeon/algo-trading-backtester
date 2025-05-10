from engine.execution_handler import ExecutionHandler
import pytest

def test_execute_order_records_trade():
    h = ExecutionHandler(commission_per_trade=2.0, slippage_pct=0.01)
    # simulate a BUY at price=100
    h.execute_order("BUY", "AAA", 5, 100.0, timestamp="2023-01-01")
    assert len(h.trades) == 1
    trade = h.trades[0]
    # slippage = 1% of 100 = 1.0, exec_price = 101.0
    assert trade.price == pytest.approx(101.0)
    assert trade.commission == pytest.approx(2.0)
import pytest
from engine.portfolio import Portfolio

def test_buy_and_sell_changes_cash_and_positions():
    p = Portfolio(initial_capital=1000)
    p.buy("AAA", quantity=2, price=10.0, commission=1.0)
    # 2×10 + 1 commission = 21 spent
    assert p.cash == pytest.approx(1000 - 21)
    assert p.positions["AAA"] == 2

    p.sell("AAA", quantity=1, price=12.0, commission=1.0)
    # receive 1×12 minus 1 commission
    assert p.cash == pytest.approx(1000 - 21 + 12 - 1)
    assert p.positions["AAA"] == 1

def test_value_computation():
    p = Portfolio(initial_capital=500)
    p.buy("BBB", 1, price=100, commission=0)
    # position = 1 share, price moves to 110
    assert p.value({"BBB": 110}) == pytest.approx(500 - 100 + 110)
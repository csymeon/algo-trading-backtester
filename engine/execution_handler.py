# engine/execution_handler.py

from .trade import Trade
from datetime import datetime

class ExecutionHandler:
    def __init__(self, commission_per_trade=1.0, slippage_pct=0.0):
        """
        commission_per_trade: fixed cost per order
        slippage_pct: fraction of price lost on each trade
        """
        self.commission = commission_per_trade
        self.total_commission = 0.0
        self.slippage_pct = slippage_pct
        self.total_slippage = 0.0
        self.trades = []  # will store Trade objects

    def execute_order(self, order_type, symbol, quantity, price, timestamp):
        # 1. Calculate slippage impact
        slippage = price * self.slippage_pct
        self.total_slippage += slippage
        self.total_commission += self.commission
        exec_price = price + slippage if order_type == "BUY" else price - slippage

        # 2. Build a Trade record
        trade = Trade(
            timestamp=timestamp,
            symbol=symbol,
            order_type=order_type,
            quantity=quantity,
            price=exec_price,
            commission=self.commission,
            slippage=slippage
        )

        # 3. Store it
        self.trades.append(trade)

        # 4. (Optional) Print to console for live visibility
        # print(f"{order_type} {quantity} {symbol} @ {exec_price:.2f} "
        #       f"(comm: {self.commission:.2f}, slip: {slippage:.2f})")
        return True
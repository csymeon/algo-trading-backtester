# engine/trade.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Trade:
    timestamp: datetime
    symbol: str
    order_type: str     # "BUY" or "SELL"
    quantity: int
    price: float
    commission: float
    slippage: float
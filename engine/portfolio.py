# engine/portfolio.py

class Portfolio:
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.positions = {}
        self.cash = initial_capital

    def buy(self, symbol, quantity, price, commission=0.0):
        self.positions[symbol] = self.positions.get(symbol, 0) + quantity
        self.cash -= quantity * price
        self.cash -= commission  # deduct commission

    def sell(self, symbol, quantity, price, commission=0.0):
        self.positions[symbol] = self.positions.get(symbol, 0) - quantity
        self.cash += quantity * price
        self.cash -= commission  # deduct commission

    def value(self, current_prices):
        value = self.cash
        for symbol, quantity in self.positions.items():
            value += current_prices.get(symbol, 0) * quantity
        return value
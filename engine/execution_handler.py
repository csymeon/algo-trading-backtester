# engine/execution_handler.py

class ExecutionHandler:
    def execute_order(self, order_type, symbol, quantity, price):
        print(f"{order_type} {quantity} shares of {symbol} at ${price:.2f}")
        return True
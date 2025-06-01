# utils/backtester.py

import pandas as pd
import numpy as np
from engine.execution_handler import ExecutionHandler
from engine.portfolio         import Portfolio

class Backtester:
    def __init__(self,
                 strategy,            # an instance of any Strategy class
                 initial_capital=100000,
                 qty_per_trade=10,
                 commission=0.0,
                 slippage=0.0,
                 stop_loss_pct=None,  # e.g. 0.05 = 5% stop‐loss
                 take_profit_pct=None # e.g. 0.10 = 10% take‐profit
    ):
        self.strategy       = strategy
        self.initial_capital= initial_capital
        self.qty_per_trade  = qty_per_trade
        self.commission     = commission
        self.slippage       = slippage
        self.stop_loss_pct  = stop_loss_pct
        self.take_profit_pct= take_profit_pct

    def run(self, price_data, symbol=None) -> pd.DataFrame:
        """
        price_data can be:
          1) a pd.Series of close prices for one symbol
          2) a pd.DataFrame (with at least a “Close” column) for one symbol
          3) a dict { symbol: Series_or_DataFrame }

        If price_data is #1 or #2, you must pass ‘symbol’ as a string.
        If price_data is #3, ‘symbol’ may be ignored because keys are in the dict.

        Returns a DataFrame indexed by date with columns:
            ["cash", "positions", "total_equity", "signal_[SYM1]", "signal_[SYM2]", …, "price_[SYM1]", …]
        """
        # ─────────────── Step 1: Normalize price_data → dict[str, pd.Series] ───────────────
        if isinstance(price_data, pd.Series):
            if symbol is None:
                raise ValueError("If you pass a pd.Series, you must also pass `symbol='…'` explicitly.")
            close_dict = { symbol: price_data.copy().astype(float) }

        elif isinstance(price_data, pd.DataFrame):
            # assume it's a single‐symbol DataFrame with a "Close" column
            if symbol is None:
                raise ValueError("If you pass a DataFrame, you must also pass `symbol='…'` explicitly.")
            if "Close" not in price_data.columns:
                raise KeyError(f"DataFrame for '{symbol}' must have a 'Close' column.")
            close_dict = { symbol: price_data["Close"].copy().astype(float) }

        elif isinstance(price_data, dict):
            # each value in price_data should be either a Series or a DataFrame
            close_dict = {}
            for sym, df_or_ser in price_data.items():
                if isinstance(df_or_ser, pd.Series):
                    close_dict[sym] = df_or_ser.copy().astype(float)
                elif isinstance(df_or_ser, pd.DataFrame):
                    if "Close" not in df_or_ser.columns:
                        raise KeyError(f"DataFrame for '{sym}' must have a 'Close' column.")
                    close_dict[sym] = df_or_ser["Close"].copy().astype(float)
                else:
                    raise TypeError(f"Expected price_data['{sym}'] to be a Series or DataFrame.")
            # After this loop, close_dict = { sym: pd.Series_of_closes }

        else:
            raise TypeError("price_data must be a pd.Series, pd.DataFrame, or dict of those.")

        # ─────────────── Step 2: Generate signals from the normalized dict ───────────────
        # Many strategies accept a dict of symbols→Series and return a DataFrame of signals.
        # e.g. for single‐symbol, they’ll return DataFrame with columns ["Close","signal"].
        # for multi‐symbol, they might return DataFrame with a column “signal_[SYM1]”, etc.
        signals_df = self.strategy.generate_signals(close_dict)

        # ─────────────── Step 3: Determine the date range to iterate ───────────────
        # We want to iterate over the intersection of all dates in close_dict,
        # or—but often better—the union. Here we’ll use the intersection, so that
        # we only trade when *all* symbols have a valid price. If you want union,
        # just replace `.intersection` with `.union`.
        common_index = None
        for ser in close_dict.values():
            if common_index is None:
                common_index = ser.index
            else:
                common_index = common_index.intersection(ser.index)

        if common_index is None or len(common_index) == 0:
            raise ValueError("No overlapping dates found across symbols in price_data.")

        # We’ll iterate in sorted date order:
        common_index = common_index.sort_values()

        # ─────────────── Step 4: Set up ExecutionHandler & Portfolio ───────────────
        exec_h = ExecutionHandler(commission_per_trade=self.commission,
                                  slippage_pct=self.slippage)
        port   = Portfolio(initial_capital=self.initial_capital)

        # Keep a list of dicts for each timestep to build a final DataFrame
        history_records = []

        # If your strategy returns multiple “signal” columns (one per symbol),
        # we’ll detect them by prefix “signal_”
        signal_cols = [col for col in signals_df.columns if col.startswith("signal")]

        # track previous‐signal per symbol so we only change position on transitions
        prev_signals = { col: 0 for col in signal_cols }

        # ─────────────── Step 5: Main loop over dates ───────────────
        for date in common_index:
            # 5a) Gather prices for each symbol at this date
            price_at_date = {}
            for sym, ser in close_dict.items():
                price_at_date[sym] = float(ser.loc[date])

            # 5b) Collect all signals for this date into a dict
            #     If the strategy returned just one “signal” column (no prefix), treat that as single‐symbol
            current_signals = {}
            if "signal" in signals_df.columns:
                # single‐symbol case
                current_signals["signal"] = int(signals_df.loc[date, "signal"])
            else:
                # multi‐symbol case, e.g. "signal_AAPL", "signal_MSFT", etc.
                for col in signal_cols:
                    current_signals[col] = int(signals_df.loc[date, col])

            # 5c) Optionally enforce stop‐loss / take‐profit BEFORE new signals:
            #     (only makes sense if you already have a position)
            if self.stop_loss_pct is not None or self.take_profit_pct is not None:
                for col in signal_cols:
                    # strip off the "signal_" prefix to find the symbol name
                    # e.g. col="signal_AAPL" → sym="AAPL"
                    sym = col.replace("signal_", "")
                    qty_held = port.positions.get(sym, 0)
                    if qty_held != 0:
                        entry_price = exec_h.last_trade_price(sym) or np.nan
                        if np.isnan(entry_price):
                            continue  # no entry price recorded → skip
                        current_price = price_at_date[sym]
                        pnl_pct = (current_price - entry_price) / entry_price

                        if self.stop_loss_pct is not None and pnl_pct <= -self.stop_loss_pct:
                            # trigger a SELL for that symbol
                            exec_h.execute_order("SELL", sym, self.qty_per_trade, current_price)
                            port.sell(sym, self.qty_per_trade, current_price, commission=self.commission)

                        elif self.take_profit_pct is not None and pnl_pct >= self.take_profit_pct:
                            exec_h.execute_order("SELL", sym, self.qty_per_trade, current_price)
                            port.sell(sym, self.qty_per_trade, current_price, commission=self.commission)

            # 5d) Now apply the strategy signals (enter/exit on crossing 0 ↔ ±1)
            for col, sig in current_signals.items():
                sym = col.replace("signal_", "") if col.startswith("signal_") else symbol
                prev = prev_signals.get(col, 0)

                if sig == 1 and prev != 1:
                    # BUY one unit of sym
                    exec_h.execute_order("BUY", sym, self.qty_per_trade, price_at_date[sym])
                    port.buy(sym, self.qty_per_trade, price_at_date[sym], commission=self.commission)

                elif sig == -1 and prev != -1:
                    # SELL one unit of sym (or close short)
                    exec_h.execute_order("SELL", sym, self.qty_per_trade, price_at_date[sym])
                    port.sell(sym, self.qty_per_trade, price_at_date[sym], commission=self.commission)

                prev_signals[col] = sig

            # 5e) Take an end‐of‐day snapshot (cash + positions + equity)
            total_equity = port.value(price_at_date)
            record = {
                "timestamp":    date,
                "cash":         port.cash,
                "positions":    port.positions.copy(),
                "total_equity": total_equity,
            }
            # attach all signals and prices to this record too:
            for col, sig in current_signals.items():
                record[col] = sig
                sym = col.replace("signal_", "") if col.startswith("signal_") else symbol
                record[f"price_{sym}"] = price_at_date[sym]

            history_records.append(record)

        # ─────────────── Step 6: Build the final DataFrame ───────────────
        result = pd.DataFrame(history_records)
        result.set_index("timestamp", inplace=True)
        return result
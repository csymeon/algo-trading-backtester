import pandas as pd
import numpy as np

class Backtester:
    def __init__(
        self,
        strategy,
        exec_handler,       # injected ExecutionHandler
        portfolio,          # injected Portfolio
        qty_per_trade: int = 10,
        stop_loss_pct: float   = None,
        take_profit_pct: float = None,
    ):
        self.strategy        = strategy
        self.exec_h          = exec_handler
        self.portfolio       = portfolio
        self.qty_per_trade   = qty_per_trade
        self.stop_loss_pct   = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def run(self, price_data, symbol=None) -> pd.DataFrame:
        price_df_dict = self._normalize_input(price_data, symbol)
        signals_df    = self.strategy.generate_signals(price_df_dict)
        history_df    = self._apply_trades(price_df_dict, signals_df)
        return history_df

    def _normalize_input(self, price_data, symbol):
        price_df_dict = {}
        if isinstance(price_data, pd.Series):
            if symbol is None:
                raise ValueError("Must pass `symbol` when giving a Series.")
            price_df_dict[symbol] = pd.DataFrame({"Close": price_data.astype(float)})
        elif isinstance(price_data, pd.DataFrame):
            if symbol is None:
                raise ValueError("Must pass `symbol` when giving a DataFrame.")
            if "Close" not in price_data.columns:
                raise KeyError(f"DataFrame for '{symbol}' needs a 'Close' column.")
            price_df_dict[symbol] = price_data.copy()
        elif isinstance(price_data, dict):
            for sym, df_or_ser in price_data.items():
                if isinstance(df_or_ser, pd.Series):
                    price_df_dict[sym] = pd.DataFrame({"Close": df_or_ser.astype(float)})
                elif isinstance(df_or_ser, pd.DataFrame):
                    if "Close" not in df_or_ser.columns:
                        raise KeyError(f"DataFrame for '{sym}' must have a 'Close' column.")
                    price_df_dict[sym] = df_or_ser.copy()
                else:
                    raise TypeError(f"Expected Series or DataFrame for '{sym}'.")
        else:
            raise TypeError("price_data must be Series, DataFrame, or dict thereof.")
        return price_df_dict

    def _apply_trades(self, price_df_dict, signals_df):
        # 1) Build intersection of all indices
        common_idx = None
        for df in price_df_dict.values():
            common_idx = df.index if common_idx is None else common_idx.intersection(df.index)
        if common_idx is None or len(common_idx) == 0:
            raise ValueError("No overlapping dates in price data.")
        common_idx = common_idx.sort_values()

        # 2) Now treat each column of signals_df as “that symbol’s signal”
        #    so signal_cols = list of tickers, e.g. ["AAPL","BRK-B","JPM","GS"]
        signal_cols = list(signals_df.columns)
        # initialize prev_signals[sym] = 0 for each ticker
        prev_signals = {sym: 0 for sym in signal_cols}

        history = []

        for date in common_idx:
            # a) gather closes for each symbol on this date
            price_at_date = {
                sym: float(df.loc[date, "Close"])
                for sym, df in price_df_dict.items()
            }

            # b) gather signals for each symbol‐column
            #    (if a column or date is missing, fallback to 0)
            current_signals = {}
            for sym in signal_cols:
                try:
                    current_signals[sym] = int(signals_df.loc[date, sym])
                except KeyError:
                    # if for some reason that date or column isn’t in signals_df,
                    # assume no signal change (0)
                    current_signals[sym] = 0

            # ─── Debug print ───
            # print(f"[{date.date()}] prices: {price_at_date}, signals: {current_signals}")

            # c) optional stop‐loss / take‐profit on existing positions
            if self.stop_loss_pct or self.take_profit_pct:
                for sym in signal_cols:
                    qty_held = self.portfolio.positions.get(sym, 0)
                    if qty_held != 0:
                        entry_price = self.exec_h.last_trade_price(sym) or np.nan
                        if not np.isnan(entry_price):
                            pnl_pct = (price_at_date[sym] - entry_price) / entry_price
                            if self.stop_loss_pct and pnl_pct <= -self.stop_loss_pct:
                                self.exec_h.execute_order("SELL", sym, self.qty_per_trade, price_at_date[sym], date)
                                self.portfolio.sell(sym, self.qty_per_trade, price_at_date[sym],
                                                    commission=self.exec_h.commission)
                                # print(f"  → STOP-LOSS SELL {sym} @ {price_at_date[sym]}")
                            elif self.take_profit_pct and pnl_pct >= self.take_profit_pct:
                                self.exec_h.execute_order("SELL", sym, self.qty_per_trade, price_at_date[sym], date)
                                self.portfolio.sell(sym, self.qty_per_trade, price_at_date[sym],
                                                    commission=self.exec_h.commission)
                                # print(f"  → TAKE-PROFIT SELL {sym} @ {price_at_date[sym]}")

            # d) apply new signals (BUY/SELL on transition from prev_signals[sym] to current_signals[sym])
            for sym in signal_cols:
                sig  = current_signals[sym]
                prev = prev_signals[sym]

                if sig == 1 and prev != 1:
                    self.exec_h.execute_order("BUY", sym, self.qty_per_trade, price_at_date[sym], date)
                    self.portfolio.buy(sym, self.qty_per_trade, price_at_date[sym],
                                       commission=self.exec_h.commission)
                    # print(f"  → BUY {sym} @ {price_at_date[sym]}")

                elif sig == -1 and prev != -1:
                    self.exec_h.execute_order("SELL", sym, self.qty_per_trade, price_at_date[sym], date)
                    self.portfolio.sell(sym, self.qty_per_trade, price_at_date[sym],
                                        commission=self.exec_h.commission)
                    # print(f"  → SELL {sym} @ {price_at_date[sym]}")

                prev_signals[sym] = sig

            # e) snapshot end‐of‐day: cash, positions, total_equity
            total_equity = self.portfolio.value(price_at_date)
            record = {
                "timestamp":    date,
                "cash":         self.portfolio.cash,
                "positions":    self.portfolio.positions.copy(),
                "total_equity": total_equity,
            }
            # also add each signal and its price to the record
            for sym in signal_cols:
                record[f"signal_{sym}"]   = current_signals[sym]
                record[f"price_{sym}"]    = price_at_date[sym]

            history.append(record)

        df_hist = pd.DataFrame(history).set_index("timestamp")
        return df_hist
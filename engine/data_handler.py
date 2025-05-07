# engine/data_handler.py

import yfinance as yf

class DataHandler:
    def __init__(self, symbol, start_date, end_date):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date

    def load_data(self):
        data = yf.download(self.symbol, start=self.start_date, end=self.end_date)
        data.dropna(inplace=True)
        return data
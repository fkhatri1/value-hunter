import requests
import pandas as pd
import numpy as np
import pickle
from datetime import date, datetime, timedelta
from src.utils import get_config, Logger
from API import Profile, get_price_data, get_market_cap, get_earnings_events, get_profile

class Stock:
    def __init__(self, symbol):
        self.symbol = symbol
        self.price_data = get_price_data(symbol, str(date.today() - timedelta(days=60))) #2 months of history

        #get technicals
        Stock.get_rsi(self.price_data)
        Stock.get_stdev(self.price_data)

        #check for signal
        if self.find_signal():
            self.earnings = get_earnings_events(symbol)
            self.profile = get_profile(symbol)
            print(f"Found signal for {self.symbol}.")
            print(self.earnings)
            print(self.profile)
    
    def get_rsi(df, field='close', rsi_span=15):
        # RSI 3 weeks
        rsi_span = 15
        change = df[field].diff()
        up = change.clip(lower=0)
        down = -1 * change.clip(upper=0)
        ema_up = up.ewm(span=rsi_span, adjust=False).mean()
        ema_down = down.ewm(span=rsi_span, adjust=False).mean()
        rs = ema_up/ema_down
        rsi = 100 - (100/(1+rs))
        df[f'rsi'] = rsi.round(2)
        df[f'rsi_lag1'] = df[f'rsi'].shift(1)
        df[f'rsi_lag2'] = df[f'rsi'].shift(2)
         
    def get_stdev(df):
        boll_span = 15
        ema = df['close'].ewm(span=boll_span, adjust=False).mean().round(2)
        emstd = df['close'].ewm(span=boll_span, adjust=False).std().round(4)
        ema_diff = df['close'] - ema
        df['num_stdev'] = ema_diff / emstd
        df['num_stdev_lag1'] = df['num_stdev'].shift(1)
        df['num_stdev_lag2'] = df['num_stdev'].shift(2)

    def find_signal(self):
        rsi_threshold = 27
        last_day = self.price_data.iloc[-1]
        if (last_day['rsi'] > rsi_threshold and last_day['rsi_lag1'] < rsi_threshold and last_day['rsi_lag2'] < rsi_threshold):
            return True
        else:
            return False
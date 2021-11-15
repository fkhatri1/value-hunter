import requests
import pandas as pd
import numpy as np

from datetime import date, datetime, timedelta
from src.utils import get_config, Logger

class Stocks():
    def __init__(self):
        self.config = get_config()
        self.log = Logger()
        self.spy_data = Stocks.get_spy_data(self.config['signals']['rsi_span'])
        

    def get_spy_data(from_date='2010-01-01', rsi_span=13):
        return Stocks.get_data('SPY', from_date, str(date.today()))

    def get_next_market_day(_date):
        log = Logger()
        spy = Stocks.get_spy_data(from_date=_date)
        spy['date_lead'] = spy['date'].shift(-1)
        try:
            res = spy.loc[_date]['date_lead']
        except Exception as e:
            log.error(f"Invalid date. {_date} is not a market date.")
            return None
        return res

    def get_data(symbol, from_date, to_date, rsi_span=13):
        url = f"https://financialmodelingprep.com/api/v3"
        config = get_config()
        apikey = f"&apikey={config['credentials']['financialmodelingprep']}"

        log = Logger()
        log.info(f"Fetching updated data for {symbol} from {from_date} to {to_date}.")
        r = requests.get(f"{url}/historical-price-full/{symbol}?from={from_date}&to={to_date}{apikey}")
        r.json()
        df = pd.json_normalize(r.json())
        try:
            history = df['historical'].values[0]
            hist_df = pd.json_normalize(history)
            hist_df = hist_df.drop(['adjClose', 'change', 'unadjustedVolume', 'changePercent', 'vwap', 'label', 'changeOverTime'], axis=1)
            hist_df = hist_df.sort_values('date', ascending=True)
        except Exception as e:
            return None

        change = hist_df['close'].diff()
        up = change.clip(lower=0)
        down = -1 * change.clip(upper=0)
        ema_up = up.ewm(span=rsi_span, adjust=False).mean()
        ema_down = down.ewm(span=rsi_span, adjust=False).mean()
        rs = ema_up/ema_down
        rsi = 100 - (100/(1+rs))
        hist_df['rsi'] = rsi

        hist_df.set_index('date', drop=False, inplace=True)

        return hist_df.round(2)
        
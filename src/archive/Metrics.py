from API import API
from datetime import date, datetime, timedelta
from typing import List
import pandas as pd
import requests
from utils import get_config, get_credentials
import logging

class Metrics():
    def get_rsi(x:pd.Series, rsi_span):
        change = x.diff()
        up = change.clip(lower=0)
        down = -1 * change.clip(upper=0)
        ema_up = up.ewm(span=rsi_span, adjust=False).mean()
        ema_down = down.ewm(span=rsi_span, adjust=False).mean()
        rs = ema_up/ema_down
        rsi = 100 - (100/(1+rs))
        return rsi

    def normalize(x:pd.Series):
        return ( x - x.mean() ) / x.std()
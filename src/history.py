import requests
import pandas as pd
import pickle

from datetime import date, datetime, timedelta
from utils import get_config, Logger

def get_signals(symbol, earnings_date) -> None:
    config = get_config()
    log = Logger()
    
    from_date = str((pd.to_datetime(earnings_date) - timedelta(days=90)).date())
    to_date = str((pd.to_datetime(earnings_date) + timedelta(days=90)).date())

    log.info(f"Fetching updated data for {symbol} from {from_date} to {to_date}.")
    r = requests.get(f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={from_date}&to={to_date}&apikey={config['credentials']['financialmodelingprep']}")
    r.json()
    df = pd.json_normalize(r.json())
    history = df['historical'].values[0]
    hist_df = pd.json_normalize(history)
    hist_df = hist_df.drop(['adjClose', 'change', 'unadjustedVolume', 'changePercent', 'vwap', 'label', 'changeOverTime'], axis=1)
    hist_df = hist_df.sort_values('date', ascending=True)
    
    # BOLLINGER
    boll_span = int(config['signals']['bollinger_span'])
    ema = hist_df['close'].ewm(span=boll_span, adjust=False).mean().round(2)
    emstd = hist_df['close'].ewm(span=boll_span, adjust=False).std().round(4)
    boll_low = (ema - 2*emstd).round(2)
    boll_sig = hist_df['low'] < boll_low
    boll_sig_lag_1 = boll_sig.shift(1)
    boll_sig_lag_2 = boll_sig.shift(2)
    hist_df['boll'] = ~boll_sig & boll_sig_lag_1 & boll_sig_lag_2

    # RSI
    rsi_span = int(config['signals']['rsi_span'])
    change = hist_df['close'].diff()
    up = change.clip(lower=0)
    down = -1 * change.clip(upper=0)
    ema_up = up.ewm(span=rsi_span, adjust=False).mean()
    ema_down = down.ewm(span=rsi_span, adjust=False).mean()
    rs = ema_up/ema_down
    rsi = 100 - (100/(1+rs))


    # EMA
    ema_sig_span = int(config['signals']['ema_span'])
    ema_sig = hist_df['close'] < hist_df['close'].ewm(span=ema_sig_span, adjust=False).mean().round(2)
    ema_sig_lag_1 = ema_sig.shift(1)
    ema_sig_lag_2 = ema_sig.shift(2)
    hist_df['ema_sig'] = ~ema_sig & ema_sig_lag_1 & ema_sig_lag_2

    buy_signal = hist_df[hist_df['boll'] & hist_df['rsi_sig'] & hist_df['ema_sig']]
    log.info(f"Found {len(buy_signal)} buy signals for {symbol}: {buy_signal['date'].values}.")
    
    return buy_signal['date'].values
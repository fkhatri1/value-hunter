from API import API, Profile, Earnings
from Metrics import Metrics
from Screener import Screener
from Email import send_signal_email
import logging
import pandas as pd
import pickle

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.ERROR)
                    
symbols = Screener.screen()
signals = []

for idx, symbol in enumerate(symbols):
    try:
        d = API.get_historical_ohlc(symbol)
        d['rsi'] = Metrics.get_rsi(d['close'], 21)
        d = d[21:]
        d['norm_rsi'] = Metrics.normalize(d['rsi'])
        d['last_norm_rsi'] = d['norm_rsi'].shift(1)

        last_rsi = d[-1:].norm_rsi.values[0]
        last5 = d[-5:]
        last5_min_rsi = min(last5.norm_rsi.values)

        if last5_min_rsi <= -2.2 and last_rsi > -1.5:
            companyName = API.get_profile(symbol).companyName.lower()
            if "fund" in companyName or "trust" in companyName:
                continue
            earnings = API.get_earnings_events(symbol)
            if float(earnings[0].estimate) < 0 or float(earnings[0].actual) < 0:
                continue
            else:
                signals.append(symbol)
                logging.error(f"Buy {symbol} today, sell once 21-day RSI reaches 1.25 stds up: {int(d['rsi'].mean() + d['rsi'].std()*1.25)}")
    except Exception as e:
        pass

#get last 5 days of signals:
last5_signals = []
with open(f"../data/last_signals.pickle", 'rb') as f:
    for i in pickle.load(f):
        last5_signals.extend(i)

for symbol in [symbol for symbol in signals if symbol not in last5_signals]:
    send_signal_email(symbol, int(d['rsi'].mean() + d['rsi'].std()*1.25))

# update last 5 signals
last5_signals = [signals] + last5_signals[0:3]
with open(f"../data/last_signals.pickle", 'wb') as f:
    pickle.dump(last5_signals, f, protocol=pickle.HIGHEST_PROTOCOL)
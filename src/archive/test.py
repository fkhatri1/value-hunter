from API import API, Profile, Earnings
from Metrics import Metrics
from Screener import Screener
import logging
import pandas as pd
import pickle

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.ERROR)
                    
symbols = Screener.screen()

signals = pd.DataFrame({})

def get_return(x,y):
    return round(100 * (y - x) / x, 2)

for idx, symbol in enumerate(symbols):
    try:
        d = API.get_historical_ohlc(symbol)
        d['rsi'] = Metrics.get_rsi(d['open'], 21)
        d = d[21:]
        d['norm_rsi'] = Metrics.normalize(d['rsi'])
        d['last_norm_rsi'] = d['norm_rsi'].shift(1)

        for idx, r in d.iterrows():
            if r['last_norm_rsi'] < -2.5 and r['norm_rsi'] - r['last_norm_rsi'] > 0.5:
                # actual buy date is day of signal, assuming we run at open
                i = d.index.searchsorted(r.name)
                signal = {
                    "symbol":[symbol], 
                    "date":[r.name], 
                    "5-day":[get_return(d.iloc[i].close, d.iloc[i+5].close)],
                    "10-day":[get_return(d.iloc[i].close, d.iloc[i+10].close)],
                    "20-day":[get_return(d.iloc[i].close, d.iloc[i+20].close)],
                    "30-day":[get_return(d.iloc[i].close, d.iloc[i+30].close)],
                    "40-day":[get_return(d.iloc[i].close, d.iloc[i+40].close)],
                    "50-day":[get_return(d.iloc[i].close, d.iloc[i+50].close)],
                    "60-day":[get_return(d.iloc[i].close, d.iloc[i+60].close)],
                    "90-day":[get_return(d.iloc[i].close, d.iloc[i+90].close)]
                }
                print(f"{signal}")
                signals = signals.append(pd.DataFrame(signal), ignore_index=True)

    except Exception as e:
        pass

with open(f"signals_open_beta2_div_2.pd", 'wb') as f:
    pickle.dump(signals, f, protocol=pickle.HIGHEST_PROTOCOL)
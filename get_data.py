import requests
import pandas as pd
import numpy as np
import pickle

from datetime import date, datetime, timedelta
from src.utils import get_config, Logger

import src.Stock as Stock

config = get_config()
log = Logger()
url = f"https://financialmodelingprep.com/api/v3"
apikey = f"&apikey={config['credentials']['financialmodelingprep']}"

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

with open(f"{config['config']['data']}/screened_symbols.pickle", 'rb') as f:
    symbols = pickle.load(f)

model_data = pd.DataFrame(columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'symbol', 'led',
       'surprise', 'days_since_led', 'rsi', 'rsi_lag1', 'rsi_lag2',
       'num_stdev', 'num_stdev_lag1', 'num_stdev_lag2', '3wk_adj_return'])

Stock.Stock.get_spy_return()

for symbol in symbols:
    ees = Stock.Stock.get_earnings_events(symbol)
    for ee in ees[:499]:
        try:
            a = Stock.Stock.get_prices(ee)
            Stock.Stock.get_rsi(a, "low")
            Stock.Stock.get_rsi(a, "close")
            Stock.Stock.get_rsi(a, "high")
            Stock.Stock.get_rsi(a, "open")
            Stock.Stock.get_stdev(a)
            Stock.Stock.get_return(a)

            model_data = model_data.append(a)
        except Exception as e:
            log.warn(f"Could not get info for {symbol} earnings event:\n {ee}.")
            print(e)
            raise e
            #continue
    

    with open(f"data/model_data.pickle", 'wb') as f:
        pickle.dump(model_data, f, protocol=pickle.HIGHEST_PROTOCOL)

    log.info(f"Done with {symbol}")
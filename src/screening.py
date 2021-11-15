from datetime import date, datetime, timedelta
from typing import List

import pandas as pd
import requests

from utils import get_config, Logger



def screener() -> List[str]:
    config = get_config()
    log = Logger(config['config']['log'])

    #api call to financialmodelingprep stock screener 
    r = requests.get(f"https://financialmodelingprep.com/api/v3/stock-screener?marketCapMoreThan={config['screening']['min_market_cap']}&country=US&betaLowerThan={config['screening']['max_beta']}&volumeMoreThan={config['screening']['min_volume']}&dividendMoreThan={config['screening']['min_dividend']}&isEtf=false&isActivelyTrading=true&apikey={config['credentials']['financialmodelingprep']}")
    df = pd.json_normalize(r.json())

    #get raw symbol list
    pre_check_symbols = df['symbol'].values
    pre_check_symbols.sort()
    log.info(f'Prescreening has selected {len(pre_check_symbols)} candidate symbols.')
    symbols = []

    #use internal function to check dividend history
    for s in pre_check_symbols:
        if dividend_history_check(s):
            symbols.append(s)
            log.info(f"{s} passed the dividend history check.")
        else:
            log.info(f"{s} failed the dividend history check.")
        

    return symbols


def dividend_history_check(symbol: str) -> bool:
    return True

def _dividend_history_check(symbol: str) -> bool:
    config = get_config()
    r = requests.get(f"https://financialmodelingprep.com/api/v3/historical-price-full/stock_dividend/{symbol.upper()}?apikey={config['credentials']['financialmodelingprep']}")
    try:
        df1 = pd.json_normalize(r.json())
        data = df1['historical'].values[0] 
        df2 = pd.json_normalize(data)

        # filter to include only positive dividends
        df2 = df2[df2['dividend'] > 0]

        # filter to include only last 2 years
        two_year_hist_date = pd.to_datetime(date.today() - timedelta(weeks=104))
        df2['date'] = pd.to_datetime(df2['date'], format='%Y-%m-%d')
        dividend_two_year = df2[df2['date'] > two_year_hist_date]
        #print(dividend_two_year)
        if len(dividend_two_year) >= int(config['screening']['min_quarters_with_dividend']):
            return True
        else:
            return False

    except Exception as e:
        print("ERROR OCCURRED:")
        print(e)
        return False
        
def get_earnings_beats(symbols):
    config = get_config()
    log = Logger(config['config']['log'])

    earnings_data = {}

    for symbol in symbols:
        earnings_data[symbol] = {}

        config = get_config()
        r = requests.get(f"https://financialmodelingprep.com/api/v3/earnings-surprises/{symbol.upper()}?apikey={config['credentials']['financialmodelingprep']}")
        try:
            #earnings = pd.json_normalize(r.json()).sort_values("date", ascending=False)
            earnings = pd.json_normalize(r.json())
            log.info(f"Got {len(earnings)} earnings beats for {symbol}.")
            for i in range(0, len(earnings)):
                earnings_data[symbol][earnings.iloc[i].date] = ''

        except Exception as e:
            log.error(f"Cannot get earnings surprises data for {symbol}.")

    return earnings_data

from API import API
from datetime import date, datetime, timedelta
from typing import List
import pandas as pd
import requests
from utils import get_config, get_credentials
import logging

class Screener():
    def screen() -> List[str]:
        config = get_config()
        
        #api call to financialmodelingprep stock screener 
        url = f"https://financialmodelingprep.com/api/v3/stock-screener"
        params = {}
        params['country'] = 'US'
        params['marketCapMoreThan'] = config['screening']['min_market_cap']
        params['betaLowerThan'] = config['screening']['max_beta']
        params['volumeMoreThan'] = config['screening']['min_volume']
        params['dividendMoreThan'] = config['screening']['min_dividend']
        params['isEtf'] = False
        params['isActivelyTrading'] = True
        params['apikey'] = get_credentials()['financialmodelingprep']

        r = requests.get(url, params)
        df = pd.json_normalize(r.json())

        #get raw symbol list
        symbols = list(df['symbol'].values)
        symbols.sort()
        logging.info(f'Screening has selected {len(symbols)} candidate symbols.')

        return symbols
        

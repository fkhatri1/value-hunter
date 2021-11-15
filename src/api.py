from collections import namedtuple
import requests
import pandas as pd
import numpy as np
import pickle
import finnhub
from datetime import date, datetime, timedelta
from src.utils import get_config, Logger

Profile = namedtuple("Profile", ['companyName', 'beta', 'div_pct', 'industry', 'website', 'description', 'sector', 'ipoDate', 'mktCap', 'volAvg'])
Earnings = namedtuple("Earnings", ['date', 'estimate', 'actual', 'surprise'])

def get_price_data(symbol, start, end=str(date.today())):
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/"
    apikey = f"&apikey={get_config()['credentials']['financialmodelingprep']}"
    r = requests.get(f"{url}{symbol}?from={start}&to={end}{apikey}")
    df = pd.json_normalize(r.json())
    try:
        history = df['historical'].values[0]
        hist_df = pd.json_normalize(history)
        hist_df = hist_df.drop(['adjClose', 'change', 'unadjustedVolume', 'changePercent', 'vwap', 'label', 'changeOverTime'], axis=1)
        hist_df = hist_df.sort_values('date', ascending=True)
        #hist_df.set_index('date', drop=False, inplace=True)
    except Exception as e:
        #print(f"Failed to fetch data for {symbol} from {start} to {end}.")
        raise e

    return hist_df

def get_market_cap(symbol, _date=str(date.today())):
    url = f"https://financialmodelingprep.com/api/v3/historical-market-capitalization/"
    apikey = f"&apikey={get_config()['credentials']['financialmodelingprep']}"
    r = requests.get(f"{url}{symbol}?limit=1000{apikey}")
    df = pd.json_normalize(r.json())
    df = df[df['date'] == date]
    try:
        cap = int(df['marketCap'].values[0]) / 1000000000  
    except Exception as e:
        profile = get_profile(symbol)
        cap = profile.mktCap
    return cap

def get_earnings_events(symbol, num_hist=4):
    url = f"https://financialmodelingprep.com/api/v3/historical/earning_calendar/"
    apikey = f"&apikey={get_config()['credentials']['financialmodelingprep']}"
    r = requests.get(f"{url}{symbol}?limit={num_hist}{apikey}")
    df = pd.json_normalize(r.json())

    earnings_events = []
    for index, row in df.iterrows():
        try:
            #true_earnings_date, volume = Stock.get_true_earnings_date(symbol, row['date'])
            earnings_events.append(
                Earnings(
                    row['date'], 
                    row['eps'], 
                    row['epsEstimated'], 
                    (float(row['eps']) - float(row['epsEstimated'])) / float(row['epsEstimated'])
                )
            )
        except Exception as e:
            pass

    return earnings_events

def get_profile(symbol):
    url = "https://financialmodelingprep.com/api/v3/profile/"
    apikey=f"?apikey={get_config()['credentials']['financialmodelingprep']}"
    r = requests.get(f"{url}{symbol}{apikey}")
    _data=r.json()[0]
    return Profile( companyName = _data['companyName'],
                    sector = _data['sector'],
                    industry = _data['industry'],
                    description = _data['description'],
                    mktCap = _data['mktCap'], 
                    beta = _data['beta'],
                    div_pct = float(_data['lastDiv']) * 4 / float(_data['price']),
                    ipoDate = _data['ipoDate'],
                    website = _data['website'],
                    volAvg = _data['volAvg']
                    )

def get_next_earnings(symbol):
    today = date.today()
    next_year = today + timedelta(weeks=52)
    fhub = finnhub.Client(api_key=get_config()['credentials']['finnhub'])
    _data = fhub.earnings_calendar(_from=str(today), to=str(next_year), symbol=symbol)
    _e = _data['earningsCalendar']
    return Earnings(_e['date'], 
                    _e['epsActual'], 
                    _e['epsEstimate'], 
                    None)
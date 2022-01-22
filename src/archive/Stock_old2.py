import requests
import pandas as pd
import numpy as np
import pickle

from datetime import date, datetime, timedelta
from utils import get_config, Logger

config = get_config()
log = Logger('warn')
url = f"https://financialmodelingprep.com/api/v3"
apikey = f"&apikey={config['credentials']['financialmodelingprep']}"

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

class Stock():
    # def __init__(self, symbol):
    #     self.symbol = symbol
    def get_spy_return():
        from_date = "2005-01-01"
        to_date = "2022-09-30"
        log.info(f"Fetching updated data for SPY from {from_date} to {to_date}.")
        r = requests.get(f"{url}/historical-price-full/SPY?from={from_date}&to={to_date}{apikey}")
        r.json()
        df = pd.json_normalize(r.json())


        history = df['historical'].values[0]
        hist_df = pd.json_normalize(history)
        hist_df = hist_df.drop(['adjClose', 'change', 'unadjustedVolume', 'changePercent', 'vwap', 'label', 'changeOverTime'], axis=1)
        hist_df = hist_df.sort_values('date', ascending=True)
        #hist_df.set_index('date', drop=False, inplace=True)

        close_4wk = hist_df['close'].shift(-20)
        hist_df['4wk_return'] = 100 * (close_4wk - hist_df['close']) / hist_df['close']

        close_3wk = hist_df['close'].shift(-15)
        hist_df['3wk_return'] = 100 * (close_3wk - hist_df['close']) / hist_df['close']

        close_2wk = hist_df['close'].shift(-10)
        hist_df['2wk_return'] = 100 * (close_2wk - hist_df['close']) / hist_df['close']

        close_1wk = hist_df['close'].shift(-5)
        hist_df['1wk_return'] = 100 * (close_1wk - hist_df['close']) / hist_df['close']

        spy_dict = {}
        for idx, row in hist_df.iterrows():
            spy_dict[row['date']] = {"1k_return": row['1wk_return'], 
                                    "2k_return": row['2wk_return'], 
                                    "3k_return": row['3wk_return'], 
                                    "4k_return": row['4wk_return'] }
            
        with open(f"data/spy_returns.pickle", 'wb') as f:
            pickle.dump(spy_dict, f, protocol=pickle.HIGHEST_PROTOCOL)

    def increment_date(_date, increment):
        try:
            inc_date = (pd.to_datetime(_date) + timedelta(days=increment)).date()
            return str(inc_date)
        except Exception:
            return -1

    def get_volume(symbol, _date):
        try:
            r = requests.get(f"{url}/historical-price-full/{symbol}?from={_date}&to={_date}{apikey}")
            df = pd.json_normalize(r.json())
            history = df['historical'].values[0]
            hist_df = pd.json_normalize(history)
            return int(hist_df['volume'].values[0])
        except Exception:
            return -1

    def get_true_earnings_date(symbol, _date):
        day_zero_volume = Stock.get_volume(symbol, _date)
        increment = 0
        day_one_volume = -1

        while (day_one_volume == -1 and increment < 10):
            increment = increment + 1
            day_one = Stock.increment_date(_date, increment)
            day_one_volume = Stock.get_volume(symbol, day_one)

        if increment == 10:
            return -1

        log.info(f"zero vol: {day_zero_volume}   one vol: {day_one_volume}  {day_one_volume > day_zero_volume}")
        if day_one_volume > day_zero_volume:
            log.info(f"Earnings after market detected - {symbol} on {_date}. True date: {day_one}")
            return (day_one, day_one_volume)
        else:
            log.info(f"Earnings before market detected - {symbol} on {_date}.")
            return (_date, day_zero_volume)


    def get_earnings_events(symbol):
        r = requests.get(f"{url}/historical/earning_calendar/{symbol}?limit=40{apikey}")
        df = pd.json_normalize(r.json())

        earnings_events = []
        for index, row in df.iterrows():
#            if (float(row['eps']) / float(row['epsEstimated'])) >= float(config['signals']['earnings_threshold']):
            try:
                true_earnings_date, volume = Stock.get_true_earnings_date(symbol, row['date'])
                earnings_events.append({
                    'symbol': symbol,
                    'date': true_earnings_date,
                    'volume': volume,
                    'eps': row['eps'],
                    'estimated': row['epsEstimated'],
                    'surprise': (float(row['eps']) - float(row['epsEstimated'])) / float(row['epsEstimated'])
                })
            except Exception as e:
                pass

        return earnings_events

    def get_prices(ee):
        from_date = str((pd.to_datetime(ee['date']) - timedelta(days=45)).date())
        to_date = str((pd.to_datetime(ee['date']) + timedelta(days=90)).date())
        log.info(f"Fetching updated data for {ee['symbol']} from {from_date} to {to_date}.")
        r = requests.get(f"{url}/historical-price-full/{ee['symbol']}?from={from_date}&to={to_date}{apikey}")
        r.json()
        df = pd.json_normalize(r.json())
        try:
            history = df['historical'].values[0]
            hist_df = pd.json_normalize(history)
            hist_df = hist_df.drop(['adjClose', 'change', 'unadjustedVolume', 'changePercent', 'vwap', 'label', 'changeOverTime'], axis=1)
            hist_df = hist_df.sort_values('date', ascending=True)
            #hist_df.set_index('date', drop=False, inplace=True)
            
            # fill in ee data
            hist_df['symbol'] = ee['symbol']
            hist_df['led'] = ee['date']
            hist_df['surprise'] = ee['surprise']
            hist_df['volume'] = hist_df['volume'] / ee['volume']

            hist_df['days_since_led'] = [int(str(pd.to_datetime(x) - pd.to_datetime(ee['date'])).split(" ")[0]) for x in hist_df['date'].values]

        except Exception as e:
            log.error(f"Failed to fetch data for {ee['symbol']} from {ee['date']} to {to_date}.")
            raise e

        return hist_df

    def get_market_cap(symbol, date):
        r = requests.get(f"https://financialmodelingprep.com/api/v3/historical-market-capitalization/{symbol}?limit=1000&apikey={config['credentials']['financialmodelingprep']}")
        r.json()
        df = pd.json_normalize(r.json())
        df = df[df['date'] == date]
        try:
            cap = int(df['marketCap'].values[0]) / 1000000000  
        except Exception as e:
            cap = None
            
        return cap

    def get_rsi(df, field):
        # RSI 3 weeks
        rsi_span = 15
        change = df[field].diff()
        up = change.clip(lower=0)
        down = -1 * change.clip(upper=0)
        ema_up = up.ewm(span=rsi_span, adjust=False).mean()
        ema_down = down.ewm(span=rsi_span, adjust=False).mean()
        rs = ema_up/ema_down
        rsi = 100 - (100/(1+rs))
        df[f'rsi_{field}'] = rsi
        df[f'rsi_{field}_lag1'] = df[f'rsi_{field}'].shift(1)
        df[f'rsi_{field}_lag2'] = df[f'rsi_{field}'].shift(2)
         
    def get_stdev(df):
        boll_span = 15
        ema = df['close'].ewm(span=boll_span, adjust=False).mean().round(2)
        emstd = df['close'].ewm(span=boll_span, adjust=False).std().round(4)
        ema_diff = df['close'] - ema
        df['num_stdev'] = ema_diff / emstd
        df['num_stdev_lag1'] = df['num_stdev'].shift(1)
        df['num_stdev_lag2'] = df['num_stdev'].shift(2)

    def get_return(df):
        with open(f"data/spy_returns.pickle", 'rb') as f:
            spy = pickle.load(f)
        spy_return = [spy[x] for x in df['date'].values]

        # need to refactor to use the dict of diffrrtn returns.

        close_4wk = df['close'].shift(-20)
        close_3wk = df['close'].shift(-15)
        close_2wk = df['close'].shift(-10)
        close_1wk = df['close'].shift(-5)

        df['4wk_adj_return'] = (100 * (close_4wk - df['close']) / df['close']) - spy_return['4wk_return']
        df['3wk_adj_return'] = (100 * (close_3wk - df['close']) / df['close']) - spy_return['3wk_return']
        df['2wk_adj_return'] = (100 * (close_2wk - df['close']) / df['close']) - spy_return['2wk_return']
        df['1wk_adj_return'] = (100 * (close_1wk - df['close']) / df['close']) - spy_return['1wk_return']


    

    def get_data(symbol, from_date, to_date):

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


        
        # BOLLINGER
        boll_span = int(config['signals']['bollinger_span'])
        ema = hist_df['close'].ewm(span=boll_span, adjust=False).mean().round(2)
        emstd = hist_df['close'].ewm(span=boll_span, adjust=False).std().round(4)
        hist_df['boll_low'] = (ema - 2*emstd).round(2)

        # RSI
        rsi_span = int(config['signals']['rsi_span'])
        change = hist_df['close'].diff()
        up = change.clip(lower=0)
        down = -1 * change.clip(upper=0)
        ema_up = up.ewm(span=rsi_span, adjust=False).mean()
        ema_down = down.ewm(span=rsi_span, adjust=False).mean()
        rs = ema_up/ema_down
        rsi = 100 - (100/(1+rs))
        hist_df['rsi'] = rsi

        # EMA
        ema_span = int(config['signals']['ema_span'])
        ema = hist_df['close'].ewm(span=ema_span, adjust=False).mean().round(2)
        hist_df['ema'] = ema
      
        return hist_df.round(2)

    def get_signals(symbol, earnings_date):
        from_date = str((pd.to_datetime(earnings_date) - timedelta(days=60)).date())
        to_date = str((pd.to_datetime(earnings_date) + timedelta(days=90)).date())

        df = Stock.get_data(symbol, from_date, to_date)
        if df is None:
            return []

        signal_dates = []

        #BOLLINGER BAND
        #Looking for 2 consecutive days of the LOW breaching the lower boll band, and then 2 days CLOSING above
        boll_low_breach = df['low'] < df['boll_low']
        boll_close_above = df['close'] > df['boll_low']

        boll_low_breach_lag3 = boll_low_breach.shift(3).replace(np.NaN, False)
        boll_low_breach_lag2 = boll_low_breach.shift(2).replace(np.NaN, False)
        boll_close_above_lag1 = boll_close_above.shift(1).replace(np.NaN, False)
        
        df['boll_sig'] = boll_close_above & boll_close_above_lag1 & boll_low_breach_lag2 & boll_low_breach_lag3

        #RSI
        #Looking for 1 day of breaching the RSI threshold, and then 2 days closing above
        rsi_breach = df['rsi'] < int(config['signals']['rsi_threshold'])
        rsi_breach_lag1 = rsi_breach.shift(1).replace(np.NaN, False)
        rsi_breach_lag2 = rsi_breach.shift(2).replace(np.NaN, False)
        df['rsi_sig'] = ~rsi_breach & ~rsi_breach_lag1 & rsi_breach_lag2

        #EMA
        #Looking for 1 day of the LOW breaching the EMA, and then 2 days CLOSING above
        ema_span = int(config['signals']['ema_span'])
        ema = df['close'].ewm(span=ema_span, adjust=False).mean().round(2)
        ema_low_breach = df['low'] < ema
        ema_low_breach_lag2 = ema_low_breach.shift(2)

        ema_close_above = df['close'] > ema
        ema_close_above_lag1 = ema_close_above.shift(1)
        df['ema_sig'] = ema_close_above & ema_close_above_lag1 & ema_low_breach_lag2

        #Filter to where all 3 signals are True
        signal_df = df[df['boll_sig'] & df['rsi_sig'] & df['ema_sig']]

        #Filter to dates after the earnings date
        signal_df = signal_df[signal_df['date'] > earnings_date]

        #Filter to dates at least 28 days earlier than today
        #signal_df = signal_df[(pd.to_datetime(signal_df['date']) - timedelta(days=28)) < date.today() ]

        return signal_df['date'].values

    def get_open_price(symbol, date):
        from_date = date #str((pd.to_datetime(date) - timedelta(days=1)).date())
        to_date = str((pd.to_datetime(date) + timedelta(days=5)).date())
        
        r = requests.get(f"{url}/historical-price-full/{symbol}?from={from_date}&to={to_date}{apikey}")
        r.json()
        df = pd.json_normalize(r.json())
        try:
            history = df['historical'].values[0]
            hist_df = pd.json_normalize(history)
            hist_df = hist_df.sort_values('date', ascending=True)
            return hist_df['open'].values[0].round(2)
        except Exception as e:
            return None

    def evaluate_signal(symbol, signal_date):
        log.info(f"Evaluating signal date {signal_date} for {symbol} relative to SPY.")
        # Buy at open on day after signal is identified
        buy_date = str((pd.to_datetime(signal_date) + timedelta(days=1)).date())
        
        try:
            spy_entry = Stock.get_open_price('SPY', buy_date).round(2)
            entry_price = Stock.get_open_price(symbol, buy_date).round(2)
        except Exception as e:
            return {
            'gain_7': None,
            'gain_14': None,
            'gain_21': None,
            'gain_28': None
            }
        #log.info(f"{symbol} entry price on {buy_date}: {entry_price}  |  SPY price: {spy_entry}")
        
        def get_gain(hold_days):
            sell_date = str((pd.to_datetime(signal_date) + timedelta(days=hold_days)).date())
            spy_exit = Stock.get_open_price('SPY', sell_date)
            if spy_exit is None:
                return None
            spy_exit = spy_exit.round(2)

            #log.info(f"SPY exit on {sell_date}: {spy_exit}.")
            spy_gain = ((spy_exit - spy_entry) / spy_entry).round(4)*100
            exit_price = Stock.get_open_price(symbol, sell_date)
            if exit_price is None:
                return None
            exit_price = exit_price.round(2)
            #log.info(f"{symbol} exit on {sell_date}: {exit_price}.")
            signal_gain = ((exit_price - entry_price) / entry_price).round(4)*100
            return (signal_gain - spy_gain).round(2)
        
        signal_perf = {
            'gain_7': get_gain(7),
            'gain_14': get_gain(14),
            'gain_21': get_gain(21),
            'gain_28': get_gain(28)
        }
        
        return signal_perf

    
# sig = Stock.get_signals("COST", '2021-03-01')
# print(Stock.evaluate_signal("COST", sig[0]))
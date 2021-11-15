import pickle
from time import sleep
from screening import screener, get_earnings_beats
from history import get_signals
from utils import Logger, get_config
from Stock_old import *


config = get_config()
log = Logger(config['config']['log'])

def _print_actions() -> None:
    print("""
    STOCKS PROGRAM ACTIONS
    	1. Refresh screened stocks list
        2. Refresh price and technicals data
        3. Refresh earnings surprises
        4. Refresh signals
        5. View buy signals
        6. Enter new position
        7. View current positions
       -1. Exit
    """)
    print("""
    Enter action: """, end='')


task = 0
while task != -1:
    _print_actions()
    task = input()
    try:
        task = int(task)
    except Exception as e:
        log.error('Invalid input.')
        sleep(2)
        continue 

    if task == 1:
        log.info('Beginning screening operation')
        symbols = screener()
        log.info(f'Screening process has selected {len(symbols)} symbols. Saving to pickle.')
        with open(f"{config['config']['data']}/screened_symbols_2.pickle", 'wb') as f:
            pickle.dump(symbols, f, protocol=pickle.HIGHEST_PROTOCOL)
        log.info(f'Screened symbols saved to pickle file.')

    elif task == 2:
        with open(f"{config['config']['data']}/screened_symbols.pickle", 'rb') as f:
            symbols = pickle.load(f)
        signals = []

        for symbol in symbols:
            log.info(f"Getting earnings events for {symbol} and searching for signals.")
            earnings_events = Stock.get_earnings_events(symbol)
            for e in earnings_events:
                _signals = Stock.get_signals(symbol, e['date'])
                for s in _signals:
                    perf = Stock.evaluate_signal(symbol, s)
                    _signal_data = dict({
                        'symbol': symbol,
                        'earnings_date': e['date'],
                        'eps': e['eps'],
                        'estimated': e['estimated'],
                        'surprise': e['surprise'],
                        'signal_date': s
                    })
                    _signal_data.update(perf)
                    signals.append(_signal_data)

        with open(f"{config['config']['data']}/signal_analysis.pickle", 'wb') as f:
            pickle.dump(signals, f, protocol=pickle.HIGHEST_PROTOCOL)

        # Evaluating signal date 2021-08-16 for CCMP relative to SPY.
        
    elif task == 3:
        with open(f"{config['config']['data']}/screened_symbols.pickle", 'rb') as f:
            symbols = pickle.load(f)
        
        


    elif task == 4:
        with open(f"{config['config']['data']}/earnings_info.pickle", 'rb') as f:
            earnings_data = pickle.load(f)

        for symbol, earnings_dates in earnings_data.items():
            for earnings_date in earnings_dates.keys():
                earnings_dates[earnings_date] = get_signals(symbol, earnings_date)

        with open(f"{config['config']['data']}/signals.pickle", 'wb') as f:
            pickle.dump(earnings_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        log.info(f'Signals saved to pickle file.')
        

    elif task == -1:
        log.info('Exiting program')
    else:
        log.error('Invalid input.')
        sleep(2)





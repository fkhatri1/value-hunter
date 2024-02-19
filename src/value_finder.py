#!/usr/bin/python3

from multiprocessing import Process
from typing import List
from OutsideWorld.Investing import Stock
import pandas as pd
import pickle
import datetime
import logging
import sys
import pandas as pd
from OutsideWorld.Investing import Stock

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# handler = logging.StreamHandler(sys.stdout)
# handler.setLevel(logging.INFO)
# formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# handler.setFormatter(formatter)
# logger.addHandler(handler)


START_DATE = "2022-01-01"

def get_symbols():
    from OutsideWorld.Investing.Screener import Screener, ScreeningCriteria, ScreeningResult

    screener = Screener()
    criteria: ScreeningCriteria = ScreeningCriteria(
        country = "US",
        min_market_cap = 5_000_000_000,
        min_volume = None,
        min_dividend = None,
        max_beta = None,
        is_etf = False,
        is_actively_trading = True
    )

    symbols: ScreeningResult = screener.screen(criteria=criteria)

    screened_symbols = [s.symbol for s in symbols]
    screened_symbols = [s.split(".")[0] for s in screened_symbols]
    screened_symbols = [s for s in screened_symbols if len(s) < 5 and "0" not in s]
    screened_symbols = list(set(screened_symbols))

    # filter against known reject list
    with open("../data/rejects.pickle", "rb") as f:
        rejects = pickle.load(f)

    res = [s for s in screened_symbols if s not in rejects]
    
    return res

def find_matches(symbols):
    matches = []
    from fetch_data import fetch_data
    import numpy as np

    start_dt = datetime.datetime.today() - datetime.timedelta(weeks=78)

    for s in symbols:
        try:
            df = fetch_data(s, start_dt.isoformat()[0:10])
            
            col = "ratio_pe"
            df["stdevs"] = (df[col] - np.mean(df[col])) / np.std(df[col])

            # persist
            with open(f"../data/dfs/{s}.pickle", "wb") as f:
                pickle.dump(df, f, protocol=pickle.HIGHEST_PROTOCOL)

            test_day = df.iloc[-1]
        except Exception as e:
            continue

        if  test_day["atoi_lag_1"] > 0 and \
            test_day["atoi"] > 0 and \
            test_day["atoi_qoq_growth"] > -0.05 and \
            test_day["owners_earnings_lag_1"] > 0 and \
            test_day["owners_earnings"] > 0 and \
            test_day["owners_earnings_qoq_growth"] > 0.11 and \
            test_day["owners_earnings_qoq_growth_lag_1"] > -0.11 and \
            test_day["net_margin"] > 0.05 and \
            test_day["net_margin_growth"] > 0 and \
            test_day["net_margin_growth_lag_1"] > 0 and \
            test_day["roic"] > 0.15 and \
            test_day["totalStockholdersEquity"] > 0 and \
            test_day["ratio_peg"] < 1 and \
            test_day["stdevs"] < -1.25:
            
            # match found
            logger.info(f"Found a match: {s}")
            matches.append(s)

    return matches

def filter_existing_matches(matches):
    with open("../data/existing_matches.pickle", "rb") as f:
        existing_matches = pickle.load(f)

    today = datetime.datetime.today()

    # drop old matches >30 days old
    if len(existing_matches) > 0:
        recent_matches = [m for m in existing_matches if today - m[1] < datetime.timedelta(days=30)]
    else:
        recent_matches = []

    today_matches = [(s, today) for s in matches if s not in [m[0] for m in recent_matches]]

    # refresh existing matches
    all_matches = recent_matches + today_matches
    with open("../data/existing_matches.pickle", "wb") as f:
        pickle.dump(all_matches, f)

    return today_matches, recent_matches 

def main():
    symbols = get_symbols()

    raw_matches = find_matches(symbols)

    today_matches, recent_matches = filter_existing_matches(raw_matches)

    logger.info(f"Found {len(today_matches)} new matches: {today_matches}.")
    logger.info(f"{len(recent_matches)} matches in last 30 days: {recent_matches}")

if __name__ == "__main__":
    main()

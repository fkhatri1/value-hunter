#!/usr/bin/python3

from multiprocessing import Process
from typing import List
from OutsideWorld.Finance import Stock
import pandas as pd
import awswrangler as wr


import logging
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


START_DATE = "2019-01-01"
DATA_PATH = "/home/ubuntu/data/stocks"

def get_symbols() -> List[str]:
    # S&P 500
    df = wr.s3.read_csv("s3://faysal/stocks/symbols/sp500.csv")
    symbols = list(df["Symbol"].values)
    # S&P 400 MidCaps
    df = wr.s3.read_csv("s3://faysal/stocks/symbols/sp400.csv")
    symbols.extend(df["Symbol"].values)
    # S&P 600 SmallCaps
    df = wr.s3.read_csv("s3://faysal/stocks/symbols/sp600.csv")
    symbols.extend(df["Symbol"].values)

    return symbols


def fetch_prices(symbols: List[str]) -> None:
    """Fetches ohlc data and stores in S3"""
    stock = Stock.Stock()

    for i, s in enumerate(symbols):
        logger.info(f"Fetching prices for {s}. {i} of {len(symbols)}")
        s = s.upper()

        try:
            loaded_prices = pd.read_csv(f"{DATA_PATH}/prices/{s}.csv").set_index(["date"])
            s_start = loaded_prices.index.min()
            s_end = loaded_prices.index.max()

            early_backfill = stock.get_historical_ohlc(s, start=START_DATE, end=s_start)
            latest_rows = stock.get_historical_ohlc(s, start=s_end)

            prices = pd.concat(
                [early_backfill, loaded_prices, latest_rows]
            ).drop_duplicates()
        except FileNotFoundError:
            prices = stock.get_historical_ohlc(s, START_DATE)

        prices.to_csv(f"{DATA_PATH}/prices/{s}.csv", index=True)

def fetch_cash_flow_statements(symbols: List[str]) -> None:
    """Fetches cf statements and stores locally"""
    stock = Stock.Stock()    
    for i, s in enumerate(symbols):
        logger.info(f"Fetching Cash Flow for {s}. {i} of {len(symbols)}")
        s = s.upper()
        try:
            cf = stock.get_historical_cash_flow_statement(s)
        except Stock.NoDataException:
            continue

        filtered = cf[cf["calendarYear"] > START_DATE[0:4]].sort_index()

        filtered.to_csv(f"{DATA_PATH}/cash_flow/{s}.csv", index=True)

def fetch_balance_sheet_statements(symbols: List[str]) -> None:
    """Fetches balance sheet statements and stores locally"""
    stock = Stock.Stock()
    for i, s in enumerate(symbols):
        logger.info(f"Fetching Balance Sheet for {s}. {i} of {len(symbols)}")
        try:
            s = s.upper()
            cf = stock.get_historical_balance_sheet_statement(s)
        except Stock.NoDataException:
            continue

        filtered = cf[cf["calendarYear"] > START_DATE[0:4]].sort_index()

        filtered.to_csv(f"{DATA_PATH}/balance_sheet/{s}.csv", index=True)

def main():
    symbols = get_symbols()
    logger.info(f"Got {len(symbols)} symbols.")

    fetch_funcs = [fetch_prices, fetch_cash_flow_statements, fetch_balance_sheet_statements]

    # instantiating process with arguments
    procs = []
    for f in fetch_funcs:
        proc = Process(target=f, args=(symbols,))
        procs.append(proc)
        proc.start()

    # complete the processes
    for proc in procs:
        proc.join()


if __name__ == "__main__":
    main()

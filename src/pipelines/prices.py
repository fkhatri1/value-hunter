#!/usr/bin/python3

from multiprocessing import Process
from typing import List
from OutsideWorld.Finance import Stock
import pandas as pd
import awswrangler as wr


import logging
import sys
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


START_DATE = "2005-01-01"
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
    # ADRs
    df = wr.s3.read_csv("s3://faysal/stocks/symbols/ADRs.csv")
    df = df[df.Country == "United States"]
    symbols.extend(df["Symbol"].values)

    return [s.upper() for s in symbols if isinstance(s, str)]




def main():
    symbols = get_symbols()
    logger.info(f"Got {len(symbols)} symbols.")

    fetch_funcs = [
        fetch_prices,
        fetch_cash_flow_statements,
        fetch_balance_sheet_statements,
        fetch_income_statements,
        fetch_market_cap,
    ]

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

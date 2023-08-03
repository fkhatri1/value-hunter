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


START_DATE = "2016-01-01"


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

    price_path = "s3://faysal/stocks/prices"
    for i, s in enumerate(symbols):
        logger.info(f"Fetching prices for {s}. {i} of {len(symbols)}")
        s = s.upper()

        try:
            loaded_prices = wr.s3.read_csv(f"{price_path}/{s}.csv").set_index(["date"])
            s_start = loaded_prices.index.min()
            s_end = loaded_prices.index.max()

            early_backfill = stock.get_historical_ohlc(s, start=START_DATE, end=s_start)
            latest_rows = stock.get_historical_ohlc(s, start=s_end)

            prices = pd.concat(
                [early_backfill, loaded_prices, latest_rows]
            ).drop_duplicates()
            wr.s3.delete_objects(f"{price_path}/{s}.csv")
        except wr.exceptions.NoFilesFound:
            prices = stock.get_historical_ohlc(s, START_DATE)

        wr.s3.to_csv(prices, f"{price_path}/{s}.csv", index=True)


def main():
    symbols = get_symbols()
    logger.info(f"Got {len(symbols)} symbols.")
    fetch_prices(symbols)


if __name__ == "__main__":
    main()

from typing import List
import pandas as pd
import awswrangler as wr


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

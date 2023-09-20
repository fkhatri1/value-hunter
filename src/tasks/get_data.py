from multiprocessing import Process
from typing import List
from OutsideWorld.Finance import Stock
import pandas as pd
import awswrangler as wr
import time
import datetime 

class DataUnavailableException(Exception):
    pass

# prices: all 
CASH_FLOW_COLS = ["symbol", "reportedCurrency" ,"freeCashFlow" ,"capitalExpenditure" ,"debtRepayment" ,"commonStockRepurchased", "dividendsPaid"]
INCOME_COLS = ["symbol", "revenue", "costOfRevenue", "ebitda" ,"netIncome" ,"eps"]
BALANCE_SHEET_COLS = ["symbol",  "cashAndCashEquivalents" ,"totalAssets" ,"goodwillAndIntangibleAssets" ,"totalLiabilities" , "retainedEarnings"]
# market_cap: all

def normalize_dates(dts: List[datetime.datetime]):
    normal_dts = []
    for d in dts:
        if d.month in (3, 4):
            normal_dts.append(datetime.date(year=d.year, month=3, day=31))
        elif d.month in (6, 7):
            normal_dts.append(datetime.date(year=d.year, month=6, day=30))
        elif d.month in (9, 10):
            normal_dts.append(datetime.date(year=d.year, month=9, day=30))
        elif d.month == 12:
            normal_dts.append(datetime.date(year=d.year, month=12, day=31))
        elif d.month == 1:
            normal_dts.append(datetime.date(year=d.year-1, month=12, day=31))
        else:
            raise ValueError(f"Cannot interpret date: {d}")

    return pd.to_datetime(normal_dts)

def fetch_data(s: str, start_date: str) -> None:
    true_start_date = pd.to_datetime(start_date)
    start_date = true_start_date - datetime.timedelta(days=93)

    stock = Stock.Stock()
    try:
        # prices
        prices = stock.get_historical_ohlc(s, start_date)

        # cash flow
        cf = stock.get_historical_cash_flow_statement(s)
        f = cf.index.to_series().between(start_date, datetime.datetime.now())
        cf = cf[f][CASH_FLOW_COLS]
        cf.index = normalize_dates(cf.index)
        cf.sort_index(inplace=True)

        # balance sheet
        bal = stock.get_historical_balance_sheet_statement(s)
        f = bal.index.to_series().between(start_date, datetime.datetime.now())
        bal = bal[f][BALANCE_SHEET_COLS]
        bal.index = normalize_dates(bal.index)
        bal.sort_index(inplace=True)

        # income statement
        income = stock.get_historical_income_statement(s)
        f = income.index.to_series().between(start_date, datetime.datetime.now())
        income = income[f][INCOME_COLS]
        income.index = normalize_dates(income.index)
        income.sort_index(inplace=True)

        # market cap
        mc = stock.get_historical_market_cap(s)
        f = mc.index.to_series().between(start_date, datetime.datetime.now())

        # merge
        df = prices.join(mc, lsuffix="", rsuffix="r")

        df1 = pd.merge_asof(df, bal, left_index=True, right_index=True, suffixes=["","_reported"])
        df2 = pd.merge_asof(df1, cf, left_index=True, right_index=True, suffixes=["","_reported"])
        df3 = pd.merge_asof(df2, income, left_index=True, right_index=True, suffixes=["","_reported"])

        return df3.loc[true_start_date:]

    except Exception as e:
        raise DataUnavailableException(e)



from OutsideWorld.Investing import Stock
import pandas as pd

def fetch_data(s, start_date):
    stock = Stock.Stock()

    mc = stock.get_historical_market_cap(s, start_date=start_date)
    cf = stock.get_historical_cash_flow_statement(s, start_date=start_date)
    bal = stock.get_historical_balance_sheet_statement(s, start_date=start_date)
    income = stock.get_historical_income_statement(s, start_date=start_date).drop(["depreciationAndAmortization"], axis=1)

    df = pd.merge_asof(mc, cf, left_index=True, right_index=True)
    df = pd.merge_asof(df, bal, left_index=True, right_index=True)
    df = pd.merge_asof(df, income, left_index=True, right_index=True)

    def floor_zero(x):
        return max(0, x)

    # derived metrics
    df["enterpriseValue"] = df["marketCap"] + df["netDebt"]
    df["cash"] = df["totalDebt"] - df["netDebt"]
    df["gross_margin"] = df["grossProfit"] / df["revenue"]
    df["oe_margin"] = df["owners_earnings"] / df["revenue"]
    df["fcf_margin"] = df["freeCashFlow"] / df["revenue"]
    df["reinvestment_rate"] = df["reinvestment"] / df["atoi"]
    df["current_investments"] = df["totalCurrentLiabilities"] - df["totalCurrentAssets"] + df["cashAndShortTermInvestments"]
    df["current_investments"] = df["current_investments"].apply(floor_zero)
    df["invested_capital"] = df["totalAssets"]- df["accountPayables"] - df["taxPayables"] - df["cashAndCashEquivalents"] + df["current_investments"]
    df["roic"] = df["atoi"] / df["invested_capital"]

    # net margin growth
    df["net_margin"] = df["netIncome"] / df["revenue"]
    df["net_margin_lag_1"] = df["net_income_lag_1"] / df["revenue_lag_1"]
    df["net_margin_lag_2"] = df["net_income_lag_2"] / df["revenue_lag_2"]
    df["net_margin_growth"] =  (df["net_margin"] - df["net_margin_lag_1"])/ df["net_margin_lag_1"]
    df["net_margin_growth_lag_1"] =   (df["net_margin_lag_1"] - df["net_margin_lag_2"])/ df["net_margin_lag_2"]

    # ratios
    df["ratio_netDebt_to_ebitda"] = df["netDebt"] / df["ebitda"]
    df["ratio_ev_to_ebitda"] = df["enterpriseValue"] / df["ebitda"]
    df["ratio_ps"] = df["marketCap"] / df["revenue"]
    df["ratio_pe"] = df["marketCap"] / df["netIncome"]
    df["ratio_peg"] = df["ratio_pe"] / df["eps_growth_annual"]
    df["ratio_poe"] = df["marketCap"] / df["owners_earnings"]
    df["ratio_pfcf"] = df["marketCap"] / df["freeCashFlow"]
    df["ratio_payout"] = -1* (df["dividendsPaid"]) / df["freeCashFlow"]
    df["ratio_total_return"] = -1* (df["dividendsPaid"] + df["commonStockRepurchased"]) / df["freeCashFlow"]
    df["ratio_current"] = df["totalCurrentAssets"] / df["totalCurrentLiabilities"]
    df["ratio_de"] = df["totalDebt"] / df["totalStockholdersEquity"]
    
    return df
    
    
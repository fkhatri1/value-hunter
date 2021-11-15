import src.Stock as s
import pickle

symbols = None

with open(f"data/screened_symbols_2.pickle", 'rb') as f:
    symbols = pickle.load(f)

for idx, symbol in enumerate(symbols):
    #print(f"{idx}/{len(symbols)}")
    try:
        company = s.Stock(symbol)
    except Exception as e:
        print(f"Bad symbol {symbol} at {idx}/{len(symbols)}")
        continue
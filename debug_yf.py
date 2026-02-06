import yfinance as yf

symbol = "ZOMATO.NS"
print(f"Downloading {symbol}...")
try:
    data = yf.download(symbol, period="1y", progress=False)
    print(f"Rows: {len(data)}")
    if not data.empty:
        print(data.tail())
    else:
        print("Empty DataFrame returned.")
except Exception as e:
    print(f"Error: {e}")

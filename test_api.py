import requests
import sys

symbol = "ZOMATO"
if len(sys.argv) > 1:
    symbol = sys.argv[1]

print(f"Testing API for {symbol}...")
try:
    url = f"http://localhost:8001/analyze/{symbol}"
    print(f"GET {url}")
    res = requests.get(url, timeout=60)
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        import json
        print("Response:", json.dumps(res.json(), indent=2, ensure_ascii=True))
    else:
        print("Error:", res.text)
except Exception as e:
    print(f"Connection Failed: {e}")

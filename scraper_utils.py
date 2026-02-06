
import requests
from bs4 import BeautifulSoup
import time
import random

def get_google_finance_price(ticker, retries=3):
    """
    Scrapes the live price from Google Finance.
    Retries multiple times to ensure data is fetched.
    Returns float or None.
    """
    for attempt in range(retries):
        try:
            url = f"https://www.google.com/finance/quote/{ticker}:NSE"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache"
            }
            resp = requests.get(url, headers=headers, timeout=10) # Increased timeout
            
            if resp.status_code != 200:
                time.sleep(1)
                continue

            soup = BeautifulSoup(resp.content, "html.parser")
            price_div = soup.find("div", {"class": "YMlKec fxKbKc"})
            
            if price_div:
                price_text = price_div.text.replace("₹", "").replace(",", "")
                return float(price_text)
                
        except Exception as e:
            print(f"[WARN] Scrape Attempt {attempt+1} Failed for {ticker}: {e}")
            time.sleep(random.uniform(1, 2)) # Random backoff
            
    print(f"[ERR] Failed to fetch live price for {ticker} after {retries} attempts")
    return None

import requests
import yfinance as yf
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time

def calculate_signal(f_score: float, t_score: int) -> str:
    """
    Unified BUY/HOLD/SELL signal based on Fundamental + Technical scores.
    f_score: 0-10 (Fundamental)
    t_score: 1-3 (Technical)
    Returns: "BUY" | "HOLD" | "SELL"
    """
    # Weighted combination: 60% Fundamental + 40% Technical
    combined = (f_score * 0.6) + ((t_score / 3) * 10 * 0.4)
    
    if combined >= 7.0:  # 70%+
        return "BUY"
    elif combined >= 5.0:  # 50-70%
        return "HOLD"
    else:
        return "SELL"

def analyze_stock_web(symbol):
    """
    Scrapes Google News RSS for recent news/analysis of the stock.
    Fetches OHLC data from yfinance.
    Returns a unified analysis format: 
    - F-Score (1-10), T-Score (1-3)
    - Reasons (News Headlines)
    - News Links
    - OHLC Data (1y)
    - Support & Resistance Levels
    """
    
    from scraper_utils import get_google_finance_price

    # 0. Live Price Check (Google Finance) -> Fallback for LTP
    live_price = get_google_finance_price(symbol)
    print(f"[DATA] Live Price for {symbol}: {live_price}")

    # 1. Google News RSS Scraping
    query = f"{symbol} stock news india"
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    
    print(f"[SEARCH] Searching Google News RSS for: {query}")
    
    news_results = []
    
    # Sentiment Bag
    pos_keywords = ["buy", "outperform", "growth", "strong", "bullish", "profit", "surge", "breakout", "uptrend", "target", "high", "gain", "rise", "jump"]
    neg_keywords = ["sell", "underperform", "loss", "weak", "bearish", "fall", "crash", "downtrend", "miss", "lower", "drop", "plunge", "down"]
    
    pos_count = 0
    neg_count = 0
    insights = []
    news_links = [] # Clickable links

    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")
        
        # Parse top 10 items
        for item in items[:10]:
            title = item.title.text
            link = item.link.text if item.link else "#"
            # desc = item.description.text if item.description else "" # Usually html clutter
            
            # Sentiment Analysis
            text = title.lower()
            p_hit = False
            n_hit = False
            
            for w in pos_keywords: 
                if w in text: 
                    pos_count += 1
                    p_hit = True
            for w in neg_keywords: 
                if w in text: 
                    neg_count += 1
                    n_hit = True
            
            clean_title = title.replace(" - Moneycontrol", "").replace(" - Economic Times", "").replace(" - Livemint", "")
            
            if p_hit or n_hit:
                 insights.append(f"[NEWS] {clean_title[:80]}...")
            
            news_links.append({"title": clean_title, "url": link})

    except Exception as e:
        print(f"Search Error: {e}")
        insights.append("[WARN] Web Search Failed")

    # 2. OHLC Data & Technicals (yfinance)
    ohlc_data = []
    support = 0
    resistance = 0
    ltp = 0
    
    try:
        print(f"[DATA] Fetching OHLC for {symbol}.NS")
        ticker = yf.Ticker(f"{symbol}.NS")
        hist = ticker.history(period="1y")
        
        if not hist.empty:
            ltp = hist['Close'].iloc[-1]
            
            # Simple S/R (3 Month Low/High)
            recent = hist.tail(60)
            support = round(recent['Low'].min(), 2)
            resistance = round(recent['High'].max(), 2)
            
            # Serialize for JSON
            for date, row in hist.iterrows():
                ohlc_data.append({
                    "time": date.strftime("%Y-%m-%d"),
                    "open": round(row['Open'], 2),
                    "high": round(row['High'], 2),
                    "low": round(row['Low'], 2),
                    "close": round(row['Close'], 2)
                })
    except Exception as e:
        print(f"yfinance Error: {e}")

    # Fallback: Mock Data if OHLC is empty (for Demo/Dev consistency)
    if not ohlc_data:
        import random
        from datetime import datetime, timedelta
        print("[WARN] Generating Mock OHLC Data due to fetch failure")
        
        # Use live price as anchor if available, else 100
        base_price = live_price if live_price else 100.0
        
        # Generate generic trend ending at base_price
        # working backwards
        details = []
        current_mock = base_price
        
        for i in range(250):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            # Random walk backwards
            change = random.uniform(-2, 2) 
            open_p = current_mock - change
            high_p = max(current_mock, open_p) + random.uniform(0, 1)
            low_p = min(current_mock, open_p) - random.uniform(0, 1)
            
            ohlc_data.insert(0, {
                "time": date,
                "open": round(open_p, 2),
                "high": round(high_p, 2),
                "low": round(low_p, 2),
                "close": round(current_mock, 2)
            })
            current_mock = open_p # Set for next iter (yesterday)
        
        # Recalculate S/R on mock data
        closes = [x['close'] for x in ohlc_data]
        support = round(min(closes[-60:]), 2)
        resistance = round(max(closes[-60:]), 2)
        ltp = live_price if live_price else closes[-1]
        insights.append("[WARN] Pricing Data is Simulated (Network Error)")
    
    # Override LTP if we have live price (more accurate than yfinance close yesterday)
    if live_price:
        ltp = live_price

    # 3. Calculate Final Scores
    total_signals = pos_count + neg_count
    
    # Default neutral if no signals
    sentiment_ratio = pos_count / total_signals if total_signals > 0 else 0.5
    
    f_score = round(sentiment_ratio * 10, 1)
    
    t_score = 2
    if sentiment_ratio > 0.6: t_score = 3
    elif sentiment_ratio < 0.4: t_score = 1
    
    t_reasons = []
    if t_score == 3: t_reasons.append(f"[OK] News Sentiment Bullish ({pos_count} Positive)")
    elif t_score == 1: t_reasons.append(f"[FAIL] News Sentiment Bearish ({neg_count} Negative)")
    else: t_reasons.append(f"[INFO] News Sentiment Neutral")
    
    # Fill insights if empty
    f_reasons = insights[:4]
    if not f_reasons: 
        if news_links: f_reasons.append("[INFO] See news links below.")
        else: f_reasons.append("[INFO] No news found.")
    
    signal = calculate_signal(f_score, t_score)
    
    return {
        "symbol": symbol,
        "f_score": f_score,
        "f_reasons": f_reasons,
        "t_score": t_score,
        "t_reasons": t_reasons,
        "signal": signal,
        "summary": f"Analyzed {len(news_links)} news items. Found {pos_count} positive signals.",
        "news_links": news_links[:5], # Top 5
        "ohlc": ohlc_data, # Full year history
        "support": support,
        "resistance": resistance,
        "ltp": round(ltp, 2)
    }

if __name__ == "__main__":
    import sys
    import json
    ticker = sys.argv[1] if len(sys.argv) > 1 else "ZOMATO"
    res = analyze_stock_web(ticker)
    
    # Truncate OHLC for print clarity
    res_print = res.copy()
    res_print['ohlc'] = f"[{len(res['ohlc'])} datapoints]"
    print(json.dumps(res_print, indent=2))

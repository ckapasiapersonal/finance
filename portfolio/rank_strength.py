import yfinance as yf
import pandas as pd

def rank_holdings_by_strength(holdings_df):
    """
    Ranks current holdings by 3-month performance.
    """
    if holdings_df.empty:
        return holdings_df
        
    symbols = holdings_df['symbol'].tolist()
    rankings = []
    
    for sym in symbols:
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="6mo")
            if len(hist) < 63: continue
            
            p_now = hist['Close'].iloc[-1]
            p_3m = hist['Close'].iloc[-63]
            perf = ((p_now - p_3m) / p_3m) * 100
            
            rankings.append({'symbol': sym, 'perf_3m': perf})
        except:
            continue
            
    rank_df = pd.DataFrame(rankings)
    if rank_df.empty:
        return holdings_df
        
    rank_df = rank_df.sort_values(by='perf_3m', ascending=False)
    
    # Merge with original holdings for display
    merged = holdings_df.merge(rank_df, on='symbol', how='left')
    return merged.sort_values(by='perf_3m', ascending=False)

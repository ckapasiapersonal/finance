import pandas as pd
import numpy as np

def add_indicators(df):
    """
    Adds Smart Swing Tech:
    - EMA 20, 50, 200
    - RSI 14
    - Volume SMA 20
    """
    df = df.copy()
    
    if 'Close' not in df.columns and 'close' in df.columns:
        df['Close'] = df['close']
        
    # EMAs
    df['ema20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['ema200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Volume SMA
    if 'Volume' in df.columns:
        df['vol_ma20'] = df['Volume'].rolling(window=20).mean()
    
    return df

def check_strategy(df):
    """
    Strategy: Trend + Pullback
    1. Price > 200 EMA (Trend)
    2. 20 EMA > 50 EMA (Momentum)
    3. RSI between 40-60 (Pullback/Consolidation)
    4. Volume > VolumeAvg (Validation)
    """
    if df.empty or len(df) < 200:
        return False, "Insufficient Data"
        
    row = df.iloc[-1]
    
    # Conditions
    c1 = row['Close'] > row['ema200']
    c2 = row['ema20'] > row['ema50']
    c3 = 40 <= row['rsi'] <= 60
    
    vol_ok = True
    if 'Volume' in df.columns and 'vol_ma20' in df.columns:
        vol_ok = row['Volume'] > row['vol_ma20']
        
    if c1 and c2 and c3 and vol_ok:
        return True, "BUY: Trend + Pullback + Vol"
        
    return False, "Wait"

def check_exit(df, entry_price):
    """
    Exit Rules:
    1. Target: +10%
    2. Stop: -5%
    3. Technical: Close < 20 EMA
    """
    row = df.iloc[-1]
    current = row['Close']
    
    if current >= entry_price * 1.10:
        return True, "Target Hit (+10%)"
    
    if current <= entry_price * 0.95:
        return True, "Stop Hit (-5%)"
        
    if current < row['ema20']:
        return True, "Trend Broken (< 20 EMA)"
        
    return False, "HOLD"

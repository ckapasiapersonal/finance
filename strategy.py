import pandas as pd
import numpy as np

def add_indicators(df):
    """
    Adds Technical Indicators:
    - EMA 20, 50, 200
    - RSI 14
    - Volume 20 SMA
    """
    df = df.copy()
    
    # Handle MultiIndex columns (yfinance new behavior)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Handle yfinance column case sensitivity
    if 'Close' not in df.columns and 'close' in df.columns:
        df['Close'] = df['close']
    if 'Volume' not in df.columns and 'volume' in df.columns:
        df['Volume'] = df['volume']

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
        
    # MACD (12, 26, 9)
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    # ADX (14) - Simple implementation
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    
    tr1 = pd.DataFrame(high - low)
    tr2 = pd.DataFrame(abs(high - close.shift(1)))
    tr3 = pd.DataFrame(abs(low - close.shift(1)))
    frames = [tr1, tr2, tr3]
    tr = pd.concat(frames, axis=1, join='inner').max(axis=1)
    atr = tr.rolling(14).mean()
    
    plus_di = 100 * (plus_dm.ewm(alpha=1/14).mean() / atr)
    minus_di = 100 * (abs(minus_dm).ewm(alpha=1/14).mean() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    df['adx'] = dx.rolling(14).mean()
    
    return df

def check_nifty_regime(nifty_df):
    """
    Market Regime Filter:
    NIFTY 50 must be above 200 EMA.
    """
    if nifty_df.empty or len(nifty_df) < 200:
        return False
        
    nifty_df = add_indicators(nifty_df)
    last_row = nifty_df.iloc[-1]
    
    return last_row['Close'] > last_row['ema200']

def check_entry_setup(df):
    """
    Core Swing Strategy (Trend Pullback):
    1. Trend: Price > 200 EMA
    2. Momentum: 20 EMA > 50 EMA
    3. Pullback: RSI(14) between 40–60
    4. Volume: > 1.5x 20-day average
    """
    if df.empty or len(df) < 200:
        return False, "Insufficient Data"
        
    row = df.iloc[-1]
    
    # Conditions
    c1 = row['Close'] > row['ema200']
    c2 = row['ema20'] > row['ema50']
    c3 = 40 <= row['rsi'] <= 60
    
    # Volume Condition (1.5x)
    val_vol = False
    if 'Volume' in df.columns and 'vol_ma20' in df.columns:
        # Avoid division by zero
        if row['vol_ma20'] > 0:
            val_vol = row['Volume'] > (1.5 * row['vol_ma20'])
            
    if c1 and c2 and c3 and val_vol:
        return True, "BUY: Trend + Pullback + 1.5x Vol"
        
    return False, "Wait"

def check_exit_setup(df, entry_price):
    """
    Exit Rules:
    1. Target: +10%
    2. Stop: -5%
    3. Technical: Close < 20 EMA
    """
    if df.empty: return False, "No Data"
    
    row = df.iloc[-1]
    current = row['Close']
    
    if current >= entry_price * 1.10:
        return True, "Target Hit (+10%)"
    
    if current <= entry_price * 0.95:
        return True, "Stop Hit (-5%)"
        
    if current < row['ema20']:
        return True, "Trend Broken (< 20 EMA)"
        
    return False, "HOLD"

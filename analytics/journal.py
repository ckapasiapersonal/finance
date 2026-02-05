import sqlite3
import pandas as pd
from data.database import get_all_trades

def get_journal_metrics():
    """
    Calculates:
    - Total trades
    - Win rate
    - Average return %
    """
    df = get_all_trades()
    if df.empty:
        return {
            'total_trades': 0,
            'win_rate': 0.0,
            'avg_return': 0.0
        }
        
    closed_trades = df[df['status'] == 'CLOSED']
    if closed_trades.empty:
        return {
            'total_trades': len(df),
            'win_rate': 0.0,
            'avg_return': 0.0
        }
        
    win_rate = (len(closed_trades[closed_trades['pnl'] > 0]) / len(closed_trades)) * 100
    avg_return = closed_trades['pnl'].mean() # This should ideally be % return
    
    return {
        'total_trades': len(df),
        'win_rate': win_rate,
        'avg_return': avg_return
    }

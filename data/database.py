import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join("data", "trades.db")

def init_db():
    """Initializes the SQLite database with the trades table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            entry_date TEXT NOT NULL,
            entry_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            stop_loss REAL NOT NULL,
            target REAL NOT NULL,
            exit_date TEXT,
            exit_price REAL,
            pnl REAL,
            status TEXT DEFAULT 'OPEN'
        )
    """)
    conn.commit()
    conn.close()

def save_trade(trade_data):
    """Saves a new trade to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trades (symbol, entry_date, entry_price, quantity, stop_loss, target, status)
        VALUES (?, ?, ?, ?, ?, ?, 'OPEN')
    """, (
        trade_data['symbol'],
        trade_data['entry_date'],
        trade_data['entry_price'],
        trade_data['quantity'],
        trade_data['stop_loss'],
        trade_data['target']
    ))
    conn.commit()
    conn.close()

def get_all_trades():
    """Fetches all trades as a pandas DataFrame."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM trades", conn)
    conn.close()
    return df

def update_trade_exit(trade_id, exit_date, exit_price, pnl):
    """Updates a trade with exit information."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE trades
        SET exit_date = ?, exit_price = ?, pnl = ?, status = 'CLOSED'
        WHERE id = ?
    """, (exit_date, exit_price, pnl, trade_id))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")

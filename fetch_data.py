"""
fetch_data.py
Downloads historical stock data from Yahoo Finance and saves as CSV.
Run this ONCE to cache the data locally - dont re-run unless you need fresh data.

Mehmet Tanil Kaplan - T0429362
"""

import yfinance as yf
import os

# the 5 tickers we decided to use for this project
TICKERS = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN']

# make sure data folder exists
if not os.path.exists('data'):
    os.makedirs('data')

for ticker in TICKERS:
    print(f"Downloading {ticker}...")
    df = yf.download(ticker, start='2015-01-01', end='2026-03-18')

    # yfinance returns multi-level columns when downloading single ticker
    # flatten them so the CSV is clean and easy to read later
    if hasattr(df.columns, 'droplevel'):
        df.columns = df.columns.droplevel('Ticker')

    # save to csv
    filepath = f'data/{ticker}.csv'
    df.to_csv(filepath)
    print(f"  Saved {ticker}.csv - {len(df)} rows")

print("\nDone! All data cached in data/ folder.")
print("You can now run the training scripts without hitting API limits.")

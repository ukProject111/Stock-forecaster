"""
preprocess.py
Helper functions for loading data, scaling, and creating sliding windows.
Both training scripts and the FastAPI backend import from here.

Mehmet Tanil Kaplan - T0429362
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

WINDOW_SIZE = 50  # 50 days of prices to predict day 51


def load_stock_data(ticker):
    """Load CSV file for a given ticker and return the Close prices as numpy array."""
    filepath = f'data/{ticker}.csv'
    df = pd.read_csv(filepath, index_col='Date', parse_dates=True)

    # we only need the Close column for our models
    prices = df[['Close']].values
    return prices, df


def create_windows(data, window_size=WINDOW_SIZE):
    """Create sliding windows from the scaled data.
    Each window is 50 consecutive prices, label is the next price."""
    X = []
    y = []
    for i in range(window_size, len(data)):
        X.append(data[i - window_size:i])
        y.append(data[i])

    X = np.array(X)
    y = np.array(y)
    return X, y


def split_data(X, y):
    """Split into train/val/test chronologically (70/15/15).
    IMPORTANT: never shuffle time series data!"""
    n = len(X)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    X_train = X[:train_end]
    y_train = y[:train_end]

    X_val = X[train_end:val_end]
    y_val = y[train_end:val_end]

    X_test = X[val_end:]
    y_test = y[val_end:]

    return X_train, y_train, X_val, y_val, X_test, y_test


def fit_scaler(train_prices):
    """Fit MinMaxScaler on training data ONLY to avoid data leakage."""
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaler.fit(train_prices)
    return scaler


def prepare_data_for_ticker(ticker, window_size=WINDOW_SIZE):
    """Full pipeline: load -> scale -> window -> split.
    Returns everything needed for training."""
    prices, df = load_stock_data(ticker)

    # figure out where training data ends (70% of raw prices)
    train_cutoff = int(len(prices) * 0.70)
    train_prices = prices[:train_cutoff]

    # fit scaler on training portion only
    scaler = fit_scaler(train_prices)

    # scale all the data using the training-fitted scaler
    scaled = scaler.transform(prices)

    # create sliding windows
    X, y = create_windows(scaled, window_size)

    # split chronologically
    X_train, y_train, X_val, y_val, X_test, y_test = split_data(X, y)

    return {
        'X_train': X_train, 'y_train': y_train,
        'X_val': X_val, 'y_val': y_val,
        'X_test': X_test, 'y_test': y_test,
        'scaler': scaler,
        'prices': prices,
        'df': df
    }

"""
train_on_demand.py
Trains models for any ticker on-the-fly when first requested.
Downloads data, trains both baseline and LSTM, caches everything.
Subsequent requests for the same ticker use cached models.

Mehmet Tanil Kaplan - T0429362
"""

import os
import sys
import numpy as np
import pandas as pd
import joblib
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam

WINDOW_SIZE = 50

# track which tickers are currently being trained to avoid double-training
_training_in_progress = set()


def get_base_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def is_trained(ticker):
    """Check if a ticker already has trained models saved."""
    models_dir = os.path.join(get_base_dir(), 'models')
    baseline_path = os.path.join(models_dir, f'baseline_{ticker}.pkl')
    lstm_path = os.path.join(models_dir, f'lstm_{ticker}.keras')
    scaler_path = os.path.join(models_dir, f'scaler_{ticker}.pkl')
    return os.path.exists(baseline_path) and os.path.exists(lstm_path) and os.path.exists(scaler_path)


def download_data(ticker):
    """Download historical data for a ticker if not already cached.
    Uses Yahoo Finance chart API directly for Docker compatibility."""
    data_dir = os.path.join(get_base_dir(), 'data')
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, f'{ticker}.csv')

    # if CSV exists and is recent enough (less than 1 day old), skip download
    if os.path.exists(csv_path):
        import time
        age_hours = (time.time() - os.path.getmtime(csv_path)) / 3600
        if age_hours < 24:
            return csv_path

    print(f"  Downloading data for {ticker}...")

    t = yf.Ticker(ticker)
    df = t.history(period='max', interval='1d', prepost=False)

    if df is None or df.empty:
        raise ValueError(f"No data available for ticker '{ticker}'. Check if it's a valid symbol.")

    # yfinance returns columns like Open, High, Low, Close, Volume
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    df.index.name = 'Date'
    df = df.dropna(subset=['Close'])
    df = df.sort_index()

    min_days = WINDOW_SIZE + 30  # need at least window size + some data for train/test split
    if len(df) < min_days:
        raise ValueError(f"Not enough data for {ticker}. Need at least {min_days} days, got {len(df)}.")

    df.to_csv(csv_path)
    print(f"  Saved {ticker}.csv - {len(df)} rows")
    return csv_path


def prepare_data(ticker):
    """Load, scale, window, and split data for a ticker."""
    data_dir = os.path.join(get_base_dir(), 'data')
    csv_path = os.path.join(data_dir, f'{ticker}.csv')

    df = pd.read_csv(csv_path, index_col='Date', parse_dates=True)
    prices = df[['Close']].values

    min_days = WINDOW_SIZE + 30
    if len(prices) < min_days:
        raise ValueError(f"Not enough data for {ticker}. Need at least {min_days} days, got {len(prices)}.")

    # fit scaler on training portion only (70%)
    train_cutoff = int(len(prices) * 0.70)
    train_prices = prices[:train_cutoff]

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaler.fit(train_prices)
    scaled = scaler.transform(prices)

    # create windows
    X, y = [], []
    for i in range(WINDOW_SIZE, len(scaled)):
        X.append(scaled[i - WINDOW_SIZE:i])
        y.append(scaled[i])

    X = np.array(X)
    y = np.array(y)

    # chronological split
    n = len(X)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    return {
        'X_train': X[:train_end], 'y_train': y[:train_end],
        'X_val': X[train_end:val_end], 'y_val': y[train_end:val_end],
        'X_test': X[val_end:], 'y_test': y[val_end:],
        'scaler': scaler
    }


def train_ticker(ticker):
    """Train both baseline and LSTM models for a single ticker.
    Returns metrics dict. Models are saved to disk."""
    ticker = ticker.upper().strip()

    if ticker in _training_in_progress:
        raise ValueError(f"{ticker} is currently being trained. Please wait.")

    _training_in_progress.add(ticker)

    try:
        print(f"\n=== ON-DEMAND TRAINING: {ticker} ===")

        # step 1: download data
        download_data(ticker)

        # step 2: prepare data
        data = prepare_data(ticker)
        scaler = data['scaler']

        models_dir = os.path.join(get_base_dir(), 'models')
        os.makedirs(models_dir, exist_ok=True)

        # step 3: train baseline (Random Forest)
        print(f"  Training baseline for {ticker}...")
        X_train_flat = data['X_train'].reshape(len(data['X_train']), -1)
        X_test_flat = data['X_test'].reshape(len(data['X_test']), -1)

        baseline = RandomForestRegressor(n_estimators=100, random_state=42)
        baseline.fit(X_train_flat, data['y_train'].ravel())

        bl_pred = scaler.inverse_transform(
            baseline.predict(X_test_flat).reshape(-1, 1)
        )
        bl_actual = scaler.inverse_transform(data['y_test'].reshape(-1, 1))
        bl_mse = mean_squared_error(bl_actual, bl_pred)
        bl_rmse = np.sqrt(bl_mse)
        print(f"  Baseline RMSE: {bl_rmse:.4f}")

        # step 4: train LSTM
        print(f"  Training LSTM for {ticker}...")
        X_train = data['X_train'].reshape(-1, WINDOW_SIZE, 1)
        X_val = data['X_val'].reshape(-1, WINDOW_SIZE, 1)
        X_test = data['X_test'].reshape(-1, WINDOW_SIZE, 1)

        lstm = Sequential([
            LSTM(128, return_sequences=True, input_shape=(WINDOW_SIZE, 1)),
            Dropout(0.15),
            LSTM(64, return_sequences=False),
            Dropout(0.15),
            Dense(32, activation='relu'),
            Dense(1)
        ])
        lstm.compile(optimizer=Adam(learning_rate=0.001), loss='mse')

        lstm.fit(
            X_train, data['y_train'],
            epochs=100,
            batch_size=32,
            validation_data=(X_val, data['y_val']),
            callbacks=[
                EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True),
                ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-5)
            ],
            verbose=0
        )

        ls_pred = scaler.inverse_transform(lstm.predict(X_test, verbose=0))
        ls_actual = scaler.inverse_transform(data['y_test'].reshape(-1, 1))
        ls_mse = mean_squared_error(ls_actual, ls_pred)
        ls_rmse = np.sqrt(ls_mse)
        print(f"  LSTM RMSE: {ls_rmse:.4f}")

        improvement = ((bl_rmse - ls_rmse) / bl_rmse) * 100
        print(f"  Improvement: {improvement:.1f}%")

        # step 5: save everything
        joblib.dump(baseline, os.path.join(models_dir, f'baseline_{ticker}.pkl'))
        lstm.save(os.path.join(models_dir, f'lstm_{ticker}.keras'))
        joblib.dump(scaler, os.path.join(models_dir, f'scaler_{ticker}.pkl'))

        # update metrics files
        bl_metrics_path = os.path.join(models_dir, 'baseline_metrics.pkl')
        ls_metrics_path = os.path.join(models_dir, 'lstm_metrics.pkl')

        bl_metrics = joblib.load(bl_metrics_path) if os.path.exists(bl_metrics_path) else {}
        ls_metrics = joblib.load(ls_metrics_path) if os.path.exists(ls_metrics_path) else {}

        bl_metrics[ticker] = {'mse': bl_mse, 'rmse': bl_rmse}
        ls_metrics[ticker] = {'mse': ls_mse, 'rmse': ls_rmse}

        joblib.dump(bl_metrics, bl_metrics_path)
        joblib.dump(ls_metrics, ls_metrics_path)

        print(f"  {ticker} training complete!\n")

        return {
            'ticker': ticker,
            'baseline_rmse': round(bl_rmse, 4),
            'lstm_rmse': round(ls_rmse, 4),
            'improvement_pct': round(improvement, 2),
            'status': 'trained'
        }

    finally:
        _training_in_progress.discard(ticker)

"""
train_baseline.py
Trains a Random Forest baseline model for each ticker.
The baseline flattens the 50-day window into a 1D feature vector.
It doesnt understand time order - thats why LSTM should beat it.

Mehmet Tanil Kaplan - T0429362
"""

import sys
import os
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

# add parent dir so we can import from backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.preprocess import prepare_data_for_ticker

TICKERS = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN']


def train_baseline_for_ticker(ticker):
    """Train Random Forest on one ticker and return metrics."""
    print(f"\n--- Training baseline for {ticker} ---")

    data = prepare_data_for_ticker(ticker)

    X_train = data['X_train']
    y_train = data['y_train']
    X_test = data['X_test']
    y_test = data['y_test']
    scaler = data['scaler']

    # flatten windows for sklearn (it cant handle 3D input)
    X_train_flat = X_train.reshape(len(X_train), -1)
    X_test_flat = X_test.reshape(len(X_test), -1)
    y_train_flat = y_train.ravel()

    # train random forest
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train_flat, y_train_flat)

    # predict on test set
    y_pred_scaled = model.predict(X_test_flat)

    # inverse transform to get actual prices
    y_pred_actual = scaler.inverse_transform(y_pred_scaled.reshape(-1, 1))
    y_test_actual = scaler.inverse_transform(y_test.reshape(-1, 1))

    # calculate error metrics
    mse = mean_squared_error(y_test_actual, y_pred_actual)
    rmse = np.sqrt(mse)

    print(f"  MSE:  {mse:.4f}")
    print(f"  RMSE: {rmse:.4f}")

    return model, scaler, mse, rmse


if __name__ == '__main__':
    os.makedirs('models', exist_ok=True)

    results = {}

    for ticker in TICKERS:
        model, scaler, mse, rmse = train_baseline_for_ticker(ticker)

        # save model and scaler for each ticker
        joblib.dump(model, f'models/baseline_{ticker}.pkl')
        joblib.dump(scaler, f'models/scaler_{ticker}.pkl')

        results[ticker] = {'mse': mse, 'rmse': rmse}

    # save results summary
    joblib.dump(results, 'models/baseline_metrics.pkl')

    print("\n\n=== BASELINE RESULTS SUMMARY ===")
    for ticker, metrics in results.items():
        print(f"  {ticker}: MSE={metrics['mse']:.4f}, RMSE={metrics['rmse']:.4f}")

    print("\nAll baseline models saved to models/ folder.")

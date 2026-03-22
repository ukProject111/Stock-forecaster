"""
train_lstm.py
Trains an optimized LSTM model for each stock ticker.
Uses larger architecture and more epochs for best possible accuracy.
LSTM should outperform the baseline by at least 10% RMSE.

Mehmet Tanil Kaplan - T0429362
"""

import sys
import os
import numpy as np
import joblib
from sklearn.metrics import mean_squared_error

# tensorflow imports
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # reduce tensorflow logging noise
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.preprocess import prepare_data_for_ticker

TICKERS = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN']


def build_lstm_model(window_size=50):
    """Build an optimized LSTM architecture.
    Larger than the basic spec to squeeze out more accuracy.
    - 128 units in first layer (up from 64) for more capacity
    - 64 units in second layer (up from 32)
    - Lower dropout (0.15) to retain more signal
    - Adam with tuned learning rate
    """
    model = Sequential([
        LSTM(128, return_sequences=True, input_shape=(window_size, 1)),
        Dropout(0.15),
        LSTM(64, return_sequences=False),
        Dropout(0.15),
        Dense(32, activation='relu'),
        Dense(1)  # predicts next day closing price
    ])

    optimizer = Adam(learning_rate=0.001)
    model.compile(optimizer=optimizer, loss='mse')
    return model


def train_lstm_for_ticker(ticker):
    """Train LSTM on one ticker, return model and metrics."""
    print(f"\n--- Training LSTM for {ticker} ---")

    data = prepare_data_for_ticker(ticker)

    # LSTM needs 3D input: (samples, timesteps, features)
    X_train = data['X_train'].reshape(-1, 50, 1)
    y_train = data['y_train']
    X_val = data['X_val'].reshape(-1, 50, 1)
    y_val = data['y_val']
    X_test = data['X_test'].reshape(-1, 50, 1)
    y_test = data['y_test']
    scaler = data['scaler']

    # build fresh model for each ticker
    model = build_lstm_model()

    # early stopping with more patience so the model has time to converge
    early_stop = EarlyStopping(
        monitor='val_loss',
        patience=15,
        restore_best_weights=True
    )

    # reduce learning rate when validation loss plateaus
    reduce_lr = ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=5,
        min_lr=0.00001,
        verbose=1
    )

    # train for more epochs (100 instead of 50) with callbacks to prevent overfitting
    history = model.fit(
        X_train, y_train,
        epochs=100,
        batch_size=32,
        validation_data=(X_val, y_val),
        callbacks=[early_stop, reduce_lr],
        verbose=1
    )

    # predict on test set
    y_pred_scaled = model.predict(X_test)

    # inverse transform back to real prices
    y_pred_actual = scaler.inverse_transform(y_pred_scaled)
    y_test_actual = scaler.inverse_transform(y_test.reshape(-1, 1))

    # metrics
    mse = mean_squared_error(y_test_actual, y_pred_actual)
    rmse = np.sqrt(mse)

    print(f"  MSE:  {mse:.4f}")
    print(f"  RMSE: {rmse:.4f}")

    return model, mse, rmse


if __name__ == '__main__':
    os.makedirs('models', exist_ok=True)

    # load baseline results to compare
    baseline_metrics = None
    if os.path.exists('models/baseline_metrics.pkl'):
        baseline_metrics = joblib.load('models/baseline_metrics.pkl')

    results = {}

    for ticker in TICKERS:
        model, mse, rmse = train_lstm_for_ticker(ticker)

        # save model in native keras format
        model.save(f'models/lstm_{ticker}.keras')

        results[ticker] = {'mse': mse, 'rmse': rmse}

    # save results
    joblib.dump(results, 'models/lstm_metrics.pkl')

    print("\n\n=== LSTM RESULTS SUMMARY ===")
    for ticker, metrics in results.items():
        print(f"  {ticker}: MSE={metrics['mse']:.4f}, RMSE={metrics['rmse']:.4f}")

    # compare with baseline if available
    if baseline_metrics:
        print("\n=== COMPARISON (LSTM vs Baseline) ===")
        for ticker in TICKERS:
            bl_rmse = baseline_metrics[ticker]['rmse']
            lstm_rmse = results[ticker]['rmse']
            improvement = ((bl_rmse - lstm_rmse) / bl_rmse) * 100
            status = "PASS" if improvement >= 10 else "NEEDS TUNING"
            print(f"  {ticker}: Baseline RMSE={bl_rmse:.4f}, LSTM RMSE={lstm_rmse:.4f}, "
                  f"Improvement={improvement:.1f}% [{status}]")

    print("\nAll LSTM models saved to models/ folder.")

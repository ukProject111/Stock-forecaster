"""
predict.py
Prediction logic used by the FastAPI endpoints.
Loads models and scalers, runs predictions for any trained ticker.
Also handles long-term rolling forecasts using the LSTM.

Mehmet Tanil Kaplan - T0429362
"""

import numpy as np
import pandas as pd
import joblib
import os
from datetime import datetime, timedelta

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'
import tensorflow as tf
# limit TF memory usage
tf.config.set_visible_devices([], 'GPU')
from tensorflow.keras.models import load_model

WINDOW_SIZE = 50

# store loaded models in memory so we dont reload every request
_models = {}
_scalers = {}


def get_models_dir():
    """Figure out where the models folder is relative to this file."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, 'models')


def get_data_dir():
    """Figure out where the data folder is."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, 'data')


def get_trained_tickers():
    """Return list of all tickers that have trained models ready."""
    models_dir = get_models_dir()
    if not os.path.exists(models_dir):
        return []

    tickers = set()
    for f in os.listdir(models_dir):
        if f.startswith('baseline_') and f.endswith('.pkl'):
            ticker = f.replace('baseline_', '').replace('.pkl', '')
            # verify all three files exist
            if (os.path.exists(os.path.join(models_dir, f'lstm_{ticker}.keras')) and
                os.path.exists(os.path.join(models_dir, f'scaler_{ticker}.pkl'))):
                tickers.add(ticker)

    return sorted(list(tickers))


def is_ticker_trained(ticker):
    """Check if a specific ticker has trained models."""
    models_dir = get_models_dir()
    return (
        os.path.exists(os.path.join(models_dir, f'baseline_{ticker}.pkl')) and
        os.path.exists(os.path.join(models_dir, f'lstm_{ticker}.keras')) and
        os.path.exists(os.path.join(models_dir, f'scaler_{ticker}.pkl'))
    )


def load_models_for_ticker(ticker):
    """Load baseline model, LSTM model, and scaler for a ticker.
    Caches them so subsequent calls are fast."""
    if ticker in _models:
        return _models[ticker], _scalers[ticker]

    models_dir = get_models_dir()

    if not is_ticker_trained(ticker):
        raise FileNotFoundError(f"No trained models for {ticker}. Train it first.")

    baseline = joblib.load(os.path.join(models_dir, f'baseline_{ticker}.pkl'))
    keras_path = os.path.join(models_dir, f'lstm_{ticker}.keras')
    lstm = load_model(keras_path)
    scaler = joblib.load(os.path.join(models_dir, f'scaler_{ticker}.pkl'))

    _models[ticker] = {'baseline': baseline, 'lstm': lstm}
    _scalers[ticker] = scaler

    return _models[ticker], _scalers[ticker]


def _load_ticker_df(ticker):
    """Load cached CSV for a ticker."""
    data_dir = get_data_dir()
    csv_path = os.path.join(data_dir, f'{ticker}.csv')
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"No data file for {ticker}.")
    df = pd.read_csv(csv_path, index_col='Date', parse_dates=True)
    return df


def get_prediction(ticker):
    """Get next-day predictions from both models for a ticker."""
    ticker = ticker.upper().strip()

    if not is_ticker_trained(ticker):
        raise FileNotFoundError(f"No trained models for {ticker}. Use /train?ticker={ticker} first.")

    models, scaler = load_models_for_ticker(ticker)
    df = _load_ticker_df(ticker)

    # grab the last 50 days of closing prices
    last_50 = df[['Close']].values[-WINDOW_SIZE:]
    scaled = scaler.transform(last_50)

    # baseline prediction
    baseline_input = scaled.reshape(1, -1)
    baseline_pred_scaled = models['baseline'].predict(baseline_input)
    baseline_pred = scaler.inverse_transform(
        baseline_pred_scaled.reshape(-1, 1)
    )[0][0]

    # lstm prediction
    lstm_input = scaled.reshape(1, WINDOW_SIZE, 1)
    lstm_pred_scaled = models['lstm'].predict(lstm_input, verbose=0)
    lstm_pred = scaler.inverse_transform(lstm_pred_scaled)[0][0]

    return {
        'ticker': ticker,
        'baseline_prediction': round(float(baseline_pred), 2),
        'lstm_prediction': round(float(lstm_pred), 2),
        'last_close': round(float(df['Close'].values[-1]), 2),
        'note': 'For educational purposes only. Not financial advice.'
    }


def get_long_term_forecast(ticker, years=10):
    """Generate a multi-year rolling forecast using the LSTM model."""
    ticker = ticker.upper().strip()

    if not is_ticker_trained(ticker):
        raise FileNotFoundError(f"No trained models for {ticker}. Train it first.")

    models, scaler = load_models_for_ticker(ticker)
    df = _load_ticker_df(ticker)

    last_prices = df[['Close']].values[-WINDOW_SIZE:]
    scaled_window = scaler.transform(last_prices).flatten().tolist()

    last_date = df.index[-1]
    last_real_price = float(df['Close'].values[-1])

    total_days = 252 * years
    lstm_model = models['lstm']

    all_preds = []
    current_window = list(scaled_window)

    for day in range(total_days):
        inp = np.array(current_window[-WINDOW_SIZE:]).reshape(1, WINDOW_SIZE, 1)
        pred_scaled = lstm_model.predict(inp, verbose=0)[0][0]
        real_price = scaler.inverse_transform([[pred_scaled]])[0][0]

        forecast_date = last_date + timedelta(days=int((day + 1) * 365.25 / 252))

        all_preds.append({
            'day': day + 1,
            'date': forecast_date.strftime('%Y-%m-%d'),
            'price': round(float(real_price), 2)
        })

        current_window.append(float(pred_scaled))

    # sample monthly
    monthly_samples = [all_preds[0]]
    for i in range(21, len(all_preds), 21):
        monthly_samples.append(all_preds[i])
    if all_preds[-1] not in monthly_samples:
        monthly_samples.append(all_preds[-1])

    # yearly summary
    yearly_summary = []
    for yr in range(1, years + 1):
        day_idx = min(yr * 252 - 1, len(all_preds) - 1)
        yearly_summary.append({
            'year': last_date.year + yr,
            'predicted_price': all_preds[day_idx]['price'],
            'date': all_preds[day_idx]['date']
        })

    return {
        'ticker': ticker,
        'start_price': last_real_price,
        'start_date': last_date.strftime('%Y-%m-%d'),
        'forecast_years': years,
        'total_trading_days': total_days,
        'monthly_forecast': monthly_samples,
        'yearly_summary': yearly_summary,
        'note': 'Long-term forecasts are highly speculative. For educational purposes only.'
    }


def get_history(ticker, days=90):
    """Return the last N days of closing prices for charting."""
    ticker = ticker.upper().strip()
    df = _load_ticker_df(ticker)

    recent = df.tail(days)
    history = []
    for date, row in recent.iterrows():
        history.append({
            'date': date.strftime('%Y-%m-%d'),
            'price': round(float(row['Close']), 2)
        })

    return history


def get_metrics(ticker):
    """Return pre-computed MSE and RMSE for both models."""
    ticker = ticker.upper().strip()

    models_dir = get_models_dir()

    baseline_metrics = joblib.load(os.path.join(models_dir, 'baseline_metrics.pkl'))
    lstm_metrics = joblib.load(os.path.join(models_dir, 'lstm_metrics.pkl'))

    if ticker not in baseline_metrics or ticker not in lstm_metrics:
        raise ValueError(f"No metrics for {ticker}. Train it first.")

    bl = baseline_metrics[ticker]
    ls = lstm_metrics[ticker]

    improvement = ((bl['rmse'] - ls['rmse']) / bl['rmse']) * 100

    return {
        'ticker': ticker,
        'baseline': {
            'mse': round(bl['mse'], 4),
            'rmse': round(bl['rmse'], 4)
        },
        'lstm': {
            'mse': round(ls['mse'], 4),
            'rmse': round(ls['rmse'], 4)
        },
        'lstm_improvement_pct': round(improvement, 2)
    }

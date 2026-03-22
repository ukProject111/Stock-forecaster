"""
main.py
FastAPI backend for the Stock Market Forecaster.
Supports any NASDAQ/US stock ticker with on-demand training.
Serves predictions, real-time data, historical data, and model metrics.

Mehmet Tanil Kaplan - T0429362
"""

import json
import asyncio
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from predict import (
    get_prediction, get_history, get_metrics,
    get_long_term_forecast, get_trained_tickers, is_ticker_trained
)
from realtime import get_nasdaq_tickers, get_realtime_data, get_ticker_info
from train_on_demand import train_ticker, is_trained

app = FastAPI(
    title="Stock Market Forecaster API",
    description="Baseline vs LSTM stock price prediction for any US stock - educational project",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "status": "running",
        "version": "2.0.0",
        "message": "Stock Market Forecaster API - supports all NASDAQ tickers",
        "disclaimer": "For educational purposes only. Not financial advice."
    }


@app.get("/tickers")
def list_tickers():
    """Return all supported tickers (full NASDAQ list)."""
    all_tickers = get_nasdaq_tickers()
    trained = get_trained_tickers()
    return {
        "total": len(all_tickers),
        "trained_count": len(trained),
        "trained": trained,
        "all_tickers": all_tickers
    }


@app.get("/trained")
def list_trained():
    """Return only tickers that have trained ML models ready."""
    trained = get_trained_tickers()
    return {"trained": trained, "count": len(trained)}


@app.get("/search")
def search_tickers(q: str = Query(..., description="Search query for ticker or company name")):
    """Search tickers by symbol prefix."""
    q = q.upper().strip()
    all_tickers = get_nasdaq_tickers()
    matches = [t for t in all_tickers if t.startswith(q)]

    # also check if query is contained in ticker for broader search
    if len(matches) < 10:
        fuzzy = [t for t in all_tickers if q in t and t not in matches]
        matches.extend(fuzzy[:20])

    trained = get_trained_tickers()
    results = []
    for t in matches[:30]:
        results.append({
            'ticker': t,
            'trained': t in trained
        })

    return {"query": q, "results": results, "count": len(results)}


@app.get("/realtime")
def realtime(
    ticker: str = Query(..., description="Stock ticker symbol"),
    period: str = Query("5d", description="Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 5y"),
    interval: str = Query("15m", description="Interval: 1m, 5m, 15m, 30m, 1h, 1d")
):
    """Get real-time / recent price data for ANY ticker (no training needed)."""
    ticker = ticker.upper().strip()

    data = get_realtime_data(ticker, period, interval)
    if data is None:
        raise HTTPException(status_code=404, detail=f"No data found for {ticker}. Check the ticker symbol.")

    return data


@app.get("/info")
def ticker_info(ticker: str = Query(..., description="Stock ticker symbol")):
    """Get basic info about a stock (name, sector, market cap)."""
    ticker = ticker.upper().strip()
    info = get_ticker_info(ticker)
    return info


@app.get("/train")
def train(ticker: str = Query(..., description="Ticker to train models for")):
    """Train baseline + LSTM models for a new ticker on-demand.
    Takes ~1-2 minutes per ticker. Models are cached after training."""
    ticker = ticker.upper().strip()

    if is_trained(ticker):
        return {
            "ticker": ticker,
            "status": "already_trained",
            "message": f"Models for {ticker} are already trained and ready."
        }

    try:
        result = train_ticker(ticker)
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@app.get("/train-stream")
def train_stream(ticker: str = Query(..., description="Ticker to train")):
    """Stream training progress via SSE with real-time status updates."""
    ticker = ticker.upper().strip()

    if is_trained(ticker):
        def already():
            yield f"data: {json.dumps({'type': 'progress', 'percent': 100, 'stage': 'Already trained'})}\n\n"
            yield f"data: {json.dumps({'type': 'result', 'data': {'ticker': ticker, 'status': 'already_trained', 'message': f'Models for {ticker} are already trained and ready.'}})}\n\n"
        return StreamingResponse(already(), media_type="text/event-stream")

    def generate():
        import threading

        progress_events = []
        result_holder = [None]
        error_holder = [None]

        def run():
            try:
                # stage 1: downloading data
                progress_events.append({'percent': 5, 'stage': 'Downloading stock data...'})
                from train_on_demand import download_data, prepare_data
                download_data(ticker)
                progress_events.append({'percent': 15, 'stage': 'Data downloaded. Preparing windows...'})

                # stage 2: prepare data
                data = prepare_data(ticker)
                scaler = data['scaler']
                progress_events.append({'percent': 25, 'stage': 'Training baseline model...'})

                # stage 3: train baseline
                import numpy as np
                from sklearn.ensemble import RandomForestRegressor
                from sklearn.metrics import mean_squared_error

                X_train_flat = data['X_train'].reshape(len(data['X_train']), -1)
                X_test_flat = data['X_test'].reshape(len(data['X_test']), -1)
                baseline = RandomForestRegressor(n_estimators=100, random_state=42)
                baseline.fit(X_train_flat, data['y_train'].ravel())

                bl_pred = scaler.inverse_transform(baseline.predict(X_test_flat).reshape(-1, 1))
                bl_actual = scaler.inverse_transform(data['y_test'].reshape(-1, 1))
                bl_mse = mean_squared_error(bl_actual, bl_pred)
                bl_rmse = np.sqrt(bl_mse)
                progress_events.append({'percent': 40, 'stage': f'Baseline RMSE: {bl_rmse:.2f}. Training LSTM...'})

                # stage 4: train LSTM
                import os
                os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
                from tensorflow.keras.models import Sequential
                from tensorflow.keras.layers import LSTM as LSTMLayer, Dense, Dropout
                from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, Callback
                from tensorflow.keras.optimizers import Adam

                WINDOW_SIZE = 50
                X_train = data['X_train'].reshape(-1, WINDOW_SIZE, 1)
                X_val = data['X_val'].reshape(-1, WINDOW_SIZE, 1)
                X_test = data['X_test'].reshape(-1, WINDOW_SIZE, 1)

                lstm = Sequential([
                    LSTMLayer(128, return_sequences=True, input_shape=(WINDOW_SIZE, 1)),
                    Dropout(0.15),
                    LSTMLayer(64, return_sequences=False),
                    Dropout(0.15),
                    Dense(32, activation='relu'),
                    Dense(1)
                ])
                lstm.compile(optimizer=Adam(learning_rate=0.001), loss='mse')

                class ProgressCB(Callback):
                    def on_epoch_end(self, epoch, logs=None):
                        pct = 40 + int((epoch / 100) * 45)
                        pct = min(pct, 85)
                        progress_events.append({'percent': pct, 'stage': f'LSTM epoch {epoch+1} — val_loss: {logs.get("val_loss", 0):.6f}'})

                lstm.fit(
                    X_train, data['y_train'], epochs=100, batch_size=32,
                    validation_data=(X_val, data['y_val']),
                    callbacks=[
                        EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True),
                        ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-5),
                        ProgressCB()
                    ], verbose=0
                )

                ls_pred = scaler.inverse_transform(lstm.predict(X_test, verbose=0))
                ls_actual = scaler.inverse_transform(data['y_test'].reshape(-1, 1))
                ls_mse = mean_squared_error(ls_actual, ls_pred)
                ls_rmse = np.sqrt(ls_mse)
                improvement = ((bl_rmse - ls_rmse) / bl_rmse) * 100

                progress_events.append({'percent': 90, 'stage': f'LSTM RMSE: {ls_rmse:.2f}. Saving models...'})

                # stage 5: save
                import joblib
                base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                models_dir = os.path.join(base, 'models')
                os.makedirs(models_dir, exist_ok=True)

                joblib.dump(baseline, os.path.join(models_dir, f'baseline_{ticker}.pkl'))
                lstm.save(os.path.join(models_dir, f'lstm_{ticker}.keras'))
                joblib.dump(scaler, os.path.join(models_dir, f'scaler_{ticker}.pkl'))

                bl_metrics_path = os.path.join(models_dir, 'baseline_metrics.pkl')
                ls_metrics_path = os.path.join(models_dir, 'lstm_metrics.pkl')
                bl_metrics = joblib.load(bl_metrics_path) if os.path.exists(bl_metrics_path) else {}
                ls_metrics = joblib.load(ls_metrics_path) if os.path.exists(ls_metrics_path) else {}
                bl_metrics[ticker] = {'mse': bl_mse, 'rmse': bl_rmse}
                ls_metrics[ticker] = {'mse': ls_mse, 'rmse': ls_rmse}
                joblib.dump(bl_metrics, bl_metrics_path)
                joblib.dump(ls_metrics, ls_metrics_path)

                progress_events.append({'percent': 100, 'stage': 'Training complete!'})

                result_holder[0] = {
                    'ticker': ticker,
                    'baseline_rmse': round(float(bl_rmse), 4),
                    'lstm_rmse': round(float(ls_rmse), 4),
                    'improvement_pct': round(float(improvement), 2),
                    'status': 'trained'
                }
            except Exception as e:
                error_holder[0] = str(e)

        thread = threading.Thread(target=run)
        thread.start()

        sent = 0
        while thread.is_alive():
            thread.join(timeout=0.5)
            while sent < len(progress_events):
                evt = progress_events[sent]
                yield f"data: {json.dumps({'type': 'progress', 'percent': evt['percent'], 'stage': evt['stage']})}\n\n"
                sent += 1

        while sent < len(progress_events):
            evt = progress_events[sent]
            yield f"data: {json.dumps({'type': 'progress', 'percent': evt['percent'], 'stage': evt['stage']})}\n\n"
            sent += 1

        if error_holder[0]:
            yield f"data: {json.dumps({'type': 'error', 'detail': error_holder[0]})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'result', 'data': result_holder[0]})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/predict")
def predict(ticker: str = Query(..., description="Stock ticker symbol")):
    """Get next-day prediction. Ticker must be trained first (use /train endpoint)."""
    ticker = ticker.upper().strip()

    try:
        result = get_prediction(ticker)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.get("/history")
def history(
    ticker: str = Query(..., description="Stock ticker symbol"),
    days: int = Query(90, description="Number of days")
):
    """Return historical closing prices from cached CSV data."""
    ticker = ticker.upper().strip()

    try:
        data = get_history(ticker, days)
        return {"ticker": ticker, "days": len(data), "history": data}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No cached data for {ticker}. Train it first to download data.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history-monthly")
def history_monthly(
    ticker: str = Query(..., description="Stock ticker symbol"),
    years: int = Query(10, description="Years of history")
):
    """Fetch monthly historical prices from Yahoo Finance for charting."""
    ticker = ticker.upper().strip()
    from realtime import _fetch_yahoo_chart, _PERIOD_MAP
    import requests as req

    try:
        range_str = f'{years}y' if years <= 10 else '10y'
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        params = {'range': range_str, 'interval': '1mo', 'includePrePost': 'false'}
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        resp = req.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        result = data.get('chart', {}).get('result')
        if not result:
            raise HTTPException(status_code=404, detail=f"No monthly data for {ticker}")

        chart = result[0]
        timestamps = chart.get('timestamp', [])
        closes = chart.get('indicators', {}).get('quote', [{}])[0].get('close', [])

        points = []
        for i, ts in enumerate(timestamps):
            if closes[i] is not None:
                from datetime import datetime
                dt = datetime.utcfromtimestamp(ts)
                points.append({
                    'date': dt.strftime('%Y-%m-%d'),
                    'price': round(float(closes[i]), 2)
                })

        return {"ticker": ticker, "count": len(points), "history": points}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
def metrics(ticker: str = Query(..., description="Stock ticker symbol")):
    """Return MSE and RMSE for both models."""
    ticker = ticker.upper().strip()

    try:
        data = get_metrics(ticker)
        return data
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/forecast")
def forecast(
    ticker: str = Query(..., description="Stock ticker symbol"),
    years: int = Query(10, description="Years to forecast (1-10)")
):
    """Generate long-term LSTM rolling forecast."""
    ticker = ticker.upper().strip()
    years = max(1, min(10, years))

    try:
        data = get_long_term_forecast(ticker, years)
        return data
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast failed: {str(e)}")


@app.get("/forecast-stream")
def forecast_stream(
    ticker: str = Query(..., description="Stock ticker symbol"),
    years: int = Query(10, description="Years to forecast (1-10)")
):
    """Stream forecast progress via Server-Sent Events, then send final result."""
    ticker = ticker.upper().strip()
    years = max(1, min(10, years))

    def generate():
        last_pct = [0]

        def on_progress(pct):
            if pct > last_pct[0]:
                last_pct[0] = pct
                yield f"data: {json.dumps({'type': 'progress', 'percent': pct})}\n\n"

        # we cant yield from inside the callback directly, so collect events
        progress_events = []

        def collect_progress(pct):
            if pct > (progress_events[-1] if progress_events else 0):
                progress_events.append(pct)

        try:
            # run forecast with progress tracking
            import threading
            result_holder = [None]
            error_holder = [None]

            def run_forecast():
                try:
                    result_holder[0] = get_long_term_forecast(ticker, years, collect_progress)
                except Exception as e:
                    error_holder[0] = str(e)

            thread = threading.Thread(target=run_forecast)
            thread.start()

            # stream progress while thread runs
            sent = 0
            while thread.is_alive():
                thread.join(timeout=0.3)
                while sent < len(progress_events):
                    pct = progress_events[sent]
                    yield f"data: {json.dumps({'type': 'progress', 'percent': pct})}\n\n"
                    sent += 1

            # send any remaining progress
            while sent < len(progress_events):
                pct = progress_events[sent]
                yield f"data: {json.dumps({'type': 'progress', 'percent': pct})}\n\n"
                sent += 1

            if error_holder[0]:
                yield f"data: {json.dumps({'type': 'error', 'detail': error_holder[0]})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'result', 'data': result_holder[0]})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

"""
main.py
FastAPI backend for the Stock Market Forecaster.
Supports any NASDAQ/US stock ticker with on-demand training.
Serves predictions, real-time data, historical data, and model metrics.

Mehmet Tanil Kaplan - T0429362
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

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
        raise HTTPException(status_code=404, detail=f"No data found for {ticker}. yfinance returned None.")
    if "error_debug" in data:
        raise HTTPException(status_code=404, detail=data["error_debug"])

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

# Real-Time Stock Market Forecaster

**Mehmet Tanil Kaplan - T0429362 - Nottingham Trent University**

A full-stack web application that fetches real-world stock data and uses machine learning to predict the next day's closing price. Compares a baseline Random Forest model against an LSTM deep learning network.

## Disclaimer

**For educational purposes only. This is not financial advice.**

## Tech Stack

- **Frontend:** React.js, Chart.js, Axios
- **Backend:** FastAPI (Python), uvicorn
- **ML Models:** scikit-learn (Random Forest baseline), TensorFlow/Keras (LSTM)
- **Data:** Yahoo Finance via yfinance
- **Database:** Supabase (prediction logging)

## Supported Tickers

AAPL, TSLA, MSFT, GOOGL, AMZN

## How to Run

### 1. Setup Python environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### 2. Fetch stock data (run once)

```bash
python fetch_data.py
```

### 3. Train models

```bash
python backend/train_baseline.py
python backend/train_lstm.py
```

### 4. Start backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 5. Start frontend

```bash
cd frontend
npm start
```

The app runs at http://localhost:3000 and talks to the API at http://localhost:8000.

## Project Structure

```
project/
├── data/              # cached CSV files per ticker
├── models/            # saved model files and scalers
├── notebooks/         # jupyter experiments
├── backend/
│   ├── main.py        # FastAPI app
│   ├── predict.py     # prediction logic
│   ├── preprocess.py  # data processing helpers
│   ├── train_baseline.py
│   ├── train_lstm.py
│   └── supabase_client.py
├── frontend/          # React app
├── fetch_data.py      # data download script
└── README.md
```

## API Endpoints

- `GET /tickers` - list supported tickers
- `GET /predict?ticker=AAPL` - get predictions from both models
- `GET /history?ticker=AAPL&days=90` - historical prices for charting
- `GET /metrics?ticker=AAPL` - MSE and RMSE for both models

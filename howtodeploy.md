# How to Deploy the Stock Forecaster

A complete step-by-step guide for building and hosting your own copy of this application — both locally for development and in the cloud for production.

**Mehmet Tanil Kaplan · T0429362 · Nottingham Trent University**

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Part A — Local Development Setup](#part-a--local-development-setup)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Set Up the Python Backend](#2-set-up-the-python-backend)
  - [3. Set Up the React Frontend](#3-set-up-the-react-frontend)
  - [4. Verify Everything Works Locally](#4-verify-everything-works-locally)
  - [5. Train Models Locally (Optional)](#5-train-models-locally-optional)
- [Part B — Cloud Deployment (Vercel + Render + Supabase)](#part-b--cloud-deployment-vercel--render--supabase)
  - [6. Push to Your Own GitHub Repository](#6-push-to-your-own-github-repository)
  - [7. Set Up Supabase (Database)](#7-set-up-supabase-database)
  - [8. Deploy the Backend on Render](#8-deploy-the-backend-on-render)
  - [9. Deploy the Frontend on Vercel](#9-deploy-the-frontend-on-vercel)
  - [10. Verify the Live Deployment](#10-verify-the-live-deployment)
- [Architecture Diagram](#architecture-diagram)
- [Important Notes & Limitations](#important-notes--limitations)
- [Adding More Pre-Trained Tickers](#adding-more-pre-trained-tickers)
- [Updating CORS Origins](#updating-cors-origins-optional)
- [Tech Stack Summary](#tech-stack-summary)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, make sure you have the following installed on your machine:

| Tool | Version | How to check | Download |
|------|---------|-------------|----------|
| **Git** | Any recent version | `git --version` | [git-scm.com](https://git-scm.com/) |
| **Python** | 3.10 or higher | `python --version` | [python.org](https://www.python.org/downloads/) |
| **pip** | Comes with Python | `pip --version` | Included with Python |
| **Node.js** | v18 or higher | `node --version` | [nodejs.org](https://nodejs.org/) |
| **npm** | Comes with Node.js | `npm --version` | Included with Node.js |

For cloud deployment, you will also need free accounts on:

| Service | Purpose | Sign up |
|---------|---------|---------|
| **GitHub** | Source code hosting & auto-deploy trigger | [github.com](https://github.com/) |
| **Render** | Backend API hosting (Docker) | [render.com](https://render.com/) |
| **Vercel** | Frontend static site hosting | [vercel.com](https://vercel.com/) |
| **Supabase** *(optional)* | PostgreSQL database for prediction logging | [supabase.com](https://supabase.com/) |

---

# Part A — Local Development Setup

This section gets the application running on your own machine. This is useful for development, testing, and understanding how the system works before deploying to the cloud.

## 1. Clone the Repository

Open a terminal and run:

```bash
git clone https://github.com/ukProject111/Stock-forecaster.git
cd Stock-forecaster
```

You should now have the full project with this structure:

```
Stock-forecaster/
├── backend/          ← Python FastAPI server + ML training scripts
├── frontend/         ← React.js dashboard
├── data/             ← Cached CSV stock data (AAPL, TSLA, etc.)
├── models/           ← Pre-trained ML model files (.pkl, .keras)
├── Dockerfile        ← Docker config for Render deployment
├── render.yaml       ← Render service configuration
└── README.md
```

## 2. Set Up the Python Backend

### 2.1 Create a Virtual Environment (Recommended)

A virtual environment keeps this project's dependencies separate from your system Python:

```bash
# Create the virtual environment
python -m venv venv

# Activate it
# On macOS / Linux:
source venv/bin/activate

# On Windows (Command Prompt):
venv\Scripts\activate

# On Windows (PowerShell):
venv\Scripts\Activate.ps1
```

You should see `(venv)` at the start of your terminal prompt.

### 2.2 Install Python Dependencies

```bash
pip install -r backend/requirements.txt
```

This installs FastAPI, TensorFlow, scikit-learn, pandas, and all other backend dependencies. The first install may take 3-5 minutes as TensorFlow is a large package.

### 2.3 Start the Backend Server

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- `--reload` enables auto-restart when you edit code (development only)
- `--host 0.0.0.0` makes the server accessible on your network
- `--port 8000` runs on port 8000

You should see output like:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### 2.4 Test the Backend

Open your browser and visit:

- **API Status:** [http://localhost:8000/](http://localhost:8000/) — should return `{"status": "running", "version": "2.0.0"}`
- **Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs) — interactive API explorer where you can test all endpoints
- **Quick test:** [http://localhost:8000/predict?ticker=AAPL](http://localhost:8000/predict?ticker=AAPL) — should return baseline and LSTM predictions

> **Leave this terminal running.** Open a new terminal window for the frontend.

## 3. Set Up the React Frontend

### 3.1 Install Node.js Dependencies

In a **new terminal**, from the project root:

```bash
cd frontend
npm install
```

This installs React, Chart.js, Axios, and all frontend dependencies. Takes 1-2 minutes.

### 3.2 Start the Development Server

```bash
npm start
```

This will:
- Start the React development server on [http://localhost:3000](http://localhost:3000)
- Automatically open your browser
- Connect to the backend at `http://localhost:8000` (the default fallback)

You should see the Stock Forecaster dashboard with a dark theme.

### 3.3 How the Frontend Connects to the Backend

The frontend reads the API URL from an environment variable:

```javascript
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

- **Locally:** No configuration needed — it defaults to `http://localhost:8000`
- **In production:** The environment variable `REACT_APP_API_URL` must be set to your Render backend URL

## 4. Verify Everything Works Locally

With both the backend (port 8000) and frontend (port 3000) running, test these features:

| Test | How | Expected Result |
|------|-----|-----------------|
| **Page loads** | Open [http://localhost:3000](http://localhost:3000) | Dashboard appears with disclaimer banner |
| **Ticker list loads** | Check the ticker search box | Should show 435+ tickers |
| **Live Chart** | Select AAPL, click the "1D" or "5D" button | Real-time price chart appears |
| **ML Prediction** | Select AAPL, click "Run ML Analysis" | Baseline and LSTM predictions shown |
| **Model Metrics** | Click the "Model Metrics" tab | MSE/RMSE comparison with improvement % |
| **10-Year Forecast** | Click the "10-Year Forecast" tab, then "Generate" | Forecast chart with confidence bands |
| **Search** | Type "Tesla" in the search box | Tesla Inc. (TSLA) appears in dropdown |
| **Untrained ticker** | Select NVDA | Live Chart works, "Train ML Models" button appears |
| **API Swagger** | Visit [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive API documentation |

## 5. Train Models Locally (Optional)

The repository includes pre-trained models for 5 tickers (AAPL, TSLA, MSFT, GOOGL, AMZN). If you want to train additional tickers or retrain existing ones:

### 5.1 Download Stock Data

```bash
python fetch_data.py
```

This downloads 10+ years of historical data from Yahoo Finance and saves CSV files in `data/`.

### 5.2 Train All Models

```bash
cd backend

# Train baseline models (Random Forest) — takes ~2 minutes
python train_baseline.py

# Train LSTM models (Deep Learning) — takes ~5-10 minutes
python train_lstm.py
```

### 5.3 Train a Single Ticker On-Demand

```bash
cd backend
python -c "from train_on_demand import train_ticker; train_ticker('NVDA')"
```

This downloads data, trains both models, and saves everything in ~1-2 minutes.

### 5.4 Verify Training Results

```bash
# Check model files exist
ls -la ../models/

# Test predictions via API
curl http://localhost:8000/predict?ticker=NVDA
curl http://localhost:8000/metrics?ticker=NVDA
```

---

# Part B — Cloud Deployment (Vercel + Render + Supabase)

This section deploys the application to the cloud so anyone can access it via a public URL.

```
┌─────────────────────────────────────────────────────────────────┐
│                     DEPLOYMENT OVERVIEW                         │
│                                                                 │
│   GitHub ──push──> Render (Backend)   ← Docker + FastAPI + ML  │
│     │                   │                                       │
│     │              API URL                                      │
│     │                   │                                       │
│     └──push──> Vercel (Frontend)      ← React + Chart.js       │
│                    │                                            │
│               Supabase (Database)     ← PostgreSQL (optional)   │
└─────────────────────────────────────────────────────────────────┘
```

## 6. Push to Your Own GitHub Repository

### 6.1 Create a New Repository on GitHub

1. Go to [github.com/new](https://github.com/new)
2. Name it something like `my-stock-forecaster`
3. Set it to **Public** (required for free Render/Vercel deployment)
4. Do **not** initialise with README (you already have one)
5. Click **Create repository**

### 6.2 Push Your Code

```bash
# Remove the original remote
git remote remove origin

# Add your own repository as the remote
git remote add origin https://github.com/YOUR_USERNAME/my-stock-forecaster.git

# Push all code
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

### 6.3 Verify on GitHub

Visit `https://github.com/YOUR_USERNAME/my-stock-forecaster` and confirm all files are there, including the `models/`, `data/`, `backend/`, and `frontend/` directories.

> **Important:** The `models/` and `data/` directories must be in the repository. Render needs them to serve predictions. If they are in `.gitignore`, remove them.

## 7. Set Up Supabase (Database)

Supabase provides a free PostgreSQL database for logging predictions. This step is **optional** — the app works without it.

### 7.1 Create a Supabase Project

1. Go to [supabase.com](https://supabase.com/) and sign in (GitHub login works)
2. Click **New Project**
3. Fill in:
   - **Name:** `stock-forecaster`
   - **Database Password:** Choose a strong password (save it somewhere safe)
   - **Region:** Choose the closest to your users
4. Click **Create new project** — wait 1-2 minutes for setup

### 7.2 Create the Prediction Logs Table

1. In your Supabase dashboard, go to **SQL Editor** (left sidebar)
2. Click **New query** and paste this SQL:

```sql
CREATE TABLE prediction_logs (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    baseline_prediction DECIMAL(12, 4),
    lstm_prediction DECIMAL(12, 4),
    last_close DECIMAL(12, 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security (Supabase requirement)
ALTER TABLE prediction_logs ENABLE ROW LEVEL SECURITY;

-- Allow anonymous inserts and reads (for the API)
CREATE POLICY "Allow anonymous inserts"
    ON prediction_logs FOR INSERT
    TO anon
    WITH CHECK (true);

CREATE POLICY "Allow anonymous reads"
    ON prediction_logs FOR SELECT
    TO anon
    USING (true);
```

3. Click **Run** — you should see "Success. No rows returned."

### 7.3 Get Your Supabase Credentials

1. Go to **Settings** > **API** in the Supabase dashboard
2. Copy these two values (you will need them for Render):

| Credential | Where to find it | Example |
|------------|-----------------|---------|
| **Project URL** | Under "Project URL" | `https://abcdefg.supabase.co` |
| **Anon public key** | Under "Project API keys" → `anon` `public` | `eyJhbGci...` (long JWT string) |

> **Keep these safe.** The anon key is public-facing but you should still treat it carefully.

## 8. Deploy the Backend on Render

Render hosts the Python FastAPI backend as a Docker container.

### 8.1 Create the Web Service

1. Go to [render.com](https://render.com/) and sign in
2. Click **New** > **Web Service**
3. Choose **Build and deploy from a Git repository** and click **Next**
4. Connect your GitHub account if not already connected
5. Find and select your `my-stock-forecaster` repository

### 8.2 Configure the Service

Fill in these settings:

| Setting | Value | Notes |
|---------|-------|-------|
| **Name** | `stock-forecaster-api` | This becomes part of your URL |
| **Region** | Choose closest to you | e.g. `Oregon (US West)` or `Frankfurt (EU Central)` |
| **Branch** | `main` | The branch to auto-deploy from |
| **Root Directory** | *(leave blank)* | The Dockerfile is at the repo root |
| **Runtime** | `Docker` | **Important:** Select Docker, not Python |
| **Dockerfile Path** | `./Dockerfile` | Should auto-detect |
| **Instance Type** | `Free` | $0/month, includes 750 hours |

### 8.3 Add Environment Variables

Scroll down to **Environment Variables** and add:

| Key | Value | Required? |
|-----|-------|-----------|
| `SUPABASE_URL` | Your Supabase Project URL from Step 7.3 | Optional |
| `SUPABASE_KEY` | Your Supabase anon public key from Step 7.3 | Optional |

> If you skip Supabase, the app works fine — prediction logging will be silently disabled.

### 8.4 Deploy

1. Click **Create Web Service**
2. Render will:
   - Clone your repository
   - Build the Docker image (installs Python, TensorFlow, etc.)
   - Start the FastAPI server
3. **Wait 5-10 minutes** for the first build — TensorFlow is large
4. Once you see **"Your service is live"**, copy your URL:

```
https://stock-forecaster-api-xxxx.onrender.com
```

### 8.5 Verify the Backend is Running

Open your Render URL in the browser. You should see:

```json
{
    "status": "running",
    "version": "2.0.0",
    "message": "Stock Market Forecaster API - supports all NASDAQ tickers",
    "disclaimer": "For educational purposes only. Not financial advice."
}
```

Test a prediction:

```
https://stock-forecaster-api-xxxx.onrender.com/predict?ticker=AAPL
```

You should get a JSON response with `baseline_prediction` and `lstm_prediction`.

## 9. Deploy the Frontend on Vercel

Vercel hosts the React frontend as a static site with automatic builds.

### 9.1 Import the Project

1. Go to [vercel.com](https://vercel.com/) and sign in
2. Click **Add New** > **Project**
3. Click **Import** next to your `my-stock-forecaster` GitHub repository

### 9.2 Configure the Build

| Setting | Value | Notes |
|---------|-------|-------|
| **Framework Preset** | `Create React App` | Vercel auto-detects this |
| **Root Directory** | `frontend` | **Important:** Click "Edit" and type `frontend` |
| **Build Command** | `npm run build` | Default for Create React App |
| **Output Directory** | `build` | Default for Create React App |

### 9.3 Add the Environment Variable

This is the **most critical step**. Without this, the frontend will not connect to the backend.

Click **Environment Variables** and add:

| Key | Value |
|-----|-------|
| `REACT_APP_API_URL` | `https://stock-forecaster-api-xxxx.onrender.com` |

Replace `xxxx` with your actual Render URL from Step 8.4.

> **Why this matters:** React bakes environment variables into the JavaScript bundle at build time. If this is wrong or missing, the frontend will try to connect to `http://localhost:8000` and fail.

### 9.4 Deploy

1. Click **Deploy**
2. Vercel will install dependencies, build the React app, and deploy it
3. Wait 1-2 minutes
4. Once complete, you'll get a URL like:

```
https://my-stock-forecaster.vercel.app
```

### 9.5 Auto-Deploy

Vercel automatically redeploys when you push to the `main` branch on GitHub. You can also trigger a manual redeploy from the Vercel dashboard under **Deployments** > **Redeploy**.

## 10. Verify the Live Deployment

Open your Vercel URL in the browser and run through this checklist:

### Functional Tests

| # | Test | Steps | Expected Result |
|---|------|-------|-----------------|
| 1 | **Page loads** | Open the Vercel URL | Dashboard loads with dark theme and disclaimer banner |
| 2 | **Ticker list** | Click the search box | 435+ tickers listed with company names |
| 3 | **Live Chart** | Select AAPL → Live Chart tab | Real-time price chart with period selectors (1D–5Y) |
| 4 | **ML Prediction** | Select AAPL → Click "Run ML Analysis" | Baseline and LSTM predictions shown with price chart |
| 5 | **Model Metrics** | Click "Model Metrics" tab | MSE/RMSE comparison, improvement ≥ 10% |
| 6 | **10-Year Forecast** | Click "10-Year Forecast" → "Generate 10Y" | Forecast chart with confidence bands |
| 7 | **Search** | Type "Tesla" in search box | TSLA appears, clickable without glitches |
| 8 | **UK stocks** | Search "Shell" | SHEL.L (LSE) and SHEL (US) appear |
| 9 | **On-demand training** | Select NVDA → Click "Train ML Models" | Progress bar, then predictions auto-load |
| 10 | **All 5 tickers** | Test AAPL, TSLA, MSFT, GOOGL, AMZN | All show predictions, metrics, and forecasts |

### API Tests (Optional)

Test the backend directly using curl or your browser:

```bash
# API status
curl https://your-api.onrender.com/

# List trained tickers
curl https://your-api.onrender.com/trained

# Get prediction
curl https://your-api.onrender.com/predict?ticker=AAPL

# Get metrics (check LSTM improvement ≥ 10%)
curl https://your-api.onrender.com/metrics?ticker=AAPL

# Search tickers
curl https://your-api.onrender.com/search?q=Microsoft

# Real-time data
curl https://your-api.onrender.com/realtime?ticker=NVDA&period=5d
```

---

## Architecture Diagram

```
┌────────────────────┐     ┌──────────────────────────────────┐
│   User's Browser   │     │         Vercel (Frontend)        │
│                    │────>│  React 19 + Chart.js + Axios     │
│  build-alpha-steel │     │  Static site, auto-deploys from  │
│  .vercel.app       │     │  GitHub on every push to main    │
└────────────────────┘     └──────────┬───────────────────────┘
                                      │
                                      │ HTTPS API calls
                                      │ (REACT_APP_API_URL)
                                      ▼
                           ┌──────────────────────────────────┐
                           │       Render (Backend)            │
                           │  Docker → Python 3.11 + FastAPI   │
                           │                                   │
                           │  ┌─────────┐  ┌───────────────┐  │
                           │  │ Models   │  │ Data (CSV)    │  │
                           │  │ .pkl     │  │ AAPL.csv      │  │
                           │  │ .keras   │  │ TSLA.csv ...  │  │
                           │  └─────────┘  └───────────────┘  │
                           │                                   │
                           │  Endpoints: /predict, /history,   │
                           │  /metrics, /realtime, /train,     │
                           │  /search, /forecast ...           │
                           └──────────┬───────────────────────┘
                                      │
                          ┌───────────┤
                          │           │
                          ▼           ▼
               ┌─────────────┐  ┌──────────────────┐
               │Yahoo Finance│  │  Supabase (DB)   │
               │  Live OHLCV │  │  prediction_logs  │
               │  Price Data  │  │  (optional)      │
               └─────────────┘  └──────────────────┘
```

---

## Important Notes & Limitations

### Render Free Tier

| Limitation | Impact | Workaround |
|------------|--------|------------|
| **Sleeps after 15 min** of inactivity | First request takes 30-60 seconds to wake up | Users see a loading state; consider upgrading to Starter ($7/month) for always-on |
| **Ephemeral storage** | On-demand trained models are lost on server restart | Pre-train important tickers locally and commit to `models/` |
| **512 MB RAM** | Training large models may fail | The 5 pre-trained models work fine; on-demand training uses CPU efficiently |
| **750 free hours/month** | Enough for one always-running service | Free tier is sufficient for a demo/educational project |

### Vercel Free Tier

| Limitation | Impact | Workaround |
|------------|--------|------------|
| **100 deployments/day** | More than enough for development | N/A |
| **Serverless functions timeout: 10s** | Not applicable — we use static site mode | N/A |
| **100 GB bandwidth/month** | More than enough for a demo app | N/A |

### Supabase Free Tier

| Limitation | Impact | Workaround |
|------------|--------|------------|
| **500 MB database** | Plenty for prediction logs | N/A |
| **Pauses after 1 week** of inactivity | Logging fails silently (app still works) | Visit the Supabase dashboard periodically to keep it active |
| **50,000 monthly active users** | More than enough | N/A |

### Pre-Trained vs On-Demand Models

| | Pre-Trained (AAPL, TSLA, MSFT, GOOGL, AMZN) | On-Demand (any other ticker) |
|---|---|---|
| **Survives restart?** | Yes — baked into Docker image | No — stored in ephemeral memory |
| **Prediction speed** | Instant (models cached in RAM) | Instant after training completes |
| **Training time** | Done offline before deployment | ~1-2 minutes per ticker |
| **Availability** | Always available | Lost when Render restarts |

---

## Adding More Pre-Trained Tickers

To permanently add a new ticker so it survives Render restarts:

### Step 1 — Download the Data

```bash
cd backend
python -c "
from train_on_demand import download_data
download_data('NVDA')
print('Done! Check data/NVDA.csv')
"
```

### Step 2 — Train the Models

```bash
python -c "
from train_on_demand import train_ticker
result = train_ticker('NVDA')
print(f'Baseline RMSE: {result[\"baseline_rmse\"]}')
print(f'LSTM RMSE: {result[\"lstm_rmse\"]}')
print(f'Improvement: {result[\"improvement_pct\"]}%')
"
```

### Step 3 — Commit and Push

```bash
cd ..
git add data/NVDA.csv models/baseline_NVDA.pkl models/lstm_NVDA.keras models/scaler_NVDA.pkl
git commit -m "Add pre-trained models for NVDA"
git push
```

Render will auto-redeploy with NVDA permanently available.

---

## Updating CORS Origins (Optional)

By default, the backend allows requests from any origin (`allow_origins=["*"]`). For production, you may want to restrict this to only your Vercel domain.

Edit `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://my-stock-forecaster.vercel.app",  # your Vercel URL
        "http://localhost:3000",                     # local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Tech Stack Summary

| Component | Technology | Version | Hosting | Cost |
|-----------|-----------|---------|---------|------|
| **Frontend** | React.js, Chart.js, Axios | React 19 | Vercel | Free |
| **Backend API** | FastAPI, uvicorn | Python 3.11 | Render | Free |
| **Baseline Model** | scikit-learn (Random Forest) | 1.3.2 | Render | — |
| **LSTM Model** | TensorFlow / Keras | 2.21.0 | Render | — |
| **Market Data** | Yahoo Finance (direct API) | — | — | Free |
| **Database** | Supabase (PostgreSQL) | — | Supabase | Free |
| **Containerisation** | Docker | Python 3.11-slim | Render | — |
| **Version Control** | Git + GitHub | — | GitHub | Free |

**Total hosting cost: $0/month** (all free tiers)

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| **"Failed to fetch"** on first load | Render free tier is waking up from sleep | Wait 30-60 seconds and refresh the page |
| **Frontend shows blank page** | `REACT_APP_API_URL` not set or wrong | Check Vercel environment variables; redeploy after changing |
| **CORS errors in browser console** | Backend doesn't allow the frontend's origin | Ensure `allow_origins=["*"]` in `backend/main.py` |
| **"Training failed"** error | Backend timed out or ticker has too little data | Check if the stock has 80+ trading days of history |
| **Models disappear after training** | Render's ephemeral storage wiped on restart | Train locally and commit to `models/` for permanent tickers |
| **Predictions return wrong prices** | Scaler mismatch or corrupted model files | Retrain the ticker: delete old model files and train again |
| **"No trained models for X"** | Server restarted and lost on-demand models | Retrain the ticker, or add it as a pre-trained ticker (see above) |
| **Supabase logging not working** | Missing env vars or table not created | Check `SUPABASE_URL` and `SUPABASE_KEY` on Render; run the SQL from Step 7.2 |
| **Build fails on Render** | Dependencies or Docker issue | Check Render build logs; ensure `requirements.txt` is up to date |
| **Build fails on Vercel** | Root directory not set to `frontend` | Check Vercel project settings → Root Directory = `frontend` |
| **npm install fails locally** | Node.js version too old | Upgrade to Node.js v18+ |
| **TensorFlow import error** | Wrong Python version or missing dependencies | Use Python 3.10-3.11; run `pip install -r backend/requirements.txt` |
| **Chart not rendering** | Chart.js not installed or version mismatch | Run `cd frontend && npm install` |
| **API returns 404 for /predict** | Ticker not trained | Use a pre-trained ticker (AAPL, TSLA, MSFT, GOOGL, AMZN) or train first |

---

*Mehmet Tanil Kaplan · T0429362 · Nottingham Trent University · 2025-2026*

# How to Deploy the Stock Forecaster

A step-by-step guide for building and hosting your own copy of this application.

---

## Prerequisites

- [Git](https://git-scm.com/)
- [Node.js](https://nodejs.org/) v18+ and npm
- [Python](https://www.python.org/) 3.11+
- A free [GitHub](https://github.com/) account
- A free [Render](https://render.com/) account (backend hosting)
- A free [Vercel](https://vercel.com/) account (frontend hosting)
- (Optional) A free [Supabase](https://supabase.com/) account (prediction logging)

---

## 1. Clone the Repository

```bash
git clone https://github.com/ukProject111/Stock-forecaster.git
cd Stock-forecaster
```

---

## 2. Run Locally (Test Before Deploying)

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be running at `http://localhost:8000`. Visit `http://localhost:8000/docs` for the interactive Swagger UI.

### Frontend

Open a new terminal:

```bash
cd frontend
npm install
npm start
```

The React app will open at `http://localhost:3000` and automatically connect to `http://localhost:8000`.

### Verify

- Open `http://localhost:3000` in your browser
- Select a pre-trained ticker (AAPL, TSLA, MSFT, GOOGL, or AMZN)
- Click "Run ML Analysis" to check predictions work
- Try the Live Chart tab with any ticker

---

## 3. Push to Your Own GitHub Repository

```bash
# Create a new repo on GitHub (e.g. "my-stock-forecaster"), then:
git remote set-url origin https://github.com/YOUR_USERNAME/my-stock-forecaster.git
git push -u origin main
```

---

## 4. Deploy the Backend on Render

1. Go to [render.com](https://render.com/) and sign in
2. Click **New** > **Web Service**
3. Connect your GitHub account and select your repository
4. Configure the service:

| Setting            | Value                                          |
|--------------------|------------------------------------------------|
| **Name**           | `stock-forecaster-api`                         |
| **Region**         | Choose the closest to you                      |
| **Branch**         | `main`                                         |
| **Root Directory** | *(leave blank)*                                |
| **Runtime**        | `Docker`                                       |
| **Instance Type**  | `Free`                                         |

5. (Optional) Add environment variables under **Environment**:

| Key              | Value                           |
|------------------|---------------------------------|
| `SUPABASE_URL`   | Your Supabase project URL       |
| `SUPABASE_KEY`   | Your Supabase anon key          |

> Supabase is optional. The app works without it — prediction logging will just be disabled.

6. Click **Create Web Service**

7. Wait for the build to finish (5-10 minutes for the first deploy). Once live, you'll get a URL like:
   ```
   https://stock-forecaster-api-xxxx.onrender.com
   ```
   Copy this URL — you'll need it for the frontend.

---

## 5. Deploy the Frontend on Vercel

1. Go to [vercel.com](https://vercel.com/) and sign in
2. Click **Add New** > **Project**
3. Import your GitHub repository
4. Configure the project:

| Setting              | Value            |
|----------------------|------------------|
| **Framework Preset** | `Create React App` |
| **Root Directory**   | `frontend`       |
| **Build Command**    | `npm run build`  |
| **Output Directory** | `build`          |

5. Add the environment variable (this is the critical step):

| Key                  | Value                                          |
|----------------------|------------------------------------------------|
| `REACT_APP_API_URL`  | `https://stock-forecaster-api-xxxx.onrender.com` |

> Replace `xxxx` with your actual Render URL from Step 4.

6. Click **Deploy**

7. Once deployed, you'll get a URL like `https://my-stock-forecaster.vercel.app`

---

## 6. Verify the Live Deployment

Open your Vercel URL in the browser and check:

- [ ] The page loads without errors
- [ ] Select AAPL and click **Run ML Analysis** — predictions should appear
- [ ] Try the **Live Chart** tab — real-time data should load for any ticker
- [ ] Try the **10-Year Forecast** tab
- [ ] Search for a stock by company name (e.g. "Tesla")
- [ ] Train a new ticker (e.g. NVDA) — should complete in ~1-2 minutes

---

## Important Notes

### Render Free Tier Limitations

- The backend **sleeps after 15 minutes** of inactivity. The first request after sleep takes 30-60 seconds.
- Storage is **ephemeral** — on-demand trained models (anything besides AAPL, TSLA, MSFT, GOOGL, AMZN) will be lost when the server restarts.
- The 5 pre-trained models survive restarts because they are baked into the Docker image.

### Adding More Pre-Trained Tickers

To permanently include a ticker in the Docker image:

```bash
# Train locally
cd backend
python train_baseline.py    # trains all tickers in data/
python train_lstm.py         # trains LSTM for all tickers in data/

# Or download data and train a specific one
python -c "
from train_on_demand import download_data, prepare_data
import pandas as pd
download_data('NVDA')
"
python train_baseline.py
python train_lstm.py
```

Then commit the new files in `models/` and `data/`, push to GitHub, and Render will redeploy with the new models included.

### Updating the CORS Origin (Optional)

The backend currently allows all origins (`allow_origins=["*"]`). To restrict it to only your Vercel domain, edit `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Setting Up Supabase (Optional)

1. Create a free project at [supabase.com](https://supabase.com/)
2. Create a table called `predictions` with columns: `id`, `ticker`, `baseline_pred`, `lstm_pred`, `actual`, `timestamp`
3. Copy the **Project URL** and **anon public key** from Settings > API
4. Add them as environment variables on Render (see Step 4)

---

## Tech Stack Summary

| Component       | Technology                          | Hosting  |
|-----------------|-------------------------------------|----------|
| Frontend        | React 19, Chart.js, Axios           | Vercel   |
| Backend API     | FastAPI, Python 3.11                | Render   |
| ML Models       | TensorFlow/Keras LSTM, scikit-learn | Render   |
| Market Data     | Yahoo Finance API                   | -        |
| Database        | Supabase (PostgreSQL)               | Supabase |
| Containerisation| Docker                              | Render   |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Failed to fetch" on first load | Render free tier is waking up. Wait 30-60 seconds and refresh. |
| Training fails for a ticker | Check if the stock has enough history (needs 80+ trading days). |
| Models disappear after training | Render's ephemeral storage. Train locally and commit to `models/` for permanent tickers. |
| Frontend shows blank page | Check that `REACT_APP_API_URL` is set correctly in Vercel environment variables. |
| CORS errors in browser console | Make sure the backend `allow_origins` includes your Vercel domain (default: all origins). |

---

*Mehmet Tanil Kaplan - T0429362 - Nottingham Trent University*

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Disclaimer from './components/Disclaimer';
import TickerSelector from './components/TickerSelector';
import RealTimeChart from './components/RealTimeChart';
import PriceChart from './components/PriceChart';
import PredictionPanel from './components/PredictionPanel';
import MetricsPanel from './components/MetricsPanel';
import ForecastPanel from './components/ForecastPanel';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [allTickers, setAllTickers] = useState([]);
  const [trainedTickers, setTrainedTickers] = useState([]);
  const [selectedTicker, setSelectedTicker] = useState('AAPL');
  const [history, setHistory] = useState([]);
  const [prediction, setPrediction] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(false);
  const [training, setTraining] = useState(false);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [forecastProgress, setForecastProgress] = useState(0);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('realtime');
  const [trainStatus, setTrainStatus] = useState('');

  // fetch ticker list on load
  useEffect(() => {
    axios.get(`${API_URL}/tickers`)
      .then(res => {
        setAllTickers(res.data.all_tickers || []);
        setTrainedTickers(res.data.trained || []);
      })
      .catch(err => {
        console.error('Failed to load tickers:', err);
        setError('Could not connect to the API. Is the backend running?');
      });
  }, []);

  const isTrained = trainedTickers.includes(selectedTicker);

  // handle ticker change
  const handleTickerChange = (ticker) => {
    setSelectedTicker(ticker);
    setPrediction(null);
    setMetrics(null);
    setHistory([]);
    setForecast(null);
    setError('');
    setTrainStatus('');
    setActiveTab('realtime');
  };

  // train a new ticker on demand with real-time SSE progress
  const handleTrain = async () => {
    if (!selectedTicker) return;
    setTraining(true);
    setError('');
    setTrainStatus(`Connecting to server...`);

    try {
      const url = `${API_URL}/train-stream?ticker=${selectedTicker}`;
      const response = await fetch(url);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const msg = JSON.parse(line.slice(6));
            if (msg.type === 'progress') {
              setTrainStatus(`[${msg.percent}%] ${msg.stage}`);
            } else if (msg.type === 'result') {
              const d = msg.data;
              if (d.status === 'already_trained') {
                setTrainStatus(`${selectedTicker} is already trained and ready!`);
              } else {
                const imp = d.improvement_pct != null ? d.improvement_pct.toFixed(1) : '—';
                setTrainStatus(`${selectedTicker} trained! Baseline RMSE: ${d.baseline_rmse} | LSTM RMSE: ${d.lstm_rmse} | Improvement: ${imp}%`);
              }
              // refresh trained list
              const tickerRes = await axios.get(`${API_URL}/tickers`);
              setTrainedTickers(tickerRes.data.trained || []);
            } else if (msg.type === 'error') {
              setError(msg.detail);
              setTrainStatus('');
            }
          } catch (e) { /* skip bad lines */ }
        }
      }
    } catch (err) {
      setError('Training failed. Backend may be starting up — try again.');
      setTrainStatus('');
    } finally {
      setTraining(false);
    }
  };

  // run ML prediction (requires trained ticker)
  const handlePredict = async () => {
    if (!selectedTicker || !isTrained) return;
    setLoading(true);
    setError('');
    setPrediction(null);
    setMetrics(null);
    setHistory([]);
    setActiveTab('predict');

    try {
      const [histRes, predRes, metRes] = await Promise.all([
        axios.get(`${API_URL}/history?ticker=${selectedTicker}&days=90`),
        axios.get(`${API_URL}/predict?ticker=${selectedTicker}`),
        axios.get(`${API_URL}/metrics?ticker=${selectedTicker}`)
      ]);
      setHistory(histRes.data.history);
      setPrediction(predRes.data);
      setMetrics(metRes.data);
    } catch (err) {
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Prediction failed. Check if the backend is running.');
      }
    } finally {
      setLoading(false);
    }
  };

  // 10-year forecast with real-time progress via SSE
  const handleForecast = async (years) => {
    if (!selectedTicker || !isTrained) return;
    setForecastLoading(true);
    setForecastProgress(0);
    setError('');
    setActiveTab('forecast');

    try {
      const url = `${API_URL}/forecast-stream?ticker=${selectedTicker}&years=${years}`;
      const response = await fetch(url);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const msg = JSON.parse(line.slice(6));
            if (msg.type === 'progress') {
              setForecastProgress(msg.percent);
            } else if (msg.type === 'result') {
              setForecast(msg.data);
            } else if (msg.type === 'error') {
              setError(msg.detail);
            }
          } catch (e) { /* skip bad lines */ }
        }
      }
    } catch (err) {
      setError('Forecast failed. Backend may be starting up — try again.');
    } finally {
      setForecastLoading(false);
      setForecastProgress(0);
    }
  };

  return (
    <div className="App">
      <Disclaimer />

      <header className="app-header">
        <div className="header-badge">Neural Network Powered</div>
        <h1>STOCK FORECASTER</h1>
        <p className="subtitle">
          Real-Time Market Data &amp; LSTM Deep Learning Predictions | {allTickers.length}+ Stocks
        </p>
      </header>

      <main className="main-content">
        {/* Controls row */}
        <div className="controls">
          <TickerSelector
            tickers={allTickers}
            trainedTickers={trainedTickers}
            selected={selectedTicker}
            onChange={handleTickerChange}
          />

          {!isTrained && (
            <button
              className="predict-btn"
              onClick={handleTrain}
              disabled={training || !selectedTicker}
              style={{
                background: training
                  ? '#64748b'
                  : 'linear-gradient(135deg, #a855f7, #ec4899)',
              }}
            >
              {training ? 'Training...' : 'Train ML Models'}
            </button>
          )}

          {isTrained && (
            <button
              className={`predict-btn ${loading ? 'loading' : ''}`}
              onClick={handlePredict}
              disabled={loading}
            >
              {loading ? 'Analysing...' : 'Run ML Analysis'}
            </button>
          )}
        </div>

        {/* Training status with progress */}
        {trainStatus && (
          <div style={{
            textAlign: 'center',
            padding: '12px 16px',
            marginBottom: '16px',
            background: training ? 'rgba(168,85,247,0.1)' : 'rgba(0,255,136,0.1)',
            border: `1px solid ${training ? 'rgba(168,85,247,0.3)' : 'rgba(0,255,136,0.3)'}`,
            borderRadius: '4px',
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: '0.75rem',
            color: training ? '#a855f7' : '#00ff88',
            letterSpacing: '0.5px',
          }}>
            {training && <span className="spinner" style={{
              display: 'inline-block', width: '14px', height: '14px',
              borderWidth: '2px', marginRight: '8px', verticalAlign: 'middle'
            }}></span>}
            {trainStatus}
            {training && trainStatus.match(/\[(\d+)%\]/) && (
              <div style={{
                width: '100%', maxWidth: '300px', height: '5px',
                background: 'rgba(168,85,247,0.15)', borderRadius: '3px',
                margin: '10px auto 0', overflow: 'hidden'
              }}>
                <div style={{
                  width: `${trainStatus.match(/\[(\d+)%\]/)[1]}%`, height: '100%',
                  background: 'linear-gradient(90deg, #a855f7, #ec4899)',
                  borderRadius: '3px', transition: 'width 0.4s ease-out'
                }} />
              </div>
            )}
          </div>
        )}

        {error && <div className="error-box"><p>{error}</p></div>}

        {/* Ticker status badges */}
        {selectedTicker && (
          <div style={{
            display: 'flex', gap: '8px', justifyContent: 'center',
            marginBottom: '20px', flexWrap: 'wrap'
          }}>
            <span style={{
              padding: '4px 12px', borderRadius: '3px',
              fontFamily: "'Share Tech Mono', monospace", fontSize: '0.65rem',
              letterSpacing: '1px', textTransform: 'uppercase',
              background: 'rgba(0,240,255,0.1)', border: '1px solid rgba(0,240,255,0.2)',
              color: '#00f0ff'
            }}>
              {selectedTicker}
            </span>
            <span style={{
              padding: '4px 12px', borderRadius: '3px',
              fontFamily: "'Share Tech Mono', monospace", fontSize: '0.65rem',
              letterSpacing: '1px',
              background: isTrained ? 'rgba(0,255,136,0.1)' : 'rgba(255,107,53,0.1)',
              border: `1px solid ${isTrained ? 'rgba(0,255,136,0.2)' : 'rgba(255,107,53,0.2)'}`,
              color: isTrained ? '#00ff88' : '#ff6b35'
            }}>
              {isTrained ? 'ML Models Ready' : 'Not Trained - Real-Time Only'}
            </span>
          </div>
        )}

        {/* Tab navigation */}
        <div className="tab-nav">
          <button
            className={`tab-btn ${activeTab === 'realtime' ? 'active' : ''}`}
            onClick={() => setActiveTab('realtime')}
          >
            Live Chart
          </button>
          {isTrained && (
            <>
              <button
                className={`tab-btn ${activeTab === 'predict' ? 'active' : ''}`}
                onClick={() => setActiveTab('predict')}
              >
                ML Prediction
              </button>
              <button
                className={`tab-btn ${activeTab === 'forecast' ? 'active' : ''}`}
                onClick={() => setActiveTab('forecast')}
              >
                10-Year Forecast
              </button>
              <button
                className={`tab-btn ${activeTab === 'metrics' ? 'active' : ''}`}
                onClick={() => setActiveTab('metrics')}
              >
                Model Metrics
              </button>
            </>
          )}
        </div>

        {/* Tab content */}
        {activeTab === 'realtime' && (
          <RealTimeChart ticker={selectedTicker} />
        )}

        {activeTab === 'predict' && (
          <>
            {loading && (
              <div className="loading-overlay">
                <div className="spinner"></div>
                <p className="loading-text">Processing neural networks...</p>
              </div>
            )}
            {!loading && prediction && <PredictionPanel prediction={prediction} />}
            {!loading && history.length > 0 && (
              <PriceChart history={history} prediction={prediction} ticker={selectedTicker} />
            )}
          </>
        )}

        {activeTab === 'forecast' && (
          <ForecastPanel
            ticker={selectedTicker}
            forecast={forecast}
            loading={forecastLoading}
            progress={forecastProgress}
            onForecast={handleForecast}
            startPrice={prediction ? prediction.last_close : null}
          />
        )}

        {activeTab === 'metrics' && metrics && (
          <MetricsPanel metrics={metrics} />
        )}
      </main>

      <footer className="app-footer">
        <p className="footer-brand">
          Mehmet Tanil Kaplan &middot; T0429362 &middot; Nottingham Trent University &middot; Supervisor: Williams Magdalena
        </p>
        <p className="disclaimer-small">
          For educational purposes only. This is not financial advice.
        </p>
      </footer>
    </div>
  );
}

export default App;

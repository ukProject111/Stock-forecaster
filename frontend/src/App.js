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

  // train a new ticker on demand
  const handleTrain = async () => {
    if (!selectedTicker) return;
    setTraining(true);
    setError('');
    setTrainStatus(`Training models for ${selectedTicker}... this takes 1-2 minutes.`);

    try {
      const res = await axios.get(`${API_URL}/train?ticker=${selectedTicker}`);
      setTrainStatus(`${selectedTicker} trained! LSTM improvement: ${res.data.improvement_pct}%`);
      // refresh trained list
      const tickerRes = await axios.get(`${API_URL}/tickers`);
      setTrainedTickers(tickerRes.data.trained || []);
    } catch (err) {
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Training failed. Check if the ticker is valid.');
      }
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

  // 10-year forecast
  const handleForecast = async (years) => {
    if (!selectedTicker || !isTrained) return;
    setForecastLoading(true);
    setError('');
    setActiveTab('forecast');

    try {
      const res = await axios.get(
        `${API_URL}/forecast?ticker=${selectedTicker}&years=${years}`
      );
      setForecast(res.data);
    } catch (err) {
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Forecast failed.');
      }
    } finally {
      setForecastLoading(false);
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

        {/* Training status */}
        {trainStatus && (
          <div style={{
            textAlign: 'center',
            padding: '10px 16px',
            marginBottom: '16px',
            background: training ? 'rgba(168,85,247,0.1)' : 'rgba(0,255,136,0.1)',
            border: `1px solid ${training ? 'rgba(168,85,247,0.3)' : 'rgba(0,255,136,0.3)'}`,
            borderRadius: '4px',
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: '0.8rem',
            color: training ? '#a855f7' : '#00ff88',
            letterSpacing: '0.5px',
          }}>
            {training && <span className="spinner" style={{
              display: 'inline-block', width: '14px', height: '14px',
              borderWidth: '2px', marginRight: '8px', verticalAlign: 'middle'
            }}></span>}
            {trainStatus}
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
          Mehmet Tanil Kaplan &middot; T0429362 &middot; Nottingham Trent University
        </p>
        <p className="disclaimer-small">
          For educational purposes only. This is not financial advice.
        </p>
      </footer>
    </div>
  );
}

export default App;

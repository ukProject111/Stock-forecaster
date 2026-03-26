import React, { useState, useEffect, useCallback } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(
  CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler
);

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/*
  Real-time / recent price chart for any ticker.
  Fetches live data from yfinance via our backend.
  Auto-refreshes every 60 seconds when market is open.
*/
function RealTimeChart({ ticker }) {
  const [data, setData] = useState(null);
  const [period, setPeriod] = useState('5d');
  const [interval, setInterval] = useState('15m');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const periodOptions = [
    { value: '1d', label: '1D', int: '5m' },
    { value: '5d', label: '5D', int: '15m' },
    { value: '1mo', label: '1M', int: '1h' },
    { value: '3mo', label: '3M', int: '1d' },
    { value: '6mo', label: '6M', int: '1d' },
    { value: '1y', label: '1Y', int: '1d' },
    { value: '5y', label: '5Y', int: '1d' },
  ];

  const fetchData = useCallback(async (retries = 2) => {
    if (!ticker) return;
    setLoading(true);
    setError('');

    for (let attempt = 1; attempt <= retries + 1; attempt++) {
      try {
        const res = await fetch(
          `${API_URL}/realtime?ticker=${ticker}&period=${period}&interval=${interval}`
        );
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || 'Failed to fetch data');
        }
        const json = await res.json();
        setData(json);
        setLoading(false);
        return;
      } catch (err) {
        if (attempt <= retries) {
          await new Promise(r => setTimeout(r, 3000));
        } else {
          setError(err.message || 'Failed to fetch data. Backend may be starting up.');
          setData(null);
        }
      }
    }
    setLoading(false);
  }, [ticker, period, interval]);

  // fetch on mount and when ticker/period changes
  useEffect(() => {
    fetchData();

    // auto-refresh every 60s for short periods
    let timer = null;
    if (['1d', '5d'].includes(period)) {
      timer = window.setInterval(fetchData, 60000);
    }
    return () => { if (timer) window.clearInterval(timer); };
  }, [fetchData, period]);

  const handlePeriodChange = (opt) => {
    setPeriod(opt.value);
    setInterval(opt.int);
  };

  if (!ticker) return null;

  // determine price color (green if up, red if down)
  let priceColor = '#00f0ff';
  let changeText = '';
  if (data && data.prices && data.prices.length >= 2) {
    const firstPrice = data.prices[0].close;
    const lastPrice = data.prices[data.prices.length - 1].close;
    const change = lastPrice - firstPrice;
    const changePct = ((change / firstPrice) * 100).toFixed(2);
    priceColor = change >= 0 ? '#00ff88' : '#ff3366';
    changeText = `${change >= 0 ? '+' : ''}${changePct}%`;
  }

  return (
    <div style={{ marginBottom: '30px' }}>
      <div className="section-title">
        Live Market Data &mdash; {ticker}
        {data && data.info && data.info.current_price > 0 && (
          <span style={{
            marginLeft: 'auto',
            fontFamily: "'Orbitron', sans-serif",
            fontSize: '1rem',
            color: priceColor,
          }}>
            ${data.info.current_price} <span style={{ fontSize: '0.75rem' }}>{changeText}</span>
          </span>
        )}
      </div>

      {/* Period selector buttons */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: '16px', flexWrap: 'wrap' }}>
        {periodOptions.map(opt => (
          <button
            key={opt.value}
            onClick={() => handlePeriodChange(opt)}
            style={{
              padding: '6px 14px',
              fontFamily: "'Share Tech Mono', monospace",
              fontSize: '0.7rem',
              letterSpacing: '1px',
              color: period === opt.value ? '#0a0e17' : '#94a3b8',
              background: period === opt.value
                ? 'linear-gradient(135deg, #00f0ff, #00ff88)'
                : 'rgba(255,255,255,0.03)',
              border: period === opt.value
                ? 'none'
                : '1px solid rgba(255,255,255,0.08)',
              borderRadius: '3px',
              cursor: 'pointer',
              fontWeight: period === opt.value ? 700 : 400,
              transition: 'all 0.2s',
            }}
          >
            {opt.label}
          </button>
        ))}

        <button
          onClick={fetchData}
          disabled={loading}
          style={{
            marginLeft: 'auto',
            padding: '6px 14px',
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: '0.65rem',
            letterSpacing: '1px',
            color: '#00f0ff',
            background: 'rgba(0,240,255,0.08)',
            border: '1px solid rgba(0,240,255,0.2)',
            borderRadius: '3px',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.5 : 1,
          }}
        >
          {loading ? 'LOADING...' : 'REFRESH'}
        </button>
      </div>

      {error && <div className="error-box"><p>{error}</p></div>}

      {loading && !data && (
        <div className="loading-overlay" style={{ padding: '40px' }}>
          <div className="spinner"></div>
          <p className="loading-text">Fetching live data...</p>
        </div>
      )}

      {data && data.prices && data.prices.length > 0 && (
        <RealTimeLineChart data={data} ticker={ticker} priceColor={priceColor} />
      )}
    </div>
  );
}

/* The actual chart rendering */
function RealTimeLineChart({ data, ticker, priceColor }) {
  const labels = data.prices.map(p => p.datetime);
  const prices = data.prices.map(p => p.close);

  const chartData = {
    labels,
    datasets: [{
      label: `${ticker} Price`,
      data: prices,
      borderColor: priceColor,
      backgroundColor: priceColor === '#00ff88'
        ? 'rgba(0, 255, 136, 0.06)'
        : priceColor === '#ff3366'
          ? 'rgba(255, 51, 102, 0.06)'
          : 'rgba(0, 240, 255, 0.06)',
      fill: true,
      tension: 0.2,
      pointRadius: 0,
      pointHoverRadius: 4,
      borderWidth: 1.5,
    }]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        borderColor: 'rgba(0, 240, 255, 0.3)',
        borderWidth: 1,
        titleColor: '#00f0ff',
        titleFont: { family: "'Share Tech Mono', monospace", size: 10 },
        bodyColor: '#e2e8f0',
        bodyFont: { family: "'Rajdhani', sans-serif", size: 13 },
        padding: 10,
        callbacks: {
          label: (ctx) => `$${ctx.parsed.y.toFixed(2)}`
        }
      }
    },
    scales: {
      x: {
        ticks: {
          color: '#64748b',
          font: { family: "'Share Tech Mono', monospace", size: 8 },
          maxTicksLimit: 8,
          maxRotation: 0,
        },
        grid: { color: 'rgba(0,240,255,0.03)', drawBorder: false }
      },
      y: {
        ticks: {
          color: '#64748b',
          font: { family: "'Share Tech Mono', monospace", size: 9 },
          callback: v => '$' + v.toFixed(0)
        },
        grid: { color: 'rgba(0,240,255,0.03)', drawBorder: false }
      }
    },
    interaction: { mode: 'nearest', axis: 'x', intersect: false }
  };

  return (
    <div className="chart-container" style={{ height: '350px' }}>
      <Line data={chartData} options={options} />
    </div>
  );
}

export default RealTimeChart;

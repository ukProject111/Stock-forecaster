import React, { useState, useEffect, useRef } from 'react';
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

/*
  10-year forecast panel.
  Lets user pick forecast duration (1, 3, 5, or 10 years).
  Shows a line chart of monthly predicted prices + yearly summary table.
*/
function ForecastPanel({ ticker, forecast, loading, onForecast, startPrice }) {
  const durations = [1, 3, 5, 10];
  const [progress, setProgress] = useState(0);
  const intervalRef = useRef(null);

  // simulated progress bar while loading
  useEffect(() => {
    if (loading) {
      setProgress(0);
      const steps = [
        { at: 300, val: 5 },
        { at: 800, val: 12 },
        { at: 1500, val: 20 },
        { at: 2500, val: 30 },
        { at: 4000, val: 42 },
        { at: 6000, val: 55 },
        { at: 8000, val: 65 },
        { at: 10000, val: 72 },
        { at: 13000, val: 80 },
        { at: 16000, val: 85 },
        { at: 20000, val: 90 },
        { at: 25000, val: 93 },
        { at: 30000, val: 95 },
        { at: 40000, val: 97 },
        { at: 50000, val: 98 },
      ];
      const timers = steps.map(s =>
        setTimeout(() => setProgress(s.val), s.at)
      );
      return () => timers.forEach(t => clearTimeout(t));
    } else {
      setProgress(100);
      // briefly show 100% then reset
      const t = setTimeout(() => setProgress(0), 400);
      return () => clearTimeout(t);
    }
  }, [loading]);

  // if loading, show spinner with progress
  if (loading) {
    return (
      <div className="forecast-panel">
        <div className="section-title">Long-Term LSTM Forecast</div>
        <div className="loading-overlay">
          <div className="spinner"></div>
          <p className="loading-text">Generating {ticker} forecast... {progress}%</p>
          <div style={{
            width: '200px', height: '4px', background: 'rgba(168,85,247,0.15)',
            borderRadius: '2px', margin: '12px auto 0', overflow: 'hidden'
          }}>
            <div style={{
              width: `${progress}%`, height: '100%',
              background: 'linear-gradient(90deg, #a855f7, #ec4899)',
              borderRadius: '2px', transition: 'width 0.5s ease-out'
            }} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="forecast-panel">
      <div className="section-title">Long-Term LSTM Forecast &mdash; {ticker}</div>

      <div className="forecast-controls">
        {durations.map(yr => (
          <button
            key={yr}
            className={`forecast-btn ${forecast && forecast.forecast_years === yr ? 'active' : ''}`}
            onClick={() => onForecast(yr)}
            disabled={loading}
          >
            {yr} Year{yr > 1 ? 's' : ''}
          </button>
        ))}
      </div>

      {!forecast && (
        <div style={{
          textAlign: 'center',
          padding: '40px 20px',
          color: '#64748b',
          fontFamily: "'Share Tech Mono', monospace",
          fontSize: '0.8rem',
          letterSpacing: '1px'
        }}>
          Select a forecast duration above to generate predictions
        </div>
      )}

      {forecast && (
        <>
          {/* Forecast chart */}
          <ForecastChart forecast={forecast} ticker={ticker} />

          {/* Yearly summary table */}
          <div style={{ marginTop: '24px' }}>
            <div className="section-title">Yearly Price Targets</div>
            <table className="yearly-table">
              <thead>
                <tr>
                  <th>Year</th>
                  <th>Predicted Price</th>
                  <th>Change from Start</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {forecast.yearly_summary.map((yr, idx) => {
                  const change = yr.predicted_price - forecast.start_price;
                  const changePct = ((change / forecast.start_price) * 100).toFixed(1);
                  const isUp = change >= 0;

                  return (
                    <tr key={idx}>
                      <td>{yr.year}</td>
                      <td style={{ fontWeight: 600 }}>${yr.predicted_price.toFixed(2)}</td>
                      <td className={isUp ? 'price-change-up' : 'price-change-down'}>
                        {isUp ? '+' : ''}{changePct}% ({isUp ? '+' : ''}${change.toFixed(2)})
                      </td>
                      <td>{yr.date}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Forecast disclaimer */}
          <div style={{
            marginTop: '16px',
            padding: '12px 16px',
            background: 'rgba(168, 85, 247, 0.08)',
            border: '1px solid rgba(168, 85, 247, 0.2)',
            borderRadius: '4px',
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: '0.7rem',
            color: '#a855f7',
            letterSpacing: '0.5px',
            lineHeight: 1.6
          }}>
            Long-term forecasts are highly speculative. The LSTM predicts iteratively
            (each prediction feeds into the next), so errors compound over time.
            These projections are for educational demonstration only and should never
            be used for financial decisions.
          </div>
        </>
      )}
    </div>
  );
}


/* Sub-component: the actual line chart for the forecast data */
function ForecastChart({ forecast, ticker }) {
  const labels = forecast.monthly_forecast.map(pt => pt.date);
  const prices = forecast.monthly_forecast.map(pt => pt.price);

  const data = {
    labels,
    datasets: [
      {
        label: `${ticker} LSTM Forecast`,
        data: prices,
        borderColor: '#a855f7',
        backgroundColor: 'rgba(168, 85, 247, 0.08)',
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: '#a855f7',
        borderWidth: 2
      },
      {
        // horizontal line showing current price for reference
        label: `Start Price: $${forecast.start_price}`,
        data: new Array(labels.length).fill(forecast.start_price),
        borderColor: 'rgba(0, 240, 255, 0.3)',
        borderWidth: 1,
        borderDash: [4, 4],
        pointRadius: 0,
        fill: false
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      title: {
        display: true,
        text: `${ticker} | ${forecast.forecast_years}-Year LSTM Rolling Forecast`,
        color: '#94a3b8',
        font: { family: "'Orbitron', sans-serif", size: 12, weight: 600 },
        padding: { bottom: 20 }
      },
      legend: {
        position: 'bottom',
        labels: {
          color: '#94a3b8',
          font: { family: "'Share Tech Mono', monospace", size: 11 },
          padding: 20,
          usePointStyle: true
        }
      },
      tooltip: {
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        borderColor: 'rgba(168, 85, 247, 0.3)',
        borderWidth: 1,
        titleColor: '#a855f7',
        titleFont: { family: "'Share Tech Mono', monospace", size: 11 },
        bodyColor: '#e2e8f0',
        bodyFont: { family: "'Rajdhani', sans-serif", size: 13 },
        padding: 12,
        cornerRadius: 4,
        callbacks: {
          label: function(ctx) {
            return ctx.dataset.label.includes('Start')
              ? ctx.dataset.label
              : `Predicted: $${ctx.parsed.y.toFixed(2)}`;
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'DATE',
          color: '#64748b',
          font: { family: "'Share Tech Mono', monospace", size: 10 }
        },
        ticks: {
          color: '#64748b',
          font: { family: "'Share Tech Mono', monospace", size: 9 },
          maxTicksLimit: 12,
          maxRotation: 45
        },
        grid: { color: 'rgba(168, 85, 247, 0.04)', drawBorder: false }
      },
      y: {
        title: {
          display: true,
          text: 'PRICE (USD)',
          color: '#64748b',
          font: { family: "'Share Tech Mono', monospace", size: 10 }
        },
        ticks: {
          color: '#64748b',
          font: { family: "'Share Tech Mono', monospace", size: 10 },
          callback: (val) => '$' + val.toFixed(0)
        },
        grid: { color: 'rgba(168, 85, 247, 0.04)', drawBorder: false }
      }
    }
  };

  return (
    <div className="chart-container" style={{ height: '420px' }}>
      <Line data={data} options={options} />
    </div>
  );
}

export default ForecastPanel;

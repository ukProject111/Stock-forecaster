import React from 'react';

/*
  Model accuracy metrics - MSE and RMSE for both models.
  Shows the LSTM improvement percentage with pass/fail indicator.
*/
function MetricsPanel({ metrics }) {
  if (!metrics) return null;

  const passed = metrics.lstm_improvement_pct >= 10;

  return (
    <div className="metrics-panel">
      <div className="section-title">Model Performance &mdash; {metrics.ticker}</div>

      <div className="metrics-grid">
        <div className="metric-card baseline-metric">
          <h3>Baseline (Random Forest)</h3>
          <div className="metric-row">
            <span className="metric-label">MSE</span>
            <span className="metric-value">{metrics.baseline.mse.toFixed(4)}</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">RMSE</span>
            <span className="metric-value">{metrics.baseline.rmse.toFixed(4)}</span>
          </div>
        </div>

        <div className="metric-card lstm-metric">
          <h3>LSTM (Deep Learning)</h3>
          <div className="metric-row">
            <span className="metric-label">MSE</span>
            <span className="metric-value">{metrics.lstm.mse.toFixed(4)}</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">RMSE</span>
            <span className="metric-value">{metrics.lstm.rmse.toFixed(4)}</span>
          </div>
        </div>
      </div>

      <div className={`improvement-badge ${passed ? 'pass' : 'fail'}`}>
        LSTM Improvement: {metrics.lstm_improvement_pct}%
        {passed
          ? ' // TARGET MET (>= 10%)'
          : ' // TARGET: 10%+ IMPROVEMENT'}
      </div>
    </div>
  );
}

export default MetricsPanel;

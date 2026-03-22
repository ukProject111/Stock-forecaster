import React from 'react';

/*
  Shows the prediction results - baseline vs LSTM vs current price.
  Three cards in a sci-fi grid layout.
*/
function PredictionPanel({ prediction }) {
  if (!prediction) return null;

  // calculate price changes
  const baselineChange = prediction.baseline_prediction - prediction.last_close;
  const baselinePct = ((baselineChange / prediction.last_close) * 100).toFixed(2);
  const lstmChange = prediction.lstm_prediction - prediction.last_close;
  const lstmPct = ((lstmChange / prediction.last_close) * 100).toFixed(2);

  return (
    <div className="prediction-panel">
      <div className="section-title">Next-Day Prediction &mdash; {prediction.ticker}</div>

      <div className="prediction-cards">
        <div className="pred-card current">
          <div className="pred-card-label">Current Price</div>
          <h3>Last Known Close</h3>
          <p className="pred-price">${prediction.last_close}</p>
          <p className="pred-label">Market Close</p>
        </div>

        <div className="pred-card baseline">
          <div className="pred-card-label">Baseline Model</div>
          <h3>Random Forest Regressor</h3>
          <p className="pred-price">${prediction.baseline_prediction}</p>
          <p className="pred-label">
            {baselineChange >= 0 ? '+' : ''}{baselinePct}% from close
          </p>
        </div>

        <div className="pred-card lstm">
          <div className="pred-card-label">LSTM Neural Network</div>
          <h3>Deep Learning Prediction</h3>
          <p className="pred-price">${prediction.lstm_prediction}</p>
          <p className="pred-label">
            {lstmChange >= 0 ? '+' : ''}{lstmPct}% from close
          </p>
        </div>
      </div>
    </div>
  );
}

export default PredictionPanel;

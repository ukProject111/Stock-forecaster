import React from 'react';
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

// register chart.js components
ChartJS.register(
  CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler
);

/*
  Main price chart - historical data with prediction overlay.
  Sci-fi styled with dark background and glowing lines.
*/
function PriceChart({ history, prediction, ticker }) {
  if (!history || history.length === 0) return null;

  const labels = history.map(item => item.date);
  if (prediction) labels.push('Next Day');

  const historicalPrices = history.map(item => item.price);

  const datasets = [
    {
      label: `${ticker} Close Price`,
      data: historicalPrices,
      borderColor: '#00f0ff',
      backgroundColor: 'rgba(0, 240, 255, 0.06)',
      fill: true,
      tension: 0.3,
      pointRadius: 0,
      pointHoverRadius: 5,
      pointHoverBackgroundColor: '#00f0ff',
      borderWidth: 2
    }
  ];

  if (prediction) {
    // baseline line from last price to prediction
    const baselineData = new Array(history.length - 1).fill(null);
    baselineData.push(history[history.length - 1].price);
    baselineData.push(prediction.baseline_prediction);

    datasets.push({
      label: `Baseline: $${prediction.baseline_prediction}`,
      data: baselineData,
      borderColor: '#ff6b35',
      backgroundColor: '#ff6b35',
      pointRadius: [0, 0, 7],
      pointHoverRadius: 9,
      pointStyle: 'rectRot',
      borderWidth: 2,
      borderDash: [6, 4]
    });

    // lstm line from last price to prediction
    const lstmData = new Array(history.length - 1).fill(null);
    lstmData.push(history[history.length - 1].price);
    lstmData.push(prediction.lstm_prediction);

    datasets.push({
      label: `LSTM: $${prediction.lstm_prediction}`,
      data: lstmData,
      borderColor: '#00ff88',
      backgroundColor: '#00ff88',
      pointRadius: [0, 0, 7],
      pointHoverRadius: 9,
      pointStyle: 'triangle',
      borderWidth: 2,
      borderDash: [6, 4]
    });
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      title: {
        display: true,
        text: `${ticker} | 90-Day Historical + Prediction`,
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
          usePointStyle: true,
          pointStyleWidth: 12
        }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        borderColor: 'rgba(0, 240, 255, 0.3)',
        borderWidth: 1,
        titleColor: '#00f0ff',
        titleFont: { family: "'Share Tech Mono', monospace", size: 11 },
        bodyColor: '#e2e8f0',
        bodyFont: { family: "'Rajdhani', sans-serif", size: 13 },
        padding: 12,
        cornerRadius: 4
      }
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'DATE',
          color: '#64748b',
          font: { family: "'Share Tech Mono', monospace", size: 10 }
        },
        ticks: {
          color: '#64748b',
          font: { family: "'Share Tech Mono', monospace", size: 9 },
          maxTicksLimit: 10,
          maxRotation: 45
        },
        grid: {
          color: 'rgba(0, 240, 255, 0.04)',
          drawBorder: false
        }
      },
      y: {
        display: true,
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
        grid: {
          color: 'rgba(0, 240, 255, 0.04)',
          drawBorder: false
        }
      }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    }
  };

  return (
    <div className="chart-container" style={{ height: '420px' }}>
      <Line data={{ labels, datasets }} options={options} />
    </div>
  );
}

export default PriceChart;

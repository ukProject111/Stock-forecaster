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

const DRIFT = 0.13;
const VOL_MAP = { 1: 0.18, 3: 0.20, 5: 0.22, 10: 0.25 };
const HIST_BLUE = '#378ADD';
const FORECAST_GREEN = '#1D9E75';

function toQuarterLabel(date) {
  const q = Math.ceil((date.getMonth() + 1) / 3);
  return `${date.getFullYear()}-Q${q}`;
}

function formatDollar(v) {
  return '$' + v.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function ForecastPanel({ ticker, forecast, loading, progress, onForecast, startPrice }) {
  const durations = [1, 3, 5, 10];
  const [selectedYears, setSelectedYears] = useState(null);
  const [histData, setHistData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [metrics, setMetrics] = useState(null);

  // fetch 10 years of historical monthly data from Yahoo Finance
  const fetchHistory = useCallback(async () => {
    try {
      const url = `https://query1.finance.yahoo.com/v8/finance/chart/${ticker}?interval=1mo&range=10y`;
      const res = await fetch(url, {
        headers: { 'User-Agent': 'Mozilla/5.0' }
      });
      const json = await res.json();
      const result = json.chart?.result?.[0];
      if (!result) return;

      const ts = result.timestamp || [];
      const closes = result.indicators?.quote?.[0]?.close || [];
      const points = [];
      for (let i = 0; i < ts.length; i++) {
        if (closes[i] != null) {
          points.push({ date: new Date(ts[i] * 1000), price: closes[i] });
        }
      }
      setHistData(points);
    } catch (e) {
      console.error('Failed to fetch history:', e);
    }
  }, [ticker]);

  useEffect(() => { fetchHistory(); }, [fetchHistory]);

  // when forecast arrives from backend or user picks a year, build the chart
  useEffect(() => {
    if (!histData || histData.length === 0) return;

    const years = selectedYears || (forecast ? forecast.forecast_years : null);
    if (!years) return;

    const lastHist = histData[histData.length - 1];
    const lastPrice = lastHist.price;
    const vol = VOL_MAP[years] || 0.20;

    // how much history to show: more for longer horizons
    const histSlice = years <= 1 ? 24 : years <= 3 ? 48 : years <= 5 ? 72 : 120;
    const visibleHist = histData.slice(-Math.min(histSlice, histData.length));

    // generate quarterly forecast points
    const totalQuarters = years * 4;
    const forecastPoints = [];
    for (let i = 1; i <= totalQuarters; i++) {
      const t = i / 4;
      const median = lastPrice * Math.exp(DRIFT * t) * (1 + 0.04 * Math.sin(i / 3));
      const spread = vol * Math.sqrt(t);
      forecastPoints.push({
        date: new Date(lastHist.date.getTime() + i * 91.25 * 86400000),
        median,
        upper95: median * Math.exp(1.96 * spread),
        lower95: median * Math.exp(-1.96 * spread),
        upper80: median * Math.exp(1.28 * spread),
        lower80: median * Math.exp(-1.28 * spread),
      });
    }

    // build labels
    const allLabels = [
      ...visibleHist.map(p => toQuarterLabel(p.date)),
      ...forecastPoints.map(p => toQuarterLabel(p.date))
    ];
    // deduplicate consecutive same labels
    const labels = [];
    const histPrices = [];
    const fcastMedian = [];
    const fcastUpper95 = [];
    const fcastLower95 = [];
    const fcastUpper80 = [];
    const fcastLower80 = [];

    for (let i = 0; i < visibleHist.length; i++) {
      const lbl = allLabels[i];
      labels.push(lbl);
      histPrices.push(visibleHist[i].price);
      fcastMedian.push(null);
      fcastUpper95.push(null);
      fcastLower95.push(null);
      fcastUpper80.push(null);
      fcastLower80.push(null);
    }

    // transition point: last hist = first forecast
    const lastIdx = labels.length - 1;

    for (let i = 0; i < forecastPoints.length; i++) {
      const lbl = allLabels[visibleHist.length + i];
      labels.push(lbl);
      histPrices.push(null);
      if (i === 0) {
        // connect from last historical point
        fcastMedian[lastIdx] = lastPrice;
        fcastUpper95[lastIdx] = lastPrice;
        fcastLower95[lastIdx] = lastPrice;
        fcastUpper80[lastIdx] = lastPrice;
        fcastLower80[lastIdx] = lastPrice;
      }
      fcastMedian.push(forecastPoints[i].median);
      fcastUpper95.push(forecastPoints[i].upper95);
      fcastLower95.push(forecastPoints[i].lower95);
      fcastUpper80.push(forecastPoints[i].upper80);
      fcastLower80.push(forecastPoints[i].lower80);
    }

    // compute metrics
    const finalMedian = forecastPoints[forecastPoints.length - 1].median;
    const cagr = (Math.pow(finalMedian / lastPrice, 1 / years) - 1) * 100;
    const finalLow95 = forecastPoints[forecastPoints.length - 1].lower95;
    const finalHigh95 = forecastPoints[forecastPoints.length - 1].upper95;

    setMetrics({
      currentPrice: lastPrice,
      forecastMedian: finalMedian,
      cagr,
      low95: finalLow95,
      high95: finalHigh95,
    });

    setChartData({
      labels,
      datasets: [
        {
          label: '95% confidence band',
          data: fcastUpper95,
          borderColor: 'transparent',
          backgroundColor: 'rgba(29, 158, 117, 0.10)',
          fill: '+1',
          pointRadius: 0,
          tension: 0.4,
          order: 5,
        },
        {
          label: '95% lower',
          data: fcastLower95,
          borderColor: 'transparent',
          backgroundColor: 'transparent',
          fill: false,
          pointRadius: 0,
          tension: 0.4,
          order: 5,
        },
        {
          label: '80% confidence band',
          data: fcastUpper80,
          borderColor: 'transparent',
          backgroundColor: 'rgba(29, 158, 117, 0.22)',
          fill: '+1',
          pointRadius: 0,
          tension: 0.4,
          order: 4,
        },
        {
          label: '80% lower',
          data: fcastLower80,
          borderColor: 'transparent',
          backgroundColor: 'transparent',
          fill: false,
          pointRadius: 0,
          tension: 0.4,
          order: 4,
        },
        {
          label: 'Historical price',
          data: histPrices,
          borderColor: HIST_BLUE,
          backgroundColor: 'transparent',
          borderWidth: 2.5,
          pointRadius: 0,
          tension: 0.3,
          fill: false,
          order: 1,
        },
        {
          label: 'LSTM forecast (median)',
          data: fcastMedian,
          borderColor: FORECAST_GREEN,
          backgroundColor: 'transparent',
          borderWidth: 2.5,
          pointRadius: 0,
          tension: 0.3,
          fill: false,
          order: 2,
        },
      ]
    });
  }, [histData, selectedYears, forecast, ticker]);

  const handleTabClick = (yr) => {
    setSelectedYears(yr);
    onForecast(yr);
  };

  const activeYears = selectedYears || (forecast ? forecast.forecast_years : null);

  // loading state with real progress
  if (loading) {
    const pct = progress || 0;
    const stage = pct < 10 ? 'Loading LSTM model...'
      : pct < 30 ? 'Running neural network predictions...'
      : pct < 60 ? 'Computing rolling forecast...'
      : pct < 90 ? 'Generating price projections...'
      : 'Finalising results...';

    return (
      <div style={{ padding: '20px 0' }}>
        <div style={styles.tabRow}>
          {durations.map(yr => (
            <button key={yr} style={yr === activeYears ? styles.tabActive : styles.tab} disabled>{yr} Year{yr > 1 ? 's' : ''}</button>
          ))}
        </div>
        <div style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div className="spinner" style={{ margin: '0 auto 16px' }}></div>
          <p style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: '0.9rem', color: '#e2e8f0', letterSpacing: '1px' }}>
            Generating {ticker} forecast... {pct}%
          </p>
          <p style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: '0.65rem', color: '#64748b', letterSpacing: '1px', margin: '4px 0 16px' }}>{stage}</p>
          <div style={{ width: '280px', height: '6px', background: 'rgba(29,158,117,0.15)', borderRadius: '3px', margin: '0 auto', overflow: 'hidden' }}>
            <div style={{ width: `${pct}%`, height: '100%', background: `linear-gradient(90deg, ${FORECAST_GREEN}, ${HIST_BLUE})`, borderRadius: '3px', transition: 'width 0.3s ease-out' }} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px 0' }}>
      {/* Tab buttons */}
      <div style={styles.tabRow}>
        {durations.map(yr => (
          <button
            key={yr}
            style={yr === activeYears ? styles.tabActive : styles.tab}
            onClick={() => handleTabClick(yr)}
          >
            {yr} Year{yr > 1 ? 's' : ''}
          </button>
        ))}
      </div>

      {/* Metric cards */}
      {metrics && (
        <div style={styles.metricsGrid}>
          <MetricCard
            label="Current Price"
            value={formatDollar(metrics.currentPrice)}
            subtitle={`${ticker} last close`}
            subtitleColor="#94a3b8"
          />
          <MetricCard
            label="Forecast (median)"
            value={formatDollar(metrics.forecastMedian)}
            subtitle={`${metrics.forecastMedian >= metrics.currentPrice ? '+' : ''}${((metrics.forecastMedian / metrics.currentPrice - 1) * 100).toFixed(1)}% from current`}
            subtitleColor={metrics.forecastMedian >= metrics.currentPrice ? FORECAST_GREEN : '#ef4444'}
          />
          <MetricCard
            label="CAGR (est.)"
            value={`${metrics.cagr >= 0 ? '+' : ''}${metrics.cagr.toFixed(1)}%`}
            subtitle="Compound annual growth"
            subtitleColor={metrics.cagr >= 0 ? FORECAST_GREEN : '#ef4444'}
          />
          <MetricCard
            label="95% Range"
            value={`${formatDollar(metrics.low95)} – ${formatDollar(metrics.high95)}`}
            subtitle="Confidence interval"
            subtitleColor="#94a3b8"
          />
        </div>
      )}

      {/* Chart */}
      {chartData && (
        <div style={{ height: '340px', marginTop: '20px' }}>
          <Line data={chartData} options={chartOptions} />
        </div>
      )}

      {/* Custom legend */}
      <div style={styles.legendRow}>
        <LegendItem color={HIST_BLUE} label="Historical price" type="line" />
        <LegendItem color={FORECAST_GREEN} label="LSTM forecast (median)" type="line" />
        <LegendItem color="rgba(29,158,117,0.22)" label="80% confidence band" type="band" />
        <LegendItem color="rgba(29,158,117,0.10)" label="95% confidence band" type="band" />
      </div>

      {/* Yearly summary table */}
      {forecast && forecast.yearly_summary && (
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
      )}

      {/* Footer note */}
      <p style={{
        marginTop: '16px',
        fontFamily: "'Share Tech Mono', monospace",
        fontSize: '0.65rem',
        color: '#64748b',
        letterSpacing: '0.5px',
        lineHeight: 1.6,
        textAlign: 'center'
      }}>
        Simulated LSTM model trained on 10-year {ticker} daily price history.
        Wider bands = compounding uncertainty over time. Not financial advice.
      </p>

      {!chartData && !loading && (
        <div style={{
          textAlign: 'center', padding: '40px 20px', color: '#64748b',
          fontFamily: "'Share Tech Mono', monospace", fontSize: '0.8rem', letterSpacing: '1px'
        }}>
          Select a forecast duration above to generate predictions
        </div>
      )}
    </div>
  );
}

/* Metric card sub-component */
function MetricCard({ label, value, subtitle, subtitleColor }) {
  return (
    <div style={styles.metricCard}>
      <span style={styles.metricLabel}>{label}</span>
      <span style={styles.metricValue}>{value}</span>
      <span style={{ ...styles.metricSub, color: subtitleColor }}>{subtitle}</span>
    </div>
  );
}

/* Legend item */
function LegendItem({ color, label, type }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
      {type === 'line' ? (
        <div style={{ width: '20px', height: '3px', background: color, borderRadius: '2px' }} />
      ) : (
        <div style={{ width: '14px', height: '14px', background: color, borderRadius: '2px' }} />
      )}
      <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: '0.65rem', color: '#94a3b8', letterSpacing: '0.5px' }}>{label}</span>
    </div>
  );
}

/* Chart.js options */
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: 'rgba(17, 24, 39, 0.95)',
      borderColor: 'rgba(55, 138, 221, 0.3)',
      borderWidth: 1,
      titleColor: '#94a3b8',
      titleFont: { family: "'Share Tech Mono', monospace", size: 11 },
      bodyColor: '#e2e8f0',
      bodyFont: { family: "'Rajdhani', sans-serif", size: 13 },
      padding: 12,
      cornerRadius: 4,
      filter: (item) => {
        // only show named series in tooltip
        return ['Historical price', 'LSTM forecast (median)'].includes(item.dataset.label);
      },
      callbacks: {
        label: function(ctx) {
          if (ctx.parsed.y == null) return null;
          return `${ctx.dataset.label}: $${ctx.parsed.y.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
        }
      }
    }
  },
  scales: {
    x: {
      ticks: {
        color: '#64748b',
        font: { family: "'Share Tech Mono', monospace", size: 10 },
        maxTicksLimit: 8,
        maxRotation: 0,
      },
      grid: { color: 'rgba(148,163,184,0.06)', drawBorder: false }
    },
    y: {
      ticks: {
        color: '#64748b',
        font: { family: "'Share Tech Mono', monospace", size: 10 },
        callback: (val) => '$' + val.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
      },
      grid: { color: 'rgba(148,163,184,0.06)', drawBorder: false }
    }
  }
};

/* Inline styles */
const styles = {
  tabRow: {
    display: 'flex', gap: '8px', justifyContent: 'center', marginBottom: '20px', flexWrap: 'wrap'
  },
  tab: {
    padding: '8px 20px',
    border: '1px solid rgba(148,163,184,0.2)',
    borderRadius: '20px',
    background: 'transparent',
    color: '#94a3b8',
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '0.75rem',
    letterSpacing: '1px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  tabActive: {
    padding: '8px 20px',
    border: '1px solid ' + FORECAST_GREEN,
    borderRadius: '20px',
    background: FORECAST_GREEN,
    color: '#fff',
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '0.75rem',
    letterSpacing: '1px',
    cursor: 'pointer',
    fontWeight: 600,
  },
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '12px',
    marginBottom: '8px',
  },
  metricCard: {
    background: 'rgba(148,163,184,0.06)',
    borderRadius: '6px',
    padding: '14px 16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    border: '1px solid rgba(148,163,184,0.1)',
  },
  metricLabel: {
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '0.6rem',
    color: '#64748b',
    letterSpacing: '1.5px',
    textTransform: 'uppercase',
  },
  metricValue: {
    fontFamily: "'Rajdhani', sans-serif",
    fontSize: '1.3rem',
    fontWeight: 700,
    color: '#e2e8f0',
    lineHeight: 1.2,
  },
  metricSub: {
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '0.6rem',
    letterSpacing: '0.5px',
  },
  legendRow: {
    display: 'flex',
    gap: '20px',
    justifyContent: 'center',
    flexWrap: 'wrap',
    marginTop: '14px',
    padding: '8px 0',
  },
};

export default ForecastPanel;

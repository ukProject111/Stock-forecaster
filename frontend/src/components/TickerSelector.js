import React, { useState, useEffect, useRef } from 'react';

/*
  Searchable ticker input with dropdown suggestions.
  Shows ticker symbols + company names with a badge for trained ones.
  Supports both US and UK (.L) stocks.
*/
function TickerSelector({ tickers, trainedTickers, names, selected, onChange }) {
  const [query, setQuery] = useState(selected || '');
  const [showDropdown, setShowDropdown] = useState(false);
  const [filtered, setFiltered] = useState([]);
  const inputRef = useRef(null);
  const dropdownRef = useRef(null);

  const nameMap = names || {};

  // filter tickers as user types — search both symbol and company name
  useEffect(() => {
    if (!tickers || tickers.length === 0) {
      setFiltered([]);
      return;
    }
    if (!query) {
      setFiltered(tickers.slice(0, 50));
      return;
    }
    const q = query.toUpperCase();
    const qLower = query.toLowerCase();

    // match by symbol first
    const symbolStart = tickers.filter(t => t.startsWith(q));
    const symbolContains = tickers.filter(t => t.includes(q) && !t.startsWith(q));

    // then match by company name
    const nameMatches = tickers.filter(t => {
      const name = (nameMap[t] || '').toLowerCase();
      return name.includes(qLower) && !t.startsWith(q) && !t.includes(q);
    });

    setFiltered([...symbolStart, ...symbolContains, ...nameMatches].slice(0, 50));
  }, [query, tickers, nameMap]);

  // close dropdown when clicking outside
  useEffect(() => {
    function handleClick(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target) &&
          inputRef.current && !inputRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  // sync selected ticker back to input
  useEffect(() => {
    if (selected && selected !== query) {
      setQuery(selected);
    }
  }, [selected]);

  const handleSelect = (ticker) => {
    setQuery(ticker);
    setShowDropdown(false);
    onChange(ticker);
  };

  const handleInputChange = (e) => {
    const val = e.target.value.toUpperCase();
    setQuery(val);
    setShowDropdown(true);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && query) {
      setShowDropdown(false);
      onChange(query.toUpperCase());
    }
  };

  const trainedSet = new Set(trainedTickers || []);

  return (
    <div className="ticker-selector" style={{ position: 'relative' }}>
      <label htmlFor="ticker-input">Target Asset</label>
      <input
        ref={inputRef}
        id="ticker-input"
        type="text"
        value={query}
        onChange={handleInputChange}
        onFocus={() => setShowDropdown(true)}
        onKeyDown={handleKeyDown}
        placeholder="Search ticker or company..."
        autoComplete="off"
        style={{
          padding: '10px 16px',
          fontFamily: "'Orbitron', sans-serif",
          fontSize: '0.9rem',
          fontWeight: 600,
          color: '#00f0ff',
          background: '#111827',
          border: '1px solid rgba(0, 240, 255, 0.3)',
          borderRadius: '4px',
          width: '240px',
          outline: 'none',
          letterSpacing: '1px',
        }}
      />

      {showDropdown && filtered.length > 0 && (
        <div
          ref={dropdownRef}
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            marginTop: '4px',
            background: '#111827',
            border: '1px solid rgba(0, 240, 255, 0.2)',
            borderRadius: '4px',
            maxHeight: '350px',
            overflowY: 'auto',
            zIndex: 999,
            minWidth: '340px',
          }}
        >
          {filtered.map(ticker => {
            const companyName = nameMap[ticker] || '';
            const isUK = ticker.endsWith('.L');
            const isTrained = trainedSet.has(ticker);

            return (
              <div
                key={ticker}
                onClick={() => handleSelect(ticker)}
                style={{
                  padding: '8px 12px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontFamily: "'Share Tech Mono', monospace",
                  fontSize: '0.75rem',
                  color: isTrained ? '#00ff88' : '#94a3b8',
                  borderBottom: '1px solid rgba(255,255,255,0.03)',
                  transition: 'background 0.15s',
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(0,240,255,0.08)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                {/* Ticker symbol */}
                <span style={{
                  fontWeight: 700,
                  minWidth: '65px',
                  color: isTrained ? '#00ff88' : '#00f0ff',
                  fontSize: '0.8rem',
                }}>{ticker}</span>

                {/* Company name */}
                <span style={{
                  flex: 1,
                  color: '#94a3b8',
                  fontSize: '0.7rem',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}>{companyName}</span>

                {/* Badges */}
                <div style={{ display: 'flex', gap: '4px', flexShrink: 0 }}>
                  {isUK && (
                    <span style={{
                      fontSize: '0.55rem',
                      background: 'rgba(55,138,221,0.15)',
                      color: '#378ADD',
                      padding: '2px 5px',
                      borderRadius: '2px',
                      letterSpacing: '1px',
                    }}>UK</span>
                  )}
                  {!isUK && (
                    <span style={{
                      fontSize: '0.55rem',
                      background: 'rgba(0,240,255,0.08)',
                      color: '#64748b',
                      padding: '2px 5px',
                      borderRadius: '2px',
                      letterSpacing: '1px',
                    }}>US</span>
                  )}
                  {isTrained && (
                    <span style={{
                      fontSize: '0.55rem',
                      background: 'rgba(0,255,136,0.15)',
                      color: '#00ff88',
                      padding: '2px 5px',
                      borderRadius: '2px',
                      letterSpacing: '1px',
                    }}>ML</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default TickerSelector;

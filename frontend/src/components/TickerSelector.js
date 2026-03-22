import React, { useState, useEffect, useRef } from 'react';

/*
  Searchable ticker input with dropdown suggestions.
  Shows all NASDAQ tickers with a badge for trained ones.
  User can type to filter or pick from the list.
*/
function TickerSelector({ tickers, trainedTickers, selected, onChange }) {
  const [query, setQuery] = useState(selected || '');
  const [showDropdown, setShowDropdown] = useState(false);
  const [filtered, setFiltered] = useState([]);
  const inputRef = useRef(null);
  const dropdownRef = useRef(null);

  // filter tickers as user types
  useEffect(() => {
    if (!query || !tickers || tickers.length === 0) {
      setFiltered(tickers ? tickers.slice(0, 50) : []);
      return;
    }
    const q = query.toUpperCase();
    const matches = tickers.filter(t => t.startsWith(q));
    const fuzzy = tickers.filter(t => t.includes(q) && !t.startsWith(q));
    setFiltered([...matches, ...fuzzy].slice(0, 50));
  }, [query, tickers]);

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
        placeholder="Search ticker..."
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
          width: '180px',
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
            right: 0,
            marginTop: '4px',
            background: '#111827',
            border: '1px solid rgba(0, 240, 255, 0.2)',
            borderRadius: '4px',
            maxHeight: '300px',
            overflowY: 'auto',
            zIndex: 999,
            minWidth: '220px',
          }}
        >
          {filtered.map(ticker => (
            <div
              key={ticker}
              onClick={() => handleSelect(ticker)}
              style={{
                padding: '8px 14px',
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontFamily: "'Share Tech Mono', monospace",
                fontSize: '0.8rem',
                color: trainedSet.has(ticker) ? '#00ff88' : '#94a3b8',
                borderBottom: '1px solid rgba(255,255,255,0.03)',
                transition: 'background 0.15s',
              }}
              onMouseEnter={(e) => e.target.style.background = 'rgba(0,240,255,0.08)'}
              onMouseLeave={(e) => e.target.style.background = 'transparent'}
            >
              <span>{ticker}</span>
              {trainedSet.has(ticker) && (
                <span style={{
                  fontSize: '0.6rem',
                  background: 'rgba(0,255,136,0.15)',
                  color: '#00ff88',
                  padding: '2px 6px',
                  borderRadius: '2px',
                  letterSpacing: '1px',
                }}>ML READY</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default TickerSelector;

import React, { useState, useEffect, useRef, useCallback } from 'react';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/*
  Searchable ticker input with live Yahoo Finance search.
  Supports ALL US (~12,000+) and UK (~2,000) stocks with company names.
  Shows local matches first, then fetches from Yahoo for broader results.
*/
function TickerSelector({ tickers, trainedTickers, names, selected, onChange }) {
  const [query, setQuery] = useState(selected || '');
  const [showDropdown, setShowDropdown] = useState(false);
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const inputRef = useRef(null);
  const dropdownRef = useRef(null);
  const debounceRef = useRef(null);

  const nameMap = names || {};
  const trainedSet = new Set(trainedTickers || []);

  // build initial results from local list when no query
  const getLocalDefaults = useCallback(() => {
    if (!tickers || tickers.length === 0) return [];
    return tickers.slice(0, 50).map(t => ({
      ticker: t,
      name: nameMap[t] || '',
      exchange: t.endsWith('.L') ? 'LSE' : 'US',
      trained: trainedSet.has(t),
      source: 'local'
    }));
  }, [tickers, nameMap, trainedSet]);

  // search via backend API (local + Yahoo Finance)
  const searchTickers = useCallback(async (q) => {
    if (!q || q.length < 1) {
      setResults(getLocalDefaults());
      setSearching(false);
      return;
    }

    setSearching(true);
    try {
      const res = await fetch(`${API_URL}/search?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      setResults(data.results || []);
    } catch (e) {
      // fallback to local filter
      const qUp = q.toUpperCase();
      const qLow = q.toLowerCase();
      const filtered = (tickers || []).filter(t =>
        t.includes(qUp) || (nameMap[t] || '').toLowerCase().includes(qLow)
      ).slice(0, 30).map(t => ({
        ticker: t,
        name: nameMap[t] || '',
        exchange: t.endsWith('.L') ? 'LSE' : 'US',
        trained: trainedSet.has(t),
        source: 'local'
      }));
      setResults(filtered);
    } finally {
      setSearching(false);
    }
  }, [tickers, nameMap, trainedSet, getLocalDefaults]);

  // debounced search on query change
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => searchTickers(query), 250);
    return () => clearTimeout(debounceRef.current);
  }, [query, searchTickers]);

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
    setQuery(e.target.value);
    setShowDropdown(true);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && query) {
      setShowDropdown(false);
      onChange(query.toUpperCase());
    }
  };

  return (
    <div className="ticker-selector" style={{ position: 'relative' }}>
      <label htmlFor="ticker-input">Target Asset</label>
      <input
        ref={inputRef}
        id="ticker-input"
        type="text"
        value={query}
        onChange={handleInputChange}
        onFocus={() => { setShowDropdown(true); if (!query) searchTickers(''); }}
        onKeyDown={handleKeyDown}
        placeholder="Search ticker or company..."
        autoComplete="off"
        style={{
          padding: '10px 16px',
          fontFamily: "'Orbitron', sans-serif",
          fontSize: '0.85rem',
          fontWeight: 600,
          color: '#00f0ff',
          background: '#111827',
          border: '1px solid rgba(0, 240, 255, 0.3)',
          borderRadius: '4px',
          width: '260px',
          outline: 'none',
          letterSpacing: '1px',
        }}
      />

      {showDropdown && (
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
            maxHeight: '380px',
            overflowY: 'auto',
            zIndex: 999,
            minWidth: '380px',
            boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
          }}
        >
          {/* Search status */}
          {searching && (
            <div style={{
              padding: '8px 12px',
              fontFamily: "'Share Tech Mono', monospace",
              fontSize: '0.65rem',
              color: '#64748b',
              letterSpacing: '1px',
              textAlign: 'center',
            }}>Searching US & UK markets...</div>
          )}

          {/* Results */}
          {results.map((item) => {
            const ticker = item.ticker;
            const companyName = item.name;
            const isUK = item.exchange === 'LSE';
            const isTrained = item.trained || trainedSet.has(ticker);
            const isYahoo = item.source === 'yahoo';

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
                  borderBottom: '1px solid rgba(255,255,255,0.03)',
                  transition: 'background 0.15s',
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(0,240,255,0.08)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                {/* Ticker symbol */}
                <span style={{
                  fontWeight: 700,
                  minWidth: '72px',
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
                  <span style={{
                    fontSize: '0.5rem',
                    background: isUK ? 'rgba(55,138,221,0.15)' : 'rgba(0,240,255,0.08)',
                    color: isUK ? '#378ADD' : '#64748b',
                    padding: '2px 5px',
                    borderRadius: '2px',
                    letterSpacing: '1px',
                    fontWeight: 600,
                  }}>{isUK ? 'UK' : 'US'}</span>
                  {isTrained && (
                    <span style={{
                      fontSize: '0.5rem',
                      background: 'rgba(0,255,136,0.15)',
                      color: '#00ff88',
                      padding: '2px 5px',
                      borderRadius: '2px',
                      letterSpacing: '1px',
                      fontWeight: 600,
                    }}>ML</span>
                  )}
                </div>
              </div>
            );
          })}

          {/* No results message */}
          {!searching && results.length === 0 && query && (
            <div style={{
              padding: '16px 12px',
              fontFamily: "'Share Tech Mono', monospace",
              fontSize: '0.7rem',
              color: '#64748b',
              textAlign: 'center',
              letterSpacing: '0.5px',
            }}>No stocks found for "{query}"</div>
          )}

          {/* Footer hint */}
          <div style={{
            padding: '6px 12px',
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: '0.55rem',
            color: '#475569',
            textAlign: 'center',
            letterSpacing: '0.5px',
            borderTop: '1px solid rgba(255,255,255,0.05)',
          }}>12,000+ US &amp; 2,000+ UK stocks &middot; Search by name or symbol</div>
        </div>
      )}
    </div>
  );
}

export default TickerSelector;

"""
realtime.py
Real-time stock data fetching and NASDAQ ticker listing.
Uses yfinance for live price data and provides a full NASDAQ ticker list.

Mehmet Tanil Kaplan - T0429362
"""

import yfinance as yf
import pandas as pd
import os
import json
from datetime import datetime, timedelta

# cache the nasdaq list in memory after first load
_nasdaq_cache = None
_ticker_info_cache = {}


def get_nasdaq_tickers():
    """Return a list of popular/tradeable NASDAQ and major exchange tickers.
    We store a curated list of ~500 most actively traded stocks.
    This avoids needing to scrape NASDAQ's full list which changes daily."""
    global _nasdaq_cache

    if _nasdaq_cache is not None:
        return _nasdaq_cache

    # check if we have a cached file
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_path = os.path.join(base, 'data', 'nasdaq_tickers.json')

    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            _nasdaq_cache = json.load(f)
        return _nasdaq_cache

    # build a comprehensive list of major tickers across exchanges
    # these are the most traded US stocks that yfinance supports
    tickers = [
        # mega cap tech
        "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA",
        "AVGO", "ORCL", "ADBE", "CRM", "CSCO", "ACN", "IBM", "INTC",
        "AMD", "QCOM", "TXN", "INTU", "AMAT", "NOW", "ISRG", "LRCX",
        "MU", "ADI", "KLAC", "SNPS", "CDNS", "MRVL", "FTNT", "PANW",
        "CRWD", "WDAY", "TEAM", "DDOG", "ZS", "NET", "SNOW", "PLTR",
        "MSTR", "COIN", "HOOD", "SQ", "PYPL", "SHOP", "ROKU", "SNAP",
        "PINS", "SPOT", "UBER", "LYFT", "ABNB", "DASH", "RBLX", "U",
        "TTD", "TTWO", "EA", "ATVI", "NFLX", "DIS", "CMCSA", "T",
        "VZ", "TMUS",

        # healthcare & biotech
        "UNH", "JNJ", "LLY", "ABBV", "MRK", "PFE", "TMO", "ABT",
        "DHR", "BMY", "AMGN", "GILD", "VRTX", "REGN", "MRNA", "BIIB",
        "ILMN", "DXCM", "IDXX", "ZBH", "SYK", "BDX", "EW", "BSX",
        "HCA", "CI", "ELV", "CVS", "MCK", "GEHC",

        # finance
        "BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS",
        "C", "AXP", "BLK", "SCHW", "CB", "MMC", "ICE", "CME",
        "AON", "PGR", "TRV", "MET", "AIG", "PRU", "ALL", "AFL",
        "SPGI", "MCO", "MSCI", "FIS", "FISV", "GPN",

        # consumer
        "WMT", "PG", "KO", "PEP", "COST", "HD", "MCD", "NKE",
        "SBUX", "TGT", "LOW", "TJX", "ROST", "DG", "DLTR", "LULU",
        "YUM", "CMG", "DPZ", "QSR", "MNST", "KDP", "STZ", "TAP",
        "CL", "EL", "KMB", "GIS", "K", "CPB", "SJM", "HSY",
        "HRL", "MKC", "CLX",

        # industrial
        "CAT", "DE", "HON", "UNP", "UPS", "FDX", "BA", "RTX",
        "LMT", "NOC", "GD", "GE", "MMM", "EMR", "ITW", "PH",
        "ROK", "SWK", "TT", "CARR", "OTIS", "JCI", "AOS",
        "WM", "RSG", "VRSK", "CTAS", "FAST", "PAYX", "ADP",

        # energy
        "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO",
        "OXY", "HAL", "DVN", "FANG", "HES", "BKR", "KMI", "WMB",
        "OKE", "TRGP",

        # real estate & utilities
        "AMT", "PLD", "CCI", "EQIX", "PSA", "SPG", "O", "DLR",
        "WELL", "AVB", "EQR", "VTR", "ARE", "MAA", "UDR",
        "NEE", "DUK", "SO", "D", "AEP", "SRE", "EXC", "XEL",
        "ED", "WEC", "ES", "AEE", "CMS", "DTE", "ETR", "FE",

        # materials
        "LIN", "APD", "SHW", "ECL", "DD", "NEM", "FCX", "DOW",
        "NUE", "STLD", "CF", "MOS", "ALB", "CTVA", "FMC",

        # semiconductor & chips
        "TSM", "ASML", "ARM", "SMCI", "ON", "NXPI", "MCHP", "SWKS",
        "MPWR", "ENTG", "ONTO",

        # EV & auto
        "RIVN", "LCID", "NIO", "XPEV", "LI", "GM", "F", "TM",
        "HMC", "STLA",

        # crypto related
        "MARA", "RIOT", "CLSK", "HUT", "BITF",

        # other popular
        "BX", "KKR", "APO", "ARES", "OWL",
        "VMW", "DELL", "HPQ", "HPE",
        "ZM", "DOCU", "OKTA", "TWLO", "MDB", "ESTC", "CFLT",
        "PATH", "AI", "BBAI", "IONQ", "RGTI",
        "SOFI", "AFRM", "UPST", "LC",
        "DKNG", "PENN", "MGM", "WYNN", "LVS", "CZR",
        "MAR", "HLT", "H", "RCL", "CCL", "NCLH",
        "DAL", "UAL", "LUV", "AAL", "ALK", "JBLU",
        "PARA", "WBD", "FOX", "FOXA", "NYT", "NWSA",
        "SE", "GRAB", "BABA", "JD", "PDD", "BIDU", "BILI",
    ]

    # remove duplicates and sort
    tickers = sorted(list(set(tickers)))

    # save the list for future use
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'w') as f:
        json.dump(tickers, f)

    _nasdaq_cache = tickers
    return tickers


def get_realtime_data(ticker, period='5d', interval='15m'):
    """Fetch recent price data for any ticker using yfinance.
    Uses yf.download() which is more reliable than Ticker.history().

    For intraday intervals, we map period to start/end dates.
    """
    try:
        import subprocess, io

        # yf.download fails inside uvicorn due to threading issues
        # so we run it in a subprocess as a workaround
        script = f"""
import yfinance as yf, sys
df = yf.download('{ticker}', period='{period}', progress=False)
if hasattr(df.columns, 'droplevel'):
    try: df.columns = df.columns.droplevel('Ticker')
    except: pass
df.to_csv(sys.stdout)
"""
        result = subprocess.run(
            ['python3', '-c', script],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None

        df = pd.read_csv(io.StringIO(result.stdout), index_col='Date', parse_dates=True)

        # flatten multi-level columns if present
        if hasattr(df.columns, 'droplevel'):
            try:
                df.columns = df.columns.droplevel('Ticker')
            except:
                pass

        if df.empty:
            return None

        # build response
        prices = []
        for idx, row in df.iterrows():
            try:
                dt_str = str(idx)[:10]
            except:
                dt_str = str(idx)[:16]

            prices.append({
                'datetime': dt_str,
                'open': round(float(row['Open']), 2),
                'high': round(float(row['High']), 2),
                'low': round(float(row['Low']), 2),
                'close': round(float(row['Close']), 2),
                'volume': int(row['Volume'])
            })

        # current price is the last close
        current_price = prices[-1]['close'] if prices else 0
        info = {
            'current_price': current_price,
            'market_cap': 0,
            'currency': 'USD',
        }

        return {
            'ticker': ticker,
            'period': period,
            'interval': interval,
            'data_points': len(prices),
            'prices': prices,
            'info': info
        }
    except Exception as e:
        return None


def get_ticker_info(ticker):
    """Get basic info about a stock ticker.
    Uses yf.download for the latest price since Ticker.info can fail."""
    if ticker in _ticker_info_cache:
        return _ticker_info_cache[ticker]

    result = {
        'ticker': ticker,
        'name': ticker,
        'sector': 'N/A',
        'industry': 'N/A',
        'market_cap': 0,
        'currency': 'USD',
        'exchange': 'N/A',
    }

    # try to get latest price via download
    try:
        from datetime import datetime, timedelta
        end = datetime.now()
        start = end - timedelta(days=5)
        df = yf.download(ticker, start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
        if not df.empty:
            if hasattr(df.columns, 'droplevel'):
                try:
                    df.columns = df.columns.droplevel('Ticker')
                except:
                    pass
            result['current_price'] = round(float(df['Close'].values[-1]), 2)
    except:
        pass

    _ticker_info_cache[ticker] = result
    return result

"""
realtime.py
Real-time stock data fetching and NASDAQ ticker listing.
Uses Yahoo Finance chart API directly via requests for reliable Docker support.

Mehmet Tanil Kaplan - T0429362
"""

import requests
import os
import json
from datetime import datetime, timedelta

# cache the nasdaq list in memory after first load
_nasdaq_cache = None
_ticker_info_cache = {}

# period to Yahoo Finance range/interval mapping
_PERIOD_MAP = {
    '1d': ('1d', '5m'),
    '5d': ('5d', '15m'),
    '1mo': ('1mo', '1d'),
    '3mo': ('3mo', '1d'),
    '6mo': ('6mo', '1d'),
    '1y': ('1y', '1d'),
    '5y': ('5y', '1wk'),
}


def _fetch_yahoo_chart(ticker, period='5d'):
    """Fetch price data directly from Yahoo Finance chart API."""
    yf_range, yf_interval = _PERIOD_MAP.get(period, ('5d', '15m'))

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {
        'range': yf_range,
        'interval': yf_interval,
        'includePrePost': 'false',
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    result = data.get('chart', {}).get('result')
    if not result:
        return None

    chart = result[0]
    timestamps = chart.get('timestamp', [])
    quote = chart.get('indicators', {}).get('quote', [{}])[0]

    opens = quote.get('open', [])
    highs = quote.get('high', [])
    lows = quote.get('low', [])
    closes = quote.get('close', [])
    volumes = quote.get('volume', [])

    prices = []
    for i, ts in enumerate(timestamps):
        if closes[i] is None:
            continue
        dt = datetime.utcfromtimestamp(ts)
        prices.append({
            'datetime': dt.strftime('%Y-%m-%d'),
            'open': round(float(opens[i] or 0), 2),
            'high': round(float(highs[i] or 0), 2),
            'low': round(float(lows[i] or 0), 2),
            'close': round(float(closes[i] or 0), 2),
            'volume': int(volumes[i] or 0)
        })

    return prices


def get_nasdaq_tickers():
    """Return a list of popular US and UK stocks.
    Includes major NASDAQ/NYSE tickers and London Stock Exchange (.L suffix) tickers."""
    global _nasdaq_cache

    if _nasdaq_cache is not None:
        return _nasdaq_cache

    # check if we have a cached file
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_path = os.path.join(base, 'data', 'nasdaq_tickers.json')

    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            cached = json.load(f)
        # check if UK stocks are present, if not regenerate
        if any(t.endswith('.L') for t in cached):
            _nasdaq_cache = cached
            return _nasdaq_cache

    # === US STOCKS (NASDAQ / NYSE) ===
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

        # other popular US
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

        # === UK STOCKS (London Stock Exchange — .L suffix) ===

        # FTSE 100 — top blue chips
        "SHEL.L", "AZN.L", "HSBA.L", "ULVR.L", "BP.L", "GSK.L",
        "RIO.L", "LSEG.L", "REL.L", "DGE.L", "BATS.L", "NG.L",
        "CRH.L", "CPG.L", "AAL.L", "GLEN.L", "VOD.L", "PRU.L",
        "LLOY.L", "BARC.L", "NWG.L", "STAN.L", "HSBC.L",
        "EXPN.L", "RKT.L", "SMT.L", "SSE.L", "SVT.L",
        "ABF.L", "ANTO.L", "BA.L", "BKG.L", "BNZL.L",
        "CCH.L", "CNA.L", "ENT.L", "FLTR.L", "FRES.L",
        "HIK.L", "HLN.L", "HWDN.L", "IAG.L", "IHG.L",
        "IMB.L", "INF.L", "ITRK.L", "ITV.L", "JD.L",
        "KGF.L", "LAND.L", "LGEN.L", "MNG.L", "MNDI.L",
        "MRO.L", "PHNX.L", "PSON.L", "PSN.L", "RMV.L",
        "RS1.L", "RTO.L", "SBRY.L", "SDR.L", "SGE.L",
        "SGRO.L", "SN.L", "SPX.L", "STJ.L", "TSCO.L",
        "TW.L", "WPP.L", "WTB.L",

        # FTSE 250 — popular mid-caps
        "AUTO.L", "BME.L", "BDEV.L", "DARK.L", "DPLM.L",
        "GAW.L", "HLMA.L", "IGG.L", "III.L", "JET2.L",
        "MGGT.L", "OXIG.L", "PAGE.L", "RWS.L", "SFOR.L",
        "TRN.L", "WEIR.L", "WHR.L", "WOSG.L",

        # popular UK ETFs and investment trusts
        "ISF.L", "VUKE.L", "VMID.L", "VWRL.L", "VUSA.L",
        "CSP1.L", "SWDA.L", "EQQQ.L",
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
    """Fetch recent price data using Yahoo Finance chart API directly."""
    try:
        prices = _fetch_yahoo_chart(ticker, period)

        if not prices:
            return None

        current_price = prices[-1]['close']
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
        print(f"Realtime data error for {ticker}: {e}")
        return None


def get_ticker_info(ticker):
    """Get basic info about a stock ticker."""
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

    try:
        prices = _fetch_yahoo_chart(ticker, '5d')
        if prices:
            result['current_price'] = prices[-1]['close']
    except:
        pass

    _ticker_info_cache[ticker] = result
    return result

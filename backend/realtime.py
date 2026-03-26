"""
realtime.py
Real-time stock data fetching and NASDAQ ticker listing.
Uses yfinance library for reliable Yahoo Finance data access.

Mehmet Tanil Kaplan - T0429362
"""

import os
import json
import yfinance as yf
from datetime import datetime, timedelta

# cache the nasdaq list in memory after first load
_nasdaq_cache = None
_ticker_info_cache = {}

# company names for display in the UI
COMPANY_NAMES = {
    # US — mega cap tech
    "AAPL": "Apple Inc.", "MSFT": "Microsoft Corp.", "GOOGL": "Alphabet (Google)",
    "GOOG": "Alphabet Class C", "AMZN": "Amazon.com", "NVDA": "NVIDIA Corp.",
    "META": "Meta Platforms", "TSLA": "Tesla Inc.", "AVGO": "Broadcom Inc.",
    "ORCL": "Oracle Corp.", "ADBE": "Adobe Inc.", "CRM": "Salesforce",
    "CSCO": "Cisco Systems", "ACN": "Accenture", "IBM": "IBM Corp.",
    "INTC": "Intel Corp.", "AMD": "Advanced Micro Devices", "QCOM": "Qualcomm",
    "TXN": "Texas Instruments", "INTU": "Intuit Inc.", "AMAT": "Applied Materials",
    "NOW": "ServiceNow", "ISRG": "Intuitive Surgical", "LRCX": "Lam Research",
    "MU": "Micron Technology", "ADI": "Analog Devices", "KLAC": "KLA Corp.",
    "SNPS": "Synopsys", "CDNS": "Cadence Design", "MRVL": "Marvell Technology",
    "FTNT": "Fortinet", "PANW": "Palo Alto Networks", "CRWD": "CrowdStrike",
    "WDAY": "Workday", "TEAM": "Atlassian", "DDOG": "Datadog",
    "ZS": "Zscaler", "NET": "Cloudflare", "SNOW": "Snowflake",
    "PLTR": "Palantir Technologies", "MSTR": "MicroStrategy", "COIN": "Coinbase",
    "HOOD": "Robinhood Markets", "SQ": "Block (Square)", "PYPL": "PayPal",
    "SHOP": "Shopify", "ROKU": "Roku Inc.", "SNAP": "Snap Inc.",
    "PINS": "Pinterest", "SPOT": "Spotify", "UBER": "Uber Technologies",
    "LYFT": "Lyft Inc.", "ABNB": "Airbnb", "DASH": "DoorDash",
    "RBLX": "Roblox", "U": "Unity Software", "TTD": "The Trade Desk",
    "TTWO": "Take-Two Interactive", "EA": "Electronic Arts", "ATVI": "Activision Blizzard",
    "NFLX": "Netflix", "DIS": "Walt Disney", "CMCSA": "Comcast",
    "T": "AT&T", "VZ": "Verizon", "TMUS": "T-Mobile US",
    # US — healthcare
    "UNH": "UnitedHealth Group", "JNJ": "Johnson & Johnson", "LLY": "Eli Lilly",
    "ABBV": "AbbVie", "MRK": "Merck & Co.", "PFE": "Pfizer",
    "TMO": "Thermo Fisher", "ABT": "Abbott Laboratories", "DHR": "Danaher",
    "BMY": "Bristol-Myers Squibb", "AMGN": "Amgen", "GILD": "Gilead Sciences",
    "VRTX": "Vertex Pharmaceuticals", "REGN": "Regeneron", "MRNA": "Moderna",
    "BIIB": "Biogen", "ILMN": "Illumina", "DXCM": "DexCom",
    "IDXX": "IDEXX Laboratories", "ZBH": "Zimmer Biomet", "SYK": "Stryker",
    "BDX": "Becton Dickinson", "EW": "Edwards Lifesciences", "BSX": "Boston Scientific",
    "HCA": "HCA Healthcare", "CI": "Cigna Group", "ELV": "Elevance Health",
    "CVS": "CVS Health", "MCK": "McKesson", "GEHC": "GE HealthCare",
    # US — finance
    "BRK-B": "Berkshire Hathaway", "JPM": "JPMorgan Chase", "V": "Visa",
    "MA": "Mastercard", "BAC": "Bank of America", "WFC": "Wells Fargo",
    "GS": "Goldman Sachs", "MS": "Morgan Stanley", "C": "Citigroup",
    "AXP": "American Express", "BLK": "BlackRock", "SCHW": "Charles Schwab",
    "CB": "Chubb Ltd.", "MMC": "Marsh McLennan", "ICE": "Intercontinental Exchange",
    "CME": "CME Group", "AON": "Aon plc", "PGR": "Progressive Corp.",
    "TRV": "Travelers", "MET": "MetLife", "AIG": "AIG",
    "PRU": "Prudential Financial", "ALL": "Allstate", "AFL": "Aflac",
    "SPGI": "S&P Global", "MCO": "Moody's", "MSCI": "MSCI Inc.",
    "FIS": "Fidelity National", "FISV": "Fiserv", "GPN": "Global Payments",
    # US — consumer
    "WMT": "Walmart", "PG": "Procter & Gamble", "KO": "Coca-Cola",
    "PEP": "PepsiCo", "COST": "Costco", "HD": "Home Depot",
    "MCD": "McDonald's", "NKE": "Nike", "SBUX": "Starbucks",
    "TGT": "Target", "LOW": "Lowe's", "TJX": "TJX Companies",
    "ROST": "Ross Stores", "DG": "Dollar General", "DLTR": "Dollar Tree",
    "LULU": "Lululemon", "YUM": "Yum! Brands", "CMG": "Chipotle",
    "DPZ": "Domino's Pizza", "QSR": "Restaurant Brands", "MNST": "Monster Beverage",
    "KDP": "Keurig Dr Pepper", "STZ": "Constellation Brands", "TAP": "Molson Coors",
    "CL": "Colgate-Palmolive", "EL": "Estee Lauder", "KMB": "Kimberly-Clark",
    "GIS": "General Mills", "K": "Kellanova", "CPB": "Campbell Soup",
    "SJM": "J.M. Smucker", "HSY": "Hershey", "HRL": "Hormel Foods",
    "MKC": "McCormick", "CLX": "Clorox",
    # US — industrial
    "CAT": "Caterpillar", "DE": "Deere & Company", "HON": "Honeywell",
    "UNP": "Union Pacific", "UPS": "UPS", "FDX": "FedEx",
    "BA": "Boeing", "RTX": "RTX Corp.", "LMT": "Lockheed Martin",
    "NOC": "Northrop Grumman", "GD": "General Dynamics", "GE": "GE Aerospace",
    "MMM": "3M Company", "EMR": "Emerson Electric", "ITW": "Illinois Tool Works",
    "PH": "Parker-Hannifin", "ROK": "Rockwell Automation", "SWK": "Stanley Black & Decker",
    "TT": "Trane Technologies", "CARR": "Carrier Global", "OTIS": "Otis Worldwide",
    "JCI": "Johnson Controls", "AOS": "A.O. Smith", "WM": "Waste Management",
    "RSG": "Republic Services", "VRSK": "Verisk Analytics", "CTAS": "Cintas",
    "FAST": "Fastenal", "PAYX": "Paychex", "ADP": "ADP",
    # US — energy
    "XOM": "ExxonMobil", "CVX": "Chevron", "COP": "ConocoPhillips",
    "SLB": "Schlumberger", "EOG": "EOG Resources", "MPC": "Marathon Petroleum",
    "PSX": "Phillips 66", "VLO": "Valero Energy", "OXY": "Occidental Petroleum",
    "HAL": "Halliburton", "DVN": "Devon Energy", "FANG": "Diamondback Energy",
    "HES": "Hess Corp.", "BKR": "Baker Hughes", "KMI": "Kinder Morgan",
    "WMB": "Williams Companies", "OKE": "ONEOK", "TRGP": "Targa Resources",
    # US — real estate & utilities
    "AMT": "American Tower", "PLD": "Prologis", "CCI": "Crown Castle",
    "EQIX": "Equinix", "PSA": "Public Storage", "SPG": "Simon Property Group",
    "O": "Realty Income", "DLR": "Digital Realty", "WELL": "Welltower",
    "AVB": "AvalonBay", "EQR": "Equity Residential", "VTR": "Ventas",
    "ARE": "Alexandria Real Estate", "MAA": "Mid-America Apartment", "UDR": "UDR Inc.",
    "NEE": "NextEra Energy", "DUK": "Duke Energy", "SO": "Southern Company",
    "D": "Dominion Energy", "AEP": "American Electric Power", "SRE": "Sempra",
    "EXC": "Exelon", "XEL": "Xcel Energy", "ED": "Consolidated Edison",
    "WEC": "WEC Energy", "ES": "Eversource Energy", "AEE": "Ameren",
    "CMS": "CMS Energy", "DTE": "DTE Energy", "ETR": "Entergy", "FE": "FirstEnergy",
    # US — materials
    "LIN": "Linde plc", "APD": "Air Products", "SHW": "Sherwin-Williams",
    "ECL": "Ecolab", "DD": "DuPont", "NEM": "Newmont",
    "FCX": "Freeport-McMoRan", "DOW": "Dow Inc.", "NUE": "Nucor",
    "STLD": "Steel Dynamics", "CF": "CF Industries", "MOS": "Mosaic",
    "ALB": "Albemarle", "CTVA": "Corteva", "FMC": "FMC Corp.",
    # US — semiconductor
    "TSM": "Taiwan Semiconductor", "ASML": "ASML Holding", "ARM": "Arm Holdings",
    "SMCI": "Super Micro Computer", "ON": "ON Semiconductor", "NXPI": "NXP Semiconductors",
    "MCHP": "Microchip Technology", "SWKS": "Skyworks", "MPWR": "Monolithic Power",
    "ENTG": "Entegris", "ONTO": "Onto Innovation",
    # US — EV & auto
    "RIVN": "Rivian", "LCID": "Lucid Group", "NIO": "NIO Inc.",
    "XPEV": "XPeng", "LI": "Li Auto", "GM": "General Motors",
    "F": "Ford Motor", "TM": "Toyota Motor", "HMC": "Honda Motor", "STLA": "Stellantis",
    # US — crypto
    "MARA": "Marathon Digital", "RIOT": "Riot Platforms", "CLSK": "CleanSpark",
    "HUT": "Hut 8 Corp.", "BITF": "Bitfarms",
    # US — other popular
    "BX": "Blackstone", "KKR": "KKR & Co.", "APO": "Apollo Global", "ARES": "Ares Management", "OWL": "Blue Owl Capital",
    "VMW": "VMware", "DELL": "Dell Technologies", "HPQ": "HP Inc.", "HPE": "Hewlett Packard Enterprise",
    "ZM": "Zoom Video", "DOCU": "DocuSign", "OKTA": "Okta", "TWLO": "Twilio",
    "MDB": "MongoDB", "ESTC": "Elastic", "CFLT": "Confluent",
    "PATH": "UiPath", "AI": "C3.ai", "BBAI": "BigBear.ai", "IONQ": "IonQ", "RGTI": "Rigetti Computing",
    "SOFI": "SoFi Technologies", "AFRM": "Affirm", "UPST": "Upstart", "LC": "LendingClub",
    "DKNG": "DraftKings", "PENN": "Penn Entertainment", "MGM": "MGM Resorts",
    "WYNN": "Wynn Resorts", "LVS": "Las Vegas Sands", "CZR": "Caesars Entertainment",
    "MAR": "Marriott", "HLT": "Hilton", "H": "Hyatt Hotels",
    "RCL": "Royal Caribbean", "CCL": "Carnival Corp.", "NCLH": "Norwegian Cruise Line",
    "DAL": "Delta Air Lines", "UAL": "United Airlines", "LUV": "Southwest Airlines",
    "AAL": "American Airlines", "ALK": "Alaska Air", "JBLU": "JetBlue Airways",
    "PARA": "Paramount Global", "WBD": "Warner Bros. Discovery", "FOX": "Fox Corp.",
    "FOXA": "Fox Corp. Class A", "NYT": "New York Times", "NWSA": "News Corp.",
    "SE": "Sea Ltd.", "GRAB": "Grab Holdings", "BABA": "Alibaba",
    "JD": "JD.com", "PDD": "PDD Holdings", "BIDU": "Baidu", "BILI": "Bilibili",

    # === UK STOCKS (London Stock Exchange) ===
    # FTSE 100
    "SHEL.L": "Shell plc", "AZN.L": "AstraZeneca", "HSBA.L": "HSBC Holdings",
    "ULVR.L": "Unilever", "BP.L": "BP plc", "GSK.L": "GSK plc",
    "RIO.L": "Rio Tinto", "LSEG.L": "London Stock Exchange Group",
    "REL.L": "RELX plc", "DGE.L": "Diageo", "BATS.L": "British American Tobacco",
    "NG.L": "National Grid", "CRH.L": "CRH plc", "CPG.L": "Compass Group",
    "AAL.L": "Anglo American", "GLEN.L": "Glencore", "VOD.L": "Vodafone Group",
    "PRU.L": "Prudential plc", "LLOY.L": "Lloyds Banking Group",
    "BARC.L": "Barclays", "NWG.L": "NatWest Group", "STAN.L": "Standard Chartered",
    "HSBC.L": "HSBC Holdings", "EXPN.L": "Experian", "RKT.L": "Reckitt Benckiser",
    "SMT.L": "Scottish Mortgage IT", "SSE.L": "SSE plc", "SVT.L": "Severn Trent",
    "ABF.L": "Associated British Foods", "ANTO.L": "Antofagasta",
    "BA.L": "BAE Systems", "BKG.L": "Berkeley Group", "BNZL.L": "Bunzl",
    "CCH.L": "Coca-Cola HBC", "CNA.L": "Centrica", "ENT.L": "Entain",
    "FLTR.L": "Flutter Entertainment", "FRES.L": "Fresnillo",
    "HIK.L": "Hikma Pharmaceuticals", "HLN.L": "Haleon",
    "HWDN.L": "Howden Joinery", "IAG.L": "International Airlines Group",
    "IHG.L": "InterContinental Hotels", "IMB.L": "Imperial Brands",
    "INF.L": "Informa", "ITRK.L": "Intertek Group", "ITV.L": "ITV plc",
    "JD.L": "JD Sports Fashion", "KGF.L": "Kingfisher", "LAND.L": "Land Securities",
    "LGEN.L": "Legal & General", "MNG.L": "M&G plc", "MNDI.L": "Mondi",
    "MRO.L": "Melrose Industries", "PHNX.L": "Phoenix Group",
    "PSON.L": "Pearson", "PSN.L": "Persimmon", "RMV.L": "Rightmove",
    "RS1.L": "RS Group", "RTO.L": "Rentokil Initial", "SBRY.L": "Sainsbury's",
    "SDR.L": "Schroders", "SGE.L": "Sage Group", "SGRO.L": "Segro",
    "SN.L": "Smith & Nephew", "SPX.L": "Spirax Group", "STJ.L": "St James's Place",
    "TSCO.L": "Tesco", "TW.L": "Taylor Wimpey", "WPP.L": "WPP plc", "WTB.L": "Whitbread",
    # FTSE 250
    "AUTO.L": "Auto Trader Group", "BME.L": "B&M European Value Retail",
    "BDEV.L": "Barratt Developments", "DARK.L": "Darktrace",
    "DPLM.L": "Diploma plc", "GAW.L": "Games Workshop",
    "HLMA.L": "Halma plc", "IGG.L": "IG Group", "III.L": "3i Group",
    "JET2.L": "Jet2 plc", "MGGT.L": "Meggitt", "OXIG.L": "Oxford Instruments",
    "PAGE.L": "PageGroup", "RWS.L": "RWS Holdings", "SFOR.L": "S4 Capital",
    "TRN.L": "Trainline", "WEIR.L": "Weir Group", "WHR.L": "Warehouse REIT",
    "WOSG.L": "Watches of Switzerland",
    # UK ETFs
    "ISF.L": "iShares Core FTSE 100", "VUKE.L": "Vanguard FTSE 100",
    "VMID.L": "Vanguard FTSE 250", "VWRL.L": "Vanguard FTSE All-World",
    "VUSA.L": "Vanguard S&P 500", "CSP1.L": "iShares Core S&P 500",
    "SWDA.L": "iShares Core MSCI World", "EQQQ.L": "Invesco NASDAQ-100",
}

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
    """Fetch price data using yfinance library (handles Yahoo auth automatically)."""
    yf_range, yf_interval = _PERIOD_MAP.get(period, ('5d', '15m'))

    try:
        t = yf.Ticker(ticker)
        df = t.history(period=yf_range, interval=yf_interval, prepost=False)

        if df is None or df.empty:
            return None

        prices = []
        for idx, row in df.iterrows():
            close_val = row.get('Close')
            if close_val is None or (hasattr(close_val, '__float__') and str(close_val) == 'nan'):
                continue
            dt = idx.to_pydatetime()
            prices.append({
                'datetime': dt.strftime('%Y-%m-%d %H:%M') if yf_interval in ('1m', '5m', '15m', '30m', '1h') else dt.strftime('%Y-%m-%d'),
                'open': round(float(row.get('Open', 0) or 0), 2),
                'high': round(float(row.get('High', 0) or 0), 2),
                'low': round(float(row.get('Low', 0) or 0), 2),
                'close': round(float(close_val), 2),
                'volume': int(row.get('Volume', 0) or 0)
            })

        return prices if prices else None
    except Exception as e:
        print(f"yfinance fetch error for {ticker}: {e}")
        return None


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
    """Get basic info about a stock ticker using yfinance."""
    if ticker in _ticker_info_cache:
        return _ticker_info_cache[ticker]

    result = {
        'ticker': ticker,
        'name': COMPANY_NAMES.get(ticker, ticker),
        'sector': 'N/A',
        'industry': 'N/A',
        'market_cap': 0,
        'currency': 'USD',
        'exchange': 'N/A',
    }

    try:
        t = yf.Ticker(ticker)
        info = t.info or {}

        if info.get('sector'):
            result['sector'] = info['sector']
        if info.get('industry'):
            result['industry'] = info['industry']
        if info.get('exchange'):
            result['exchange'] = info['exchange']
        if info.get('currency'):
            result['currency'] = info['currency']
        if info.get('marketCap'):
            result['market_cap'] = info['marketCap']
        if info.get('currentPrice'):
            result['current_price'] = round(float(info['currentPrice']), 2)
        elif info.get('regularMarketPrice'):
            result['current_price'] = round(float(info['regularMarketPrice']), 2)
        if info.get('shortName'):
            result['name'] = info['shortName']
    except:
        # fallback to chart data for at least the current price
        try:
            prices = _fetch_yahoo_chart(ticker, '5d')
            if prices:
                result['current_price'] = prices[-1]['close']
        except:
            pass

    _ticker_info_cache[ticker] = result
    return result

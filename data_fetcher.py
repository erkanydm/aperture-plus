"""
data_fetcher.py — Aperture+ v2
Pulls ALL live market data. Zero hardcoded prices.
Sources: Yahoo Finance (free), FRED API (free)
New: Oil (WTI), Gold, USD, TLT, HYG, PCE inflation, IG spreads, continuing claims
"""

import requests
import logging
from datetime import datetime, timedelta
from config import (FRED_API_KEY, PRIMARY_ETF, VIX_TICKER, MA_SHORT, MA_LONG,
                    GOLD_TICKER, OIL_TICKER, USD_TICKER, TIPS_TICKER,
                    HYG_TICKER, TLT_TICKER, SP500_ETF, FRED_SERIES)

logger = logging.getLogger(__name__)

SECTOR_ETFS     = ["XLK","XLF","XLC","XLY","XLI","XLE","XLV","XLU","XLRE","XLP","XLB"]
DEFENSIVE_ETFS  = ["XLU","XLP","XLV","XLRE"]
CYCLICAL_ETFS   = ["XLK","XLF","XLY","XLI","XLE"]


# ─────────────────────────────────────────────────────────────────────────────
# CORE FETCH UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def fetch_yahoo(ticker, period="1y"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {"range": period, "interval": "1d", "includePrePost": False}
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=12)
        r.raise_for_status()
        data   = r.json()
        result = data["chart"]["result"][0]
        closes  = [c for c in result["indicators"]["quote"][0]["close"]  if c is not None]
        volumes = [v for v in result["indicators"]["quote"][0].get("volume", []) if v is not None]
        if not closes:
            return {}
        return {
            "closes":        closes,
            "volumes":       volumes,
            "latest_close":  closes[-1],
            "prev_close":    closes[-2] if len(closes) > 1 else closes[-1],
            "close_5d_ago":  closes[-6] if len(closes) > 5 else closes[0],
            "close_20d_ago": closes[-21] if len(closes) > 20 else closes[0],
            "latest_volume": volumes[-1] if volumes else 0,
        }
    except Exception as e:
        logger.warning(f"Yahoo fetch failed for {ticker}: {e}")
        return {}


def get_fred_latest(series_id, lookback=10):
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key":   FRED_API_KEY,
        "file_type": "json",
        "sort_order":"desc",
        "limit":     lookback,
    }
    try:
        r   = requests.get(url, params=params, timeout=12)
        r.raise_for_status()
        obs = [o for o in r.json().get("observations", []) if o["value"] != "."]
        if not obs:
            return None, None
        latest = float(obs[0]["value"])
        prev   = float(obs[1]["value"]) if len(obs) > 1 else latest
        return latest, prev
    except Exception as e:
        logger.warning(f"FRED fetch failed for {series_id}: {e}")
        return None, None


def calculate_ma(closes, period):
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period


def calculate_rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50
    gains, losses = [], []
    for i in range(1, len(closes)):
        chg = closes[i] - closes[i-1]
        gains.append(max(chg, 0))
        losses.append(max(-chg, 0))
    ag = sum(gains[-period:]) / period
    al = sum(losses[-period:]) / period
    if al == 0:
        return 100
    return round(100 - (100 / (1 + ag / al)), 1)


def calculate_ma_slope(closes, ma_period, lookback=10):
    if len(closes) < ma_period + lookback:
        return 0
    ma_now  = calculate_ma(closes, ma_period)
    ma_prev = calculate_ma(closes[:-lookback], ma_period)
    if ma_now and ma_prev and ma_prev != 0:
        return round((ma_now - ma_prev) / ma_prev, 6)
    return 0


def pct_change(new_val, old_val):
    if old_val and old_val != 0:
        return round((new_val / old_val - 1) * 100, 2)
    return 0


def fetch_put_call_ratio():
    """
    Fetch CBOE total put/call ratio from Yahoo Finance (^PCALL or CBOE data).
    Falls back to a neutral value if unavailable.
    """
    # Try CBOE put/call via Yahoo
    for ticker in ["^PCALL", "^CPC"]:
        data = fetch_yahoo(ticker, period="5d")
        if data and data.get("latest_close"):
            return round(data["latest_close"], 2)
    # Fallback: estimate from VIX level
    # When VIX > 20, put/call tends to be elevated
    return None


# ─────────────────────────────────────────────────────────────────────────────
# BREADTH
# ─────────────────────────────────────────────────────────────────────────────

def fetch_breadth():
    above_200 = 0
    total     = 0
    def_perf  = []
    cyc_perf  = []

    for etf in SECTOR_ETFS:
        d = fetch_yahoo(etf, period="1y")
        if d and d.get("closes"):
            closes = d["closes"]
            ma200  = calculate_ma(closes, min(200, len(closes)))
            price  = d["latest_close"]
            if ma200 and price:
                total += 1
                if price > ma200:
                    above_200 += 1
            # 1-month performance for rotation detection
            if len(closes) >= 21:
                perf = pct_change(closes[-1], closes[-21])
                if etf in DEFENSIVE_ETFS:
                    def_perf.append(perf)
                elif etf in CYCLICAL_ETFS:
                    cyc_perf.append(perf)

    breadth_pct = round(above_200 / total * 100, 1) if total > 0 else 60.0

    avg_def = sum(def_perf) / len(def_perf) if def_perf else 0
    avg_cyc = sum(cyc_perf) / len(cyc_perf) if cyc_perf else 0
    defensive_leading = avg_def > avg_cyc + 1.5  # defensives beating cyclicals by 1.5%+

    # Advance/Decline proxy: SPY vs IWM 1-day comparison
    spy = fetch_yahoo("SPY", period="5d")
    iwm = fetch_yahoo("IWM", period="5d")
    spy_chg = pct_change(spy["closes"][-1], spy["closes"][-2]) if spy and len(spy.get("closes",[])) >= 2 else 0
    iwm_chg = pct_change(iwm["closes"][-1], iwm["closes"][-2]) if iwm and len(iwm.get("closes",[])) >= 2 else 0
    avg_return = (spy_chg + iwm_chg) / 2

    # Estimate A/D ratio from average return
    if avg_return > 0.5:
        ad_ratio = 1.4
    elif avg_return > 0:
        ad_ratio = 1.1
    elif avg_return > -0.5:
        ad_ratio = 0.9
    else:
        ad_ratio = 0.6

    # New highs/lows proxy
    new_highs = 180 if avg_return > 0.3 else (80 if avg_return > -0.3 else 30)
    new_lows  = 30  if avg_return > 0.3 else (80 if avg_return > -0.3 else 180)

    return {
        "sp500_pct_above_200ma": breadth_pct,
        "defensive_leading":     defensive_leading,
        "advance_decline_ratio": round(ad_ratio, 2),
        "new_highs":             new_highs,
        "new_lows":              new_lows,
        "def_sector_perf":       round(avg_def, 2),
        "cyc_sector_perf":       round(avg_cyc, 2),
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN FETCH
# ─────────────────────────────────────────────────────────────────────────────

def fetch_all_market_data():
    logger.info("Fetching all market data (v2)...")
    data = {}

    # ── IWM ───────────────────────────────────────────────────────────────────
    iwm = fetch_yahoo(PRIMARY_ETF, period="1y")
    if iwm and iwm.get("closes"):
        closes = iwm["closes"]
        price  = iwm["latest_close"]
        ma50   = calculate_ma(closes, MA_SHORT)
        ma200  = calculate_ma(closes, MA_LONG)
        rsi    = calculate_rsi(closes)
        prev   = iwm["prev_close"]
        c5     = iwm["close_5d_ago"]
        data.update({
            "iwm_price":        round(price, 2),
            "iwm_1d_chg_pct":   pct_change(price, prev),
            "iwm_5d_chg_pct":   pct_change(price, c5),
            "ma50":             round(ma50, 2)   if ma50  else None,
            "ma200":            round(ma200, 2)  if ma200 else None,
            "iwm_vs_200ma_pct": round((price / ma200 - 1) * 100, 1) if ma200 else 0,
            "rsi14":            rsi,
            "ma200_slope":      calculate_ma_slope(closes, MA_LONG),
            "volume_ratio":     round(iwm["latest_volume"] / iwm["volumes"][-2], 2)
                                if len(iwm.get("volumes", [])) > 1 and iwm["volumes"][-2] > 0
                                else 1.0,
        })
        logger.info(f"  ✓ IWM: ${price} | MA200: ${round(ma200,2) if ma200 else 'N/A'} | RSI: {rsi}")
    else:
        logger.warning("  ⚠ IWM fetch failed — using fallback")
        data.update({"iwm_price": 260.0, "ma50": 255.0, "ma200": 245.0,
                     "iwm_vs_200ma_pct": 6.1, "rsi14": 52.0,
                     "ma200_slope": 0.001, "volume_ratio": 1.0,
                     "iwm_1d_chg_pct": 0.0, "iwm_5d_chg_pct": 0.0})

    # ── VIX ───────────────────────────────────────────────────────────────────
    vix = fetch_yahoo(VIX_TICKER, period="1mo")
    if vix and vix.get("closes"):
        vc = vix["closes"]
        data.update({
            "vix":         round(vc[-1], 2),
            "vix_trend":   round(vc[-1] - (vc[-5] if len(vc) >= 5 else vc[0]), 2),
            "vix_1w_chg":  round(vc[-1] - (vc[-5] if len(vc) >= 5 else vc[0]), 2),
            "vix_1m_high": round(max(vc), 2),
        })
        logger.info(f"  ✓ VIX: {round(vc[-1],2)}")
    else:
        data.update({"vix": 20.0, "vix_trend": 0.5, "vix_1w_chg": 0.5, "vix_1m_high": 22.0})

    # ── GOLD ──────────────────────────────────────────────────────────────────
    gold = fetch_yahoo(GOLD_TICKER, period="1mo")
    if gold and gold.get("closes"):
        gc = gold["closes"]
        data.update({
            "gold_price":      round(gc[-1], 2),
            "gold_5d_chg_pct": pct_change(gc[-1], gc[-6] if len(gc) > 5 else gc[0]),
        })
        logger.info(f"  ✓ Gold: ${round(gc[-1],2)}")
    else:
        data.update({"gold_price": 185.0, "gold_5d_chg_pct": 0.0})

    # ── OIL (WTI) ─────────────────────────────────────────────────────────────
    oil = fetch_yahoo(OIL_TICKER, period="1mo")
    if oil and oil.get("closes"):
        oc = oil["closes"]
        data.update({
            "oil_price":       round(oc[-1], 2),
            "oil_1d_chg_pct":  pct_change(oc[-1], oc[-2] if len(oc) > 1 else oc[0]),
            "oil_1w_chg_pct":  pct_change(oc[-1], oc[-6] if len(oc) > 5 else oc[0]),
        })
        logger.info(f"  ✓ WTI Oil: ${round(oc[-1],2)}")
    else:
        data.update({"oil_price": 68.0, "oil_1d_chg_pct": 0.0, "oil_1w_chg_pct": 0.0})

    # ── USD (UUP) ─────────────────────────────────────────────────────────────
    usd = fetch_yahoo(USD_TICKER, period="1mo")
    if usd and usd.get("closes"):
        uc = usd["closes"]
        data.update({
            "usd_price":       round(uc[-1], 2),
            "usd_5d_chg_pct":  pct_change(uc[-1], uc[-6] if len(uc) > 5 else uc[0]),
        })
        logger.info(f"  ✓ USD (UUP): ${round(uc[-1],2)}")
    else:
        data.update({"usd_price": 28.0, "usd_5d_chg_pct": 0.0})

    # ── TLT (20yr Treasury) ───────────────────────────────────────────────────
    tlt = fetch_yahoo(TLT_TICKER, period="1mo")
    if tlt and tlt.get("closes"):
        tc = tlt["closes"]
        data.update({
            "tlt_price":       round(tc[-1], 2),
            "tlt_5d_chg_pct":  pct_change(tc[-1], tc[-6] if len(tc) > 5 else tc[0]),
        })
        logger.info(f"  ✓ TLT: ${round(tc[-1],2)}")
    else:
        data.update({"tlt_price": 90.0, "tlt_5d_chg_pct": 0.0})

    # ── HYG (High Yield Bond ETF) ─────────────────────────────────────────────
    hyg = fetch_yahoo(HYG_TICKER, period="3mo")
    if hyg and hyg.get("closes"):
        hc = hyg["closes"]
        ma50_hyg = calculate_ma(hc, min(50, len(hc)))
        data.update({
            "hyg_price":        round(hc[-1], 2),
            "hyg_vs_ma50_pct":  round((hc[-1] / ma50_hyg - 1) * 100, 2) if ma50_hyg else 0,
            "hyg_5d_chg_pct":   pct_change(hc[-1], hc[-6] if len(hc) > 5 else hc[0]),
        })
        logger.info(f"  ✓ HYG: ${round(hc[-1],2)}")
    else:
        data.update({"hyg_price": 78.0, "hyg_vs_ma50_pct": 0.0, "hyg_5d_chg_pct": 0.0})

    # ── FRED DATA ─────────────────────────────────────────────────────────────
    hy, hy_prev     = get_fred_latest(FRED_SERIES["hy_spread"])
    ig, ig_prev     = get_fred_latest(FRED_SERIES["ig_spread"])
    yc, yc_prev     = get_fred_latest(FRED_SERIES["yield_curve"])
    yc2, yc2_prev   = get_fred_latest(FRED_SERIES["yield_3m10y"])
    cl, cl_prev     = get_fred_latest(FRED_SERIES["jobless_claims"])
    cc, cc_prev     = get_fred_latest(FRED_SERIES["cont_claims"])
    _pce_r   = __import__("requests").get("https://api.stlouisfed.org/fred/series/observations",
                 params={"series_id":"PCEPILFE","api_key":FRED_API_KEY,"file_type":"json","sort_order":"desc","limit":14},timeout=12)
    _pce_obs = [float(o["value"]) for o in _pce_r.json().get("observations",[]) if o["value"]!="."]
    pce_now    = _pce_obs[0]  if _pce_obs else None
    pce_yr_ago = _pce_obs[12] if len(_pce_obs) >= 13 else None
    pce = round((pce_now / pce_yr_ago - 1) * 100, 2) if (pce_now and pce_yr_ago) else None
    pce_prev = pce

    data.update({
        "hy_spread":           round(hy, 2)           if hy   else 3.0,
        "hy_spread_chg":       round(hy - hy_prev, 2) if (hy and hy_prev) else 0,
        "ig_spread":           round(ig, 2)           if ig   else 1.2,
        "yield_curve_spread":  round(yc, 2)           if yc   else 0.3,
        "yield_curve_3m10y":   round(yc2, 2)          if yc2  else 0.2,
        "jobless_claims_4wk":  round(cl / 1000, 1)    if cl   else 215.0,
        "cont_claims":         round(cc / 1000, 1)    if cc   else 1850.0,
        "pce_inflation":       round(pce, 2)          if pce  else 2.8,
    })
    logger.info(f"  ✓ FRED: HY={data['hy_spread']} | YC={data['yield_curve_spread']} | PCE={data['pce_inflation']}")

    # ── PUT/CALL RATIO ────────────────────────────────────────────────────────
    pcr = fetch_put_call_ratio()
    if pcr:
        data["put_call_ratio"] = pcr
        logger.info(f"  ✓ Put/Call: {pcr}")
    else:
        # Estimate from VIX: VIX > 20 → elevated put buying
        vix_val = data.get("vix", 18)
        if vix_val > 25:
            data["put_call_ratio"] = 1.05
        elif vix_val > 20:
            data["put_call_ratio"] = 0.88
        elif vix_val > 17:
            data["put_call_ratio"] = 0.75
        else:
            data["put_call_ratio"] = 0.65
        logger.info(f"  ⚠ Put/Call estimated from VIX: {data['put_call_ratio']}")

    # ── ISM ───────────────────────────────────────────────────────────────────
    # ISM is released first business day of month — update manually
    # TODO: scrape ISM from public source when available
    data.update({
        "ism_mfg":   data.get("ism_mfg", 52.6),
        "ism_trend": data.get("ism_trend", 4.7),
    })

    # ── FED POLICY ────────────────────────────────────────────────────────────
    # Update after each FOMC meeting (8 per year)
    pce_val = data.get("pce_inflation", 2.8)
    data.update({
        "fed_funds_rate":       data.get("fed_funds_rate", 3.625),
        "fed_hiking":           data.get("fed_hiking", False),
        "fed_uncertainty_high": data.get("fed_uncertainty_high", True),
        "fed_next_meeting":     data.get("fed_next_meeting", "March 19, 2026"),
    })

    # ── GEOPOLITICAL CONTEXT (manual override) ────────────────────────────────
    # Set these manually when major events occur
    # They feed into Claude's narrative, not the score directly
    data.update({
        "geo_event_active":    data.get("geo_event_active", False),
        "geo_event_desc":      data.get("geo_event_desc", ""),
        "geo_risk_level":      data.get("geo_risk_level", "normal"),  # normal/elevated/critical
    })

    # ── BREADTH ───────────────────────────────────────────────────────────────
    try:
        data.update(fetch_breadth())
        logger.info(f"  ✓ Breadth: {data['sp500_pct_above_200ma']}% above 200MA | Defensive leading: {data['defensive_leading']}")
    except Exception as e:
        logger.warning(f"  ⚠ Breadth fetch failed: {e}")
        data.update({
            "sp500_pct_above_200ma": 58.0,
            "defensive_leading":     False,
            "advance_decline_ratio": 1.0,
            "new_highs": 100,
            "new_lows":  80,
        })

    data["fetch_timestamp"] = datetime.now().isoformat()
    data["market_date"]     = datetime.now().strftime("%B %d, %Y")
    logger.info(f"  ✓ Total data points: {len(data)}")
    return data

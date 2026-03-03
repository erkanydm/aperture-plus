"""
config.py — Aperture+ v2 Configuration
Upgraded scoring system: 24 signals across 3 time horizons (Near / Mid / Long)
Each horizon scored separately AND combined into a composite risk score.
"""

import os
from dotenv import load_dotenv
load_dotenv()

# ── API KEYS ──────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY   = os.getenv("ANTHROPIC_API_KEY")
FRED_API_KEY        = os.getenv("FRED_API_KEY")
TIINGO_API_KEY      = os.getenv("TIINGO_API_KEY")
BEEHIIV_API_KEY     = os.getenv("BEEHIIV_API_KEY")
BEEHIIV_PUB_ID      = os.getenv("BEEHIIV_PUBLICATION_ID")

# ── BRAND ─────────────────────────────────────────────────────────────────────
BRAND_NAME          = "Aperture+"
BRAND_TAGLINE       = "See what's coming."
BRAND_WEBSITE       = "https://aperture.plus"
EMAIL_SUBJECT_PREFIX = "Aperture+"

# ── TICKERS ───────────────────────────────────────────────────────────────────
PRIMARY_ETF   = "IWM"
SP500_ETF     = "SPY"
VIX_TICKER    = "^VIX"
GOLD_TICKER   = "GLD"
OIL_TICKER    = "CL=F"       # WTI Crude Oil Futures
USD_TICKER    = "UUP"        # USD Bullish ETF (safe haven proxy)
TIPS_TICKER   = "TIP"        # TIPS ETF (inflation expectations proxy)
HYG_TICKER    = "HYG"        # High Yield Bond ETF (credit stress proxy)
TLT_TICKER    = "TLT"        # 20yr Treasury ETF (duration/rate risk)
MA_SHORT      = 50
MA_LONG       = 200

# ── FRED SERIES ───────────────────────────────────────────────────────────────
FRED_SERIES = {
    "hy_spread":       "BAMLH0A0HYM2",   # High Yield OAS
    "ig_spread":       "BAMLC0A0CM",     # Investment Grade OAS
    "yield_curve":     "T10Y2Y",         # 10yr minus 2yr
    "yield_3m10y":     "T10Y3M",         # 10yr minus 3mo (recession signal)
    "jobless_claims":  "IC4WSA",         # Initial claims (weekly)
    "cont_claims":     "CCSA",           # Continuing claims
    "pce_inflation":      "PCEPILFE",       # Core PCE YoY
    "m2_growth":       "M2SL",           # M2 money supply
}

# ── SCORE LEVELS (per horizon) ────────────────────────────────────────────────
# Near-term: 0-8 signals
NEAR_LEVELS = [
    (0, 2,  "Clear",    "Short-term conditions favorable.",              "#3ECF8E"),
    (3, 5,  "Caution",  "Near-term stress building. Watch key levels.",  "#C9A84C"),
    (6, 8,  "Alert",    "Immediate risk elevated. Reduce exposure.",     "#E05252"),
]

# Mid-term: 0-8 signals
MID_LEVELS = [
    (0, 2,  "Stable",   "Medium-term trend intact.",                     "#3ECF8E"),
    (3, 5,  "Shifting", "Trend deteriorating. Reassess positioning.",    "#C9A84C"),
    (6, 8,  "Broken",   "Medium-term structure damaged. Defensive.",     "#E05252"),
]

# Long-term: 0-8 signals
LONG_LEVELS = [
    (0, 2,  "Healthy",  "Macro backdrop supportive.",                    "#3ECF8E"),
    (3, 5,  "Stressed", "Macro deteriorating. Prepare for volatility.",  "#C9A84C"),
    (6, 8,  "Crisis",   "Macro cycle turning. Maximum caution.",         "#E05252"),
]

# Composite: 0-24 signals
COMPOSITE_LEVELS = [
    (0,  5,  "Low Risk",   "Stay invested. No defensive action needed.",         "#3ECF8E"),
    (6,  11, "Elevated",   "Monitor closely. Consider trimming 20% exposure.",   "#C9A84C"),
    (12, 17, "High Risk",  "Reduce equity exposure significantly. Add hedges.",  "#E07B39"),
    (18, 24, "Crisis",     "Exit or hedge fully. Move to defensive positions.",  "#E05252"),
]

# ── SIGNAL RULES — 24 TOTAL (8 per horizon) ──────────────────────────────────
#
# NEAR-TERM (0–5 trading days): Price action, momentum, sentiment
# MID-TERM  (1–8 weeks):        Trend, breadth, flow, credit
# LONG-TERM (1–6 months):       Macro, cycle, structural
#
SIGNAL_RULES = [

    # ═══════════════════════════════════════════════════
    # NEAR-TERM SIGNALS (8) — horizon: "near"
    # ═══════════════════════════════════════════════════

    {
        "id": "nt_price_ma200",
        "name": "IWM vs 200MA",
        "horizon": "near",
        "pillar": "Technical",
        "crisis_if": lambda d: d.get("iwm_vs_200ma_pct", 5) < -3,
        "description": "IWM more than 3% below 200-day MA — momentum is negative",
        "weight": 1,
    },
    {
        "id": "nt_rsi_weak",
        "name": "RSI Momentum",
        "horizon": "near",
        "pillar": "Technical",
        "crisis_if": lambda d: d.get("rsi14", 50) < 45,
        "description": "RSI below 45 — momentum weakening, buyers losing control",
        "weight": 1,
    },
    {
        "id": "nt_volume_sell",
        "name": "Volume Selling Pressure",
        "horizon": "near",
        "pillar": "Technical",
        "crisis_if": lambda d: d.get("volume_ratio", 1.0) > 1.4 and d.get("iwm_1d_chg_pct", 0) < -0.8,
        "description": "High-volume down day — institutional selling detected",
        "weight": 1,
    },
    {
        "id": "nt_vix_spike",
        "name": "VIX Spike",
        "horizon": "near",
        "pillar": "Sentiment",
        "crisis_if": lambda d: d.get("vix", 15) > 22 or d.get("vix_1w_chg", 0) > 4,
        "description": "VIX above 22 or surged >4pts in a week — fear entering market",
        "weight": 1,
    },
    {
        "id": "nt_put_call",
        "name": "Put/Call Ratio",
        "horizon": "near",
        "pillar": "Sentiment",
        "crisis_if": lambda d: d.get("put_call_ratio", 0.7) > 0.85,
        "description": "Elevated put buying — hedging demand rising, bearish sentiment",
        "weight": 1,
    },
    {
        "id": "nt_oil_shock",
        "name": "Oil Price Shock",
        "horizon": "near",
        "pillar": "Geopolitical",
        "crisis_if": lambda d: d.get("oil_1w_chg_pct", 0) > 6 or d.get("oil_1w_chg_pct", 0) < -8,
        "description": "Oil moved >6% in a week — supply shock or demand collapse signal",
        "weight": 1,
    },
    {
        "id": "nt_gold_flight",
        "name": "Gold Safe-Haven Surge",
        "horizon": "near",
        "pillar": "Geopolitical",
        "crisis_if": lambda d: d.get("gold_5d_chg_pct", 0) > 2.5 and d.get("iwm_5d_chg_pct", 0) < 0,
        "description": "Gold rising while equities fall — classic flight-to-safety pattern",
        "weight": 1,
    },
    {
        "id": "nt_usd_surge",
        "name": "USD Safe-Haven Demand",
        "horizon": "near",
        "pillar": "Geopolitical",
        "crisis_if": lambda d: d.get("usd_5d_chg_pct", 0) > 1.5 and d.get("iwm_5d_chg_pct", 0) < -1,
        "description": "Dollar surging vs equities falling — risk-off capital flight",
        "weight": 1,
    },

    # ═══════════════════════════════════════════════════
    # MID-TERM SIGNALS (8) — horizon: "mid"
    # ═══════════════════════════════════════════════════

    {
        "id": "mt_death_cross",
        "name": "Death Cross (50/200MA)",
        "horizon": "mid",
        "pillar": "Technical",
        "crisis_if": lambda d: d.get("ma50", 999) < d.get("ma200", 0),
        "description": "50MA crossed below 200MA — medium-term trend confirmed bearish",
        "weight": 1,
    },
    {
        "id": "mt_ma200_slope",
        "name": "200MA Direction",
        "horizon": "mid",
        "pillar": "Technical",
        "crisis_if": lambda d: d.get("ma200_slope", 1) < -0.0002,
        "description": "200MA trending down — long-term trend turning negative",
        "weight": 1,
    },
    {
        "id": "mt_breadth_200",
        "name": "S&P500 Breadth (200MA)",
        "horizon": "mid",
        "pillar": "Breadth",
        "crisis_if": lambda d: d.get("sp500_pct_above_200ma", 60) < 45,
        "description": "Less than 45% of S&P500 stocks above 200MA — broad deterioration",
        "weight": 1,
    },
    {
        "id": "mt_new_highs_lows",
        "name": "New Highs vs New Lows",
        "horizon": "mid",
        "pillar": "Breadth",
        "crisis_if": lambda d: d.get("new_lows", 50) > d.get("new_highs", 150) * 1.5,
        "description": "New lows outnumber new highs by 1.5x — market breadth collapsing",
        "weight": 1,
    },
    {
        "id": "mt_ad_line",
        "name": "Advance/Decline Line",
        "horizon": "mid",
        "pillar": "Breadth",
        "crisis_if": lambda d: d.get("advance_decline_ratio", 1.0) < 0.7,
        "description": "More declining stocks than advancing — broad selling pressure",
        "weight": 1,
    },
    {
        "id": "mt_hyg_credit",
        "name": "HY Credit Stress (HYG)",
        "horizon": "mid",
        "pillar": "Credit",
        "crisis_if": lambda d: d.get("hyg_vs_ma50_pct", 0) < -2 or d.get("hy_spread", 3) > 4.0,
        "description": "HYG falling below MA or spreads >400bps — credit market stress",
        "weight": 1,
    },
    {
        "id": "mt_sector_rotation",
        "name": "Defensive Sector Rotation",
        "horizon": "mid",
        "pillar": "Breadth",
        "crisis_if": lambda d: d.get("defensive_leading", False),
        "description": "Utilities/staples/healthcare outperforming — risk-off rotation",
        "weight": 1,
    },
    {
        "id": "mt_tlt_signal",
        "name": "Treasury Flight Signal",
        "horizon": "mid",
        "pillar": "Credit",
        "crisis_if": lambda d: d.get("tlt_5d_chg_pct", 0) > 2 and d.get("iwm_5d_chg_pct", 0) < -2,
        "description": "Bonds rallying while equities fall — flight to safety in bonds",
        "weight": 1,
    },

    # ═══════════════════════════════════════════════════
    # LONG-TERM SIGNALS (8) — horizon: "long"
    # ═══════════════════════════════════════════════════

    {
        "id": "lt_yield_curve_2_10",
        "name": "Yield Curve (2yr-10yr)",
        "horizon": "long",
        "pillar": "Macro",
        "crisis_if": lambda d: d.get("yield_curve_spread", 0.5) < 0,
        "description": "2-10yr curve inverted — historically precedes recession by 12-18mo",
        "weight": 1,
    },
    {
        "id": "lt_yield_curve_3m10y",
        "name": "Yield Curve (3mo-10yr)",
        "horizon": "long",
        "pillar": "Macro",
        "crisis_if": lambda d: d.get("yield_curve_3m10y", 0.5) < 0,
        "description": "3mo-10yr inverted — strongest recession predictor in Fed research",
        "weight": 1,
    },
    {
        "id": "lt_hy_spread_wide",
        "name": "HY Credit Spread",
        "horizon": "long",
        "pillar": "Macro",
        "crisis_if": lambda d: d.get("hy_spread", 3) > 4.5,
        "description": "HY spreads above 450bps — credit markets pricing recession risk",
        "weight": 1,
    },
    {
        "id": "lt_ism_contraction",
        "name": "ISM Manufacturing",
        "horizon": "long",
        "pillar": "Macro",
        "crisis_if": lambda d: d.get("ism_mfg", 50) < 48.5 and d.get("ism_trend", 0) < 0,
        "description": "ISM below 48.5 and declining — manufacturing cycle contracting",
        "weight": 1,
    },
    {
        "id": "lt_jobless_claims",
        "name": "Jobless Claims Trend",
        "horizon": "long",
        "pillar": "Macro",
        "crisis_if": lambda d: d.get("jobless_claims_4wk", 200) > 260 or d.get("cont_claims", 1800) > 2200,
        "description": "Claims rising above 260k or continuing claims >2.2M — labor weakening",
        "weight": 1,
    },
    {
        "id": "lt_fed_policy",
        "name": "Fed Policy Stance",
        "horizon": "long",
        "pillar": "Macro",
        "crisis_if": lambda d: d.get("fed_hiking", False) or (d.get("fed_uncertainty_high", False) and d.get("pce_inflation", 2.5) > 3.0),
        "description": "Fed hiking OR uncertainty high with inflation above 3% — restrictive policy",
        "weight": 1,
    },
    {
        "id": "lt_inflation_sticky",
        "name": "Core Inflation Persistence",
        "horizon": "long",
        "pillar": "Macro",
        "crisis_if": lambda d: d.get("pce_inflation", 2.5) > 3.2,
        "description": "Core PCE above 3.2% — inflation too high for Fed to pivot",
        "weight": 1,
    },
    {
        "id": "lt_ig_spread",
        "name": "Investment Grade Spreads",
        "horizon": "long",
        "pillar": "Macro",
        "crisis_if": lambda d: d.get("ig_spread", 1.0) > 1.8,
        "description": "IG spreads >180bps — corporate credit stress spreading to quality",
        "weight": 1,
    },
]

# ── CLAUDE MODEL ──────────────────────────────────────────────────────────────
CLAUDE_MODEL      = "claude-sonnet-4-6"
CLAUDE_MAX_TOKENS = 5000

# ── SCHEDULE ──────────────────────────────────────────────────────────────────
SEND_TIME = os.getenv("SEND_TIME", "06:00")
TIMEZONE  = os.getenv("TIMEZONE", "America/New_York")
LOG_FILE  = "logs/aperture.log"

SCORE_LEVELS = COMPOSITE_LEVELS

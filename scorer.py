"""
scorer.py — Aperture+ v2
Three-horizon scoring: Near-term (0-8), Mid-term (0-8), Long-term (0-8)
Composite score: 0-24
"""

import logging
from config import SIGNAL_RULES, NEAR_LEVELS, MID_LEVELS, LONG_LEVELS, COMPOSITE_LEVELS

logger = logging.getLogger(__name__)


def get_level(score, levels):
    for level in levels:
        if level[0] <= score <= level[1]:
            return level
    return levels[-1]


def calculate_score(data):
    near_signals = []
    mid_signals  = []
    long_signals = []

    near_score = 0
    mid_score  = 0
    long_score = 0

    pillar_scores = {}
    pillar_max    = {}

    for rule in SIGNAL_RULES:
        horizon = rule["horizon"]
        pillar  = rule["pillar"]

        key = f"{horizon}_{pillar}"
        pillar_scores.setdefault(key, 0)
        pillar_max.setdefault(key, 0)
        pillar_max[key] += 1

        try:
            is_crisis = rule["crisis_if"](data)
        except Exception as e:
            logger.warning(f"Signal '{rule['id']}' error: {e}")
            is_crisis = False

        score = rule.get("weight", 1) if is_crisis else 0

        if horizon == "near":
            near_score += score
            near_signals.append(_make_signal(rule, score, is_crisis))
        elif horizon == "mid":
            mid_score += score
            mid_signals.append(_make_signal(rule, score, is_crisis))
        else:
            long_score += score
            long_signals.append(_make_signal(rule, score, is_crisis))

        if is_crisis:
            pillar_scores[key] += score

    composite = near_score + mid_score + long_score

    near_level = get_level(near_score, NEAR_LEVELS)
    mid_level  = get_level(mid_score,  MID_LEVELS)
    long_level = get_level(long_score, LONG_LEVELS)
    comp_level = get_level(composite,  COMPOSITE_LEVELS)

    # Horizon summaries
    horizons = [
        {
            "name":        "Near-Term",
            "timeframe":   "0–5 trading days",
            "score":       near_score,
            "max":         8,
            "label":       near_level[2],
            "action":      near_level[3],
            "color":       near_level[4],
            "signals":     near_signals,
            "crisis":      [s for s in near_signals if s["is_crisis"]],
            "clear":       [s for s in near_signals if not s["is_crisis"]],
            "pct":         round(near_score / 8 * 100),
        },
        {
            "name":        "Mid-Term",
            "timeframe":   "1–8 weeks",
            "score":       mid_score,
            "max":         8,
            "label":       mid_level[2],
            "action":      mid_level[3],
            "color":       mid_level[4],
            "signals":     mid_signals,
            "crisis":      [s for s in mid_signals if s["is_crisis"]],
            "clear":       [s for s in mid_signals if not s["is_crisis"]],
            "pct":         round(mid_score / 8 * 100),
        },
        {
            "name":        "Long-Term",
            "timeframe":   "1–6 months",
            "score":       long_score,
            "max":         8,
            "label":       long_level[2],
            "action":      long_level[3],
            "color":       long_level[4],
            "signals":     long_signals,
            "crisis":      [s for s in long_signals if s["is_crisis"]],
            "clear":       [s for s in long_signals if not s["is_crisis"]],
            "pct":         round(long_score / 8 * 100),
        },
    ]

    all_signals    = near_signals + mid_signals + long_signals
    crisis_signals = [s for s in all_signals if s["is_crisis"]]
    clear_signals  = [s for s in all_signals if not s["is_crisis"]]

    # Pillar summary across all horizons
    pillar_summary = _build_pillar_summary(all_signals)

    return {
        # Composite
        "total_score":     composite,
        "max_score":       24,
        "score_pct":       round(composite / 24 * 100),
        "level_label":     comp_level[2],
        "level_action":    comp_level[3],
        "level_color":     comp_level[4],

        # Horizons
        "near_score":      near_score,
        "mid_score":       mid_score,
        "long_score":      long_score,
        "horizons":        horizons,

        # Signals
        "signals":         all_signals,
        "crisis_signals":  crisis_signals,
        "clear_signals":   clear_signals,

        # Pillars
        "pillars":         pillar_summary,
    }


def _make_signal(rule, score, is_crisis):
    return {
        "id":          rule["id"],
        "name":        rule["name"],
        "horizon":     rule["horizon"],
        "pillar":      rule["pillar"],
        "score":       score,
        "is_crisis":   is_crisis,
        "description": rule["description"],
    }


def _build_pillar_summary(all_signals):
    pillars = {}
    icons   = {
        "Technical":   "📊",
        "Breadth":     "🌊",
        "Macro":       "🏛",
        "Sentiment":   "🧠",
        "Geopolitical":"🌍",
        "Credit":      "💳",
    }
    for s in all_signals:
        p = s["pillar"]
        if p not in pillars:
            pillars[p] = {"name": p, "icon": icons.get(p, ""), "scored": 0, "total": 0}
        pillars[p]["total"]  += 1
        pillars[p]["scored"] += s["score"]

    result = []
    for p, v in pillars.items():
        pct = round(v["scored"] / v["total"] * 100) if v["total"] else 0
        result.append({
            "name":   v["name"],
            "icon":   v["icon"],
            "score":  v["scored"],
            "max":    v["total"],
            "pct":    pct,
            "status": "danger" if pct >= 60 else ("warn" if pct > 0 else "clear"),
        })
    return sorted(result, key=lambda x: x["score"], reverse=True)


def format_score_for_prompt(score_result, market_data):
    lines = []
    lines.append(f"COMPOSITE RISK SCORE: {score_result['total_score']}/24 ({score_result['score_pct']}%)")
    lines.append(f"LEVEL: {score_result['level_label']} — {score_result['level_action']}")
    lines.append("")

    for h in score_result["horizons"]:
        lines.append(f"{'─'*50}")
        lines.append(f"{h['name'].upper()} ({h['timeframe']}): {h['score']}/8 — {h['label']}")
        if h["crisis"]:
            for s in h["crisis"]:
                lines.append(f"  ⚠ [{s['pillar']}] {s['name']}: {s['description']}")
        else:
            lines.append(f"  ✓ All clear")

    lines.append("")
    lines.append("PILLAR BREAKDOWN:")
    for p in score_result["pillars"]:
        bar = "█" * p["score"] + "░" * (p["max"] - p["score"])
        lines.append(f"  {p['icon']} {p['name']:<14} {bar} {p['score']}/{p['max']}")

    lines.append("")
    lines.append("KEY MARKET DATA:")
    fields = [
        ("IWM Price",             f"${market_data.get('iwm_price','N/A')}"),
        ("1-Day Change",          f"{market_data.get('iwm_1d_chg_pct',0):+.2f}%"),
        ("5-Day Change",          f"{market_data.get('iwm_5d_chg_pct',0):+.2f}%"),
        ("IWM vs 200MA",          f"{market_data.get('iwm_vs_200ma_pct',0):+.1f}%"),
        ("RSI (14)",              f"{market_data.get('rsi14','N/A')}"),
        ("VIX",                   f"{market_data.get('vix','N/A')} (1wk chg: {market_data.get('vix_1w_chg',0):+.1f})"),
        ("WTI Oil",               f"${market_data.get('oil_price','N/A')} (1wk: {market_data.get('oil_1w_chg_pct',0):+.1f}%)"),
        ("Gold (GLD)",            f"${market_data.get('gold_price','N/A')} (5d: {market_data.get('gold_5d_chg_pct',0):+.1f}%)"),
        ("USD (UUP)",             f"${market_data.get('usd_price','N/A')} (5d: {market_data.get('usd_5d_chg_pct',0):+.1f}%)"),
        ("Put/Call Ratio",        f"{market_data.get('put_call_ratio','N/A')}"),
        ("HY Credit Spread",      f"{market_data.get('hy_spread','N/A')}% (chg: {market_data.get('hy_spread_chg',0):+.2f})"),
        ("IG Credit Spread",      f"{market_data.get('ig_spread','N/A')}%"),
        ("Yield Curve (2-10yr)",  f"{market_data.get('yield_curve_spread',0):+.2f}%"),
        ("Yield Curve (3m-10yr)", f"{market_data.get('yield_curve_3m10y',0):+.2f}%"),
        ("Core PCE Inflation",    f"{market_data.get('pce_inflation','N/A')}%"),
        ("Jobless Claims (4wk)",  f"{market_data.get('jobless_claims_4wk','N/A')}k"),
        ("Continuing Claims",     f"{market_data.get('cont_claims','N/A')}k"),
        ("ISM Manufacturing",     f"{market_data.get('ism_mfg','N/A')}"),
        ("S&P500 Breadth",        f"{market_data.get('sp500_pct_above_200ma','N/A')}% above 200MA"),
        ("HYG vs 50MA",           f"{market_data.get('hyg_vs_ma50_pct',0):+.1f}%"),
    ]
    for label, value in fields:
        lines.append(f"  {label:<30} {value}")

    # Geopolitical context
    if market_data.get("geo_event_active"):
        lines.append("")
        lines.append(f"⚠ GEOPOLITICAL EVENT ACTIVE: {market_data.get('geo_event_desc','')}")
        lines.append(f"  Risk Level: {market_data.get('geo_risk_level','elevated').upper()}")

    return "\n".join(lines)

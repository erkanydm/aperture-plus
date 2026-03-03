"""
email_builder.py — Aperture+ v2
Updated: new signal IDs, 3-horizon section, score bar to /24, Oil/Gold/PCE in snapshot.
"""

import logging
from datetime import datetime
from config import BRAND_NAME, BRAND_WEBSITE, COMPOSITE_LEVELS
SCORE_LEVELS = COMPOSITE_LEVELS  # backwards compat

logger = logging.getLogger(__name__)


def get_score_color(score):
    for level in COMPOSITE_LEVELS:
        if level[0] <= score <= level[1]:
            return level[4]
    return "#E05252"


def get_signal_display_value(signal_id, data):
    mapping = {
        # Near-term (new IDs)
        "nt_price_ma200":   f"{data.get('iwm_vs_200ma_pct', 0):+.1f}% vs 200MA",
        "nt_rsi_weak":      f"RSI {data.get('rsi14', 'N/A')}",
        "nt_volume_sell":   f"Vol ratio: {data.get('volume_ratio', 1.0):.1f}x | {data.get('iwm_1d_chg_pct',0):+.1f}% day",
        "nt_vix_spike":     f"VIX {data.get('vix', 'N/A')} | 1wk chg: {data.get('vix_1w_chg',0):+.1f}",
        "nt_put_call":      f"P/C ratio: {data.get('put_call_ratio', 'N/A')}",
        "nt_oil_shock":     f"WTI ${data.get('oil_price','N/A')} | 1wk: {data.get('oil_1w_chg_pct',0):+.1f}%",
        "nt_gold_flight":   f"GLD {data.get('gold_5d_chg_pct',0):+.1f}% / IWM {data.get('iwm_5d_chg_pct',0):+.1f}% (5d)",
        "nt_usd_surge":     f"USD {data.get('usd_5d_chg_pct',0):+.1f}% / IWM {data.get('iwm_5d_chg_pct',0):+.1f}% (5d)",
        # Mid-term (new IDs)
        "mt_death_cross":     f"50MA ${data.get('ma50','?')} vs 200MA ${data.get('ma200','?')}",
        "mt_ma200_slope":     f"Slope: {'↑ Rising' if data.get('ma200_slope',0) > 0 else '↓ Falling'}",
        "mt_breadth_200":     f"{data.get('sp500_pct_above_200ma','N/A')}% above 200MA",
        "mt_new_highs_lows":  f"NH: {data.get('new_highs','?')} / NL: {data.get('new_lows','?')}",
        "mt_ad_line":         f"A/D ratio: {data.get('advance_decline_ratio','N/A')}",
        "mt_hyg_credit":      f"HYG vs 50MA: {data.get('hyg_vs_ma50_pct',0):+.1f}% | HY: {data.get('hy_spread','N/A')}%",
        "mt_sector_rotation": f"{'⚠ Defensive leading' if data.get('defensive_leading') else '✓ Cyclicals leading'}",
        "mt_tlt_signal":      f"TLT {data.get('tlt_5d_chg_pct',0):+.1f}% / IWM {data.get('iwm_5d_chg_pct',0):+.1f}% (5d)",
        # Long-term (new IDs)
        "lt_yield_curve_2_10":  f"{data.get('yield_curve_spread',0):+.2f}% (2-10yr)",
        "lt_yield_curve_3m10y": f"{data.get('yield_curve_3m10y',0):+.2f}% (3m-10yr)",
        "lt_hy_spread_wide":    f"HY spread: {data.get('hy_spread','N/A')}%",
        "lt_ism_contraction":   f"ISM: {data.get('ism_mfg','N/A')} | Trend: {data.get('ism_trend',0):+.1f}",
        "lt_jobless_claims":    f"Claims: {data.get('jobless_claims_4wk','N/A')}k | Cont: {data.get('cont_claims','N/A')}k",
        "lt_fed_policy":        f"{'Hiking' if data.get('fed_hiking') else 'Holding'} @ {data.get('fed_funds_rate','?')}% | PCE: {data.get('pce_inflation','N/A')}%",
        "lt_inflation_sticky":  f"Core PCE: {data.get('pce_inflation','N/A')}%",
        "lt_ig_spread":         f"IG spread: {data.get('ig_spread','N/A')}%",
        # Legacy IDs (kept for backwards compat)
        "ma_depth":        f"{data.get('iwm_vs_200ma_pct', 0):+.1f}% vs 200MA",
        "death_cross":     f"50MA ${data.get('ma50','?')} vs 200MA ${data.get('ma200','?')}",
        "ma200_direction": f"Slope: {'Rising' if data.get('ma200_slope', 0) > 0 else 'Falling'}",
        "rsi":             f"RSI {data.get('rsi14', 'N/A')}",
        "volume":          f"Vol ratio: {data.get('volume_ratio', 1.0):.1f}x",
        "breadth_200":     f"{data.get('sp500_pct_above_200ma', 'N/A')}% above 200MA",
        "nh_nl":           f"NH: {data.get('new_highs','?')} / NL: {data.get('new_lows','?')}",
        "ad_line":         f"A/D ratio: {data.get('advance_decline_ratio', 'N/A')}",
        "sector_rotation": f"{'Defensive leading' if data.get('defensive_leading') else 'Cyclicals leading'}",
        "yield_curve":     f"{data.get('yield_curve_spread', 0):+.2f}% (2-10yr)",
        "hy_spread":       f"{data.get('hy_spread', 'N/A')}%",
        "ism":             f"{data.get('ism_mfg', 'N/A')}",
        "jobless_claims":  f"{data.get('jobless_claims_4wk', 'N/A')}k",
        "fed_policy":      f"{'Hiking' if data.get('fed_hiking') else 'Pausing'} @ {data.get('fed_funds_rate','?')}%",
        "vix":             f"VIX {data.get('vix', 'N/A')}",
        "put_call":        f"P/C ratio: {data.get('put_call_ratio', 'N/A')}",
    }
    return mapping.get(signal_id, "N/A")


def build_email_html(content, score_result, market_data, issue_number):
    score     = score_result["total_score"]
    max_score = score_result["max_score"]
    color     = get_score_color(score)
    bar_width = round(score / max_score * 100, 1)
    date_str  = datetime.now().strftime("%A, %B %d, %Y")
    golden    = (market_data.get("ma50") or 0) > (market_data.get("ma200") or 0)
    hy        = market_data.get("hy_spread", 0)
    yc        = market_data.get("yield_curve_spread", 0)
    iwm_chg   = market_data.get("iwm_1d_chg_pct", 0)

    iwm_chg_str   = f"{'▲' if iwm_chg >= 0 else '▼'} {abs(iwm_chg):.2f}% yesterday"
    iwm_chg_color = "#3ECF8E" if iwm_chg >= 0 else "#E05252"

    # ── THREE HORIZON CARDS ────────────────────────────────────────────────────
    horizons_html = ""
    horizon_colors = {
        "Clear":"#3ECF8E","Caution":"#C9A84C","Alert":"#E05252",
        "Stable":"#3ECF8E","Shifting":"#C9A84C","Broken":"#E05252",
        "Healthy":"#3ECF8E","Stressed":"#C9A84C","Crisis":"#E05252",
    }
    horizon_summary = content.get("horizon_summary", {})
    for h in score_result.get("horizons", []):
        hc = horizon_colors.get(h["label"], "#C9A84C")
        key = h["name"].split("-")[0].lower().strip()
        hs = horizon_summary.get(key, {})
        one_line = hs.get("one_line", h["action"])
        crisis_names = " · ".join([s["name"] for s in h["crisis"]]) if h["crisis"] else "All clear"
        horizons_html += f'''<div style="background:#FDFAF4;border:1px solid #E5E0D5;border-top:3px solid {hc};border-radius:4px;padding:16px 18px">
          <div style="font-size:9px;color:#999;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px">{h["name"]} · {h["timeframe"]}</div>
          <div style="display:flex;align-items:baseline;gap:6px;margin-bottom:6px">
            <span style="font-size:24px;font-weight:700;color:{hc};font-family:monospace">{h["score"]}</span>
            <span style="font-size:11px;color:#999">/8</span>
            <span style="font-size:10px;color:{hc};background:{hc}15;padding:2px 8px;border-radius:2px;margin-left:4px">{h["label"]}</span>
          </div>
          <div style="font-size:11px;color:#777;line-height:1.5;margin-bottom:6px">{one_line}</div>
          <div style="font-size:10px;color:#999;font-family:monospace">{"⚠ " + crisis_names if h["crisis"] else "✓ " + crisis_names}</div>
        </div>'''

    # ── SIGNAL TABLE (grouped by horizon) ────────────────────────────────────
    signal_rows = ""
    current_horizon = None
    horizon_labels = {
        "near": "⚡ Near-Term (0–5 days)",
        "mid":  "📈 Mid-Term (1–8 weeks)",
        "long": "🏛 Long-Term (1–6 months)"
    }
    horizon_bg = {"near": "#F0FBF6", "mid": "#FBF8F0", "long": "#F5F0FB"}
    for sig in score_result["signals"]:
        if sig["horizon"] != current_horizon:
            current_horizon = sig["horizon"]
            bg = horizon_bg.get(current_horizon, "#FAF7F1")
            signal_rows += f'''<tr><td colspan="4" style="padding:10px 12px 6px;font-size:10px;font-weight:700;color:#555;text-transform:uppercase;letter-spacing:0.1em;background:{bg};border-bottom:1px solid #E5E0D5">{horizon_labels.get(current_horizon,"")}</td></tr>'''
        val    = get_signal_display_value(sig["id"], market_data)
        status = sig["description"] if sig["is_crisis"] else "Clear"
        dot_c  = "#E05252" if sig["is_crisis"] else "#3ECF8E"
        signal_rows += f'''<tr>
          <td style="padding:10px 12px;font-size:12px;border-bottom:1px solid #F0EBE3;color:#2A2A2A;font-weight:500;width:30%">{sig["name"]}</td>
          <td style="padding:10px 12px;font-size:10px;border-bottom:1px solid #F0EBE3;color:#888;width:10%">{sig["pillar"]}</td>
          <td style="padding:10px 12px;font-size:11px;border-bottom:1px solid #F0EBE3;font-family:monospace;color:#555;width:25%">{val}</td>
          <td style="padding:10px 12px;font-size:11px;border-bottom:1px solid #F0EBE3;width:35%">
            <span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:{dot_c};margin-right:6px;vertical-align:middle"></span>{status}
          </td></tr>'''

    # ── INSIGHTS ─────────────────────────────────────────────────────────────
    horizon_tag_colors = {"near":"#3ECF8E","mid":"#C9A84C","long":"#9B6EE0"}
    insights_html = ""
    for ins in content.get("insights", []):
        h_color = horizon_tag_colors.get(ins.get("horizon","near"), "#C9A84C")
        signal_badge = ins.get("signal","")
        signal_color = "#3ECF8E" if signal_badge=="Bullish" else ("#E05252" if signal_badge=="Bearish" else "#999")
        insights_html += f'''<div style="display:flex;gap:16px;padding:16px 18px;background:#FDFAF4;border:1px solid #E5E0D5;border-left:3px solid {h_color};border-radius:0 4px 4px 0;margin-bottom:12px">
          <div style="font-family:Georgia,serif;font-size:28px;font-weight:900;color:#E5E0D5;line-height:1;flex-shrink:0;width:28px">{ins["number"]}</div>
          <div style="flex:1">
            <div style="font-size:14px;font-weight:600;color:#0E0E0E;margin-bottom:5px">{ins["title"]}</div>
            <div style="font-size:13px;color:#555;line-height:1.65">{ins["body"]}</div>
            <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap">
              <span style="font-size:9px;color:#fff;background:{h_color};padding:2px 7px;border-radius:2px;text-transform:uppercase;letter-spacing:0.06em">{ins.get("horizon","").upper()}</span>
              <span style="font-size:9px;color:#999;background:#E5E0D5;padding:2px 7px;border-radius:2px;text-transform:uppercase;letter-spacing:0.06em">{ins.get("tag","")}</span>
              <span style="font-size:9px;color:{signal_color};background:{signal_color}15;padding:2px 7px;border-radius:2px;text-transform:uppercase;letter-spacing:0.06em">{signal_badge}</span>
            </div>
          </div></div>'''

    # ── KEY LEVELS ────────────────────────────────────────────────────────────
    key_levels  = content.get("key_levels", {})
    levels_html = ""
    if key_levels:
        level_items = [
            ("IWM Support 1",  key_levels.get("iwm_support_1","—"),    "#3ECF8E"),
            ("IWM Support 2",  key_levels.get("iwm_support_2","—"),    "#3ECF8E"),
            ("IWM Resistance", key_levels.get("iwm_resistance_1","—"), "#E05252"),
            ("VIX Trigger",    key_levels.get("vix_trigger","—"),      "#C9A84C"),
            ("Oil Trigger",    key_levels.get("oil_trigger","—"),      "#C9A84C"),
        ]
        for label, val, lc in level_items:
            levels_html += f'''<div style="background:#FDFAF4;border:1px solid #E5E0D5;border-left:3px solid {lc};border-radius:0 4px 4px 0;padding:12px 16px;margin-bottom:8px">
              <div style="font-size:9px;color:#999;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:3px">{label}</div>
              <div style="font-size:13px;color:#2A2A2A;font-family:monospace">{val}</div>
            </div>'''

    # ── WATCH TODAY ───────────────────────────────────────────────────────────
    watch_html = ""
    for w in content.get("watch_today", []):
        impact_c = "#E05252" if "High" in w.get("impact","") else "#C9A84C"
        watch_html += f'''<div style="background:#FDFAF4;border:1px solid #E5E0D5;border-radius:4px;padding:16px;margin-bottom:10px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
            <div style="font-size:11px;color:#C9A84C;font-weight:600;font-family:monospace">{w["time"]}</div>
            <div style="font-size:9px;color:#fff;background:{impact_c};padding:2px 8px;border-radius:2px;text-transform:uppercase;letter-spacing:0.06em">{w.get("impact","")}</div>
          </div>
          <div style="font-size:13px;font-weight:600;color:#0E0E0E;margin-bottom:5px">{w["event"]}</div>
          <div style="font-size:12px;color:#777;line-height:1.55">{w["why"]}</div>
        </div>'''

    # ── BE CAREFUL ────────────────────────────────────────────────────────────
    careful_html = ""
    for c in content.get("be_careful", []):
        bg = "#FFF5F5" if c.get("severity") == "danger" else "#FFF8F0"
        bc = "#E05252" if c.get("severity") == "danger" else "#E07B39"
        h_label = {"near":"⚡ Near","mid":"📈 Mid","long":"🏛 Long"}.get(c.get("horizon","near"),"")
        careful_html += f'''<div style="background:{bg};border:1px solid {bc}40;border-left:4px solid {bc};border-radius:0 4px 4px 0;padding:20px 22px;margin-bottom:14px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <div style="font-size:14px;font-weight:600;color:{bc}">{"🔴" if c.get("severity")=="danger" else "⚠️"} {c["title"]}</div>
            <div style="font-size:9px;color:{bc};background:{bc}15;padding:2px 8px;border-radius:2px;text-transform:uppercase">{h_label}</div>
          </div>
          <div style="font-size:13px;color:#555;line-height:1.65">{c["body"]}</div>
        </div>'''

    # ── READ THIS (optional) ─────────────────────────────────────────────────
    read_html = ""
    for r in content.get("read_this", []):
        read_html += f'''<div style="display:flex;gap:14px;padding:14px 16px;background:#FDFAF4;border:1px solid #E5E0D5;border-radius:4px;margin-bottom:8px">
          <div style="flex:1">
            <div style="font-size:9px;color:#999;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px">{r["source"]}</div>
            <div style="font-size:13px;font-weight:600;color:#0E0E0E;margin-bottom:4px">{r["title"]}</div>
            <div style="font-size:12px;color:#777">{r["why"]}</div>
          </div>
          <div style="font-size:16px;color:#C9A84C">→</div>
        </div>'''

    # ── GEOPOLITICAL NOTE ─────────────────────────────────────────────────────
    geo_note = content.get("geopolitical_note")
    geo_html = ""
    if geo_note and geo_note not in (None, "null", ""):
        geo_html = f'''<div style="padding:32px 40px;border-bottom:1px solid #E5E0D5">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px">
            <span style="font-size:11px;color:#E05252;background:#E0525215;border:1px solid #E0525240;padding:3px 8px;border-radius:2px">🌍 GEO</span>
            <span style="font-size:20px;font-weight:700;color:#0E0E0E">Geopolitical Risk Note</span>
          </div>
          <div style="background:#FFF5F5;border:1px solid #E0525230;border-left:4px solid #E05252;border-radius:0 4px 4px 0;padding:20px 22px">
            <div style="font-size:13px;color:#555;line-height:1.75">{geo_note}</div>
          </div>
        </div>'''

    # ── PILLARS ───────────────────────────────────────────────────────────────
    pillars_html = ""
    status_colors = {"clear":"#3ECF8E","warn":"#C9A84C","danger":"#E05252"}
    for p in score_result["pillars"]:
        c = status_colors.get(p["status"], "#3ECF8E")
        pillars_html += f'''<div style="background:#1E1E1E;border:1px solid #2A2A2A;border-radius:4px;padding:12px;text-align:center;border-left:3px solid {c}">
          <div style="font-size:18px;margin-bottom:6px">{p["icon"]}</div>
          <div style="font-size:10px;color:#666;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.05em">{p["name"]}</div>
          <div style="font-size:18px;font-weight:500;color:{c};font-family:monospace">{p["score"]}<span style="font-size:11px;color:#444">/{p["max"]}</span></div>
        </div>'''

    oil_wk   = market_data.get('oil_1w_chg_pct', 0)
    oil_c    = "#E05252" if abs(oil_wk) > 4 else "#999"
    pce      = market_data.get('pce_inflation', 0) or 0
    pce_c    = "#E05252" if pce > 3 else "#3ECF8E"
    gold_5d  = market_data.get('gold_5d_chg_pct', 0)
    gold_c   = "#E07B39" if gold_5d > 2 else "#999"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Aperture+ — {date_str}</title></head>
<body style="margin:0;padding:0;background:#F5F2EC;font-family:'DM Sans',Arial,sans-serif;color:#1A1A1A">
<div style="max-width:680px;margin:0 auto;background:#F5F2EC">

  <!-- HEADER -->
  <div style="background:#0E0E0E;padding:28px 40px 24px;border-bottom:3px solid #C9A84C">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <div style="font-size:28px;font-weight:900;color:#F5F2EC;letter-spacing:-0.5px">Aperture<span style="color:#C9A84C">+</span></div>
      <div style="text-align:right">
        <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.1em">{date_str}</div>
        <div style="font-size:10px;color:#555;text-transform:uppercase;letter-spacing:0.08em">Daily Intelligence · Issue #{issue_number}</div>
      </div>
    </div>
  </div>

  <!-- SCORE HERO -->
  <div style="background:#0E0E0E;padding:32px 40px 36px">
    <div style="display:flex;align-items:flex-start;gap:32px">
      <div>
        <div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:6px">Risk Score</div>
        <div style="font-size:72px;font-weight:900;line-height:1;color:{color}">{score}</div>
        <div style="font-size:16px;color:#555;margin-top:4px;font-family:monospace">/ {max_score}</div>
      </div>
      <div style="padding-top:4px;border-left:2px solid #2A2A2A;padding-left:32px;flex:1">
        <div style="display:inline-block;background:{color}22;border:1px solid {color};color:{color};font-size:11px;text-transform:uppercase;padding:4px 12px;border-radius:2px;margin-bottom:12px;letter-spacing:0.1em">{score_result["level_label"]}</div>
        <div style="font-size:22px;font-weight:700;color:#F5F2EC;line-height:1.3;margin-bottom:10px">{content.get("verdict_headline","")}</div>
        <div style="font-size:13px;color:#999;line-height:1.7">{content.get("verdict_body","")}</div>
      </div>
    </div>
  </div>

  <!-- SCORE BAR -->
  <div style="background:#161616;padding:16px 40px;border-bottom:1px solid #2A2A2A">
    <div style="background:#2A2A2A;border-radius:3px;height:6px;overflow:hidden">
      <div style="height:100%;border-radius:3px;background:linear-gradient(90deg,#3ECF8E,#C9A84C 50%,#E05252);width:{bar_width}%"></div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:8px">
      <span style="font-size:9px;color:#555;text-transform:uppercase;letter-spacing:0.08em">0 Clear</span>
      <span style="font-size:9px;color:#555;text-transform:uppercase;letter-spacing:0.08em">6 Watch</span>
      <span style="font-size:9px;color:#555;text-transform:uppercase;letter-spacing:0.08em">12 Reduce</span>
      <span style="font-size:9px;color:#555;text-transform:uppercase;letter-spacing:0.08em">18 Exit</span>
      <span style="font-size:9px;color:#555;text-transform:uppercase;letter-spacing:0.08em">24 Crisis</span>
    </div>
  </div>

  <!-- PILLARS -->
  <div style="background:#161616;padding:24px 40px;border-bottom:1px solid #2A2A2A">
    <div style="font-size:10px;color:#555;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:16px">Score Breakdown</div>
    <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:8px">{pillars_html}</div>
  </div>

  <!-- THREE HORIZONS -->
  <div style="background:#161616;padding:24px 40px;border-bottom:1px solid #2A2A2A">
    <div style="font-size:10px;color:#555;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:16px">Risk by Horizon</div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px">{horizons_html}</div>
  </div>

  <!-- CONTENT BODY -->
  <div style="background:#F5F2EC">

    <!-- SNAPSHOT -->
    <div style="padding:32px 40px;border-bottom:1px solid #E5E0D5">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px">
        <span style="font-size:11px;color:#C9A84C;background:#C9A84C15;border:1px solid #C9A84C40;padding:3px 8px;border-radius:2px">01</span>
        <span style="font-size:20px;font-weight:700;color:#0E0E0E">Market Snapshot</span>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1px;background:#E5E0D5;border:1px solid #E5E0D5;border-radius:4px;overflow:hidden;margin-bottom:20px">
        <div style="background:#FDFAF4;padding:16px 18px">
          <div style="font-size:9px;color:#999;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">IWM (Russell 2000)</div>
          <div style="font-size:18px;font-weight:500;color:#0E0E0E;font-family:monospace">${market_data.get('iwm_price','N/A')}</div>
          <div style="font-size:11px;color:{iwm_chg_color};margin-top:3px">{iwm_chg_str}</div>
        </div>
        <div style="background:#FDFAF4;padding:16px 18px">
          <div style="font-size:9px;color:#999;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">200-Day MA</div>
          <div style="font-size:18px;font-weight:500;color:#0E0E0E;font-family:monospace">${market_data.get('ma200','N/A')}</div>
          <div style="font-size:11px;color:#3ECF8E;margin-top:3px">+{market_data.get('iwm_vs_200ma_pct',0):.1f}% above</div>
        </div>
        <div style="background:#FDFAF4;padding:16px 18px">
          <div style="font-size:9px;color:#999;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">50-Day MA</div>
          <div style="font-size:18px;font-weight:500;color:#0E0E0E;font-family:monospace">${market_data.get('ma50','N/A')}</div>
          <div style="font-size:11px;color:{'#3ECF8E' if golden else '#E05252'};margin-top:3px">{'Golden Cross ✓' if golden else 'Death Cross ⚠'}</div>
        </div>
        <div style="background:#FDFAF4;padding:16px 18px">
          <div style="font-size:9px;color:#999;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">VIX</div>
          <div style="font-size:18px;font-weight:500;color:#0E0E0E;font-family:monospace">{market_data.get('vix','N/A')}</div>
          <div style="font-size:11px;color:#999;margin-top:3px">{'↑ Rising' if market_data.get('vix_trend',0) > 1 else '→ Stable'}</div>
        </div>
        <div style="background:#FDFAF4;padding:16px 18px">
          <div style="font-size:9px;color:#999;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">WTI Oil</div>
          <div style="font-size:18px;font-weight:500;color:#0E0E0E;font-family:monospace">${market_data.get('oil_price','N/A')}</div>
          <div style="font-size:11px;color:{oil_c};margin-top:3px">{oil_wk:+.1f}% this week</div>
        </div>
        <div style="background:#FDFAF4;padding:16px 18px">
          <div style="font-size:9px;color:#999;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">HY Credit Spread</div>
          <div style="font-size:18px;font-weight:500;color:#0E0E0E;font-family:monospace">{hy}%</div>
          <div style="font-size:11px;color:{'#E05252' if hy > 4 else '#3ECF8E'};margin-top:3px">{'⚠ Stressed' if hy > 4 else 'Tight — Low stress'}</div>
        </div>
        <div style="background:#FDFAF4;padding:16px 18px">
          <div style="font-size:9px;color:#999;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">Yield Curve</div>
          <div style="font-size:18px;font-weight:500;color:#0E0E0E;font-family:monospace">{'+' if yc >= 0 else ''}{yc:.2f}%</div>
          <div style="font-size:11px;color:{'#3ECF8E' if yc > 0 else '#E05252'};margin-top:3px">{'Normal' if yc > 0 else '⚠ INVERTED'}</div>
        </div>
        <div style="background:#FDFAF4;padding:16px 18px">
          <div style="font-size:9px;color:#999;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">Gold (GLD)</div>
          <div style="font-size:18px;font-weight:500;color:#0E0E0E;font-family:monospace">${market_data.get('gold_price','N/A')}</div>
          <div style="font-size:11px;color:{gold_c};margin-top:3px">{gold_5d:+.1f}% (5d)</div>
        </div>
        <div style="background:#FDFAF4;padding:16px 18px">
          <div style="font-size:9px;color:#999;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">Core PCE</div>
          <div style="font-size:18px;font-weight:500;color:#0E0E0E;font-family:monospace">{pce}%</div>
          <div style="font-size:11px;color:{pce_c};margin-top:3px">{'⚠ Above 3% threshold' if pce > 3 else '✓ Near target'}</div>
        </div>
      </div>
      <p style="font-size:15px;line-height:1.85;color:#2A2A2A">{content.get('situation_paragraph','')}</p>
    </div>

    <!-- INSIGHTS -->
    <div style="padding:32px 40px;border-bottom:1px solid #E5E0D5">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px">
        <span style="font-size:11px;color:#C9A84C;background:#C9A84C15;border:1px solid #C9A84C40;padding:3px 8px;border-radius:2px">02</span>
        <span style="font-size:20px;font-weight:700;color:#0E0E0E">Key Insights</span>
      </div>
      {insights_html}
    </div>

    <!-- KEY LEVELS (only if present) -->
    {'<div style="padding:32px 40px;border-bottom:1px solid #E5E0D5"><div style="display:flex;align-items:center;gap:12px;margin-bottom:20px"><span style="font-size:11px;color:#C9A84C;background:#C9A84C15;border:1px solid #C9A84C40;padding:3px 8px;border-radius:2px">03</span><span style="font-size:20px;font-weight:700;color:#0E0E0E">Key Levels to Watch</span></div>' + levels_html + '</div>' if levels_html else ''}

    <!-- WATCH TODAY -->
    <div style="padding:32px 40px;border-bottom:1px solid #E5E0D5">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px">
        <span style="font-size:11px;color:#C9A84C;background:#C9A84C15;border:1px solid #C9A84C40;padding:3px 8px;border-radius:2px">04</span>
        <span style="font-size:20px;font-weight:700;color:#0E0E0E">Watch Today</span>
      </div>
      {watch_html}
    </div>

    {geo_html}

    <!-- BE CAREFUL -->
    <div style="padding:32px 40px;border-bottom:1px solid #E5E0D5">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px">
        <span style="font-size:11px;color:#C9A84C;background:#C9A84C15;border:1px solid #C9A84C40;padding:3px 8px;border-radius:2px">05</span>
        <span style="font-size:20px;font-weight:700;color:#0E0E0E">Be Careful About This</span>
      </div>
      {careful_html}
    </div>

    {'<div style="padding:32px 40px;border-bottom:1px solid #E5E0D5"><div style="display:flex;align-items:center;gap:12px;margin-bottom:20px"><span style="font-size:11px;color:#C9A84C;background:#C9A84C15;border:1px solid #C9A84C40;padding:3px 8px;border-radius:2px">06</span><span style="font-size:20px;font-weight:700;color:#0E0E0E">Read This Today</span></div>' + read_html + '</div>' if read_html else ''}

    <!-- SIGNAL TABLE -->
    <div style="padding:32px 40px;border-bottom:1px solid #E5E0D5">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px">
        <span style="font-size:11px;color:#C9A84C;background:#C9A84C15;border:1px solid #C9A84C40;padding:3px 8px;border-radius:2px">07</span>
        <span style="font-size:20px;font-weight:700;color:#0E0E0E">Full Signal Status (24 Signals)</span>
      </div>
      <table style="width:100%;border-collapse:collapse">
        <thead><tr>
          <th style="font-size:9px;color:#999;text-transform:uppercase;letter-spacing:0.1em;padding:8px 12px;text-align:left;border-bottom:1px solid #E5E0D5;background:#FAF7F1">Signal</th>
          <th style="font-size:9px;color:#999;text-transform:uppercase;letter-spacing:0.1em;padding:8px 12px;text-align:left;border-bottom:1px solid #E5E0D5;background:#FAF7F1">Pillar</th>
          <th style="font-size:9px;color:#999;text-transform:uppercase;letter-spacing:0.1em;padding:8px 12px;text-align:left;border-bottom:1px solid #E5E0D5;background:#FAF7F1">Reading</th>
          <th style="font-size:9px;color:#999;text-transform:uppercase;letter-spacing:0.1em;padding:8px 12px;text-align:left;border-bottom:1px solid #E5E0D5;background:#FAF7F1">Status</th>
        </tr></thead>
        <tbody>{signal_rows}</tbody>
      </table>
    </div>

  </div>

  <!-- BOTTOM LINE -->
  <div style="background:#0E0E0E;padding:28px 40px">
    <div style="font-size:10px;color:#555;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:10px">The Bottom Line</div>
    <div style="font-size:18px;color:#F5F2EC;line-height:1.6;font-style:italic">{content.get('bottom_line','')}</div>
    <div style="margin-top:16px;padding-top:14px;border-top:1px solid #1E1E1E;font-size:12px;color:#555">{score_result['level_action']}</div>
  </div>

  <!-- FOOTER -->
  <div style="background:#0A0A0A;padding:24px 40px;border-top:1px solid #1E1E1E">
    <div style="font-size:16px;font-weight:700;color:#F5F2EC">Aperture<span style="color:#C9A84C">+</span></div>
    <div style="font-size:11px;color:#444;line-height:1.6;margin-top:16px">
      Aperture+ is an automated market intelligence service. All content is generated by algorithmic
      analysis and AI synthesis of publicly available market data. This is not investment advice.
      Aperture+ does not manage money, hold licenses as a financial advisor, or make recommendations
      to buy or sell any security. Always consult a licensed financial advisor before making investment decisions.
    </div>
    <div style="margin-top:12px;font-size:10px;color:#333">
      aperture.plus · <a href="{{{{unsubscribe_url}}}}" style="color:#555;text-decoration:none">Unsubscribe</a>
    </div>
  </div>

</div></body></html>"""

    return html

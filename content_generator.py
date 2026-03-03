"""
content_generator.py — Uses Claude API to generate all email content.
This is the core IP of Aperture+.
"""

import anthropic
import json
import logging
from datetime import datetime
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, CLAUDE_MAX_TOKENS, BRAND_NAME, BRAND_WEBSITE
from scorer import format_score_for_prompt

logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are the senior macro analyst behind Aperture+, a daily market intelligence
service focused on IWM (Russell 2000 ETF) and US small cap markets. Website: aperture.plus

Your readers are sophisticated self-directed investors, independent financial advisors, and
small family offices managing $1M-$50M. They are smart, busy, and intolerant of vague content.

VOICE RULES:
- Write like a seasoned analyst who lived through 2008, 2020, and 2022
- Be specific: always connect data points to DIRECT impact on IWM/small caps
- Never use filler: "it's important to note", "as we can see", "interestingly"
- Quantify everything: not "elevated" — say "VIX at 19.6, up from 17.8 last week"
- Each insight must teach something they couldn't get from a Bloomberg headline
- Confident without being arrogant. Cautious without being alarmist.

CONTENT RULES:
- Every claim must be grounded in the data provided. Do not invent statistics.
- Always connect macro signals to Russell 2000 / small cap mechanism specifically
- The Bottom Line must be a single decisive statement

OUTPUT: Return valid JSON only. No markdown, no prose outside the JSON."""


def build_user_prompt(score_result, market_data, issue_number):
    score_summary = format_score_for_prompt(score_result, market_data)
    date_str = datetime.now().strftime("%A, %B %d, %Y")
    return f"""Today is {date_str}. Issue #{issue_number}.

{score_summary}

Generate the complete Aperture+ daily email content as JSON:

{{
  "subject_line": "Aperture+ — Score: X/16 | [compelling 5-word description]",
  "verdict_headline": "2 sentences. Bold declarative statement about market state.",
  "verdict_body": "2-3 sentences. Include 2 specific data points.",
  "situation_paragraph": "3-4 sentences. Full picture with at least 3 specific numbers.",
  "insights": [
    {{
      "number": 1,
      "title": "Specific informative title",
      "body": "3-4 sentences. Data point, mechanism, small cap impact, what to watch.",
      "tag": "category | Bullish/Bearish/Watch"
    }}
  ],
  "watch_today": [
    {{
      "time": "HH:MM EST",
      "event": "Specific event name",
      "why": "2 sentences: what it is and why it matters for IWM today",
      "impact": "High Impact | Medium Impact | Technical Level | Fed Watch"
    }}
  ],
  "be_careful": [
    {{
      "title": "Specific warning title",
      "body": "3-4 sentences. Risk, mechanism, specific trigger level.",
      "severity": "warning | danger"
    }}
  ],
  "read_this": [
    {{
      "source": "Publication name",
      "title": "Article title or topic",
      "why": "1 sentence: why essential for IWM investors TODAY"
    }}
  ],
  "bottom_line": "2 sentences. Most important takeaway. Score + specific level or event.",
  "score_change_from_yesterday": 0
}}

Return ONLY valid JSON."""


def generate_email_content(score_result, market_data, issue_number=1, prev_score=None):
    logger.info("Generating content via Claude API...")
    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_user_prompt(score_result, market_data, issue_number)}]
        )
        raw = message.content[0].text
        # Strip markdown code fences if Claude wrapped the JSON
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        content = json.loads(raw)
        if prev_score is not None:
            content["score_change_from_yesterday"] = score_result["total_score"] - prev_score
        content["generated_at"] = datetime.now().isoformat()
        logger.info(f"  ✓ Content generated")
        return content
    except json.JSONDecodeError as e:
        logger.error(f"Claude returned invalid JSON: {e}")
        return generate_fallback_content(score_result, market_data)
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return generate_fallback_content(score_result, market_data)


def generate_fallback_content(score_result, market_data):
    score = score_result["total_score"]
    level = score_result["level_label"]
    price = market_data.get("iwm_price", "N/A")
    return {
        "subject_line": f"Aperture+ — Score: {score}/16 | {level}",
        "verdict_headline": f"Risk score: {score}/16. Market status: {level}.",
        "verdict_body": f"IWM at ${price}.",
        "situation_paragraph": "See signal table below for full breakdown.",
        "insights": [{"number": 1, "title": f"Score: {score}/16", "body": f"IWM ${price}.", "tag": level}],
        "watch_today": [],
        "be_careful": [{"title": "Review signal table", "body": "See below.", "severity": "warning"}],
        "read_this": [],
        "bottom_line": f"Score: {score}/16. {level}.",
        "score_change_from_yesterday": 0,
        "generated_at": datetime.now().isoformat(),
        "is_fallback": True,
    }
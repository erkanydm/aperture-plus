"""
social_poster.py — Posts to Twitter/X, Instagram, LinkedIn automatically.
"""

import os, requests, logging
from datetime import datetime

logger = logging.getLogger(__name__)

TWITTER_API_KEY      = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET   = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET= os.getenv("TWITTER_ACCESS_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
BUFFER_TOKEN         = os.getenv("BUFFER_ACCESS_TOKEN")
BUFFER_INSTAGRAM_ID  = os.getenv("BUFFER_INSTAGRAM_PROFILE_ID")
BUFFER_LINKEDIN_ID   = os.getenv("BUFFER_LINKEDIN_PROFILE_ID")
SIGNAL_WEBSITE       = os.getenv("SIGNAL_WEBSITE", "https://aperture.plus")


def post_twitter_thread(score_result, content, market_data):
    try:
        import tweepy
        client = tweepy.Client(
            bearer_token=TWITTER_BEARER_TOKEN,
            consumer_key=TWITTER_API_KEY, consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN, access_token_secret=TWITTER_ACCESS_SECRET,
        )
        score = score_result["total_score"]
        level = score_result["level_label"]
        iwm   = market_data.get("iwm_price","N/A")
        vix   = market_data.get("vix","N/A")
        hy    = market_data.get("hy_spread","N/A")
        emoji = "🟢" if score<=4 else "🟡" if score<=8 else "🟠" if score<=12 else "🔴"
        date  = datetime.now().strftime("%b %d")

        t1 = f"""{emoji} Aperture+ Risk Score: {score}/16 — {level}

{date} snapshot:
• IWM: ${iwm}
• 200MA: ${market_data.get("ma200","N/A")} ({market_data.get("iwm_vs_200ma_pct",0):+.1f}% above)
• VIX: {vix}
• HY Spread: {hy}%

{score_result["level_action"]}

🧵"""

        top = content.get("insights",[{}])[0]
        t2 = f"""📊 Top insight today:

{top.get("title","")}

{top.get("body","")[:220]}..."""

        warn = content.get("be_careful",[{}])[0]
        t3 = f"""⚠️ Be careful:

{warn.get("title","")}

{warn.get("body","")[:200]}..."""

        t4 = f"""📬 Full Aperture+ analysis:
• 5 insights · Key events · 16-signal breakdown

Free trial → {SIGNAL_WEBSITE}

#IWM #Russell2000 #investing #markets"""

        r1 = client.create_tweet(text=t1)
        tid = r1.data["id"]
        r2 = client.create_tweet(text=t2, in_reply_to_tweet_id=tid)
        tid = r2.data["id"]
        r3 = client.create_tweet(text=t3, in_reply_to_tweet_id=tid)
        tid = r3.data["id"]
        client.create_tweet(text=t4, in_reply_to_tweet_id=tid)

        logger.info("  ✓ Twitter thread posted")
        return True
    except Exception as e:
        logger.error(f"Twitter failed: {e}")
        return False


def build_instagram_caption(score_result, content, market_data):
    score = score_result["total_score"]
    level = score_result["level_label"]
    date  = datetime.now().strftime("%B %d, %Y")
    opening = "✅" if score<=4 else "🟡" if score<=8 else "🟠" if score<=12 else "🔴"
    insights = content.get("insights",[])
    lines = "\n".join([f"{i+1}. {ins['title']}" for i, ins in enumerate(insights[:3])])
    bl = content.get("bottom_line","")[:180]
    return f"""{opening} Aperture+ Risk Score: {score}/16 — {level}
{date}

Today's top insights:{lines}

Bottom line: {bl}

─────────────────
💡 Save this — scores change daily
📬 Full analysis → link in bio (aperture.plus)
─────────────────
#IWM #Russell2000 #StockMarket #Investing #Finance #MarketAnalysis #TechnicalAnalysis #FinancialEducation #WealthManagement #Stocks #Trading #SmallCap #MacroEconomics"""


def post_instagram_carousel(image_paths, caption):
    if not BUFFER_TOKEN or not BUFFER_INSTAGRAM_ID:
        logger.warning("Buffer credentials not set.")
        return False
    headers = {"Authorization": f"Bearer {BUFFER_TOKEN}"}
    media_ids = []
    for path in image_paths[:10]:
        try:
            with open(path,"rb") as f:
                r = requests.post("https://api.bufferapp.com/1/media/upload.json",
                    headers={"Authorization": f"Bearer {BUFFER_TOKEN}"},
                    files={"file": (path.split("/")[-1], f, "image/png")})
                r.raise_for_status()
                mid = r.json().get("id")
                if mid: media_ids.append(mid)
        except Exception as e:
            logger.error(f"Buffer upload failed: {e}")
    if not media_ids:
        return False
    try:
        r = requests.post("https://api.bufferapp.com/1/updates/create.json",
            headers=headers,
            json={"profile_ids":[BUFFER_INSTAGRAM_ID],"text":caption,
                  "media":{"photo_ids":media_ids},"now":True})
        r.raise_for_status()
        logger.info(f"  ✓ Instagram carousel posted ({len(media_ids)} slides)")
        return True
    except Exception as e:
        logger.error(f"Buffer Instagram failed: {e}")
        return False


def post_linkedin(score_result, content, market_data):
    if not BUFFER_TOKEN or not BUFFER_LINKEDIN_ID:
        return False
    score = score_result["total_score"]
    level = score_result["level_label"]
    date  = datetime.now().strftime("%B %d, %Y")
    top   = content.get("insights",[{}])[0]
    bl    = content.get("bottom_line","")
    text  = f"""Aperture+ Daily Intelligence — {date}

Risk Score: {score}/16 ({level})
IWM: ${market_data.get("iwm_price","N/A")}

Key insight: {top.get("title","")}
{top.get("body","")[:300]}

Bottom line: {bl}

Not investment advice. aperture.plus

#Finance #Investing #MarketAnalysis #IWM"""
    try:
        r = requests.post("https://api.bufferapp.com/1/updates/create.json",
            headers={"Authorization": f"Bearer {BUFFER_TOKEN}"},
            json={"profile_ids":[BUFFER_LINKEDIN_ID],"text":text,"now":True})
        r.raise_for_status()
        logger.info("  ✓ LinkedIn posted")
        return True
    except Exception as e:
        logger.error(f"LinkedIn failed: {e}")
        return False


def post_all_social(score_result, content, market_data, carousel_paths, dry_run=False):
    if dry_run:
        logger.info("  ⚡ DRY RUN — social not posted")
        return {}
    results = {}
    logger.info("  Posting to social...")
    results["twitter"]   = post_twitter_thread(score_result, content, market_data)
    caption = build_instagram_caption(score_result, content, market_data)
    results["instagram"] = post_instagram_carousel(carousel_paths, caption)
    results["linkedin"]  = post_linkedin(score_result, content, market_data)
    logger.info(f"  ✓ Social complete: {sum(1 for v in results.values() if v)}/{len(results)} platforms")
    return results
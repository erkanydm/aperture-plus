"""
scheduler.py — Master controller for Aperture+

Usage:
  python scheduler.py           # Start daily scheduler (6am ET, weekdays)
  python scheduler.py --dry-run # Run pipeline, print output, don't send
  python scheduler.py --test    # Run once, send test email to TEST_EMAIL
  python scheduler.py --send    # Run once and send to all subscribers
"""

import os, sys, json, logging, argparse, schedule, time
from datetime import datetime
from pathlib import Path

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(), logging.FileHandler("logs/aperture.log")]
)
logger = logging.getLogger(__name__)

from config import SEND_TIME, BRAND_NAME
from data_fetcher import fetch_all_market_data
from scorer import calculate_score
from content_generator import generate_email_content
from email_builder import build_email_html
from carousel_generator import generate_carousel
from social_poster import post_all_social, build_instagram_caption
from sender import create_and_send_post, send_test_email, get_subscriber_count

STATE_FILE = "logs/state.json"

def load_state():
    if Path(STATE_FILE).exists():
        with open(STATE_FILE) as f: return json.load(f)
    return {"issue_number": 1, "last_score": None, "last_run": None}

def save_state(state):
    with open(STATE_FILE, "w") as f: json.dump(state, f, indent=2)


def run_pipeline(send=False, test_email=None, dry_run=False):
    state        = load_state()
    issue_number = state["issue_number"]
    prev_score   = state.get("last_score")
    today        = datetime.now()

    logger.info(f"\n{'='*60}")
    logger.info(f"  Aperture+ Pipeline — Issue #{issue_number}")
    logger.info(f"  {today.strftime('%A, %B %d, %Y %H:%M:%S ET')}")
    logger.info(f"{'='*60}\n")

    # STEP 1: Fetch Data
    logger.info("STEP 1: Fetching market data")
    market_data = fetch_all_market_data()
    logger.info(f"  IWM: ${market_data.get('iwm_price')} | VIX: {market_data.get('vix')}\n")

    # STEP 2: Score
    logger.info("STEP 2: Calculating risk score")
    score_result = calculate_score(market_data)
    score        = score_result["total_score"]
    logger.info(f"  ── SCORE: {score}/{score_result['max_score']} — {score_result['level_label']} ──\n")

    # STEP 3: Generate Content
    logger.info("STEP 3: Generating content via Claude API")
    content = generate_email_content(score_result, market_data, issue_number, prev_score)
    logger.info(f"  Subject: {content.get('subject_line')}\n")

    # STEP 4: Build Email
    logger.info("STEP 4: Building HTML email")
    html = build_email_html(content, score_result, market_data, issue_number)
    archive_path = f"logs/email_{issue_number:04d}_{today.strftime('%Y%m%d')}.html"
    with open(archive_path, "w") as f: f.write(html)
    with open(f"logs/content_{issue_number:04d}.json", "w") as f:
        json.dump({"issue": issue_number, "score": score, "content": content,
                   "market_data": {k:v for k,v in market_data.items()
                                   if not callable(v)}}, f, indent=2)
    logger.info(f"  ✓ Saved to {archive_path}\n")

    # STEP 5: Generate Carousel
    logger.info("STEP 5: Generating carousel slides")
    carousel_dir  = f"logs/carousel_{today.strftime('%Y%m%d')}"
    carousel_data = {
        "score":       score,
        "date":        today.strftime("%A, %B %d, %Y"),
        "verdict":     content.get("verdict_headline",""),
        "bottom_line": content.get("bottom_line",""),
        "key_levels": [
            f"IWM 200MA: ${market_data.get('ma200')} — primary support",
            f"IWM 50MA: ${market_data.get('ma50')} — must hold",
            f"VIX >25 = re-score trigger",
        ],
        "market_data": market_data,
        "pillars":     score_result["pillars"],
        "insights":    content.get("insights",[]),
    }
    carousel_paths = generate_carousel(carousel_data, carousel_dir)
    logger.info(f"  ✓ {len(carousel_paths)} slides generated\n")

    if dry_run:
        logger.info("  ⚡ DRY RUN complete — nothing sent")
        logger.info(f"  Email: {archive_path}")
        logger.info(f"  Carousel: {carousel_dir}/")
        return

    subject = content.get("subject_line", f"Aperture+ — Score: {score}/16")

    # STEP 6: Send Email
    logger.info("STEP 6: Sending email")
    if test_email:
        send_test_email(html, subject, test_email)
    elif send:
        subs = get_subscriber_count()
        logger.info(f"  Sending to {subs.get('total','?')} subscribers")
        create_and_send_post(subject, html, score, issue_number, test_mode=False)

        # STEP 7: Social
        logger.info("\nSTEP 7: Posting to social media")
        caption = build_instagram_caption(score_result, content, market_data)
        post_all_social(score_result, content, market_data, carousel_paths)

        state.update({"issue_number": issue_number+1, "last_score": score,
                      "last_run": today.isoformat()})
        save_state(state)

    logger.info(f"\n{'='*60}")
    logger.info(f"  ✅ Complete — Issue #{issue_number} — Score: {score}/16")
    logger.info(f"{'='*60}\n")


def start_scheduler():
    logger.info(f"Aperture+ Scheduler — daily at {SEND_TIME} ET (weekdays only)")
    for day in ["monday","tuesday","wednesday","thursday","friday"]:
        getattr(schedule.every(), day).at(SEND_TIME).do(lambda: run_pipeline(send=True))
    logger.info(f"Next run: {schedule.next_run()}")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aperture+ Daily Pipeline")
    parser.add_argument("--test",    action="store_true")
    parser.add_argument("--send",    action="store_true")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run")
    args = parser.parse_args()

    if args.test:
        email = os.getenv("TEST_EMAIL","")
        if not email:
            print("Set TEST_EMAIL in .env first")
            sys.exit(1)
        run_pipeline(test_email=email)
    elif args.send:
        run_pipeline(send=True)
    elif args.dry_run:
        run_pipeline(dry_run=True)
    else:
        start_scheduler()
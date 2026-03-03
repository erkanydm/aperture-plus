"""
sender.py — Sends email via Resend API.
"""

import resend
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

resend.api_key = os.getenv("RESEND_API_KEY")
TEST_EMAIL = os.getenv("TEST_EMAIL", "")


def send_test_email(html_content, subject, test_email):
    try:
        params = {
            "from": "Aperture+ <hello@aperture.plus>",
            "to": [test_email],
            "subject": subject,
            "html": html_content,
        }
        email = resend.Emails.send(params)
        logger.info(f"  ✓ Test email sent to {test_email} (id: {email['id']})")
        return True
    except Exception as e:
        logger.error(f"Test email failed: {e}")
        return False


def create_and_send_post(subject, html_content, score, issue_number, send_to="both", test_mode=False):
    try:
        params = {
            "from": "Aperture+ <hello@aperture.plus>",
            "to": [TEST_EMAIL],
            "subject": subject,
            "html": html_content,
        }
        email = resend.Emails.send(params)
        logger.info(f"  ✓ Email sent (id: {email['id']})")
        return {"status": "sent", "id": email["id"]}
    except Exception as e:
        logger.error(f"Resend failed: {e}")
        raise


def get_subscriber_count():
    return {"total": 0}

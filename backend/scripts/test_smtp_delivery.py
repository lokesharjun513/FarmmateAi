import sys
import os
import secrets
import logging
from email.message import EmailMessage
import smtplib

# Add project root to sys.path
sys.path.append(os.path.abspath("backend"))

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_test_email(to_address: str):
    otp = "".join(secrets.choice("0123456789") for _ in range(6))

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_address
    msg["Subject"] = "FarmMate AI — Test OTP"
    text_content = f"This is an SMTP delivery test. Your test code is: {otp}."
    msg.set_content(text_content)

    try:
        logger.info("Attempting to connect to SMTP server: %s:%s", settings.SMTP_HOST, settings.SMTP_PORT)
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(settings.SMTP_USER, settings.SMTP_PASS)
        server.send_message(msg)
        server.quit()
        print("REPORT: SMTP submission status: Success - Gmail SMTP accepted the email.")
    except Exception as e:
        print(f"REPORT: SMTP submission status: Failed - Error: {e}")

if __name__ == "__main__":
    send_test_email("ramsonu.d.failure@gmail.com")

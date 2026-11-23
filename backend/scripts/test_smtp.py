import os
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage
import sys
import argparse

# Load .env
load_dotenv()

def test_smtp(recipient):
    host = os.getenv("SMTP_HOST")
    port = os.getenv("SMTP_PORT")
    username = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    from_address = os.getenv("SMTP_FROM")

    print(f"SMTP Configuration:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  User: {username}")
    print(f"  From: {from_address}")

    if not all([host, port, username, password, from_address]):
        print("Error: Missing SMTP environment variables.")
        sys.exit(1)

    msg = EmailMessage()
    msg["From"] = from_address
    msg["To"] = recipient
    msg["Subject"] = "FarmMate AI — SMTP Test"
    msg.set_content("This is a test email from FarmMate AI.\n\nIf you received this message, SMTP email delivery is working.\n\nNo password reset was requested.")

    try:
        print(f"\nConnecting to {host}:{port}...")
        server = smtplib.SMTP(host, int(port), timeout=15)
        server.ehlo()
        print("Starting TLS...")
        server.starttls()
        server.ehlo()
        print("Authenticating...")
        server.login(username, password)
        print("Sending email...")
        server.send_message(msg)
        server.quit()
        print("Success: Email sent.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", required=True, help="Recipient email address")
    args = parser.parse_args()
    test_smtp(args.to)

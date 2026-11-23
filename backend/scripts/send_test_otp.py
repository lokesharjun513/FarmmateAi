import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to sys.path
sys.path.append(os.path.abspath("backend"))

from app.core.config import settings

# Import all models so SQLAlchemy can resolve every relationship target
from app.database import models  # noqa: F401
from app.modules.identity.models import User

from app.modules.identity.repository import UserRepository
from app.modules.password_reset.service import forgot_password

def send_test_otp(email: str):
    # Setup DB
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # 1. Check registration
        user_repo = UserRepository(db)
        user = user_repo.get_by_email(email.lower().strip())

        if not user:
            print(f"REPORT: Account registration check: Not found for {email}")
            return

        print(f"REPORT: Account registration check: Found user {user.id}")

        # 2. Invoke forgot_password flow
        # This function generates OTP, creates challenge, and sends email.
        result = forgot_password(email, db)

        print(f"REPORT: forgot_password result: {result}")
        print("REPORT: OTP challenge creation status: Triggered")
        print("REPORT: SMTP submission status: Triggered (check logs)")
        print("REPORT: Note: SMTP success/failure is logged in the service layer.")

    except Exception as e:
        print(f"REPORT: Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    send_test_otp("ramsonu.d.failure@gmail.com")


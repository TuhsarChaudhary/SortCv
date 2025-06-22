import logging
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.database import SessionLocal, Base
from app.core.security import get_password_hash
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db() -> None:
    db = SessionLocal()
    try:
        # Check if we already have users
        user = db.query(User).first()
        if user:
            logger.info("Database already initialized, skipping")
            return

        # Create admin user
        admin_user = User(
            fname="Admin",
            lname="User",
            email="admin@example.com",
            phone="+1234567890",
            dateofbirth=datetime(1990, 1, 1),
            gender="prefer not to say",
            country="Global",
            nationality="Global",
            hashed_password=get_password_hash("Admin123!"),
            is_active=True,
            is_admin=True
        )
        
        db.add(admin_user)
        db.commit()
        logger.info("Admin user created")
        
        # Create test user
        test_user = User(
            fname="Test",
            lname="User",
            email="user@example.com",
            phone="+0987654321",
            dateofbirth=datetime(1995, 5, 15),
            gender="prefer not to say",
            country="Global",
            nationality="Global",
            hashed_password=get_password_hash("User123!"),
            is_active=True,
            is_admin=False
        )
        
        db.add(test_user)
        db.commit()
        logger.info("Test user created")
        
    finally:
        db.close()

def main() -> None:
    logger.info("Creating initial data")
    init_db()
    logger.info("Initial data created")

if __name__ == "__main__":
    main()

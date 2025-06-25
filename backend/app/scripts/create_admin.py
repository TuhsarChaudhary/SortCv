import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def create_admin():
    db: Session = SessionLocal()

    admin_email = "admin@example.com"
    existing_admin = db.query(User).filter(User.email == admin_email).first()

    if existing_admin:
        # print("Admin user already exists.")
        return

    admin_user = User(
        fname="Admin",
        lname="User",
        email=admin_email,
        phone="0000000000",
        dateofbirth=None,
        gender="Other",
        country="Global",
        nationality="Global",
        hashed_password=get_password_hash("Admin@12345"),
        is_active=True,
        is_admin=True,
        cv_access=True
    )

    db.add(admin_user)
    db.commit()
    # print("Admin user created successfully.")

if __name__ == "__main__":
    create_admin()

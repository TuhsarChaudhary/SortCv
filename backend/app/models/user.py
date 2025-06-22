from sqlalchemy import Boolean, Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import date


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    fname = Column(String, index=True)
    lname = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    dateofbirth = Column(Date)
    gender = Column(String)
    country = Column(String)
    nationality = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    cv_access = Column(Boolean, default=False)  # Permission to access shortlist/longlist features
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship to password reset OTPs
    reset_otps = relationship("PasswordResetOTP", back_populates="user")


class PasswordResetOTP(Base):
    __tablename__ = "password_reset_otps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    otp_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)

    user = relationship("User", back_populates="reset_otps")

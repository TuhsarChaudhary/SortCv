from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class ResumePDF(Base):
    """ORM model for storing resume-related artefacts.

    At the moment only resume parsing (long-listing) has been implemented so
    `long_listing_csv` is populated while `short_listing_csv` and
    `job_desc_path` are left blank.  When the short-listing flow is wired up
    those fields can be updated easily using the same record.
    """

    __tablename__ = "resume_pdfs"

    id = Column(Integer, primary_key=True, index=True)

    # File / storage info
    pdf_name = Column(String, index=True, nullable=False)
    pdf_hash = Column(String(64), unique=True, index=True, nullable=False)  # SHA-256 hex digest identifying the file
    pdf_path = Column(String, nullable=False)
    csv_path = Column(String, nullable=False)  # Path for auto-generated long-list CSV

    # Optional artefacts – may be null initially
    long_listing_csv = Column(String, nullable=True)
    short_listing_csv = Column(String, nullable=True)
    job_desc_path = Column(String, nullable=True)

    # Misc
    size = Column(Integer, nullable=True)  # Size of the uploaded PDF in bytes
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship (optional)
    user = relationship("User")

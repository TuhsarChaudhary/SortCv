from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class ResumePDF(Base):
    """ORM model for storing resume-related artefacts."""

    __tablename__ = "resume_pdfs"

    id = Column(Integer, primary_key=True, index=True)

    # File / storage info
    pdf_name = Column(String, index=True, nullable=False)
    # SHA-256 hex digest identifying the file (duplicates allowed across users)
    pdf_hash = Column(String(64), index=True, nullable=False)
    pdf_path = Column(String, nullable=False)
    csv_path = Column(String, nullable=False)  # Path for auto-generated long-list CSV

    # Optional artefacts – may be null initially
    long_listing_csv = Column(String, nullable=True)
    # short_listing_csv = Column(String, nullable=True)
    # job_desc_path = Column(String, nullable=True)

    # Misc
    size: int | None = Column(Integer, nullable=True)

    # Filter thresholds used to produce the stored long_listing_csv
    min_experience: int | None = Column(Integer, nullable=True)
    min_degree: str | None = Column(String, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Link to the most recently used JD (optional convenience foreign key)
    jd_id = Column(Integer, ForeignKey("jd_pdfs.id"), nullable=True)
    jd = relationship("JobDescriptionPDF", foreign_keys=[jd_id])

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship (optional)
    user = relationship("User")
    # Link to job-descriptions processed against this resume
    job_descriptions = relationship(
        "JobDescriptionPDF",
        back_populates="resume",
        cascade="all, delete-orphan",
        foreign_keys="JobDescriptionPDF.resume_id",
    )

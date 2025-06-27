from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class JobDescriptionPDF(Base):
    """ORM model for storing JD files and the shortlist generated from them."""

    __tablename__ = "jd_pdfs"

    id: int = Column(Integer, primary_key=True, index=True)

    # File metadata
    jd_name: str = Column(String, nullable=False, index=True)
    jd_hash: str = Column(String(64), nullable=False, index=True)  # SHA-256 hex digest
    jd_path: str = Column(String, nullable=False)

    # Template used to extract relevant sections (e.g. "UNV Template")
    template_type: str = Column(String, nullable=False)

    # Artefacts
    shortlist_csv: str | None = Column(String, nullable=True)
    relevant_text_path: str | None = Column(String, nullable=True)

    # Relationship back to the originating resume
    resume_id: int = Column(Integer, ForeignKey("resume_pdfs.id"), nullable=False)
    resume = relationship(
        "ResumePDF",
        back_populates="job_descriptions",
        foreign_keys=[resume_id],
    )

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

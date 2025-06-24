"""ResumePDF data-access helpers (no FastAPI or business rules here)."""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.resume_pdf import ResumePDF


def get_by_hash(db: Session, pdf_hash: str) -> Optional[ResumePDF]:
    """Get a resume by its hash."""
    return db.query(ResumePDF).filter(ResumePDF.pdf_hash == pdf_hash).first()


def get_by_id(db: Session, pdf_id: int) -> Optional[ResumePDF]:
    """Get a resume by its id."""
    return db.query(ResumePDF).filter(ResumePDF.id == pdf_id).first()


def add(db: Session, obj: ResumePDF) -> ResumePDF:
    """Add a new resume."""
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, obj: ResumePDF) -> ResumePDF:
    """Update a resume."""
    db.commit()
    db.refresh(obj)
    return obj

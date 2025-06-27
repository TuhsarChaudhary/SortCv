"""ResumePDF data-access helpers (no FastAPI or business rules here)."""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.resume_pdf import ResumePDF

def get_by_hash(db: Session, pdf_hash: str) -> Optional[ResumePDF]:
    """Alias to the first row with this hash (kept for backward compatibility)."""
    return get_first_by_hash(db, pdf_hash)


def get_first_by_hash(db: Session, pdf_hash: str) -> Optional[ResumePDF]:
    """Return *any* ResumePDF row with this hash (first match)."""
    return db.query(ResumePDF).filter(ResumePDF.pdf_hash == pdf_hash).first()


def get_by_hash_and_user(db: Session, pdf_hash: str, user_id: int) -> Optional[ResumePDF]:
    """Return resume for a specific user & hash if it exists."""
    return (
        db.query(ResumePDF)
        .filter(ResumePDF.pdf_hash == pdf_hash, ResumePDF.uploaded_by == user_id)
        .first()
    )


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
